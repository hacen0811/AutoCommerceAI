import streamlit as st

from app.ui.content_pack.helpers import copybox


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