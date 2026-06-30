import json
import streamlit as st
from modules.project.repository import ProjectRepository
from modules.capcut.preset_engine import CapCutPresetEngine
from app.ui.render import copybox


def show_capcut():
    st.title("✂️ CapCut 편집")

    st.subheader("하센 CapCut 프리셋")
    engine = CapCutPresetEngine()
    preset_name = st.selectbox("프리셋 선택", list(engine.presets().keys()))
    copybox("프리셋 지시서", engine.guide_text(preset_name), 300)

    st.divider()

    projects = ProjectRepository().all()
    if not projects:
        st.info("프로젝트가 없습니다.")
        return

    labels = {f"{p.id} | {p.product_name}": p for p in projects}
    project = labels[st.selectbox("프로젝트", list(labels.keys()))]
    data = json.loads(project.data_json or "{}")
    capcut = data.get("capcut", {})
    video_analysis = data.get("video_analysis", {})

    st.subheader("프로젝트 CapCut 지시서")
    for key, value in capcut.items():
        if isinstance(value, list):
            copybox(key, "\n".join(value), 170)
        elif isinstance(value, dict):
            copybox(key, "\n".join(f"{k}: {v}" for k, v in value.items()), 170)
        else:
            st.write(f"**{key}**: {value}")

    st.subheader("영상 기반 안전영역")
    safe = video_analysis.get("safe_area", {})
    for key, value in safe.items():
        st.write(f"**{key}**: {value}")
