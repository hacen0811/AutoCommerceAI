import json
import re
import threading
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


UI_VERSION = "sprint130-4-ui-project-display-trace"
RESULT_DIR = Path("exports/one_click_results")
REVIEW_IMAGE_ROOT = Path("assets/review_images")
PRODUCT_IMAGE_ROOT = Path("assets/products")
SUPPORTED_PRODUCT_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
SUPPORTED_REVIEW_IMAGE_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
}


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
    product_image_paths=None,
    product_image_path="",
    youtube_privacy_status="private",
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
        return _run_project_pipeline_impl(
            project=project,
            sample_count=sample_count,
            review_image_paths=review_image_paths,
            review_text=review_text,
            product_image_paths=product_image_paths,
            product_image_path=product_image_path,
            youtube_privacy_status=youtube_privacy_status,
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
    product_image_paths=None,
    product_image_path="",
    youtube_privacy_status="private",
):
    print(
        "[Sprint72-1] run_project_pipeline entered",
        flush=True,
    )

    review_image_paths = list(review_image_paths or [])
    review_text = str(review_text or "").strip()
    product_image_paths = list(product_image_paths or [])
    if product_image_path and product_image_path not in product_image_paths:
        product_image_paths.insert(0, product_image_path)
    product_image_path = product_image_paths[0] if product_image_paths else ""

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
        "[Sprint94-1 Manual Images] Product Images:",
        len(product_image_paths),
        product_image_paths,
        flush=True,
    )

    result = WorkflowEngine().run_project(
        project,
        sample_count=sample_count,
        review_image_paths=review_image_paths,
        review_text=review_text,
        product_image_paths=product_image_paths,
        product_image_path=product_image_path,
        youtube_privacy_status=youtube_privacy_status,
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


def show_one_click_pipeline():
    st.title("⚡ 원클릭 파이프라인")
    st.caption(
        "상품명 + 상품/상세 이미지 + 리뷰 캡처를 기본 입력으로 사용합니다. "
        "쿠팡 링크는 선택사항입니다."
    )
    st.caption(f"UI 버전: {UI_VERSION}")

    sample_count = st.slider(
        "Vision 분석 프레임 수",
        4,
        12,
        6,
        2,
    )

    youtube_privacy_label = st.selectbox(
        "YouTube 공개 범위",
        [
            "🔒 비공개",
            "🔗 일부 공개",
            "🌍 공개",
        ],
        index=0,
        help=(
            "비공개: 본인만 시청 / "
            "일부 공개: 링크를 아는 사람만 시청 / "
            "공개: 누구나 검색과 시청 가능"
        ),
    )
    youtube_privacy_status = {
        "🔒 비공개": "private",
        "🔗 일부 공개": "unlisted",
        "🌍 공개": "public",
    }[youtube_privacy_label]

    st.caption(
        "이번 원클릭 실행의 YouTube 공개 설정: "
        f"{youtube_privacy_label}"
    )

    st.divider()
    st.subheader("공통 리뷰 · 댓글 직접 입력")
    st.caption(
        "여기에 붙여넣은 리뷰는 새 프로젝트 생성과 기존 프로젝트 원클릭 실행에 "
        "같이 사용됩니다. 내용이 있으면 리뷰 이미지 OCR을 건너뜁니다."
    )
    common_review_text = st.text_area(
        "리뷰 또는 댓글 붙여넣기",
        height=260,
        placeholder=(
            "쿠팡 리뷰, 유튜브·틱톡·인스타 댓글을 그대로 붙여넣으세요.\n"
            "리뷰 사이에는 빈 줄을 넣어주세요."
        ),
        key="sprint115_common_review_text",
    )
    if not common_review_text:
        common_review_text = str(
            st.session_state.get(
                "sprint115_common_review_text",
                "",
            )
        )

    from pathlib import Path
    import json

    Path("utf8_text_area_debug.json").write_text(
        json.dumps(
            {
                "text": common_review_text,
                "repr": repr(common_review_text),
                "codepoints": [
                    f"U+{ord(char):04X}"
                    for char in common_review_text
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        "[UTF8 TRACE text_area type]",
        type(common_review_text).__name__,
        flush=True,
    )

    print(
        "[UTF8 TRACE text_area repr]",
        repr(common_review_text),
        flush=True,
    )

    print(
        "[UTF8 TRACE session_state repr]",
        repr(st.session_state.get("sprint115_common_review_text")),
        flush=True,
    )

    common_review_text = str(common_review_text or "")

    print(
        "[UTF8 TRACE common_review_text UI RAW]",
        repr(common_review_text),
        flush=True,
    )

    st.caption(f"현재 입력 글자 수: {len(common_review_text.strip())}")
    if common_review_text.strip():
        st.success(
            f"공통 직접 입력 리뷰가 준비되었습니다. "
            f"({len(common_review_text.strip())}자)"
        )

    st.divider()
    st.subheader("수동 자료로 새 프로젝트 생성")

    coupang_url = st.text_area(
        "쿠팡 링크 (선택)",
        height=80,
        placeholder="링크 없이도 생성할 수 있습니다.",
    )

    product_name = st.text_area(
        "상품명",
        height=100,
        placeholder="쿠팡 상품명을 붙여넣어 주세요.",
    )

    print(
        "[UTF8 TEXT_AREA RAW]",
        product_name,
        flush=True,
    )
    print(
        "[UTF8 TEXT_AREA REPR]",
        repr(product_name),
        flush=True,
    )
    print(
        "[UTF8 TEXT_AREA UNICODE ESCAPE]",
        product_name.encode("unicode_escape").decode("ascii"),
        flush=True,
    )
    print(
        "[UTF8 TEXT_AREA UTF8 HEX]",
        product_name.encode("utf-8").hex(),
        flush=True,
    )

    new_project_product_images = st.file_uploader(
        "새 프로젝트 상품 이미지 · 상세페이지 캡처",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key="new_project_product_images",
        help=(
            "첫 번째 이미지는 대표 이미지, 나머지는 상세 이미지로 저장됩니다."
        ),
    )

    if new_project_product_images:
        st.success(
            f"상품 이미지 {len(new_project_product_images)}장이 선택되었습니다."
        )

    new_project_review_images = st.file_uploader(
        "새 프로젝트 리뷰 이미지",
        type=["png", "jpg", "jpeg", "webp", "bmp"],
        accept_multiple_files=True,
        key="new_project_review_images",
        help=(
            "프로젝트 생성 후 "
            "assets/review_images/project_{프로젝트ID}에 저장됩니다."
        ),
    )

    if new_project_review_images:
        st.success(
            f"리뷰 이미지 {len(new_project_review_images)}장이 "
            "선택되었습니다."
        )

    auto_run = st.checkbox(
        "프로젝트 생성 후 바로 원클릭 실행",
        value=False,
    )

    if st.button(
        "수동 자료로 프로젝트 생성",
        type="primary",
        use_container_width=True,
    ):
        print(
            "[UTF8 UI INPUT ON CREATE]",
            json.dumps(
                {
                    "product_name": product_name,
                    "coupang_url": coupang_url,
                },
                ensure_ascii=False,
                default=str,
            ),
            flush=True,
        )

        if not product_name.strip():
            st.error("상품명을 입력해 주세요.")
            return

        with st.spinner("프로젝트와 검색 키워드를 생성 중입니다..."):
            try:
                if coupang_url.strip():
                    project, product_payload, keywords = (
                        rebuild_project_from_coupang(
                            coupang_url.strip(),
                            product_name.strip(),
                        )
                    )
                else:
                    product_payload = {
                        "coupang_url": "",
                        "product_name": product_name.strip(),
                        "title": product_name.strip(),
                        "source": "manual_upload",
                    }
                    keywords = build_keywords(
                        product_payload,
                        product_name.strip(),
                    )
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
                    project_id = getattr(project, "id", None)
                    if project_id:
                        project = ProjectRepository().get(project_id) or project
            except Exception as exc:
                st.error(f"프로젝트 생성 실패: {exc}")
                return

        print(
            "[UTF8 PROJECT AFTER SAVE]",
            json.dumps(
                {
                    "id": getattr(project, "id", None),
                    "product_name": getattr(project, "product_name", ""),
                    "title": getattr(project, "title", ""),
                    "data_json": getattr(project, "data_json", ""),
                },
                ensure_ascii=False,
                default=str,
            ),
            flush=True,
        )

        try:
            product_image_paths = save_uploaded_product_images(
                project,
                new_project_product_images,
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
                new_project_review_images,
            )
        except Exception as exc:
            st.error(f"리뷰 이미지 저장 실패: {exc}")
            return

        st.session_state["sprint50_created_project_id"] = (
            getattr(project, "id", None)
        )
        st.session_state["sprint50_product_payload"] = product_payload
        st.session_state["sprint50_keywords"] = keywords

        st.success("수동 자료 기반 프로젝트를 생성했습니다.")

        if product_image_paths:
            st.success(
                f"상품 이미지 {len(product_image_paths)}장을 저장했습니다."
            )
            st.caption(str(product_image_dir(project)))

        if review_paths:
            st.success(
                f"리뷰 이미지 {len(review_paths)}장을 저장했습니다."
            )
            st.caption(str(review_image_dir(project)))

        show_search_links(keywords, key_prefix="created")

        if auto_run:
            with st.spinner(
                "생성된 프로젝트로 원클릭 후보 수집을 실행 중입니다..."
            ):
                try:
                    result = run_project_pipeline(
                        project,
                        sample_count,
                        review_image_paths=review_paths,
                        review_text=common_review_text,
                        product_image_paths=product_image_paths,
                        product_image_path=product_image_path,
                        youtube_privacy_status=youtube_privacy_status,
                    )
                    st.success("원클릭 후보 수집까지 완료했습니다.")

                    outputs = (
                        result.get("outputs", {})
                        if isinstance(result, dict)
                        else {}
                    )
                    review_ocr = outputs.get("review_ocr", {})
                    review_insight = outputs.get(
                        "review_insight",
                        {},
                    )

                    st.write(
                        "OCR 리뷰 수:",
                        review_ocr.get("review_count", 0),
                    )
                    st.write(
                        "리뷰 분석 성공:",
                        bool(review_insight.get("ok")),
                    )
                except Exception as exc:
                    st.error(f"원클릭 실행 실패: {exc}")

        if st.session_state.get("sprint50_keywords"):
            with st.expander(
                "최근 생성 키워드 보기",
                expanded=False,
            ):
                show_search_links(
                    st.session_state.get(
                        "sprint50_keywords",
                        {},
                    ),
                    key_prefix="recent",
                )

    st.divider()
    st.subheader("기존 프로젝트 선택 실행")

    selector = ProjectSelector()
    projects = selector.all_projects()

    if not projects:
        st.info(
            "아직 프로젝트가 없습니다. "
            "위 쿠팡 링크 입력으로 새 프로젝트를 생성해 주세요."
        )
        return

    labels = selector.labels(projects)

    created_project_id = st.session_state.get(
        "sprint50_created_project_id"
    )
    default_index = 0

    if created_project_id:
        for idx, item in enumerate(labels.values()):
            if str(getattr(item, "id", "")) == str(
                created_project_id
            ):
                default_index = idx
                break

    selected_label = st.selectbox(
        "프로젝트 선택",
        list(labels.keys()),
        index=default_index,
    )

    project = labels[selected_label]
    project = ProjectRepository().get(project.id) or project

    render_project_pipeline(
        project,
        sample_count,
        review_text=common_review_text,
        youtube_privacy_status=youtube_privacy_status,
    )

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
    for file_path in PipelineState().list_recent(10):
        st.write(f"• {file_path.name}")


from app.pages.pipeline_page import show_pipeline_page


if __name__ == "__main__":
    show_pipeline_page()