import json
from pathlib import Path
import streamlit as st

from modules.project.repository import ProjectRepository
from modules.project.project_selector import ProjectSelector
from modules.pipeline.real_vision_runner import RealVisionRunner
from modules.pipeline.vision_result_repository import VisionResultRepository
from app.ui.render import copybox


def show_real_vision_runner():
    st.title("🚀 Real Vision Runner")
    st.caption("설치된 AI 모델은 실제 실행하고, 미설치 모델은 자동 대체 분석으로 이어갑니다.")

    projects = ProjectSelector().all_projects()
    if not projects:
        st.info("프로젝트가 없습니다.")
        return

    labels = ProjectSelector().labels(projects)
    project = labels[st.selectbox("프로젝트", list(labels.keys()))]

    if not project.video_path:
        st.warning("원본 영상이 없습니다. 영상관리에서 먼저 영상을 업로드하세요.")
        return

    c1, c2, c3 = st.columns(3)
    sample_count = c1.slider("분석 프레임 수", 4, 20, 8, 2)
    use_yolo = c2.checkbox("YOLO 실제 실행 시도", value=True)
    use_paddle = c3.checkbox("PaddleOCR 실제 실행 시도", value=True)

    if st.button("실제 Vision 분석 실행", use_container_width=True):
        with st.spinner("영상 분석 중입니다. YOLO/PaddleOCR가 설치된 경우 시간이 오래 걸릴 수 있습니다..."):
            result = RealVisionRunner().run(project, sample_count=sample_count, use_yolo=use_yolo, use_paddle=use_paddle)

        if not result.get("ok"):
            st.warning(result.get("summary"))
            return

        saved_path = VisionResultRepository().save(project, result)

        st.success(result.get("summary"))
        st.write("결과 저장:", saved_path)

        status = result.get("status", {})
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Video AI", "OK" if status.get("video_ai") else "NO")
        s2.metric("Vision AI", "OK" if status.get("vision_ai") else "NO")
        s3.metric("YOLO", "OK" if status.get("yolo") else "대체")
        s4.metric("PaddleOCR", "OK" if status.get("paddleocr") else "대체")

        if result.get("fallback_used"):
            st.info(" / ".join(result.get("fallback_used")))

        tab1, tab2, tab3, tab4, tab5 = st.tabs(["다음 작업", "추천컷", "CapCut", "콘텐츠", "전체 결과"])

        with tab1:
            for item in result.get("next_actions", []):
                st.write("✅", item)

        with tab2:
            smart = result.get("smart_cut", {})
            hook = smart.get("hook_cut", {})
            st.subheader("후킹 컷")
            if hook.get("frame") and Path(hook.get("frame")).exists():
                st.image(hook.get("frame"), width=320)
            st.write("시간:", hook.get("time"))
            st.write("점수:", hook.get("score"))
            st.caption(hook.get("capcut"))

            st.subheader("썸네일 후보")
            for item in smart.get("thumbnail_candidates", [])[:5]:
                with st.container(border=True):
                    cols = st.columns([1, 3])
                    if item.get("frame") and Path(item.get("frame")).exists():
                        cols[0].image(item.get("frame"), width=160)
                    cols[1].write(f"**{item.get('rank')}위 / {item.get('time')}초**")
                    cols[1].write("점수:", item.get("score"))
                    cols[1].caption(item.get("reason"))

        with tab3:
            editor = result.get("auto_editor", {})
            st.subheader("CapCut 프리셋")
            for k, v in editor.get("capcut_preset", {}).items():
                st.write(f"**{k}**: {v}")

            st.subheader("타임라인")
            for cut in editor.get("timeline", []):
                with st.container(border=True):
                    st.write(f"**{cut.get('time')} / {cut.get('role') or cut.get('scene')}**")
                    st.write("자막:", cut.get("caption"))
                    st.caption(cut.get("capcut"))

        with tab4:
            shorts = result.get("shopping_shorts", {})
            for name, lines in shorts.get("scripts", {}).items():
                copybox(name, "\n".join(lines), 180)
            for key, value in shorts.get("platform_copy", {}).items():
                copybox(key, value, 120)

        with tab5:
            copybox("Real Vision Runner JSON", json.dumps(result, ensure_ascii=False, indent=2), 600)

    st.divider()
    st.subheader("최근 분석 결과")
    for f in VisionResultRepository().latest_files(10):
        st.write(f"• {f.name}")
