#!/usr/bin/env python3
"""Habitus v2.0 — Lanceur"""
import os, sys

def check():
    errors = []
    try:
        import tkinter
    except ImportError:
        errors.append("python3-tk manquant  →  sudo apt install python3-tk")

    try:
        from PIL import Image
    except ImportError:
        errors.append("Pillow manquant  →  pip install Pillow")

    if errors:
        print("=== DÉPENDANCES REQUISES MANQUANTES ===")
        for e in errors: print(f"  • {e}")
        sys.exit(1)

    # Optionnels
    try:    import tkinterweb
    except ImportError:
        print("INFO : tkinterweb absent — lecteur web désactivé (pip install tkinterweb)")

    try:    import youtube_transcript_api
    except ImportError:
        print("INFO : youtube-transcript-api absent — transcripts désactivés")

    try:    import fitz
    except ImportError:
        print("INFO : PyMuPDF absent — visionneuse PDF désactivée (pip install pymupdf)")

    try:    import bs4
    except ImportError:
        print("INFO : beautifulsoup4 absent — extraction HTML basique")

if __name__ == "__main__":
    check()
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    from main import HabitusApp, SplashScreen
    app = HabitusApp()
    app.withdraw()
    def on_done():
        app.deiconify(); app.lift()
    SplashScreen(app, on_done)
    app.mainloop()
