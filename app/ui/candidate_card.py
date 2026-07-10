import subprocess
import sys

import streamlit as st

from app.ui.download_connect import open_with_login_browser
from app.utils.selected_sources import select_source


def make_search_url(platform, query):
    from urllib.parse import quote_plus

    q = quote_plus(query or "")

    if platform == "taobao":
        return f"https://s.taobao.com/search?q={q}"

    if platform == "1688":
        return f"https://s.1688.com/selloffer/offer_search.htm?keywords={q}"

    if platform in ["douyin", "tiktok"]:
        return f"https://www.tiktok.com/search?q={q}"

    return ""


def collect_with_playwright(url):
    if not url:
        return False

    subprocess.Popen(
        [
            sys.executable,
            "tools/open_source_collect.py",
            url,
        ]
    )
    return True


def candidate_query(item, platform=None):
    if platform == "taobao":
        return (
            item.get("taobao_keyword")
            or item.get("query_cn")
            or item.get("cn_query")
            or item.get("query")
            or item.get("keyword")
            or item.get("search_query")
            or item.get("title")
            or ""
        )

    if platform == "1688":
        return (
            item.get("source_1688_keyword")
            or item.get("query_cn")
            or item.get("cn_query")
            or item.get("query")
            or item.get("keyword")
            or item.get("search_query")
            or item.get("title")
            or ""
        )

    if platform in ["douyin", "tiktok"]:
        return (
            item.get("douyin_keyword")
            or item.get("query")
            or item.get("keyword")
            or item.get("search_query")
            or item.get("title")
            or ""
        )

    return (
        item.get("query")
        or item.get("keyword")
        or item.get("search_query")
        or item.get("title")
        or ""
    )


def normalize_candidate(item, platform):
    query = candidate_query(item, platform)
    final_url = make_search_url(platform, query)

    return {
        **item,
        "platform": platform,
        "query": query,
        "keyword": item.get("keyword") or query,
        "search_query": item.get("search_query") or query,
        "url": final_url,
        "search_url": final_url,
    }


def show_candidate_card(project, platform, item, safe_project_id):
    query = candidate_query(item, platform)

    rank = item.get("rank", "")
    purpose = item.get("purpose", "")
    score = item.get("score", "")

    url = make_search_url(platform, query)

    key_base = f"{safe_project_id(project)}_{platform}_{rank}_{abs(hash(query))}"

    with st.container(border=True):
        st.markdown(f"### {rank}. {platform.upper()}")
        st.markdown(f"**검색어:** {query or '-'}")
        st.markdown(f"**목적:** {purpose or '-'}")
        st.markdown(f"**추천 점수:** {score or '-'}")

        b1, b2, b3 = st.columns(3)

        with b1:
            if url:
                if st.button(
                    "검색 열기",
                    key=f"open_{key_base}",
                    use_container_width=True,
                ):
                    open_with_login_browser(url)
                    st.success("검색 페이지를 열었습니다.")

        with b2:
            if url:
                if st.button(
                    "후보 수집",
                    key=f"collect_{key_base}",
                    use_container_width=True,
                ):
                    collect_with_playwright(url)
                    st.success("후보 수집을 시작했습니다. 잠시 후 새로고침하세요.")

        with b3:
            if st.button(
                "이 후보 채택",
                key=f"select_{key_base}",
                use_container_width=True,
            ):
                normalized = normalize_candidate(item, platform)
                added = select_source(
                    project,
                    platform,
                    normalized,
                    normalized.get("url"),
                )

                if added:
                    st.success("후보를 채택하고 저장했습니다.")
                else:
                    st.info("이미 채택한 후보입니다.")