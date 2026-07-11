import streamlit as st

from app.ui.candidate_card import show_candidate_card
from app.ui.live_sources import show_live_sources
from app.ui.content_pack.source_candidates_view import show_source_candidates
from app.utils.project_keys import safe_project_id


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


def candidate_query(item):
    return (
        item.get("query")
        or item.get("keyword")
        or item.get("search_query")
        or item.get("title")
        or "-"
    )


def candidate_url(item):
    return (
        item.get("url")
        or item.get("search_url")
        or item.get("video_url")
        or item.get("play_url")
        or ""
    )


def show_top_candidates(project, outputs):
    source_plan = outputs.get("source_plan", {}) or {}
    video_sources = outputs.get("video_sources", {}) or {}
    product_plan = outputs.get("product_plan", {}) or {}

    #candidate_groups = [
        #("타오바오 TOP10", "taobao", product_plan.get("taobao_top10") or source_plan.get("taobao_top10")),
        #("1688 TOP10", "1688", product_plan.get("source_1688_top10") or source_plan.get("source_1688_top10")),
        #("도우인 TOP10", "tiktok", product_plan.get("douyin_top10") or source_plan.get("douyin_top10")),
    #]

    #shown = False

    #for title, platform, items in candidate_groups:
        #if not items:
            #continue

        #shown = True
        #st.markdown(f"### {title}")

        #for idx, item in enumerate(items, start=1):
            #if not isinstance(item, dict):
                #continue

            #item = dict(item)
            #item.setdefault("rank", idx)

            #show_candidate_card(
                #project=project,
                #platform=platform,
                #item=item,
                #safe_project_id=safe_project_id,
            #)

    candidates = video_sources.get("candidates") or []
    if candidates:
        shown = True
        st.markdown("### 전체 검색 후보")

        for idx, item in enumerate(candidates[:12], start=1):
            if not isinstance(item, dict):
                continue

            item = dict(item)
            item.setdefault("rank", idx)

            show_candidate_card(
                project=project,
                platform=item.get("platform", "source"),
                item=item,
                safe_project_id=safe_project_id,
            )

    live_sources = (
        video_sources.get("live_collection")
        or source_plan.get("live_collection")
        or outputs.get("live_collection")
    )

    if live_sources:
        shown = True
        show_live_sources(project, live_sources)

    if not shown:
        st.caption("표시할 후보 카드가 없습니다.")


def show_result_summary(project, outputs):
    st.markdown("### AI 상품 분석 요약")

    product_plan = outputs.get("product_plan", {})
    keywords = product_plan.get("keywords", [])

    if keywords:
        st.write(", ".join(keywords))
    else:
        st.caption("상품 분석 키워드가 없습니다.")

    st.markdown("### 후보 카드")
    show_top_candidates(project, outputs)
    
    st.divider()
    show_source_candidates()


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
        show_result_summary(project, outputs)
        show_video_quality(outputs, state)

    with tab2:
        st.json(outputs)

    with tab3:
        st.json(state)