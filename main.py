#!/usr/bin/env python3
"""HABITUS v2.0 — Parcours d'apprentissage"""
import tkinter as tk
from tkinter import ttk, messagebox
import time, sys, os
from PIL import Image, ImageTk

sys.path.insert(0, os.path.dirname(__file__))
from database import Database
from content_viewer import ContentViewer

APP_DIR = os.path.dirname(os.path.abspath(__file__))

C = {
    "bg":       "#12141a", "bg2":     "#181b23", "panel":   "#1e2130",
    "panel2":   "#252840", "border":  "#2a2e45", "border2": "#3a3f60",
    "accent":   "#5b7fff", "accent2": "#3a5acc", "accentbg":"#181e3a",
    "green":    "#3dd68c", "greenbg": "#0e2a1e", "amber":   "#f5a623",
    "red":      "#e05252", "redbg":   "#2a1010", "cyan":    "#36c8d4",
    "purple":   "#a07ae0", "text":    "#dde1f0", "text2":   "#7a8099",
    "text3":    "#3d4260", "white":   "#f0f2ff", "sel":     "#1e2545",
    "done_bg":  "#0e1a10",
}

FM  = "Courier New"
_pf = sys.platform
F   = ("Segoe UI",10)      if _pf=="win32" else ("SF Pro Text",10)      if _pf=="darwin" else ("DejaVu Sans",10)
FS  = ("Segoe UI",9)       if _pf=="win32" else ("SF Pro Text",9)       if _pf=="darwin" else ("DejaVu Sans",9)
FB  = ("Segoe UI",10,"bold") if _pf=="win32" else ("SF Pro Text",10,"bold") if _pf=="darwin" else ("DejaVu Sans",10,"bold")
FLB = ("Segoe UI",13,"bold") if _pf=="win32" else ("SF Pro Text",13,"bold") if _pf=="darwin" else ("DejaVu Sans",13,"bold")
FMB = (FM,9,"bold")
FM_ = (FM,9)

LEVELS = {
    1:("Novice",     "#3dd68c"), 2:("Apprenti","#5b7fff"),
    3:("Initié",     "#36c8d4"), 4:("Maître",  "#a07ae0"),
    5:("Architecte", "#f5a623"),
}
TYPE_LABEL = {
    "wikipedia":"Wikipedia","video":"Vidéo","article":"Article",
    "book":"Livre","web":"Web","pdf":"PDF","custom":"Lien",
}
TYPE_COLOR = {
    "wikipedia":C["green"],"video":C["cyan"],"article":C["amber"],
    "book":C["purple"],"web":C["accent"],"pdf":C["red"],"custom":C["text2"],
}
FOLDER_COLORS = ["#5b7fff","#3dd68c","#f5a623","#e05252","#36c8d4","#a07ae0","#f07a30"]
XP_PER_DONE=50
XP_THRESHOLDS=[0,200,500,1000,2000,4000]
RANK_NAMES=["Curieux","Explorateur","Chercheur","Analyste","Expert","Maître"]

def compute_rank(xp):
    lvl=0
    for i,t in enumerate(XP_THRESHOLDS):
        if xp>=t: lvl=i
    nxt=XP_THRESHOLDS[lvl+1] if lvl+1<len(XP_THRESHOLDS) else XP_THRESHOLDS[-1]+1000
    return lvl,RANK_NAMES[lvl],XP_THRESHOLDS[lvl],nxt


# ══════════════════════════════════════════════════════════════════
# SPLASH — logo torche PNG avec fondu
# ══════════════════════════════════════════════════════════════════

class SplashScreen(tk.Toplevel):
    STEPS = 40
    PAUSE = 600

    def __init__(self, parent, on_done):
        super().__init__(parent)
        self._on_done = on_done
        self.overrideredirect(True)
        self.configure(bg=C["bg"])
        self.attributes("-alpha", 0.0)
        self.attributes("-topmost", True)

        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        W, H = 380, 280
        self.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")

        cv = tk.Canvas(self, bg=C["bg"], width=W, height=H, highlightthickness=0)
        cv.pack(fill="both", expand=True)

        # Logo torche
        icon_path = os.path.join(APP_DIR, "icon_splash.png")
        if os.path.exists(icon_path):
            try:
                img = Image.open(icon_path).resize((110, 110), Image.LANCZOS)
                self._img = ImageTk.PhotoImage(img)
                cv.create_image(W//2, 100, image=self._img, anchor="center")
            except Exception:
                pass

        cv.create_text(W//2, 178, text="Habitus",
                       font=("Segoe UI",30,"bold") if _pf=="win32"
                            else ("SF Pro Display",30,"bold") if _pf=="darwin"
                            else ("DejaVu Sans",28,"bold"),
                       fill=C["white"], anchor="center")
        cv.create_text(W//2, 220, text="Parcours d'apprentissage",
                       font=FS, fill=C["text3"], anchor="center")

        self._step = 0
        self._fade_in()

    def _fade_in(self):
        self._step += 1
        self.attributes("-alpha", min(self._step/self.STEPS, 1.0))
        if self._step < self.STEPS:
            self.after(18, self._fade_in)
        else:
            self.after(self.PAUSE, self._start_fade_out)

    def _start_fade_out(self):
        self._step = self.STEPS
        self._fade_out()

    def _fade_out(self):
        self._step -= 1
        self.attributes("-alpha", max(self._step/self.STEPS, 0.0))
        if self._step > 0:
            self.after(18, self._fade_out)
        else:
            self.destroy()
            self._on_done()


# ══════════════════════════════════════════════════════════════════
# WIDGETS
# ══════════════════════════════════════════════════════════════════

def _rounded_rect(cv, x1, y1, x2, y2, r, color):
    cv.create_arc(x1,y1,x1+2*r,y1+2*r,start=90,extent=90,fill=color,outline=color)
    cv.create_arc(x2-2*r,y1,x2,y1+2*r,start=0,extent=90,fill=color,outline=color)
    cv.create_arc(x1,y2-2*r,x1+2*r,y2,start=180,extent=90,fill=color,outline=color)
    cv.create_arc(x2-2*r,y2-2*r,x2,y2,start=270,extent=90,fill=color,outline=color)
    cv.create_rectangle(x1+r,y1,x2-r,y2,fill=color,outline=color)
    cv.create_rectangle(x1,y1+r,x2,y2-r,fill=color,outline=color)


class Btn(tk.Canvas):
    STYLES = {
        "primary":("white",  C["accent2"], C["white"],  C["accent"]),
        "default":(C["text2"],C["panel2"], C["text"],   "#2e3455"),
        "success":(C["white"],"#0d6636",  C["white"],  "#0f7a40"),
        "danger": (C["white"],"#7a1a1a",  C["white"],  C["red"]),
        "ghost":  (C["text3"],C["bg"],    C["text2"],  C["panel"]),
        "flat":   (C["text2"],C["bg2"],   C["text"],   C["panel"]),
    }
    _R = 6

    def __init__(self, parent, text, cmd, style="default", pad=(12,6), **kw):
        fg,bg,hfg,hbg = self.STYLES[style]
        est_w = max(len(text)*7+pad[0]*2, 40)
        est_h = 14+pad[1]*2
        super().__init__(parent, width=est_w, height=est_h,
                         highlightthickness=0, cursor="hand2",
                         bg=parent.cget("bg"), **kw)
        self._text=text; self._cmd=cmd
        self._fg,self._bg,self._hfg,self._hbg=fg,bg,hfg,hbg
        self._hover=False
        self.bind("<Map>",       lambda e: self._redraw(self._bg,self._fg))
        self.bind("<Configure>", lambda e: self._redraw(
            self._hbg if self._hover else self._bg,
            self._hfg if self._hover else self._fg))
        self.bind("<Button-1>",  lambda e: cmd())
        self.bind("<Enter>",     lambda e: self._enter())
        self.bind("<Leave>",     lambda e: self._leave())

    def _enter(self): self._hover=True;  self._redraw(self._hbg,self._hfg)
    def _leave(self): self._hover=False; self._redraw(self._bg, self._fg)

    def _redraw(self, bg, fg):
        self.delete("all")
        w,h = self.winfo_width(), self.winfo_height()
        if w<4 or h<4: return
        _rounded_rect(self,0,0,w,h,self._R,bg)
        self.create_text(w//2,h//2,text=self._text,fill=fg,font=FS,anchor="center")


def mk_entry(parent, var):
    return tk.Entry(parent, textvariable=var, font=F,
                    bg=C["panel2"], fg=C["text"], insertbackground=C["accent"],
                    selectbackground=C["accent2"], relief="flat", bd=0,
                    highlightthickness=1, highlightbackground=C["border2"],
                    highlightcolor=C["accent"])


# ══════════════════════════════════════════════════════════════════
# XP BAR
# ══════════════════════════════════════════════════════════════════

class XPWidget(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=C["bg"])
        self._disp=0.0
        self._cv=tk.Canvas(self,bg=C["bg"],height=38,width=300,highlightthickness=0)
        self._cv.pack()
        self._cv.bind("<Configure>", lambda e: self._draw())

    def set_xp(self, xp): self._anim(xp)

    def _anim(self, target, cur=None):
        if cur is None: cur=self._disp
        if abs(cur-target)<0.5: self._disp=target; self._draw(); return
        self._disp=cur+(target-cur)*0.2; self._draw()
        self.after(16, lambda: self._anim(target,self._disp))

    def _draw(self):
        cv=self._cv; cv.delete("all")
        w=cv.winfo_width()
        if w<10: return
        ri,rn,xmin,xmax=compute_rank(int(self._disp))
        pct=min(1.0,(self._disp-xmin)/max(1,xmax-xmin))
        cv.create_text(0,8,text=rn.upper(),anchor="w",fill=C["accent"],font=(FM,9,"bold"))
        cv.create_text(w,8,text=f"{int(self._disp)} XP",anchor="e",fill=C["text2"],font=(FM,8))
        cv.create_rectangle(0,20,w,27,fill=C["panel2"],outline="")
        fw=int(w*pct)
        if fw>2:
            cv.create_rectangle(0,20,fw,27,fill=C["accent2"],outline="")
            cv.create_rectangle(max(0,fw-3),20,fw,27,fill=C["accent"],outline="")
        if ri+1<len(RANK_NAMES):
            cv.create_text(0,36,text=f"→ {RANK_NAMES[ri+1]}",anchor="w",fill=C["text3"],font=(FM,7))
            cv.create_text(w,36,text=f"{int(xmax-self._disp)} XP",anchor="e",fill=C["text3"],font=(FM,7))


class ProgBar(tk.Canvas):
    def __init__(self, parent):
        super().__init__(parent,bg=C["bg2"],height=3,highlightthickness=0)
        self._disp=0.0
        self.bind("<Configure>", lambda e: self._draw())

    def set_val(self, pct, animate=True):
        if animate: self._anim(pct)
        else: self._disp=pct; self._draw()

    def _anim(self, target, cur=None):
        if cur is None: cur=self._disp
        if abs(cur-target)<0.3: self._disp=target; self._draw(); return
        self._disp=cur+(target-cur)*0.18; self._draw()
        self.after(16, lambda: self._anim(target,self._disp))

    def _draw(self):
        self.delete("all"); w=self.winfo_width()
        if w<2: return
        self.create_rectangle(0,0,w,3,fill=C["panel2"],outline="")
        fw=int(w*self._disp/100)
        if fw>0: self.create_rectangle(0,0,fw,3,fill=C["accent"],outline="")


# ══════════════════════════════════════════════════════════════════
# ROUNDED FRAME + RESCARD
# ══════════════════════════════════════════════════════════════════

class RoundedFrame(tk.Canvas):
    def __init__(self, parent, bg_color, border_color, radius=8, **kw):
        super().__init__(parent, bg=parent.cget("bg"), highlightthickness=0, **kw)
        self._bgc=bg_color; self._bdc=border_color; self._r=radius
        self._inner=tk.Frame(self, bg=bg_color)
        self.bind("<Map>",       self._redraw)
        self.bind("<Configure>", self._redraw)

    def _redraw(self, e=None):
        self.delete("all")
        w,h=self.winfo_width(),self.winfo_height()
        if w<4 or h<4: return
        r=self._r
        _rounded_rect(self,1,1,w-1,h-1,r,self._bgc)
        # bordure
        for pts in [
            (1,1+r,1,h-1-r),(w-1,1+r,w-1,h-1-r),
            (1+r,1,w-1-r,1),(1+r,h-1,w-1-r,h-1),
        ]: self.create_line(*pts,fill=self._bdc)
        self.create_arc(1,1,1+2*r,1+2*r,start=90,extent=90,outline=self._bdc,style="arc")
        self.create_arc(w-1-2*r,1,w-1,1+2*r,start=0,extent=90,outline=self._bdc,style="arc")
        self.create_arc(1,h-1-2*r,1+2*r,h-1,start=180,extent=90,outline=self._bdc,style="arc")
        self.create_arc(w-1-2*r,h-1-2*r,w-1,h-1,start=270,extent=90,outline=self._bdc,style="arc")
        self._inner.place(x=r,y=r,width=w-2*r,height=h-2*r)

    def set_border(self,c): self._bdc=c; self._redraw()
    def inner(self): return self._inner


class ResCard(RoundedFrame):
    def __init__(self, parent, resource, on_open, on_toggle, on_remove, on_select):
        done=bool(resource.get("done"))
        bg=C["done_bg"] if done else C["panel"]
        super().__init__(parent, bg_color=bg, border_color=C["border"], radius=8, cursor="hand2")
        self.rid=resource["id"]; self.r=resource; self._done=done
        self._on_open=on_open; self._on_toggle=on_toggle
        self._on_remove=on_remove; self._on_select=on_select
        self.config(height=76 if not resource.get("notes") else 92)
        self.bind("<Map>", lambda e: self._build_inner())
        self._built=False

    def _build_inner(self):
        if self._built: return
        self._built=True
        r=self.r; done=self._done
        tcolor=TYPE_COLOR.get(r.get("type","custom"),C["text2"])
        tlabel=TYPE_LABEL.get(r.get("type","custom"),r.get("type",""))
        lvl=r.get("level",1); _,lc=LEVELS.get(lvl,(str(lvl),C["accent"]))
        bg=C["done_bg"] if done else C["panel"]
        inn=self.inner()

        row=tk.Frame(inn,bg=bg); row.pack(fill="x",padx=10,pady=(8,3))
        chk=tk.Label(row,text="✓" if done else "○",
                     font=FB,fg=C["green"] if done else C["text3"],bg=bg,cursor="hand2")
        chk.pack(side="left",padx=(0,8))
        chk.bind("<Button-1>",lambda e: self._on_toggle(self.rid))
        tk.Label(row,text=f" {tlabel} ",font=(FM,8,"bold"),fg=tcolor,bg=C["bg2"],pady=1).pack(side="left",padx=(0,8))
        tk.Label(row,text=r["title"],font=F,fg=C["text3"] if done else C["text"],
                 bg=bg,anchor="w").pack(side="left",fill="x",expand=True)
        tk.Label(row,text=f"Lv.{lvl}",font=(FM,8,"bold"),fg=lc,bg=bg).pack(side="right",padx=4)

        sub=tk.Frame(inn,bg=bg); sub.pack(fill="x",padx=10,pady=(0,7))
        url=r.get("url","")
        tk.Label(sub,text=url[:68]+("…" if len(url)>68 else ""),
                 font=(FM,7),fg=C["text3"],bg=bg,anchor="w").pack(side="left",fill="x",expand=True)
        Btn(sub,"Ouvrir",lambda: self._on_open(self.rid),"primary",pad=(10,3)).pack(side="right")
        Btn(sub,"Suppr.",lambda: self._on_remove(self.rid),"danger",pad=(8,3)).pack(side="right",padx=(0,4))

        note=r.get("notes","") or ""
        if note:
            nf=tk.Frame(inn,bg=bg); nf.pack(fill="x",padx=10,pady=(0,6))
            tk.Label(nf,text=note[:100],font=(FM,8),fg=C["text3"],bg=bg,anchor="w").pack(fill="x")

        for w in [self,inn,row,sub]:
            w.bind("<Button-1>",lambda e: self._on_select(self.rid))

    def set_selected(self,sel):
        self._bdc=C["accent"] if sel else C["border"]
        self._redraw()


# ══════════════════════════════════════════════════════════════════
# APPLICATION
# ══════════════════════════════════════════════════════════════════

class HabitusApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Habitus")
        self.configure(bg=C["bg"])
        self.geometry("1340x860")
        self.minsize(960,640)

        # Icône de la fenêtre
        icon_path = os.path.join(APP_DIR, "icon_transparent.png")
        if os.path.exists(icon_path):
            try:
                img = Image.open(icon_path).resize((32,32), Image.LANCZOS)
                self._icon = ImageTk.PhotoImage(img)
                self.iconphoto(True, self._icon)
            except Exception:
                pass

        self.db=Database()
        self.sel_folder=None; self.sel_path=None; self.sel_res=None
        self._refreshing=False

        self._build()
        self._clock_tick()
        self._full_refresh()

    def _build(self):
        self._build_header()
        tk.Frame(self,bg=C["border"],height=1).pack(fill="x")
        body=tk.Frame(self,bg=C["bg"]); body.pack(fill="both",expand=True)
        self._build_sidebar(body)
        tk.Frame(body,bg=C["border"],width=1).pack(side="left",fill="y")
        self._build_main(body)
        tk.Frame(self,bg=C["border"],height=1).pack(fill="x")
        self._build_footer()

    def _build_header(self):
        h=tk.Frame(self,bg=C["bg"],height=56); h.pack(fill="x"); h.pack_propagate(False)

        # Logo torche PNG
        icon_path = os.path.join(APP_DIR, "icon_transparent.png")
        if os.path.exists(icon_path):
            try:
                img = Image.open(icon_path).resize((34,34), Image.LANCZOS)
                self._logo_img = ImageTk.PhotoImage(img)
                logo_lbl = tk.Label(h, image=self._logo_img, bg=C["bg"])
                logo_lbl.pack(side="left", padx=(16,6), pady=10)
            except Exception:
                pass

        tk.Label(h,text="Habitus",font=FLB,fg=C["white"],bg=C["bg"]).pack(side="left",pady=8)
        self.clock_lbl=tk.Label(h,text="",font=FM_,fg=C["text3"],bg=C["bg"])
        self.clock_lbl.pack(side="right",padx=20)
        self.xp_widget=XPWidget(h); self.xp_widget.pack(side="right",padx=20,pady=8)

    def _build_sidebar(self, parent):
        sb=tk.Frame(parent,bg=C["bg2"],width=250); sb.pack(side="left",fill="y"); sb.pack_propagate(False)

        dh=tk.Frame(sb,bg=C["bg2"]); dh.pack(fill="x",padx=14,pady=(16,6))
        tk.Label(dh,text="Dossiers",font=FB,fg=C["text"],bg=C["bg2"]).pack(side="left")
        Btn(dh,"+",self._new_folder,"primary",pad=(7,3)).pack(side="right")
        Btn(dh,"✎",self._edit_folder,"flat",pad=(6,3)).pack(side="right",padx=(0,5))
        Btn(dh,"⌫",self._del_folder,"danger",pad=(6,3)).pack(side="right")

        fw=tk.Frame(sb,bg=C["bg2"]); fw.pack(fill="x",padx=6,pady=(0,8))
        fsb=tk.Scrollbar(fw,width=4,bg=C["bg2"],troughcolor=C["panel"],relief="flat"); fsb.pack(side="right",fill="y")
        self.folder_lb=tk.Listbox(fw,bg=C["bg2"],fg=C["text2"],selectbackground=C["sel"],
                                   selectforeground=C["accent"],font=FS,bd=0,highlightthickness=0,
                                   activestyle="none",height=7,yscrollcommand=fsb.set)
        self.folder_lb.pack(side="left",fill="x",expand=True)
        fsb.config(command=self.folder_lb.yview)
        self.folder_lb.bind("<<ListboxSelect>>",self._on_folder_sel)

        tk.Frame(sb,bg=C["border"],height=1).pack(fill="x",padx=8)

        ph=tk.Frame(sb,bg=C["bg2"]); ph.pack(fill="x",padx=14,pady=(12,6))
        self.paths_lbl=tk.Label(ph,text="Parcours",font=FB,fg=C["text"],bg=C["bg2"]); self.paths_lbl.pack(side="left")
        Btn(ph,"+",self._new_path,"primary",pad=(7,3)).pack(side="right")
        Btn(ph,"✎",self._edit_path,"flat",pad=(6,3)).pack(side="right",padx=(0,5))
        Btn(ph,"⌫",self._del_path,"danger",pad=(6,3)).pack(side="right")

        sf=tk.Frame(sb,bg=C["bg2"]); sf.pack(fill="x",padx=6,pady=(0,6))
        tk.Label(sf,text="  ⌕",font=FS,fg=C["text3"],bg=C["bg2"]).pack(side="left")
        self.search_var=tk.StringVar()
        self.search_var.trace("w",lambda *a: self._filter_paths())
        mk_entry(sf,self.search_var).pack(side="left",fill="x",expand=True,ipady=4)

        pw=tk.Frame(sb,bg=C["bg2"]); pw.pack(fill="both",expand=True,padx=6)
        psb=tk.Scrollbar(pw,width=4,bg=C["bg2"],troughcolor=C["panel"],relief="flat"); psb.pack(side="right",fill="y")
        self.path_lb=tk.Listbox(pw,bg=C["bg2"],fg=C["text2"],selectbackground=C["sel"],
                                 selectforeground=C["accent"],font=FS,bd=0,highlightthickness=0,
                                 activestyle="none",yscrollcommand=psb.set)
        self.path_lb.pack(side="left",fill="both",expand=True)
        psb.config(command=self.path_lb.yview)
        self.path_lb.bind("<<ListboxSelect>>",self._on_path_sel)

        tk.Frame(sb,bg=C["border"],height=1).pack(fill="x",padx=8)
        self.stats_lbl=tk.Label(sb,text="",font=FM_,fg=C["text3"],bg=C["bg2"],justify="left",anchor="w")
        self.stats_lbl.pack(fill="x",padx=14,pady=10)

    def _build_main(self, parent):
        main=tk.Frame(parent,bg=C["bg"]); main.pack(side="left",fill="both",expand=True)

        banner=tk.Frame(main,bg=C["panel"],height=60); banner.pack(fill="x"); banner.pack_propagate(False)
        self.path_title_lbl=tk.Label(banner,text="Sélectionner un parcours",
                                      font=FLB,fg=C["text3"],bg=C["panel"],anchor="w")
        self.path_title_lbl.pack(side="left",padx=20,pady=10)
        self.path_xp_lbl=tk.Label(banner,text="",font=FMB,fg=C["accent"],bg=C["panel"])
        self.path_xp_lbl.pack(side="right",padx=20)
        self.path_tags_lbl=tk.Label(banner,text="",font=FM_,fg=C["text3"],bg=C["panel"])
        self.path_tags_lbl.pack(side="right",padx=4)

        self.prog_bar=ProgBar(main); self.prog_bar.pack(fill="x")

        tb=tk.Frame(main,bg=C["bg2"]); tb.pack(fill="x")
        tk.Frame(tb,bg=C["border"],height=1).pack(fill="x")
        tbi=tk.Frame(tb,bg=C["bg2"]); tbi.pack(fill="x",padx=14,pady=8)
        Btn(tbi,"+ Ajouter",self._add_res,"primary",pad=(14,6)).pack(side="left")
        Btn(tbi,"Ouvrir",self._open_res,"default",pad=(12,6)).pack(side="left",padx=(8,0))
        Btn(tbi,"Marquer fait",self._toggle_done,"success",pad=(12,6)).pack(side="left",padx=(8,0))
        Btn(tbi,"Supprimer",self._remove_res,"danger",pad=(12,6)).pack(side="left",padx=(8,0))
        tk.Label(tbi,text="Niveau :",font=FS,fg=C["text3"],bg=C["bg2"]).pack(side="right",padx=(0,4))
        self.lvl_var=tk.StringVar(value="Tous")
        self._setup_combo_style()
        lvl_cb=ttk.Combobox(tbi,textvariable=self.lvl_var,values=["Tous","1","2","3","4","5"],
                             width=7,state="readonly",font=FS)
        lvl_cb.pack(side="right",padx=(0,12))
        lvl_cb.bind("<<ComboboxSelected>>",lambda e: self._refresh_res())
        tk.Frame(tb,bg=C["border"],height=1).pack(fill="x")

        res_wrap=tk.Frame(main,bg=C["bg"]); res_wrap.pack(fill="both",expand=True)
        self._res_sb=tk.Scrollbar(res_wrap,width=6,bg=C["bg2"],troughcolor=C["panel"],relief="flat")
        self._res_sb.pack(side="right",fill="y")
        self._res_cv=tk.Canvas(res_wrap,bg=C["bg"],highlightthickness=0,yscrollcommand=self._res_sb.set)
        self._res_cv.pack(side="left",fill="both",expand=True)
        self._res_sb.config(command=self._res_cv.yview)
        self._res_inner=tk.Frame(self._res_cv,bg=C["bg"])
        self._res_win=self._res_cv.create_window((0,0),window=self._res_inner,anchor="nw")
        self._res_inner.bind("<Configure>",lambda e: self._res_cv.configure(scrollregion=self._res_cv.bbox("all")))
        self._res_cv.bind("<Configure>",lambda e: self._res_cv.itemconfig(self._res_win,width=e.width))
        self._res_cv.bind_all("<MouseWheel>",lambda e: self._res_cv.yview_scroll(int(-1*(e.delta/120)),"units"))
        self._cards=[]

    def _build_footer(self):
        f=tk.Frame(self,bg=C["bg2"],height=26); f.pack(fill="x",side="bottom"); f.pack_propagate(False)
        self.status_lbl=tk.Label(f,text="Prêt",font=FM_,fg=C["text3"],bg=C["bg2"],anchor="w")
        self.status_lbl.pack(side="left",padx=14,pady=4)
        tk.Label(f,text="Habitus v2.0 · SQLite local",font=FM_,fg=C["text3"],bg=C["bg2"]).pack(side="right",padx=14)

    def _setup_combo_style(self):
        s=ttk.Style(); s.theme_use("clam")
        s.configure("TCombobox",fieldbackground=C["panel2"],background=C["panel2"],
                     foreground=C["text"],selectbackground=C["accent2"],
                     bordercolor=C["border2"],arrowcolor=C["text2"])

    def _clock_tick(self):
        self.clock_lbl.config(text=time.strftime("%H:%M"))
        self.after(30000,self._clock_tick)

    # ── Refresh ───────────────────────────────────────────────────

    def _full_refresh(self):
        self._refresh_folders(); self._refresh_paths()
        self._refresh_res(); self._update_stats(); self._update_xp()

    def _update_stats(self):
        nf=len(self.db.get_all_folders()); np_=len(self.db.get_all_paths())
        nr=self.db.count_all_resources(); nd=self.db.count_all_done()
        pct=int(nd/nr*100) if nr else 0
        self.stats_lbl.config(text=f"{nf} dossier(s)  ·  {np_} parcours\n{nd}/{nr} ressources  ({pct}%)")

    def _update_xp(self): self.xp_widget.set_xp(self.db.count_all_done()*XP_PER_DONE)

    def _set_status(self,msg,t=4000):
        self.status_lbl.config(text=msg,fg=C["text2"])
        if t: self.after(t,lambda: self.status_lbl.config(text="Prêt",fg=C["text3"]))

    def _set_status_xp(self,msg):
        self.status_lbl.config(text=msg,fg=C["green"])
        self.after(2500,lambda: self.status_lbl.config(text="Prêt",fg=C["text3"]))

    # ── Dossiers ──────────────────────────────────────────────────

    def _refresh_folders(self):
        self._folders=self.db.get_all_folders()
        self.folder_lb.delete(0,"end")
        for f in self._folders:
            n=self.db.count_paths_in_folder(f["id"])
            self.folder_lb.insert("end",f"  {f['name']}  ({n})")
        if self.sel_folder:
            for i,f in enumerate(self._folders):
                if f["id"]==self.sel_folder: self.folder_lb.selection_set(i); break

    def _on_folder_sel(self,e):
        if self._refreshing: return
        s=self.folder_lb.curselection()
        if not s: return
        self.sel_folder=self._folders[s[0]]["id"]
        self.paths_lbl.config(text=f"Parcours — {self._folders[s[0]]['name']}")
        self._refresh_paths()

    def _new_folder(self):
        d=FolderDialog(self)
        if d.result: self.db.create_folder(**d.result); self._full_refresh()

    def _edit_folder(self):
        if not self.sel_folder: return self._set_status("Sélectionner un dossier d'abord")
        d=FolderDialog(self,data=self.db.get_folder(self.sel_folder))
        if d.result: self.db.update_folder(self.sel_folder,**d.result); self._full_refresh()

    def _del_folder(self):
        if not self.sel_folder: return
        f=self.db.get_folder(self.sel_folder)
        if messagebox.askyesno("Supprimer",f"Supprimer « {f['name']} » ?",parent=self):
            self.db.delete_folder(self.sel_folder); self.sel_folder=None
            self.paths_lbl.config(text="Parcours"); self._full_refresh()

    # ── Parcours ──────────────────────────────────────────────────

    def _refresh_paths(self):
        self._paths=self.db.get_all_paths(folder_id=self.sel_folder)
        self._filter_paths()

    def _filter_paths(self):
        q=self.search_var.get().lower()
        self._refreshing=True
        self.path_lb.delete(0,"end"); self._dpaths=[]
        for p in self._paths:
            if q and q not in p["title"].lower() and q not in (p.get("tags") or "").lower(): continue
            total=self.db.count_resources(p["id"]); done=self.db.count_done(p["id"])
            pct=int(done/total*100) if total else 0
            self.path_lb.insert("end",f"  {p['title'][:28]}  {pct}%")
            self._dpaths.append(p)
        if self.sel_path:
            for i,p in enumerate(self._dpaths):
                if p["id"]==self.sel_path: self.path_lb.selection_set(i); break
        self._refreshing=False

    def _on_path_sel(self,e):
        if self._refreshing: return
        s=self.path_lb.curselection()
        if not s: return
        p=self._dpaths[s[0]]
        if p["id"]!=self.sel_path: self.sel_res=None
        self.sel_path=p["id"]; self._load_path(p)

    def _load_path(self,p):
        self.path_title_lbl.config(text=p["title"],fg=C["white"])
        self.path_tags_lbl.config(text=p.get("tags") or "")
        self._refresh_res()

    def _new_path(self):
        d=PathDialog(self,folders=self.db.get_all_folders(),default_folder_id=self.sel_folder)
        if d.result:
            self.db.create_path(**d.result)
            if d.result.get("folder_id"): self.sel_folder=d.result["folder_id"]
            self._full_refresh()

    def _edit_path(self):
        if not self.sel_path: return self._set_status("Sélectionner un parcours d'abord")
        d=PathDialog(self,data=self.db.get_path(self.sel_path),folders=self.db.get_all_folders())
        if d.result:
            self.db.update_path(self.sel_path,**d.result); self._full_refresh()
            p=self.db.get_path(self.sel_path)
            if p: self._load_path(p)

    def _del_path(self):
        if not self.sel_path: return
        p=self.db.get_path(self.sel_path)
        if messagebox.askyesno("Supprimer",f"Supprimer « {p['title']} » ?",parent=self):
            self.db.delete_path(self.sel_path); self.sel_path=None; self.sel_res=None
            self.path_title_lbl.config(text="Sélectionner un parcours",fg=C["text3"])
            self.path_tags_lbl.config(text=""); self.path_xp_lbl.config(text="")
            self._full_refresh(); self._clear_cards()

    # ── Ressources ────────────────────────────────────────────────

    def _refresh_res(self):
        self._refresh_paths(); self._update_stats(); self._update_xp()
        if not self.sel_path: self._clear_cards(); return
        lvl_s=self.lvl_var.get(); level=None if lvl_s=="Tous" else int(lvl_s)
        resources=self.db.get_resources(self.sel_path,level=level)
        all_res=self.db.get_resources(self.sel_path)
        done_n=sum(1 for r in all_res if r["done"])
        pct=done_n/len(all_res)*100 if all_res else 0
        self.prog_bar.set_val(pct)
        self.path_xp_lbl.config(text=f"{done_n*XP_PER_DONE} XP  ·  {done_n}/{len(all_res)}")
        self._clear_cards()
        if not resources:
            msg="Aucune ressource à ce niveau." if all_res else \
                "  Parcours vide — cliquez sur « + Ajouter » pour commencer."
            lbl=tk.Label(self._res_inner,text="\n"+msg,font=FS,fg=C["text3"],bg=C["bg"],anchor="w")
            lbl.pack(fill="x",padx=20,pady=10); self._cards.append(lbl); return
        by_lvl={}
        for r in resources: by_lvl.setdefault(r["level"],[]).append(r)
        for lvl in sorted(by_lvl.keys()):
            hdr=self._lvl_header(lvl,by_lvl[lvl])
            hdr.pack(fill="x",padx=16,pady=(18,6)); self._cards.append(hdr)
            for r in by_lvl[lvl]:
                card=ResCard(self._res_inner,r,on_open=self._open_by_id,
                             on_toggle=self._toggle_by_id,on_remove=self._remove_by_id,
                             on_select=self._select_res)
                card.set_selected(r["id"]==self.sel_res)
                card.pack(fill="x",padx=16,pady=3); self._cards.append(card)

    def _lvl_header(self,lvl,resources):
        name,color=LEVELS.get(lvl,(f"Niveau {lvl}",C["accent"]))
        done=sum(1 for r in resources if r["done"])
        f=tk.Frame(self._res_inner,bg=C["bg"])
        tk.Label(f,text=f"Niveau {lvl}  —  {name}",font=FMB,fg=color,bg=C["bg"]).pack(side="left")
        tk.Label(f,text=f"  {done}/{len(resources)}",font=FM_,fg=C["text3"],bg=C["bg"]).pack(side="left")
        return f

    def _clear_cards(self):
        for w in self._cards: w.destroy()
        self._cards=[]; self.prog_bar.set_val(0,animate=False)

    def _select_res(self,rid):
        self.sel_res=rid
        for c in self._cards:
            if isinstance(c,ResCard): c.set_selected(c.rid==rid)

    def _add_res(self):
        if not self.sel_path: return self._set_status("Sélectionner un parcours d'abord")
        d=ResourceDialog(self)
        if d.result:
            self.db.add_resource(self.sel_path,**d.result)
            self._refresh_res(); self._set_status(f"Ressource ajoutée : {d.result['title']}")

    def _open_res(self):
        if not self.sel_res: return self._set_status("Sélectionner une ressource d'abord")
        self._open_by_id(self.sel_res)

    def _open_by_id(self,rid):
        r=self.db.get_resource(rid)
        if r: ContentViewer(self,r,self.db)

    def _toggle_done(self):
        rid=self.sel_res
        if rid is None: return self._set_status("Sélectionner une ressource d'abord")
        self._toggle_by_id(rid)

    def _toggle_by_id(self,rid):
        was=bool(self.db.get_resource(rid)["done"])
        self.db.toggle_done(rid); self._refresh_res()
        self.sel_res=rid
        for c in self._cards:
            if isinstance(c,ResCard) and c.rid==rid: c.set_selected(True)
        if not was: self._set_status_xp(f"+{XP_PER_DONE} XP — Ressource complétée !")
        else: self._set_status("Ressource non complétée.")

    def _remove_res(self):
        if not self.sel_res: return self._set_status("Sélectionner une ressource d'abord")
        self._remove_by_id(self.sel_res)

    def _remove_by_id(self,rid):
        r=self.db.get_resource(rid)
        if messagebox.askyesno("Supprimer",f"Supprimer « {r['title']} » ?",parent=self):
            self.db.remove_resource(rid); self.sel_res=None; self._refresh_res()


# ══════════════════════════════════════════════════════════════════
# DIALOGUES
# ══════════════════════════════════════════════════════════════════

class BaseDialog(tk.Toplevel):
    def __init__(self,parent,title_text,w=500,h=420):
        super().__init__(parent); self.title(title_text)
        self.configure(bg=C["bg"]); self.geometry(f"{w}x{h}")
        self.resizable(False,False); self.grab_set(); self.transient(parent)
        self.result=None

    def _header(self,text):
        h=tk.Frame(self,bg=C["panel"]); h.pack(fill="x")
        tk.Label(h,text=text,font=FLB,fg=C["white"],bg=C["panel"]).pack(side="left",padx=20,pady=14)
        tk.Frame(self,bg=C["border"],height=1).pack(fill="x")

    def _field(self,parent,label_text,var=None,multi=False,mh=3):
        f=tk.Frame(parent,bg=C["bg"]); f.pack(fill="x",pady=(12,0))
        tk.Label(f,text=label_text,font=FS,fg=C["text2"],bg=C["bg"],anchor="w").pack(fill="x",pady=(0,4))
        if multi:
            w=tk.Text(f,font=F,bg=C["panel2"],fg=C["text"],insertbackground=C["accent"],
                      relief="flat",bd=0,highlightthickness=1,highlightbackground=C["border2"],
                      highlightcolor=C["accent"],height=mh)
            w.pack(fill="x",ipady=4); return w
        e=mk_entry(f,var); e.pack(fill="x",ipady=7); return e

    def _footer(self,ok_label,ok_cmd):
        tk.Frame(self,bg=C["border"],height=1).pack(fill="x")
        f=tk.Frame(self,bg=C["bg"]); f.pack(fill="x",padx=20,pady=14)
        Btn(f,"Annuler",self.destroy,"default",pad=(16,7)).pack(side="right",padx=(8,0))
        Btn(f,ok_label,ok_cmd,"primary",pad=(18,7)).pack(side="right")


class FolderDialog(BaseDialog):
    def __init__(self,parent,data=None):
        super().__init__(parent,"Dossier",440,320); self._d=data or {}
        self._header("Nouveau dossier" if not data else "Modifier le dossier")
        form=tk.Frame(self,bg=C["bg"]); form.pack(fill="both",expand=True,padx=20)
        self._name=tk.StringVar(value=self._d.get("name",""))
        self._desc=tk.StringVar(value=self._d.get("description",""))
        self._field(form,"Nom",self._name); self._field(form,"Description (optionnel)",self._desc)
        cf=tk.Frame(form,bg=C["bg"]); cf.pack(fill="x",pady=(14,0))
        tk.Label(cf,text="Couleur",font=FS,fg=C["text2"],bg=C["bg"]).pack(anchor="w",pady=(0,6))
        self._color=tk.StringVar(value=self._d.get("color",FOLDER_COLORS[0]))
        cr=tk.Frame(cf,bg=C["bg"]); cr.pack(fill="x")
        for col in FOLDER_COLORS:
            b=tk.Label(cr,text="   ",bg=col,width=3,cursor="hand2",highlightthickness=2,
                       highlightbackground=C["white"] if col==self._color.get() else col)
            b.pack(side="left",padx=3)
            b.bind("<Button-1>",lambda e,c=col: self._pick(c,cr))
        self._footer("Enregistrer",self._submit); self.wait_window()

    def _pick(self,color,cr):
        self._color.set(color)
        for b in cr.winfo_children():
            b.config(highlightbackground=C["white"] if b.cget("bg")==color else b.cget("bg"))

    def _submit(self):
        name=self._name.get().strip()
        if not name: return messagebox.showwarning("Erreur","Le nom est requis",parent=self)
        self.result={"name":name,"description":self._desc.get().strip() or None,"color":self._color.get()}
        self.destroy()


class PathDialog(BaseDialog):
    def __init__(self,parent,data=None,folders=None,default_folder_id=None):
        super().__init__(parent,"Parcours",500,440)
        self._d=data or {}; self._folders=folders or []; self._def_fid=default_folder_id
        self._header("Nouveau parcours" if not data else "Modifier le parcours")
        form=tk.Frame(self,bg=C["bg"]); form.pack(fill="both",expand=True,padx=20)
        self._title=tk.StringVar(value=self._d.get("title",""))
        self._tags=tk.StringVar(value=self._d.get("tags",""))
        self._field(form,"Titre",self._title); self._field(form,"Tags (séparés par virgules)",self._tags)
        if self._folders:
            ff=tk.Frame(form,bg=C["bg"]); ff.pack(fill="x",pady=(12,0))
            tk.Label(ff,text="Dossier",font=FS,fg=C["text2"],bg=C["bg"]).pack(fill="x",pady=(0,4))
            self._folder_var=tk.StringVar()
            names=["— Aucun —"]+[f["name"] for f in self._folders]
            cur_fid=self._d.get("folder_id") or self._def_fid
            if cur_fid:
                for f in self._folders:
                    if f["id"]==cur_fid: self._folder_var.set(f["name"]); break
            else: self._folder_var.set("— Aucun —")
            cb=ttk.Combobox(ff,textvariable=self._folder_var,values=names,state="readonly",font=FS)
            cb.pack(fill="x",ipady=5)
        else: self._folder_var=None
        of=tk.Frame(form,bg=C["bg"]); of.pack(fill="x",pady=(12,0))
        tk.Label(of,text="Objectif",font=FS,fg=C["text2"],bg=C["bg"]).pack(fill="x",pady=(0,4))
        self._goal=tk.Text(of,font=F,bg=C["panel2"],fg=C["text"],insertbackground=C["accent"],
                            relief="flat",bd=0,highlightthickness=1,highlightbackground=C["border2"],
                            highlightcolor=C["accent"],height=3)
        self._goal.pack(fill="x",ipady=4)
        if self._d.get("goal"): self._goal.insert("1.0",self._d["goal"])
        self._footer("Enregistrer",self._submit); self.wait_window()

    def _submit(self):
        title=self._title.get().strip()
        if not title: return messagebox.showwarning("Erreur","Le titre est requis",parent=self)
        fid=None
        if self._folder_var and self._folder_var.get()!="— Aucun —":
            for f in self._folders:
                if f["name"]==self._folder_var.get(): fid=f["id"]; break
        self.result={"title":title,"folder_id":fid,"description":None,
                     "tags":self._tags.get().strip() or None,
                     "goal":self._goal.get("1.0","end-1c").strip() or None}
        self.destroy()


class ResourceDialog(BaseDialog):
    def __init__(self,parent):
        super().__init__(parent,"Nouvelle ressource",540,520)
        self._header("Ajouter une ressource")
        form=tk.Frame(self,bg=C["bg"]); form.pack(fill="both",expand=True,padx=20)
        tf=tk.Frame(form,bg=C["bg"]); tf.pack(fill="x",pady=(12,0))
        tk.Label(tf,text="Type de contenu",font=FS,fg=C["text2"],bg=C["bg"]).pack(anchor="w",pady=(0,6))
        self._type=tk.StringVar(value="wikipedia")
        tr=tk.Frame(tf,bg=C["bg"]); tr.pack(fill="x")
        self._type_btns={}
        for t in ["wikipedia","video","article","book","web","pdf","custom"]:
            col=TYPE_COLOR.get(t,C["text2"]); lbl=TYPE_LABEL.get(t,t)
            btn=tk.Label(tr,text=lbl,font=FS,fg=col,bg=C["panel2"],cursor="hand2",
                         padx=7,pady=5,highlightthickness=1,highlightbackground=C["border"])
            btn.pack(side="left",padx=2)
            btn.bind("<Button-1>",lambda e,typ=t: self._pick_type(typ))
            self._type_btns[t]=btn
        self._pick_type("wikipedia")
        self._title_v=tk.StringVar(); self._url_v=tk.StringVar()
        self._field(form,"Titre",self._title_v); self._field(form,"URL / Chemin fichier",self._url_v)
        lf=tk.Frame(form,bg=C["bg"]); lf.pack(fill="x",pady=(12,0))
        tk.Label(lf,text="Niveau de difficulté",font=FS,fg=C["text2"],bg=C["bg"]).pack(anchor="w",pady=(0,6))
        self._lvl=tk.IntVar(value=1)
        lr=tk.Frame(lf,bg=C["bg"]); lr.pack(fill="x")
        for i in range(1,6):
            n,col=LEVELS[i]
            tk.Radiobutton(lr,text=f"{i} · {n}",variable=self._lvl,value=i,
                           font=FS,fg=col,bg=C["bg"],selectcolor=C["panel2"],
                           activebackground=C["bg"],cursor="hand2").pack(side="left",padx=(0,10))
        nf=tk.Frame(form,bg=C["bg"]); nf.pack(fill="x",pady=(12,0))
        tk.Label(nf,text="Notes (optionnel)",font=FS,fg=C["text2"],bg=C["bg"]).pack(anchor="w",pady=(0,4))
        self._notes=tk.Text(nf,font=F,bg=C["panel2"],fg=C["text"],insertbackground=C["accent"],
                             relief="flat",bd=0,highlightthickness=1,highlightbackground=C["border2"],
                             highlightcolor=C["accent"],height=2)
        self._notes.pack(fill="x",ipady=4)
        self._footer("Ajouter",self._submit); self.wait_window()

    def _pick_type(self,t):
        self._type.set(t)
        for k,btn in self._type_btns.items():
            btn.config(highlightbackground=C["accent"] if k==t else C["border"],
                       highlightthickness=2 if k==t else 1)

    def _submit(self):
        title=self._title_v.get().strip(); url=self._url_v.get().strip()
        if not title or not url:
            return messagebox.showwarning("Erreur","Le titre et l'URL sont requis",parent=self)
        self.result={"title":title,"url":url,"type":self._type.get(),
                     "level":self._lvl.get(),
                     "notes":self._notes.get("1.0","end-1c").strip() or None}
        self.destroy()


if __name__ == "__main__":
    app = HabitusApp()
    app.withdraw()

    def on_splash_done():
        app.deiconify(); app.lift()

    SplashScreen(app, on_splash_done)
    app.mainloop()
