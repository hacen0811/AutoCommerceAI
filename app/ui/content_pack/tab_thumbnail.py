import streamlit as st

from app.ui.content_pack.helpers import copybox


def show_thumbnail_tab(pack):
    thumbnail = pack.get("thumbnail", {})
    inpock = pack.get("inpock", {})
    edit = pack.get("edit_assistant", {})

    thumbnail_guide = edit.get("thumbnail_guide", {})
    inpock_guide = edit.get("inpock_guide", {})

    st.markdown("### 쇼츠 썸네일 9:16")

    copybox(
        "메인 문구",
        thumbnail.get("main_text")
        or thumbnail_guide.get("main_text")
        or "왜 이제 알았지?",
    )

    copybox(
        "서브 문구",
        thumbnail.get("sub_text")
        or thumbnail_guide.get("sub_text")
        or pack.get("project_name", "선택 상품"),
    )

    copybox(
        "레이아웃",
        thumbnail.get("layout")
        or thumbnail_guide.get("layout")
        or "제품 크게 + 왼쪽 상단 후킹 문구 + 하단 짧은 설명",
    )

    copybox(
        "이미지 프롬프트",
        thumbnail.get("image_prompt", ""),
    )

    st.markdown("### 인포크 이미지 1000×1000")

    copybox(
        "타이틀",
        inpock.get("title")
        or inpock_guide.get("title")
        or pack.get("project_name", "선택 상품"),
    )

    copybox(
        "메인 문구",
        inpock.get("main_text")
        or inpock_guide.get("main_text")
        or "생활이 편해지는 추천템",
    )

    copybox(
        "서브 문구",
        inpock.get("sub_text")
        or inpock_guide.get("sub_text")
        or "제품 정보는 링크에서 확인",
    )

    copybox(
        "이미지 프롬프트",
        inpock.get("image_prompt", ""),
    )