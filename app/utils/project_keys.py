import re


def safe_project_id(project):
    raw_id = str(getattr(project, "id", "") or "unknown_project")
    return re.sub(r"[^0-9A-Za-z가-힣._-]+", "_", raw_id).strip("_") or "unknown_project"


def selected_session_key(project):
    return f"selected_sources_{safe_project_id(project)}"


def selected_notice_key(project):
    return f"selected_sources_notice_{safe_project_id(project)}"