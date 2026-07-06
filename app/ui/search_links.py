import streamlit as st

from app.ui.download_connect import open_with_login_browser
from app.utils.candidate_source import make_search_url


def show_search_links(keywords):
    taobao_keyword = keywords.get("taobao_keyword", "")
    main_keyword = keywords.get("main_keyword", "")

    st.subheader("검색 키워드")
    st.write("타오바오:", taobao_keyword)
    st.write("1688:", taobao_keyword or main_keyword)

    c1, c2 = st.columns(2)

    with c1:
        if st.button(
            "타오바오 검색 열기",
            use_container_width=True,
        ):
            url = make_search_url(
                "taobao",
                taobao_keyword,
            )

            open_with_login_browser(url)

            st.success(
                "Playwright 로그인 브라우저를 열었습니다."
            )

    with c2:
        if st.button(
            "1688 검색 열기",
            use_container_width=True,
        ):
            url = make_search_url(
                "1688",
                taobao_keyword or main_keyword,
            )

            open_with_login_browser(url)

            st.success(
                "Playwright 로그인 브라우저를 열었습니다."
            )