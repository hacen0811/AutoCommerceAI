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


def show_download_center(project, content_pack=None, capcut_export=None):
    st.divider()
    st.subheader("📁 다운로드 센터")

    if not content_pack and not capcut_export:
        st.caption("아직 다운로드할 제작 결과가 없습니다.")
        return

    if content_pack:
        st.markdown("### AI 콘텐츠 팩")

        json_path = content_pack.get("json_path")
        txt_path = content_pack.get("txt_path")

        c1, c2 = st.columns(2)

        with c1:
            show_download_button("콘텐츠팩 JSON 다운로드", json_path, "application/json")

        with c2:
            show_download_button("콘텐츠팩 TXT 다운로드", txt_path, "text/plain")

    if capcut_export:
        st.markdown("### CapCut")

        json_path = capcut_export.get("json")
        txt_path = capcut_export.get("txt")

        c1, c2 = st.columns(2)

        with c1:
            show_download_button("CapCut JSON 다운로드", json_path, "application/json")

        with c2:
            show_download_button("CapCut TXT 다운로드", txt_path, "text/plain")