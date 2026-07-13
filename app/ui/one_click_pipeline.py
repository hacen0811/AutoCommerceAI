import json
import re
from pathlib import Path
from urllib.parse import quote_plus

import streamlit as st

from app.utils.project_keys import safe_project_id
from app.utils.selected_sources import init_selected_sources

from modules.project.project_selector import ProjectSelector
from modules.project.repository import ProjectRepository
from modules.project.service import ProjectService
from modules.workflow.workflow_engine import WorkflowEngine
from modules.workflow.job_queue import JobQueue
from modules.workflow.pipeline_state import PipelineState

from app.ui.pipeline_result import show_pipeline_result
from app.ui.selected_sources_view import show_selected_sources
from app.ui.content_pack.content_pack_view import (
    show_content_pack_view as show_content_pack_view_new,
)
from app.ui.download_connect import open_with_login_browser

from modules.video.video_path_resolver import VideoPathResolver

try:
    from modules.product.product_engine import ProductEngine
except Exception:
    ProductEngine = None

try:
    from modules.search.search_keyword_engine import SearchKeywordEngine
except Exception:
    SearchKeywordEngine = None


UI_VERSION = "sprint50-coupang-restore-001"
RESULT_DIR = Path("exports/one_click_results")


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
    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )


def normalize_text(value, fallback=""):
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def make_search_url(platform, query):
    encoded = quote_plus(query or "")

    if platform == "taobao":
        return f"https://s.taobao.com/search?q={encoded}"

    if platform == "douyin":
        return f"https://www.douyin.com/search/{encoded}"

    if platform == "1688":
        return f"https://s.1688.com/selloffer/offer_search.htm?keywords={encoded}"

    return ""


def safe_file_name(text, fallback="video"):
    text = str(text or fallback).strip()
    text = re.sub(r"[^0-9A-Za-z가-힣._-]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text[:80] or fallback


def pipeline_result_path(project):
    return RESULT_DIR / f"{safe_project_id(project)}_latest_result.json"


def save_pipeline_result(project, result):
    if isinstance(result, dict) and result:
        write_json(pipeline_result_path(project), result)


def load_pipeline_result(project):
    data = read_json(pipeline_result_path(project), {})
    return data if isinstance(data, dict) else {}


def extract_product_payload(built, coupang_url, product_name):
    if not isinstance(built, dict):
        return {
            "coupang_url": coupang_url,
            "product_name": product_name,
            "title": product_name,
        }

    for key in ["payload", "product", "project", "data", "result"]:
        value = built.get(key)
        if isinstance(value, dict):
            payload = dict(value)
            payload.setdefault("coupang_url", coupang_url)
            payload.setdefault("product_name", product_name)
            payload.setdefault("title", product_name)
            return payload

    payload = dict(built)
    payload.setdefault("coupang_url", coupang_url)
    payload.setdefault("product_name", product_name)
    payload.setdefault("title", product_name)
    return payload


def build_keywords(product_payload, product_name):
    fallback = {
        "main_keyword": product_name,
        "taobao_keyword": product_name,
        "keyword": product_name,
        "keywords": [product_name],
    }

    if SearchKeywordEngine is None:
        return fallback

    engine = SearchKeywordEngine()

    for method_name in ["build", "generate", "run", "create", "extract"]:
        method = getattr(engine, method_name, None)
        if not callable(method):
            continue

        try:
            result = method(product_payload)
        except TypeError:
            try:
                result = method(product_name)
            except Exception:
                continue
        except Exception:
            continue

        if isinstance(result, dict):
            result.setdefault("main_keyword", product_name)
            result.setdefault("taobao_keyword", result.get("main_keyword", product_name))
            return result

    return fallback


def create_project_from_payload(product_payload, keywords):
    payload = dict(product_payload)
    payload["keywords"] = keywords

    service = ProjectService()

    for method_name in [
        "create_project",
        "create",
        "save_project",
        "create_from_product",
        "build_project",
    ]:
        method = getattr(service, method_name, None)
        if not callable(method):
            continue

        try:
            project = method(payload)
            if project:
                return project
        except TypeError:
            try:
                project = method(
                    product_name=payload.get("product_name") or payload.get("title"),
                    coupang_url=payload.get("coupang_url"),
                    keywords=keywords,
                    payload=payload,
                )
                if project:
                    return project
            except Exception:
                continue
        except Exception:
            continue

    raise RuntimeError("ProjectService에서 사용 가능한 프로젝트 생성 메서드를 찾지 못했습니다.")


def rebuild_project_from_coupang(coupang_url, product_name):
    if ProductEngine is None:
        raise RuntimeError("ProductEngine import 실패: modules.product.product_engine 확인 필요")

    built = ProductEngine().build_from_coupang(
        coupang_url,
        product_name=product_name,
        manual_product_name=product_name,
    )

    product_payload = extract_product_payload(built, coupang_url, product_name)
    keywords = build_keywords(product_payload, product_name)

    project = create_project_from_payload(product_payload, keywords)

    project_id = getattr(project, "id", None)
    if project_id:
        project = ProjectRepository().get(project_id) or project

    return project, product_payload, keywords


def show_search_links(keywords, key_prefix="main"):
    if not keywords:
        return

    main_keyword = (
        keywords.get("main_keyword")
        or keywords.get("keyword")
        or ""
    )

    taobao_keyword = (
        keywords.get("taobao_keyword")
        or main_keyword
    )

    source_1688_keyword = (
        keywords.get("source_1688_keyword")
        or keywords.get("1688_keyword")
        or taobao_keyword
    )

    douyin_keyword = (
        keywords.get("douyin_keyword")
        or main_keyword
        or taobao_keyword
    )

    st.subheader("자동 검색 키워드")
    st.write("타오바오:", taobao_keyword)
    st.write("1688:", source_1688_keyword)
    st.write("도우인:", douyin_keyword)

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button(
            "타오바오 열기",
            key=f"{key_prefix}_search_taobao",
            use_container_width=True,
        ):
            open_with_login_browser(make_search_url("taobao", taobao_keyword))
            st.success("타오바오 검색을 열었습니다.")

    with c2:
        if st.button(
            "1688 열기",
            key=f"{key_prefix}_search_1688",
            use_container_width=True,
        ):
            open_with_login_browser(make_search_url("1688", source_1688_keyword))
            st.success("1688 검색을 열었습니다.")

    with c3:
        if st.button(
            "도우인 열기",
            key=f"{key_prefix}_search_douyin",
            use_container_width=True,
        ):
            open_with_login_browser(make_search_url("douyin", douyin_keyword))
            st.success("도우인 검색을 열었습니다.")

def run_project_pipeline(project, sample_count):
    print(
        "[Sprint61] run_project_pipeline entered",
        flush=True,
    )
    result = WorkflowEngine().run_project(project, sample_count=sample_count)
    save_pipeline_result(project, result)
    st.session_state[f"one_click_result_{safe_project_id(project)}"] = result
    return result


def render_project_pipeline(project, sample_count):
    init_selected_sources(project)

    project_safe_id = safe_project_id(project)
    result_key = f"one_click_result_{project_safe_id}"

    path_debug = VideoPathResolver().debug(project)
    project_name = getattr(project, "product_name", "") or getattr(project, "title", "")

    st.success(f"선택된 프로젝트: {project_name}")

    if not path_debug.get("exists"):
        st.warning("이 프로젝트에는 아직 원본 영상이 없습니다.")
    else:
        st.caption(f"영상: {path_debug.get('video_path')} / {path_debug.get('size_mb')}MB")

    c1, c2 = st.columns(2)

    if c1.button("현재 프로젝트 원클릭 실행", use_container_width=True):
        print(
            "[Sprint61] One Click button pressed",
            flush=True,
        )

        
        with st.spinner("One Click Pipeline 실행 중입니다..."):
            result = run_project_pipeline(project, sample_count)
        st.success("원클릭 실행 결과를 저장했습니다.")

    if c2.button("큐에 추가", use_container_width=True):
        job = JobQueue().add(getattr(project, "id", ""), project_name)
        st.success(f"큐 추가 완료: {job.get('job_id')}")

    result = st.session_state.get(result_key)

    if not result:
        result = load_pipeline_result(project)
        if result:
            st.session_state[result_key] = result
            st.caption(f"최근 원클릭 결과를 복원했습니다: {pipeline_result_path(project)}")

    if result:
        st.success("최근 원클릭 실행 결과가 있습니다.")

        show_result_detail = st.checkbox(
            "최근 실행 결과 상세 화면 열기",
            value=False,
            key=f"show_result_detail_{project_safe_id}",
        )

        if show_result_detail:
            show_pipeline_result(
                project,
                result,
                path_debug,
            )

        # ✅ 채택 영상 후보 화면
            show_selected_sources(
                project
            )

            show_content_pack_view_new(
                project=project,
                result=result,
                content_pack=st.session_state.get(
                    f"content_pack_{project_safe_id}",
                    {},
                ),
                paths=st.session_state.get(
                    f"ai_content_pack_export_{getattr(project, 'id', '')}",
                    {},
                ),
            )

    else:
        st.info(
            "원클릭 결과가 아직 없습니다. "
            "먼저 원클릭 실행을 완료해 주세요."
        )


def show_one_click_pipeline():
    st.title("⚡ 원클릭 파이프라인")
    st.caption("쿠팡 링크 → 상품 분석 → 검색 키워드 → 프로젝트 생성 → 후보 수집 → 콘텐츠 팩까지 연결합니다.")
    st.caption(f"UI 버전: {UI_VERSION}")
    
    sample_count = st.slider("Vision 분석 프레임 수", 4, 12, 6, 2)

    st.divider()
    st.subheader("쿠팡 링크로 새 프로젝트 생성")

    coupang_url = st.text_area(
        "쿠팡 링크",
        height=80,
        placeholder="https://www.coupang.com/vp/products/...",
    )

    product_name = st.text_area(
        "상품명",
        height=100,
        placeholder="쿠팡 상품명을 붙여넣어 주세요.",
    )

    auto_run = st.checkbox("프로젝트 생성 후 바로 원클릭 실행", value=True)

    if st.button("쿠팡 링크로 프로젝트 생성", type="primary", use_container_width=True):
        if not coupang_url.strip():
            st.error("쿠팡 링크를 입력해 주세요.")
            return

        if not product_name.strip():
            st.error("상품명을 입력해 주세요.")
            return

        with st.spinner("ProductEngine → SearchKeywordEngine → ProjectService 실행 중입니다..."):
            try:
                project, product_payload, keywords = rebuild_project_from_coupang(
                    coupang_url.strip(),
                    product_name.strip(),
                )
            except Exception as e:
                st.error(f"프로젝트 생성 실패: {e}")
                return

        st.session_state["sprint50_created_project_id"] = getattr(project, "id", None)
        st.session_state["sprint50_product_payload"] = product_payload
        st.session_state["sprint50_keywords"] = keywords

        st.success("쿠팡 링크 기반 프로젝트를 생성했습니다.")
        show_search_links(keywords, key_prefix="created")

        if auto_run:
            with st.spinner("생성된 프로젝트로 원클릭 후보 수집을 실행 중입니다..."):
                try:
                    run_project_pipeline(project, sample_count)
                    st.success("원클릭 후보 수집까지 완료했습니다.")
                except Exception as e:
                    st.error(f"원클릭 실행 실패: {e}")

        if st.session_state.get("sprint50_keywords"):
            with st.expander("최근 생성 키워드 보기", expanded=False):
                show_search_links(
                    st.session_state.get("sprint50_keywords", {}),
                    key_prefix="recent",
                )

    st.divider()
    st.subheader("기존 프로젝트 선택 실행")

    selector = ProjectSelector()
    projects = selector.all_projects()

    if not projects:
        st.info("아직 프로젝트가 없습니다. 위 쿠팡 링크 입력으로 새 프로젝트를 생성해 주세요.")
        return

    labels = selector.labels(projects)

    created_project_id = st.session_state.get("sprint50_created_project_id")
    default_index = 0

    if created_project_id:
        for idx, item in enumerate(labels.values()):
            if str(getattr(item, "id", "")) == str(created_project_id):
                default_index = idx
                break

    selected_label = st.selectbox(
        "프로젝트 선택",
        list(labels.keys()),
        index=default_index,
    )

    project = labels[selected_label]
    project = ProjectRepository().get(project.id) or project

    render_project_pipeline(project, sample_count)

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


from app.pages.pipeline_page import show_pipeline_page


if __name__ == "__main__":
    show_pipeline_page()