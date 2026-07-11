from pathlib import Path
import hashlib

import streamlit as st


def read_file_text(path):
    try:
        if not path:
            return ""

        file_path = Path(path)

        if file_path.exists() and file_path.is_file():
            return file_path.read_text(encoding="utf-8")

    except Exception:
        return ""

    return ""


def safe_button_key(key_prefix, slot_name, path):
    """
    다운로드 버튼마다 고유하고 안정적인 Streamlit key를 생성합니다.
    """
    raw_path = str(path or "")
    path_hash = hashlib.sha1(
        raw_path.encode("utf-8")
    ).hexdigest()[:12]

    return (
        f"download_"
        f"{key_prefix}_"
        f"{slot_name}_"
        f"{path_hash}"
    )


def show_download_button(
    label,
    path,
    mime="text/plain",
    *,
    key_prefix="download_center",
    slot_name="file",
):
    if not path:
        return

    file_path = Path(path)

    if not file_path.exists() or not file_path.is_file():
        st.caption(
            f"{label} 파일을 찾을 수 없습니다: {path}"
        )
        return

    try:
        file_data = file_path.read_bytes()

    except Exception as exc:
        st.error(
            f"{label} 파일을 읽지 못했습니다: {exc}"
        )
        return

    button_key = safe_button_key(
        key_prefix=key_prefix,
        slot_name=slot_name,
        path=file_path,
    )

    st.download_button(
        label=label,
        data=file_data,
        file_name=file_path.name,
        mime=mime,
        key=button_key,
        width="stretch",
    )


def show_download_center(
    content_pack_result,
    key_prefix="content_pack_download",
):
    st.divider()
    st.subheader("📥 다운로드 센터")

    if not content_pack_result:
        st.caption(
            "아직 다운로드할 콘텐츠 생성 결과가 없습니다."
        )
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

    project_zip_path = (
        content_pack_result.get("project_zip")
        or content_pack_result.get("capcut_project_zip")
    )

    show_download_button(
        "⬇ AI 콘텐츠 팩 JSON 다운로드",
        json_path,
        "application/json",
        key_prefix=key_prefix,
        slot_name="content_pack_json",
    )

    show_download_button(
        "⬇ AI 콘텐츠 팩 TXT 다운로드",
        txt_path,
        "text/plain",
        key_prefix=key_prefix,
        slot_name="content_pack_txt",
    )

    show_download_button(
        "⬇ CapCut Export JSON 다운로드",
        capcut_path,
        "application/json",
        key_prefix=key_prefix,
        slot_name="capcut_export_json",
    )

    show_download_button(
        "⬇ CapCut Draft JSON 다운로드",
        draft_path,
        "application/json",
        key_prefix=key_prefix,
        slot_name="capcut_draft_json",
    )

    show_download_button(
        "⬇ AI 편집 가이드 TXT 다운로드",
        edit_guide_path,
        "text/plain",
        key_prefix=key_prefix,
        slot_name="edit_guide_txt",
    )

    show_download_button(
        "⬇ CapCut Project ZIP 다운로드",
        project_zip_path,
        "application/zip",
        key_prefix=key_prefix,
        slot_name="capcut_project_zip",
    )