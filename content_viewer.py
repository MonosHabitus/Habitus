#!/usr/bin/env python3
"""
Visionneur de contenu — Habitus v2.0
Supporte : Wikipedia, YouTube, Web, Articles, Livres, PDF
Fonctions : surlignage persistant avec notes, taille de police variable
"""
import tkinter as tk
from tkinter import ttk, simpledialog, colorchooser
import threading, re, urllib.request, urllib.parse, json
import html as html_module, sys, os

APP_DIR = os.path.dirname(os.path.abspath(__file__))

C = {
    "bg":"#12141a","bg2":"#181b23","panel":"#1e2130","panel2":"#252840",
    "border":"#2a2e45","border2":"#3a3f60","accent":"#5b7fff","accent2":"#3a5acc",
    "green":"#3dd68c","amber":"#f5a623","red":"#e05252","cyan":"#36c8d4",
    "purple":"#a07ae0","text":"#dde1f0","text2":"#7a8099","text3":"#3d4260",
    "white":"#f0f2ff",
    # Couleurs de surlignage
    "hl_yellow": "#f5e642", "hl_green":  "#42f584",
    "hl_cyan":   "#42d4f5", "hl_pink":   "#f542a7",
    "hl_orange": "#f5a623",
}

FM  = "Courier New"
_pf = sys.platform
F   = ("Segoe UI",10)       if _pf=="win32" else ("SF Pro Text",10)       if _pf=="darwin" else ("DejaVu Sans",10)
FS  = ("Segoe UI",9)        if _pf=="win32" else ("SF Pro Text",9)        if _pf=="darwin" else ("DejaVu Sans",9)
FB  = ("Segoe UI",10,"bold") if _pf=="win32" else ("SF Pro Text",10,"bold") if _pf=="darwin" else ("DejaVu Sans",10,"bold")
FLB = ("Segoe UI",13,"bold") if _pf=="win32" else ("SF Pro Text",13,"bold") if _pf=="darwin" else ("DejaVu Sans",13,"bold")

TYPE_LABEL = {"wikipedia":"Wikipedia","video":"Vidéo","article":"Article",
              "book":"Livre","web":"Page web","pdf":"PDF","custom":"Lien"}
TYPE_COLOR = {
    "wikipedia":C["green"],"video":C["cyan"],"article":C["amber"],
    "book":C["purple"],"web":C["accent"],"pdf":C["red"],"custom":C["text2"],
}

HIGHLIGHT_COLORS = [
    ("#f5e64280", "Jaune"),
    ("#42f58480", "Vert"),
    ("#42d4f580", "Cyan"),
    ("#f542a780", "Rose"),
    ("#f5a62380", "Orange"),
]

try:
    import tkinterweb
    HAS_WEBVIEW = True
except ImportError:
    HAS_WEBVIEW = False


# ══════════════════════════════════════════════════════════════════
# CONTENT VIEWER
# ══════════════════════════════════════════════════════════════════

class ContentViewer(tk.Toplevel):
    def __init__(self, parent, resource, db=None):
        super().__init__(parent)
        self.resource = resource
        self.db       = db
        self.title(resource["title"])
        self.configure(bg=C["bg"])
        self.geometry("1140x780")
        self.minsize(800,560)
        self._hl_tag_counter = 0  # compteur pour noms de tags uniques
        self._build()
        self._load_content()

    # ═══════════════════════════════════════════════════════════════
    # BUILD
    # ═══════════════════════════════════════════════════════════════

    def _build(self):
        r     = self.resource
        rtype = r.get("type","custom")
        color = TYPE_COLOR.get(rtype, C["text2"])
        label = TYPE_LABEL.get(rtype, rtype)
        url   = r.get("url","")

        # ── Header ─────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=C["panel"])
        hdr.pack(fill="x")
        tk.Label(hdr, text=label.upper(), font=(FM,8,"bold"),
                 fg=color, bg=C["panel"]).pack(side="left", padx=14, pady=11)
        tk.Label(hdr, text=r["title"], font=FLB,
                 fg=C["white"], bg=C["panel"]).pack(side="left", padx=4)

        def copy_url():
            self.clipboard_clear(); self.clipboard_append(url)
        lnk = tk.Label(hdr, text="Copier lien", font=FS, fg=C["text3"],
                        bg=C["panel"], cursor="hand2")
        lnk.pack(side="right", padx=14, pady=11)
        lnk.bind("<Button-1>", lambda e: copy_url())
        lnk.bind("<Enter>", lambda e: lnk.config(fg=C["accent"]))
        lnk.bind("<Leave>", lambda e: lnk.config(fg=C["text3"]))

        tk.Label(hdr, text=url[:55]+("…" if len(url)>55 else ""),
                 font=(FM,7), fg=C["text3"], bg=C["panel"]).pack(side="right", padx=4)

        tk.Frame(self, bg=C["border"], height=1).pack(fill="x")

        # ── Barre d'outils ─────────────────────────────────────────
        self._toolbar = tk.Frame(self, bg=C["bg2"])
        self._toolbar.pack(fill="x")

        self.status_lbl = tk.Label(self._toolbar, text="Chargement…",
                                    font=FS, fg=C["amber"], bg=C["bg2"])
        self.status_lbl.pack(side="left", padx=14, pady=6)

        # Contrôles taille police (droite)
        tk.Label(self._toolbar, text="Police :", font=FS,
                 fg=C["text3"], bg=C["bg2"]).pack(side="right", padx=(0,6), pady=6)
        self._font_size = tk.IntVar(value=14)
        for sz, lbl in [(10,"S"),(12,"M"),(14,"L"),(16,"XL"),(18,"XXL")]:
            rb = tk.Radiobutton(self._toolbar, text=lbl, variable=self._font_size,
                                value=sz, command=self._update_font,
                                font=FS, fg=C["text3"], bg=C["bg2"],
                                selectcolor=C["panel2"], activebackground=C["bg2"])
            rb.pack(side="right", padx=1)

        # Barre de surlignage (visible pour vues texte uniquement)
        self._hl_bar = tk.Frame(self, bg=C["bg2"])
        # packée conditionnellement après

        tk.Frame(self, bg=C["border"], height=1).pack(fill="x")

        # ── Contenu ────────────────────────────────────────────────
        content = tk.Frame(self, bg=C["bg"])
        content.pack(fill="both", expand=True)

        rtype = r.get("type","custom")
        if rtype == "video":
            self._build_video(content)
        elif rtype == "web":
            self._build_web(content)
        elif rtype == "pdf":
            self._build_pdf(content)
        else:
            self._build_text(content)
            self._build_hl_bar()

        # Note ressource
        if r.get("notes"):
            nf = tk.Frame(self, bg=C["panel"])
            nf.pack(fill="x", side="bottom")
            tk.Frame(self, bg=C["border"], height=1).pack(fill="x", side="bottom")
            tk.Label(nf, text=f"Note : {r['notes']}", font=FS,
                     fg=C["text3"], bg=C["panel"], anchor="w").pack(
                     fill="x", padx=14, pady=7)

    # ── Barre de surlignage ───────────────────────────────────────

    def _build_hl_bar(self):
        """Barre d'outils surlignage — insérée dans le toolbar."""
        sep = tk.Frame(self._toolbar, bg=C["border2"], width=1)
        sep.pack(side="left", fill="y", padx=8, pady=4)

        tk.Label(self._toolbar, text="Surligner :", font=FS,
                 fg=C["text3"], bg=C["bg2"]).pack(side="left", pady=6)

        self._hl_color = HIGHLIGHT_COLORS[0][0]
        self._hl_btns  = {}

        for color_hex, color_name in HIGHLIGHT_COLORS:
            solid = color_hex[:7]  # sans alpha
            b = tk.Label(self._toolbar, text="  ", bg=solid, width=2,
                         cursor="hand2", relief="flat",
                         highlightthickness=2,
                         highlightbackground=C["white"] if color_hex==self._hl_color else solid)
            b.pack(side="left", padx=2, pady=6)
            b.bind("<Button-1>", lambda e, c=color_hex, btn=b: self._pick_hl_color(c))
            self._hl_btns[color_hex] = b

        # Bouton "Surligner la sélection"
        sep2 = tk.Frame(self._toolbar, bg=C["border2"], width=1)
        sep2.pack(side="left", fill="y", padx=8, pady=4)

        apply_btn = tk.Label(self._toolbar, text="Appliquer", font=FS,
                              fg=C["accent"], bg=C["bg2"], cursor="hand2", pady=6, padx=6)
        apply_btn.pack(side="left")
        apply_btn.bind("<Button-1>", lambda e: self._apply_highlight())
        apply_btn.bind("<Enter>", lambda e: apply_btn.config(fg=C["white"]))
        apply_btn.bind("<Leave>", lambda e: apply_btn.config(fg=C["accent"]))

        clear_btn = tk.Label(self._toolbar, text="Effacer", font=FS,
                              fg=C["text3"], bg=C["bg2"], cursor="hand2", pady=6, padx=6)
        clear_btn.pack(side="left")
        clear_btn.bind("<Button-1>", lambda e: self._remove_highlight_at_cursor())
        clear_btn.bind("<Enter>", lambda e: clear_btn.config(fg=C["red"]))
        clear_btn.bind("<Leave>", lambda e: clear_btn.config(fg=C["text3"]))

    def _pick_hl_color(self, color_hex):
        self._hl_color = color_hex
        for c, btn in self._hl_btns.items():
            solid = c[:7]
            btn.config(highlightbackground=C["white"] if c==color_hex else solid)

    # ── VUE TEXTE ─────────────────────────────────────────────────

    def _build_text(self, parent):
        sb = tk.Scrollbar(parent, width=6, bg=C["bg2"],
                          troughcolor=C["panel"], relief="flat")
        sb.pack(side="right", fill="y")
        self.text_w = tk.Text(
            parent, font=(FM, self._font_size.get()),
            bg=C["bg"], fg=C["text"],
            insertbackground=C["accent"],
            selectbackground=C["accent2"],
            selectforeground=C["white"],
            bd=0, highlightthickness=0,
            padx=32, pady=22, wrap="word",
            state="disabled",
            yscrollcommand=sb.set)
        self.text_w.pack(fill="both", expand=True)
        sb.config(command=self.text_w.yview)
        # Tags de mise en forme
        self.text_w.tag_configure("title", font=(FM,22,"bold"), foreground=C["white"])
        self.text_w.tag_configure("h2",    font=(FM,17,"bold"), foreground=C["accent"])
        self.text_w.tag_configure("h3",    font=(FM,15,"bold"), foreground=C["cyan"])
        self.text_w.tag_configure("body",  font=(FM,14),        foreground=C["text"])
        self.text_w.tag_configure("dim",   font=(FM,12),        foreground=C["text3"])
        self.text_w.tag_configure("sep",   font=(FM,11),        foreground=C["border2"])
        self.text_w.tag_configure("error", font=(FM,14),        foreground=C["red"])
        # Clic droit → menu contextuel
        self.text_w.bind("<Button-3>", self._ctx_menu)

    def _update_font(self):
        if hasattr(self, "text_w"):
            sz = self._font_size.get()
            self.text_w.config(font=(FM, sz))
            # Mettre à jour les tags de taille relative
            self.text_w.tag_configure("title", font=(FM, sz+8, "bold"))
            self.text_w.tag_configure("h2",    font=(FM, sz+3, "bold"))
            self.text_w.tag_configure("h3",    font=(FM, sz+1, "bold"))
            self.text_w.tag_configure("body",  font=(FM, sz))
            self.text_w.tag_configure("dim",   font=(FM, sz-1))

    # ── SURLIGNAGE ────────────────────────────────────────────────

    def _apply_highlight(self):
        """Surligne la sélection courante et la sauvegarde en DB."""
        try:
            start = self.text_w.index("sel.first")
            end   = self.text_w.index("sel.last")
        except tk.TclError:
            return  # pas de sélection

        color  = self._hl_color
        solid  = color[:7]
        tag_id = f"hl_{self._hl_tag_counter}"
        self._hl_tag_counter += 1

        self.text_w.tag_configure(tag_id,
                                   background=solid,
                                   foreground="#000000")
        self.text_w.tag_add(tag_id, start, end)
        self.text_w.tag_bind(tag_id, "<Button-1>",
                              lambda e, tid=tag_id: self._show_hl_popup(e, tid))

        # Sauvegarder en DB
        if self.db:
            hid = self.db.add_highlight(
                self.resource["id"], start, end, color, note=None)
            # Stocker l'id DB dans le nom du tag pour retrouver plus tard
            self.text_w.tag_configure(tag_id, background=solid)
            self._tag_to_hid = getattr(self, "_tag_to_hid", {})
            self._tag_to_hid[tag_id] = hid

    def _restore_highlights(self):
        """Recharge les surlignages sauvegardés depuis la DB."""
        if not self.db: return
        self._tag_to_hid = {}
        highlights = self.db.get_highlights(self.resource["id"])
        for hl in highlights:
            try:
                tag_id = f"hl_{self._hl_tag_counter}"
                self._hl_tag_counter += 1
                solid  = hl["color"][:7]
                self.text_w.tag_configure(tag_id,
                                           background=solid,
                                           foreground="#000000")
                self.text_w.tag_add(tag_id, hl["start_idx"], hl["end_idx"])
                self.text_w.tag_bind(tag_id, "<Button-1>",
                                      lambda e, tid=tag_id: self._show_hl_popup(e, tid))
                self._tag_to_hid[tag_id] = hl["id"]
            except Exception:
                pass  # index invalide (contenu modifié)

    def _show_hl_popup(self, event, tag_id):
        """Popup au clic sur un surlignage : affiche/édite la note."""
        hid = getattr(self, "_tag_to_hid", {}).get(tag_id)
        if hid is None: return

        # Lire la note actuelle
        highlights = self.db.get_highlights(self.resource["id"]) if self.db else []
        current_note = ""
        for hl in highlights:
            if hl["id"] == hid:
                current_note = hl.get("note") or ""; break

        popup = tk.Toplevel(self)
        popup.title("Note de surlignage")
        popup.configure(bg=C["panel"])
        popup.geometry("320x200")
        popup.resizable(False, False)
        popup.transient(self)
        # Positionner près du clic
        popup.geometry(f"+{event.x_root+10}+{event.y_root+10}")

        tk.Label(popup, text="Note", font=FB, fg=C["white"],
                 bg=C["panel"]).pack(anchor="w", padx=14, pady=(12,4))
        txt = tk.Text(popup, font=F, bg=C["panel2"], fg=C["text"],
                      insertbackground=C["accent"], relief="flat",
                      bd=0, highlightthickness=1, highlightbackground=C["border2"],
                      height=4)
        txt.pack(fill="x", padx=14, pady=(0,8))
        if current_note: txt.insert("1.0", current_note)

        def save_note():
            note = txt.get("1.0","end-1c").strip()
            if self.db: self.db.update_highlight_note(hid, note or None)
            popup.destroy()

        def delete_hl():
            if self.db: self.db.delete_highlight(hid)
            self.text_w.tag_delete(tag_id)
            if tag_id in getattr(self,"_tag_to_hid",{}):
                del self._tag_to_hid[tag_id]
            popup.destroy()

        btn_row = tk.Frame(popup, bg=C["panel"])
        btn_row.pack(fill="x", padx=14, pady=(0,12))
        tk.Button(btn_row, text="Supprimer", command=delete_hl,
                  font=FS, fg=C["white"], bg="#7a1a1a",
                  activeforeground=C["white"], activebackground=C["red"],
                  relief="flat", bd=0, padx=10, pady=5,
                  cursor="hand2").pack(side="left")
        tk.Button(btn_row, text="Enregistrer", command=save_note,
                  font=FS, fg=C["white"], bg=C["accent2"],
                  activeforeground=C["white"], activebackground=C["accent"],
                  relief="flat", bd=0, padx=10, pady=5,
                  cursor="hand2").pack(side="right")

    def _remove_highlight_at_cursor(self):
        """Supprime le surlignage sous le curseur de la souris."""
        try:
            idx = self.text_w.index("current")
        except Exception:
            return
        for tag in self.text_w.tag_names(idx):
            if tag.startswith("hl_"):
                hid = getattr(self,"_tag_to_hid",{}).get(tag)
                if hid and self.db: self.db.delete_highlight(hid)
                self.text_w.tag_delete(tag)
                if tag in getattr(self,"_tag_to_hid",{}):
                    del self._tag_to_hid[tag]
                break

    def _ctx_menu(self, event):
        """Menu contextuel clic droit."""
        menu = tk.Menu(self, tearoff=0, bg=C["panel"], fg=C["text"],
                       activebackground=C["sel"], activeforeground=C["accent"],
                       font=FS)
        menu.add_command(label="Surligner la sélection",
                         command=self._apply_highlight)
        menu.add_separator()
        for color_hex, color_name in HIGHLIGHT_COLORS:
            def pick_and_apply(c=color_hex):
                self._hl_color = c; self._apply_highlight()
            menu.add_command(label=f"  Surligner en {color_name}", command=pick_and_apply)
        menu.add_separator()
        menu.add_command(label="Effacer surlignage ici",
                         command=self._remove_highlight_at_cursor)
        menu.post(event.x_root, event.y_root)

    # ── VUE PDF ───────────────────────────────────────────────────

    def _build_pdf(self, parent):
        """Visionneuse PDF avec défilement page par page via PyMuPDF."""
        try:
            import fitz  # PyMuPDF
            self._pdf_available = True
        except ImportError:
            self._pdf_available = False

        if not self._pdf_available:
            self._build_text(parent)
            self._build_hl_bar()
            self.after(100, lambda: self._show_error(
                "PyMuPDF non installé.\n\npip install pymupdf\n\n"
                "Pour afficher les PDF, installez ce module."))
            return

        # Barre de navigation PDF
        nav = tk.Frame(parent, bg=C["bg2"])
        nav.pack(fill="x")
        tk.Frame(parent, bg=C["border"], height=1).pack(fill="x") # already packed after

        self._pdf_page = 0
        self._pdf_doc  = None

        def nav_btn(txt, cmd):
            b = tk.Label(nav, text=txt, font=FS, fg=C["text2"],
                         bg=C["bg2"], cursor="hand2", padx=10, pady=6)
            b.pack(side="left")
            b.bind("<Button-1>", lambda e: cmd())
            b.bind("<Enter>", lambda e: b.config(fg=C["accent"]))
            b.bind("<Leave>", lambda e: b.config(fg=C["text2"]))

        nav_btn("◀ Préc.", self._pdf_prev)
        self._pdf_page_lbl = tk.Label(nav, text="Page — / —", font=FM_,
                                       fg=C["text2"], bg=C["bg2"])
        self._pdf_page_lbl = tk.Label(nav, text="Page — / —", font=(FM,9),
                                       fg=C["text2"], bg=C["bg2"])
        self._pdf_page_lbl.pack(side="left", padx=8)
        nav_btn("Suiv. ▶", self._pdf_next)

        # Zoom
        tk.Label(nav, text="Zoom :", font=FS, fg=C["text3"],
                 bg=C["bg2"]).pack(side="right", padx=(0,4))
        self._pdf_zoom = tk.DoubleVar(value=1.2)
        for z, lbl in [(0.8,"80%"),(1.0,"100%"),(1.2,"120%"),(1.5,"150%"),(2.0,"200%")]:
            tk.Radiobutton(nav, text=lbl, variable=self._pdf_zoom, value=z,
                           command=self._pdf_render_current,
                           font=FS, fg=C["text3"], bg=C["bg2"],
                           selectcolor=C["panel2"],
                           activebackground=C["bg2"]).pack(side="right", padx=1)

        # Canvas de rendu
        cv_wrap = tk.Frame(parent, bg=C["bg"])
        cv_wrap.pack(fill="both", expand=True)
        vsb = tk.Scrollbar(cv_wrap, width=6, bg=C["bg2"],
                           troughcolor=C["panel"], relief="flat")
        vsb.pack(side="right", fill="y")
        hsb = tk.Scrollbar(cv_wrap, orient="horizontal", width=6,
                           bg=C["bg2"], troughcolor=C["panel"], relief="flat")
        hsb.pack(side="bottom", fill="x")

        self._pdf_canvas = tk.Canvas(cv_wrap, bg=C["bg"], highlightthickness=0,
                                      yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self._pdf_canvas.pack(fill="both", expand=True)
        vsb.config(command=self._pdf_canvas.yview)
        hsb.config(command=self._pdf_canvas.xview)
        self._pdf_canvas.bind("<MouseWheel>",
            lambda e: self._pdf_canvas.yview_scroll(int(-1*(e.delta/120)),"units"))

    def _pdf_prev(self):
        if self._pdf_doc and self._pdf_page > 0:
            self._pdf_page -= 1; self._pdf_render_current()

    def _pdf_next(self):
        if self._pdf_doc and self._pdf_page < len(self._pdf_doc)-1:
            self._pdf_page += 1; self._pdf_render_current()

    def _pdf_render_current(self):
        if not self._pdf_doc: return
        import fitz
        from PIL import Image, ImageTk
        page  = self._pdf_doc[self._pdf_page]
        zoom  = self._pdf_zoom.get()
        mat   = fitz.Matrix(zoom, zoom)
        pix   = page.get_pixmap(matrix=mat, alpha=False)
        img   = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self._pdf_photo = ImageTk.PhotoImage(img)
        cv = self._pdf_canvas
        cv.delete("all")
        cv.create_image(0, 0, anchor="nw", image=self._pdf_photo)
        cv.configure(scrollregion=(0, 0, pix.width, pix.height))
        total = len(self._pdf_doc)
        self._pdf_page_lbl.config(text=f"Page {self._pdf_page+1} / {total}")

    # ── VUE VIDÉO YOUTUBE ─────────────────────────────────────────

    def _build_video(self, parent):
        url = self.resource.get("url","")
        left = tk.Frame(parent, bg=C["bg2"], width=320)
        left.pack(side="left", fill="y"); left.pack_propagate(False)
        tk.Frame(parent, bg=C["border"], width=1).pack(side="left", fill="y")

        tk.Label(left, text="VIDÉO YOUTUBE", font=(FM,8,"bold"),
                 fg=C["text3"], bg=C["bg2"]).pack(anchor="w", padx=16, pady=(16,6))
        self.vid_info_lbl = tk.Label(left, text="Chargement…", font=FS,
                                      fg=C["text2"], bg=C["bg2"],
                                      justify="left", anchor="nw", wraplength=285)
        self.vid_info_lbl.pack(fill="x", padx=16, pady=(0,10))

        def open_browser():
            import webbrowser; webbrowser.open(url)

        btn_f = tk.Frame(left, bg=C["bg2"]); btn_f.pack(fill="x", padx=16, pady=(0,12))
        ob = tk.Button(btn_f, text="▶  Ouvrir dans le navigateur", command=open_browser,
                       font=FS, fg=C["white"], bg=C["accent2"],
                       activeforeground=C["white"], activebackground=C["accent"],
                       relief="flat", bd=0, padx=14, pady=8, cursor="hand2",
                       highlightthickness=0)
        ob.pack(fill="x")
        ob.bind("<Enter>", lambda e: ob.config(bg=C["accent"]))
        ob.bind("<Leave>", lambda e: ob.config(bg=C["accent2"]))

        tk.Frame(left, bg=C["border"], height=1).pack(fill="x", padx=8, pady=(0,10))
        tk.Label(left, text="TRANSCRIPT", font=(FM,8,"bold"),
                 fg=C["text3"], bg=C["bg2"]).pack(anchor="w", padx=16, pady=(0,6))
        tsb = tk.Scrollbar(left, width=4, bg=C["bg2"],
                           troughcolor=C["panel"], relief="flat")
        tsb.pack(side="right", fill="y")
        self.transcript_w = tk.Text(left, font=(FM,8), bg=C["bg2"], fg=C["text"],
                                     bd=0, highlightthickness=0, padx=16, pady=4,
                                     wrap="word", state="disabled", yscrollcommand=tsb.set)
        self.transcript_w.pack(fill="both", expand=True)
        tsb.config(command=self.transcript_w.yview)

        right = tk.Frame(parent, bg=C["bg"]); right.pack(side="left", fill="both", expand=True)
        self._thumb_canvas = tk.Canvas(right, bg=C["panel"], highlightthickness=0)
        self._thumb_canvas.pack(fill="both", expand=True, padx=16, pady=16)
        self._thumb_canvas.bind("<Configure>", self._draw_video_placeholder)
        self._has_player = False

    def _draw_video_placeholder(self, event=None):
        cv = self._thumb_canvas; cv.delete("all")
        w = cv.winfo_width(); h = cv.winfo_height()
        if w < 4 or h < 4: return
        cv.create_rectangle(0,0,w,h, fill=C["panel"], outline="")
        cv.create_text(w//2, h//2-20, text="▶", font=("DejaVu Sans",48),
                       fill=C["text3"], anchor="center")
        cv.create_text(w//2, h//2+30, text="Ouvrez la vidéo dans le navigateur",
                       font=FS, fill=C["text3"], anchor="center")

    # ── VUE WEB ───────────────────────────────────────────────────

    def _build_web(self, parent):
        if HAS_WEBVIEW:
            nav = tk.Frame(parent, bg=C["bg2"]); nav.pack(fill="x")
            self._url_var = tk.StringVar(value=self.resource.get("url",""))
            ue = tk.Entry(nav, textvariable=self._url_var, font=FS,
                          bg=C["panel2"], fg=C["text"], insertbackground=C["accent"],
                          relief="flat", bd=0, highlightthickness=1,
                          highlightbackground=C["border2"], highlightcolor=C["accent"])
            ue.pack(side="left", fill="x", expand=True, padx=10, pady=7, ipady=5)
            ue.bind("<Return>", lambda e: self._navigate(self._url_var.get()))
            for txt, cmd in [("◀",lambda: self._web_go("back")),
                              ("▶",lambda: self._web_go("forward")),
                              ("↺",lambda: self._navigate(self._url_var.get()))]:
                b = tk.Label(nav, text=txt, font=F, fg=C["text2"],
                             bg=C["bg2"], cursor="hand2", padx=8, pady=6)
                b.pack(side="left", padx=2)
                b.bind("<Button-1>", lambda e,c=cmd: c())
                b.bind("<Enter>", lambda e: e.widget.config(fg=C["accent"]))
                b.bind("<Leave>", lambda e: e.widget.config(fg=C["text2"]))
            tk.Frame(parent, bg=C["border"], height=1).pack(fill="x")
            self._webview = tkinterweb.HtmlFrame(parent, messages_enabled=False)
            self._webview.pack(fill="both", expand=True)
            self._has_player = True
        else:
            self._build_text(parent); self._build_hl_bar()
            self._has_player = False

    def _navigate(self, url):
        if not url.startswith("http"): url = "https://"+url
        self._url_var.set(url); self._webview.load_url(url)

    def _web_go(self, d):
        try:
            if d=="back": self._webview.go_back()
            else:         self._webview.go_forward()
        except Exception: pass

    # ═══════════════════════════════════════════════════════════════
    # CHARGEMENT
    # ═══════════════════════════════════════════════════════════════

    def _load_content(self):
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        r = self.resource; rtype = r.get("type","custom"); url = r.get("url","")
        try:
            if rtype=="wikipedia":  self._fetch_wikipedia(url)
            elif rtype=="video":    self._fetch_youtube(url)
            elif rtype=="web":      self._fetch_web_url(url)
            elif rtype=="article":  self._fetch_article(url)
            elif rtype=="book":     self._fetch_book(url)
            elif rtype=="pdf":      self._fetch_pdf(url)
            else:                   self._fetch_generic(url)
        except Exception as e:
            self._show_error(f"Erreur :\n{e}")

    # ── Wikipedia ─────────────────────────────────────────────────

    def _fetch_wikipedia(self, url):
        self._set_status("Requête Wikipedia…")
        title = re.search(r'wikipedia\.org/wiki/(.+)', url)
        if not title: self._show_error(f"URL Wikipedia invalide :\n{url}"); return
        title = urllib.parse.unquote(title.group(1).split("&")[0].split("#")[0])
        lang  = (re.search(r'(\w+)\.wikipedia', url) or type('x',(object,),{'group':lambda s,n:"fr"})).group(1)
        api   = (f"https://{lang}.wikipedia.org/w/api.php?action=query&prop=extracts"
                 f"&exlimit=1&titles={urllib.parse.quote(title)}&format=json"
                 f"&explaintext=1&exsectionformat=wiki")
        req = urllib.request.Request(api, headers={"User-Agent":"Habitus/2.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        pages   = data.get("query",{}).get("pages",{})
        page    = next(iter(pages.values()))
        extract = page.get("extract","")
        if not extract: self._show_error("Aucun contenu Wikipedia."); return
        self._set_status("Contenu chargé.")
        self.after(0, lambda: self._render_wiki(page.get("title",""), extract))

    def _render_wiki(self, title, text):
        self._render_text_content(title, text, mode="wiki")

    # ── YouTube ───────────────────────────────────────────────────

    def _fetch_youtube(self, url):
        self._set_status("Analyse YouTube…")
        m = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})', url)
        if not m: self._show_error(f"URL YouTube invalide :\n{url}"); return
        vid_id = m.group(1)
        try:
            oe = f"https://www.youtube.com/oembed?url={urllib.parse.quote(url)}&format=json"
            req = urllib.request.Request(oe, headers={"User-Agent":"Habitus/2.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                info = json.loads(resp.read().decode())
            info_text = f"Titre :\n{info.get('title','—')}\n\nChaîne :\n{info.get('author_name','—')}\n\nID : {vid_id}"
        except Exception:
            info_text = f"ID : {vid_id}\nURL : {url}"
        self.after(0, lambda: self.vid_info_lbl.config(text=info_text))
        self._set_status("Chargement transcript…")
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            try:    tr = YouTubeTranscriptApi.get_transcript(vid_id, languages=["fr","en","fr-FR","en-US"])
            except: tr = YouTubeTranscriptApi.get_transcript(vid_id)
            lines = []
            for e in tr:
                t=int(e.get("start",0)); mn,sc=divmod(t,60)
                lines.append(f"[{mn:02d}:{sc:02d}]  {e.get('text','')}")
            txt = "\n".join(lines)
            self.after(0, lambda: self._render_transcript(txt))
            self._set_status("Transcript chargé.")
        except ImportError:
            self.after(0, lambda: self._render_transcript("pip install youtube-transcript-api"))
            self._set_status("Module manquant.")
        except Exception as ex:
            self.after(0, lambda: self._render_transcript(f"Transcript indisponible.\n{str(ex)[:200]}"))
            self._set_status("Transcript indisponible.")

    def _render_transcript(self, text):
        w=self.transcript_w; w.config(state="normal"); w.delete("1.0","end")
        w.insert("end",text); w.config(state="disabled")

    # ── Web ───────────────────────────────────────────────────────

    def _fetch_web_url(self, url):
        if self._has_player:
            self.after(0, lambda: self._webview.load_url(url))
            self._set_status("Navigation…")
        else:
            self._fetch_generic(url)

    # ── Article ───────────────────────────────────────────────────

    def _fetch_article(self, url):
        self._set_status("Téléchargement…")
        if "arxiv.org" in url:
            m = re.search(r'arxiv\.org/(?:abs|pdf)/([0-9.]+(?:v\d+)?)', url)
            if m:
                req = urllib.request.Request(f"https://export.arxiv.org/abs/{m.group(1)}",
                                              headers={"User-Agent":"Habitus/2.0"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    raw = resp.read().decode("utf-8",errors="replace")
                text = self._html_to_text(raw)
                self._set_status("Chargé.")
                self.after(0, lambda: self._render_plain(f"[arXiv:{m.group(1)}]\n\n{text}","ARTICLE ARXIV"))
                return
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8",errors="replace")
        text = self._html_to_text(raw)
        self._set_status("Chargé.")
        self.after(0, lambda: self._render_plain(text, "ARTICLE"))

    def _fetch_book(self, url):
        self._set_status("Chargement…")
        req = urllib.request.Request(url, headers={"User-Agent":"Habitus/2.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8",errors="replace")
        text = self._html_to_text(raw)
        self._set_status("Chargé.")
        self.after(0, lambda: self._render_plain(text, "EXTRAIT DE LIVRE"))

    def _fetch_generic(self, url):
        self._set_status("Chargement…")
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"Habitus/2.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8",errors="replace")
            text = self._html_to_text(raw)
            self._set_status("Chargé.")
            self.after(0, lambda: self._render_plain(text, "CONTENU WEB"))
        except Exception as e:
            self._show_error(f"Erreur :\n{e}\n\nURL : {url}")

    # ── PDF ───────────────────────────────────────────────────────

    def _fetch_pdf(self, url):
        self._set_status("Chargement PDF…")
        import fitz
        try:
            # Fichier local
            if os.path.exists(url):
                doc = fitz.open(url)
            else:
                # Télécharger
                req = urllib.request.Request(url, headers={"User-Agent":"Habitus/2.0"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = resp.read()
                doc = fitz.open(stream=data, filetype="pdf")
            self._pdf_doc = doc
            self._set_status(f"PDF chargé — {len(doc)} page(s).")
            self.after(0, self._pdf_render_current)
        except Exception as e:
            self._show_error(f"Erreur PDF :\n{e}")

    # ── HTML → texte ──────────────────────────────────────────────

    def _html_to_text(self, html):
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html,"lxml")
            for tag in soup(["script","style","nav","header","footer","aside","form","button"]):
                tag.decompose()
            main = (soup.find("article") or soup.find("main") or
                    soup.find(id="content") or soup.find(id="mw-content-text") or
                    soup.body or soup)
            lines=[]
            for el in main.descendants:
                if el.name in ["h1","h2"]:
                    t=el.get_text(strip=True)
                    if t: lines.append(f"\n\n== {t} ==\n")
                elif el.name=="h3":
                    t=el.get_text(strip=True)
                    if t: lines.append(f"\n=== {t} ===\n")
                elif el.name=="p":
                    t=el.get_text(strip=True)
                    if t and len(t)>20: lines.append(t+"\n")
                elif el.name=="li":
                    t=el.get_text(strip=True)
                    if t: lines.append(f"  • {t}")
            return "\n".join(lines) or html_module.unescape(re.sub(r'<[^>]+',' ',html))[:5000]
        except ImportError:
            clean=re.sub(r'<script[^>]*>.*?</script>','',html,flags=re.DOTALL|re.IGNORECASE)
            clean=re.sub(r'<style[^>]*>.*?</style>','',clean,flags=re.DOTALL|re.IGNORECASE)
            clean=re.sub(r'<[^>]+',' ',clean)
            return html_module.unescape(re.sub(r'\s+',' ',clean))[:8000]

    # ── Rendu texte ───────────────────────────────────────────────

    def _render_text_content(self, title, text, mode="plain"):
        w=self.text_w; w.config(state="normal"); w.delete("1.0","end")
        w.insert("end",f"\n{title}\n","title")
        w.insert("end","─"*60+"\n\n","sep")
        for line in text.split("\n"):
            if re.match(r'^== .+ ==$',line):
                w.insert("end",f"\n\n{line.strip('= ').strip().upper()}\n","h2")
                w.insert("end","─"*50+"\n","sep")
            elif re.match(r'^=== .+ ===$',line):
                w.insert("end",f"\n{line.strip('= ').strip()}\n","h3")
            elif line.strip().startswith("•"):
                w.insert("end",f"  {line.strip()}\n","body")
            elif line.strip():
                w.insert("end",line+"\n","body")
            else:
                w.insert("end","\n")
        w.insert("end","\n\n─── Fin du contenu ───\n","sep")
        w.config(state="disabled"); w.yview_moveto(0)
        # Restaurer les surlignages sauvegardés
        self.after(100, self._restore_highlights)

    def _render_plain(self, text, label="CONTENU"):
        self._render_text_content(label, text)

    # ── Utils ─────────────────────────────────────────────────────

    def _set_status(self, msg):
        self.after(0, lambda: self.status_lbl.config(text=msg, fg=C["text2"]))

    def _show_error(self, msg):
        self._set_status("Erreur.")
        if hasattr(self,"text_w"):
            def _do():
                w=self.text_w; w.config(state="normal"); w.delete("1.0","end")
                w.insert("end","\nErreur\n","error")
                w.insert("end","─"*40+"\n\n","sep")
                w.insert("end",msg+"\n","error")
                w.config(state="disabled")
            self.after(0,_do)
        elif hasattr(self,"vid_info_lbl"):
            self.after(0,lambda: self.vid_info_lbl.config(text=f"Erreur :\n{msg}"))

# Polices complémentaires
FM_ = (FM, 9)
