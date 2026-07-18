import streamlit as st


def render_inpock_tab(ai: dict):
    st.subheader("인포크")

    inpock = ai.get("inpock", {})

    st.markdown("### 제목")
    st.write(inpock.get("title", ""))

    st.markdown("### 설명")
    st.write(inpock.get("description", ""))

    st.markdown("### 1000x1000 이미지 문구")
    st.success(inpock.get("image_text", ""))

    st.markdown("### 사이즈")
    st.code(inpock.get("size", "1000x1000"))