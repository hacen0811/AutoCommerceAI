import streamlit as st


def show_summary_tab(pack, selected_sources=None, analysis=None):
    project_name = (
        pack.get("project_name")
        or pack.get("product_name")
        or "선택 상품"
    )

    st.markdown("### 콘텐츠 팩 요약")

    st.write(f"**상품명:** {project_name}")

    selected_sources = selected_sources or pack.get("selected_sources", [])

    if selected_sources:
        st.markdown("### 채택 후보")
        for idx, source in enumerate(selected_sources, start=1):
            with st.container(border=True):
                st.write(f"**{idx}. {source.get('platform', '-')}**")
                st.write(f"- 검색어: {source.get('query', '-')}")
                st.write(f"- 목적: {source.get('purpose', '-')}")
                st.write(f"- 점수: {source.get('score', '-')}")
                if source.get("url"):
                    st.link_button(
                        "후보 열기",
                        source.get("url"),
                        use_container_width=True,
                    )

    strategy = pack.get("content_strategy", {}) or analysis or {}

    if strategy:
        st.markdown("### 콘텐츠 전략")
        st.write(f"- 메인 앵글: {strategy.get('main_angle', '')}")
        st.write(f"- 구조: {strategy.get('structure', '')}")
        st.write(f"- 타깃: {strategy.get('target', '')}")

        selling_points = strategy.get("selling_points", [])

        if selling_points:
            st.write("- 셀링 포인트:")
            for point in selling_points:
                st.write(f"  - {point}")

        if strategy.get("recommended_format"):
            st.write(f"- 추천 포맷: {strategy.get('recommended_format')}")