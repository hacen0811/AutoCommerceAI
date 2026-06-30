import streamlit as st
from modules.project.repository import ProjectRepository
from modules.analytics.repository import PerformanceRepository


def show_performance():
    st.title("📈 성과")

    projects = ProjectRepository().all()
    if not projects:
        st.info("프로젝트가 없습니다.")
        return

    labels = {f"{p.id} | {p.product_name}": p for p in projects}
    project = labels[st.selectbox("프로젝트", list(labels.keys()))]

    with st.form("perf"):
        views = st.number_input("조회수", min_value=0, step=100)
        likes = st.number_input("좋아요", min_value=0, step=10)
        comments = st.number_input("댓글", min_value=0, step=1)
        saves = st.number_input("저장", min_value=0, step=1)
        note = st.text_area("메모")
        if st.form_submit_button("성과 저장"):
            PerformanceRepository().create(project.id, views, likes, comments, saves, note)
            ProjectRepository().update_checklist(project.id, performance=True)
            st.success("성과 저장 완료")

    st.divider()
    rows = PerformanceRepository().all()
    for r in rows[:20]:
        st.write(f"프로젝트 {r.project_id} / 조회수 {r.views:,} / 좋아요 {r.likes:,} / 댓글 {r.comments:,} / 저장 {r.saves:,}")
