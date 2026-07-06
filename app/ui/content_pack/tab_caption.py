import streamlit as st

from app.ui.content_pack.helpers import copybox


def show_caption_tab(pack):
    captions = pack.get("captions", {})
    upload = pack.get("upload_bundle", {})
    edit = pack.get("edit_assistant", {})
    platforms = edit.get("platforms", {})
    shorts_variants = pack.get("shorts_variants", [])

    active_content = (
        pack.get("selected_variant")
        or next((v for v in shorts_variants if v.get("recommended")), None)
        or (shorts_variants[0] if shorts_variants else {})
        or {}
    )

    st.markdown("### 유튜브 쇼츠")

    youtube_title = (
        active_content.get("title")
        or upload.get("youtube_title")
        or ""
    )

    if youtube_title:
        copybox("유튜브 제목", youtube_title)

    youtube_desc = (
        captions.get("youtube_shorts")
        or upload.get("youtube_desc")
        or ""
    )

    if not youtube_desc:
        youtube_cta = (
            active_content.get("cta")
            or platforms.get("youtube_shorts", {}).get("cta")
            or "댓글에 '정보' 남겨주세요 👇"
        )

        youtube_desc = (
            "🔗 제품 정보는 영상 아래 설명란 링크 또는 프로필 링크를 확인해주세요.\n\n"
            "쿠팡파트너스 활동을 통해 일정액의 수수료를 제공받을 수 있습니다.\n\n"
            f"{youtube_cta}"
        )

    copybox("유튜브 설명", youtube_desc)

    st.divider()

    st.markdown("### 인스타그램 릴스")

    instagram_body = (
        captions.get("instagram_reels")
        or upload.get("instagram_body")
        or ""
    )

    if not instagram_body:
        instagram_cta = (
            active_content.get("cta")
            or platforms.get("instagram_reels", {}).get("cta")
            or "팔로우 하시고, 댓글에 '정보' 남겨주세요 👇"
        )

        instagram_body = (
            "왜 이제 알았지 싶은 생활템 ✨\n\n"
            "매일 쓰는 제품은 작은 차이가 크게 느껴지더라고요.\n\n"
            f"{instagram_cta}"
        )

    copybox("릴스 본문", instagram_body)

    hashtags = upload.get("hashtags", [])

    if hashtags:
        copybox("해시태그", " ".join(hashtags))