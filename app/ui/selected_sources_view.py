import streamlit as st

from modules.video.video_path_resolver import VideoPathResolver
from modules.video.download_utils import latest_downloaded_video

from app.ui.ai_product_analysis import show_ai_product_analysis
from app.ui.download_connect import (
    open_with_login_browser,
    connect_latest_download_to_project,
)
from app.utils.selected_sources import (
    init_selected_sources,
    save_selected_sources,
)


def show_selected_sources(project):
    """
    사용자가 채택한 영상 후보를 표시하고 관리합니다.

    주요 기능:
    - 후보 원본 링크 열기
    - Downloads 폴더의 최신 실제 제품 영상 연결
    - 후보별 video_path 저장
    - selected_sources.json 즉시 저장
    - 후보 순서 변경 및 삭제
    """
    key = init_selected_sources(project)
    selected = st.session_state.get(key, [])

    st.subheader("🎞️ 채택 영상 후보")

   
    resolver = VideoPathResolver()
    path_debug = resolver.debug(project)

    if path_debug.get("exists"):
        st.success(
            f"현재 프로젝트 연결 영상: "
            f"{path_debug.get('video_path')} / "
            f"{path_debug.get('size_mb')}MB"
        )
    else:
        st.warning(
            "현재 프로젝트에 연결된 영상이 없습니다. "
            "후보 링크에서 영상을 다운로드한 뒤 "
            "'최신 다운로드 영상 연결' 버튼을 눌러주세요."
        )

    latest_video = latest_downloaded_video()

    if latest_video:
        try:
            latest_size = round(
                latest_video.stat().st_size / (1024 * 1024),
                2,
            )

            st.caption(
                f"Downloads 최신 영상 감지: "
                f"{latest_video.name} / {latest_size}MB"
            )

        except Exception:
            st.caption(
                f"Downloads 최신 영상 감지: {latest_video.name}"
            )
    else:
        st.caption(
            "Downloads 폴더에서 최근 mp4, mov, webm 파일을 "
            "아직 찾지 못했습니다."
        )

    for i, item in enumerate(selected):
        platform = item.get("platform", "-")
        query = (
            item.get("query")
            or item.get("keyword")
            or item.get("search_query")
            or "-"
        )

        purpose = item.get("purpose", "-")
        score = item.get("score", "-")
        url = (
            item.get("url")
            or item.get("search_url")
            or item.get("video_url")
            or item.get("play_url")
            or ""
        )

        connected_video_path = item.get("video_path", "")
        download_connected = item.get("download_connected", False)

        with st.container(border=True):
            st.markdown(
                f"**{i + 1}. [{platform}] {query}**"
            )

            st.caption(
                f"목적: {purpose} / 점수: {score}"
            )

            if connected_video_path:
                st.success("실제 제품 영상 연결 완료")
                st.caption(
                    f"연결 영상: {connected_video_path}"
                )
            elif download_connected:
                st.warning(
                    "연결 상태는 있으나 video_path가 없습니다."
                )
            else:
                st.info(
                    "아직 실제 제품 영상이 연결되지 않았습니다."
                )

            if url:
                if st.button(
                    "후보 열기",
                    key=f"open_source_url_{project.id}_{i}",
                    use_container_width=True,
                ):
                    open_with_login_browser(url)
                    st.success(
                        "로그인 유지 브라우저로 후보 링크를 열었습니다."
                    )
            else:
                st.warning("이 후보에는 열 수 있는 URL이 없습니다.")

            if st.button(
                "📥 최신 다운로드 영상 연결",
                key=f"auto_connect_latest_download_{project.id}_{i}",
                use_container_width=True,
                type="primary",
            ):
                result = connect_latest_download_to_project(
                    project=project,
                    item=item,
                    index=i,
                )

                if result.get("ok"):
                    item["video_path"] = result.get(
                        "video_path",
                        "",
                    )

                    item["download_source_path"] = result.get(
                        "source_path",
                        "",
                    )

                    item["download_connected"] = True
                    item["is_test_video"] = False

                    selected[i] = item

                    st.session_state[key] = selected

                    save_selected_sources(
                        project,
                        selected,
                    )

                    st.success(result.get("message", "영상 연결 완료"))

                    st.caption(
                        f"연결 영상: "
                        f"{result.get('video_path')} / "
                        f"{result.get('size_mb')}MB"
                    )

                    st.rerun()

                else:
                    st.error(
                        result.get(
                            "message",
                            "영상 연결에 실패했습니다.",
                        )
                    )

                    if result.get("source_path"):
                        st.caption(
                            f"감지된 파일: "
                            f"{result.get('source_path')}"
                        )

            c1, c2, c3 = st.columns(3)

            with c1:
                if st.button(
                    "⬆ 위로",
                    key=f"selected_up_{project.id}_{i}",
                    disabled=i == 0,
                    use_container_width=True,
                ):
                    selected[i - 1], selected[i] = (
                        selected[i],
                        selected[i - 1],
                    )

                    st.session_state[key] = selected
                    save_selected_sources(project, selected)

                    st.success("후보 순서를 위로 이동했습니다.")
                    st.rerun()

            with c2:
                if st.button(
                    "⬇ 아래로",
                    key=f"selected_down_{project.id}_{i}",
                    disabled=i == len(selected) - 1,
                    use_container_width=True,
                ):
                    selected[i + 1], selected[i] = (
                        selected[i],
                        selected[i + 1],
                    )

                    st.session_state[key] = selected
                    save_selected_sources(project, selected)

                    st.success("후보 순서를 아래로 이동했습니다.")
                    st.rerun()

            with c3:
                if st.button(
                    "🗑 삭제",
                    key=f"selected_delete_{project.id}_{i}",
                    use_container_width=True,
                ):
                    selected.pop(i)

                    st.session_state[key] = selected
                    save_selected_sources(project, selected)

                    st.success("후보를 삭제했습니다.")
                    st.rerun()

    st.caption(
        "현재 후보 순서는 AI 컷 추천과 Content Pack 생성 순서에 사용됩니다."
    )

    show_ai_product_analysis(
        project,
        selected,
    )

    content_pack_result = st.session_state.get(
        f"ai_content_pack_export_{project.id}",
        {},
    )

    if not content_pack_result:
        content_pack_result = st.session_state.get(
            f"ai_content_pack_result_{project.id}",
            {},
        )

    #show_download_center(content_pack_result)