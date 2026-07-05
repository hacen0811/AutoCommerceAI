import streamlit as st

from app.ui.content_pack.helpers import copybox


def show_caption_tab(pack):
    captions = pack.get("captions", {})
    edit = pack.get("edit_assistant", {})
    platforms = edit.get("platforms", {})

    st.markdown("### 유튜브 쇼츠")

    youtube = captions.get("youtube_shorts", "")

    if not youtube:
        youtube_cta = (
            platforms.get("youtube_shorts", {}).get("cta")
            or "댓글에 '정보' 남겨주세요 👇"
        )

        youtube = (
            "🔗 제품 정보는 영상 아래 설명란 링크 또는 프로필 링크를 확인해주세요.\n"
            "(해당 링크를 통해 구매 시 일정 수수료를 제공받을 수 있습니다.)\n\n"
            f"{youtube_cta}"
        )

    copybox("유튜브 설명", youtube)

    st.markdown("### 인스타그램 릴스")

    instagram = captions.get("instagram_reels", "")

    if not instagram:
        instagram_cta = (
            platforms.get("instagram_reels", {}).get("cta")
            or "팔로우 하시고, 댓글에 '정보' 남겨주세요 👇"
        )

        instagram = (
            "생활이 조금 편해지는 추천템입니다.\n\n"
            f"{instagram_cta}\n\n"
            "#쇼핑쇼츠 #생활용품추천 #살림템 #쿠팡추천 #쿠팡파트너스"
        )

    copybox("릴스 본문", instagram)