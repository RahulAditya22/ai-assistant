import sqlite3
from pathlib import Path
from typing import Any
from .config import DATABASE_PATH

def get_conn():
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn=sqlite3.connect(DATABASE_PATH); conn.row_factory=sqlite3.Row; conn.execute("PRAGMA foreign_keys=ON"); return conn

def init_db():
    with get_conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS documents(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,file_hash TEXT UNIQUE NOT NULL,file_type TEXT NOT NULL,pages INTEGER DEFAULT 0,char_count INTEGER DEFAULT 0,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS chunks(id INTEGER PRIMARY KEY AUTOINCREMENT,document_id INTEGER NOT NULL,chunk_index INTEGER NOT NULL,page INTEGER,section TEXT,text TEXT NOT NULL,FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE,UNIQUE(document_id,chunk_index));
        CREATE TABLE IF NOT EXISTS edges(id INTEGER PRIMARY KEY AUTOINCREMENT,document_id INTEGER NOT NULL,subject TEXT NOT NULL,relation TEXT NOT NULL,object TEXT NOT NULL,source_chunk_id INTEGER,FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE,FOREIGN KEY(source_chunk_id) REFERENCES chunks(id) ON DELETE SET NULL);
        CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id); CREATE INDEX IF NOT EXISTS idx_edges_document ON edges(document_id);
        """)

def add_document(name,file_hash,file_type,pages,char_count,chunks:list[dict[str,Any]],edges:list[dict[str,Any]])->int:
    with get_conn() as c:
        existing=c.execute("SELECT id FROM documents WHERE file_hash=?",(file_hash,)).fetchone()
        if existing:return int(existing["id"])
        cur=c.execute("INSERT INTO documents(name,file_hash,file_type,pages,char_count) VALUES(?,?,?,?,?)",(name,file_hash,file_type,pages,char_count)); doc_id=cur.lastrowid; ids={}
        for ch in chunks:
            cur=c.execute("INSERT INTO chunks(document_id,chunk_index,page,section,text) VALUES(?,?,?,?,?)",(doc_id,ch["chunk_index"],ch.get("page"),ch.get("section"),ch["text"])); ids[ch["chunk_index"]]=cur.lastrowid
        for e in edges:c.execute("INSERT INTO edges(document_id,subject,relation,object,source_chunk_id) VALUES(?,?,?,?,?)",(doc_id,e["subject"],e["relation"],e["object"],ids.get(e.get("chunk_index"))))
        return int(doc_id)

def list_documents():
    with get_conn() as c:return [dict(r) for r in c.execute("SELECT * FROM documents ORDER BY created_at DESC,id DESC")]

def get_chunks(doc_ids=None):
    with get_conn() as c:
        if doc_ids:
            q=",".join("?" for _ in doc_ids); rows=c.execute(f"SELECT c.*,d.name document_name FROM chunks c JOIN documents d ON d.id=c.document_id WHERE c.document_id IN ({q}) ORDER BY c.document_id,c.chunk_index",tuple(doc_ids)).fetchall()
        else: rows=c.execute("SELECT c.*,d.name document_name FROM chunks c JOIN documents d ON d.id=c.document_id ORDER BY c.document_id,c.chunk_index").fetchall()
        return [dict(r) for r in rows]

def get_edges(doc_ids=None):
    with get_conn() as c:
        if doc_ids:
            q=",".join("?" for _ in doc_ids); rows=c.execute(f"SELECT e.*,c.page,c.text chunk_text,d.name document_name FROM edges e LEFT JOIN chunks c ON c.id=e.source_chunk_id JOIN documents d ON d.id=e.document_id WHERE e.document_id IN ({q})",tuple(doc_ids)).fetchall()
        else: rows=c.execute("SELECT e.*,c.page,c.text chunk_text,d.name document_name FROM edges e LEFT JOIN chunks c ON c.id=e.source_chunk_id JOIN documents d ON d.id=e.document_id").fetchall()
        return [dict(r) for r in rows]
