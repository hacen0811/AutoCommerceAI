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


def build_product_profile(product_name, source_query=""):
    text = f"{product_name} {source_query}".lower()

    if any(k in text for k in ["건조", "신발", "제습", "말리"]):
        return {
            "problem": "젖거나 냄새나는 신발 때문에 은근 신경 쓰이는 순간",
            "solution": "신발 안쪽까지 간편하게 관리해주는 아이템",
            "benefit": "비 오는 날이나 운동 후에도 훨씬 깔끔하게 관리할 수 있어요",
            "features": ["냄새 관리", "습기 제거", "간편 사용"],
            "scene": "젖은 신발 / 운동화 / 현관",
            "keyword": "신발",
        }

    if any(k in text for k in ["트레이", "얼음", "아이스", "보틀"]):
        return {
            "problem": "얼음 얼리고 빼는 과정이 매번 귀찮은 순간",
            "solution": "얼음을 더 편하게 만들고 꺼낼 수 있는 아이템",
            "benefit": "홈카페 준비가 훨씬 간단해져요",
            "features": ["간편 분리", "공간 절약", "홈카페 활용"],
            "scene": "얼음 트레이 / 컵 / 냉동실",
            "keyword": "얼음",
        }

    if any(k in text for k in ["수전", "세면대", "연장", "탭"]):
        return {
            "problem": "세면대 물줄기가 짧아서 손 씻기나 청소가 불편한 순간",
            "solution": "물줄기 방향을 더 편하게 바꿔주는 아이템",
            "benefit": "세면대 사용과 청소가 훨씬 편해져요",
            "features": ["각도 조절", "물튀김 감소", "간편 설치"],
            "scene": "세면대 / 손 씻기 / 물줄기",
            "keyword": "수전",
        }

    if any(k in text for k in ["장갑", "홀더", "비닐"]):
        return {
            "problem": "비닐장갑 꺼내고 끼는 과정이 매번 번거로운 순간",
            "solution": "장갑을 더 깔끔하고 빠르게 꺼낼 수 있게 도와주는 아이템",
            "benefit": "요리 전 준비 시간이 줄고 주방이 더 정리돼요",
            "features": ["빠른 사용", "깔끔 정리", "주방 동선 개선"],
            "scene": "주방 / 비닐장갑 / 싱크대",
            "keyword": "장갑",
        }

    return {
        "problem": "매일 쓰는 물건인데 은근 불편함이 반복되는 순간",
        "solution": "생활 속 작은 불편을 줄여주는 아이템",
        "benefit": "반복되는 귀찮음이 줄어 생활이 조금 더 편해져요",
        "features": ["간편 사용", "정리 효과", "생활 편의"],
        "scene": "생활 공간 / 제품 사용 전후",
        "keyword": "제품",
    }


def build_hooks(product_name, profile):
    hook_groups = generate_hooks(product_name, profile)

    if isinstance(hook_groups, dict):
        flat_hooks = []
        for group_name, hooks in hook_groups.items():
            for hook in hooks:
                hook = str(hook or "").strip()
                if hook and hook not in flat_hooks:
                    flat_hooks.append(hook)

        return flat_hooks[:5]

    if isinstance(hook_groups, list):
        return hook_groups[:5]

    keyword = profile.get("keyword", "제품")
    return [
        f"아직도 {keyword} 때문에 불편하세요?",
        f"{product_name}, 왜 이제 알았지?",
        "이거 하나로 매일 귀찮던 일이 줄어듭니다.",
        "써보면 차이가 바로 느껴지는 생활템이에요.",
        "Before / After로 보면 더 확실합니다.",
    ]

def build_script(product_name, profile):
    hooks = build_hooks(product_name, profile)

    problems = profile.get("problem_candidates") or []
    benefits = profile.get("benefit_candidates") or []
    features = profile.get("features") or []

    hook = hooks[0] if hooks else f"아직도 {profile.get('keyword', '제품')} 때문에 불편하세요?"
    problem_1 = problems[0] if problems else profile.get("problem", "")
    problem_2 = problems[1] if len(problems) > 1 else "그냥 참고 쓰면 되겠지 했는데, 매번 반복되니까 은근 스트레스였어요."
    benefit_1 = benefits[0] if benefits else profile.get("benefit", "")
    benefit_2 = benefits[1] if len(benefits) > 1 else profile.get("benefit", "")

    lines = [
        f"[Hook] {hook}",
        f"[Problem] {problem_1}",
        f"[Problem] {problem_2}",
        f"[Solution] 그래서 찾은 게 바로 {product_name}입니다.",
        f"[Solution] 핵심은 {profile.get('solution', '생활 속 불편을 줄여주는 아이템')}이라는 점이에요.",
        f"[Benefit] 특히 {', '.join(features)} 이 부분이 쇼츠에서 보여주기 좋습니다.",
        f"[Benefit] {benefit_1}",
        f"[Benefit] {benefit_2}",
        f"[CTA] 제품 정보가 궁금하시면 댓글에 '{profile.get('keyword', '제품')}' 남겨주세요 👇",
    ]
    return "\n".join(lines)

def build_capcut_timeline(product_name, hooks, profile):
    return [
        {
            "time": "0-2초",
            "scene": f"{profile['scene']} 불편한 장면 초근접",
            "caption": hooks[0],
            "capcut": "첫 자막 크게 / 빠른 줌인 / Pop 효과음 35% / BGM 12%",
        },
        {
            "time": "2-6초",
            "scene": "기존 방식 반복 장면",
            "caption": "이게 매번 은근 귀찮더라고요",
            "capcut": "0.5초 단위 빠른 컷 / 실패음 또는 딸깍 효과음 / 자막 하단 40%",
        },
        {
            "time": "6-10초",
            "scene": "제품 첫 등장",
            "caption": f"그래서 찾은 {product_name}",
            "capcut": "제품 중앙 배치 / 바운스 애니메이션 / 강조색 #FFD54F",
        },
        {
            "time": "10-20초",
            "scene": "핵심 기능 3가지",
            "caption": "간편함 / 정리 / 편리함",
            "capcut": "체크리스트 자막 / 체크 효과음 40% / 컷마다 1초 유지",
        },
        {
            "time": "20-32초",
            "scene": "사용 전후 비교",
            "caption": "차이가 바로 보이죠?",
            "capcut": "좌우 비교 화면 / Before After 텍스트 / 줌인 105%",
        },
        {
            "time": "32-42초",
            "scene": "실사용 장면 반복",
            "caption": profile["benefit"],
            "capcut": "속도 1.1배 / 밝기 살짝 보정 / BGM 18%",
        },
        {
            "time": "42-50초",
            "scene": "제품 클로즈업 + CTA",
            "caption": f"댓글에 '{profile['keyword']}' 남겨주세요 👇",
            "capcut": "CTA 하단 고정 / 자막 테두리 70 / BGM 22%",
        },
    ]

def content_pack_to_txt(pack):
    shorts = pack.get("shorts", {})
    upload = pack.get("upload_bundle", {})
    thumb = pack.get("thumbnail", {})
    inpock = pack.get("inpock", {})
    variants = pack.get("shorts_variants", [])

    active_content = (
        pack.get("selected_variant")
        or next((v for v in variants if v.get("recommended")), None)
        or (variants[0] if variants else {})
        or {}
    )

    title = active_content.get("title") or (shorts.get("titles", [""]) or [""])[0]
    hook = active_content.get("hook") or (shorts.get("hooks", [""]) or [""])[0]
    script = active_content.get("script") or shorts.get("script", "")
    cta = active_content.get("cta") or shorts.get("cta", "")
    capcut_items = active_content.get("capcut") or shorts.get("capcut_timeline", [])

    lines = []
    lines.append("# AI 콘텐츠 팩")
    lines.append("")
    lines.append(f"프로젝트: {pack.get('project_name', '')}")
    lines.append(f"대표 상품/검색어: {pack.get('primary_source', {}).get('query', '')}")
    lines.append("")
    lines.append("## 대표 콘텐츠")
    if active_content.get("type"):
        lines.append(f"유형: {active_content.get('type')} / 점수: {active_content.get('score', '-')}")
    lines.append("")
    lines.append("## 쇼츠 제목")
    lines.append(f"- {title}")
    lines.append("")
    lines.append("## 후킹")
    lines.append(f"- {hook}")
    lines.append("")
    lines.append("## 대본")
    lines.append(str(script))
    lines.append("")
    lines.append("## CTA")
    lines.append(str(cta))
    lines.append("")
    lines.append("## CapCut 타임라인")
    for item in capcut_items:
        if isinstance(item, dict):
            lines.append(f"- {item.get('time')} / {item.get('scene')} / {item.get('caption')} / {item.get('capcut')}")
        else:
            lines.append(f"- {item}")
    lines.append("")
    lines.append("## 썸네일")
    lines.append(f"메인 문구: {thumb.get('main_text', '')}")
    lines.append(f"보조 문구: {thumb.get('sub_text', '')}")
    lines.append(f"프롬프트: {thumb.get('image_prompt', '')}")
    lines.append("")
    lines.append("## 인포크 1000x1000")
    lines.append(f"메인 문구: {inpock.get('main_text', '')}")
    lines.append(f"보조 문구: {inpock.get('sub_text', '')}")
    lines.append(f"프롬프트: {inpock.get('image_prompt', '')}")
    lines.append("")
    lines.append("## 업로드")
    lines.append(f"유튜브 제목: {upload.get('youtube_title', '')}")
    lines.append(f"유튜브 설명:\n{upload.get('youtube_desc', '')}")
    lines.append(f"인스타 본문:\n{upload.get('instagram_body', '')}")
    lines.append("해시태그: " + " ".join(upload.get("hashtags", [])))
    return "\n".join(lines)


def save_content_pack(project, pack):
    json_path = content_pack_path(project)
    txt_path = content_pack_txt_path(project)
    write_json(json_path, pack)
    txt_path.parent.mkdir(parents=True, exist_ok=True)
    txt_path.write_text(content_pack_to_txt(pack), encoding="utf-8")
    return {"json": str(json_path), "txt": str(txt_path)}


def load_content_pack(project):
    data = read_json(content_pack_path(project), {})
    return data if isinstance(data, dict) else {}


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