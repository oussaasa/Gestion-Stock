import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime

# ─── ReportLab PDF ────────────────────────────────────────────────────────────
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm, cm
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                     Paragraph, Spacer, HRFlowable)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False

# ─── Data Storage ─────────────────────────────────────────────────────────────

DATA_FILE = os.path.join(os.path.expanduser("~"), "stock_data.json")

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
            d.setdefault("clients", [])
            d.setdefault("commandes", [])
            return d
    return {"produits": [], "mouvements": [], "clients": [], "commandes": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def next_id(lst, key="id", prefix=""):
    if not lst:
        return f"{prefix}001"
    nums = []
    for x in lst:
        try:
            nums.append(int(str(x.get(key,"0")).replace(prefix,"")))
        except:
            nums.append(0)
    return f"{prefix}{max(nums)+1:03d}"

# ─── PDF Generator ────────────────────────────────────────────────────────────

def generer_facture_pdf(commande, client, produits_map, filepath):
    """Generate a professional invoice PDF using reportlab."""
    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        rightMargin=1.5*cm, leftMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )

    BLUE_DARK  = colors.HexColor("#1a2744")
    BLUE_MID   = colors.HexColor("#2563eb")
    BLUE_LIGHT = colors.HexColor("#dbeafe")
    GRAY_LIGHT = colors.HexColor("#f8fafc")
    GRAY_MID   = colors.HexColor("#e2e8f0")
    GRAY_TEXT  = colors.HexColor("#64748b")
    BLACK      = colors.HexColor("#0f172a")

    styles = getSampleStyleSheet()

    def style(name, **kw):
        return ParagraphStyle(name, **kw)

    s_title   = style("title",   fontSize=26, textColor=BLUE_DARK,
                      fontName="Helvetica-Bold", leading=30)
    s_normal  = style("normal",  fontSize=9,  textColor=BLACK,
                      fontName="Helvetica", leading=13)
    s_small   = style("small",   fontSize=8,  textColor=GRAY_TEXT,
                      fontName="Helvetica", leading=11)
    s_bold    = style("bold",    fontSize=9,  textColor=BLACK,
                      fontName="Helvetica-Bold", leading=13)
    s_right   = style("right",   fontSize=9,  textColor=BLACK,
                      fontName="Helvetica", alignment=TA_RIGHT)
    s_total   = style("total",   fontSize=12, textColor=BLUE_DARK,
                      fontName="Helvetica-Bold", alignment=TA_RIGHT)
    s_sub     = style("sub",     fontSize=8,  textColor=GRAY_TEXT,
                      fontName="Helvetica")

    story = []
    W = A4[0] - 3*cm  # usable width

    # ── HEADER: Logo + FACTURE ──────────────────────────────────────────────
    header_data = [[
        Paragraph("<b><font color='#1a2744' size='18'>GestionStock</font></b><br/>"
                  "<font color='#64748b' size='9'>Logiciel de gestion commerciale</font>", styles["Normal"]),
        Paragraph(f"<b><font color='#2563eb' size='26'>FACTURE</font></b><br/>"
                  f"<font color='#64748b' size='9'>N° {commande['numero']}</font>", styles["Normal"]),
    ]]
    header_tbl = Table(header_data, colWidths=[W*0.55, W*0.45])
    header_tbl.setStyle(TableStyle([
        ("ALIGN",     (1,0), (1,0), "RIGHT"),
        ("VALIGN",    (0,0), (-1,-1), "TOP"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 14),
    ]))
    story.append(header_tbl)
    story.append(HRFlowable(width="100%", thickness=2, color=BLUE_MID, spaceAfter=14))

    # ── INFO BLOCK: Émetteur / Client / Détails ─────────────────────────────
    date_cmd  = commande.get("date", datetime.now().strftime("%Y-%m-%d"))
    date_ech  = commande.get("echeance", date_cmd)
    statut    = commande.get("statut", "En attente")

    emetteur = (
        "<b>De :</b><br/>"
        "<b>Votre Entreprise SARL</b><br/>"
        "123 Rue du Commerce<br/>"
        "20000 Casablanca, Maroc<br/>"
        "Tél : +212 5XX-XXXXXX<br/>"
        "Email : contact@entreprise.ma<br/>"
        "IF : 12345678 | RC : 987654"
    )
    client_txt = (
        f"<b>Facturé à :</b><br/>"
        f"<b>{client.get('nom','')}</b><br/>"
        f"{client.get('adresse','')}<br/>"
        f"{client.get('ville','')}<br/>"
        f"Tél : {client.get('telephone','')}<br/>"
        f"Email : {client.get('email','')}<br/>"
        f"ICE : {client.get('ice','')}"
    )
    details_txt = (
        f"<b>Date de facturation :</b> {date_cmd}<br/>"
        f"<b>Date d'échéance :</b> {date_ech}<br/>"
        f"<b>Statut :</b> {statut}<br/>"
        f"<b>Conditions :</b> {commande.get('conditions','30 jours net')}"
    )

    info_data = [[
        Paragraph(emetteur,    s_normal),
        Paragraph(client_txt,  s_normal),
        Paragraph(details_txt, s_normal),
    ]]
    info_tbl = Table(info_data, colWidths=[W*0.33, W*0.34, W*0.33])
    info_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (0,0), GRAY_LIGHT),
        ("BACKGROUND",    (1,0), (1,0), BLUE_LIGHT),
        ("BACKGROUND",    (2,0), (2,0), GRAY_LIGHT),
        ("BOX",           (0,0), (-1,-1), 0.5, GRAY_MID),
        ("INNERGRID",     (0,0), (-1,-1), 0.5, GRAY_MID),
        ("TOPPADDING",    (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ]))
    story.append(info_tbl)
    story.append(Spacer(1, 18))

    # ── TABLE LIGNES ────────────────────────────────────────────────────────
    col_headers = ["Réf.", "Désignation", "Qté", "P.U. HT (MAD)", "TVA", "Total HT (MAD)"]
    col_widths  = [W*0.10, W*0.35, W*0.08, W*0.17, W*0.10, W*0.20]

    table_data = [col_headers]
    sous_total_ht = 0
    total_tva = 0

    for ligne in commande.get("lignes", []):
        p = produits_map.get(ligne["produit_nom"], {})
        ref   = p.get("ref", "-")
        qte   = ligne["quantite"]
        prix  = ligne["prix_unit"]
        tva   = ligne.get("tva", 20)
        ht    = qte * prix
        tva_m = ht * tva / 100
        sous_total_ht += ht
        total_tva     += tva_m
        table_data.append([
            Paragraph(str(ref), s_small),
            Paragraph(str(ligne["produit_nom"]), s_normal),
            Paragraph(str(qte), s_right),
            Paragraph(f"{prix:,.2f}", s_right),
            Paragraph(f"{tva}%", s_right),
            Paragraph(f"{ht:,.2f}", s_right),
        ])

    lines_tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    lines_tbl.setStyle(TableStyle([
        # Header row
        ("BACKGROUND",    (0,0), (-1,0), BLUE_DARK),
        ("TEXTCOLOR",     (0,0), (-1,0), colors.white),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,0), 9),
        ("ALIGN",         (0,0), (-1,0), "CENTER"),
        ("TOPPADDING",    (0,0), (-1,0), 10),
        ("BOTTOMPADDING", (0,0), (-1,0), 10),
        # Data rows
        ("FONTNAME",      (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE",      (0,1), (-1,-1), 9),
        ("ALIGN",         (2,1), (-1,-1), "RIGHT"),
        ("TOPPADDING",    (0,1), (-1,-1), 8),
        ("BOTTOMPADDING", (0,1), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("RIGHTPADDING",  (0,0), (-1,-1), 8),
        # Alternating rows
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, GRAY_LIGHT]),
        # Grid
        ("BOX",           (0,0), (-1,-1), 0.5, GRAY_MID),
        ("INNERGRID",     (0,0), (-1,-1), 0.3, GRAY_MID),
    ]))
    story.append(lines_tbl)
    story.append(Spacer(1, 16))

    # ── TOTALS ──────────────────────────────────────────────────────────────
    remise_pct  = commande.get("remise", 0)
    remise_mnt  = sous_total_ht * remise_pct / 100
    net_ht      = sous_total_ht - remise_mnt
    tva_net     = net_ht * (total_tva / sous_total_ht if sous_total_ht else 0.20)
    total_ttc   = net_ht + tva_net

    totals_data = []
    def total_row(label, val, bold=False, highlight=False):
        lp = Paragraph(f"<b>{label}</b>" if bold else label, s_right)
        vp = Paragraph(f"<b>{val}</b>"   if bold else val,   s_right)
        return [lp, vp]

    totals_data.append(total_row("Sous-total HT :", f"{sous_total_ht:,.2f} MAD"))
    if remise_pct:
        totals_data.append(total_row(f"Remise ({remise_pct}%) :", f"- {remise_mnt:,.2f} MAD"))
    totals_data.append(total_row("Net HT :", f"{net_ht:,.2f} MAD"))
    totals_data.append(total_row("TVA :", f"{tva_net:,.2f} MAD"))
    totals_data.append(total_row("TOTAL TTC :", f"{total_ttc:,.2f} MAD", bold=True))

    totals_tbl = Table(totals_data, colWidths=[W*0.7, W*0.3])
    ts = TableStyle([
        ("ALIGN",         (0,0), (-1,-1), "RIGHT"),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 8),
        ("LINEABOVE",     (0,-1), (-1,-1), 1.5, BLUE_MID),
        ("BACKGROUND",    (0,-1), (-1,-1), BLUE_LIGHT),
        ("FONTNAME",      (0,-1), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE",      (0,-1), (-1,-1), 11),
        ("TEXTCOLOR",     (0,-1), (-1,-1), BLUE_DARK),
    ])
    totals_tbl.setStyle(ts)
    story.append(totals_tbl)
    story.append(Spacer(1, 20))

    # ── NOTE / CONDITIONS ───────────────────────────────────────────────────
    note = commande.get("note", "")
    if note:
        story.append(Paragraph("<b>Note :</b>", s_bold))
        story.append(Paragraph(note, s_normal))
        story.append(Spacer(1, 10))

    story.append(HRFlowable(width="100%", thickness=1, color=GRAY_MID, spaceAfter=8))
    story.append(Paragraph(
        "Merci pour votre confiance. Ce document tient lieu de facture conformément "
        "à la legislation marocaine en vigueur. En cas de litige, seul le tribunal de "
        "Casablanca est compétent.",
        s_small
    ))

    doc.build(story)
    return filepath

# ─── Main Application ─────────────────────────────────────────────────────────

class GestionStock(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("📦 GestionStock Pro")
        self.geometry("1200x720")
        self.minsize(1000, 620)
        self.configure(bg="#0f1117")

        self.data = load_data()

        self.BG       = "#0f1117"
        self.PANEL    = "#1a1d27"
        self.CARD     = "#22263a"
        self.ACCENT   = "#4f8ef7"
        self.GREEN    = "#2ecc71"
        self.RED      = "#e74c3c"
        self.ORANGE   = "#f39c12"
        self.PURPLE   = "#9b59b6"
        self.FG       = "#e8eaf6"
        self.FG2      = "#8892b0"
        self.BORDER   = "#2d3155"

        self.font_title  = ("Segoe UI", 20, "bold")
        self.font_header = ("Segoe UI", 11, "bold")
        self.font_body   = ("Segoe UI", 10)
        self.font_small  = ("Segoe UI", 9)

        self._build_ui()

    def _build_ui(self):
        sidebar = tk.Frame(self, bg=self.PANEL, width=230)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        logo_frame = tk.Frame(sidebar, bg=self.PANEL)
        logo_frame.pack(fill="x", pady=(24, 16), padx=18)
        tk.Label(logo_frame, text="📦", font=("Segoe UI", 28), bg=self.PANEL, fg=self.ACCENT).pack()
        tk.Label(logo_frame, text="GestionStock Pro", font=("Segoe UI", 13, "bold"),
                 bg=self.PANEL, fg=self.FG).pack()
        tk.Label(logo_frame, text="v2.0", font=self.font_small, bg=self.PANEL, fg=self.FG2).pack()

        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", padx=14, pady=6)

        # Section labels
        def section(text):
            tk.Label(sidebar, text=text, font=("Segoe UI", 8, "bold"),
                     bg=self.PANEL, fg=self.FG2).pack(anchor="w", padx=18, pady=(10,2))

        self.nav_buttons = {}
        nav_items = [
            (None, "STOCK"),
            ("🏠  Tableau de bord", "dashboard"),
            ("📋  Produits",        "produits"),
            ("📥  Entrée stock",    "entree"),
            ("📤  Sortie stock",    "sortie"),
            ("📊  Historique",      "historique"),
            (None, "COMMERCIAL"),
            ("👥  Clients",         "clients"),
            ("🛒  Commandes",       "commandes"),
            ("🧾  Factures",        "factures"),
        ]
        for item in nav_items:
            label, key = item
            if label is None:
                section(key)
                continue
            btn = tk.Button(
                sidebar, text=label, anchor="w", font=self.font_body,
                bg=self.PANEL, fg=self.FG2, relief="flat", cursor="hand2",
                padx=18, pady=9, activebackground=self.CARD,
                activeforeground=self.ACCENT,
                command=lambda k=key: self._show_page(k)
            )
            btn.pack(fill="x", pady=1)
            self.nav_buttons[key] = btn

        tk.Label(sidebar, text="© 2026 GestionStock",
                 font=self.font_small, bg=self.PANEL, fg=self.FG2).pack(side="bottom", pady=12)

        self.main = tk.Frame(self, bg=self.BG)
        self.main.pack(side="left", fill="both", expand=True)
        self._show_page("dashboard")

    def _show_page(self, key):
        for k, btn in self.nav_buttons.items():
            btn.configure(bg=(self.CARD if k == key else self.PANEL),
                          fg=(self.ACCENT if k == key else self.FG2))
        for w in self.main.winfo_children():
            w.destroy()

        pages = {
            "dashboard":  self._page_dashboard,
            "produits":   self._page_produits,
            "entree":     lambda: self._page_mouvement("entree"),
            "sortie":     lambda: self._page_mouvement("sortie"),
            "historique": self._page_historique,
            "clients":    self._page_clients,
            "commandes":  self._page_commandes,
            "factures":   self._page_factures,
        }
        if key in pages:
            pages[key]()

    # ════════════════════════════════════════════════════════════════════════
    # PAGE: DASHBOARD
    # ════════════════════════════════════════════════════════════════════════

    def _page_dashboard(self):
        self._header("🏠 Tableau de bord", "Vue d'ensemble de votre activité")

        produits  = self.data["produits"]
        commandes = self.data["commandes"]
        clients   = self.data["clients"]

        total_valeur   = sum(p.get("prix",0)*p.get("quantite",0) for p in produits)
        alertes        = [p for p in produits if p.get("quantite",0) <= p.get("seuil_alerte",5)]
        ca_total       = sum(c.get("total_ttc",0) for c in commandes)
        nb_en_attente  = sum(1 for c in commandes if c.get("statut","") == "En attente")

        kpis = [
            ("📦 Produits",       str(len(produits)),        self.ACCENT),
            ("👥 Clients",        str(len(clients)),         self.PURPLE),
            ("🛒 Commandes",      str(len(commandes)),       self.ORANGE),
            ("💰 CA Total",       f"{ca_total:,.0f} MAD",    self.GREEN),
            ("⚠️ Alertes stock",  str(len(alertes)),         self.RED),
        ]
        kpi_frame = tk.Frame(self.main, bg=self.BG)
        kpi_frame.pack(fill="x", padx=28, pady=(10,18))
        for i, (title, val, color) in enumerate(kpis):
            card = tk.Frame(kpi_frame, bg=self.CARD, padx=20, pady=16)
            card.grid(row=0, column=i, sticky="nsew", padx=6)
            kpi_frame.columnconfigure(i, weight=1)
            tk.Label(card, text=title, font=self.font_small, bg=self.CARD, fg=self.FG2).pack(anchor="w")
            tk.Label(card, text=val, font=("Segoe UI",16,"bold"), bg=self.CARD, fg=color).pack(anchor="w", pady=(4,0))

        # Two columns bottom
        cols = tk.Frame(self.main, bg=self.BG)
        cols.pack(fill="both", expand=True, padx=28, pady=4)
        cols.columnconfigure(0, weight=2)
        cols.columnconfigure(1, weight=1)

        left = tk.Frame(cols, bg=self.CARD, padx=16, pady=14)
        left.grid(row=0, column=0, sticky="nsew", padx=(0,10))
        tk.Label(left, text="🧾 Dernières commandes", font=self.font_header,
                 bg=self.CARD, fg=self.FG).pack(anchor="w", pady=(0,10))
        tree_cols = ("N°", "Client", "Date", "Total TTC", "Statut")
        tree = ttk.Treeview(left, columns=tree_cols, show="headings", height=10)
        self._style_tree(tree, tree_cols, [80, 200, 110, 110, 100])
        tree.pack(fill="both", expand=True)
        for c in reversed(commandes[-12:]):
            color_tag = {"Payée":"payee","En attente":"attente","Annulée":"annulee"}.get(c.get("statut",""),"")
            tree.insert("", "end", values=(
                c.get("numero",""), c.get("client_nom",""), c.get("date",""),
                f"{c.get('total_ttc',0):,.2f} MAD", c.get("statut","")
            ), tags=(color_tag,))
        tree.tag_configure("payee",   foreground=self.GREEN)
        tree.tag_configure("attente", foreground=self.ORANGE)
        tree.tag_configure("annulee", foreground=self.RED)

        right = tk.Frame(cols, bg=self.CARD, padx=16, pady=14)
        right.grid(row=0, column=1, sticky="nsew")
        tk.Label(right, text="⚠️ Alertes stock", font=self.font_header,
                 bg=self.CARD, fg=self.ORANGE).pack(anchor="w", pady=(0,8))
        if not alertes:
            tk.Label(right, text="✅ Aucune alerte", font=self.font_body,
                     bg=self.CARD, fg=self.GREEN).pack(pady=20)
        else:
            for p in alertes[:10]:
                row = tk.Frame(right, bg=self.PANEL, padx=10, pady=5)
                row.pack(fill="x", pady=2)
                c = self.RED if p["quantite"] == 0 else self.ORANGE
                tk.Label(row, text=p["nom"], font=self.font_small, bg=self.PANEL, fg=self.FG).pack(anchor="w")
                tk.Label(row, text=f"Qté : {p['quantite']}", font=self.font_small, bg=self.PANEL, fg=c).pack(anchor="w")

    # ════════════════════════════════════════════════════════════════════════
    # PAGE: CLIENTS
    # ════════════════════════════════════════════════════════════════════════

    def _page_clients(self):
        self._header("👥 Gestion des clients", "Créer et gérer vos clients")

        tb = tk.Frame(self.main, bg=self.BG)
        tb.pack(fill="x", padx=28, pady=(4,12))
        self._btn(tb, "➕ Nouveau client",  self._dialog_client,     self.GREEN).pack(side="left", padx=(0,8))
        self._btn(tb, "✏️ Modifier",        self._modifier_client,   self.ACCENT).pack(side="left", padx=(0,8))
        self._btn(tb, "🗑️ Supprimer",       self._supprimer_client,  self.RED).pack(side="left")

        frame = tk.Frame(self.main, bg=self.BG)
        frame.pack(fill="both", expand=True, padx=28, pady=(0,16))

        cols = ("ID", "Nom", "Téléphone", "Email", "Ville", "ICE", "Nb commandes")
        self.tree_clients = ttk.Treeview(frame, columns=cols, show="headings", height=18)
        self._style_tree(self.tree_clients, cols, [60,200,120,200,120,110,100])
        sb = ttk.Scrollbar(frame, orient="vertical", command=self.tree_clients.yview)
        self.tree_clients.configure(yscrollcommand=sb.set)
        self.tree_clients.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._refresh_clients()

    def _refresh_clients(self):
        if not hasattr(self, "tree_clients"): return
        self.tree_clients.delete(*self.tree_clients.get_children())
        for c in self.data["clients"]:
            nb_cmd = sum(1 for cmd in self.data["commandes"] if cmd.get("client_id") == c.get("id"))
            self.tree_clients.insert("", "end", values=(
                c.get("id",""), c.get("nom",""), c.get("telephone",""),
                c.get("email",""), c.get("ville",""), c.get("ice",""), nb_cmd
            ))

    def _dialog_client(self, client=None):
        win = self._dialog("Nouveau client" if not client else "Modifier client", 460, 500)
        fields = {}
        form_fields = [
            ("Nom / Raison sociale *", "nom",       client.get("nom","")       if client else ""),
            ("Téléphone",              "telephone", client.get("telephone","") if client else ""),
            ("Email",                  "email",     client.get("email","")     if client else ""),
            ("Adresse",                "adresse",   client.get("adresse","")   if client else ""),
            ("Ville",                  "ville",     client.get("ville","")     if client else ""),
            ("ICE / CIN",              "ice",       client.get("ice","")       if client else ""),
        ]
        for label, key, default in form_fields:
            tk.Label(win, text=label, font=self.font_small, bg=self.CARD, fg=self.FG2).pack(anchor="w", padx=24, pady=(8,2))
            e = tk.Entry(win, font=self.font_body, bg=self.PANEL, fg=self.FG,
                         insertbackground=self.FG, relief="flat")
            e.insert(0, default)
            e.pack(fill="x", padx=24, ipady=6)
            fields[key] = e

        def save():
            nom = fields["nom"].get().strip()
            if not nom:
                messagebox.showerror("Erreur", "Le nom est obligatoire.", parent=win)
                return
            c = {k: fields[k].get().strip() for k in fields}
            if client:
                c["id"] = client["id"]
                idx = next(i for i,x in enumerate(self.data["clients"]) if x["id"]==client["id"])
                self.data["clients"][idx] = c
            else:
                c["id"] = next_id(self.data["clients"], "id", "C")
                self.data["clients"].append(c)
            save_data(self.data)
            win.destroy()
            self._refresh_clients()

        bf = tk.Frame(win, bg=self.CARD)
        bf.pack(fill="x", padx=24, pady=16)
        self._btn(bf, "💾 Enregistrer", save, self.GREEN).pack(side="right", padx=(8,0))
        self._btn(bf, "Annuler", win.destroy, "#555").pack(side="right")

    def _modifier_client(self):
        c = self._get_selected_client()
        if c: self._dialog_client(c)

    def _supprimer_client(self):
        c = self._get_selected_client()
        if c and messagebox.askyesno("Confirmer", f"Supprimer le client « {c['nom']} » ?"):
            self.data["clients"] = [x for x in self.data["clients"] if x["id"] != c["id"]]
            save_data(self.data)
            self._refresh_clients()

    def _get_selected_client(self):
        if not hasattr(self, "tree_clients"): return None
        sel = self.tree_clients.selection()
        if not sel:
            messagebox.showinfo("Info", "Sélectionnez un client.")
            return None
        cid = str(self.tree_clients.item(sel[0])["values"][0])
        return next((c for c in self.data["clients"] if str(c.get("id","")) == cid), None)

    # ════════════════════════════════════════════════════════════════════════
    # PAGE: COMMANDES
    # ════════════════════════════════════════════════════════════════════════

    def _page_commandes(self):
        self._header("🛒 Commandes", "Créer et gérer les commandes clients")

        tb = tk.Frame(self.main, bg=self.BG)
        tb.pack(fill="x", padx=28, pady=(4,12))
        self._btn(tb, "➕ Nouvelle commande",  self._dialog_commande,     self.GREEN).pack(side="left", padx=(0,8))
        self._btn(tb, "✏️ Modifier statut",    self._modifier_statut_cmd, self.ACCENT).pack(side="left", padx=(0,8))
        self._btn(tb, "🗑️ Supprimer",          self._supprimer_commande,  self.RED).pack(side="left", padx=(0,8))
        self._btn(tb, "📄 Générer PDF",        self._generer_pdf_commande, self.PURPLE).pack(side="left")

        frame = tk.Frame(self.main, bg=self.BG)
        frame.pack(fill="both", expand=True, padx=28, pady=(0,16))

        cols = ("N°", "Date", "Client", "Nb articles", "Total HT", "Total TTC", "Statut")
        self.tree_cmd = ttk.Treeview(frame, columns=cols, show="headings", height=18)
        self._style_tree(self.tree_cmd, cols, [80,110,200,90,120,120,100])
        sb = ttk.Scrollbar(frame, orient="vertical", command=self.tree_cmd.yview)
        self.tree_cmd.configure(yscrollcommand=sb.set)
        self.tree_cmd.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree_cmd.bind("<Double-1>", lambda e: self._voir_commande())
        self._refresh_commandes()

    def _refresh_commandes(self):
        if not hasattr(self, "tree_cmd"): return
        self.tree_cmd.delete(*self.tree_cmd.get_children())
        for c in reversed(self.data["commandes"]):
            tag = {"Payée":"payee","En attente":"attente","Annulée":"annulee"}.get(c.get("statut",""),"")
            nb = sum(l["quantite"] for l in c.get("lignes",[]))
            self.tree_cmd.insert("", "end", values=(
                c.get("numero",""), c.get("date",""), c.get("client_nom",""),
                nb, f"{c.get('total_ht',0):,.2f}", f"{c.get('total_ttc',0):,.2f}", c.get("statut","")
            ), tags=(tag,))
        self.tree_cmd.tag_configure("payee",   foreground=self.GREEN)
        self.tree_cmd.tag_configure("attente", foreground=self.ORANGE)
        self.tree_cmd.tag_configure("annulee", foreground=self.RED)

    def _dialog_commande(self):
        if not self.data["clients"]:
            messagebox.showwarning("Attention", "Ajoutez d'abord un client.")
            return
        if not self.data["produits"]:
            messagebox.showwarning("Attention", "Ajoutez d'abord des produits.")
            return

        win = tk.Toplevel(self)
        win.title("Nouvelle commande")
        win.geometry("860x640")
        win.configure(bg=self.CARD)
        win.grab_set()

        tk.Label(win, text="🛒 Nouvelle Commande", font=self.font_header,
                 bg=self.CARD, fg=self.FG).pack(pady=(18,4))
        ttk.Separator(win, orient="horizontal").pack(fill="x", padx=24, pady=6)

        # Top: Client info
        top = tk.Frame(win, bg=self.CARD)
        top.pack(fill="x", padx=24, pady=6)

        # Client selector
        tk.Label(top, text="Client *", font=self.font_small, bg=self.CARD, fg=self.FG2).grid(row=0,column=0,sticky="w",pady=4)
        client_names = [f"{c['id']} - {c['nom']}" for c in self.data["clients"]]
        client_var = tk.StringVar()
        client_cb = ttk.Combobox(top, textvariable=client_var, values=client_names,
                                  state="readonly", font=self.font_body, width=28)
        client_cb.grid(row=0,column=1,sticky="w",padx=(12,0),pady=4)

        # Client info display
        client_info = tk.Label(top, text="", font=self.font_small, bg=self.CARD, fg=self.FG2)
        client_info.grid(row=1,column=1,sticky="w",padx=(12,0))

        def on_client(e=None):
            val = client_var.get()
            cid = val.split(" - ")[0] if val else ""
            c = next((x for x in self.data["clients"] if str(x.get("id",""))==cid), None)
            if c:
                client_info.configure(text=f"{c.get('telephone','')}  |  {c.get('email','')}  |  {c.get('ville','')}")
        client_cb.bind("<<ComboboxSelected>>", on_client)

        # Date + remise + conditions
        tk.Label(top, text="Date",       font=self.font_small, bg=self.CARD, fg=self.FG2).grid(row=0,column=2,sticky="w",padx=(24,0))
        date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        tk.Entry(top, textvariable=date_var, font=self.font_body, bg=self.PANEL, fg=self.FG,
                 insertbackground=self.FG, relief="flat", width=12).grid(row=0,column=3,sticky="w",padx=(8,0),ipady=4)

        tk.Label(top, text="Remise %",   font=self.font_small, bg=self.CARD, fg=self.FG2).grid(row=1,column=2,sticky="w",padx=(24,0))
        remise_var = tk.StringVar(value="0")
        tk.Entry(top, textvariable=remise_var, font=self.font_body, bg=self.PANEL, fg=self.FG,
                 insertbackground=self.FG, relief="flat", width=8).grid(row=1,column=3,sticky="w",padx=(8,0),ipady=4)

        ttk.Separator(win, orient="horizontal").pack(fill="x", padx=24, pady=6)

        # Add article
        add_frame = tk.Frame(win, bg=self.PANEL, padx=14, pady=10)
        add_frame.pack(fill="x", padx=24, pady=(0,6))
        tk.Label(add_frame, text="Ajouter une ligne :", font=self.font_small,
                 bg=self.PANEL, fg=self.FG2).grid(row=0,column=0,columnspan=6,sticky="w",pady=(0,6))

        prod_names = [p["nom"] for p in self.data["produits"]]
        prod_var2 = tk.StringVar()
        ttk.Combobox(add_frame, textvariable=prod_var2, values=prod_names,
                     state="readonly", font=self.font_body, width=22).grid(row=1,column=0,padx=(0,8))

        tk.Label(add_frame, text="Qté", font=self.font_small, bg=self.PANEL, fg=self.FG2).grid(row=1,column=1)
        qte_var2 = tk.StringVar(value="1")
        tk.Entry(add_frame, textvariable=qte_var2, font=self.font_body, bg=self.CARD, fg=self.FG,
                 insertbackground=self.FG, relief="flat", width=6).grid(row=1,column=2,padx=6,ipady=4)

        tk.Label(add_frame, text="P.U. HT", font=self.font_small, bg=self.PANEL, fg=self.FG2).grid(row=1,column=3)
        pu_var = tk.StringVar()
        pu_entry = tk.Entry(add_frame, textvariable=pu_var, font=self.font_body, bg=self.CARD, fg=self.FG,
                            insertbackground=self.FG, relief="flat", width=10)
        pu_entry.grid(row=1,column=4,padx=6,ipady=4)

        tk.Label(add_frame, text="TVA %", font=self.font_small, bg=self.PANEL, fg=self.FG2).grid(row=1,column=5)
        tva_var = tk.StringVar(value="20")
        tk.Entry(add_frame, textvariable=tva_var, font=self.font_body, bg=self.CARD, fg=self.FG,
                 insertbackground=self.FG, relief="flat", width=6).grid(row=1,column=6,padx=6,ipady=4)

        def auto_prix(e=None):
            nom = prod_var2.get()
            p = next((x for x in self.data["produits"] if x["nom"]==nom), None)
            if p:
                pu_var.set(str(p.get("prix",0)))
        prod_var2.trace("w", lambda *a: auto_prix())

        lignes = []

        # Lines table
        lines_frame = tk.Frame(win, bg=self.BG)
        lines_frame.pack(fill="both", expand=True, padx=24)

        line_cols = ("Produit", "Qté", "P.U. HT", "TVA", "Total HT")
        tree_lines = ttk.Treeview(lines_frame, columns=line_cols, show="headings", height=8)
        self._style_tree(tree_lines, line_cols, [260,70,110,70,130])
        tree_lines.pack(fill="both", expand=True)

        # Totals label
        total_lbl = tk.Label(win, text="", font=("Segoe UI",11,"bold"),
                              bg=self.CARD, fg=self.GREEN)
        total_lbl.pack(anchor="e", padx=28, pady=4)

        def refresh_lines():
            tree_lines.delete(*tree_lines.get_children())
            ht = 0
            for l in lignes:
                lht = l["quantite"]*l["prix_unit"]
                ht += lht
                tree_lines.insert("", "end", values=(
                    l["produit_nom"], l["quantite"],
                    f"{l['prix_unit']:.2f}", f"{l.get('tva',20)}%", f"{lht:.2f}"
                ))
            remise = float(remise_var.get() or 0)
            net_ht = ht * (1 - remise/100)
            tva_mnt = net_ht * 0.20
            ttc = net_ht + tva_mnt
            total_lbl.configure(text=f"HT : {net_ht:,.2f} MAD  |  TVA : {tva_mnt:,.2f} MAD  |  TTC : {ttc:,.2f} MAD")

        def ajouter_ligne():
            nom = prod_var2.get()
            if not nom:
                messagebox.showwarning("Attention", "Choisissez un produit.", parent=win)
                return
            try:
                qte = int(qte_var2.get())
                pu  = float(pu_var.get())
                tva = float(tva_var.get())
            except ValueError:
                messagebox.showerror("Erreur", "Quantité, prix et TVA doivent être des nombres.", parent=win)
                return
            # Check stock
            p = next((x for x in self.data["produits"] if x["nom"]==nom), None)
            already = sum(l["quantite"] for l in lignes if l["produit_nom"]==nom)
            if p and p["quantite"] - already < qte:
                messagebox.showerror("Erreur", f"Stock insuffisant ! Disponible : {p['quantite'] - already}", parent=win)
                return
            # Update or add
            existing = next((l for l in lignes if l["produit_nom"]==nom), None)
            if existing:
                existing["quantite"] += qte
            else:
                lignes.append({"produit_nom":nom,"quantite":qte,"prix_unit":pu,"tva":tva})
            refresh_lines()

        def suppr_ligne():
            sel = tree_lines.selection()
            if sel:
                nom = tree_lines.item(sel[0])["values"][0]
                lignes[:] = [l for l in lignes if l["produit_nom"]!=nom]
                refresh_lines()

        self._btn(add_frame, "➕ Ajouter", ajouter_ligne, self.GREEN).grid(row=1,column=7,padx=(10,0))
        self._btn(add_frame, "🗑️", suppr_ligne, self.RED).grid(row=1,column=8,padx=4)

        # Note
        note_frame = tk.Frame(win, bg=self.CARD)
        note_frame.pack(fill="x", padx=24, pady=4)
        tk.Label(note_frame, text="Note :", font=self.font_small, bg=self.CARD, fg=self.FG2).pack(side="left")
        note_var = tk.StringVar()
        tk.Entry(note_frame, textvariable=note_var, font=self.font_body, bg=self.PANEL, fg=self.FG,
                 insertbackground=self.FG, relief="flat").pack(side="left", fill="x", expand=True, padx=8, ipady=4)

        # Buttons
        bf = tk.Frame(win, bg=self.CARD)
        bf.pack(fill="x", padx=24, pady=12)

        def valider():
            if not client_var.get():
                messagebox.showerror("Erreur", "Choisissez un client.", parent=win)
                return
            if not lignes:
                messagebox.showerror("Erreur", "Ajoutez au moins un produit.", parent=win)
                return
            val = client_var.get()
            cid = val.split(" - ")[0]
            client = next((c for c in self.data["clients"] if str(c.get("id",""))==cid), None)

            remise = float(remise_var.get() or 0)
            ht = sum(l["quantite"]*l["prix_unit"] for l in lignes)
            net_ht = ht * (1-remise/100)
            tva_mnt = net_ht * 0.20
            ttc = net_ht + tva_mnt

            # Decrease stock
            for l in lignes:
                p = next((x for x in self.data["produits"] if x["nom"]==l["produit_nom"]), None)
                if p:
                    p["quantite"] -= l["quantite"]
                    self.data["mouvements"].append({
                        "date":    datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "produit": l["produit_nom"],
                        "type":    "sortie",
                        "quantite":l["quantite"],
                        "note":    f"Commande {next_id(self.data['commandes'],'numero','CMD')}",
                    })

            cmd = {
                "numero":     next_id(self.data["commandes"], "numero", "CMD"),
                "date":       date_var.get(),
                "echeance":   date_var.get(),
                "client_id":  client["id"] if client else "",
                "client_nom": client["nom"] if client else val,
                "lignes":     lignes[:],
                "remise":     remise,
                "total_ht":   round(net_ht,2),
                "total_tva":  round(tva_mnt,2),
                "total_ttc":  round(ttc,2),
                "statut":     "En attente",
                "note":       note_var.get(),
                "conditions": "30 jours net",
            }
            self.data["commandes"].append(cmd)
            save_data(self.data)
            win.destroy()
            self._refresh_commandes()
            if messagebox.askyesno("Succès", f"Commande {cmd['numero']} créée !\nGénérer le PDF maintenant ?"):
                self._generer_pdf_pour(cmd)

        self._btn(bf, "✅ Valider la commande", valider, self.GREEN).pack(side="right", padx=(8,0))
        self._btn(bf, "Annuler", win.destroy, "#555").pack(side="right")

    def _modifier_statut_cmd(self):
        cmd = self._get_selected_commande()
        if not cmd: return
        win = self._dialog("Modifier le statut", 320, 200)
        statut_var = tk.StringVar(value=cmd.get("statut","En attente"))
        for s in ["En attente", "Payée", "Annulée"]:
            colors_map = {"En attente": self.ORANGE, "Payée": self.GREEN, "Annulée": self.RED}
            tk.Radiobutton(win, text=s, variable=statut_var, value=s,
                           bg=self.CARD, fg=colors_map[s], selectcolor=self.PANEL,
                           activebackground=self.CARD, font=self.font_body).pack(pady=6)
        def save():
            idx = next(i for i,c in enumerate(self.data["commandes"]) if c["numero"]==cmd["numero"])
            self.data["commandes"][idx]["statut"] = statut_var.get()
            save_data(self.data)
            win.destroy()
            self._refresh_commandes()
        self._btn(win, "💾 Enregistrer", save, self.GREEN).pack(pady=10)

    def _supprimer_commande(self):
        cmd = self._get_selected_commande()
        if cmd and messagebox.askyesno("Confirmer", f"Supprimer la commande {cmd['numero']} ?"):
            self.data["commandes"] = [c for c in self.data["commandes"] if c["numero"]!=cmd["numero"]]
            save_data(self.data)
            self._refresh_commandes()

    def _voir_commande(self):
        cmd = self._get_selected_commande()
        if not cmd: return
        win = tk.Toplevel(self)
        win.title(f"Commande {cmd['numero']}")
        win.geometry("600x500")
        win.configure(bg=self.CARD)
        tk.Label(win, text=f"Commande {cmd['numero']}  —  {cmd['client_nom']}",
                 font=self.font_header, bg=self.CARD, fg=self.FG).pack(pady=(16,4))
        ttk.Separator(win, orient="horizontal").pack(fill="x", padx=24, pady=6)
        cols = ("Produit","Qté","P.U. HT","TVA","Total HT")
        tree = ttk.Treeview(win, columns=cols, show="headings", height=12)
        self._style_tree(tree, cols, [240,70,110,70,110])
        tree.pack(fill="both", expand=True, padx=24)
        for l in cmd.get("lignes",[]):
            ht = l["quantite"]*l["prix_unit"]
            tree.insert("","end",values=(l["produit_nom"],l["quantite"],f"{l['prix_unit']:.2f}",f"{l.get('tva',20)}%",f"{ht:.2f}"))
        tk.Label(win, text=f"Total TTC : {cmd.get('total_ttc',0):,.2f} MAD  |  Statut : {cmd.get('statut','')}",
                 font=("Segoe UI",11,"bold"), bg=self.CARD, fg=self.GREEN).pack(pady=10)
        self._btn(win, "📄 Générer PDF", lambda: self._generer_pdf_pour(cmd), self.PURPLE).pack(pady=4)

    def _generer_pdf_commande(self):
        cmd = self._get_selected_commande()
        if cmd: self._generer_pdf_pour(cmd)

    def _generer_pdf_pour(self, cmd):
        if not REPORTLAB_OK:
            messagebox.showerror("Erreur", "reportlab n'est pas installé.\nLancez : pip install reportlab")
            return
        client = next((c for c in self.data["clients"] if str(c.get("id",""))==str(cmd.get("client_id",""))), {})
        produits_map = {p["nom"]: p for p in self.data["produits"]}

        default_name = f"Facture_{cmd['numero']}_{cmd['client_nom'].replace(' ','_')}.pdf"
        filepath = filedialog.asksaveasfilename(
            title="Enregistrer la facture PDF",
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("PDF files","*.pdf")]
        )
        if not filepath: return
        try:
            generer_facture_pdf(cmd, client, produits_map, filepath)
            messagebox.showinfo("Succès", f"Facture générée :\n{filepath}")
        except Exception as e:
            messagebox.showerror("Erreur PDF", str(e))

    def _get_selected_commande(self):
        if not hasattr(self, "tree_cmd"): return None
        sel = self.tree_cmd.selection()
        if not sel:
            messagebox.showinfo("Info", "Sélectionnez une commande.")
            return None
        num = str(self.tree_cmd.item(sel[0])["values"][0])
        return next((c for c in self.data["commandes"] if str(c.get("numero",""))==num), None)

    # ════════════════════════════════════════════════════════════════════════
    # PAGE: FACTURES
    # ════════════════════════════════════════════════════════════════════════

    def _page_factures(self):
        self._header("🧾 Factures", "Générer et gérer vos factures PDF")

        tb = tk.Frame(self.main, bg=self.BG)
        tb.pack(fill="x", padx=28, pady=(4,12))
        self._btn(tb, "📄 Générer PDF sélection", self._generer_pdf_commande2, self.PURPLE).pack(side="left", padx=(0,8))
        self._btn(tb, "👁️ Voir détails",          self._voir_commande2,        self.ACCENT).pack(side="left", padx=(0,8))

        # Filter by status
        filter_var = tk.StringVar(value="Toutes")
        filter_frame = tk.Frame(tb, bg=self.BG)
        filter_frame.pack(side="right")
        for val in ["Toutes","En attente","Payée","Annulée"]:
            tk.Radiobutton(filter_frame, text=val, variable=filter_var, value=val,
                           bg=self.BG, fg=self.FG, selectcolor=self.CARD,
                           activebackground=self.BG, font=self.font_small,
                           command=lambda: self._refresh_factures(filter_var.get())
                           ).pack(side="left", padx=6)

        frame = tk.Frame(self.main, bg=self.BG)
        frame.pack(fill="both", expand=True, padx=28, pady=(0,16))

        cols = ("N° Facture","Date","Client","Total HT","TVA","Total TTC","Statut")
        self.tree_fact = ttk.Treeview(frame, columns=cols, show="headings", height=18)
        self._style_tree(self.tree_fact, cols, [100,110,210,110,110,120,100])
        sb = ttk.Scrollbar(frame, orient="vertical", command=self.tree_fact.yview)
        self.tree_fact.configure(yscrollcommand=sb.set)
        self.tree_fact.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree_fact.bind("<Double-1>", lambda e: self._generer_pdf_commande2())
        self._refresh_factures("Toutes")

    def _refresh_factures(self, filtre):
        if not hasattr(self, "tree_fact"): return
        self.tree_fact.delete(*self.tree_fact.get_children())
        for c in reversed(self.data["commandes"]):
            if filtre != "Toutes" and c.get("statut","") != filtre: continue
            tag = {"Payée":"payee","En attente":"attente","Annulée":"annulee"}.get(c.get("statut",""),"")
            self.tree_fact.insert("", "end", values=(
                c.get("numero",""), c.get("date",""), c.get("client_nom",""),
                f"{c.get('total_ht',0):,.2f}", f"{c.get('total_tva',0):,.2f}",
                f"{c.get('total_ttc',0):,.2f}", c.get("statut","")
            ), tags=(tag,))
        self.tree_fact.tag_configure("payee",   foreground=self.GREEN)
        self.tree_fact.tag_configure("attente", foreground=self.ORANGE)
        self.tree_fact.tag_configure("annulee", foreground=self.RED)

    def _generer_pdf_commande2(self):
        if not hasattr(self, "tree_fact"): return
        sel = self.tree_fact.selection()
        if not sel:
            messagebox.showinfo("Info","Sélectionnez une facture.")
            return
        num = str(self.tree_fact.item(sel[0])["values"][0])
        cmd = next((c for c in self.data["commandes"] if str(c.get("numero",""))==num), None)
        if cmd: self._generer_pdf_pour(cmd)

    def _voir_commande2(self):
        if not hasattr(self, "tree_fact"): return
        sel = self.tree_fact.selection()
        if not sel: return
        num = str(self.tree_fact.item(sel[0])["values"][0])
        cmd = next((c for c in self.data["commandes"] if str(c.get("numero",""))==num), None)
        if cmd: self._voir_commande_detail(cmd)

    def _voir_commande_detail(self, cmd):
        win = tk.Toplevel(self)
        win.title(f"Facture {cmd['numero']}")
        win.geometry("620x520")
        win.configure(bg=self.CARD)
        client = next((c for c in self.data["clients"] if str(c.get("id",""))==str(cmd.get("client_id",""))), {})

        tk.Label(win, text=f"Facture {cmd['numero']}", font=self.font_header, bg=self.CARD, fg=self.FG).pack(pady=(16,2))
        tk.Label(win, text=f"Client : {cmd['client_nom']}  |  Date : {cmd['date']}  |  {cmd.get('statut','')}",
                 font=self.font_small, bg=self.CARD, fg=self.FG2).pack()
        if client:
            tk.Label(win, text=f"Tél : {client.get('telephone','')}  |  Email : {client.get('email','')}  |  Ville : {client.get('ville','')}",
                     font=self.font_small, bg=self.CARD, fg=self.ACCENT).pack()
        ttk.Separator(win, orient="horizontal").pack(fill="x", padx=24, pady=8)

        cols = ("Produit","Qté","P.U. HT","TVA","Total HT")
        tree = ttk.Treeview(win, columns=cols, show="headings", height=10)
        self._style_tree(tree, cols, [240,70,110,70,110])
        tree.pack(fill="both", expand=True, padx=24)
        for l in cmd.get("lignes",[]):
            ht = l["quantite"]*l["prix_unit"]
            tree.insert("","end",values=(l["produit_nom"],l["quantite"],f"{l['prix_unit']:.2f}",f"{l.get('tva',20)}%",f"{ht:.2f}"))

        total_frame = tk.Frame(win, bg=self.PANEL, padx=20, pady=12)
        total_frame.pack(fill="x", padx=24, pady=8)
        for label, val in [
            ("Total HT :", f"{cmd.get('total_ht',0):,.2f} MAD"),
            ("TVA :",      f"{cmd.get('total_tva',0):,.2f} MAD"),
            ("TOTAL TTC :",f"{cmd.get('total_ttc',0):,.2f} MAD"),
        ]:
            row = tk.Frame(total_frame, bg=self.PANEL)
            row.pack(fill="x")
            tk.Label(row, text=label, font=self.font_body, bg=self.PANEL, fg=self.FG2, width=14, anchor="e").pack(side="left")
            tk.Label(row, text=val, font=("Segoe UI",10,"bold"), bg=self.PANEL, fg=self.GREEN).pack(side="left", padx=8)

        bf = tk.Frame(win, bg=self.CARD)
        bf.pack(pady=8)
        self._btn(bf, "📄 Générer PDF", lambda: self._generer_pdf_pour(cmd), self.PURPLE).pack(side="left", padx=8)
        self._btn(bf, "Fermer", win.destroy, "#555").pack(side="left")

    # ════════════════════════════════════════════════════════════════════════
    # PAGES STOCK (unchanged from v1)
    # ════════════════════════════════════════════════════════════════════════

    def _page_produits(self):
        self._header("📋 Gestion des produits", "Ajouter, modifier et supprimer des produits")
        tb = tk.Frame(self.main, bg=self.BG)
        tb.pack(fill="x", padx=28, pady=(4,12))
        self._btn(tb, "➕ Nouveau produit", self._dialog_ajouter_produit, self.GREEN).pack(side="left", padx=(0,8))
        self._btn(tb, "✏️ Modifier",        self._modifier_produit,       self.ACCENT).pack(side="left", padx=(0,8))
        self._btn(tb, "🗑️ Supprimer",       self._supprimer_produit,      self.RED).pack(side="left")
        search_var = tk.StringVar()
        search_var.trace("w", lambda *a: self._filter_produits(search_var.get()))
        sf = tk.Frame(tb, bg=self.BG)
        sf.pack(side="right")
        tk.Label(sf, text="🔍", bg=self.BG, fg=self.FG2, font=self.font_body).pack(side="left")
        tk.Entry(sf, textvariable=search_var, bg=self.CARD, fg=self.FG,
                 insertbackground=self.FG, relief="flat", font=self.font_body, width=22).pack(side="left", ipady=5, ipadx=8)
        frame = tk.Frame(self.main, bg=self.BG)
        frame.pack(fill="both", expand=True, padx=28, pady=(0,16))
        cols = ("Référence","Nom","Catégorie","Quantité","Prix unit.","Valeur","Seuil alerte","Statut")
        self.tree_prod = ttk.Treeview(frame, columns=cols, show="headings", height=18)
        self._style_tree(self.tree_prod, cols, [100,200,130,80,90,100,100,90])
        sb = ttk.Scrollbar(frame, orient="vertical", command=self.tree_prod.yview)
        self.tree_prod.configure(yscrollcommand=sb.set)
        self.tree_prod.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._search_query = ""
        self._refresh_produits()

    def _filter_produits(self, q):
        self._search_query = q.lower()
        self._refresh_produits()

    def _refresh_produits(self):
        if not hasattr(self, "tree_prod"): return
        self.tree_prod.delete(*self.tree_prod.get_children())
        for p in self.data["produits"]:
            q = getattr(self, "_search_query", "")
            if q and q not in p["nom"].lower() and q not in p.get("ref","").lower(): continue
            valeur = p.get("prix",0) * p.get("quantite",0)
            qte, seuil = p.get("quantite",0), p.get("seuil_alerte",5)
            statut = "🔴 Rupture" if qte==0 else ("🟡 Faible" if qte<=seuil else "🟢 Normal")
            tag = "rupture" if qte==0 else ("faible" if qte<=seuil else "normal")
            self.tree_prod.insert("","end",values=(
                p.get("ref",""),p["nom"],p.get("categorie",""),qte,
                f"{p.get('prix',0):.2f}",f"{valeur:.2f}",seuil,statut
            ),tags=(tag,))
        self.tree_prod.tag_configure("rupture", foreground=self.RED)
        self.tree_prod.tag_configure("faible",  foreground=self.ORANGE)
        self.tree_prod.tag_configure("normal",  foreground=self.GREEN)

    def _dialog_ajouter_produit(self, produit=None):
        win = self._dialog("Nouveau produit" if not produit else "Modifier produit", 420, 460)
        fields = {}
        form = [
            ("Référence","ref",str(produit.get("ref","")) if produit else ""),
            ("Nom du produit","nom",produit.get("nom","") if produit else ""),
            ("Catégorie","categorie",produit.get("categorie","") if produit else ""),
            ("Quantité","quantite",str(produit.get("quantite",0)) if produit else "0"),
            ("Prix unitaire","prix",str(produit.get("prix",0)) if produit else "0"),
            ("Seuil alerte","seuil_alerte",str(produit.get("seuil_alerte",5)) if produit else "5"),
        ]
        for label, key, default in form:
            tk.Label(win,text=label,font=self.font_small,bg=self.CARD,fg=self.FG2).pack(anchor="w",padx=24,pady=(8,2))
            e = tk.Entry(win,font=self.font_body,bg=self.PANEL,fg=self.FG,insertbackground=self.FG,relief="flat")
            e.insert(0,default)
            e.pack(fill="x",padx=24,ipady=6)
            fields[key] = e
        def save():
            try:
                p = {"ref":fields["ref"].get().strip(),"nom":fields["nom"].get().strip(),
                     "categorie":fields["categorie"].get().strip(),
                     "quantite":int(fields["quantite"].get()),"prix":float(fields["prix"].get()),
                     "seuil_alerte":int(fields["seuil_alerte"].get())}
                if not p["nom"]:
                    messagebox.showerror("Erreur","Nom obligatoire.",parent=win); return
                if produit:
                    idx = self.data["produits"].index(produit)
                    self.data["produits"][idx] = p
                else:
                    self.data["produits"].append(p)
                save_data(self.data); win.destroy(); self._refresh_produits()
            except ValueError:
                messagebox.showerror("Erreur","Quantité, prix et seuil doivent être des nombres.",parent=win)
        bf = tk.Frame(win,bg=self.CARD)
        bf.pack(fill="x",padx=24,pady=16)
        self._btn(bf,"💾 Enregistrer",save,self.GREEN).pack(side="right",padx=(8,0))
        self._btn(bf,"Annuler",win.destroy,"#555").pack(side="right")

    def _modifier_produit(self):
        s = self._selected_produit()
        if s: self._dialog_ajouter_produit(s)

    def _supprimer_produit(self):
        s = self._selected_produit()
        if s and messagebox.askyesno("Confirmer",f"Supprimer « {s['nom']} » ?"):
            self.data["produits"].remove(s); save_data(self.data); self._refresh_produits()

    def _selected_produit(self):
        if not hasattr(self,"tree_prod"): return None
        sel = self.tree_prod.selection()
        if not sel: messagebox.showinfo("Info","Sélectionnez un produit."); return None
        ref = str(self.tree_prod.item(sel[0])["values"][0])
        nom = self.tree_prod.item(sel[0])["values"][1]
        return next((p for p in self.data["produits"] if p["nom"]==nom and str(p.get("ref",""))==ref), None)

    def _page_mouvement(self, mode):
        label = "📥 Entrée de stock" if mode=="entree" else "📤 Sortie de stock"
        self._header(label)
        card = tk.Frame(self.main,bg=self.CARD,padx=32,pady=28)
        card.pack(padx=60,pady=20,fill="x")
        tk.Label(card,text="Produit",font=self.font_body,bg=self.CARD,fg=self.FG2).grid(row=0,column=0,sticky="w",pady=8)
        noms = [p["nom"] for p in self.data["produits"]]
        prod_var = tk.StringVar()
        combo = ttk.Combobox(card,textvariable=prod_var,values=noms,state="readonly",font=self.font_body,width=30)
        combo.grid(row=0,column=1,sticky="w",padx=(16,0),pady=8)
        stock_lbl = tk.Label(card,text="",font=self.font_body,bg=self.CARD,fg=self.FG2)
        stock_lbl.grid(row=1,column=1,sticky="w",padx=(16,0))
        def on_sel(e=None):
            p = next((x for x in self.data["produits"] if x["nom"]==prod_var.get()),None)
            if p:
                c = self.GREEN if p["quantite"]>p.get("seuil_alerte",5) else self.ORANGE
                stock_lbl.configure(text=f"Stock actuel : {p['quantite']} unités",fg=c)
        combo.bind("<<ComboboxSelected>>",on_sel)
        tk.Label(card,text="Quantité",font=self.font_body,bg=self.CARD,fg=self.FG2).grid(row=2,column=0,sticky="w",pady=8)
        qte_var = tk.StringVar(value="1")
        tk.Entry(card,textvariable=qte_var,font=self.font_body,bg=self.PANEL,fg=self.FG,
                 insertbackground=self.FG,relief="flat",width=12).grid(row=2,column=1,sticky="w",padx=(16,0),ipady=6)
        tk.Label(card,text="Note",font=self.font_body,bg=self.CARD,fg=self.FG2).grid(row=3,column=0,sticky="w",pady=8)
        note_var = tk.StringVar()
        tk.Entry(card,textvariable=note_var,font=self.font_body,bg=self.PANEL,fg=self.FG,
                 insertbackground=self.FG,relief="flat",width=30).grid(row=3,column=1,sticky="w",padx=(16,0),ipady=6)
        def valider():
            nom = prod_var.get()
            if not nom: messagebox.showwarning("Attention","Choisissez un produit."); return
            try:
                qte = int(qte_var.get())
                if qte<=0: raise ValueError
            except ValueError:
                messagebox.showerror("Erreur","Quantité entier positif."); return
            p = next((x for x in self.data["produits"] if x["nom"]==nom),None)
            if mode=="sortie" and p["quantite"]<qte:
                messagebox.showerror("Erreur",f"Stock insuffisant ! Disponible : {p['quantite']}"); return
            p["quantite"] += qte if mode=="entree" else -qte
            self.data["mouvements"].append({"date":datetime.now().strftime("%Y-%m-%d %H:%M"),
                "produit":nom,"type":"entrée" if mode=="entree" else "sortie","quantite":qte,"note":note_var.get()})
            save_data(self.data)
            messagebox.showinfo("Succès",f"Mouvement enregistré !\nNouveau stock : {p['quantite']}")
            prod_var.set(""); qte_var.set("1"); note_var.set(""); stock_lbl.configure(text="")
        color_btn = self.GREEN if mode=="entree" else self.RED
        btn_text  = "✅ Valider l'entrée" if mode=="entree" else "✅ Valider la sortie"
        self._btn(card,btn_text,valider,color_btn).grid(row=4,column=1,sticky="w",padx=(16,0),pady=20)

    def _page_historique(self):
        self._header("📊 Historique des mouvements")
        tb = tk.Frame(self.main,bg=self.BG)
        tb.pack(fill="x",padx=28,pady=(4,10))
        def effacer():
            if messagebox.askyesno("Confirmer","Effacer tout l'historique ?"):
                self.data["mouvements"]=[]; save_data(self.data); self._page_historique()
        self._btn(tb,"🗑️ Effacer",effacer,self.RED).pack(side="right")
        filter_var = tk.StringVar(value="Tous")
        for val in ["Tous","Entrées","Sorties"]:
            tk.Radiobutton(tb,text=val,variable=filter_var,value=val,bg=self.BG,fg=self.FG,
                           selectcolor=self.CARD,activebackground=self.BG,font=self.font_body,
                           command=lambda:self._refresh_historique(filter_var.get())).pack(side="left",padx=6)
        frame = tk.Frame(self.main,bg=self.BG)
        frame.pack(fill="both",expand=True,padx=28,pady=(0,16))
        cols=("Date","Produit","Type","Quantité","Note")
        self.tree_hist=ttk.Treeview(frame,columns=cols,show="headings",height=18)
        self._style_tree(self.tree_hist,cols,[150,240,80,80,280])
        sb=ttk.Scrollbar(frame,orient="vertical",command=self.tree_hist.yview)
        self.tree_hist.configure(yscrollcommand=sb.set)
        self.tree_hist.pack(side="left",fill="both",expand=True)
        sb.pack(side="right",fill="y")
        self._refresh_historique("Tous")

    def _refresh_historique(self, filtre):
        if not hasattr(self,"tree_hist"): return
        self.tree_hist.delete(*self.tree_hist.get_children())
        for m in reversed(self.data["mouvements"]):
            if filtre=="Entrées" and m["type"]!="entrée": continue
            if filtre=="Sorties" and m["type"]!="sortie": continue
            tag = "entree" if m["type"]=="entrée" else "sortie"
            self.tree_hist.insert("","end",values=(m["date"],m["produit"],m["type"],m["quantite"],m.get("note","")),tags=(tag,))
        self.tree_hist.tag_configure("entree",foreground=self.GREEN)
        self.tree_hist.tag_configure("sortie",foreground=self.RED)

    # ════════════════════════════════════════════════════════════════════════
    # HELPERS
    # ════════════════════════════════════════════════════════════════════════

    def _header(self, title, subtitle=""):
        f = tk.Frame(self.main,bg=self.BG)
        f.pack(fill="x",padx=28,pady=(22,8))
        tk.Label(f,text=title,font=self.font_title,bg=self.BG,fg=self.FG).pack(anchor="w")
        if subtitle:
            tk.Label(f,text=subtitle,font=self.font_body,bg=self.BG,fg=self.FG2).pack(anchor="w")

    def _btn(self, parent, text, cmd, color):
        return tk.Button(parent,text=text,command=cmd,font=self.font_body,
                         bg=color,fg="white",relief="flat",cursor="hand2",
                         padx=14,pady=7,activebackground=color)

    def _dialog(self, title, w=400, h=400):
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry(f"{w}x{h}")
        win.configure(bg=self.CARD)
        win.grab_set()
        tk.Label(win,text=title,font=self.font_header,bg=self.CARD,fg=self.FG).pack(pady=(20,4))
        ttk.Separator(win,orient="horizontal").pack(fill="x",padx=24,pady=8)
        return win

    def _style_tree(self, tree, cols, widths):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",background=self.PANEL,fieldbackground=self.PANEL,
                        foreground=self.FG,rowheight=32,font=("Segoe UI",10),borderwidth=0)
        style.configure("Treeview.Heading",background=self.CARD,foreground=self.ACCENT,
                        font=("Segoe UI",10,"bold"),relief="flat")
        style.map("Treeview",background=[("selected",self.BORDER)])
        for col,w in zip(cols,widths):
            tree.heading(col,text=col)
            tree.column(col,width=w,minwidth=50)


if __name__ == "__main__":
    app = GestionStock()
    app.mainloop()