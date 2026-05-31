#!/usr/bin/env python3
"""Base de données SQLite — Habitus"""
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), "autodidact.db")

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_schema()
        self._seed_demo()

    def _init_schema(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS folders (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            description TEXT,
            color       TEXT DEFAULT '#5b7fff',
            created_at  TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS paths (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            folder_id   INTEGER REFERENCES folders(id) ON DELETE SET NULL,
            title       TEXT NOT NULL,
            description TEXT,
            tags        TEXT,
            goal        TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS resources (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            path_id    INTEGER NOT NULL REFERENCES paths(id) ON DELETE CASCADE,
            title      TEXT NOT NULL,
            url        TEXT NOT NULL,
            type       TEXT DEFAULT 'custom',
            level      INTEGER DEFAULT 1,
            notes      TEXT,
            done       INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS highlights (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            resource_id INTEGER NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
            start_idx   TEXT NOT NULL,
            end_idx     TEXT NOT NULL,
            color       TEXT DEFAULT '#f5a62380',
            note        TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        );
        """)
        self.conn.commit()

    def _seed_demo(self):
        if self.conn.execute("SELECT COUNT(*) FROM folders").fetchone()[0] > 0:
            return
        f1 = self.conn.execute(
            "INSERT INTO folders (name,description,color) VALUES (?,?,?)",
            ("Sciences & Tech","Informatique, IA, mathématiques","#5b7fff")).lastrowid
        f2 = self.conn.execute(
            "INSERT INTO folders (name,description,color) VALUES (?,?,?)",
            ("Humanités","Philosophie, histoire, littérature","#a07ae0")).lastrowid
        p1 = self.conn.execute(
            "INSERT INTO paths (folder_id,title,description,tags,goal) VALUES (?,?,?,?,?)",
            (f1,"Machine Learning","Du débutant à l'expert","ml,ia,python",
             "Comprendre les algorithmes fondamentaux")).lastrowid
        p2 = self.conn.execute(
            "INSERT INTO paths (folder_id,title,description,tags,goal) VALUES (?,?,?,?,?)",
            (f2,"Histoire de la Philosophie","Des présocratiques à aujourd'hui",
             "philosophie,histoire","Acquérir une culture philosophique solide")).lastrowid
        for title,url,rtype,level,notes in [
            ("Wikipedia — Intelligence artificielle",
             "https://fr.wikipedia.org/wiki/Intelligence_artificielle","wikipedia",1,"Lire Historique et Applications"),
            ("Wikipedia — Apprentissage automatique",
             "https://fr.wikipedia.org/wiki/Apprentissage_automatique","wikipedia",1,"Focus sur les types d'apprentissage"),
            ("3Blue1Brown — Neural Networks",
             "https://www.youtube.com/watch?v=aircAruvnKk","video",2,"Série complète — 4 vidéos"),
            ("ArXiv — Attention Is All You Need",
             "https://arxiv.org/abs/1706.03762","article",5,"Papier fondateur des Transformers"),
        ]:
            self.conn.execute(
                "INSERT INTO resources (path_id,title,url,type,level,notes) VALUES (?,?,?,?,?,?)",
                (p1,title,url,rtype,level,notes))
        for title,url,rtype,level,notes in [
            ("Wikipedia — Philosophie antique",
             "https://fr.wikipedia.org/wiki/Philosophie_antique","wikipedia",1,"Vue d'ensemble"),
            ("Wikipedia — Socrate",
             "https://fr.wikipedia.org/wiki/Socrate","wikipedia",1,"Méthode socratique"),
            ("Wikipedia — Platon",
             "https://fr.wikipedia.org/wiki/Platon","wikipedia",2,"Allégorie de la caverne"),
        ]:
            self.conn.execute(
                "INSERT INTO resources (path_id,title,url,type,level,notes) VALUES (?,?,?,?,?,?)",
                (p2,title,url,rtype,level,notes))
        self.conn.commit()

    # ── Dossiers ──────────────────────────────────────────────────
    def get_all_folders(self):
        return [dict(r) for r in self.conn.execute("SELECT * FROM folders ORDER BY name").fetchall()]
    def get_folder(self,fid):
        r=self.conn.execute("SELECT * FROM folders WHERE id=?",(fid,)).fetchone()
        return dict(r) if r else None
    def create_folder(self,name,description=None,color="#5b7fff"):
        self.conn.execute("INSERT INTO folders (name,description,color) VALUES (?,?,?)",(name,description,color)); self.conn.commit()
    def update_folder(self,fid,name,description=None,color="#5b7fff"):
        self.conn.execute("UPDATE folders SET name=?,description=?,color=? WHERE id=?",(name,description,color,fid)); self.conn.commit()
    def delete_folder(self,fid):
        self.conn.execute("DELETE FROM folders WHERE id=?",(fid,)); self.conn.commit()
    def count_paths_in_folder(self,fid):
        return self.conn.execute("SELECT COUNT(*) FROM paths WHERE folder_id=?",(fid,)).fetchone()[0]

    # ── Parcours ──────────────────────────────────────────────────
    def get_all_paths(self,folder_id=None):
        if folder_id is not None:
            rows=self.conn.execute("SELECT * FROM paths WHERE folder_id=? ORDER BY title",(folder_id,)).fetchall()
        else:
            rows=self.conn.execute("SELECT * FROM paths ORDER BY title").fetchall()
        return [dict(r) for r in rows]
    def get_path(self,pid):
        r=self.conn.execute("SELECT * FROM paths WHERE id=?",(pid,)).fetchone(); return dict(r) if r else None
    def create_path(self,title,folder_id=None,description=None,tags=None,goal=None):
        self.conn.execute("INSERT INTO paths (folder_id,title,description,tags,goal) VALUES (?,?,?,?,?)",(folder_id,title,description,tags,goal)); self.conn.commit()
    def update_path(self,pid,title,folder_id=None,description=None,tags=None,goal=None):
        self.conn.execute("UPDATE paths SET title=?,folder_id=?,description=?,tags=?,goal=? WHERE id=?",(title,folder_id,description,tags,goal,pid)); self.conn.commit()
    def delete_path(self,pid):
        self.conn.execute("DELETE FROM paths WHERE id=?",(pid,)); self.conn.commit()

    # ── Ressources ────────────────────────────────────────────────
    def get_resources(self,path_id,level=None):
        if level:
            rows=self.conn.execute("SELECT * FROM resources WHERE path_id=? AND level=? ORDER BY level,id",(path_id,level)).fetchall()
        else:
            rows=self.conn.execute("SELECT * FROM resources WHERE path_id=? ORDER BY level,id",(path_id,)).fetchall()
        return [dict(r) for r in rows]
    def get_resource(self,rid):
        r=self.conn.execute("SELECT * FROM resources WHERE id=?",(rid,)).fetchone(); return dict(r) if r else None
    def add_resource(self,path_id,title,url,type="custom",level=1,notes=None):
        self.conn.execute("INSERT INTO resources (path_id,title,url,type,level,notes) VALUES (?,?,?,?,?,?)",(path_id,title,url,type,level,notes)); self.conn.commit()
    def remove_resource(self,rid):
        self.conn.execute("DELETE FROM resources WHERE id=?",(rid,)); self.conn.commit()
    def toggle_done(self,rid):
        self.conn.execute("UPDATE resources SET done=1-done WHERE id=?",(rid,)); self.conn.commit()
    def count_resources(self,pid):
        return self.conn.execute("SELECT COUNT(*) FROM resources WHERE path_id=?",(pid,)).fetchone()[0]
    def count_done(self,pid):
        return self.conn.execute("SELECT COUNT(*) FROM resources WHERE path_id=? AND done=1",(pid,)).fetchone()[0]
    def count_all_resources(self):
        return self.conn.execute("SELECT COUNT(*) FROM resources").fetchone()[0]
    def count_all_done(self):
        return self.conn.execute("SELECT COUNT(*) FROM resources WHERE done=1").fetchone()[0]

    # ── Surlignages ───────────────────────────────────────────────
    def get_highlights(self,resource_id):
        rows=self.conn.execute("SELECT * FROM highlights WHERE resource_id=? ORDER BY id",(resource_id,)).fetchall()
        return [dict(r) for r in rows]
    def add_highlight(self,resource_id,start_idx,end_idx,color="#f5a62380",note=None):
        cur=self.conn.execute("INSERT INTO highlights (resource_id,start_idx,end_idx,color,note) VALUES (?,?,?,?,?)",
                               (resource_id,start_idx,end_idx,color,note))
        self.conn.commit(); return cur.lastrowid
    def update_highlight_note(self,hid,note):
        self.conn.execute("UPDATE highlights SET note=? WHERE id=?",(note,hid)); self.conn.commit()
    def delete_highlight(self,hid):
        self.conn.execute("DELETE FROM highlights WHERE id=?",(hid,)); self.conn.commit()
