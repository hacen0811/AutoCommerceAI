import json
from pathlib import Path
import streamlit as st

from modules.project.repository import ProjectRepository
from modules.video.object_detector import ObjectDetector
from app.ui.render import copybox


def show_object_ai():
    st.title("🧲 Object AI Starter")
    st.caption("상품/손동작/썸네일 후보 장면을 OpenCV 기반으로 추천합니다.")

    projects = ProjectRepository().all()
    if not projects:
        st.info("프로젝트가 없습니다.")
        return

    labels = {f"{p.id} | {p.product_name}": p for p in projects}
    project = labels[st.selectbox("프로젝트", list(labels.keys()))]

    if not project.video_path:
        st.warning("원본 영상이 없습니다. 영상관리에서 먼저 영상을 업로드하세요.")
        return

    sample_count = st.slider("분석 프레임 수", 6, 24, 10, 2)

    if st.button("Object AI 분석 실행", use_container_width=True):
        with st.spinner("상품/움직임 후보를 분석 중입니다..."):
            result = ObjectDetector().detect(project.video_path, sample_count=sample_count)

        if not result.get("ok"):
            st.warning(result.get("error"))
            return

        st.success("Object AI 분석 완료")

        tab1, tab2, tab3 = st.tabs(["추천 장면", "움직임 후보", "원본"])

        with tab1:
            st.subheader("상품/썸네일 후보")
            for item in result.get("best_product_frames", []):
                with st.container(border=True):
                    cols = st.columns([1, 3])
                    if item.get("frame") and Path(item.get("frame")).exists():
                        cols[0].image(item.get("frame"), width=180)
                    cols[1].write(f"**{item.get('time')}초 / 점수 {item.get('score')}**")
                    cols[1].write(item.get("recommend"))
                    cols[1].caption(f"움직임 {item.get('movement')}")
            st.subheader("추천 가이드")
            for k, v in result.get("guide", {}).items():
                st.write(f"**{k}**: {v}")

        with tab2:
            for item in result.get("best_motion_frames", []):
                st.write(f"• {item.get('time')}초 / 움직임 {item.get('movement')} / {item.get('recommend')}")

        with tab3:
            copybox("Object AI JSON", json.dumps(result, ensure_ascii=False, indent=2), 500)
