import streamlit as st


def safe_project_id(project):
    return str(getattr(project, "id", "default")).replace(" ", "_").replace("/", "_")


def show_tab_edit_ai(pack, project):
    st.subheader("✂️ AI 컷 추천 / AI Edit Assistant")

    if not st.checkbox("편집 AI 상세 보기", key=f"show_edit_ai_{safe_project_id(project)}"):
        st.info("필요할 때만 편집 AI 상세 내용을 열어보세요.")
    else:
        cut_plan = pack.get("cut_plan", [])

        if not cut_plan:
            st.info("아직 AI 컷 추천이 없습니다. AI 콘텐츠 팩을 다시 생성해 주세요.")
        else:
            for cut in cut_plan:
                with st.container(border=True):
                    st.markdown(f"#### Scene {cut.get('scene', '-')}")
                    st.write(f"후보영상: {cut.get('candidate', '-')}")
                    st.write(f"검색어: {cut.get('query', '-')}")
                    st.write(f"추천 구간: {cut.get('start', '-')} ~ {cut.get('end', '-')}")
                    st.write(f"Confidence: {cut.get('confidence', '-')}")
                    st.write(f"추천 이유: {cut.get('reason', '-')}")
                    st.write(f"효과음: {cut.get('effect', '-')}")
                    st.write(f"줌: {cut.get('zoom', '-')}")
                    st.write(f"자막: {cut.get('subtitle', '-')}")

                    if cut.get("url"):
                        st.link_button(
                            "후보영상 열기",
                            cut.get("url"),
                            use_container_width=True,
                        )

    st.divider()

    edit = pack.get("edit_assistant", {})

    st.subheader("🎬 AI Edit Assistant")

    if not edit:
        st.info("아직 편집 AI 데이터가 없습니다.")
        return

    st.markdown(f"**스타일:** {edit.get('style', '')}")
    st.markdown(f"**목표:** {edit.get('goal', '')}")

    bgm = edit.get("bgm", {})
    st.markdown("### BGM")
    st.write(f"- 타입: {bgm.get('type', '')}")
    st.write(f"- 볼륨: {bgm.get('volume', '')}")

    subtitle = edit.get("subtitle", {})
    st.markdown("### 자막 프리셋")
    st.write(f"- 폰트: {subtitle.get('font', '')}")
    st.write(f"- 크기: {subtitle.get('size', '')}")
    st.write(f"- 색상: {subtitle.get('color', '')}")
    st.write(f"- 강조색: {subtitle.get('highlight', '')}")
    st.write(f"- 획: {subtitle.get('stroke', '')}")
    st.write(f"- 위치: {subtitle.get('position', '')}")
    st.write(f"- 애니메이션: {subtitle.get('animation', '')}")

    st.markdown("### 장면별 편집 지시서")

    timeline = edit.get("timeline", [])

    if not timeline:
        st.caption("장면별 편집 지시서가 없습니다.")
    else:
        for i, item in enumerate(timeline, start=1):
            with st.container(border=True):
                st.markdown(f"#### Scene {i}")
                st.write(f"컷: {item.get('cut', '')}")
                st.write(f"줌: {item.get('zoom', '')}")
                st.write(f"자막 위치: {item.get('subtitle_position', '')}")
                st.write(f"자막 애니메이션: {item.get('subtitle_animation', '')}")
                st.write(f"효과음: {item.get('sfx', '')}")
                st.write(f"BGM 볼륨: {item.get('bgm_volume', '')}")

    st.markdown("### CTA")
    st.write(edit.get("cta", ""))

    st.markdown("---")
    st.subheader("✅ 편집 체크리스트")

    tasks = [
        "컷 편집 완료",
        "자동 자막 생성",
        "자막 수정",
        "강조색 적용",
        "효과음 적용",
        "BGM 적용",
        "CTA 확인",
        "썸네일 저장",
        "인포크 저장",
        "영상 내보내기",
        "업로드",
    ]

    for task in tasks:
        st.checkbox(
            task,
            key=f"edit_task_{safe_project_id(project)}_{task}",
        )