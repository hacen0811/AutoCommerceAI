import streamlit as st

from app.utils.selected_sources import select_source
from app.utils.project_keys import safe_project_id


def show_live_sources(project, live_sources):
    if not live_sources:
        return

    if live_sources.get("live_collection"):
        live_sources = live_sources.get("live_collection", {})

    results = live_sources.get("results", [])

    if not results:
        st.info("실제 웹 수집 결과가 없습니다.")
        return

    st.divider()
    st.markdown("## 실제 Playwright 수집 결과")

    st.caption(
        f"상태: ok={live_sources.get('ok')} / "
        f"ready={live_sources.get('status', {}).get('ready')}"
    )

    for i, item in enumerate(results, start=1):
        if not isinstance(item, dict):
            continue

        title = item.get("title") or item.get("text") or "제목 없음"
        url = item.get("url") or item.get("link") or ""
        thumbnail = (
            item.get("thumbnail")
            or item.get("thumbnail_url")
            or item.get("image")
            or ""
        )

        views = item.get("views") or item.get("view_count") or "-"
        likes = item.get("likes") or item.get("like_count") or "-"
        duration = (
            item.get("duration")
            or item.get("video_length")
            or item.get("length")
            or "-"
        )

        with st.container(border=True):
            cols = st.columns([1, 3])

            with cols[0]:
                if thumbnail:
                    st.image(thumbnail, use_container_width=True)
                else:
                    st.caption("썸네일 없음")

            with cols[1]:
                st.markdown(f"### {i}. {title}")

                st.caption(
                    f"조회수: {views} / "
                    f"좋아요: {likes} / "
                    f"길이: {duration}"
                )

                if url:
                    st.link_button(
                        "영상 열기",
                        url,
                        use_container_width=True,
                    )

                source_item = {
                    "rank": i,
                    "platform": item.get("platform", "live"),
                    "title": title,
                    "query": item.get("query") or item.get("keyword") or title,
                    "keyword": item.get("keyword") or item.get("query") or title,
                    "search_query": item.get("search_query") or item.get("query") or item.get("keyword") or title,
                    "purpose": "실제 Playwright 수집 후보",
                    "score": item.get("score", 80),
                    "thumbnail": thumbnail,
                    "url": url,
                    "search_url": item.get("search_url") or url,
                }

                if st.button(
                    "이 후보 채택",
                    key=f"live_select_{safe_project_id(project)}_{i}",
                    use_container_width=True,
                ):
                    added = select_source(
                        project,
                        item.get("platform", "live"),
                        source_item,
                        url,
                    )

                    if added:
                        st.success("후보를 채택하고 저장했습니다.")
                    else:
                        st.info("이미 채택한 후보입니다.")