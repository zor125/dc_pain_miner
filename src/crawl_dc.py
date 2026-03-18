# src/crawl_dc.py
import re
import asyncio
from typing import List, Dict, Any, Optional

# dc_api는 비공식 라이브러리 (eunchuldev/dcinside-python3-api)
import dc_api

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
POST_NO_RE = re.compile(r"[&?]no=(\d+)")


def _get_post_no(url: str) -> Optional[int]:
    m = POST_NO_RE.search(url)
    return int(m.group(1)) if m else None


async def _alist_recent_posts(gallery_id: str, page: int, limit: int) -> List[Dict[str, Any]]:
    """
    dc_api로 목록 수집.
    NOTE:
      - dc_api의 board(board_id=...)는 "programming" 같은 board_id를 받음 (DC의 id 파라미터와 동일하게 쓰는 편)
      - num=-1은 무한에 가깝게 순회하는 예시가 README에 있음. :contentReference[oaicite:2]{index=2}
      - 여기서는 limit개만 받고 끊음.
    """
    items: List[Dict[str, Any]] = []

    async with dc_api.API() as api:
        # start_page를 page로, limit만큼만 소비
        # (dc_api 쪽 파라미터가 바뀌면 여기만 손보면 됨)
        count = 0
        async for index in api.board(board_id=gallery_id, start_page=page, num=-1):
            # index.title / index.id / index.time / index.view_count / index.comment_count 등은 README에 예시로 나옴 :contentReference[oaicite:3]{index=3}
            url = f"https://gall.dcinside.com/mgallery/board/view/?id={gallery_id}&no={index.id}&page={page}"
            items.append({
                "gallery_id": gallery_id,
                "url": url,
                "post_no": int(index.id),
                "title": str(getattr(index, "title", "") or ""),
                "reply_count": int(getattr(index, "comment_count", 0) or 0),
                "view_count": int(getattr(index, "view_count", 0) or 0),
                "created_at": str(getattr(index, "time", "") or ""),
            })
            count += 1
            if count >= limit:
                break

    return items


def list_recent_posts(gallery_id: str, page: int = 1, limit: int = 50, client: Any = None) -> List[Dict[str, Any]]:
    """
    pipeline.py가 동기라서, 여기서 asyncio.run으로 감싸서 제공.
    (client 인자는 기존 인터페이스 호환용으로 무시)
    """
    return asyncio.run(_alist_recent_posts(gallery_id, page, limit))


async def _afetch_post_detail(gallery_id: str, post_no: int) -> Dict[str, Any]:
    async with dc_api.API() as api:
        # 문서 본문 가져오기: README 예시에 index.document() / api.document() 흐름이 있음 :contentReference[oaicite:4]{index=4}
        doc = await api.document(board_id=gallery_id, document_id=post_no)

        title = str(getattr(doc, "title", "") or "")
        author = str(getattr(doc, "author", "") or "")
        created_at = str(getattr(doc, "time", "") or "")
        view_count = getattr(doc, "view_count", None)
        contents = str(getattr(doc, "contents", "") or "")

        return {
            "url": f"https://gall.dcinside.com/mgallery/board/view/?id={gallery_id}&no={post_no}",
            "title": title,
            "author": author,
            "created_at": created_at,
            "view_count": int(view_count) if isinstance(view_count, int) else None,
            "body": contents,
        }


def fetch_post_detail(url: str, client: Any = None) -> Dict[str, Any]:
    """
    URL에서 no= 를 뽑아서 dc_api로 상세를 가져옴.
    """
    post_no = _get_post_no(url)
    if post_no is None:
        return {"url": url, "title": "", "author": "", "created_at": "", "view_count": None, "body": ""}

    # gallery_id는 url의 id= 로부터 뽑아도 되는데,
    # 여기선 mgallery view URL이니까 pipeline에서 넘긴 gallery_id를 쓰는 방식이 더 안전함.
    # 다만 pipeline이 url만 넘기니, url에서 id= 를 파싱해보자.
    m = re.search(r"[&?]id=([^&]+)", url)
    gallery_id = m.group(1) if m else "sajang"

    return asyncio.run(_afetch_post_detail(gallery_id, post_no))