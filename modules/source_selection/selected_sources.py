import streamlit as st


def selected_sources_key(project):
    return f"selected_sources_{project.id}"


def init_selected_sources(project):
    key = selected_sources_key(project)

    if key not in st.session_state:
        st.session_state[key] = []

    return key


def select_source(project, platform, item, url):
    key = init_selected_sources(project)

    selected = {
        "platform": platform,
        "rank": item.get("rank"),
        "query": item.get("query"),
        "purpose": item.get("purpose"),
        "score": item.get("score"),
        "url": url,
    }

    exists = any(
        s.get("platform") == selected["platform"]
        and s.get("rank") == selected["rank"]
        and s.get("query") == selected["query"]
        for s in st.session_state[key]
    )

    if not exists:
        st.session_state[key].append(selected)

    return selected


def get_selected_sources(project):
    key = init_selected_sources(project)
    return st.session_state.get(key, [])


def clear_selected_sources(project):
    key = init_selected_sources(project)
    st.session_state[key] = []