from pathlib import Path

import streamlit as st


def read_file_text(path):
    try:
        p = Path(path)
        if p.exists():
            return p.read_text(encoding="utf-8")
    except Exception:
        return ""
    return ""


def show_download_button(label, path, mime="text/plain"):
    if not path:
        return

    file_text = read_file_text(path)

    if file_text:
        st.download_button(
            label=label,
            data=file_text,
            file_name=Path(path).name,
            mime=mime,
            use_container_width=True,
        )
    else:
        st.caption(f"{label} 파일을 찾을 수 없습니다: {path}")


def show_download_center(content_pack_result):
    st.divider()
    st.subheader("📁 다운로드 센터")

    if not content_pack_result:
        st.caption("아직 다운로드할 제작 결과가 없습니다.")
        return

    json_path = (
        content_pack_result.get("json_path")
        or content_pack_result.get("json")
    )
    txt_path = (
        content_pack_result.get("txt_path")
        or content_pack_result.get("txt")
    )
    capcut_path = (
        content_pack_result.get("capcut_path")
        or content_pack_result.get("capcut_export_path")
        or content_pack_result.get("capcut")
    )
    draft_path = (
        content_pack_result.get("draft_path")
        or content_pack_result.get("capcut_draft_path")
        or content_pack_result.get("draft")
    )
    edit_guide_path = (
        content_pack_result.get("edit_guide_path")
        or content_pack_result.get("edit_guide")
    )

    show_download_button("⬇ AI 콘텐츠 팩 JSON 다운로드", json_path, "application/json")
    show_download_button("⬇ AI 콘텐츠 팩 TXT 다운로드", txt_path, "text/plain")
    show_download_button("⬇ CapCut Export JSON 다운로드", capcut_path, "application/json")
    show_download_button("⬇ CapCut Draft JSON 다운로드", draft_path, "application/json")
    show_download_button("⬇ AI 편집 가이드 TXT 다운로드", edit_guide_path, "text/plain")