import pandas as pd
import streamlit as st


def render_hooks_tab(ai: dict):
    st.subheader("후킹 10개")

    hooks = ai.get("hooks", [])

    if not hooks:
        st.warning("후킹 데이터가 없습니다.")
        return

    best_hook = ai.get("best_hook", "")

    st.markdown("### 🥇 최종 추천 후킹")
    st.success(best_hook)

    st.text_area(
        "추천 후킹 복사용",
        best_hook,
        height=80,
    )

    st.divider()

    rows = []
    for index, hook in enumerate(hooks, start=1):
        rows.append({
            "순위": index,
            "CTR 점수": hook.get("score", ""),
            "유형": hook.get("type", ""),
            "후킹": hook.get("text", ""),
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()

    all_hooks_text = "\n".join([
        f"{row['순위']}. [{row['유형']}] {row['후킹']} / CTR {row['CTR 점수']}점"
        for row in rows
    ])

    st.text_area(
        "전체 후킹 복사용",
        all_hooks_text,
        height=260,
    )