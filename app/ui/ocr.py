import json
import streamlit as st

from modules.project.repository import ProjectRepository
from modules.video.ocr_detector import OCRDetector
from app.ui.render import copybox


def show_ocr():
    st.title("🔍 OCR/자막 위험 감지")
    st.caption("중국어 자막·워터마크 가능 영역을 감지하고 CapCut 편집 위치를 추천합니다.")

    projects = ProjectRepository().all()
    if not projects:
        st.info("프로젝트가 없습니다.")
        return

    labels = {f"{p.id} | {p.product_name}": p for p in projects}
    project = labels[st.selectbox("프로젝트", list(labels.keys()))]

    if not project.video_path:
        st.warning("이 프로젝트에는 원본 영상이 없습니다. 영상관리에서 먼저 영상을 업로드하세요.")
        return

    sample_count = st.slider("분석 프레임 수", 4, 20, 8, 2)

    if st.button("자막/워터마크 위험 감지 실행", use_container_width=True):
        with st.spinner("영상 영역을 분석 중입니다..."):
            result = OCRDetector().detect(project.video_path, sample_count=sample_count)

        if not result.get("ok"):
            st.warning(result.get("error"))
            return

        st.success("감지 완료")

        st.subheader("위험도 요약")
        risk = result.get("risk", {})
        labels_ko = {
            "top_text": "상단 텍스트",
            "bottom_caption": "하단 자막",
            "left_logo": "좌측 로고",
            "right_logo": "우측 로고",
            "bottom_left_mark": "좌하단 워터마크",
            "bottom_right_mark": "우하단 워터마크",
        }

        for key, info in risk.items():
            st.write(f"**{labels_ko.get(key, key)}**: {info.get('level')} / 감지 {info.get('hit_count')}회 / 비율 {info.get('ratio')}")

        st.subheader("CapCut 추천")
        rec = result.get("recommendation", {})
        st.write("자막 위치:", rec.get("subtitle_position"))
        st.write("크롭:", rec.get("crop"))
        st.write("블러:", rec.get("blur"))

        st.subheader("즉시 적용 액션")
        for action in result.get("capcut_actions", []):
            with st.container(border=True):
                st.write(f"**{action.get('action')}**: {action.get('value')}")
                st.caption(action.get("reason"))

        copybox("OCR/자막 위험 감지 JSON", json.dumps(result, ensure_ascii=False, indent=2), 420)
