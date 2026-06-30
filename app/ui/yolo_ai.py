import json
from pathlib import Path
import streamlit as st

from modules.project.repository import ProjectRepository
from modules.video.yolo_engine import YOLOEngine
from app.ui.render import copybox


def show_yolo_ai():
    st.title("🧠 YOLO Vision")
    st.caption("YOLOv8로 객체를 탐지해 후킹/썸네일/확대 후보를 추천합니다.")

    status = YOLOEngine().check()
    if not status.get("ready"):
        st.warning(status.get("message"))
        st.code(status.get("install_command"), language="powershell")
        st.info("설치 후 프로그램을 재시작하세요.")

    projects = ProjectRepository().all()
    if not projects:
        st.info("프로젝트가 없습니다.")
        return

    labels = {f"{p.id} | {p.product_name}": p for p in projects}
    project = labels[st.selectbox("프로젝트", list(labels.keys()))]

    if not project.video_path:
        st.warning("원본 영상이 없습니다. 영상관리에서 먼저 영상을 업로드하세요.")
        return

    sample_count = st.slider("분석 프레임 수", 2, 12, 4, 1)
    model_name = st.text_input("YOLO 모델", value="yolov8n.pt")

    if st.button("YOLO 분석 실행", use_container_width=True):
        with st.spinner("YOLO 분석 중입니다. 첫 실행은 모델 다운로드 때문에 시간이 걸릴 수 있습니다..."):
            result = YOLOEngine().analyze_video(project.video_path, sample_count=sample_count, model_name=model_name)

        if not result.get("ok"):
            st.warning(result.get("error"))
            return

        st.success(result.get("guide", {}).get("summary"))

        tab1, tab2, tab3 = st.tabs(["추천", "감지 결과", "원본"])

        with tab1:
            guide = result.get("guide", {})
            for k, v in guide.items():
                st.write(f"**{k}**: {v}")

            st.subheader("CapCut 액션")
            for action in result.get("capcut_actions", []):
                with st.container(border=True):
                    st.write(f"**{action.get('action')}**: {action.get('value')}")
                    st.caption(action.get("reason"))

        with tab2:
            if not result.get("detections"):
                st.info("감지된 객체가 없습니다.")
            for d in result.get("detections", []):
                st.write(f"• {d.get('time')}초 / {d.get('label')} / {d.get('confidence')} / {d.get('role')}")

            st.subheader("샘플 이미지")
            for item in result.get("sample_images", []):
                if Path(item.get("frame", "")).exists():
                    st.image(item.get("frame"), width=260, caption=f"{item.get('time')}초")

        with tab3:
            copybox("YOLO JSON", json.dumps(result, ensure_ascii=False, indent=2), 500)
