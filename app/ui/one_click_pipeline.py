import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote_plus

import streamlit as st

from app.utils.project_keys import (
    safe_project_id,
    selected_session_key,
    selected_notice_key,
)

from modules.project.project_selector import ProjectSelector
from modules.workflow.workflow_engine import WorkflowEngine
from modules.workflow.job_queue import JobQueue
from modules.workflow.pipeline_state import PipelineState

from app.ui.pipeline_result import show_pipeline_result
from app.ui.content_pack.content_pack_view import show_content_pack_view as show_content_pack_view_new
from app.ui.candidate_card import show_candidate_card
from app.ui.download_connect import open_with_login_browser

from modules.video.video_path_resolver import VideoPathResolver
from modules.video.download_utils import latest_downloaded_video
from modules.project.repository import ProjectRepository

from app.ui.product_analyzer import analyze_product
from app.ui.hook_generator import generate_hooks
from app.ui.content_variant_generator import generate_content_variants
from app.ui.content_ranker import rank_content_variants

UI_VERSION = "0630-final-stable-selected-sources"
SELECTED_DIR = Path("exports/selected_sources")
RESULT_DIR = Path("exports/one_click_results")
CONTENT_PACK_DIR = Path("exports/content_packs")



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

def content_pack_path(project):
    return CONTENT_PACK_DIR / f"{safe_project_id(project)}_content_pack.json"

def capcut_export_path(project):
    return CONTENT_PACK_DIR / f"{safe_project_id(project)}_capcut_export.json"


def capcut_draft_path(project):
    return CONTENT_PACK_DIR / f"{safe_project_id(project)}_capcut_draft.json"

def content_pack_txt_path(project):
    return CONTENT_PACK_DIR / f"{safe_project_id(project)}_content_pack.txt"


def normalize_text(value, fallback=""):
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback

def pipeline_result_session_key(project):
    return f"one_click_pipeline_result_{safe_project_id(project)}"


def make_search_url(platform, query):
    encoded = quote_plus(query or "")

    if platform == "taobao":
        return f"https://s.taobao.com/search?q={encoded}"

    if platform == "douyin":
        return f"https://www.douyin.com/search/{encoded}"

    if platform == "1688":
        return f"https://s.1688.com/selloffer/offer_search.htm?keywords={encoded}"

    return ""


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



def safe_file_name(text, fallback="video"):
    text = str(text or fallback).strip()
    text = re.sub(r"[^0-9A-Za-z가-힣._-]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text[:80] or fallback


def project_source_video_dir(project):
    project_id = safe_project_id(project)
    project_name = safe_file_name(
        getattr(project, "product_name", "") or getattr(project, "title", ""),
        "project",
    )
    folder = Path("assets") / "source_videos" / f"project_{project_id}_{project_name}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def download_folders():
    folders = []
    home_downloads = Path.home() / "Downloads"
    folders.append(home_downloads)

    # Windows 기본 다운로드 폴더 보조 탐색
    for candidate in [
        Path(r"C:\Users\user\Downloads"),
        Path(r"C:\Users\user\다운로드"),
        Path.home() / "다운로드",
    ]:
        if candidate not in folders:
            folders.append(candidate)

    return [folder for folder in folders if folder.exists()]


def latest_downloaded_video(max_age_minutes=240):
    allowed = {".mp4", ".mov", ".webm"}
    candidates = []

    for folder in download_folders():
        try:
            for path in folder.iterdir():
                if not path.is_file():
                    continue
                if path.suffix.lower() not in allowed:
                    continue
                if path.name.lower().endswith(".crdownload") or path.name.lower().endswith(".part"):
                    continue
                candidates.append(path)
        except Exception:
            pass

    if not candidates:
        return None

    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    latest = candidates[0]

    try:
        age_seconds = __import__("time").time() - latest.stat().st_mtime
        if age_seconds > max_age_minutes * 60:
            # 오래된 파일이라도 후보로 반환하되 UI에서 경고할 수 있게 둡니다.
            return latest
    except Exception:
        pass

    return latest

 
def show_top10(project, title, platform, items):
    if not items:
        return

    st.markdown(f"## {title}")

    for item in items:
        if isinstance(item, dict):
            show_candidate_card(project, platform, item)

def show_live_sources(project, live_sources):
    if not live_sources:
        return

    if live_sources.get("live_collection"):
        live_sources = live_sources.get("live_collection", {})

    results = live_sources.get("results", [])
    if not results:
        st.info("실제 웹 수집 결과가 없습니다.")
        return

    st.divider()
    st.markdown("## 실제 Playwright 수집 결과")

    st.caption(
        f"상태: ok={live_sources.get('ok')} / "
        f"ready={live_sources.get('status', {}).get('ready')}"
    )

    for i, item in enumerate(results, start=1):
        if not isinstance(item, dict):
            continue

        title = item.get("title") or item.get("text") or "제목 없음"
        url = item.get("url") or item.get("link") or ""
        thumbnail = item.get("thumbnail") or item.get("thumbnail_url") or item.get("image") or ""
        views = item.get("views") or item.get("view_count") or "-"
        likes = item.get("likes") or item.get("like_count") or "-"
        duration = item.get("duration") or item.get("video_length") or item.get("length") or "-"

        with st.container(border=True):
            cols = st.columns([1, 3])

            with cols[0]:
                if thumbnail:
                    st.image(thumbnail, use_container_width=True)
                else:
                    st.caption("썸네일 없음")

            with cols[1]:
                st.markdown(f"### {i}. {title}")
                st.caption(f"조회수: {views} / 좋아요: {likes} / 길이: {duration}")

                if url:
                    st.link_button("영상 열기", url, use_container_width=True)

                source_item = {
                    "rank": i,
                    "query": title,
                    "purpose": "실제 Playwright 수집 후보",
                    "score": item.get("score", 80),
                    "thumbnail": thumbnail,
                }
                if st.button("이 후보 채택", key=f"live_select_{safe_project_id(project)}_{i}", use_container_width=True):
                    added = select_source(project, item.get("platform", "live"), source_item, url)
                    if added:
                        st.success("후보를 채택하고 저장했습니다.")
                    else:
                        st.info("이미 채택한 후보입니다.")

def show_search_links(keywords):
    taobao_keyword = keywords.get("taobao_keyword", "")
    main_keyword = keywords.get("main_keyword", "")

    st.subheader("검색 키워드")
    st.write("타오바오:", taobao_keyword)
    st.write("1688:", taobao_keyword or main_keyword)

    c1, c2 = st.columns(2)

    with c1:
        if st.button("타오바오 검색 열기", use_container_width=True):
            url = make_search_url("taobao", taobao_keyword)

            open_with_login_browser(url)

            st.success("Playwright 로그인 브라우저를 열었습니다.")

    with c2:
        if st.button("1688 검색 열기", use_container_width=True):
            url = make_search_url("1688", taobao_keyword or main_keyword)

            open_with_login_browser(url)

            st.success("Playwright 로그인 브라우저를 열었습니다.")

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

def show_one_click_pipeline():
    st.title("⚡ 원클릭 파이프라인")
    st.caption("상품 계획 → 소스 영상 → Vision 분석 → CapCut → 콘텐츠 생성까지 한 번에 실행합니다.")
    st.caption("UI 버전: sprint6-7-ai-content-pack-001")

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

        show_content_pack_view_new(project=project,
            result=result,
            content_pack=st.session_state.get(
                f"content_pack_{safe_project_id(project)}",
                {}
            ),
            paths=st.session_state.get(
                f"ai_content_pack_export_{project.id}",
                {}
            ),
        )

    else:
        st.info("원클릭 결과가 아직 없습니다. 먼저 원클릭 실행을 완료해 주세요.")

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