import json
from pathlib import Path
import streamlit as st

from modules.project.repository import ProjectRepository
from modules.project.project_selector import ProjectSelector
from modules.source.source_video_engine import SourceVideoEngine
from modules.source.video_ranker import SourceVideoRanker
from modules.source.batch_analyzer import BatchAnalyzer
from app.ui.render import copybox


def show_source_video_ai():
    st.title("🎥 Source Video AI")
    st.caption("타오바오/도우인 원본 영상 후보를 프로젝트별로 관리하고 랭킹합니다.")

    projects = ProjectSelector().all_projects()
    if not projects:
        st.info("프로젝트가 없습니다.")
        return

    labels = ProjectSelector().labels(projects)
    project = labels[st.selectbox("프로젝트", list(labels.keys()))]

    engine = SourceVideoEngine()
    plan = engine.make_search_plan(project)

    tab1, tab2, tab3, tab4 = st.tabs(["검색 계획", "영상 등록", "후보 랭킹", "Batch Analyze"])

    with tab1:
        st.subheader("검색어")
        for k, v in plan.get("search_queries", {}).items():
            copybox(k, v, 80)

        st.subheader("타오바오 TOP10")
        for item in plan.get("taobao_top10", []):
            st.write(f"{item.get('rank')}. {item.get('query')} — {item.get('purpose')}")

        st.subheader("도우인 TOP10")
        for item in plan.get("douyin_top10", []):
            st.write(f"{item.get('rank')}. {item.get('query')} — {item.get('purpose')}")

        st.subheader("수집 체크리스트")
        for item in plan.get("collection_checklist", []):
            st.write("□", item)
        st.warning(plan.get("legal_note"))

    with tab2:
        st.subheader("소스 URL 등록")
        url = st.text_input("도우인/타오바오 URL")
        memo = st.text_input("메모")
        if st.button("URL 등록", use_container_width=True):
            if not url.strip():
                st.warning("URL을 입력하세요.")
            else:
                item = engine.register_source_url(project, url.strip(), memo=memo.strip())
                st.success(f"등록 완료: {item.get('platform')}")

        st.divider()
        st.subheader("원본 영상 파일 업로드")
        platform = st.selectbox("플랫폼", ["douyin", "taobao", "1688", "local"])
        file = st.file_uploader("원본 영상", type=["mp4", "mov", "webm"])
        video_memo = st.text_input("영상 메모")
        if st.button("영상 저장", use_container_width=True):
            if not file:
                st.warning("영상을 업로드하세요.")
            else:
                path = engine.save_uploaded_video(project, file, platform=platform, memo=video_memo)
                st.success(f"저장 완료: {path}")

        st.subheader("등록된 영상")
        for item in engine.list_project_videos(project):
            st.write(f"• {item.get('platform')} / {item.get('filename')} / {item.get('memo','')}")

    with tab3:
        sample_count = st.slider("빠른 분석 프레임 수", 4, 12, 6, 2)
        if st.button("영상 후보 랭킹", use_container_width=True):
            videos = engine.list_project_videos(project)
            ranked = SourceVideoRanker().rank(videos, sample_count=sample_count)

            if not ranked:
                st.info("등록된 영상이 없습니다.")
            for item in ranked:
                with st.container(border=True):
                    st.write(f"**{item.get('grade')} {item.get('score')}점 / {item.get('recommend')}**")
                    st.write(item.get("filename"))
                    st.caption(item.get("reason"))
                    st.write("경로:", item.get("path"))

            copybox("랭킹 JSON", json.dumps(ranked, ensure_ascii=False, indent=2), 420)

    with tab4:
        st.caption("상위 후보를 Real Vision Runner로 연속 분석합니다. YOLO/PaddleOCR 설치 여부에 따라 시간이 걸릴 수 있습니다.")
        limit = st.slider("분석할 후보 수", 1, 5, 3)
        if st.button("Batch Analyze 실행", use_container_width=True):
            videos = engine.list_project_videos(project)
            ranked = SourceVideoRanker().rank(videos, sample_count=4)
            results = BatchAnalyzer().analyze(project, ranked, limit=limit, sample_count=6)

            for r in results:
                with st.container(border=True):
                    source = r.get("source", {})
                    st.write(f"**{source.get('filename')}**")
                    if r.get("ok"):
                        st.success(r.get("summary"))
                    else:
                        st.warning(r.get("error", "분석 실패"))
            copybox("Batch Analyze JSON", json.dumps(results, ensure_ascii=False, indent=2), 500)
