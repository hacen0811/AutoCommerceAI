import streamlit as st


def show_step_status(state, path_debug=None):
    st.subheader("단계별 상태")

    for step in state.get("steps", []):
        status = step.get("status")
        icon = "✅" if status == "done" else "⚠️" if status == "failed" else "□"
        st.write(f"{icon} {step.get('label')} / {status}")

    if state.get("errors"):
        st.subheader("오류")

        for err in state.get("errors", []):
            st.warning(f"{err.get('step')}: {err.get('error')}")

            if path_debug:
                st.caption(f"영상 경로 확인: {path_debug}")


def show_result_summary(outputs):
    product_plan = outputs.get("product_plan", {})
    keywords = product_plan.get("keywords", [])

    st.markdown("### AI 상품 분석 요약")

    if keywords:
        st.write(", ".join(keywords))
    else:
        st.caption("상품 분석 키워드가 없습니다.")

    selected = outputs.get("candidate_selection", {}).get("top3", [])

    if selected:
        st.markdown("### 채택 영상 후보")

        for idx, item in enumerate(selected, start=1):
            st.write(
                f"{idx}. {item.get('platform', '')} / "
                f"{item.get('query', '')} / "
                f"{item.get('url', '')}"
            )
    else:
        st.caption("채택된 영상 후보가 없습니다.")


def show_video_quality(outputs, state):
    video_quality = outputs.get("video_quality") or state.get("results", {}).get("video_quality", {})

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

    if score is not None:
        st.metric("품질 점수", score)

    if grade:
        st.write(f"등급: {grade}")

    if summary:
        st.caption(summary)


def show_pipeline_result(project, result, path_debug=None):
    st.success(result.get("summary", "원클릭 파이프라인이 완료되었습니다."))

    state = result.get("state", {})
    outputs = result.get("outputs", {})

    progress = int(state.get("progress", 0) or 0)
    st.progress(progress)

    show_step_status(state, path_debug)

    tab1, tab2, tab3 = st.tabs(["요약", "결과 JSON", "상태 JSON"])

    with tab1:
        show_result_summary(outputs)

    with tab2:
        st.json(outputs)

    with tab3:
        st.json(state)

    show_video_quality(outputs, state)