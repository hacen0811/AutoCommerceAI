import json
from pathlib import Path
import streamlit as st

from modules.project.repository import ProjectRepository
from modules.video.vision_ai_engine import VisionAIEngine
from app.ui.render import copybox


def show_vision_ai():
    st.title("👁️ Vision AI")
    st.caption("텍스트/자막/워터마크 가능 영역을 분석하고 CapCut 편집값을 추천합니다.")

    projects = ProjectRepository().all()
    if not projects:
        st.info("프로젝트가 없습니다.")
        return

    labels = {f"{p.id} | {p.product_name}": p for p in projects}
    project = labels[st.selectbox("프로젝트", list(labels.keys()))]

    if not project.video_path:
        st.warning("원본 영상이 없습니다. 영상관리에서 먼저 영상을 업로드하세요.")
        return

    sample_count = st.slider("분석 프레임 수", 4, 20, 8, 2)
    use_ocr = st.checkbox("실제 OCR 시도(Tesseract 설치 필요)", value=False)

    if st.button("Vision AI 분석 실행", use_container_width=True):
        with st.spinner("영상 화면 영역을 분석 중입니다..."):
            result = VisionAIEngine().analyze(project.video_path, sample_count=sample_count, use_ocr=use_ocr)

        if not result.get("ok"):
            st.warning(result.get("error"))
            return

        st.success(result.get("guide", {}).get("summary"))

        tab1, tab2, tab3, tab4 = st.tabs(["추천값", "위험 영역", "샘플 프레임", "원본"])

        with tab1:
            st.subheader("CapCut 추천값")
            guide = result.get("guide", {})
            st.write("자막 위치:", guide.get("subtitle_position"))
            st.write("크롭:", guide.get("crop"))
            st.write("블러:", guide.get("blur"))
            st.write("AI 음성:", guide.get("voice_db"))
            st.write("BGM:", guide.get("bgm_db"))
            st.write("Pop:", guide.get("pop_db"))
            st.write("Click:", guide.get("click_db"))
            st.write("Whoosh:", guide.get("whoosh_db"))
            st.write("OCR 상태:", result.get("ocr_status"))

            st.subheader("즉시 적용 액션")
            for action in result.get("capcut_actions", []):
                with st.container(border=True):
                    st.write(f"**{action.get('action')}**: {action.get('value')}")
                    st.caption(action.get("reason"))

        with tab2:
            st.subheader("위험 영역 분석")
            risk = result.get("risk", {})
            labels_ko = {
                "top_text": "상단 텍스트",
                "bottom_caption": "하단 자막",
                "center_product": "중앙 상품/선명도",
                "left_logo": "좌측 로고",
                "right_logo": "우측 로고",
                "bottom_left_mark": "좌하단 워터마크",
                "bottom_right_mark": "우하단 워터마크",
            }

            for key, item in risk.items():
                with st.container(border=True):
                    st.write(f"**{labels_ko.get(key, key)}**")
                    for k, v in item.items():
                        st.write(f"- {k}: {v}")

            if result.get("ocr_texts"):
                st.subheader("OCR 텍스트")
                for item in result.get("ocr_texts", []):
                    st.write(f"{item.get('time')}초 / {item.get('region')}: {item.get('text')}")
            else:
                st.caption("감지된 OCR 텍스트가 없습니다. Tesseract OCR이 설치되어 있지 않거나, OCR 옵션을 끈 상태일 수 있습니다.")

        with tab3:
            if result.get("overlay_image") and Path(result.get("overlay_image")).exists():
                st.subheader("위험 영역 표시 이미지")
                st.image(result.get("overlay_image"), width=360)
            st.subheader("샘플 프레임")
            for item in result.get("sample_images", []):
                if Path(item.get("frame", "")).exists():
                    st.image(item.get("frame"), width=220, caption=f"{item.get('time')}초")

        with tab4:
            copybox("Vision AI JSON", json.dumps(result, ensure_ascii=False, indent=2), 500)
