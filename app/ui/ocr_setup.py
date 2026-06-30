import streamlit as st
from modules.video.ocr_setup import OCRSetupChecker


def show_ocr_setup():
    st.title("🧩 OCR 설치 확인")
    st.caption("실제 중국어/한국어/영어 자막 인식을 위한 Tesseract OCR 상태를 확인합니다.")

    result = OCRSetupChecker().check()

    c1, c2, c3 = st.columns(3)
    c1.metric("pytesseract", "OK" if result["pytesseract"] else "NO")
    c2.metric("Tesseract 프로그램", "OK" if result["tesseract_program"] else "NO")
    c3.metric("OCR 준비", "OK" if result["ready"] else "NO")

    st.write("상태:", result["message"])
    st.write("버전:", result.get("version") or "-")
    st.write("언어팩:", ", ".join(result.get("languages", [])) or "-")

    st.subheader("설치 가이드")
    for item in result["install_guide"]:
        st.write("•", item)

    st.info("OCR이 준비되면 Vision AI에서 '실제 OCR 시도'를 켜고 중국어 자막 인식을 테스트할 수 있습니다.")
