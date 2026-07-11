from pathlib import Path

import streamlit as st

from modules.content.content_pack_service import build_ai_content_pack
from modules.content.content_factory import ContentFactory

from app.utils.selected_sources import load_selected_sources

from app.ui.content_pack.tab_summary import show_summary_tab
from app.ui.content_pack.tab_scripts import show_shorts_tab
from app.ui.content_pack.tab_caption import show_caption_tab
from app.ui.content_pack.tab_thumbnail import show_thumbnail_tab
from app.ui.content_pack.tab_capcut import show_capcut_tab
from app.ui.content_pack.tab_edit_ai import show_tab_edit_ai
from app.ui.download_center import show_download_center


TEST_VIDEO_KEYWORDS = {
    "default_final",
    "default_merged",
    "test_shorts",
    "test_video",
    "sample",
    "subtitle_test",
    "하센맘",
}


def safe_project_id(project):
    return (
        str(getattr(project, "id", "default"))
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )


def is_test_video(video_path):
    """
    자동 생성 테스트 영상이나 샘플 영상을 제외합니다.
    """
    if not video_path:
        return True

    file_name = Path(str(video_path)).name.lower()

    return any(
        keyword.lower() in file_name
        for keyword in TEST_VIDEO_KEYWORDS
    )


def normalize_video_path(source):
    """
    후보에서 실제 연결 영상 경로를 하나의 video_path로 정리합니다.
    """
    if not isinstance(source, dict):
        return ""

    return str(
        source.get("video_path")
        or source.get("local_path")
        or source.get("path")
        or ""
    ).strip()


def get_connected_sources(selected_sources):
    """
    video_path가 있고 실제 파일이 존재하며 테스트 영상이 아닌 후보만 반환합니다.
    """
    connected = []

    for source in selected_sources or []:
        if not isinstance(source, dict):
            continue

        video_path = normalize_video_path(source)

        if not video_path:
            continue

        if is_test_video(video_path):
            continue

        path = Path(video_path)

        if not path.exists() or not path.is_file():
            continue

        normalized = dict(source)
        normalized["video_path"] = str(path)
        normalized["download_connected"] = True
        normalized["is_test_video"] = False

        connected.append(normalized)

    return connected


def show_content_pack_view(
    project,
    result=None,
    content_pack=None,
    paths=None,
):
    st.divider()
    st.subheader("📦 AI 콘텐츠 팩")

    project_key = safe_project_id(project)
    pack_key = f"content_pack_{project_key}"

    export_key = (
        f"ai_content_pack_export_"
        f"{getattr(project, 'id', project_key)}"
    )

    if content_pack:
        st.session_state[pack_key] = content_pack

    if paths:
        st.session_state[export_key] = paths

    current_pack = st.session_state.get(pack_key, {})
    current_paths = st.session_state.get(export_key, {})

    outputs = result.get("outputs", {}) if result else {}

    saved_selected_sources = load_selected_sources(project)

    selected_sources = (
        saved_selected_sources
        or outputs.get("candidate_selection", {}).get("top3", [])
        or outputs.get("selected_sources", [])
        or outputs.get("candidates", [])
    )

    connected_sources = get_connected_sources(selected_sources)

    selected_count = len(selected_sources)
    connected_count = len(connected_sources)

    st.caption(
        f"채택 후보: {selected_count}개 / "
        f"실제 영상 연결 완료: {connected_count}개"
    )

    if selected_sources and not connected_sources:
        st.warning(
            "채택 후보는 있지만 실제 제품 영상이 연결되지 않았습니다. "
            "채택 영상 후보에서 각 영상의 "
            "'최신 다운로드 영상 연결' 버튼을 눌러주세요."
        )

    elif connected_sources:
        st.success(
            f"실제 제품 영상 {connected_count}개를 "
            "Content Pack 생성에 사용합니다."
        )

        with st.expander(
            "사용할 실제 제품 영상 확인",
            expanded=False,
        ):
            for index, source in enumerate(
                connected_sources,
                start=1,
            ):
                st.write(
                    f"{index}. "
                    f"{source.get('platform', '-')} / "
                    f"{source.get('query', '-')}"
                )
                st.caption(source.get("video_path", ""))

    smart = (
        outputs.get("smart")
        or outputs.get("video_intel")
        or outputs.get("video_quality")
        or {}
    )

    vision = (
        outputs.get("vision")
        or outputs.get("ocr_result")
        or outputs.get("real_vision")
        or {}
    )

    if st.button(
        "🚀 AI 콘텐츠 팩 생성",
        key=f"content_pack_generate_{project_key}",
        type="primary",
        width="stretch",
    ):
        if not result:
            st.warning(
                "원클릭 실행 결과가 없어 "
                "AI 콘텐츠 팩을 생성할 수 없습니다."
            )
            return

        if not selected_sources:
            st.warning(
                "채택된 영상 후보가 없어 "
                "AI 콘텐츠 팩을 생성할 수 없습니다."
            )
            return

        if not connected_sources:
            st.error(
                "실제 제품 영상이 연결된 후보가 없습니다. "
                "테스트 영상이나 video_path가 없는 후보는 "
                "Content Pack에 사용할 수 없습니다."
            )
            return

        try:
            with st.spinner(
                "실제 제품 영상으로 AI 콘텐츠 팩을 생성하는 중입니다..."
            ):
                pack = build_ai_content_pack(
                    project=project,
                    selected_sources=connected_sources,
                    latest_result=result,
                )

                # Content Pack 내부에도 실제 연결 후보만 강제로 유지합니다.
                pack["selected_sources"] = connected_sources

                pack["source_video_count"] = len(
                    connected_sources
                )

                pack["source_video_policy"] = (
                    "connected-real-videos-only"
                )

                # 이후 CutPlanner가 후보별 video_path를 사용합니다.
                pack = ContentFactory().apply_edit_assistant(
                    pack,
                    project=project,
                )

                saved_paths = ContentFactory().save_content_pack(
                    project,
                    pack,
                )

                st.session_state[pack_key] = pack
                st.session_state[export_key] = saved_paths

            st.success(
                "실제 제품 영상만 사용해 "
                "AI 콘텐츠 팩을 생성하고 저장했습니다."
            )
            st.rerun()

        except Exception as exc:
            st.error(
                f"AI 콘텐츠 팩 생성 중 오류가 발생했습니다: {exc}"
            )
            return

    current_pack = st.session_state.get(
        pack_key,
        current_pack,
    )

    current_paths = st.session_state.get(
        export_key,
        current_paths,
    )

    if not current_pack:
        st.info(
            "아직 AI 콘텐츠 팩이 없습니다. "
            "실제 제품 영상을 연결한 뒤 생성 버튼을 눌러주세요."
        )
        return

    tabs = st.tabs(
        [
            "요약",
            "쇼츠",
            "자막",
            "썸네일",
            "CapCut",
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
        show_tab_edit_ai(
            current_pack,
            project,
        )

    with tabs[6]:
        show_download_center(
            current_paths,
            key_prefix=f"content_pack_{project_key}",
        )