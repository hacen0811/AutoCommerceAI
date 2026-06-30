import json
import streamlit as st
from modules.project.repository import ProjectRepository
from modules.project.project_selector import ProjectSelector
from modules.video.ai_analyzer import VideoAIAnalyzer
from modules.video.vision_ai_engine import VisionAIEngine
from modules.video.yolo_engine import YOLOEngine
from modules.video.paddle_ocr_engine import PaddleOCREngine
from modules.video.smart_cut_engine import SmartCutEngine
from modules.ai.shopping_shorts_engine import ShoppingShortsEngine
from modules.editor.auto_editor_engine import AutoEditorEngine
from app.ui.render import copybox


def show_auto_editor():
    st.title("🎬 Auto Editor")
    st.caption("영상 분석 결과를 바탕으로 CapCut 편집 지시서를 자동 생성합니다.")

    projects = ProjectSelector().all_projects()
    if not projects:
        st.info("프로젝트가 없습니다.")
        return

    labels = ProjectSelector().labels(projects)
    project = labels[st.selectbox("프로젝트", list(labels.keys()))]

    sample_count = st.slider("분석 프레임 수", 8, 30, 16, 2)

    if st.button("Auto Editor 실행", use_container_width=True):
        ai_result = {}
        vision = {}
        smart = {}
        shorts = {}

        if project.video_path:
            with st.spinner("영상 분석 중..."):
                ai_result = VideoAIAnalyzer().analyze(project.video_path, sample_count=sample_count)
                vision = VisionAIEngine().analyze(project.video_path, sample_count=8, use_ocr=False)
                smart = SmartCutEngine().build(ai_result, project.product_name, project.keyword)
                yolo = YOLOEngine().analyze_video(project.video_path, sample_count=4)
                paddle = PaddleOCREngine().analyze_video(project.video_path, sample_count=2)

        shorts = ShoppingShortsEngine().generate(project.product_name, project.keyword, smart, vision)
        plan = AutoEditorEngine().create_plan(project.product_name, project.keyword, smart, vision, shorts)

        st.success(plan.get("summary"))

        tab1, tab2, tab3 = st.tabs(["CapCut 설정", "편집 타임라인", "전체 JSON"])

        with tab1:
            preset = plan.get("capcut_preset", {})
            for k, v in preset.items():
                st.write(f"**{k}**: {v}")
            st.subheader("내보내기 체크리스트")
            for item in plan.get("export_checklist", []):
                st.write("□", item)

        with tab2:
            for cut in plan.get("timeline", []):
                with st.container(border=True):
                    st.write(f"**{cut.get('time')} / {cut.get('role') or cut.get('scene')}**")
                    if cut.get("guide"):
                        st.write(cut.get("guide"))
                    st.write("자막:", cut.get("caption"))
                    st.caption(cut.get("capcut"))

        with tab3:
            try:
                copybox("YOLO 결과", json.dumps(yolo, ensure_ascii=False, indent=2), 300)
                copybox("PaddleOCR 결과", json.dumps(paddle, ensure_ascii=False, indent=2), 300)
            except Exception:
                pass
            copybox("Auto Editor Plan JSON", json.dumps(plan, ensure_ascii=False, indent=2), 500)
