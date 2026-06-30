import streamlit as st
from config.app_config import AppConfig


def show_settings():
    st.title("⚙️ 설정")
    st.caption("AutoCommerceAI 기본값을 관리합니다.")

    cfg = AppConfig().load()

    st.subheader("CapCut 기본값")
    capcut = cfg.get("capcut", {})
    capcut["voice_db"] = st.text_input("AI 음성", value=capcut.get("voice_db", "20 dB"))
    capcut["bgm_db"] = st.text_input("BGM", value=capcut.get("bgm_db", "8 dB"))
    capcut["pop_db"] = st.text_input("Pop", value=capcut.get("pop_db", "7 dB"))
    capcut["click_db"] = st.text_input("Click", value=capcut.get("click_db", "8 dB"))
    capcut["whoosh_db"] = st.text_input("Whoosh", value=capcut.get("whoosh_db", "6 dB"))
    capcut["subtitle_position"] = st.text_input("자막 위치", value=capcut.get("subtitle_position", "중앙 하단 / 하단 40%"))
    cfg["capcut"] = capcut

    st.subheader("AI 모델")
    models = cfg.get("ai_models", {})
    models["yolo_model"] = st.text_input("YOLO 모델", value=models.get("yolo_model", "yolov8n.pt"))
    models["paddleocr_lang"] = st.selectbox(
        "PaddleOCR 언어",
        ["ch", "korean", "en"],
        index=["ch", "korean", "en"].index(models.get("paddleocr_lang", "ch")) if models.get("paddleocr_lang", "ch") in ["ch", "korean", "en"] else 0,
    )
    cfg["ai_models"] = models

    if st.button("설정 저장", use_container_width=True):
        AppConfig().save(cfg)
        st.success("설정 저장 완료")
