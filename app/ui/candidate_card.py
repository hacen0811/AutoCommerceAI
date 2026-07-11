import subprocess
import sys

import streamlit as st

from app.ui.download_connect import open_with_login_browser
from app.utils.selected_sources import select_source


def normalize_platform(platform):
    text = str(platform or "").strip().lower()

    aliases = {
        "타오바오": "taobao",
        "淘宝": "taobao",
        "taobao": "taobao",

        "틱톡": "tiktok",
        "tiktok": "tiktok",
        "douyin": "tiktok",
        "도우인": "tiktok",
        "抖音": "tiktok",

        "1688": "1688",
        "알리바바": "1688",
    }

    return aliases.get(text, text)


def make_search_url(platform, query):
    from urllib.parse import quote_plus

    platform = normalize_platform(platform)
    q = quote_plus(str(query or "").strip())

    if not q:
        return ""

    if platform == "taobao":
        return f"https://s.taobao.com/search?q={q}"

    if platform == "1688":
        return (
            "https://s.1688.com/selloffer/"
            f"offer_search.htm?keywords={q}"
        )

    if platform == "tiktok":
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
    platform_key = normalize_platform(platform)
    query = candidate_query(item, platform_key)

    rank = item.get("rank", "")
    purpose = item.get("purpose", "")
    score = item.get("score", "")

    url = make_search_url(platform_key, query)

    project_key = safe_project_id(project)

    # UUID를 사용하지 않는 고정 Key
    key_base = (
        f"{project_key}_"
        f"{platform_key}_"
        f"{rank}_"
        f"{abs(hash(query))}"
    )

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
                    width="stretch",
                ):
                    ok = open_with_login_browser(url)

                    if ok:
                        st.success("검색 페이지를 열었습니다.")
                    else:
                        st.error("브라우저를 열지 못했습니다.")

        with b2:
            if url:
                if st.button(
                    "후보 수집",
                    key=f"collect_{key_base}",
                    width="stretch",
                ):
                    collect_with_playwright(url)
                    st.success(
                        "후보 수집을 시작했습니다. 잠시 후 새로고침하세요."
                    )

        with b3:
            if st.button(
                "이 후보 채택",
                key=f"select_{key_base}",
                width="stretch",
            ):
                normalized = normalize_candidate(
                    item,
                    platform_key,
                )

                added = select_source(
                    project,
                    platform_key,
                    normalized,
                    normalized.get("url"),
                )

                if added:
                    st.success("후보를 채택하고 저장했습니다.")
                else:
                    st.info("이미 채택한 후보입니다.")