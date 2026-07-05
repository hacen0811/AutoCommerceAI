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
    st.divider()
    st.subheader("📁 다운로드 센터")

    if not content_pack_result:
        st.info("아직 생성된 콘텐츠 팩이 없습니다.")
        return

    # json / txt 모두 지원
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

    st.markdown("### 제작 보조 TXT")

    c1, c2 = st.columns(2)

    with c1:
        show_download_button(
            "CapCut 편집 TXT 다운로드",
            capcut_edit_path,
        )

    with c2:
        show_download_button(
            "썸네일 Prompt TXT 다운로드",
            thumbnail_prompt_path,
        )

    c3, c4 = st.columns(2)

    with c3:
        show_download_button(
            "인포크 Prompt TXT 다운로드",
            inpock_prompt_path,
        )

    with c4:
        show_download_button(
            "업로드 문구 TXT 다운로드",
            upload_path,
        )