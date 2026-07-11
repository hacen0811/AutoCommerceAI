import streamlit as st


def safe_project_id(project):
    return (
        str(getattr(project, "id", "default"))
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )


def _value(data, *keys, default="-"):
    """
    여러 키 중 값이 존재하는 첫 번째 값을 반환합니다.
    기존 데이터 구조와 새 CutPlanner 구조를 모두 지원합니다.
    """
    if not isinstance(data, dict):
        return default

    for key in keys:
        value = data.get(key)

        if value is not None and value != "":
            return value

    return default


def _format_confidence(value):
    if value in (None, ""):
        return "-"

    try:
        number = float(value)

        if number.is_integer():
            return f"{int(number)}점"

        return f"{number:.1f}점"
    except (TypeError, ValueError):
        return str(value)


def _show_confidence_progress(value):
    try:
        number = float(value)
        normalized = max(0.0, min(number / 100.0, 1.0))
        st.progress(normalized)
    except (TypeError, ValueError):
        pass


def show_tab_edit_ai(pack, project):
    """
    AI 컷 추천과 AI Edit Assistant 정보를 표시합니다.

    주요 표시 항목:
    - 후보 영상
    - 검색어와 URL
    - 추천 구간
    - Confidence
    - 추천 이유
    - 전환 효과
    - 재생 속도
    - 카메라 연출
    - 자막 위치
    - Hook Level
    - BGM
    - 효과음
    """

    pack = pack or {}
    project_key = safe_project_id(project)

    st.subheader("✂️ AI 컷 추천 / AI Edit Assistant")

    show_detail = st.checkbox(
        "편집 AI 상세 보기",
        key=f"show_edit_ai_{project_key}",
    )

    if not show_detail:
        st.info("필요할 때 편집 AI 상세 내용을 열어보세요.")
        return

    cut_plan = pack.get("cut_plan") or []

    st.markdown("### AI 컷 추천")

    if not cut_plan:
        st.info(
            "아직 AI 컷 추천 결과가 없습니다. "
            "AI 콘텐츠 팩을 다시 생성해 주세요."
        )
    else:
        st.success(f"총 {len(cut_plan)}개 장면의 편집 추천이 생성되었습니다.")

        for index, cut in enumerate(cut_plan, start=1):
            scene = _value(
                cut,
                "scene",
                "scene_number",
                default=index,
            )

            purpose = _value(
                cut,
                "purpose",
                "role",
                "scene_purpose",
            )

            candidate = _value(
                cut,
                "candidate",
                "platform",
                "source",
            )

            query = _value(
                cut,
                "query",
                "keyword",
                "search_query",
            )

            url = _value(
                cut,
                "url",
                "search_url",
                "video_url",
                "play_url",
                default="",
            )

            start = _value(
                cut,
                "start",
                "start_time",
            )

            end = _value(
                cut,
                "end",
                "end_time",
            )

            confidence = _value(
                cut,
                "confidence",
                "confidence_score",
                default="-",
            )

            reason = _value(
                cut,
                "reason",
                "recommendation_reason",
            )

            transition = _value(
                cut,
                "transition",
                "transition_effect",
                "effect",
            )

            speed = _value(
                cut,
                "speed",
                "playback_speed",
            )

            camera = _value(
                cut,
                "camera",
                "camera_motion",
                "camera_effect",
                "zoom",
            )

            subtitle_position = _value(
                cut,
                "subtitle_position",
                "caption_position",
                "subtitle",
            )

            hook_level = _value(
                cut,
                "hook_level",
                "hook_strength",
            )

            bgm = _value(
                cut,
                "bgm",
                "bgm_recommendation",
                "music",
            )

            bgm_volume = _value(
                cut,
                "bgm_volume",
                "music_volume",
            )

            sound_effect = _value(
                cut,
                "sound_effect",
                "sfx",
                "effect_sound",
            )

            with st.container(border=True):
                st.markdown(f"#### Scene {scene}")

                if purpose != "-":
                    st.write(f"**장면 목적:** {purpose}")

                source_col, timing_col = st.columns(2)

                with source_col:
                    st.write(f"**후보 영상:** {candidate}")
                    st.write(f"**검색어:** {query}")

                with timing_col:
                    st.write(f"**추천 구간:** {start} ~ {end}")
                    st.write(
                        f"**Confidence:** "
                        f"{_format_confidence(confidence)}"
                    )

                _show_confidence_progress(confidence)

                if url:
                    st.link_button(
                        "후보 영상 열기",
                        str(url),
                        use_container_width=True,
                    )

                st.divider()

                edit_col1, edit_col2 = st.columns(2)

                with edit_col1:
                    st.write(f"**전환 효과:** {transition}")
                    st.write(f"**재생 속도:** {speed}")
                    st.write(f"**카메라 연출:** {camera}")
                    st.write(f"**Hook Level:** {hook_level}")

                with edit_col2:
                    st.write(f"**자막 위치:** {subtitle_position}")
                    st.write(f"**BGM:** {bgm}")
                    st.write(f"**BGM 볼륨:** {bgm_volume}")
                    st.write(f"**효과음:** {sound_effect}")

                st.divider()
                st.write(f"**추천 이유:** {reason}")

    st.divider()

    edit = pack.get("edit_assistant") or {}

    st.subheader("🎬 AI Edit Assistant")

    if not edit:
        st.info("아직 편집 AI 데이터가 없습니다.")
        return

    style = edit.get("style") or "-"
    goal = edit.get("goal") or "-"

    st.markdown(f"**스타일:** {style}")
    st.markdown(f"**목표:** {goal}")

    bgm = edit.get("bgm") or {}

    st.markdown("### BGM")
    st.write(f"- 유형: {_value(bgm, 'type', 'style', 'name')}")
    st.write(f"- 볼륨: {_value(bgm, 'volume', 'bgm_volume')}")
    st.write(f"- 분위기: {_value(bgm, 'mood', 'tone')}")

    subtitle = edit.get("subtitle") or {}

    st.markdown("### 자막 스타일")
    st.write(f"- 폰트: {_value(subtitle, 'font')}")
    st.write(f"- 크기: {_value(subtitle, 'size')}")
    st.write(f"- 색상: {_value(subtitle, 'color')}")
    st.write(f"- 강조색: {_value(subtitle, 'highlight')}")
    st.write(f"- 외곽선: {_value(subtitle, 'stroke')}")
    st.write(f"- 위치: {_value(subtitle, 'position')}")
    st.write(f"- 애니메이션: {_value(subtitle, 'animation')}")

    st.markdown("### 장면별 편집 지시서")

    timeline = (
        edit.get("timeline")
        or edit.get("scene_plan")
        or []
    )

    if not timeline:
        st.caption("장면별 편집 지시서가 없습니다.")
    else:
        for index, item in enumerate(timeline, start=1):
            scene = _value(
                item,
                "scene",
                "scene_number",
                default=index,
            )

            with st.container(border=True):
                st.markdown(f"#### Scene {scene}")

                timeline_col1, timeline_col2 = st.columns(2)

                with timeline_col1:
                    st.write(
                        f"**컷 편집:** "
                        f"{_value(item, 'cut', 'edit', 'purpose')}"
                    )
                    st.write(
                        f"**전환 효과:** "
                        f"{_value(item, 'transition', 'effect')}"
                    )
                    st.write(
                        f"**재생 속도:** "
                        f"{_value(item, 'speed', 'playback_speed')}"
                    )
                    st.write(
                        f"**카메라 연출:** "
                        f"{_value(item, 'camera', 'camera_motion', 'zoom')}"
                    )

                with timeline_col2:
                    st.write(
                        f"**자막 위치:** "
                        f"{_value(item, 'subtitle_position')}"
                    )
                    st.write(
                        f"**자막 애니메이션:** "
                        f"{_value(item, 'subtitle_animation')}"
                    )
                    st.write(
                        f"**효과음:** "
                        f"{_value(item, 'sound_effect', 'sfx')}"
                    )
                    st.write(
                        f"**BGM 볼륨:** "
                        f"{_value(item, 'bgm_volume')}"
                    )

    st.markdown("### CTA")
    st.write(edit.get("cta") or "-")

    st.markdown("---")
    st.subheader("✅ 편집 체크리스트")

    tasks = [
        "컷 편집 완료",
        "자동 자막 생성",
        "자막 수정",
        "강조색 적용",
        "전환 효과 적용",
        "재생 속도 확인",
        "카메라 연출 적용",
        "효과음 적용",
        "BGM 적용",
        "CTA 확인",
        "썸네일 확인",
        "인포크 확인",
        "영상 내보내기",
        "업로드",
    ]

    for index, task in enumerate(tasks):
        st.checkbox(
            task,
            key=f"edit_task_{project_key}_{index}",
        )