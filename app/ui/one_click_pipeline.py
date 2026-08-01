import json
import os
import re
import sys
import threading
import traceback
from pathlib import Path
from urllib.parse import quote_plus


def _configure_utf8_runtime():
    """Windows CP949 환경에서 파이프라인 로그와 자식 프로세스를 UTF-8로 고정합니다."""
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if not callable(reconfigure):
            continue
        try:
            reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:
            pass


_configure_utf8_runtime()

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


UI_VERSION = "sprint157-cost-guard-ui"
RESULT_DIR = Path("exports/one_click_results")
REVIEW_IMAGE_ROOT = Path("assets/review_images")
PRODUCT_IMAGE_ROOT = Path("assets/products")
VIRAL_UPLOAD_ROOT = Path("assets/viral_uploads")
SUPPORTED_VIRAL_VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}
SUPPORTED_PRODUCT_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
SUPPORTED_REVIEW_IMAGE_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
}


print(
    "######## ONE_CLICK_PIPELINE SPRINT157 COST GUARD UI LOADED ########",
    __file__,
    flush=True,
)

# Sprint102-3: 한 Streamlit 프로세스에서 동일 프로젝트 중복 실행을 차단합니다.
_PIPELINE_RUN_GUARD = threading.RLock()
_ACTIVE_PIPELINE_PROJECTS = set()


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


def review_image_dir(project):
    return REVIEW_IMAGE_ROOT / f"project_{safe_project_id(project)}"


def list_saved_review_images(project):
    folder = review_image_dir(project)

    if not folder.exists():
        return []

    return [
        str(path)
        for path in sorted(folder.iterdir())
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_REVIEW_IMAGE_SUFFIXES
    ]


def save_uploaded_review_images(project, uploaded_files):
    """
    업로드된 리뷰 이미지를 프로젝트별 폴더에 저장합니다.

    같은 프로젝트에서 새 이미지를 업로드하면 기존 review_* 이미지들은
    제거한 뒤 이번 업로드 파일로 교체합니다.
    """
    files = list(uploaded_files or [])

    if not files:
        return list_saved_review_images(project)

    folder = review_image_dir(project)
    folder.mkdir(parents=True, exist_ok=True)

    for old_path in folder.iterdir():
        if (
            old_path.is_file()
            and old_path.suffix.lower() in SUPPORTED_REVIEW_IMAGE_SUFFIXES
        ):
            old_path.unlink()

    saved_paths = []

    for index, uploaded_file in enumerate(files, start=1):
        original_name = getattr(uploaded_file, "name", "") or ""
        suffix = Path(original_name).suffix.lower()

        if suffix not in SUPPORTED_REVIEW_IMAGE_SUFFIXES:
            suffix = ".png"

        destination = folder / f"review_{index:02d}{suffix}"
        destination.write_bytes(uploaded_file.getbuffer())
        saved_paths.append(str(destination))

    return saved_paths


def product_image_dir(project):
    return PRODUCT_IMAGE_ROOT / f"project_{safe_project_id(project)}"


def list_saved_product_images(project):
    """프로젝트별로 저장된 상품/상세 이미지를 순서대로 반환합니다."""
    folder = product_image_dir(project)
    if not folder.exists():
        return []

    return [
        str(path)
        for path in sorted(folder.iterdir())
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_PRODUCT_IMAGE_SUFFIXES
    ]


def find_saved_product_image(project):
    """기존 1장 호출부 호환용 대표 이미지 경로를 반환합니다."""
    paths = list_saved_product_images(project)
    return paths[0] if paths else ""


def save_uploaded_product_images(project, uploaded_files):
    """
    상품 대표 이미지와 상세페이지 캡처를 프로젝트 폴더에 저장합니다.

    새 파일이 선택되면 기존 상품 이미지들을 모두 교체합니다.
    첫 번째 이미지는 00_main, 나머지는 detail 이미지로 저장합니다.
    """
    files = list(uploaded_files or [])

    if not files:
        return list_saved_product_images(project)

    folder = product_image_dir(project)
    folder.mkdir(parents=True, exist_ok=True)

    for old_path in folder.iterdir():
        if (
            old_path.is_file()
            and old_path.suffix.lower() in SUPPORTED_PRODUCT_IMAGE_SUFFIXES
        ):
            old_path.unlink()

    saved_paths = []

    for index, uploaded_file in enumerate(files):
        original_name = getattr(uploaded_file, "name", "") or ""
        suffix = Path(original_name).suffix.lower()
        if suffix not in SUPPORTED_PRODUCT_IMAGE_SUFFIXES:
            suffix = ".jpg"

        filename = (
            f"00_main{suffix}"
            if index == 0
            else f"{index:02d}_detail{suffix}"
        )
        destination = folder / filename
        destination.write_bytes(uploaded_file.getbuffer())
        saved_paths.append(str(destination))

    return saved_paths


def save_uploaded_product_image(project, uploaded_file):
    """기존 1장 호출부 호환용 저장 함수입니다."""
    files = [] if uploaded_file is None else [uploaded_file]
    paths = save_uploaded_product_images(project, files)
    return paths[0] if paths else ""


def show_product_image_upload_area(project, key_prefix):
    project_safe_id = safe_project_id(project)
    saved_paths = list_saved_product_images(project)

    st.subheader("상품 이미지 · 상세페이지 캡처")
    st.caption(
        "상품 대표 이미지와 상세페이지 캡처를 여러 장 선택하세요. "
        "첫 번째 이미지는 대표 이미지, 나머지는 상세 이미지로 사용합니다."
    )

    uploaded_files = st.file_uploader(
        "상품 이미지 여러 장 선택",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key=f"{key_prefix}_product_images_{project_safe_id}",
    )

    if uploaded_files:
        st.success(
            f"새 상품 이미지 {len(uploaded_files)}장이 선택되었습니다."
        )
        preview_columns = st.columns(min(4, len(uploaded_files)))
        for index, uploaded_file in enumerate(uploaded_files[:4]):
            with preview_columns[index % len(preview_columns)]:
                st.image(
                    uploaded_file,
                    caption=("대표" if index == 0 else f"상세 {index}"),
                    width=180,
                )
    elif saved_paths:
        st.info(
            f"저장된 상품 이미지 {len(saved_paths)}장을 다시 사용합니다."
        )
        st.caption(str(product_image_dir(project)))
    else:
        st.warning(
            "상품 이미지가 없습니다. Vision·Image Tagger·Scene Planner를 건너뜁니다."
        )

    return uploaded_files


def viral_upload_dir(project):
    return VIRAL_UPLOAD_ROOT / f"project_{safe_project_id(project)}"


def list_saved_viral_videos(project):
    folder = viral_upload_dir(project)
    if not folder.exists():
        return []
    return [
        str(path)
        for path in sorted(folder.iterdir())
        if path.is_file() and path.suffix.lower() in SUPPORTED_VIRAL_VIDEO_SUFFIXES
    ]


def save_uploaded_viral_videos(project, uploaded_files):
    files = list(uploaded_files or [])[:10]
    if not files:
        return list_saved_viral_videos(project)

    folder = viral_upload_dir(project)
    folder.mkdir(parents=True, exist_ok=True)
    for old_path in folder.iterdir():
        if old_path.is_file() and old_path.suffix.lower() in SUPPORTED_VIRAL_VIDEO_SUFFIXES:
            old_path.unlink()

    saved_paths = []
    for index, uploaded_file in enumerate(files, start=1):
        original_name = getattr(uploaded_file, "name", "") or ""
        suffix = Path(original_name).suffix.lower()
        if suffix not in SUPPORTED_VIRAL_VIDEO_SUFFIXES:
            suffix = ".mp4"
        destination = folder / f"viral_{index:02d}{suffix}"
        destination.write_bytes(uploaded_file.getbuffer())
        saved_paths.append(str(destination))
    return saved_paths


def parse_viral_urls(value):
    urls = []
    for line in str(value or "").splitlines():
        clean = line.strip()
        if clean and clean.startswith(("http://", "https://")) and clean not in urls:
            urls.append(clean)
    return urls[:10]


def show_viral_input_area(project, key_prefix):
    project_safe_id = safe_project_id(project)
    saved_paths = list_saved_viral_videos(project)

    st.subheader("바이럴 쇼츠 참고 영상")
    st.caption(
        "직접 고른 바이럴 쇼츠 URL 또는 영상 파일을 최대 10개 입력하세요. "
        "영상 자체를 복제하지 않고 장면 길이·컷 속도·모션·자막 위치 패턴만 분석합니다."
    )
    viral_urls_text = st.text_area(
        "바이럴 쇼츠 URL (한 줄에 하나)",
        height=130,
        placeholder="https://www.youtube.com/shorts/...",
        key=f"{key_prefix}_viral_urls_{project_safe_id}",
    )
    uploaded_files = st.file_uploader(
        "바이럴 쇼츠 영상 파일",
        type=["mp4", "mov", "mkv", "webm", "m4v"],
        accept_multiple_files=True,
        key=f"{key_prefix}_viral_videos_{project_safe_id}",
    )
    url_count = len(parse_viral_urls(viral_urls_text))
    upload_count = len(uploaded_files or [])
    if url_count + upload_count > 10:
        st.warning("URL과 파일을 합쳐 앞의 10개만 분석합니다.")
    elif url_count or upload_count:
        st.success(f"바이럴 참고 영상 {url_count + upload_count}개가 준비됐습니다.")
    elif saved_paths:
        st.info(f"저장된 바이럴 영상 {len(saved_paths)}개를 다시 사용합니다.")
    else:
        st.caption("입력하지 않으면 바이럴 편집 분석 단계만 건너뜁니다.")
    return viral_urls_text, uploaded_files


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
            result.setdefault(
                "taobao_keyword",
                result.get("main_keyword", product_name),
            )
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
                    product_name=(
                        payload.get("product_name")
                        or payload.get("title")
                    ),
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

    raise RuntimeError(
        "ProjectService에서 사용 가능한 프로젝트 생성 메서드를 찾지 못했습니다."
    )


def rebuild_project_from_coupang(
    coupang_url,
    product_name,
):
    if ProductEngine is None:
        raise RuntimeError(
            "ProductEngine import 실패: "
            "modules.product.product_engine 확인 필요"
        )

    print(
        "[PROJECT CREATE] 1. ProductEngine START",
        flush=True,
    )

    try:
        built = ProductEngine().build_from_coupang(
            coupang_url,
            product_name=product_name,
            manual_product_name=product_name,
        )
    except Exception as exc:
        raise RuntimeError(
            "ProductEngine 단계 실패: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    print(
        "[PROJECT CREATE] 1. ProductEngine DONE",
        flush=True,
    )

    print(
        "[PROJECT CREATE] 2. Product Payload START",
        flush=True,
    )

    try:
        product_payload = extract_product_payload(
            built,
            coupang_url,
            product_name,
        )
    except Exception as exc:
        raise RuntimeError(
            "Product Payload 단계 실패: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    print(
        "[PROJECT CREATE] 2. Product Payload DONE",
        flush=True,
    )

    print(
        "[PROJECT CREATE] 3. Keyword Build START",
        flush=True,
    )

    try:
        keywords = build_keywords(
            product_payload,
            product_name,
        )
    except Exception as exc:
        raise RuntimeError(
            "Keyword Build 단계 실패: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    print(
        "[PROJECT CREATE] 3. Keyword Build DONE",
        flush=True,
    )

    print(
        "[PROJECT CREATE] 4. Project Save START",
        flush=True,
    )

    try:
        print(
            "[UTF8 PAYLOAD BEFORE SAVE]",
            json.dumps(
                {
                    "product_payload": product_payload,
                    "keywords": keywords,
                },
                ensure_ascii=False,
                default=str,
            ),
            flush=True,
        )
        project = create_project_from_payload(
            product_payload,
            keywords,
        )
    except Exception as exc:
        raise RuntimeError(
            "Project Save 단계 실패: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    print(
        "[PROJECT CREATE] 4. Project Save DONE",
        flush=True,
    )

    project_id = getattr(
        project,
        "id",
        None,
    )

    if project_id:
        project = (
            ProjectRepository().get(project_id)
            or project
        )

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
            open_with_login_browser(
                make_search_url("taobao", taobao_keyword)
            )
            st.success("타오바오 검색을 열었습니다.")

    with c2:
        if st.button(
            "1688 열기",
            key=f"{key_prefix}_search_1688",
            use_container_width=True,
        ):
            open_with_login_browser(
                make_search_url("1688", source_1688_keyword)
            )
            st.success("1688 검색을 열었습니다.")

    with c3:
        if st.button(
            "도우인 열기",
            key=f"{key_prefix}_search_douyin",
            use_container_width=True,
        ):
            open_with_login_browser(
                make_search_url("douyin", douyin_keyword)
            )
            st.success("도우인 검색을 열었습니다.")


def run_project_pipeline(
    project,
    sample_count,
    review_image_paths=None,
    review_text="",
    locked_script="",
    product_image_paths=None,
    product_image_path="",
    youtube_privacy_status="private",
    viral_video_sources=None,
    declared_review_count=0,
    review_checked_at="",
    monthly_purchase_count=0,
    rating=0.0,
    input_product_name="",
    stop_after_image_generation=False,
):
    """Sprint102-3: UI에서 동일 프로젝트의 중복 원클릭 진입을 차단합니다."""
    project_key = str(safe_project_id(project))

    with _PIPELINE_RUN_GUARD:
        if project_key in _ACTIVE_PIPELINE_PROJECTS:
            print(
                "[Sprint102-3 One Click Guard] SKIPPED:",
                project_key,
                flush=True,
            )
            cached = st.session_state.get(
                f"one_click_result_{project_key}",
                {},
            )
            if isinstance(cached, dict) and cached:
                return cached
            return {
                "job_id": "",
                "state": {},
                "outputs": {
                    "duplicate_execution_skipped": True,
                    "project_key": project_key,
                },
                "summary": "동일 프로젝트가 이미 실행 중이어서 중복 실행을 건너뛰었습니다.",
                "duplicate_execution_skipped": True,
            }

        _ACTIVE_PIPELINE_PROJECTS.add(project_key)

    print(
        "[Sprint102-3 One Click Guard] ACQUIRED:",
        project_key,
        flush=True,
    )

    try:
        print(
            "[Sprint147-5 UI ROUTE]",
            {
                "project_key": project_key,
                "stop_after_image_generation": bool(stop_after_image_generation),
                "locked_script_chars": len(str(locked_script or "").strip()),
            },
            flush=True,
        )
        return _run_project_pipeline_impl(
            project=project,
            sample_count=sample_count,
            review_image_paths=review_image_paths,
            review_text=review_text,
            locked_script=locked_script,
            product_image_paths=product_image_paths,
            product_image_path=product_image_path,
            youtube_privacy_status=youtube_privacy_status,
            viral_video_sources=viral_video_sources,
            declared_review_count=declared_review_count,
            review_checked_at=review_checked_at,
            monthly_purchase_count=monthly_purchase_count,
            rating=rating,
            input_product_name=input_product_name,
            stop_after_image_generation=stop_after_image_generation,
        )
    finally:
        with _PIPELINE_RUN_GUARD:
            _ACTIVE_PIPELINE_PROJECTS.discard(project_key)
        print(
            "[Sprint102-3 One Click Guard] RELEASED:",
            project_key,
            flush=True,
        )


def _run_project_pipeline_impl(
    project,
    sample_count,
    review_image_paths=None,
    review_text="",
    locked_script="",
    product_image_paths=None,
    product_image_path="",
    youtube_privacy_status="private",
    viral_video_sources=None,
    declared_review_count=0,
    review_checked_at="",
    monthly_purchase_count=0,
    rating=0.0,
    input_product_name="",
    stop_after_image_generation=False,
):
    print(
        "[Sprint72-1] run_project_pipeline entered",
        flush=True,
    )

    review_image_paths = list(review_image_paths or [])
    review_text = str(review_text or "").strip()
    locked_script = str(locked_script or "").strip()
    product_image_paths = list(product_image_paths or [])
    if product_image_path and product_image_path not in product_image_paths:
        product_image_paths.insert(0, product_image_path)
    product_image_path = product_image_paths[0] if product_image_paths else ""
    viral_video_sources = [str(item).strip() for item in list(viral_video_sources or []) if str(item).strip()][:10]

    print(
        "[Sprint72-1] Review Images:",
        len(review_image_paths),
        review_image_paths,
        flush=True,
    )

    print(
        "[Sprint115-1 Evidence Input] Manual Review Text:",
        bool(review_text),
        "chars=",
        len(review_text),
        flush=True,
    )

    print(
        "[Sprint134-1 Viral Input] Sources:",
        len(viral_video_sources),
        viral_video_sources,
        flush=True,
    )

    print(
        "[Sprint94-1 Manual Images] Product Images:",
        len(product_image_paths),
        product_image_paths,
        flush=True,
    )

    print(
        "[Sprint146-9 UI -> WORKFLOW]",
        {
            "locked_script_chars": len(locked_script),
            "monthly_purchase_count": int(monthly_purchase_count or 0),
            "review_count": int(declared_review_count or 0),
            "rating": float(rating or 0),
            "review_checked_at": str(review_checked_at or ""),
            "image_count": len(product_image_paths),
        },
        flush=True,
    )

    print(
        "[Sprint147-5 UI -> WORKFLOW CALL]",
        {
            "stop_after_image_generation": bool(stop_after_image_generation),
            "locked_script_chars": len(locked_script),
            "image_count": len(product_image_paths),
        },
        flush=True,
    )

    result = WorkflowEngine().run_project(
        project,
        sample_count=sample_count,
        review_image_paths=review_image_paths,
        review_text=review_text,
        locked_script=locked_script,
        product_image_paths=product_image_paths,
        product_image_path=product_image_path,
        youtube_privacy_status=youtube_privacy_status,
        viral_video_sources=viral_video_sources,
        declared_review_count=declared_review_count,
        review_checked_at=review_checked_at,
        monthly_purchase_count=monthly_purchase_count,
        rating=rating,
        input_product_name=input_product_name,
        stop_after_image_generation=stop_after_image_generation,
    )

    save_pipeline_result(project, result)

    st.session_state[
        f"one_click_result_{safe_project_id(project)}"
    ] = result

    return result


def show_review_upload_area(project, key_prefix):
    project_safe_id = safe_project_id(project)
    saved_paths = list_saved_review_images(project)

    st.subheader("리뷰 이미지 OCR")
    st.caption(
        "쿠팡 리뷰 캡처 이미지를 여러 장 선택하면 "
        "프로젝트별 폴더에 저장한 뒤 OCR과 리뷰 분석에 사용합니다."
    )

    uploaded_files = st.file_uploader(
        "리뷰 이미지 선택",
        type=["png", "jpg", "jpeg", "webp", "bmp"],
        accept_multiple_files=True,
        key=f"{key_prefix}_review_images_{project_safe_id}",
    )

    if uploaded_files:
        st.success(
            f"새 리뷰 이미지 {len(uploaded_files)}장이 선택되었습니다."
        )
    elif saved_paths:
        st.info(
            f"이 프로젝트에 저장된 리뷰 이미지 {len(saved_paths)}장을 "
            "다시 사용합니다."
        )
        st.caption(str(review_image_dir(project)))
    else:
        st.caption("선택되거나 저장된 리뷰 이미지가 없습니다.")

    return uploaded_files


def show_review_text_input_area(project, key_prefix):
    """Sprint115-3: 리뷰 입력값을 text_area 반환값으로 직접 전달합니다."""
    project_safe_id = safe_project_id(project)
    state_key = f"{key_prefix}_review_text_{project_safe_id}"

    st.subheader("리뷰 · 댓글 직접 입력")
    st.caption(
        "한글 리뷰나 댓글을 그대로 붙여넣으세요. "
        "내용이 있으면 리뷰 이미지 OCR보다 직접 입력값을 우선 사용합니다."
    )

    review_text = st.text_area(
        "리뷰 또는 댓글 붙여넣기",
        height=220,
        placeholder=(
            "바퀴가 부드럽게 잘 굴러가요.\n\n"
            "3박 4일 여행에 크기가 잘 맞았습니다."
        ),
        key=state_key,
    )

    review_text = str(review_text or "")

    st.caption(f"현재 입력 글자 수: {len(review_text.strip())}")

    if review_text.strip():
        st.success(
            f"직접 입력 리뷰가 준비됐습니다. "
            f"({len(review_text.strip())}자)"
        )

    return review_text


def render_project_pipeline(
    project,
    sample_count,
    review_text="",
    youtube_privacy_status="private",
):
    init_selected_sources(project)

    project_safe_id = safe_project_id(project)
    result_key = f"one_click_result_{project_safe_id}"

    path_debug = VideoPathResolver().debug(project)
    project_name = (
        getattr(project, "product_name", "")
        or getattr(project, "title", "")
    )

    print(
        "[UTF8 UI PROJECT DISPLAY]",
        {
            "product_name_raw": getattr(project, "product_name", ""),
            "product_name_repr": repr(getattr(project, "product_name", "")),
            "title_raw": getattr(project, "title", ""),
            "title_repr": repr(getattr(project, "title", "")),
            "project_name_raw": project_name,
            "project_name_repr": repr(project_name),
        },
        flush=True,
    )

    st.success(f"선택된 프로젝트: {project_name}")

    if not path_debug.get("exists"):
        st.warning("이 프로젝트에는 아직 원본 영상이 없습니다.")
    else:
        st.caption(
            f"영상: {path_debug.get('video_path')} / "
            f"{path_debug.get('size_mb')}MB"
        )

    uploaded_product_images = show_product_image_upload_area(
        project,
        key_prefix="existing",
    )

    uploaded_review_images = show_review_upload_area(
        project,
        key_prefix="existing",
    )

    viral_urls_text, uploaded_viral_videos = show_viral_input_area(
        project,
        key_prefix="existing",
    )

    manual_review_text = str(review_text or "")

    c1, c2 = st.columns(2)

    if c1.button(
        "현재 프로젝트 원클릭 실행",
        use_container_width=True,
        key=f"existing_one_click_{project_safe_id}",
    ):
        manual_review_text = str(manual_review_text or "")
        print(
            "[Sprint115-4 Unified Review Value] chars=",
            len(manual_review_text.strip()),
            flush=True,
        )
        print(
            "[Sprint72-1] One Click button pressed",
            flush=True,
        )

        try:
            product_image_paths = save_uploaded_product_images(
                project,
                uploaded_product_images,
            )
            product_image_path = (
                product_image_paths[0] if product_image_paths else ""
            )
        except Exception as exc:
            st.error(f"상품 대표 이미지 저장 실패: {exc}")
            return

        try:
            review_paths = save_uploaded_review_images(
                project,
                uploaded_review_images,
            )
        except Exception as exc:
            st.error(f"리뷰 이미지 저장 실패: {exc}")
            return

        try:
            viral_file_paths = save_uploaded_viral_videos(project, uploaded_viral_videos)
            viral_sources = (parse_viral_urls(viral_urls_text) + viral_file_paths)[:10]
        except Exception as exc:
            st.error(f"바이럴 영상 저장 실패: {exc}")
            return

        if product_image_paths:
            st.info(
                f"상품 이미지 {len(product_image_paths)}장을 AI Director에 전달합니다."
            )

        if manual_review_text.strip():
            st.info("직접 입력한 한글 리뷰를 우선 사용합니다. 리뷰 이미지 OCR은 건너뜁니다.")
        elif review_paths:
            st.info(
                f"리뷰 이미지 {len(review_paths)}장을 OCR에 전달합니다."
            )

        with st.spinner("One Click Pipeline 실행 중입니다..."):
            try:
                result = run_project_pipeline(
                    project,
                    sample_count,
                    review_image_paths=review_paths,
                    review_text=manual_review_text,
                    product_image_paths=product_image_paths,
                    product_image_path=product_image_path,
                    youtube_privacy_status=youtube_privacy_status,
                    viral_video_sources=viral_sources,
                    input_product_name=project_name,
                )
            except Exception as exc:
                st.error(f"원클릭 실행 실패: {exc}")
                return

        st.success("원클릭 실행 결과를 저장했습니다.")

        outputs = (
            result.get("outputs", {})
            if isinstance(result, dict)
            else {}
        )

        review_ocr = outputs.get("review_ocr", {})
        review_insight = outputs.get("review_insight", {})
        product_plan = outputs.get("product_plan", {})

        st.write(
            "OCR 이미지 수:",
            review_ocr.get("image_count", len(review_paths)),
        )
        st.write(
            "OCR 리뷰 수:",
            review_ocr.get("review_count", 0),
        )
        st.write(
            "최종 병합 리뷰 수:",
            product_plan.get(
                "review_count",
                review_insight.get("review_count", 0),
            ),
        )
        st.write(
            "리뷰 분석 성공:",
            bool(review_insight.get("ok")),
        )

        project_latest = ProjectRepository().get(getattr(project, "id", "")) or project
        try:
            data = json.loads(getattr(project_latest, "data_json", "") or "{}")
        except Exception:
            data = {}

        youtube = data.get("youtube", {})
        youtube_history = data.get("youtube_history", [])

        if youtube.get("watch_url"):
            st.divider()
            st.subheader("📺 YouTube 업로드")
            st.success("YouTube 업로드 완료")
            st.write("Video ID:", youtube.get("video_id", ""))
            st.write("Watch URL:", youtube.get("watch_url", ""))
            st.link_button(
                "브라우저에서 열기",
                youtube.get("watch_url"),
                use_container_width=True,
            )

        if isinstance(youtube_history, list) and youtube_history:
            st.divider()
            st.subheader("📚 YouTube 업로드 이력")
            st.caption(
                f"총 {len(youtube_history)}개의 업로드 이력이 있습니다."
            )

            for index, item in enumerate(
                youtube_history,
                start=1,
            ):
                if not isinstance(item, dict):
                    continue

                video_id = item.get("video_id", "")
                watch_url = item.get("watch_url", "")
                uploaded_at = item.get("uploaded_at", "")
                status = item.get("status", "")
                manifest_path = item.get("manifest_path", "")

                with st.expander(
                    f"{index}. {video_id or 'Video ID 없음'}",
                    expanded=index == 1,
                ):
                    st.write("상태:", status)
                    st.write("업로드 시간:", uploaded_at)
                    st.write("Video ID:", video_id)
                    st.write("Watch URL:", watch_url)

                    if manifest_path:
                        st.caption(
                            f"Manifest: {manifest_path}"
                        )

                    if watch_url:
                        st.link_button(
                            "영상 열기",
                            watch_url,
                            use_container_width=True,
                            key=(
                                f"youtube_history_link_"
                                f"{project_safe_id}_{index}"
                            ),
                        )

    if c2.button("큐에 추가", use_container_width=True):
        job = JobQueue().add(
            getattr(project, "id", ""),
            project_name,
        )
        st.success(f"큐 추가 완료: {job.get('job_id')}")

    result = st.session_state.get(result_key)

    if not result:
        result = load_pipeline_result(project)
        if result:
            st.session_state[result_key] = result
            st.caption(
                "최근 원클릭 결과를 복원했습니다: "
                f"{pipeline_result_path(project)}"
            )

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

            show_selected_sources(project)

            show_content_pack_view_new(
                project=project,
                result=result,
                content_pack=st.session_state.get(
                    f"content_pack_{project_safe_id}",
                    {},
                ),
                paths=st.session_state.get(
                    f"ai_content_pack_export_"
                    f"{getattr(project, 'id', '')}",
                    {},
                ),
            )

    else:
        st.info(
            "원클릭 결과가 아직 없습니다. "
            "먼저 원클릭 실행을 완료해 주세요."
        )


def _resolve_final_video_path(result):
    """Sprint146-5: Workflow 결과 구조가 달라도 실제 최종 MP4를 찾습니다."""
    outputs = result.get("outputs", {}) if isinstance(result, dict) else {}
    candidates = []

    final_video = outputs.get("final_video")
    if isinstance(final_video, dict):
        candidates.extend(
            [
                final_video.get("output_path"),
                final_video.get("video_path"),
                final_video.get("path"),
            ]
        )
    else:
        candidates.append(final_video)

    for key in (
        "final_video_path",
        "produced_final_path",
        "active_video_path",
        "ai_video_path",
        "image_motion_video_path",
        "merged_video_path",
    ):
        candidates.append(outputs.get(key))

    content_factory = outputs.get("content_factory")
    if isinstance(content_factory, dict):
        for key in (
            "final_video_path",
            "video_path",
            "active_video_path",
            "output_path",
        ):
            candidates.append(content_factory.get(key))

    for raw_path in candidates:
        path_text = str(raw_path or "").strip()
        if not path_text:
            continue
        path = Path(path_text)
        if path.is_file() and path.suffix.lower() == ".mp4":
            return str(path)

    return ""


def _extract_image_review_scenes(result):
    outputs = result.get("outputs", {}) if isinstance(result, dict) else {}
    review = outputs.get("image_review", {})
    if not isinstance(review, dict):
        return []
    return [dict(item) for item in list(review.get("scenes") or []) if isinstance(item, dict)]



def _first_existing_image_path(*values):
    for value in values:
        path_text = str(value or "").strip()
        if path_text and Path(path_text).is_file():
            return path_text
    return ""


def _find_first_value(data, keys):
    """중첩 dict/list에서 지정 키의 첫 유효 값을 찾습니다."""
    if isinstance(data, dict):
        for key in keys:
            value = data.get(key)
            if value not in (None, "", [], {}):
                return value
        for value in data.values():
            found = _find_first_value(value, keys)
            if found not in (None, "", [], {}):
                return found
    elif isinstance(data, list):
        for item in data:
            found = _find_first_value(item, keys)
            if found not in (None, "", [], {}):
                return found
    return None


def _director_json_candidates(project_id):
    folder = PRODUCT_IMAGE_ROOT / f"project_{project_id}"
    preferred = [
        folder / "ai_image_director_154_2.json",
        folder / "ai_image_director_154.json",
        folder / "ai_image_director_150_4.json",
        folder / "ai_image_manifest.json",
        folder / "manifest.json",
    ]
    existing = [path for path in preferred if path.is_file()]

    extras = sorted(
        folder.glob("ai_image_director*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for path in extras:
        if path not in existing:
            existing.append(path)
    return existing


def _recover_review_scenes_from_project(project_id):
    """
    기존 Director JSON과 생성 시도 PNG에서 검토용 장면을 복원합니다.
    새 Gemini 생성이나 Vision 호출은 하지 않습니다.
    """
    project_id = str(project_id).strip()
    folder = PRODUCT_IMAGE_ROOT / f"project_{project_id}"
    source_path = None
    director_data = {}

    for candidate in _director_json_candidates(project_id):
        loaded = read_json(candidate, {})
        if isinstance(loaded, dict) and loaded:
            director_data = loaded
            source_path = candidate
            if isinstance(loaded.get("generation_runs"), list):
                break

    generation_runs = (
        director_data.get("generation_runs")
        if isinstance(director_data.get("generation_runs"), list)
        else []
    )

    if not generation_runs:
        nested = _find_first_value(director_data, ("generation_runs",))
        if isinstance(nested, list):
            generation_runs = nested

    scenes = []
    for index, raw_run in enumerate(generation_runs, start=1):
        if not isinstance(raw_run, dict):
            continue

        scene_id = str(
            raw_run.get("scene_id")
            or f"scene_{index:02d}"
        ).strip()
        attempts = [
            dict(item)
            for item in list(raw_run.get("attempts") or [])
            if isinstance(item, dict)
        ]

        best_attempt = None
        for item in attempts:
            candidate_path = _first_existing_image_path(
                item.get("generated_image_path"),
                item.get("image_path"),
                item.get("output_image_path"),
                item.get("output_path"),
            )
            if not candidate_path:
                continue
            candidate = dict(item)
            candidate["_existing_path"] = candidate_path
            score = float(
                candidate.get("score")
                or candidate.get("fidelity_score")
                or candidate.get("product_identity_score")
                or 0
            )
            candidate["_score"] = score
            if best_attempt is None or score > best_attempt["_score"]:
                best_attempt = candidate

        selected_path = _first_existing_image_path(
            raw_run.get("selected_image_path"),
            raw_run.get("review_image_path"),
            raw_run.get("generated_image_path"),
            raw_run.get("resolved_image_path"),
        )
        if not selected_path and best_attempt:
            selected_path = best_attempt["_existing_path"]

        # JSON에 시도가 없더라도 프로젝트 폴더의 장면 PNG를 복원합니다.
        if not selected_path:
            scene_files = sorted(
                folder.glob(f"{scene_id}_ai_attempt_*.png"),
                key=lambda path: path.stat().st_mtime,
            )
            if scene_files:
                selected_path = str(scene_files[-1])

        source_scene = (
            raw_run.get("source_scene")
            if isinstance(raw_run.get("source_scene"), dict)
            else {}
        )
        fidelity = (
            best_attempt.get("fidelity")
            if best_attempt and isinstance(best_attempt.get("fidelity"), dict)
            else {}
        )
        issues = list(
            raw_run.get("issues")
            or fidelity.get("issues")
            or (
                best_attempt.get("issues")
                if best_attempt else []
            )
            or []
        )
        score = float(
            raw_run.get("best_score")
            or fidelity.get("fidelity_score")
            or (
                best_attempt.get("_score")
                if best_attempt else 0
            )
            or 0
        )
        passed = bool(
            raw_run.get("passed")
            or fidelity.get("passed")
            or (
                best_attempt.get("passed")
                if best_attempt else False
            )
        )

        scenes.append(
            {
                "scene_id": scene_id,
                "scene_index": int(
                    raw_run.get("scene_index")
                    or source_scene.get("scene_index")
                    or index
                ),
                "image_path": selected_path,
                "selected_image_path": selected_path,
                "review_image_path": selected_path,
                "generated_image_path": selected_path,
                "passed": passed,
                "fidelity_passed": passed,
                "best_score": score,
                "fidelity_score": score,
                "issues": issues,
                "attempts": attempts,
                "attempt_count": len(attempts),
                "subtitle_text": str(
                    raw_run.get("subtitle_text")
                    or source_scene.get("subtitle_text")
                    or source_scene.get("subtitle")
                    or source_scene.get("dialogue")
                    or ""
                ).strip(),
                "prompt": str(
                    raw_run.get("prompt")
                    or raw_run.get("image_prompt")
                    or source_scene.get("image_prompt")
                    or source_scene.get("prompt")
                    or ""
                ),
                "negative_prompt": str(
                    raw_run.get("negative_prompt")
                    or source_scene.get("negative_prompt")
                    or ""
                ),
                "reference_image_path": str(
                    raw_run.get("reference_image_path")
                    or source_scene.get("reference_image_path")
                    or folder / "00_main.png"
                ),
                "recovered_from_project": True,
            }
        )

    # generation_runs 구조를 못 찾으면 파일명으로 장면을 복원합니다.
    if not scenes:
        grouped = {}
        for path in sorted(folder.glob("scene_*_ai_attempt_*.png")):
            match = re.match(r"(scene_\d+)_ai_attempt_(\d+)\.png$", path.name)
            if not match:
                continue
            grouped.setdefault(match.group(1), []).append(path)

        for index, (scene_id, paths) in enumerate(sorted(grouped.items()), start=1):
            selected_path = str(paths[-1])
            scenes.append(
                {
                    "scene_id": scene_id,
                    "scene_index": index,
                    "image_path": selected_path,
                    "selected_image_path": selected_path,
                    "review_image_path": selected_path,
                    "generated_image_path": selected_path,
                    "passed": False,
                    "fidelity_passed": False,
                    "best_score": 0.0,
                    "issues": ["기존 생성 이미지를 파일에서 복원했습니다."],
                    "attempts": [
                        {
                            "attempt": attempt_index,
                            "generated_image_path": str(path),
                            "passed": False,
                        }
                        for attempt_index, path in enumerate(paths, start=1)
                    ],
                    "attempt_count": len(paths),
                    "subtitle_text": "",
                    "prompt": "",
                    "negative_prompt": "",
                    "reference_image_path": str(folder / "00_main.png"),
                    "recovered_from_project": True,
                }
            )

    return {
        "ok": bool(scenes),
        "project_id": project_id,
        "source_path": str(source_path or ""),
        "scenes": scenes,
        "scene_count": len(scenes),
    }


def _recover_project_input_payload(project, project_id):
    """최종 영상 제작에 필요한 기존 Locked Script와 신뢰 입력값을 복원합니다."""
    latest_result = read_json(
        RESULT_DIR / f"{project_id}_latest_result.json",
        {},
    )
    try:
        project_data = json.loads(getattr(project, "data_json", "") or "{}")
    except Exception:
        project_data = {}

    sources = [latest_result, project_data]
    locked_script = ""
    for source in sources:
        value = _find_first_value(
            source,
            (
                "locked_script",
                "approved_script_text",
                "original_best_script",
                "best_script",
            ),
        )
        if value:
            locked_script = str(value).strip()
            break

    def recover_number(keys, default):
        for source in sources:
            value = _find_first_value(source, keys)
            if value not in (None, ""):
                try:
                    return type(default)(value)
                except Exception:
                    continue
        return default

    return {
        "product_name": str(
            getattr(project, "product_name", "")
            or getattr(project, "title", "")
            or ""
        ),
        "locked_script": locked_script,
        "monthly_purchase_count": recover_number(
            ("monthly_purchase_count",),
            1,
        ),
        "declared_review_count": recover_number(
            ("declared_review_count", "review_count"),
            1,
        ),
        "rating": recover_number(("rating",), 0.0),
        "review_checked_at": str(
            _find_first_value(
                latest_result,
                ("review_checked_at",),
            )
            or _find_first_value(
                project_data,
                ("review_checked_at",),
            )
            or ""
        ),
    }


def _open_existing_project_review(project_id):
    project_id = str(project_id or "").strip()
    if not project_id:
        return {"ok": False, "message": "프로젝트 ID를 입력해 주세요."}

    project = ProjectRepository().get(project_id)
    if project is None:
        try:
            project = ProjectRepository().get(int(project_id))
        except Exception:
            project = None
    if project is None:
        return {
            "ok": False,
            "message": f"프로젝트 {project_id}를 DB에서 찾지 못했습니다.",
        }

    recovery = _recover_review_scenes_from_project(project_id)
    if not recovery.get("ok"):
        return {
            "ok": False,
            "message": (
                f"project_{project_id}에서 생성 이미지를 복원하지 못했습니다."
            ),
        }

    safe_id = str(safe_project_id(project))
    result = {
        "ok": True,
        "status": "recovered_project_review",
        "outputs": {
            "image_review": {
                "ok": True,
                "status": "recovered",
                "scenes": recovery["scenes"],
                "source_path": recovery["source_path"],
            }
        },
    }
    st.session_state["sprint147_active_project_id"] = getattr(
        project,
        "id",
        project_id,
    )
    st.session_state[f"one_click_result_{safe_id}"] = result
    st.session_state[f"sprint147_review_scenes_{safe_id}"] = recovery["scenes"]
    st.session_state[f"sprint147_approved_{safe_id}"] = {}
    st.session_state[f"sprint147_input_{safe_id}"] = (
        _recover_project_input_payload(project, safe_id)
    )
    st.session_state[f"sprint147_stage_{safe_id}"] = "review"

    print(
        "[Sprint155 Project Review] Opened:",
        safe_id,
        "Scenes:",
        recovery["scene_count"],
        "Source:",
        recovery["source_path"],
        flush=True,
    )
    return {
        "ok": True,
        "project": project,
        "project_id": safe_id,
        "scene_count": recovery["scene_count"],
        "source_path": recovery["source_path"],
    }


def _generate_single_scene_image(scene, output_path):
    """Sprint147-1: 선택한 장면 한 장만 Gemini 이미지 API로 다시 생성합니다."""
    generator_class = None
    import_errors = []
    for module_name, class_name in (
        ("modules.image_ai.gemini_image_generator", "GeminiImageGenerator"),
        ("modules.image_ai.ai_image_generator", "AIImageGenerator"),
    ):
        try:
            module = __import__(module_name, fromlist=[class_name])
            generator_class = getattr(module, class_name, None)
            if generator_class is not None:
                break
        except Exception as exc:
            import_errors.append(f"{module_name}: {type(exc).__name__}: {exc}")
    if generator_class is None:
        raise RuntimeError("이미지 생성기 import 실패: " + " | ".join(import_errors))

    engine = generator_class()
    payload = {
        "scene_id": str(scene.get("scene_id") or "scene"),
        "attempt": int(scene.get("attempt_count") or 1) + 1,
        "prompt": str(scene.get("prompt") or ""),
        "image_prompt": str(scene.get("prompt") or ""),
        "negative_prompt": str(scene.get("negative_prompt") or ""),
        "reference_image_path": str(scene.get("reference_image_path") or ""),
        "output_image_path": str(output_path),
        "output_path": str(output_path),
        "overwrite": True,
    }
    last_type_error = None
    for method_name in ("generate_image", "generate", "run", "create"):
        method = getattr(engine, method_name, None)
        if not callable(method):
            continue
        for call in (lambda: method(**payload), lambda: method(payload)):
            try:
                raw = call()
                candidate = ""
                if isinstance(raw, dict):
                    candidate = str(
                        raw.get("output_image_path")
                        or raw.get("output_path")
                        or raw.get("image_path")
                        or raw.get("path")
                        or ""
                    )
                elif isinstance(raw, (str, Path)):
                    candidate = str(raw)
                if candidate and Path(candidate).is_file():
                    return candidate
                if Path(output_path).is_file():
                    return str(output_path)
            except TypeError as exc:
                last_type_error = exc
                continue
    if last_type_error:
        raise last_type_error
    raise RuntimeError("이미지 생성 결과 파일을 확인하지 못했습니다.")


def _save_review_uploaded_image(project_id, scene_id, uploaded_file):
    suffix = Path(getattr(uploaded_file, "name", "") or "").suffix.lower()
    if suffix not in SUPPORTED_PRODUCT_IMAGE_SUFFIXES:
        suffix = ".png"
    folder = PRODUCT_IMAGE_ROOT / f"project_{project_id}" / "approved_images"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{safe_file_name(scene_id, 'scene')}_user{suffix}"
    path.write_bytes(uploaded_file.getbuffer())
    return str(path)


def _render_ai_image_review(project, result):
    project_id = str(safe_project_id(project))
    scenes_key = f"sprint147_review_scenes_{project_id}"
    approved_key = f"sprint147_approved_{project_id}"
    result_key = f"one_click_result_{project_id}"

    if scenes_key not in st.session_state:
        st.session_state[scenes_key] = _extract_image_review_scenes(result)
    if approved_key not in st.session_state:
        st.session_state[approved_key] = {}

    scenes = list(st.session_state.get(scenes_key) or [])
    approved = dict(st.session_state.get(approved_key) or {})
    if not scenes:
        outputs = result.get("outputs", {}) if isinstance(result, dict) else {}
        review = outputs.get("image_review", {}) if isinstance(outputs, dict) else {}
        st.error("생성된 장면 이미지가 없습니다.")
        if isinstance(review, dict):
            st.write("이미지 생성 상태:", review.get("status", ""))
            st.write("Director 상태:", review.get("director_status", ""))
            st.write("Closed Loop 상태:", review.get("closed_loop_status", ""))
            errors = list(review.get("generation_errors") or [])
            if errors:
                st.error(" / ".join(str(item) for item in errors))
        return

    st.divider()
    st.header("장면별 AI 이미지 확인")
    st.caption("마음에 드는 이미지는 승인하고, 마음에 들지 않는 장면만 다시 생성하세요.")

    for index, scene in enumerate(scenes):
        scene_id = str(scene.get("scene_id") or f"scene_{index + 1:02d}")
        image_path = str(
            scene.get("image_path")
            or scene.get("selected_image_path")
            or scene.get("approved_image_path")
            or scene.get("generated_image_path")
            or scene.get("final_image_path")
            or scene.get("resolved_image_path")
            or scene.get("output_image_path")
            or scene.get("review_image_path")
            or (
                (scene.get("attempts") or [{}])[-1].get("generated_image_path")
                if isinstance(scene.get("attempts"), list) and scene.get("attempts")
                else ""
            )
            or ""
        ).strip()
        with st.container(border=True):
            st.subheader(f"장면 {index + 1}")
            subtitle = str(scene.get("subtitle_text") or "").strip()
            if subtitle:
                st.write(f"자막: {subtitle}")

            passed = bool(
                scene.get("passed")
                or scene.get("fidelity_passed")
            )
            score = (
                scene.get("best_score")
                or scene.get("fidelity_score")
                or scene.get("score")
                or 0
            )
            issues = list(
                scene.get("issues")
                or scene.get("validation_issues")
                or []
            )

            if passed:
                st.success(f"자동 검수 통과 · 점수 {float(score or 0):.1f}")
            else:
                st.warning(
                    f"자동 검수 미통과 · 최고 점수 {float(score or 0):.1f} · "
                    "이미지를 확인한 뒤 직접 승인하거나 다시 생성하세요."
                )
                if issues:
                    st.caption(
                        "검수 사유: "
                        + " / ".join(str(item) for item in issues[:5])
                    )
            if image_path and Path(image_path).is_file():
                print(
                    "[Sprint154-1 Image Path Fallback] Scene:",
                    scene_id,
                    "Path:",
                    image_path,
                    flush=True,
                )
                st.image(image_path, use_container_width=True)
                st.caption(image_path)
            else:
                st.error("이미지 파일을 찾지 못했습니다.")

            c1, c2 = st.columns(2)
            if c1.button(
                "승인 완료" if approved.get(scene_id) else "이 이미지 승인",
                key=f"approve_{project_id}_{scene_id}",
                use_container_width=True,
                disabled=bool(approved.get(scene_id)) or not (image_path and Path(image_path).is_file()),
            ):
                approved[scene_id] = image_path
                st.session_state[approved_key] = approved
                st.rerun()

            if c2.button(
                "다시 생성",
                key=f"regen_{project_id}_{scene_id}",
                use_container_width=True,
            ):
                output_dir = PRODUCT_IMAGE_ROOT / f"project_{project_id}" / "generated_regenerated"
                output_dir.mkdir(parents=True, exist_ok=True)
                attempt = int(scene.get("attempt_count") or 1) + 1
                output_path = output_dir / f"{scene_id}_attempt_{attempt:02d}.png"
                with st.spinner(f"장면 {index + 1} 이미지를 다시 생성 중입니다..."):
                    try:
                        new_path = _generate_single_scene_image(scene, output_path)
                    except Exception as exc:
                        st.error(f"재생성 실패: {type(exc).__name__}: {exc}")
                    else:
                        scene["image_path"] = new_path
                        scene["selected_image_path"] = new_path
                        scene["approved_image_path"] = new_path
                        scene["generated_image_path"] = new_path
                        scene["final_image_path"] = new_path
                        scene["resolved_image_path"] = new_path
                        scene["output_image_path"] = new_path
                        scene["attempt_count"] = attempt
                        scenes[index] = scene
                        approved.pop(scene_id, None)
                        st.session_state[scenes_key] = scenes
                        st.session_state[approved_key] = approved
                        print(
                            "[Sprint147-3 Image Review] Regenerated:",
                            scene_id,
                            new_path,
                            flush=True,
                        )
                        st.rerun()

            replacement = st.file_uploader(
                "내 이미지로 교체",
                type=["png", "jpg", "jpeg", "webp"],
                key=f"replace_{project_id}_{scene_id}",
            )
            if replacement is not None:
                replacement_flag = f"replace_saved_{project_id}_{scene_id}_{replacement.name}_{replacement.size}"
                if not st.session_state.get(replacement_flag):
                    new_path = _save_review_uploaded_image(project_id, scene_id, replacement)
                    scene["image_path"] = new_path
                    scene["selected_image_path"] = new_path
                    scene["approved_image_path"] = new_path
                    scene["generated_image_path"] = new_path
                    scene["final_image_path"] = new_path
                    scene["resolved_image_path"] = new_path
                    scene["output_image_path"] = new_path
                    scenes[index] = scene
                    approved.pop(scene_id, None)
                    st.session_state[scenes_key] = scenes
                    st.session_state[approved_key] = approved
                    st.session_state[replacement_flag] = True
                    st.rerun()

    approved_count = sum(1 for scene in scenes if approved.get(str(scene.get("scene_id") or "")))
    st.progress(approved_count / max(1, len(scenes)))
    st.write(f"승인 완료: {approved_count} / {len(scenes)}")

    if approved_count != len(scenes):
        st.info("모든 장면을 승인하면 최종 영상 제작 버튼이 활성화됩니다.")
        return

    if st.button(
        "승인 이미지로 최종 영상 제작",
        type="primary",
        use_container_width=True,
        key=f"finalize_{project_id}",
    ):
        selected_paths = [approved[str(scene.get("scene_id") or "")] for scene in scenes]
        payload = st.session_state.get(f"sprint147_input_{project_id}", {})
        with st.spinner("승인된 이미지로 모션·자막·최종 영상을 제작 중입니다..."):
            final_result = run_project_pipeline(
                project=project,
                sample_count=6,
                review_text="",
                locked_script=str(payload.get("locked_script") or ""),
                review_image_paths=[],
                product_image_paths=selected_paths,
                product_image_path=selected_paths[0],
                youtube_privacy_status="private",
                viral_video_sources=[],
                declared_review_count=int(payload.get("declared_review_count") or 1),
                review_checked_at=str(payload.get("review_checked_at") or ""),
                monthly_purchase_count=int(payload.get("monthly_purchase_count") or 1),
                rating=float(payload.get("rating") or 0),
                input_product_name=str(payload.get("product_name") or ""),
                stop_after_image_generation=False,
            )
        st.session_state[result_key] = final_result
        st.session_state[f"sprint147_stage_{project_id}"] = "completed"
        st.rerun()


def show_one_click_pipeline():
    st.title("⚡ 원클릭 쇼츠 완성")
    st.caption("확정 대본을 장면으로 나누고, 필요한 AI 이미지를 한 장씩 만든 뒤 승인된 이미지만 영상에 사용합니다.")
    st.caption(f"UI 버전: {UI_VERSION}")

    with st.expander("📂 기존 프로젝트 다시 열기", expanded=True):
        st.caption(
            "이미 생성된 장면을 다시 생성하지 않고 검토·승인합니다."
        )
        review_project_id = st.text_input(
            "프로젝트 ID",
            value=str(
                st.session_state.get(
                    "sprint155_review_project_id",
                    "348",
                )
            ),
            key="sprint155_review_project_id",
        )
        if st.button(
            "기존 이미지 검토 열기",
            type="secondary",
            use_container_width=True,
            key="sprint155_open_review",
        ):
            opened = _open_existing_project_review(review_project_id)
            if not opened.get("ok"):
                st.error(opened.get("message", "프로젝트를 열지 못했습니다."))
            else:
                st.success(
                    f"프로젝트 {opened['project_id']}의 기존 장면 "
                    f"{opened['scene_count']}개를 복원했습니다."
                )
                st.rerun()

    active_project_id = st.session_state.get("sprint147_active_project_id")
    if active_project_id:
        active_project = ProjectRepository().get(active_project_id)
        project_key = str(safe_project_id(active_project)) if active_project else str(active_project_id)
        result = (
            st.session_state.get(f"one_click_result_{project_key}")
            or st.session_state.get(f"one_click_result_{active_project_id}")
            or {}
        )
        stage = (
            st.session_state.get(f"sprint147_stage_{project_key}")
            or st.session_state.get(f"sprint147_stage_{active_project_id}")
            or ""
        )

        if active_project and stage == "review":
            review_scenes = _extract_image_review_scenes(result)
            cached_scenes = st.session_state.get(
                f"sprint147_review_scenes_{project_key}",
                [],
            )
            if review_scenes or cached_scenes:
                _render_ai_image_review(active_project, result)
                if st.button("새 상품으로 처음부터 시작", use_container_width=True):
                    for key in list(st.session_state.keys()):
                        if (
                            str(project_key) in str(key)
                            or str(active_project_id) in str(key)
                            or str(key).startswith("sprint147_active_project")
                        ):
                            st.session_state.pop(key, None)
                    st.rerun()
                return

            # Sprint147-2: 장면 결과가 없는 오래된 review 상태는 자동 해제합니다.
            print(
                "[Sprint147-2 Input Recovery] Cleared stale review state:",
                project_key,
                flush=True,
            )
            for key in list(st.session_state.keys()):
                if (
                    str(project_key) in str(key)
                    or str(active_project_id) in str(key)
                    or str(key).startswith("sprint147_active_project")
                ):
                    st.session_state.pop(key, None)
            active_project_id = None

        elif active_project and stage == "completed":
            final_path = _resolve_final_video_path(result)
            if final_path:
                st.success("쇼츠 전체 제작이 완료됐습니다.")
                st.video(final_path)
                st.caption(f"최종 영상: {final_path}")
            else:
                st.warning("최종 MP4를 확인하지 못했습니다.")
                st.json(result)
            if st.button("새 상품 제작", type="primary", use_container_width=True):
                for key in list(st.session_state.keys()):
                    if (
                        str(project_key) in str(key)
                        or str(active_project_id) in str(key)
                        or str(key).startswith("sprint147_active_project")
                    ):
                        st.session_state.pop(key, None)
                st.rerun()
            return

    product_name = st.text_input("상품명", placeholder="상품명을 입력하세요.", key="sprint147_product_name")
    c1, c2 = st.columns(2)
    with c1:
        monthly_purchase_count = st.number_input("최근 한 달 구매 수", min_value=1, value=1, step=1, key="sprint147_monthly_purchase_count")
        rating = st.number_input("평점", min_value=0.0, max_value=5.0, value=0.0, step=0.1, format="%.1f", key="sprint147_rating")
    with c2:
        declared_review_count = st.number_input("리뷰 개수", min_value=1, value=1, step=1, key="sprint147_declared_review_count")
        review_checked_at = st.date_input("리뷰 확인일", key="sprint147_review_checked_at")

    locked_script = st.text_area("대본", height=360, placeholder="최종 확정된 쇼츠 대본을 붙여넣으세요.", key="sprint147_locked_script")
    uploaded_product_images = st.file_uploader(
        "실제 상품 이미지 (선택)",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key="sprint147_product_images",
    )
    st.caption("실제 상품 이미지는 상품 형태를 유지하는 참고 자료로 사용합니다. 없는 장면은 AI가 생성합니다.")

    if not st.button("대본 기준 이미지 만들기", type="primary", use_container_width=True, key="sprint147_generate_images"):
        return

    print(
        "[Sprint147-5 BUTTON CLICKED] 대본 기준 이미지 만들기",
        flush=True,
    )

    errors = []
    if not str(product_name or "").strip(): errors.append("상품명을 입력해 주세요.")
    if not str(locked_script or "").strip(): errors.append("최종 확정 대본을 입력해 주세요.")
    if errors:
        for error in errors: st.error(error)
        return

    payload = {
        "coupang_url": "",
        "product_name": product_name.strip(),
        "title": product_name.strip(),
        "source": "one_click_ai_image_review_147_3",
        "monthly_purchase_count": int(monthly_purchase_count),
        "declared_review_count": int(declared_review_count),
        "rating": float(rating),
        "review_checked_at": review_checked_at.isoformat(),
        "locked_script": locked_script.strip(),
        "viral_video_sources": [],
    }
    try:
        keywords = build_keywords(payload, product_name.strip())
        project = create_project_from_payload(payload, keywords)
        project_id = getattr(project, "id", None)
        if project_id:
            project = ProjectRepository().get(project_id) or project
    except Exception as exc:
        st.error(f"프로젝트 생성 실패: {exc}")
        return

    try:
        product_image_paths = save_uploaded_product_images(project, uploaded_product_images)
    except Exception as exc:
        st.error(f"상품 이미지 저장 실패: {exc}")
        return

    with st.spinner("대본을 분석하고 장면별 이미지를 한 장씩 생성 중입니다..."):
        try:
            result = run_project_pipeline(
                project=project,
                sample_count=6,
                review_text="",
                locked_script=locked_script.strip(),
                review_image_paths=[],
                product_image_paths=product_image_paths,
                product_image_path=product_image_paths[0] if product_image_paths else "",
                youtube_privacy_status="private",
                viral_video_sources=[],
                declared_review_count=int(declared_review_count),
                review_checked_at=review_checked_at.isoformat(),
                monthly_purchase_count=int(monthly_purchase_count),
                rating=float(rating),
                input_product_name=product_name.strip(),
                stop_after_image_generation=True,
            )
        except Exception as exc:
            safe_traceback = traceback.format_exc()
            Path("full_error.log").write_text(safe_traceback, encoding="utf-8")
            st.error(f"이미지 생성 단계 실패: {type(exc).__name__}: {exc}")
            return

    project_id = str(safe_project_id(project))
    st.session_state["sprint147_active_project_id"] = getattr(project, "id", project_id)
    st.session_state[f"sprint147_input_{project_id}"] = payload
    st.session_state[f"one_click_result_{project_id}"] = result
    st.session_state[f"sprint147_stage_{project_id}"] = "review"
    st.session_state.pop(f"sprint147_review_scenes_{project_id}", None)
    st.session_state.pop(f"sprint147_approved_{project_id}", None)
    st.rerun()


render = show_one_click_pipeline