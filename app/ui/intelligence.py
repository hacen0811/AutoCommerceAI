import json
import streamlit as st
from pathlib import Path

from modules.project.repository import ProjectRepository
from modules.video.ai_analyzer import VideoAIAnalyzer
from modules.video.intelligence import VideoIntelligence
from modules.video.ocr_detector import OCRDetector
from app.ui.render import copybox


def show_intelligence():
    st.title("🧠 Video Intelligence")
    st.caption("영상 분석 결과를 바탕으로 CapCut 편집 액션과 쇼핑쇼츠 타임라인을 추천합니다.")

    projects = ProjectRepository().all()
    if not projects:
        st.info("프로젝트가 없습니다.")
        return

    labels = {f"{p.id} | {p.product_name}": p for p in projects}
    project = labels[st.selectbox("프로젝트", list(labels.keys()))]

    if not project.video_path:
        st.warning("이 프로젝트에는 원본 영상이 없습니다. 영상관리에서 먼저 영상을 업로드하세요.")
        return

    sample_count = st.slider("분석 프레임 수", 6, 30, 14, 2)

    if st.button("Video Intelligence 실행", use_container_width=True):
        with st.spinner("영상 프레임과 편집 포인트를 분석 중입니다..."):
            ai_result = VideoAIAnalyzer().analyze(project.video_path, sample_count=sample_count)
            intel = VideoIntelligence().inspect(ai_result)

        if not ai_result.get("ok"):
            st.warning(ai_result.get("error"))
            return

        st.success(intel.get("edit_summary"))

        st.subheader("추천 후킹 프레임")
        hook = intel.get("best_hook_frame", {})
        if hook.get("frame") and Path(hook.get("frame")).exists():
            st.image(hook.get("frame"), width=260)
        st.write(f"시간: {hook.get('time', '-')}초 / 점수: {hook.get('score', '-')}")
        st.caption(hook.get("recommend", ""))

        st.subheader("추천 썸네일 프레임")
        thumb = intel.get("best_thumbnail_frame", {})
        if thumb.get("frame") and Path(thumb.get("frame")).exists():
            st.image(thumb.get("frame"), width=260)
        st.write(f"시간: {thumb.get('time', '-')}초 / 점수: {thumb.get('score', '-')}")
        st.caption(thumb.get("recommend", ""))

        st.subheader("CapCut 액션")
        for action in intel.get("capcut_actions", []):
            with st.container(border=True):
                st.write(f"**{action.get('action')}**: {action.get('value')}")
                st.caption(action.get("reason"))

        st.subheader("20초 쇼핑쇼츠 타임라인")
        for cut in intel.get("shopping_shorts_timeline", []):
            with st.container(border=True):
                st.write(f"**{cut.get('time')} / {cut.get('role')}**")
                st.write(cut.get("guide"))
                st.caption(cut.get("capcut"))

        st.divider()
        st.subheader("자막/워터마크 위험 감지")
        ocr = OCRDetector().detect(project.video_path, sample_count=8)
        if ocr.get("ok"):
            for key, info in ocr.get("risk", {}).items():
                st.write(f"**{key}**: {info.get('level')} / {info.get('ratio')}")
            st.write("추천 자막 위치:", ocr.get("recommendation", {}).get("subtitle_position"))
            st.write("추천 크롭:", ocr.get("recommendation", {}).get("crop"))
        else:
            st.warning(ocr.get("error"))

        copybox("편집 지시서 전체", json.dumps(intel, ensure_ascii=False, indent=2), 360)
        copybox("자막/워터마크 감지 결과", json.dumps(ocr, ensure_ascii=False, indent=2), 360)
