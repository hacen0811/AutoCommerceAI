import streamlit as st


def as_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [value]
    return []


def bullet_list(items):
    items = as_list(items)
    if not items:
        return "- 없음"
    return "\n".join([f"- {item}" for item in items])


def render_product_tab(ai: dict):
    analysis = ai.get("product_analysis", {})

    st.subheader("제품 분석")

    st.markdown("### 카테고리")
    st.write(analysis.get("category", ""))

    st.markdown("### 주요 고객")
    st.markdown(bullet_list(analysis.get("target_customer", [])))

    st.markdown("### 고객 불편")
    st.markdown(bullet_list(analysis.get("pain_points", [])))

    st.markdown("### 구매 포인트")
    st.markdown(bullet_list(analysis.get("buying_points", [])))

    st.markdown("### 댓글 키워드")
    st.code(analysis.get("comment_keyword", ""), language=None)