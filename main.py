import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
from datetime import datetime

# ─── Data Storage ────────────────────────────────────────────────────────────

DATA_FILE = os.path.join(os.path.expanduser("~"), "stock_data.json")

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"produits": [], "mouvements": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ─── Main Application ─────────────────────────────────────────────────────────

class GestionStock(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("📦 Gestion de Stock")
        self.geometry("1100x680")
        self.minsize(900, 600)
        self.configure(bg="#0f1117")

        self.data = load_data()

        # ── Fonts & Colors ──
        self.BG       = "#0f1117"
        self.PANEL    = "#1a1d27"
        self.CARD     = "#22263a"
        self.ACCENT   = "#4f8ef7"
        self.GREEN    = "#2ecc71"
        self.RED      = "#e74c3c"
        self.ORANGE   = "#f39c12"
        self.FG       = "#e8eaf6"
        self.FG2      = "#8892b0"
        self.BORDER   = "#2d3155"

        self.font_title  = ("Segoe UI", 20, "bold")
        self.font_header = ("Segoe UI", 11, "bold")
        self.font_body   = ("Segoe UI", 10)
        self.font_small  = ("Segoe UI", 9)
        self.font_num    = ("Consolas", 11, "bold")

        self._build_ui()

    # ── Build Layout ──────────────────────────────────────────────────────────

    def _build_ui(self):
        # Sidebar
        sidebar = tk.Frame(self, bg=self.PANEL, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Logo
        logo_frame = tk.Frame(sidebar, bg=self.PANEL)
        logo_frame.pack(fill="x", pady=(28, 20), padx=18)
        tk.Label(logo_frame, text="📦", font=("Segoe UI", 28), bg=self.PANEL, fg=self.ACCENT).pack()
        tk.Label(logo_frame, text="GestionStock", font=("Segoe UI", 14, "bold"),
                 bg=self.PANEL, fg=self.FG).pack()
        tk.Label(logo_frame, text="v1.0", font=self.font_small,
                 bg=self.PANEL, fg=self.FG2).pack()

        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", padx=14, pady=8)

        # Nav buttons
        self.nav_buttons = {}
        nav_items = [
            ("🏠  Tableau de bord", "dashboard"),
            ("📋  Produits",        "produits"),
            ("📥  Entrée stock",    "entree"),
            ("📤  Sortie stock",    "sortie"),
            ("📊  Historique",      "historique"),
        ]
        for label, key in nav_items:
            btn = tk.Button(
                sidebar, text=label, anchor="w", font=self.font_body,
                bg=self.PANEL, fg=self.FG2, relief="flat", cursor="hand2",
                padx=18, pady=10, activebackground=self.CARD,
                activeforeground=self.ACCENT,
                command=lambda k=key: self._show_page(k)
            )
            btn.pack(fill="x", pady=1)
            self.nav_buttons[key] = btn

        # Bottom info
        tk.Label(sidebar, text=f"© 2026 GestionStock",
                 font=self.font_small, bg=self.PANEL, fg=self.FG2).pack(side="bottom", pady=14)

        # Main area
        self.main = tk.Frame(self, bg=self.BG)
        self.main.pack(side="left", fill="both", expand=True)

        # Pages
        self.pages = {}
        self._show_page("dashboard")

    def _show_page(self, key):
        # Update nav highlight
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(bg=self.CARD, fg=self.ACCENT, relief="flat")
            else:
                btn.configure(bg=self.PANEL, fg=self.FG2, relief="flat")

        # Clear main
        for w in self.main.winfo_children():
            w.destroy()

        if key == "dashboard":  self._page_dashboard()
        elif key == "produits":  self._page_produits()
        elif key == "entree":    self._page_mouvement("entree")
        elif key == "sortie":    self._page_mouvement("sortie")
        elif key == "historique":self._page_historique()

    # ── Page: Dashboard ───────────────────────────────────────────────────────

    def _page_dashboard(self):
        self._header("🏠 Tableau de bord", "Vue d'ensemble de votre stock")

        produits = self.data["produits"]
        total_articles = len(produits)
        total_valeur = sum(p.get("prix", 0) * p.get("quantite", 0) for p in produits)
        alertes = [p for p in produits if p.get("quantite", 0) <= p.get("seuil_alerte", 5)]
        ruptures = [p for p in produits if p.get("quantite", 0) == 0]

        # KPI cards
        kpi_frame = tk.Frame(self.main, bg=self.BG)
        kpi_frame.pack(fill="x", padx=28, pady=(10, 18))

        kpis = [
            ("📦 Produits",       str(total_articles),         self.ACCENT),
            ("💰 Valeur totale",  f"{total_valeur:,.2f} MAD",  self.GREEN),
            ("⚠️  Alertes stock", str(len(alertes)),            self.ORANGE),
            ("🚨 Ruptures",       str(len(ruptures)),           self.RED),
        ]
        for i, (title, val, color) in enumerate(kpis):
            card = tk.Frame(kpi_frame, bg=self.CARD, padx=22, pady=18)
            card.grid(row=0, column=i, sticky="nsew", padx=8)
            kpi_frame.columnconfigure(i, weight=1)
            tk.Label(card, text=title, font=self.font_body, bg=self.CARD, fg=self.FG2).pack(anchor="w")
            tk.Label(card, text=val, font=("Segoe UI", 18, "bold"), bg=self.CARD, fg=color).pack(anchor="w", pady=(4,0))

        # Two columns
        cols = tk.Frame(self.main, bg=self.BG)
        cols.pack(fill="both", expand=True, padx=28, pady=4)
        cols.columnconfigure(0, weight=2)
        cols.columnconfigure(1, weight=1)

        # Recent movements
        left = tk.Frame(cols, bg=self.CARD, padx=16, pady=14)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        tk.Label(left, text="📋 Derniers mouvements", font=self.font_header,
                 bg=self.CARD, fg=self.FG).pack(anchor="w", pady=(0,10))

        cols_mv = ("Date", "Produit", "Type", "Quantité")
        tree = ttk.Treeview(left, columns=cols_mv, show="headings", height=10)
        self._style_tree(tree, cols_mv, [130, 200, 80, 80])
        tree.pack(fill="both", expand=True)

        mouvements = list(reversed(self.data["mouvements"][-15:]))
        for m in mouvements:
            tag = "entree" if m["type"] == "entrée" else "sortie"
            tree.insert("", "end", values=(
                m["date"], m["produit"], m["type"], m["quantite"]
            ), tags=(tag,))
        tree.tag_configure("entree", foreground=self.GREEN)
        tree.tag_configure("sortie", foreground=self.RED)

        # Alert list
        right = tk.Frame(cols, bg=self.CARD, padx=16, pady=14)
        right.grid(row=0, column=1, sticky="nsew")
        tk.Label(right, text="⚠️ Alertes de stock", font=self.font_header,
                 bg=self.CARD, fg=self.ORANGE).pack(anchor="w", pady=(0,10))

        if not alertes:
            tk.Label(right, text="✅ Aucune alerte", font=self.font_body,
                     bg=self.CARD, fg=self.GREEN).pack(pady=20)
        else:
            for p in alertes:
                row = tk.Frame(right, bg=self.PANEL, padx=10, pady=6)
                row.pack(fill="x", pady=2)
                color = self.RED if p["quantite"] == 0 else self.ORANGE
                tk.Label(row, text=p["nom"], font=self.font_body, bg=self.PANEL, fg=self.FG).pack(anchor="w")
                tk.Label(row, text=f"Qté: {p['quantite']}", font=self.font_small,
                         bg=self.PANEL, fg=color).pack(anchor="w")

    # ── Page: Produits ────────────────────────────────────────────────────────

    def _page_produits(self):
        self._header("📋 Gestion des produits", "Ajouter, modifier et supprimer des produits")

        # Toolbar
        toolbar = tk.Frame(self.main, bg=self.BG)
        toolbar.pack(fill="x", padx=28, pady=(4, 12))

        self._btn(toolbar, "➕ Nouveau produit", self._dialog_ajouter_produit, self.GREEN).pack(side="left", padx=(0,8))
        self._btn(toolbar, "✏️ Modifier",        self._modifier_produit, self.ACCENT).pack(side="left", padx=(0,8))
        self._btn(toolbar, "🗑️ Supprimer",       self._supprimer_produit, self.RED).pack(side="left")

        # Search
        search_var = tk.StringVar()
        search_var.trace("w", lambda *a: self._filter_produits(search_var.get()))
        search_frame = tk.Frame(toolbar, bg=self.BG)
        search_frame.pack(side="right")
        tk.Label(search_frame, text="🔍", bg=self.BG, fg=self.FG2, font=self.font_body).pack(side="left")
        entry = tk.Entry(search_frame, textvariable=search_var, bg=self.CARD, fg=self.FG,
                         insertbackground=self.FG, relief="flat", font=self.font_body, width=22)
        entry.pack(side="left", ipady=5, ipadx=8)

        # Table
        frame = tk.Frame(self.main, bg=self.BG)
        frame.pack(fill="both", expand=True, padx=28, pady=(0, 16))

        cols = ("Référence", "Nom", "Catégorie", "Quantité", "Prix unit.", "Valeur", "Seuil alerte", "Statut")
        self.tree_prod = ttk.Treeview(frame, columns=cols, show="headings", height=18)
        self._style_tree(self.tree_prod, cols, [100, 200, 130, 80, 90, 100, 100, 90])

        sb = ttk.Scrollbar(frame, orient="vertical", command=self.tree_prod.yview)
        self.tree_prod.configure(yscrollcommand=sb.set)
        self.tree_prod.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self._search_query = ""
        self._refresh_produits()

    def _filter_produits(self, query):
        self._search_query = query.lower()
        self._refresh_produits()

    def _refresh_produits(self):
        if not hasattr(self, "tree_prod"):
            return
        self.tree_prod.delete(*self.tree_prod.get_children())
        for p in self.data["produits"]:
            query = getattr(self, "_search_query", "")
            if query and query not in p["nom"].lower() and query not in p.get("ref","").lower():
                continue
            valeur = p.get("prix", 0) * p.get("quantite", 0)
            qte = p.get("quantite", 0)
            seuil = p.get("seuil_alerte", 5)
            if qte == 0:
                statut = "🔴 Rupture"
                tag = "rupture"
            elif qte <= seuil:
                statut = "🟡 Faible"
                tag = "faible"
            else:
                statut = "🟢 Normal"
                tag = "normal"
            self.tree_prod.insert("", "end", values=(
                p.get("ref", ""), p["nom"], p.get("categorie", ""),
                qte, f"{p.get('prix',0):.2f}", f"{valeur:.2f}", seuil, statut
            ), tags=(tag,))
        self.tree_prod.tag_configure("rupture", foreground=self.RED)
        self.tree_prod.tag_configure("faible",  foreground=self.ORANGE)
        self.tree_prod.tag_configure("normal",  foreground=self.GREEN)

    def _dialog_ajouter_produit(self, produit=None):
        win = self._dialog("Nouveau produit" if not produit else "Modifier produit", 420, 460)

        fields = {}
        labels = [
            ("Référence",      "ref",          produit.get("ref","")          if produit else ""),
            ("Nom du produit", "nom",          produit.get("nom","")          if produit else ""),
            ("Catégorie",      "categorie",    produit.get("categorie","")    if produit else ""),
            ("Quantité",       "quantite",     str(produit.get("quantite",0)) if produit else "0"),
            ("Prix unitaire",  "prix",         str(produit.get("prix",0))     if produit else "0"),
            ("Seuil alerte",   "seuil_alerte", str(produit.get("seuil_alerte",5)) if produit else "5"),
        ]

        for label, key, default in labels:
            tk.Label(win, text=label, font=self.font_body, bg=self.CARD, fg=self.FG2).pack(anchor="w", padx=24, pady=(10, 2))
            e = tk.Entry(win, font=self.font_body, bg=self.PANEL, fg=self.FG,
                         insertbackground=self.FG, relief="flat")
            e.insert(0, default)
            e.pack(fill="x", padx=24, ipady=6)
            fields[key] = e

        def save():
            try:
                p = {
                    "ref":          fields["ref"].get().strip(),
                    "nom":          fields["nom"].get().strip(),
                    "categorie":    fields["categorie"].get().strip(),
                    "quantite":     int(fields["quantite"].get()),
                    "prix":         float(fields["prix"].get()),
                    "seuil_alerte": int(fields["seuil_alerte"].get()),
                }
                if not p["nom"]:
                    messagebox.showerror("Erreur", "Le nom est obligatoire.", parent=win)
                    return
                if produit:
                    idx = self.data["produits"].index(produit)
                    self.data["produits"][idx] = p
                else:
                    self.data["produits"].append(p)
                save_data(self.data)
                win.destroy()
                self._refresh_produits()
            except ValueError:
                messagebox.showerror("Erreur", "Quantité, prix et seuil doivent être des nombres.", parent=win)

        btn_frame = tk.Frame(win, bg=self.CARD)
        btn_frame.pack(fill="x", padx=24, pady=20)
        self._btn(btn_frame, "💾 Enregistrer", save, self.GREEN).pack(side="right", padx=(8,0))
        self._btn(btn_frame, "Annuler", win.destroy, "#555").pack(side="right")

    def _modifier_produit(self):
        sel = self._selected_produit()
        if sel:
            self._dialog_ajouter_produit(produit=sel)

    def _supprimer_produit(self):
        sel = self._selected_produit()
        if sel and messagebox.askyesno("Confirmer", f"Supprimer « {sel['nom']} » ?"):
            self.data["produits"].remove(sel)
            save_data(self.data)
            self._refresh_produits()

    def _selected_produit(self):
        if not hasattr(self, "tree_prod"):
            return None
        sel = self.tree_prod.selection()
        if not sel:
            messagebox.showinfo("Info", "Veuillez sélectionner un produit.")
            return None
        ref = self.tree_prod.item(sel[0])["values"][0]
        nom = self.tree_prod.item(sel[0])["values"][1]
        for p in self.data["produits"]:
            if p["nom"] == nom and p.get("ref","") == str(ref):
                return p
        return None

    # ── Page: Mouvement (Entrée / Sortie) ─────────────────────────────────────

    def _page_mouvement(self, mode):
        label = "📥 Entrée de stock" if mode == "entree" else "📤 Sortie de stock"
        sub   = "Réceptionner des marchandises" if mode == "entree" else "Expédier ou consommer du stock"
        self._header(label, sub)

        card = tk.Frame(self.main, bg=self.CARD, padx=32, pady=28)
        card.pack(padx=60, pady=20, fill="x")

        # Product selector
        tk.Label(card, text="Produit", font=self.font_body, bg=self.CARD, fg=self.FG2).grid(row=0, column=0, sticky="w", pady=8)
        noms = [p["nom"] for p in self.data["produits"]]
        prod_var = tk.StringVar()
        combo = ttk.Combobox(card, textvariable=prod_var, values=noms, state="readonly",
                             font=self.font_body, width=30)
        combo.grid(row=0, column=1, sticky="w", padx=(16,0), pady=8)

        # Show current stock
        stock_lbl = tk.Label(card, text="", font=self.font_body, bg=self.CARD, fg=self.FG2)
        stock_lbl.grid(row=1, column=1, sticky="w", padx=(16,0))

        def on_select(e=None):
            nom = prod_var.get()
            p = next((x for x in self.data["produits"] if x["nom"] == nom), None)
            if p:
                color = self.GREEN if p["quantite"] > p.get("seuil_alerte",5) else self.ORANGE
                stock_lbl.configure(text=f"Stock actuel : {p['quantite']} unités", fg=color)
        combo.bind("<<ComboboxSelected>>", on_select)

        # Quantity
        tk.Label(card, text="Quantité", font=self.font_body, bg=self.CARD, fg=self.FG2).grid(row=2, column=0, sticky="w", pady=8)
        qte_var = tk.StringVar(value="1")
        tk.Entry(card, textvariable=qte_var, font=self.font_body, bg=self.PANEL, fg=self.FG,
                 insertbackground=self.FG, relief="flat", width=12).grid(row=2, column=1, sticky="w", padx=(16,0), ipady=6)

        # Note
        tk.Label(card, text="Note / Référence", font=self.font_body, bg=self.CARD, fg=self.FG2).grid(row=3, column=0, sticky="w", pady=8)
        note_var = tk.StringVar()
        tk.Entry(card, textvariable=note_var, font=self.font_body, bg=self.PANEL, fg=self.FG,
                 insertbackground=self.FG, relief="flat", width=30).grid(row=3, column=1, sticky="w", padx=(16,0), ipady=6)

        color_btn = self.GREEN if mode == "entree" else self.RED
        btn_text  = "✅ Valider l'entrée" if mode == "entree" else "✅ Valider la sortie"

        def valider():
            nom = prod_var.get()
            if not nom:
                messagebox.showwarning("Attention", "Choisissez un produit.")
                return
            try:
                qte = int(qte_var.get())
                if qte <= 0: raise ValueError
            except ValueError:
                messagebox.showerror("Erreur", "La quantité doit être un entier positif.")
                return

            p = next((x for x in self.data["produits"] if x["nom"] == nom), None)
            if mode == "sortie" and p["quantite"] < qte:
                messagebox.showerror("Erreur", f"Stock insuffisant ! Disponible : {p['quantite']}")
                return

            if mode == "entree":
                p["quantite"] += qte
            else:
                p["quantite"] -= qte

            self.data["mouvements"].append({
                "date":    datetime.now().strftime("%Y-%m-%d %H:%M"),
                "produit": nom,
                "type":    "entrée" if mode == "entree" else "sortie",
                "quantite":qte,
                "note":    note_var.get(),
            })
            save_data(self.data)
            messagebox.showinfo("Succès", f"Mouvement enregistré !\nNouveau stock : {p['quantite']}")
            prod_var.set("")
            qte_var.set("1")
            note_var.set("")
            stock_lbl.configure(text="")

        self._btn(card, btn_text, valider, color_btn).grid(row=4, column=1, sticky="w", padx=(16,0), pady=20)

    # ── Page: Historique ──────────────────────────────────────────────────────

    def _page_historique(self):
        self._header("📊 Historique des mouvements", "Suivi de toutes les entrées et sorties")

        toolbar = tk.Frame(self.main, bg=self.BG)
        toolbar.pack(fill="x", padx=28, pady=(4, 10))

        def effacer():
            if messagebox.askyesno("Confirmer", "Effacer tout l'historique ?"):
                self.data["mouvements"] = []
                save_data(self.data)
                self._page_historique()

        self._btn(toolbar, "🗑️ Effacer historique", effacer, self.RED).pack(side="right")

        # Filter
        filter_var = tk.StringVar(value="Tous")
        for val in ["Tous", "Entrées", "Sorties"]:
            tk.Radiobutton(toolbar, text=val, variable=filter_var, value=val,
                           bg=self.BG, fg=self.FG, selectcolor=self.CARD,
                           activebackground=self.BG, font=self.font_body,
                           command=lambda: self._refresh_historique(filter_var.get())
                           ).pack(side="left", padx=6)

        frame = tk.Frame(self.main, bg=self.BG)
        frame.pack(fill="both", expand=True, padx=28, pady=(0, 16))

        cols = ("Date", "Produit", "Type", "Quantité", "Note")
        self.tree_hist = ttk.Treeview(frame, columns=cols, show="headings", height=18)
        self._style_tree(self.tree_hist, cols, [150, 240, 80, 80, 280])

        sb = ttk.Scrollbar(frame, orient="vertical", command=self.tree_hist.yview)
        self.tree_hist.configure(yscrollcommand=sb.set)
        self.tree_hist.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self._refresh_historique("Tous")

    def _refresh_historique(self, filtre):
        if not hasattr(self, "tree_hist"):
            return
        self.tree_hist.delete(*self.tree_hist.get_children())
        for m in reversed(self.data["mouvements"]):
            if filtre == "Entrées" and m["type"] != "entrée":
                continue
            if filtre == "Sorties" and m["type"] != "sortie":
                continue
            tag = "entree" if m["type"] == "entrée" else "sortie"
            self.tree_hist.insert("", "end", values=(
                m["date"], m["produit"], m["type"], m["quantite"], m.get("note","")
            ), tags=(tag,))
        self.tree_hist.tag_configure("entree", foreground=self.GREEN)
        self.tree_hist.tag_configure("sortie", foreground=self.RED)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _header(self, title, subtitle=""):
        frame = tk.Frame(self.main, bg=self.BG)
        frame.pack(fill="x", padx=28, pady=(22, 8))
        tk.Label(frame, text=title, font=self.font_title, bg=self.BG, fg=self.FG).pack(anchor="w")
        if subtitle:
            tk.Label(frame, text=subtitle, font=self.font_body, bg=self.BG, fg=self.FG2).pack(anchor="w")

    def _btn(self, parent, text, cmd, color):
        return tk.Button(parent, text=text, command=cmd, font=self.font_body,
                         bg=color, fg="white", relief="flat", cursor="hand2",
                         padx=14, pady=7, activebackground=color)

    def _dialog(self, title, w=400, h=400):
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry(f"{w}x{h}")
        win.configure(bg=self.CARD)
        win.grab_set()
        tk.Label(win, text=title, font=self.font_header, bg=self.CARD, fg=self.FG).pack(pady=(20,4))
        ttk.Separator(win, orient="horizontal").pack(fill="x", padx=24, pady=8)
        return win

    def _style_tree(self, tree, cols, widths):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
            background=self.PANEL, fieldbackground=self.PANEL, foreground=self.FG,
            rowheight=32, font=("Segoe UI", 10), borderwidth=0)
        style.configure("Treeview.Heading",
            background=self.CARD, foreground=self.ACCENT, font=("Segoe UI", 10, "bold"),
            relief="flat")
        style.map("Treeview", background=[("selected", self.BORDER)])
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, minwidth=50)


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = GestionStock()
    app.mainloop()