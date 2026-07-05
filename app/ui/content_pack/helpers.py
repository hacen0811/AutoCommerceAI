import json
from pathlib import Path

import streamlit as st


def read_json(path):
    try:
        if not path:
            return {}
        p = Path(path)
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {}


def copybox(label, text):
    st.markdown(f"**{label}**")
    st.code(text or "", language="text")


def show_content_pack_view(
    project,
    selected_sources=None,
    analysis=None,
    content_pack=None,
    paths=None,
):
    st.divider()
    st.subheader("📦 AI 콘텐츠 팩")

    pack = content_pack or {}

    if not pack and paths:
        json_path = paths.get("json_path")
        pack = read_json(json_path)

    if not pack:
        st.info("아직 생성된 콘텐츠 팩이 없습니다.")
        st.caption("원클릭 실행을 완료하면 AI 콘텐츠 팩이 여기에 표시됩니다.")
        return

    project_name = (
        pack.get("project_name")
        or pack.get("product_name")
        or getattr(project, "product_name", "")
        or getattr(project, "title", "")
        or "선택 상품"
    )

    st.success(f"{project_name} 콘텐츠 팩이 생성되었습니다.")

    if paths:
        json_path = paths.get("json_path")
        txt_path = paths.get("txt_path")

        if json_path:
            st.caption(f"JSON 저장 위치: {json_path}")
        if txt_path:
            st.caption(f"TXT 저장 위치: {txt_path}")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "요약",
            "쇼츠 문구",
            "본문/CTA",
            "썸네일",
            "CapCut",
            "전체 JSON",
        ]
    )

    with tab1:
        show_summary_tab(pack, selected_sources, analysis)

    with tab2:
        show_shorts_tab(pack)

    with tab3:
        show_caption_tab(pack)

    with tab4:
        show_thumbnail_tab(pack)

    with tab5:
        show_capcut_tab(pack)

    with tab6:
        st.json(pack)


def show_summary_tab(pack, selected_sources=None, analysis=None):
    project_name = pack.get("project_name", "선택 상품")

    st.markdown("### 콘텐츠 팩 요약")
    st.write(f"**상품명:** {project_name}")

    final_package = pack.get("final_package", {})
    if final_package:
        st.write(f"**상태:** {final_package.get('status', 'ready')}")

        items = final_package.get("items", [])
        if items:
            st.markdown("**포함 항목**")
            for item in items:
                st.write(f"- {item}")

    edit = pack.get("edit_assistant", {})
    if edit:
        st.markdown("### 편집 가이드 요약")
        st.write(edit.get("summary", ""))

    if selected_sources:
        st.markdown("### 채택 영상 후보")
        for idx, item in enumerate(selected_sources, start=1):
            st.write(
                f"{idx}. {item.get('platform', '')} / "
                f"{item.get('query', '')} / "
                f"{item.get('url', '')}"
            )

    if analysis:
        st.markdown("### 상품 분석 요약")
        keywords = analysis.get("keywords", [])
        if keywords:
            st.write(", ".join(keywords))


def show_shorts_tab(pack):
    shorts = pack.get("shorts", {})

    titles = shorts.get("titles", [])
    hooks = shorts.get("hooks", [])

    st.markdown("### 쇼츠 제목")
    if titles:
        for idx, title in enumerate(titles, start=1):
            copybox(f"제목 {idx}", title)
    else:
        st.caption("생성된 제목이 없습니다.")

    st.markdown("### 후킹 문구")
    if hooks:
        for idx, hook in enumerate(hooks, start=1):
            copybox(f"후킹 {idx}", hook)
    else:
        st.caption("생성된 후킹 문구가 없습니다.")


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


def show_capcut_tab(pack):
    edit = pack.get("edit_assistant", {})
    capcut = edit.get("capcut", {})
    scene_plan = edit.get("scene_plan", [])

    st.markdown("### CapCut 기본 설정")

    st.write(f"**화면비율:** {capcut.get('format', '9:16')}")
    st.write(f"**자막 위치:** {capcut.get('subtitle_position', '중앙 하단')}")

    subtitle = capcut.get("subtitle_style", {})
    if subtitle:
        st.markdown("### 자막 스타일")
        st.write(f"- 폰트: {subtitle.get('font', '')}")
        st.write(f"- 본문 크기: {subtitle.get('main_size', '')}")
        st.write(f"- 강조 크기: {subtitle.get('highlight_size', '')}")
        st.write(f"- 자막 획: {subtitle.get('stroke', '')}")
        st.write(f"- 그림자: {subtitle.get('shadow', '')}")
        st.write(f"- 강조 색상: {subtitle.get('highlight_color', '')}")

    bgm = capcut.get("bgm", {})
    if bgm:
        st.markdown("### BGM")
        st.write(f"- 분위기: {bgm.get('type', '')}")
        st.write(f"- 볼륨: {bgm.get('volume', '')}")

    sfx = capcut.get("sfx", [])
    if sfx:
        st.markdown("### 효과음")
        for item in sfx:
            st.write(
                f"- {item.get('scene', '')}: "
                f"{item.get('effect', '')} / "
                f"{item.get('volume', '')}"
            )

    if scene_plan:
        st.markdown("### 장면별 편집 계획")
        for scene in scene_plan:
            st.markdown(f"**{scene.get('scene')}. {scene.get('role')}**")
            st.write(f"- 시간: {scene.get('duration', '')}")
            st.write(f"- 문구: {scene.get('text', '')}")
            st.write(f"- 편집: {scene.get('edit', '')}")