# src/aggregate.py
import re
import sqlite3
from collections import defaultdict, Counter
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple


DB_PATH = "data/app.db"


@dataclass
class ClusterItem:
    cluster_label: str
    count: int
    avg_score: float
    posts: List[Dict[str, Any]]


@dataclass
class SignalGroup:
    signal: str
    count: int
    avg_score: float
    clusters: List[ClusterItem]


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def load_recent_posts(
    gallery_id: str = "sajang",
    recent_n: int = 300,
    min_score: int = 1,
) -> List[sqlite3.Row]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT url, title, body, e_score, reasons, updated_at
            FROM posts
            WHERE gallery_id = ?
              AND e_score >= ?
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (gallery_id, min_score, recent_n),
        ).fetchall()
        return rows
    finally:
        conn.close()


def normalize_reason(reason: str) -> str:
    reason = (reason or "").strip()
    if not reason:
        return "기타"

    mapping = {
        "review_fraud": "리뷰 먹튀/리뷰 문제",
        "review_low": "리뷰 전환/리뷰 저조",
        "delivery_block": "배달 지연/라이더 문제",
        "commerce_money": "플랫폼 환불/마진 문제",
        "pos_integration": "포스/연동 문제",
        "question/help": "질문/정보 공백",
        "number(money/percent)": "돈/가격/수치 언급",
        "repeat": "반복 고통",
        "noise": "잡음",
        "unknown": "기타",
    }
    return mapping.get(reason, reason)


def tokenize_title(title: str) -> List[str]:
    """
    제목을 거칠게 토큰화.
    한글/영문/숫자만 남기고, 의미 없는 짧은 토큰 제거.
    """
    title = (title or "").lower().strip()
    title = re.sub(r"[^0-9a-zA-Z가-힣\s]", " ", title)
    raw_tokens = title.split()

    stopwords = {
        "이", "그", "저", "좀", "진짜", "너무", "왜", "뭐", "이거", "저거",
        "하는", "인데", "있냐", "있음", "없냐", "없음", "같음", "같은",
        "형님들", "다들", "요즘", "오늘", "지금", "그냥", "어케", "어떻게",
        "근데", "아니", "시발", "씨발", "개", "좆", "존나", "ㅈㄴ"
    }

    tokens = []
    for tok in raw_tokens:
        if len(tok) <= 1:
            continue
        if tok in stopwords:
            continue
        tokens.append(tok)

    return tokens


def choose_cluster_label(titles: List[str]) -> str:
    """
    클러스터 대표 제목을 만들기 위해 가장 자주 나오는 핵심 토큰 2개 정도를 조합.
    """
    counter = Counter()
    for title in titles:
        counter.update(tokenize_title(title))

    common = [word for word, _ in counter.most_common(3)]
    if common:
        return " / ".join(common[:2])

    # 토큰이 너무 없으면 첫 제목을 축약해서 사용
    if titles:
        return titles[0][:30]
    return "기타"


def title_similarity(title_a: str, title_b: str) -> float:
    """
    아주 단순한 제목 유사도:
    토큰 집합의 자카드 유사도 사용
    """
    a = set(tokenize_title(title_a))
    b = set(tokenize_title(title_b))

    if not a or not b:
        return 0.0

    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def cluster_posts_by_title(
    posts: List[sqlite3.Row],
    similarity_threshold: float = 0.34,
    max_posts_per_cluster: int = 3,
) -> List[ClusterItem]:
    """
    같은 signal 그룹 안에서 제목 유사도로 다시 클러스터링.
    """
    clusters: List[List[sqlite3.Row]] = []

    for post in posts:
        title = post["title"] or ""

        assigned = False
        for cluster in clusters:
            rep_title = cluster[0]["title"] or ""
            sim = title_similarity(title, rep_title)
            if sim >= similarity_threshold:
                cluster.append(post)
                assigned = True
                break

        if not assigned:
            clusters.append([post])

    results: List[ClusterItem] = []

    for cluster in clusters:
        sorted_cluster = sorted(cluster, key=lambda x: int(x["e_score"] or 0), reverse=True)
        titles = [c["title"] or "" for c in cluster]
        label = choose_cluster_label(titles)

        avg_score = sum(int(x["e_score"] or 0) for x in cluster) / len(cluster)

        posts_out = []
        seen = set()
        for item in sorted_cluster:
            if item["url"] in seen:
                continue
            seen.add(item["url"])
            posts_out.append(
                {
                    "title": item["title"],
                    "url": item["url"],
                    "score": item["e_score"],
                    "updated_at": item["updated_at"],
                }
            )
            if len(posts_out) >= max_posts_per_cluster:
                break

        results.append(
            ClusterItem(
                cluster_label=label,
                count=len(cluster),
                avg_score=avg_score,
                posts=posts_out,
            )
        )

    results.sort(key=lambda x: (x.count, x.avg_score), reverse=True)
    return results


def aggregate_signals(
    gallery_id: str = "sajang",
    recent_n: int = 300,
    min_score: int = 1,
    top_k_signals: int = 10,
    top_k_clusters_per_signal: int = 5,
    max_posts_per_cluster: int = 3,
) -> List[SignalGroup]:
    rows = load_recent_posts(gallery_id=gallery_id, recent_n=recent_n, min_score=min_score)

    grouped: Dict[str, List[sqlite3.Row]] = defaultdict(list)

    for row in rows:
        reasons_raw = (row["reasons"] or "").strip()
        reasons = [r.strip() for r in reasons_raw.split(",") if r.strip()]

        if not reasons:
            reasons = ["unknown"]

        # 보조 신호 제외하고 핵심 신호 우선
        filtered = [
            r for r in reasons
            if r not in {"question/help", "number(money/percent)", "repeat"}
        ]

        if not filtered:
            filtered = reasons[:1]

        for reason in filtered:
            grouped[normalize_reason(reason)].append(row)

    signal_groups: List[SignalGroup] = []

    for signal, items in grouped.items():
        avg_score = sum(int(x["e_score"] or 0) for x in items) / len(items)

        clusters = cluster_posts_by_title(
            items,
            similarity_threshold=0.34,
            max_posts_per_cluster=max_posts_per_cluster,
        )[:top_k_clusters_per_signal]

        signal_groups.append(
            SignalGroup(
                signal=signal,
                count=len(items),
                avg_score=avg_score,
                clusters=clusters,
            )
        )

    signal_groups.sort(key=lambda x: (x.count, x.avg_score), reverse=True)
    return signal_groups[:top_k_signals]


if __name__ == "__main__":
    groups = aggregate_signals()
    for group in groups:
        print(f"\n[{group.signal}] count={group.count}, avg_score={group.avg_score:.2f}")
        for cluster in group.clusters:
            print(f"  - cluster: {cluster.cluster_label} ({cluster.count})")
            for p in cluster.posts:
                print("    *", p["title"])