from pathlib import Path

import streamlit as st


def show_download_button(label, file_path, mime="text/plain"):
    if not file_path:
        return

    path = Path(str(file_path))

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

    json_path = (
        content_pack_result.get("json_path")
        or content_pack_result.get("json")
    )

    txt_path = (
        content_pack_result.get("txt_path")
        or content_pack_result.get("txt")
    )

    capcut_export_path = (
        content_pack_result.get("capcut_export_json_path")
        or content_pack_result.get("capcut_export_json")
    )

    capcut_draft_path = (
        content_pack_result.get("capcut_draft_json_path")
        or content_pack_result.get("capcut_draft_json")
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