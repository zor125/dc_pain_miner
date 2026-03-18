import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List

DB_PATH = Path("data/app.db")

def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH.as_posix())
    conn.row_factory = sqlite3.Row
    return conn

def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        url TEXT PRIMARY KEY,
        gallery_id TEXT NOT NULL,
        post_no INTEGER,
        title TEXT,
        author TEXT,
        created_at TEXT,
        view_count INTEGER,
        reply_count INTEGER,
        body TEXT,

        e_score INTEGER DEFAULT 0,
        reasons TEXT DEFAULT "",

        fetched_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    );
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_posts_gallery_created ON posts(gallery_id, created_at);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_posts_gallery_score ON posts(gallery_id, e_score);")
    conn.commit()

def upsert_post(conn: sqlite3.Connection, item: Dict[str, Any]) -> None:
    # url은 필수
    conn.execute("""
    INSERT INTO posts (
        url, gallery_id, post_no, title, author, created_at, view_count, reply_count, body,
        e_score, reasons, fetched_at, updated_at
    ) VALUES (
        :url, :gallery_id, :post_no, :title, :author, :created_at, :view_count, :reply_count, :body,
        :e_score, :reasons, datetime('now'), datetime('now')
    )
    ON CONFLICT(url) DO UPDATE SET
        title=excluded.title,
        author=excluded.author,
        created_at=excluded.created_at,
        view_count=excluded.view_count,
        reply_count=excluded.reply_count,
        body=excluded.body,
        e_score=excluded.e_score,
        reasons=excluded.reasons,
        updated_at=datetime('now');
    """, item)
    conn.commit()

def url_exists(conn: sqlite3.Connection, url: str) -> bool:
    cur = conn.execute("SELECT 1 FROM posts WHERE url=? LIMIT 1;", (url,))
    return cur.fetchone() is not None

def fetch_top_today(conn: sqlite3.Connection, gallery_id: str, limit: int = 10) -> List[sqlite3.Row]:
    # created_at이 디시에서 안정적으로 안 뽑히는 경우 대비: updated_at 기반으로도 보정 가능
    cur = conn.execute("""
    SELECT url, title, created_at, e_score, reasons
    FROM posts
    WHERE gallery_id = ?
      AND date(updated_at) = date('now', 'localtime')
    ORDER BY e_score DESC, updated_at DESC
    LIMIT ?;
    """, (gallery_id, limit))
    return cur.fetchall()
