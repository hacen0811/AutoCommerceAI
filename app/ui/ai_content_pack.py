import streamlit as st

from modules.content.content_factory import ContentFactory


def show_content_pack_view(project, selected_sources=None, analysis=None):
    st.divider()
    st.subheader("🚀 AI 콘텐츠 팩")

    if st.button(
        "🚀 AI 콘텐츠 팩 생성",
        key=f"create_content_pack_{project.id}",
        use_container_width=True,
    ):
        factory = ContentFactory()

        content_pack = factory.build_content_pack(
            project=project,
            selected_sources=selected_sources or [],
            analysis=analysis,
        )

        saved = factory.save_content_pack(project, content_pack)

        st.session_state[f"ai_content_pack_result_{project.id}"] = saved
        st.success("AI 콘텐츠 팩을 생성했습니다.")

    saved = st.session_state.get(f"ai_content_pack_result_{project.id}")

    if not saved:
        st.caption("아직 생성된 AI 콘텐츠 팩이 없습니다.")
        return None

    data = saved.get("data", {})

    st.markdown("### 상품 분석")
    analysis_data = data.get("analysis", {})
    if analysis_data.get("summary"):
        st.write(analysis_data.get("summary"))

    if analysis_data.get("hooks"):
        st.markdown("**후킹 포인트**")
        for hook in analysis_data.get("hooks", []):
            st.write(f"- {hook}")

    st.markdown("### 쇼츠 제목")
    for title in data.get("shorts", {}).get("titles", []):
        st.write(f"- {title}")

    st.markdown("### 후킹 문구")
    for hook in data.get("shorts", {}).get("hooks", []):
        st.write(f"- {hook}")

    st.markdown("### 대본")
    for line in data.get("shorts", {}).get("script", []):
        st.write(f"- {line}")

    st.markdown("### CapCut 타임라인")
    for item in data.get("capcut", {}).get("timeline", []):
        st.write(
            f"- {item.get('time')} / "
            f"{item.get('scene')} / "
            f"{item.get('caption')}"
        )

    st.markdown("### 썸네일")
    thumbnail = data.get("thumbnail", {})
    st.write(thumbnail.get("main_text", ""))
    if thumbnail.get("sub_text"):
        st.caption(thumbnail.get("sub_text"))
    if thumbnail.get("image_prompt"):
        st.text_area(
            "썸네일 이미지 프롬프트",
            thumbnail.get("image_prompt", ""),
            height=100,
        )

    st.markdown("### 인포크")
    inpock = data.get("inpock", {})
    st.write(inpock.get("main_text", ""))
    if inpock.get("image_prompt"):
        st.text_area(
            "인포크 이미지 프롬프트",
            inpock.get("image_prompt", ""),
            height=100,
        )

    st.markdown("### 업로드")
    upload = data.get("upload", {})
    st.write(upload.get("youtube_title", ""))
    st.text_area(
        "유튜브 설명",
        upload.get("youtube_desc", ""),
        height=100,
    )
    st.text_area(
        "인스타 본문",
        upload.get("instagram_body", ""),
        height=120,
    )

    hashtags = upload.get("hashtags", [])
    if hashtags:
        st.write(" ".join(hashtags))

    return saved