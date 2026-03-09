"""
GestionStock Pro v3 — Login + UI améliorée + HiDPI
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json, os, hashlib, ctypes, sys
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════════════
# FIX PIXELISATION (Windows DPI + macOS Retina)
# ══════════════════════════════════════════════════════════════════════════════
def fix_dpi():
    if sys.platform == "win32":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

fix_dpi()

# ══════════════════════════════════════════════════════════════════════════════
# ReportLab
# ══════════════════════════════════════════════════════════════════════════════
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors as rl_colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                     Paragraph, Spacer, HRFlowable)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_RIGHT, TA_LEFT
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False

# ══════════════════════════════════════════════════════════════════════════════
# DATA
# ══════════════════════════════════════════════════════════════════════════════
DATA_FILE  = os.path.join(os.path.expanduser("~"), "stock_data_v3.json")
USERS_FILE = os.path.join(os.path.expanduser("~"), "stock_users.json")

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
            for k in ("produits","mouvements","clients","commandes"):
                d.setdefault(k, [])
            return d
    return {"produits":[],"mouvements":[],"clients":[],"commandes":[]}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # Default admin
    default = [{"username":"admin","password":hash_pw("admin123"),"role":"admin","nom":"Administrateur"}]
    save_users(default)
    return default

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

CONFIG_FILE = os.path.join(os.path.expanduser("~"), "stock_config.json")

DEFAULT_CONFIG = {
    "entreprise_nom":     "Votre Entreprise SARL",
    "entreprise_adresse": "123 Rue du Commerce",
    "entreprise_ville":   "20000 Casablanca, Maroc",
    "entreprise_tel":     "+212 5XX-XXXXXX",
    "entreprise_email":   "contact@entreprise.ma",
    "entreprise_if":      "12345678",
    "entreprise_rc":      "",
    "entreprise_ice":     "",
    "facture_conditions": "30 jours net",
    "facture_monnaie":    "MAD",
    "facture_tva_defaut": "20",
    "facture_pied":       "Merci pour votre confiance. Document conforme à la législation marocaine.",
    "facture_couleur":    "#1a2744",
    "facture_couleur_accent": "#2563eb",
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            c = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                c.setdefault(k, v)
            return c
    save_config(DEFAULT_CONFIG.copy())
    return DEFAULT_CONFIG.copy()

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def next_id(lst, key="id", prefix=""):
    if not lst: return f"{prefix}001"
    nums = []
    for x in lst:
        try: nums.append(int(str(x.get(key,"0")).replace(prefix,"")))
        except: nums.append(0)
    return f"{prefix}{max(nums)+1:03d}"

# ══════════════════════════════════════════════════════════════════════════════
# PDF
# ══════════════════════════════════════════════════════════════════════════════
def generer_facture_pdf(commande, client, produits_map, filepath, config=None):
    if config is None:
        config = load_config()
    monnaie = config.get("facture_monnaie", "MAD")
    doc = SimpleDocTemplate(filepath, pagesize=A4,
        rightMargin=1.5*cm, leftMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm)
    BD=rl_colors.HexColor(config.get("facture_couleur","#1a2744"))
    BM=rl_colors.HexColor(config.get("facture_couleur_accent","#2563eb"))
    BL=rl_colors.HexColor("#dbeafe"); GL=rl_colors.HexColor("#f8fafc")
    GM=rl_colors.HexColor("#e2e8f0"); GT=rl_colors.HexColor("#64748b")
    BK=rl_colors.HexColor("#0f172a")
    def S(n,**k): return ParagraphStyle(n,**k)
    sn=S("n",fontSize=9,textColor=BK,fontName="Helvetica",leading=13)
    ss=S("s",fontSize=8,textColor=GT,fontName="Helvetica",leading=11)
    sb=S("b",fontSize=9,textColor=BK,fontName="Helvetica-Bold",leading=13)
    sr=S("r",fontSize=9,textColor=BK,fontName="Helvetica",alignment=TA_RIGHT)
    styles=getSampleStyleSheet(); story=[]
    W=A4[0]-3*cm
    ent_nom = config.get("entreprise_nom","")
    ent_hex = config.get("facture_couleur","#1a2744")
    acc_hex = config.get("facture_couleur_accent","#2563eb")
    hd=[[Paragraph(f"<b><font color='{ent_hex}' size='18'>{ent_nom}</font></b><br/><font color='#64748b' size='9'>Logiciel de gestion commerciale</font>",styles["Normal"]),
          Paragraph(f"<b><font color='{acc_hex}' size='26'>FACTURE</font></b><br/><font color='#64748b' size='9'>N° {commande['numero']}</font>",styles["Normal"])]]
    ht=Table(hd,colWidths=[W*.55,W*.45])
    ht.setStyle(TableStyle([("ALIGN",(1,0),(1,0),"RIGHT"),("VALIGN",(0,0),(-1,-1),"TOP"),("BOTTOMPADDING",(0,0),(-1,-1),14)]))
    story.append(ht); story.append(HRFlowable(width="100%",thickness=2,color=BM,spaceAfter=14))
    # Build emetteur block from config
    em_lines = [f"<b>De :</b>", f"<b>{config.get('entreprise_nom','')}</b>"]
    if config.get("entreprise_adresse"): em_lines.append(config["entreprise_adresse"])
    if config.get("entreprise_ville"):   em_lines.append(config["entreprise_ville"])
    if config.get("entreprise_tel"):     em_lines.append(f"Tél : {config['entreprise_tel']}")
    if config.get("entreprise_email"):   em_lines.append(f"Email : {config['entreprise_email']}")
    if config.get("entreprise_if"):      em_lines.append(f"IF : {config['entreprise_if']}")
    if config.get("entreprise_rc"):      em_lines.append(f"RC : {config['entreprise_rc']}")
    if config.get("entreprise_ice"):     em_lines.append(f"ICE : {config['entreprise_ice']}")
    em = "<br/>".join(em_lines)
    cl=(f"<b>Facturé à :</b><br/><b>{client.get('nom','')}</b><br/>{client.get('adresse','')}<br/>{client.get('ville','')}<br/>Tél : {client.get('telephone','')}<br/>Email : {client.get('email','')}<br/>ICE : {client.get('ice','')}")
    cond = commande.get('conditions', config.get('facture_conditions','30 jours'))
    dt=(f"<b>Date :</b> {commande.get('date','')}<br/><b>Échéance :</b> {commande.get('echeance','')}<br/><b>Statut :</b> {commande.get('statut','')}<br/><b>Conditions :</b> {cond}")
    it=Table([[Paragraph(em,sn),Paragraph(cl,sn),Paragraph(dt,sn)]],colWidths=[W*.33,W*.34,W*.33])
    it.setStyle(TableStyle([("BACKGROUND",(0,0),(0,0),GL),("BACKGROUND",(1,0),(1,0),BL),("BACKGROUND",(2,0),(2,0),GL),
        ("BOX",(0,0),(-1,-1),.5,GM),("INNERGRID",(0,0),(-1,-1),.5,GM),
        ("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),10),
        ("LEFTPADDING",(0,0),(-1,-1),10),("RIGHTPADDING",(0,0),(-1,-1),10),("VALIGN",(0,0),(-1,-1),"TOP")]))
    story.append(it); story.append(Spacer(1,18))
    ch=["Réf.","Désignation","Qté","P.U. HT","TVA","Total HT"]
    cw=[W*.10,W*.35,W*.08,W*.17,W*.10,W*.20]; td=[ch]
    sht=0; ttva=0
    for l in commande.get("lignes",[]):
        p=produits_map.get(l["produit_nom"],{}); ref=p.get("ref","-")
        qte=l["quantite"]; pu=l["prix_unit"]; tva=l.get("tva",20)
        ht=qte*pu; tva_m=ht*tva/100; sht+=ht; ttva+=tva_m
        td.append([Paragraph(str(ref),ss),Paragraph(str(l["produit_nom"]),sn),
                   Paragraph(str(qte),sr),Paragraph(f"{pu:,.2f}",sr),
                   Paragraph(f"{tva}%",sr),Paragraph(f"{ht:,.2f}",sr)])
    lt=Table(td,colWidths=cw,repeatRows=1)
    lt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),BD),("TEXTCOLOR",(0,0),(-1,0),rl_colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,0),9),("ALIGN",(0,0),(-1,0),"CENTER"),
        ("TOPPADDING",(0,0),(-1,0),10),("BOTTOMPADDING",(0,0),(-1,0),10),
        ("FONTNAME",(0,1),(-1,-1),"Helvetica"),("FONTSIZE",(0,1),(-1,-1),9),
        ("ALIGN",(2,1),(-1,-1),"RIGHT"),("TOPPADDING",(0,1),(-1,-1),8),("BOTTOMPADDING",(0,1),(-1,-1),8),
        ("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[rl_colors.white,GL]),
        ("BOX",(0,0),(-1,-1),.5,GM),("INNERGRID",(0,0),(-1,-1),.3,GM)]))
    story.append(lt); story.append(Spacer(1,16))
    rem=commande.get("remise",0); rem_m=sht*rem/100; net=sht-rem_m
    tv2=net*(ttva/sht if sht else .20); ttc=net+tv2
    def tr(lbl,val,bold=False):
        return [Paragraph(f"<b>{lbl}</b>" if bold else lbl,sr),Paragraph(f"<b>{val}</b>" if bold else val,sr)]
    tot=[tr(f"Sous-total HT :",f"{sht:,.2f} {monnaie}")]
    if rem: tot.append(tr(f"Remise ({rem}%) :",f"- {rem_m:,.2f} {monnaie}"))
    tot+=[tr(f"Net HT :",f"{net:,.2f} {monnaie}"),tr(f"TVA :",f"{tv2:,.2f} {monnaie}"),tr(f"TOTAL TTC :",f"{ttc:,.2f} {monnaie}",True)]
    tt=Table(tot,colWidths=[W*.7,W*.3])
    tt.setStyle(TableStyle([("ALIGN",(0,0),(-1,-1),"RIGHT"),("TOPPADDING",(0,0),(-1,-1),6),
        ("BOTTOMPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),8),
        ("LINEABOVE",(0,-1),(-1,-1),1.5,BM),("BACKGROUND",(0,-1),(-1,-1),BL),
        ("FONTNAME",(0,-1),(-1,-1),"Helvetica-Bold"),("FONTSIZE",(0,-1),(-1,-1),11),("TEXTCOLOR",(0,-1),(-1,-1),BD)]))
    story.append(tt); story.append(Spacer(1,20))
    if commande.get("note"):
        story.append(Paragraph("<b>Note :</b>",sb)); story.append(Paragraph(commande["note"],sn)); story.append(Spacer(1,10))
    story.append(HRFlowable(width="100%",thickness=1,color=GM,spaceAfter=8))
    pied = config.get("facture_pied","Merci pour votre confiance.")
    story.append(Paragraph(pied, ss))
    doc.build(story)
    return filepath

# ══════════════════════════════════════════════════════════════════════════════
# THEME & STYLES
# ══════════════════════════════════════════════════════════════════════════════
C = {
    "bg":       "#0d1117",
    "sidebar":  "#161b22",
    "card":     "#21262d",
    "card2":    "#2d333b",
    "border":   "#30363d",
    "accent":   "#58a6ff",
    "accent2":  "#1f6feb",
    "green":    "#3fb950",
    "red":      "#f85149",
    "orange":   "#d29922",
    "purple":   "#bc8cff",
    "fg":       "#e6edf3",
    "fg2":      "#7d8590",
    "fg3":      "#484f58",
    "white":    "#ffffff",
    "input_bg": "#0d1117",
    "hover":    "#30363d",
    "success_bg":"#1a3a2a",
    "warn_bg":  "#3a2f0f",
}

FONTS = {
    "title":   ("Segoe UI Semibold", 22),
    "heading": ("Segoe UI Semibold", 13),
    "body":    ("Segoe UI", 10),
    "small":   ("Segoe UI", 9),
    "mono":    ("Consolas", 10),
    "num":     ("Segoe UI Semibold", 18),
    "logo":    ("Segoe UI Semibold", 14),
    "nav":     ("Segoe UI", 10),
    "btn":     ("Segoe UI Semibold", 10),
}

def apply_treeview_style():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Custom.Treeview",
        background=C["card"], fieldbackground=C["card"],
        foreground=C["fg"], rowheight=38,
        font=FONTS["body"], borderwidth=0,
        relief="flat")
    style.configure("Custom.Treeview.Heading",
        background=C["card2"], foreground=C["accent"],
        font=("Segoe UI Semibold", 10), relief="flat",
        borderwidth=0, padding=(8, 10))
    style.map("Custom.Treeview",
        background=[("selected", C["accent2"])],
        foreground=[("selected", C["white"])])
    style.configure("TSeparator", background=C["border"])

# ══════════════════════════════════════════════════════════════════════════════
# WIDGETS HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def make_btn(parent, text, cmd, color=None, width=None, small=False):
    bg = color or C["accent2"]
    f = FONTS["small"] if small else FONTS["btn"]
    px, py = (10,4) if small else (16,8)
    b = tk.Button(parent, text=text, command=cmd, font=f,
                  bg=bg, fg=C["white"], relief="flat", cursor="hand2",
                  padx=px, pady=py, activebackground=bg, activeforeground=C["white"],
                  bd=0)
    if width: b.configure(width=width)
    def on_enter(e): b.configure(bg=_lighten(bg))
    def on_leave(e): b.configure(bg=bg)
    b.bind("<Enter>", on_enter)
    b.bind("<Leave>", on_leave)
    return b

def _lighten(hex_color):
    h = hex_color.lstrip("#")
    rgb = tuple(min(255, int(h[i:i+2],16)+30) for i in (0,2,4))
    return "#{:02x}{:02x}{:02x}".format(*rgb)

def make_entry(parent, textvariable=None, show=None, width=None, font=None):
    e = tk.Entry(parent,
        textvariable=textvariable,
        show=show,
        font=font or FONTS["body"],
        bg=C["input_bg"], fg=C["fg"],
        insertbackground=C["accent"],
        relief="flat", bd=0,
        highlightthickness=1,
        highlightbackground=C["border"],
        highlightcolor=C["accent"])
    if width: e.configure(width=width)
    return e

def make_label(parent, text, font=None, fg=None, bg=None, **kw):
    return tk.Label(parent, text=text,
        font=font or FONTS["body"],
        fg=fg or C["fg"],
        bg=bg or C["bg"],
        **kw)

def card_frame(parent, padx=20, pady=16, bg=None):
    f = tk.Frame(parent, bg=bg or C["card"],
                 highlightthickness=1,
                 highlightbackground=C["border"])
    return f

def separator(parent):
    return tk.Frame(parent, bg=C["border"], height=1)

def make_combobox(parent, textvariable, values, width=20, state="readonly"):
    style = ttk.Style()
    style.configure("Custom.TCombobox",
        fieldbackground=C["input_bg"], background=C["card2"],
        foreground=C["fg"], selectbackground=C["accent2"],
        selectforeground=C["white"], arrowcolor=C["fg2"],
        relief="flat", borderwidth=1)
    style.map("Custom.TCombobox",
        fieldbackground=[("readonly",C["input_bg"])],
        foreground=[("readonly",C["fg"])],
        selectbackground=[("readonly",C["accent2"])])
    cb = ttk.Combobox(parent, textvariable=textvariable, values=values,
                      state=state, font=FONTS["body"], width=width,
                      style="Custom.TCombobox")
    return cb

def scrolled_tree(parent, cols, widths, height=15):
    apply_treeview_style()
    frame = tk.Frame(parent, bg=C["card"])
    tree = ttk.Treeview(frame, columns=cols, show="headings",
                        height=height, style="Custom.Treeview",
                        selectmode="browse")
    sb_v = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb_v.set)
    for col, w in zip(cols, widths):
        tree.heading(col, text=col, anchor="w")
        tree.column(col, width=w, minwidth=50, anchor="w")
    tree.pack(side="left", fill="both", expand=True)
    sb_v.pack(side="right", fill="y")
    return frame, tree

# ══════════════════════════════════════════════════════════════════════════════
# LOGIN WINDOW
# ══════════════════════════════════════════════════════════════════════════════
class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GestionStock Pro — Connexion")
        self.resizable(False, False)
        self.configure(bg=C["bg"])
        self.logged_user = None

        # Center window
        w, h = 420, 560
        self.geometry(f"{w}x{h}")
        self._center(w, h)

        self.users = load_users()
        self._build()

        # Set icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

    def _center(self, w, h):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self):
        # Top accent bar
        tk.Frame(self, bg=C["accent"], height=4).pack(fill="x")

        # Logo area
        logo_frame = tk.Frame(self, bg=C["bg"])
        logo_frame.pack(pady=(40, 10))
        tk.Label(logo_frame, text="📦", font=("Segoe UI", 48),
                 bg=C["bg"], fg=C["accent"]).pack()
        tk.Label(logo_frame, text="GestionStock Pro",
                 font=("Segoe UI Semibold", 20), bg=C["bg"], fg=C["fg"]).pack()
        tk.Label(logo_frame, text="Connectez-vous à votre espace",
                 font=FONTS["small"], bg=C["bg"], fg=C["fg2"]).pack(pady=(4,0))

        # Card
        card = card_frame(self, padx=32, pady=28)
        card.pack(padx=40, pady=30, fill="x")

        # Username
        tk.Label(card, text="Nom d'utilisateur", font=FONTS["small"],
                 bg=C["card"], fg=C["fg2"]).pack(anchor="w", pady=(0,4))
        self.user_var = tk.StringVar(value="admin")
        user_entry = make_entry(card, textvariable=self.user_var, width=32)
        user_entry.pack(fill="x", ipady=8)

        tk.Frame(card, bg=C["bg"], height=14).pack()

        # Password
        tk.Label(card, text="Mot de passe", font=FONTS["small"],
                 bg=C["card"], fg=C["fg2"]).pack(anchor="w", pady=(0,4))
        self.pw_var = tk.StringVar()
        pw_entry = make_entry(card, textvariable=self.pw_var, show="●", width=32)
        pw_entry.pack(fill="x", ipady=8)
        pw_entry.bind("<Return>", lambda e: self._login())

        # Show/hide password
        show_var = tk.BooleanVar(value=False)
        def toggle_pw():
            pw_entry.configure(show="" if show_var.get() else "●")
        tk.Checkbutton(card, text="Afficher le mot de passe",
                       variable=show_var, command=toggle_pw,
                       font=FONTS["small"], bg=C["card"], fg=C["fg2"],
                       selectcolor=C["card2"], activebackground=C["card"],
                       activeforeground=C["fg2"]).pack(anchor="w", pady=(8,0))

        # Error label
        self.err_lbl = tk.Label(card, text="", font=FONTS["small"],
                                bg=C["card"], fg=C["red"])
        self.err_lbl.pack(pady=(8,0))

        # Login button
        tk.Frame(card, bg=C["card"], height=6).pack()
        make_btn(card, "  Se connecter  →", self._login, C["accent2"]).pack(fill="x", ipady=4)

        # Hint
        tk.Label(self, text="Compte par défaut : admin / admin123",
                 font=FONTS["small"], bg=C["bg"], fg=C["fg3"]).pack(pady=(0,10))

    def _login(self):
        username = self.user_var.get().strip()
        password = self.pw_var.get()
        if not username or not password:
            self.err_lbl.configure(text="⚠  Remplissez tous les champs.")
            return
        h = hash_pw(password)
        user = next((u for u in self.users if u["username"]==username and u["password"]==h), None)
        if user:
            self.logged_user = user
            self.destroy()
        else:
            self.err_lbl.configure(text="✕  Identifiants incorrects.")
            self.pw_var.set("")

# ══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════════════════
class GestionStock(tk.Tk):
    def __init__(self, user):
        super().__init__()
        self.current_user = user
        self.data = load_data()
        self.users = load_users()

        self.title("📦 GestionStock Pro")
        self.state("zoomed") if sys.platform=="win32" else self.geometry("1280x800")
        self.configure(bg=C["bg"])
        self.minsize(1100, 680)

        # Load config
        self.config_data = load_config()

        # Set window icon (looks for app_icon.ico next to the script)
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        apply_treeview_style()
        self._build_layout()

    def _build_layout(self):
        # ── Sidebar ──────────────────────────────────────────────────────────
        self.sidebar = tk.Frame(self, bg=C["sidebar"], width=240)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        logo = tk.Frame(self.sidebar, bg=C["sidebar"])
        logo.pack(fill="x", padx=20, pady=(28,6))
        tk.Label(logo, text="📦", font=("Segoe UI",30), bg=C["sidebar"], fg=C["accent"]).pack(anchor="w")
        tk.Label(logo, text="GestionStock Pro", font=FONTS["logo"],
                 bg=C["sidebar"], fg=C["fg"]).pack(anchor="w")

        separator(self.sidebar).pack(fill="x", padx=16, pady=(10,6))

        # Nav
        self.nav_btns = {}
        sections = [
            ("STOCK", [
                ("🏠", "Tableau de bord", "dashboard"),
                ("📦", "Produits",        "produits"),
                ("📥", "Entrée stock",    "entree"),
                ("📤", "Sortie stock",    "sortie"),
                ("📊", "Historique",      "historique"),
            ]),
            ("COMMERCIAL", [
                ("👥", "Clients",   "clients"),
                ("🛒", "Commandes", "commandes"),
                ("🧾", "Factures",  "factures"),
            ]),
        ]
        if self.current_user.get("role") == "admin":
            sections.append(("ADMINISTRATION", [
                ("👤", "Utilisateurs", "users"),
                ("⚙️", "Paramètres",   "settings"),
            ]))

        for section_title, items in sections:
            tk.Label(self.sidebar, text=section_title, font=("Segoe UI Semibold", 8),
                     bg=C["sidebar"], fg=C["fg3"]).pack(anchor="w", padx=22, pady=(14,2))
            for icon, label, key in items:
                f = tk.Frame(self.sidebar, bg=C["sidebar"], cursor="hand2")
                f.pack(fill="x", padx=10, pady=1)
                icon_lbl = tk.Label(f, text=icon, font=("Segoe UI",13),
                                    bg=C["sidebar"], fg=C["fg2"], width=3)
                icon_lbl.pack(side="left", padx=(6,4), pady=6)
                text_lbl = tk.Label(f, text=label, font=FONTS["nav"],
                                    bg=C["sidebar"], fg=C["fg2"], anchor="w")
                text_lbl.pack(side="left", fill="x", expand=True, pady=6)
                indicator = tk.Frame(f, bg=C["sidebar"], width=3)
                indicator.pack(side="right", fill="y")

                self.nav_btns[key] = (f, icon_lbl, text_lbl, indicator)

                def make_click(k):
                    def click(e=None): self._show_page(k)
                    return click
                click_fn = make_click(key)
                for w in (f, icon_lbl, text_lbl):
                    w.bind("<Button-1>", click_fn)
                    w.bind("<Enter>", lambda e,fr=f: fr.configure(bg=C["hover"]) or
                           [c.configure(bg=C["hover"]) for c in fr.winfo_children()])
                    w.bind("<Leave>", lambda e,fr=f,k2=key: self._nav_reset(fr,k2))

        # Bottom: user info
        separator(self.sidebar).pack(fill="x", padx=16, pady=(10,0), side="bottom")
        user_bar = tk.Frame(self.sidebar, bg=C["sidebar"])
        user_bar.pack(fill="x", padx=14, pady=10, side="bottom")
        tk.Label(user_bar, text="👤", font=("Segoe UI",16),
                 bg=C["sidebar"], fg=C["accent"]).pack(side="left", padx=(0,8))
        uf = tk.Frame(user_bar, bg=C["sidebar"])
        uf.pack(side="left", fill="x", expand=True)
        tk.Label(uf, text=self.current_user.get("nom",""),
                 font=("Segoe UI Semibold",9), bg=C["sidebar"], fg=C["fg"]).pack(anchor="w")
        tk.Label(uf, text=self.current_user.get("role",""),
                 font=FONTS["small"], bg=C["sidebar"], fg=C["fg2"]).pack(anchor="w")
        make_btn(user_bar, "↩", self._logout, C["card2"], small=True).pack(side="right")

        # ── Main area ─────────────────────────────────────────────────────────
        self.main = tk.Frame(self, bg=C["bg"])
        self.main.pack(side="left", fill="both", expand=True)

        self._show_page("dashboard")

    def _nav_reset(self, frame, key):
        active = getattr(self, "_active_page", None)
        if key != active:
            frame.configure(bg=C["sidebar"])
            for c in frame.winfo_children():
                c.configure(bg=C["sidebar"])

    def _show_page(self, key):
        self._active_page = key
        # Update nav highlight
        for k, (f, il, tl, ind) in self.nav_btns.items():
            if k == key:
                f.configure(bg=C["card2"])
                for w in (f, il, tl): w.configure(bg=C["card2"])
                il.configure(fg=C["accent"])
                tl.configure(fg=C["accent"], font=("Segoe UI Semibold",10))
                ind.configure(bg=C["accent"])
            else:
                f.configure(bg=C["sidebar"])
                for w in (f, il, tl): w.configure(bg=C["sidebar"])
                il.configure(fg=C["fg2"])
                tl.configure(fg=C["fg2"], font=FONTS["nav"])
                ind.configure(bg=C["sidebar"])

        for w in self.main.winfo_children():
            w.destroy()

        pages = {
            "dashboard": self._page_dashboard,
            "produits":  self._page_produits,
            "entree":    lambda: self._page_mouvement("entree"),
            "sortie":    lambda: self._page_mouvement("sortie"),
            "historique":self._page_historique,
            "clients":   self._page_clients,
            "commandes": self._page_commandes,
            "factures":  self._page_factures,
            "users":     self._page_users,
            "settings":  self._page_settings,
        }
        if key in pages:
            pages[key]()

    def _logout(self):
        if messagebox.askyesno("Déconnexion", "Se déconnecter ?"):
            self.destroy()
            main()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE HEADER
    # ══════════════════════════════════════════════════════════════════════════
    def _header(self, title, subtitle="", actions=None):
        bar = tk.Frame(self.main, bg=C["bg"])
        bar.pack(fill="x", padx=28, pady=(24,12))
        left = tk.Frame(bar, bg=C["bg"])
        left.pack(side="left", fill="x", expand=True)
        tk.Label(left, text=title, font=FONTS["title"],
                 bg=C["bg"], fg=C["fg"]).pack(anchor="w")
        if subtitle:
            tk.Label(left, text=subtitle, font=FONTS["small"],
                     bg=C["bg"], fg=C["fg2"]).pack(anchor="w", pady=(2,0))
        if actions:
            right = tk.Frame(bar, bg=C["bg"])
            right.pack(side="right")
            for text, cmd, color in actions:
                make_btn(right, text, cmd, color).pack(side="left", padx=4)
        separator(self.main).pack(fill="x", padx=28, pady=(0,16))

    # ══════════════════════════════════════════════════════════════════════════
    # DASHBOARD
    # ══════════════════════════════════════════════════════════════════════════
    def _page_dashboard(self):
        self._header("Tableau de bord",
                     f"Bienvenue, {self.current_user.get('nom','')}  •  {datetime.now().strftime('%A %d %B %Y')}")

        produits  = self.data["produits"]
        commandes = self.data["commandes"]
        clients   = self.data["clients"]

        total_valeur  = sum(p.get("prix",0)*p.get("quantite",0) for p in produits)
        alertes       = [p for p in produits if p.get("quantite",0) <= p.get("seuil_alerte",5)]
        ca_total      = sum(c.get("total_ttc",0) for c in commandes)
        nb_attente    = sum(1 for c in commandes if c.get("statut","")=="En attente")

        # KPI cards
        kpi_row = tk.Frame(self.main, bg=C["bg"])
        kpi_row.pack(fill="x", padx=28, pady=(0,20))
        kpis = [
            ("📦 Produits",       str(len(produits)),       C["accent"],  "en stock"),
            ("👥 Clients",        str(len(clients)),        C["purple"],  "enregistrés"),
            ("🧾 Commandes",      str(len(commandes)),      C["orange"],  f"{nb_attente} en attente"),
            ("💰 Chiffre d'aff.", f"{ca_total:,.0f}",       C["green"],   "MAD total"),
            ("⚠️ Alertes",        str(len(alertes)),        C["red"],     "produits faibles"),
        ]
        for i,(title,val,color,sub) in enumerate(kpis):
            kpi_row.columnconfigure(i, weight=1)
            c = card_frame(kpi_row)
            c.grid(row=0, column=i, sticky="nsew", padx=6, pady=2)
            inner = tk.Frame(c, bg=C["card"], padx=18, pady=16)
            inner.pack(fill="both", expand=True)
            # color bar left
            tk.Frame(inner, bg=color, width=4).pack(side="left", fill="y", padx=(0,12))
            content = tk.Frame(inner, bg=C["card"])
            content.pack(side="left", fill="both", expand=True)
            tk.Label(content, text=title, font=FONTS["small"], bg=C["card"], fg=C["fg2"]).pack(anchor="w")
            tk.Label(content, text=val, font=FONTS["num"], bg=C["card"], fg=color).pack(anchor="w", pady=(4,2))
            tk.Label(content, text=sub, font=FONTS["small"], bg=C["card"], fg=C["fg3"]).pack(anchor="w")

        # Two columns
        cols = tk.Frame(self.main, bg=C["bg"])
        cols.pack(fill="both", expand=True, padx=28, pady=(0,20))
        cols.columnconfigure(0, weight=3)
        cols.columnconfigure(1, weight=2)

        # Left: recent orders
        left = card_frame(cols)
        left.grid(row=0, column=0, sticky="nsew", padx=(0,10))
        left_inner = tk.Frame(left, bg=C["card"], padx=18, pady=16)
        left_inner.pack(fill="both", expand=True)
        tk.Label(left_inner, text="Dernières commandes", font=FONTS["heading"],
                 bg=C["card"], fg=C["fg"]).pack(anchor="w", pady=(0,12))

        cols_tree = ("N°","Client","Date","Total TTC","Statut")
        f_tree, tree = scrolled_tree(left_inner, cols_tree, [90,200,110,120,100], height=9)
        f_tree.pack(fill="both", expand=True)
        for cmd in reversed(self.data["commandes"][-12:]):
            tag = {"Payée":"ok","En attente":"warn","Annulée":"err"}.get(cmd.get("statut",""),"")
            tree.insert("","end",values=(
                cmd.get("numero",""), cmd.get("client_nom",""), cmd.get("date",""),
                f"{cmd.get('total_ttc',0):,.2f} MAD", cmd.get("statut","")
            ), tags=(tag,))
        tree.tag_configure("ok",   foreground=C["green"])
        tree.tag_configure("warn", foreground=C["orange"])
        tree.tag_configure("err",  foreground=C["red"])

        # Right: alerts
        right = card_frame(cols)
        right.grid(row=0, column=1, sticky="nsew")
        right_inner = tk.Frame(right, bg=C["card"], padx=18, pady=16)
        right_inner.pack(fill="both", expand=True)
        tk.Label(right_inner, text="Alertes de stock", font=FONTS["heading"],
                 bg=C["card"], fg=C["orange"]).pack(anchor="w", pady=(0,10))

        scroll_canvas = tk.Canvas(right_inner, bg=C["card"], highlightthickness=0)
        scroll_canvas.pack(fill="both", expand=True)
        alerts_frame = tk.Frame(scroll_canvas, bg=C["card"])
        scroll_canvas.create_window((0,0), window=alerts_frame, anchor="nw")

        if not alertes:
            tk.Label(alerts_frame, text="✅  Aucune alerte de stock",
                     font=FONTS["body"], bg=C["card"], fg=C["green"]).pack(pady=20)
        else:
            for p in alertes[:12]:
                row = tk.Frame(alerts_frame, bg=C["card2"],
                               highlightthickness=1, highlightbackground=C["border"])
                row.pack(fill="x", pady=3)
                color = C["red"] if p["quantite"]==0 else C["orange"]
                tk.Frame(row, bg=color, width=4).pack(side="left", fill="y")
                info = tk.Frame(row, bg=C["card2"], padx=10, pady=7)
                info.pack(side="left", fill="x", expand=True)
                tk.Label(info, text=p["nom"], font=("Segoe UI Semibold",9),
                         bg=C["card2"], fg=C["fg"]).pack(anchor="w")
                status = "RUPTURE" if p["quantite"]==0 else f"Stock : {p['quantite']}"
                tk.Label(info, text=status, font=FONTS["small"],
                         bg=C["card2"], fg=color).pack(anchor="w")

    # ══════════════════════════════════════════════════════════════════════════
    # PRODUITS
    # ══════════════════════════════════════════════════════════════════════════
    def _page_produits(self):
        self._header("Produits", "Gérer le catalogue de produits", [
            ("➕  Nouveau produit", self._dialog_produit, C["green"]),
            ("✏️  Modifier",        self._modifier_produit, C["accent2"]),
            ("🗑️  Supprimer",       self._supprimer_produit, C["red"]),
        ])

        # Search bar
        search_bar = tk.Frame(self.main, bg=C["bg"])
        search_bar.pack(fill="x", padx=28, pady=(0,12))
        search_var = tk.StringVar()
        search_var.trace("w", lambda *a: self._refresh_produits(search_var.get()))
        tk.Label(search_bar, text="🔍", font=("Segoe UI",12),
                 bg=C["bg"], fg=C["fg2"]).pack(side="left", padx=(0,6))
        se = make_entry(search_bar, textvariable=search_var, width=30)
        se.pack(side="left", ipady=6, ipadx=4)
        tk.Label(search_bar, text="Rechercher par nom ou référence...",
                 font=FONTS["small"], bg=C["bg"], fg=C["fg3"]).pack(side="left", padx=8)

        # Stats row
        stats_row = tk.Frame(self.main, bg=C["bg"])
        stats_row.pack(fill="x", padx=28, pady=(0,10))
        total_val = sum(p.get("prix",0)*p.get("quantite",0) for p in self.data["produits"])
        for txt,val,col in [
            ("Total produits", str(len(self.data["produits"])), C["accent"]),
            ("Valeur totale", f"{total_val:,.2f} MAD", C["green"]),
            ("En rupture", str(sum(1 for p in self.data["produits"] if p.get("quantite",0)==0)), C["red"]),
        ]:
            f = tk.Frame(stats_row, bg=C["card2"], padx=14, pady=8,
                         highlightthickness=1, highlightbackground=C["border"])
            f.pack(side="left", padx=(0,8))
            tk.Label(f, text=txt, font=FONTS["small"], bg=C["card2"], fg=C["fg2"]).pack(side="left", padx=(0,8))
            tk.Label(f, text=val, font=("Segoe UI Semibold",10), bg=C["card2"], fg=col).pack(side="left")

        # Table
        frame = tk.Frame(self.main, bg=C["bg"])
        frame.pack(fill="both", expand=True, padx=28, pady=(0,20))
        cols = ("Réf.","Nom du produit","Catégorie","Qté","Prix HT","Valeur stock","Seuil","Statut")
        f_tree, self.tree_prod = scrolled_tree(frame, cols, [80,220,130,70,90,110,70,100])
        f_tree.pack(fill="both", expand=True)
        self.tree_prod.bind("<Double-1>", lambda e: self._modifier_produit())
        self._search_q = ""
        self._refresh_produits()

    def _refresh_produits(self, query=""):
        if not hasattr(self,"tree_prod"): return
        self._search_q = query.lower()
        self.tree_prod.delete(*self.tree_prod.get_children())
        for p in self.data["produits"]:
            if self._search_q and self._search_q not in p.get("nom","").lower() and self._search_q not in str(p.get("ref","")).lower():
                continue
            val = p.get("prix",0)*p.get("quantite",0)
            qte, seuil = p.get("quantite",0), p.get("seuil_alerte",5)
            if qte==0:   st,tag = "🔴 Rupture","rup"
            elif qte<=seuil: st,tag = "🟡 Faible","low"
            else:        st,tag = "🟢 Normal","ok"
            self.tree_prod.insert("","end",values=(
                p.get("ref",""), p.get("nom",""), p.get("categorie",""),
                qte, f"{p.get('prix',0):.2f}", f"{val:,.2f}", seuil, st
            ), tags=(tag,))
        self.tree_prod.tag_configure("rup", foreground=C["red"])
        self.tree_prod.tag_configure("low", foreground=C["orange"])
        self.tree_prod.tag_configure("ok",  foreground=C["green"])

    def _dialog_produit(self, produit=None):
        win, fields = self._form_dialog(
            "Nouveau produit" if not produit else "Modifier le produit",
            [
                ("Référence",      "ref",          str(produit.get("ref",""))           if produit else ""),
                ("Nom du produit *","nom",          produit.get("nom","")               if produit else ""),
                ("Catégorie",      "categorie",    produit.get("categorie","")          if produit else ""),
                ("Quantité",       "quantite",     str(produit.get("quantite",0))       if produit else "0"),
                ("Prix unitaire HT","prix",        str(produit.get("prix",0))           if produit else "0"),
                ("Seuil alerte",   "seuil_alerte", str(produit.get("seuil_alerte",5))  if produit else "5"),
            ],
            500, 520
        )
        def save():
            try:
                p = {k: fields[k].get().strip() for k in ("ref","nom","categorie")}
                p.update({"quantite":int(fields["quantite"].get()),
                           "prix":float(fields["prix"].get()),
                           "seuil_alerte":int(fields["seuil_alerte"].get())})
                if not p["nom"]: messagebox.showerror("Erreur","Nom obligatoire.",parent=win); return
                if produit:
                    idx = self.data["produits"].index(produit)
                    self.data["produits"][idx] = p
                else:
                    self.data["produits"].append(p)
                save_data(self.data); win.destroy(); self._refresh_produits(self._search_q)
            except ValueError:
                messagebox.showerror("Erreur","Quantité, prix et seuil doivent être des nombres.",parent=win)
        self._dialog_footer(win, save)

    def _modifier_produit(self):
        p = self._get_sel(getattr(self,"tree_prod",None), self.data["produits"],
                          lambda row: (str(row[0]),str(row[1])),
                          lambda p: (str(p.get("ref","")),str(p.get("nom",""))))
        if p: self._dialog_produit(p)

    def _supprimer_produit(self):
        p = self._get_sel(getattr(self,"tree_prod",None), self.data["produits"],
                          lambda row: (str(row[0]),str(row[1])),
                          lambda p: (str(p.get("ref","")),str(p.get("nom",""))))
        if p and messagebox.askyesno("Confirmer",f"Supprimer « {p['nom']} » ?"):
            self.data["produits"].remove(p); save_data(self.data); self._refresh_produits(self._search_q)

    # ══════════════════════════════════════════════════════════════════════════
    # MOUVEMENT
    # ══════════════════════════════════════════════════════════════════════════
    def _page_mouvement(self, mode):
        label = "Entrée de stock" if mode=="entree" else "Sortie de stock"
        sub   = "Réceptionner des marchandises" if mode=="entree" else "Expédier ou consommer du stock"
        self._header(label, sub)

        # Center card
        outer = tk.Frame(self.main, bg=C["bg"])
        outer.pack(fill="both", expand=True, padx=40, pady=10)
        card = card_frame(outer)
        card.pack(fill="x", pady=10)
        inner = tk.Frame(card, bg=C["card"], padx=36, pady=28)
        inner.pack(fill="both")

        color = C["green"] if mode=="entree" else C["red"]
        icon  = "📥" if mode=="entree" else "📤"
        tk.Label(inner, text=f"{icon}  {label}", font=FONTS["heading"],
                 bg=C["card"], fg=color).grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,20))

        def lbl(r,text):
            tk.Label(inner,text=text,font=FONTS["small"],bg=C["card"],fg=C["fg2"]).grid(row=r,column=0,sticky="w",pady=8,padx=(0,20))

        lbl(1,"Produit")
        noms=[p["nom"] for p in self.data["produits"]]
        prod_var = tk.StringVar()
        cb = make_combobox(inner,prod_var,noms,width=32)
        cb.grid(row=1,column=1,sticky="w",pady=8)

        stock_lbl = tk.Label(inner,text="",font=FONTS["small"],bg=C["card"],fg=C["fg2"])
        stock_lbl.grid(row=2,column=1,sticky="w")

        def on_sel(e=None):
            p=next((x for x in self.data["produits"] if x["nom"]==prod_var.get()),None)
            if p:
                c=C["green"] if p["quantite"]>p.get("seuil_alerte",5) else C["orange"]
                stock_lbl.configure(text=f"Stock actuel : {p['quantite']} unités",fg=c)
        cb.bind("<<ComboboxSelected>>",on_sel)

        lbl(3,"Quantité")
        qte_var=tk.StringVar(value="1")
        make_entry(inner,textvariable=qte_var,width=14).grid(row=3,column=1,sticky="w",pady=8,ipady=6)

        lbl(4,"Note / Référence")
        note_var=tk.StringVar()
        make_entry(inner,textvariable=note_var,width=38).grid(row=4,column=1,sticky="w",pady=8,ipady=6)

        tk.Frame(inner,bg=C["card"],height=10).grid(row=5,column=0)

        def valider():
            nom=prod_var.get()
            if not nom: messagebox.showwarning("Attention","Choisissez un produit."); return
            try:
                qte=int(qte_var.get())
                if qte<=0: raise ValueError
            except ValueError:
                messagebox.showerror("Erreur","La quantité doit être un entier positif."); return
            p=next((x for x in self.data["produits"] if x["nom"]==nom),None)
            if mode=="sortie" and p["quantite"]<qte:
                messagebox.showerror("Erreur",f"Stock insuffisant ! Disponible : {p['quantite']}"); return
            p["quantite"]+=qte if mode=="entree" else -qte
            self.data["mouvements"].append({"date":datetime.now().strftime("%Y-%m-%d %H:%M"),
                "produit":nom,"type":"entrée" if mode=="entree" else "sortie",
                "quantite":qte,"note":note_var.get()})
            save_data(self.data)
            messagebox.showinfo("Succès",f"Mouvement enregistré !\nNouveau stock : {p['quantite']}")
            prod_var.set(""); qte_var.set("1"); note_var.set(""); stock_lbl.configure(text="")

        action_label = "l'entrée" if mode == "entree" else "la sortie"
        make_btn(inner, f"  ✅  Valider {action_label}  ",
                 valider, color).grid(row=6,column=1,sticky="w",pady=16)

    # ══════════════════════════════════════════════════════════════════════════
    # HISTORIQUE
    # ══════════════════════════════════════════════════════════════════════════
    def _page_historique(self):
        def effacer():
            if messagebox.askyesno("Confirmer","Effacer tout l'historique ?"):
                self.data["mouvements"]=[]; save_data(self.data); self._page_historique()

        self._header("Historique des mouvements","Suivi complet des entrées et sorties",[
            ("🗑️  Effacer",effacer,C["red"])
        ])

        filter_bar = tk.Frame(self.main,bg=C["bg"])
        filter_bar.pack(fill="x",padx=28,pady=(0,10))
        filter_var=tk.StringVar(value="Tous")
        tk.Label(filter_bar,text="Filtrer :",font=FONTS["small"],bg=C["bg"],fg=C["fg2"]).pack(side="left",padx=(0,10))
        for val,col in [("Tous",C["fg2"]),("Entrées",C["green"]),("Sorties",C["red"])]:
            tk.Radiobutton(filter_bar,text=val,variable=filter_var,value=val,
                           bg=C["bg"],fg=col,selectcolor=C["card2"],
                           activebackground=C["bg"],font=FONTS["body"],
                           command=lambda:self._refresh_historique(filter_var.get())
                           ).pack(side="left",padx=8)

        frame=tk.Frame(self.main,bg=C["bg"])
        frame.pack(fill="both",expand=True,padx=28,pady=(0,20))
        cols=("Date","Produit","Type","Quantité","Note")
        f_tree,self.tree_hist=scrolled_tree(frame,cols,[160,250,90,90,300])
        f_tree.pack(fill="both",expand=True)
        self._refresh_historique("Tous")

    def _refresh_historique(self,filtre):
        if not hasattr(self,"tree_hist"): return
        self.tree_hist.delete(*self.tree_hist.get_children())
        for m in reversed(self.data["mouvements"]):
            if filtre=="Entrées" and m["type"]!="entrée": continue
            if filtre=="Sorties" and m["type"]!="sortie": continue
            tag="in" if m["type"]=="entrée" else "out"
            self.tree_hist.insert("","end",values=(
                m["date"],m["produit"],m["type"],m["quantite"],m.get("note","")),tags=(tag,))
        self.tree_hist.tag_configure("in", foreground=C["green"])
        self.tree_hist.tag_configure("out",foreground=C["red"])

    # ══════════════════════════════════════════════════════════════════════════
    # CLIENTS
    # ══════════════════════════════════════════════════════════════════════════
    def _page_clients(self):
        self._header("Clients","Gérer les clients",[
            ("➕  Nouveau client",  self._dialog_client,    C["green"]),
            ("✏️  Modifier",        self._modifier_client,  C["accent2"]),
            ("🗑️  Supprimer",       self._supprimer_client, C["red"]),
        ])
        frame=tk.Frame(self.main,bg=C["bg"])
        frame.pack(fill="both",expand=True,padx=28,pady=(0,20))
        cols=("ID","Nom","Téléphone","Email","Ville","ICE","Commandes")
        f_tree,self.tree_clients=scrolled_tree(frame,cols,[70,220,130,220,120,130,90])
        f_tree.pack(fill="both",expand=True)
        self.tree_clients.bind("<Double-1>",lambda e:self._modifier_client())
        self._refresh_clients()

    def _refresh_clients(self):
        if not hasattr(self,"tree_clients"): return
        self.tree_clients.delete(*self.tree_clients.get_children())
        for c in self.data["clients"]:
            nb=sum(1 for cmd in self.data["commandes"] if cmd.get("client_id")==c.get("id"))
            self.tree_clients.insert("","end",values=(
                c.get("id",""),c.get("nom",""),c.get("telephone",""),
                c.get("email",""),c.get("ville",""),c.get("ice",""),nb))

    def _dialog_client(self, client=None):
        win,fields=self._form_dialog(
            "Nouveau client" if not client else "Modifier le client",
            [("Nom / Raison sociale *","nom",client.get("nom","") if client else ""),
             ("Téléphone","telephone",client.get("telephone","") if client else ""),
             ("Email","email",client.get("email","") if client else ""),
             ("Adresse","adresse",client.get("adresse","") if client else ""),
             ("Ville","ville",client.get("ville","") if client else ""),
             ("ICE / CIN","ice",client.get("ice","") if client else "")],
            500, 520
        )
        def save():
            nom=fields["nom"].get().strip()
            if not nom: messagebox.showerror("Erreur","Nom obligatoire.",parent=win); return
            c={k:fields[k].get().strip() for k in fields}
            if client:
                c["id"]=client["id"]
                idx=next(i for i,x in enumerate(self.data["clients"]) if x["id"]==client["id"])
                self.data["clients"][idx]=c
            else:
                c["id"]=next_id(self.data["clients"],"id","C")
                self.data["clients"].append(c)
            save_data(self.data); win.destroy(); self._refresh_clients()
        self._dialog_footer(win,save)

    def _modifier_client(self):
        c=self._get_sel(getattr(self,"tree_clients",None),self.data["clients"],
                        lambda r:(str(r[0]),),lambda c:(str(c.get("id","")),))
        if c: self._dialog_client(c)

    def _supprimer_client(self):
        c=self._get_sel(getattr(self,"tree_clients",None),self.data["clients"],
                        lambda r:(str(r[0]),),lambda c:(str(c.get("id","")),))
        if c and messagebox.askyesno("Confirmer",f"Supprimer « {c['nom']} » ?"):
            self.data["clients"]=[x for x in self.data["clients"] if x["id"]!=c["id"]]
            save_data(self.data); self._refresh_clients()

    # ══════════════════════════════════════════════════════════════════════════
    # COMMANDES
    # ══════════════════════════════════════════════════════════════════════════
    def _page_commandes(self):
        self._header("Commandes","Créer et gérer les commandes clients",[
            ("➕  Nouvelle commande", self._dialog_commande,    C["green"]),
            ("🔄  Statut",            self._modifier_statut,    C["accent2"]),
            ("📄  PDF",               self._pdf_commande,       C["purple"]),
            ("🗑️  Supprimer",         self._supprimer_commande, C["red"]),
        ])
        frame=tk.Frame(self.main,bg=C["bg"])
        frame.pack(fill="both",expand=True,padx=28,pady=(0,20))
        cols=("N°","Date","Client","Articles","Total HT","Total TTC","Statut")
        f_tree,self.tree_cmd=scrolled_tree(frame,cols,[90,110,210,80,120,130,100])
        f_tree.pack(fill="both",expand=True)
        self.tree_cmd.bind("<Double-1>",lambda e:self._voir_commande())
        self._refresh_commandes()

    def _refresh_commandes(self):
        if not hasattr(self,"tree_cmd"): return
        self.tree_cmd.delete(*self.tree_cmd.get_children())
        for c in reversed(self.data["commandes"]):
            tag={"Payée":"ok","En attente":"warn","Annulée":"err"}.get(c.get("statut",""),"")
            nb=sum(l["quantite"] for l in c.get("lignes",[]))
            self.tree_cmd.insert("","end",values=(
                c.get("numero",""),c.get("date",""),c.get("client_nom",""),
                nb,f"{c.get('total_ht',0):,.2f}",f"{c.get('total_ttc',0):,.2f}",c.get("statut","")),tags=(tag,))
        self.tree_cmd.tag_configure("ok",  foreground=C["green"])
        self.tree_cmd.tag_configure("warn",foreground=C["orange"])
        self.tree_cmd.tag_configure("err", foreground=C["red"])

    def _dialog_commande(self):
        if not self.data["clients"]:
            messagebox.showwarning("Attention","Ajoutez d'abord un client."); return
        if not self.data["produits"]:
            messagebox.showwarning("Attention","Ajoutez d'abord des produits."); return

        win=tk.Toplevel(self); win.title("Nouvelle commande")
        win.geometry("920x700"); win.configure(bg=C["bg"]); win.grab_set()
        tk.Frame(win,bg=C["accent"],height=4).pack(fill="x")

        header=tk.Frame(win,bg=C["bg"])
        header.pack(fill="x",padx=24,pady=(16,8))
        tk.Label(header,text="🛒  Nouvelle commande",font=FONTS["heading"],bg=C["bg"],fg=C["fg"]).pack(side="left")

        # Client + meta
        top=card_frame(win); top.pack(fill="x",padx=24,pady=(0,8))
        ti=tk.Frame(top,bg=C["card"],padx=20,pady=14); ti.pack(fill="x")

        def lbl2(parent,r,c,text):
            tk.Label(parent,text=text,font=FONTS["small"],bg=C["card"],fg=C["fg2"]).grid(row=r,column=c*2,sticky="w",padx=(0,8),pady=4)

        lbl2(ti,0,0,"Client *")
        client_names=[f"{c['id']} — {c['nom']}" for c in self.data["clients"]]
        client_var=tk.StringVar()
        cb=make_combobox(ti,client_var,client_names,width=28)
        cb.grid(row=0,column=1,sticky="w",padx=(0,20),pady=4)
        client_info=tk.Label(ti,text="",font=FONTS["small"],bg=C["card"],fg=C["accent"])
        client_info.grid(row=1,column=1,sticky="w")
        def on_client(e=None):
            val=client_var.get(); cid=val.split(" — ")[0] if val else ""
            c=next((x for x in self.data["clients"] if str(x.get("id",""))==cid),None)
            if c: client_info.configure(text=f"📍 {c.get('ville','')}  📞 {c.get('telephone','')}  ✉ {c.get('email','')}")
        cb.bind("<<ComboboxSelected>>",on_client)

        lbl2(ti,0,2,"Date")
        date_var=tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        make_entry(ti,textvariable=date_var,width=14).grid(row=0,column=5,sticky="w",pady=4,ipady=5)

        lbl2(ti,1,2,"Remise %")
        remise_var=tk.StringVar(value="0")
        make_entry(ti,textvariable=remise_var,width=8).grid(row=1,column=5,sticky="w",pady=4,ipady=5)

        # Add line area
        add_card=card_frame(win); add_card.pack(fill="x",padx=24,pady=(0,6))
        af=tk.Frame(add_card,bg=C["card"],padx=16,pady=10); af.pack(fill="x")
        tk.Label(af,text="Ajouter une ligne :",font=("Segoe UI Semibold",9),bg=C["card"],fg=C["fg2"]).grid(row=0,column=0,columnspan=8,sticky="w",pady=(0,6))

        prod_names=[p["nom"] for p in self.data["produits"]]
        prod_var2=tk.StringVar()
        make_combobox(af,prod_var2,prod_names,width=22).grid(row=1,column=0,padx=(0,8))

        def make_lbl_entry(col,lbl_text,width,default=""):
            tk.Label(af,text=lbl_text,font=FONTS["small"],bg=C["card"],fg=C["fg2"]).grid(row=1,column=col,padx=(0,3))
            v=tk.StringVar(value=default)
            make_entry(af,textvariable=v,width=width).grid(row=1,column=col+1,padx=(0,10),ipady=5)
            return v

        qte_v=make_lbl_entry(1,"Qté",6,"1")
        pu_v =make_lbl_entry(3,"P.U.",10,"0")
        tva_v=make_lbl_entry(5,"TVA%",6,"20")

        def auto_pu(*a):
            p=next((x for x in self.data["produits"] if x["nom"]==prod_var2.get()),None)
            if p: pu_v.set(str(p.get("prix",0)))
        prod_var2.trace("w",auto_pu)

        lignes=[]

        lines_card=card_frame(win); lines_card.pack(fill="both",expand=True,padx=24,pady=(0,6))
        lc=tk.Frame(lines_card,bg=C["card"],padx=16,pady=10); lc.pack(fill="both",expand=True)

        lcols=("Produit","Qté","P.U. HT","TVA","Total HT"); lw=[280,70,110,70,130]
        lf,tree_lines=scrolled_tree(lc,lcols,lw,height=7)
        lf.pack(fill="both",expand=True)

        total_lbl=tk.Label(lc,text="",font=("Segoe UI Semibold",11),bg=C["card"],fg=C["green"])
        total_lbl.pack(anchor="e",pady=(8,0))

        def refresh_lines():
            tree_lines.delete(*tree_lines.get_children())
            ht=sum(l["quantite"]*l["prix_unit"] for l in lignes)
            for l in lignes:
                lht=l["quantite"]*l["prix_unit"]
                tree_lines.insert("","end",values=(l["produit_nom"],l["quantite"],f"{l['prix_unit']:.2f}",f"{l.get('tva',20)}%",f"{lht:.2f}"))
            r=float(remise_var.get() or 0); net=ht*(1-r/100); tv=net*.20; ttc=net+tv
            total_lbl.configure(text=f"HT : {net:,.2f}  |  TVA : {tv:,.2f}  |  TTC : {ttc:,.2f} MAD")

        def ajouter_ligne():
            nom=prod_var2.get()
            if not nom: messagebox.showwarning("Attention","Choisissez un produit.",parent=win); return
            try:
                qte=int(qte_v.get()); pu=float(pu_v.get()); tva=float(tva_v.get())
            except: messagebox.showerror("Erreur","Valeurs invalides.",parent=win); return
            p=next((x for x in self.data["produits"] if x["nom"]==nom),None)
            already=sum(l["quantite"] for l in lignes if l["produit_nom"]==nom)
            if p and p["quantite"]-already<qte:
                messagebox.showerror("Erreur",f"Stock insuffisant ! Dispo : {p['quantite']-already}",parent=win); return
            ex=next((l for l in lignes if l["produit_nom"]==nom),None)
            if ex: ex["quantite"]+=qte
            else: lignes.append({"produit_nom":nom,"quantite":qte,"prix_unit":pu,"tva":tva})
            refresh_lines()

        def suppr_ligne():
            sel=tree_lines.selection()
            if sel:
                nom=tree_lines.item(sel[0])["values"][0]
                lignes[:]=[l for l in lignes if l["produit_nom"]!=nom]
                refresh_lines()

        make_btn(af,"➕ Ajouter",ajouter_ligne,C["green"],small=True).grid(row=1,column=7,padx=(8,0))
        make_btn(af,"🗑️",suppr_ligne,C["red"],small=True).grid(row=1,column=8,padx=4)

        # Note + buttons
        bf=tk.Frame(win,bg=C["bg"]); bf.pack(fill="x",padx=24,pady=10)
        note_v=tk.StringVar()
        tk.Label(bf,text="Note :",font=FONTS["small"],bg=C["bg"],fg=C["fg2"]).pack(side="left")
        make_entry(bf,textvariable=note_v,width=40).pack(side="left",padx=8,ipady=5,fill="x",expand=True)

        def valider():
            if not client_var.get(): messagebox.showerror("Erreur","Choisissez un client.",parent=win); return
            if not lignes: messagebox.showerror("Erreur","Ajoutez au moins un produit.",parent=win); return
            cid=client_var.get().split(" — ")[0]
            client=next((c for c in self.data["clients"] if str(c.get("id",""))==cid),None)
            r=float(remise_var.get() or 0)
            ht=sum(l["quantite"]*l["prix_unit"] for l in lignes)
            net=ht*(1-r/100); tv=net*.20; ttc=net+tv
            for l in lignes:
                p=next((x for x in self.data["produits"] if x["nom"]==l["produit_nom"]),None)
                if p: p["quantite"]-=l["quantite"]
            cmd={"numero":next_id(self.data["commandes"],"numero","CMD"),
                 "date":date_var.get(),"echeance":date_var.get(),
                 "client_id":client["id"] if client else "",
                 "client_nom":client["nom"] if client else "",
                 "lignes":lignes[:],"remise":r,
                 "total_ht":round(net,2),"total_tva":round(tv,2),"total_ttc":round(ttc,2),
                 "statut":"En attente","note":note_v.get(),"conditions":"30 jours net"}
            self.data["commandes"].append(cmd); save_data(self.data)
            win.destroy(); self._refresh_commandes()
            if messagebox.askyesno("Succès",f"Commande {cmd['numero']} créée !\nGénérer le PDF ?"):
                self._generer_pdf_pour(cmd)

        make_btn(bf,"  ✅  Valider la commande  ",valider,C["green"]).pack(side="right",padx=(8,0))
        make_btn(bf,"Annuler",win.destroy,"#555").pack(side="right")

    def _voir_commande(self):
        cmd=self._get_cmd()
        if not cmd: return
        win=tk.Toplevel(self); win.title(f"Commande {cmd['numero']}")
        win.geometry("680x560"); win.configure(bg=C["bg"])
        tk.Frame(win,bg=C["accent"],height=4).pack(fill="x")
        client=next((c for c in self.data["clients"] if str(c.get("id",""))==str(cmd.get("client_id",""))),{})
        tk.Label(win,text=f"Commande {cmd['numero']}",font=FONTS["heading"],bg=C["bg"],fg=C["fg"]).pack(pady=(16,2),padx=24,anchor="w")
        info=f"Client : {cmd['client_nom']}  •  {cmd.get('date','')}  •  {cmd.get('statut','')}"
        if client.get("telephone"): info+=f"  •  📞 {client['telephone']}"
        tk.Label(win,text=info,font=FONTS["small"],bg=C["bg"],fg=C["fg2"]).pack(padx=24,anchor="w")
        separator(win).pack(fill="x",padx=24,pady=10)
        frame=tk.Frame(win,bg=C["bg"]); frame.pack(fill="both",expand=True,padx=24)
        cols=("Produit","Qté","P.U. HT","TVA","Total HT")
        f_tree,tree=scrolled_tree(frame,cols,[260,70,110,70,120],height=10)
        f_tree.pack(fill="both",expand=True)
        for l in cmd.get("lignes",[]):
            ht=l["quantite"]*l["prix_unit"]
            tree.insert("","end",values=(l["produit_nom"],l["quantite"],f"{l['prix_unit']:.2f}",f"{l.get('tva',20)}%",f"{ht:.2f}"))
        totals=tk.Frame(win,bg=C["card2"],padx=24,pady=12); totals.pack(fill="x",padx=24,pady=8)
        for lbl_t,val,col in [
            ("Total HT",f"{cmd.get('total_ht',0):,.2f} MAD",C["fg"]),
            ("TVA (20%)",f"{cmd.get('total_tva',0):,.2f} MAD",C["fg2"]),
            ("TOTAL TTC",f"{cmd.get('total_ttc',0):,.2f} MAD",C["green"]),
        ]:
            row=tk.Frame(totals,bg=C["card2"]); row.pack(fill="x",pady=2)
            tk.Label(row,text=lbl_t,font=FONTS["small"],bg=C["card2"],fg=C["fg2"],width=14,anchor="e").pack(side="left")
            tk.Label(row,text=val,font=("Segoe UI Semibold",11),bg=C["card2"],fg=col).pack(side="left",padx=10)
        bf=tk.Frame(win,bg=C["bg"]); bf.pack(pady=8)
        make_btn(bf,"📄  Générer PDF",lambda:self._generer_pdf_pour(cmd),C["purple"]).pack(side="left",padx=8)
        make_btn(bf,"Fermer",win.destroy,"#555").pack(side="left")

    def _modifier_statut(self):
        cmd=self._get_cmd()
        if not cmd: return
        win=tk.Toplevel(self); win.title("Modifier le statut")
        win.geometry("300,220".replace(",","x")); win.configure(bg=C["bg"]); win.grab_set()
        tk.Frame(win,bg=C["accent"],height=4).pack(fill="x")
        tk.Label(win,text="Nouveau statut",font=FONTS["heading"],bg=C["bg"],fg=C["fg"]).pack(pady=(20,16))
        s_var=tk.StringVar(value=cmd.get("statut",""))
        for s,col in [("En attente",C["orange"]),("Payée",C["green"]),("Annulée",C["red"])]:
            f=tk.Frame(win,bg=C["bg"]); f.pack(fill="x",padx=40,pady=4)
            tk.Radiobutton(f,text=s,variable=s_var,value=s,font=FONTS["body"],
                           bg=C["bg"],fg=col,selectcolor=C["card2"],
                           activebackground=C["bg"]).pack(side="left")
        def save():
            idx=next(i for i,c in enumerate(self.data["commandes"]) if c["numero"]==cmd["numero"])
            self.data["commandes"][idx]["statut"]=s_var.get()
            save_data(self.data); win.destroy(); self._refresh_commandes()
        make_btn(win,"💾  Enregistrer",save,C["green"]).pack(pady=20)

    def _supprimer_commande(self):
        cmd=self._get_cmd()
        if cmd and messagebox.askyesno("Confirmer",f"Supprimer {cmd['numero']} ?"):
            self.data["commandes"]=[c for c in self.data["commandes"] if c["numero"]!=cmd["numero"]]
            save_data(self.data); self._refresh_commandes()

    def _pdf_commande(self):
        cmd=self._get_cmd()
        if cmd: self._generer_pdf_pour(cmd)

    def _get_cmd(self):
        t=getattr(self,"tree_cmd",None)
        if not t: return None
        sel=t.selection()
        if not sel: messagebox.showinfo("Info","Sélectionnez une commande."); return None
        num=str(t.item(sel[0])["values"][0])
        return next((c for c in self.data["commandes"] if str(c.get("numero",""))==num),None)

    def _generer_pdf_pour(self,cmd):
        if not REPORTLAB_OK:
            messagebox.showerror("Erreur","reportlab non installé.\npip install reportlab"); return
        client=next((c for c in self.data["clients"] if str(c.get("id",""))==str(cmd.get("client_id",""))),{})
        pm={p["nom"]:p for p in self.data["produits"]}
        fn=f"Facture_{cmd['numero']}_{cmd['client_nom'].replace(' ','_')}.pdf"
        fp=filedialog.asksaveasfilename(title="Enregistrer",defaultextension=".pdf",
                                        initialfile=fn,filetypes=[("PDF","*.pdf")])
        if not fp: return
        try:
            generer_facture_pdf(cmd, client, pm, fp, config=self.config_data)
            messagebox.showinfo("Succès",f"PDF généré :\n{fp}")
        except Exception as e:
            messagebox.showerror("Erreur PDF",str(e))

    # ══════════════════════════════════════════════════════════════════════════
    # FACTURES
    # ══════════════════════════════════════════════════════════════════════════
    def _page_factures(self):
        self._header("Factures","Gérer et exporter les factures PDF")
        filter_bar=tk.Frame(self.main,bg=C["bg"]); filter_bar.pack(fill="x",padx=28,pady=(0,10))
        filter_var=tk.StringVar(value="Toutes")
        tk.Label(filter_bar,text="Filtrer :",font=FONTS["small"],bg=C["bg"],fg=C["fg2"]).pack(side="left",padx=(0,10))
        for v,col in [("Toutes",C["fg2"]),("En attente",C["orange"]),("Payée",C["green"]),("Annulée",C["red"])]:
            tk.Radiobutton(filter_bar,text=v,variable=filter_var,value=v,bg=C["bg"],fg=col,
                           selectcolor=C["card2"],activebackground=C["bg"],font=FONTS["body"],
                           command=lambda:self._refresh_factures(filter_var.get())).pack(side="left",padx=6)
        make_btn(filter_bar,"📄  Générer PDF sélection",self._pdf_facture,C["purple"]).pack(side="right")

        frame=tk.Frame(self.main,bg=C["bg"]); frame.pack(fill="both",expand=True,padx=28,pady=(0,20))
        cols=("N° Facture","Date","Client","Total HT","TVA","Total TTC","Statut")
        f_tree,self.tree_fact=scrolled_tree(frame,cols,[100,110,220,110,110,130,100])
        f_tree.pack(fill="both",expand=True)
        self.tree_fact.bind("<Double-1>",lambda e:self._pdf_facture())
        self._refresh_factures("Toutes")

    def _refresh_factures(self,filtre):
        if not hasattr(self,"tree_fact"): return
        self.tree_fact.delete(*self.tree_fact.get_children())
        for c in reversed(self.data["commandes"]):
            if filtre!="Toutes" and c.get("statut","")!=filtre: continue
            tag={"Payée":"ok","En attente":"warn","Annulée":"err"}.get(c.get("statut",""),"")
            self.tree_fact.insert("","end",values=(
                c.get("numero",""),c.get("date",""),c.get("client_nom",""),
                f"{c.get('total_ht',0):,.2f}",f"{c.get('total_tva',0):,.2f}",
                f"{c.get('total_ttc',0):,.2f}",c.get("statut","")),tags=(tag,))
        self.tree_fact.tag_configure("ok",  foreground=C["green"])
        self.tree_fact.tag_configure("warn",foreground=C["orange"])
        self.tree_fact.tag_configure("err", foreground=C["red"])

    def _pdf_facture(self):
        if not hasattr(self,"tree_fact"): return
        sel=self.tree_fact.selection()
        if not sel: messagebox.showinfo("Info","Sélectionnez une facture."); return
        num=str(self.tree_fact.item(sel[0])["values"][0])
        cmd=next((c for c in self.data["commandes"] if str(c.get("numero",""))==num),None)
        if cmd: self._generer_pdf_pour(cmd)

    # ══════════════════════════════════════════════════════════════════════════
    # UTILISATEURS
    # ══════════════════════════════════════════════════════════════════════════
    def _page_users(self):
        self._header("Utilisateurs","Gérer les comptes d'accès",[
            ("➕  Nouvel utilisateur", self._dialog_user,    C["green"]),
            ("🔑  Changer mot de passe", self._changer_mdp, C["accent2"]),
            ("🗑️  Supprimer",           self._supprimer_user,C["red"]),
        ])
        frame=tk.Frame(self.main,bg=C["bg"]); frame.pack(fill="both",expand=True,padx=28,pady=(0,20))
        cols=("Nom d'utilisateur","Nom complet","Rôle")
        f_tree,self.tree_users=scrolled_tree(frame,cols,[200,300,150],height=15)
        f_tree.pack(fill="both",expand=True)
        self._refresh_users()

    def _refresh_users(self):
        if not hasattr(self,"tree_users"): return
        self.tree_users.delete(*self.tree_users.get_children())
        for u in self.users:
            self.tree_users.insert("","end",values=(u.get("username",""),u.get("nom",""),u.get("role","")))

    def _dialog_user(self):
        win,fields=self._form_dialog("Nouvel utilisateur",[
            ("Nom d'utilisateur *","username",""),
            ("Nom complet","nom",""),
            ("Rôle (admin/user)","role","user"),
        ],440,380)
        tk.Label(win,text="Mot de passe *",font=FONTS["small"],bg=C["card"],fg=C["fg2"]).pack(anchor="w",padx=24,pady=(8,2))
        pw_var=tk.StringVar()
        make_entry(win,textvariable=pw_var,show="●").pack(fill="x",padx=24,ipady=6)
        def save():
            u=fields["username"].get().strip()
            if not u: messagebox.showerror("Erreur","Nom d'utilisateur obligatoire.",parent=win); return
            if any(x["username"]==u for x in self.users):
                messagebox.showerror("Erreur","Cet utilisateur existe déjà.",parent=win); return
            pw=pw_var.get()
            if not pw: messagebox.showerror("Erreur","Mot de passe obligatoire.",parent=win); return
            self.users.append({"username":u,"password":hash_pw(pw),
                                "nom":fields["nom"].get().strip(),"role":fields["role"].get().strip() or "user"})
            save_users(self.users); win.destroy(); self._refresh_users()
        self._dialog_footer(win,save)

    def _changer_mdp(self):
        sel=self.tree_users.selection() if hasattr(self,"tree_users") else None
        if not sel: messagebox.showinfo("Info","Sélectionnez un utilisateur."); return
        uname=self.tree_users.item(sel[0])["values"][0]
        win=tk.Toplevel(self); win.title("Changer le mot de passe")
        win.geometry("380x280"); win.configure(bg=C["bg"]); win.grab_set()
        tk.Frame(win,bg=C["accent"],height=4).pack(fill="x")
        tk.Label(win,text=f"Nouveau mot de passe pour {uname}",font=FONTS["heading"],bg=C["bg"],fg=C["fg"]).pack(pady=(20,16),padx=24)
        pw1=tk.StringVar(); pw2=tk.StringVar()
        for txt,v in [("Nouveau mot de passe",pw1),("Confirmer",pw2)]:
            tk.Label(win,text=txt,font=FONTS["small"],bg=C["bg"],fg=C["fg2"]).pack(anchor="w",padx=24,pady=(6,2))
            make_entry(win,textvariable=v,show="●").pack(fill="x",padx=24,ipady=6)
        def save():
            if pw1.get()!=pw2.get(): messagebox.showerror("Erreur","Les mots de passe ne correspondent pas.",parent=win); return
            if not pw1.get(): messagebox.showerror("Erreur","Mot de passe vide.",parent=win); return
            for u in self.users:
                if u["username"]==uname: u["password"]=hash_pw(pw1.get())
            save_users(self.users); win.destroy(); messagebox.showinfo("Succès","Mot de passe modifié.")
        make_btn(win,"💾  Enregistrer",save,C["green"]).pack(pady=16)

    def _supprimer_user(self):
        if not hasattr(self,"tree_users"): return
        sel=self.tree_users.selection()
        if not sel: return
        uname=self.tree_users.item(sel[0])["values"][0]
        if uname==self.current_user["username"]:
            messagebox.showerror("Erreur","Impossible de supprimer votre propre compte."); return
        if messagebox.askyesno("Confirmer",f"Supprimer l'utilisateur « {uname} » ?"):
            self.users=[u for u in self.users if u["username"]!=uname]
            save_users(self.users); self._refresh_users()

    # ══════════════════════════════════════════════════════════════════════════
    # PARAMÈTRES / CONFIGURATION FACTURE
    # ══════════════════════════════════════════════════════════════════════════
    def _page_settings(self):
        self._header("Paramètres", "Configuration de l'entreprise et des factures")

        # Scrollable container
        canvas = tk.Canvas(self.main, bg=C["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.main, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        scroll_frame = tk.Frame(canvas, bg=C["bg"])
        scroll_win = canvas.create_window((0,0), window=scroll_frame, anchor="nw")

        def on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def on_canvas_resize(e):
            canvas.itemconfig(scroll_win, width=e.width)
        scroll_frame.bind("<Configure>", on_configure)
        canvas.bind("<Configure>", on_canvas_resize)

        # Mouse wheel
        def on_mousewheel(e):
            canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)

        fields = {}

        def section_card(title, icon, form_fields):
            """Build a settings card with labeled fields."""
            outer = card_frame(scroll_frame)
            outer.pack(fill="x", padx=28, pady=(0,16))
            inner = tk.Frame(outer, bg=C["card"], padx=24, pady=20)
            inner.pack(fill="x")

            # Card title
            title_row = tk.Frame(inner, bg=C["card"])
            title_row.pack(fill="x", pady=(0,14))
            tk.Label(title_row, text=icon, font=("Segoe UI",16),
                     bg=C["card"], fg=C["accent"]).pack(side="left", padx=(0,10))
            tk.Label(title_row, text=title, font=FONTS["heading"],
                     bg=C["card"], fg=C["fg"]).pack(side="left")
            separator(inner).pack(fill="x", pady=(0,14))

            # Two-column grid
            grid = tk.Frame(inner, bg=C["card"])
            grid.pack(fill="x")
            grid.columnconfigure(1, weight=1)
            grid.columnconfigure(3, weight=1)

            for i, (label, key, hint) in enumerate(form_fields):
                row = i // 2
                col_base = (i % 2) * 2
                tk.Label(grid, text=label, font=FONTS["small"],
                         bg=C["card"], fg=C["fg2"], anchor="w",
                         width=18).grid(row=row*2, column=col_base, sticky="w",
                                        padx=(0 if col_base==0 else 20, 8), pady=(8,2))
                v = tk.StringVar(value=self.config_data.get(key, ""))
                e = make_entry(grid, textvariable=v)
                e.grid(row=row*2+1, column=col_base, sticky="ew",
                       padx=(0 if col_base==0 else 20, 8), ipady=6)
                if hint:
                    tk.Label(grid, text=hint, font=("Segoe UI",8),
                             bg=C["card"], fg=C["fg3"]).grid(row=row*2+2, column=col_base, sticky="w",
                                                              padx=(0 if col_base==0 else 20, 8))
                fields[key] = v

        # Section 1: Entreprise
        section_card("Informations de l'entreprise", "🏢", [
            ("Nom / Raison sociale",  "entreprise_nom",     "Apparaît en haut de la facture"),
            ("Adresse",               "entreprise_adresse", "Rue, numéro..."),
            ("Ville / Code postal",   "entreprise_ville",   "Ex : 20000 Casablanca"),
            ("Téléphone",             "entreprise_tel",     ""),
            ("Email",                 "entreprise_email",   ""),
            ("Identifiant fiscal (IF)","entreprise_if",     ""),
            ("Registre Commerce (RC)","entreprise_rc",      ""),
            ("ICE",                   "entreprise_ice",     "Identifiant Commun de l'Entreprise"),
        ])

        # Section 2: Facture
        section_card("Configuration des factures", "🧾", [
            ("Conditions de paiement","facture_conditions","Ex : 30 jours net, Paiement immédiat..."),
            ("Devise / Monnaie",      "facture_monnaie",   "Ex : MAD, EUR, USD"),
            ("TVA par défaut (%)",    "facture_tva_defaut","Appliquée automatiquement aux nouvelles lignes"),
            ("",                      "",                  ""),
        ])

        # Pied de page (full width)
        outer2 = card_frame(scroll_frame)
        outer2.pack(fill="x", padx=28, pady=(0,16))
        inner2 = tk.Frame(outer2, bg=C["card"], padx=24, pady=20)
        inner2.pack(fill="x")
        title_row2 = tk.Frame(inner2, bg=C["card"])
        title_row2.pack(fill="x", pady=(0,10))
        tk.Label(title_row2, text="📝", font=("Segoe UI",16),
                 bg=C["card"], fg=C["accent"]).pack(side="left", padx=(0,10))
        tk.Label(title_row2, text="Pied de page de la facture", font=FONTS["heading"],
                 bg=C["card"], fg=C["fg"]).pack(side="left")
        separator(inner2).pack(fill="x", pady=(0,12))
        tk.Label(inner2, text="Texte de bas de facture", font=FONTS["small"],
                 bg=C["card"], fg=C["fg2"]).pack(anchor="w", pady=(0,4))
        pied_v = tk.StringVar(value=self.config_data.get("facture_pied",""))
        pied_e = make_entry(inner2, textvariable=pied_v)
        pied_e.pack(fill="x", ipady=8)
        fields["facture_pied"] = pied_v

        # Section 3: Couleurs PDF
        outer3 = card_frame(scroll_frame)
        outer3.pack(fill="x", padx=28, pady=(0,16))
        inner3 = tk.Frame(outer3, bg=C["card"], padx=24, pady=20)
        inner3.pack(fill="x")
        title_row3 = tk.Frame(inner3, bg=C["card"])
        title_row3.pack(fill="x", pady=(0,10))
        tk.Label(title_row3, text="🎨", font=("Segoe UI",16),
                 bg=C["card"], fg=C["accent"]).pack(side="left", padx=(0,10))
        tk.Label(title_row3, text="Couleurs du PDF", font=FONTS["heading"],
                 bg=C["card"], fg=C["fg"]).pack(side="left")
        separator(inner3).pack(fill="x", pady=(0,12))
        colors_grid = tk.Frame(inner3, bg=C["card"])
        colors_grid.pack(fill="x")
        for i,(label,key,default) in enumerate([
            ("Couleur principale",  "facture_couleur",        "#1a2744"),
            ("Couleur accent",      "facture_couleur_accent", "#2563eb"),
        ]):
            col = i * 2
            colors_grid.columnconfigure(col+1, weight=1)
            tk.Label(colors_grid, text=label, font=FONTS["small"],
                     bg=C["card"], fg=C["fg2"]).grid(row=0, column=col, sticky="w", padx=(0 if col==0 else 20, 8))
            v = tk.StringVar(value=self.config_data.get(key, default))
            entry = make_entry(colors_grid, textvariable=v, width=12)
            entry.grid(row=1, column=col, sticky="ew", padx=(0 if col==0 else 20, 8), ipady=6)
            # Color preview swatch
            swatch = tk.Label(colors_grid, text="  ", bg=self.config_data.get(key,default), width=4)
            swatch.grid(row=1, column=col+1, sticky="w", padx=(0,8))
            def update_swatch(e, sv=v, sw=swatch):
                try: sw.configure(bg=sv.get())
                except: pass
            entry.bind("<KeyRelease>", update_swatch)
            fields[key] = v

        tk.Label(inner3, text="Format hexadécimal : ex #1a2744  •  Modifiez la valeur pour voir l'aperçu →",
                 font=("Segoe UI",8), bg=C["card"], fg=C["fg3"]).pack(anchor="w", pady=(10,0))

        # Preview + Save row
        action_row = tk.Frame(scroll_frame, bg=C["bg"])
        action_row.pack(fill="x", padx=28, pady=(4,24))

        def save_settings():
            for key, var in fields.items():
                if key:
                    self.config_data[key] = var.get().strip()
            save_config(self.config_data)
            # Show confirmation banner
            banner = tk.Frame(scroll_frame, bg=C["green"], pady=8)
            banner.pack(fill="x", padx=28)
            tk.Label(banner, text="✅  Paramètres enregistrés avec succès !",
                     font=FONTS["body"], bg=C["green"], fg=C["white"]).pack()
            banner.after(3000, banner.destroy)

        def preview_pdf():
            # Generate a preview PDF with dummy data
            if not REPORTLAB_OK:
                messagebox.showerror("Erreur","reportlab non installé."); return
            # Apply current field values temporarily
            temp_cfg = {k: v.get().strip() for k,v in fields.items() if k}
            for k,v in self.config_data.items():
                temp_cfg.setdefault(k,v)
            dummy_cmd = {
                "numero":"PREVIEW-001","date":datetime.now().strftime("%Y-%m-%d"),
                "echeance":datetime.now().strftime("%Y-%m-%d"),"statut":"Aperçu",
                "client_nom":"Client Exemple","remise":0,
                "lignes":[
                    {"produit_nom":"Produit A","quantite":2,"prix_unit":500,"tva":20},
                    {"produit_nom":"Produit B","quantite":5,"prix_unit":120,"tva":20},
                ],
                "total_ht":1600,"total_tva":320,"total_ttc":1920,
                "note":"Ceci est un aperçu de votre facture.",
                "conditions": temp_cfg.get("facture_conditions","30 jours"),
            }
            dummy_client = {"nom":"Client Exemple SARL","adresse":"45 Bd Mohammed V",
                            "ville":"20000 Casablanca","telephone":"+212 522-000000",
                            "email":"client@exemple.ma","ice":"001234567000000"}
            fp = filedialog.asksaveasfilename(title="Aperçu PDF",
                defaultextension=".pdf",initialfile="apercu_facture.pdf",
                filetypes=[("PDF","*.pdf")])
            if not fp: return
            try:
                generer_facture_pdf(dummy_cmd, dummy_client, {}, fp, config=temp_cfg)
                messagebox.showinfo("Aperçu généré", f"PDF enregistré :\n{fp}")
            except Exception as ex:
                messagebox.showerror("Erreur", str(ex))

        make_btn(action_row, "👁️  Aperçu PDF", preview_pdf, C["accent2"]).pack(side="left", padx=(0,8))
        make_btn(action_row, "💾  Enregistrer les paramètres", save_settings, C["green"]).pack(side="left")

    # ══════════════════════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════════════════════
    def _form_dialog(self, title, fields, w=480, h=480):
        win=tk.Toplevel(self); win.title(title)
        win.geometry(f"{w}x{h}"); win.configure(bg=C["bg"]); win.grab_set()
        tk.Frame(win,bg=C["accent"],height=4).pack(fill="x")
        tk.Label(win,text=title,font=FONTS["heading"],bg=C["bg"],fg=C["fg"]).pack(pady=(20,4),padx=24,anchor="w")
        separator(win).pack(fill="x",padx=24,pady=(0,8))
        entries={}
        for label,key,default in fields:
            tk.Label(win,text=label,font=FONTS["small"],bg=C["bg"],fg=C["fg2"]).pack(anchor="w",padx=24,pady=(8,2))
            v=tk.StringVar(value=default)
            e=make_entry(win,textvariable=v)
            e.pack(fill="x",padx=24,ipady=7)
            entries[key]=v
        return win,entries

    def _dialog_footer(self,win,save_fn):
        bf=tk.Frame(win,bg=C["bg"]); bf.pack(fill="x",padx=24,pady=16)
        make_btn(bf,"💾  Enregistrer",save_fn,C["green"]).pack(side="right",padx=(8,0))
        make_btn(bf,"Annuler",win.destroy,"#555").pack(side="right")

    def _get_sel(self, tree, lst, row_key_fn, item_key_fn):
        if tree is None: return None
        sel=tree.selection()
        if not sel: messagebox.showinfo("Info","Sélectionnez un élément."); return None
        row=tree.item(sel[0])["values"]
        key=row_key_fn(row)
        return next((x for x in lst if item_key_fn(x)==key),None)

# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
def main():
    login=LoginWindow()
    login.mainloop()
    if login.logged_user:
        app=GestionStock(login.logged_user)
        app.mainloop()

if __name__=="__main__":
    main()