from pathlib import Path

import streamlit as st


def show_download_button(label, file_path, mime="text/plain"):
    if not file_path:
        return

    path = Path(file_path)

    if not path.exists():
        st.caption(f"{label} 파일을 찾을 수 없습니다.\n{file_path}")
        return

    st.download_button(
        label=label,
        data=path.read_bytes(),
        file_name=path.name,
        mime=mime,
        use_container_width=True,
    )


def show_download_center(content_pack_result):
    st.error("DOWNLOAD CENTER TEST")
    
    st.divider()
    st.subheader("📁 다운로드 센터")

    st.write("DEBUG content_pack_result")
    st.json(content_pack_result)

    if not content_pack_result:
        st.info("아직 생성된 콘텐츠 팩이 없습니다.")
        return

    json_path = (
        content_pack_result.get("json_path")
        or content_pack_result.get("json")
    )

    txt_path = (
        content_pack_result.get("txt_path")
        or content_pack_result.get("txt")
    )

    capcut_edit_path = (
        content_pack_result.get("capcut_edit_txt_path")
        or content_pack_result.get("capcut_edit_txt")
    )

    thumbnail_prompt_path = (
        content_pack_result.get("thumbnail_prompt_txt_path")
        or content_pack_result.get("thumbnail_prompt_txt")
    )

    inpock_prompt_path = (
        content_pack_result.get("inpock_prompt_txt_path")
        or content_pack_result.get("inpock_prompt_txt")
    )

    upload_path = (
        content_pack_result.get("upload_txt_path")
        or content_pack_result.get("upload_txt")
    )

    capcut_export_path = (
        content_pack_result.get("capcut_export_json_path")
        or content_pack_result.get("capcut_export_json")
    )

    capcut_draft_path = (
        content_pack_result.get("capcut_draft_json_path")
        or content_pack_result.get("capcut_draft_json")
    )
    if not capcut_draft_path and content_pack_result.get("json_path"):
        capcut_draft_path = content_pack_result.get("json_path").replace(
            "_content_pack_",
            "_capcut_draft_",
        )

    st.markdown("### AI 콘텐츠 팩")

    c1, c2 = st.columns(2)

    with c1:
        show_download_button(
            "AI 콘텐츠팩 JSON 다운로드",
            json_path,
            "application/json",
        )

    with c2:
        show_download_button(
            "AI 콘텐츠팩 TXT 다운로드",
            txt_path,
            "text/plain",
        )

    st.markdown("### CapCut Export / Draft")

    c3, c4 = st.columns(2)

    with c3:
        show_download_button(
            "CapCut Export JSON 다운로드",
            capcut_export_path,
            "application/json",
        )

    with c4:
        show_download_button(
            "CapCut Draft JSON 다운로드",
            capcut_draft_path,
            "application/json",
        )

    st.markdown("### 제작 보조 TXT")

    c5, c6 = st.columns(2)

    with c5:
        show_download_button(
            "CapCut 편집 TXT 다운로드",
            capcut_edit_path,
        )

    with c6:
        show_download_button(
            "썸네일 Prompt TXT 다운로드",
            thumbnail_prompt_path,
        )

    c7, c8 = st.columns(2)

    with c7:
        show_download_button(
            "인포크 Prompt TXT 다운로드",
            inpock_prompt_path,
        )

    with c8:
        show_download_button(
            "업로드 문구 TXT 다운로드",
            upload_path,
        )