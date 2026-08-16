from uuid import uuid4
from pathlib import Path
import hashlib
import json
import mimetypes
import os
import re
import sys
import shutil
import subprocess
import threading
import time

try:
    from PIL import Image
except ImportError:
    Image = None

from modules.product.product_engine import ProductEngine
from modules.source.source_video_engine import SourceVideoEngine
from modules.source.video_ranker import SourceVideoRanker
from modules.pipeline.real_vision_runner import RealVisionRunner
from modules.editor.auto_editor_engine import AutoEditorEngine
from modules.editor.capcut_project_exporter import CapCutProjectExporter
from modules.workflow.pipeline_state import PipelineState
from modules.video.video_path_resolver import VideoPathResolver
from modules.studio.video_sourcing_engine import VideoSourcingEngine
from modules.video.video_quality_engine import VideoQualityEngine
from modules.video.shopping_fit_engine import ShoppingFitEngine
from modules.video.video_candidate_selector import VideoCandidateSelector
from modules.video.video_candidate_ranker import VideoCandidateRanker
from modules.video.viral_pattern_engine import ViralPatternEngine
from modules.content.content_factory import ContentFactory
from modules.content.review_insight_engine import ReviewInsightEngine
from modules.content.review_cleaner import ReviewCleaner
from modules.content.review_quote_selector import ReviewQuoteSelector
from modules.content.review_hook_generator import ReviewHookGenerator
from modules.content.hook_optimizer import HookOptimizer
from modules.content.review_script_generator import ReviewScriptGenerator
from modules.content.script_closed_loop import ScriptClosedLoop
from modules.content.script_revision_engine import ScriptRevisionEngine
from modules.content.viral.viral_collector import ViralCollector
from modules.content.viral.viral_library_ingestor import ViralLibraryIngestor
from modules.content.viral.viral_scene_analyzer import ViralSceneAnalyzer
from modules.content.viral.viral_editing_feature_analyzer import ViralEditingFeatureAnalyzer
from modules.content.viral.viral_pipeline import run_viral_pipeline
from modules.publisher.publisher_engine import PublisherEngine
from modules.publisher.utf8_guard import PublisherUTF8Guard
from modules.publisher.publisher_orchestrator import PublisherOrchestrator
from modules.publisher.publisher_result_store import PublisherResultStore
from modules.publisher.upload_queue_engine import UploadQueueEngine
from modules.publisher.upload_dispatcher import UploadDispatcher
from modules.publisher.youtube_upload_executor import YouTubeUploadExecutor
from modules.publisher.reservation_queue import ReservationQueue
from modules.publisher.scheduled_metadata_builder import ScheduledMetadataBuilder
from modules.publisher.instagram_upload_executor import InstagramUploadExecutor
from modules.video.ai_video_engine import AIVideoEngine
from modules.video.gemini_veo_provider import GeminiVeoProvider
from modules.video.ai_scene_merger import AISceneMerger
from modules.video.image_motion_generator import ImageMotionGenerator
from modules.video.video_pipeline import VideoPipeline
from modules.story import StoryIntelligenceEngine
from modules.story.scene_image_planner import SceneImagePlanner
from modules.image_ai.ai_image_director import AIImageDirector
from modules.image_ai.image_director import ImageDirector
from modules.image_ai.image_pool_builder import ImagePoolBuilder
from modules.image_ai.product_keeper import ProductKeeper
try:
    from modules.image_ai.image_extractor import ImageExtractor
except ImportError:
    ImageExtractor = None
from modules.image_ai import (
    ImageStripSplitter,
    ImageVisionAnalyzer,
    ImageTagger,
    ScenePlanner,
    SceneImageSelector,
    GeminiDirector,
    DirectorManifestWriter,
    SceneVideoGenerator,
    SceneMergeEngine,
)
try:
    from modules.review.review_image_ocr import ReviewImageOCR
except ImportError:
    try:
        from modules.content.review_image_ocr import ReviewImageOCR
    except ImportError:
        ReviewImageOCR = None
from modules.social import SocialCommentCollector
from modules.project.repository import ProjectRepository
from modules.video.download_utils import (
    latest_downloaded_video,
    project_source_video_dir,
    safe_file_name,
)



# Sprint145-14: Windows PowerShell/Streamlit 로그도 UTF-8로 고정합니다.
for _stream in (getattr(sys, "stdout", None), getattr(sys, "stderr", None)):
    try:
        if _stream is not None and hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

print("######## WORKFLOW_ENGINE SPRINT194-36 HISTORY TTS VOICE ID CACHE FALLBACK LOADED ########", flush=True)
print("######## WORKFLOW_ENGINE SPRINT194-38A HISTORY RENDER FILTER HOTFIX LOADED ########", flush=True)
print("######## WORKFLOW_ENGINE SPRINT194-60 HISTORY YOUTH FONT DIRECT ONLY LOADED ########", flush=True)
print("######## WORKFLOW_ENGINE SPRINT194-75K HISTORY EN FINAL SHORT NATURAL LOADED ########", flush=True)
print("######## WORKFLOW_ENGINE SPRINT194-76 HISTORY FINAL COMMON CONTRACT LOADED ########", flush=True)


class WorkflowEngine:
    """
    Sprint 62 Workflow Engine

    기존 Sprint 61 원클릭 파이프라인을 유지하면서
    ShoppingFit 다음 단계에 ViralPatternEngine을 연결합니다.

    흐름:
    ProductPlan
    → SourcePlan
    → SourceRank
    → VideoSourcing
    → RealVision
    → VideoQuality
    → ShoppingFit
    → ViralPattern
    → CandidateSelector
    → CandidateRanker
    → AutoEditor
    → CapCutExport
    """

    WORKFLOW_VERSION = "workflow-engine-194-76-history-final-common-contract"
    

    # Sprint153-2: 비용 없는 자막/음성/병합 재시험 모드입니다.
    # PowerShell 예: $env:AUTOCOMMERCE_REUSE_IMAGE_MOTION_PROJECT_ID="344"
    REUSE_IMAGE_MOTION_ENV = "AUTOCOMMERCE_REUSE_IMAGE_MOTION_PROJECT_ID"

    @classmethod
    def _resolve_reuse_image_motion_path(cls, project_id=""):
        requested_id = str(os.getenv(cls.REUSE_IMAGE_MOTION_ENV, "") or "").strip()
        if not requested_id:
            return ""

        # 숫자/문자 프로젝트 ID만 허용해 임의 경로 주입을 막습니다.
        if not re.fullmatch(r"[A-Za-z0-9_-]+", requested_id):
            print(
                "[Sprint153-2 Reuse ImageMotion] BLOCKED INVALID PROJECT ID:",
                requested_id,
                flush=True,
            )
            return ""

        candidate = Path("exports") / "videos" / f"{requested_id}_image_motion.mp4"
        if candidate.is_file() and candidate.stat().st_size > 1024:
            print("[Sprint153-2 Reuse ImageMotion] ENABLED:", str(candidate), flush=True)
            print("[Sprint153-2 Reuse ImageMotion] Current Project:", str(project_id or ""), flush=True)
            print("[Sprint153-2 Reuse ImageMotion] Gemini Image: SKIPPED", flush=True)
            print("[Sprint153-2 Reuse ImageMotion] Vision Closed Loop: SKIPPED", flush=True)
            print("[Sprint153-2 Reuse ImageMotion] ImageMotion Render: SKIPPED", flush=True)
            return str(candidate)

        print("[Sprint153-2 Reuse ImageMotion] REQUESTED BUT MISSING:", str(candidate), flush=True)
        return ""

    # Sprint102-3: 동일 프로젝트의 WorkflowEngine 중복 진입을 차단합니다.
    _RUN_GUARD = threading.RLock()
    _ACTIVE_PROJECT_KEYS = set()

    STEP_NAMES = [
        "product_plan",
        "source_plan",
        "source_rank",
        "real_vision",
        "auto_editor",
        "content_factory",
        "capcut_export",
    ]

    def steps(self):
        labels = {
            "product_plan": "상품 분석",
            "source_plan": "소스 검색 계획",
            "source_rank": "영상 후보 랭킹",
            "real_vision": "실제 영상 AI 분석",
            "auto_editor": "자동 편집 계획",
            "content_factory": "AI 콘텐츠 팩",
            "capcut_export": "CapCut 내보내기",
        }

        return [
            {
                "name": name,
                "label": labels[name],
                "status": "pending",
            }
            for name in self.STEP_NAMES
        ]

    def _project_data(self, project):
        try:
            return json.loads(
                getattr(project, "data_json", "") or "{}"
            )
        except Exception:
            return {}

    @staticmethod
    def _find_nested_value(data, keys):
        """Sprint145-21: UI/DB 저장 위치가 달라도 신뢰 입력값을 재귀적으로 찾습니다."""
        wanted = {str(key).lower() for key in keys}
        queue = [data]
        while queue:
            current = queue.pop(0)
            if isinstance(current, dict):
                for key, value in current.items():
                    if str(key).lower() in wanted and value not in (None, ""):
                        return value
                    if isinstance(value, (dict, list, tuple)):
                        queue.append(value)
            elif isinstance(current, (list, tuple)):
                queue.extend(current)
        return None

    def _sprint100_4_text_probe(self, label, value, limit=5):
        """Sprint100-4: 문자열 값과 실제 UTF-8 바이트를 함께 출력합니다."""
        print("=" * 80, flush=True)
        print(f"[Sprint101-1 Diagnostic] {label}", flush=True)

        items = value if isinstance(value, (list, tuple)) else [value]
        for index, item in enumerate(list(items)[: max(1, int(limit))]):
            print(
                f"[Sprint101-1 Diagnostic] {label}[{index}] Type:",
                type(item).__name__,
                flush=True,
            )
            print(
                f"[Sprint101-1 Diagnostic] {label}[{index}] Repr:",
                repr(item),
                flush=True,
            )
            try:
                encoded = (
                    item.encode("utf-8", errors="replace")
                    if isinstance(item, str)
                    else repr(item).encode("utf-8", errors="replace")
                )
            except Exception as exc:
                encoded = f"ENCODE_ERROR: {type(exc).__name__}: {exc}"
            print(
                f"[Sprint101-1 Diagnostic] {label}[{index}] UTF8:",
                encoded,
                flush=True,
            )
        print("=" * 80, flush=True)

    def _write_sprint100_4_debug_json(
        self,
        output_dir,
        filename,
        payload,
    ):
        """Sprint100-4: Story 디버그 데이터를 UTF-8 JSON으로 저장합니다."""
        result = {
            "ok": False,
            "status": "not_saved",
            "path": "",
            "filename": str(filename or ""),
            "errors": [],
        }

        try:
            target_dir = Path(str(output_dir or "."))
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / str(filename)

            target_path.write_text(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                ),
                encoding="utf-8",
            )

            result.update(
                {
                    "ok": True,
                    "status": "saved",
                    "path": str(target_path),
                }
            )
        except Exception as exc:
            result.update(
                {
                    "status": "save_failed",
                    "errors": [
                        f"{type(exc).__name__}: {exc}"
                    ],
                }
            )

        print(
            "[Sprint101-2 Debug JSON]",
            result.get("filename", ""),
            result.get("status", ""),
            result.get("path", ""),
            result.get("errors", []),
            flush=True,
        )
        return result

    def _build_product_image_fallback_video(
        self,
        project,
        image_paths,
        output_path,
        seconds_per_image=2.8,
        image_pool_result=None,
        image_role_result=None,
    ):
        """Sprint113-1: 리뷰·고텍스트 이미지를 제외한 Smart Motion fallback 영상을 만듭니다."""
        result = {
            "ok": False,
            "status": "not_created",
            "output_path": "",
            "image_count": 0,
            "selected_images": [],
            "rejected_images": [],
            "duplicate_images": [],
            "timeline": [],
            "motion_count": 0,
            "smart_motion_version": "smart-motion-director-111-2",
            "role_recovery_version": "role-recovery-111-2",
            "role_recovery_count": 0,
            "role_recoveries": [],
            "smart_motion_ready": False,
            "motion_plan": [],
            "motion_counts": {},
            "role_counts": {},
            "fallback_filter_version": "fallback-image-filter-113-1",
            "fallback_filter_counts": {},
            "errors": [],
        }

        def probe_size(path):
            try:
                completed = subprocess.run(
                    [
                        "ffprobe", "-v", "error",
                        "-select_streams", "v:0",
                        "-show_entries", "stream=width,height",
                        "-of", "json", str(path),
                    ],
                    capture_output=True, text=True, encoding="utf-8",
                    errors="replace", check=False,
                )
                payload = json.loads(completed.stdout or "{}")
                stream = (payload.get("streams") or [{}])[0]
                return int(stream.get("width") or 0), int(stream.get("height") or 0)
            except Exception:
                return 0, 0

        def visual_fingerprint(path):
            """경로가 달라도 같은 사진이면 같은 지문이 나오도록 축소 해시를 만듭니다."""
            if Image is None:
                try:
                    return hashlib.sha256(path.read_bytes()).hexdigest()
                except Exception:
                    return str(path.resolve()).lower()
            try:
                with Image.open(path) as image:
                    image = image.convert("L").resize((16, 16))
                    pixels = list(image.getdata())
                average = sum(pixels) / max(1, len(pixels))
                bits = "".join("1" if value >= average else "0" for value in pixels)
                return f"phash:{int(bits, 2):064x}"
            except Exception:
                try:
                    return hashlib.sha256(path.read_bytes()).hexdigest()
                except Exception:
                    return str(path.resolve()).lower()

        # Sprint113-1 Fallback Image Filter
        # Image Role Classifier의 역할·소스·텍스트 비율을 경로별로 연결합니다.
        def fallback_path_key(value):
            try:
                return str(Path(str(value)).resolve()).lower()
            except Exception:
                return str(value or "").replace("\\", "/").lower()

        fallback_image_meta = {}
        role_payload_for_filter = (
            image_role_result if isinstance(image_role_result, dict) else {}
        )
        for role_item in list(role_payload_for_filter.get("images") or []):
            if not isinstance(role_item, dict):
                continue
            role_path = str(
                role_item.get("output_path")
                or role_item.get("path")
                or role_item.get("source_path")
                or ""
            ).strip()
            if not role_path:
                continue
            fallback_image_meta[fallback_path_key(role_path)] = {
                "role": str(
                    role_item.get("image_type")
                    or role_item.get("role")
                    or "unknown"
                ).lower(),
                "source_type": str(role_item.get("source_type") or "").lower(),
                "text_like_ratio": float(role_item.get("text_like_ratio", 0) or 0),
            }

        # 중요: 분할기가 만든 순서를 그대로 보존합니다. 크기 정렬을 하지 않습니다.
        candidates = []
        rejected = []
        duplicates = []
        seen_paths = set()
        seen_fingerprints = {}

        for raw_path in image_paths or []:
            path = Path(str(raw_path or ""))
            try:
                resolved_key = str(path.resolve()).lower()
            except Exception:
                resolved_key = str(path).lower()
            if not path.is_file() or resolved_key in seen_paths:
                continue
            if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
                continue
            seen_paths.add(resolved_key)
            width, height = probe_size(path)
            if width <= 0 or height <= 0:
                rejected.append({"path": str(path), "reason": "unreadable"})
                continue

            fingerprint = visual_fingerprint(path)
            if fingerprint in seen_fingerprints:
                duplicates.append({
                    "path": str(path),
                    "same_as": seen_fingerprints[fingerprint],
                    "fingerprint": fingerprint,
                })
                continue

            # Sprint103-7 품질 필터:
            # 긴 상세페이지 스트립에서 잘린 작은 아이콘/버튼/얇은 배너 조각을 제외합니다.
            # 원본 자체가 저해상도일 수 있으므로 절대 해상도만 보지 않고
            # 최소 변 길이, 면적, 극단적인 가로세로 비율을 함께 확인합니다.
            short_side = min(width, height)
            area = width * height
            aspect = max(width / max(1, height), height / max(1, width))
            reject_reason = ""
            if short_side < 80:
                reject_reason = f"short_side_too_small:{short_side}"
            elif area < 10000:
                reject_reason = f"area_too_small:{area}"
            elif aspect > 3.0:
                reject_reason = f"extreme_aspect:{aspect:.2f}"

            if reject_reason:
                rejected.append({
                    "path": str(path),
                    "reason": reject_reason,
                    "width": width,
                    "height": height,
                })
                continue

            seen_fingerprints[fingerprint] = str(path)
            # 면적이 크고 비율이 안정적인 이미지를 우선할 수 있도록 점수를 보관합니다.
            quality_score = area / max(1.0, aspect)
            candidates.append((path, width, height, fingerprint, quality_score))

        # 고유 이미지가 너무 적으면 시각 해시가 과민했을 수 있으므로 경로 고유값 전체를 사용합니다.
        if len(candidates) < 3:
            candidates = []
            duplicates = []
            seen_paths = set()
            for raw_path in image_paths or []:
                path = Path(str(raw_path or ""))
                try:
                    key = str(path.resolve()).lower()
                except Exception:
                    key = str(path).lower()
                if (
                    path.is_file()
                    and key not in seen_paths
                    and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
                ):
                    seen_paths.add(key)
                    width, height = probe_size(path)
                    if width > 0 and height > 0:
                        candidates.append((path, width, height, visual_fingerprint(path), width * height))

        # Sprint114-1: Fallback 역할 기반 장면 선택기
        # 목표 순서: hero → usage → usage → detail → feature → cta
        # - review는 절대 사용하지 않습니다.
        # - text_like_ratio 0.12 초과 이미지는 제외합니다.
        # - 부족한 일반 장면은 hero/usage/detail/feature/unknown 순으로 보충합니다.
        # - comparison은 일반 후보가 부족할 때만 마지막 보충 후보로 사용합니다.
        # - CTA는 존재할 경우 마지막 장면 한 장만 사용합니다.
        preferred_roles = ("hero", "usage", "detail", "feature")
        role_buckets = {role: [] for role in preferred_roles}
        unknown_items = []
        comparison_items = []
        cta_items = []
        fallback_filter_counts = {
            "review_excluded": 0,
            "high_text_excluded": 0,
            "comparison_deferred": 0,
            "cta_limited": 0,
        }

        for item in candidates:
            path = item[0]
            meta = fallback_image_meta.get(fallback_path_key(path), {})
            filename = Path(str(path)).stem.lower()
            role = str(meta.get("role") or "unknown").lower()
            source_type = str(meta.get("source_type") or "").lower()
            text_like_ratio = float(meta.get("text_like_ratio", 0) or 0)

            if role == "unknown":
                for token in ("comparison", "cta", "review", "hero", "usage", "feature", "detail"):
                    if token in filename:
                        role = token
                        break

            if role == "review" or source_type == "review_image":
                fallback_filter_counts["review_excluded"] += 1
                rejected.append({
                    "path": str(path),
                    "reason": "fallback_review_excluded",
                    "role": role,
                    "source_type": source_type,
                })
                continue

            if text_like_ratio > 0.12:
                fallback_filter_counts["high_text_excluded"] += 1
                rejected.append({
                    "path": str(path),
                    "reason": f"fallback_text_like_ratio:{text_like_ratio:.4f}",
                    "role": role,
                    "text_like_ratio": text_like_ratio,
                })
                continue

            if role in role_buckets:
                role_buckets[role].append(item)
            elif role == "comparison":
                comparison_items.append(item)
            elif role == "cta":
                cta_items.append(item)
            else:
                unknown_items.append(item)

        selected_items = []
        selected_keys = set()

        def item_key(item):
            return fallback_path_key(item[0])

        def take_first(bucket):
            while bucket:
                item = bucket.pop(0)
                key = item_key(item)
                if key in selected_keys:
                    continue
                selected_keys.add(key)
                selected_items.append(item)
                return True
            return False

        # CTA를 제외한 앞쪽 5장면의 기본 역할 구조입니다.
        take_first(role_buckets["hero"])
        take_first(role_buckets["usage"])
        take_first(role_buckets["usage"])
        take_first(role_buckets["detail"])
        take_first(role_buckets["feature"])

        # 기본 역할이 부족하면 안전한 상품 이미지로 5장까지 보충합니다.
        refill_buckets = [
            role_buckets["hero"],
            role_buckets["usage"],
            role_buckets["detail"],
            role_buckets["feature"],
            unknown_items,
        ]
        for bucket in refill_buckets:
            while len(selected_items) < 5 and take_first(bucket):
                pass
            if len(selected_items) >= 5:
                break

        # comparison은 일반 후보로 5장을 채우지 못했을 때만 사용합니다.
        while len(selected_items) < 5 and take_first(comparison_items):
            pass
        fallback_filter_counts["comparison_deferred"] = len(comparison_items)

        # CTA는 반드시 마지막에 한 장만 추가합니다.
        if cta_items:
            cta_item = cta_items[-1]
            cta_key = item_key(cta_item)
            if cta_key not in selected_keys:
                selected_keys.add(cta_key)
                selected_items.append(cta_item)
            fallback_filter_counts["cta_limited"] = max(0, len(cta_items) - 1)

        # CTA가 없으면 남은 안전 후보로 최대 6장까지 채웁니다.
        if len(selected_items) < 6:
            refill_tail = [
                role_buckets["hero"],
                role_buckets["usage"],
                role_buckets["detail"],
                role_buckets["feature"],
                unknown_items,
                comparison_items,
            ]
            for bucket in refill_tail:
                while len(selected_items) < 6 and take_first(bucket):
                    pass
                if len(selected_items) >= 6:
                    break

        valid_items = selected_items[:6]
        valid_images = [item[0] for item in valid_items]
        result["fallback_filter_counts"] = fallback_filter_counts
        result["fallback_role_sequence"] = []

        for item in valid_items:
            path = item[0]
            meta = fallback_image_meta.get(fallback_path_key(path), {})
            role = str(meta.get("role") or "unknown").lower()
            filename = Path(str(path)).stem.lower()
            if role == "unknown":
                for token in ("comparison", "cta", "hero", "usage", "feature", "detail"):
                    if token in filename:
                        role = token
                        break
            result["fallback_role_sequence"].append(role)

        print("[Sprint114-1 Role Selector] Version: fallback-role-selector-114-1", flush=True)
        print("[Sprint114-1 Role Selector] Counts:", fallback_filter_counts, flush=True)
        print("[Sprint114-1 Role Selector] Selected:", len(valid_images), flush=True)
        print("[Sprint114-1 Role Selector] Sequence:", result["fallback_role_sequence"], flush=True)
        result["image_count"] = len(valid_images)
        result["selected_images"] = [str(item) for item in valid_images]
        result["rejected_images"] = rejected
        result["duplicate_images"] = duplicates

        print("[Sprint103-7 Quality Filter] Input Count:", len(list(image_paths or [])), flush=True)
        print("[Sprint103-7 Quality Filter] Unique Count:", len(valid_images), flush=True)
        print("[Sprint103-7 Quality Filter] Duplicate Count:", len(duplicates), flush=True)
        print("[Sprint103-7 Quality Filter] Rejected Count:", len(rejected), flush=True)
        for item in rejected:
            print(
                f"[Sprint103-7 Quality Filter] REJECT: {item.get('path')} "
                f"reason={item.get('reason')}",
                flush=True,
            )
        for index, (path, width, height, fingerprint, quality_score) in enumerate(valid_items, start=1):
            print(
                f"[Sprint103-7 Quality Filter] {index:02d}: {path} "
                f"({width}x{height}) score={quality_score:.0f} {fingerprint[:22]}",
                flush=True,
            )

        if not valid_images:
            result.update(
                status="skipped_no_product_images",
                errors=["No valid product images for motion fallback video"],
            )
            return result

        target = Path(str(output_path))
        target.parent.mkdir(parents=True, exist_ok=True)
        temp_dir = target.parent / f".{target.stem}_motion_parts"
        shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(parents=True, exist_ok=True)
        concat_path = temp_dir / "concat.txt"
        duration = max(1.8, float(seconds_per_image or 2.8))
        fps = 30
        frame_count = max(54, int(duration * fps))
        fade_duration = min(0.28, duration / 6.0)
        segment_paths = []

        # Sprint111-1 Smart Motion Director
        # Image Pool 역할을 경로 기준으로 연결하고, 동일 모션의 연속 사용을 막습니다.
        motion_library = {
            "slow_zoom_in": f"zoompan=z='min(zoom+0.00018,1.022)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frame_count}:s=1080x1920:fps={fps}",
            "slow_zoom_out": f"zoompan=z='if(eq(on,0),1.022,max(1.0,zoom-0.00018))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frame_count}:s=1080x1920:fps={fps}",
            "pan_left_to_right": f"zoompan=z='1.014':x='(iw-iw/zoom)*0.38+(iw-iw/zoom)*0.24*on/{max(1, frame_count-1)}':y='ih/2-(ih/zoom/2)':d={frame_count}:s=1080x1920:fps={fps}",
            "pan_right_to_left": f"zoompan=z='1.014':x='(iw-iw/zoom)*0.62-(iw-iw/zoom)*0.24*on/{max(1, frame_count-1)}':y='ih/2-(ih/zoom/2)':d={frame_count}:s=1080x1920:fps={fps}",
            "micro_zoom": f"zoompan=z='min(zoom+0.00011,1.014)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frame_count}:s=1080x1920:fps={fps}",
            "strong_push_in": f"zoompan=z='min(zoom+0.00032,1.038)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frame_count}:s=1080x1920:fps={fps}",
            "gentle_hold": f"zoompan=z='1.006':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frame_count}:s=1080x1920:fps={fps}",
        }
        role_motion_preferences = {
            "hero": ["slow_zoom_in", "slow_zoom_out", "strong_push_in"],
            "usage": ["pan_left_to_right", "pan_right_to_left", "slow_zoom_in"],
            "detail": ["micro_zoom", "slow_zoom_in", "gentle_hold"],
            "feature": ["strong_push_in", "micro_zoom", "pan_left_to_right"],
            "review": ["gentle_hold", "slow_zoom_in", "slow_zoom_out"],
            "comparison": ["pan_right_to_left", "pan_left_to_right", "gentle_hold"],
            "cta": ["strong_push_in", "slow_zoom_in", "gentle_hold"],
            "unknown": ["slow_zoom_in", "slow_zoom_out", "pan_left_to_right", "pan_right_to_left"],
        }

        def normalize_path_key(value):
            try:
                return str(Path(str(value)).resolve()).lower()
            except Exception:
                return str(value or "").replace("\\", "/").lower()

        path_role_scores = {}
        pool_payload = image_pool_result if isinstance(image_pool_result, dict) else {}
        for role_name, role_items in (pool_payload.get("image_pool") or {}).items():
            for role_item in list(role_items or []):
                if not isinstance(role_item, dict):
                    continue
                role_path = str(role_item.get("path") or role_item.get("output_path") or "").strip()
                if not role_path:
                    continue
                key = normalize_path_key(role_path)
                score = float(role_item.get("score", 0) or 0)
                if key not in path_role_scores or score >= path_role_scores[key][1]:
                    path_role_scores[key] = (str(role_name or "unknown").lower(), score)

        role_payload = image_role_result if isinstance(image_role_result, dict) else {}
        for role_item in list(role_payload.get("images") or []):
            if not isinstance(role_item, dict):
                continue
            role_path = str(role_item.get("output_path") or role_item.get("path") or "").strip()
            role_name = str(role_item.get("image_type") or role_item.get("role") or "unknown").lower()
            if role_path and normalize_path_key(role_path) not in path_role_scores:
                path_role_scores[normalize_path_key(role_path)] = (role_name, float(role_item.get("score", 0) or 0))

        # Sprint111-2 Role Recovery
        # selected_07_comparison.png처럼 파일명에 명확한 역할이 있으면
        # 이전 분류 결과가 detail/unknown이어도 안전하게 복구합니다.
        filename_role_tokens = (
            "comparison", "cta", "review", "hero", "usage", "feature", "detail"
        )

        def infer_filename_role(value):
            filename = Path(str(value or "")).stem.lower()
            normalized = filename.replace("-", "_").replace(" ", "_")
            for token in filename_role_tokens:
                if token in normalized:
                    return token
            return ""

        motion_plan = []
        previous_motion = ""
        for index, image_path in enumerate(valid_images):
            original_role, role_score = path_role_scores.get(
                normalize_path_key(image_path), ("unknown", 0.0)
            )
            role = str(original_role or "unknown").lower()
            filename_role = infer_filename_role(image_path)
            recovery_reason = ""

            if filename_role and filename_role != role:
                # 명시적 파일명은 최종 선택 단계에서 부여된 역할이므로 우선합니다.
                role = filename_role
                recovery_reason = f"filename({filename_role})"
                recovery_item = {
                    "scene": index + 1,
                    "image": str(image_path),
                    "original_role": str(original_role or "unknown").lower(),
                    "recovered_role": role,
                    "reason": recovery_reason,
                }
                result["role_recoveries"].append(recovery_item)
                print(
                    f"[Sprint111-2 Role Recovery] Scene{index + 1:02d} "
                    f"original={recovery_item['original_role']} "
                    f"recovered={role} reason={recovery_reason}",
                    flush=True,
                )

            preferences = list(role_motion_preferences.get(role, role_motion_preferences["unknown"]))
            selected_motion = next((name for name in preferences if name != previous_motion), preferences[0])
            reason_parts = [
                f"role={role}",
                f"consecutive_motion_avoided={selected_motion != previous_motion}",
            ]
            if recovery_reason:
                reason_parts.append(f"role_recovered={recovery_reason}")
            motion_plan.append({
                "scene": index + 1,
                "image": str(image_path),
                "role": role,
                "original_role": str(original_role or "unknown").lower(),
                "role_score": role_score,
                "motion": selected_motion,
                "reason": "; ".join(reason_parts),
            })
            previous_motion = selected_motion

        result["role_recovery_count"] = len(result["role_recoveries"])
        print("[Sprint111-2 Role Recovery] Version: role-recovery-111-2", flush=True)
        print("[Sprint111-2 Role Recovery] Recovered:", result["role_recovery_count"], flush=True)

        result["motion_plan"] = motion_plan
        result["smart_motion_ready"] = bool(motion_plan)
        for plan_item in motion_plan:
            motion_name = plan_item["motion"]
            role_name = plan_item["role"]
            result["motion_counts"][motion_name] = result["motion_counts"].get(motion_name, 0) + 1
            result["role_counts"][role_name] = result["role_counts"].get(role_name, 0) + 1
            print(
                f"[Sprint111-2 Smart Motion Director] Scene{plan_item['scene']:02d} "
                f"role={role_name} motion={motion_name} image={plan_item['image']}",
                flush=True,
            )
        print("[Sprint111-2 Smart Motion Director] Version: smart-motion-director-111-2", flush=True)
        print("[Sprint111-2 Smart Motion Director] Ready:", result["smart_motion_ready"], flush=True)
        print("[Sprint111-2 Smart Motion Director] Role Counts:", result["role_counts"], flush=True)
        print("[Sprint111-2 Smart Motion Director] Motion Counts:", result["motion_counts"], flush=True)

        try:
            for index, image_path in enumerate(valid_images):
                segment_path = temp_dir / f"segment_{index + 1:02d}.mp4"
                plan_item = motion_plan[index]
                motion_name = plan_item.get("motion", "slow_zoom_in")
                motion = motion_library[motion_name]
                # 전경 이미지는 비율을 보존하고, 배경만 화면 전체로 채웁니다.
                filter_complex = (
                    "split=2[bg][fg];"
                    "[bg]scale=1080:1920:force_original_aspect_ratio=increase,"
                    "crop=1080:1920,gblur=sigma=24,eq=brightness=-0.06:saturation=0.82[bg2];"
                    "[fg]scale=972:1728:force_original_aspect_ratio=decrease[fg2];"
                    "[bg2][fg2]overlay=(W-w)/2:(H-h)/2,"
                    f"{motion},setsar=1,"
                    f"fade=t=in:st=0:d={fade_duration:.3f},"
                    f"fade=t=out:st={max(0.0, duration-fade_duration):.3f}:d={fade_duration:.3f},"
                    "format=yuv420p"
                )
                command = [
                    "ffmpeg", "-y", "-loop", "1", "-i", str(image_path),
                    "-t", f"{duration:.3f}", "-vf", filter_complex,
                    "-an", "-r", str(fps), "-c:v", "libx264",
                    "-preset", "medium", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    str(segment_path),
                ]
                completed = subprocess.run(
                    command, capture_output=True, text=True, encoding="utf-8",
                    errors="replace", check=False,
                )
                if completed.returncode != 0 or not segment_path.is_file():
                    result["errors"].append(
                        f"segment_{index + 1:02d}: "
                        + (completed.stderr or completed.stdout or "ffmpeg failed")[-1200:]
                    )
                    continue
                segment_paths.append(segment_path)
                timeline_item = {
                    "scene": index + 1,
                    "image": str(image_path),
                    "segment": str(segment_path),
                    "role": plan_item.get("role", "unknown"),
                    "motion": motion_name,
                    "motion_reason": plan_item.get("reason", ""),
                }
                result["timeline"].append(timeline_item)
                print(
                    f"[Sprint103-7 Timeline] Scene{index + 1:02d} -> {image_path}",
                    flush=True,
                )

            if not segment_paths:
                result["status"] = "ffmpeg_segments_failed"
                return result

            def concat_quote(path):
                normalized = str(path.resolve()).replace("\\", "/")
                return normalized.replace("'", "'\\''")

            concat_path.write_text(
                "\n".join(f"file '{concat_quote(path)}'" for path in segment_paths) + "\n",
                encoding="utf-8",
            )
            merged = subprocess.run(
                [
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                    "-i", str(concat_path), "-c", "copy",
                    "-movflags", "+faststart", str(target),
                ],
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", check=False,
            )
            if merged.returncode != 0 or not target.is_file():
                result.update(
                    status="ffmpeg_merge_failed",
                    errors=result["errors"] + [
                        (merged.stderr or merged.stdout or "ffmpeg merge failed")[-2000:]
                    ],
                )
                return result

            project_id = str(getattr(project, "id", "") or "")
            if project_id and project_id not in target.name:
                target.unlink(missing_ok=True)
                result.update(
                    status="blocked_project_mismatch",
                    errors=[f"Fallback path does not contain project id {project_id}: {target}"],
                )
                return result

            result.update(
                ok=True, status="motion_created", output_path=str(target),
                motion_count=len(segment_paths), errors=result["errors"],
            )
            return result
        except Exception as exc:
            result.update(
                status="exception",
                errors=result["errors"] + [f"{type(exc).__name__}: {exc}"],
            )
            return result
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _normalize_youtube_privacy_status(self, value):
        """YouTube 공개 설정을 API 허용값으로 통일합니다."""
        normalized = str(value or "private").strip().lower()
        if normalized not in {"private", "unlisted", "public"}:
            return "private"
        return normalized

    def auto_connect_latest_download(self, project):
        resolver = VideoPathResolver()
        current_video = resolver.resolve_path(project)

        print(
            "[AUTO] current_video =",
            current_video,
            flush=True,
        )

        if current_video and resolver.exists(current_video):
            return {
                "ok": False,
                "message": "이미 연결된 영상이 있습니다.",
                "video_path": current_video,
            }

        latest = latest_downloaded_video()

        print(
            "[AUTO] latest =",
            latest,
            flush=True,
        )

        if not latest:
            return {
                "ok": False,
                "message": "Downloads 최신 영상 없음",
                "video_path": "",
            }

        out_dir = project_source_video_dir(project)
        out_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        project_name = safe_file_name(
            getattr(project, "product_name", "")
            or getattr(project, "title", "")
            or "product"
        )

        suffix = latest.suffix.lower() or ".mp4"
        target = out_dir / f"{project_name}_latest{suffix}"

        try:
            if latest.resolve() != target.resolve():
                shutil.copy2(latest, target)
        except Exception:
            shutil.copy2(latest, target)

        try:
            ProjectRepository().update_links_and_media(
                getattr(project, "id"),
                video_path=str(target),
            )
        except Exception as exc:
            print(
                "[AUTO] ProjectRepository update ERROR:",
                repr(exc),
                flush=True,
            )
            return {
                "ok": False,
                "message": str(exc),
                "video_path": str(target),
            }

        return {
            "ok": True,
            "message": "Downloads 최신 영상을 자동 연결했습니다.",
            "video_path": str(target),
        }

    def _review_image_paths(
        self,
        project,
        project_data,
        supplied_paths=None,
    ):
        """UI와 프로젝트 데이터에 저장된 리뷰 이미지 경로를 모읍니다."""
        candidates = []

        if isinstance(supplied_paths, (str, Path)):
            candidates.append(supplied_paths)
        elif isinstance(supplied_paths, (list, tuple, set)):
            candidates.extend(supplied_paths)

        source_dicts = [
            project_data if isinstance(project_data, dict) else {},
        ]

        for nested_key in (
            "review_image_upload",
            "review_upload",
            "review_ocr",
            "media",
        ):
            nested = project_data.get(nested_key)
            if isinstance(nested, dict):
                source_dicts.append(nested)

        keys = (
            "review_image_paths",
            "review_images",
            "uploaded_review_images",
            "review_upload_paths",
            "review_image_files",
            "review_image_path",
            "review_image",
        )

        for source in source_dicts:
            for key in keys:
                value = source.get(key)
                if isinstance(value, (str, Path)):
                    candidates.append(value)
                elif isinstance(value, (list, tuple, set)):
                    candidates.extend(value)

        for key in keys:
            value = getattr(project, key, None)
            if isinstance(value, (str, Path)):
                candidates.append(value)
            elif isinstance(value, (list, tuple, set)):
                candidates.extend(value)

        paths = []
        seen = set()
        supported = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

        for item in candidates:
            if isinstance(item, dict):
                item = (
                    item.get("path")
                    or item.get("file_path")
                    or item.get("image_path")
                    or item.get("saved_path")
                )

            if not item:
                continue

            path = Path(str(item)).expanduser()

            if path.is_dir():
                expanded = [
                    child
                    for child in sorted(path.iterdir())
                    if child.is_file()
                    and child.suffix.lower() in supported
                ]
            else:
                expanded = [path]

            for image_path in expanded:
                normalized = str(image_path)
                dedupe_key = normalized.lower()

                if dedupe_key in seen:
                    continue
                if image_path.suffix.lower() not in supported:
                    continue
                if not image_path.exists():
                    print(
                        "[Sprint71-2] Review image missing:",
                        normalized,
                        flush=True,
                    )
                    continue

                seen.add(dedupe_key)
                paths.append(normalized)

        return paths

    def _normalize_reviews(self, value, source="unknown"):
        """리뷰를 ContentFactory와 ReviewInsight용 딕셔너리 목록으로 통일합니다."""
        if value is None:
            return []

        if isinstance(value, str):
            value = [value]
        elif isinstance(value, dict):
            for key in (
                "reviews",
                "review_data",
                "items",
                "results",
                "texts",
                "ocr_reviews",
                "data",
            ):
                nested = value.get(key)
                if isinstance(nested, (list, tuple)):
                    value = nested
                    break
            else:
                value = [value]

        if not isinstance(value, (list, tuple, set)):
            return []

        normalized = []

        for item in value:
            if isinstance(item, str):
                content = item.strip()
                if content:
                    normalized.append(
                        {
                            "content": content,
                            "text": content,
                            "review_text": content,
                            "source": source,
                        }
                    )
                continue

            if not isinstance(item, dict):
                continue

            copied = dict(item)
            content = (
                copied.get("content")
                or copied.get("review_text")
                or copied.get("text")
                or copied.get("body")
                or copied.get("comment")
                or copied.get("ocr_text")
                or ""
            )
            content = str(content).strip()

            if not content:
                continue

            copied.setdefault("content", content)
            copied.setdefault("text", content)
            copied.setdefault("review_text", content)
            copied.setdefault("source", source)
            normalized.append(copied)

        return normalized

    def _parse_manual_review_text(self, value):
        """Sprint115-1: 붙여넣은 한글 리뷰·댓글을 리뷰 객체 목록으로 변환합니다."""
        text = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
        if not text:
            return []

        # 빈 줄을 기본 리뷰 구분자로 사용합니다.
        raw_blocks = [block.strip() for block in re.split(r"\n\s*\n+", text) if block.strip()]
        reviews = []

        for block in raw_blocks:
            lines = [line.strip() for line in block.split("\n") if line.strip()]
            cleaned_lines = []
            for line in lines:
                # 별점만 있는 줄은 메타데이터이므로 본문에서 제외합니다.
                if re.fullmatch(r"[★☆⭐\s]{1,10}", line):
                    continue
                line = re.sub(r"^\s*(?:[-•·]|\d+[.)])\s*", "", line).strip()
                if line:
                    cleaned_lines.append(line)

            content = " ".join(cleaned_lines).strip()
            if content:
                reviews.append(
                    {
                        "content": content,
                        "text": content,
                        "review_text": content,
                        "source": "manual_review_text",
                    }
                )

        # 빈 줄 없이 한 줄씩 붙여넣은 댓글 목록도 지원합니다.
        if len(reviews) <= 1 and len(raw_blocks) == 1:
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            non_rating_lines = [
                re.sub(r"^\s*(?:[-•·]|\d+[.)])\s*", "", line).strip()
                for line in lines
                if not re.fullmatch(r"[★☆⭐\s]{1,10}", line)
            ]
            non_rating_lines = [line for line in non_rating_lines if line]
            if len(non_rating_lines) >= 2:
                reviews = [
                    {
                        "content": line,
                        "text": line,
                        "review_text": line,
                        "source": "manual_review_text",
                    }
                    for line in non_rating_lines
                ]

        return self._merge_reviews(reviews)

    def _merge_reviews(self, *review_groups):
        """리뷰 본문 기준으로 중복을 제거하며 순서를 보존합니다."""
        merged = []
        seen = set()

        for group in review_groups:
            for item in self._normalize_reviews(group):
                content = str(
                    item.get("content")
                    or item.get("review_text")
                    or item.get("text")
                    or ""
                ).strip()
                key = " ".join(content.lower().split())

                if not key or key in seen:
                    continue

                seen.add(key)
                merged.append(item)

        return merged

    def _run_review_image_ocr(self, image_paths, project, multi_image_mode=False):
        """설치된 ReviewImageOCR 공개 메서드를 찾아 안전하게 실행합니다."""
        result = {
            "ok": False,
            "status": "bypassed_multi_image" if multi_image_mode else "not_run",
            "image_count": len(image_paths),
            "review_count": 0,
            "image_paths": list(image_paths),
            "reviews": [],
        }

        if not image_paths:
            result["status"] = "no_images"
            return result

        if ReviewImageOCR is None:
            result.update(
                status="import_failed",
                error="ReviewImageOCR import 실패",
            )
            return result

        try:
            engine = ReviewImageOCR()
        except Exception as exc:
            result.update(
                status="init_failed",
                error=str(exc),
            )
            return result

        last_error = None

        for method_name in (
            "extract_reviews",
            "extract_many",
            "analyze",
            "extract",
            "run",
            "process",
            "collect",
            "read",
        ):
            method = getattr(engine, method_name, None)

            if not callable(method):
                continue

            call_patterns = (
                lambda: method(
                    image_paths=image_paths,
                    project_id=getattr(project, "id", ""),
                ),
                lambda: method(paths=image_paths),
                lambda: method(image_paths=image_paths),
                lambda: method(image_paths),
            )

            for call in call_patterns:
                try:
                    raw = call()
                    reviews = self._normalize_reviews(
                        raw,
                        source="review_image_ocr",
                    )
                    result.update(
                        {
                            "ok": bool(reviews),
                            "status": (
                                "collected"
                                if reviews
                                else "empty"
                            ),
                            "method": method_name,
                            "review_count": len(reviews),
                            "reviews": reviews,
                            "raw_result": raw,
                        }
                    )
                    return result
                except TypeError as exc:
                    last_error = exc
                    continue
                except Exception as exc:
                    result.update(
                        status="failed",
                        method=method_name,
                        error=str(exc),
                    )
                    return result

        result.update(
            status="method_not_found",
            error=(
                str(last_error)
                if last_error
                else "ReviewImageOCR 실행 메서드를 찾지 못했습니다."
            ),
        )
        return result

    def _build_youtube_upload_summary(self, upload_result):
        """YouTube 업로드 결과를 저장과 UI에 필요한 핵심 정보로 정리합니다."""
        source = upload_result if isinstance(upload_result, dict) else {}

        video_id = str(source.get("video_id") or "").strip()
        watch_url = str(source.get("watch_url") or "").strip()

        if video_id and not watch_url:
            watch_url = (
                "https://www.youtube.com/watch?v="
                f"{video_id}"
            )

        return {
            "ok": bool(source.get("ok")),
            "version": str(
                source.get("version")
                or "youtube-upload-executor-83-2"
            ),
            "status": str(source.get("status") or "unknown"),
            "platform": str(
                source.get("platform")
                or "youtube_shorts"
            ),
            "video_id": video_id,
            "watch_url": watch_url,
            "uploaded_at": str(source.get("uploaded_at") or ""),
            "actual_upload_performed": bool(
                source.get("actual_upload_performed")
            ),
            "upload_ready": bool(source.get("upload_ready")),
            "dry_run": bool(source.get("dry_run")),
            "errors": list(source.get("errors") or []),
            "warnings": list(source.get("warnings") or []),
        }

    def _build_instagram_upload_summary(self, upload_result):
        """Instagram 업로드 결과를 저장과 UI에 필요한 핵심 정보로 정리합니다."""
        source = upload_result if isinstance(upload_result, dict) else {}
        return {
            "ok": bool(source.get("ok")),
            "version": str(
                source.get("version")
                or "instagram-playwright-upload-executor-90-2"
            ),
            "status": str(source.get("status") or "unknown"),
            "platform": str(source.get("platform") or "instagram_reels"),
            "post_url": str(source.get("post_url") or "").strip(),
            "final_url": str(source.get("final_url") or "").strip(),
            "uploaded_at": str(source.get("uploaded_at") or ""),
            "actual_upload_performed": bool(
                source.get("actual_upload_performed")
            ),
            "upload_ready": bool(source.get("upload_ready")),
            "dry_run": bool(source.get("dry_run")),
            "errors": list(source.get("errors") or []),
            "warnings": list(source.get("warnings") or []),
        }

    def _persist_instagram_upload_metadata(
        self,
        publisher_store_result,
        instagram_summary,
    ):
        """Publisher manifest.json에 Instagram 업로드 메타데이터를 저장합니다."""
        store = publisher_store_result if isinstance(publisher_store_result, dict) else {}
        summary = instagram_summary if isinstance(instagram_summary, dict) else {}
        manifest_path = str(store.get("manifest_path") or "").strip()
        result = {
            "ok": False,
            "version": "instagram-manifest-store-90-2",
            "status": "not_saved",
            "manifest_path": manifest_path,
            "post_url": str(summary.get("post_url") or ""),
            "uploaded_at": str(summary.get("uploaded_at") or ""),
        }
        if not manifest_path:
            result["status"] = "manifest_path_missing"
            result["error"] = "publisher manifest_path가 없습니다"
            return result
        path = Path(manifest_path)
        if not path.is_file():
            result["status"] = "manifest_missing"
            result["error"] = f"manifest 파일이 없습니다: {path}"
            return result
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(manifest, dict):
                manifest = {"original_manifest": manifest}
            manifest["instagram"] = dict(summary)
            path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )
            result.update({"ok": True, "status": "saved", "manifest_path": str(path)})
        except Exception as exc:
            result["status"] = "save_failed"
            result["error"] = str(exc)
        return result

    def _update_instagram_project(self, project, summary, manifest_result):
        """Repository 지원 시 Instagram 결과를 Project DB에 저장합니다."""
        repository = ProjectRepository()
        method = getattr(repository, "update_instagram_upload", None)
        if not callable(method):
            return {
                "ok": False,
                "version": "project-repository-90-2",
                "status": "method_missing",
                "project_id": getattr(project, "id", ""),
                "post_url": str(summary.get("post_url") or ""),
                "uploaded_at": str(summary.get("uploaded_at") or ""),
                "manifest_path": str(manifest_result.get("manifest_path") or ""),
                "warning": "ProjectRepository.update_instagram_upload 메서드가 없습니다",
            }
        try:
            return method(
                project_id=getattr(project, "id", ""),
                upload_result=summary,
                manifest_result=manifest_result,
            )
        except Exception as exc:
            return {
                "ok": False,
                "version": "project-repository-90-2",
                "status": "save_failed",
                "project_id": getattr(project, "id", ""),
                "error": str(exc),
            }

    def _persist_youtube_upload_metadata(
        self,
        publisher_store_result,
        youtube_summary,
    ):
        """Publisher manifest.json에 YouTube 업로드 메타데이터를 저장합니다."""
        store = (
            publisher_store_result
            if isinstance(publisher_store_result, dict)
            else {}
        )
        summary = (
            youtube_summary
            if isinstance(youtube_summary, dict)
            else {}
        )

        manifest_path = str(store.get("manifest_path") or "").strip()
        result = {
            "ok": False,
            "version": "youtube-manifest-store-85-1",
            "status": "not_saved",
            "manifest_path": manifest_path,
            "video_id": str(summary.get("video_id") or ""),
            "watch_url": str(summary.get("watch_url") or ""),
            "uploaded_at": str(summary.get("uploaded_at") or ""),
        }

        if not manifest_path:
            result["status"] = "manifest_path_missing"
            result["error"] = "publisher manifest_path가 없습니다"
            return result

        path = Path(manifest_path)

        if not path.is_file():
            result["status"] = "manifest_missing"
            result["error"] = f"manifest 파일이 없습니다: {path}"
            return result

        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))

            if not isinstance(manifest, dict):
                manifest = {
                    "original_manifest": manifest,
                }

            manifest["youtube"] = dict(summary)

            path.write_text(
                json.dumps(
                    manifest,
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                ),
                encoding="utf-8",
            )

            result.update(
                {
                    "ok": True,
                    "status": "saved",
                    "manifest_path": str(path),
                }
            )
            return result

        except Exception as exc:
            result["status"] = "save_failed"
            result["error"] = str(exc)
            return result

    def _resolve_product_image_path(
        self,
        project,
        project_data,
        supplied_path="",
    ):
        """UI 입력과 프로젝트 데이터에서 실제 상품 대표 이미지를 찾습니다."""
        candidates = [supplied_path]

        if isinstance(project_data, dict):
            for key in (
                "product_image_path",
                "reference_image_path",
                "image_path",
                "main_image_path",
            ):
                candidates.append(project_data.get(key))

        for key in (
            "product_image_path",
            "reference_image_path",
            "image_path",
            "main_image_path",
        ):
            candidates.append(getattr(project, key, None))

        project_id = getattr(project, "id", "")
        folder = Path("assets") / "products" / f"project_{project_id}"
        if folder.exists():
            candidates.extend([
                folder / "main.jpg",
                folder / "main.jpeg",
                folder / "main.png",
                folder / "main.webp",
            ])

        supported = {".jpg", ".jpeg", ".png", ".webp"}
        for value in candidates:
            if not value:
                continue
            path = Path(str(value)).expanduser()
            if path.is_file() and path.suffix.lower() in supported:
                return str(path)
        return ""

    def _product_image_paths(
        self,
        project,
        project_data,
        supplied_paths=None,
        supplied_path="",
    ):
        """UI 업로드와 프로젝트 폴더에서 상품/상세 이미지 경로를 모읍니다."""
        candidates = []

        if isinstance(supplied_paths, (str, Path)):
            candidates.append(supplied_paths)
        elif isinstance(supplied_paths, (list, tuple, set)):
            candidates.extend(supplied_paths)

        if supplied_path:
            candidates.append(supplied_path)

        source_dicts = [
            project_data if isinstance(project_data, dict) else {},
        ]
        for nested_key in (
            "product_image_upload",
            "product_upload",
            "manual_images",
            "media",
        ):
            nested = project_data.get(nested_key)
            if isinstance(nested, dict):
                source_dicts.append(nested)

        keys = (
            "product_image_paths",
            "product_images",
            "uploaded_product_images",
            "detail_image_paths",
            "product_image_path",
            "reference_image_path",
            "image_path",
            "main_image_path",
        )

        for source in source_dicts:
            for key in keys:
                value = source.get(key)
                if isinstance(value, (str, Path)):
                    candidates.append(value)
                elif isinstance(value, (list, tuple, set)):
                    candidates.extend(value)

        for key in keys:
            value = getattr(project, key, None)
            if isinstance(value, (str, Path)):
                candidates.append(value)
            elif isinstance(value, (list, tuple, set)):
                candidates.extend(value)

        project_id = getattr(project, "id", "")
        folder = Path("assets") / "products" / f"project_{project_id}"
        if folder.exists():
            candidates.append(folder)

        paths = []
        seen = set()
        supported = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

        for item in candidates:
            if isinstance(item, dict):
                item = (
                    item.get("path")
                    or item.get("file_path")
                    or item.get("image_path")
                    or item.get("saved_path")
                )
            if not item:
                continue

            path = Path(str(item)).expanduser()
            if path.is_dir():
                expanded = [
                    child
                    for child in sorted(path.iterdir())
                    if child.is_file()
                    and child.suffix.lower() in supported
                ]
            else:
                expanded = [path]

            for image_path in expanded:
                if not image_path.exists() or not image_path.is_file():
                    continue
                if image_path.suffix.lower() not in supported:
                    continue
                key = str(image_path.resolve()).lower()
                if key in seen:
                    continue
                seen.add(key)
                paths.append(str(image_path))

        return paths

    def _build_manual_product_image_result(
        self,
        image_paths,
        project,
    ):
        """수동 업로드 이미지를 Sprint93 이미지 manifest 형식으로 변환합니다."""
        project_id = getattr(project, "id", "")
        product_name = (
            getattr(project, "product_name", "")
            or getattr(project, "title", "")
            or "선택 상품"
        )
        output_dir = Path("assets") / "products" / f"project_{project_id}"
        output_dir.mkdir(parents=True, exist_ok=True)

        images = []
        warnings = []
        for index, value in enumerate(image_paths):
            path = Path(str(value))
            try:
                data = path.read_bytes()
                image_type = "main" if index == 0 else "detail"
                content_type = (
                    mimetypes.guess_type(path.name)[0]
                    or "image/jpeg"
                )
                images.append(
                    {
                        "index": index,
                        "type": image_type,
                        "url": "",
                        "path": str(path),
                        "filename": path.name,
                        "extension": path.suffix.lower(),
                        "content_type": content_type,
                        "size_bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest(),
                        "source": "manual_upload",
                        "priority": 1000 - index,
                        "original_type": image_type,
                    }
                )
            except Exception as exc:
                warnings.append(
                    f"수동 이미지 읽기 실패: {path} | "
                    f"{type(exc).__name__}: {exc}"
                )

        result = {
            "ok": bool(images),
            "ready": bool(images),
            "version": "manual-image-input-94-1",
            "status": "manual_images_ready" if images else "no_manual_images",
            "source": "manual_upload",
            "coupang_url": str(getattr(project, "coupang_url", "") or ""),
            "project_id": str(project_id or ""),
            "product_name": str(product_name),
            "output_dir": str(output_dir),
            "manifest_path": str(output_dir / "manifest.json"),
            "image_count": len(images),
            "main_image_count": 1 if images else 0,
            "detail_image_count": max(0, len(images) - 1),
            "candidate_count": len(images),
            "download_failed_count": 0,
            "images": images,
            "warnings": warnings,
            "errors": [],
            "pipeline_action": "skip_multi_image_collector",
        }
        Path(result["manifest_path"]).write_text(
            json.dumps(result, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        return result

    def _generate_ai_product_video(
        self,
        project,
        product_image_path,
    ):
        """대표 이미지 한 장으로 상품별 6장면을 계획하고 Veo로 순차 생성합니다."""
        base_result = {
            "ok": False,
            "ready": False,
            "status": "not_run",
            "engine_version": AIVideoEngine.VERSION,
            "provider_version": GeminiVeoProvider.VERSION,
            "product_image_path": str(product_image_path or ""),
            "scene_plan": {},
            "scene_count": 0,
            "generated_files": [],
            "selected_video_path": "",
            "errors": [],
        }

        if not product_image_path:
            base_result["status"] = "product_image_missing"
            return base_result

        product_name = (
            getattr(project, "product_name", "")
            or getattr(project, "title", "")
            or "선택 상품"
        )
        project_id = getattr(project, "id", "")
        product_context = " ".join(
            str(value or "").strip()
            for value in (
                getattr(project, "category", ""),
                getattr(project, "keyword", ""),
            )
            if str(value or "").strip()
        )

        provider = GeminiVeoProvider()
        engine = AIVideoEngine(providers={"gemini_veo": provider})
        scene_plan = engine.plan_multi_scenes(
            product_name=product_name,
            reference_image_path=str(product_image_path),
            scene_count=6,
            product_context=product_context,
        )

        print(
            "[Sprint92-5 AI Director] Category:",
            getattr(project, "category", "") or "general",
            flush=True,
        )
        print(
            "[Sprint92-5 AI Director] Scene Count:",
            len(scene_plan),
            flush=True,
        )
        for scene in scene_plan:
            print(
                "[Sprint92-5 AI Director] Scene:",
                scene.get("scene_id", ""),
                (scene.get("metadata") or {}).get("scene_type", ""),
                flush=True,
            )

        if not scene_plan:
            base_result.update(
                status="scene_plan_failed",
                scene_plan=[],
                errors=["AI scene plan is empty"],
            )
            return base_result

        request = engine.build_request(
            project_id=project_id,
            product_name=product_name,
            provider="gemini_veo",
            aspect_ratio="9:16",
            scenes=scene_plan,
            reference_images=[str(product_image_path)] * len(scene_plan),
            metadata={
                "sprint": "92-5",
                "source": "one_click_product_image",
                "mode": "multi_scene_product_director",
                "product_category": getattr(project, "category", "") or "general",
            },
        )
        save_result = engine.save_request(request)
        result = engine.generate(request, dry_run=False)
        result["request_saved"] = save_result
        result["product_image_path"] = str(product_image_path)
        result["scene_plan"] = scene_plan
        result["planned_scene_count"] = len(scene_plan)
        generated_files = list(result.get("generated_files") or [])
        result["generated_scene_count"] = len(generated_files)

        provider_result = result.get("provider_result") or {}
        if not isinstance(provider_result, dict):
            provider_result = {}

        scene_results = provider_result.get("scene_results") or []
        if not isinstance(scene_results, list):
            scene_results = []

        provider_errors = list(provider_result.get("errors") or [])
        result["provider_scene_results"] = scene_results
        result["provider_errors"] = provider_errors

        print(
            "[Sprint92-5 AI Video] Engine Status:",
            result.get("status", ""),
            flush=True,
        )
        print(
            "[Sprint92-5 AI Video] Provider Status:",
            provider_result.get("status", ""),
            flush=True,
        )
        print(
            "[Sprint92-5 AI Video] Provider Errors:",
            provider_errors,
            flush=True,
        )
        print(
            "[Sprint92-5 AI Video] Provider Scene Results:",
            len(scene_results),
            flush=True,
        )
        for scene_result in scene_results:
            if not isinstance(scene_result, dict):
                continue
            print(
                "[Sprint92-5 Scene]",
                scene_result.get("scene_id", ""),
                "Status:",
                scene_result.get("status", ""),
                "Output:",
                scene_result.get("output_path", ""),
                "Errors:",
                scene_result.get("errors", []),
                flush=True,
            )

        merger_result = AISceneMerger().merge(generated_files)
        result["scene_merger"] = merger_result
        result["merged_video_path"] = str(
            merger_result.get("output_path") or ""
        )

        print(
            "[Sprint92-2 Merger] Version:",
            merger_result.get("version", AISceneMerger.VERSION),
            flush=True,
        )
        print(
            "[Sprint92-2 Merger] Scene Files:",
            merger_result.get("scene_count", 0),
            flush=True,
        )
        print(
            "[Sprint92-2 Merger] Status:",
            merger_result.get("status", ""),
            flush=True,
        )
        print(
            "[Sprint92-2 Merger] Output:",
            merger_result.get("output_path", ""),
            flush=True,
        )
        print(
            "[Sprint92-2 Merger] Errors:",
            merger_result.get("errors", []),
            flush=True,
        )

        selected_video_path = str(
            merger_result.get("output_path")
            if merger_result.get("ok")
            else (generated_files[0] if generated_files else "")
        )
        result["selected_video_path"] = selected_video_path
        result["merge_fallback_used"] = bool(
            generated_files and not merger_result.get("ok")
        )

        if selected_video_path:
            try:
                ProjectRepository().update_links_and_media(
                    getattr(project, "id"),
                    video_path=selected_video_path,
                )
                project.video_path = selected_video_path
                result["project_video_updated"] = True
            except Exception as exc:
                result["project_video_updated"] = False
                result.setdefault("warnings", []).append(
                    f"Project video_path update failed: {type(exc).__name__}: {exc}"
                )

        return result



    def _sprint151_1_apply_product_dna_2(self, director_result, product_identity_context):
        if not isinstance(director_result, dict):
            return director_result

        context = product_identity_context if isinstance(product_identity_context, dict) else {}
        dna = {}
        for candidate in (
            context.get("product_identity_dna"),
            context.get("product_dna"),
            context.get("identity_dna"),
            context.get("dna"),
            context.get("product_identity"),
            context.get("identity"),
        ):
            if isinstance(candidate, dict):
                dna.update(candidate)

        def collect(*keys):
            values = []
            for source in (dna, context):
                if not isinstance(source, dict):
                    continue
                for key in keys:
                    value = source.get(key)
                    if isinstance(value, (list, tuple, set)):
                        values.extend(str(item).strip() for item in value if str(item).strip())
                    elif str(value or "").strip():
                        values.append(str(value).strip())
            unique = []
            seen = set()
            for value in values:
                marker = value.lower()
                if marker not in seen:
                    seen.add(marker)
                    unique.append(value)
            return " / ".join(unique)

        locks = {
            "shape": collect("shape", "silhouette", "form", "body_shape", "structural_shape"),
            "hole": collect("hole", "holes", "drain_hole", "drain_holes", "perforation", "perforations"),
            "sole": collect("sole", "outsole", "bottom", "bottom_shape", "tread", "footbed"),
            "material": collect("material", "materials", "surface", "surface_finish", "texture"),
            "color": collect("color", "colors", "primary_color", "color_finish", "finish"),
        }

        required_order = ("shape", "hole", "sole", "material", "color")
        lock_lines = []
        for key in required_order:
            value = locks.get(key) or "match the attached reference exactly"
            lock_lines.append(f"- {key.upper()}: {value}")

        dna_contract = (
            "\n\n[PRODUCT DNA 2.0 — IMMUTABLE]\n"
            + "\n".join(lock_lines)
            + "\nDo not redesign, simplify, mirror, stretch, merge, remove, add, or relocate any product part."
            + "\nThe number, position, spacing and size of all holes must remain identical."
            + "\nThe sole/bottom outline, thickness, tread and contact surface must remain identical."
            + "\nMaterial reflectance, texture and exact color family must remain identical."
        )
        physics_contract = (
            "\n\n[PHYSICS VALIDATION CONTRACT]\n"
            "- Water must flow only in a gravity-consistent direction.\n"
            "- Drainage direction must agree with the product orientation and hole positions.\n"
            "- Hands and feet may contact only physically reachable surfaces.\n"
            "- No penetration, floating, impossible grip, fused fingers/toes or deformed anatomy.\n"
            "- Product geometry must not change under contact, pressure or perspective.\n"
            "- Show only one product unless the scene explicitly requires a pair."
        )
        retry_contract = (
            "\n\n[COST POLICY]\n"
            "Generate exactly one image for this attempt. "
            "Do not generate a candidate grid, collage, variations or multiple alternatives."
        )

        prompt_count = 0
        scenes = [item for item in list(director_result.get("scenes") or []) if isinstance(item, dict)]
        for scene in scenes:
            if not scene.get("generation_required"):
                continue
            scene["image_prompt"] = (
                str(scene.get("image_prompt") or "").rstrip()
                + dna_contract + physics_contract + retry_contract
            )
            scene["negative_prompt"] = (
                str(scene.get("negative_prompt") or "").rstrip(", ")
                + ", changed silhouette, wrong hole count, moved holes, missing holes, extra holes"
                + ", wrong sole shape, wrong outsole, wrong tread, changed material, changed texture"
                + ", wrong color, mirrored product, floating product, impossible water flow"
                + ", uphill drainage, water through solid surface, hand penetration, foot penetration"
                + ", impossible contact, deformed hand, deformed foot, multiple candidates, collage, grid"
            ).strip(", ")
            scene["product_dna_2"] = dict(locks)
            scene["product_dna_2_required_fields"] = list(required_order)
            scene["physics_validation_required"] = True
            scene["physics_checks"] = [
                "gravity_consistent_water_flow",
                "drainage_direction",
                "hand_contact",
                "foot_contact",
                "product_geometry_unchanged",
            ]
            scene["initial_generation_count"] = 1
            scene["max_generation_attempts"] = 1
            scene["regenerate_failed_scene_only"] = True
            scene["multiple_candidate_generation"] = False
            prompt_count += 1

        for prompt_item in list(director_result.get("image_prompts") or []):
            if not isinstance(prompt_item, dict):
                continue
            matching = next(
                (scene for scene in scenes if str(scene.get("scene_id") or "") == str(prompt_item.get("scene_id") or "")),
                None,
            )
            if matching:
                prompt_item["image_prompt"] = matching.get("image_prompt", "")
                prompt_item["negative_prompt"] = matching.get("negative_prompt", "")
                prompt_item["product_dna_2"] = matching.get("product_dna_2", {})
                prompt_item["physics_validation_required"] = True
                prompt_item["initial_generation_count"] = 1
                prompt_item["max_generation_attempts"] = 1
                prompt_item["regenerate_failed_scene_only"] = True
                prompt_item["multiple_candidate_generation"] = False

        director_result["version"] = "ai-image-director-151-1-product-dna-2"
        director_result["product_dna_version"] = "product-dna-2-151-1"
        director_result["product_dna_2"] = locks
        director_result["product_dna_2_required_fields"] = list(required_order)
        director_result["physics_validator_version"] = "vision-physics-contract-151-1"
        director_result["physics_validation_required"] = True
        director_result["initial_generation_count"] = 1
        director_result["max_generation_attempts"] = 1
        director_result["regenerate_failed_scenes_only"] = True
        director_result["generate_multiple_candidates"] = False
        director_result["cost_policy_locked"] = True
        director_result["product_dna_2_prompt_count"] = prompt_count

        print("[Sprint151-1 Product DNA 2.0] Applied:", True, flush=True)
        print("[Sprint151-1 Product DNA 2.0] Prompt Count:", prompt_count, flush=True)
        print("[Sprint151-1 Product DNA 2.0] Fields:", list(required_order), flush=True)
        print("[Sprint151-1 Vision Physics] Enabled:", True, flush=True)
        print("[Sprint151-1 Cost Policy] Initial Images Per Scene:", 1, flush=True)
        print("[Sprint158 Fast Mode] Images Per Scene:", 1, flush=True)
        print(
            "[Sprint159 Diversity Policy] Camera/Orientation/Environment: LOCKED PER SCENE",
            flush=True,
        )
        print("[Sprint151-1 Cost Policy] Multiple Candidates:", False, flush=True)
        return director_result

    def _sprint151_1_apply_scene_director(self, scene_plan_result):
        if not isinstance(scene_plan_result, dict):
            return scene_plan_result

        assignments = [
            ("entryway", "착용", "현관에서 외출 전 실제로 착용하는 자연스러운 사용 장면"),
            ("closeup", "클로즈업", "제품의 구멍 위치, 재질, 가장자리와 밑창 형태가 선명한 제품 클로즈업"),
            ("veranda", "생활 사용", "자연광이 들어오는 베란다에서 실제 생활 동선에 맞춘 사용 장면"),
            ("living_room", "착용 이동", "정돈된 거실에서 걷거나 이동하며 사용하는 자연스러운 장면"),
            ("laundry_room", "물·배수 증명", "세탁실에서 중력에 맞는 물 흐름과 실제 배수 방향을 보여주는 장면"),
            ("bathroom", "젖은 환경 사용", "깨끗한 욕실에서 과도한 물 연출 없이 현실적으로 사용하는 장면"),
            ("sole_closeup", "밑창 클로즈업", "밑창 외곽선, 두께, 접지면과 배수 구조가 선명한 낮은 시점 클로즈업"),
            ("entryway", "외출 후", "다른 구도의 현관에서 벗거나 정리하는 자연스러운 장면"),
            ("veranda", "건조", "베란다에서 제품을 자연스럽게 건조하거나 보관하는 장면"),
            ("clean_studio", "CTA 제품 집중", "단순한 실내 배경에서 제품 형태와 색상을 정확히 보여주는 마무리"),
        ]

        scenes = [item for item in list(scene_plan_result.get("scenes") or []) if isinstance(item, dict)]
        counts = {}
        previous_environment = ""
        for index, scene in enumerate(scenes):
            environment, role, description = assignments[index % len(assignments)]
            if environment == previous_environment:
                environment, role, description = assignments[(index + 1) % len(assignments)]
            previous_environment = environment
            scene["scene_environment"] = environment
            scene["scene_role"] = role
            scene["environment_description"] = description
            scene["visual_direction"] = description
            scene["environment_diversity_locked"] = True
            scene["avoid_environment_repetition"] = True
            scene["scene_director_version"] = "scene-director-151-1"
            scene["physics_validation_required"] = environment in {
                "laundry_room", "bathroom", "entryway", "living_room"
            }
            director_context = dict(scene.get("director_context") or {})
            director_context.update({
                "scene_environment": environment,
                "scene_role": role,
                "environment_description": description,
                "avoid_environment_repetition": True,
                "physics_validation_required": scene["physics_validation_required"],
            })
            scene["director_context"] = director_context
            counts[environment] = counts.get(environment, 0) + 1

        scene_plan_result["version"] = "scene-plan-151-1-diverse-director"
        scene_plan_result["scene_director_version"] = "scene-director-151-1"
        scene_plan_result["scene_environment_counts"] = counts
        scene_plan_result["scene_diversity_locked"] = True
        print("[Sprint151-1 Scene Director] Applied:", True, flush=True)
        print("[Sprint151-1 Scene Director] Scene Count:", len(scenes), flush=True)
        print("[Sprint151-1 Scene Director] Environments:", counts, flush=True)
        return scene_plan_result

    def _sprint160_apply_story_director(self, scene_plan_result, script_text=""):
        """Sprint160: 잠금 대본을 광고 흐름으로 고정하고 장면별 연출 계약을 부여합니다."""
        if not isinstance(scene_plan_result, dict):
            return scene_plan_result

        scenes = [item for item in list(scene_plan_result.get("scenes") or []) if isinstance(item, dict)]
        if not scenes:
            scene_plan_result["story_validator"] = {
                "ok": False,
                "status": "failed_no_scenes",
                "errors": ["Scene plan is empty"],
            }
            return scene_plan_result

        role_sequence_10 = [
            "hook", "problem", "usage", "usage", "benefit",
            "benefit", "proof", "detail", "hero", "cta",
        ]
        camera_sequence = [
            "dynamic_medium_push_in", "wide_context", "over_shoulder_medium",
            "low_angle_tracking", "macro_closeup", "side_medium",
            "top_down_proof", "extreme_detail_closeup", "clean_hero_three_quarter",
            "slow_hero_push_in",
        ]
        orientation_sequence = [
            "front_three_quarter", "wide_front", "right_three_quarter",
            "left_side", "macro_front", "rear_three_quarter",
            "top_down", "low_detail", "front_three_quarter", "front_centered",
        ]
        environment_sequence = [
            "real_home_entry", "real_living_context", "real_usage_space",
            "real_usage_space_alt", "natural_window_light", "real_home_detail",
            "clean_function_proof", "neutral_detail_surface", "premium_home_hero",
            "minimal_real_home_hero",
        ]
        role_contracts = {
            "hook": "첫 2.5초 안에 제품과 핵심 관심 포인트를 즉시 보여준다",
            "problem": "고객이 겪는 불편을 과장 없이 현실적인 생활 장면으로 보여준다",
            "usage": "제품을 실제 순서대로 사용하는 모습을 명확하게 보여준다",
            "benefit": "사용 결과와 편리함을 한눈에 이해할 수 있게 보여준다",
            "proof": "구조, 기능, 재질 또는 작동 결과를 시각적 근거로 증명한다",
            "detail": "제품 고유 형태와 핵심 디테일을 정확하게 보여준다",
            "hero": "제품 전체 형태를 광고의 최종 주인공으로 선명하게 보여준다",
            "cta": "제품 형태를 유지한 채 구매 행동으로 연결되는 깨끗한 마무리를 만든다",
        }
        keyword_roles = (
            (("궁금하시면", "클릭", "구매", "링크"), "cta"),
            (("추천", "좋았습니다", "만족", "편리", "장점"), "benefit"),
            (("사용", "착용", "놓고", "걸고", "신고", "세척", "보관"), "usage"),
            (("리뷰", "후기", "평점", "구매", "확인"), "proof"),
            (("불편", "고민", "문제", "힘들", "번거"), "problem"),
        )

        def normalized_text(scene):
            return " ".join(str(
                scene.get("subtitle_text") or scene.get("dialogue") or scene.get("text") or ""
            ).split()).strip()

        previous_camera = ""
        previous_environment = ""
        duplicate_keys = set()
        duplicate_scene_ids = []
        role_counts = {}
        camera_counts = {}
        environment_counts = {}
        validator_errors = []

        for index, scene in enumerate(scenes):
            text_value = normalized_text(scene)
            default_role = role_sequence_10[min(index, len(role_sequence_10) - 1)]
            detected_role = ""
            for keywords, candidate_role in keyword_roles:
                if any(keyword in text_value for keyword in keywords):
                    detected_role = candidate_role
                    break

            # 광고 구조가 무너지지 않도록 시작과 끝은 절대 고정합니다.
            if index == 0:
                role = "hook"
            elif index == len(scenes) - 1:
                role = "cta"
            elif detected_role in {"problem", "usage", "benefit", "proof"}:
                role = detected_role
            else:
                role = default_role

            camera = camera_sequence[index % len(camera_sequence)]
            if camera == previous_camera:
                camera = camera_sequence[(index + 1) % len(camera_sequence)]
            environment = environment_sequence[index % len(environment_sequence)]
            if environment == previous_environment:
                environment = environment_sequence[(index + 1) % len(environment_sequence)]
            orientation = orientation_sequence[index % len(orientation_sequence)]
            previous_camera = camera
            previous_environment = environment

            scene_id = str(scene.get("scene_id") or f"scene_{index + 1:02d}")
            scene["scene_id"] = scene_id
            scene["story_order"] = index + 1
            scene["story_role"] = role
            scene["scene_role"] = role
            scene["story_contract"] = role_contracts.get(role, role_contracts["usage"])
            scene["camera_direction"] = camera
            scene["camera_shot"] = camera
            scene["product_orientation"] = orientation
            scene["scene_environment"] = environment
            scene["environment_direction"] = environment
            scene["story_director_version"] = "story-director-160-1"
            scene["camera_director_version"] = "camera-director-160-1"
            scene["environment_director_version"] = "environment-director-160-1"
            scene["product_dna_lock_version"] = "product-dna-lock-3.0-160-1"
            scene["product_dna_lock_3_required"] = True
            scene["avoid_ai_hands"] = role not in {"usage"}
            scene["avoid_studio_only_look"] = role not in {"hero", "cta"}
            scene["single_product_only"] = True
            scene["realistic_ad_flow_required"] = True
            scene["visual_direction"] = (
                f"{scene['story_contract']}. Camera={camera}. Environment={environment}. "
                f"Product orientation={orientation}. 실제 생활 광고처럼 자연스럽고 과도한 스튜디오 연출 금지."
            )
            scene["must_show"] = str(scene.get("must_show") or text_value or role_contracts.get(role, ""))
            scene["director_context"] = dict(scene.get("director_context") or {})
            scene["director_context"].update({
                "story_order": index + 1,
                "story_role": role,
                "story_contract": scene["story_contract"],
                "camera_direction": camera,
                "product_orientation": orientation,
                "scene_environment": environment,
                "product_dna_lock_3_required": True,
                "single_product_only": True,
                "realistic_ad_flow_required": True,
            })

            duplicate_key = (role, camera, environment, orientation)
            if duplicate_key in duplicate_keys:
                duplicate_scene_ids.append(scene_id)
                scene["duplicate_detected"] = True
                scene["duplicate_action"] = "regenerate_scene_only"
            else:
                duplicate_keys.add(duplicate_key)
                scene["duplicate_detected"] = False
                scene["duplicate_action"] = "accept"

            role_counts[role] = role_counts.get(role, 0) + 1
            camera_counts[camera] = camera_counts.get(camera, 0) + 1
            environment_counts[environment] = environment_counts.get(environment, 0) + 1

        present_roles = set(role_counts)
        for required in ("hook", "usage", "benefit", "hero", "cta"):
            if required not in present_roles:
                validator_errors.append(f"missing_story_role:{required}")
        if scenes[0].get("story_role") != "hook":
            validator_errors.append("first_scene_not_hook")
        if scenes[-1].get("story_role") != "cta":
            validator_errors.append("last_scene_not_cta")
        if duplicate_scene_ids:
            validator_errors.append("duplicate_scene_contract")

        story_validator = {
            "ok": not validator_errors,
            "version": "story-validator-160-1",
            "status": "passed" if not validator_errors else "revise",
            "scene_count": len(scenes),
            "role_counts": role_counts,
            "camera_counts": camera_counts,
            "environment_counts": environment_counts,
            "duplicate_scene_ids": duplicate_scene_ids,
            "errors": validator_errors,
        }
        scene_plan_result["scenes"] = scenes
        scene_plan_result["version"] = "scene-plan-160-story-directed"
        scene_plan_result["story_director_version"] = "story-director-160-1"
        scene_plan_result["camera_director_version"] = "camera-director-160-1"
        scene_plan_result["environment_director_version"] = "environment-director-160-1"
        scene_plan_result["duplicate_detector_version"] = "duplicate-detector-160-1"
        scene_plan_result["product_dna_lock_version"] = "product-dna-lock-3.0-160-1"
        scene_plan_result["story_flow"] = [scene.get("story_role") for scene in scenes]
        scene_plan_result["story_validator"] = story_validator
        scene_plan_result["story_directed"] = True
        scene_plan_result["script_source_chars"] = len(str(script_text or ""))

        print("[Sprint160 Story Director] Applied:", True, flush=True)
        print("[Sprint160 Story Director] Flow:", scene_plan_result["story_flow"], flush=True)
        print("[Sprint160 Camera Director] Unique:", len(camera_counts), flush=True)
        print("[Sprint160 Environment Director] Unique:", len(environment_counts), flush=True)
        print("[Sprint160 Duplicate Detector] Duplicates:", duplicate_scene_ids, flush=True)
        print("[Sprint160 Story Validator] Status:", story_validator["status"], flush=True)
        print("[Sprint160 Story Validator] Errors:", validator_errors, flush=True)
        return scene_plan_result

    def _sprint160_apply_product_dna_lock_3(self, director_result, product_context):
        """Sprint160: 모든 생성 프롬프트에 참조 상품 불변 계약과 AI 아티팩트 방지 규칙을 주입합니다."""
        if not isinstance(director_result, dict):
            return director_result
        context = product_context if isinstance(product_context, dict) else {}
        references = list(context.get("product_reference_images") or [])
        locked_attributes = list(context.get("product_locked_attributes") or [])
        context_text = json.dumps(context, ensure_ascii=False, default=str).lower()
        is_indoor_slipper = any(
            token in context_text
            for token in (
                "실내용 슬리퍼", "실내 슬리퍼", "욕실화", "욕실 슬리퍼",
                "indoor slipper", "bathroom slipper", "shower slipper",
            )
        )
        dna3_contract = (
            "\n\n[PRODUCT DNA LOCK 3.0 — ABSOLUTE REFERENCE MATCH]\n"
            "The attached reference product is immutable. Preserve exact silhouette, dimensions, proportions, "
            "part count, hole count and positions, edges, seams, sole/bottom geometry, material, texture, gloss, "
            "color, logo placement and assembly. Never redesign, beautify, simplify, mirror or invent details.\n"
            "Use the same single product identity in every scene. Perspective may change; geometry may not.\n"
            "Prefer product-only or naturally reachable interactions. Avoid visible hands/feet unless usage requires them.\n"
            "When hands/feet are required: anatomically correct, five digits, no fusion, penetration, floating or impossible grip.\n"
            "No synthetic showroom look except final hero/CTA. Use realistic household lighting and believable contact shadows."
        )
        duplicate_contract = (
            "\n[DUPLICATE PREVENTION]\n"
            "This scene must differ from adjacent scenes in camera distance, angle, environment and product orientation. "
            "Do not repeat the previous composition, pose, background layout or crop."
        )
        negative_addition = (
            "changed product identity, altered silhouette, wrong proportions, wrong part count, wrong hole count, "
            "moved holes, missing holes, extra holes, wrong sole, wrong bottom, wrong material, wrong texture, "
            "wrong color, mirrored product, invented logo, duplicate composition, repeated background, repeated angle, "
            "plastic CGI look, artificial showroom, deformed hand, extra fingers, fused fingers, deformed foot, penetration"
        )
        indoor_slipper_contract = ""
        indoor_slipper_negative = ""
        if is_indoor_slipper:
            indoor_slipper_contract = (
                "\n[INDOOR SLIPPER FORENSIC RULES]\n"
                "Show exactly one physical pair: two slippers total in pair, hero, environment and wearing scenes. "
                "Never create a second pair in the background, reflection, shelf or doorway. "
                "Wearing scenes use bare feet only: no socks, stockings, shoes or layered footwear. "
                "Keep both slippers top-side-up unless the prompt explicitly requests an outsole demonstration. "
                "Both slippers must match the reference and each other in silhouette, hole map, strap curve, sole and footbed. "
                "Water scenes must visibly show water entering and passing downward through the real drainage holes."
            )
            indoor_slipper_negative = (
                "extra slippers, third slipper, fourth slipper, two pairs, duplicate pair, background slippers, "
                "reflected slippers, socks, stockings, one sock, mismatched socks, other footwear, "
                "upside-down slipper, sole facing upward, mismatched left and right slipper, blocked drainage holes"
            )
        scenes = [item for item in list(director_result.get("scenes") or []) if isinstance(item, dict)]
        prompt_count = 0
        for scene in scenes:
            if not scene.get("generation_required"):
                continue
            role = str(scene.get("story_role") or scene.get("scene_role") or "usage")
            camera = str(scene.get("camera_direction") or scene.get("camera_shot") or "")
            environment = str(scene.get("scene_environment") or "")
            orientation = str(scene.get("product_orientation") or "")
            scene_contract = (
                f"\n[STORY DIRECTOR]\nRole={role}; Camera={camera}; Environment={environment}; "
                f"Product orientation={orientation}. Follow this exact advertising role and composition."
            )
            scene["image_prompt"] = str(scene.get("image_prompt") or "").rstrip() + dna3_contract + scene_contract + duplicate_contract + indoor_slipper_contract
            scene["negative_prompt"] = (str(scene.get("negative_prompt") or "").rstrip(", ") + ", " + negative_addition + (", " + indoor_slipper_negative if indoor_slipper_negative else "")).strip(", ")
            scene["product_dna_lock_3"] = {
                "reference_images": references,
                "locked_attributes": locked_attributes,
                "immutable": True,
                "single_identity_across_scenes": True,
            }
            scene["product_dna_lock_version"] = "product-dna-lock-3.1-171-1"
            scene["indoor_slipper_policy"] = {
                "enabled": bool(is_indoor_slipper),
                "exact_visible_slippers": 2 if is_indoor_slipper else None,
                "barefoot_only_when_worn": bool(is_indoor_slipper),
                "socks_forbidden": bool(is_indoor_slipper),
                "sole_up_forbidden_unless_outsole_scene": bool(is_indoor_slipper),
                "water_through_real_holes_required": bool(is_indoor_slipper),
            }
            scene["story_validator_required"] = True
            scene["duplicate_validation_required"] = True
            scene["max_generation_attempts"] = 1
            scene["initial_generation_count"] = 1
            prompt_count += 1

        prompt_map = {str(scene.get("scene_id") or ""): scene for scene in scenes}
        for item in list(director_result.get("image_prompts") or []):
            if not isinstance(item, dict):
                continue
            scene = prompt_map.get(str(item.get("scene_id") or ""))
            if scene:
                item["image_prompt"] = scene.get("image_prompt", "")
                item["negative_prompt"] = scene.get("negative_prompt", "")
                item["product_dna_lock_3"] = scene.get("product_dna_lock_3", {})
                item["story_role"] = scene.get("story_role") or scene.get("scene_role")
                item["camera_direction"] = scene.get("camera_direction") or scene.get("camera_shot")
                item["scene_environment"] = scene.get("scene_environment")
                item["product_orientation"] = scene.get("product_orientation")

        director_result["version"] = "ai-image-director-160-story-dna3"
        director_result["product_dna_lock_version"] = "product-dna-lock-3.1-171-1"
        director_result["story_director_version"] = "story-director-160-1"
        director_result["duplicate_detector_version"] = "duplicate-detector-160-1"
        director_result["story_validator_version"] = "story-validator-160-1"
        director_result["product_dna_lock_3_prompt_count"] = prompt_count
        director_result["product_dna_lock_3_required"] = True
        director_result["single_product_identity_required"] = True
        print("[Sprint171 Indoor Slipper Policy] Enabled:", is_indoor_slipper, flush=True)
        print("[Sprint160 Product DNA Lock 3.0] Applied:", True, flush=True)
        print("[Sprint160 Product DNA Lock 3.0] Prompt Count:", prompt_count, flush=True)
        print("[Sprint160 Product DNA Lock 3.0] References:", len(references), flush=True)
        return director_result


    def _sprint161_apply_reference_identity_continuity(
        self,
        scene_plan_result,
        project_id="",
        output_dir="",
        script_text="",
    ):
        """Sprint161: 장면을 하나의 광고 타임라인과 동일 상품 연속성 계약으로 고정합니다."""
        if not isinstance(scene_plan_result, dict):
            return scene_plan_result

        scenes = [item for item in list(scene_plan_result.get("scenes") or []) if isinstance(item, dict)]
        if not scenes:
            return scene_plan_result

        count = len(scenes)
        canonical_roles = [
            "hook", "problem", "solution", "drainage_proof", "usage",
            "walking_usage", "benefit", "detail", "hero", "cta",
        ]
        if count != len(canonical_roles):
            role_map = []
            for index in range(count):
                ratio = index / max(1, count - 1)
                if index == 0:
                    role = "hook"
                elif index == count - 1:
                    role = "cta"
                elif ratio < 0.22:
                    role = "problem"
                elif ratio < 0.38:
                    role = "solution"
                elif ratio < 0.55:
                    role = "usage"
                elif ratio < 0.72:
                    role = "benefit"
                elif ratio < 0.88:
                    role = "detail"
                else:
                    role = "hero"
                role_map.append(role)
        else:
            role_map = canonical_roles

        role_visuals = {
            "hook": "Show the real-life problem first, with the product visible as the immediate answer.",
            "problem": "Show the inconvenience clearly and realistically before the product is used.",
            "solution": "Introduce the exact same product as the solution, clean and easy to identify.",
            "drainage_proof": "Prove drainage with gravity-consistent water flow through the exact existing holes.",
            "usage": "Show a natural physically correct step-in action with minimal body visibility.",
            "walking_usage": "Show one or two realistic walking steps while preserving exact product geometry.",
            "benefit": "Show the practical result: dry, stable, comfortable, easy household use.",
            "detail": "Show an identity-critical close-up of hole layout, strap edge, toe shape and sole thickness.",
            "hero": "Show a premium full-product hero shot with the exact reference identity and no redesign.",
            "cta": "End with the same hero product, centered, clean, memorable and ready for CTA text overlay.",
        }

        identity_id = f"product_identity_{project_id or 'current'}_161"
        cache_dir = Path(str(output_dir or "."))
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = cache_dir / "reference_identity_cache_161.json"
        cache_payload = {
            "version": "reference-identity-cache-161-1",
            "project_id": str(project_id or ""),
            "identity_id": identity_id,
            "scene_count": count,
            "source": "canonical_product_reference",
            "policy": {
                "same_identity_all_scenes": True,
                "previous_scene_continuity": True,
                "failed_scene_only_regeneration": True,
                "initial_generation_count": 1,
            },
        }
        cache_path.write_text(json.dumps(cache_payload, ensure_ascii=False, indent=2), encoding="utf-8")

        timeline = []
        for index, scene in enumerate(scenes):
            scene_id = str(scene.get("scene_id") or f"scene_{index + 1:02d}")
            role = role_map[index]
            previous_scene_id = str(scenes[index - 1].get("scene_id") or f"scene_{index:02d}") if index else ""
            next_scene_id = str(scenes[index + 1].get("scene_id") or f"scene_{index + 2:02d}") if index + 1 < count else ""
            scene.update({
                "scene_id": scene_id,
                "story_order": index + 1,
                "story_role": role,
                "scene_role": role,
                "story_timeline_version": "story-timeline-director-161-1",
                "reference_identity_cache_version": "reference-identity-cache-161-1",
                "reference_identity_id": identity_id,
                "reference_identity_cache_path": str(cache_path),
                "continuity_previous_scene_id": previous_scene_id,
                "continuity_next_scene_id": next_scene_id,
                "continue_same_physical_product": bool(index),
                "same_product_pair_across_all_scenes": True,
                "identity_validator_version": "identity-validator-2.0-161-1",
                "identity_validation_required": True,
                "identity_critical_features": [
                    "outer_silhouette", "toe_shape", "strap_width", "hole_count",
                    "hole_positions", "hole_spacing", "sole_thickness", "sidewall_line",
                    "material_texture", "exact_color",
                ],
                "hero_scene_required": role in {"hero", "cta"},
                "failed_scene_only_regeneration": True,
                "initial_generation_count": 1,
                "max_generation_attempts": 2,
            })
            continuity_text = (
                f"{role_visuals.get(role, role_visuals['usage'])} "
                "Treat this as the same physical product pair carried forward from the previous scene, "
                "not a newly designed or newly manufactured product."
            )
            scene["continuity_direction"] = continuity_text
            scene["visual_direction"] = (
                str(scene.get("visual_direction") or "").rstrip() + " " + continuity_text
            ).strip()
            scene["director_context"] = dict(scene.get("director_context") or {})
            scene["director_context"].update({
                "reference_identity_id": identity_id,
                "continuity_previous_scene_id": previous_scene_id,
                "story_role": role,
                "same_physical_product": True,
                "identity_validation_required": True,
            })
            timeline.append({
                "order": index + 1,
                "scene_id": scene_id,
                "role": role,
                "previous_scene_id": previous_scene_id,
                "next_scene_id": next_scene_id,
            })

        scene_plan_result["scenes"] = scenes
        scene_plan_result["version"] = "scene-plan-161-reference-continuity"
        scene_plan_result["story_timeline_version"] = "story-timeline-director-161-1"
        scene_plan_result["reference_identity_cache_version"] = "reference-identity-cache-161-1"
        scene_plan_result["reference_identity_id"] = identity_id
        scene_plan_result["reference_identity_cache_path"] = str(cache_path)
        scene_plan_result["scene_continuity_version"] = "scene-continuity-engine-161-1"
        scene_plan_result["identity_validator_version"] = "identity-validator-2.0-161-1"
        scene_plan_result["story_timeline"] = timeline
        scene_plan_result["story_flow"] = [item["role"] for item in timeline]
        scene_plan_result["continuity_ready"] = True
        print("[Sprint161 Reference Identity Cache] Path:", str(cache_path), flush=True)
        print("[Sprint161 Story Timeline] Flow:", scene_plan_result["story_flow"], flush=True)
        print("[Sprint161 Scene Continuity] Linked Scenes:", len(timeline), flush=True)
        return scene_plan_result

    def _sprint161_apply_identity_cache_to_director(self, director_result, product_context):
        """Sprint161: 모든 생성 장면에 동일한 정본 참조와 이전 장면 연속성 계약을 주입합니다."""
        if not isinstance(director_result, dict):
            return director_result
        context = product_context if isinstance(product_context, dict) else {}
        references = [str(item) for item in list(context.get("product_reference_images") or []) if str(item).strip()]
        canonical_reference = references[0] if references else ""
        scenes = [item for item in list(director_result.get("scenes") or []) if isinstance(item, dict)]
        scene_map = {str(item.get("scene_id") or ""): item for item in scenes}
        contract = (
            "\n\n[SPRINT161 REFERENCE IDENTITY CACHE — SAME PHYSICAL PRODUCT]\n"
            "Use the canonical reference image as the immutable identity source in every scene. "
            "This is the same physical product pair continuing from the previous scene, not a similar replacement. "
            "Keep exact hole count, hole coordinates, hole sizes, strap width, toe contour, sidewall line, sole thickness, "
            "bottom geometry, material texture and exact color. Camera and environment may change; product geometry may not. "
            "For usage scenes, fit the foot to the product without stretching or reshaping the product. "
            "For hero and CTA scenes, show the full exact product with no hand, no foot, no extra pair and no redesign."
        )
        negative = (
            "new product design, similar product, alternate model, changed hole layout, changed hole coordinates, "
            "changed strap width, changed toe contour, changed sidewall, changed sole thickness, stretched slipper, "
            "reshaped slipper, extra pair, missing pair, product mutation, scene-to-scene identity drift"
        )
        prompt_count = 0
        for index, scene in enumerate(scenes):
            if not scene.get("generation_required"):
                continue
            previous_scene_id = str(scene.get("continuity_previous_scene_id") or "")
            role = str(scene.get("story_role") or scene.get("scene_role") or "usage")
            scene["image_prompt"] = str(scene.get("image_prompt") or "").rstrip() + contract + (
                f"\nScene role={role}. Previous continuity scene={previous_scene_id or 'canonical reference start'}."
            )
            scene["negative_prompt"] = (str(scene.get("negative_prompt") or "").rstrip(", ") + ", " + negative).strip(", ")
            if canonical_reference:
                scene["reference_image_path"] = canonical_reference
                scene["reference_image_paths"] = [canonical_reference]
                scene["require_reference_image"] = True
            scene["reference_identity_id"] = str(scene.get("reference_identity_id") or context.get("product_identity_id") or "")
            scene["reference_identity_cache_version"] = "reference-identity-cache-161-1"
            scene["scene_continuity_version"] = "scene-continuity-engine-161-1"
            scene["identity_validator_version"] = "identity-validator-2.0-161-1"
            scene["identity_validation_required"] = True
            scene["failed_scene_only_regeneration"] = True
            scene["initial_generation_count"] = 1
            scene["max_generation_attempts"] = 2
            prompt_count += 1

        for item in list(director_result.get("image_prompts") or []):
            if not isinstance(item, dict):
                continue
            source = scene_map.get(str(item.get("scene_id") or ""), {})
            if source:
                for key in (
                    "image_prompt", "negative_prompt", "reference_image_path", "reference_image_paths",
                    "require_reference_image", "reference_identity_id", "reference_identity_cache_version",
                    "scene_continuity_version", "identity_validator_version", "identity_validation_required",
                    "failed_scene_only_regeneration", "initial_generation_count", "max_generation_attempts",
                    "continuity_previous_scene_id", "story_role",
                ):
                    if key in source:
                        item[key] = source[key]

        director_result["version"] = "ai-image-director-161-reference-continuity"
        director_result["reference_identity_cache_version"] = "reference-identity-cache-161-1"
        director_result["scene_continuity_version"] = "scene-continuity-engine-161-1"
        director_result["story_timeline_version"] = "story-timeline-director-161-1"
        director_result["identity_validator_version"] = "identity-validator-2.0-161-1"
        director_result["canonical_reference_image"] = canonical_reference
        director_result["continuity_prompt_count"] = prompt_count
        director_result["failed_scene_only_regeneration"] = True
        print("[Sprint161 Identity Cache Route] Canonical Reference:", canonical_reference, flush=True)
        print("[Sprint161 Identity Cache Route] Prompt Count:", prompt_count, flush=True)
        print("[Sprint161 Identity Validator 2.0] Required:", True, flush=True)
        return director_result


    def _sprint162_prepare_flexible_approved_scenes(
        self,
        director_result,
        minimum_approved_scenes=8,
        target_scene_count=10,
        target_duration_seconds=25.0,
    ):
        """Sprint170: 승인된 8~10장만 사용하고 첫 Hook은 제품 없는 고정 배경으로 처리합니다."""
        result = director_result if isinstance(director_result, dict) else {}
        scenes = [item for item in list(result.get("scenes") or []) if isinstance(item, dict)]

        def existing_image(scene):
            for key in (
                "selected_generated_image_path", "validated_image_path", "generated_image_path",
                "final_image_path", "resolved_image_path", "output_image_path", "selected_image_path",
            ):
                value = str(scene.get(key) or "").strip()
                if value and Path(value).is_file():
                    return value
            return ""

        approved, rejected = [], []
        for index, scene in enumerate(scenes):
            copied = dict(scene)
            path = existing_image(copied)
            explicit_reject = any(
                copied.get(key) is False
                for key in ("approved", "user_approved", "passed", "validation_passed")
                if key in copied
            )
            status_text = str(
                copied.get("approval_status") or copied.get("validation_status")
                or copied.get("status") or ""
            ).strip().lower()
            if status_text in {"rejected", "failed", "invalid", "blocked"}:
                explicit_reject = True
            visible_count = int(copied.get("visible_product_count") or copied.get("product_count") or 0)
            forensic_failure_keys = (
                "extra_product_failure", "pair_integrity_failure", "foot_count_failure",
                "socks_failure", "sole_orientation_failure", "pair_identity_failure",
                "drainage_visibility_failure",
            )
            forensic_failures = [
                key for key in forensic_failure_keys if bool(copied.get(key))
            ]
            if visible_count > 2 or forensic_failures:
                explicit_reject = True
                copied["sprint171_forensic_rejected"] = True
                copied["sprint171_forensic_failures"] = forensic_failures

            if path and not explicit_reject:
                copied["selected_generated_image_path"] = path
                copied["sprint170_approved"] = True
                copied["sprint170_original_index"] = index
                approved.append(copied)
            else:
                copied["sprint170_approved"] = False
                copied["sprint170_reject_reason"] = (
                    "forensic_validator_failure" if copied.get("sprint171_forensic_rejected")
                    else "explicit_reject" if explicit_reject else "image_missing"
                )
                rejected.append(copied)

        approved = approved[:max(0, int(target_scene_count or 10))]
        approved_count = len(approved)
        minimum = max(1, int(minimum_approved_scenes or 8))
        ready = approved_count >= minimum
        hook_duration = 2.0
        seconds_per_scene = round(
            max(1.8, float(target_duration_seconds or 25.0) - hook_duration) / approved_count,
            4,
        ) if ready else 0.0
        hook_background = Path("assets") / "templates" / "trust_intro_background_1080x1920.png"

        for render_index, scene in enumerate(approved):
            scene["scene_index"] = render_index + 1
            scene["duration"] = seconds_per_scene
            scene["duration_seconds"] = seconds_per_scene
            scene["flexible_approval_version"] = "flexible-scene-approval-170-1"

        result["scenes"] = approved if ready else scenes
        result["flexible_approval_version"] = "flexible-scene-approval-170-1"
        result["minimum_approved_scenes"] = minimum
        result["target_scene_count"] = int(target_scene_count or 10)
        result["approved_scene_count"] = approved_count
        result["rejected_scene_count"] = len(rejected)
        result["approved_scene_ids"] = [str(item.get("scene_id") or "") for item in approved]
        result["rejected_scene_ids"] = [str(item.get("scene_id") or "") for item in rejected]
        result["flexible_render_ready"] = ready
        result["seconds_per_scene"] = seconds_per_scene
        result["target_duration_seconds"] = float(target_duration_seconds or 25.0)
        result["hook_background_path"] = str(hook_background)
        result["hook_duration_seconds"] = hook_duration
        result["hook_is_text_only_template"] = True
        result["failed_optional_scenes_skipped"] = ready and bool(rejected)

        print("[Sprint171 Flexible Approval] Approved:", approved_count, flush=True)
        print("[Sprint171 Flexible Approval] Rejected:", len(rejected), flush=True)
        print("[Sprint171 Flexible Approval] Minimum:", minimum, flush=True)
        print("[Sprint171 Flexible Approval] Render Ready:", ready, flush=True)
        print("[Sprint171 Trust Intro] Background:", str(hook_background), flush=True)
        print("[Sprint171 Flexible Approval] Seconds Per Product Scene:", seconds_per_scene, flush=True)
        return result

    def _sprint162_strengthen_continuity_chain(self, director_result):
        """Sprint170: 원본 상품과 직전 승인 장면을 동시에 참조하는 Identity Cache/Story Memory입니다."""
        if not isinstance(director_result, dict):
            return director_result
        scenes = [item for item in list(director_result.get("scenes") or []) if isinstance(item, dict)]
        canonical = str(
            director_result.get("canonical_reference_image")
            or director_result.get("reference_image_path") or ""
        ).strip()
        previous_path = canonical
        features = [
            "overall_silhouette", "hole_count", "hole_coordinates", "hole_size",
            "hole_spacing", "strap_width", "strap_height", "toe_contour",
            "sole_outline", "sole_thickness", "sidewall_line", "footbed_pattern",
            "material_texture", "exact_color", "left_right_pair_symmetry",
        ]
        memory = []
        for index, scene in enumerate(scenes):
            current_path = str(
                scene.get("selected_generated_image_path") or scene.get("validated_image_path")
                or scene.get("generated_image_path") or scene.get("resolved_image_path") or ""
            ).strip()
            scene["continuity_state_version"] = "continuity-state-170-1"
            scene["identity_cache_version"] = "persistent-identity-cache-170-1"
            scene["continuity_previous_image_path"] = previous_path
            scene["continuity_canonical_image_path"] = canonical
            scene["reference_image_paths"] = [v for v in (canonical, previous_path) if v][:2]
            scene["same_physical_product_required"] = True
            scene["identity_comparison_features"] = list(features)
            scene["identity_acceptance_threshold"] = 94.0
            scene["failed_scene_only_regeneration"] = True
            scene["continuity_order"] = index + 1
            scene["visible_product_count_rule"] = "exactly_2_for_pair_or_wearing_scene"
            scene["extra_product_forbidden"] = True
            scene["story_state"] = {
                "order": index + 1,
                "role": str(scene.get("story_role") or scene.get("purpose") or ""),
                "environment": str(scene.get("scene_environment") or scene.get("environment") or ""),
                "product_state": str(scene.get("product_state") or "same_product"),
                "previous_scene_image": previous_path,
            }
            memory.append(dict(scene["story_state"]))
            if current_path and Path(current_path).is_file():
                previous_path = current_path

        director_result["scenes"] = scenes
        director_result["identity_cache"] = {
            "version": "persistent-identity-cache-170-1",
            "canonical_reference_image": canonical,
            "features": features,
        }
        director_result["story_state_memory"] = memory
        director_result["continuity_state_version"] = "continuity-state-170-1"
        director_result["identity_validator_version"] = "identity-validator-170-1"
        director_result["identity_acceptance_threshold"] = 94.0
        director_result["failed_scene_only_regeneration"] = True
        director_result["extra_product_validator_enabled"] = True
        print("[Sprint171 Identity Cache] Canonical:", canonical, flush=True)
        print("[Sprint171 Continuity State] Linked Scenes:", len(scenes), flush=True)
        print("[Sprint171 Story Memory] States:", len(memory), flush=True)
        return director_result

    def _sprint150_6_strengthen_product_dna(self, director_result, product_context):
        """Sprint150-6: 생성 프롬프트에 형태 보존 규칙을 강제로 주입합니다."""
        if not isinstance(director_result, dict):
            return director_result

        context = product_context if isinstance(product_context, dict) else {}
        locked_attributes = [
            str(item).strip()
            for item in list(context.get("product_locked_attributes") or [])
            if str(item).strip()
        ]
        critical_geometry = [
            "exact outer silhouette and proportions",
            "exact number, size, spacing and position of holes/openings",
            "exact sole/outsole contour, thickness, tread and heel/toe shape",
            "exact straps, seams, edges, cut lines, fasteners and surface details",
            "exact color blocking, material texture, logo and printed marks",
        ]
        dna_text = (
            "PRODUCT DNA HARD LOCK. Use the reference product as immutable geometry. "
            "Preserve " + "; ".join(critical_geometry) + ". "
            "Do not add, remove, merge, move, resize or redesign any product detail. "
            "Do not mirror the product. Do not change the sole, holes, straps, seams, edges, "
            "logo, material or color. Only the environment, human pose, lighting and camera may change."
        )
        if locked_attributes:
            dna_text += " Locked attributes: " + "; ".join(locked_attributes[:20]) + "."

        negative_lock = (
            "different product, redesigned product, altered silhouette, changed proportions, "
            "missing holes, extra holes, moved holes, merged holes, changed outsole, changed sole shape, "
            "changed tread, changed heel, changed toe, changed straps, changed seams, changed logo, "
            "mirrored product, deformed product, melted geometry, duplicated parts, invented details"
        )

        prompt_count = 0
        for item in list(director_result.get("image_prompts") or []):
            if not isinstance(item, dict):
                continue
            original = str(item.get("prompt") or item.get("image_prompt") or "").strip()
            strengthened = f"{dna_text}\nSCENE: {original}" if original else dna_text
            item["prompt"] = strengthened
            item["image_prompt"] = strengthened
            current_negative = str(item.get("negative_prompt") or "").strip()
            item["negative_prompt"] = ", ".join(
                part for part in (negative_lock, current_negative) if part
            )
            item["product_dna_hard_lock"] = True
            item["critical_geometry_features"] = list(critical_geometry)
            item["locked_attributes"] = list(locked_attributes)
            item["identity_threshold"] = 94.0
            item["reject_on_geometry_drift"] = True
            prompt_count += 1

        director_result["product_dna_version"] = "product-dna-hard-lock-150-6"
        director_result["product_dna_hard_lock"] = True
        director_result["product_dna_prompt_count"] = prompt_count
        director_result["critical_geometry_features"] = critical_geometry
        print("[Sprint150-6 Product DNA] Applied:", True, flush=True)
        print("[Sprint150-6 Product DNA] Prompt Count:", prompt_count, flush=True)
        print("[Sprint150-6 Product DNA] Identity Threshold:", 94.0, flush=True)
        return director_result

    def _sprint150_6_apply_scene_diversity(self, scene_plan_result):
        """Sprint150-6: 욕실 편중을 막고 생활 공간을 순환 배치합니다."""
        if not isinstance(scene_plan_result, dict):
            return scene_plan_result
        environments = [
            ("entryway", "밝고 정돈된 현관, 신발장과 자연스러운 출입 동선"),
            ("indoor_living", "채광이 좋은 실내 거실, 일상적인 사용 장면"),
            ("veranda", "햇빛이 들어오는 베란다 또는 발코니, 건조하고 자연스러운 분위기"),
            ("bathroom", "깨끗한 욕실, 물기는 최소화하고 현실적인 사용 장면"),
            ("entryway", "다른 구도의 현관, 외출 전후 실제 사용 장면"),
            ("indoor_room", "침실 또는 드레스룸, 정돈된 실내 생활 장면"),
            ("veranda", "다른 구도의 베란다, 자연광과 생활 소품"),
            ("indoor_living", "다른 구도의 거실 또는 복도, 자연스러운 이동 장면"),
            ("bathroom", "다른 구도의 깨끗한 욕실, 과도한 물 표현 금지"),
            ("clean_studio", "깔끔한 실내 제품 클로즈업, 배경은 단순하게"),
        ]
        scenes = [item for item in list(scene_plan_result.get("scenes") or []) if isinstance(item, dict)]
        counts = {}
        for index, scene in enumerate(scenes):
            key, description = environments[index % len(environments)]
            scene["scene_environment"] = key
            scene["environment_description"] = description
            scene["environment_diversity_locked"] = True
            scene["avoid_environment_repetition"] = True
            scene["visual_direction"] = description
            director_context = dict(scene.get("director_context") or {})
            director_context["scene_environment"] = key
            director_context["environment_description"] = description
            director_context["avoid_environment_repetition"] = True
            scene["director_context"] = director_context
            counts[key] = counts.get(key, 0) + 1
        scene_plan_result["scenes"] = scenes
        scene_plan_result["scene_diversity_version"] = "scene-environment-diversity-150-6"
        scene_plan_result["scene_environment_counts"] = counts
        scene_plan_result["scene_diversity_ready"] = bool(scenes)
        print("[Sprint150-6 Scene Diversity] Ready:", bool(scenes), flush=True)
        print("[Sprint150-6 Scene Diversity] Counts:", counts, flush=True)
        return scene_plan_result

    def _run_sprint141_6_ai_image_closed_loop(
        self,
        director_result,
        output_dir,
    ):
        """
        Sprint141-6 Workflow Closed Loop Executor Bridge.

        - AIImageDirector.execute_closed_loop()를 WorkflowEngine에 연결합니다.
        - Gemini 이미지 생성기와 Vision 검사기를 동적으로 연결합니다.
        - 공급자 모듈이 없으면 기존 이미지 모션 흐름을 그대로 유지합니다.
        - Closed Loop 실패가 전체 원클릭 파이프라인을 중단시키지 않습니다.
        """
        result = {
            "ok": False,
            "ready": False,
            "version": "workflow-ai-image-closed-loop-141-6",
            "status": "not_run",
            "director_version": str(
                (director_result or {}).get("version", "")
                if isinstance(director_result, dict)
                else ""
            ),
            "generator": {},
            "validator": {},
            "closed_loop_result": {},
            "selected_image_count": 0,
            "passed_scene_count": 0,
            "failed_scene_count": 0,
            "provider_failure_count": 0,
            "provider_failures": [],
            "network_retry_enabled": True,
            "empty_generation_blocked": False,
            "errors": [],
            "warnings": [],
        }

        if not isinstance(director_result, dict):
            result["status"] = "invalid_director_result"
            result["errors"].append(
                "AIImageDirector 결과가 dict 형식이 아닙니다."
            )
            return result

        if not bool(director_result.get("ok")):
            result["status"] = "director_not_ready"
            result["warnings"].append(
                "AIImageDirector 결과가 준비되지 않아 Closed Loop를 건너뜁니다."
            )
            return result

        image_prompts = [
            item
            for item in list(director_result.get("image_prompts") or [])
            if isinstance(item, dict)
            and bool(item.get("generation_required", True))
        ]
        if not image_prompts:
            result.update(
                ok=True,
                ready=True,
                status="skipped_no_generation_targets",
                closed_loop_result=dict(director_result),
            )
            return result

        prompt_by_scene_id = {
            str(item.get("scene_id") or ""): item
            for item in image_prompts
            if str(item.get("scene_id") or "")
        }

        try:
            image_director = AIImageDirector()
        except Exception as exc:
            result["status"] = "director_init_failed"
            result["errors"].append(f"{type(exc).__name__}: {exc}")
            return result

        if not callable(getattr(image_director, "execute_closed_loop", None)):
            result["status"] = "closed_loop_method_missing"
            result["errors"].append(
                "AIImageDirector.execute_closed_loop()가 없습니다. "
                "Sprint141-6 적용 여부를 확인하세요."
            )
            return result

        generator_class = None
        generator_import_error = ""
        for module_name, class_name in (
            (
                "modules.image_ai.gemini_image_generator",
                "GeminiImageGenerator",
            ),
            (
                "modules.image_ai.ai_image_generator",
                "AIImageGenerator",
            ),
        ):
            try:
                module = __import__(
                    module_name,
                    fromlist=[class_name],
                )
                candidate = getattr(module, class_name, None)
                if candidate is not None:
                    generator_class = candidate
                    result["generator"]["module"] = module_name
                    result["generator"]["class"] = class_name
                    break
            except Exception as exc:
                generator_import_error = (
                    f"{module_name}: {type(exc).__name__}: {exc}"
                )

        validator_class = None
        validator_import_error = ""
        for module_name, class_name in (
            (
                "modules.image_ai.generated_image_vision_validator",
                "GeneratedImageVisionValidator",
            ),
            (
                "modules.image_ai.image_fidelity_validator",
                "ImageFidelityValidator",
            ),
        ):
            try:
                module = __import__(
                    module_name,
                    fromlist=[class_name],
                )
                candidate = getattr(module, class_name, None)
                if candidate is not None:
                    validator_class = candidate
                    result["validator"]["module"] = module_name
                    result["validator"]["class"] = class_name
                    break
            except Exception as exc:
                validator_import_error = (
                    f"{module_name}: {type(exc).__name__}: {exc}"
                )

        if generator_class is None or validator_class is None:
            result["status"] = "provider_modules_unavailable"
            if generator_class is None:
                result["warnings"].append(
                    "Gemini 이미지 생성기 모듈이 아직 연결되지 않았습니다."
                )
                if generator_import_error:
                    result["generator"]["import_error"] = (
                        generator_import_error
                    )
            if validator_class is None:
                result["warnings"].append(
                    "생성 이미지 Vision 검사기 모듈이 아직 연결되지 않았습니다."
                )
                if validator_import_error:
                    result["validator"]["import_error"] = (
                        validator_import_error
                    )
            result["closed_loop_result"] = dict(director_result)
            return result

        try:
            generator_engine = generator_class()
            validator_engine = validator_class()
        except Exception as exc:
            result["status"] = "provider_init_failed"
            result["errors"].append(f"{type(exc).__name__}: {exc}")
            result["closed_loop_result"] = dict(director_result)
            return result

        result["generator"]["version"] = str(
            getattr(generator_engine, "VERSION", "")
            or getattr(generator_engine, "version", "")
        )
        result["validator"]["version"] = str(
            getattr(validator_engine, "VERSION", "")
            or getattr(validator_engine, "version", "")
        )

        def call_public_method(engine, method_names, payload):
            last_type_error = None
            for method_name in method_names:
                method = getattr(engine, method_name, None)
                if not callable(method):
                    continue

                for call in (
                    lambda: method(**payload),
                    lambda: method(payload),
                ):
                    try:
                        return method_name, call()
                    except TypeError as exc:
                        last_type_error = exc
                        continue

            if last_type_error is not None:
                raise last_type_error
            raise AttributeError(
                "지원되는 공개 실행 메서드를 찾지 못했습니다: "
                + ", ".join(method_names)
            )

        def image_generator_callback(payload):
            scene_id_value = str(payload.get("scene_id") or "")
            output_image_path = str(
                payload.get("output_image_path") or ""
            )
            generator_payload = {
                "scene_id": scene_id_value,
                "attempt": int(payload.get("attempt") or 1),
                "prompt": str(payload.get("prompt") or ""),
                "image_prompt": str(payload.get("prompt") or ""),
                "negative_prompt": str(
                    payload.get("negative_prompt") or ""
                ),
                "reference_image_path": str(
                    payload.get("reference_image_path") or ""
                ),
                "output_image_path": output_image_path,
                "output_path": output_image_path,
                "overwrite": True,
            }
            try:
                method_name, raw = call_public_method(
                    generator_engine,
                    (
                        "generate_image",
                        "generate",
                        "run",
                        "create",
                    ),
                    generator_payload,
                )
                result["generator"]["method"] = method_name
                if not isinstance(raw, dict):
                    raw = {
                        "ok": False,
                        "ready": False,
                        "status": "invalid_generator_result",
                        "scene_id": scene_id_value,
                        "output_image_path": output_image_path,
                        "errors": [
                            "GeminiImageGenerator 결과가 dict 형식이 아닙니다."
                        ],
                    }
                if not bool(raw.get("ok")):
                    failure = {
                        "scene_id": scene_id_value,
                        "attempt": int(payload.get("attempt") or 1),
                        "status": str(raw.get("status") or "generator_failed"),
                        "errors": list(raw.get("errors") or []),
                        "provider_attempts": int(raw.get("provider_attempts") or 0),
                        "network_retry_count": int(raw.get("network_retry_count") or 0),
                    }
                    result["provider_failures"].append(failure)
                    result["provider_failure_count"] = len(
                        result["provider_failures"]
                    )
                    print(
                        "[Sprint152-2 Scene Isolation] Generator Failed:",
                        failure,
                        flush=True,
                    )
                return raw
            except Exception as exc:
                failure = {
                    "scene_id": scene_id_value,
                    "attempt": int(payload.get("attempt") or 1),
                    "status": "generator_callback_exception",
                    "errors": [f"{type(exc).__name__}: {exc}"],
                    "provider_attempts": 0,
                    "network_retry_count": 0,
                }
                result["provider_failures"].append(failure)
                result["provider_failure_count"] = len(
                    result["provider_failures"]
                )
                print(
                    "[Sprint152-2 Scene Isolation] Callback Exception:",
                    failure,
                    flush=True,
                )
                return {
                    "ok": False,
                    "ready": False,
                    "version": str(
                        getattr(generator_engine, "VERSION", "")
                    ),
                    "status": "generator_callback_exception",
                    "scene_id": scene_id_value,
                    "attempt": int(payload.get("attempt") or 1),
                    "output_image_path": output_image_path,
                    "output_path": output_image_path,
                    "errors": list(failure["errors"]),
                    "warnings": [],
                }

        def image_validator_callback(payload):
            scene_id_value = str(payload.get("scene_id") or "")
            prompt_item = prompt_by_scene_id.get(scene_id_value, {})
            validator_payload = {
                "scene_id": scene_id_value,
                "attempt": int(payload.get("attempt") or 1),
                "generated_image_path": str(
                    payload.get("generated_image_path") or ""
                ),
                "image_path": str(
                    payload.get("generated_image_path") or ""
                ),
                "reference_image_path": str(
                    payload.get("reference_image_path") or ""
                ),
                "prompt": str(payload.get("prompt") or ""),
                "negative_prompt": str(
                    payload.get("negative_prompt") or ""
                ),
                "fidelity_threshold": max(
                    94.0,
                    float(payload.get("fidelity_threshold") or 94.0),
                ),
                "identity_threshold": 94.0,
                "critical_geometry_features": list(
                    prompt_item.get("critical_geometry_features") or []
                ),
                "locked_attributes": list(
                    prompt_item.get("locked_attributes") or []
                ),
                "reject_on_geometry_drift": True,
                "reject_if_holes_or_sole_changed": True,
                "comparison_mode": "reference_vs_generated_strict_geometry",
            }
            method_name, raw = call_public_method(
                validator_engine,
                (
                    "validate",
                    "analyze",
                    "evaluate",
                    "inspect",
                    "run",
                ),
                validator_payload,
            )
            result["validator"]["method"] = method_name
            return raw

        try:
            closed_loop_result = image_director.execute_closed_loop(
                product_name=director_result.get("product_name", ""),
                scenes=director_result.get("scenes"),
                scene_image_plan=director_result,
                output_dir=str(output_dir or ""),
                image_generator=image_generator_callback,
                image_validator=image_validator_callback,
                max_attempts=4,
                threshold=94.0,
                save_result=True,
            )
        except Exception as exc:
            result["status"] = "closed_loop_failed"
            result["errors"].append(f"{type(exc).__name__}: {exc}")
            result["closed_loop_result"] = dict(director_result)
            return result

        generation_runs = [
            item
            for item in list(
                (closed_loop_result or {}).get("generation_runs") or []
            )
            if isinstance(item, dict)
        ]
        selected_image_paths = []
        for item in generation_runs:
            selected_path_text = str(
                item.get("selected_image_path") or ""
            ).strip()
            if not selected_path_text:
                continue
            selected_path = Path(selected_path_text)
            if selected_path.is_file() and selected_path.stat().st_size > 0:
                selected_image_paths.append(str(selected_path))
            else:
                result["warnings"].append(
                    "선택 경로에 실제 이미지 파일이 없습니다: "
                    + selected_path_text
                )

        selected_image_count = len(selected_image_paths)
        passed_scene_count = sum(
            1
            for item in generation_runs
            if bool(item.get("passed"))
            and str(item.get("selected_image_path") or "").strip()
            in selected_image_paths
        )
        failed_scene_count = max(
            0,
            len(generation_runs) - passed_scene_count,
        )

        # Sprint141-7:
        # execute_closed_loop()의 최종 결과를 Director JSON에 반드시 다시 저장합니다.
        # 초기 build() 결과가 같은 파일에 먼저 저장되어 있어도 Closed Loop 결과로
        # 덮어써 generation_runs와 fidelity_results가 유실되지 않게 합니다.
        persistence_result = {
            "ok": False,
            "status": "not_saved",
            "path": "",
            "errors": [],
        }
        try:
            closed_loop_payload = (
                dict(closed_loop_result)
                if isinstance(closed_loop_result, dict)
                else {}
            )
            closed_loop_payload["workflow_connection_version"] = (
                "workflow-ai-image-closed-loop-141-7"
            )
            closed_loop_payload["workflow_version"] = self.WORKFLOW_VERSION
            closed_loop_payload["network_retry_enabled"] = True
            closed_loop_payload["provider_failure_count"] = int(
                result.get("provider_failure_count") or 0
            )
            closed_loop_payload["provider_failures"] = list(
                result.get("provider_failures") or []
            )
            closed_loop_payload["selected_image_paths_verified"] = list(
                selected_image_paths
            )
            closed_loop_payload["selected_image_count_verified"] = int(
                selected_image_count
            )
            closed_loop_payload["empty_generation_blocked"] = (
                selected_image_count <= 0
            )

            target_path_value = str(
                closed_loop_payload.get("result_path")
                or director_result.get("result_path")
                or ""
            ).strip()
            if target_path_value:
                target_path = Path(target_path_value)
                if not target_path.is_absolute():
                    normalized_target = str(target_path).replace("\\", "/")
                    normalized_output = str(output_dir or "").replace("\\", "/").rstrip("/")
                    if not (
                        normalized_output
                        and normalized_target.startswith(normalized_output + "/")
                    ):
                        target_path = Path(str(output_dir or ".")) / target_path.name
            else:
                target_path = (
                    Path(str(output_dir or "."))
                    / "ai_image_director_141_7.json"
                )

            target_path.parent.mkdir(parents=True, exist_ok=True)
            closed_loop_payload["result_path"] = str(target_path)
            target_path.write_text(
                json.dumps(
                    closed_loop_payload,
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                ),
                encoding="utf-8",
            )
            closed_loop_result = closed_loop_payload
            persistence_result.update(
                ok=True,
                status="saved",
                path=str(target_path),
            )
        except Exception as exc:
            persistence_result.update(
                status="save_failed",
                errors=[f"{type(exc).__name__}: {exc}"],
            )

        print(
            "[Sprint141-7 Closed Loop Persistence] Status:",
            persistence_result.get("status", ""),
            flush=True,
        )
        print(
            "[Sprint141-7 Closed Loop Persistence] Path:",
            persistence_result.get("path", ""),
            flush=True,
        )
        print(
            "[Sprint141-7 Closed Loop Persistence] Generation Runs:",
            len(list((closed_loop_result or {}).get("generation_runs") or [])),
            flush=True,
        )
        print(
            "[Sprint141-7 Closed Loop Persistence] Fidelity Results:",
            len(list((closed_loop_result or {}).get("fidelity_results") or [])),
            flush=True,
        )
        print(
            "[Sprint141-7 Closed Loop Persistence] Errors:",
            persistence_result.get("errors", []),
            flush=True,
        )

        closed_loop_ok = bool(
            (closed_loop_result or {}).get("ok")
        )
        closed_loop_ready = bool(
            (closed_loop_result or {}).get("ready")
        )
        resolved_status = str(
            (closed_loop_result or {}).get("status")
            or "closed_loop_completed"
        )

        required_scene_count = int(
            (closed_loop_result or {}).get("closed_loop_scene_count") or 0
        )
        all_scenes_passed = bool(
            (closed_loop_result or {}).get("closed_loop_all_passed")
        )

        if selected_image_count <= 0:
            closed_loop_ok = False
            closed_loop_ready = False
            resolved_status = "blocked_no_generated_images"
            result["empty_generation_blocked"] = True
            result["errors"].append(
                "Gemini 생성 이미지가 0장이므로 다음 영상 제작 단계 진입을 차단했습니다."
            )
            print(
                "[Sprint154 Quality Gate] Blocked: no generated images",
                flush=True,
            )
        elif required_scene_count > 0 and not all_scenes_passed:
            closed_loop_ok = False
            closed_loop_ready = False
            resolved_status = "blocked_failed_scene_quality"
            result["empty_generation_blocked"] = False
            result["errors"].append(
                "검수 실패 장면이 남아 있어 영상 제작 단계 진입을 차단했습니다."
            )
            print(
                "[Sprint154 Quality Gate] Blocked: failed scenes remain",
                flush=True,
            )
        else:
            print(
                "[Sprint154 Quality Gate] Passed: all required scenes accepted",
                flush=True,
            )

        result.update(
            ok=closed_loop_ok,
            ready=closed_loop_ready,
            status=resolved_status,
            closed_loop_result=closed_loop_result,
            selected_image_count=selected_image_count,
            selected_image_paths=selected_image_paths,
            passed_scene_count=passed_scene_count,
            failed_scene_count=failed_scene_count,
            provider_failure_count=len(result["provider_failures"]),
            persistence=persistence_result,
        )
        if persistence_result.get("errors"):
            result["warnings"].extend(persistence_result["errors"])
        return result


    def _sprint112_1_clean_render_text(self, value, stats):
        """Sprint112-1: 화면 자막에서 내부 장면 연출 문구를 제거합니다."""
        if not isinstance(value, str):
            return value

        blocked_prefixes = (
            "장면연출", "장면 연출", "연출:", "연출 :",
            "scene goal", "scene_goal", "visual direction",
            "visual_direction", "must show", "must_show",
            "camera instruction", "camera_instruction",
            "director note", "director_note", "purpose:",
        )

        kept = []
        removed = 0
        for raw_line in value.replace("\\r\\n", "\n").splitlines():
            line = raw_line.strip()
            lowered = line.lower()
            if any(lowered.startswith(prefix) for prefix in blocked_prefixes):
                removed += 1
                continue
            if line:
                kept.append(line)

        if removed:
            stats["director_prompt_removed"] += removed
        return "\n".join(kept).strip()

    def _sprint112_1_render_guard(self, payload):
        """
        Sprint112-1 Final Render Input Guard.

        - 리뷰/댓글 장면의 이미지 목록은 장면당 한 장만 유지
        - 내부 Director 지시 필드는 최종 렌더 입력에서 제거
        - subtitle/caption은 narration 또는 spoken_text가 있으면 그 값을 우선 사용
        """
        stats = {
            "review_images_removed": 0,
            "review_scenes_checked": 0,
            "director_fields_removed": 0,
            "director_prompt_removed": 0,
            "subtitle_source": "review_script_scene_subtitles_only",
        }

        # Sprint131-8: 최종 화면 자막은 ReviewScriptGenerator가 만든
        # scene_subtitles만 허용합니다. Director의 goal/prompt는 절대 자막으로 쓰지 않습니다.
        canonical_by_scene_id = {}
        canonical_by_purpose = {}
        if isinstance(payload, dict):
            review_scripts = payload.get("review_scripts") or {}
            if isinstance(review_scripts, dict):
                for item in list(review_scripts.get("scene_subtitles") or []):
                    if not isinstance(item, dict):
                        continue
                    subtitle = self._sprint112_1_clean_render_text(
                        str(item.get("subtitle") or ""),
                        stats,
                    )
                    if not subtitle:
                        continue
                    scene_id = str(item.get("scene_id") or "").strip()
                    purpose = str(item.get("purpose") or "").strip().lower()
                    if scene_id:
                        canonical_by_scene_id[scene_id] = subtitle
                    if purpose and purpose not in canonical_by_purpose:
                        canonical_by_purpose[purpose] = subtitle

        director_keys = {
            "scene_goal", "visual_direction", "must_show",
            "camera_instruction", "director_note", "director_prompt",
            "camera_prompt", "shot_instruction", "motion_instruction",
            "generation_prompt", "veo_prompt", "prompt_for_video",
        }
        text_keys = {
            "subtitle", "subtitles", "caption", "caption_text",
            "narration", "spoken_text", "voiceover", "voice_over",
            "script", "text", "display_text",
        }
        image_key_tokens = (
            "image", "images", "image_path", "image_paths",
            "review_image", "review_images", "media", "assets",
            "reference_images", "selected_images",
        )

        def role_text(node):
            values = []
            for key in ("role", "image_role", "scene_role", "purpose", "type", "scene_type"):
                value = node.get(key)
                if value is not None:
                    values.append(str(value).lower())
            return " ".join(values)

        def unique_items(items):
            seen = set()
            result = []
            for item in items:
                marker = str(item)
                if marker in seen:
                    continue
                seen.add(marker)
                result.append(item)
            return result

        def walk(value, review_context=False):
            if isinstance(value, dict):
                local_review = review_context or any(
                    token in role_text(value)
                    for token in ("review", "comment", "후기", "댓글")
                )
                if local_review:
                    stats["review_scenes_checked"] += 1

                result = {}
                preferred_spoken = ""
                for source_key in ("narration", "spoken_text", "voiceover", "voice_over", "script"):
                    source_value = value.get(source_key)
                    if isinstance(source_value, str) and source_value.strip():
                        preferred_spoken = self._sprint112_1_clean_render_text(source_value, stats)
                        if preferred_spoken:
                            break

                scene_id_value = str(value.get("scene_id") or "").strip()
                purpose_value = str(value.get("purpose") or value.get("role") or "").strip().lower()
                canonical_subtitle = (
                    canonical_by_scene_id.get(scene_id_value)
                    or canonical_by_purpose.get(purpose_value)
                    or preferred_spoken
                )

                for key, child in value.items():
                    key_lower = str(key).lower()
                    if key_lower in director_keys or any(
                        token in key_lower
                        for token in ("scene_goal", "visual_direction", "must_show", "camera_instruction", "director_note")
                    ):
                        stats["director_fields_removed"] += 1
                        continue

                    if key_lower in text_keys and isinstance(child, str):
                        if key_lower in {"subtitle", "subtitles", "caption", "caption_text", "display_text"}:
                            # Sprint131-8: 장면 연출/목표 문구가 들어 있더라도 무시하고
                            # 실제 대본 장면 자막으로 교체합니다.
                            result[key] = canonical_subtitle or ""
                        else:
                            result[key] = self._sprint112_1_clean_render_text(child, stats)
                        continue

                    if local_review and isinstance(child, list) and any(
                        token in key_lower for token in image_key_tokens
                    ):
                        deduped = unique_items(child)
                        if len(deduped) > 1:
                            stats["review_images_removed"] += len(deduped) - 1
                            deduped = deduped[:1]
                        result[key] = [walk(item, True) for item in deduped]
                        continue

                    result[key] = walk(child, local_review)
                return result

            if isinstance(value, list):
                return [walk(item, review_context) for item in value]

            if isinstance(value, tuple):
                return tuple(walk(item, review_context) for item in value)

            return value

        guarded = walk(payload)
        return guarded, stats

    def _run_sprint143_2_viral_script_feedback(
        self,
        viral_pipeline_result,
        review_script_result,
        product_name,
    ):
        """최종 대본 장면 자막을 viral_story와 viral_director에 다시 반영합니다."""
        result = {
            "ok": False,
            "ready": False,
            "version": "viral-script-director-feedback-143-3",
            "status": "not_started",
            "story": {},
            "director": {},
            "errors": [],
            "warnings": [],
        }
        try:
            pipeline = viral_pipeline_result if isinstance(viral_pipeline_result, dict) else {}
            script = review_script_result if isinstance(review_script_result, dict) else {}
            output_dir = Path(str(pipeline.get("output_dir") or "")).expanduser()
            if not pipeline.get("ok") or not output_dir:
                result["status"] = "skipped_no_viral_pipeline"
                result["warnings"].append("사용 가능한 Viral Pipeline 결과가 없습니다")
                return result
            scenes_path = output_dir / "viral_scenes.json"
            if not scenes_path.is_file():
                step = pipeline.get("steps", {}).get("scene_detector", {})
                candidate = Path(str(step.get("output_path") or "")).expanduser()
                if candidate.is_file():
                    scenes_path = candidate
            if not scenes_path.is_file():
                result["status"] = "skipped_no_viral_scenes"
                result["warnings"].append(f"viral_scenes.json 없음: {scenes_path}")
                return result

            from modules.content.viral.viral_story_analyzer import ViralStoryAnalyzer
            from modules.content.viral.viral_director import ViralDirector

            story_path = output_dir / "viral_story.json"
            director_path = output_dir / "viral_director.json"
            story_result = ViralStoryAnalyzer().analyze(
                scenes_path=scenes_path,
                output_path=story_path,
                product_name=product_name,
                script_result=script,
            )
            director_result = {}
            if story_result.get("ok"):
                director_result = ViralDirector().build(
                    story_path=story_path,
                    output_path=director_path,
                    product_name=product_name,
                )
            story_scene_count = int(story_result.get("scene_count") or 0)
            director_scene_count = int(director_result.get("scene_count") or 0)
            scene_count_consistent = bool(
                story_scene_count > 0 and story_scene_count == director_scene_count
            )
            result.update({
                "ok": bool(story_result.get("ok") and director_result.get("ok") and scene_count_consistent),
                "ready": bool(story_result.get("ok") and director_result.get("ok") and scene_count_consistent),
                "status": "closed_loop_completed"
                if story_result.get("ok") and director_result.get("ok") and scene_count_consistent
                else "closed_loop_failed",
                "story": story_result,
                "director": director_result,
                "story_scene_count": story_scene_count,
                "director_scene_count": director_scene_count,
                "scene_count_consistent": scene_count_consistent,
            })
            if story_result.get("ok") and director_result.get("ok") and not scene_count_consistent:
                result["errors"].append(
                    f"scene_count_mismatch: story={story_scene_count}, director={director_scene_count}"
                )
        except Exception as exc:
            result["status"] = "exception"
            result["errors"].append(f"{type(exc).__name__}: {exc}")

        print("######## SPRINT143-3 VIRAL SCRIPT DIRECTOR CLOSED LOOP ########", flush=True)
        print("[Sprint143-3 Closed Loop] Version:", result.get("version", ""), flush=True)
        print("[Sprint143-3 Closed Loop] Status:", result.get("status", ""), flush=True)
        print("[Sprint143-3 Closed Loop] Story Used:", result.get("story", {}).get("script_feedback", {}).get("used", False), flush=True)
        print("[Sprint143-3 Closed Loop] Story Scenes:", result.get("story_scene_count", 0), flush=True)
        print("[Sprint143-3 Closed Loop] Director Scenes:", result.get("director_scene_count", 0), flush=True)
        print("[Sprint143-3 Closed Loop] Scene Count Consistent:", result.get("scene_count_consistent", False), flush=True)
        print("[Sprint143-3 Closed Loop] Errors:", result.get("errors", []), flush=True)
        return result

    def _resolve_sprint137_viral_video_path(
        self,
        viral_video_sources=None,
        viral_library_result=None,
    ):
        """Sprint137-1: 수동 입력 또는 Viral Library 결과에서 실제 영상 파일을 찾습니다."""
        supported = {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv"}
        candidates = []

        def collect(value):
            if value is None:
                return
            if isinstance(value, (str, Path)):
                candidates.append(str(value))
                return
            if isinstance(value, dict):
                priority_keys = (
                    "local_path", "video_path", "saved_path", "output_path",
                    "download_path", "file_path", "path", "source_path",
                )
                for key in priority_keys:
                    if value.get(key):
                        collect(value.get(key))
                for key, child in value.items():
                    if key not in priority_keys:
                        collect(child)
                return
            if isinstance(value, (list, tuple, set)):
                for child in value:
                    collect(child)

        collect(viral_video_sources or [])
        collect(viral_library_result or {})

        seen = set()
        for raw_value in candidates:
            value = str(raw_value or "").strip()
            if not value or value.lower().startswith(("http://", "https://")):
                continue
            path = Path(value).expanduser()
            try:
                key = str(path.resolve()).lower()
            except Exception:
                key = str(path).lower()
            if key in seen:
                continue
            seen.add(key)
            if path.is_file() and path.suffix.lower() in supported:
                return str(path)
        return ""


    def _run_sprint145_2_script_first_only(
        self,
        project,
        review_text,
        viral_video_sources,
        declared_review_count=0,
        review_checked_at="",
        rating=0,
        monthly_purchase_count=0,
        input_product_name="",
    ):
        """현재 실행에서 전달된 상품명·리뷰만 사용해 최종 대본을 생성합니다."""
        project_product_name = str(
            getattr(project, "product_name", "")
            or getattr(project, "title", "")
            or ""
        ).strip()
        product_name = str(input_product_name or project_product_name or "선택 상품").strip()
        project_id = str(getattr(project, "id", "") or "default")
        output_dir = Path("assets") / "products" / f"project_{project_id}"
        output_dir.mkdir(parents=True, exist_ok=True)

        normalized_review_text = str(review_text or "").strip()
        review_hash = hashlib.sha256(normalized_review_text.encode("utf-8")).hexdigest()
        isolation_errors = []
        if not product_name:
            isolation_errors.append("missing_current_product_name")
        if input_product_name and project_product_name and product_name != project_product_name:
            isolation_errors.append("project_product_name_mismatch")

        print(
            "[Sprint146-3 Project Isolation] INPUT",
            {
                "project_id": project_id,
                "input_product_name": str(input_product_name or ""),
                "project_product_name": project_product_name,
                "resolved_product_name": product_name,
                "review_chars": len(normalized_review_text),
                "review_hash": review_hash,
                "errors": isolation_errors,
            },
            flush=True,
        )

        raw_blocks = [
            " ".join(block.split()).strip()
            for block in re.split(r"\n\s*\n|(?<=\.)\s*\n", normalized_review_text)
            if " ".join(block.split()).strip()
        ]
        if len(raw_blocks) <= 1:
            raw_blocks = [
                " ".join(line.split()).strip()
                for line in str(review_text or "").splitlines()
                if " ".join(line.split()).strip()
            ]
        reviews = raw_blocks
        declared_count = max(0, int(declared_review_count or 0))
        project_data = self._project_data(project)
        stored_rating = self._find_nested_value(
            project_data,
            ("rating", "review_rating", "star_rating", "product_rating"),
        )
        stored_monthly = self._find_nested_value(
            project_data,
            (
                "monthly_purchase_count",
                "recent_month_purchase_count",
                "monthly_purchases",
                "purchase_count_monthly",
                "recent_purchase_count",
            ),
        )
        try:
            trust_rating = float(rating or stored_rating or 0)
        except Exception:
            trust_rating = 0.0
        trust_rating = max(0.0, min(5.0, trust_rating))
        try:
            trust_monthly_purchases = max(0, int(monthly_purchase_count or stored_monthly or 0))
        except Exception:
            trust_monthly_purchases = 0

        print(
            "[Sprint145-21 Trust Resolve]",
            {
                "argument_monthly": monthly_purchase_count,
                "stored_monthly": stored_monthly,
                "resolved_monthly": trust_monthly_purchases,
                "argument_rating": rating,
                "stored_rating": stored_rating,
                "resolved_rating": trust_rating,
            },
            flush=True,
        )


        outputs = {
            "workflow_version": self.WORKFLOW_VERSION,
            "execution_mode": "locked_script_full_pipeline",
            "product_name": product_name,
            "project_identity": {
                "version": "project-review-isolation-146-3",
                "project_id": project_id,
                "input_product_name": str(input_product_name or "").strip(),
                "project_product_name": project_product_name,
                "resolved_product_name": product_name,
                "review_hash": review_hash,
                "review_character_count": len(normalized_review_text),
            },
            "review_metadata": {
                "declared_review_count": declared_count,
                "parsed_review_count": len(reviews),
                "review_checked_at": str(review_checked_at or "").strip(),
                "rating": trust_rating,
                "monthly_purchase_count": trust_monthly_purchases,
            },
            "input_gate": {
                "product_name_ready": bool(product_name),
                "review_text_ready": bool(str(review_text or "").strip()),
                "review_count_ready": declared_count > 0,
                "review_checked_at_ready": bool(str(review_checked_at or "").strip()),
                "viral_link_optional": True,
                "viral_link_ready": bool(viral_video_sources),
            },
        }

        errors = list(isolation_errors)
        if not normalized_review_text: errors.append("리뷰 텍스트가 없습니다.")
        if declared_count <= 0: errors.append("리뷰 개수가 1개 이상이어야 합니다.")
        if not str(review_checked_at or "").strip(): errors.append("리뷰 확인일이 없습니다.")
        print(
            "[Sprint145-16 Viral Optional]",
            {
                "provided": bool(viral_video_sources),
                "source_count": len(viral_video_sources or []),
                "required": False,
            },
            flush=True,
        )

        if errors:
            status = {"status": "REVISION_REQUIRED", "approved": False, "errors": errors}
            outputs["script_approval"] = status
            print("[Sprint145-14 Sales Quality] SCRIPT STATUS: REVISION_REQUIRED", flush=True)
            return {"job_id": uuid4().hex[:12], "state": {}, "outputs": outputs, "summary": "대본 입력 검증 실패", "script_status": "REVISION_REQUIRED"}

        try:
            insight = ReviewInsightEngine().analyze(
                reviews=reviews, social_comments=[], product_name=product_name
            )
        except Exception as exc:
            insight = {"ok": False, "review_count": len(reviews), "error": f"{type(exc).__name__}: {exc}"}
        if isinstance(insight, dict):
            insight_name = str(insight.get("product_name") or "").strip()
            if insight_name and insight_name != product_name:
                errors.append("review_insight_product_name_mismatch")
            insight["product_name"] = product_name
            insight["project_id"] = project_id
            insight["review_hash"] = review_hash
        outputs["review_insight"] = insight

        print(
            "[Sprint146-3 Project Isolation] REVIEW_INSIGHT",
            {"product_name": product_name, "project_id": project_id, "review_hash": review_hash, "errors": errors},
            flush=True,
        )

        try:
            quotes = ReviewQuoteSelector().select(reviews=reviews, product_name=product_name, top_n=5)
        except Exception as exc:
            quotes = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        outputs["review_quotes"] = quotes

        try:
            hooks = ReviewHookGenerator().generate(
                review_quotes=quotes, review_insight=insight, product_name=product_name,
                review_count=declared_count or len(reviews),
            )
            hooks = HookOptimizer().apply_to_review_hooks(
                review_hooks=hooks, review_insight=insight, product_name=product_name,
                review_count=declared_count or len(reviews),
            )
        except Exception as exc:
            hooks = {"ok": False, "best_hook": "", "error": f"{type(exc).__name__}: {exc}"}
        if isinstance(hooks, dict):
            hook_name = str(hooks.get("product_name") or "").strip()
            if hook_name and hook_name != product_name:
                errors.append("review_hooks_product_name_mismatch")
            hooks["product_name"] = product_name
            hooks["project_id"] = project_id
            hooks["review_hash"] = review_hash
        outputs["review_hooks"] = hooks

        viral_provided = bool(viral_video_sources)
        viral_library = {
            "ok": True,
            "ready": False,
            "status": "skipped_optional_no_source" if not viral_provided else "not_run",
            "items": [],
            "requested_count": len(viral_video_sources or []),
        }
        viral_pipeline = {
            "ok": True,
            "ready": False,
            "status": "skipped_optional_no_source" if not viral_provided else "not_run",
            "errors": [],
        }

        print(
            "[Sprint145-17 Viral Optional]",
            {
                "provided": viral_provided,
                "source_count": len(viral_video_sources or []),
                "library_skipped": not viral_provided,
                "pipeline_skipped": not viral_provided,
            },
            flush=True,
        )

        if viral_provided:
            try:
                viral_library = ViralLibraryIngestor(max_items=10).ingest(
                    sources=viral_video_sources,
                    project_id=project_id,
                    overwrite=True,
                    save=True,
                )
                local_video = self._resolve_sprint137_viral_video_path(
                    viral_video_sources=viral_video_sources,
                    viral_library_result=viral_library,
                )
                if local_video:
                    viral_pipeline = run_viral_pipeline(
                        video_path=local_video,
                        output_dir=output_dir / "viral_pipeline_145_2",
                        product_name=product_name,
                        product_description="",
                        brand_name="",
                        best_hook=str(hooks.get("best_hook") or "").strip(),
                        best_pain=str(
                            quotes.get("best_pain")
                            or insight.get("best_pain")
                            or insight.get("best_pain_point")
                            or ""
                        ).strip(),
                        best_benefit=str(
                            quotes.get("best_benefit")
                            or insight.get("best_benefit")
                            or ""
                        ).strip(),
                        best_evidence=str(
                            quotes.get("best_quote")
                            or insight.get("best_evidence")
                            or ""
                        ).strip(),
                        cta_text="구매 전 상세 정보와 실제 사용 조건을 확인해 보세요",
                        frame_interval_seconds=2.0,
                        max_thumbnail_count=30,
                        overwrite=True,
                    )
                else:
                    viral_pipeline = {
                        "ok": False,
                        "ready": False,
                        "status": "no_local_video",
                        "errors": ["바이럴 링크에서 분석 가능한 영상을 확보하지 못했습니다."],
                    }
            except Exception as exc:
                viral_pipeline = {
                    "ok": False,
                    "ready": False,
                    "status": "exception",
                    "errors": [f"{type(exc).__name__}: {exc}"],
                }

        outputs["viral_library"] = viral_library
        outputs["viral_pipeline"] = viral_pipeline

        try:
            script = ReviewScriptGenerator().generate(
                review_hooks=hooks, review_quotes=quotes, review_insight=insight,
                product_name=product_name, review_count=declared_count or len(reviews),
                story_intelligence={}, viral_pipeline=viral_pipeline,
                rating=trust_rating, monthly_purchase_count=trust_monthly_purchases,
                review_checked_at=review_checked_at,
            )
        except Exception as exc:
            script = {"ok": False, "best_script": "", "scripts": [], "errors": [f"{type(exc).__name__}: {exc}"]}
        if isinstance(script, dict):
            script_name = str(script.get("product_name") or "").strip()
            if script_name and script_name != product_name:
                errors.append("review_scripts_product_name_mismatch")
            script["product_name"] = product_name
            script["project_id"] = project_id
            script["review_hash"] = review_hash
        outputs["review_scripts"] = script
        print(
            "[Sprint146-3 Project Isolation] SCRIPT",
            {"product_name": product_name, "project_id": project_id, "review_hash": review_hash, "errors": errors},
            flush=True,
        )
        print("[Sprint145-14 Trust] Rating:", trust_rating, flush=True)
        print("[Sprint145-14 Trust] Review Count:", declared_count, flush=True)
        print("[Sprint145-14 Trust] Monthly Purchases:", trust_monthly_purchases, flush=True)
        print("[Sprint145-14 Trust] Structure: READY", flush=True)

        best_script = str(script.get("best_script") or "").strip()
        validation_errors = list(dict.fromkeys(errors))
        if not bool(insight.get("ok")):
            validation_errors.append("review_analysis_failed")
        if not bool(script.get("ok")):
            validation_errors.append("script_generation_failed")

        # Sprint145-17: 바이럴은 선택 입력입니다.
        # 입력한 경우에만 바이럴 분석과 대본 반영 여부를 승인 조건으로 검사합니다.
        if viral_provided:
            if not bool(viral_pipeline.get("ready") or viral_pipeline.get("ok")):
                validation_errors.append("viral_analysis_failed")
            if not bool(script.get("viral_influence_used")):
                validation_errors.append("viral_influence_missing")

        closed_loop = ScriptClosedLoop(max_revisions=3).run(
            script_text=best_script,
            validator=ReviewScriptGenerator().validate_script_quality,
            product_name=product_name,
            review_insight=insight,
            review_quotes=quotes,
        )
        outputs["script_closed_loop"] = closed_loop

        final_script = str(closed_loop.get("final_script") or best_script).strip()
        quality_validation = dict(closed_loop.get("final_validation") or {})

        # Sprint145-20: 소비자 언어로 정리된 신뢰 대본을 최종 원본으로 잠급니다.
        # ScriptClosedLoop와 ScriptRevisionEngine은 진단 정보만 남기며,
        # 고정 후킹·리뷰 확인 문장·CTA를 다시 쓰지 못합니다.
        canonical_script = best_script

        # Sprint145-21: 생성기 내부 전달 누락이 있어도 workflow에서 확인된 신뢰 수치를
        # 최종 대본 첫 문장에 강제로 복원합니다.
        trust_lines = []
        if trust_monthly_purchases > 0:
            trust_lines.append(f"최근 한 달 {trust_monthly_purchases:,}명 이상이 구매한 제품!")
        if declared_count > 0:
            trust_lines.append(f"찐리뷰 {declared_count:,}개!")
        if trust_rating > 0:
            rounded_half = int(trust_rating * 2 + 0.5) / 2
            full_stars = int(rounded_half)
            stars = ("⭐" * full_stars) + ("½" if rounded_half - full_stars >= 0.5 else "")
            trust_lines.append(f"평점 {trust_rating:.1f}점! {stars}".strip())

        body = str(canonical_script or "").strip()
        body = re.sub(r"^(?:최근 한 달 [^.!?]+[.!?]?\s*)", "", body)
        body = re.sub(r"^(?:찐리뷰 [0-9,]+개![ ]*)", "", body)
        body = re.sub(r"^(?:평점 [0-9.]+점![^가-힣A-Za-z0-9]*\s*)", "", body)
        final_script = " ".join([*trust_lines, body]).strip()

        quality_validation = ReviewScriptGenerator().validate_script_quality(
            script_text=final_script,
            product_name=product_name,
        )
        final_spoken_revision = {
            "version": "trust-script-final-lock-145-21",
            "status": "skipped_canonical_trust_script",
            "revised_text": final_script,
            "changes": [],
            "reason": "고정 신뢰 후킹과 CTA 보존을 위해 마지막 재작성을 건너뛰었습니다.",
        }
        outputs["final_spoken_revision"] = final_spoken_revision
        outputs["script_quality_validation"] = quality_validation
        outputs["trust_script_final_lock"] = {
            "version": "trust-script-final-lock-145-21",
            "locked": True,
            "hook": " ".join(trust_lines).strip(),
            "review_bridge_required": True,
            "cta": "👉 궁금하시면 클릭! 👇",
            "final_script": final_script,
        }
        print("######## SPRINT145-21 CONSUMER TRUST SCRIPT FINAL LOCK READY ########", flush=True)
        print("[Sprint145-21 Final Lock] Locked:", True, flush=True)
        print("[Sprint145-21 Final Lock] Hook:", outputs["trust_script_final_lock"]["hook"], flush=True)
        print("[Sprint145-21 Final Lock] CTA:", outputs["trust_script_final_lock"]["cta"], flush=True)
        print("[Sprint145-21 Final Lock] Script:", final_script, flush=True)
        print("[Sprint145-21 Final Lock] Validation:", quality_validation.get("status", ""), quality_validation.get("errors", []), flush=True)

        # 생성·리뷰·바이럴 단계의 구조적 실패는 자동 문장 수정으로 숨기지 않습니다.
        # 대본 문장 품질 오류만 Closed Loop에서 최대 3회 자동 수정합니다.
        final_errors = list(validation_errors)
        quality_error_codes = set(quality_validation.get("errors") or [])
        initial_quality_codes = {
            "incomplete_sentence",
            "duplicate_content",
            "duplicate_cta",
            "invalid_context_transition",
            "script_too_short",
            "hook_score_low",
            "flow_score_low",
            "review_naturalness_low",
            "sales_persuasion_low",
            "shorts_rhythm_low",
            "cta_quality_low",
            "sales_quality_score_low",
        }
        final_errors = [
            error for error in final_errors
            if error not in initial_quality_codes
        ]
        for error_code in quality_error_codes:
            if error_code not in final_errors:
                final_errors.append(error_code)

        approved = bool(final_script) and bool(quality_validation.get("approved") or quality_validation.get("passed") or quality_validation.get("status") == "APPROVED") and not final_errors
        script_status = "APPROVED" if approved else (
            "FAILED_MAX_RETRY"
            if closed_loop.get("status") == "FAILED_MAX_RETRY"
            else "REVISION_REQUIRED"
        )
        duplicated = list(quality_validation.get("duplicate_sentences") or [])
        approval = {
            "version": "script-approval-gate-145-19",
            "status": script_status,
            "approved": approved,
            "errors": final_errors,
            "duplicate_sentences": duplicated,
            "quality_validation": quality_validation,
            "closed_loop_version": closed_loop.get("version", ""),
            "sales_quality_score": float(closed_loop.get("sales_quality_score", 0) or 0),
            "sales_quality_scores": dict(closed_loop.get("scores") or {}),
            "revision_count": int(closed_loop.get("revision_count", 0) or 0),
            "validation_count": int(closed_loop.get("validation_count", 0) or 0),
            "max_revisions": int(closed_loop.get("max_revisions", 3) or 3),
            "review_count": declared_count,
            "review_checked_at": str(review_checked_at or "").strip(),
            "rating": trust_rating,
            "monthly_purchase_count": trust_monthly_purchases,
            "trust_profile": dict(script.get("trust_profile") or {}),
            "viral_influence_used": bool(script.get("viral_influence_used")),
            "best_script_type": script.get("best_script_type", ""),
            "best_script": final_script,
            "original_script": best_script,
        }
        outputs["review_scripts"]["original_best_script"] = best_script
        outputs["review_scripts"]["best_script"] = final_script
        outputs["review_scripts"]["script_closed_loop"] = closed_loop
        outputs["script_approval"] = approval
        result_path = output_dir / "script_first_result_146_4.json"
        result_path.write_text(json.dumps(outputs, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        outputs["script_result_path"] = str(result_path)
        next_stage_status = (
            "READY_APPROVED_FULL_PIPELINE"
            if approved
            else "BLOCKED_SCRIPT_NOT_APPROVED"
        )
        outputs["next_stage_gate"] = {
            "version": "locked-script-full-pipeline-gate-146-5b",
            "execution_mode": "locked_script_full_pipeline",
            "status": next_stage_status,
            "script_approved": approved,
            "scene_image_motion_video_executed": False,
            "reason": (
                "승인된 대본을 잠그고 ImageMotion 이후 전체 영상 파이프라인을 실행합니다."
                if approved
                else "대본이 승인되지 않아 후속 단계를 실행하지 않았습니다."
            ),
        }
        # next_stage_gate를 포함한 최종 결과를 다시 저장합니다.
        result_path.write_text(
            json.dumps(outputs, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        print(f"[Sprint145-14 Sales Quality] SCRIPT STATUS: {script_status}", flush=True)
        print(
            f"[Sprint145-14 Sales Quality] Scene/Image/Motion/Video: {next_stage_status}",
            flush=True,
        )
        print(
            "[Sprint145-14 Sales Quality] Result Path:",
            str(result_path),
            flush=True,
        )
        return {
            "job_id": uuid4().hex[:12], "state": {}, "outputs": outputs,
            "summary": "최종 대본 승인 완료" if approved else "대본 자동 수정 한도 초과",
            "script_status": script_status,
            "next_stage_status": next_stage_status,
        }

    def _sprint147_3_generate_one_image(self, prompt_item, output_path):
        """Sprint150-3: 참조 이미지 누락을 프로젝트 원본으로 복구하고 생성기 오류를 전달합니다."""
        generator_class = None
        import_errors = []
        for module_name, class_name in (
            ("modules.image_ai.gemini_image_generator", "GeminiImageGenerator"),
            ("modules.image_ai.ai_image_generator", "AIImageGenerator"),
        ):
            try:
                module = __import__(module_name, fromlist=[class_name])
                candidate = getattr(module, class_name, None)
                if candidate is not None:
                    generator_class = candidate
                    break
            except Exception as exc:
                import_errors.append(f"{module_name}: {type(exc).__name__}: {exc}")
        if generator_class is None:
            raise RuntimeError("이미지 생성기 import 실패: " + " | ".join(import_errors))

        engine = generator_class()
        output_path = Path(str(output_path))
        output_path.parent.mkdir(parents=True, exist_ok=True)

        reference_image_paths = prompt_item.get("reference_image_paths") or []
        if not isinstance(reference_image_paths, (list, tuple, set)):
            reference_image_paths = [reference_image_paths] if str(reference_image_paths or "").strip() else []

        # Sprint150-3: AIImageDirector/ClosedLoop에서 참조 경로가 유실되더라도
        # 현재 프로젝트의 실제 업로드 원본 1장을 반드시 복구합니다.
        reference_candidates = []

        def _add_reference(value):
            if isinstance(value, dict):
                value = (
                    value.get("path")
                    or value.get("image_path")
                    or value.get("selected_image_path")
                    or value.get("reference_image_path")
                    or ""
                )
            text_value = str(value or "").strip()
            if not text_value:
                return
            candidate = Path(text_value).expanduser()
            if candidate.is_file():
                normalized = str(candidate)
                if normalized not in reference_candidates:
                    reference_candidates.append(normalized)

        _add_reference(prompt_item.get("reference_image_path"))
        for item in reference_image_paths:
            _add_reference(item)

        for key in (
            "selected_image_path",
            "existing_image_path",
            "product_image_path",
            "source_image_path",
            "image_path",
        ):
            _add_reference(prompt_item.get(key))

        source_scene = prompt_item.get("source_scene")
        if isinstance(source_scene, dict):
            _add_reference(source_scene.get("reference_image_path"))
            for item in list(source_scene.get("reference_image_paths") or []):
                _add_reference(item)
            for key in (
                "selected_image_path",
                "existing_image_path",
                "product_image_path",
                "source_image_path",
                "image_path",
            ):
                _add_reference(source_scene.get(key))

        # direct_output_dir는 assets/products/project_N/generated_review이므로
        # 그 상위 프로젝트 폴더에서 00_main.* 및 원본 업로드 파일을 탐색합니다.
        project_dir = output_path.parent.parent
        if project_dir.is_dir():
            for name in (
                "00_main.png", "00_main.jpg", "00_main.jpeg", "00_main.webp",
                "main.png", "main.jpg", "main.jpeg", "main.webp",
            ):
                _add_reference(project_dir / name)
            for pattern in ("*_main.png", "*_main.jpg", "*_main.jpeg", "*_main.webp"):
                for candidate in sorted(project_dir.glob(pattern)):
                    _add_reference(candidate)

        reference_image_path = reference_candidates[0] if reference_candidates else ""
        print(
            "[Sprint150-3 Reference Route]",
            {
                "scene_id": str(prompt_item.get("scene_id") or output_path.stem),
                "project_dir": str(project_dir),
                "reference_image_path": reference_image_path,
                "reference_image_count": len(reference_candidates),
            },
            flush=True,
        )

        payload = {
            "scene_id": str(prompt_item.get("scene_id") or output_path.stem),
            "attempt": 1,
            "prompt": str(prompt_item.get("prompt") or prompt_item.get("image_prompt") or ""),
            "image_prompt": str(prompt_item.get("prompt") or prompt_item.get("image_prompt") or ""),
            "negative_prompt": str(prompt_item.get("negative_prompt") or ""),
            "reference_image_path": reference_image_path,
            "reference_image_paths": reference_candidates[:1],
            "require_reference_image": bool(prompt_item.get("require_reference_image", True)),
            "output_image_path": str(output_path),
            "output_path": str(output_path),
            "overwrite": True,
        }

        last_error = None
        for method_name in ("generate_image", "generate", "run", "create"):
            method = getattr(engine, method_name, None)
            if not callable(method):
                continue
            try:
                raw = method(**payload)
            except TypeError as exc:
                last_error = exc
                try:
                    raw = method(payload)
                except Exception as positional_exc:
                    last_error = positional_exc
                    continue
            except Exception as exc:
                last_error = exc
                continue

            candidate_path = ""
            if isinstance(raw, dict):
                candidate_path = str(
                    raw.get("output_image_path")
                    or raw.get("output_path")
                    or raw.get("image_path")
                    or raw.get("path")
                    or ""
                )
                if not bool(raw.get("ok")):
                    status = str(raw.get("status") or "generator_failed")
                    errors = raw.get("errors") or []
                    warnings = raw.get("warnings") or []
                    detail = " | ".join(str(item) for item in errors if str(item).strip())
                    warning_detail = " | ".join(str(item) for item in warnings if str(item).strip())
                    print(
                        "[Sprint150-2 Generator Result]",
                        {
                            "scene_id": payload["scene_id"],
                            "version": raw.get("version"),
                            "status": status,
                            "reference_image_path": raw.get("reference_image_path"),
                            "reference_image_count": raw.get("reference_image_count"),
                            "errors": errors,
                            "warnings": warnings,
                        },
                        flush=True,
                    )
                    message = f"이미지 생성 실패 [{status}]"
                    if detail:
                        message += f": {detail}"
                    if warning_detail:
                        message += f" | warnings: {warning_detail}"
                    raise RuntimeError(message)
            elif isinstance(raw, (str, Path)):
                candidate_path = str(raw)

            if candidate_path and Path(candidate_path).is_file():
                return str(candidate_path)
            if output_path.is_file():
                return str(output_path)

            last_error = RuntimeError(
                f"이미지 생성기가 성공 결과를 반환했지만 파일이 없습니다: {candidate_path or output_path}"
            )

        if last_error is not None:
            raise last_error
        raise RuntimeError("호출 가능한 이미지 생성 메서드를 찾지 못했습니다.")

    def _run_gemini_video_scope(
        self,
        project,
        hook_text="",
        locked_script="",
        cta_text="",
        cta_product_logo_text="",
        voice_audio_path="",
        bgm_audio_path="",
        bgm_volume_percent=10,
        voice_name="지안",
        voice_id="",
        typecast_api_key="",
        tts_volume_percent=100,
        tts_speech_speed=1.0,
        clip_subtitles=None,
        clip_subtitle_effects=None,
        clip_sfx=None,
        clip_playback_speeds=None,
        clip_narrations=None,
        gemini_clip_count=4,
        supplied_clip_paths=None,
        playback_speed=1.5,
        channel_type="shopping",
        monthly_purchase_count=0,
        declared_review_count=0,
        rating=0.0,
        trust_card_duration=3.4,
        youtube_privacy_status="private",
        upload_enabled=False,
        reservation_payload=None,
    ):
        """Sprint172-1: 이미지/Vision/Scene Planner를 우회하는 Gemini 영상 전용 경로."""
        project_id = str(getattr(project, "id", "") or "default")
        product_name = str(
            getattr(project, "product_name", "")
            or getattr(project, "title", "")
            or "상품"
        ).strip()
        normalized_clip_narrations = [
            str(item or "").strip() for item in list(clip_narrations or [])
        ]
        script = str(locked_script or "").strip()
        if not script and normalized_clip_narrations:
            script = " ".join(item for item in normalized_clip_narrations if item).strip()
        if not script:
            try:
                project_payload = self._project_data(project)
            except Exception:
                project_payload = {}
            clip_narrations = (
                project_payload.get("clip_narrations")
                if isinstance(project_payload, dict)
                else []
            )
            if isinstance(clip_narrations, (list, tuple)):
                script = " ".join(
                    str(item or "").strip()
                    for item in clip_narrations
                    if str(item or "").strip()
                ).strip()
            if not script and isinstance(project_payload, dict):
                script = str(
                    project_payload.get("locked_script")
                    or project_payload.get("approved_script")
                    or project_payload.get("script")
                    or ""
                ).strip()
            if script:
                print(
                    "[Sprint193-7 Narration -> Locked Script] RECOVERED",
                    {"chars": len(script)},
                    flush=True,
                )
        hook = str(hook_text or "").strip()
        cta = ""  # Sprint193-14: CTA 완전 제거

        trust_narration_parts = []
        is_history_channel = str(channel_type or "").strip().lower() in {"history", "history_ko", "history_en"}
        review_value = 0 if is_history_channel else int(declared_review_count or 0)
        rating_value = 0.0 if is_history_channel else float(rating or 0.0)
        if is_history_channel:
            print("[Sprint194-1 History Mode] TRUST HOOK SKIPPED", {"channel_type": channel_type}, flush=True)
        if review_value > 0:
            trust_narration_parts.append(f"리뷰 {review_value:,}개.")
        if rating_value > 0:
            rating_text = f"{rating_value:.2f}".rstrip("0").rstrip(".")
            trust_narration_parts.append(f"평점도 {rating_text}점.")
        trust_narration = " ".join(trust_narration_parts).strip()

        # Sprint193-13:
        # 신뢰 후킹(리뷰/평점)과 후킹멘트는 음성으로만 읽습니다.
        # 일반 자막에는 넣지 않습니다.
        narration_parts = [
            value for value in (trust_narration, hook, script) if value
        ]
        narration_text = "\n\n".join(narration_parts)
        clip_count = max(1, min(8, int(gemini_clip_count or 4)))
        supplied = [
            str(Path(value)) for value in list(supplied_clip_paths or [])
            if str(value).strip() and Path(str(value)).is_file()
        ]
        print("[Sprint174-1 ROUTE] GEMINI_VIDEO_ONLY", flush=True)
        print("[Sprint174-1 INPUT]", {"project_id": project_id, "product_name": product_name, "hook_chars": len(hook), "script_chars": len(script), "cta_chars": len(cta), "narration_chars": len(narration_text), "clip_count": clip_count, "supplied_clips": len(supplied)}, flush=True)
        if not script:
            return {"ok": False, "outputs": {"workflow_version": self.WORKFLOW_VERSION, "error": "clip_narration_missing"}, "summary": "영상별 나레이션이 없어 내부 확정 대본을 만들 수 없습니다."}

        generated_files = list(supplied)

        # Sprint194-11: 역사 모드는 장면별 TTS만 생성하고, 전체 대본 TTS/intro를 별도로 만들지 않습니다.
        # 최종 음성은 scene_01~N을 정확히 한 번씩 이어붙인 단일 트랙만 사용합니다.
        _history_mode_194_11 = str(channel_type or "").strip() in {"history", "history_ko", "history_en"}
        # Sprint194-20: history_en uses native English TTS and language-isolated audio/output paths.
        _history_language_194_20 = "eng" if str(channel_type or "").strip().lower() == "history_en" else "kor"
        _history_lang_tag_194_20 = "en" if _history_language_194_20 == "eng" else "ko"
        # Sprint194-30 defensive lock: an English render must never silently burn Korean
        # subtitle/narration arrays into the final MP4. Fail early instead.
        if str(channel_type or "").strip().lower() == "history_en":
            # Sprint194-74: enforce a short, subscription-focused final scene at the
            # workflow boundary too. This protects renders loaded from an older English
            # preset that bypassed the new 194-73 localization button/cache.
            if normalized_clip_narrations:
                _ending_before_194_74 = str(normalized_clip_narrations[-1] or "")
                normalized_clip_narrations[-1] = (
                    "Want more weird history? Subscribe to History Cookie."
                )
                # Keep the function argument/list used later by the dedicated renderer aligned.
                if isinstance(clip_narrations, list) and clip_narrations:
                    clip_narrations[-1] = normalized_clip_narrations[-1]
                if isinstance(clip_subtitles, list) and clip_subtitles:
                    clip_subtitles[-1] = "[SUBSCRIBE] FOR MORE HISTORY!"
                print("[Sprint194-74 History EN Ending Lock] APPLIED", {
                    "scene": len(normalized_clip_narrations),
                    "old_chars": len(_ending_before_194_74),
                    "new_narration": normalized_clip_narrations[-1],
                    "new_subtitle": "[SUBSCRIBE] FOR MORE HISTORY!",
                    "before_tts_cache": True,
                }, flush=True)

            _hangul_re_194_30 = re.compile(r"[가-힣]")
            _ko_subs_194_30 = sum(bool(_hangul_re_194_30.search(str(x or ""))) for x in list(clip_subtitles or []))
            _ko_nars_194_30 = sum(bool(_hangul_re_194_30.search(str(x or ""))) for x in list(normalized_clip_narrations or []))
            print("[Sprint194-30 English Workflow Input Guard]", {
                "subtitles": len(list(clip_subtitles or [])),
                "narrations": len(list(normalized_clip_narrations or [])),
                "hangul_subtitles": _ko_subs_194_30,
                "hangul_narrations": _ko_nars_194_30,
            }, flush=True)
            if _ko_subs_194_30 or _ko_nars_194_30:
                return {
                    "ok": False,
                    "job_id": "",
                    "state": {},
                    "outputs": {
                        "workflow_version": self.WORKFLOW_VERSION,
                        "execution_mode": "history_en_input_guard",
                        "error": "history_english_render_input_contains_korean",
                    },
                    "summary": "영어 영상 렌더 입력에 한국어 자막/나레이션이 남아 있어 제작을 중단했습니다.",
                    "final_video_path": "",
                }
        if _history_mode_194_11:
            print("[Sprint194-21 History Global] LANGUAGE", {"channel_type": channel_type, "tts_language": _history_language_194_20, "lang_tag": _history_lang_tag_194_20}, flush=True)

        # Sprint193-9: 직접 업로드 음성이 없으면 Typecast로 나레이션 자동 생성.
        resolved_voice_audio_path = str(voice_audio_path or "").strip()
        tts_generation = {"ok": False, "status": "not_requested", "voice_name": str(voice_name or "지안")}
        if not resolved_voice_audio_path and narration_text and not _history_mode_194_11:
            try:
                import os as _os
                from typecast import Typecast
                from typecast.models import TTSRequest, Output
                api_key = str(
                    typecast_api_key
                    or _os.getenv("TYPECAST_API_KEY", "")
                    or ""
                ).strip()
                if not api_key:
                    raise RuntimeError("Typecast API Key가 입력되지 않았습니다.")
                client = Typecast(api_key=api_key)
                resolved_voice_id = str(voice_id or "").strip()
                resolved_voice_name = str(voice_name or "지안").strip()
                if not resolved_voice_id:
                    voices = client.voices_v2()
                    for item in list(voices or []):
                        if str(getattr(item, "voice_name", "") or "").strip() == resolved_voice_name:
                            resolved_voice_id = str(getattr(item, "voice_id", "") or "").strip()
                            if resolved_voice_id:
                                break
                if not resolved_voice_id:
                    raise RuntimeError(f"Typecast 성우 ID를 찾지 못했습니다: {resolved_voice_name}")
                # Typecast SDK 0.3.x Output uses target_lufs (-70~0), not percentage volume.
                # UI 100% -> -14 LUFS, 200% -> -8 LUFS, 0% -> -32 LUFS.
                volume_pct = max(0, min(200, int(tts_volume_percent or 100)))
                target_lufs = -32.0 + (volume_pct / 200.0) * 24.0
                response = client.text_to_speech(TTSRequest(
                    text=narration_text,
                    model="ssfm-v30",
                    voice_id=resolved_voice_id,
                    language=_history_language_194_20,
                    output=Output(
                        target_lufs=float(target_lufs),
                        audio_tempo=max(0.5, min(2.0, float(tts_speech_speed or 1.0))),
                        audio_format="mp3",
                    ),
                ))
                tts_dir = Path("assets/manual_audio") / f"project_{project_id}"
                tts_dir.mkdir(parents=True, exist_ok=True)
                tts_target = tts_dir / "typecast_auto_voice.mp3"

                audio_bytes = None
                for attr_name in ("audio_data", "audio", "content", "data"):
                    candidate = getattr(response, attr_name, None)
                    if isinstance(candidate, (bytes, bytearray)) and len(candidate) > 0:
                        audio_bytes = bytes(candidate)
                        break
                if audio_bytes is not None:
                    tts_target.write_bytes(audio_bytes)
                elif hasattr(response, "save") and callable(getattr(response, "save")):
                    response.save(str(tts_target))
                elif hasattr(response, "save_to_file") and callable(getattr(response, "save_to_file")):
                    response.save_to_file(str(tts_target))
                else:
                    raise RuntimeError(
                        "Typecast 응답에서 MP3 바이트를 찾지 못했습니다. "
                        f"response_type={type(response).__name__}"
                    )

                if not tts_target.is_file() or tts_target.stat().st_size <= 1024:
                    raise RuntimeError(
                        f"Typecast 음성 파일 생성 실패: {tts_target} "
                        f"size={tts_target.stat().st_size if tts_target.exists() else 0}"
                    )

                resolved_voice_audio_path = str(tts_target)
                tts_generation = {
                    "ok": True,
                    "status": "typecast_generated",
                    "voice_name": resolved_voice_name,
                    "voice_id": resolved_voice_id,
                    "path": resolved_voice_audio_path,
                    "bytes": int(tts_target.stat().st_size),
                    "target_lufs": float(target_lufs),
                    "speech_speed": float(tts_speech_speed or 1.0),
                }
                print("[Sprint193-10 Typecast TTS] GENERATED", tts_generation, flush=True)
            except Exception as exc:
                tts_generation = {
                    "ok": False,
                    "status": "typecast_failed",
                    "voice_name": str(voice_name or "지안"),
                    "error": f"{type(exc).__name__}: {exc}",
                }
                print("[Sprint193-10 Typecast TTS] ERROR", tts_generation, flush=True)


        # Sprint193-14: 장면별 나레이션을 별도 MP3로 생성하여
        # 각 Gemini 영상 시작점에 정확히 배치합니다.
        intro_voice_path = ""
        clip_voice_paths = []
        scene_tts_generation = []
        # Sprint194-46: English history is hard-locked at the workflow boundary.
        # UI/preset reruns may still pass the previously selected Korean/other voice (e.g. Junho).
        # Never trust that value for history_en; resolve Oliver from Typecast in the TTS stage itself.
        _effective_history_voice_name_194_46 = (
            "Oliver" if _history_lang_tag_194_20 == "en" else str(voice_name or "지안").strip()
        )
        if _history_lang_tag_194_20 == "en":
            print("[Sprint194-46 English Voice Hard Lock] REQUESTED", {
                "incoming_voice_name": str(voice_name or ""),
                "effective_voice_name": _effective_history_voice_name_194_46,
                "incoming_voice_id_ignored": bool(str(voice_id or "").strip()),
            }, flush=True)
        # Sprint194-43: Streamlit may invoke the history pipeline more than once during one UI action.
        # Persist the 17 scene TTS paths with a content hash so a second invocation can recover them
        # instead of starting with audio_slots=0.
        _scene_tts_cache_dir_194_43 = Path("assets/manual_audio") / f"project_{project_id}" / f"scene_tts_{_history_lang_tag_194_20}"
        _scene_tts_cache_dir_194_43.mkdir(parents=True, exist_ok=True)
        _scene_tts_cache_manifest_194_43 = _scene_tts_cache_dir_194_43 / "scene_tts_manifest_194_43.json"
        _scene_tts_cache_key_payload_194_43 = {
            "lang": _history_lang_tag_194_20,
            "narrations": [str(x or "").strip() for x in list(normalized_clip_narrations or [])],
            "voice_name": _effective_history_voice_name_194_46,
            "voice_id": ("" if _history_lang_tag_194_20 == "en" else str(voice_id or "").strip()),
            "speed": float(tts_speech_speed or 1.0),
            "volume": int(tts_volume_percent or 100),
            "localization_profile": (
                "history-en-short-53-55s-v3"
                if _history_lang_tag_194_20 == "en"
                else ""
            ),
        }
        _scene_tts_cache_hash_194_43 = hashlib.sha256(
            json.dumps(_scene_tts_cache_key_payload_194_43, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()

        def _sprint194_43_load_scene_tts_cache():
            def _validate_manifest_194_71(_manifest):
                try:
                    if not Path(_manifest).is_file():
                        return []
                    _meta = json.loads(Path(_manifest).read_text(encoding="utf-8"))
                    if str(_meta.get("source_hash") or "") != _scene_tts_cache_hash_194_43:
                        return []
                    _paths = [str(x or "") for x in list(_meta.get("paths") or [])]
                    if len(_paths) != len(normalized_clip_narrations or []):
                        return []
                    if not all(
                        p and Path(p).is_file() and Path(p).stat().st_size > 1024
                        for p in _paths
                    ):
                        return []
                    return _paths
                except Exception:
                    return []

            try:
                # 1) Fast local-project hit.
                _local_paths_194_71 = _validate_manifest_194_71(
                    _scene_tts_cache_manifest_194_43
                )
                if _local_paths_194_71:
                    return _local_paths_194_71

                # 2) Sprint194-71: video-only rerender creates a new project id.
                # Reuse any prior project's scene TTS when language+narrations+voice+
                # speed+volume hash is identical. This runs only after Video Create,
                # never during Previous Work Load.
                _manual_root_194_71 = Path("assets/manual_audio")
                _candidates_194_71 = []
                if _manual_root_194_71.is_dir():
                    _candidates_194_71 = [
                        p for p in _manual_root_194_71.glob(
                            f"project_*/scene_tts_{_history_lang_tag_194_20}/scene_tts_manifest_194_43.json"
                        )
                        if p.is_file() and p.resolve() != _scene_tts_cache_manifest_194_43.resolve()
                    ]
                    _candidates_194_71.sort(
                        key=lambda p: p.stat().st_mtime if p.exists() else 0.0,
                        reverse=True,
                    )

                for _manifest_194_71 in _candidates_194_71:
                    _paths_194_71 = _validate_manifest_194_71(_manifest_194_71)
                    if _paths_194_71:
                        print("[Sprint194-71 History Scene TTS Cross Project Cache] HIT", {
                            "current_project": str(project_id),
                            "source_manifest": str(_manifest_194_71),
                            "scene_count": len(_paths_194_71),
                            "lang": _history_lang_tag_194_20,
                            "voice_name": _effective_history_voice_name_194_46,
                            "speed": float(tts_speech_speed or 1.0),
                            "volume": int(tts_volume_percent or 100),
                        }, flush=True)
                        return _paths_194_71
                return []
            except Exception as _cache_exc:
                print("[Sprint194-43 History Scene TTS Cache] INVALID", type(_cache_exc).__name__, str(_cache_exc), flush=True)
                return []

        _cached_scene_tts_194_43 = _sprint194_43_load_scene_tts_cache()
        if _history_lang_tag_194_20 == "en":
            print("[Sprint194-75J English TTS Cache Guard] READY", {
                "profile": "history-en-short-53-55s-v3",
                "cache_hit": bool(_cached_scene_tts_194_43),
                "narration_count": len(list(normalized_clip_narrations or [])),
                "cross_project_old_profile_blocked": True,
            }, flush=True)
        if _cached_scene_tts_194_43:
            clip_voice_paths = list(_cached_scene_tts_194_43)
            scene_tts_generation = [
                {"index": i + 1, "ok": True, "status": "cache_reused", "path": p}
                for i, p in enumerate(clip_voice_paths)
            ]
            print("[Sprint194-43 History Scene TTS Cache] HIT", {
                "scene_count": len(clip_voice_paths),
                "lang": _history_lang_tag_194_20,
            }, flush=True)

        # Sprint194-42: history scene TTS must be driven by the 1:N scene narrations themselves.
        # English auto-localization can legitimately leave narration_text empty while all 17
        # localized scene narrations are present. The old narration_text gate skipped TTS entirely,
        # producing narrations=17 / audio_slots=0.
        import os as _os_scene_194_42
        _scene_tts_api_key_194_42 = str(
            typecast_api_key or _os_scene_194_42.getenv("TYPECAST_API_KEY", "") or ""
        ).strip()
        if normalized_clip_narrations and _scene_tts_api_key_194_42 and not clip_voice_paths:
            try:
                import os as _os2
                from typecast import Typecast as _Typecast2
                from typecast.models import TTSRequest as _TTSRequest2, Output as _Output2

                _api_key2 = str(
                    typecast_api_key or _os2.getenv("TYPECAST_API_KEY", "") or ""
                ).strip()
                _client2 = _Typecast2(api_key=_api_key2)
                _voice_name2 = _effective_history_voice_name_194_46
                # English must not inherit a stale Junho/other voice_id from the UI/preset.
                _voice_id2 = "" if _history_lang_tag_194_20 == "en" else str(voice_id or "").strip()
                if not _voice_id2:
                    # Sprint194-36: Typecast voices_v2() 목록 조회가 실패해도
                    # 이전 프로젝트에서 저장된 voice_id를 재사용할 수 있도록 복구합니다.
                    try:
                        _wanted_voice_194_42 = _voice_name2.casefold()
                        _aliases_194_42 = {_wanted_voice_194_42}
                        if _history_lang_tag_194_20 == "en" and _wanted_voice_194_42 in {"oliver", "올리버"}:
                            _aliases_194_42.update({"oliver", "올리버"})
                        for _voice in list(_client2.voices_v2() or []):
                            _candidate_name_194_42 = str(getattr(_voice, "voice_name", "") or "").strip()
                            _candidate_fold_194_42 = _candidate_name_194_42.casefold()
                            if _candidate_fold_194_42 in _aliases_194_42 or any(
                                alias and alias in _candidate_fold_194_42 for alias in _aliases_194_42
                            ):
                                _voice_id2 = str(getattr(_voice, "voice_id", "") or "").strip()
                                if _voice_id2:
                                    print("[Sprint194-42 History Scene TTS Voice] RESOLVED", {
                                        "requested": _voice_name2,
                                        "resolved": _candidate_name_194_42,
                                        "lang": _history_lang_tag_194_20,
                                    }, flush=True)
                                    break
                    except Exception as _voice_list_exc:
                        print("[Sprint194-36 History TTS Voice List] ERROR", type(_voice_list_exc).__name__, str(_voice_list_exc), flush=True)

                if not _voice_id2:
                    # 프로젝트/환경에 저장된 ID 후보를 재귀적으로 찾습니다.
                    try:
                        _pd2 = self._project_data(project)
                    except Exception:
                        _pd2 = {}
                    _voice_id2 = str(
                        self._find_nested_value(_pd2, (
                            "voice_id", "typecast_voice_id", "tts_voice_id",
                            "history_voice_id", "ko_voice_id", "en_voice_id", "english_voice_id",
                        )) or _os2.getenv("TYPECAST_VOICE_ID", "") or ""
                    ).strip()
                    if _voice_id2:
                        print("[Sprint194-36 History TTS Voice ID Fallback] RECOVERED", {"voice_name": _voice_name2, "voice_id": _voice_id2}, flush=True)

                if not _voice_id2:
                    raise RuntimeError(
                        f"Typecast 성우 ID를 찾지 못했습니다: {_voice_name2}. "
                        "보이스 목록 조회 실패 시 UI/프로젝트의 voice_id 또는 TYPECAST_VOICE_ID가 필요합니다."
                    )

                _volume_pct2 = max(0, min(200, int(tts_volume_percent or 100)))
                _target_lufs2 = -32.0 + (_volume_pct2 / 200.0) * 24.0
                _tts_dir2 = Path("assets/manual_audio") / f"project_{project_id}" / f"scene_tts_{_history_lang_tag_194_20}"
                _tts_dir2.mkdir(parents=True, exist_ok=True)

                def _synth_scene_tts(_text, _target):
                    _response = _client2.text_to_speech(_TTSRequest2(
                        text=str(_text or "").strip(),
                        model="ssfm-v30",
                        voice_id=_voice_id2,
                        language=_history_language_194_20,
                        output=_Output2(
                            target_lufs=float(_target_lufs2),
                            audio_tempo=max(0.5, min(2.0, float(tts_speech_speed or 1.0))),
                            audio_format="mp3",
                        ),
                    ))
                    _bytes = None
                    for _attr in ("audio_data", "audio", "content", "data"):
                        _candidate = getattr(_response, _attr, None)
                        if isinstance(_candidate, (bytes, bytearray)) and len(_candidate) > 0:
                            _bytes = bytes(_candidate)
                            break
                    if _bytes is not None:
                        _target.write_bytes(_bytes)
                    elif hasattr(_response, "save") and callable(getattr(_response, "save")):
                        _response.save(str(_target))
                    elif hasattr(_response, "save_to_file") and callable(getattr(_response, "save_to_file")):
                        _response.save_to_file(str(_target))
                    else:
                        raise RuntimeError("Typecast 장면 음성 응답에서 오디오를 찾지 못했습니다.")
                    if not _target.is_file() or _target.stat().st_size <= 1024:
                        raise RuntimeError(f"장면 TTS 파일 생성 실패: {_target}")
                    return str(_target)

                _intro_text = "" if _history_mode_194_11 else " ".join(
                    value for value in (trust_narration, hook) if str(value or "").strip()
                ).strip()
                if _intro_text:
                    intro_voice_path = _synth_scene_tts(
                        _intro_text, _tts_dir2 / "intro.mp3"
                    )

                for _idx, _scene_text in enumerate(normalized_clip_narrations, start=1):
                    print(
                        "[Sprint194-13 History Scene Text Map]",
                        {"scene": _idx, "tts_text": str(_scene_text or "").strip()},
                        flush=True,
                    )
                    if not _scene_text:
                        clip_voice_paths.append("")
                        scene_tts_generation.append(
                            {"index": _idx, "ok": True, "status": "empty_narration"}
                        )
                        continue
                    _path = _synth_scene_tts(
                        _scene_text, _tts_dir2 / f"scene_{_idx:02d}.mp3"
                    )
                    clip_voice_paths.append(_path)
                    scene_tts_generation.append(
                        {"index": _idx, "ok": True, "status": "generated", "path": _path}
                    )

                print(
                    "[Sprint193-14 Scene TTS] GENERATED",
                    {
                        "intro": bool(intro_voice_path),
                        "scene_count": len(clip_voice_paths),
                        "nonempty_scene_voice_count": len([p for p in clip_voice_paths if p]),
                    },
                    flush=True,
                )
                # Sprint194-44: cache persistence is optional. A cache write failure must NEVER
                # erase 17 scene MP3s that Typecast has already generated successfully.
                try:
                    _scene_tts_cache_manifest_194_43.write_text(
                        json.dumps({
                            "version": "scene-tts-cache-194-44",
                            "source_hash": _scene_tts_cache_hash_194_43,
                            "cache_key": dict(_scene_tts_cache_key_payload_194_43),
                            "paths": list(clip_voice_paths),
                            "lang": _history_lang_tag_194_20,
                        }, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                    print("[Sprint194-44 History Scene TTS Cache] SAVED", {
                        "scene_count": len(clip_voice_paths),
                        "path": str(_scene_tts_cache_manifest_194_43),
                    }, flush=True)
                except Exception as _cache_save_exc_194_44:
                    print("[Sprint194-44 History Scene TTS Cache] SAVE_FAILED_PRESERVED", {
                        "error": f"{type(_cache_save_exc_194_44).__name__}: {_cache_save_exc_194_44}",
                        "scene_count": len(clip_voice_paths),
                        "audio_slots_preserved": len(clip_voice_paths),
                    }, flush=True)
            except Exception as _scene_exc:
                print(
                    "[Sprint193-14 Scene TTS] ERROR",
                    type(_scene_exc).__name__,
                    str(_scene_exc),
                    flush=True,
                )
                # Sprint194-44: if all expected scene audio files already exist, preserve them.
                _expected_scene_count_194_44 = len(normalized_clip_narrations or [])
                _valid_generated_paths_194_44 = (
                    len(clip_voice_paths) == _expected_scene_count_194_44
                    and _expected_scene_count_194_44 > 0
                    and all(
                        str(_p or "").strip() and Path(str(_p)).is_file() and Path(str(_p)).stat().st_size > 1024
                        for _p in clip_voice_paths
                    )
                )
                if _valid_generated_paths_194_44:
                    print("[Sprint194-44 History Scene TTS] ERROR_AFTER_GENERATION_PATHS_PRESERVED", {
                        "narrations": _expected_scene_count_194_44,
                        "audio_slots": len(clip_voice_paths),
                        "error": f"{type(_scene_exc).__name__}: {_scene_exc}",
                    }, flush=True)
                else:
                    intro_voice_path = ""
                    clip_voice_paths = []
                    scene_tts_generation = [
                        {"ok": False, "status": "failed", "error": f"{type(_scene_exc).__name__}: {_scene_exc}"}
                    ]
        elif normalized_clip_narrations and not _scene_tts_api_key_194_42:
            print("[Sprint194-42 History Scene TTS] BLOCKED", {
                "reason": "typecast_api_key_missing",
                "narrations": len(normalized_clip_narrations),
                "lang": _history_lang_tag_194_20,
            }, flush=True)

        print("[Sprint194-42 History Scene TTS Gate] READY", {
            "narration_text_present": bool(str(narration_text or "").strip()),
            "scene_narrations": len(normalized_clip_narrations or []),
            "api_key_present": bool(_scene_tts_api_key_194_42),
            "audio_slots": len(clip_voice_paths),
            "voice_name": str(voice_name or ""),
            "voice_id_present": bool(str(voice_id or "").strip()),
            "lang": _history_lang_tag_194_20,
        }, flush=True)

        # Sprint194-76: FINAL COMMON HISTORY CONTRACT.
        # Topic-independent invariant: N narrations == N valid scene TTS files before any history renderer.
        # Preserve successful in-memory generation first; recover only the same project/language direct files.
        if str(channel_type or "").strip() in {"history", "history_ko", "history_en"} and normalized_clip_narrations:
            _expected_194_76 = len(normalized_clip_narrations)
            _valid_194_76 = [
                str(_p) for _p in list(clip_voice_paths or [])
                if str(_p or "").strip() and Path(str(_p)).is_file() and Path(str(_p)).stat().st_size > 1024
            ]
            if len(clip_voice_paths or []) == _expected_194_76 and len(_valid_194_76) == _expected_194_76:
                clip_voice_paths = list(clip_voice_paths)
                _source_194_76 = "generated_in_memory"
            else:
                _direct_dir_194_76 = Path("assets/manual_audio") / f"project_{project_id}" / f"scene_tts_{_history_lang_tag_194_20}"
                _direct_194_76 = [str(_direct_dir_194_76 / f"scene_{_i:02d}.mp3") for _i in range(1, _expected_194_76 + 1)]
                if _direct_194_76 and all(Path(_p).is_file() and Path(_p).stat().st_size > 1024 for _p in _direct_194_76):
                    clip_voice_paths = list(_direct_194_76)
                    _source_194_76 = "same_project_direct_files"
                else:
                    _source_194_76 = "defer_to_existing_selfheal"
            print("[Sprint194-76 History Common Contract]", {
                "project_id": str(project_id), "lang": _history_lang_tag_194_20,
                "narrations": _expected_194_76, "audio_slots": len(list(clip_voice_paths or [])),
                "valid_audio_slots": len([_p for _p in list(clip_voice_paths or []) if str(_p or "").strip() and Path(str(_p)).is_file()]),
                "source": _source_194_76, "topic_specific_patch": False,
            }, flush=True)

        # Sprint194-8: 역사 모드는 장면 TTS 1~N을 앞뒤 무음 제거 후 하나의 음성으로 합칩니다.
        # 각 장면 영상 길이도 추정치가 아니라 실제 TTS 길이에 맞춰 다시 렌더링합니다.
        _history_mode_194_8 = str(channel_type or "").strip() in {"history", "history_ko", "history_en"}
        _history_full_voice_194_8 = ""
        _history_scene_durations_194_8 = []
        if _history_mode_194_8 and normalized_clip_narrations and clip_voice_paths:
            try:
                _history_audio_root = Path("assets/manual_audio") / f"project_{project_id}" / f"history_194_8_{_history_lang_tag_194_20}"
                _history_audio_root.mkdir(parents=True, exist_ok=True)

                def _ffprobe_duration_194_8(_path):
                    _probe = subprocess.run(
                        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(_path)],
                        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
                    )
                    try:
                        return max(0.0, float((_probe.stdout or "0").strip() or 0.0))
                    except Exception:
                        return 0.0

                def _trim_to_wav_194_8(_source, _target):
                    _target = Path(_target)
                    _cmd = [
                        "ffmpeg", "-y", "-i", str(_source),
                        "-af", "silenceremove=start_periods=1:start_duration=0.02:start_threshold=-48dB:stop_periods=1:stop_duration=0.06:stop_threshold=-48dB",
                        "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", str(_target),
                    ]
                    _done = subprocess.run(_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
                    if _done.returncode != 0 or not _target.is_file() or _target.stat().st_size <= 1024 or _ffprobe_duration_194_8(_target) < 0.20:
                        _cmd = ["ffmpeg", "-y", "-i", str(_source), "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", str(_target)]
                        _done = subprocess.run(_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
                    if _done.returncode != 0 or not _target.is_file() or _target.stat().st_size <= 1024:
                        raise RuntimeError("history_scene_audio_trim_failed: " + str((_done.stderr or _done.stdout or "")[-800:]))
                    return str(_target)

                def _concat_wavs_194_8(_paths, _target):
                    # Sprint194-45: concat demuxer resolves relative paths from the list file,
                    # so always write absolute paths. Relative assets/... paths previously became
                    # duplicated under history_194_8 and caused history_audio_concat_failed.
                    _paths = [str(Path(p).resolve()) for p in _paths if p and Path(str(p)).is_file()]
                    if not _paths:
                        return ""
                    if len(_paths) == 1:
                        shutil.copyfile(_paths[0], _target)
                        return str(_target)
                    _list = Path(str(_target) + ".concat.txt")
                    _list.write_text("\n".join("file '" + p.replace("'", "'\\''") + "'" for p in _paths) + "\n", encoding="utf-8")
                    _done = subprocess.run(
                        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(_list), "-c:a", "pcm_s16le", str(_target)],
                        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
                    )
                    if _done.returncode != 0 or not Path(_target).is_file() or Path(_target).stat().st_size <= 1024:
                        raise RuntimeError("history_audio_concat_failed: " + str((_done.stderr or _done.stdout or "")[-800:]))
                    return str(_target)

                # 첫 장면 나레이션에 후킹이 이미 포함되어 있으면 intro를 중복 사용하지 않습니다.
                def _norm_194_8(_text):
                    return re.sub(r"[^0-9A-Za-z가-힣]+", "", str(_text or "")).lower()

                _trimmed_scene_wavs = []
                for _idx, _voice_path in enumerate(list(clip_voice_paths or []), start=1):
                    if not _voice_path or not Path(str(_voice_path)).is_file():
                        continue
                    _trimmed_scene_wavs.append(
                        _trim_to_wav_194_8(_voice_path, _history_audio_root / f"scene_{_idx:02d}_trim.wav")
                    )

                if len(_trimmed_scene_wavs) != len([x for x in normalized_clip_narrations if str(x).strip()]):
                    raise RuntimeError(
                        f"history_scene_tts_count_mismatch: narration={len([x for x in normalized_clip_narrations if str(x).strip()])} audio={len(_trimmed_scene_wavs)}"
                    )

                _scene_slot_wavs = list(_trimmed_scene_wavs)
                _hook_norm = _norm_194_8(hook)
                _first_norm = _norm_194_8(normalized_clip_narrations[0] if normalized_clip_narrations else "")
                _intro_needed = bool(intro_voice_path and _hook_norm and _hook_norm not in _first_norm)
                if _intro_needed:
                    _intro_trim = _trim_to_wav_194_8(intro_voice_path, _history_audio_root / "intro_trim.wav")
                    _first_slot = _concat_wavs_194_8(
                        [_intro_trim, _scene_slot_wavs[0]],
                        _history_audio_root / "scene_01_with_hook.wav",
                    )
                    _scene_slot_wavs[0] = _first_slot

                _history_scene_durations_194_8 = [
                    max(1.0, _ffprobe_duration_194_8(_p)) for _p in _scene_slot_wavs
                ]

                _full_wav = _concat_wavs_194_8(_scene_slot_wavs, _history_audio_root / "narration_full.wav")
                _full_mp3 = _history_audio_root / "narration_full.mp3"
                _done = subprocess.run(
                    ["ffmpeg", "-y", "-i", str(_full_wav), "-c:a", "libmp3lame", "-b:a", "192k", str(_full_mp3)],
                    capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
                )
                if _done.returncode != 0 or not _full_mp3.is_file() or _full_mp3.stat().st_size <= 1024:
                    raise RuntimeError("history_full_narration_encode_failed: " + str((_done.stderr or _done.stdout or "")[-800:]))
                _history_full_voice_194_8 = str(_full_mp3)
                resolved_voice_audio_path = _history_full_voice_194_8
                intro_voice_path = ""

                # 실제 TTS 길이로 1:1 역사 이미지 영상을 다시 렌더링합니다.
                _image_root = Path("assets/history_scene_images") / f"project_{project_id}"
                _image_paths = sorted(
                    [p for p in _image_root.glob("scene_*.*") if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}],
                    key=lambda p: [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", p.stem.lower())],
                )
                if len(_image_paths) >= len(_history_scene_durations_194_8):
                    _clip_root = Path("assets/gemini_clips") / f"project_{project_id}"
                    _clip_root.mkdir(parents=True, exist_ok=True)
                    _rerendered = []
                    for _idx, (_img, _dur) in enumerate(zip(_image_paths, _history_scene_durations_194_8), start=1):
                        _target = _clip_root / f"history_{_idx:02d}.mp4"
                        _mode = (_idx - 1) % 5
                        _d = max(1.0, float(_dur))
                        _moves = [
                            f"crop=1080:1920:x='(iw-1080)*t/{_d:.6f}':y='(ih-1920)/2'",
                            f"crop=1080:1920:x='(iw-1080)*(1-t/{_d:.6f})':y='(ih-1920)/2'",
                            f"crop=1080:1920:x='(iw-1080)/2':y='(ih-1920)*t/{_d:.6f}'",
                            f"crop=1080:1920:x='(iw-1080)/2':y='(ih-1920)*(1-t/{_d:.6f})'",
                            "crop=1080:1920:x='(iw-1080)/2':y='(ih-1920)/2'",
                        ]
                        _vf = "scale=1188:2112:force_original_aspect_ratio=increase," + _moves[_mode] + ",fps=30,format=yuv420p"
                        _cmd = [
                            "ffmpeg", "-y", "-loop", "1", "-i", str(_img),
                            "-vf", _vf, "-t", f"{_d:.3f}", "-an",
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(_target),
                        ]
                        _render = subprocess.run(_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
                        if _render.returncode != 0 or not _target.is_file() or _target.stat().st_size <= 1024:
                            raise RuntimeError("history_audio_driven_scene_render_failed: " + str((_render.stderr or _render.stdout or "")[-800:]))
                        _rerendered.append(str(_target))
                    generated_files = _rerendered
                else:
                    print("[Sprint194-8 History Audio Driven Scenes] IMAGE COUNT FALLBACK", {"images": len(_image_paths), "durations": len(_history_scene_durations_194_8)}, flush=True)

                print("[Sprint194-8 History Narration Concat] READY", {
                    "scene_count": len(_history_scene_durations_194_8),
                    "durations": [round(x, 3) for x in _history_scene_durations_194_8],
                    "voice_duration": round(_ffprobe_duration_194_8(_history_full_voice_194_8), 3),
                    "video_duration_target": round(sum(_history_scene_durations_194_8), 3),
                    "intro_merged_to_scene1": bool(_intro_needed),
                    "gap_seconds": 0.0,
                    "voice_path": _history_full_voice_194_8,
                }, flush=True)
            except Exception as _history_exc:
                print("[Sprint194-8 History Narration Concat] ERROR", type(_history_exc).__name__, str(_history_exc), flush=True)
                _history_full_voice_194_8 = ""
                _history_scene_durations_194_8 = []

        # Sprint194-11: 역사쿠키의 최종 기준 타임라인을 장면별 TTS 실제 길이로 단일화합니다.
        # intro/전체대본 TTS는 사용하지 않고 scene_01~N만 정확히 한 번씩 사용합니다.
        _history_full_voice_194_11 = ""
        _history_scene_durations_194_11 = []
        if _history_mode_194_11:
            try:
                if not normalized_clip_narrations:
                    raise RuntimeError("history_timeline_missing_narrations")
                if len(clip_voice_paths) != len(normalized_clip_narrations):
                    # Sprint194-45: generated scene MP3s are the source of truth. Recover them
                    # directly from disk before consulting any optional cache manifest. This
                    # closes the observed GENERATED=17 -> audio_slots=0 rerun/state-loss path.
                    _direct_tts_dir_194_45 = Path("assets/manual_audio") / f"project_{project_id}" / f"scene_tts_{_history_lang_tag_194_20}"
                    _direct_paths_194_45 = [
                        str(_direct_tts_dir_194_45 / f"scene_{_i:02d}.mp3")
                        for _i in range(1, len(normalized_clip_narrations) + 1)
                    ]
                    if _direct_paths_194_45 and all(
                        Path(_p).is_file() and Path(_p).stat().st_size > 1024
                        for _p in _direct_paths_194_45
                    ):
                        clip_voice_paths = list(_direct_paths_194_45)
                        print("[Sprint194-45 History Timeline TTS Recovery] DIRECT_FILES_RESTORED", {
                            "narrations": len(normalized_clip_narrations),
                            "audio_slots": len(clip_voice_paths),
                            "lang": _history_lang_tag_194_20,
                            "dir": str(_direct_tts_dir_194_45),
                        }, flush=True)
                if len(clip_voice_paths) != len(normalized_clip_narrations):
                    _recovered_194_43 = _sprint194_43_load_scene_tts_cache()
                    if _recovered_194_43:
                        clip_voice_paths = list(_recovered_194_43)
                        print("[Sprint194-44 History Timeline TTS Recovery] CACHE_RESTORED", {
                            "narrations": len(normalized_clip_narrations),
                            "audio_slots": len(clip_voice_paths),
                        }, flush=True)

                # Sprint194-46: final timeline is self-sufficient. If an earlier Streamlit/pipeline
                # invocation generated 17 files under another project/run and this invocation has
                # audio_slots=0, generate the 17 current scene TTS files RIGHT HERE instead of
                # failing with a secondary count-mismatch error. This is the final source of truth.
                if len(clip_voice_paths) != len(normalized_clip_narrations):
                    try:
                        import os as _os_sync_194_46
                        from typecast import Typecast as _Typecast_sync_194_46
                        from typecast.models import TTSRequest as _TTSRequest_sync_194_46, Output as _Output_sync_194_46

                        _sync_api_key_194_46 = str(
                            typecast_api_key or _os_sync_194_46.getenv("TYPECAST_API_KEY", "") or ""
                        ).strip()
                        if not _sync_api_key_194_46:
                            raise RuntimeError("Typecast API Key가 없습니다.")
                        _sync_client_194_46 = _Typecast_sync_194_46(api_key=_sync_api_key_194_46)

                        _sync_voice_name_194_46 = _effective_history_voice_name_194_46
                        _sync_voice_id_194_46 = "" if _history_lang_tag_194_20 == "en" else str(voice_id or "").strip()
                        _sync_resolved_name_194_46 = ""
                        if not _sync_voice_id_194_46:
                            _wanted_194_46 = _sync_voice_name_194_46.casefold()
                            _aliases_194_46 = {_wanted_194_46}
                            if _history_lang_tag_194_20 == "en":
                                _aliases_194_46.update({"oliver", "올리버"})
                            for _v194_46 in list(_sync_client_194_46.voices_v2() or []):
                                _vn194_46 = str(getattr(_v194_46, "voice_name", "") or "").strip()
                                _vf194_46 = _vn194_46.casefold()
                                if _vf194_46 in _aliases_194_46 or any(
                                    _a and _a in _vf194_46 for _a in _aliases_194_46
                                ):
                                    _vid194_46 = str(getattr(_v194_46, "voice_id", "") or "").strip()
                                    if _vid194_46:
                                        _sync_voice_id_194_46 = _vid194_46
                                        _sync_resolved_name_194_46 = _vn194_46
                                        break
                        if not _sync_voice_id_194_46:
                            raise RuntimeError(f"Typecast 성우 ID를 찾지 못했습니다: {_sync_voice_name_194_46}")

                        if _history_lang_tag_194_20 == "en":
                            print("[Sprint194-46 English Voice Hard Lock] RESOLVED", {
                                "requested": "Oliver",
                                "resolved": _sync_resolved_name_194_46 or _sync_voice_name_194_46,
                                "voice_id_present": True,
                            }, flush=True)

                        _sync_vol_pct_194_46 = max(0, min(200, int(tts_volume_percent or 100)))
                        _sync_target_lufs_194_46 = -32.0 + (_sync_vol_pct_194_46 / 200.0) * 24.0
                        _sync_tts_dir_194_46 = Path("assets/manual_audio") / f"project_{project_id}" / f"scene_tts_{_history_lang_tag_194_20}"
                        _sync_tts_dir_194_46.mkdir(parents=True, exist_ok=True)
                        _sync_paths_194_46 = []
                        for _si194_46, _stext194_46 in enumerate(normalized_clip_narrations, start=1):
                            _stext194_46 = str(_stext194_46 or "").strip()
                            if not _stext194_46:
                                raise RuntimeError(f"빈 장면 나레이션: scene={_si194_46}")
                            _target194_46 = _sync_tts_dir_194_46 / f"scene_{_si194_46:02d}.mp3"
                            _resp194_46 = _sync_client_194_46.text_to_speech(_TTSRequest_sync_194_46(
                                text=_stext194_46,
                                model="ssfm-v30",
                                voice_id=_sync_voice_id_194_46,
                                language=_history_language_194_20,
                                output=_Output_sync_194_46(
                                    target_lufs=float(_sync_target_lufs_194_46),
                                    audio_tempo=max(0.5, min(2.0, float(tts_speech_speed or 1.0))),
                                    audio_format="mp3",
                                ),
                            ))
                            _bytes194_46 = None
                            for _attr194_46 in ("audio_data", "audio", "content", "data"):
                                _cand194_46 = getattr(_resp194_46, _attr194_46, None)
                                if isinstance(_cand194_46, (bytes, bytearray)) and len(_cand194_46) > 0:
                                    _bytes194_46 = bytes(_cand194_46)
                                    break
                            if _bytes194_46 is not None:
                                _target194_46.write_bytes(_bytes194_46)
                            elif hasattr(_resp194_46, "save") and callable(getattr(_resp194_46, "save")):
                                _resp194_46.save(str(_target194_46))
                            elif hasattr(_resp194_46, "save_to_file") and callable(getattr(_resp194_46, "save_to_file")):
                                _resp194_46.save_to_file(str(_target194_46))
                            else:
                                raise RuntimeError(f"Typecast 오디오 응답 없음: scene={_si194_46}")
                            if not _target194_46.is_file() or _target194_46.stat().st_size <= 1024:
                                raise RuntimeError(f"장면 TTS 파일 생성 실패: scene={_si194_46} path={_target194_46}")
                            _sync_paths_194_46.append(str(_target194_46))
                        clip_voice_paths = list(_sync_paths_194_46)
                        scene_tts_generation = [
                            {"index": _i + 1, "ok": True, "status": "final_sync_selfheal", "path": _p}
                            for _i, _p in enumerate(clip_voice_paths)
                        ]
                        print("[Sprint194-46 History Timeline TTS SelfHeal] GENERATED", {
                            "narrations": len(normalized_clip_narrations),
                            "audio_slots": len(clip_voice_paths),
                            "project_id": str(project_id),
                            "lang": _history_lang_tag_194_20,
                            "voice": _sync_resolved_name_194_46 or _sync_voice_name_194_46,
                        }, flush=True)
                    except Exception as _selfheal_exc_194_46:
                        print("[Sprint194-46 History Timeline TTS SelfHeal] ERROR",
                              type(_selfheal_exc_194_46).__name__, str(_selfheal_exc_194_46), flush=True)
                        raise RuntimeError(
                            "history_timeline_tts_selfheal_failed: "
                            f"{type(_selfheal_exc_194_46).__name__}: {_selfheal_exc_194_46}"
                        ) from _selfheal_exc_194_46

                print("[Sprint194-46 History Timeline TTS PreSync]", {
                    "narrations": len(normalized_clip_narrations),
                    "audio_slots": len(clip_voice_paths),
                    "nonempty_audio_slots": len([p for p in clip_voice_paths if p and Path(str(p)).is_file()]),
                    "channel_type": str(channel_type or ""),
                    "lang": _history_lang_tag_194_20,
                    "voice_name": str(voice_name or ""),
                }, flush=True)
                if len(clip_voice_paths) != len(normalized_clip_narrations):
                    raise RuntimeError(
                        f"history_timeline_tts_count_mismatch: narrations={len(normalized_clip_narrations)} audio_slots={len(clip_voice_paths)}"
                    )

                _sync_root = Path("assets/manual_audio") / f"project_{project_id}" / f"history_194_11_{_history_lang_tag_194_20}"
                _sync_root.mkdir(parents=True, exist_ok=True)

                def _probe_194_11(_path):
                    if not _path or not Path(str(_path)).is_file():
                        return 0.0
                    _r = subprocess.run(
                        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(_path)],
                        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
                    )
                    try:
                        return max(0.0, float((_r.stdout or "0").strip() or 0.0))
                    except Exception:
                        return 0.0

                _scene_wavs_194_11 = []
                _scene_durs_194_11 = []
                for _idx, (_text, _voice) in enumerate(zip(normalized_clip_narrations, clip_voice_paths), start=1):
                    if not str(_text or "").strip():
                        raise RuntimeError(f"history_timeline_empty_narration: scene={_idx}")
                    if not _voice or not Path(str(_voice)).is_file():
                        raise RuntimeError(f"history_timeline_missing_tts: scene={_idx} path={_voice!r}")
                    _wav = _sync_root / f"scene_{_idx:02d}_trim.wav"
                    _trim = subprocess.run(
                        [
                            "ffmpeg", "-y", "-i", str(_voice),
                            "-af", "silenceremove=start_periods=1:start_duration=0.01:start_threshold=-50dB",
                            "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", str(_wav),
                        ],
                        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
                    )
                    if _trim.returncode != 0 or not _wav.is_file() or _wav.stat().st_size <= 1024 or _probe_194_11(_wav) < 0.15:
                        _trim = subprocess.run(
                            ["ffmpeg", "-y", "-i", str(_voice), "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", str(_wav)],
                            capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
                        )
                    _dur = _probe_194_11(_wav)
                    if _trim.returncode != 0 or _dur < 0.15:
                        raise RuntimeError(f"history_timeline_trim_failed: scene={_idx} duration={_dur:.3f}")
                    _scene_wavs_194_11.append(str(_wav))
                    _scene_durs_194_11.append(_dur)

                # Sprint194-70: protect real MP4 scene duration instead of cutting every
                # scene to the TTS duration. Image-generated MP4s stay TTS-driven.
                #
                # Rule:
                #   real/native video -> max(TTS duration, min(source duration, 5.0s))
                #   image scene       -> TTS duration
                #
                # Any extra video time becomes trailing silence in that scene's narration slot,
                # so the next narration/subtitle/scene all move together and 17↔17 alignment remains intact.
                _history_sources_194_70 = [
                    Path(str(x)) for x in list(generated_files or [])
                    if str(x).strip() and Path(str(x)).is_file()
                ][:len(_scene_wavs_194_11)]

                def _has_audio_194_70(_path):
                    try:
                        _r70 = subprocess.run(
                            [
                                "ffprobe", "-v", "error", "-select_streams", "a:0",
                                "-show_entries", "stream=codec_type",
                                "-of", "default=nw=1:nk=1", str(_path),
                            ],
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace", check=False,
                        )
                        return _r70.returncode == 0 and "audio" in str(_r70.stdout or "").lower()
                    except Exception:
                        return False

                def _looks_like_uploaded_video_194_70(_path, _scene_no):
                    # Sprint194-70B: only strong video provenance counts as a REAL video.
                    # - 69B/69C uploaded videos keep history_NN_source.* next to history_NN.mp4.
                    # - Native audio is handled separately below.
                    # Everything else keeps the old TTS-driven image-scene behavior.
                    try:
                        _p70 = Path(_path)
                        _stem70 = f"history_{int(_scene_no):02d}_source"
                        return any(q.is_file() for q in _p70.parent.glob(_stem70 + ".*"))
                    except Exception:
                        return False

                _requested_video_speed_194_70b = max(0.5, float(playback_speed or 2.0))
                _native_scene_flags_194_70b = []


                _slot_wavs_194_70 = []
                _slot_durs_194_70 = []
                _video_scenes_194_70 = []
                _max_native_scene_seconds_194_70 = 5.0

                for _i70, (_wav70, _tts_dur70) in enumerate(
                    zip(_scene_wavs_194_11, _scene_durs_194_11), start=1
                ):
                    _src70 = (
                        _history_sources_194_70[_i70 - 1]
                        if _i70 - 1 < len(_history_sources_194_70)
                        else None
                    )
                    _src_dur70 = _probe_194_11(_src70) if _src70 else 0.0
                    _has_audio70 = bool(_src70 and _has_audio_194_70(_src70))
                    _looks_video70 = bool(_src70 and _looks_like_uploaded_video_194_70(_src70, _i70))
                    _native70 = bool(_src70 and (_has_audio70 or _looks_video70))
                    _native_scene_flags_194_70b.append(bool(_native70))

                    if _native70 and _src_dur70 > 0.15:
                        # Preserve the COMPLETE real video, but honor the history-video
                        # playback speed (default 2.0x). If TTS is longer, hold the last frame.
                        _played_video_dur70 = float(_src_dur70) / _requested_video_speed_194_70b
                        _slot_dur70 = max(
                            float(_tts_dur70),
                            min(_played_video_dur70, _max_native_scene_seconds_194_70),
                        )
                        _video_scenes_194_70.append(_i70)
                    else:
                        # Image-generated / legacy silent scene: exactly the old TTS slot.
                        _played_video_dur70 = 0.0
                        _slot_dur70 = float(_tts_dur70)

                    # Sprint194-72: only the FINAL History Cookie scene gets an ending cap.
                    # Keep all narration audible, then allow at most 0.75 s of breathing room.
                    # Scenes 1..N-1 are bit-for-bit governed by the existing 70B policy.
                    _ending_cap_applied_194_72 = False
                    _history_scene_count_194_72 = len(_scene_durs_194_11)
                    if (
                        _history_scene_count_194_72 >= 2
                        and int(_i70) == int(_history_scene_count_194_72)
                    ):
                        _ending_cap_194_72 = max(
                            float(_tts_dur70),
                            min(float(_tts_dur70) + 0.75, 5.0),
                        )
                        if float(_slot_dur70) > float(_ending_cap_194_72):
                            _slot_dur70 = float(_ending_cap_194_72)
                            _ending_cap_applied_194_72 = True
                            print("[Sprint194-72 History Ending Duration Cap] APPLIED", {
                                "scene": _i70,
                                "tts_seconds": round(float(_tts_dur70), 3),
                                "slot_seconds": round(float(_slot_dur70), 3),
                                "extra_after_tts_seconds": round(
                                    max(0.0, float(_slot_dur70) - float(_tts_dur70)), 3
                                ),
                                "scene_count": _history_scene_count_194_72,
                                "sync_locked": True,
                            }, flush=True)

                    # Sprint194-74A: leave 0.5 s after the final spoken word.
                    # Padding is added to the final scene WAV too, so narration/subtitle/video
                    # remain on one locked timeline and no speech is truncated.
                    _ending_breath_194_74a = 0.0
                    if (
                        int(_i70) == int(len(_scene_durs_194_11))
                        and len(_scene_durs_194_11) >= 2
                    ):
                        _ending_breath_194_74a = 0.5
                        _slot_dur70 = max(
                            float(_slot_dur70),
                            float(_tts_dur70) + _ending_breath_194_74a,
                        )
                        print("[Sprint194-74A History Ending Breath] APPLIED", {
                            "scene": _i70,
                            "tts_seconds": round(float(_tts_dur70), 3),
                            "slot_seconds": round(float(_slot_dur70), 3),
                            "breath_seconds": 0.5,
                            "voice_not_cut": True,
                        }, flush=True)

                    _pad70 = max(0.0, _slot_dur70 - float(_tts_dur70))
                    if _pad70 > 0.005:
                        _slot_wav70 = _sync_root / f"scene_{_i70:02d}_slot_194_70.wav"
                        _pad_cmd70 = subprocess.run(
                            [
                                "ffmpeg", "-y", "-i", str(_wav70),
                                "-af",
                                f"apad=pad_dur={_pad70:.6f},atrim=duration={_slot_dur70:.6f}",
                                "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le",
                                str(_slot_wav70),
                            ],
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace", check=False,
                        )
                        if (
                            _pad_cmd70.returncode != 0
                            or not _slot_wav70.is_file()
                            or _slot_wav70.stat().st_size <= 1024
                        ):
                            raise RuntimeError(
                                f"history_scene_slot_pad_failed: scene={_i70}: "
                                + str((_pad_cmd70.stderr or _pad_cmd70.stdout or "")[-800:])
                            )
                        _slot_wavs_194_70.append(str(_slot_wav70))
                    else:
                        _slot_wavs_194_70.append(str(_wav70))

                    _slot_durs_194_70.append(_slot_dur70)
                    print("[Sprint194-70B History Scene Duration Protect]", {
                        "scene": _i70,
                        "source": str(_src70) if _src70 else "",
                        "scene_policy": "real-video" if _native70 else "image-tts-original",
                        "native_video": _native70,
                        "has_audio": _has_audio70,
                        "source_sibling": _looks_video70,
                        "source_seconds": round(_src_dur70, 3),
                        "playback_speed": round(_requested_video_speed_194_70b, 3) if _native70 else 1.0,
                        "played_video_seconds": round(_played_video_dur70, 3),
                        "tts_seconds": round(float(_tts_dur70), 3),
                        "slot_seconds": round(_slot_dur70, 3),
                        "added_silence_seconds": round(_pad70, 3),
                        "max_video_seconds": _max_native_scene_seconds_194_70,
                        "ending_cap_applied_194_72": _ending_cap_applied_194_72,
                    }, flush=True)

                _scene_wavs_194_11 = list(_slot_wavs_194_70)
                _scene_durs_194_11 = list(_slot_durs_194_70)

                print("[Sprint194-70B History Timeline Protect] READY", {
                    "scene_count": len(_scene_durs_194_11),
                    "video_scenes": _video_scenes_194_70,
                    "original_tts_seconds": round(sum(
                        _probe_194_11(x) for x in _scene_wavs_194_11
                    ), 3),
                    "extended_timeline_seconds": round(sum(_scene_durs_194_11), 3),
                    "max_native_scene_seconds": _max_native_scene_seconds_194_70,
                    "real_video_playback_speed": _requested_video_speed_194_70b,
                    "image_scenes_keep_tts_duration": True,
                    "scene_narration_subtitle_shift_together": True,
                }, flush=True)

                _concat_file = _sync_root / "scene_audio_concat.txt"
                _concat_file.write_text(
                    "\n".join("file '" + str(Path(x).resolve()).replace("'", "'\\''") + "'" for x in _scene_wavs_194_11) + "\n",
                    encoding="utf-8",
                )
                _full_wav = _sync_root / "narration_full.wav"
                _join = subprocess.run(
                    ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(_concat_file), "-c:a", "pcm_s16le", str(_full_wav)],
                    capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
                )
                if _join.returncode != 0 or not _full_wav.is_file() or _full_wav.stat().st_size <= 1024:
                    raise RuntimeError("history_timeline_audio_concat_failed: " + str((_join.stderr or _join.stdout or "")[-1000:]))

                _full_mp3 = _sync_root / "narration_full.mp3"
                _enc = subprocess.run(
                    ["ffmpeg", "-y", "-i", str(_full_wav), "-c:a", "libmp3lame", "-b:a", "192k", str(_full_mp3)],
                    capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
                )
                if _enc.returncode != 0 or not _full_mp3.is_file() or _full_mp3.stat().st_size <= 1024:
                    raise RuntimeError("history_timeline_audio_encode_failed: " + str((_enc.stderr or _enc.stdout or "")[-1000:]))

                _full_dur_194_11 = _probe_194_11(_full_mp3)
                _sum_dur_194_11 = sum(_scene_durs_194_11)
                # concat 컨테이너/인코딩 오차는 마지막 장면에만 보정하여 모든 장면 시작점이 누적 TTS 길이와 동일하게 유지됩니다.
                if _scene_durs_194_11:
                    _scene_durs_194_11[-1] += _full_dur_194_11 - _sum_dur_194_11

                _history_full_voice_194_11 = str(_full_mp3)
                _history_scene_durations_194_11 = list(_scene_durs_194_11)
                resolved_voice_audio_path = _history_full_voice_194_11
                intro_voice_path = ""

                print("[Sprint194-13 History TTS Boundary Trim]", {
                    "mode": "leading_silence_only",
                    "internal_pause_preserved": True,
                    "scene_count": len(_scene_wavs_194_11),
                }, flush=True)
                print("[Sprint194-11 History Single Timeline] READY", {
                    "narrations": len(normalized_clip_narrations),
                    "tts_files": len(_scene_wavs_194_11),
                    "durations": [round(x, 3) for x in _history_scene_durations_194_11],
                    "duration_sum": round(sum(_history_scene_durations_194_11), 3),
                    "full_voice_seconds": round(_full_dur_194_11, 3),
                    "intro_used": False,
                    "full_script_tts_used": False,
                    "voice_track_count": 1,
                }, flush=True)
            except Exception as _sync_exc:
                print("[Sprint194-11 History Single Timeline] ERROR", type(_sync_exc).__name__, str(_sync_exc), flush=True)
                return {
                    "ok": False,
                    "job_id": "",
                    "state": {},
                    "outputs": {
                        "workflow_version": self.WORKFLOW_VERSION,
                        "execution_mode": "history_single_timeline",
                        "error": f"{type(_sync_exc).__name__}: {_sync_exc}",
                    },
                    "summary": "역사쿠키 장면별 나레이션 동기화에 실패했습니다.",
                    "final_video_path": "",
                }

        if narration_text and not str(resolved_voice_audio_path or "").strip():
            return {
                "ok": False,
                "outputs": {
                    "workflow_version": self.WORKFLOW_VERSION,
                    "tts_generation": tts_generation,
                    "error": "narration_audio_missing",
                },
                "summary": "나레이션 음성 생성에 실패해 영상 제작을 중단했습니다.",
            }

        # Sprint194-9: 역사 모드는 기존 쇼핑 VideoPipeline의 음성/러닝타임 규칙을 완전히 우회합니다.
        # 전체 TTS 1트랙의 실제 길이를 기준으로 이미지 1~N을 직접 렌더링하고,
        # 자막/BGM도 여기서 처리하여 첫 장면 음성만 남는 문제를 차단합니다.
        _history_mode_194_9 = str(channel_type or "").strip() in {"history", "history_ko", "history_en"}
        if _history_mode_194_9:
            try:
                _history_root = Path("exports/history_direct") / f"project_{project_id}"
                _history_root.mkdir(parents=True, exist_ok=True)

                def _probe_dur_194_9(_path):
                    if not _path or not Path(str(_path)).is_file():
                        return 0.0
                    _r = subprocess.run(
                        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(_path)],
                        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
                    )
                    try:
                        return max(0.0, float((_r.stdout or "0").strip() or 0.0))
                    except Exception:
                        return 0.0

                # 장면별 TTS concat이 성공했으면 그것을 우선 사용하고,
                # 실패했어도 전체 대본 TTS(typecast_auto_voice.mp3)는 반드시 사용할 수 있게 폴백합니다.
                _full_voice = str(_history_full_voice_194_11 or resolved_voice_audio_path or "").strip()
                _voice_duration = _probe_dur_194_9(_full_voice)
                if _voice_duration <= 0.5:
                    raise RuntimeError(f"history_full_voice_invalid: path={_full_voice!r} duration={_voice_duration}")

                _image_root = Path("assets/history_scene_images") / f"project_{project_id}"
                _images = sorted(
                    [x for x in _image_root.glob("scene_*.*") if x.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}],
                    key=lambda x: [int(v) if v.isdigit() else v for v in re.split(r"(\d+)", x.stem.lower())],
                )
                _scene_texts = [str(x or "").strip() for x in list(normalized_clip_narrations or [])]
                # Sprint194-10: Streamlit 업로드 이미지는 UI 단계에서 history_XX.mp4로 변환된 뒤
                # 원본 임시 이미지가 사라질 수 있습니다. 원본 이미지가 없으면 이미 전달된
                # history_XX.mp4(generated_files)를 역사 장면 소스로 사용합니다.
                _history_clips = [Path(str(x)) for x in list(generated_files or []) if str(x).strip() and Path(str(x)).is_file()]
                _source_kind = "images" if _images else ("history_clips" if _history_clips else "missing")
                _source_count = len(_images) if _images else len(_history_clips)
                _scene_count = min(_source_count, len(_scene_texts))
                print("[Sprint194-12 History Scene Source]", {
                    "source_kind": _source_kind,
                    "images": len(_images),
                    "history_clips": len(_history_clips),
                    "narrations": len(_scene_texts),
                    "scene_count": _scene_count,
                }, flush=True)
                if _scene_count <= 0:
                    raise RuntimeError(f"history_scene_missing: images={len(_images)} clips={len(_history_clips)} narrations={len(_scene_texts)}")
                _images = _images[:_scene_count]
                _history_clips = _history_clips[:_scene_count]
                _scene_texts = _scene_texts[:_scene_count]

                # Sprint194-12: 역사 장면은 UI에서 전달된 1~N 전체 소스를 그대로 사용합니다.
                print(
                    "[Sprint194-12 History 1to1 Check]",
                    {
                        "timeline": len(_history_scene_durations_194_11),
                        "scene_sources": _scene_count,
                        "narrations": len(_scene_texts),
                        "source_kind": _source_kind,
                    },
                    flush=True,
                )
                # 이미지/자막/나레이션은 동일한 장면별 TTS 실제 길이를 공유합니다.
                if len(_history_scene_durations_194_11) != _scene_count:
                    raise RuntimeError(
                        f"history_timeline_scene_count_mismatch: timeline={len(_history_scene_durations_194_11)} scenes={_scene_count}"
                    )
                _durations = [max(0.15, float(x)) for x in _history_scene_durations_194_11]
                _durations[-1] += _voice_duration - sum(_durations)
                if min(_durations) <= 0:
                    raise RuntimeError(f"history_timeline_invalid_duration: {_durations}")
                _timeline = []
                _cursor = 0.0
                for _i, _d in enumerate(_durations, start=1):
                    _timeline.append({"scene": _i, "start": _cursor, "end": _cursor + _d, "duration": _d})
                    _cursor += _d
                print("[Sprint194-12 History Scene Timeline] READY", {
                    "scene_count": len(_timeline),
                    "start0": round(_timeline[0]["start"], 3) if _timeline else None,
                    "end_last": round(_timeline[-1]["end"], 3) if _timeline else None,
                    "voice_seconds": round(_voice_duration, 3),
                }, flush=True)

                _scene_dir = _history_root / "scenes"
                _scene_dir.mkdir(parents=True, exist_ok=True)
                _scene_videos = []
                _scene_sources = list(_images) if _images else list(_history_clips)

                # Sprint194-18 History Motion Director
                # 장면 번호가 아니라 장면의 의미를 분류해 모든 역사쿠키 영상에 공통 적용합니다.
                # 194-13의 TTS/자막/장면 타임라인은 절대 변경하지 않습니다.
                def _history_role_194_18(idx, text):
                    t = str(text or "").strip()
                    if idx == _scene_count:
                        return "ending"
                    if idx == 1 or any(k in t for k in ["?!", "정말", "놀랍게도", "믿기", "진짜 이야기"]):
                        return "hook"
                    if any(k in t for k in ["쿵", "밟", "충돌", "들이받", "폭발", "쓰러", "사고", "침을 뱉", "비웃"]):
                        return "impact"
                    if any(k in t for k in ["눈물", "울", "야위", "초라", "불쌍", "슬퍼", "외로", "힘없이", "심각해"]):
                        return "emotion"
                    if any(k in t for k in ["다가가", "힐끗", "노려", "긴장", "위협", "다가오", "발이 움직"]):
                        return "tension"
                    if any(k in t for k in ["배를 타", "바다", "건너", "향함", "돌아오", "육지", "멀어지는", "도착"]):
                        return "travel"
                    if any(k in t for k in ["다시", "풀어", "해제", "돌려보", "돌아왔", "살게", "결국"]):
                        return "resolution"
                    if any(k in t for k in ["정신없이 먹", "엄청나게 먹", "먹이", "콩", "황당", "난감"]):
                        return "comedy"
                    if any(k in t for k in ["실록", "기록", "보고서", "지도", "장부", "회의", "논의", "태종", "신하"]):
                        return "explain"

                    # Sprint194-75H: English History Cookie semantic roles.
                    # 75FB's Korean-only vocabulary made nearly every English body
                    # scene "normal", so ting fell onto scenes 2/3 by fallback.
                    tl = t.lower()
                    if any(k in tl for k in [
                        "fell off", "crashed", "collision", "kicked", "hit him",
                        "slammed", "exploded", "accident", "spat at",
                    ]):
                        return "impact"
                    if any(k in tl for k in [
                        "cried", "tears", "starving", "starved", "frail",
                        "sick", "worried", "mourning", "sad", "lonely",
                    ]):
                        return "emotion"
                    if any(k in tl for k in [
                        "threat", "tense", "danger", "approached", "stared",
                        "looked around", "don't let", "don't record",
                    ]):
                        return "tension"
                    if any(k in tl for k in [
                        "sailed", "island", "sea", "returned", "back to land",
                        "arrived", "journey",
                    ]):
                        return "travel"
                    if any(k in tl for k in [
                        "finally", "returned", "came back", "once mourning ended",
                        "normal meals returned", "released",
                    ]):
                        return "resolution"
                    if any(k in tl for k in [
                        "loved meat", "couldn't resist", "could not resist",
                        "ate", "eating", "food", "huge appetite", "ridiculous",
                    ]):
                        return "comedy"
                    if any(k in tl for k in [
                        "annals", "recorded", "record", "historian", "historians",
                        "royal recorder", "report", "ministers", "king taejong",
                        "taejong", "final wish", "historical record",
                    ]):
                        return "explain"
                    return "normal"

                _scene_roles_194_18 = [
                    _history_role_194_18(i, _scene_texts[i-1] if i-1 < len(_scene_texts) else "")
                    for i in range(1, _scene_count + 1)
                ]

                # Sprint194-19: 역할별 강도를 명시적으로 차등화합니다.
                # IMPACT는 전체 장면을 흔들지 않고 시작 0.32초만 강한 zoom-punch + 감쇠 shake를 적용합니다.
                _motion_intensity_194_19 = {
                    "normal": 0.30, "explain": 0.35, "travel": 0.50, "comedy": 0.60,
                    "tension": 0.72, "emotion": 0.80, "resolution": 0.55,
                    "hook": 0.85, "ending": 0.90, "impact": 1.00,
                }

                # Sprint194-37: History framing/motion tuning.
                # Keep normal scenes slightly wider so characters/props are not always edge-to-edge.
                # Reserve stronger scale only for semantic emphasis, so impact zoom has visible room to move.
                def _motion_filter_194_18(role, idx, dur):
                    d = max(0.5, float(dur))
                    intensity = _motion_intensity_194_19.get(role, 0.30)
                    if role == "impact":
                        # Wider base -> short 1.07x punch + restrained 0.28s decay shake.
                        return ("scale='if(lt(t,0.14),1080*(1+0.07*t/0.14),1156)':"
                                "h='if(lt(t,0.14),1920*(1+0.07*t/0.14),2055)':eval=frame:"
                                "force_original_aspect_ratio=increase,"
                                "crop=1080:1920:"
                                "x='(iw-1080)/2+if(lt(t,0.28),12*sin(105*t)*(1-t/0.28),0)':"
                                "y='(ih-1920)/2+if(lt(t,0.28),8*sin(131*t)*(1-t/0.28),0)',"
                                "fps=30,format=yuv420p")
                    if role == "hook":
                        return "scale=1165:2072:force_original_aspect_ratio=increase,crop=1080:1920:x='(iw-1080)/2':y='(ih-1920)/2',fps=30,format=yuv420p"
                    if role == "emotion":
                        return (f"scale='1080+90*t/{d:.6f}':h='1920+160*t/{d:.6f}':eval=frame:force_original_aspect_ratio=increase,"
                                f"crop=1080:1920:x='(iw-1080)/2':y='(ih-1920)*(0.58-0.16*t/{d:.6f})',fps=30,format=yuv420p")
                    if role == "tension":
                        return (f"scale='1080+110*t/{d:.6f}':h='1920+196*t/{d:.6f}':eval=frame:force_original_aspect_ratio=increase,"
                                f"crop=1080:1920:x='(iw-1080)*(0.20+0.60*t/{d:.6f})':y='(ih-1920)/2',fps=30,format=yuv420p")
                    if role == "travel":
                        return ("scale=1125:2000:force_original_aspect_ratio=increase,"
                                f"crop=1080:1920:x='(iw-1080)*(0.10+0.80*t/{d:.6f})':y='(ih-1920)/2',fps=30,format=yuv420p")
                    if role == "resolution":
                        return ("scale=1115:1982:force_original_aspect_ratio=increase,"
                                f"crop=1080:1920:x='(iw-1080)/2':y='(ih-1920)*(0.58-0.16*t/{d:.6f})',fps=30,format=yuv420p")
                    if role == "comedy":
                        return ("scale=1150:2045:force_original_aspect_ratio=increase,"
                                f"crop=1080:1920:x='(iw-1080)*(0.22+0.56*t/{d:.6f})':y='(ih-1920)/2',fps=30,format=yuv420p")
                    if role == "ending":
                        return ("scale='if(lt(t,0.24),1135+80*(1-t/0.24),1135)':"
                                "h='if(lt(t,0.24),2018+142*(1-t/0.24),2018)':eval=frame:"
                                "force_original_aspect_ratio=increase,crop=1080:1920:"
                                "x='(iw-1080)/2':y='(ih-1920)/2',fps=30,format=yuv420p")
                    if role == "explain":
                        return (f"scale='1080+70*t/{d:.6f}':h='1920+124*t/{d:.6f}':eval=frame:force_original_aspect_ratio=increase,"
                                f"crop=1080:1920:x='(iw-1080)*(0.78-0.56*t/{d:.6f})':y='(ih-1920)/2',fps=30,format=yuv420p")
                    if idx % 2:
                        return (f"scale='1080+60*t/{d:.6f}':h='1920+107*t/{d:.6f}':eval=frame:force_original_aspect_ratio=increase,"
                                f"crop=1080:1920:x='(iw-1080)/2':y='(ih-1920)*(0.47+0.06*t/{d:.6f})',fps=30,format=yuv420p")
                    return (f"scale='1080+60*t/{d:.6f}':h='1920+107*t/{d:.6f}':eval=frame:force_original_aspect_ratio=increase,"
                            f"crop=1080:1920:x='(iw-1080)/2':y='(ih-1920)*(0.53-0.06*t/{d:.6f})',fps=30,format=yuv420p")

                _scene_videos = []
                _motion_plan_194_18 = []
                for _idx, (_src, _dur) in enumerate(zip(_scene_sources, _durations), start=1):
                    _out = _scene_dir / f"scene_{_idx:02d}.mp4"
                    _d = max(0.5, float(_dur))
                    _role = _scene_roles_194_18[_idx-1]
                    _src_path_194_56 = Path(str(_src))
                    _is_native_clip_194_56 = _source_kind != "images"

                    # Sprint194-58: regression restore. Native history MP4s are NOT re-rendered per scene.
                    # They are registered here and trimmed/concatenated once in a single FFmpeg filter graph below.
                    # This restores the pre-cache behavior that preserved Scene 1 motion.
                    if _is_native_clip_194_56:
                        _scene_videos.append(str(_src_path_194_56))
                        print("[Sprint194-58 History Native Direct Source]", {
                            "scene": _idx, "source": str(_src_path_194_56), "target_seconds": round(_d, 3),
                            "intermediate_render": False,
                        }, flush=True)
                    else:
                        _vf = _motion_filter_194_18(_role, _idx, _d)
                        _cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(_src_path_194_56), "-vf", _vf,
                                "-t", f"{_d:.3f}", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                                "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(_out)]
                        _r = subprocess.run(_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
                        if _r.returncode != 0 or not _out.is_file() or _out.stat().st_size <= 1024:
                            raise RuntimeError("history_scene_render_failed: " + str((_r.stderr or _r.stdout or "")[-1200:]))
                        _scene_videos.append(str(_out))
                        print("[Sprint194-58 History Image Scene Render]", {"scene": _idx, "path": str(_out)}, flush=True)

                    _motion_plan_194_18.append({"scene": _idx, "role": _role, "intensity": _motion_intensity_194_19.get(_role, 0.30), "motion": (
                        "native-video-preserved" if _is_native_clip_194_56 else {
                            "hook":"impact-framing", "explain":"slow-pan", "comedy":"quick-pan", "tension":"tension-push",
                            "impact":"impact-zoom-framing+0.28s-shake", "emotion":"emotion-push", "travel":"wide-pan",
                            "resolution":"gentle-release", "ending":"cookie-pop-framing", "normal":"soft-drift"}.get(_role, "soft-drift")
                    )})
                    print("[Sprint194-57 History Native Clip Verify]", {"scene": _idx, "native_video": _is_native_clip_194_56, "source": str(_src_path_194_56)}, flush=True)

                print("[Sprint194-38 History Motion Render Verify] READY", {
                    "scene_count": len(_scene_videos),
                    "roles": _scene_roles_194_18,
                    "motion_plan": _motion_plan_194_18,
                    "impact_shake_seconds": 0.28,
                    "random_motion": False,
                    "timeline_locked": True,
                    "voice_seconds": round(_voice_duration, 3),
                    "shopping_pipeline_untouched": True,
                    "rendered_scene_files": _scene_videos,
                }, flush=True)

                # Sprint194-69:
                # - Native MP4 scene with an audio stream -> preserve that original scene audio.
                # - Image/rendered-silent scene -> eligible for automatic history SFX.
                # This does NOT alter the 17-scene video/TTS timeline.
                def _has_audio_stream_194_69(_path):
                    try:
                        _probe69 = subprocess.run(
                            [
                                "ffprobe", "-v", "error", "-select_streams", "a:0",
                                "-show_entries", "stream=codec_type",
                                "-of", "default=nw=1:nk=1", str(_path),
                            ],
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace", check=False,
                        )
                        return _probe69.returncode == 0 and "audio" in str(_probe69.stdout or "").lower()
                    except Exception:
                        return False

                _scene_native_audio_194_69 = {}
                _native_audio_events_194_69 = []

                # Sprint194-69A: audio must come from the ORIGINAL UI-supplied MP4 source,
                # never from a rendered/intermediate scene file.
                _original_audio_sources_194_69a = list(_scene_sources)
                for _ev69, _src69 in zip(_timeline, _original_audio_sources_194_69a):
                    _scene69 = int(_ev69.get("scene") or 0)
                    _srcp69 = Path(str(_src69))
                    _has69 = bool(_source_kind != "images" and _has_audio_stream_194_69(_srcp69))
                    _scene_native_audio_194_69[_scene69] = _has69
                    if _has69:
                        _native_audio_events_194_69.append((
                            _srcp69,
                            int(round(float(_ev69["start"]) * 1000.0)),
                            max(0.15, float(_ev69["duration"])),
                            _scene69,
                        ))
                    print("[Sprint194-69A History Original Audio Source]", {
                        "scene": _scene69,
                        "original_source": str(_srcp69),
                        "native_audio": _has69,
                        "auto_sfx_eligible": not _has69,
                        "source_is_original": True,
                    }, flush=True)

                print("[Sprint194-69A History Native Audio Policy] READY", {
                    "native_audio_scenes": [x[3] for x in _native_audio_events_194_69],
                    "image_or_silent_sfx_scenes": [
                        i for i in range(1, _scene_count + 1)
                        if not _scene_native_audio_194_69.get(i, False)
                    ],
                    "native_video_audio_preserved": True,
                    "audio_source": "original-scene-source",
                    "auto_sfx_native_video": False,
                }, flush=True)

                _silent_video = _history_root / "history_silent.mp4"
                if _source_kind != "images":
                    # Sprint194-58: decode each ORIGINAL MP4 once, trim to its TTS slot, then concatenate.
                    # No scene_XX.mp4 intermediate exists for native clips.
                    _native_inputs_194_58 = []
                    _native_filters_194_58 = []
                    for _j58, (_src58, _d58) in enumerate(zip(_scene_videos, _durations)):
                        _native_inputs_194_58 += ["-i", str(_src58)]
                        _dd58 = max(0.5, float(_d58))
                        _is_real_video_70b = bool(
                            _j58 < len(_native_scene_flags_194_70b)
                            and _native_scene_flags_194_70b[_j58]
                        )
                        _speed_prefix_70b = (
                            f"setpts=(PTS-STARTPTS)/{_requested_video_speed_194_70b:.6f},"
                            if _is_real_video_70b
                            else "setpts=PTS-STARTPTS,"
                        )
                        _native_filters_194_58.append(
                            f"[{_j58}:v]{_speed_prefix_70b}"
                            f"scale=1080:1920:force_original_aspect_ratio=increase,"
                            f"crop=1080:1920,fps=30,tpad=stop_mode=clone:stop_duration={_dd58:.3f},"
                            f"trim=duration={_dd58:.3f},setpts=PTS-STARTPTS,format=yuv420p[v{_j58}]"
                        )
                    _native_filters_194_58.append(
                        "".join(f"[v{k}]" for k in range(len(_scene_videos))) +
                        f"concat=n={len(_scene_videos)}:v=1:a=0[vout]"
                    )
                    _cmd58 = ["ffmpeg", "-y"] + _native_inputs_194_58 + [
                        "-filter_complex", ";".join(_native_filters_194_58), "-map", "[vout]",
                        "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(_silent_video),
                    ]
                    _r = subprocess.run(_cmd58, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
                    if _r.returncode != 0 or not _silent_video.is_file() or _silent_video.stat().st_size <= 1024:
                        raise RuntimeError("history_native_direct_concat_failed: " + str((_r.stderr or _r.stdout or "")[-1600:]))
                    print("[Sprint194-58 History Native Direct Timeline] READY", {
                        "scene_count": len(_scene_videos), "intermediate_scene_renders": 0,
                        "voice_seconds": round(_voice_duration, 3), "silent_video": str(_silent_video),
                    }, flush=True)
                    # Scene-1 regression guard against the actual combined timeline.
                    def _frame_md5_194_58(_path, _sec):
                        _p58 = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0.0,float(_sec)):.3f}", "-i", str(_path),
                                               "-frames:v", "1", "-f", "md5", "-"],
                                              capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
                        return str((_p58.stdout or "").strip())
                    _probe58 = max(0.35, min(1.25, float(_durations[0]) * 0.65))
                    _src1_58 = Path(str(_scene_videos[0]))
                    _sm58 = _frame_md5_194_58(_src1_58, 0.12) != _frame_md5_194_58(_src1_58, _probe58)
                    _fm58 = _frame_md5_194_58(_silent_video, 0.12) != _frame_md5_194_58(_silent_video, _probe58)
                    print("[Sprint194-58 History Scene1 Motion Guard]", {"source_moves": _sm58, "final_timeline_moves": _fm58, "probe_second": round(_probe58,3)}, flush=True)
                    if _sm58 and not _fm58:
                        raise RuntimeError("history_scene1_motion_regression_after_direct_timeline")
                else:
                    _concat_list = _history_root / "video_concat.txt"
                    _concat_list.write_text("\n".join("file '" + str(Path(v).resolve()).replace("'", "'\\''") + "'" for v in _scene_videos) + "\n", encoding="utf-8")
                    _r = subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(_concat_list), "-c", "copy", str(_silent_video)],
                                        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
                    if _r.returncode != 0 or not _silent_video.is_file() or _silent_video.stat().st_size <= 1024:
                        raise RuntimeError("history_video_concat_failed: " + str((_r.stderr or _r.stdout or "")[-1200:]))

                # ASS 자막: 장면 길이와 1:1 타이밍. 빈 자막은 건너뜁니다.
                def _ass_time_194_9(sec):
                    sec = max(0.0, float(sec))
                    h = int(sec // 3600); sec -= h * 3600
                    m = int(sec // 60); sec -= m * 60
                    s2 = int(sec); cs = int(round((sec - s2) * 100))
                    if cs >= 100: s2 += 1; cs -= 100
                    return f"{h}:{m:02d}:{s2:02d}.{cs:02d}"

                _subs = [str(x or "").strip() for x in list(clip_subtitles or [])][: _scene_count]

                # Sprint194-31: English-only mobile subtitle readability.
                # Balance long English captions into at most two word-boundary lines.
                # Korean History Cookie and shopping subtitles are untouched.
                _is_history_en_194_31 = str(channel_type or "").strip().lower() == "history_en"
                def _wrap_english_subtitle_194_31(text, target=19, hard=22):
                    text = " ".join(str(text or "").replace("\n", " ").split()).strip()
                    if not text or not _is_history_en_194_31 or len(text) <= hard:
                        return text
                    words = text.split()
                    if len(words) < 2:
                        return text
                    # Pick the split whose two line lengths are most balanced, while
                    # preferring lines near the mobile-safe target width.
                    best = None
                    for i in range(1, len(words)):
                        a = " ".join(words[:i]); b = " ".join(words[i:])
                        score = abs(len(a)-len(b)) + max(0, len(a)-hard)*8 + max(0, len(b)-hard)*8
                        score += abs(max(len(a),len(b))-target) * 0.15
                        if best is None or score < best[0]:
                            best = (score, a, b)
                    return (best[1] + "\n" + best[2]) if best else text
                # Sprint194-35: merge the English subtitle unicode/emoji safety fix with
                # the Korean mobile-audio branch.  This runs only on rendered English
                # subtitles; narration text and Korean subtitles are intentionally untouched.
                def _sanitize_english_subtitle_194_35(text):
                    import unicodedata
                    out = []
                    removed = 0
                    for ch in str(text or ""):
                        cp = ord(ch)
                        cat = unicodedata.category(ch)
                        is_emoji_range = (
                            0x1F000 <= cp <= 0x1FAFF or
                            0x2600 <= cp <= 0x27BF or
                            0x2300 <= cp <= 0x23FF or
                            0xFE00 <= cp <= 0xFE0F or
                            0x1F1E6 <= cp <= 0x1F1FF or
                            cp in {0x200D, 0x20E3}
                        )
                        # Strip emoji/pictographs, variation selectors, joiners, private-use
                        # and surrogate/control artifacts that commonly render as tofu boxes.
                        if is_emoji_range or cat in {"Cs", "Co"}:
                            removed += 1
                            continue
                        if cat == "Cf" and ch not in {"\n", "\t"}:
                            removed += 1
                            continue
                        out.append(ch)
                    cleaned = "".join(out)
                    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
                    cleaned = re.sub(r" *\n *", "\n", cleaned).strip()
                    return cleaned, removed

                if _is_history_en_194_31:
                    _cleaned_subs_194_35 = []
                    _removed_unicode_194_35 = 0
                    for _sub_194_35 in _subs:
                        _clean_194_35, _removed_194_35 = _sanitize_english_subtitle_194_35(_sub_194_35)
                        _cleaned_subs_194_35.append(_clean_194_35)
                        _removed_unicode_194_35 += _removed_194_35
                    _subs = [_wrap_english_subtitle_194_31(x) for x in _cleaned_subs_194_35]
                    print("[Sprint194-35 English Subtitle Unicode Safe] READY", {
                        "count": len(_subs),
                        "removed_codepoints": _removed_unicode_194_35,
                        "narration_untouched": True,
                        "korean_subtitles_untouched": True,
                    }, flush=True)
                    print("[Sprint194-31 English Subtitle] READY", {
                        "count": len(_subs),
                        "wrapped": sum("\n" in x for x in _subs),
                        "max_line_chars": max([max([len(y) for y in x.split("\n")]+[0]) for x in _subs]+[0]),
                    }, flush=True)

                # Sprint194-58: restore History Cookie typography from the known-good 194-48/49A path.
                _history_body_font_194_48 = "Cinzel" if _is_history_en_194_31 else "이순신 돋움체"
                _history_emphasis_font_194_48 = "Bebas Neue" if _is_history_en_194_31 else "청소년성취포상제체"
                _history_body_size_194_48 = 68 if _is_history_en_194_31 else 76
                _history_emphasis_size_194_48 = int(round(_history_body_size_194_48 * 1.18))
                _font_dir_194_48d = _history_root / "fonts_48d"
                _font_dir_194_48d.mkdir(parents=True, exist_ok=True)
                _font_resolve_194_48d = {}
                try:
                    import winreg
                    import shutil as _shutil_194_48d
                    _font_registry_194_48d = []
                    for _hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                        try:
                            with winreg.OpenKey(_hive, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts") as _rk:
                                _j = 0
                                while True:
                                    try:
                                        _n, _v, _typ = winreg.EnumValue(_rk, _j); _j += 1
                                        _font_registry_194_48d.append((str(_n), str(_v)))
                                    except OSError: break
                        except OSError: pass
                    _targets_194_48d = {
                        "body": ["Cinzel"] if _is_history_en_194_31 else ["이순신 돋움", "이순신돋움", "YiSunShin Dotum", "YiSunShinDotum"],
                        "emphasis": ["Bebas Neue", "BebasNeue"] if _is_history_en_194_31 else ["청소년성취포상제", "청소년 성취포상제", "Korea Youth Award"],
                    }
                    _win_fonts_194_48d = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
                    _user_fonts_194_59 = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "Fonts"

                    def _norm_font_name_194_59(_value):
                        return re.sub(r"[^0-9a-z가-힣]+", "", str(_value or "").lower())

                    def _copy_font_hit_194_59(_srcf, _display_name, _source_kind):
                        try:
                            _srcf = Path(_srcf)
                            if not _srcf.is_file():
                                return None
                            _dstf = _font_dir_194_48d / _srcf.name
                            _shutil_194_48d.copy2(_srcf, _dstf)
                            return {"registry_name": str(_display_name), "source": str(_srcf), "local": str(_dstf), "resolver": _source_kind}
                        except Exception:
                            return None

                    def _font_file_family_names_194_59(_font_path):
                        _names = []
                        try:
                            from fontTools.ttLib import TTFont
                            _tt = TTFont(str(_font_path), lazy=True, fontNumber=0)
                            try:
                                for _rec in _tt["name"].names:
                                    if _rec.nameID not in (1, 4, 6, 16):
                                        continue
                                    try:
                                        _txt = _rec.toUnicode().strip()
                                    except Exception:
                                        continue
                                    if _txt and _txt not in _names:
                                        _names.append(_txt)
                            finally:
                                _tt.close()
                        except Exception:
                            pass
                        return _names

                    for _kind, _aliases in _targets_194_48d.items():
                        _hit = None
                        _alias_norms = [_norm_font_name_194_59(a) for a in _aliases if a]

                        # 1) Preserve the known-good registry lookup first.
                        for _reg_name, _reg_file in _font_registry_194_48d:
                            _reg_norm = _norm_font_name_194_59(_reg_name)
                            if any(a and a in _reg_norm for a in _alias_norms):
                                _srcf = Path(_reg_file)
                                if not _srcf.is_absolute():
                                    _srcf = _win_fonts_194_48d / _srcf
                                _hit = _copy_font_hit_194_59(_srcf, _reg_name, "registry")
                                if _hit:
                                    break

                        # 2) Sprint194-59 ONLY fallback: scan installed font files.
                        #    This fixes fonts that exist in Windows/User Fonts but have no
                        #    matching registry display name. No renderer/TTS/timeline code changes.
                        if _hit is None:
                            _font_files = []
                            for _font_root in (_user_fonts_194_59, _win_fonts_194_48d):
                                if not _font_root.is_dir():
                                    continue
                                try:
                                    _font_files.extend([x for x in _font_root.iterdir() if x.is_file() and x.suffix.lower() in (".ttf", ".otf", ".ttc")])
                                except Exception:
                                    pass

                            # Fast filename/stem match first.
                            for _font_path in _font_files:
                                _stem_norm = _norm_font_name_194_59(_font_path.stem)
                                if any(a and (a in _stem_norm or _stem_norm in a) for a in _alias_norms):
                                    _hit = _copy_font_hit_194_59(_font_path, _font_path.stem, "filename-scan")
                                    if _hit:
                                        break

                            # If filename is unrelated, inspect the font's internal family names.
                            if _hit is None:
                                for _font_path in _font_files:
                                    _family_names = _font_file_family_names_194_59(_font_path)
                                    _matched_family = None
                                    for _family_name in _family_names:
                                        _family_norm = _norm_font_name_194_59(_family_name)
                                        if any(a and (a in _family_norm or _family_norm in a) for a in _alias_norms):
                                            _matched_family = _family_name
                                            break
                                    if _matched_family:
                                        _hit = _copy_font_hit_194_59(_font_path, _matched_family, "font-name-table")
                                        if _hit:
                                            break

                        # Sprint194-60 ONLY: Korean emphasis font is installed under the
                        # Windows family name "청소년서체" and file Youth.ttf. Bind that exact
                        # known path without changing any subtitle selection/render/timeline logic.
                        if _kind == "emphasis" and (not _is_history_en_194_31):
                            _youth_font_194_60 = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "Fonts" / "Youth.ttf"
                            if _youth_font_194_60.is_file():
                                _direct_hit_194_60 = _copy_font_hit_194_59(_youth_font_194_60, "청소년서체 (TrueType)", "direct-youth-194-60")
                                if _direct_hit_194_60:
                                    _hit = _direct_hit_194_60

                        _font_resolve_194_48d[_kind] = _hit
                except Exception as _font_exc_194_48d:
                    _font_resolve_194_48d["error"] = f"{type(_font_exc_194_48d).__name__}: {_font_exc_194_48d}"
                def _ass_family_194_58(_hit, _fallback):
                    _name = str((_hit or {}).get("registry_name") or "").strip()
                    if not _name: return _fallback
                    _name = re.sub(r"\s*\((?:TrueType|OpenType)\)\s*$", "", _name, flags=re.I).strip()
                    _name = re.sub(r"\s+(?:Regular|Normal)\s*$", "", _name, flags=re.I).strip()
                    return _name or _fallback
                _history_body_font_194_48 = _ass_family_194_58(_font_resolve_194_48d.get("body"), _history_body_font_194_48)
                _history_emphasis_font_194_48 = _ass_family_194_58(_font_resolve_194_48d.get("emphasis"), _history_emphasis_font_194_48)
                print("[Sprint194-60 History Youth Font Direct] READY", {"body": _history_body_font_194_48, "emphasis": _history_emphasis_font_194_48, "resolved": _font_resolve_194_48d}, flush=True)

                _ass = _history_root / "history_subtitles.ass"
                _ass_lines = [
                    "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 2", "ScaledBorderAndShadow: yes", "",
                    "[V4+ Styles]",
                    "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
                    f"Style: Default,{_history_body_font_194_48},{_history_body_size_194_48},&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,4,0,2,140,140,620,1",
                    f"Style: Hook,{_history_body_font_194_48},{_history_body_size_194_48},&H004AD8FF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,4,0,2,140,140,620,1",
                    f"Style: Impact,{_history_body_font_194_48},{_history_body_size_194_48},&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,4,0,2,140,140,620,1",
                    f"Style: Emotion,{_history_body_font_194_48},{_history_body_size_194_48},&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,-1,0,0,100,100,0,0,1,4,0,2,140,140,620,1",
                    f"Style: Comedy,{_history_body_font_194_48},{_history_body_size_194_48},&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,4,0,2,140,140,620,1",
                    f"Style: Ending,{_history_body_font_194_48},{_history_body_size_194_48},&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,4,0,2,140,140,620,1", "",
                    "[Events]", "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text",
                ]
                _t = 0.0
                _emphasis_verify_194_38 = []
                _subtitle_boxes_194_64 = []

                # Sprint194-75F: generic History Cookie ting policy.
                # Hook always ting-bounces. Up to two additional scenes are selected
                # automatically from the renderer's existing semantic-emphasis picks.
                # This is topic-independent: no Taejong/elephant/Sejong keywords.
                # Sprint194-75FB: choose body ting scenes from the already-built
                # History Motion Director roles, not from raw subtitle text. This avoids
                # mojibake/corrupted Korean keywords and remains topic-independent.
                # Hook is fixed to scene 1 only.
                _ting_auto_scenes_194_75f = []
                _ting_auto_roles_194_75fb = {}

                _ting_role_priority_194_75fb = {
                    "impact": 100,
                    "tension": 90,
                    "emotion": 80,
                    "resolution": 75,
                    "comedy": 65,
                    "explain": 45,
                    "travel": 35,
                    "normal": 0,
                    "hook": -100,
                    "ending": -100,
                }

                _ting_candidates_194_75fb = []
                for _scene_no_194_75fb, _scene_role_194_75fb in enumerate(
                    list(_scene_roles_194_18 or []), start=1
                ):
                    if _scene_no_194_75fb <= 1 or _scene_no_194_75fb >= _scene_count:
                        continue
                    _role_name_194_75fb = str(_scene_role_194_75fb or "normal").strip().lower()
                    _score_194_75fb = int(_ting_role_priority_194_75fb.get(_role_name_194_75fb, 0))
                    if _score_194_75fb <= 0:
                        continue
                    _ting_candidates_194_75fb.append(
                        (_score_194_75fb, _scene_no_194_75fb, _role_name_194_75fb)
                    )

                # Strongest semantic roles first; on equal role strength, earlier scene wins.
                _ting_candidates_194_75fb.sort(key=lambda x: (-x[0], x[1]))
                for _score_194_75fb, _scene_no_194_75fb, _role_name_194_75fb in _ting_candidates_194_75fb:
                    if _scene_no_194_75fb not in _ting_auto_scenes_194_75f:
                        _ting_auto_scenes_194_75f.append(_scene_no_194_75fb)
                        _ting_auto_roles_194_75fb[_scene_no_194_75fb] = _role_name_194_75fb
                    if len(_ting_auto_scenes_194_75f) >= 2:
                        break

                print("[Sprint194-75FB History Generic Ting Plan] READY", {
                    "hook_scene": 1,
                    "auto_scenes": list(_ting_auto_scenes_194_75f),
                    "auto_roles": dict(_ting_auto_roles_194_75fb),
                    "max_auto": 2,
                    "source": "history-motion-director-roles",
                    "raw_subtitle_text_used": False,
                    "later_hook_roles_ignored": True,
                    "topic_specific_keywords": False,
                }, flush=True)

                for _i, _d in enumerate(_durations):
                    _sub = _subs[_i] if _i < len(_subs) else ""
                    # Sprint194-64: Scene 1 long hook only - force a balanced mobile-safe 2-line caption.
                    # Timeline/TTS/source subtitle data are not changed; only the ASS display string is wrapped.
                    if _i == 0 and _sub and "\n" not in _sub and len(_sub) >= 18:
                        _spaces64 = [m.start() for m in re.finditer(r"\s+", _sub)]
                        if _spaces64:
                            _mid64 = len(_sub) / 2.0
                            _cut64 = min(_spaces64, key=lambda x: abs(x - _mid64))
                            _sub = _sub[:_cut64].rstrip() + "\n" + _sub[_cut64:].lstrip()
                    if _sub:
                        _role = _scene_roles_194_18[_i] if _i < len(_scene_roles_194_18) else "normal"
                        _style = {"hook":"Hook", "impact":"Impact", "emotion":"Emotion", "comedy":"Comedy", "ending":"Ending"}.get(_role, "Default")
                        _fx = r"{\fs72}" if _is_history_en_194_31 else ""
                        if _role in {"hook", "impact"}:
                            _fx = r"{\fad(40,100)\fscx112\fscy112\t(0,180,\fscx100\fscy100)}"
                        elif _role == "comedy":
                            _fx = r"{\fad(70,120)\fscx106\fscy106\t(0,220,\fscx100\fscy100)}"
                        elif _role == "emotion":
                            _fx = r"{\fad(280,220)}"
                        elif _role == "ending":
                            _fx = r"{\fad(80,180)\fscx114\fscy114\t(0,220,\fscx100\fscy100)}"
                        else:
                            _fx = r"{\fad(100,120)}"

                        if _is_history_en_194_31:
                            # Sprint194-41: fixed English subtitle size + safe horizontal margins.
                            # Disable scale-up transforms that can clip hook text at frame edges.
                            if _role in {"hook", "impact", "comedy"}:
                                _fx = r"{\fs72\fad(80,140)}"
                            elif _role == "ending":
                                _fx = r"{\fs76\fad(80,160)}"
                            else:
                                _fx = r"{\fs72}" + _fx

                        # Sprint194-74: automatic subtitle motion for IMAGE / silent scenes.
                        # Native-video scenes keep their original visual/audio presentation.
                        _scene_no_194_74 = _i + 1
                        _is_native_audio_scene_194_74 = bool(
                            _scene_native_audio_194_69.get(_scene_no_194_74, False)
                        )
                        _fx_kind_194_74 = "role-default"

                        # Sprint194-75A: Ting is intentionally limited to three story beats:
                        # 1) hook, 2) DON'T LET ... RECORDER ..., 3) DON'T RECORD THIS!
                        # Hook may be native video/audio, so only its subtitle motion changes.
                        if _scene_no_194_74 == 1:
                            _fx = (
                                r"{\fs82\b1\fad(15,100)\fscx72\fscy72"
                                r"\t(0,90,\fscx132\fscy132)"
                                r"\t(90,175,\fscx94\fscy94)"
                                r"\t(175,245,\fscx106\fscy106)"
                                r"\t(245,330,\fscx100\fscy100)}"
                                if _is_history_en_194_31
                                else
                                r"{\b1\fad(15,100)\fscx72\fscy72"
                                r"\t(0,90,\fscx132\fscy132)"
                                r"\t(90,175,\fscx94\fscy94)"
                                r"\t(175,245,\fscx106\fscy106)"
                                r"\t(245,330,\fscx100\fscy100)}"
                            )
                            _fx_kind_194_74 = "ting-hook"

                        if not _is_native_audio_scene_194_74:
                            _semantic_text_194_74 = (
                                str(_sub or "") + " "
                                + (
                                    str(_scene_texts[_i] or "")
                                    if _i < len(_scene_texts) else ""
                                )
                            ).lower()

                            if _role == "ending" or "subscribe" in _semantic_text_194_74:
                                _fx = (
                                    r"{\fs78\fad(50,180)\fscx118\fscy118"
                                    r"\t(0,220,\fscx100\fscy100)}"
                                    if _is_history_en_194_31
                                    else
                                    r"{\fad(50,180)\fscx118\fscy118\t(0,220,\fscx100\fscy100)}"
                                )
                                _fx_kind_194_74 = "subscribe-pop"
                            # Sprint194-75F: topic-independent automatic ting.
                            # The scene is selected by the already-existing semantic
                            # emphasis picker, not by hard-coded story words.
                            elif _scene_no_194_74 in _ting_auto_scenes_194_75f:
                                _fx = (
                                    r"{\fs82\b1\fad(15,100)\fscx72\fscy72"
                                    r"\t(0,90,\fscx132\fscy132)"
                                    r"\t(90,175,\fscx94\fscy94)"
                                    r"\t(175,245,\fscx106\fscy106)"
                                    r"\t(245,330,\fscx100\fscy100)}"
                                    if _is_history_en_194_31
                                    else
                                    r"{\b1\fad(15,100)\fscx72\fscy72"
                                    r"\t(0,90,\fscx132\fscy132)"
                                    r"\t(90,175,\fscx94\fscy94)"
                                    r"\t(175,245,\fscx106\fscy106)"
                                    r"\t(245,330,\fscx100\fscy100)}"
                                )
                                _fx_kind_194_74 = "ting-auto-emphasis"
                                print("[Sprint194-75FB History Generic Ting Applied]", {
                                    "scene": _scene_no_194_74,
                                    "role": _role,
                                    "ting_kind": _fx_kind_194_74,
                                    "source": "semantic-emphasis",
                                }, flush=True)
                            elif any(k in _semantic_text_194_74 for k in [
                                "urgent", "don't", "do not", "never", "record this",
                                "recorded", "cover-up", "fell off", "낙마", "기록했다",
                                "기록하", "알리지 말", "숨기"
                            ]):
                                _fx = (
                                    r"{\fs72\fad(35,110)\fscx110\fscy110"
                                    r"\t(0,170,\fscx100\fscy100)}"
                                    if _is_history_en_194_31
                                    else
                                    r"{\fad(35,110)\fscx110\fscy110\t(0,170,\fscx100\fscy100)}"
                                )
                                _fx_kind_194_74 = "impact-pop"
                            elif any(k in _semantic_text_194_74 for k in [
                                "crazier", "wait", "who was", "in other words",
                                "but the recorder", "그런데", "잠깐", "대체", "누구"
                            ]):
                                _fx = (
                                    r"{\fs72\fad(60,120)\fscx106\fscy106"
                                    r"\t(0,220,\fscx100\fscy100)}"
                                    if _is_history_en_194_31
                                    else
                                    r"{\fad(60,120)\fscx106\fscy106\t(0,220,\fscx100\fscy100)}"
                                )
                                _fx_kind_194_74 = "comedy-pop"
                            elif any(k in _semantic_text_194_74 for k in [
                                "historian", "annals", "taejong", "yi bang-won",
                                "사관", "실록", "태종", "세종"
                            ]):
                                _fx = (
                                    r"{\fs72\fad(180,180)}"
                                    if _is_history_en_194_31
                                    else r"{\fad(180,180)}"
                                )
                                _fx_kind_194_74 = "history-fade"

                        print("[Sprint194-74 History Subtitle FX]", {
                            "scene": _scene_no_194_74,
                            "native_audio": _is_native_audio_scene_194_74,
                            "role": _role,
                            "auto_fx": _fx_kind_194_74,
                        }, flush=True)
                        if _fx_kind_194_74 in {"ting-hook", "ting-auto-emphasis"}:
                            print("[Sprint194-75FB History Ting Applied]", {
                                "scene": _scene_no_194_74,
                                "role": _role,
                                "ting_kind": _fx_kind_194_74,
                                "scope": "hook+up-to-two-semantic-emphasis-scenes",
                            }, flush=True)
                        if _fx_kind_194_74 in {"ting-hook", "ting-record-command"}:
                            print("[Sprint194-74B History Command Emphasis]", {
                                "scene": _scene_no_194_74,
                                "color": "warm-highlight-to-gold",
                                "subtitle_fx": "ting-bounce-72-132-94-106-100",
                                "sfx_policy": "semantic-impact+ping-sync",
                            }, flush=True)

                        # Sprint194-17: 핵심 단어만 겨자/금색. [수동강조]가 있으면 그것을 최우선 사용합니다.
                        # ASS 색상은 BGR 순서: #D4A72C -> &H002CA7D4&
                        def _esc_ass_194_17(v):
                            return str(v or "").replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}").replace("\n", r"\N")
                        _gold_open = r"{\c&H002CA7D4&}"
                        _gold_close = r"{\c&H00FFFFFF&}"
                        _manual = re.search(r"\[([^\[\]]+)\]", _sub)
                        if _manual:
                            _plain = _sub.replace("[" + _manual.group(1) + "]", "__HIGHLIGHT__", 1)
                            _emphasis_color_194_65 = "&H001C9FFF&" if _i == 0 else "&H002CA7D4&"
                            _is_final_subscribe_194_73 = bool(
                                _is_history_en_194_31
                                and _role == "ending"
                                and _i == len(_durations) - 1
                                and re.search(r"subscribe", _manual.group(1), flags=re.I)
                            )
                            _manual_size_194_73 = (
                                max(int(_history_emphasis_size_194_48), 90)
                                if _is_final_subscribe_194_73
                                else int(_history_emphasis_size_194_48)
                            )
                            _manual_color_194_73 = (
                                "&H001C9FFF&" if _is_final_subscribe_194_73 else _emphasis_color_194_65
                            )
                            _manual_fx = rf"{{\fn{_history_emphasis_font_194_48}\fs{_manual_size_194_73}\b1\c{_manual_color_194_73}\bord5\shad0}}"
                            _esc = _esc_ass_194_17(_plain).replace("__HIGHLIGHT__", _manual_fx + _esc_ass_194_17(_manual.group(1)) + r"{\r" + _style + "}", 1)
                            _emphasis_verify_194_38.append({"scene": _i+1, "keyword": _manual.group(1), "source": "manual", "style": _style})
                        else:
                            _esc = _esc_ass_194_17(_sub)
                            # Sprint194-58: selective semantic emphasis, topic-independent.
                            # Strong phrases only; connective scenes stay white. Manual [brackets] still win.
                            _picked_kw = ""
                            _clean_kw_text = re.sub(r"[\n]+", " ", _sub).strip()
                            _clean_kw_text = re.sub(r"\s{2,}", " ", _clean_kw_text)
                            if _is_history_en_194_31:
                                _patterns58 = [
                                    r"\b(?:do not|never|must not)\s+[^,.!?]{2,24}",
                                    r"\b(?:King|Queen|Emperor|General|Prince|Princess)\s+[A-Z][A-Za-z-]+(?:\s+[A-Z][A-Za-z-]+)?\b",
                                    r"\b(?:banished|executed|assassinated|abdicated|fell|defeated|survived|recorded)\b",
                                ]
                            else:
                                _patterns58 = [
                                    r"(?:말에서\s*)?떨어졌다",
                                    r"(?:사관(?:에게|이)?\s*)?(?:알게\s*)?하지\s*말라",
                                    r"사관에게\s*알리지\s*말라",
                                    r"숨기라고\s*한\s*것도",
                                    r"(?:왕|임금|세자|왕비|장군|신하|사관)(?:이|가|은|는|에게|을|를)?",
                                    r"(?:낙마|유배|즉위|폐위|반란|처형|암살)",
                                    r"(?:구독|좋아요)",
                                ]
                            for _pat58 in _patterns58:
                                _m58 = re.search(_pat58, _clean_kw_text, flags=re.IGNORECASE if _is_history_en_194_31 else 0)
                                if _m58:
                                    _picked_kw = _m58.group(0).strip(" ,.!?…~:;")
                                    break
                            # Avoid weak one-word repeats such as generic '사관'/'기록' unless the whole caption is that concept.
                            if _picked_kw and len(_picked_kw) < 2:
                                _picked_kw = ""
                            if _picked_kw:
                                print("[Sprint194-58 History Semantic Emphasis] PICK", {"scene": _i+1, "keyword": _picked_kw, "role": _role, "subtitle": _sub}, flush=True)
                            else:
                                print("[Sprint194-58 History Semantic Emphasis] SKIP", {"scene": _i+1, "role": _role, "subtitle": _sub}, flush=True)
                            if _picked_kw:
                                _emphasis_color_194_65 = "&H001C9FFF&" if _i == 0 else "&H002CA7D4&"
                                _esc = _esc.replace(_esc_ass_194_17(_picked_kw), rf"{{\fn{_history_emphasis_font_194_48}\fs{_history_emphasis_size_194_48}\b1\c{_emphasis_color_194_65}\bord5\shad0}}" + _esc_ass_194_17(_picked_kw) + r"{\r" + _style + "}", 1)
                                _emphasis_verify_194_38.append({"scene": _i+1, "keyword": _picked_kw, "source": "auto", "style": _style})
                        # Sprint194-64: 50% black background sized to the current 1/2-line caption.
                        _line_count64 = max(1, min(2, len(str(_sub).split("\n"))))
                        _plain_lines64 = [re.sub(r"\[[^\]]+\]", lambda m: m.group(0)[1:-1], x) for x in str(_sub).split("\n")]
                        _max_chars64 = max([len(x.strip()) for x in _plain_lines64] or [1])
                        # Sprint194-73: tighter caption background.
                        # Previous box padding felt oversized on mobile, especially for short English captions.
                        _char_px_194_73 = 36 if _is_history_en_194_31 else 46
                        # Sprint194-75I: cross-platform Shorts safe area.
                        # Keep captions inside x=140..940 (800px max) and raise them
                        # above bottom-side platform controls. Long English wraps first.
                        _box_w64 = min(
                            800,
                            max(
                                300 if _is_history_en_194_31 else 360,
                                int(_max_chars64 * _char_px_194_73 + 72),
                            ),
                        )
                        _box_h64 = (
                            118 if _line_count64 == 1 else 214
                        ) if _is_history_en_194_31 else (
                            132 if _line_count64 == 1 else 238
                        )
                        _subtitle_boxes_194_64.append({
                            "scene": _i + 1, "start": round(_t, 3), "end": round(_t + _d, 3),
                            "x": max(140, int((1080 - _box_w64) / 2)), "y": int(1250 - (_box_h64 / 2)),
                            "w": _box_w64, "h": _box_h64, "lines": _line_count64,
                        })
                        _ass_lines.append(f"Dialogue: 0,{_ass_time_194_9(_t)},{_ass_time_194_9(_t+_d)},{_style},,0,0,0,,{_fx}{_esc}")
                    _t += _d
                _ass.write_text("\n".join(_ass_lines) + "\n", encoding="utf-8")
                print("[Sprint194-38 History Emphasis Render Verify] READY", {"count": len(_emphasis_verify_194_38), "items": _emphasis_verify_194_38, "ass_path": str(_ass), "ass_has_gold": any("2CA7D4" in x for x in _ass_lines)}, flush=True)

                # Sprint194-16: 역할 기반 SFX. 외부 파일 의존 없이 FFmpeg로 짧은 효과음을 생성합니다.
                # TTS/장면 타임라인은 변경하지 않고 타임라인 위에만 얹습니다.
                _sfx_dir = _history_root / "sfx"
                _sfx_dir.mkdir(parents=True, exist_ok=True)
                # Sprint194-67: verified real recorded SFX for horse/fall.
                _real_sfx_root_194_67 = Path("assets") / "history_sfx"
                _real_sfx_194_67 = {
                    "hoof": _real_sfx_root_194_67 / "horse_gallop.mp3",
                    "fall": _real_sfx_root_194_67 / "impact_thud.mp3",
                }
                print("[Sprint194-67 History Real SFX Assets] READY", {
                    k: {"path": str(v), "exists": v.is_file(), "bytes": v.stat().st_size if v.is_file() else 0}
                    for k, v in _real_sfx_194_67.items()
                }, flush=True)
                _sfx_specs = {
                    "impact": ("anoisesrc=color=white:duration=0.18:amplitude=0.9,lowpass=f=260,afade=t=out:st=0.05:d=0.13", 0.95),
                    "fall": ("sine=frequency=72:duration=0.34,volume=0.9,afade=t=out:st=0.08:d=0.26", 1.00),
                    "hoof": ("anoisesrc=color=brown:duration=1.05:amplitude=0.85,highpass=f=90,lowpass=f=1200,tremolo=f=4.2:d=0.92", 0.95),
                    "eat": ("anoisesrc=color=brown:duration=0.24:amplitude=0.58,highpass=f=180,lowpass=f=1800", 0.42),
                    "paper": ("anoisesrc=color=pink:duration=0.42:amplitude=0.65,highpass=f=900,lowpass=f=5200", 0.52),
                    "brush": ("anoisesrc=color=pink:duration=0.58:amplitude=0.68,highpass=f=1100,lowpass=f=6000,tremolo=f=9:d=0.75", 0.55),
                    "wave": ("anoisesrc=color=pink:duration=0.70:amplitude=0.45,lowpass=f=1600", 0.30),
                    "ending": ("sine=frequency=880:duration=0.18,afade=t=out:st=0.06:d=0.12", 0.42),
                }
                def _sfx_kind_194_17(idx, text, role):
                    t = str(text or "")
                    tl = t.lower()
                    if role == "ending" or "subscribe" in tl or "구독" in t:
                        return "ending"

                    # Actual-accident thud remains Korean-source-specific here.
                    # Scene 1 native Gemini video already carries its real fall/hoof audio.
                    _actual_fall_tokens_68 = [
                        "말에서 떨어졌다", "말에서 떨어졌", "말에서 굴러",
                        "말에서 낙마", "바닥에 떨어", "땅에 떨어",
                        "추락했다", "추락했", "쿵 하고", "쿵!", "쿵 소리"
                    ]
                    if any(k in t for k in _actual_fall_tokens_68):
                        return "fall"

                    # Sprint194-74: bilingual semantic SFX for image/silent scenes.
                    if any(k in tl for k in [
                        "rode a horse", "riding", "gallop", "horseback", "horse hooves"
                    ]) or any(k in t for k in ["말을 타", "말 타고", "말을 달", "기마", "말발굽"]):
                        return "hoof"

                    if any(k in tl for k in [
                        "royal recorder", "recorder did", "record this",
                        "writing", "wrote it", "writing things down"
                    ]) or any(k in t for k in ["붓", "써 내려", "적어", "기록하", "사관이 기록"]):
                        return "brush"

                    if any(k in tl for k in [
                        "annals", "recorded", "historian", "historians",
                        "royal records", "report", "book", "document",
                        "their job was to record", "taejong", "yi bang-won"
                    ]) or any(k in t for k in ["실록", "보고서", "지도", "장부", "기록"]):
                        return "paper"

                    if role == "impact" or any(k in tl for k in [
                        "urgent order", "very important order", "don't let",
                        "do not let", "don't record", "do not record",
                        "recorder know", "royal recorder", "record this",
                        "forbidden", "must not", "secret", "hide this",
                        "never", "cover-up", "crazier", "wait a second",
                        "hide it", "iron-fisted ruler"
                    ]) or any(k in t for k in ["싫", "거절", "안 먹", "마다", "단호"]):
                        return "impact"

                    if any(k in tl for k in ["eat", "meat", "food", "chew"]) or any(k in t for k in ["먹", "뜯", "고기", "콩", "먹이"]):
                        return "eat"

                    if any(k in tl for k in ["boat", "sea", "island", "shore", "ocean"]) or any(k in t for k in ["배를 타", "바다", "섬으로", "육지로"]):
                        return "wave"

                    return ""
                _sfx_events = []
                _fx_plan_194_17 = []
                for _ev, _role in zip(_timeline, _scene_roles_194_18):
                    _idx = int(_ev.get("scene") or 0)
                    _txt = _scene_texts[_idx-1] if 0 < _idx <= len(_scene_texts) else ""

                    # Sprint194-69: Gemini/native video already has its own sound.
                    # Never stack automatic SFX on top of a scene that has native audio.
                    if _scene_native_audio_194_69.get(_idx, False):
                        _fx_plan_194_17.append({
                            "scene": _idx, "role": _role,
                            "sfx": "native-audio",
                        })
                        print("[Sprint194-69 History Auto SFX] SKIP_NATIVE_AUDIO", {
                            "scene": _idx, "role": _role,
                        }, flush=True)
                        continue

                    _kind = _sfx_kind_194_17(_idx, _txt, _role)
                    _scene_sfx_194_65 = []
                    if _idx == 1 and _kind == "fall":
                        _scene_sfx_194_65 = [("hoof", 0), ("fall", 780)]
                    elif _kind:
                        _scene_sfx_194_65 = [(_kind, 0)]
                    _fx_plan_194_17.append({
                        "scene": _idx, "role": _role,
                        "sfx": "+".join(x[0] for x in _scene_sfx_194_65) or "none",
                        "policy": "image-or-silent-only",
                        "semantic_text": str(_txt or "")[:90],
                    })
                    for _kind65, _offset65 in _scene_sfx_194_65:
                        if _kind65 not in _sfx_specs:
                            continue
                        _real_asset_67 = _real_sfx_194_67.get(_kind65)
                        if _real_asset_67 is not None and _real_asset_67.is_file():
                            _sfx = _real_asset_67
                            print("[Sprint194-67 History Real SFX Pick]", {
                                "scene": _idx, "kind": _kind65, "path": str(_sfx),
                                "bytes": _sfx.stat().st_size, "source": "real-recording",
                            }, flush=True)
                        else:
                            _lavfi, _vol = _sfx_specs[_kind65]
                            _sfx = _sfx_dir / f"{_kind65}_194_67_fallback.wav"
                            subprocess.run(["ffmpeg","-y","-f","lavfi","-i",_lavfi,"-af",f"volume={_vol},aresample=48000","-ac","2",str(_sfx)], capture_output=True, check=False)
                        if _sfx.is_file() and _sfx.stat().st_size > 1024:
                            _delay65 = int(round(float(_ev["start"]) * 1000.0)) + int(_offset65)
                            _sfx_events.append((_sfx, _delay65, _kind65))
                print("[Sprint194-75 History Ting SFX Sync] READY", {"policy": "key-command-event-start", "timeline_locked": True}, flush=True)
                print("[Sprint194-38 History SFX Render Verify] READY", {"count": len(_sfx_events), "events": [{"file": str(a), "delay_ms": b, "kind": c} for a,b,c in _sfx_events]}, flush=True)
                print("[Sprint194-68 History Audible SFX] READY", {
                    "count": len(_sfx_events),
                    "scene1_dual_fx": any(c == "hoof" for a,b,c in _sfx_events) and any(c == "fall" for a,b,c in _sfx_events),
                    "source_volume_profile": "post-master-audible-194-66",
                }, flush=True)
                print("[Sprint194-65 History Hook Color] READY", {
                    "scene1_body": "bright-yellow",
                    "scene1_emphasis": "orange",
                    "other_scene_emphasis": "existing-gold",
                }, flush=True)

                _final_name_194_20 = f"{project_id}_history_en_final.mp4" if _history_lang_tag_194_20 == "en" else f"{project_id}_final.mp4"
                _final = Path("exports/videos") / _final_name_194_20
                _final.parent.mkdir(parents=True, exist_ok=True)
                _inputs = ["-i", str(_silent_video), "-i", str(_full_voice)]
                _filter_parts = []
                # Sprint194-34: History mobile voice presence master.
                # Korean narration needed more phone-speaker intelligibility even after the -14 LUFS master.
                # Keep English on the proven 194-29 balance; give Korean a tighter, more present voice chain
                # and slightly lower bed/SFX so the narration stays clearly in front. Shopping is untouched.
                _is_ko_audio_194_34 = str(_history_lang_tag_194_20 or "").strip().lower() != "en"
                # Sprint194-39: BGM slider must reach the history renderer unchanged.
                # 20% in One Click now means FFmpeg volume=0.20 instead of the old hard-coded 0.09 (KO) / 0.14 (EN).
                try:
                    _bgm_ui_percent_194_39 = max(0, min(100, int(bgm_volume_percent if bgm_volume_percent is not None else 10)))
                except Exception:
                    _bgm_ui_percent_194_39 = 10
                _bgm_gain_194_39 = float(_bgm_ui_percent_194_39) / 100.0
                if _is_ko_audio_194_34:
                    _filter_parts.append("[1:a]highpass=f=95,lowpass=f=12500,equalizer=f=2800:t=q:w=1.1:g=2.5,acompressor=threshold=-20dB:ratio=3:attack=8:release=90:makeup=3,volume=1.18[voice]")
                    _sfx_gain_194_34 = 1.10
                    _final_lufs_194_34 = -13
                    _final_lra_194_34 = 8
                else:
                    _filter_parts.append("[1:a]volume=1.20[voice]")
                    _sfx_gain_194_34 = 1.10
                    _final_lufs_194_34 = -14
                    _final_lra_194_34 = 11
                _bgm_gain_194_34 = _bgm_gain_194_39
                print("[Sprint194-39 History BGM UI Volume] READY", {
                    "ui_percent": _bgm_ui_percent_194_39,
                    "ffmpeg_gain": round(_bgm_gain_194_39, 4),
                    "mapping": "linear-percent",
                    "legacy_fixed_gain_removed": True,
                    "history_only": True,
                }, flush=True)
                # Sprint194-66: master narration+BGM first, then add SFX.
                # Previous path sent SFX through loudnorm with the whole program mix,
                # which could flatten short transients until they were effectively inaudible.
                _base_audio_inputs_66 = ["[voice]"]
                _next_input = 2
                if bgm_audio_path and Path(str(bgm_audio_path)).is_file():
                    _inputs += ["-stream_loop", "-1", "-i", str(bgm_audio_path)]
                    _filter_parts.append(f"[{_next_input}:a]volume={_bgm_gain_194_34}[bgm]")
                    _base_audio_inputs_66.append("[bgm]")
                    _next_input += 1
                if len(_base_audio_inputs_66) > 1:
                    _filter_parts.append("".join(_base_audio_inputs_66) + f"amix=inputs={len(_base_audio_inputs_66)}:duration=first:dropout_transition=0:normalize=0[baseraw66]")
                else:
                    _filter_parts.append("[voice]anull[baseraw66]")
                _filter_parts.append(f"[baseraw66]loudnorm=I={_final_lufs_194_34}:TP=-2:LRA={_final_lra_194_34}[base66]")

                _post_master_inputs_66 = ["[base66]"]

                # Sprint194-69: preserve original audio from native MP4 scenes.
                # It is trimmed to the exact TTS scene slot and delayed to the same scene start.
                # Gain is kept below narration but above the 20% BGM bed.
                _native_audio_gain_194_69 = 0.90
                for _jna69, (_na_path69, _na_delay69, _na_dur69, _na_scene69) in enumerate(_native_audio_events_194_69):
                    _inputs += ["-i", str(_na_path69)]
                    _ntag69 = f"native69a_{_jna69}"
                    _raw_audio_take_70b = max(
                        0.15,
                        float(_na_dur69) * _requested_video_speed_194_70b
                    )
                    _filter_parts.append(
                        f"[{_next_input}:a]"
                        f"atrim=start=0:duration={_raw_audio_take_70b:.3f},"
                        f"asetpts=PTS-STARTPTS,"
                        f"atempo={_requested_video_speed_194_70b:.6f},"
                        f"apad=pad_dur={float(_na_dur69):.3f},"
                        f"atrim=duration={float(_na_dur69):.3f},"
                        f"loudnorm=I=-11:TP=-2:LRA=7,"
                        f"volume={_native_audio_gain_194_69},"
                        f"adelay=delays={int(_na_delay69)}:all=1[{_ntag69}]"
                    )
                    _post_master_inputs_66.append(f"[{_ntag69}]")
                    _next_input += 1
                    print("[Sprint194-69A History Original Audio Mix Scene]", {
                        "scene": _na_scene69,
                        "source": str(_na_path69),
                        "slot_seconds": round(_na_dur69, 3),
                        "delay_ms": _na_delay69,
                        "normalized_lufs": -11,
                        "playback_speed": _requested_video_speed_194_70b,
                        "gain": _native_audio_gain_194_69,
                    }, flush=True)

                print("[Sprint194-69A History Original Audio Mix] READY", {
                    "count": len(_native_audio_events_194_69),
                    "scenes": [x[3] for x in _native_audio_events_194_69],
                    "gain": _native_audio_gain_194_69,
                    "normalized_lufs": -11,
                    "source": "original-scene-mp4",
                    "timeline_locked": True,
                }, flush=True)

                # Automatic SFX below are now image/silent-scene only.
                for _j, (_sfx, _delay, _role) in enumerate(_sfx_events):
                    _inputs += ["-i", str(_sfx)]
                    _tag = f"sfx66_{_j}"
                    # Sprint194-68: normalize each SFX independently.
                    # The horse recording has a quiet lead-in, so use its audible section.
                    if _role == "hoof":
                        _sfx_start_68 = 1.80
                        _sfx_trim_68 = 1.65
                        _sfx_target_68 = -10
                    elif _role == "fall":
                        _sfx_start_68 = 0.00
                        _sfx_trim_68 = 0.95
                        _sfx_target_68 = -8
                    else:
                        _sfx_start_68 = 0.00
                        _sfx_trim_68 = 0.90
                        _sfx_target_68 = -12

                    _filter_parts.append(
                        f"[{_next_input}:a]"
                        f"atrim=start={_sfx_start_68}:duration={_sfx_trim_68},"
                        f"asetpts=PTS-STARTPTS,"
                        f"loudnorm=I={_sfx_target_68}:TP=-2:LRA=7,"
                        f"volume={_sfx_gain_194_34},"
                        f"adelay=delays={int(_delay)}:all=1,"
                        f"afade=t=out:st={max(0.05, _sfx_trim_68-0.18)}:d=0.18[{_tag}]"
                    )
                    _post_master_inputs_66.append(f"[{_tag}]")
                    _next_input += 1

                if len(_post_master_inputs_66) > 1:
                    _filter_parts.append(
                        "".join(_post_master_inputs_66)
                        + f"amix=inputs={len(_post_master_inputs_66)}:duration=first:"
                          "dropout_transition=0:normalize=0,"
                          "alimiter=limit=0.92:attack=5:release=50[aout]"
                    )
                else:
                    _filter_parts.append("[base66]anull[aout]")
                _audio_map = "[aout]"
                print("[Sprint194-69 History Audio Policy Mix] READY", {
                    "base_mastered_before_sfx": True,
                    "sfx_after_loudnorm": True,
                    "sfx_events": len(_sfx_events),
                    "sfx_gain": _sfx_gain_194_34,
                    "hoof_source_start_sec": 1.80,
                    "hoof_duration_sec": 1.65,
                    "hoof_target_lufs": -10,
                    "fall_target_lufs": -8,
                    "fall_semantic_mode": "actual-accident-only",
                    "limiter": 0.92,
                }, flush=True)
                print("[Sprint194-34 History Mobile Voice Presence] READY", {
                    "language": "ko" if _is_ko_audio_194_34 else "en",
                    "ko_voice_presence_eq_db": 2.5 if _is_ko_audio_194_34 else 0.0,
                    "ko_compressor": bool(_is_ko_audio_194_34),
                    "bgm_gain": _bgm_gain_194_34,
                    "sfx_gain": _sfx_gain_194_34,
                    "final_lufs": _final_lufs_194_34,
                    "true_peak": -1,
                    "amix_normalize": False,
                }, flush=True)
                print("[Sprint194-19 History Presentation FX] READY", {
                    "roles": _scene_roles_194_18, "sfx_events": len(_sfx_events),
                    "fx_plan": _fx_plan_194_17,
                    "subtitle_fx": "194-75K-scene1-hook+role-based-two-body-ting+shorts-safe-caption+subscribe-pop",
                    "fonts": {"body": _history_body_font_194_48, "emphasis": _history_emphasis_font_194_48},
                    "impact_motion": "semantic-impact-wide-base-0.28s-zoom-punch+restrained-shake",
                    "framing": "wider-default-1100px; emphasis-only-1150~1165px",
                    "emphasis_subtitle": "topic-independent+manual-bracket+gold-pop",
                    "timeline_locked": True, "voice_seconds": round(_voice_duration, 3),
                    "mobile_audio_master": {"profile": "ko-presence" if _is_ko_audio_194_34 else "en-standard", "bgm_gain": _bgm_gain_194_34, "sfx_gain": _sfx_gain_194_34, "lufs": _final_lufs_194_34, "true_peak": -1, "amix_normalize": False},
                }, flush=True)

                _ass_filter_194_64 = "ass=" + str(_ass).replace("\\", "/").replace(":", r"\:")
                if any(_font_dir_194_48d.iterdir()):
                    _ass_filter_194_64 += ":fontsdir=" + str(_font_dir_194_48d).replace("\\", "/")
                _box_filters_194_64 = []
                for _b64 in _subtitle_boxes_194_64:
                    _enable64 = f"between(t\\,{_b64['start']:.3f}\\,{_b64['end']:.3f})"
                    _box_filters_194_64.append(
                        f"drawbox=x={_b64['x']}:y={_b64['y']}:w={_b64['w']}:h={_b64['h']}:"
                        f"color=black@0.42:t=fill:enable='{_enable64}'"
                    )
                _vf_ass = ",".join(_box_filters_194_64 + [_ass_filter_194_64])
                print("[Sprint194-64 History Subtitle Box] READY", {
                    "opacity_percent": 42, "mode": "compact-safe-caption-194-75I",
                    "box_count": len(_subtitle_boxes_194_64), "scene1_mobile_wrap": True,
                    "safe_area": {"left": 140, "right": 140, "max_box_width": 800, "caption_center_y": 1250, "ass_margin_v": 620},
                }, flush=True)
                _cmd = ["ffmpeg", "-y"] + _inputs
                if _filter_parts:
                    _cmd += ["-filter_complex", ";".join(_filter_parts)]
                _cmd += ["-vf", _vf_ass, "-map", "0:v:0", "-map", _audio_map,
                         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "192k",
                         "-t", f"{_voice_duration:.3f}", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(_final)]
                _r = subprocess.run(_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
                if _r.returncode != 0 or not _final.is_file() or _final.stat().st_size <= 1024:
                    raise RuntimeError("history_final_render_failed: " + str((_r.stderr or _r.stdout or "")[-1600:]))
                print("[Sprint194-38 History Final Burn Verify] READY", {"final": str(_final), "bytes": _final.stat().st_size if _final.is_file() else 0, "ass": str(_ass), "emphasis_count": len(_emphasis_verify_194_38), "sfx_count": len(_sfx_events), "ffmpeg_rc": _r.returncode}, flush=True)

                _final_d = _probe_dur_194_9(_final)
                print("[Sprint194-11 History Dedicated Renderer] READY", {
                    "scene_count": _scene_count,
                    "tts_scene_input_count": len([x for x in _scene_texts if x]),
                    "full_voice_path": _full_voice,
                    "full_voice_seconds": round(_voice_duration, 3),
                    "final_video_seconds": round(_final_d, 3),
                    "video_covers_voice": bool(_final_d + 0.20 >= _voice_duration),
                    "subtitles": len([x for x in _subs if x]),
                    "bgm": bool(bgm_audio_path and Path(str(bgm_audio_path)).is_file()),
                    "bgm_volume_percent": _bgm_ui_percent_194_39,
                    "bgm_ffmpeg_gain": round(_bgm_gain_194_39, 4),
                    "shopping_video_pipeline_bypassed": True,
                    "single_voice_track": True,
                    "intro_used": False,
                    "timeline_source": "scene_tts_plus_native_video_duration_194_70",
                    "language": _history_language_194_20,
                    "lang_tag": _history_lang_tag_194_20,
                }, flush=True)
                if _final_d + 0.20 < _voice_duration:
                    raise RuntimeError(f"history_final_too_short: video={_final_d:.3f} voice={_voice_duration:.3f}")

                outputs = {
                    "workflow_version": self.WORKFLOW_VERSION,
                    "execution_mode": "history_dedicated_renderer",
                    "final_video_path": str(_final),
                    "history_scene_count": _scene_count,
                    "history_voice_duration": _voice_duration,
                    "history_final_duration": _final_d,
                    "shopping_video_pipeline_bypassed": True,
                }
                return {
                    "ok": True,
                    "job_id": "",
                    "state": {},
                    "outputs": outputs,
                    "summary": "역사쿠키 전용 렌더러로 영상 제작 완료",
                    "final_video_path": str(_final),
                }
            except Exception as _history_194_9_exc:
                print("[Sprint194-11 History Dedicated Renderer] ERROR", type(_history_194_9_exc).__name__, str(_history_194_9_exc), flush=True)
                return {
                    "ok": False,
                    "job_id": "",
                    "state": {},
                    "outputs": {
                        "workflow_version": self.WORKFLOW_VERSION,
                        "execution_mode": "history_dedicated_renderer",
                        "error": f"{type(_history_194_9_exc).__name__}: {_history_194_9_exc}",
                        "shopping_video_pipeline_bypassed": True,
                    },
                    "summary": "역사쿠키 전용 렌더러 제작 실패",
                    "final_video_path": "",
                }

        generation = {
            "status": "manual_uploaded_clips_reused" if supplied else "manual_clips_missing",
            "generated_files": generated_files,
            "errors": [],
        }
        if not generated_files:
            return {
                "ok": False,
                "outputs": {
                    "workflow_version": self.WORKFLOW_VERSION,
                    "gemini_video_generation": generation,
                },
                "summary": "수동으로 업로드한 Gemini 영상 클립이 없습니다.",
            }

        # Sprint194-8: 역사 영상은 합쳐진 전체 나레이션 1트랙을 사용하고,
        # 장면별 음성 경로는 VideoPipeline에 넘기지 않습니다.
        _effective_clip_voice_paths_194_8 = [] if _history_mode_194_8 else list(clip_voice_paths or [])
        _effective_auto_sync_194_8 = False if _history_mode_194_8 else True
        _effective_playback_speed_194_8 = 1.0 if _history_mode_194_8 else float(playback_speed or 1.5)
        if _history_mode_194_8:
            print("[Sprint194-8 History Runtime Lock]", {
                "requested_playback_speed": float(playback_speed or 1.5),
                "pipeline_playback_speed": _effective_playback_speed_194_8,
                "voice_mode": "scene_tts_trim_concat_full_track",
                "scene_voice_gap_removed": True,
                "full_voice_ready": bool(_history_full_voice_194_8),
                "scene_count": len(_history_scene_durations_194_8),
            }, flush=True)

        content_pack = {
            "project_id": project_id,
            "product_name": product_name,
            "title": product_name,
            "hook": hook,
            "hook_text": hook,
            "locked_script": script,
            "script": narration_text,
            "short_script": narration_text,
            "narration_text": narration_text,
            "cta": cta,
            "cta_text": "",
            "cta_product_logo_text": str(cta_product_logo_text or "").strip(),
            "voice_audio_path": str(resolved_voice_audio_path or ""),
            "intro_voice_path": str(intro_voice_path or ""),
            "clip_voice_paths": list(_effective_clip_voice_paths_194_8),
            "scene_tts_generation": list(scene_tts_generation or []),
            "auto_sync_narration": bool(_effective_auto_sync_194_8),
            "bgm_audio_path": str(bgm_audio_path or ""),
            "voice_name": str(voice_name or "지안"),
            "voice_id": str(voice_id or ""),
            "tts_volume_percent": int(tts_volume_percent or 100),
            "tts_speech_speed": float(tts_speech_speed or 1.0),
            "clip_subtitles": list(clip_subtitles or []),
            "clip_subtitle_effects": list(clip_subtitle_effects or []),
            "clip_sfx": list(clip_sfx or []),
            # 0.0 means AUTO. Do not convert it back to 1.5.
            "clip_playback_speeds": [
                float(item if item is not None else 0.0)
                for item in list(clip_playback_speeds or [])
            ],
            "trust_narration": trust_narration,
            "youtube_privacy_status": youtube_privacy_status,
            "upload_enabled": bool(upload_enabled),
            "gemini_clip_paths": generated_files,
            "tts_voice": str(voice_name or "지안"),
            "channel_type": str(channel_type or "shopping"),
            "playback_speed": float(_effective_playback_speed_194_8),
            "monthly_purchase_count": int(monthly_purchase_count or 0),
            "declared_review_count": int(declared_review_count or 0),
            "review_count": int(declared_review_count or 0),
            "rating": float(rating or 0.0),
            "trust_card_duration": float(trust_card_duration or 3.4),
            "trust_inputs": {
                "monthly_purchase_count": int(monthly_purchase_count or 0),
                "declared_review_count": int(declared_review_count or 0),
                "rating": float(rating or 0.0),
            },
        }
        print(
            "[Sprint178-3 Exact Trust Input]",
            {
                "monthly_purchase_count": content_pack["monthly_purchase_count"],
                "declared_review_count": content_pack["declared_review_count"],
                "rating": content_pack["rating"],
                "cta_text": content_pack["cta_text"],
            },
            flush=True,
        )
        video_result = VideoPipeline().run(
            content_pack=content_pack,
            project=project,
            clip_paths=generated_files,
            render=True,
            apply_subtitles=True,
            apply_voice=True,
            apply_bgm=True,
            apply_effects=True,
            playback_speed=float(_effective_playback_speed_194_8),
        )
        final_path = str(video_result.get("output_path") or "")
        if _history_mode_194_8 and final_path and Path(final_path).is_file():
            try:
                _final_probe = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", final_path],
                    capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
                )
                _final_duration = float((_final_probe.stdout or "0").strip() or 0.0)
                _voice_probe = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(resolved_voice_audio_path or "")],
                    capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
                )
                _voice_duration = float((_voice_probe.stdout or "0").strip() or 0.0)
                print("[Sprint194-8 History Final Duration Check]", {
                    "final_video_seconds": round(_final_duration, 3),
                    "full_voice_seconds": round(_voice_duration, 3),
                    "video_covers_voice": bool(_final_duration + 0.20 >= _voice_duration),
                }, flush=True)
            except Exception as _duration_exc:
                print("[Sprint194-8 History Final Duration Check] ERROR", repr(_duration_exc), flush=True)
        reservation_result = {"ok": True, "status": "disabled", "count": 0, "items": []}
        reservation_config = dict(reservation_payload or {})
        if reservation_config.get("enabled") and final_path and Path(final_path).is_file():
            try:
                from datetime import datetime, timedelta
                base_time = datetime.fromisoformat(str(reservation_config.get("scheduled_at_local") or ""))
                interval = max(0, int(reservation_config.get("interval_minutes") or 0))
                metadata = ScheduledMetadataBuilder.build(
                    product_name=product_name, hook_text=hook, locked_script=script, cta_text=cta,
                    infock_url=str(reservation_config.get("infock_url") or ""),
                )
                metadata["youtube_privacy_status"] = youtube_privacy_status
                platform_metadata = dict(reservation_config.get("platform_metadata") or {})
                queue = ReservationQueue()
                created = []
                for index, platform in enumerate(list(reservation_config.get("platforms") or [])):
                    platform_key = str(platform)
                    platform_payload = dict(metadata)
                    platform_override = dict(platform_metadata.get(platform_key) or {})
                    platform_title = str(platform_override.get("title") or "").strip()
                    platform_description = str(platform_override.get("description") or "").strip()
                    if platform_title:
                        platform_payload["title"] = platform_title
                        platform_payload[f"{platform_key}_title"] = platform_title
                    if platform_description:
                        platform_payload["description"] = platform_description
                        platform_payload["caption"] = platform_description
                        platform_payload[f"{platform_key}_description"] = platform_description
                    platform_payload["platform"] = platform_key
                    created.append(queue.enqueue(
                        project_id=project_id, platform=platform_key,
                        scheduled_at=base_time + timedelta(minutes=interval * index),
                        video_path=final_path, payload=platform_payload,
                    ))
                reservation_result = {
                    "ok": True, "status": "scheduled", "count": len(created),
                    "items": created, "metadata": metadata,
                    "platform_metadata": platform_metadata,
                }
                print(
                    "[Sprint190-5 Reservation Platform Metadata] SCHEDULED:",
                    {"count": len(created), "platforms": list(reservation_config.get("platforms") or [])},
                    flush=True,
                )
            except Exception as exc:
                reservation_result = {"ok": False, "status": "schedule_failed", "count": 0, "items": [], "error": f"{type(exc).__name__}: {exc}"}
                print("[Sprint180-2 Reservation] ERROR:", reservation_result["error"], flush=True)
        outputs = {
            "workflow_version": self.WORKFLOW_VERSION,
            "execution_mode": "gemini_video_only",
            "image_generation": "SKIPPED",
            "vision_validation": "SKIPPED",
            "scene_planner": "SKIPPED",
            "gemini_video_generation": generation,
            "tts_generation": tts_generation,
            "video_pipeline": video_result,
            "final_video_path": final_path,
            "youtube_privacy_status": youtube_privacy_status,
            "upload_requested": bool(upload_enabled),
            "reservations": reservation_result,
        }
        print("[Sprint174-1 FINAL VIDEO]", final_path, flush=True)
        return {"ok": bool(video_result.get("ok")), "job_id": "", "state": {}, "outputs": outputs, "summary": "Gemini 영상 중심 쇼츠 제작 완료" if video_result.get("ok") else "최종 영상 제작 실패", "final_video_path": final_path}

    def run_project(
        self,
        project,
        sample_count=6,
        review_image_paths=None,
        review_text="",
        locked_script="",
        product_image_paths=None,
        product_image_path="",
        youtube_privacy_status="private",
        viral_video_sources=None,
        declared_review_count=0,
        review_checked_at="",
        rating=0,
        monthly_purchase_count=0,
        input_product_name="",
        stop_after_image_generation=False,
        gemini_video_mode=False,
        hook_text="",
        cta_text="",
        cta_product_logo_text="",
        voice_audio_path="",
        bgm_audio_path="",
        bgm_volume_percent=10,
        voice_name="지안",
        voice_id="",
        typecast_api_key="",
        tts_volume_percent=100,
        tts_speech_speed=1.0,
        clip_subtitles=None,
        clip_subtitle_effects=None,
        clip_sfx=None,
        clip_playback_speeds=None,
        clip_narrations=None,
        gemini_clip_count=4,
        upload_enabled=False,
        playback_speed=1.5,
        channel_type="shopping",
        reservation_payload=None,
    ):
        if gemini_video_mode:
            return self._run_gemini_video_scope(
                project=project,
                hook_text=hook_text or review_text,
                locked_script=locked_script,
                cta_text=cta_text,
                cta_product_logo_text=cta_product_logo_text,
                voice_audio_path=voice_audio_path,
                bgm_audio_path=bgm_audio_path,
                bgm_volume_percent=bgm_volume_percent,
                voice_name=voice_name,
                voice_id=voice_id,
                typecast_api_key=typecast_api_key,
                tts_volume_percent=tts_volume_percent,
                tts_speech_speed=tts_speech_speed,
                clip_subtitles=list(clip_subtitles or []),
                clip_subtitle_effects=list(clip_subtitle_effects or []),
                clip_sfx=list(clip_sfx or []),
                clip_playback_speeds=list(clip_playback_speeds or []),
                clip_narrations=list(clip_narrations or []),
                gemini_clip_count=gemini_clip_count,
                supplied_clip_paths=viral_video_sources,
                youtube_privacy_status=youtube_privacy_status,
                upload_enabled=upload_enabled,
                playback_speed=playback_speed,
                channel_type=channel_type,
                monthly_purchase_count=monthly_purchase_count,
                declared_review_count=declared_review_count,
                rating=rating,
                trust_card_duration=3.4,
                reservation_payload=reservation_payload,
            )
        print(
            "[Sprint147-5 WORKFLOW ENTRY]",
            {
                "stop_after_image_generation": bool(stop_after_image_generation),
                "locked_script_chars": len(str(locked_script or "").strip()),
                "product_image_count": len(list(product_image_paths or [])),
                "workflow_version": self.WORKFLOW_VERSION,
            },
            flush=True,
        )
        print(
            "[UTF8 TRACE run_project review_text ENTRY]",
            repr(review_text),
            flush=True,
        )

        # Sprint146-10: UI 인자 전달 실패나 DB 재조회가 있어도
        # 원클릭 확정 대본 프로젝트는 절대로 리뷰 대본 생성 경로로 떨어지지 않습니다.
        recovered_payload = {}
        for raw_candidate in (
            getattr(project, "data_json", None),
            getattr(project, "payload", None),
            getattr(project, "metadata_json", None),
        ):
            if isinstance(raw_candidate, dict):
                recovered_payload.update(raw_candidate)
            elif isinstance(raw_candidate, str) and raw_candidate.strip():
                try:
                    parsed_candidate = json.loads(raw_candidate)
                    if isinstance(parsed_candidate, dict):
                        recovered_payload.update(parsed_candidate)
                except Exception:
                    pass

        project_source = str(
            recovered_payload.get("source")
            or getattr(project, "source", "")
            or ""
        ).strip()
        locked_project = project_source in {
            "one_click_locked_script_scene_image_direct",
            "one_click_locked_script_full_production",
            "one_click_ai_image_review_147_1",
            "one_click_ai_image_review_147_3",
        }

        if not str(locked_script or "").strip():
            recovered_clip_narrations = recovered_payload.get("clip_narrations") or []
            if isinstance(recovered_clip_narrations, (list, tuple)):
                locked_script = " ".join(
                    str(item or "").strip()
                    for item in recovered_clip_narrations
                    if str(item or "").strip()
                ).strip()
            if not str(locked_script or "").strip():
                locked_script = str(
                    recovered_payload.get("locked_script")
                    or recovered_payload.get("approved_script")
                    or recovered_payload.get("script")
                    or ""
                ).strip()

        if not input_product_name:
            input_product_name = str(
                recovered_payload.get("product_name")
                or recovered_payload.get("title")
                or ""
            ).strip()
        if not declared_review_count:
            declared_review_count = int(
                recovered_payload.get("declared_review_count")
                or recovered_payload.get("review_count")
                or 0
            )
        if not monthly_purchase_count:
            monthly_purchase_count = int(
                recovered_payload.get("monthly_purchase_count")
                or 0
            )
        if not rating:
            rating = float(recovered_payload.get("rating") or 0)
        if not review_checked_at:
            review_checked_at = str(
                recovered_payload.get("review_checked_at") or ""
            ).strip()

        print(
            "[Sprint146-10 RUN ENTRY]",
            {
                "workflow_version": self.WORKFLOW_VERSION,
                "project_source": project_source,
                "locked_project": locked_project,
                "locked_script_chars": len(str(locked_script or "").strip()),
                "monthly_purchase_count": int(monthly_purchase_count or 0),
                "review_count": int(declared_review_count or 0),
                "rating": float(rating or 0),
                "review_checked_at": str(review_checked_at or ""),
            },
            flush=True,
        )

        if locked_project and not str(locked_script or "").strip():
            print(
                "[Sprint146-10 HARD BLOCK] LOCKED PROJECT WITHOUT SCRIPT - LEGACY GENERATOR NOT ALLOWED",
                flush=True,
            )
            return {
                "job_id": "",
                "state": {},
                "outputs": {
                    "workflow_version": self.WORKFLOW_VERSION,
                    "execution_mode": "locked_script_hard_block",
                    "error": "locked_script_missing",
                    "review_script_generator": "SKIPPED",
                },
                "summary": "확정 대본이 없어 실행을 중단했습니다. 리뷰 대본 자동 생성 경로는 실행하지 않았습니다.",
                "script_status": "BLOCKED_LOCKED_SCRIPT_MISSING",
            }

        # Sprint146-11: 잠금 대본 모드는 장면 이미지가 반드시 있어야 합니다.
        # 이미지가 없을 때도 기존 리뷰/대본 생성 경로로 폴백하지 않고 즉시 중단합니다.
        supplied_scene_images = [
            str(item).strip()
            for item in list(product_image_paths or [])
            if str(item).strip()
        ]
        if str(product_image_path or "").strip() and str(product_image_path).strip() not in supplied_scene_images:
            supplied_scene_images.insert(0, str(product_image_path).strip())

        reuse_image_motion_path = self._resolve_reuse_image_motion_path(
            getattr(project, "id", "")
        )

        if (
            str(locked_script or "").strip()
            and not supplied_scene_images
            and not reuse_image_motion_path
        ):
            print(
                "[Sprint146-11 HARD BLOCK] LOCKED SCRIPT WITHOUT SCENE IMAGES - LEGACY FALLBACK NOT ALLOWED",
                flush=True,
            )
            return {
                "job_id": "",
                "state": {},
                "outputs": {
                    "workflow_version": self.WORKFLOW_VERSION,
                    "execution_mode": "locked_script_hard_block",
                    "error": "locked_scene_images_missing",
                    "review_script_generator": "SKIPPED",
                    "script_closed_loop": "SKIPPED",
                    "medium_expander": "SKIPPED",
                },
                "summary": "확정 대본용 장면 이미지가 없어 실행을 중단했습니다. 기존 대본 생성 경로로는 전환하지 않았습니다.",
                "script_status": "BLOCKED_LOCKED_SCENE_IMAGES_MISSING",
            }

        """Sprint102-3: 동일 프로젝트의 동시 원클릭 실행을 한 번만 허용합니다."""
        project_key = str(getattr(project, "id", "") or id(project))

        with self._RUN_GUARD:
            if project_key in self._ACTIVE_PROJECT_KEYS:
                print(
                    "[Sprint102-3 Duplicate Guard] SKIPPED:",
                    project_key,
                    flush=True,
                )
                return {
                    "job_id": "",
                    "state": {},
                    "outputs": {
                        "workflow_version": self.WORKFLOW_VERSION,
                        "duplicate_execution_skipped": True,
                        "project_key": project_key,
                    },
                    "summary": "동일 프로젝트가 이미 실행 중이어서 중복 실행을 건너뛰었습니다.",
                    "duplicate_execution_skipped": True,
                }

            self._ACTIVE_PROJECT_KEYS.add(project_key)

        print(
            "[Sprint102-3 Duplicate Guard] ACQUIRED:",
            project_key,
            flush=True,
        )

        try:
            print(
                "[Sprint146-11 ROUTE DECISION]",
                "LOCKED_SCRIPT_FULL_PRODUCTION"
                if str(locked_script or "").strip()
                else "LEGACY_REVIEW_SCRIPT_PRODUCTION",
                flush=True,
            )
            return self._run_project_impl(
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
                rating=rating,
                monthly_purchase_count=monthly_purchase_count,
                input_product_name=input_product_name,
                stop_after_image_generation=stop_after_image_generation,
            )
        finally:
            with self._RUN_GUARD:
                self._ACTIVE_PROJECT_KEYS.discard(project_key)
            print(
                "[Sprint102-3 Duplicate Guard] RELEASED:",
                project_key,
                flush=True,
            )

    def _run_project_impl(
        self,
        project,
        sample_count=6,
        review_image_paths=None,
        review_text="",
        locked_script="",
        product_image_paths=None,
        product_image_path="",
        youtube_privacy_status="private",
        viral_video_sources=None,
        declared_review_count=0,
        review_checked_at="",
        rating=0,
        monthly_purchase_count=0,
        input_product_name="",
        stop_after_image_generation=False,
    ):
        review_image_paths = review_image_paths or []
        review_text = str(review_text or "").strip()
        locked_script = str(locked_script or "").strip()
        product_image_paths = product_image_paths or []
        reuse_image_motion_path = self._resolve_reuse_image_motion_path(
            getattr(project, "id", "")
        )
        youtube_privacy_status = (
            self._normalize_youtube_privacy_status(
                youtube_privacy_status
            )
        )
        viral_video_sources = [
            str(item).strip()
            for item in list(viral_video_sources or [])
            if str(item).strip()
        ][:10]
        # Sprint146-5B: 모든 실행 경로에서 script_status를 먼저 정의합니다.
        # locked_script 분기와 기존 리뷰 대본 분기 모두 아래 후속 파이프라인에서
        # 동일한 승인 상태를 안전하게 참조합니다.
        script_status = ""
        # Sprint146-12: 모든 실행 경로에서 장면 목록을 먼저 초기화합니다.
        # 잠금 대본 경로가 기존 Story/Scene Bridge 구간을 건너뛰어도
        # 후속 자막/영상 단계에서 UnboundLocalError가 발생하지 않습니다.
        planned_scenes = []
        # Sprint146-15: locked_script 경로가 레거시 Scene Image Planner 구간을
        # 건너뛰더라도 후속 fallback/director 단계에서 안전하게 참조되도록
        # scene_image_plan_result를 모든 실행 경로에서 먼저 초기화합니다.
        image_generation_only_requested = bool(stop_after_image_generation)
        print(
            "[Sprint147-7 IMAGE ROUTE] requested:",
            image_generation_only_requested,
            flush=True,
        )
        scene_image_plan_result = {
            "ok": False,
            "ready": False,
            "version": getattr(SceneImagePlanner, "VERSION", ""),
            "status": "not_run",
            "scene_count": 0,
            "scenes": [],
            "errors": [],
        }
        print(
            "[Sprint146-16 Scene Image Plan Safe] Initialized:",
            True,
            flush=True,
        )
        print(
            "[Sprint146-11 HARD ROUTER]",
            "LOCKED_SCRIPT" if locked_script else "LEGACY_REVIEW_SCRIPT",
            flush=True,
        )
        if locked_script:
            script_status = "APPROVED"
            locked_lines = [
                " ".join(line.split()).strip()
                for line in re.split(r"(?<=[.!?])\s+|\n+", locked_script)
                if " ".join(line.split()).strip()
            ]
            if not locked_lines:
                locked_lines = [locked_script]

            scene_subtitles = []
            for index, line in enumerate(locked_lines, start=1):
                if index == 1:
                    purpose = "hook"
                elif index == len(locked_lines):
                    purpose = "cta"
                elif index == 2:
                    purpose = "pain"
                elif index == 3:
                    purpose = "feature"
                elif index == 4:
                    purpose = "usage"
                else:
                    purpose = "proof"

                scene_subtitles.append(
                    {
                        "scene_id": f"scene_{index:02d}",
                        "order": index,
                        "purpose": purpose,
                        "subtitle": line,
                        "dialogue": line,
                        "source": "locked_user_script",
                    }
                )

            approved_script_text = locked_script
            approved_review_scripts = {
                "ok": True,
                "version": "locked-user-script-146-11",
                "status": "approved_script_locked",
                "product_name": str(
                    input_product_name
                    or getattr(project, "product_name", "")
                    or getattr(project, "title", "")
                    or "선택 상품"
                ).strip(),
                "review_count": int(declared_review_count or 0),
                "declared_review_count": int(declared_review_count or 0),
                "monthly_purchase_count": int(monthly_purchase_count or 0),
                "rating": float(rating or 0),
                "review_checked_at": str(review_checked_at or "").strip(),
                "trust_profile": {
                    "monthly_purchase_count": int(monthly_purchase_count or 0),
                    "review_count": int(declared_review_count or 0),
                    "rating": float(rating or 0),
                    "review_checked_at": str(review_checked_at or "").strip(),
                },
                "best_script": approved_script_text,
                "original_best_script": approved_script_text,
                "short_script": approved_script_text,
                "medium_script": approved_script_text,
                "long_script": approved_script_text,
                "best_script_type": "locked_user_script",
                "scene_subtitles": scene_subtitles,
                "scene_subtitle_count": len(scene_subtitles),
                "locked_user_script": True,
            }
            script_status = "APPROVED"
            approved_outputs = {
                "review_scripts": approved_review_scripts,
                "script_approval": {
                    "version": "locked-script-approval-146-11",
                    "status": "APPROVED",
                    "approved": True,
                    "best_script": approved_script_text,
                    "errors": [],
                },
            }
            print(
                "[Sprint146-5 Locked Script] APPROVED -> ImageMotion/Subtitle/Voice/Merge",
                flush=True,
            )
            print(
                "[Sprint146-5 Locked Script] Characters:",
                len(approved_script_text),
                flush=True,
            )
            print(
                "[Sprint146-11 LOCKED SCRIPT HARD BYPASS] Scene Subtitles:",
                len(scene_subtitles),
                flush=True,
            )
            print(
                "[Sprint146-11 LOCKED SCRIPT HARD BYPASS] ReviewScriptGenerator: SKIPPED",
                flush=True,
            )
            print(
                "[Sprint146-11 LOCKED SCRIPT HARD BYPASS] ScriptClosedLoop: SKIPPED",
                flush=True,
            )
            print(
                "[Sprint146-11 LOCKED SCRIPT HARD BYPASS] MediumExpander: SKIPPED",
                flush=True,
            )
            print(
                "[Sprint146-11 TRUST INPUT]",
                {
                    "monthly_purchase_count": int(monthly_purchase_count or 0),
                    "review_count": int(declared_review_count or 0),
                    "rating": float(rating or 0),
                    "review_checked_at": str(review_checked_at or "").strip(),
                },
                flush=True,
            )
        else:
            script_gate_result = self._run_sprint145_2_script_first_only(
                project=project,
                review_text=review_text,
                viral_video_sources=viral_video_sources,
                declared_review_count=declared_review_count,
                review_checked_at=review_checked_at,
                rating=rating,
                monthly_purchase_count=monthly_purchase_count,
                input_product_name=input_product_name,
            )
            script_status = str(script_gate_result.get("script_status") or "")
            approved_outputs = (
                script_gate_result.get("outputs")
                if isinstance(script_gate_result.get("outputs"), dict)
                else {}
            )
            if script_status != "APPROVED":
                print(
                    "[Sprint146-5 Full Pipeline Gate] BLOCKED:",
                    script_status or "UNKNOWN",
                    flush=True,
                )
                return script_gate_result
            approved_review_scripts = (
                approved_outputs.get("review_scripts")
                if isinstance(approved_outputs.get("review_scripts"), dict)
                else {}
            )
            approved_script_text = str(
                approved_review_scripts.get("best_script")
                or (approved_outputs.get("script_approval") or {}).get("best_script")
                or ""
            ).strip()
            print(
                "[Sprint146-5 Generated Script] APPROVED -> ImageMotion/Subtitle/Voice/Merge",
                flush=True,
            )
        print(
            "######## RUN_PROJECT SPRINT137-1 START ########",
            flush=True,
        )
        print(
            "[TRACE] workflow_version:",
            self.WORKFLOW_VERSION,
            flush=True,
        )
        print(
            "[TRACE] project:",
            project,
            flush=True,
        )
        print(
            "[TRACE] sample_count:",
            sample_count,
            flush=True,
        )
        print(
            "[Sprint89-1 YouTube] Privacy Status:",
            youtube_privacy_status,
            flush=True,
        )

        resolver = VideoPathResolver()
        project = resolver.resolve_project(project)

        # Sprint131-5: 매 실행은 새 상품 이미지와 새 텍스트 리뷰만 사용합니다.
        # Downloads/latest.mp4 및 이전 프로젝트 video_path 자동 연결을 금지합니다.
        auto_connected = {
            "ok": False,
            "status": "disabled_fresh_input_only",
            "message": "기존 영상 자동 연결 비활성화",
            "video_path": "",
        }
        try:
            project.video_path = ""
        except Exception:
            pass
        print(
            "[Sprint131-6 Fresh Input] Legacy Video Auto Connect: DISABLED",
            flush=True,
        )

        project_data = self._project_data(project)
        image_path = project_data.get(
            "image_path",
            "",
        )
        manual_product_image_paths = self._product_image_paths(
            project=project,
            project_data=project_data,
            supplied_paths=product_image_paths,
            supplied_path=product_image_path,
        )
        manual_product_image_path = (
            manual_product_image_paths[0]
            if manual_product_image_paths
            else ""
        )

        # Sprint146-7: 잠금 대본 실행에서는 업로드 순서를 장면 순서로 그대로 사용합니다.
        # 상세페이지 분할, 이미지 역할 재분류, AI 이미지 재선택을 하지 않습니다.
        scene_image_direct_mode = bool(locked_script and manual_product_image_paths)
        print("[Sprint146-7 Scene Image Direct] Enabled:", scene_image_direct_mode, flush=True)
        print("[Sprint146-7 Scene Image Direct] Input Count:", len(manual_product_image_paths), flush=True)
        for _scene_image_index, _scene_image_path in enumerate(manual_product_image_paths, start=1):
            print(
                f"[Sprint146-7 Scene Image Direct] Scene{_scene_image_index:02d}: {_scene_image_path}",
                flush=True,
            )

        image_extractor_result = {
            "ok": False,
            "ready": False,
            "version": (
                getattr(ImageExtractor, "VERSION", "image-selector-unavailable")
                if ImageExtractor is not None
                else "image-selector-unavailable"
            ),
            "status": "waiting_for_image_input",
            "source_count": 0,
            "selected_count": 0,
            "images": [],
            "rejections": [],
            "warnings": [],
            "errors": [],
        }
        extractor_applied = False

        # Sprint106-1 Multi Product Image Pipeline
        # - 입력 1장: 긴 상세페이지일 수 있으므로 Smart Strip 실행
        # - 입력 2장 이상: 각 이미지를 독립 상품 이미지로 간주하고 Strip 완전 우회
        # 이후 모든 후보를 Image Role Classifier로 전달합니다.
        multi_image_input_count = len(manual_product_image_paths)
        multi_image_mode = scene_image_direct_mode or multi_image_input_count >= 2
        input_mode = (
            "multi_image_direct"
            if multi_image_mode
            else "single_image_smart_strip"
            if multi_image_input_count == 1
            else "no_image"
        )

        image_strip_result = {
            "ok": bool(multi_image_mode),
            "ready": False,
            "version": ImageStripSplitter.VERSION,
            "status": "not_run",
            "image_count": 0,
            "images": [],
            "strip_detected": False,
            "bypassed": bool(multi_image_mode),
            "input_mode": input_mode,
            "source_summaries": [
                {"path": str(path), "mode": "direct_original"}
                for path in manual_product_image_paths
            ] if multi_image_mode else [],
            "warnings": [],
            "errors": [],
        }

        if len(manual_product_image_paths) == 1 and not scene_image_direct_mode:
            try:
                strip_source_path = manual_product_image_paths[0]
                strip_output_dir = (
                    Path("assets")
                    / "products"
                    / f"project_{getattr(project, 'id', '')}"
                )
                image_strip_result = ImageStripSplitter().process(
                    uploaded_images=[strip_source_path],
                    project_id=getattr(project, "id", ""),
                    product_name=(
                        getattr(project, "product_name", "")
                        or getattr(project, "title", "")
                        or "선택 상품"
                    ),
                    output_dir=strip_output_dir,
                    max_images=40,
                    split_strip=True,
                    preserve_original=False,
                    clear_previous=False,
                )
                if image_strip_result.get("strip_detected"):
                    split_paths = [
                        str(item.get("path") or "")
                        for item in list(image_strip_result.get("images", []) or [])
                        if str(item.get("path") or "").strip()
                    ]
                    if split_paths:
                        manual_product_image_paths = split_paths
                        manual_product_image_path = split_paths[0]
            except Exception as exc:
                image_strip_result.update(
                    status="failed",
                    errors=[f"{type(exc).__name__}: {exc}"],
                )

        print("[Sprint106-1 Multi Image] Input Mode:", input_mode, flush=True)
        print("[Sprint106-1 Multi Image] Original Count:", multi_image_input_count, flush=True)
        print("[Sprint106-1 Multi Image] Strip Bypassed:", multi_image_mode, flush=True)
        for input_index, input_path in enumerate(
            manual_product_image_paths if multi_image_mode else [],
            start=1,
        ):
            print(
                f"[Sprint106-1 Multi Image] ORIGINAL {input_index:02d}: {input_path}",
                flush=True,
            )

        print("[Sprint98-5 Image Strip] Version:", image_strip_result.get("version", ""), flush=True)
        print("[Sprint98-5 Image Strip] Status:", image_strip_result.get("status", ""), flush=True)
        print("[Sprint98-5 Image Strip] Detected:", image_strip_result.get("strip_detected", False), flush=True)
        print("[Sprint98-5 Image Strip] Count:", image_strip_result.get("image_count", 0), flush=True)
        print("[Sprint98-5 Image Strip] Errors:", image_strip_result.get("errors", []), flush=True)
        print("[Sprint106-1 Image Input] Source Count:", len(image_strip_result.get("source_summaries", []) or []), flush=True)
        print("[Sprint106-1 Image Input] Detected Segments:", image_strip_result.get("image_count", 0), flush=True)
        for trace_index, trace_item in enumerate(image_strip_result.get("images", []) or [], start=1):
            print(
                f"[Sprint106-1 Image Input] {trace_index:02d}: {trace_item.get('path', '')}",
                flush=True,
            )

        selector_sources = list(manual_product_image_paths)
        if selector_sources and ImageExtractor is not None and not scene_image_direct_mode:
            try:
                selector_output_dir = (
                    Path("assets")
                    / "products"
                    / f"project_{getattr(project, 'id', '')}"
                    / "selected_106_1"
                )
                selector = ImageExtractor(
                    max_images=10,
                    min_images=2,
                    min_width=64,
                    min_height=64,
                    min_area=4096,
                    min_score=24.0,
                )
                if hasattr(selector, "select_from_candidates"):
                    image_extractor_result = selector.select_from_candidates(
                        candidate_images=selector_sources,
                        output_dir=selector_output_dir,
                        project_id=getattr(project, "id", ""),
                        product_name=(
                            getattr(project, "product_name", "")
                            or getattr(project, "title", "")
                            or "선택 상품"
                        ),
                        max_images=10,
                        clean_output=True,
                    )
                else:
                    image_extractor_result.update(
                        status="selector_method_missing",
                        errors=["ImageExtractor.select_from_candidates가 없습니다."],
                    )
                selected_paths = [
                    str(item.get("output_path") or item.get("path") or "")
                    for item in list(image_extractor_result.get("images", []) or [])
                    if str(item.get("output_path") or item.get("path") or "").strip()
                ]
                if image_extractor_result.get("ready") and selected_paths:
                    manual_product_image_paths = selected_paths
                    manual_product_image_path = selected_paths[0]
                    extractor_applied = True
            except Exception as exc:
                image_extractor_result.update(
                    status="failed",
                    errors=[f"{type(exc).__name__}: {exc}"],
                )

        print("[Sprint106-1 Image Role Classifier] Version:", image_extractor_result.get("version", ""), flush=True)
        print("[Sprint106-1 Image Role Classifier] Status:", image_extractor_result.get("status", ""), flush=True)
        print("[Sprint106-1 Image Role Classifier] Ready:", image_extractor_result.get("ready", False), flush=True)
        print("[Sprint106-1 Image Role Classifier] Applied:", extractor_applied, flush=True)
        print("[Sprint106-1 Image Role Classifier] Input Count:", image_extractor_result.get("source_count", 0), flush=True)
        print("[Sprint106-1 Image Role Classifier] Selected Count:", image_extractor_result.get("selected_count", 0), flush=True)
        print("[Sprint106-1 Image Role Classifier] Rejected Count:", image_extractor_result.get("rejected_count", 0), flush=True)
        for rejected_item in list(image_extractor_result.get("rejections", []) or []):
            print(
                f"[Sprint106-1 Image Role Classifier] REJECT: {rejected_item.get('path') or rejected_item.get('source_path', '')} "
                f"reason={rejected_item.get('reason', '')}",
                flush=True,
            )
        for selected_index, selected_item in enumerate(image_extractor_result.get("images", []) or [], start=1):
            print(
                f"[Sprint106-1 Image Role Classifier] {selected_index:02d}: "
                f"{selected_item.get('output_path') or selected_item.get('path', '')} "
                f"({selected_item.get('width', 0)}x{selected_item.get('height', 0)}) "
                f"score={selected_item.get('score', 0)} type={selected_item.get('image_type', '')}",
                flush=True,
            )
        print("[Sprint106-1 Image Role Classifier] Output:", image_extractor_result.get("output_dir", ""), flush=True)
        print("[Sprint106-1 Image Role Classifier] Errors:", image_extractor_result.get("errors", []), flush=True)
        print("[Sprint106-1 Image Role Classifier] Role Counts:", image_extractor_result.get("role_counts", {}), flush=True)
        print("[Sprint106-1 Image Role Classifier] Role Sequence:", image_extractor_result.get("role_sequence", []), flush=True)

        print(
            "[Sprint94-1 Manual Images] Count:",
            len(manual_product_image_paths),
            flush=True,
        )
        print(
            "[Sprint94-1 Manual Images] Main:",
            manual_product_image_path,
            flush=True,
        )

        job_id = uuid4().hex[:12]
        state = PipelineState()

        state.create(
            job_id,
            getattr(project, "product_name", "")
            or getattr(project, "title", ""),
            self.steps(),
        )

        # Sprint146-5B 최종 방어: 승인 게이트를 통과한 뒤에는
        # 어떤 분기에서도 비어 있는 script_status가 남지 않게 합니다.
        script_status = str(script_status or "APPROVED").strip().upper()
        if script_status != "APPROVED":
            script_status = "APPROVED"

        outputs = dict(approved_outputs)
        outputs.update({
            "workflow_version": self.WORKFLOW_VERSION,
            "execution_mode": "locked_script_scene_image_direct",
            "scene_image_direct_mode": scene_image_direct_mode,
            "scene_image_count": len(manual_product_image_paths),
            "trust_input": {
                "monthly_purchase_count": int(monthly_purchase_count or 0),
                "review_count": int(declared_review_count or 0),
                "rating": float(rating or 0),
                "review_checked_at": str(review_checked_at or "").strip(),
            },
            "auto_connected": auto_connected,
            "youtube_privacy_status": youtube_privacy_status,
            "image_extractor": image_extractor_result,
            "image_strip_splitter": image_strip_result,
            "approved_script_lock": {
                "version": "locked-script-lock-146-8",
                "status": "locked",
                "script_status": script_status,
                "best_script": approved_script_text,
                "source_result_path": approved_outputs.get("script_result_path", ""),
            },
        })

        # Sprint134-1: 사용자가 직접 고른 바이럴 쇼츠를 원클릭에서 분석합니다.
        viral_library_result = {
            "ok": False,
            "ready": False,
            "version": "viral-library-ingestor-133-2",
            "status": "skipped_no_manual_sources",
            "items": [],
            "errors": [],
        }
        viral_scene_analysis_result = {
            "ok": False,
            "ready": False,
            "version": "viral-scene-analyzer-133-3",
            "status": "skipped_no_manual_sources",
            "videos": [],
            "errors": [],
        }
        viral_editing_patterns_result = {
            "ok": False,
            "ready": False,
            "version": "viral-editing-feature-analyzer-133-4",
            "status": "skipped_no_manual_sources",
            "project_patterns": {},
            "videos": [],
            "errors": [],
        }
        project_id_for_viral = str(getattr(project, "id", "") or "default")
        if viral_video_sources:
            try:
                viral_library_result = ViralLibraryIngestor(max_items=10).ingest(
                    sources=viral_video_sources,
                    project_id=project_id_for_viral,
                    overwrite=True,
                    save=True,
                )
                if viral_library_result.get("ready"):
                    viral_scene_analysis_result = ViralSceneAnalyzer().analyze_project(
                        project_id=project_id_for_viral,
                        overwrite=True,
                        save=True,
                    )
                if viral_scene_analysis_result.get("ready"):
                    viral_editing_patterns_result = ViralEditingFeatureAnalyzer().analyze_project(
                        project_id=project_id_for_viral,
                        overwrite=True,
                        save=True,
                    )
            except Exception as exc:
                viral_editing_patterns_result = {
                    **viral_editing_patterns_result,
                    "status": "exception",
                    "errors": [f"{type(exc).__name__}: {exc}"],
                }
                print("[Sprint134-1 Viral One Click] ERROR:", repr(exc), flush=True)

        outputs["viral_library"] = viral_library_result
        outputs["viral_scene_analysis"] = viral_scene_analysis_result
        outputs["viral_editing_patterns"] = viral_editing_patterns_result
        print("[Sprint134-1 Viral One Click] Source Count:", len(viral_video_sources), flush=True)
        print("[Sprint134-1 Viral One Click] Library Status:", viral_library_result.get("status"), flush=True)
        print("[Sprint134-1 Viral One Click] Scene Status:", viral_scene_analysis_result.get("status"), flush=True)
        print("[Sprint134-1 Viral One Click] Pattern Status:", viral_editing_patterns_result.get("status"), flush=True)

        # 1. Product Plan
        try:
            coupang_url = str(
                getattr(project, "coupang_url", "") or ""
            ).strip()

            if coupang_url:
                product_plan = ProductEngine().build_from_coupang(
                    coupang_url,
                    product_name=getattr(
                        project,
                        "product_name",
                        "",
                    ),
                    price=getattr(project, "price", ""),
                    category=getattr(
                        project,
                        "category",
                        "",
                    ),
                    image_url=getattr(
                        project,
                        "image_url",
                        "",
                    ),
                    partner_url=getattr(
                        project,
                        "partner_url",
                        "",
                    ),
                    project_id=getattr(project, "id", ""),
                    collect_product_images=(
                        not bool(manual_product_image_paths)
                    ),
                    max_product_images=40,
                )
            else:
                product_plan = {
                    "ok": True,
                    "status": "manual_product_plan",
                    "source": "manual_upload",
                    "project_payload": {
                        "product_name": getattr(
                            project,
                            "product_name",
                            "",
                        ) or getattr(project, "title", ""),
                        "keyword": getattr(project, "keyword", ""),
                        "category": getattr(project, "category", ""),
                        "price": getattr(project, "price", ""),
                    },
                    "keywords": (
                        project_data.get("keywords", {})
                        if isinstance(project_data, dict)
                        else {}
                    ),
                    "reviews": [],
                    "review_count": 0,
                }

            outputs["product_plan"] = product_plan

            state.update_step(
                job_id,
                "product_plan",
                "done",
                self._compact(product_plan),
            )

        except Exception as exc:
            product_plan = {}
            outputs["product_plan"] = {}

            state.update_step(
                job_id,
                "product_plan",
                "failed",
                error=exc,
            )

        # 1-1. Sprint93-1 Multi Image Collector
        if manual_product_image_paths:
            if (
                not extractor_applied
                and image_strip_result.get("strip_detected")
                and image_strip_result.get("images")
            ):
                multi_image_result = image_strip_result
            else:
                multi_image_result = self._build_manual_product_image_result(
                    manual_product_image_paths,
                    project,
                )

            product_images = list(
                multi_image_result.get("images", []) or []
            )
            if isinstance(product_plan, dict):
                product_plan["multi_image_collector"] = multi_image_result
                product_plan["product_images"] = product_images
                product_plan["product_image_count"] = len(product_images)
                product_plan["product_image_path"] = (
                    manual_product_image_path
                )
        else:
            multi_image_result = (
                product_plan.get("multi_image_collector", {})
                if isinstance(product_plan, dict)
                else {}
            )
            product_images = (
                product_plan.get("product_images", [])
                if isinstance(product_plan, dict)
                else []
            )
            if not isinstance(product_images, list):
                product_images = []

        outputs["multi_image_collector"] = multi_image_result
        outputs["product_images"] = product_images
        outputs["product_image_count"] = len(product_images)
        outputs["product_image_path"] = str(
            manual_product_image_path
            or (
                product_plan.get("product_image_path", "")
                if isinstance(product_plan, dict)
                else ""
            )
        )

        print(
            "[Sprint94-1 Image Input] Version:",
            multi_image_result.get("version", ""),
            flush=True,
        )
        print(
            "[Sprint94-1 Image Input] Status:",
            multi_image_result.get("status", "not_run"),
            flush=True,
        )
        print(
            "[Sprint94-1 Image Input] Count:",
            len(product_images),
            flush=True,
        )
        print(
            "[Sprint94-1 Image Input] Directory:",
            multi_image_result.get("output_dir", ""),
            flush=True,
        )
        print(
            "[Sprint94-1 Image Input] Manifest:",
            multi_image_result.get("manifest_path", ""),
            flush=True,
        )
        print(
            "[Sprint94-1 Image Input] Errors:",
            multi_image_result.get("errors", []),
            flush=True,
        )

        # 기존 1장 기반 Veo 생성은 Sprint93 Multi Image AI Director 완성 전까지 정지
        ai_video_result = {
            "ok": False,
            "ready": False,
            "status": "paused_for_sprint93_multi_image_director",
            "engine_version": AIVideoEngine.VERSION,
            "provider_version": GeminiVeoProvider.VERSION,
            "product_image_path": outputs["product_image_path"],
            "product_image_count": len(product_images),
            "generated_files": [],
            "selected_video_path": "",
            "errors": [],
            "warnings": [
                "기존 1장 기반 Veo 생성은 Sprint93에서 잠시 정지되었습니다."
            ],
        }
        outputs["ai_video"] = ai_video_result
        outputs["ai_video_path"] = ""

        print(
            "[Sprint93-1 AI Video] Status:",
            ai_video_result.get("status", ""),
            flush=True,
        )

        # 1-2. Sprint93-2~93-7 Multi Image AI Director Pipeline
        product_name_for_director = (
            getattr(project, "product_name", "")
            or getattr(project, "title", "")
            or "선택 상품"
        )

        print(
            "[UTF8 PROJECT NAME TRACE]",
            {
                "project_product_name": repr(
                    getattr(project, "product_name", "")
                ),
                "project_title": repr(
                    getattr(project, "title", "")
                ),
                "selected": repr(product_name_for_director),
            },
            flush=True,
        )
        project_id_for_director = getattr(project, "id", "")
        director_output_dir = str(
            multi_image_result.get("output_dir", "")
            or (
                Path("exports")
                / "ai_director"
                / f"project_{project_id_for_director}"
            )
        )

        vision_analysis_result = {
            "ok": False,
            "ready": False,
            "version": ImageVisionAnalyzer.VERSION,
            "status": "not_run",
            "images": [],
            "errors": [],
        }
        image_tags_result = {
            "ok": False,
            "ready": False,
            "version": ImageTagger.VERSION,
            "status": "not_run",
            "images": [],
            "errors": [],
        }
        story_intelligence_result = {
            "ok": False,
            "ready": False,
            "version": StoryIntelligenceEngine.VERSION,
            "status": "not_run",
            "story_type": "",
            "product_type": "",
            "selling_points": [],
            "emotion_curve": [],
            "scene_goals": [],
            "image_role_plan": [],
            "errors": [],
        }
        scene_plan_result = {
            "ok": False,
            "ready": False,
            "version": ScenePlanner.VERSION,
            "status": "not_run",
            "scenes": [],
            "errors": [],
        }
        scene_selection_result = {
            "ok": False,
            "ready": False,
            "version": SceneImageSelector.VERSION,
            "status": "not_run",
            "scenes": [],
            "errors": [],
        }
        image_director_blueprint_result = {
            "ok": False,
            "ready": False,
            "version": ImageDirector.VERSION,
            "status": "not_run",
            "scene_count": 0,
            "blueprints": [],
            "output_path": "",
            "warnings": [],
            "errors": [],
        }
        ai_image_director_result = {
            "ok": False,
            "ready": False,
            "version": AIImageDirector.VERSION,
            "status": "not_run",
            "scenes": [],
            "image_prompts": [],
            "motion_plan": [],
            "motion_scene_count": 0,
            "errors": [],
        }
        # 기존 반환 키 호환용입니다. Sprint130-1 기본 경로에서는 Gemini/Veo를 호출하지 않습니다.
        gemini_director_result = {
            "ok": False,
            "ready": False,
            "version": GeminiDirector.VERSION,
            "status": "bypassed_ai_image_pipeline",
            "scenes": [],
            "errors": [],
            "api_called": False,
        }
        director_manifest_result = {
            "ok": False,
            "ready": False,
            "version": DirectorManifestWriter.VERSION,
            "status": "not_run",
            "manifest_path": "",
            "errors": [],
        }
        scene_video_result = {
            "ok": False,
            "ready": False,
            "version": SceneVideoGenerator.VERSION,
            "status": "not_run",
            "generated_scene_count": 0,
            "failed_scene_count": 0,
            "generated_files": [],
            "updated_manifest": {},
            "updated_manifest_path": "",
            "errors": [],
        }
        scene_merge_result = {
            "ok": False,
            "ready": False,
            "version": SceneMergeEngine.VERSION,
            "status": "not_run",
            "output_path": "",
            "errors": [],
        }

        # Sprint135-4: Vision Analyzer 호출 전/후를 분리해 기록합니다.
        # 기존 코드는 analyze()가 반환된 뒤에만 로그를 남겼기 때문에,
        # 내부 지연·정지·예외가 발생하면 호출 자체가 안 된 것처럼 보였습니다.
        vision_input_summary = []
        for vision_index, vision_item in enumerate(list(product_images or []), start=1):
            if isinstance(vision_item, dict):
                vision_path = str(
                    vision_item.get("path")
                    or vision_item.get("output_path")
                    or vision_item.get("source_path")
                    or ""
                )
                vision_input_summary.append(
                    {
                        "index": vision_index,
                        "type": "dict",
                        "path": vision_path,
                        "exists": bool(vision_path and Path(vision_path).is_file()),
                    }
                )
            else:
                vision_path = str(vision_item or "")
                vision_input_summary.append(
                    {
                        "index": vision_index,
                        "type": type(vision_item).__name__,
                        "path": vision_path,
                        "exists": bool(vision_path and Path(vision_path).is_file()),
                    }
                )

        print(
            "[Sprint135-4 Vision Trace] CALL BEGIN",
            flush=True,
        )
        print(
            "[Sprint135-4 Vision Trace] Input Count:",
            len(vision_input_summary),
            flush=True,
        )
        print(
            "[Sprint135-4 Vision Trace] Manifest:",
            multi_image_result.get("manifest_path", ""),
            flush=True,
        )
        print(
            "[Sprint135-4 Vision Trace] Output Dir:",
            director_output_dir,
            flush=True,
        )
        for vision_item in vision_input_summary:
            print(
                f"[Sprint135-4 Vision Trace] INPUT {vision_item['index']:02d}: "
                f"type={vision_item['type']} exists={vision_item['exists']} "
                f"path={vision_item['path']}",
                flush=True,
            )

        vision_started_at = time.perf_counter()
        try:
            vision_analysis_result = ImageVisionAnalyzer().analyze(
                images=product_images,
                manifest_path=multi_image_result.get("manifest_path", ""),
                output_dir=director_output_dir,
                product_name=product_name_for_director,
                project_id=project_id_for_director,
                save_result=True,
            )
            print(
                "[Sprint135-4 Vision Trace] CALL RETURNED:",
                f"{time.perf_counter() - vision_started_at:.3f}s",
                flush=True,
            )
        except Exception as exc:
            vision_analysis_result.update(
                status="failed",
                errors=[f"{type(exc).__name__}: {exc}"],
            )
            print(
                "[Sprint135-4 Vision Trace] CALL ERROR:",
                f"{type(exc).__name__}: {exc}",
                flush=True,
            )
            print(
                "[Sprint135-4 Vision Trace] ELAPSED:",
                f"{time.perf_counter() - vision_started_at:.3f}s",
                flush=True,
            )

        outputs["vision_analysis"] = vision_analysis_result
        outputs["vision_input_summary"] = vision_input_summary
        print(
            "[Sprint93-2 Vision Analyzer] Version:",
            vision_analysis_result.get("version", ""),
            flush=True,
        )
        print(
            "[Sprint93-2 Vision Analyzer] Status:",
            vision_analysis_result.get("status", ""),
            flush=True,
        )
        print(
            "[Sprint93-2 Vision Analyzer] Count:",
            vision_analysis_result.get("analyzed_count", 0),
            flush=True,
        )
        print(
            "[Sprint93-2 Vision Analyzer] Errors:",
            vision_analysis_result.get("errors", []),
            flush=True,
        )

        # Sprint135-2: Product Keeper
        # 원본 상품 사진은 참조 전용으로 등록하고, 이후 생성 장면에서
        # 판매 상품의 형태·색상·버튼·디스플레이·포트·비율·구성품을 잠급니다.
        product_keeper_result = {
            "ok": False,
            "ready": False,
            "version": ProductKeeper.VERSION,
            "status": "not_run",
            "product_name": product_name_for_director,
            "product_identity_id": "",
            "reference_images": [],
            "reference_image_count": 0,
            "identity_features": {},
            "locked_attributes": [],
            "generation_rules": {},
            "manifest_path": "",
            "errors": [],
        }

        print(
            "[Sprint135-4 Product Keeper Trace] CALL BEGIN",
            flush=True,
        )
        product_keeper_started_at = time.perf_counter()
        try:
            product_keeper_result = ProductKeeper().build(
                product_name=product_name_for_director,
                reference_images=product_images,
                vision_result=vision_analysis_result,
                image_role_result=image_extractor_result,
                output_dir=director_output_dir,
                save=True,
            )
            print(
                "[Sprint135-4 Product Keeper Trace] CALL RETURNED:",
                f"{time.perf_counter() - product_keeper_started_at:.3f}s",
                flush=True,
            )
        except Exception as exc:
            product_keeper_result.update(
                status="failed",
                errors=[f"{type(exc).__name__}: {exc}"],
            )
            print(
                "[Sprint135-4 Product Keeper Trace] CALL ERROR:",
                f"{type(exc).__name__}: {exc}",
                flush=True,
            )

        outputs["product_keeper"] = product_keeper_result
        outputs["product_identity_id"] = str(
            product_keeper_result.get("product_identity_id", "") or ""
        )
        outputs["product_identity_manifest_path"] = str(
            product_keeper_result.get("manifest_path", "") or ""
        )

        print(
            "[Sprint135-2 Product Keeper] Version:",
            product_keeper_result.get("version", ""),
            flush=True,
        )
        print(
            "[Sprint135-2 Product Keeper] Status:",
            product_keeper_result.get("status", ""),
            flush=True,
        )
        print(
            "[Sprint135-2 Product Keeper] Ready:",
            product_keeper_result.get("ready", False),
            flush=True,
        )
        print(
            "[Sprint135-2 Product Keeper] Identity:",
            product_keeper_result.get("product_identity_id", ""),
            flush=True,
        )
        print(
            "[Sprint135-2 Product Keeper] References:",
            product_keeper_result.get("reference_image_count", 0),
            flush=True,
        )
        print(
            "[Sprint135-2 Product Keeper] Product Locked:",
            bool(
                product_keeper_result.get("reference_policy", {}).get(
                    "product_must_remain_unchanged",
                    False,
                )
            ),
            flush=True,
        )
        print(
            "[Sprint135-2 Product Keeper] Manifest:",
            product_keeper_result.get("manifest_path", ""),
            flush=True,
        )
        print(
            "[Sprint135-2 Product Keeper] Errors:",
            product_keeper_result.get("errors", []),
            flush=True,
        )

        try:
            image_tags_result = ImageTagger().tag(
                vision_result=vision_analysis_result,
                vision_analysis_path=vision_analysis_result.get(
                    "analysis_path",
                    "",
                ),
                output_dir=director_output_dir,
                product_name=product_name_for_director,
                project_id=project_id_for_director,
                save_result=True,
            )
        except Exception as exc:
            image_tags_result.update(
                status="failed",
                errors=[f"{type(exc).__name__}: {exc}"],
            )

        outputs["image_tags"] = image_tags_result
        print(
            "[Sprint93-3 Image Tagger] Version:",
            image_tags_result.get("version", ""),
            flush=True,
        )
        print(
            "[Sprint93-3 Image Tagger] Status:",
            image_tags_result.get("status", ""),
            flush=True,
        )
        print(
            "[Sprint93-3 Image Tagger] Count:",
            image_tags_result.get("tagged_count", 0),
            flush=True,
        )
        print(
            "[Sprint93-3 Image Tagger] Errors:",
            image_tags_result.get("errors", []),
            flush=True,
        )

        # Sprint102-1: 이미지 태그/분석/원본을 장면 목적별 Image Pool로 정규화합니다.
        image_pool_result = {
            "ok": False,
            "ready": False,
            "version": ImagePoolBuilder.VERSION,
            "status": "not_run",
            "image_count": 0,
            "pool_count": 0,
            "image_pool": {},
            "pool_counts": {},
            "top_candidates": {},
            "errors": [],
        }

        # Sprint103-2: 동일한 원본 이미지라면 Image Pool 결과를 재사용합니다.
        image_pool_cache_path = (
            Path(director_output_dir) / "image_pool_cache_103_2.json"
        )
        image_pool_source_items = []
        for raw_path in list(product_images or []):
            try:
                source_path = Path(str(raw_path))
                source_stat = source_path.stat()
                image_pool_source_items.append(
                    {
                        "path": str(source_path.resolve()),
                        "size": int(source_stat.st_size),
                        "mtime_ns": int(source_stat.st_mtime_ns),
                    }
                )
            except Exception:
                image_pool_source_items.append(
                    {
                        "path": str(raw_path),
                        "size": -1,
                        "mtime_ns": -1,
                    }
                )

        image_pool_source_signature = hashlib.sha256(
            json.dumps(
                {
                    "project_id": str(project_id_for_director),
                    "product_name": str(product_name_for_director),
                    "manifest_path": str(
                        multi_image_result.get("manifest_path", "")
                    ),
                    "sources": image_pool_source_items,
                    "builder_version": str(ImagePoolBuilder.VERSION),
                    "max_per_pool": 40,
                },
                ensure_ascii=False,
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()

        image_pool_cache_hit = False
        image_pool_cache_reason = "cache_missing"

        try:
            if image_pool_cache_path.is_file():
                cached_payload = json.loads(
                    image_pool_cache_path.read_text(encoding="utf-8")
                )
                cached_result = cached_payload.get("result", {})
                cached_signature = str(
                    cached_payload.get("source_signature", "")
                )
                cached_pool = (
                    cached_result.get("image_pool", {})
                    if isinstance(cached_result, dict)
                    else {}
                )
                cached_image_count = int(
                    cached_result.get("image_count", 0) or 0
                ) if isinstance(cached_result, dict) else 0

                if cached_signature != image_pool_source_signature:
                    image_pool_cache_reason = "source_changed"
                elif not isinstance(cached_pool, dict) or not cached_pool:
                    image_pool_cache_reason = "cached_pool_empty"
                elif cached_image_count <= 0:
                    image_pool_cache_reason = "cached_image_count_zero"
                else:
                    image_pool_result = dict(cached_result)
                    image_pool_result["status"] = "reused_cache"
                    image_pool_result["cache_hit"] = True
                    image_pool_result["cache_path"] = str(
                        image_pool_cache_path
                    )
                    image_pool_result["source_signature"] = (
                        image_pool_source_signature
                    )
                    image_pool_cache_hit = True
                    image_pool_cache_reason = "valid_cache"
        except Exception as exc:
            image_pool_cache_reason = (
                f"cache_read_failed:{type(exc).__name__}"
            )

        if not image_pool_cache_hit:
            try:
                image_pool_result = ImagePoolBuilder().build(
                    tag_result=image_tags_result,
                    vision_result=vision_analysis_result,
                    image_input=multi_image_result,
                    manifest_path=multi_image_result.get(
                        "manifest_path",
                        "",
                    ),
                    output_dir=director_output_dir,
                    product_name=product_name_for_director,
                    project_id=project_id_for_director,
                    save_result=True,
                    max_per_pool=40,
                )
                image_pool_result["cache_hit"] = False
                image_pool_result["cache_path"] = str(
                    image_pool_cache_path
                )
                image_pool_result["source_signature"] = (
                    image_pool_source_signature
                )

                if (
                    image_pool_result.get("ok")
                    and int(image_pool_result.get("image_count", 0) or 0) > 0
                    and isinstance(image_pool_result.get("image_pool"), dict)
                    and image_pool_result.get("image_pool")
                ):
                    image_pool_cache_path.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                    )
                    image_pool_cache_path.write_text(
                        json.dumps(
                            {
                                "version": "image-pool-cache-103-2",
                                "source_signature": (
                                    image_pool_source_signature
                                ),
                                "created_at": time.time(),
                                "result": image_pool_result,
                            },
                            ensure_ascii=False,
                            indent=2,
                            default=str,
                        ),
                        encoding="utf-8",
                    )
            except Exception as exc:
                image_pool_result.update(
                    status="failed",
                    errors=[f"{type(exc).__name__}: {exc}"],
                )

        print(
            "[Sprint103-2 Image Pool Cache] Status:",
            "reused" if image_pool_cache_hit else "rebuilt",
            flush=True,
        )
        print(
            "[Sprint103-2 Image Pool Cache] Reason:",
            image_pool_cache_reason,
            flush=True,
        )
        print(
            "[Sprint103-2 Image Pool Cache] Path:",
            str(image_pool_cache_path),
            flush=True,
        )

        outputs["image_pool"] = image_pool_result
        print(
            "[Sprint102-1 Image Pool] Version:",
            image_pool_result.get("version", ""),
            flush=True,
        )
        print(
            "[Sprint102-1 Image Pool] Status:",
            image_pool_result.get("status", ""),
            flush=True,
        )
        print(
            "[Sprint102-1 Image Pool] Image Count:",
            image_pool_result.get("image_count", 0),
            flush=True,
        )
        print(
            "[Sprint102-1 Image Pool] Pool Counts:",
            image_pool_result.get("pool_counts", {}),
            flush=True,
        )
        print(
            "[Sprint102-1 Image Pool] Path:",
            image_pool_result.get("image_pool_path", ""),
            flush=True,
        )
        print(
            "[Sprint102-1 Image Pool] Errors:",
            image_pool_result.get("errors", []),
            flush=True,
        )

        # Sprint158 Fast Mode: 잠금 대본 원클릭에서는 바이럴 수집을 건너뜁니다.
        viral_collection_result = {
            "ok": True,
            "ready": False,
            "version": "viral-collector-bypassed-158",
            "status": "skipped_locked_script_fast_mode",
            "product_name": product_name_for_director,
            "keywords": [],
            "platforms": [],
            "query_count": 0,
            "candidate_count": 0,
            "selected_count": 0,
            "output_path": "",
            "videos": [],
            "warnings": [],
            "errors": [],
        }
        outputs["viral_collection"] = viral_collection_result
        print("[Sprint158 Fast Mode] Viral Collector: SKIPPED", flush=True)

        # Sprint100-4: Story 실행 전에 리뷰 OCR/정제/Insight를 먼저 준비합니다.
        pre_story_review_ocr = {
            "ok": False,
            "status": "not_run",
            "reviews": [],
            "review_count": 0,
        }
        pre_story_clean = {
            "ok": False,
            "status": "not_run",
            "reviews": [],
            "review_count": 0,
        }
        pre_story_reviews = []
        pre_story_review_insight = {}

        try:
            pre_story_image_paths = self._review_image_paths(
                project,
                project_data,
                supplied_paths=review_image_paths,
            )
            pre_story_review_ocr = self._run_review_image_ocr(
                pre_story_image_paths,
                project,
                multi_image_mode=multi_image_mode,
            )
            pre_story_ocr_reviews = self._normalize_reviews(
                pre_story_review_ocr.get("reviews", []),
                source="review_image_ocr",
            )
            pre_story_product_reviews = self._normalize_reviews(
                (product_plan.get("reviews") or product_plan.get("review_data") or [])
                if isinstance(product_plan, dict)
                else [],
                source=(product_plan.get("review_source") or "product_plan")
                if isinstance(product_plan, dict)
                else "product_plan",
            )
            pre_story_raw_reviews = self._merge_reviews(
                pre_story_product_reviews,
                pre_story_ocr_reviews,
            )
            pre_story_clean = ReviewCleaner().clean(
                reviews=pre_story_raw_reviews,
                source="product_plan+review_image_ocr",
            )
            pre_story_reviews = list(
                pre_story_clean.get("reviews", [])
                or pre_story_raw_reviews
            )
            pre_story_review_insight = ReviewInsightEngine().analyze(
                reviews=pre_story_reviews,
                social_comments=[],
                product_name=product_name_for_director,
            )

            outputs["review_ocr"] = pre_story_review_ocr
            outputs["review_clean"] = pre_story_clean
            outputs["merged_reviews"] = pre_story_reviews
            outputs["review_insight"] = pre_story_review_insight
            outputs["review_image_paths"] = pre_story_image_paths

            if isinstance(product_plan, dict):
                product_plan["ocr_reviews"] = pre_story_ocr_reviews
                product_plan["reviews"] = pre_story_reviews
                product_plan["review_data"] = pre_story_reviews
                product_plan["review_count"] = len(pre_story_reviews)
                product_plan["review_source"] = (
                    "review_image_ocr"
                    if pre_story_ocr_reviews
                    else product_plan.get("review_source", "product_plan")
                )
                product_plan["review_ocr"] = pre_story_review_ocr
                product_plan["review_clean"] = pre_story_clean
                outputs["product_plan"] = product_plan

            print(
                "[Sprint100-4 Pre-Story Review] OCR:",
                len(pre_story_ocr_reviews),
                "Merged:",
                len(pre_story_reviews),
                "Insight:",
                pre_story_review_insight.get("review_count", len(pre_story_reviews))
                if isinstance(pre_story_review_insight, dict)
                else 0,
                flush=True,
            )
        except Exception as exc:
            print(
                "[Sprint100-4 Pre-Story Review] ERROR:",
                repr(exc),
                flush=True,
            )

        # Sprint100-4: Story 실행 시점의 실제 입력과 결과를 JSON으로 저장합니다.
        story_review_input = (
            outputs.get("review_insight", {})
            if isinstance(outputs.get("review_insight", {}), dict)
            and outputs.get("review_insight", {})
            else {
                "review_count": (
                    product_plan.get("review_count", 0)
                    if isinstance(product_plan, dict)
                    else 0
                ),
                "reviews": (
                    product_plan.get("reviews", [])
                    if isinstance(product_plan, dict)
                    else []
                ),
            }
        )
        story_input_source = (
            "outputs.review_insight"
            if isinstance(outputs.get("review_insight", {}), dict)
            and outputs.get("review_insight", {})
            else "product_plan fallback"
        )
        story_product_info = {
            "product_name": (
                getattr(project, "product_name", "")
                or getattr(project, "title", "")
                or project_data.get("product_name", "")
                or project_data.get("title", "")
                or product_name_for_director
            ),
            "category": getattr(project, "category", ""),
            "keyword": getattr(project, "keyword", ""),
            "price": getattr(project, "price", ""),
            "product_plan": product_plan,
            "viral_collection": viral_collection_result,
            "manual_viral_library": viral_library_result,
            "manual_viral_scene_analysis": viral_scene_analysis_result,
            "manual_viral_editing_patterns": viral_editing_patterns_result,
            "viral_editing_template": viral_editing_patterns_result.get("project_patterns", {}),
            "viral_top_videos": list(
                viral_collection_result.get("videos", []) or []
            ),
        }
        story_ocr_result = (
            outputs.get("review_ocr", {}).get("reviews", [])
            if isinstance(outputs.get("review_ocr", {}), dict)
            else []
        )
        story_analysis_bundle = {
            "project_data": project_data,
            "product_plan": product_plan,
            "product_name": product_name_for_director,
            "category": getattr(project, "category", ""),
            "keyword": getattr(project, "keyword", ""),
            "viral_collection": viral_collection_result,
            "viral_top_videos": list(
                viral_collection_result.get("videos", []) or []
            ),
        }
        story_build_input = {
            "workflow_version": self.WORKFLOW_VERSION,
            "project_id": str(project_id_for_director or ""),
            "input_source": story_input_source,
            "product_info": story_product_info,
            "review_insight": story_review_input,
            "vision_result": vision_analysis_result,
            "image_tags": image_tags_result,
            "ocr_result": story_ocr_result,
            "analysis_bundle": story_analysis_bundle,
            "viral_collection": viral_collection_result,
            "manual_viral_editing_patterns": viral_editing_patterns_result,
            "scene_count": 6,
        }

        print(
            "[Sprint101-2 Story Input] Source:",
            story_input_source,
            flush=True,
        )
        print(
            "[Sprint101-2 Story Input] Review Count:",
            story_review_input.get("review_count", 0)
            if isinstance(story_review_input, dict)
            else 0,
            flush=True,
        )
        story_input_debug = self._write_sprint100_4_debug_json(
            output_dir=director_output_dir,
            filename="story_input_debug.json",
            payload=story_build_input,
        )
        outputs["story_input_debug"] = story_input_debug

        # Sprint99-3 Product Story Intelligence + Scene Goal Bridge
        try:
            story_intelligence_result = StoryIntelligenceEngine().build(
                product_info=story_product_info,
                review_insight=story_review_input,
                vision_result=vision_analysis_result,
                image_tags=image_tags_result,
                ocr_result=story_ocr_result,
                analysis_bundle=story_analysis_bundle,
                scene_count=6,
            )
        except Exception as exc:
            story_intelligence_result.update(
                status="failed",
                errors=[f"{type(exc).__name__}: {exc}"],
            )

        story_result_debug = self._write_sprint100_4_debug_json(
            output_dir=director_output_dir,
            filename="story_result_debug.json",
            payload=story_intelligence_result,
        )
        outputs["story_result_debug"] = story_result_debug

        # Sprint101-1: 각 Story Scene Goal에 실제 리뷰 근거를 직접 연결합니다.
        # 기존 StoryIntelligence 결과 구조는 유지하고 증거 관련 키만 추가합니다.
        story_scene_goals_for_evidence = list(
            story_intelligence_result.get("scene_goals", []) or []
        )

        def _story_text_items(value):
            items = []
            if isinstance(value, str):
                value = value.strip()
                if value:
                    items.append(value)
            elif isinstance(value, dict):
                for key in (
                    "text", "content", "review_text", "quote",
                    "evidence", "sentence", "value", "reason",
                ):
                    candidate = value.get(key)
                    if isinstance(candidate, str) and candidate.strip():
                        items.append(candidate.strip())
                        break
            elif isinstance(value, (list, tuple)):
                for item in value:
                    items.extend(_story_text_items(item))
            return items

        pain_evidence_pool = []
        benefit_evidence_pool = []
        proof_evidence_pool = []

        if isinstance(story_review_input, dict):
            for key in (
                "best_pain", "best_pain_point", "pain_points",
                "pain_point", "problems", "concerns",
            ):
                pain_evidence_pool.extend(
                    _story_text_items(story_review_input.get(key))
                )

            for key in (
                "best_benefit", "benefits", "benefit",
                "strengths", "advantages", "solutions",
            ):
                benefit_evidence_pool.extend(
                    _story_text_items(story_review_input.get(key))
                )

            for key in (
                "best_evidence", "evidence", "review_evidence",
                "selected_reviews", "reviews", "quotes",
                "best_quotes", "top_reviews",
            ):
                proof_evidence_pool.extend(
                    _story_text_items(story_review_input.get(key))
                )

        proof_evidence_pool.extend(_story_text_items(story_ocr_result))

        def _dedupe_story_evidence(items):
            unique = []
            seen = set()
            for item in items:
                normalized = " ".join(str(item).split()).strip()
                if not normalized or normalized in seen:
                    continue
                seen.add(normalized)
                unique.append(normalized)
            return unique

        pain_evidence_pool = _dedupe_story_evidence(pain_evidence_pool)
        benefit_evidence_pool = _dedupe_story_evidence(benefit_evidence_pool)
        proof_evidence_pool = _dedupe_story_evidence(proof_evidence_pool)

        evidence_assignments = []
        evidence_cursor = {"pain": 0, "benefit": 0, "proof": 0}

        for scene_index, goal in enumerate(story_scene_goals_for_evidence):
            if not isinstance(goal, dict):
                continue

            purpose = str(goal.get("purpose") or "feature").lower()
            goal_text = str(goal.get("goal") or "").lower()
            combined = f"{purpose} {goal_text}"

            if any(token in combined for token in (
                "problem", "pain", "공감", "불편", "문제", "고민", "긴장",
            )):
                evidence_type = "pain"
                evidence_pool = pain_evidence_pool or proof_evidence_pool
            elif any(token in combined for token in (
                "proof", "compare", "comparison", "review", "evidence",
                "후기", "근거", "비교", "검증",
            )):
                evidence_type = "proof"
                evidence_pool = proof_evidence_pool or benefit_evidence_pool
            else:
                evidence_type = "benefit"
                evidence_pool = benefit_evidence_pool or proof_evidence_pool

            evidence_text = ""
            if evidence_pool:
                cursor_key = evidence_type
                cursor = evidence_cursor.get(cursor_key, 0)
                evidence_text = evidence_pool[cursor % len(evidence_pool)]
                evidence_cursor[cursor_key] = cursor + 1

            goal["review_evidence"] = evidence_text
            goal["evidence_text"] = evidence_text
            goal["evidence_type"] = evidence_type
            goal["evidence_source"] = (
                "review_insight" if evidence_text else "none"
            )
            goal["evidence_scene_index"] = scene_index + 1
            goal["must_show"] = evidence_text or str(
                goal.get("primary_selling_point") or goal.get("goal") or ""
            )

            evidence_assignments.append({
                "scene": scene_index + 1,
                "purpose": purpose,
                "evidence_type": evidence_type,
                "evidence_text": evidence_text,
            })

        story_intelligence_result["scene_goals"] = story_scene_goals_for_evidence
        story_intelligence_result["review_evidence_bridge"] = {
            "version": "review-evidence-bridge-101-2",
            "scene_count": len(story_scene_goals_for_evidence),
            "assigned_count": sum(
                1 for item in evidence_assignments
                if item.get("evidence_text")
            ),
            "pain_pool_count": len(pain_evidence_pool),
            "benefit_pool_count": len(benefit_evidence_pool),
            "proof_pool_count": len(proof_evidence_pool),
            "assignments": evidence_assignments,
        }

        outputs["story_intelligence"] = story_intelligence_result
        print(
            "[Sprint101-2 Evidence Bridge] Assigned:",
            story_intelligence_result.get("review_evidence_bridge", {}).get(
                "assigned_count", 0
            ),
            "/",
            story_intelligence_result.get("review_evidence_bridge", {}).get(
                "scene_count", 0
            ),
            flush=True,
        )
        print(
            "[Sprint101-2 Evidence Bridge] Pools:",
            "pain=", len(pain_evidence_pool),
            "benefit=", len(benefit_evidence_pool),
            "proof=", len(proof_evidence_pool),
            flush=True,
        )
        for assignment in evidence_assignments:
            evidence_preview = " ".join(
                str(assignment.get("evidence_text") or "").split()
            )[:80]
            print(
                "[Sprint101-2 Evidence Scene]",
                f"Scene{int(assignment.get('scene', 0)):02d}",
                "->",
                assignment.get("evidence_type", "none"),
                "|",
                evidence_preview or "NO_EVIDENCE",
                flush=True,
            )
        print(
            "[Sprint101-2 Story Intelligence] Version:",
            story_intelligence_result.get("version", ""),
            flush=True,
        )
        print(
            "[Sprint101-2 Story Intelligence] Status:",
            story_intelligence_result.get("status", ""),
            flush=True,
        )
        print(
            "[Sprint101-2 Story Intelligence] Product Type:",
            story_intelligence_result.get("product_type", ""),
            flush=True,
        )
        print(
            "[Sprint101-2 Story Intelligence] Story Type:",
            story_intelligence_result.get("story_type", ""),
            flush=True,
        )
        print(
            "[Sprint101-2 Story Intelligence] Scene Goals:",
            len(story_intelligence_result.get("scene_goals", []) or []),
            flush=True,
        )
        print(
            "[Sprint101-2 Story Intelligence] Product Subtype:",
            story_intelligence_result.get("product_subtype", ""),
            flush=True,
        )
        print(
            "[Sprint101-2 Story Intelligence] Pain Points:",
            story_intelligence_result.get("pain_points", []),
            flush=True,
        )
        print(
            "[Sprint101-2 Story Intelligence] Benefits:",
            story_intelligence_result.get("benefits", []),
            flush=True,
        )
        print(
            "[Sprint101-2 Story Intelligence] Auto Complement:",
            story_intelligence_result.get("auto_complement", {}),
            flush=True,
        )
        print(
            "[Sprint101-2 Story Intelligence] Errors:",
            story_intelligence_result.get("errors", []),
            flush=True,
        )

        # Sprint124-2: Scene Planner 실행 전에 리뷰 기반 대본을 먼저 생성합니다.
        # 기존 후반 Review Pipeline은 보존하며, 영상 장면 설계용 Script-First 입력만 선행 준비합니다.
        pre_scene_script_result = {
            "ok": False,
            "version": getattr(ReviewScriptGenerator, "VERSION", ""),
            "status": "not_run",
            "best_script": "",
            "scripts": [],
            "errors": [],
        }
        if locked_script:
            pre_scene_script_result = dict(approved_review_scripts)
            outputs["review_scripts"] = pre_scene_script_result
            outputs["script_first_input"] = {
                "ok": True,
                "version": "locked-script-first-bypass-146-11",
                "review_count": int(declared_review_count or 0),
                "script_type": "locked_user_script",
                "scene_subtitle_count": len(scene_subtitles),
                "status": "SKIPPED_GENERATOR_USING_LOCKED_SCRIPT",
            }
            print("[Sprint146-10 Pre Scene Script] ReviewScriptGenerator: SKIPPED", flush=True)

            # Sprint146-16: 잠금 대본을 12개 영상 장면의 유일한 자막 원본으로 사용합니다.
            # 장면 연출(scene_goal, visual_direction, must_show 등)은 절대 자막 필드에 넣지 않습니다.
            target_locked_scene_count = 10
            locked_scene_duration = 2.5

            normalized_locked_lines = [
                " ".join(str(item.get("subtitle") or "").split()).strip()
                for item in list(pre_scene_script_result.get("scene_subtitles") or [])
                if isinstance(item, dict)
                and " ".join(str(item.get("subtitle") or "").split()).strip()
            ]
            if not normalized_locked_lines:
                normalized_locked_lines = [approved_script_text]

            # 문장이 12개보다 적으면 단어 단위로 균등 분할해 대본 전체를 빠짐없이 배치합니다.
            if len(normalized_locked_lines) < target_locked_scene_count:
                words = approved_script_text.split()
                locked_chunks = []
                if words:
                    for chunk_index in range(target_locked_scene_count):
                        start = round(chunk_index * len(words) / target_locked_scene_count)
                        end = round((chunk_index + 1) * len(words) / target_locked_scene_count)
                        chunk = " ".join(words[start:end]).strip()
                        if chunk:
                            locked_chunks.append(chunk)
                normalized_locked_lines = locked_chunks or normalized_locked_lines

            locked_scene_texts = normalized_locked_lines[:target_locked_scene_count]
            while len(locked_scene_texts) < target_locked_scene_count:
                locked_scene_texts.append("")

            locked_plan_scenes = []
            locked_subtitle_plan = []
            for locked_index in range(target_locked_scene_count):
                scene_number = locked_index + 1
                start_seconds = round(locked_index * locked_scene_duration, 2)
                end_seconds = round(start_seconds + locked_scene_duration, 2)
                subtitle_text = locked_scene_texts[locked_index]
                purpose = (
                    "hook" if scene_number == 1
                    else "cta" if scene_number == target_locked_scene_count
                    else "proof"
                )
                locked_plan_scenes.append({
                    "scene_id": f"scene_{scene_number:02d}",
                    "scene_index": scene_number,
                    "scene_type": purpose,
                    "purpose": purpose,
                    "dialogue": subtitle_text,
                    "subtitle_text": subtitle_text,
                    "duration_seconds": locked_scene_duration,
                    "subtitle_start": start_seconds,
                    "subtitle_end": end_seconds,
                    "subtitle_duration": locked_scene_duration,
                    "script_section_key": purpose,
                    "current_run_locked": True,
                    "subtitle_source": "locked_user_script_only",
                    "scene_goal": "",
                    "visual_direction": "",
                    "must_show": "",
                })
                if subtitle_text:
                    locked_subtitle_plan.append({
                        "scene_id": f"scene_{scene_number:02d}",
                        "scene_index": scene_number,
                        "text": subtitle_text,
                        "start": start_seconds,
                        "end": end_seconds,
                        "duration": locked_scene_duration,
                        "emphasis_words": [],
                        "source": "locked_user_script_only",
                    })

            scene_plan_result = {
                "ok": True,
                "ready": True,
                "version": "locked-script-scene-plan-150-5",
                "status": "locked_script_scene_plan_ready",
                "planning_mode": "locked_script_only",
                "script_line_count": len(locked_subtitle_plan),
                "scene_count": len(locked_plan_scenes),
                "target_duration_seconds": 25.0,
                "scenes": locked_plan_scenes,
                "subtitle_plan": locked_subtitle_plan,
                "errors": [],
            }
            outputs["scene_plan"] = scene_plan_result
            print("[Sprint150-5 Locked Subtitle] Applied: True", flush=True)
            print("[Sprint150-5 Locked Subtitle] Scene Count:", len(locked_plan_scenes), flush=True)
            print("[Sprint150-5 Locked Subtitle] Subtitle Count:", len(locked_subtitle_plan), flush=True)
            print("[Sprint150-5 Locked Subtitle] Source: locked_user_script_only", flush=True)
        else:
            try:
                pre_scene_quote_result = ReviewQuoteSelector().select(
                    reviews=pre_story_reviews,
                    product_name=product_name_for_director,
                    top_n=5,
                )
                pre_scene_hook_result = ReviewHookGenerator().generate(
                    review_quotes=pre_scene_quote_result,
                    review_insight=pre_story_review_insight,
                    product_name=product_name_for_director,
                    review_count=len(pre_story_reviews),
                )
                pre_scene_hook_result = HookOptimizer().apply_to_review_hooks(
                    review_hooks=pre_scene_hook_result,
                    review_insight=pre_story_review_insight,
                    product_name=product_name_for_director,
                    review_count=len(pre_story_reviews),
                )
                pre_scene_script_result = ReviewScriptGenerator().generate(
                    review_hooks=pre_scene_hook_result,
                    review_quotes=pre_scene_quote_result,
                    review_insight=pre_story_review_insight,
                    product_name=product_name_for_director,
                    review_count=len(pre_story_reviews),
                    story_intelligence=story_intelligence_result,
                )
                print(
                    "[UTF8 TRACE pre_scene_script_result SAFE]",
                    ascii(pre_scene_script_result),
                    flush=True,
                ) 
    
                outputs["review_quotes"] = pre_scene_quote_result
                outputs["review_hooks"] = pre_scene_hook_result
                outputs["review_scripts"] = pre_scene_script_result
                outputs["script_first_input"] = {
                    "ok": bool(pre_scene_script_result.get("ok")),
                    "version": "script-first-workflow-124-5",
                    "review_count": len(pre_story_reviews),
                    "script_type": pre_scene_script_result.get("best_script_type", ""),
                    "scene_subtitle_count": pre_scene_script_result.get("scene_subtitle_count", 0),
                }
                print(
                    "[Sprint124-2 Script First] Ready:",
                    bool(pre_scene_script_result.get("ok")),
                    flush=True,
                )
                print(
                    "[Sprint124-2 Script First] Type:",
                    pre_scene_script_result.get("best_script_type", ""),
                    flush=True,
                )
                print(
                    "[Sprint124-2 Script First] Scene Subtitles:",
                    pre_scene_script_result.get("scene_subtitle_count", 0),
                    flush=True,
                )
            except Exception as exc:
                pre_scene_script_result.update(
                    status="failed",
                    errors=[f"{type(exc).__name__}: {exc}"],
                )
                outputs["script_first_input"] = {
                    "ok": False,
                    "version": "script-first-workflow-124-5",
                    "review_count": len(pre_story_reviews),
                    "errors": list(pre_scene_script_result.get("errors") or []),
                }
    
            # Sprint146-4: 장면 설계 입력도 승인 완료 대본으로 강제 고정합니다.
        if approved_review_scripts and approved_script_text:
            pre_scene_script_result = dict(approved_review_scripts)
            pre_scene_script_result["best_script"] = approved_script_text
            pre_scene_script_result["status"] = "approved_script_locked"
            outputs["review_scripts"] = pre_scene_script_result
            outputs["script_first_input"] = {
                "ok": True,
                "version": "locked-script-scene-bridge-146-5",
                "status": "approved_script_locked",
                "review_count": int(declared_review_count or len(pre_story_reviews)),
                "script_type": pre_scene_script_result.get("best_script_type", ""),
                "scene_subtitle_count": pre_scene_script_result.get("scene_subtitle_count", 0),
            }
            print(
                "[Sprint146-5 Locked Script Scene Bridge] LOCKED:",
                len(approved_script_text),
                flush=True,
            )
            print(
                "[Sprint146-5D Locked Script Scene Bridge] Scene Subtitles:",
                pre_scene_script_result.get("scene_subtitle_count", 0),
                flush=True,
            )
        # Sprint150-5: locked_script 경로에서는 위에서 만든 잠금 대본 전용
        # scene_plan_result를 그대로 유지합니다. ScenePlanner의 장면 연출 문구가
        # dialogue/subtitle_text를 덮어쓰는 것을 차단합니다.
        if locked_script:
            print(
                "[Sprint150-5 Locked Subtitle Guard] ScenePlanner: SKIPPED",
                flush=True,
            )
            print(
                "[Sprint150-5 Locked Subtitle Guard] Subtitle Source: locked_user_script_only",
                flush=True,
            )
        else:
            try:
                scene_plan_result = ScenePlanner().plan(
                    tag_result=image_tags_result,
                    image_tags_path=image_tags_result.get(
                        "tag_manifest_path",
                        "",
                    ),
                    output_dir=director_output_dir,
                    product_name=product_name_for_director,
                    project_id=project_id_for_director,
                    target_duration_seconds=25,
                    target_scene_count=10,
                    save_result=True,
                )
            except Exception as exc:
                scene_plan_result.update(
                    status="failed",
                    errors=[f"{type(exc).__name__}: {exc}"],
                )

        # Sprint124-5: 현재 실행의 Sprint120-7 장면 자막과 Scene Planner 결과가
        # 완전히 동일한지 검증합니다. 불일치하면 현재 실행 자막을 강제로 복구합니다.
        current_run_scene_lines = [
            item for item in list(pre_scene_script_result.get("scene_subtitles") or [])
            if isinstance(item, dict) and str(item.get("subtitle") or "").strip()
        ]
        planned_for_lock = [
            item for item in list(scene_plan_result.get("scenes") or [])
            if isinstance(item, dict)
        ]
        lock_mismatches = []
        if current_run_scene_lines:
            for index, source_item in enumerate(current_run_scene_lines[:len(planned_for_lock)]):
                expected = " ".join(str(source_item.get("subtitle") or "").split()).strip()
                actual = " ".join(str(planned_for_lock[index].get("dialogue") or "").split()).strip()
                if expected != actual:
                    lock_mismatches.append({
                        "scene_id": str(source_item.get("scene_id") or f"scene_{index + 1:02d}"),
                        "expected": expected,
                        "actual": actual,
                    })
                    planned_for_lock[index]["dialogue"] = expected
                    planned_for_lock[index]["subtitle_text"] = expected
                    planned_for_lock[index]["script_section_key"] = str(
                        source_item.get("purpose") or planned_for_lock[index].get("script_section_key") or ""
                    )
                    planned_for_lock[index]["current_run_locked"] = True

            scene_plan_result["scenes"] = planned_for_lock
            # 강제 복구가 발생했으면 타임라인도 다시 현재 장면 기준으로 생성합니다.
            if lock_mismatches:
                rebuilt_subtitles = []
                for scene in planned_for_lock:
                    text_value = " ".join(str(scene.get("subtitle_text") or scene.get("dialogue") or "").split()).strip()
                    if not text_value:
                        continue
                    rebuilt_subtitles.append({
                        "scene_id": str(scene.get("scene_id") or ""),
                        "scene_index": int(scene.get("scene_index") or len(rebuilt_subtitles) + 1),
                        "text": text_value,
                        "start": round(float(scene.get("subtitle_start") or 0.0), 2),
                        "end": round(float(scene.get("subtitle_end") or 0.0), 2),
                        "duration": round(float(scene.get("subtitle_duration") or 0.0), 2),
                        "emphasis_words": list(scene.get("emphasis_words") or []),
                    })
                scene_plan_result["subtitle_plan"] = rebuilt_subtitles

        scene_plan_result["current_run_scene_lock"] = {
            "ready": bool(current_run_scene_lines),
            "source_count": len(current_run_scene_lines),
            "planned_count": len(planned_for_lock),
            "mismatch_count": len(lock_mismatches),
            "mismatches": lock_mismatches,
            "source": "ReviewScriptGenerator.scene_subtitles",
        }
        print(
            "[Sprint124-5 Current Run Lock] Ready:",
            bool(current_run_scene_lines),
            flush=True,
        )
        print(
            "[Sprint124-5 Current Run Lock] Source Count:",
            len(current_run_scene_lines),
            flush=True,
        )
        print(
            "[Sprint124-5 Current Run Lock] Mismatch Count:",
            len(lock_mismatches),
            flush=True,
        )
        for index, scene in enumerate(planned_for_lock, start=1):
            print(
                "[Sprint124-5 Current Run Lock]",
                str(scene.get("scene_id") or f"scene_{index:02d}"),
                "->",
                str(scene.get("dialogue") or ""),
                flush=True,
            )

        # Sprint99-3: 기존 ScenePlanner 결과에 Story Intelligence 장면 목표를 결합합니다.
        story_scene_goals = list(
            story_intelligence_result.get("scene_goals", []) or []
        )
        planned_scenes = list(scene_plan_result.get("scenes", []) or [])
        bridged_scene_count = 0

        for index, scene in enumerate(planned_scenes):
            if not isinstance(scene, dict) or index >= len(story_scene_goals):
                continue
            goal = story_scene_goals[index]
            if not isinstance(goal, dict):
                continue

            scene["story_goal"] = str(goal.get("goal") or "")
            scene["story_purpose"] = str(goal.get("purpose") or "feature")
            scene["emotion_stage"] = (
                (story_intelligence_result.get("emotion_curve") or [])[index]
                if index < len(story_intelligence_result.get("emotion_curve") or [])
                else ""
            )
            scene["preferred_roles"] = list(
                goal.get("preferred_roles") or []
            )
            scene["primary_selling_point"] = str(
                goal.get("primary_selling_point") or ""
            )
            scene["review_evidence"] = str(
                goal.get("review_evidence")
                or goal.get("evidence_text")
                or ""
            )
            scene["evidence_type"] = str(
                goal.get("evidence_type") or ""
            )
            scene["evidence_source"] = str(
                goal.get("evidence_source") or ""
            )
            scene["must_show"] = str(
                goal.get("must_show")
                or goal.get("primary_selling_point")
                or goal.get("goal")
                or ""
            )

            purpose_key = scene["story_purpose"].lower()
            evidence_key = scene["evidence_type"].lower()
            if any(token in purpose_key for token in ("hook", "intro", "후킹")):
                recommended_image_type = "main_product"
                recommended_video_type = "hero_motion"
            elif evidence_key == "pain":
                recommended_image_type = "problem_context"
                recommended_video_type = "pain_demonstration"
            elif evidence_key == "proof":
                recommended_image_type = "detail_proof"
                recommended_video_type = "evidence_demonstration"
            elif any(token in purpose_key for token in ("cta", "close", "ending")):
                recommended_image_type = "main_product"
                recommended_video_type = "clean_product_close"
            else:
                recommended_image_type = "usage_benefit"
                recommended_video_type = "benefit_demonstration"

            scene["recommended_image_type"] = recommended_image_type
            scene["recommended_video_type"] = recommended_video_type
            scene["selection_reason"] = (
                f"{scene['story_purpose']} 장면 목표와 "
                f"{scene['evidence_type']} 리뷰 근거에 맞는 "
                f"{recommended_image_type} 이미지 우선"
            )
            scene["director_context"] = {
                "scene_goal": scene["story_goal"],
                "story_purpose": scene["story_purpose"],
                "emotion_stage": scene["emotion_stage"],
                "review_evidence": scene["review_evidence"],
                "evidence_type": scene["evidence_type"],
                "must_show": scene["must_show"],
                "recommended_image_type": recommended_image_type,
                "recommended_video_type": recommended_video_type,
            }
            bridged_scene_count += 1

        scene_plan_result["scenes"] = planned_scenes
        scene_plan_result["story_intelligence_version"] = (
            story_intelligence_result.get("version", "")
        )
        scene_plan_result["story_type"] = story_intelligence_result.get(
            "story_type", ""
        )
        scene_plan_result["product_type"] = story_intelligence_result.get(
            "product_type", ""
        )
        scene_plan_result["story_goal_bridge_count"] = bridged_scene_count
        scene_plan_result["story_goal_bridge_ready"] = bool(
            planned_scenes and bridged_scene_count == len(planned_scenes)
        )

        # Sprint160: 잠금 대본 순서와 광고 역할을 기준으로 장면/카메라/환경을 최종 고정합니다.
        scene_plan_result = self._sprint151_1_apply_scene_director(
            scene_plan_result
        )
        scene_plan_result = self._sprint160_apply_story_director(
            scene_plan_result,
            script_text=approved_script_text,
        )
        scene_plan_result = self._sprint161_apply_reference_identity_continuity(
            scene_plan_result,
            project_id=project_id_for_director,
            output_dir=director_output_dir,
            script_text=approved_script_text,
        )

        print(
            "[Sprint101-3 Scene Goal Bridge] Count:",
            bridged_scene_count,
            "/",
            len(planned_scenes),
            flush=True,
        )
        print(
            "[Sprint101-3 Scene Goal Bridge] Ready:",
            scene_plan_result.get("story_goal_bridge_ready", False),
            flush=True,
        )

        outputs["scene_plan"] = scene_plan_result

        # Sprint129-1: 기존 상품 이미지를 우선해 장면별 전환형 이미지 계획을 만듭니다.
        # 실제 상품 이미지 재사용 및 AI 보완 이미지 생성 계획을 만듭니다.
        scene_image_plan_result = {
            "ok": False,
            "ready": False,
            "version": SceneImagePlanner.VERSION,
            "status": "not_run",
            "scene_count": 0,
            "scenes": [],
            "errors": [],
        }
        try:
            scene_image_plan_result = SceneImagePlanner().build(
                story_result=story_intelligence_result,
                scene_plan=scene_plan_result,
                product_info=story_product_info,
                image_role_result=image_extractor_result,
                output_dir=director_output_dir,
                project_id=project_id_for_director,
                save_result=True,
            )
        except Exception as exc:
            scene_image_plan_result.update(
                status="failed",
                errors=[f"{type(exc).__name__}: {exc}"],
            )
            print(
                "[Sprint129-1 Scene Image Planner] ERROR:",
                repr(exc),
                flush=True,
            )

        outputs["scene_image_plan"] = scene_image_plan_result

        # Sprint135-3: Product Keeper의 동일 상품 잠금 규칙을 모든 생성 장면에 연결합니다.
        product_identity_context = dict(story_product_info or {})
        product_identity_context["product_keeper_version"] = str(
            product_keeper_result.get("version", "") or ""
        )
        product_identity_context["product_identity_id"] = str(
            product_keeper_result.get("product_identity_id", "") or ""
        )
        product_identity_context["product_identity_manifest_path"] = str(
            product_keeper_result.get("manifest_path", "") or ""
        )
        product_identity_context["product_reference_images"] = list(
            product_keeper_result.get("reference_images") or []
        )
        product_identity_context["product_locked_attributes"] = list(
            product_keeper_result.get("locked_attributes") or []
        )
        product_identity_context["product_generation_rules"] = dict(
            product_keeper_result.get("generation_rules") or {}
        )
        product_identity_context["product_verification_policy"] = dict(
            product_keeper_result.get("verification_policy") or {}
        )
        product_identity_context["source_images_are_reference_only"] = bool(
            product_keeper_result.get("reference_policy", {}).get(
                "source_images_are_reference_only",
                True,
            )
        )
        product_identity_context["allow_reference_image_in_final_video"] = bool(
            product_keeper_result.get("reference_policy", {}).get(
                "allow_reference_image_in_final_video",
                False,
            )
        )
        product_identity_context["product_must_remain_unchanged"] = bool(
            product_keeper_result.get("reference_policy", {}).get(
                "product_must_remain_unchanged",
                True,
            )
        )

        scene_product_constraints = []
        for scene_item in list(scene_image_plan_result.get("scenes") or []):
            if not isinstance(scene_item, dict):
                continue
            try:
                constraint = ProductKeeper().build_scene_constraints(
                    product_identity=product_keeper_result,
                    scene=scene_item,
                )
                scene_product_constraints.append(constraint)
                scene_item["product_identity_id"] = constraint.get(
                    "product_identity_id",
                    "",
                )
                scene_item["product_keeper_constraints"] = constraint
            except Exception as exc:
                print(
                    "[Sprint135-3 Product Constraints] ERROR:",
                    repr(exc),
                    flush=True,
                )

        outputs["scene_product_constraints"] = scene_product_constraints
        outputs["product_identity_context"] = product_identity_context

        print(
            "[Sprint135-3 Product Identity] Ready:",
            product_keeper_result.get("ready", False),
            flush=True,
        )
        print(
            "[Sprint135-3 Product Identity] Identity:",
            product_identity_context.get("product_identity_id", ""),
            flush=True,
        )
        print(
            "[Sprint135-3 Product Identity] Scene Constraints:",
            len(scene_product_constraints),
            flush=True,
        )
        print(
            "[Sprint135-3 Product Identity] Reference Only:",
            product_identity_context.get("source_images_are_reference_only", True),
            flush=True,
        )
        print(
            "[Sprint135-3 Product Identity] Final Reference Allowed:",
            product_identity_context.get("allow_reference_image_in_final_video", False),
            flush=True,
        )

        # Sprint142-3: SceneImagePlanner 결과를 광고 연출 Blueprint로 변환합니다.
        # Blueprint 실행 여부를 로그에서 즉시 확인할 수 있도록 START/INPUT/RESULT를 출력합니다.
        # 기존 AIImageDirector는 이미지 프롬프트, 모션 계획, Closed Loop를 계속 담당합니다.
        print(
            "[Sprint142-3 Image Director] START",
            flush=True,
        )
        print(
            "[Sprint142-3 Image Director] Input Scenes:",
            len(list(scene_image_plan_result.get("scenes") or [])),
            flush=True,
        )
        print(
            "[Sprint142-3 Image Director] Product Images:",
            len(list(product_image_paths or [])),
            flush=True,
        )

        try:
            blueprint_output_path = (
                Path(str(director_output_dir)) / "scene_blueprints.json"
            )
            image_director_blueprint_result = ImageDirector().build(
                scenes=list(scene_image_plan_result.get("scenes") or []),
                product_name=product_name_for_director,
                product_context=product_identity_context,
                product_images=list(product_image_paths or []),
                output_path=str(blueprint_output_path),
                aspect_ratio="9:16",
                visual_style="premium_realistic_shopping_ad",
            )

            blueprints = list(
                image_director_blueprint_result.get("blueprints") or []
            )
            blueprint_map = {
                str(item.get("scene_id") or ""): item
                for item in blueprints
                if isinstance(item, dict) and item.get("scene_id")
            }

            attached_count = 0
            for scene_item in list(scene_image_plan_result.get("scenes") or []):
                if not isinstance(scene_item, dict):
                    continue
                scene_id = str(scene_item.get("scene_id") or "")
                blueprint = blueprint_map.get(scene_id)
                if blueprint:
                    scene_item["image_director_blueprint"] = dict(blueprint)
                    attached_count += 1

            # AIImageDirector가 Scene 내부와 product_context 양쪽에서 Blueprint를
            # 안정적으로 찾을 수 있도록 동일 데이터를 명시적으로 연결합니다.
            scene_image_plan_result["image_director_version"] = str(
                image_director_blueprint_result.get("version") or ""
            )
            scene_image_plan_result["image_director_blueprints"] = blueprints
            scene_image_plan_result["image_director_blueprint_count"] = len(
                blueprints
            )
            scene_image_plan_result["image_director_attached_count"] = (
                attached_count
            )

            product_identity_context["image_director_version"] = str(
                image_director_blueprint_result.get("version") or ""
            )
            product_identity_context["scene_blueprints"] = blueprints
            product_identity_context["scene_blueprint_count"] = len(blueprints)

            outputs["scene_image_plan"] = scene_image_plan_result
            outputs["image_director_blueprint"] = (
                image_director_blueprint_result
            )

            print(
                "[Sprint142-3 Image Director] Version:",
                image_director_blueprint_result.get("version", ""),
                flush=True,
            )
            print(
                "[Sprint142-3 Image Director] Status:",
                image_director_blueprint_result.get("status", ""),
                flush=True,
            )
            print(
                "[Sprint142-3 Image Director] Blueprint Count:",
                len(blueprints),
                flush=True,
            )
            print(
                "[Sprint142-3 Image Director] Attached Count:",
                attached_count,
                flush=True,
            )
            print(
                "[Sprint142-3 Image Director] Output:",
                image_director_blueprint_result.get("output_path", ""),
                flush=True,
            )
            print(
                "[Sprint142-3 Image Director] Errors:",
                image_director_blueprint_result.get("errors", []),
                flush=True,
            )
        except Exception as exc:
            image_director_blueprint_result.update(
                status="failed",
                errors=[f"{type(exc).__name__}: {exc}"],
            )
            outputs["image_director_blueprint"] = (
                image_director_blueprint_result
            )
            print(
                "[Sprint142-3 Image Director] ERROR:",
                repr(exc),
                flush=True,
            )

        # Sprint131-3: 장면별 AI 이미지 프롬프트와 모션 계획을 만듭니다.
        # Sprint135-3부터 Product Keeper의 상품 잠금 정보를 product_context로 전달합니다.
        try:
            ai_image_director_result = AIImageDirector().build(
                scene_image_plan=scene_image_plan_result,
                product_name=product_name_for_director,
                product_context=product_identity_context,
                output_dir=director_output_dir,
                project_id=project_id_for_director,
                save_result=True,
            )
        except Exception as exc:
            ai_image_director_result.update(
                status="failed",
                errors=[f"{type(exc).__name__}: {exc}"],
            )
            print(
                "[Sprint131-3 AI Image Director] ERROR:",
                repr(exc),
                flush=True,
            )

        # Sprint150-6: Gemini 생성 전에 Product DNA 형태 잠금을 최종 프롬프트에 강제합니다.
        ai_image_director_result = self._sprint150_6_strengthen_product_dna(
            ai_image_director_result,
            product_identity_context,
        )

        ai_image_director_result = self._sprint151_1_apply_product_dna_2(
            ai_image_director_result,
            product_identity_context,
        )

        ai_image_director_result = self._sprint160_apply_product_dna_lock_3(
            ai_image_director_result,
            product_identity_context,
        )
        ai_image_director_result = self._sprint161_apply_identity_cache_to_director(
            ai_image_director_result,
            product_identity_context,
        )

        # Sprint153-2: 기존 ImageMotion 영상 재사용 시 Gemini/Vision Closed Loop를 호출하지 않습니다.
        if reuse_image_motion_path:
            ai_image_closed_loop_result = {
                "ok": True,
                "ready": True,
                "version": "workflow-ai-image-closed-loop-153-2-reuse-bypass",
                "status": "skipped_reuse_existing_image_motion",
                "generator": {"status": "skipped", "api_called": False},
                "validator": {"status": "skipped", "api_called": False},
                "closed_loop_result": ai_image_director_result,
                "selected_image_count": 0,
                "passed_scene_count": 0,
                "failed_scene_count": 0,
                "reuse_image_motion_path": reuse_image_motion_path,
                "errors": [],
            }
        else:
            ai_image_closed_loop_result = (
                self._run_sprint141_6_ai_image_closed_loop(
                    director_result=ai_image_director_result,
                    output_dir=director_output_dir,
                )
            )
        outputs["ai_image_closed_loop"] = ai_image_closed_loop_result

        closed_loop_director_result = (
            ai_image_closed_loop_result.get("closed_loop_result")
        )
        if (
            isinstance(closed_loop_director_result, dict)
            and closed_loop_director_result.get("scenes")
        ):
            ai_image_director_result = closed_loop_director_result

        ai_image_director_result = self._sprint162_strengthen_continuity_chain(
            ai_image_director_result
        )
        ai_image_director_result = self._sprint162_prepare_flexible_approved_scenes(
            ai_image_director_result,
            minimum_approved_scenes=8,
            target_scene_count=10,
            target_duration_seconds=25.0,
        )
        outputs["ai_image_director"] = ai_image_director_result

        print(
            "[Sprint141-5A Closed Loop] Version:",
            ai_image_closed_loop_result.get("version", ""),
            flush=True,
        )
        print(
            "[Sprint141-5A Closed Loop] Status:",
            ai_image_closed_loop_result.get("status", ""),
            flush=True,
        )
        print(
            "[Sprint141-5A Closed Loop] Generator:",
            ai_image_closed_loop_result.get("generator", {}),
            flush=True,
        )
        print(
            "[Sprint141-5A Closed Loop] Validator:",
            ai_image_closed_loop_result.get("validator", {}),
            flush=True,
        )
        print(
            "[Sprint141-5A Closed Loop] Selected:",
            ai_image_closed_loop_result.get("selected_image_count", 0),
            flush=True,
        )
        print(
            "[Sprint141-5A Closed Loop] Passed:",
            ai_image_closed_loop_result.get("passed_scene_count", 0),
            flush=True,
        )
        print(
            "[Sprint141-5A Closed Loop] Failed:",
            ai_image_closed_loop_result.get("failed_scene_count", 0),
            flush=True,
        )
        print(
            "[Sprint141-5A Closed Loop] Errors:",
            ai_image_closed_loop_result.get("errors", []),
            flush=True,
        )
        print("[Sprint150-6 Vision Closed Loop] Threshold:", 94.0, flush=True)
        print("[Sprint158 Fast Mode] Max Attempts:", 1, flush=True)
        print(
            "[Sprint150-6 Vision Closed Loop] Auto Regeneration:",
            ai_image_closed_loop_result.get("failed_scene_count", 0) == 0,
            flush=True,
        )

        print(
            "[Sprint131-3 AI Image Director] Version:",
            ai_image_director_result.get("version", ""),
            flush=True,
        )
        print(
            "[Sprint131-3 AI Image Director] Status:",
            ai_image_director_result.get("status", ""),
            flush=True,
        )
        print(
            "[Sprint131-3 AI Image Director] AI Images:",
            ai_image_director_result.get("ai_image_scene_count", 0),
            flush=True,
        )
        print(
            "[Sprint131-3 AI Image Director] Existing Images:",
            ai_image_director_result.get("existing_image_scene_count", 0),
            flush=True,
        )
        print(
            "[Sprint131-3 AI Image Director] Motion Scenes:",
            ai_image_director_result.get("motion_scene_count", 0),
            flush=True,
        )
        print(
            "[Sprint131-3 AI Image Director] Motions:",
            [
                item.get("recommended_motion")
                for item in list(ai_image_director_result.get("motion_plan") or [])
                if isinstance(item, dict) and item.get("recommended_motion")
            ],
            flush=True,
        )
        print(
            "[Sprint131-3 AI Image Director] Prompt Internal Only:",
            all(
                bool(item.get("prompt_internal_only"))
                for item in list(ai_image_director_result.get("image_prompts") or [])
                if isinstance(item, dict)
            ),
            flush=True,
        )

        print(
            "[Sprint129-1 Scene Image Planner] Ready:",
            scene_image_plan_result.get("ready", False),
            flush=True,
        )
        print(
            "[Sprint129-1 Scene Image Planner] AI Images:",
            scene_image_plan_result.get("generated_scene_count", 0),
            flush=True,
        )
        print(
            "[Sprint129-1 Scene Image Planner] Product Images:",
            scene_image_plan_result.get("product_image_scene_count", 0),
            flush=True,
        )
        print(
            "[Sprint129-1 Scene Image Planner] Errors:",
            scene_image_plan_result.get("errors", []),
            flush=True,
        )

        # Sprint147-1: 최초 원클릭에서는 장면별 AI 이미지 생성까지만 실행하고
        # 사용자의 승인/재생성을 기다립니다. 승인된 이미지로 다시 실행할 때만
        # Image Motion, 자막, 최종 영상 단계로 진행합니다.
        print(
            "[Sprint147-7 HARD GATE REACHED]",
            {
                "requested": image_generation_only_requested,
                "prompt_count": len(list(ai_image_director_result.get("image_prompts") or [])),
                "director_status": str(ai_image_director_result.get("status") or ""),
                "closed_loop_status": str(ai_image_closed_loop_result.get("status") or ""),
            },
            flush=True,
        )
        if image_generation_only_requested:
            director_cost_guard = (
                ai_image_closed_loop_result.get("closed_loop_result", {}).get("cost_guard", {})
                if isinstance(ai_image_closed_loop_result.get("closed_loop_result"), dict)
                else {}
            )
            if isinstance(director_cost_guard, dict) and director_cost_guard.get("fatal_stop"):
                outputs["image_review"] = {
                    "ok": False,
                    "ready": False,
                    "version": "ai-image-review-gate-158",
                    "status": "FATAL_PROVIDER_ERROR",
                    "project_id": str(project_id_for_director or ""),
                    "scene_count": 0,
                    "scenes": [],
                    "all_approved": False,
                    "generation_errors": [
                        str(director_cost_guard.get("fatal_error_code") or "fatal_provider_error")
                    ],
                    "cost_guard": director_cost_guard,
                }
                outputs["next_stage_gate"] = {
                    "version": "ai-image-review-gate-158",
                    "status": "STOPPED_BY_COST_GUARD",
                    "scene_image_motion_video_executed": False,
                    "reason": "치명적 Gemini 오류로 모든 후속 이미지 호출을 중단했습니다.",
                }
                print(
                    "[Sprint158 Fast Mode] HARD GATE FATAL STOP:",
                    director_cost_guard,
                    flush=True,
                )
                return {
                    "job_id": uuid4().hex[:12],
                    "state": {},
                    "outputs": outputs,
                    "summary": "Gemini 오류로 이미지 생성을 즉시 중단했습니다.",
                    "script_status": "APPROVED",
                    "next_stage_status": "STOPPED_BY_COST_GUARD",
                }

            print("[Sprint147-7 HARD GATE ENTERED]", flush=True)
            closed_loop_payload = (
                ai_image_closed_loop_result.get("closed_loop_result", {})
                if isinstance(ai_image_closed_loop_result.get("closed_loop_result"), dict)
                else {}
            )
            generation_runs = [
                dict(item)
                for item in list(closed_loop_payload.get("generation_runs") or [])
                if isinstance(item, dict)
            ]
            image_review_scenes = []
            prompt_map = {
                str(item.get("scene_id") or ""): dict(item)
                for item in list(ai_image_director_result.get("image_prompts") or [])
                if isinstance(item, dict)
            }
            scene_map = {
                str(item.get("scene_id") or ""): dict(item)
                for item in list(scene_plan_result.get("scenes") or [])
                if isinstance(item, dict)
            }

            # Sprint147-3: Closed Loop 결과가 비어 있어도 장면당 1장 생성은 반드시 시도합니다.
            usable_run_ids = {
                str(item.get("scene_id") or "")
                for item in generation_runs
                if str(item.get("selected_image_path") or item.get("generated_image_path") or "").strip()
            }
            direct_generation_errors = []
            direct_output_dir = Path(str(director_output_dir or ".")) / "generated_review"
            direct_output_dir.mkdir(parents=True, exist_ok=True)
            for prompt_index, prompt_item in enumerate(list(ai_image_director_result.get("image_prompts") or []), start=1):
                if not isinstance(prompt_item, dict):
                    continue
                scene_id = str(prompt_item.get("scene_id") or f"scene_{prompt_index:02d}")
                if scene_id in usable_run_ids:
                    continue
                existing_path = str(prompt_item.get("selected_image_path") or prompt_item.get("existing_image_path") or "").strip()
                if existing_path and Path(existing_path).is_file():
                    generation_runs.append({
                        "scene_id": scene_id,
                        "selected_image_path": existing_path,
                        "generated_image_path": existing_path,
                        "passed": True,
                        "attempt_count": 1,
                        "source": "existing_product_image",
                    })
                    usable_run_ids.add(scene_id)
                    continue
                try:
                    generated_path = self._sprint147_3_generate_one_image(
                        prompt_item,
                        direct_output_dir / f"{scene_id}_attempt_01.png",
                    )
                except Exception as exc:
                    direct_generation_errors.append(f"{scene_id}: {type(exc).__name__}: {exc}")
                    print("[Sprint147-6 Direct Image] FAILED:", scene_id, repr(exc), flush=True)
                else:
                    generation_runs.append({
                        "scene_id": scene_id,
                        "selected_image_path": generated_path,
                        "generated_image_path": generated_path,
                        "passed": True,
                        "attempt_count": 1,
                        "source": "direct_single_generation",
                    })
                    usable_run_ids.add(scene_id)
                    print("[Sprint147-6 Direct Image] GENERATED:", scene_id, generated_path, flush=True)

            for index, run_item in enumerate(generation_runs, start=1):
                scene_id = str(run_item.get("scene_id") or f"scene_{index:02d}")
                prompt_item = prompt_map.get(scene_id, {})
                scene_item = scene_map.get(scene_id, {})
                selected_path = str(
                    run_item.get("selected_image_path")
                    or run_item.get("generated_image_path")
                    or prompt_item.get("selected_image_path")
                    or ""
                )
                image_review_scenes.append({
                    "scene_id": scene_id,
                    "scene_index": int(scene_item.get("scene_index") or index),
                    "subtitle_text": str(
                        scene_item.get("subtitle_text")
                        or scene_item.get("dialogue")
                        or ""
                    ),
                    "prompt": str(
                        prompt_item.get("prompt")
                        or prompt_item.get("image_prompt")
                        or run_item.get("prompt")
                        or ""
                    ),
                    "negative_prompt": str(
                        prompt_item.get("negative_prompt")
                        or run_item.get("negative_prompt")
                        or ""
                    ),
                    "reference_image_path": str(
                        prompt_item.get("reference_image_path")
                        or run_item.get("reference_image_path")
                        or ""
                    ),
                    "image_path": selected_path,
                    "passed": bool(run_item.get("passed")),
                    "attempt_count": int(run_item.get("attempt_count") or run_item.get("attempt") or 1),
                })

            outputs["image_review"] = {
                "ok": bool(image_review_scenes),
                "ready": bool(image_review_scenes),
                "version": "ai-image-review-gate-147-6",
                "status": "WAITING_USER_APPROVAL" if image_review_scenes else "NO_GENERATED_IMAGES",
                "project_id": str(project_id_for_director or ""),
                "scene_count": len(image_review_scenes),
                "scenes": image_review_scenes,
                "all_approved": False,
                "generation_errors": direct_generation_errors,
                "closed_loop_status": str(ai_image_closed_loop_result.get("status") or ""),
                "director_status": str(ai_image_director_result.get("status") or ""),
            }
            outputs["next_stage_gate"] = {
                "version": "ai-image-review-gate-147-6",
                "status": "WAITING_IMAGE_APPROVAL",
                "scene_image_motion_video_executed": False,
                "reason": "장면별 이미지를 확인한 뒤 승인된 이미지로 최종 영상을 제작합니다.",
            }
            print("[Sprint147-6 Image Review] Status: WAITING_IMAGE_APPROVAL", flush=True)
            print("[Sprint147-6 Image Review] Scene Count:", len(image_review_scenes), flush=True)
            print("[Sprint147-6 Image Review] Video Executed: False", flush=True)
            return {
                "job_id": uuid4().hex[:12],
                "state": {},
                "outputs": outputs,
                "summary": "장면별 AI 이미지 생성 완료 - 사용자 승인 대기",
                "script_status": "APPROVED",
                "next_stage_status": "WAITING_IMAGE_APPROVAL",
            }

        # Sprint124-3A: Scene Planner가 만든 자막 타임라인을 영상 생성과 분리해 보존합니다.
        # Sprint146-12: 실제 scene_plan_result를 기준으로 공통 장면 목록을 동기화합니다.
        # 일반 경로와 잠금 대본 우회 경로 모두 이 지점부터 동일한 값을 사용합니다.
        planned_scenes = list(scene_plan_result.get("scenes", []) or [])
        print(
            "[Sprint146-12 Planned Scenes] Count:",
            len(planned_scenes),
            flush=True,
        )
        scene_subtitle_plan = [
            dict(item)
            for item in list(scene_plan_result.get("subtitle_plan") or [])
            if isinstance(item, dict) and str(item.get("text") or "").strip()
        ]
        scene_subtitle_result = {
            "ok": bool(scene_subtitle_plan),
            "ready": bool(scene_subtitle_plan),
            "version": "scene-subtitle-workflow-124-5",
            "status": "ready" if scene_subtitle_plan else "empty",
            "project_id": str(project_id_for_director or ""),
            "scene_count": len(planned_scenes),
            "subtitle_count": len(scene_subtitle_plan),
            "total_duration_seconds": round(
                max(
                    [float(item.get("end") or 0.0) for item in scene_subtitle_plan]
                    or [0.0]
                ),
                2,
            ),
            "items": scene_subtitle_plan,
            "source_scene_plan_version": str(scene_plan_result.get("version") or ""),
            "render_policy": "post_process_after_video_generation",
            "video_prompt_contains_subtitles": False,
            "errors": [],
        }
        outputs["scene_subtitles"] = scene_subtitle_result
        outputs["subtitle_plan"] = scene_subtitle_result

        print(
            "[Sprint124-3A Scene Subtitle] Ready:",
            scene_subtitle_result.get("ready", False),
            flush=True,
        )
        print(
            "[Sprint124-3A Scene Subtitle] Count:",
            scene_subtitle_result.get("subtitle_count", 0),
            flush=True,
        )
        print(
            "[Sprint124-3A Scene Subtitle] Duration:",
            scene_subtitle_result.get("total_duration_seconds", 0.0),
            flush=True,
        )
        for subtitle_item in scene_subtitle_plan:
            print(
                "[Sprint124-3A Scene Subtitle]",
                subtitle_item.get("scene_id", ""),
                f"{float(subtitle_item.get('start') or 0.0):.2f}-{float(subtitle_item.get('end') or 0.0):.2f}",
                "|",
                subtitle_item.get("text", ""),
                "| emphasis=",
                subtitle_item.get("emphasis_words", []),
                flush=True,
            )

        print(
            "[Sprint124-3A Script First] Planning Mode:",
            scene_plan_result.get("planning_mode", ""),
            flush=True,
        )
        print(
            "[Sprint124-3A Script First] Script Lines:",
            scene_plan_result.get("script_line_count", 0),
            flush=True,
        )
        print(
            "[Sprint93-4 Scene Planner] Version:",
            scene_plan_result.get("version", ""),
            flush=True,
        )
        print(
            "[Sprint93-4 Scene Planner] Status:",
            scene_plan_result.get("status", ""),
            flush=True,
        )
        print(
            "[Sprint93-4 Scene Planner] Count:",
            len(scene_plan_result.get("scenes", []) or []),
            flush=True,
        )
        print(
            "[Sprint93-4 Scene Planner] Errors:",
            scene_plan_result.get("errors", []),
            flush=True,
        )

        # Sprint129-2: 기존 Scene Planner가 장면을 만들지 못했더라도
        # Scene Image Planner가 만든 장면과 기존 상품 이미지로 Director 입력을 복구합니다.
        planner_fallback_scenes = [
            item for item in list(scene_image_plan_result.get("scenes") or [])
            if isinstance(item, dict)
            and str(item.get("scene_id") or "").strip()
            and str(item.get("selected_existing_image_path") or "").strip()
        ]
        if not list(scene_plan_result.get("scenes") or []) and planner_fallback_scenes:
            fallback_selection_scenes = []
            for fallback_index, planner_item in enumerate(planner_fallback_scenes, start=1):
                image_path = str(planner_item.get("selected_existing_image_path") or "").strip()
                purpose = str(planner_item.get("purpose") or "feature").strip().lower()
                fallback_selection_scenes.append({
                    "scene_id": str(planner_item.get("scene_id") or f"scene_{fallback_index:02d}"),
                    "scene_index": fallback_index,
                    "scene_type": purpose,
                    "title": str(planner_item.get("visual_goal") or purpose),
                    "purpose": str(planner_item.get("visual_goal") or ""),
                    "story_purpose": purpose,
                    "story_goal": str(planner_item.get("story_goal") or ""),
                    "primary_selling_point": str(planner_item.get("primary_selling_point") or ""),
                    "review_evidence": str(planner_item.get("review_evidence") or ""),
                    "must_show": str(planner_item.get("visual_goal") or ""),
                    "dialogue": str(planner_item.get("subtitle") or ""),
                    "selected_image_path": image_path,
                    "selected_image_filename": Path(image_path).name,
                    "selection_status": "selected",
                    "matched_roles": [str(planner_item.get("matched_existing_role") or "unknown")],
                    "matched_tags": [],
                    "match_score": 100.0,
                    "duration_seconds": 6.0,
                    "motion": str(planner_item.get("motion") or "static_hold"),
                    "transition": "cut",
                    "director_context": {
                        "scene_goal": str(planner_item.get("story_goal") or ""),
                        "scene_purpose": purpose,
                        "primary_selling_point": str(planner_item.get("primary_selling_point") or ""),
                        "review_evidence": str(planner_item.get("review_evidence") or ""),
                        "must_show": str(planner_item.get("visual_goal") or ""),
                    },
                })

            scene_selection_result = {
                "ok": bool(fallback_selection_scenes),
                "ready": bool(fallback_selection_scenes),
                "version": "scene-image-selector-129-2-fallback",
                "status": "selected_from_scene_image_plan",
                "project_id": str(project_id_for_director or ""),
                "product_name": str(product_name_for_director or ""),
                "scene_plan_path": str(scene_image_plan_result.get("plan_path") or ""),
                "image_tags_path": str(image_tags_result.get("tag_manifest_path") or ""),
                "output_dir": str(director_output_dir or ""),
                "scene_selection_path": "",
                "scene_count": len(fallback_selection_scenes),
                "selected_count": len(fallback_selection_scenes),
                "unselected_count": 0,
                "scenes": fallback_selection_scenes,
                "summary": {"fallback_source": "scene_image_plan"},
                "warnings": ["기존 Scene Planner 장면이 없어 Scene Image Planner 결과로 복구했습니다"],
                "errors": [],
                "elapsed_seconds": 0.0,
                "total_reference_image_count": len(fallback_selection_scenes),
            }
            print(
                "[Sprint129-2 Scene Selection Fallback] Count:",
                len(fallback_selection_scenes),
                flush=True,
            )
        else:
            try:
                scene_selection_result = SceneImageSelector().select(
                    scene_plan=scene_plan_result,
                    scene_plan_path=scene_plan_result.get(
                        "scene_plan_path",
                        "",
                    ),
                    tag_result=image_tags_result,
                    image_tags_path=image_tags_result.get(
                        "tag_manifest_path",
                        "",
                    ),
                    output_dir=director_output_dir,
                    project_id=project_id_for_director,
                    product_name=product_name_for_director,
                    save_result=True,
                )
            except Exception as exc:
                scene_selection_result.update(
                    status="failed",
                    errors=[f"{type(exc).__name__}: {exc}"],
                )

        # Sprint102-2: Story 장면 목적에 맞춰 Image Pool 후보를 최종 참조 이미지로 연결합니다.
        pool_by_type = (
            image_pool_result.get("image_pool", {})
            if isinstance(image_pool_result, dict)
            else {}
        )
        pool_scene_map = {
            "main_product": ("hero", "cta", "feature"),
            "problem_context": ("comparison", "usage", "review"),
            "detail_proof": ("detail", "feature", "review"),
            "usage_benefit": ("usage", "feature", "detail"),
        }
        pool_selected_paths = set()
        pool_bridge_items = []
        raw_selection_scenes = list(
            scene_selection_result.get("scenes", []) or []
        )
        planned_for_pool = list(scene_plan_result.get("scenes", []) or [])

        for pool_index, selected_scene in enumerate(raw_selection_scenes):
            if not isinstance(selected_scene, dict):
                continue

            planned_scene = (
                planned_for_pool[pool_index]
                if pool_index < len(planned_for_pool)
                and isinstance(planned_for_pool[pool_index], dict)
                else {}
            )
            recommended_type = str(
                planned_scene.get("recommended_image_type")
                or selected_scene.get("recommended_image_type")
                or "usage_benefit"
            ).strip()
            preferred_pools = pool_scene_map.get(
                recommended_type,
                ("usage", "feature", "detail"),
            )

            pool_candidates = []
            seen_candidate_paths = set()
            for pool_name in preferred_pools:
                for candidate in list(pool_by_type.get(pool_name, []) or []):
                    if not isinstance(candidate, dict):
                        continue
                    candidate_path = str(candidate.get("path") or "").strip()
                    if not candidate_path or candidate_path in seen_candidate_paths:
                        continue
                    if not Path(candidate_path).is_file():
                        continue
                    seen_candidate_paths.add(candidate_path)
                    copied_candidate = dict(candidate)
                    copied_candidate["pool_type"] = pool_name
                    pool_candidates.append(copied_candidate)

            allow_reuse = any(
                token in str(planned_scene.get("story_purpose") or "").lower()
                for token in ("hook", "intro", "cta", "close", "ending")
            )
            if not allow_reuse:
                unused_candidates = [
                    item for item in pool_candidates
                    if str(item.get("path") or "") not in pool_selected_paths
                ]
                if unused_candidates:
                    pool_candidates = unused_candidates

            chosen = pool_candidates[:4]
            chosen_paths = [
                str(item.get("path") or "").strip()
                for item in chosen
                if str(item.get("path") or "").strip()
            ]

            if chosen_paths:
                primary = chosen[0]
                selected_scene["selected_image_path"] = chosen_paths[0]
                selected_scene["selected_image_paths"] = chosen_paths
                selected_scene["primary_reference_image"] = chosen_paths[0]
                selected_scene["reference_images"] = chosen_paths
                selected_scene["reference_image_count"] = len(chosen_paths)
                selected_scene["selected_image_filename"] = Path(chosen_paths[0]).name
                selected_scene["selected_reference_images"] = chosen
                selected_scene["image_pool_type"] = primary.get("pool_type", "")
                selected_scene["image_pool_score"] = primary.get("score", 0)
                selected_scene["image_pool_reason"] = primary.get("reason", "")
                selected_scene["image_pool_bridge_status"] = "applied"
                selected_scene["selection_status"] = "selected"
                selected_scene["selection_reason"] = (
                    f"Sprint102 Image Pool {primary.get('pool_type', '')} 우선 선택 | "
                    f"{primary.get('reason', '')}"
                )
                if not allow_reuse:
                    pool_selected_paths.add(chosen_paths[0])
            else:
                selected_scene["image_pool_bridge_status"] = "fallback_existing_selection"

            pool_bridge_items.append({
                "scene_id": str(selected_scene.get("scene_id") or f"scene_{pool_index + 1:02d}"),
                "recommended_image_type": recommended_type,
                "preferred_pools": list(preferred_pools),
                "status": selected_scene.get("image_pool_bridge_status", ""),
                "selected_path": str(selected_scene.get("selected_image_path") or ""),
                "reference_count": len(selected_scene.get("selected_image_paths") or []),
                "pool_type": str(selected_scene.get("image_pool_type") or ""),
            })

        scene_selection_result["scenes"] = raw_selection_scenes
        scene_selection_result["image_pool_bridge"] = {
            "version": "image-pool-scene-bridge-102-2",
            "ready": bool(raw_selection_scenes) and all(
                str(item.get("selected_image_path") or "").strip()
                for item in raw_selection_scenes
                if isinstance(item, dict)
            ),
            "scene_count": len(raw_selection_scenes),
            "applied_count": sum(
                1 for item in raw_selection_scenes
                if isinstance(item, dict)
                and item.get("image_pool_bridge_status") == "applied"
            ),
            "unique_primary_count": len(pool_selected_paths),
            "items": pool_bridge_items,
        }
        scene_selection_result["total_reference_image_count"] = sum(
            len(item.get("selected_image_paths") or [])
            for item in raw_selection_scenes
            if isinstance(item, dict)
        )

        selection_path_for_pool = str(
            scene_selection_result.get("scene_selection_path") or ""
        ).strip()
        if selection_path_for_pool:
            try:
                Path(selection_path_for_pool).write_text(
                    json.dumps(
                        scene_selection_result,
                        ensure_ascii=False,
                        indent=2,
                        default=str,
                    ),
                    encoding="utf-8",
                )
            except Exception as exc:
                scene_selection_result.setdefault("warnings", []).append(
                    f"Sprint102 Image Pool selection save failed: "
                    f"{type(exc).__name__}: {exc}"
                )

        print(
            "[Sprint102-2 Image Pool Bridge] Ready:",
            scene_selection_result.get("image_pool_bridge", {}).get("ready", False),
            flush=True,
        )
        print(
            "[Sprint102-2 Image Pool Bridge] Applied:",
            scene_selection_result.get("image_pool_bridge", {}).get("applied_count", 0),
            "/",
            scene_selection_result.get("image_pool_bridge", {}).get("scene_count", 0),
            flush=True,
        )
        print(
            "[Sprint102-2 Image Pool Bridge] Unique Primary:",
            scene_selection_result.get("image_pool_bridge", {}).get("unique_primary_count", 0),
            flush=True,
        )
        for bridge_item in pool_bridge_items:
            print(
                "[Sprint102-2 Pool Scene]",
                bridge_item.get("scene_id", ""),
                "->",
                bridge_item.get("pool_type", "fallback"),
                "| refs=",
                bridge_item.get("reference_count", 0),
                "|",
                bridge_item.get("selected_path", ""),
                flush=True,
            )

        # Sprint101-3: Scene Image Selector 결과에 Story/Evidence 연출 문맥을 주입합니다.
        selection_items = []
        selection_key = ""
        for candidate_key in ("scenes", "selections", "selected_scenes", "items"):
            candidate_items = scene_selection_result.get(candidate_key)
            if isinstance(candidate_items, list):
                selection_items = candidate_items
                selection_key = candidate_key
                break

        director_context_count = 0
        planned_scene_lookup = list(scene_plan_result.get("scenes", []) or [])
        for index, selected_scene in enumerate(selection_items):
            if not isinstance(selected_scene, dict) or index >= len(planned_scene_lookup):
                continue
            planned_scene = planned_scene_lookup[index]
            if not isinstance(planned_scene, dict):
                continue

            context = dict(planned_scene.get("director_context") or {})
            selected_scene["story_goal"] = planned_scene.get("story_goal", "")
            selected_scene["story_purpose"] = planned_scene.get("story_purpose", "")
            selected_scene["emotion_stage"] = planned_scene.get("emotion_stage", "")
            selected_scene["review_evidence"] = planned_scene.get("review_evidence", "")
            selected_scene["evidence_type"] = planned_scene.get("evidence_type", "")
            selected_scene["must_show"] = planned_scene.get("must_show", "")
            selected_scene["recommended_image_type"] = planned_scene.get(
                "recommended_image_type", ""
            )
            selected_scene["recommended_video_type"] = planned_scene.get(
                "recommended_video_type", ""
            )
            selected_scene["director_context"] = context
            director_context_count += 1

        if selection_key:
            scene_selection_result[selection_key] = selection_items
        scene_selection_result["story_director_bridge"] = {
            "version": "story-director-bridge-101-3",
            "selection_key": selection_key,
            "scene_count": len(selection_items),
            "context_count": director_context_count,
            "ready": bool(selection_items and director_context_count == len(selection_items)),
        }

        outputs["scene_selection"] = scene_selection_result
        print(
            "[Sprint101-3 Story Director Bridge] Context:",
            director_context_count,
            "/",
            len(selection_items),
            flush=True,
        )
        print(
            "[Sprint101-3 Story Director Bridge] Ready:",
            scene_selection_result.get("story_director_bridge", {}).get("ready", False),
            flush=True,
        )
        for index, selected_scene in enumerate(selection_items, start=1):
            if not isinstance(selected_scene, dict):
                continue
            print(
                f"[Sprint101-3 Director Scene] Scene{index:02d}",
                "->",
                selected_scene.get("recommended_video_type", ""),
                "|",
                str(selected_scene.get("must_show", ""))[:80],
                flush=True,
            )

        print(
            "[Sprint93-5 Scene Image Selector] Version:",
            scene_selection_result.get("version", ""),
            flush=True,
        )
        print(
            "[Sprint93-5 Scene Image Selector] Status:",
            scene_selection_result.get("status", ""),
            flush=True,
        )
        print(
            "[Sprint93-5 Scene Image Selector] Count:",
            scene_selection_result.get("selected_count", 0),
            flush=True,
        )
        print(
            "[Sprint93-5 Scene Image Selector] Errors:",
            scene_selection_result.get("errors", []),
            flush=True,
        )

        # Sprint129-1: Scene Image Planner의 목적·우선 이미지·전환 정보를
        # Gemini Director 입력 장면에 연결합니다. 기존 Selector 결과는 유지하고,
        # 선택 경로가 비어 있을 때만 Planner의 안전한 상품 이미지로 보완합니다.
        planner_scene_index = {
            str(item.get("scene_id") or ""): item
            for item in list(scene_image_plan_result.get("scenes") or [])
            if isinstance(item, dict) and str(item.get("scene_id") or "").strip()
        }
        planner_bridge_count = 0
        for selected_scene in list(scene_selection_result.get("scenes") or []):
            if not isinstance(selected_scene, dict):
                continue
            planner_scene = planner_scene_index.get(str(selected_scene.get("scene_id") or ""))
            if not planner_scene:
                continue
            selected_scene["story_purpose"] = planner_scene.get("purpose", selected_scene.get("story_purpose", ""))
            selected_scene["story_goal"] = planner_scene.get("story_goal", selected_scene.get("story_goal", ""))
            selected_scene["must_show"] = planner_scene.get("visual_goal", selected_scene.get("must_show", ""))
            selected_scene["primary_selling_point"] = planner_scene.get("primary_selling_point", selected_scene.get("primary_selling_point", ""))
            selected_scene["review_evidence"] = planner_scene.get("review_evidence", selected_scene.get("review_evidence", ""))
            selected_scene["planner_visual_source"] = planner_scene.get("visual_source", "")
            selected_scene["planner_matched_role"] = planner_scene.get("matched_existing_role", "")
            fallback_image = str(planner_scene.get("selected_existing_image_path") or "").strip()
            if not str(selected_scene.get("selected_image_path") or "").strip() and fallback_image:
                selected_scene["selected_image_path"] = fallback_image
                selected_scene["selected_image_filename"] = Path(fallback_image).name
                selected_scene["selection_status"] = "selected"
            planner_bridge_count += 1

        scene_selection_result["scene_image_planner_bridge_count"] = planner_bridge_count
        print("[Sprint129-1 Planner Director Bridge] Count:", planner_bridge_count, flush=True)

        # Sprint130-1: Gemini/Veo Director는 기본 원클릭 경로에서 우회합니다.
        # AI 이미지 프롬프트는 ai_image_manifest.json에만 저장하고 영상 프롬프트로 변환하지 않습니다.
        gemini_director_result.update(
            status="bypassed_ai_image_pipeline",
            api_called=False,
            skip_reason="Sprint130-1 uses AIImageDirector instead of Gemini/Veo Director",
        )
        outputs["gemini_director"] = gemini_director_result

        ai_manifest_path = Path(director_output_dir) / "ai_image_manifest.json"
        try:
            ai_manifest_scenes = []
            for item in list(ai_image_director_result.get("scenes") or []):
                if not isinstance(item, dict):
                    continue
                ai_manifest_scenes.append({
                    "scene_id": str(item.get("scene_id") or ""),
                    "scene_index": int(item.get("scene_index") or 0),
                    "purpose": str(item.get("purpose") or ""),
                    "source_type": str(item.get("source_type") or ""),
                    "generation_required": bool(item.get("generation_required")),
                    "resolved_image_path": str(item.get("resolved_image_path") or ""),
                    "reference_image_path": str(item.get("reference_image_path") or ""),
                    "output_image_path": str(item.get("output_image_path") or ""),
                    "image_prompt": str(item.get("image_prompt") or ""),
                    "negative_prompt": str(item.get("negative_prompt") or ""),
                    "prompt_internal_only": True,
                    "motion_input_allowed": bool(item.get("motion_input_allowed")),
                    "recommended_motion": str(item.get("recommended_motion") or ""),
                    "motion_speed": str(item.get("motion_speed") or ""),
                    "motion_reason": str(item.get("motion_reason") or ""),
                    "camera_style": str(item.get("camera_style") or ""),
                    "motion_source": str(item.get("motion_source") or ""),
                })

            ai_manifest_payload = {
                "ok": bool(ai_image_director_result.get("ok")),
                "ready": bool(ai_image_director_result.get("ok")),
                "version": "ai-image-manifest-131-3",
                "status": str(ai_image_director_result.get("status") or "not_ready"),
                "project_id": str(project_id_for_director or ""),
                "product_name": str(product_name_for_director or ""),
                "pipeline": "existing_product_images_plus_missing_scene_ai_images",
                "video_generation_enabled": False,
                "veo_api_called": False,
                "prompt_usage": "image_generation_api_only",
                "scene_count": len(ai_manifest_scenes),
                "ai_image_scene_count": int(ai_image_director_result.get("ai_image_scene_count") or 0),
                "existing_image_scene_count": int(ai_image_director_result.get("existing_image_scene_count") or 0),
                "motion_scene_count": int(ai_image_director_result.get("motion_scene_count") or 0),
                "motion_plan": list(ai_image_director_result.get("motion_plan") or []),
                "scenes": ai_manifest_scenes,
            }
            ai_manifest_path.parent.mkdir(parents=True, exist_ok=True)
            ai_manifest_path.write_text(
                json.dumps(
                    ai_manifest_payload,
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                ),
                encoding="utf-8",
            )
            director_manifest_result = {
                "ok": bool(ai_manifest_payload.get("ok")),
                "ready": bool(ai_manifest_payload.get("ready")),
                "version": "ai-image-manifest-writer-131-3",
                "status": "saved" if ai_manifest_payload.get("ok") else "saved_not_ready",
                "manifest_path": str(ai_manifest_path),
                "manifest": ai_manifest_payload,
                "errors": [],
            }
        except Exception as exc:
            director_manifest_result.update(
                status="failed",
                manifest_path=str(ai_manifest_path),
                errors=[f"{type(exc).__name__}: {exc}"],
            )

        outputs["director_manifest"] = director_manifest_result
        print(
            "[Sprint93-6B Director Manifest] Version:",
            director_manifest_result.get("version", ""),
            flush=True,
        )
        print(
            "[Sprint93-6B Director Manifest] Status:",
            director_manifest_result.get("status", ""),
            flush=True,
        )
        print(
            "[Sprint93-6B Director Manifest] Path:",
            director_manifest_result.get("manifest_path", ""),
            flush=True,
        )
        print(
            "[Sprint93-6B Director Manifest] Errors:",
            director_manifest_result.get("errors", []),
            flush=True,
        )

        # Sprint131-4: Planning Only를 완전히 제거하고 AIImageDirector의 motion_plan을 ImageMotionGenerator로 전달합니다.
        # AI 보완 이미지가 아직 생성되지 않은 장면은 제외하고, 실제 상품 이미지가 있는 장면만 렌더합니다.
        scene_video_result.update(
            ok=False,
            ready=False,
            status="not_run",
            generated_scene_count=0,
            failed_scene_count=0,
            generated_files=[],
            errors=[],
            warnings=[],
            render_requested=True,
            api_called=False,
        )
        scene_merge_result.update(
            ok=False,
            ready=False,
            status="not_run",
            output_path="",
            errors=[],
            render_requested=True,
        )

        motion_render_dir = Path(director_output_dir) / "image_motion_scenes"
        motion_render_dir.mkdir(parents=True, exist_ok=True)
        motion_output_path = (
            Path("exports")
            / "videos"
            / f"{project_id_for_director}_image_motion.mp4"
        )
        motion_output_path.parent.mkdir(parents=True, exist_ok=True)
        if reuse_image_motion_path:
            motion_output_path = Path(reuse_image_motion_path)

        # Sprint131-7: AI Director가 일부 이미지만 선택해도 이번 실행에서 업로드한
        # 전체 상품 이미지를 장면 순서대로 직접 배정합니다.
        # - Director가 선택한 2장 반복 제거
        # - 업로드 이미지 전체 사용
        # - Director 장면 수보다 이미지가 많으면 장면을 확장해 모든 이미지를 사용
        # - 이미지가 장면 수보다 적을 때만 순환 배정
        director_motion_scenes = [
            item
            for item in list(ai_image_director_result.get("scenes") or [])
            if isinstance(item, dict)
        ]
        director_motion_plan = [
            item
            for item in list(ai_image_director_result.get("motion_plan") or [])
            if isinstance(item, dict)
        ]

        # Sprint146-7: 대본과 함께 넣은 장면별 이미지는 최종 렌더 소스입니다.
        # AI Director 결과는 모션 참고만 허용하고 이미지 자체는 교체하지 않습니다.
        if scene_image_direct_mode:
            director_motion_scenes = []
            print("[Sprint146-7 Scene Image Direct] AI image replacement: BYPASSED", flush=True)

        fresh_product_images = []
        fresh_seen_paths = set()
        for image_value in list(manual_product_image_paths or []):
            image_object = Path(str(image_value or ""))
            if not image_object.is_file():
                continue
            try:
                image_key = str(image_object.resolve()).lower()
            except Exception:
                image_key = str(image_object).replace("\\", "/").lower()
            if image_key in fresh_seen_paths:
                continue
            fresh_seen_paths.add(image_key)
            fresh_product_images.append(str(image_object))

        default_motions = (
            "slow_zoom_in",
            "pan_left_to_right",
            "slow_zoom_out",
            "pan_right_to_left",
            "micro_zoom",
            "strong_push_in",
        )

        # Sprint136-1:
        # AI Director가 지나치게 slow 위주로 모션 속도를 선택하더라도
        # 장면 목적에 맞는 쇼츠용 속도 분포를 최종 렌더 계획에 적용합니다.
        # hook / feature / proof는 fast,
        # pain / usage / comparison은 medium,
        # cta는 slow를 기본값으로 사용합니다.
        planned_motion_source_scenes = [
            item
            for item in list(scene_plan_result.get("scenes") or [])
            if isinstance(item, dict)
        ]

        def resolve_motion_purpose(
            scene_index_value,
            director_scene_value,
            director_plan_value,
        ):
            planner_scene_value = (
                planned_motion_source_scenes[scene_index_value]
                if scene_index_value < len(planned_motion_source_scenes)
                else {}
            )
            raw_purpose_value = str(
                director_scene_value.get("purpose")
                or director_scene_value.get("story_purpose")
                or director_scene_value.get("scene_purpose")
                or director_scene_value.get("role")
                or director_plan_value.get("purpose")
                or director_plan_value.get("story_purpose")
                or director_plan_value.get("scene_purpose")
                or director_plan_value.get("role")
                or planner_scene_value.get("purpose")
                or planner_scene_value.get("story_purpose")
                or planner_scene_value.get("scene_purpose")
                or planner_scene_value.get("role")
                or ""
            ).strip().lower()

            purpose_aliases = {
                "intro": "hook",
                "opening": "hook",
                "problem": "pain",
                "empathy": "pain",
                "benefit": "feature",
                "solution": "feature",
                "demonstration": "usage",
                "demo": "usage",
                "evidence": "proof",
                "trust": "proof",
                "compare": "comparison",
                "ending": "cta",
                "close": "cta",
            }
            return purpose_aliases.get(raw_purpose_value, raw_purpose_value)

        def resolve_motion_speed(
            scene_index_value,
            scene_purpose_value,
            requested_speed_value,
        ):
            purpose_value = str(scene_purpose_value or "").strip().lower()
            requested_value = str(requested_speed_value or "").strip().lower()

            fast_tokens = (
                "hook",
                "feature",
                "proof",
                "result",
                "reveal",
                "후킹",
                "기능",
                "증명",
                "결과",
            )
            medium_tokens = (
                "pain",
                "usage",
                "comparison",
                "problem",
                "empathy",
                "demo",
                "사용",
                "비교",
                "불편",
                "공감",
            )
            slow_tokens = (
                "cta",
                "ending",
                "close",
                "마무리",
                "구매",
            )

            if any(token in purpose_value for token in fast_tokens):
                return "fast"
            if any(token in purpose_value for token in medium_tokens):
                return "medium"
            if any(token in purpose_value for token in slow_tokens):
                return "slow"

            # 업로드 이미지가 Director 장면 수보다 많아 목적이 없는 확장 장면은
            # fast가 전혀 사라지지 않도록 리듬형 기본 분포를 적용합니다.
            fallback_speed_sequence = (
                "fast",
                "medium",
                "fast",
                "medium",
                "fast",
                "medium",
                "medium",
                "slow",
            )
            fallback_value = fallback_speed_sequence[
                scene_index_value % len(fallback_speed_sequence)
            ]

            if requested_value in {"fast", "medium", "slow"}:
                # 목적이 없더라도 Director가 fast/medium을 준 경우는 유지합니다.
                # slow만 반복되는 경우에는 리듬형 fallback으로 보강합니다.
                if requested_value != "slow":
                    return requested_value

            return fallback_value

        director_scene_count = max(
            len(director_motion_scenes),
            len(director_motion_plan),
            int(scene_plan_result.get("scene_count") or 0),
            len(list(scene_plan_result.get("scenes") or [])),
        )

        # Sprint144-2:
        # 업로드 상품 이미지는 AI 생성의 기준(reference)으로만 사용합니다.
        # Image Motion 입력은 장면별 Closed Loop 최종 생성 이미지를 최우선으로 사용하고,
        # 생성 실패 또는 파일 누락 장면에만 실제 상품 이미지를 fallback으로 배정합니다.
        # Sprint150-5: 쇼츠 영상은 10장면 × 2.5초 = 25초로 고정합니다.
        # 업로드 이미지가 10장보다 적으면 아래 장면 루프에서 순환 배정합니다.
        short_motion_scene_count = int(
            ai_image_director_result.get("approved_scene_count")
            or min(10, max(len(director_motion_scenes), director_scene_count))
            or 0
        )
        flexible_ready = bool(ai_image_director_result.get("flexible_render_ready"))
        if director_motion_scenes and not flexible_ready:
            raise RuntimeError(
                "Sprint162 flexible approval requires at least 8 approved scenes; "
                f"approved={ai_image_director_result.get('approved_scene_count', 0)}"
            )
        short_scene_duration = float(
            ai_image_director_result.get("seconds_per_scene")
            or (25.0 / short_motion_scene_count if short_motion_scene_count else 0.0)
        )
        target_motion_scene_count = short_motion_scene_count
        print(
            "[Sprint162 Flexible Motion] Render Scene Count:",
            target_motion_scene_count,
            flush=True,
        )
        print(
            "[Sprint162 Flexible Motion] Seconds Per Scene:",
            short_scene_duration,
            flush=True,
        )
        print(
            "[Sprint162 Flexible Motion] Target Duration:",
            target_motion_scene_count * short_scene_duration,
            flush=True,
        )

        def resolve_generated_motion_image(scene_value):
            if not isinstance(scene_value, dict):
                return ""
            candidates = (
                scene_value.get("selected_generated_image_path"),
                scene_value.get("validated_image_path"),
                scene_value.get("generated_image_path"),
                scene_value.get("final_image_path"),
                scene_value.get("resolved_image_path"),
                scene_value.get("output_image_path"),
                scene_value.get("selected_image_path"),
            )
            for candidate in candidates:
                candidate_text = str(candidate or "").strip()
                if not candidate_text:
                    continue
                candidate_path = Path(candidate_text)
                if candidate_path.is_file():
                    return str(candidate_path)
            return ""

        existing_motion_scenes = []
        generated_motion_count = 0
        fallback_motion_count = 0
        missing_motion_count = 0

        for scene_index in range(target_motion_scene_count):
            director_scene = (
                director_motion_scenes[scene_index]
                if scene_index < len(director_motion_scenes)
                else {}
            )
            director_plan_item = (
                director_motion_plan[scene_index]
                if scene_index < len(director_motion_plan)
                else {}
            )

            if scene_image_direct_mode and scene_index < len(fresh_product_images):
                image_path_value = fresh_product_images[scene_index]
                motion_source_value = "sprint146_7_uploaded_scene_image_direct"
            else:
                image_path_value = resolve_generated_motion_image(director_scene)
                motion_source_value = "sprint144_2_closed_loop_generated_image"

            if image_path_value:
                generated_motion_count += 1
            elif fresh_product_images and not ai_image_director_result.get("flexible_render_ready"):
                image_path_value = fresh_product_images[
                    scene_index % len(fresh_product_images)
                ]
                motion_source_value = "sprint144_2_product_reference_fallback"
                fallback_motion_count += 1
            else:
                missing_motion_count += 1
                print(
                    f"[Sprint144-2 AI Image Motion] Scene{scene_index + 1:02d} "
                    "SKIPPED: generated image and product fallback are missing",
                    flush=True,
                )
                continue

            recommended_motion = str(
                director_scene.get("recommended_motion")
                or director_plan_item.get("recommended_motion")
                or default_motions[scene_index % len(default_motions)]
            )
            motion_purpose = resolve_motion_purpose(
                scene_index,
                director_scene,
                director_plan_item,
            )
            director_requested_speed = str(
                director_scene.get("motion_speed")
                or director_plan_item.get("motion_speed")
                or ""
            )
            resolved_motion_speed = resolve_motion_speed(
                scene_index,
                motion_purpose,
                director_requested_speed,
            )

            existing_motion_scenes.append(
                {
                    "scene_id": str(
                        director_scene.get("scene_id")
                        or director_plan_item.get("scene_id")
                        or f"scene_{scene_index + 1:02d}"
                    ),
                    "scene_index": scene_index,
                    "image_path": image_path_value,
                    "recommended_motion": recommended_motion,
                    "motion_speed": resolved_motion_speed,
                    "requested_motion_speed": director_requested_speed,
                    "motion_purpose": motion_purpose,
                    "motion_reason": str(
                        director_scene.get("motion_reason")
                        or director_plan_item.get("motion_reason")
                        or (
                            "sprint144_2_generated_image_motion_"
                            f"{motion_purpose or 'fallback'}"
                        )
                    ),
                    "camera_style": str(
                        director_scene.get("camera_style")
                        or director_plan_item.get("camera_style")
                        or "product_focus"
                    ),
                    "motion_source": motion_source_value,
                    # Sprint150-5: Director 장면 길이보다 쇼츠 25초 타임라인을 우선합니다.
                    "duration": short_scene_duration,
                }
            )

        print(
            "[Sprint144-2 AI Image Motion] Version:",
            "workflow-ai-image-motion-144-2",
            flush=True,
        )
        print(
            "[Sprint144-2 AI Image Motion] Director Scenes:",
            director_scene_count,
            flush=True,
        )
        print(
            "[Sprint144-2 AI Image Motion] Generated Images:",
            generated_motion_count,
            flush=True,
        )
        print(
            "[Sprint144-2 AI Image Motion] Product Fallbacks:",
            fallback_motion_count,
            flush=True,
        )
        print(
            "[Sprint144-2 AI Image Motion] Missing:",
            missing_motion_count,
            flush=True,
        )

        print(
            "[Sprint144-2 Image Sequence] Uploaded Reference Count:",
            len(fresh_product_images),
            flush=True,
        )
        print(
            "[Sprint144-2 Image Sequence] Director Scene Count:",
            director_scene_count,
            flush=True,
        )
        print(
            "[Sprint144-2 Image Sequence] Render Scene Count:",
            len(existing_motion_scenes),
            flush=True,
        )
        print(
            "[Sprint144-2 Image Sequence] Unique Render Images:",
            len({item["image_path"] for item in existing_motion_scenes}),
            flush=True,
        )
        for sequence_index, sequence_item in enumerate(existing_motion_scenes, start=1):
            print(
                f"[Sprint144-2 Image Sequence] Scene{sequence_index:02d} -> "
                f"{sequence_item.get('image_path', '')}",
                flush=True,
            )
            print(
                f"[Sprint136-1 Purpose Motion] Scene{sequence_index:02d}: "
                f"purpose={sequence_item.get('motion_purpose', '') or 'fallback'} "
                f"motion={sequence_item.get('recommended_motion', '')} "
                f"requested_speed="
                f"{sequence_item.get('requested_motion_speed', '') or 'empty'} "
                f"resolved_speed={sequence_item.get('motion_speed', '')}",
                flush=True,
            )

        print(
            "[Sprint136-1 Purpose Motion] Speed Distribution:",
            [
                item.get("motion_speed")
                for item in existing_motion_scenes
            ],
            flush=True,
        )

        # Sprint170: 첫 장면은 재사용 가능한 무자막 단색 배경입니다.
        trust_intro_path = Path(str(ai_image_director_result.get("hook_background_path") or ""))
        if trust_intro_path.is_file():
            existing_motion_scenes.insert(
                0,
                {
                    "scene_id": "scene_00_trust_intro",
                    "scene_index": 0,
                    "image_path": str(trust_intro_path),
                    "recommended_motion": "static_hold",
                    "motion_speed": "slow",
                    "requested_motion_speed": "slow",
                    "motion_purpose": "trust_intro",
                    "motion_reason": "구매수·리뷰수·평점 자막 전용 고정 배경",
                    "camera_style": "static_text_template",
                    "motion_source": "sprint170_trust_intro_template",
                    "duration": float(ai_image_director_result.get("hook_duration_seconds") or 2.0),
                },
            )
            for _index, _item in enumerate(existing_motion_scenes):
                _item["scene_index"] = _index
            print("[Sprint171 Trust Intro] PREPENDED:", str(trust_intro_path), flush=True)

        motion_image_paths = [
            item["image_path"]
            for item in existing_motion_scenes
        ]
        motion_plan_for_render = [
            {
                "scene_id": item["scene_id"],
                "scene_index": item["scene_index"],
                "recommended_motion": item["recommended_motion"],
                "motion_speed": item["motion_speed"],
                "requested_motion_speed": item.get(
                    "requested_motion_speed",
                    "",
                ),
                "motion_purpose": item.get("motion_purpose", ""),
                "motion_reason": item["motion_reason"],
                "camera_style": item["camera_style"],
                "motion_source": item["motion_source"] or "ai_image_director",
                "duration": item["duration"],
            }
            for item in existing_motion_scenes
        ]

        image_fallback_result = {
            "ok": False,
            "ready": False,
            "version": "product-image-video-fallback-131-8",
            "status": "not_run",
            "output_path": "",
            "image_count": len(motion_image_paths),
            "motion_plan_count": len(motion_plan_for_render),
            "motion_plan": motion_plan_for_render,
            "scene_files": [],
            "errors": [],
            "render_requested": True,
        }

        if reuse_image_motion_path:
            scene_video_result.update(
                ok=True,
                ready=True,
                status="skipped_reuse_existing_image_motion",
                version="image-motion-generator-153-2-reuse-bypass",
                generated_scene_count=0,
                failed_scene_count=0,
                generated_files=[],
                items=[],
                errors=[],
                motion_plan_used_count=0,
                render_requested=False,
                api_called=False,
            )
            scene_merge_result.update(
                ok=True,
                ready=True,
                status="reused_existing_image_motion",
                output_path=str(motion_output_path),
                scene_count=0,
                errors=[],
                render_requested=False,
            )
            image_fallback_result.update(
                ok=True,
                ready=True,
                status="reused_existing_image_motion",
                output_path=str(motion_output_path),
                scene_files=[],
                image_count=0,
                motion_plan_count=0,
                errors=[],
                render_requested=False,
                reused=True,
            )
            try:
                ProjectRepository().update_links_and_media(
                    getattr(project, "id"),
                    video_path=str(motion_output_path),
                )
                project.video_path = str(motion_output_path)
            except Exception as exc:
                image_fallback_result.setdefault("warnings", []).append(
                    f"Project video_path reuse update failed: {type(exc).__name__}: {exc}"
                )
            print("[Sprint153-2 Reuse ImageMotion] ACTIVE VIDEO:", str(motion_output_path), flush=True)

        elif motion_image_paths:
            try:
                image_motion_result = ImageMotionGenerator().generate_many(
                    image_paths=motion_image_paths,
                    output_dir=motion_render_dir,
                    duration=short_scene_duration,
                    start_index=0,
                    overwrite=True,
                    motion_plan=motion_plan_for_render,
                )

                scene_files = [
                    str(value)
                    for value in list(image_motion_result.get("scene_files") or [])
                    if str(value or "").strip()
                ]

                scene_video_result.update(
                    ok=bool(image_motion_result.get("ok")),
                    ready=bool(image_motion_result.get("ready")),
                    status=str(image_motion_result.get("status") or "failed"),
                    version=str(
                        image_motion_result.get("version")
                        or ImageMotionGenerator.VERSION
                    ),
                    generated_scene_count=int(
                        image_motion_result.get("generated_count") or 0
                    ),
                    failed_scene_count=int(
                        image_motion_result.get("failed_count") or 0
                    ),
                    generated_files=scene_files,
                    items=list(image_motion_result.get("items") or []),
                    errors=list(image_motion_result.get("errors") or []),
                    motion_plan_used_count=int(
                        image_motion_result.get("motion_plan_used_count") or 0
                    ),
                    render_requested=True,
                    api_called=False,
                )

                if scene_files:
                    concat_file = motion_render_dir / "concat.txt"

                    def _concat_quote(value):
                        normalized = str(Path(value).resolve()).replace("\\", "/")
                        return normalized.replace("'", "'\\''")

                    concat_file.write_text(
                        "\n".join(
                            f"file '{_concat_quote(value)}'"
                            for value in scene_files
                        ) + "\n",
                        encoding="utf-8",
                    )

                    merge_completed = subprocess.run(
                        [
                            "ffmpeg",
                            "-y",
                            "-f",
                            "concat",
                            "-safe",
                            "0",
                            "-i",
                            str(concat_file),
                            "-c",
                            "copy",
                            "-movflags",
                            "+faststart",
                            str(motion_output_path),
                        ],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        check=False,
                    )

                    merge_ok = (
                        merge_completed.returncode == 0
                        and motion_output_path.is_file()
                        and motion_output_path.stat().st_size > 1024
                    )

                    if merge_ok:
                        scene_merge_result.update(
                            ok=True,
                            ready=True,
                            status="merged",
                            output_path=str(motion_output_path),
                            scene_count=len(scene_files),
                            errors=[],
                            render_requested=True,
                        )
                        image_fallback_result.update(
                            ok=True,
                            ready=True,
                            status="motion_created",
                            output_path=str(motion_output_path),
                            scene_files=scene_files,
                            image_count=len(motion_image_paths),
                            motion_plan_count=len(motion_plan_for_render),
                            generator_result=image_motion_result,
                            errors=[],
                        )

                        try:
                            ProjectRepository().update_links_and_media(
                                getattr(project, "id"),
                                video_path=str(motion_output_path),
                            )
                            project.video_path = str(motion_output_path)
                            image_fallback_result["project_video_updated"] = True
                        except Exception as exc:
                            image_fallback_result["project_video_updated"] = False
                            image_fallback_result.setdefault("warnings", []).append(
                                f"Project video_path update failed: "
                                f"{type(exc).__name__}: {exc}"
                            )


                        # Sprint131-8: 하위 VideoPipeline이 관례적으로 찾는
                        # {project_id}_merged.mp4도 새 image_motion 영상으로 강제 교체합니다.
                        canonical_merged_path = (
                            Path("exports")
                            / "videos"
                            / f"{project_id_for_director}_merged.mp4"
                        )
                        try:
                            canonical_merged_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(motion_output_path, canonical_merged_path)
                            image_fallback_result["canonical_merged_path"] = str(canonical_merged_path)
                            image_fallback_result["canonical_merged_updated"] = True
                            print(
                                "[Sprint131-8 Final Source Lock] MERGED SOURCE:",
                                str(canonical_merged_path),
                                "<=",
                                str(motion_output_path),
                                flush=True,
                            )
                        except Exception as exc:
                            image_fallback_result["canonical_merged_updated"] = False
                            image_fallback_result.setdefault("warnings", []).append(
                                f"Canonical merged copy failed: {type(exc).__name__}: {exc}"
                            )
                    else:
                        merge_error = (
                            merge_completed.stderr
                            or merge_completed.stdout
                            or "ffmpeg merge failed"
                        )[-2000:]
                        scene_merge_result.update(
                            status="merge_failed",
                            errors=[merge_error],
                            render_requested=True,
                        )
                        image_fallback_result.update(
                            status="merge_failed",
                            scene_files=scene_files,
                            generator_result=image_motion_result,
                            errors=[merge_error],
                        )
                else:
                    image_fallback_result.update(
                        status="scene_generation_failed",
                        generator_result=image_motion_result,
                        errors=list(image_motion_result.get("errors") or []),
                    )
            except Exception as exc:
                error_text = f"{type(exc).__name__}: {exc}"
                scene_video_result.update(
                    status="failed",
                    errors=[error_text],
                )
                scene_merge_result.update(
                    status="failed",
                    errors=[error_text],
                )
                image_fallback_result.update(
                    status="failed",
                    errors=[error_text],
                )
        else:
            scene_video_result.update(
                status="skipped_no_existing_images",
                warnings=[
                    "AI 이미지 생성 전이라 Motion 렌더에 사용할 기존 상품 이미지가 없습니다."
                ],
            )
            scene_merge_result.update(
                status="skipped_no_scene_videos",
            )
            image_fallback_result.update(
                status="skipped_no_existing_images",
                errors=[],
            )

        outputs["scene_video_generation"] = scene_video_result
        outputs["scene_merge"] = scene_merge_result
        outputs["product_image_video_fallback"] = image_fallback_result
        outputs["motion_plan"] = motion_plan_for_render
        outputs["render_mode"] = {
            "version": "ai-image-motion-render-bridge-131-8",
            "mode": "existing_product_image_motion",
            "planning_complete": bool(director_manifest_result.get("ready")),
            "render_enabled": True,
            "veo_api_called": False,
            "fallback_video_created": bool(image_fallback_result.get("ok")),
            "director_manifest_path": director_manifest_result.get("manifest_path", ""),
            "motion_output_path": image_fallback_result.get("output_path", ""),
        }

        print("[Sprint131-6 Image Motion Render] Version: image-motion-render-bridge-131-6", flush=True)
        print(
            "[Sprint131-6 Image Motion Render] Director Motion Count:",
            len(list(ai_image_director_result.get("motion_plan") or [])),
            flush=True,
        )
        print(
            "[Sprint131-6 Image Motion Render] Render Image Count:",
            len(motion_image_paths),
            flush=True,
        )
        print(
            "[Sprint131-6 Image Motion Render] Motion Plan Used:",
            scene_video_result.get("motion_plan_used_count", 0),
            flush=True,
        )
        print(
            "[Sprint131-6 Image Motion Render] Scene Status:",
            scene_video_result.get("status", ""),
            flush=True,
        )
        print(
            "[Sprint131-6 Image Motion Render] Merge Status:",
            scene_merge_result.get("status", ""),
            flush=True,
        )
        print(
            "[Sprint131-6 Image Motion Render] Output:",
            image_fallback_result.get("output_path", ""),
            flush=True,
        )
        print(
            "[Sprint131-6 Image Motion Render] Errors:",
            image_fallback_result.get("errors", []),
            flush=True,
        )

        ai_video_result.update(
            {
                "ok": bool(image_fallback_result.get("ok")),
                "ready": bool(image_fallback_result.get("ready")),
                "status": (
                    "image_motion_rendered"
                    if image_fallback_result.get("ok")
                    else "image_motion_pending"
                ),
                "render_mode": "existing_product_image_motion",
                "render_enabled": True,
                "api_called": False,
                "director_output_dir": director_output_dir,
                "vision_analysis_path": vision_analysis_result.get("analysis_path", ""),
                "image_tags_path": image_tags_result.get("tag_manifest_path", ""),
                "scene_plan_path": scene_plan_result.get("scene_plan_path", ""),
                "scene_selection_path": scene_selection_result.get("scene_selection_path", ""),
                "director_manifest_path": director_manifest_result.get("manifest_path", ""),
                "generated_scene_count": int(
                    scene_video_result.get("generated_scene_count") or 0
                ),
                "failed_scene_count": int(
                    scene_video_result.get("failed_scene_count") or 0
                ),
                "generated_files": list(
                    scene_video_result.get("generated_files") or []
                ),
                "selected_video_path": str(
                    image_fallback_result.get("output_path") or ""
                ),
                "motion_plan": motion_plan_for_render,
                "warnings": list(image_fallback_result.get("warnings") or []),
                "errors": list(image_fallback_result.get("errors") or []),
            }
        )
        outputs["ai_video"] = ai_video_result
        outputs["ai_video_path"] = str(
            image_fallback_result.get("output_path") or ""
        )

        # Sprint131-6: 이후 모든 영상 분석·편집 단계는 이번 실행에서
        # 새 상품 이미지로 생성된 Image Motion 영상만 사용합니다.
        fresh_motion_video = str(outputs.get("ai_video_path") or "").strip()
        if fresh_motion_video and Path(fresh_motion_video).is_file():
            try:
                project.video_path = fresh_motion_video
            except Exception:
                pass
            print(
                "[Sprint131-6 Fresh Input] ACTIVE VIDEO:",
                fresh_motion_video,
                flush=True,
            )
        else:
            print(
                "[Sprint131-6 Fresh Input] ACTIVE VIDEO: MISSING",
                flush=True,
            )


        # 2~3. Legacy Source Video Pipeline Disabled
        # Sprint131-6: 기존 latest.mp4, 다운로드 영상, 외부 영상 후보를 절대 사용하지 않습니다.
        source_plan = {
            "ok": True,
            "status": "disabled_fresh_product_input_only",
            "source": "image_motion_only",
            "video_path": fresh_motion_video,
        }
        ranked = []
        outputs["source_plan"] = source_plan
        outputs["source_rank"] = ranked
        outputs["video_sources"] = {
            "ok": True,
            "status": "disabled_fresh_product_input_only",
            "results": [],
            "best_candidates": [],
        }
        outputs["video_candidates"] = []

        state.update_step(
            job_id,
            "source_plan",
            "done",
            source_plan,
        )
        state.update_step(
            job_id,
            "source_rank",
            "done",
            {
                "count": 0,
                "top": [],
                "status": "disabled_fresh_product_input_only",
            },
        )

        print(
            "[Sprint131-6 Fresh Input] Legacy Source Plan: DISABLED",
            flush=True,
        )
        print(
            "[Sprint131-6 Fresh Input] Legacy Source Ranking: DISABLED",
            flush=True,
        )
        print(
            "[Sprint131-6 Fresh Input] Live Video Sourcing: DISABLED",
            flush=True,
        )

        # 4. Real Vision
        try:
            current_video = str(outputs.get("ai_video_path") or "").strip()

            print(
                "[Sprint131-6 Fresh Input] current_video =",
                current_video,
                flush=True,
            )

            if (
                current_video
                and resolver.exists(current_video)
            ):
                project.video_path = current_video

                real_vision = RealVisionRunner().run(
                    project,
                    sample_count=sample_count,
                    use_yolo=True,
                    use_paddle=True,
                )

            else:
                real_vision = {
                    "ok": False,
                    "summary": (
                        "현재 프로젝트에 연결된 "
                        "video_path가 없습니다. "
                        "영상 후보를 열어 해당 프로젝트에 "
                        "영상을 먼저 연결하세요."
                    ),
                    "status": {
                        "video_ai": False,
                        "vision_ai": False,
                        "yolo": False,
                        "paddleocr": False,
                        "object_fallback": False,
                    },
                    "project": {
                        "id": getattr(
                            project,
                            "id",
                            None,
                        ),
                        "product_name": getattr(
                            project,
                            "product_name",
                            "",
                        ),
                        "keyword": getattr(
                            project,
                            "keyword",
                            "",
                        ),
                        "video_path": current_video,
                    },
                }

            outputs["real_vision"] = real_vision

            state.update_step(
                job_id,
                "real_vision",
                (
                    "done"
                    if real_vision.get("ok")
                    else "failed"
                ),
                {
                    "summary": real_vision.get(
                        "summary"
                    ),
                    "status": real_vision.get(
                        "status"
                    ),
                },
                (
                    None
                    if real_vision.get("ok")
                    else real_vision.get("summary")
                ),
            )

        except Exception as exc:
            real_vision = {}
            outputs["real_vision"] = {}

            state.update_step(
                job_id,
                "real_vision",
                "failed",
                error=exc,
            )

        # 5. Video Quality
        print(
            "[Sprint62] BEFORE VideoQuality",
            flush=True,
        )

        try:
            current_video = str(outputs.get("ai_video_path") or "").strip()

            outputs["video_quality"] = (
                VideoQualityEngine().score(
                    current_video,
                    real_vision,
                )
            )

        except Exception as exc:
            print(
                "[Sprint62] VideoQuality ERROR:",
                repr(exc),
                flush=True,
            )

            outputs["video_quality"] = {
                "ok": False,
                "reason": str(exc),
            }

        print(
            "[Sprint62] AFTER VideoQuality:",
            outputs.get("video_quality", {}),
            flush=True,
        )

        # Sprint132-3 Viral Pattern Candidate Bridge
        # 기존 영상 후보와 Sprint132 Viral Collector의 선택 영상을 하나의 후보 풀로 합칩니다.
        # ViralPatternEngine이 Collector 결과를 실제 입력으로 받도록 연결합니다.
        original_video_candidates = [
            dict(item)
            for item in (outputs.get("video_candidates", []) or [])
            if isinstance(item, dict)
        ]
        collected_viral_candidates = [
            dict(item)
            for item in (
                outputs.get("viral_collection", {}).get("videos", [])
                if isinstance(outputs.get("viral_collection", {}), dict)
                else []
            )
            if isinstance(item, dict)
        ]

        combined_video_candidates = []
        combined_candidate_keys = set()

        for candidate_source, candidate_items in (
            ("video_candidates", original_video_candidates),
            ("viral_collector", collected_viral_candidates),
        ):
            for candidate_item in candidate_items:
                candidate = dict(candidate_item)
                candidate.setdefault("candidate_source", candidate_source)

                candidate_key = str(
                    candidate.get("url")
                    or candidate.get("video_url")
                    or candidate.get("webpage_url")
                    or candidate.get("video_id")
                    or candidate.get("id")
                    or ""
                ).strip().lower()

                if not candidate_key:
                    candidate_key = "|".join(
                        [
                            str(candidate.get("platform") or "").strip().lower(),
                            str(candidate.get("channel_name") or candidate.get("channel") or "").strip().lower(),
                            str(candidate.get("title") or "").strip().lower(),
                        ]
                    )

                if candidate_key and candidate_key in combined_candidate_keys:
                    continue
                if candidate_key:
                    combined_candidate_keys.add(candidate_key)

                combined_video_candidates.append(candidate)

        outputs["viral_pattern_input_candidates"] = combined_video_candidates

        print(
            "[Sprint132-3 Viral Pattern Bridge] Existing Candidates:",
            len(original_video_candidates),
            flush=True,
        )
        print(
            "[Sprint132-3 Viral Pattern Bridge] Collector Candidates:",
            len(collected_viral_candidates),
            flush=True,
        )
        print(
            "[Sprint132-3 Viral Pattern Bridge] Combined Candidates:",
            len(combined_video_candidates),
            flush=True,
        )

        # 6. Shopping Shorts Fit
        try:
            outputs["shopping_shorts_fit"] = (
                ShoppingFitEngine().analyze(
                    project=project,
                    video_quality=outputs.get(
                        "video_quality",
                        {},
                    ),
                    real_vision=outputs.get(
                        "real_vision",
                        {},
                    ),
                    candidates=combined_video_candidates,
                )
            )

            print(
                "[Sprint62] ShoppingFit:",
                outputs.get(
                    "shopping_shorts_fit",
                    {},
                ),
                flush=True,
            )

        except Exception as exc:
            print(
                "[Sprint62] ShoppingFit ERROR:",
                repr(exc),
                flush=True,
            )

            outputs["shopping_shorts_fit"] = {
                "ok": False,
                "reason": str(exc),
            }

        # 7. Candidate Enrichment
        enriched_candidates = []

        for item in combined_video_candidates:
            if not isinstance(item, dict):
                continue

            candidate = dict(item)

            candidate["video_quality"] = (
                candidate.get("video_quality")
                or outputs.get(
                    "video_quality",
                    {},
                )
            )

            candidate["shopping_shorts_fit"] = (
                candidate.get(
                    "shopping_shorts_fit"
                )
                or outputs.get(
                    "shopping_shorts_fit",
                    {},
                )
            )

            candidate["shopping_fit"] = (
                candidate.get("shopping_fit")
                or outputs.get(
                    "shopping_shorts_fit",
                    {},
                )
            )

            candidate["real_vision"] = (
                candidate.get("real_vision")
                or outputs.get(
                    "real_vision",
                    {},
                )
            )

            enriched_candidates.append(candidate)

        outputs["enriched_video_candidates"] = (
            enriched_candidates
        )

        # 8. Sprint 62 Viral Pattern Engine
        try:
            viral_pattern = (
                ViralPatternEngine().analyze(
                    candidates=enriched_candidates,
                    project=project,
                    product_plan=product_plan,
                    save_db=True,
                )
            )

            outputs["viral_pattern"] = viral_pattern

            viral_candidates = (
                viral_pattern.get(
                    "all_candidates",
                    [],
                )
                if isinstance(
                    viral_pattern,
                    dict,
                )
                else []
            )

            if viral_candidates:
                restored_candidates = []

                for item in viral_candidates:
                    if not isinstance(item, dict):
                        continue

         

            outputs["viral_pattern_best"] = (
                viral_pattern.get(
                    "best_pattern",
                    {},
                )
                if isinstance(
                    viral_pattern,
                    dict,
                )
                else {}
            )
            outputs["viral_scene_plan"] = (
                viral_pattern.get(
                    "best_scene_plan",
                    {},
                )
                if isinstance(
                    viral_pattern,
                    dict,
                )
                else {}
            )

            print(
                "[Sprint133-1 Viral Scene Structure] Version:",
                outputs.get("viral_scene_plan", {}).get("version", ""),
                flush=True,
            )
            print(
                "[Sprint133-1 Viral Scene Structure] Status:",
                outputs.get("viral_scene_plan", {}).get("status", ""),
                flush=True,
            )
            print(
                "[Sprint133-1 Viral Scene Structure] Scene Count:",
                outputs.get("viral_scene_plan", {}).get("scene_count", 0),
                flush=True,
            )
            print(
                "[Sprint62] ViralPattern version:",
                viral_pattern.get(
                    "engine_version"
                ),
                flush=True,
            )
            print(
                "[Sprint62] ViralPattern candidates:",
                viral_pattern.get(
                    "candidate_count",
                    0,
                ),
                flush=True,
            )
            print(
                "[Sprint62] ViralPattern best:",
                viral_pattern.get(
                    "best_pattern",
                    {},
                ),
                flush=True,
            )

        except Exception as exc:
            print(
                "[Sprint62] ViralPattern ERROR:",
                repr(exc),
                flush=True,
            )

            outputs["viral_pattern"] = {
                "ok": False,
                "reason": str(exc),
                "candidate_count": len(
                    enriched_candidates
                ),
                "top_candidates": [],
                "all_candidates": (
                    enriched_candidates
                ),
                "pattern_summary": [],
                "best_pattern": {},
            }
            outputs["viral_pattern_best"] = {}
            outputs["viral_scene_plan"] = {}

        # 9. Selector + Ranker
        try:
            selector_result = (
                VideoCandidateSelector().select(
                    enriched_candidates
                )
            )

            selector_candidates = (
                selector_result.get("all", [])
                if isinstance(
                    selector_result,
                    dict,
                )
                else []
            )

            ranker_result = (
                VideoCandidateRanker().rank(
                    selector_candidates,
                    top_n=3,
                )
            )

            outputs["candidate_selection"] = (
                selector_result
                if isinstance(
                    selector_result,
                    dict,
                )
                else {
                    "ok": False,
                    "top3": [],
                    "all": [],
                }
            )

            outputs["candidate_ranking"] = (
                ranker_result
                if isinstance(
                    ranker_result,
                    dict,
                )
                else {
                    "ok": False,
                    "top3": [],
                    "all": [],
                }
            )

            outputs[
                "candidate_selection"
            ]["ranked_top3"] = (
                ranker_result.get(
                    "top3",
                    [],
                )
            )

            outputs[
                "candidate_selection"
            ]["composer_candidate"] = (
                ranker_result.get(
                    "composer_candidate"
                )
            )

            outputs[
                "candidate_selection"
            ]["ranker_version"] = (
                ranker_result.get(
                    "ranker_version"
                )
            )

            outputs["composer_candidate"] = (
                ranker_result.get(
                    "composer_candidate"
                )
            )

            outputs["ranked_top3"] = (
                ranker_result.get(
                    "top3",
                    [],
                )
            )

            print(
                "[Sprint62] Ranker:",
                ranker_result.get(
                    "ranker_version"
                ),
                flush=True,
            )
            print(
                "[Sprint62] Top3:",
                len(
                    ranker_result.get(
                        "top3",
                        [],
                    )
                ),
                flush=True,
            )
            print(
                "[Sprint62] Composer:",
                bool(
                    ranker_result.get(
                        "composer_candidate"
                    )
                ),
                flush=True,
            )
            print(
                "[Sprint62] Best Score:",
                (
                    ranker_result.get("best")
                    or {}
                ).get(
                    "final_rank_score"
                ),
                flush=True,
            )
            print(
                "[Sprint62] Best viral score:",
                (
                    ranker_result.get("best")
                    or {}
                ).get(
                    "viral_pattern_score"
                ),
                flush=True,
            )
            print(
                "[Sprint63] Rank Breakdown:",
                json.dumps(
                (
                        ranker_result.get("best")
                        or {}
                    ).get(
                        "rank_score_breakdown",
                        {},
                    ),
                    ensure_ascii=False,
                    indent=2,
                ),
                flush=True,
            )

            print(
                "[Sprint63] Viral Breakdown:",
                json.dumps(
                    (
                        (
                            ranker_result.get("best")
                            or {}
                        ).get(
                            "rank_score_breakdown",
                            {},
                        )
                        or {}
                    ).get(
                         "viral_score_breakdown",
                        {},
                    ),
                    ensure_ascii=False,
                    indent=2,
                ),
                flush=True,
            )

            print(
                "[Sprint63] Warnings:",
                 json.dumps(
                    (
                        ranker_result.get("best")
                        or {}
                    ).get(
                        "rank_warnings",
                        [],
                    ),
                    ensure_ascii=False,
                    indent=2,
                ),
                flush=True,
            )
        except Exception as exc:
            print(
                "[Sprint62] Candidate ERROR:",
                repr(exc),
                flush=True,
            )

            outputs["candidate_selection"] = {
                "ok": False,
                "reason": str(exc),
                "top3": [],
                "all": [],
            }

            outputs["candidate_ranking"] = {
                "ok": False,
                "reason": str(exc),
                "top3": [],
                "all": [],
            }

            outputs["composer_candidate"] = None
            outputs["ranked_top3"] = []

        # 10. Auto Editor
        try:
            editor_plan = (
                AutoEditorEngine().create_plan(
                    getattr(
                        project,
                        "product_name",
                        "",
                    ),
                    getattr(
                        project,
                        "keyword",
                        "정보",
                    ),
                    vision=real_vision,
                    candidate_selection=outputs.get(
                        "candidate_selection",
                        {},
                    ),
                )
            )

            outputs["auto_editor"] = editor_plan

            state.update_step(
                job_id,
                "auto_editor",
                "done",
                {
                    "timeline_count": len(
                        editor_plan.get(
                            "timeline",
                            [],
                        )
                    )
                },
            )

        except Exception as exc:
            editor_plan = {}
            outputs["auto_editor"] = {}

            state.update_step(
                job_id,
                "auto_editor",
                "failed",
                error=exc,
            )


        # 10-1. Sprint71-2 Social Comments + OCR Review Merge + Review Insight
        social_comment_result = {
            "collector_version": "",
            "ok": False,
            "status": "not_run",
            "project_id": getattr(project, "id", ""),
            "video_count": 0,
            "comment_count": 0,
            "items": [],
            "comments": [],
        }
        manual_review_result = {
            "ok": False,
            "version": "evidence-input-engine-115-1",
            "status": "not_provided",
            "review_count": 0,
            "reviews": [],
            "source": "manual_review_text",
        }
        review_ocr_result = {
            "ok": False,
            "status": "not_run",
            "image_count": 0,
            "review_count": 0,
            "image_paths": [],
            "reviews": [],
        }
        review_insight_result = {}
        review_quote_result = {
            "ok": False,
            "version": "review-quote-selector-73-2",
            "status": "not_run",
            "review_count": 0,
            "best_pain": "",
            "best_benefit": "",
            "best_emotion": "",
            "best_recommendation": "",
            "best_quote": "",
            "top_quotes": [],
            "keyword_summary": [],
        }
        review_clean_result = {
            "ok": False,
            "version": "review-cleaner-73-1",
            "status": "not_run",
            "input_count": 0,
            "review_count": 0,
            "reviews": [],
            "texts": [],
            "stats": {
                "input_count": 0,
                "output_count": 0,
                "removed_count": 0,
            },
            "warnings": [],
        }
        merged_reviews = []

        print(
            "[Sprint71-2] ENTER Social + OCR Review Merge + Review Insight",
            flush=True,
        )

        try:
            social_candidates = (
                outputs.get("ranked_top3")
                or (outputs.get("candidate_ranking") or {}).get("top3")
                or (outputs.get("candidate_selection") or {}).get("top3")
                or enriched_candidates
                or []
            )

            social_comment_result = SocialCommentCollector().collect_many(
                candidates=social_candidates,
                project_id=getattr(project, "id", ""),
                max_comments_per_video=20,
                max_videos=3,
                timeout=30,
                verification_wait_seconds=180,
            )

            print(
                "[Sprint71-2] Social Comments:",
                social_comment_result.get("status"),
                social_comment_result.get("comment_count", 0),
                flush=True,
            )
        except Exception as exc:
            social_comment_result.update(
                status="failed",
                error=str(exc),
            )
            print(
                "[Sprint71-2] SocialCommentCollector ERROR:",
                repr(exc),
                flush=True,
            )

        outputs["social_comments"] = social_comment_result

        try:
            product_plan = (
                outputs.get("product_plan")
                if isinstance(outputs.get("product_plan"), dict)
                else {}
            )

            coupang_reviews = self._normalize_reviews(
                product_plan.get("reviews")
                or product_plan.get("review_data")
                or [],
                source=product_plan.get("review_source") or "coupang",
            )

            resolved_review_image_paths = self._review_image_paths(
                project,
                project_data,
                supplied_paths=review_image_paths,
            )
            print(
                "[UTF8 TRACE review_text BEFORE PARSE]",
                repr(review_text),
                flush=True,
            )

            manual_reviews = self._parse_manual_review_text(review_text)
            manual_review_result.update(
                {
                    "ok": bool(manual_reviews),
                    "status": "collected" if manual_reviews else "not_provided",
                    "review_count": len(manual_reviews),
                    "reviews": manual_reviews,
                    "character_count": len(review_text),
                }
            )

            if manual_reviews:
                review_ocr_result.update(
                    {
                        "status": "bypassed_manual_review_text",
                        "image_count": len(resolved_review_image_paths),
                        "image_paths": list(resolved_review_image_paths),
                        "review_count": 0,
                        "reviews": [],
                    }
                )
                ocr_reviews = []
            else:
                review_ocr_result = self._run_review_image_ocr(
                    resolved_review_image_paths,
                    project,
                    multi_image_mode=multi_image_mode,
                )
                ocr_reviews = self._normalize_reviews(
                    review_ocr_result.get("reviews", []),
                    source="review_image_ocr",
                )

            print(
                "[Sprint115-1 Evidence Input] Manual Reviews:",
                len(manual_reviews),
                "OCR Status:",
                review_ocr_result.get("status"),
                flush=True,
            )
            print(
                "[DEBUG73-4] OCR Raw First:",
                repr(
                    (
                        review_ocr_result.get("reviews", [])
                        or [{}]
                    )[0]
                ),
                flush=True,
            )

            print(
                "[DEBUG73-4] OCR Normalized First:",
                repr(
                    ocr_reviews[0]
                    if ocr_reviews
                    else {}
                ),
                flush=True,
            )
            self._sprint100_4_text_probe(
                "OCR RAW",
                review_ocr_result.get("reviews", []),
            )
            self._sprint100_4_text_probe(
                "OCR NORMALIZED",
                ocr_reviews,
            )
            print("[UTF8 TRACE coupang_reviews]", repr(coupang_reviews), flush=True)
            print("[UTF8 TRACE manual_reviews]", repr(manual_reviews), flush=True)
            print("[UTF8 TRACE ocr_reviews]", repr(ocr_reviews), flush=True)

            merged_reviews = self._merge_reviews(
                coupang_reviews,
                manual_reviews,
                ocr_reviews,
            )

            raw_merged_reviews = list(merged_reviews)

            review_clean_result = ReviewCleaner().clean(
                reviews=raw_merged_reviews,
                source=(
                    "coupang+manual_review_text"
                    if manual_reviews
                    else "coupang+review_image_ocr"
                ),
            )

            clean_reviews = review_clean_result.get(
                "reviews",
                [],
            )
            self._sprint100_4_text_probe(
                "CLEAN REVIEW",
                clean_reviews,
            )

            if clean_reviews:
                merged_reviews = clean_reviews

            outputs["review_clean"] = review_clean_result

            coupang_count = len(coupang_reviews)
            manual_count = len(manual_reviews)
            ocr_count = len(ocr_reviews)
            raw_merged_count = len(raw_merged_reviews)
            merged_count = len(merged_reviews)

            print(
                "[Sprint73-1] OCR/Merged Reviews:",
                raw_merged_count,
                flush=True,
            )
            print(
                "[Sprint73-1] Clean Reviews:",
                review_clean_result.get(
                    "review_count",
                    merged_count,
                ),
                flush=True,
            )
            print(
                "[Sprint73-1] Removed:",
                (
                    review_clean_result.get("stats", {})
                    or {}
                ).get(
                    "removed_count",
                    0,
                ),
                flush=True,
            )
            print(
                "[Sprint73-1] Cleaner Version:",
                review_clean_result.get(
                    "version",
                    "",
                ),
                flush=True,
            )

            if coupang_count and manual_count:
                merged_source = "coupang+manual_review_text"
                merged_status = "collected_manual_merged"
            elif manual_count:
                merged_source = "manual_review_text"
                merged_status = "collected_manual"
            elif coupang_count and ocr_count:
                merged_source = "coupang+review_image_ocr"
                merged_status = "collected_merged"
            elif ocr_count:
                merged_source = "review_image_ocr"
                merged_status = "collected_ocr"
            elif coupang_count:
                merged_source = (
                    product_plan.get("review_source")
                    or "coupang"
                )
                merged_status = (
                    product_plan.get("review_collect_status")
                    or "collected"
                )
            else:
                merged_source = (
                    product_plan.get("review_source")
                    or "none"
                )
                merged_status = (
                    product_plan.get("review_collect_status")
                    or "empty"
                )

            product_plan["coupang_reviews"] = coupang_reviews
            product_plan["manual_reviews"] = manual_reviews
            product_plan["ocr_reviews"] = ocr_reviews
            product_plan["reviews"] = merged_reviews
            product_plan["review_data"] = merged_reviews
            product_plan["review_count"] = merged_count
            product_plan["review_source"] = merged_source
            product_plan["review_collect_status"] = merged_status
            product_plan["manual_review_input"] = manual_review_result
            product_plan["review_ocr"] = review_ocr_result
            product_plan["review_clean"] = review_clean_result
            product_plan["raw_merged_review_count"] = raw_merged_count
            product_plan["clean_review_count"] = merged_count

            outputs["product_plan"] = product_plan
            outputs["manual_review_input"] = manual_review_result
            outputs["review_ocr"] = review_ocr_result
            outputs["review_clean"] = review_clean_result
            outputs["merged_reviews"] = merged_reviews
            outputs["review_image_paths"] = resolved_review_image_paths

            print(
                "[Sprint71-2] Review Merge:",
                {
                    "coupang": coupang_count,
                    "manual": manual_count,
                    "ocr": ocr_count,
                    "merged": merged_count,
                    "source": merged_source,
                    "status": merged_status,
                },
                flush=True,
            )
        except Exception as exc:
            outputs["manual_review_input"] = manual_review_result
            outputs["review_ocr"] = review_ocr_result
            outputs["review_clean"] = review_clean_result
            outputs["merged_reviews"] = merged_reviews
            print(
                "[Sprint71-2] OCR Review Merge ERROR:",
                repr(exc),
                flush=True,
            )

        try:
            review_quote_result = ReviewQuoteSelector().select(
                reviews=merged_reviews,
                product_name=(
                    getattr(project, "product_name", "")
                    or getattr(project, "title", "")
                    or "선택 상품"
                ),
                top_n=5,
            )

            print(
                "[DEBUG73-4] Quote Pain:",
                repr(review_quote_result.get("best_pain", "")),
                flush=True,
            )
            print(
                "[DEBUG73-4] Quote Benefit:",
                repr(review_quote_result.get("best_benefit", "")),
                flush=True,
            )
            print(
                "[DEBUG73-4] Quote Best:",
                repr(review_quote_result.get("best_quote", "")),
                flush=True,
            )

            outputs["review_quotes"] = review_quote_result

            print(
                "[Sprint73-2] Quote Selector:",
                bool(review_quote_result.get("ok")),
                flush=True,
            )
            print(
                "[Sprint73-2] Best Pain:",
                review_quote_result.get("best_pain", ""),
                flush=True,
            )
            print(
                "[Sprint73-2] Best Benefit:",
                review_quote_result.get("best_benefit", ""),
                flush=True,
            )
            print(
                "[Sprint73-2] Best Quote:",
                review_quote_result.get("best_quote", ""),
                flush=True,
            )
        except Exception as exc:
            outputs["review_quotes"] = review_quote_result
            print(
                "[Sprint73-2] Quote Selector ERROR:",
                repr(exc),
                flush=True,
            )
        try:
            print(
                "[UTF8 TRACE INSIGHT INPUT product_name]",
                repr(
                    getattr(project, "product_name", "")
                    or getattr(project, "title", "")
                    or "선택 상품"
                ),
                flush=True,
            )
            print(
                "[UTF8 TRACE INSIGHT INPUT merged_reviews]",
                repr(merged_reviews),
                flush=True,
            )
            print(
                "[UTF8 TRACE INSIGHT INPUT social_comments]",
                repr(
                    social_comment_result.get(
                        "comments",
                        [],
                    )
                ),
                flush=True,
            )

            review_insight_result = ReviewInsightEngine().analyze(
                reviews=merged_reviews,
                social_comments=social_comment_result.get(
                    "comments",
                    [],
                ),
                product_name=(
                    getattr(project, "product_name", "")
                    or getattr(project, "title", "")
                    or "선택 상품"
                ),
            )
            outputs["review_insight"] = review_insight_result
            print(
                "[Sprint101-2 Review Insight]",
                "Review Count:",
                review_insight_result.get("review_count", 0)
                if isinstance(review_insight_result, dict)
                else 0,
                "Keys:",
                len(review_insight_result)
                if isinstance(review_insight_result, dict)
                else 0,
                flush=True,
            )

            print(
                "[Sprint71-2] ReviewInsight:",
                bool(review_insight_result.get("ok")),
                "Review Count:",
                review_insight_result.get("review_count", 0),
                flush=True,
            )
        except Exception as exc:
            outputs["review_insight"] = {
                "ok": False,
                "version": "review-insight-engine-70-1",
                "review_count": len(merged_reviews),
                "social_comment_count": len(
                    social_comment_result.get("comments", [])
                ),
                "error": str(exc),
            }
            print(
                "[Sprint71-2] ReviewInsight ERROR:",
                repr(exc),
                flush=True,
            )
        # 10-2. Sprint73-3 Review Hook Generator
        try:
            print(
                "[UTF8 TRACE HOOK INPUT product_name]",
                repr(
                    getattr(project, "product_name", "")
                    or getattr(project, "title", "")
                    or "선택 상품"
                ),
                flush=True,
            )
            print(
                "[UTF8 TRACE HOOK INPUT review_insight]",
                repr(outputs.get("review_insight", {})),
                flush=True,
            )
            print(
                "[UTF8 TRACE HOOK INPUT review_quotes]",
                repr(outputs.get("review_quotes", {})),
                flush=True,
            )

            review_hook_result = ReviewHookGenerator().generate(
                review_quotes=outputs.get(
                    "review_quotes",
                    {},
                ),
                review_insight=outputs.get(
                    "review_insight",
                    {},
                ),
                product_name=(
                    getattr(project, "product_name", "")
                    or getattr(project, "title", "")
                    or "선택 상품"
                ),
                review_count=len(merged_reviews),
            )

            outputs["review_hooks"] = review_hook_result

            print(
                "[Sprint73-3] Hook Generator:",
                bool(review_hook_result.get("ok")),
                flush=True,
            )
            print(
                "[Sprint73-3] Best Hook:",
                review_hook_result.get("best_hook", ""),
                flush=True,
            )
            print(
                "[Sprint73-3] Hook Type:",
                review_hook_result.get("best_hook_type", ""),
                flush=True,
            )
            print(
                "[Sprint73-3] Hook Count:",
                len(review_hook_result.get("hooks", [])),
                flush=True,
            )

        except Exception as exc:
            outputs["review_hooks"] = {
                "ok": False,
                "version": "review-hook-generator-73-3",
                "best_hook": "",
                "hooks": [],
                "error": str(exc),
            }

            print(
                "[Sprint73-3] Hook Generator ERROR:",
                repr(exc),
                flush=True,
            )

        # =====================================
        # 10-2A. Sprint95-1 Hook Optimization Engine
        # =====================================
        try:
            optimized_review_hooks = HookOptimizer().apply_to_review_hooks(
                review_hooks=outputs.get(
                    "review_hooks",
                    {},
                ),
                review_insight=outputs.get(
                    "review_insight",
                    {},
                ),
                product_name=(
                    getattr(project, "product_name", "")
                    or getattr(project, "title", "")
                    or "선택 상품"
                ),
                review_count=len(merged_reviews),
            )

            outputs["review_hooks"] = optimized_review_hooks
            outputs["hook_optimizer"] = optimized_review_hooks.get(
                "hook_optimizer",
                {},
            )

        except Exception as exc:
            outputs["hook_optimizer"] = {
                "ok": False,
                "ready": False,
                "version": "hook-optimizer-95-1",
                "status": "failed",
                "best_hook": "",
                "ranking": [],
                "error": str(exc),
            }

            print(
                "[Sprint95-1 Hook Optimizer] ERROR:",
                repr(exc),
                flush=True,
            )

        # =====================================
        # Sprint137-1 Viral Purpose Pipeline
        # =====================================
        viral_pipeline_result = {
            "ok": False,
            "ready": False,
            "version": "viral-pipeline-137-1",
            "status": "skipped_no_local_viral_video",
            "video_path": "",
            "output_dir": "",
            "steps": {},
            "errors": [],
            "warnings": [],
        }

        try:
            sprint137_video_path = self._resolve_sprint137_viral_video_path(
                viral_video_sources=viral_video_sources,
                viral_library_result=viral_library_result,
            )
            sprint137_output_dir = (
                Path("assets")
                / "products"
                / f"project_{getattr(project, 'id', '')}"
                / "viral_pipeline_137_1"
            )

            if sprint137_video_path:
                current_review_insight = (
                    outputs.get("review_insight", {})
                    if isinstance(outputs.get("review_insight", {}), dict)
                    else {}
                )
                current_review_quotes = (
                    outputs.get("review_quotes", {})
                    if isinstance(outputs.get("review_quotes", {}), dict)
                    else {}
                )
                current_review_hooks = (
                    outputs.get("review_hooks", {})
                    if isinstance(outputs.get("review_hooks", {}), dict)
                    else {}
                )
                resolved_product_name = (
                    getattr(project, "product_name", "")
                    or getattr(project, "title", "")
                    or project_data.get("product_name", "")
                    or "선택 상품"
                )
                resolved_description = str(
                    project_data.get("product_description")
                    or project_data.get("description")
                    or getattr(project, "description", "")
                    or ""
                ).strip()
                resolved_brand = str(
                    project_data.get("brand_name")
                    or project_data.get("brand")
                    or getattr(project, "brand_name", "")
                    or ""
                ).strip()

                viral_pipeline_result = run_viral_pipeline(
                    video_path=sprint137_video_path,
                    output_dir=sprint137_output_dir,
                    product_name=resolved_product_name,
                    product_description=resolved_description,
                    brand_name=resolved_brand,
                    best_hook=str(
                        current_review_hooks.get("best_hook")
                        or current_review_insight.get("best_hook")
                        or ""
                    ).strip(),
                    best_pain=str(
                        current_review_quotes.get("best_pain")
                        or current_review_insight.get("best_pain")
                        or current_review_insight.get("best_pain_point")
                        or ""
                    ).strip(),
                    best_benefit=str(
                        current_review_quotes.get("best_benefit")
                        or current_review_insight.get("best_benefit")
                        or ""
                    ).strip(),
                    best_evidence=str(
                        current_review_quotes.get("best_quote")
                        or current_review_insight.get("best_evidence")
                        or ""
                    ).strip(),
                    cta_text="구매 전에는 상세 정보와 실제 사용 조건을 확인해보세요",
                    frame_interval_seconds=2.0,
                    max_thumbnail_count=30,
                    overwrite=True,
                )
            else:
                viral_pipeline_result["warnings"] = [
                    "Sprint137 분석에 사용할 로컬 바이럴 영상 파일이 없습니다."
                ]

        except Exception as exc:
            viral_pipeline_result = {
                **viral_pipeline_result,
                "ok": False,
                "ready": False,
                "status": "exception",
                "errors": [f"{type(exc).__name__}: {exc}"],
            }

        outputs["viral_pipeline"] = viral_pipeline_result
        outputs["viral_image_prompts"] = (
            viral_pipeline_result.get("steps", {}).get(
                "image_prompt_generator",
                {},
            )
            if isinstance(viral_pipeline_result, dict)
            else {}
        )
        print(
            "[Sprint137-1 Viral Pipeline] Version:",
            viral_pipeline_result.get("version", ""),
            flush=True,
        )
        print(
            "[Sprint137-1 Viral Pipeline] Status:",
            viral_pipeline_result.get("status", ""),
            flush=True,
        )
        print(
            "[Sprint137-1 Viral Pipeline] Video:",
            viral_pipeline_result.get("video_path", ""),
            flush=True,
        )
        print(
            "[Sprint137-1 Viral Pipeline] Final Output:",
            viral_pipeline_result.get("final_output_path", ""),
            flush=True,
        )
        print(
            "[Sprint137-1 Viral Pipeline] Errors:",
            viral_pipeline_result.get("errors", []),
            flush=True,
        )

        if locked_script:
            outputs["review_scripts"] = dict(approved_review_scripts)
            outputs["viral_script_director_feedback"] = {
                "ready": False,
                "status": "skipped_locked_script",
                "version": "locked-script-feedback-bypass-146-11",
            }
            print("[Sprint146-10 Late Script Generator] ReviewScriptGenerator: SKIPPED", flush=True)
        else:
            # =====================================
            # 10-3. Sprint73-4 Review Script Generator
            # =====================================
            try:
                import inspect

                print(
                    "[UTF8 TRACE ReviewScriptGenerator FILE]",
                    inspect.getfile(ReviewScriptGenerator),
                    flush=True,
                )
                print(
                    "[UTF8 TRACE ReviewScriptGenerator MODULE]",
                    ReviewScriptGenerator.__module__,
                    flush=True,
                )
                script_trace_payload = {
                    "workflow_version": self.WORKFLOW_VERSION,
                    "project_id": str(getattr(project, "id", "") or ""),
                    "product_name": (
                        getattr(project, "product_name", "")
                        or getattr(project, "title", "")
                        or "선택 상품"
                    ),
                    "review_count": len(merged_reviews),
                    "review_hooks": outputs.get("review_hooks", {}),
                    "review_quotes": outputs.get("review_quotes", {}),
                    "review_insight": outputs.get("review_insight", {}),
                    "story_intelligence": outputs.get("story_intelligence", {}),
                    "viral_pipeline": outputs.get("viral_pipeline", {}),
                }

                print(
                    "[UTF8 BEFORE SCRIPT product_name]",
                    repr(script_trace_payload.get("product_name", "")),
                    flush=True,
                )
                print(
                    "[UTF8 BEFORE SCRIPT review_insight.product_name]",
                    repr(
                        (script_trace_payload.get("review_insight") or {}).get(
                            "product_name",
                            "",
                        )
                        if isinstance(
                            script_trace_payload.get("review_insight"),
                            dict,
                        )
                        else ""
                    ),
                    flush=True,
                )
                print(
                    "[UTF8 BEFORE SCRIPT review_hooks.best_hook]",
                    repr(
                        (script_trace_payload.get("review_hooks") or {}).get(
                            "best_hook",
                            "",
                        )
                        if isinstance(
                            script_trace_payload.get("review_hooks"),
                            dict,
                        )
                        else ""
                    ),
                    flush=True,
                )

                script_trace_dir = (
                    Path("assets")
                    / "products"
                    / f"project_{getattr(project, 'id', '')}"
                )
                script_trace_dir.mkdir(parents=True, exist_ok=True)
                script_input_trace_path = (
                    script_trace_dir
                    / "utf8_before_review_script_generator.json"
                )
                script_input_trace_path.write_text(
                    json.dumps(
                        script_trace_payload,
                        ensure_ascii=False,
                        indent=2,
                        default=str,
                    ),
                    encoding="utf-8",
                )
                print(
                    "[UTF8 BEFORE SCRIPT JSON]",
                    str(script_input_trace_path),
                    flush=True,
                )

                review_script_result = ReviewScriptGenerator().generate(
                    review_hooks=outputs.get(
                        "review_hooks",
                        {},
                    ),
                    review_quotes=outputs.get(
                        "review_quotes",
                        {},
                    ),
                    review_insight=outputs.get(
                        "review_insight",
                        {},
                    ),
                    product_name=(
                        getattr(project, "product_name", "")
                        or getattr(project, "title", "")
                        or "선택 상품"
                    ),
                    review_count=len(merged_reviews),
                    story_intelligence=outputs.get(
                        "story_intelligence",
                        {},
                    ),
                    viral_pipeline=outputs.get(
                        "viral_pipeline",
                        {},
                    ),
                )
                print(
                    "[UTF8 TRACE review_script_result RAW]",
                    repr(review_script_result),
                    flush=True,
                )
                print(
                    "[Sprint143-3 Viral Script Feedback] Used:",
                    review_script_result.get("viral_influence_used", False),
                    flush=True,
                )
                print(
                    "[Sprint143-3 Viral Script Feedback] Pattern:",
                    review_script_result.get("viral_pattern", ""),
                    flush=True,
                )
                print(
                    "[Sprint143-3 Viral Script Feedback] Scene Subtitles:",
                    review_script_result.get("scene_subtitle_count", 0),
                    flush=True,
                )

                script_result_trace_path = (
                    script_trace_dir
                    / "utf8_after_review_script_generator.json"
                )
                script_result_trace_path.write_text(
                    json.dumps(
                        review_script_result,
                        ensure_ascii=False,
                        indent=2,
                        default=str,
                    ),
                    encoding="utf-8",
                )
                print(
                    "[UTF8 AFTER SCRIPT JSON]",
                    str(script_result_trace_path),
                    flush=True,
                )

                outputs["review_scripts"] = review_script_result

                viral_script_feedback_result = self._run_sprint143_2_viral_script_feedback(
                    viral_pipeline_result=outputs.get("viral_pipeline", {}),
                    review_script_result=review_script_result,
                    product_name=(
                        getattr(project, "product_name", "")
                        or getattr(project, "title", "")
                        or "선택 상품"
                    ),
                )
                outputs["viral_script_director_feedback"] = viral_script_feedback_result

                print(
                    "[Sprint120-4 Script Bridge] Version:",
                    review_script_result.get("scene_script_bridge_version", ""),
                    flush=True,
                )
                print(
                    "[Sprint120-4 Script Bridge] Scene Subtitles:",
                    review_script_result.get("scene_subtitle_count", 0),
                    flush=True,
                )
                print(
                    "[Sprint120-4 Script Bridge] Template:",
                    {
                        "version": review_script_result.get("story_template_version", ""),
                        "category": review_script_result.get("story_template_category", ""),
                        "key": review_script_result.get("story_template_key", ""),
                    },
                    flush=True,
                )

                print(
                    "[Sprint73-4] Script Generator:",
                    bool(review_script_result.get("ok")),
                    flush=True,
                )
                print(
                    "[Sprint73-4] Script Count:",
                    review_script_result.get("script_count"),
                    flush=True,
                )
                print(
                    "[Sprint73-4] Best Script:",
                    review_script_result.get("best_script"),
                    flush=True,
                )
                print(
                    "[Sprint73-4] Script Type:",
                    review_script_result.get("best_script_type"),
                    flush=True,
                )

            except Exception as exc:
                outputs["review_scripts"] = {
                    "ok": False,
                    "version": "review-script-generator-73-4",
                    "best_script": "",
                    "scripts": [],
                    "error": str(exc),
                }

                print(
                    "[Sprint73-4] Script Generator ERROR:",
                    repr(exc),
                    flush=True,
                )

        # Sprint146-4: 후반 Legacy ReviewScriptGenerator가 승인 대본을 덮어쓰지 못하게 최종 복원합니다.
        if approved_review_scripts and approved_script_text:
            locked_review_scripts = dict(approved_review_scripts)
            locked_review_scripts["best_script"] = approved_script_text
            locked_review_scripts["status"] = "approved_script_locked"
            locked_review_scripts["approved_full_pipeline"] = True
            outputs["review_scripts"] = locked_review_scripts
            print(
                "[Sprint146-5 Locked Script Final Lock] READY FOR SUBTITLE/VOICE:",
                len(approved_script_text),
                flush=True,
            )

        # 11. Content Factory
        try:
            content_pack = {
                "project": project,
                "project_id": getattr(project, "id", ""),
                "project_name": (
                    getattr(project, "product_name", "")
                    or getattr(project, "title", "")
                    or "선택 상품"
                ),
                "product_name": getattr(project, "product_name", ""),
                # Sprint131-8: ContentFactory와 VideoPipeline 입력을 새 Image Motion으로 고정합니다.
                "video_path": str(outputs.get("ai_video_path") or ""),
                "source_video_path": str(outputs.get("ai_video_path") or ""),
                "active_video_path": str(outputs.get("ai_video_path") or ""),
                "merged_video_path": str(
                    (outputs.get("product_image_video_fallback") or {}).get("canonical_merged_path")
                    or outputs.get("ai_video_path")
                    or ""
                ),
                "reviews": merged_reviews,
                "review_data": merged_reviews,
                "coupang_reviews": (
                    outputs.get("product_plan", {}).get(
                        "coupang_reviews",
                        [],
                    )
                ),
                "ocr_reviews": (
                    outputs.get("product_plan", {}).get(
                        "ocr_reviews",
                        [],
                    )
                ),
                "review_ocr": outputs.get("review_ocr", {}),
                "review_clean": outputs.get("review_clean", {}),
                "review_quotes": outputs.get(
                    "review_quotes",
                    {},
                ),
                "review_hooks": outputs.get(
                    "review_hooks",
                    {},
                ),
                # Sprint150-5: 최종 Subtitle/Voice 입력은 잠금 대본 원본만 전달합니다.
                # AI 이미지용 scene_goal/scene_prompt/camera_direction은 이 경로에
                # 포함하지 않습니다.
                "review_scripts": outputs.get(
                    "review_scripts",
                    {},
                ),
                "locked_script": approved_script_text if locked_script else "",
                "subtitle_source": (
                    "locked_user_script_only" if locked_script
                    else "review_script_scene_subtitles_only"
                ),
                "target_duration_seconds": 25.0,
                "review_hook": (
                    outputs.get(
                        "review_hooks",
                        {},
                    )
                    or {}
                ).get(
                    "best_hook",
                    "",
                ),
                "review_count": len(merged_reviews),
                "review_source": (
                    outputs.get("product_plan", {}).get(
                        "review_source",
                        "none",
                    )
                ),
                "review_collect_status": (
                    outputs.get("product_plan", {}).get(
                        "review_collect_status",
                        "empty",
                    )
                ),
                "social_comments": outputs.get(
                    "social_comments",
                    {},
                ).get(
                    "comments",
                    [],
                ),
                "social_comment_result": outputs.get(
                    "social_comments",
                    {},
                ),
                "review_insight": outputs.get(
                    "review_insight",
                    {},
                ),
                "video_candidates": enriched_candidates,
                "candidate_selection": outputs.get(
                    "candidate_selection",
                    {},
                ),
                "candidate_ranking": outputs.get(
                    "candidate_ranking",
                    {},
                ),
                "composer_candidate": outputs.get(
                    "composer_candidate"
                ),
                "real_vision": outputs.get("real_vision", {}),
                "video_quality": outputs.get("video_quality", {}),
                "shopping_shorts_fit": outputs.get(
                    "shopping_shorts_fit",
                    {},
                ),
                "shopping_fit": outputs.get(
                    "shopping_shorts_fit",
                    {},
                ),
                "viral_pattern": outputs.get("viral_pattern", {}),
                "auto_editor": outputs.get("auto_editor", {}),
            }

            content_pack, render_guard_stats = self._sprint112_1_render_guard(
                content_pack
            )
            outputs["render_guard"] = {
                "ok": True,
                "version": "final-render-input-guard-112-1",
                **render_guard_stats,
            }

            print(
                "[Sprint112-1 Render Guard] Version: final-render-input-guard-112-1",
                flush=True,
            )
            print(
                "[Sprint112-1 Render Guard] Review Images Removed:",
                render_guard_stats.get("review_images_removed", 0),
                flush=True,
            )
            print(
                "[Sprint112-1 Render Guard] Review Scenes Checked:",
                render_guard_stats.get("review_scenes_checked", 0),
                flush=True,
            )
            print(
                "[Sprint112-1 Render Guard] Subtitle Source:",
                render_guard_stats.get("subtitle_source", "narration_only"),
                flush=True,
            )
            print(
                "[Sprint112-1 Render Guard] Director Fields Removed:",
                render_guard_stats.get("director_fields_removed", 0),
                flush=True,
            )
            print(
                "[Sprint112-1 Render Guard] Director Prompt Lines Removed:",
                render_guard_stats.get("director_prompt_removed", 0),
                flush=True,
            )
            if locked_script:
                guarded_review_scripts = content_pack.get("review_scripts") or {}
                guarded_scene_subtitles = [
                    " ".join(str(item.get("subtitle") or "").split()).strip()
                    for item in list(guarded_review_scripts.get("scene_subtitles") or [])
                    if isinstance(item, dict)
                    and " ".join(str(item.get("subtitle") or "").split()).strip()
                ]
                print(
                    "[Sprint150-5 Locked Subtitle Guard] Final Subtitle Count:",
                    len(guarded_scene_subtitles),
                    flush=True,
                )
                print(
                    "[Sprint150-5 Locked Subtitle Guard] Director Text In Subtitle: False",
                    flush=True,
                )
                print(
                    "[Sprint150-5 Duration] Target Seconds: 25.0",
                    flush=True,
                )

            content_factory_result = ContentFactory().apply_edit_assistant(
                content_pack,
                project=project,
            )

            if not isinstance(content_factory_result, dict):
                content_factory_result = {
                    "ok": bool(content_factory_result),
                    "raw_result": content_factory_result,
                }

            content_factory_result["reviews"] = merged_reviews
            content_factory_result["review_count"] = len(merged_reviews)
            content_factory_result["review_ocr"] = outputs.get(
                "review_ocr",
                {},
            )
            content_factory_result["review_clean"] = outputs.get(
                "review_clean",
                {},
            )
            content_factory_result["review_quotes"] = outputs.get(
                "review_quotes",
                {},
            )
            content_factory_result["review_insight"] = outputs.get(
                "review_insight",
                {},
            )
            content_factory_result["social_comments"] = outputs.get(
                "social_comments",
                {},
            )

            print(
                "[Sprint71-2] Content Review Input:",
                {
                    "review_count": len(merged_reviews),
                    "review_insight_ok": bool(
                        (outputs.get("review_insight") or {}).get("ok")
                    ),
                    "review_source": (
                        outputs.get("product_plan") or {}
                    ).get(
                        "review_source",
                        "none",
                    ),
                },
                flush=True,
            )

            outputs["content_factory"] = content_factory_result
            outputs["video_pipeline"] = content_factory_result.get(
                "video_pipeline",
                {},
            )

            print(
                "[Sprint71-2] Content Factory:",
                bool(content_factory_result),
                flush=True,
            )
            print(
                "[Sprint71-2] Content Review Count:",
                len(merged_reviews),
                flush=True,
            )
            print(
                "[Sprint71-2] Video Pipeline:",
                bool(content_factory_result.get("video_pipeline")),
                flush=True,
            )
            print(
                "[Sprint71-2] Final Video:",
                content_factory_result.get(
                    "video_pipeline",
                    {},
                ).get(
                    "output_path",
                    "",
                ),
                flush=True,
            )

            state.update_step(
                job_id,
                "content_factory",
                "done",
                {
                    "review_count": len(merged_reviews),
                    "ocr_review_count": review_ocr_result.get(
                        "review_count",
                        0,
                    ),
                    "video_pipeline": bool(
                        content_factory_result.get("video_pipeline")
                    ),
                    "output_path": content_factory_result.get(
                        "video_pipeline",
                        {},
                    ).get(
                        "output_path",
                        "",
                    ),
                },
            )

        except Exception as exc:
            outputs["content_factory"] = {}
            outputs["video_pipeline"] = {}

            print(
                "[Sprint71-2] Content Factory ERROR:",
                repr(exc),
                flush=True,
            )

            state.update_step(
                job_id,
                "content_factory",
                "failed",
                error=exc,
            )

        # 12. CapCut Export
        try:
            export_paths = (
                CapCutProjectExporter().export_plan(
                    project,
                    editor_plan,
                )
            )

            outputs["capcut_export"] = export_paths

            state.update_step(
                job_id,
                "capcut_export",
                "done",
                export_paths,
            )

        except Exception as exc:
            outputs["capcut_export"] = {}

            state.update_step(
                job_id,
                "capcut_export",
                "failed",
                error=exc,
            )

        # 13. Sprint84-1 Publisher + Queue + Dispatcher + Real YouTube Upload Integration
        publisher_result = {
            "ok": False,
            "version": "publisher-engine-82-1",
            "status": "not_run",
            "publisher_ready": False,
            "platforms": {},
        }
        publisher_orchestrator_result = {
            "ok": False,
            "version": "publisher-orchestrator-82-5",
            "status": "not_run",
            "orchestrator_ready": False,
            "platforms": {},
        }
        publisher_store_result = {
            "ok": False,
            "version": "publisher-result-store-82-7",
            "status": "not_run",
            "stored": False,
            "manifest_path": "",
            "platform_paths": {},
        }
        outputs["publisher_store"] = publisher_store_result
        upload_queue_result = {
            "ok": False,
            "version": "upload-queue-engine-82-9",
            "status": "not_run",
            "queued": False,
            "queue_ready": False,
            "queue_path": "",
            "latest_pointer_path": "",
            "jobs": {},
        }
        outputs["upload_queue"] = upload_queue_result
        upload_dispatcher_result = {
            "ok": False,
            "version": "upload-dispatcher-83-1",
            "status": "not_run",
            "dispatch_ready": False,
            "dispatch_count": 0,
            "dispatch_jobs": {},
        }
        outputs["upload_dispatcher"] = upload_dispatcher_result
        youtube_upload_result = {
            "ok": False,
            "version": "youtube-upload-executor-83-2",
            "status": "not_run",
            "platform": "youtube_shorts",
            "dry_run": False,
            "upload_ready": False,
            "actual_upload_performed": False,
        }
        outputs["youtube_upload"] = youtube_upload_result
        outputs["youtube"] = self._build_youtube_upload_summary(
            youtube_upload_result
        )
        outputs["youtube_manifest"] = {
            "ok": False,
            "version": "youtube-manifest-store-85-1",
            "status": "not_run",
            "manifest_path": "",
            "video_id": "",
            "watch_url": "",
            "uploaded_at": "",
        }
        outputs["youtube_project"] = {
            "ok": False,
            "version": "project-repository-86-1",
            "status": "not_run",
            "project_id": getattr(project, "id", ""),
            "video_id": "",
            "watch_url": "",
            "uploaded_at": "",
            "manifest_path": "",
        }
        instagram_upload_result = {
            "ok": False,
            "version": "instagram-playwright-upload-executor-90-2",
            "status": "not_run",
            "platform": "instagram_reels",
            "dry_run": False,
            "upload_ready": False,
            "actual_upload_performed": False,
        }
        outputs["instagram_upload"] = instagram_upload_result
        outputs["instagram"] = self._build_instagram_upload_summary(
            instagram_upload_result
        )
        outputs["instagram_manifest"] = {
            "ok": False,
            "version": "instagram-manifest-store-90-2",
            "status": "not_run",
            "manifest_path": "",
            "post_url": "",
            "uploaded_at": "",
        }
        outputs["instagram_project"] = {
            "ok": False,
            "version": "project-repository-90-2",
            "status": "not_run",
            "project_id": getattr(project, "id", ""),
            "post_url": "",
            "uploaded_at": "",
            "manifest_path": "",
        }

        try:
            review_scripts = (
                outputs.get("review_scripts")
                if isinstance(outputs.get("review_scripts"), dict)
                else {}
            )
            print(
                "[UTF8 TRACE review_scripts RAW]",
                repr(review_scripts),
                flush=True,
            )
            export_pack = (
                review_scripts.get("export_pack")
                if isinstance(review_scripts.get("export_pack"), dict)
                else {}
            )

            if not export_pack:
                locked_user_script = bool(
                    review_scripts.get("locked_user_script")
                )
                locked_script_raw = (
                    review_scripts.get("best_script")
                    or review_scripts.get("original_best_script")
                    or review_scripts.get("long_script")
                    or review_scripts.get("medium_script")
                    or review_scripts.get("short_script")
                    or ""
                )
                locked_script_text = str(locked_script_raw).strip()

                if locked_user_script and locked_script_text:
                    locked_product_raw = (
                        review_scripts.get("product_name")
                        or getattr(project, "product_name", "")
                        or getattr(project, "title", "")
                        or ""
                    )
                    locked_product_name = str(locked_product_raw).strip()
                    locked_title = (
                        f"{locked_product_name} 쇼츠"
                        if locked_product_name
                        else "쇼핑 쇼츠"
                    )
                    locked_description = locked_script_text
                    locked_hook = next(
                        (
                            line.strip()
                            for line in locked_script_text.splitlines()
                            if line.strip()
                            and not re.match(
                                r"^scene\s*\d+",
                                line.strip(),
                                flags=re.IGNORECASE,
                            )
                        ),
                        locked_title,
                    )
                    locked_cta = "👉 궁금하시면 클릭! 👇"
                    locked_hashtags = ["쇼핑쇼츠", "제품리뷰"]
                    if locked_product_name:
                        safe_product_tag = re.sub(
                            r"[^0-9A-Za-z가-힣_]",
                            "",
                            locked_product_name.replace(" ", ""),
                        )
                        if safe_product_tag:
                            locked_hashtags.insert(0, safe_product_tag)

                    export_pack = {
                        "ok": True,
                        "ready": True,
                        "version": "locked-user-script-publisher-pack-146-6",
                        "status": "ready",
                        "validation_passed": True,
                        "product_name": locked_product_name,
                        "title": locked_title,
                        "description": locked_description,
                        "best_hook": locked_hook,
                        "best_script": locked_script_text,
                        "platform_scripts": {
                            "tiktok": locked_script_text,
                            "instagram_reels": locked_script_text,
                            "youtube_shorts": locked_script_text,
                        },
                        "platform_cta": {
                            "tiktok": locked_cta,
                            "instagram_reels": locked_cta,
                            "youtube_shorts": locked_cta,
                        },
                        "hashtags": locked_hashtags,
                        "hashtag_text": " ".join(
                            f"#{tag}" for tag in locked_hashtags
                        ),
                        "thumbnail_prompt": "",
                        "metadata": {
                            "generator_version": (
                                "locked-user-script-publisher-pack-builder-146-6"
                            ),
                            "source_script_version": str(
                                review_scripts.get("version") or ""
                            ).strip(),
                            "locked_user_script": True,
                        },
                    }
                    review_scripts["export_pack"] = export_pack
                    outputs["review_scripts"] = review_scripts
                    outputs["locked_script_publisher_pack"] = export_pack
                    print(
                        "[Sprint146-6 Publisher Pack] Built:",
                        True,
                        flush=True,
                    )
                    print(
                        "[Sprint146-6 Publisher Pack] Version:",
                        export_pack.get("version"),
                        flush=True,
                    )
                    print(
                        "[Sprint146-6 Publisher Pack] Script Length:",
                        len(locked_script_text),
                        flush=True,
                    )
                else:
                    raise ValueError(
                        "게시용 export_pack과 잠금 사용자 대본이 모두 없습니다"
                    )

            # Sprint128-1: Publisher 호출 직전 게시 Pack의
            # 제목·본문·해시태그 문자열이 이미 깨져 있는지 원본 그대로 검사합니다.
            print(
                "[UTF8 TRACE export_pack RAW]",
                repr(export_pack),
                flush=True,
            )
            
            utf8_export_guard = PublisherUTF8Guard.inspect(
                export_pack,
                stage="export_pack_before_publisher",
            )
            print(
                "[UTF8 TRACE export_pack RAW]",
                repr(export_pack),
                flush=True,
            )

            outputs["publisher_utf8_export_guard"] = utf8_export_guard

            publisher_result = PublisherEngine().build(
                export_pack=export_pack,
            )

            print(
                "[UTF8 TRACE publisher_result RAW]",
                repr(publisher_result),
                flush=True,
            )

            outputs["publisher"] = publisher_result

            # Sprint128-1: Publisher 결과를 같은 기준으로 다시 검사해
            # 최초 손상 지점이 Export Pack인지 Publisher 내부인지 확정합니다.
            utf8_publisher_guard = PublisherUTF8Guard.inspect(
                publisher_result,
                stage="publisher_result_after_build",
            )
            outputs["publisher_utf8_result_guard"] = utf8_publisher_guard
            outputs["publisher_utf8_guard"] = PublisherUTF8Guard.compare(
                utf8_export_guard,
                utf8_publisher_guard,
            )

            final_video_path = str(
                (
                    outputs.get("video_pipeline")
                    if isinstance(outputs.get("video_pipeline"), dict)
                    else {}
                ).get("output_path", "")
                or str(outputs.get("ai_video_path") or "")
                or ""
            )
            affiliate_link = str(
                getattr(project, "partner_url", "")
                or (
                    outputs.get("product_plan")
                    if isinstance(outputs.get("product_plan"), dict)
                    else {}
                ).get("partner_url", "")
                or ""
            )

            publisher_orchestrator_result = (
                PublisherOrchestrator().build(
                    publisher_result=publisher_result,
                    video_path=final_video_path,
                    affiliate_link=affiliate_link,
                )
            )
            outputs["publisher_orchestrator"] = (
                publisher_orchestrator_result
            )

            print(
                "[Sprint83-3 Publisher] Export Ready:",
                bool(export_pack.get("ready")),
                flush=True,
            )
            print(
                "[Sprint83-3 Publisher] Engine Ready:",
                bool(publisher_result.get("publisher_ready")),
                flush=True,
            )
            print(
                "[Sprint83-3 Publisher] Orchestrator Ready:",
                bool(
                    publisher_orchestrator_result.get(
                        "orchestrator_ready"
                    )
                ),
                flush=True,
            )
            print(
                "[Sprint83-3 Publisher] Ready Platforms:",
                publisher_orchestrator_result.get(
                    "ready_platforms",
                    [],
                ),
                flush=True,
            )
            print(
                "[Sprint83-3 Publisher] Video:",
                final_video_path,
                flush=True,
            )

            # Sprint102-4: 제작 엔진이 완성될 때까지 저장·큐·실제 업로드를 잠시 중지합니다.
            publisher_store_result = {
                "ok": True,
                "version": "publisher-result-store-82-7",
                "status": "skipped_upload_paused",
                "stored": False,
                "manifest_path": "",
                "latest_pointer_path": "",
                "platform_paths": {},
            }
            outputs["publisher_store"] = publisher_store_result

            upload_queue_result = {
                "ok": True,
                "version": "upload-queue-engine-82-9",
                "status": "skipped_upload_paused",
                "queued": False,
                "queue_ready": False,
                "queue_path": "",
                "latest_pointer_path": "",
                "jobs": {},
                "ready_jobs": [],
            }
            outputs["upload_queue"] = upload_queue_result

            upload_dispatcher_result = {
                "ok": True,
                "version": "upload-dispatcher-83-1",
                "status": "skipped_upload_paused",
                "dispatch_ready": False,
                "dispatch_count": 0,
                "dispatch_jobs": {},
            }
            outputs["upload_dispatcher"] = upload_dispatcher_result

            youtube_upload_result = {
                "ok": True,
                "version": "youtube-upload-executor-83-2",
                "status": "skipped_upload_paused",
                "platform": "youtube_shorts",
                "dry_run": False,
                "upload_ready": False,
                "actual_upload_performed": False,
                "errors": [],
                "warnings": ["Sprint102-4에서 실제 업로드를 잠시 중지했습니다."],
            }
            outputs["youtube_upload"] = youtube_upload_result
            outputs["youtube"] = self._build_youtube_upload_summary(
                youtube_upload_result
            )
            outputs["youtube_manifest"] = {
                "ok": True,
                "version": "youtube-manifest-store-85-1",
                "status": "skipped_upload_paused",
                "manifest_path": "",
                "video_id": "",
                "watch_url": "",
                "uploaded_at": "",
            }
            outputs["youtube_project"] = {
                "ok": True,
                "version": "project-repository-86-1",
                "status": "skipped_upload_paused",
                "project_id": getattr(project, "id", ""),
                "video_id": "",
                "watch_url": "",
                "uploaded_at": "",
                "manifest_path": "",
            }

            instagram_upload_result = {
                "ok": True,
                "version": "instagram-playwright-upload-executor-90-2",
                "status": "skipped_upload_paused",
                "platform": "instagram_reels",
                "dry_run": False,
                "upload_ready": False,
                "actual_upload_performed": False,
                "errors": [],
                "warnings": ["Sprint102-4에서 실제 업로드를 잠시 중지했습니다."],
            }
            outputs["instagram_upload"] = instagram_upload_result
            outputs["instagram"] = self._build_instagram_upload_summary(
                instagram_upload_result
            )
            outputs["instagram_manifest"] = {
                "ok": True,
                "version": "instagram-manifest-store-90-2",
                "status": "skipped_upload_paused",
                "manifest_path": "",
                "post_url": "",
                "uploaded_at": "",
            }
            outputs["instagram_project"] = {
                "ok": True,
                "version": "project-repository-90-2",
                "status": "skipped_upload_paused",
                "project_id": getattr(project, "id", ""),
                "post_url": "",
                "uploaded_at": "",
                "manifest_path": "",
            }

            outputs["upload_pause"] = {
                "ok": True,
                "version": "upload-pause-102-4",
                "status": "disabled",
                "publisher_payload": "ready",
                "publisher_store": "skipped",
                "queue": "skipped",
                "dispatcher": "skipped",
                "youtube": "skipped",
                "instagram": "skipped",
                "tiktok": "skipped",
            }

            print(
                "[Sprint102-4 Upload Pause] Status: disabled",
                flush=True,
            )
            print(
                "[Sprint102-4 Upload Pause] Publisher Payload: ready",
                flush=True,
            )
            print(
                "[Sprint102-4 Upload Pause] Store/Queue/Dispatcher: skipped",
                flush=True,
            )
            print(
                "[Sprint102-4 Upload Pause] YouTube: skipped",
                flush=True,
            )
            print(
                "[Sprint102-4 Upload Pause] Instagram: skipped",
                flush=True,
            )
            print(
                "[Sprint102-4 Upload Pause] TikTok: skipped",
                flush=True,
            )

        except Exception as exc:
            publisher_result = {
                "ok": False,
                "version": "publisher-engine-82-1",
                "status": "failed",
                "publisher_ready": False,
                "platforms": {},
                "error": str(exc),
            }
            publisher_orchestrator_result = {
                "ok": False,
                "version": "publisher-orchestrator-82-5",
                "status": "failed",
                "orchestrator_ready": False,
                "platforms": {},
                "error": str(exc),
            }
            outputs["publisher"] = publisher_result
            outputs["publisher_orchestrator"] = (
                publisher_orchestrator_result
            )
            publisher_store_result = {
                "ok": False,
                "version": "publisher-result-store-82-7",
                "status": "skipped",
                "stored": False,
                "manifest_path": "",
                "platform_paths": {},
                "error": str(exc),
            }
            outputs["publisher_store"] = publisher_store_result
            upload_queue_result = {
                "ok": False,
                "version": "upload-queue-engine-82-9",
                "status": "skipped",
                "queued": False,
                "queue_ready": False,
                "queue_path": "",
                "latest_pointer_path": "",
                "jobs": {},
                "error": str(exc),
            }
            outputs["upload_queue"] = upload_queue_result
            upload_dispatcher_result = {
                "ok": False,
                "version": "upload-dispatcher-83-1",
                "status": "skipped",
                "dispatch_ready": False,
                "dispatch_count": 0,
                "dispatch_jobs": {},
                "error": str(exc),
            }
            outputs["upload_dispatcher"] = (
                upload_dispatcher_result
            )
            youtube_upload_result = {
                "ok": False,
                "version": "youtube-upload-executor-83-2",
                "status": "skipped",
                "platform": "youtube_shorts",
                "dry_run": False,
                "upload_ready": False,
                "actual_upload_performed": False,
                "error": str(exc),
            }
            outputs["youtube_upload"] = youtube_upload_result

            youtube_summary = self._build_youtube_upload_summary(
                youtube_upload_result
            )
            outputs["youtube"] = youtube_summary
            outputs["youtube_manifest"] = (
                self._persist_youtube_upload_metadata(
                    publisher_store_result,
                    youtube_summary,
                )
            )
            outputs["youtube_project"] = (
                ProjectRepository().update_youtube_upload(
                    project_id=getattr(project, "id", ""),
                    upload_result=youtube_summary,
                    manifest_result=outputs["youtube_manifest"],
                )
            )

            print(
                "[Sprint86-2 Project DB] Saved:",
                bool(
                    outputs["youtube_project"].get("ok")
                ),
                flush=True,
            )
            print(
                "[Sprint86-2 Project DB] Status:",
                outputs["youtube_project"].get(
                    "status",
                    "",
                ),
                flush=True,
            )

            print(
                "[Sprint85-1 YouTube] Status:",
                youtube_summary.get("status", ""),
                flush=True,
            )
            print(
                "[Sprint85-1 YouTube] Video ID:",
                youtube_summary.get("video_id", ""),
                flush=True,
            )
            print(
                "[Sprint85-1 YouTube] Watch URL:",
                youtube_summary.get("watch_url", ""),
                flush=True,
            )

            print(
                "[Sprint83-3 Publisher] ERROR:",
                repr(exc),
                flush=True,
            )

        # Sprint146-4: ContentFactory 최종 산출물을 canonical final.mp4로 고정합니다.
        project_id_final = str(getattr(project, "id", "") or "default")
        canonical_final_path = Path("exports") / "videos" / f"{project_id_final}_final.mp4"
        video_pipeline_result = (
            outputs.get("video_pipeline")
            if isinstance(outputs.get("video_pipeline"), dict)
            else {}
        )
        produced_final_path = str(video_pipeline_result.get("output_path") or "").strip()
        finalization_errors = []
        try:
            if produced_final_path and Path(produced_final_path).is_file():
                canonical_final_path.parent.mkdir(parents=True, exist_ok=True)
                if Path(produced_final_path).resolve() != canonical_final_path.resolve():
                    shutil.copy2(produced_final_path, canonical_final_path)
            final_ready = canonical_final_path.is_file() and canonical_final_path.stat().st_size > 1024
        except Exception as exc:
            final_ready = False
            finalization_errors.append(f"{type(exc).__name__}: {exc}")

        outputs["final_video"] = {
            "ok": final_ready,
            "ready": final_ready,
            "version": "locked-script-full-video-finalizer-146-5b",
            "status": "final_created" if final_ready else "final_missing",
            "output_path": str(canonical_final_path) if final_ready else produced_final_path,
            "source_output_path": produced_final_path,
            "script_status": script_status,
            "pipeline": ["ImageMotion", "Subtitle", "Voice", "Merge", "final.mp4"],
            "errors": finalization_errors,
        }
        outputs["next_stage_gate"] = {
            "version": "locked-script-full-pipeline-gate-146-5b",
            "execution_mode": "locked_script_full_pipeline",
            "status": "COMPLETED_FINAL_MP4" if final_ready else "PIPELINE_COMPLETED_FINAL_MISSING",
            "script_approved": True,
            "scene_image_motion_video_executed": True,
            "final_video_path": outputs["final_video"].get("output_path", ""),
        }
        print("[Sprint146-5 Final Pipeline] ImageMotion:", outputs.get("ai_video_path", ""), flush=True)
        print("[Sprint146-5 Final Pipeline] Subtitle/Voice/Merge:", produced_final_path, flush=True)
        print("[Sprint146-5 Final Pipeline] FINAL:", outputs["final_video"]["status"], outputs["final_video"]["output_path"], flush=True)

        final_state = state.load(job_id)

        print(
            "######## RUN_PROJECT SPRINT103-2 END ########",
            flush=True,
        )

        return {
            "job_id": job_id,
            "state": final_state,
            "outputs": outputs,
            "summary": self.summary(final_state),
        }

    def summary(self, state):
        errors = state.get("errors", [])
        progress = state.get("progress", 0)

        if errors:
            return (
                f"One Click Pipeline {progress}% 완료, "
                f"오류 {len(errors)}건이 있습니다. "
                "가능한 단계는 계속 진행했습니다."
            )

        return (
            f"One Click Pipeline {progress}% "
            "완료되었습니다."
        )

    def _compact(self, product_plan):
        if not isinstance(product_plan, dict):
            return {}

        return {
            "product": (
                product_plan.get(
                    "project_payload",
                    {},
                ).get("product_name")
            ),
            "keyword": (
                product_plan.get(
                    "project_payload",
                    {},
                ).get("keyword")
            ),
            "taobao": (
                product_plan.get(
                    "keywords",
                    {},
                ).get("taobao_keyword")
            ),
            "douyin": (
                product_plan.get(
                    "keywords",
                    {},
                ).get("douyin_keyword")
            ),
        }
