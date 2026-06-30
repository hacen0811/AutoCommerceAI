import json
from pathlib import Path
import streamlit as st

from modules.project.repository import ProjectRepository
from modules.pipeline.real_vision_pipeline import RealVisionPipeline
from modules.pipeline.report_repository import PipelineReportRepository
from app.ui.render import copybox


def show_real_vision():
    st.title("🚀 Real Vision MVP")
    st.caption("YOLO + PaddleOCR + Smart Cut + Auto Editor를 한 번에 실행합니다.")

    projects = ProjectRepository().all()
    if not projects:
        st.info("프로젝트가 없습니다.")
        return

    labels = {f"{p.id} | {p.product_name}": p for p in projects}
    project = labels[st.selectbox("프로젝트", list(labels.keys()))]

    if not project.video_path:
        st.warning("원본 영상이 없습니다. 영상관리에서 먼저 영상을 업로드하세요.")
        return

    c1, c2, c3 = st.columns(3)
    sample_count = c1.slider("분석 프레임 수", 4, 16, 6, 2)
    run_yolo = c2.checkbox("YOLO 실행", value=True)
    run_paddle = c3.checkbox("PaddleOCR 실행", value=True)

    if st.button("Real Vision 실행", use_container_width=True):
        with st.spinner("실제 AI 파이프라인을 실행 중입니다. 첫 실행은 오래 걸릴 수 있습니다..."):
            report = RealVisionPipeline().run(
                project,
                sample_count=sample_count,
                run_yolo=run_yolo,
                run_paddle=run_paddle,
            )

        paths = PipelineReportRepository().save(project, report)

        st.success(report.get("summary"))

        s1, s2, s3, s4 = st.columns(4)
        status = report.get("status", {})
        s1.metric("Video AI", "OK" if status.get("video_ai") else "NO")
        s2.metric("Vision", "OK" if status.get("vision") else "NO")
        s3.metric("YOLO", "OK" if status.get("yolo") else "NO")
        s4.metric("PaddleOCR", "OK" if status.get("paddleocr") else "NO")

        st.write("저장:", paths)

        tab1, tab2, tab3, tab4, tab5 = st.tabs(["다음 작업", "추천 컷", "Auto Editor", "콘텐츠", "원본"])

        with tab1:
            for item in report.get("next_actions", []):
                st.write("✅", item)

            st.subheader("Caption Safe")
            safe = report.get("caption_safe", {})
            st.write("자막 위치:", safe.get("safe_subtitle_position"))
            st.write("크롭:", safe.get("crop"))
            st.write("블러:", safe.get("blur"))

        with tab2:
            smart = report.get("smart_cut", {})
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
            plan = report.get("auto_editor", {})
            st.subheader("CapCut 프리셋")
            for k, v in plan.get("capcut_preset", {}).items():
                st.write(f"**{k}**: {v}")

            st.subheader("타임라인")
            for cut in plan.get("timeline", []):
                with st.container(border=True):
                    st.write(f"**{cut.get('time')} / {cut.get('role') or cut.get('scene')}**")
                    st.write("자막:", cut.get("caption"))
                    st.caption(cut.get("capcut"))

        with tab4:
            shorts = report.get("shopping_shorts", {})
            strategy = shorts.get("strategy", {})
            st.write("추천 유형:", strategy.get("recommended_type"))
            st.write("이유:", strategy.get("reason"))

            for name, lines in shorts.get("scripts", {}).items():
                copybox(name, "\n".join(lines), 190)

            for key, value in shorts.get("platform_copy", {}).items():
                copybox(key, value, 120)

        with tab5:
            copybox("Real Vision Report JSON", json.dumps(report, ensure_ascii=False, indent=2), 600)
