import streamlit as st

from app.ui.download_connect import open_with_login_browser


def show_candidate_card(
    project,
    platform,
    item,
    safe_project_id,
):
    
    query = item.get("query", "")
    rank = item.get("rank", "")
    purpose = item.get("purpose", "")
    score = item.get("score", "")
    url = make_search_url(platform, query)
    key_prefix = f"select_{safe_project_id(project)}_{platform}_{rank}_{query}"

    with st.container(border=True):
        st.markdown(f"### {rank}위 · {platform.upper()}")
        st.markdown(f"**검색어:** {query}")
        st.markdown(f"**목적:** {purpose}")
        st.markdown(f"**추천 점수:** ⭐ {score}점")

        b1, b2 = st.columns(2)

        with b1:
            if url:
                if st.button(
                    "검색 열기",
                    key=f"search_{platform}_{rank}_{query}",
                    use_container_width=True,
                ):
                    open_with_login_browser(url)
                    st.success("Playwright 로그인 브라우저로 열었습니다.")

        with b2:
            if st.button(
                "이 후보 채택",
                key=key_prefix,
                use_container_width=True,
            ):
                added = select_source(project, platform, item, url)

                if added:
                    st.success("후보를 채택하고 저장했습니다.")
                else:
                    st.info("이미 채택한 후보입니다.")