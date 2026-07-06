import streamlit as st

from modules.video.video_path_resolver import VideoPathResolver
from modules.video.download_utils import latest_downloaded_video

from app.ui.ai_product_analysis import show_ai_product_analysis
from app.ui.download_center import show_download_center
from app.utils.selected_sources import (
    init_selected_sources,
    save_selected_sources,
)

from app.ui.download_connect import (
    open_with_login_browser,
    connect_latest_download_to_project,
)

def show_selected_sources(project):
    key = init_selected_sources(project)
    selected = st.session_state.get(key, [])

    st.subheader("🎬 채택한 영상 후보")

    if not selected:
        st.info("아직 채택한 영상 후보가 없습니다.")
        return

    resolver = VideoPathResolver()
    path_debug = resolver.debug(project)

    if path_debug.get("exists"):
        st.success(
            f"현재 연결된 영상: {path_debug.get('video_path')} / "
            f"{path_debug.get('size_mb')}MB"
        )
    else:
        st.warning("현재 프로젝트에 연결된 영상이 없습니다. 영상 링크에서 MP4를 다운로드한 뒤 자동 연결 버튼을 눌러주세요.")

    latest_video = latest_downloaded_video()

    if latest_video:
        try:
            latest_size = round(latest_video.stat().st_size / (1024 * 1024), 2)
            st.caption(f"Downloads 최신 영상 감지: {latest_video.name} / {latest_size}MB")
        except Exception:
            st.caption(f"Downloads 최신 영상 감지: {latest_video.name}")
    else:
        st.caption("Downloads 폴더에서 최근 mp4/mov/webm 파일을 아직 찾지 못했습니다.")

    for i, item in enumerate(selected):
        with st.container(border=True):
            st.markdown(f"**{i + 1}. [{item.get('platform')}] {item.get('query', '')}**")

            st.caption(
                f"목적: {item.get('purpose', '-')} / "
                f"점수: {item.get('score', '-')}점"
            )

            url = item.get("url")

            if url:
                if st.button(
                    "영상 링크 열기(로그인 브라우저)",
                    key=f"open_source_url_{project.id}_{i}",
                    use_container_width=True,
                ):
                    open_with_login_browser(url)
                    st.success("Playwright 로그인 브라우저로 열었습니다.")

            if st.button(
                "⬇ 다운로드 완료 후 자동 연결",
                key=f"auto_connect_latest_download_{project.id}_{i}",
                use_container_width=True,
            ):
                result = connect_latest_download_to_project(
                    project,
                    item=item,
                    index=i,
                )

                if result.get("ok"):
                    item["video_path"] = result.get("video_path", "")
                    item["download_source_path"] = result.get("source_path", "")
                    item["download_connected"] = True

                    selected[i] = item
                    st.session_state[key] = selected
                    save_selected_sources(project, selected)

                    st.success(result.get("message"))
                    st.caption(
                        f"연결된 영상: {result.get('video_path')} / "
                        f"{result.get('size_mb')}MB"
                    )
                    st.rerun()

                else:
                    st.error(result.get("message"))

                    if result.get("source_path"):
                        st.caption(f"감지된 파일: {result.get('source_path')}")

            c1, c2, c3 = st.columns(3)

            with c1:
                if st.button(
                    "⬆️ 위로",
                    key=f"selected_up_{project.id}_{i}",
                    disabled=i == 0,
                ):
                    selected[i - 1], selected[i] = selected[i], selected[i - 1]
                    st.session_state[key] = selected
                    save_selected_sources(project, selected)
                    st.success("순서를 위로 이동했습니다.")
                    st.rerun()

            with c2:
                if st.button(
                    "⬇️ 아래로",
                    key=f"selected_down_{project.id}_{i}",
                    disabled=i == len(selected) - 1,
                ):
                    selected[i + 1], selected[i] = selected[i], selected[i + 1]
                    st.session_state[key] = selected
                    save_selected_sources(project, selected)
                    st.success("순서를 아래로 이동했습니다.")
                    st.rerun()

            with c3:
                if st.button(
                    "🗑 삭제",
                    key=f"selected_delete_{project.id}_{i}",
                ):
                    selected.pop(i)
                    st.session_state[key] = selected
                    save_selected_sources(project, selected)
                    st.success("후보를 삭제했습니다.")
                    st.rerun()

    st.caption("현재 순서가 CapCut 내보내기와 TXT 생성 순서의 기준이 됩니다.")

    show_ai_product_analysis(project, selected)

    content_pack_result = st.session_state.get(
        f"ai_content_pack_export_{project.id}",
        {}
    )

    if not content_pack_result:
        content_pack_result = st.session_state.get(
            f"ai_content_pack_result_{project.id}",
            {}
        )

    show_download_center(content_pack_result)