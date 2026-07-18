import streamlit as st


def render_social_tab(ai: dict):
    st.subheader("릴스 / 유튜브")

    st.text_area(
        "인스타 릴스 본문",
        ai.get("reels_caption", ""),
        height=180,
    )

    st.text_area(
        "유튜브 쇼츠 설명",
        ai.get("youtube_description", ""),
        height=180,
    )

    st.text_area(
        "해시태그",
        ai.get("hashtags", ""),
        height=120,
    )