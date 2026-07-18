import streamlit as st


def render_scripts_tab(ai: dict):
    st.subheader("쇼츠 대본")

    scripts = ai.get("scripts", {})

    st.text_area(
        "10초 대본",
        scripts.get("10sec", ""),
        height=150,
    )

    st.text_area(
        "20초 대본",
        scripts.get("20sec", ""),
        height=180,
    )

    st.text_area(
        "30초 대본",
        scripts.get("30sec", ""),
        height=220,
    )