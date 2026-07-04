import streamlit as st
from pathlib import Path


def show_download_button(label, file_path, mime):
    if not file_path:
        return

    path = Path(file_path)

    if not path.exists():
        return

    with open(path, "rb") as f:
        st.download_button(
            label=label,
            data=f,
            file_name=path.name,
            mime=mime,
            use_container_width=True,
        )


def show_download_center(content_pack):
    st.subheader("다운로드 센터")

    col1, col2 = st.columns(2)

    with col1:
        show_download_button(
            "AI 콘텐츠팩 JSON",
            content_pack.get("json_path"),
            "application/json",
        )

    with col2:
        show_download_button(
            "AI 콘텐츠팩 TXT",
            content_pack.get("txt_path"),
            "text/plain",
        )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        show_download_button(
            "CapCut 편집 TXT",
            content_pack.get("capcut_edit_txt_path"),
            "text/plain",
        )

    with col2:
        show_download_button(
            "썸네일 Prompt TXT",
            content_pack.get("thumbnail_prompt_txt_path"),
            "text/plain",
        )

    col1, col2 = st.columns(2)

    with col1:
        show_download_button(
            "인포크 Prompt TXT",
            content_pack.get("inpock_prompt_txt_path"),
            "text/plain",
        )

    with col2:
        show_download_button(
            "업로드 문구 TXT",
            content_pack.get("upload_txt_path"),
            "text/plain",
        )