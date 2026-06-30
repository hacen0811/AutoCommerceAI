import json
from pathlib import Path
import streamlit as st

from modules.project.repository import ProjectRepository
from modules.video.paddle_ocr_engine import PaddleOCREngine
from app.ui.render import copybox


def show_paddle_ocr():
    st.title("🧠 PaddleOCR")
    st.caption("중국어/한국어/영어 자막을 실제 OCR로 인식하는 선택 기능입니다.")

    engine = PaddleOCREngine()
    status = engine.check()

    c1, c2 = st.columns(2)
    c1.metric("PaddleOCR", "OK" if status.get("installed") else "NO")
    c2.metric("사용 가능", "OK" if status.get("ready") else "NO")
    st.write(status.get("message"))
    st.code(status.get("install_command"), language="powershell")

    projects = ProjectRepository().all()
    if not projects:
        st.info("프로젝트가 없습니다.")
        return

    labels = {f"{p.id} | {p.product_name}": p for p in projects}
    project = labels[st.selectbox("프로젝트", list(labels.keys()))]

    if not project.video_path:
        st.warning("원본 영상이 없습니다. 영상관리에서 먼저 영상을 업로드하세요.")
        return

    sample_count = st.slider("OCR 분석 프레임 수", 2, 12, 4, 1)
    lang = st.selectbox("OCR 언어", ["ch", "korean", "en"], index=0)

    if st.button("PaddleOCR 분석 실행", use_container_width=True):
        with st.spinner("OCR 분석 중입니다. 영상과 PC 성능에 따라 시간이 걸릴 수 있습니다..."):
            result = engine.analyze_video(project.video_path, sample_count=sample_count, lang=lang)

        if not result.get("ok"):
            st.warning(result.get("error"))
            return

        st.success(result.get("guide", {}).get("summary"))

        tab1, tab2, tab3 = st.tabs(["CapCut 추천", "감지 텍스트", "원본"])

        with tab1:
            guide = result.get("guide", {})
            st.write("자막 위치:", guide.get("subtitle_position"))
            st.write("크롭:", guide.get("crop"))
            st.write("블러:", guide.get("blur"))
            st.write("AI 음성:", guide.get("voice_db"))
            st.write("BGM:", guide.get("bgm_db"))

            for action in result.get("capcut_actions", []):
                with st.container(border=True):
                    st.write(f"**{action.get('action')}**: {action.get('value')}")
                    st.caption(action.get("reason"))

        with tab2:
            detections = result.get("detections", [])
            if not detections:
                st.info("감지된 텍스트가 없습니다.")
            for d in detections:
                with st.container(border=True):
                    st.write(f"**{d.get('time')}초 / {d.get('region')} / score {d.get('score')}**")
                    st.write(d.get("text") or d.get("error", ""))
                    st.caption(d.get("box"))

        with tab3:
            for item in result.get("sample_images", []):
                if Path(item.get("frame", "")).exists():
                    st.image(item.get("frame"), width=240, caption=f"{item.get('time')}초")
            copybox("PaddleOCR JSON", json.dumps(result, ensure_ascii=False, indent=2), 500)
