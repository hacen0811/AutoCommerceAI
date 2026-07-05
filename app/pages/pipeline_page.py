import json
from pathlib import Path

import streamlit as st

from modules.project.project_selector import ProjectSelector
from modules.workflow.workflow_engine import WorkflowEngine
from modules.workflow.job_queue import JobQueue
from modules.workflow.pipeline_state import PipelineState

from modules.video.video_path_resolver import VideoPathResolver
from modules.project.repository import ProjectRepository

from app.ui.pipeline_result import show_pipeline_result
from app.ui.ai_content_pack import show_content_pack_view

from app.utils.project_keys import safe_project_id
from main import init_selected_sources


def show_pipeline_page():
    st.title("⚡ 원클릭 파이프라인")
    st.caption("상품 계획 → 소스 영상 → Vision 분석 → CapCut → 콘텐츠 생성까지 한 번에 실행합니다.")
    st.caption("UI 버전: sprint29-pipeline-page-001")

    selector = ProjectSelector()
    projects = selector.all_projects()

    if not projects:
        st.info("프로젝트가 없습니다. 먼저 🛒 제품 AI에서 프로젝트를 생성해주세요.")
        return

    labels = selector.labels(projects)
    selected_label = st.selectbox("프로젝트 선택", list(labels.keys()))

    project = labels[selected_label]
    project = ProjectRepository().get(project.id) or project

    init_selected_sources(project)

    project_safe_id = safe_project_id(project)
    result_key = f"one_click_result_{project_safe_id}"
    result_dir = Path("exports/one_click_results")
    result_path = result_dir / f"{project_safe_id}_latest_result.json"

    def save_result(result):
        result_dir.mkdir(parents=True, exist_ok=True)
        result_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load_result():
        if not result_path.exists():
            return None

        try:
            data = json.loads(result_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else None
        except Exception:
            return None

    path_debug = VideoPathResolver().debug(project)
    project_name = project.product_name or project.title

    st.success(f"선택된 프로젝트: {project_name}")

    if not path_debug.get("exists"):
        st.warning("이 프로젝트에는 아직 원본 영상이 없습니다.")
    else:
        st.caption(
            f"영상: {path_debug.get('video_path')} / "
            f"{path_debug.get('size_mb')}MB"
        )

    sample_count = st.slider("Vision 분석 프레임 수", 4, 12, 6, 2)

    c1, c2 = st.columns(2)

    if c1.button("현재 프로젝트 원클릭 실행", use_container_width=True):
        with st.spinner("One Click Pipeline 실행 중입니다..."):
            result = WorkflowEngine().run_project(
                project,
                sample_count=sample_count,
            )

        st.session_state[result_key] = result
        save_result(result)
        st.success("원클릭 실행 결과를 저장했습니다.")

    if c2.button("큐에 추가", use_container_width=True):
        job = JobQueue().add(project.id, project_name)
        st.success(f"큐 추가 완료: {job.get('job_id')}")

    result = st.session_state.get(result_key)

    if not result:
        result = load_result()

        if result:
            st.session_state[result_key] = result
            st.caption(f"최근 원클릭 결과를 복원했습니다: {result_path}")

    if result:
        show_pipeline_result(project, result, path_debug)
        show_content_pack_view(project, result)
    else:
        st.info("원클릭 결과가 아직 없습니다. 먼저 원클릭 실행을 완료해 주세요.")

    st.divider()
    st.subheader("작업 큐")

    jobs = JobQueue().load()

    if not jobs:
        st.caption("큐가 비어 있습니다.")

    for job in jobs:
        st.write(
            f"• {job.get('job_id')} / "
            f"{job.get('project_name')} / "
            f"{job.get('status')}"
        )

    st.subheader("최근 Pipeline 상태")

    for f in PipelineState().list_recent(10):
        st.write(f"• {f.name}")