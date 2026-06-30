import streamlit as st

from modules.analytics.repository import PerformanceRepository
from modules.analytics.learning_engine import LearningEngine


def show_learning():
    st.title("📊 Learning AI")
    st.caption("성과 데이터를 바탕으로 다음 콘텐츠 전략을 추천합니다.")

    rows = PerformanceRepository().all()
    result = LearningEngine().evaluate(rows)

    st.subheader(result.get("status"))
    st.write(result.get("summary"))

    metrics = result.get("metrics", {})
    if metrics:
        c1, c2, c3 = st.columns(3)
        c1.metric("저장률", f"{metrics.get('save_rate')}%")
        c2.metric("댓글률", f"{metrics.get('comment_rate')}%")
        c3.metric("좋아요율", f"{metrics.get('like_rate')}%")

    st.subheader("추천")
    for item in result.get("recommendation", []):
        st.write("✅", item)

    st.subheader("다음 전략")
    for item in result.get("next_strategy", []):
        st.write("•", item)
