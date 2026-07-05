import streamlit as st

from app.ui.content_pack.helpers import read_json
from app.ui.content_pack.tab_summary import show_summary_tab
from app.ui.content_pack.tab_scripts import show_shorts_tab
from app.ui.content_pack.tab_caption import show_caption_tab
from app.ui.content_pack.tab_thumbnail import show_thumbnail_tab
from app.ui.content_pack.tab_capcut import show_capcut_tab
from app.ui.content_pack.tab_json import show_json_tab


def show_content_pack_view(
    project,
    selected_sources=None,
    analysis=None,
    content_pack=None,
    paths=None,
):
    st.divider()
    st.subheader("📦 AI 콘텐츠 팩")

    pack = content_pack or {}

    if not pack and paths:
        pack = read_json(paths.get("json_path"))

    if not pack:
        st.info("아직 생성된 콘텐츠 팩이 없습니다.")
        st.caption("원클릭 실행을 완료하면 AI 콘텐츠 팩이 여기에 표시됩니다.")
        return

    project_name = (
        pack.get("project_name")
        or pack.get("product_name")
        or getattr(project, "product_name", "")
        or getattr(project, "title", "")
        or "선택 상품"
    )

    st.success(f"{project_name} 콘텐츠 팩이 생성되었습니다.")

    if paths:
        if paths.get("json_path"):
            st.caption(f"JSON 저장 위치: {paths.get('json_path')}")
        if paths.get("txt_path"):
            st.caption(f"TXT 저장 위치: {paths.get('txt_path')}")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["요약", "쇼츠 문구", "본문/CTA", "썸네일", "CapCut", "전체 JSON"]
    )

    with tab1:
        show_summary_tab(pack, selected_sources, analysis)

    with tab2:
        show_shorts_tab(pack)

    with tab3:
        show_caption_tab(pack)

    with tab4:
        show_thumbnail_tab(pack)

    with tab5:
        show_capcut_tab(pack)

    with tab6:
        show_json_tab(pack)