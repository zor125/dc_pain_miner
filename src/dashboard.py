# src/dashboard.py
import os
import sys
import streamlit as st

sys.path.append(os.path.dirname(__file__))

from aggregate import aggregate_signals

st.set_page_config(
    page_title="자영업 고통 신호판",
    layout="wide",
)

st.title("디시 자영업갤 고통 신호 대시보드")

with st.sidebar:
    st.header("설정")
    gallery_id = st.text_input("갤러리 ID", value="sajang")
    recent_n = st.slider("최근 글 수", min_value=50, max_value=1000, value=300, step=50)
    min_score = st.slider("최소 점수", min_value=0, max_value=10, value=1, step=1)
    top_k = st.slider("표시할 신호 개수", min_value=3, max_value=20, value=10, step=1)
    top_clusters = st.slider("신호당 클러스터 수", min_value=1, max_value=10, value=5, step=1)
    max_posts = st.slider("클러스터당 대표 글 수", min_value=1, max_value=5, value=3, step=1)

st.caption("반복적으로 등장하는 고통 신호와 비슷한 제목 패턴을 함께 묶어 보여줍니다.")

signals = aggregate_signals(
    gallery_id=gallery_id,
    recent_n=recent_n,
    min_score=min_score,
    top_k_signals=top_k,
    top_k_clusters_per_signal=top_clusters,
    max_posts_per_cluster=max_posts,
)

if not signals:
    st.warning("표시할 데이터가 없습니다. pipeline을 먼저 실행해봐.")
else:
    cols = st.columns(2)

    for idx, signal in enumerate(signals):
        with cols[idx % 2]:
            with st.container(border=True):
                st.subheader(f"{signal.signal}")
                st.write(f"빈도: **{signal.count}건**")
                st.write(f"평균 점수: **{signal.avg_score:.2f}**")

                for cluster in signal.clusters:
                    st.markdown(f"### {cluster.cluster_label}")
                    st.write(f"- 클러스터 빈도: **{cluster.count}건**")
                    st.write(f"- 평균 점수: **{cluster.avg_score:.2f}**")

                    for post in cluster.posts:
                        st.markdown(
                            f"- [{post['title']}]({post['url']})  \n"
                            f"  점수: {post['score']} / 수집시각: {post['updated_at']}"
                        )