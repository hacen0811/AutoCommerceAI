import streamlit as st


def render_capcut_tab(ai: dict):
    st.subheader("캡컷 편집안")

    plan = ai.get("capcut_plan", "")

    if not plan:
        st.warning("캡컷 편집안이 없습니다.")
        return

    st.text_area(
        "CapCut 편집 가이드",
        plan,
        height=320,
    )