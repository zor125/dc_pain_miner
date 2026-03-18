# src/report.py
import csv
import os
import datetime as dt
import sqlite3
from typing import List, Tuple

DB_PATH = "data/app.db"
REPORT_DIR = "data/reports"

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def write_daily_report(
    gallery_id: str,
    threshold: int = 0,
    top_n: int = 10,
    recent_n: int = 200,   # ✅ 최근 N개 기준으로 랭킹
) -> str:
    """
    최근 24시간 필터 대신:
    - 최근 recent_n개 글을 가져오고
    - e_score 내림차순 TOP_N을 뽑아 저장
    (created_at 시간 신뢰가 낮아도 운영 가능)
    """
    _ensure_dir(REPORT_DIR)
    today = dt.date.today().strftime("%Y-%m-%d")
    out_path = os.path.join(REPORT_DIR, f"top_sajang_{today}.csv")

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    rows = con.execute(
        """
        SELECT url, title, created_at, e_score, reasons, updated_at, LENGTH(body) AS body_len
        FROM posts
        WHERE gallery_id = ?
        ORDER BY updated_at DESC
        LIMIT ?
        """,
        (gallery_id, recent_n),
    ).fetchall()

    # 최근 recent_n개 중에서 threshold 이상만 남기고, 점수로 정렬해서 top_n
    filtered = [r for r in rows if int(r["e_score"] or 0) >= threshold]
    ranked = sorted(filtered, key=lambda r: (int(r["e_score"] or 0), int(r["body_len"] or 0)), reverse=True)[:top_n]

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["url", "title", "created_at", "e_score", "reasons", "body_len", "updated_at"])
        for r in ranked:
            w.writerow([
                r["url"],
                r["title"],
                r["created_at"],
                r["e_score"],
                r["reasons"],
                r["body_len"],
                r["updated_at"],
            ])

    con.close()
    print(f"[report] wrote: {out_path} (rows={len(ranked)})")
    return out_path