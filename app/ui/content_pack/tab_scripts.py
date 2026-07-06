import streamlit as st

from app.ui.content_pack.helpers import copybox


def show_shorts_tab(pack):
    shorts = pack.get("shorts", {})
    upload = pack.get("upload_bundle", {})
    shorts_variants = pack.get("shorts_variants", [])

    active_content = (
        pack.get("selected_variant")
        or next(
            (v for v in shorts_variants if v.get("recommended")),
            None,
        )
        or (shorts_variants[0] if shorts_variants else {})
        or {}
    )

    if active_content:
        st.success(
            f"⭐ 대표 콘텐츠 : "
            f"{active_content.get('type', '추천안')} / "
            f"{active_content.get('score', '-')}점"
        )

    st.markdown("### 제목")

    title = (
        active_content.get("title")
        or (shorts.get("titles", [""]) or [""])[0]
    )

    copybox("대표 제목", title)

    if shorts.get("titles"):
        with st.expander("전체 제목 보기"):
            for idx, item in enumerate(shorts.get("titles", []), start=1):
                copybox(f"제목 {idx}", item)

    st.markdown("### 후킹")

    hook = (
        active_content.get("hook")
        or (shorts.get("hooks", [""]) or [""])[0]
    )

    copybox("대표 후킹", hook)

    if shorts.get("hooks"):
        with st.expander("전체 후킹 보기"):
            for idx, item in enumerate(shorts.get("hooks", []), start=1):
                copybox(f"후킹 {idx}", item)

    st.markdown("### 대본")

    st.text_area(
        "대표 대본",
        active_content.get("script")
        or shorts.get("script", ""),
        height=220,
    )

    st.markdown("### CTA")

    st.write(
        active_content.get("cta")
        or shorts.get("cta", "")
    )

    if shorts_variants:
        st.divider()

        st.subheader("📦 콘텐츠 유형별 후보")

        for variant in shorts_variants:

            with st.expander(
                f"{variant.get('rank', '-')}. "
                f"{variant.get('type', '')} "
                f"({variant.get('score', '-') }점)"
            ):

                st.markdown("### 제목")
                st.write(variant.get("title", ""))

                st.markdown("### 후킹")
                st.write(variant.get("hook", ""))

                st.markdown("### 대본")

                st.text_area(
                    f"script_{variant.get('type')}",
                    variant.get("script", ""),
                    height=180,
                )

                st.markdown("### CTA")

                st.write(variant.get("cta", ""))

                capcut = variant.get("capcut", [])

                if capcut:
                    st.markdown("### CapCut")

                    for line in capcut:
                        st.write(f"• {line}")

    st.divider()

    st.subheader("업로드 미리보기")

    st.write(
        "유튜브 제목 :",
        upload.get("youtube_title", ""),
    )

    st.write(
        "해시태그 :",
        " ".join(upload.get("hashtags", [])),
    )