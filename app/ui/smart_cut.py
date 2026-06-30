import json
from pathlib import Path
import streamlit as st

from modules.project.repository import ProjectRepository
from modules.video.ai_analyzer import VideoAIAnalyzer
from modules.video.ocr_detector import OCRDetector
from modules.video.smart_cut_engine import SmartCutEngine
from modules.ai.hook_selector import HookSelector
from app.ui.render import copybox


def show_smart_cut():
    st.title("🎯 Smart Cut / Thumbnail AI")
    st.caption("영상에서 후킹 컷, 썸네일 후보, 삭제 후보, 줌 후보를 추천합니다.")

    projects = ProjectRepository().all()
    if not projects:
        st.info("프로젝트가 없습니다.")
        return

    labels = {f"{p.id} | {p.product_name}": p for p in projects}
    project = labels[st.selectbox("프로젝트", list(labels.keys()))]

    if not project.video_path:
        st.warning("원본 영상이 없습니다. 영상관리에서 먼저 영상을 업로드하세요.")
        return

    sample_count = st.slider("분석 프레임 수", 8, 30, 16, 2)

    if st.button("Smart Cut 분석 실행", use_container_width=True):
        with st.spinner("영상 컷과 썸네일 후보를 분석 중입니다..."):
            ai_result = VideoAIAnalyzer().analyze(project.video_path, sample_count=sample_count)
            ocr_result = OCRDetector().detect(project.video_path, sample_count=8)
            smart = SmartCutEngine().build(ai_result, project.product_name, project.keyword)
            hooks = HookSelector().select(project.product_name, project.keyword, smart, ocr_result)

        st.success("Smart Cut 분석 완료")

        tab1, tab2, tab3, tab4 = st.tabs(["추천 컷", "썸네일 후보", "후킹 추천", "전체 JSON"])

        with tab1:
            hook = smart.get("hook_cut", {})
            st.subheader("추천 후킹 컷")
            if hook.get("frame") and Path(hook.get("frame")).exists():
                st.image(hook.get("frame"), width=300)
            st.write("시간:", hook.get("time"))
            st.write("점수:", hook.get("score"))
            st.write("이유:", hook.get("reason"))
            st.caption(hook.get("capcut"))

            st.subheader("20초 편집 타임라인")
            for cut in smart.get("timeline", []):
                with st.container(border=True):
                    st.write(f"**{cut.get('time')} / {cut.get('role')}**")
                    st.write("원본 구간:", cut.get("source_time"))
                    st.write("가이드:", cut.get("guide"))
                    st.write("자막:", cut.get("caption"))
                    st.caption(cut.get("capcut"))

            st.subheader("삭제 후보")
            if not smart.get("delete_candidates"):
                st.write("삭제 후보가 뚜렷하지 않습니다.")
            for item in smart.get("delete_candidates", []):
                st.write(f"• {item.get('time')}초: {item.get('reason')} / {item.get('action')}")

            st.subheader("줌 후보")
            for item in smart.get("zoom_candidates", []):
                st.write(f"• {item.get('time')}초: {item.get('reason')} / {item.get('action')}")

        with tab2:
            for item in smart.get("thumbnail_candidates", []):
                with st.container(border=True):
                    cols = st.columns([1, 3])
                    if item.get("frame") and Path(item.get("frame")).exists():
                        cols[0].image(item.get("frame"), width=180)
                    cols[1].write(f"**후보 {item.get('rank')} / {item.get('time')}초**")
                    cols[1].write("점수:", item.get("score"))
                    cols[1].caption(item.get("reason"))

        with tab3:
            st.subheader("추천 후킹")
            rec = hooks.get("recommended", {})
            st.success(f"{rec.get('hook')} / {rec.get('score')}점")
            st.caption(rec.get("reason"))
            st.write(hooks.get("guide"))

            for item in hooks.get("hooks", []):
                copybox(f"{item.get('type')} / {item.get('score')}점", item.get("hook"), 70)
                st.caption(item.get("reason"))

        with tab4:
            copybox("Smart Cut JSON", json.dumps(smart, ensure_ascii=False, indent=2), 420)
            copybox("Hook AI JSON", json.dumps(hooks, ensure_ascii=False, indent=2), 300)
            copybox("OCR JSON", json.dumps(ocr_result, ensure_ascii=False, indent=2), 300)
