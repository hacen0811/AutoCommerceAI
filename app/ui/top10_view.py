import streamlit as st

from app.ui.candidate_card import show_candidate_card


def show_top10(
    project,
    title,
    platform,
    items,
    safe_project_id,
):
    if not items:
        return

    st.markdown(f"## {title}")

    for item in items:
        if isinstance(item, dict):
            show_candidate_card(
                project,
                platform,
                item,
                safe_project_id,
            )