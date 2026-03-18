import datetime as dt

from src.crawl_dc import list_recent_posts, fetch_post_detail
from src.db import connect, init_db, upsert_post, url_exists
from src.e_score import e_score
from src.report import write_daily_report

GALLERY_ID = "sajang"
SCAN_LIMIT = 200
PAGES = 2
THRESHOLD = 2
TOP_N = 20
REFRESH_EXISTING = True

def run_once() -> None:
    conn = connect()
    init_db(conn)

    new_count = 0
    try:
        # 1) 목록 수집
        candidates = []
        for p in range(1, PAGES + 1):
            candidates.extend(list_recent_posts(GALLERY_ID, page=p, limit=SCAN_LIMIT))

        print("CANDIDATES:", len(candidates))
        print("FIRST_URL:", candidates[0]["url"] if candidates else None)

        # 2) 상세 수집 + 스코어링 + DB upsert
        for item in candidates:
            url = item["url"]

            is_existing = url_exists(conn, url)
            if (not REFRESH_EXISTING) and is_existing:
                continue

            print("FETCHING:", url)
            detail = fetch_post_detail(url)

            # body 보강
            body = (detail.get("body") or "").strip()
            if not body:
                body = (detail.get("title") or item.get("title") or "").strip()

            # created_at / view_count fallback
            created_at = (detail.get("created_at") or item.get("created_at") or "").strip()

            view_count = detail.get("view_count")
            if view_count is None:
                view_count = item.get("view_count")

            score, reasons = e_score(detail.get("title") or item.get("title", ""), body)

            upsert_post(conn, {
                "url": url,
                "gallery_id": GALLERY_ID,
                "post_no": item.get("post_no"),
                "title": detail.get("title") or item.get("title", ""),
                "author": detail.get("author", ""),
                "created_at": created_at,
                "view_count": view_count,
                "reply_count": item.get("reply_count"),
                "body": body,
                "e_score": int(score),
                "reasons": ",".join(reasons),
            })

            if not is_existing:
                new_count += 1

    finally:
        conn.close()

    # 3) 리포트 생성
    write_daily_report(gallery_id=GALLERY_ID, threshold=THRESHOLD, top_n=TOP_N)

    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] run_once done. new_posts={new_count}")

if __name__ == "__main__":
    run_once()