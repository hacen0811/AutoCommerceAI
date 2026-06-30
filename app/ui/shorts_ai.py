import json
import streamlit as st

from modules.project.repository import ProjectRepository
from modules.video.ai_analyzer import VideoAIAnalyzer
from modules.video.intelligence import VideoIntelligence
from modules.video.ocr_detector import OCRDetector
from modules.ai.shopping_shorts_engine import ShoppingShortsEngine
from app.ui.render import copybox


def show_shorts_ai():
    st.title("🤖 쇼핑쇼츠 AI")
    st.caption("영상 분석 결과를 바탕으로 후킹, 대본, 썸네일, CapCut 타임라인을 생성합니다.")

    projects = ProjectRepository().all()
    if not projects:
        st.info("프로젝트가 없습니다.")
        return

    labels = {f"{p.id} | {p.product_name}": p for p in projects}
    project = labels[st.selectbox("프로젝트", list(labels.keys()))]

    keyword = st.text_input("댓글 키워드", value=project.keyword or "정보")

    if not project.video_path:
        st.warning("원본 영상이 없으면 영상 기반 분석 없이 기본 쇼핑쇼츠 패키지를 생성합니다.")

    sample_count = st.slider("영상 분석 프레임 수", 6, 24, 12, 2)

    if st.button("쇼핑쇼츠 패키지 생성", use_container_width=True):
        video_intel = {}
        ocr_result = {}

        if project.video_path:
            with st.spinner("영상 분석 중..."):
                ai_result = VideoAIAnalyzer().analyze(project.video_path, sample_count=sample_count)
                video_intel = VideoIntelligence().inspect(ai_result)
                ocr_result = OCRDetector().detect(project.video_path, sample_count=8)

        package = ShoppingShortsEngine().generate(
            product_name=project.product_name,
            keyword=keyword,
            video_intel=video_intel,
            ocr_result=ocr_result,
        )

        st.success("쇼핑쇼츠 패키지 생성 완료")

        tab1, tab2, tab3, tab4, tab5 = st.tabs(["전략", "후킹/대본", "CapCut 타임라인", "업로드 문구", "원본"])

        with tab1:
            strategy = package.get("strategy", {})
            st.subheader("추천 전략")
            st.write("유형:", strategy.get("recommended_type"))
            st.write("이유:", strategy.get("reason"))
            st.write("후킹 프레임:", strategy.get("hook_frame"))
            st.write("자막 위치:", strategy.get("subtitle_position"))
            st.write("크롭:", strategy.get("crop"))
            st.write("CTA:", strategy.get("cta"))
            st.subheader("오디오 dB")
            for k, v in strategy.get("audio", {}).items():
                st.write(f"**{k}**: {v}")

        with tab2:
            hooks = package.get("hooks", {})
            for group, items in hooks.items():
                st.subheader(group)
                for i, hook in enumerate(items, 1):
                    copybox(f"{group} {i}", hook, 70)

            scripts = package.get("scripts", {})
            for name, lines in scripts.items():
                copybox(name, "\n".join(lines), 200)

            copybox("썸네일", "\n".join(package.get("thumbnail", [])), 120)

        with tab3:
            for item in package.get("capcut_timeline", []):
                with st.container(border=True):
                    st.write(f"**{item.get('time')} / {item.get('scene')}**")
                    st.write("자막:", item.get("caption"))
                    st.caption(item.get("capcut"))

        with tab4:
            for key, value in package.get("platform_copy", {}).items():
                copybox(key, value, 130)

            st.subheader("업로드 체크")
            for item in package.get("upload_check", []):
                st.write("□", item)

        with tab5:
            copybox("쇼핑쇼츠 패키지 JSON", json.dumps(package, ensure_ascii=False, indent=2), 450)
