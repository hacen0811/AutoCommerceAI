import json
import streamlit as st

from modules.project.repository import ProjectRepository
from modules.project.project_selector import ProjectSelector
from modules.editor.auto_editor_engine import AutoEditorEngine
from modules.editor.capcut_project_exporter import CapCutProjectExporter
from app.ui.render import copybox


def show_capcut_export():
    st.title("📤 CapCut Export")
    st.caption("CapCut 편집 지시서를 JSON/TXT로 내보냅니다.")

    projects = ProjectSelector().all_projects()
    if not projects:
        st.info("프로젝트가 없습니다.")
        return

    labels = ProjectSelector().labels(projects)
    project = labels[st.selectbox("프로젝트", list(labels.keys()))]

    plan = AutoEditorEngine().create_plan(project.product_name, project.keyword)

    if st.button("CapCut 지시서 내보내기", use_container_width=True):
        paths = CapCutProjectExporter().export_plan(project, plan)
        st.success("내보내기 완료")
        st.write("JSON:", paths.get("json"))
        st.write("TXT:", paths.get("txt"))

    copybox("CapCut 편집 지시서 미리보기", json.dumps(plan, ensure_ascii=False, indent=2), 420)
