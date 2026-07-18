import streamlit as st


def render_dashboard():
    st.subheader("대시보드")

    st.write("현재 목표: 쿠팡 링크 하나로 쇼핑쇼츠 생성 AI 완성")
    st.write("현재 단계: GPT 쇼츠 생성 + UI 모듈화")

    st.markdown("### 진행 상황")
    st.markdown("""
- ✅ GitHub 저장소 연결
- ✅ Streamlit 실행
- ✅ 쿠팡 링크 분석
- ✅ OpenAI 연결
- ✅ GPT 쇼츠 생성
- ✅ UI 모듈화 진행
- ⬜ 복사 버튼
- ⬜ TXT / PDF / DOCX 저장
- ⬜ 쿠팡 상품명 자동 추출
""")