import streamlit as st

from modules.content.content_factory import ContentFactory

from modules.video.cut_planner import CutPlanner

def _get_selected_variant(data):
    variants = data.get("shorts_variants", [])

    if not variants:
        return {}

    return next(
        (v for v in variants if v.get("recommended")),
        variants[0],
    )


def _write_script(script):
    if isinstance(script, list):
        for line in script:
            st.write(f"- {line}")
    elif isinstance(script, str):
        for line in script.splitlines():
            st.write(line)
    else:
        st.write(script)


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

        content_pack["cut_plan"] = CutPlanner().build(content_pack)

        saved = factory.save_content_pack(project, content_pack)
        st.session_state[f"ai_content_pack_result_{project.id}"] = saved
        st.success("AI 콘텐츠 팩을 생성했습니다.")

    saved = st.session_state.get(f"ai_content_pack_result_{project.id}")

    if not saved:
        st.caption("아직 생성된 AI 콘텐츠 팩이 없습니다.")
        return None

    data = saved.get("data", {})
    selected = _get_selected_variant(data)

    st.write("DEBUG cut_plan:", data.get("cut_plan"))
    st.markdown("### 상품 분석")
    analysis_data = data.get("analysis", {})
    if analysis_data.get("summary"):
        st.write(analysis_data.get("summary"))

    if selected:
        st.info(
            f"대표 콘텐츠: {selected.get('type', '추천안')} / "
            f"점수 {selected.get('score', '-')}"
        )

    st.markdown("### 쇼츠 제목")
    if selected.get("title"):
        st.write(f"- {selected.get('title')}")
    else:
        for title in data.get("shorts", {}).get("titles", []):
            st.write(f"- {title}")

    st.markdown("### 후킹 문구")
    if selected.get("hook"):
        st.write(f"- {selected.get('hook')}")
    else:
        for hook in data.get("shorts", {}).get("hooks", []):
            st.write(f"- {hook}")

    st.markdown("### 대본")
    if selected.get("script"):
        _write_script(selected.get("script"))
    else:
        _write_script(data.get("shorts", {}).get("script", []))

    st.markdown("### CapCut 타임라인")
    capcut_items = selected.get("capcut") or data.get("shorts", {}).get("capcut_timeline", [])

    for item in capcut_items:
        if isinstance(item, dict):
            st.write(
                f"- {item.get('time', '')} / "
                f"{item.get('scene', '')} / "
                f"{item.get('caption', '')}"
            )
        else:
            st.write(f"- {item}")

    st.markdown("### 썸네일")
    thumbnail = data.get("thumbnail", {})
    st.write(thumbnail.get("main_text", selected.get("hook", "")))
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
    st.write(inpock.get("main_text", selected.get("hook", "")))
    if inpock.get("image_prompt"):
        st.text_area(
            "인포크 이미지 프롬프트",
            inpock.get("image_prompt", ""),
            height=100,
        )

    st.markdown("### 업로드")
    upload = data.get("upload_bundle") or data.get("upload", {})
    st.write(upload.get("youtube_title", selected.get("title", "")))
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