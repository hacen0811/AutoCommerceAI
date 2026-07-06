import streamlit as st

from modules.content.content_factory import ContentFactory
from modules.content.content_pack_service import build_ai_content_pack

from app.ui.content_pack.tab_summary import show_summary_tab
from app.ui.content_pack.tab_scripts import show_shorts_tab
from app.ui.content_pack.tab_caption import show_caption_tab
from app.ui.content_pack.tab_thumbnail import show_thumbnail_tab
from app.ui.content_pack.tab_capcut import show_capcut_tab
from app.ui.content_pack.tab_edit_ai import show_tab_edit_ai
from app.ui.download_center import show_download_center


def safe_project_id(project):
    return str(getattr(project, "id", "default")).replace(" ", "_").replace("/", "_")


def show_content_pack_view(project, result=None, content_pack=None, paths=None):
    st.divider()
    st.subheader("📦 AI 콘텐츠 팩")

    project_key = safe_project_id(project)
    pack_key = f"content_pack_{project_key}"
    export_key = f"ai_content_pack_export_{getattr(project, 'id', project_key)}"

    if content_pack:
        st.session_state[pack_key] = content_pack

    if paths:
        st.session_state[export_key] = paths

    current_pack = st.session_state.get(pack_key, {})
    current_paths = st.session_state.get(export_key, {})

    outputs = result.get("outputs", {}) if result else {}
    selected_sources = outputs.get("candidate_selection", {}).get("top3", [])

    if st.button(
        "🚀 AI 콘텐츠 팩 생성",
        key=f"content_pack_generate_{project_key}",
        type="primary",
        use_container_width=True,
    ):
        if not result:
            st.warning("원클릭 실행 결과가 없어 AI 콘텐츠 팩을 생성할 수 없습니다.")
            return

        if not selected_sources:
            st.warning("채택된 영상 후보가 없어 AI 콘텐츠 팩을 생성할 수 없습니다.")
            return

        try:
            with st.spinner("AI 콘텐츠 팩을 생성하는 중입니다..."):
                pack = build_ai_content_pack(
                    project=project,
                    selected_sources=selected_sources,
                    latest_result=result,
                )

                pack = ContentFactory().apply_edit_assistant(pack)
                saved_paths = ContentFactory().save_content_pack(project, pack)

                st.session_state[pack_key] = pack
                st.session_state[export_key] = saved_paths

            st.success("AI 콘텐츠 팩을 생성하고 저장했습니다.")
            st.rerun()

        except Exception as exc:
            st.error(f"AI 콘텐츠 팩 생성 중 오류가 발생했습니다: {exc}")
            return

    current_pack = st.session_state.get(pack_key, current_pack)
    current_paths = st.session_state.get(export_key, current_paths)

    if not current_pack:
        st.info("아직 AI 콘텐츠 팩이 없습니다. 위 버튼을 눌러 생성하세요.")
        return

    tabs = st.tabs(
        [
            "요약",
            "대본",
            "자막",
            "썸네일",
            "캡컷",
            "편집 AI",
            "다운로드",
        ]
    )

    with tabs[0]:
        show_summary_tab(current_pack)

    with tabs[1]:
        show_shorts_tab(current_pack)

    with tabs[2]:
        show_caption_tab(current_pack)

    with tabs[3]:
        show_thumbnail_tab(current_pack)

    with tabs[4]:
        show_capcut_tab(current_pack)

    with tabs[5]:
        show_tab_edit_ai(current_pack, project)

    with tabs[6]:
        show_download_center(current_paths)