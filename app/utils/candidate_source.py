from urllib.parse import quote_plus

import streamlit as st

from app.utils.selected_sources import (
    init_selected_sources,
    save_selected_sources,
)

from app.ui.download_connect import open_with_login_browser

def make_search_url(platform, query):
    encoded = quote_plus(query or "")

    if platform == "taobao":
        return f"https://s.taobao.com/search?q={encoded}"

    if platform == "douyin":
        return f"https://www.douyin.com/search/{encoded}"

    if platform == "1688":
        return (
            f"https://s.1688.com/selloffer/offer_search.htm?keywords={encoded}"
        )

    return ""


def normalize_selected_source(project, platform, item, url):
    return {
        "project_id": getattr(project, "id", ""),
        "platform": str(platform or "").strip().lower(),
        "rank": item.get("rank"),
        "query": item.get("query", ""),
        "purpose": item.get("purpose", ""),
        "score": item.get("score", ""),
        "url": url or "",
    }


def source_identity(platform, item):
    return (
        str(platform or "").strip().lower(),
        str(item.get("rank", "")).strip(),
        str(item.get("query", "")).strip(),
    )


def select_source(project, platform, item, url):
    key = init_selected_sources(project)

    selected = normalize_selected_source(
        project,
        platform,
        item,
        url,
    )

    selected_id = source_identity(
        selected.get("platform"),
        selected,
    )

    current_sources = st.session_state.get(key, [])

    exists = any(
        source_identity(source.get("platform"), source) == selected_id
        for source in current_sources
        if isinstance(source, dict)
    )

    if exists:
        return False

    st.session_state[key] = [*current_sources, selected]
    save_selected_sources(project, st.session_state[key])

    return True