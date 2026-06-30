import json
import re
from pathlib import Path
from urllib.parse import quote_plus

import streamlit as st

from modules.project.project_selector import ProjectSelector
from modules.workflow.workflow_engine import WorkflowEngine
from modules.workflow.job_queue import JobQueue
from modules.workflow.pipeline_state import PipelineState
from app.ui.render import copybox
from modules.video.video_path_resolver import VideoPathResolver
from modules.project.repository import ProjectRepository


UI_VERSION = "0630-final-stable-selected-sources"
SELECTED_DIR = Path("exports/selected_sources")
RESULT_DIR = Path("exports/one_click_results")


def read_file_text(path):
    try:
        p = Path(path)
        if p.exists():
            return p.read_text(encoding="utf-8")
    except Exception:
        return ""
    return ""


def read_json(path, default=None):
    try:
        p = Path(path)
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def safe_project_id(project):
    """Return a filesystem/session safe project id without changing the project itself."""
    raw_id = str(getattr(project, "id", "") or "unknown_project")
    return re.sub(r"[^0-9A-Za-z가-힣._-]+", "_", raw_id).strip("_") or "unknown_project"


def selected_sources_path(project):
    return SELECTED_DIR / f"{safe_project_id(project)}_selected_sources.json"


def load_selected_sources(project):
    path = selected_sources_path(project)
    if not path.exists():
        return []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
    except Exception:
        return []

    return []


def save_selected_sources(project, sources):
    clean_sources = []
    for source in sources or []:
        if isinstance(source, dict):
            clean_sources.append(source)
    write_json(selected_sources_path(project), clean_sources)


def latest_result_path(project):
    return RESULT_DIR / f"{safe_project_id(project)}_latest_result.json"


def load_latest_result(project):
    data = read_json(latest_result_path(project), {})
    return data if isinstance(data, dict) else {}


def save_latest_result(project, result):
    if isinstance(result, dict) and result:
        write_json(latest_result_path(project), result)


def pipeline_result_session_key(project):
    return f"one_click_pipeline_result_{safe_project_id(project)}"


def show_download_button(label, path, mime="text/plain"):
    if not path:
        return

    file_text = read_file_text(path)

    if file_text:
        st.download_button(
            label=label,
            data=file_text,
            file_name=Path(path).name,
            mime=mime,
            use_container_width=True,
        )
    else:
        st.caption(f"{label} 파일을 찾을 수 없습니다: {path}")


def make_search_url(platform, query):
    encoded = quote_plus(query or "")

    if platform == "taobao":
        return f"https://s.taobao.com/search?q={encoded}"

    if platform == "douyin":
        return f"https://www.douyin.com/search/{encoded}"

    if platform == "1688":
        return f"https://s.1688.com/selloffer/offer_search.htm?keywords={encoded}"

    return ""


def selected_session_key(project):
    return f"selected_sources_{safe_project_id(project)}"


def selected_notice_key(project):
    return f"selected_sources_notice_{safe_project_id(project)}"


def init_selected_sources(project, force_reload=False):
    key = selected_session_key(project)
    if force_reload or key not in st.session_state:
        st.session_state[key] = load_selected_sources(project)
    return key


def source_identity(platform, item):
    """A stable identity used to prevent duplicate selected candidates."""
    return (
        str(platform or "").strip().lower(),
        str(item.get("rank", "")).strip(),
        str(item.get("query", "")).strip(),
    )


def normalize_selected_source(project, platform, item, url):
    return {
        "project_id": getattr(project, "id", ""),
        "platform": str(platform or "").strip().lower(),
        "rank": item.get("rank"),
        "query": item.get("query", ""),
        "purpose": item.get("purpose", ""),
        "score": item.get("score", ""),
        "url": url or "",
    }


def select_source(project, platform, item, url):
    key = init_selected_sources(project)
    selected = normalize_selected_source(project, platform, item, url)
    selected_id = source_identity(selected.get("platform"), selected)

    current_sources = st.session_state.get(key, [])
    exists = any(
        source_identity(source.get("platform"), source) == selected_id
        for source in current_sources
        if isinstance(source, dict)
    )

    if exists:
        return False

    st.session_state[key] = [*current_sources, selected]
    save_selected_sources(project, st.session_state[key])
    return True


def clear_selected_sources(project):
    key = init_selected_sources(project)
    st.session_state[key] = []
    save_selected_sources(project, [])

def show_selected_sources(project):
    key = init_selected_sources(project)
    selected = st.session_state.get(key, [])

    st.subheader("🎬 채택한 영상 후보")

    if not selected:
        st.info("아직 채택한 영상 후보가 없습니다.")
        return

    for i, item in enumerate(selected):
        with st.container(border=True):
            st.markdown(f"**{i + 1}. [{item.get('platform')}] {item.get('query', '')}**")

            st.caption(
                f"목적: {item.get('purpose', '-')} / "
                f"점수: {item.get('score', '-')}점"
            )

            url = item.get("url")
            if url:
                st.link_button("영상 링크 열기", url)

            c1, c2, c3 = st.columns(3)

            with c1:
                if st.button("⬆️ 위로", key=f"selected_up_{project.id}_{i}", disabled=i == 0):
                    selected[i - 1], selected[i] = selected[i], selected[i - 1]
                    st.session_state[key] = selected
                    save_selected_sources(project, selected)
                    st.success("순서를 위로 이동했습니다.")
                    st.rerun()

            with c2:
                if st.button("⬇️ 아래로", key=f"selected_down_{project.id}_{i}", disabled=i == len(selected) - 1):
                    selected[i + 1], selected[i] = selected[i], selected[i + 1]
                    st.session_state[key] = selected
                    save_selected_sources(project, selected)
                    st.success("순서를 아래로 이동했습니다.")
                    st.rerun()

            with c3:
                if st.button("🗑 삭제", key=f"selected_delete_{project.id}_{i}"):
                    selected.pop(i)
                    st.session_state[key] = selected
                    st.success("후보를 삭제했습니다.")
                    st.rerun()

    st.caption("현재 순서가 CapCut 내보내기와 TXT 생성 순서의 기준이 됩니다.")

def show_candidate_card(project, platform, item):
    query = item.get("query", "")
    rank = item.get("rank", "")
    purpose = item.get("purpose", "")
    score = item.get("score", "")
    url = make_search_url(platform, query)
    key_prefix = f"select_{safe_project_id(project)}_{platform}_{rank}_{query}"

    with st.container(border=True):
        st.markdown(f"### {rank}위 · {platform.upper()}")
        st.markdown(f"**검색어:** {query}")
        st.markdown(f"**목적:** {purpose}")
        st.markdown(f"**추천 점수:** ⭐ {score}점")

        b1, b2 = st.columns(2)

        with b1:
            if url:
                st.link_button("검색 열기", url, use_container_width=True)

        with b2:
            if st.button(
                 "이 후보 채택",
                 key=key_prefix,
                 use_container_width=True,
):
                 added = select_source(project, platform, item, url)

                 if added:
                     st.success("후보를 채택하고 저장했습니다.")
                 else:
                     st.info("이미 채택한 후보입니다.")

def show_top10(project, title, platform, items):
    if not items:
        return

    st.markdown(f"## {title}")

    for item in items:
        if isinstance(item, dict):
            show_candidate_card(project, platform, item)


def show_search_links(keywords):
    taobao_keyword = keywords.get("taobao_keyword", "")
    douyin_keyword = keywords.get("douyin_keyword", "")
    main_keyword = keywords.get("main_keyword", "")

    st.subheader("검색 키워드")
    st.write("타오바오:", taobao_keyword)
    st.write("도우인:", douyin_keyword)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.link_button(
            "타오바오 검색 열기",
            make_search_url("taobao", taobao_keyword),
            use_container_width=True,
        )

    with c2:
        st.link_button(
            "도우인 검색 열기",
            make_search_url("douyin", douyin_keyword),
            use_container_width=True,
        )

    with c3:
        st.link_button(
            "1688 검색 열기",
            make_search_url("1688", taobao_keyword or main_keyword),
            use_container_width=True,
        )


def show_content_factory(content_factory):
    if not content_factory:
        st.info("콘텐츠 생성 결과가 없습니다.")
        return

    st.divider()
    st.subheader("콘텐츠 생성 결과")

    shorts = content_factory.get("shorts", {})
    upload_bundle = content_factory.get("upload_bundle", {})
    blog = content_factory.get("blog", {})
    inpock = content_factory.get("inpock", {})

    if upload_bundle:
        st.markdown("### 유튜브 / 인스타 업로드 문구")

        if upload_bundle.get("youtube_title"):
            st.write("유튜브 제목:", upload_bundle.get("youtube_title"))

        if upload_bundle.get("youtube_desc"):
            st.text_area("유튜브 설명", upload_bundle.get("youtube_desc"), height=140)

        if upload_bundle.get("instagram_body"):
            st.text_area("인스타 본문", upload_bundle.get("instagram_body"), height=160)

        if upload_bundle.get("fixed_comment"):
            st.write("고정 댓글:", upload_bundle.get("fixed_comment"))

        if upload_bundle.get("partner_notice"):
            st.caption(upload_bundle.get("partner_notice"))

    platform_copy = shorts.get("platform_copy", {})
    if platform_copy:
        st.markdown("### 플랫폼별 문구")
        for key, value in platform_copy.items():
            st.text_area(key, value, height=90)

    if shorts.get("capcut_timeline"):
        st.markdown("### CapCut 타임라인")
        for item in shorts.get("capcut_timeline", []):
            st.write(
                f"{item.get('time')} / {item.get('scene')} / "
                f"{item.get('caption')} / {item.get('capcut')}"
            )

    if shorts.get("hooks"):
        st.markdown("### 후킹 문구")
        for group, hooks in shorts.get("hooks", {}).items():
            st.write(f"**{group}**")
            for hook in hooks:
                st.write(f"- {hook}")

    if blog:
        st.markdown("### 블로그")
        if blog.get("title"):
            st.write("제목:", blog.get("title"))
        if blog.get("body"):
            st.text_area("본문", blog.get("body"), height=180)

    if inpock:
        st.markdown("### 인포크")
        for key, value in inpock.items():
            st.write(f"{key}: {value}")


def show_pipeline_result(project, result, path_debug):
    st.success(result.get("summary"))
    state = result.get("state", {})
    outputs = result.get("outputs", {})
    st.progress(int(state.get("progress", 0)))

    st.subheader("단계별 상태")
    for step in state.get("steps", []):
        status = step.get("status")
        icon = "✅" if status == "done" else "⚠️" if status == "failed" else "□"
        st.write(f"{icon} {step.get('label')} / {status}")

    if state.get("errors"):
        st.subheader("오류")
        for err in state.get("errors", []):
            st.warning(f"{err.get('step')}: {err.get('error')}")
            st.caption(f"영상 경로 확인: {path_debug}")

    tab1, tab2, tab3 = st.tabs(["요약", "결과 JSON", "상태 JSON"])

    with tab1:
        product_plan = outputs.get("product_plan", {})
        keywords = product_plan.get("keywords", {})

        show_selected_sources(project)

        if keywords:
            show_search_links(keywords)
            show_top10(project, "타오바오 TOP10", "taobao", keywords.get("taobao_top10", []))
            show_top10(project, "도우인 TOP10", "douyin", keywords.get("douyin_top10", []))
        else:
            st.info("상품 기획 키워드 결과가 없습니다.")

        real_vision = outputs.get("real_vision") or state.get("results", {}).get("real_vision", {})
        if real_vision:
            st.divider()
            st.subheader("Vision")
            st.write(real_vision.get("summary"))

        capcut_export = outputs.get("capcut_export") or state.get("results", {}).get("capcut_export", {})
        if capcut_export:
            st.divider()
            st.subheader("CapCut 내보내기")
            st.write(capcut_export)

            json_path = capcut_export.get("json")
            txt_path = capcut_export.get("txt")

            d1, d2 = st.columns(2)

            with d1:
                show_download_button("CapCut JSON 다운로드", json_path, "application/json")

            with d2:
                show_download_button("CapCut TXT 다운로드", txt_path, "text/plain")

        content_factory = (
            outputs.get("content_factory")
            or result.get("content_factory")
            or state.get("results", {}).get("content_factory", {})
            or {}
        )
        show_content_factory(content_factory)

    with tab2:
        copybox(
            "One Click Result",
            json.dumps(result, ensure_ascii=False, indent=2),
            520,
        )

    with tab3:
        copybox(
            "Pipeline State",
            json.dumps(state, ensure_ascii=False, indent=2),
            420,
        )


def show_one_click_pipeline():
    st.title("⚡ 원클릭 파이프라인")
    st.caption("상품 계획 → 소스 영상 → Vision 분석 → CapCut → 콘텐츠 생성까지 한 번에 실행합니다.")
    st.caption("UI 버전: sprint5-result-persist-001")

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
        st.caption(f"영상: {path_debug.get('video_path')} / {path_debug.get('size_mb')}MB")

    sample_count = st.slider("Vision 분석 프레임 수", 4, 12, 6, 2)

    c1, c2 = st.columns(2)

    if c1.button("현재 프로젝트 원클릭 실행", use_container_width=True):
        with st.spinner("One Click Pipeline 실행 중입니다..."):
            result = WorkflowEngine().run_project(project, sample_count=sample_count)

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
    else:
        show_selected_sources(project)

    st.divider()
    st.subheader("작업 큐")
    jobs = JobQueue().load()

    if not jobs:
        st.caption("큐가 비어 있습니다.")

    for job in jobs:
        st.write(f"• {job.get('job_id')} / {job.get('project_name')} / {job.get('status')}")

    st.subheader("최근 Pipeline 상태")
    for f in PipelineState().list_recent(10):
        st.write(f"• {f.name}")
    