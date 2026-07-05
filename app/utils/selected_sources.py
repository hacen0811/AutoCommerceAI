import json
from pathlib import Path

import streamlit as st

from app.utils.project_keys import safe_project_id, selected_session_key

SELECTED_DIR = Path("exports/selected_sources")


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def selected_sources_path(project):
    return SELECTED_DIR / f"{safe_project_id(project)}_selected_sources.json"


def load_selected_sources(project):
    path = selected_sources_path(project)

    if not path.exists():
        return []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
    except Exception:
        return []

    return []


def save_selected_sources(project, sources):
    clean_sources = []

    for source in sources or []:
        if isinstance(source, dict):
            clean_sources.append(source)

    write_json(selected_sources_path(project), clean_sources)


def init_selected_sources(project, force_reload=False):
    key = selected_session_key(project)

    if force_reload or key not in st.session_state:
        st.session_state[key] = load_selected_sources(project)

    return key


def source_identity(platform, item):
    return (
        str(platform or "").strip().lower(),
        str(item.get("rank", "")).strip(),
        str(item.get("query", "")).strip(),
    )


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


def select_source(project, platform, item, url):
    key = init_selected_sources(project)

    selected = normalize_selected_source(project, platform, item, url)
    selected_id = source_identity(selected.get("platform"), selected)

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


def clear_selected_sources(project):
    key = init_selected_sources(project)
    st.session_state[key] = []
    save_selected_sources(project, [])