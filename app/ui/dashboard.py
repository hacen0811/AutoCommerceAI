import streamlit as st
from modules.project.repository import ProjectRepository
from modules.analytics.repository import PerformanceRepository


def show_dashboard():
    projects = ProjectRepository().all()
    performances = PerformanceRepository().all()

    st.title("🏠 AutoCommerceAI X")
    st.caption("상품 + 영상 + CapCut + 업로드 + 성과를 한 곳에서 관리합니다.")

    c1, c2, c3 = st.columns(3)
    c1.metric("프로젝트", len(projects))
    c2.metric("성과 데이터", len(performances))
    c3.metric("총 조회수", f"{sum(p.views for p in performances):,}")

    st.divider()
    st.subheader("오늘 해야 할 작업")
    if not projects:
        st.info("새 프로젝트를 먼저 생성하세요.")
        return

    for p in projects[:10]:
        checklist = ProjectRepository().checklist(p.id)
        missing = []
        if not checklist.source_video:
            missing.append("원본영상")
        if not checklist.capcut_edit:
            missing.append("CapCut")
        if not checklist.inpock:
            missing.append("인포크")
        if not checklist.youtube:
            missing.append("유튜브")
        if not checklist.instagram:
            missing.append("인스타")
        if not checklist.performance:
            missing.append("성과")
        st.write(f"• **{p.product_name}** → 남은 작업: {', '.join(missing) if missing else '완료'}")
