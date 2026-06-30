import streamlit as st
from modules.ai.ai_connector_status import AIConnectorStatus


def show_ai_connectors():
    st.title("🔌 AI 모델 연결")
    st.caption("YOLO와 PaddleOCR 설치 상태를 확인합니다.")

    result = AIConnectorStatus().check_all()

    c1, c2, c3 = st.columns(3)
    c1.metric("연결 완료", f"{result.get('ready_count')}/{result.get('total')}")
    c2.metric("YOLO", "OK" if result["yolo"].get("ready") else "NO")
    c3.metric("PaddleOCR", "OK" if result["paddleocr"].get("ready") else "NO")

    st.subheader("YOLO")
    st.write(result["yolo"].get("message"))
    st.code(result["yolo"].get("install_command"), language="powershell")

    st.subheader("PaddleOCR")
    st.write(result["paddleocr"].get("message"))
    st.code(result["paddleocr"].get("install_command"), language="powershell")

    st.subheader("다음 단계")
    for item in result.get("next_steps", []):
        st.write("•", item)
