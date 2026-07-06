import streamlit as st


def show_step_status(state, path_debug=None):
    st.subheader("단계별 상태")

    steps = state.get("steps", [])

    if not steps:
        st.caption("표시할 단계 상태가 없습니다.")
        return

    for step in steps:
        status = step.get("status", "unknown")
        label = step.get("label") or step.get("step") or "unknown"

        if status == "done":
            icon = "✅"
        elif status == "failed":
            icon = "⚠️"
        elif status == "running":
            icon = "🔄"
        else:
            icon = "□"

        st.write(f"{icon} {label} / {status}")

    errors = state.get("errors", [])

    if errors:
        st.subheader("오류")

        for err in errors:
            st.warning(f"{err.get('step', 'unknown')}: {err.get('error', '알 수 없는 오류')}")

        if path_debug:
            with st.expander("영상 경로 디버그"):
                st.json(path_debug)


def show_result_summary(outputs):
    st.markdown("### AI 상품 분석 요약")

    product_plan = outputs.get("product_plan", {})
    keywords = product_plan.get("keywords", [])

    if keywords:
        st.write(", ".join(keywords))
    else:
        st.caption("상품 분석 키워드가 없습니다.")

    selected = outputs.get("candidate_selection", {}).get("top3", [])

    st.markdown("### 채택 영상 후보")

    if not selected:
        st.caption("채택된 영상 후보가 없습니다.")
        return

    for idx, item in enumerate(selected, start=1):
        platform = item.get("platform", "-")
        query = item.get("query", "-")
        url = item.get("url", "-")

        with st.container(border=True):
            st.write(f"**{idx}. {platform}**")
            st.write(f"검색어: {query}")
            st.write(f"URL: {url}")


def show_video_quality(outputs, state):
    video_quality = (
        outputs.get("video_quality")
        or state.get("results", {}).get("video_quality", {})
    )

    if not video_quality:
        return

    st.divider()
    st.subheader("AI 영상 품질 평가")

    if video_quality.get("ok") is False:
        st.warning(
            f"영상 품질 평가 실패: {video_quality.get('reason', '알 수 없는 오류')}"
        )
        return

    score = video_quality.get("score")
    grade = video_quality.get("grade")
    summary = (
        video_quality.get("summary")
        or video_quality.get("reason")
        or video_quality.get("recommendation")
    )

    col1, col2 = st.columns(2)

    with col1:
        if score is not None:
            st.metric("품질 점수", score)
        else:
            st.caption("품질 점수가 없습니다.")

    with col2:
        if grade:
            st.metric("등급", grade)
        else:
            st.caption("등급 정보가 없습니다.")

    if summary:
        st.caption(summary)


def show_pipeline_result(project, result, path_debug=None):
    if not result:
        st.info("아직 원클릭 실행 결과가 없습니다.")
        return

    st.success(result.get("summary", "원클릭 파이프라인이 완료되었습니다."))

    state = result.get("state", {})
    outputs = result.get("outputs", {})

    progress = int(state.get("progress", 0) or 0)
    progress = max(0, min(progress, 100))

    st.progress(progress)

    show_step_status(state, path_debug)

    tab1, tab2, tab3 = st.tabs(["요약", "결과 JSON", "상태 JSON"])

    with tab1:
        show_result_summary(outputs)
        show_video_quality(outputs, state)

    with tab2:
        st.json(outputs)

    with tab3:
        st.json(state)