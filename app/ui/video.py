import json
import streamlit as st
from pathlib import Path

from modules.project.repository import ProjectRepository
from modules.project.project_selector import ProjectSelector
from modules.video.service import VideoService
from modules.video.analyzer import VideoAnalyzer
from modules.video.ai_analyzer import VideoAIAnalyzer
from modules.video.intelligence import VideoIntelligence
from app.ui.render import copybox


def show_video():
    st.title("🎬 영상관리 / AI 분석")
    projects = ProjectSelector().all_projects()
    if not projects:
        st.info("프로젝트가 없습니다.")
        return

    labels = ProjectSelector().labels(projects)
    project = labels[st.selectbox("프로젝트", list(labels.keys()))]

    uploaded_video = st.file_uploader("원본 영상 추가/교체", type=["mp4", "mov", "webm"])
    if st.button("영상 저장", use_container_width=True):
        if not uploaded_video:
            st.warning("영상 파일을 업로드하세요.")
            return
        video_path = VideoService().save_uploaded_video(uploaded_video)
        ProjectRepository().update_links_and_media(project.id, video_path=video_path)
        ProjectRepository().update_checklist(project.id, source_video=True)
        st.success(f"영상 저장 완료: {video_path}")
        st.rerun()

    project = ProjectRepository().get(project.id) or project
    video_path = project.video_path

    tab1, tab2 = st.tabs(["기본 분석", "AI 프레임 분석"])

    with tab1:
        analysis = VideoAnalyzer().analyze(video_path)
        st.subheader("영상 기본 정보")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("파일", analysis.get("filename") or "-")
        c2.metric("크기", f"{analysis.get('size_mb', 0)} MB")
        c3.metric("해상도", f"{analysis.get('width') or '-'} x {analysis.get('height') or '-'}")
        c4.metric("FPS", analysis.get("fps") or "-")

        st.write("방향:", analysis.get("orientation") or "-")
        st.write("길이:", analysis.get("duration") or "-")

        st.subheader("자막 안전영역")
        for key, value in analysis.get("safe_area", {}).items():
            st.write(f"**{key}**: {value}")

        st.subheader("편집 위험 요소")
        for item in analysis.get("edit_risk", []):
            st.write("⚠️", item)

        st.subheader("추천 컷 타임라인")
        for cut in analysis.get("timeline", []):
            with st.container(border=True):
                st.write(f"**{cut.get('time')} / {cut.get('use')}**")
                st.write(cut.get("guide"))
                st.caption(cut.get("capcut"))

    with tab2:
        st.caption("OpenCV 기반 샘플 프레임 분석입니다. OCR/객체 인식은 다음 단계에서 확장합니다.")
        sample_count = st.slider("샘플 프레임 수", min_value=6, max_value=24, value=12, step=2)

        if st.button("AI 프레임 분석 실행", use_container_width=True):
            with st.spinner("프레임을 분석 중입니다..."):
                result = VideoAIAnalyzer().analyze(video_path, sample_count=sample_count)

            if not result.get("ok"):
                st.warning(result.get("error", "분석 실패"))
            else:
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("길이", result.get("duration", "-"))
                c2.metric("해상도", f"{result.get('width')} x {result.get('height')}")
                c3.metric("FPS", result.get("fps", "-"))
                c4.metric("방향", result.get("orientation", "-"))

                st.subheader("추천 썸네일/후킹 프레임 TOP")
                for frame in result.get("top_frames", []):
                    with st.container(border=True):
                        cols = st.columns([1, 3])
                        if Path(frame.get("frame", "")).exists():
                            cols[0].image(frame.get("frame"), width=160)
                        cols[1].write(f"**{frame.get('time')}초 / 점수 {frame.get('score')}**")
                        cols[1].write(frame.get("recommend"))
                        cols[1].caption(f"밝기 {frame.get('brightness')} / 대비 {frame.get('contrast')} / 변화 {frame.get('change')}")

                st.subheader("장면 전환 후보")
                for s in result.get("scene_changes", []):
                    st.write(f"• {s.get('time')}초 / 변화도 {s.get('change')} / 점수 {s.get('score')}")

                st.subheader("AI 타임라인")
                for cut in result.get("timeline", []):
                    with st.container(border=True):
                        st.write(f"**{cut.get('time')} / {cut.get('role')}**")
                        st.write(cut.get("guide"))
                        st.caption(cut.get("capcut"))

                st.subheader("자막 안전영역")
                for key, value in result.get("caption_safety", {}).items():
                    st.write(f"**{key}**: {value}")

                st.divider()
                st.header("Video Intelligence")
                intel = VideoIntelligence().inspect(result)
                st.success(intel.get("edit_summary"))

                st.subheader("CapCut 즉시 적용 액션")
                for action in intel.get("capcut_actions", []):
                    with st.container(border=True):
                        st.write(f"**{action.get('action')}**: {action.get('value')}")
                        st.caption(action.get("reason"))

                st.subheader("쇼핑쇼츠 타임라인")
                for cut in intel.get("shopping_shorts_timeline", []):
                    with st.container(border=True):
                        st.write(f"**{cut.get('time')} / {cut.get('role')}**")
                        st.write(cut.get("guide"))
                        st.caption(cut.get("capcut"))

                st.subheader("다음 작업")
                for step in intel.get("next_step", []):
                    st.write("✅", step)

                copybox("AI 영상 분석 JSON", json.dumps(result, ensure_ascii=False, indent=2), 350)
                copybox("Video Intelligence JSON", json.dumps(intel, ensure_ascii=False, indent=2), 350)
