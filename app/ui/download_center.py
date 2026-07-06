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

    json_path = content_pack_result.get("json_path")
    txt_path = content_pack_result.get("txt_path")
    capcut_path = content_pack_result.get("capcut_path")

    show_download_button("⬇ AI 콘텐츠 팩 JSON 다운로드", json_path, "application/json")
    show_download_button("⬇ AI 콘텐츠 팩 TXT 다운로드", txt_path, "text/plain")
    show_download_button("⬇ CapCut 내보내기 다운로드", capcut_path, "text/plain")