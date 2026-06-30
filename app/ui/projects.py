import streamlit as st
from modules.project.repository import ProjectRepository
from modules.project.service import ProjectService
from modules.video.service import VideoService
from app.ui.render import render_project_detail


def show_projects():
    st.title("📦 프로젝트")

    mode = st.radio("작업", ["새 프로젝트", "프로젝트 열기"], horizontal=True)

    if mode == "새 프로젝트":
        with st.form("new_project"):
            product_name = st.text_input("상품명", placeholder="예: 문틈 방충망")
            coupang_url = st.text_input("쿠팡 원본 링크")
            partner_url = st.text_input("쿠팡파트너스 링크")
            taobao_url = st.text_input("타오바오 링크")
            douyin_url = st.text_input("도우인 링크")
            image_url = st.text_input("대표 이미지 URL")
            price = st.text_input("가격")
            category = st.text_input("카테고리")
            keyword = st.text_input("댓글 키워드", value="정보")
            uploaded_video = st.file_uploader("원본 영상 업로드", type=["mp4", "mov", "webm"])

            submitted = st.form_submit_button("프로젝트 생성")
            if submitted:
                if not product_name:
                    st.warning("상품명을 입력하세요.")
                    return
                video_path = VideoService().save_uploaded_video(uploaded_video) if uploaded_video else ""
                project = ProjectService().create_project({
                    "product_name": product_name,
                    "coupang_url": coupang_url,
                    "partner_url": partner_url,
                    "taobao_url": taobao_url,
                    "douyin_url": douyin_url,
                    "image_url": image_url,
                    "price": price,
                    "category": category,
                    "keyword": keyword,
                    "video_path": video_path,
                })
                st.success("프로젝트 생성 완료")
                checklist = ProjectRepository().checklist(project.id)
                render_project_detail(project, checklist)

    else:
        repo = ProjectRepository()
        projects = repo.all()
        if not projects:
            st.info("프로젝트가 없습니다.")
            return

        search = st.text_input("검색")
        if search:
            projects = [p for p in projects if search.lower() in p.product_name.lower()]

        labels = {f"{p.id} | {p.product_name} | {p.status}": p for p in projects}
        project = labels[st.selectbox("프로젝트 선택", list(labels.keys()))]
        checklist = repo.checklist(project.id)

        statuses = ["기획", "영상확보", "편집", "업로드", "성과확인", "완료"]
        new_status = st.selectbox("상태", statuses, index=statuses.index(project.status) if project.status in statuses else 0)
        if st.button("상태 저장"):
            repo.update_status(project.id, new_status)
            st.success("저장 완료")
            st.rerun()

        with st.expander("체크리스트 수정"):
            source_video = st.checkbox("원본 영상 확보", checklist.source_video)
            capcut_edit = st.checkbox("CapCut 편집", checklist.capcut_edit)
            inpock = st.checkbox("인포크 등록", checklist.inpock)
            youtube = st.checkbox("유튜브 업로드", checklist.youtube)
            instagram = st.checkbox("인스타 업로드", checklist.instagram)
            performance = st.checkbox("성과 입력", checklist.performance)
            if st.button("체크리스트 저장"):
                repo.update_checklist(
                    project.id,
                    source_video=source_video,
                    capcut_edit=capcut_edit,
                    inpock=inpock,
                    youtube=youtube,
                    instagram=instagram,
                    performance=performance,
                )
                st.success("체크리스트 저장 완료")
                st.rerun()

        render_project_detail(project, checklist)
