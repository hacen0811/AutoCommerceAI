from uuid import uuid4
from pathlib import Path
import hashlib
import json
import mimetypes
import re
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
from modules.publisher.publisher_engine import PublisherEngine
from modules.publisher.publisher_orchestrator import PublisherOrchestrator
from modules.publisher.publisher_result_store import PublisherResultStore
from modules.publisher.upload_queue_engine import UploadQueueEngine
from modules.publisher.upload_dispatcher import UploadDispatcher
from modules.publisher.youtube_upload_executor import YouTubeUploadExecutor
from modules.publisher.instagram_upload_executor import InstagramUploadExecutor
from modules.video.ai_video_engine import AIVideoEngine
from modules.video.gemini_veo_provider import GeminiVeoProvider
from modules.video.ai_scene_merger import AISceneMerger
from modules.story import StoryIntelligenceEngine
from modules.image_ai.image_pool_builder import ImagePoolBuilder
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


print("######## WORKFLOW_ENGINE SPRINT121-1 LOADED ########", flush=True)


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

    WORKFLOW_VERSION = "workflow-engine-121-1"

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
            "subtitle_source": "narration_only",
        }

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

                for key, child in value.items():
                    key_lower = str(key).lower()
                    if key_lower in director_keys or any(
                        token in key_lower
                        for token in ("scene_goal", "visual_direction", "must_show", "camera_instruction", "director_note")
                    ):
                        stats["director_fields_removed"] += 1
                        continue

                    if key_lower in text_keys and isinstance(child, str):
                        if key_lower in {"subtitle", "subtitles", "caption", "caption_text", "display_text"} and preferred_spoken:
                            result[key] = preferred_spoken
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

    def run_project(
        self,
        project,
        sample_count=6,
        review_image_paths=None,
        review_text="",
        product_image_paths=None,
        product_image_path="",
        youtube_privacy_status="private",
    ):
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
            return self._run_project_impl(
                project=project,
                sample_count=sample_count,
                review_image_paths=review_image_paths,
                review_text=review_text,
                product_image_paths=product_image_paths,
                product_image_path=product_image_path,
                youtube_privacy_status=youtube_privacy_status,
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
        product_image_paths=None,
        product_image_path="",
        youtube_privacy_status="private",
    ):
        review_image_paths = review_image_paths or []
        review_text = str(review_text or "").strip()
        product_image_paths = product_image_paths or []
        youtube_privacy_status = (
            self._normalize_youtube_privacy_status(
                youtube_privacy_status
            )
        )
        print(
            "######## RUN_PROJECT SPRINT103-2 START ########",
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

        auto_connected = self.auto_connect_latest_download(
            project
        )

        if auto_connected.get("ok"):
            project = resolver.resolve_project(project)

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
        multi_image_mode = multi_image_input_count >= 2
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

        if len(manual_product_image_paths) == 1:
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
        if selector_sources and ImageExtractor is not None:
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

        outputs = {
            "workflow_version": self.WORKFLOW_VERSION,
            "auto_connected": auto_connected,
            "youtube_privacy_status": youtube_privacy_status,
            "image_extractor": image_extractor_result,
            "image_strip_splitter": image_strip_result,
        }

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
        gemini_director_result = {
            "ok": False,
            "ready": False,
            "version": GeminiDirector.VERSION,
            "status": "not_run",
            "scenes": [],
            "errors": [],
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

        try:
            vision_analysis_result = ImageVisionAnalyzer().analyze(
                images=product_images,
                manifest_path=multi_image_result.get("manifest_path", ""),
                output_dir=director_output_dir,
                product_name=product_name_for_director,
                project_id=project_id_for_director,
                save_result=True,
            )
        except Exception as exc:
            vision_analysis_result.update(
                status="failed",
                errors=[f"{type(exc).__name__}: {exc}"],
            )

        outputs["vision_analysis"] = vision_analysis_result
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
                target_duration_seconds=36,
                target_scene_count=6,
                save_result=True,
            )
        except Exception as exc:
            scene_plan_result.update(
                status="failed",
                errors=[f"{type(exc).__name__}: {exc}"],
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

        try:
            gemini_director_result = GeminiDirector().build(
                scene_selection=scene_selection_result,
                scene_selection_path=scene_selection_result.get(
                    "scene_selection_path",
                    "",
                ),
                vision_analysis=vision_analysis_result,
                vision_analysis_path=vision_analysis_result.get(
                    "analysis_path",
                    "",
                ),
                image_tags=image_tags_result,
                image_tags_path=image_tags_result.get(
                    "tag_manifest_path",
                    "",
                ),
                product_name=product_name_for_director,
                project_id=project_id_for_director,
                model_name="veo",
                language="en",
            )
        except Exception as exc:
            gemini_director_result.update(
                status="failed",
                errors=[f"{type(exc).__name__}: {exc}"],
            )

        outputs["gemini_director"] = gemini_director_result
        print(
            "[Sprint93-6A Gemini Director] Version:",
            gemini_director_result.get("version", ""),
            flush=True,
        )
        print(
            "[Sprint93-6A Gemini Director] Status:",
            gemini_director_result.get("status", ""),
            flush=True,
        )
        print(
            "[Sprint93-6A Gemini Director] Count:",
            len(gemini_director_result.get("scenes", []) or []),
            flush=True,
        )
        print(
            "[Sprint93-6A Gemini Director] Errors:",
            gemini_director_result.get("errors", []),
            flush=True,
        )

        try:
            director_manifest_result = DirectorManifestWriter().write(
                director_result=gemini_director_result,
                output_dir=director_output_dir,
                project_id=project_id_for_director,
                save_negative_prompts=True,
            )
        except Exception as exc:
            director_manifest_result.update(
                status="failed",
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

        # Sprint103-1: Veo 429 발생 후 1시간 동안 API 호출 자체를 즉시 건너뜁니다.
        quota_guard_path = Path(director_output_dir) / "veo_quota_guard.json"
        quota_guard_cooldown_seconds = 60 * 60
        quota_guard_active = False
        quota_guard_remaining_seconds = 0

        try:
            if quota_guard_path.exists():
                quota_guard_data = json.loads(
                    quota_guard_path.read_text(encoding="utf-8")
                )
                blocked_at = float(quota_guard_data.get("blocked_at", 0) or 0)
                elapsed = max(0.0, time.time() - blocked_at)
                if elapsed < quota_guard_cooldown_seconds:
                    quota_guard_active = True
                    quota_guard_remaining_seconds = int(
                        quota_guard_cooldown_seconds - elapsed
                    )
                else:
                    quota_guard_path.unlink(missing_ok=True)
        except Exception:
            quota_guard_active = False
            quota_guard_remaining_seconds = 0

        if quota_guard_active:
            scene_video_result.update(
                ok=False,
                ready=False,
                status="skipped_quota_cooldown",
                generated_files=[],
                errors=[],
                quota_exhausted=True,
                retry_blocked=True,
                skip_reason="Gemini/Veo quota cooldown active",
                quota_guard_path=str(quota_guard_path),
                quota_guard_remaining_seconds=quota_guard_remaining_seconds,
            )
            print(
                "[Sprint103-1 Veo Fast Skip] Status: skipped_quota_cooldown",
                flush=True,
            )
            print(
                "[Sprint103-1 Veo Fast Skip] Remaining Seconds:",
                quota_guard_remaining_seconds,
                flush=True,
            )
        else:
            try:
                scene_video_result = SceneVideoGenerator().generate(
                    director_manifest_path=director_manifest_result.get(
                        "manifest_path",
                        "",
                    ),
                    output_dir=director_output_dir,
                    project_id=project_id_for_director,
                    product_name=product_name_for_director,
                    aspect_ratio="9:16",
                    update_manifest=True,
                    max_attempts=1,
                    retry_delay_seconds=0.0,
                    reuse_existing=True,
                )
            except Exception as exc:
                scene_video_result.update(
                    status="failed",
                    errors=[f"{type(exc).__name__}: {exc}"],
                )

        scene_video_errors = list(scene_video_result.get("errors") or [])
        scene_video_error_text = " ".join(
            str(item) for item in scene_video_errors
        ).lower()
        quota_exhausted = any(
            token in scene_video_error_text
            for token in (
                "resource_exhausted",
                "quota",
                "429",
                "rate limit",
                "rate-limit",
            )
        )
        scene_video_result["quota_exhausted"] = quota_exhausted
        scene_video_result["retry_blocked"] = quota_exhausted

        if quota_exhausted and not quota_guard_active:
            try:
                quota_guard_path.parent.mkdir(parents=True, exist_ok=True)
                quota_guard_path.write_text(
                    json.dumps(
                        {
                            "blocked_at": time.time(),
                            "reason": "RESOURCE_EXHAUSTED",
                            "cooldown_seconds": quota_guard_cooldown_seconds,
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                scene_video_result["quota_guard_path"] = str(quota_guard_path)
                print(
                    "[Sprint103-1 Veo Fast Skip] Guard Saved:",
                    str(quota_guard_path),
                    flush=True,
                )
            except Exception as exc:
                print(
                    "[Sprint103-1 Veo Fast Skip] Guard Save ERROR:",
                    f"{type(exc).__name__}: {exc}",
                    flush=True,
                )

        outputs["scene_video_generation"] = scene_video_result
        print(
            "[Sprint101-4 Quota Guard] Exhausted:",
            quota_exhausted,
            flush=True,
        )
        print(
            "[Sprint101-4 Quota Guard] Retry Blocked:",
            bool(quota_exhausted),
            flush=True,
        )
        print(
            "[Sprint97-1 Scene Video Generator] Version:",
            scene_video_result.get("version", ""),
            flush=True,
        )
        print(
            "[Sprint97-1 Scene Video Generator] Status:",
            scene_video_result.get("status", ""),
            flush=True,
        )
        print(
            "[Sprint97-1 Scene Video Generator] Attempts:",
            scene_video_result.get("attempt_count", 0),
            "/",
            scene_video_result.get("max_attempts", 0),
            flush=True,
        )
        print(
            "[Sprint97-1 Scene Video Generator] Reused:",
            scene_video_result.get("reused_scene_count", 0),
            flush=True,
        )
        print(
            "[Sprint97-1 Scene Video Generator] Generated:",
            scene_video_result.get("generated_scene_count", 0),
            flush=True,
        )
        print(
            "[Sprint97-1 Scene Video Generator] Failed:",
            scene_video_result.get("failed_scene_count", 0),
            flush=True,
        )
        print(
            "[Sprint97-1 Scene Video Generator] Files:",
            scene_video_result.get("generated_files", []),
            flush=True,
        )
        print(
            "[Sprint97-1 Scene Video Generator] Errors:",
            scene_video_result.get("errors", []),
            flush=True,
        )

        # Sprint101-4: quota 초과 또는 생성 파일 없음이면 병합을 실행하지 않습니다.
        generated_scene_files = list(
            scene_video_result.get("generated_files") or []
        )
        if quota_exhausted:
            scene_merge_result.update(
                ok=False,
                ready=False,
                status="skipped_quota_exhausted",
                errors=[],
                skip_reason="Gemini/Veo quota exhausted",
            )
            print(
                "[Sprint101-4 Scene Merge Guard] Skipped: quota_exhausted",
                flush=True,
            )
        elif not generated_scene_files:
            scene_merge_result.update(
                ok=False,
                ready=False,
                status="skipped_no_generated_scenes",
                errors=[],
                skip_reason="No generated scene video files",
            )
            print(
                "[Sprint101-4 Scene Merge Guard] Skipped: no_generated_scenes",
                flush=True,
            )
        else:
            try:
                scene_merge_result = SceneMergeEngine().merge(
                    director_manifest=scene_video_result.get(
                        "updated_manifest",
                        {},
                    ),
                    director_manifest_path=(
                        scene_video_result.get(
                            "updated_manifest_path",
                            "",
                        )
                        or director_manifest_result.get(
                            "manifest_path",
                            "",
                        )
                    ),
                    scenes_dir=director_output_dir,
                    output_path=(
                        Path("exports")
                        / "videos"
                        / f"{project_id_for_director}_ai_director_final.mp4"
                    ),
                    project_id=project_id_for_director,
                    execute=True,
                    overwrite=True,
                )
            except Exception as exc:
                scene_merge_result.update(
                    status="failed",
                    errors=[f"{type(exc).__name__}: {exc}"],
                )

        outputs["scene_merge"] = scene_merge_result
        print(
            "[Sprint93-7 Scene Merge] Version:",
            scene_merge_result.get("version", ""),
            flush=True,
        )
        print(
            "[Sprint93-7 Scene Merge] Status:",
            scene_merge_result.get("status", ""),
            flush=True,
        )
        print(
            "[Sprint93-7 Scene Merge] Output:",
            scene_merge_result.get("output_path", ""),
            flush=True,
        )
        print(
            "[Sprint93-7 Scene Merge] Errors:",
            scene_merge_result.get("errors", []),
            flush=True,
        )

        # Sprint103-7: Veo 장면이 없거나 병합하지 못하면 현재 프로젝트의
        # 상품 이미지에 9:16 커버·줌·패닝 모션을 적용한 fallback MP4를 생성합니다.
        image_fallback_result = {
            "ok": False,
            "status": "not_needed",
            "output_path": "",
            "image_count": 0,
            "errors": [],
        }
        if not scene_merge_result.get("ok"):
            fallback_path = (
                Path("exports")
                / "videos"
                / f"{project_id_for_director}_product_image_motion_fallback.mp4"
            )
            image_fallback_result = self._build_product_image_fallback_video(
                project=project,
                image_paths=manual_product_image_paths,
                output_path=fallback_path,
                image_pool_result=image_pool_result,
                image_role_result=image_extractor_result,
            )
            print(
                "[Sprint103-7 Quality Fallback] Status:",
                image_fallback_result.get("status", ""),
                flush=True,
            )
            print(
                "[Sprint103-7 Quality Fallback] Images:",
                image_fallback_result.get("image_count", 0),
                flush=True,
            )
            print(
                "[Sprint103-7 Quality Fallback] Motions:",
                image_fallback_result.get("motion_count", 0),
                flush=True,
            )
            print(
                "[Sprint103-7 Quality Fallback] Rejected:",
                len(image_fallback_result.get("rejected_images", []) or []),
                flush=True,
            )
            print(
                "[Sprint103-7 Quality Fallback] Output:",
                image_fallback_result.get("output_path", ""),
                flush=True,
            )
            print(
                "[Sprint103-7 Quality Fallback] Errors:",
                image_fallback_result.get("errors", []),
                flush=True,
            )
            print(
                "[Sprint111-2 Smart Motion Director] Plan Count:",
                len(image_fallback_result.get("motion_plan", []) or []),
                flush=True,
            )
            print(
                "[Sprint111-2 Smart Motion Director] Ready:",
                image_fallback_result.get("smart_motion_ready", False),
                flush=True,
            )

            if image_fallback_result.get("ok"):
                scene_merge_result = {
                    **scene_merge_result,
                    "ok": True,
                    "ready": True,
                    "status": "product_image_motion_fallback_created",
                    "output_path": image_fallback_result.get("output_path", ""),
                    "errors": [],
                    "fallback_type": "current_project_product_image_motion",
                }

        outputs["product_image_video_fallback"] = image_fallback_result

        ai_video_result.update(
            {
                "ok": bool(scene_merge_result.get("ok")),
                "ready": bool(scene_merge_result.get("ready")),
                "status": (
                    "merged"
                    if scene_merge_result.get("ok")
                    else (
                        "scene_video_generation_failed"
                        if not scene_video_result.get("ok")
                        else "scene_merge_failed"
                    )
                ),
                "director_output_dir": director_output_dir,
                "vision_analysis_path": vision_analysis_result.get(
                    "analysis_path",
                    "",
                ),
                "image_tags_path": image_tags_result.get(
                    "tag_manifest_path",
                    "",
                ),
                "scene_plan_path": scene_plan_result.get(
                    "scene_plan_path",
                    "",
                ),
                "scene_selection_path": scene_selection_result.get(
                    "scene_selection_path",
                    "",
                ),
                "director_manifest_path": director_manifest_result.get(
                    "manifest_path",
                    "",
                ),
                "scene_video_generator_version": scene_video_result.get(
                    "version",
                    "",
                ),
                "generated_scene_count": scene_video_result.get(
                    "generated_scene_count",
                    0,
                ),
                "failed_scene_count": scene_video_result.get(
                    "failed_scene_count",
                    0,
                ),
                "generated_files": scene_video_result.get(
                    "generated_files",
                    [],
                ),
                "selected_video_path": (
                    scene_merge_result.get("output_path", "")
                    if scene_merge_result.get("ok")
                    else ""
                ),
                "warnings": (
                    []
                    if scene_merge_result.get("ok")
                    else (
                        list(scene_video_result.get("errors") or [])
                        + list(scene_merge_result.get("errors") or [])
                    )
                ),
            }
        )
        outputs["ai_video"] = ai_video_result
        outputs["ai_video_path"] = ai_video_result.get(
            "selected_video_path",
            "",
        )

        if scene_merge_result.get("ok"):
            merged_ai_video_path = str(
                scene_merge_result.get("output_path") or ""
            )
            if merged_ai_video_path:
                try:
                    ProjectRepository().update_links_and_media(
                        getattr(project, "id"),
                        video_path=merged_ai_video_path,
                    )
                    project.video_path = merged_ai_video_path
                    outputs["ai_video"]["project_video_updated"] = True
                except Exception as exc:
                    outputs["ai_video"]["project_video_updated"] = False
                    outputs["ai_video"].setdefault(
                        "warnings",
                        [],
                    ).append(
                        "Project video_path update failed: "
                        f"{type(exc).__name__}: {exc}"
                    )

        # 2. Source Plan
        try:
            source_plan = (
                SourceVideoEngine().make_search_plan(
                    project,
                    product_plan=product_plan,
                )
            )

            outputs["source_plan"] = source_plan

            state.update_step(
                job_id,
                "source_plan",
                "done",
                source_plan,
            )

        except Exception as exc:
            source_plan = {}
            outputs["source_plan"] = {}

            state.update_step(
                job_id,
                "source_plan",
                "failed",
                error=exc,
            )

        # 3. Source Ranking
        try:
            videos = (
                SourceVideoEngine().list_project_videos(
                    project
                )
            )

            ranked = SourceVideoRanker().rank(
                videos,
                sample_count=4,
            )

            outputs["source_rank"] = ranked

            state.update_step(
                job_id,
                "source_rank",
                "done",
                {
                    "count": len(ranked),
                    "top": ranked[:3],
                },
            )

        except Exception as exc:
            ranked = []
            outputs["source_rank"] = []

            state.update_step(
                job_id,
                "source_rank",
                "failed",
                error=exc,
            )

        # 3-1. Live Video Source Collection
        try:
            keywords = (
                product_plan.get("keywords", {})
                if isinstance(product_plan, dict)
                else {}
            )

            print(
                "[WORKFLOW] keywords keys =",
                list(keywords.keys()),
                flush=True,
            )
            print(
                "[WORKFLOW] taobao_keyword =",
                keywords.get("taobao_keyword"),
                flush=True,
            )
            print(
                "[WORKFLOW] source_1688_keyword =",
                keywords.get("source_1688_keyword"),
                flush=True,
            )
            print(
                "[WORKFLOW] douyin_keyword =",
                keywords.get("douyin_keyword"),
                flush=True,
            )

            live_sources = VideoSourcingEngine().collect(
                {
                    "name": getattr(
                        project,
                        "product_name",
                        "",
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
                    "coupang_url": getattr(
                        project,
                        "coupang_url",
                        "",
                    ),
                    "partner_url": getattr(
                        project,
                        "partner_url",
                        "",
                    ),
                    "image_url": getattr(
                        project,
                        "image_url",
                        "",
                    ),
                    "image_path": image_path,
                    "taobao_keyword": keywords.get(
                        "taobao_keyword",
                        "",
                    ),
                    "source_1688_keyword": keywords.get(
                        "source_1688_keyword",
                        "",
                    ),
                    "douyin_keyword": keywords.get(
                        "douyin_keyword",
                        "",
                    ),
                    "taobao_top10": keywords.get(
                        "taobao_top10",
                        [],
                    ),
                    "source_1688_top10": keywords.get(
                        "source_1688_top10",
                        [],
                    ),
                    "douyin_top10": keywords.get(
                        "douyin_top10",
                        [],
                    ),
                    "clean_name": keywords.get(
                        "clean_name",
                        "",
                    ),
                    "tokens": keywords.get(
                        "tokens",
                        [],
                    ),
                    "category": keywords.get(
                        "category",
                        "",
                    ),
                }
            )

            outputs["video_sources"] = live_sources

            video_candidates = (
                live_sources.get(
                    "best_candidates",
                    [],
                )
                or live_sources.get(
                    "candidates",
                    [],
                )
                or live_sources.get(
                    "results",
                    [],
                )
            )

            outputs["video_candidates"] = (
                video_candidates
                if isinstance(video_candidates, list)
                else []
            )

            print(
                "[Sprint62] Video candidates:",
                len(outputs["video_candidates"]),
                flush=True,
            )

        except Exception as exc:
            print(
                "[Sprint62] VideoSourcing ERROR:",
                repr(exc),
                flush=True,
            )

            outputs["video_sources"] = {
                "ok": False,
                "reason": str(exc),
            }
            outputs["video_candidates"] = []

        # 4. Real Vision
        try:
            current_video = resolver.resolve_path(
                project
            )

            print(
                "[AUTO] current_video =",
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
            current_video = resolver.resolve_path(
                project
            )

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
                    candidates=outputs.get(
                        "video_candidates",
                        [],
                    ),
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

        for item in outputs.get(
            "video_candidates",
            [],
        ):
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
        # 10-3. Sprint73-4 Review Script Generator
        # =====================================
        try:
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
            )

            outputs["review_scripts"] = review_script_result

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
                "review_scripts": outputs.get(
                    "review_scripts",
                    {},
                ),
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
            export_pack = (
                review_scripts.get("export_pack")
                if isinstance(review_scripts.get("export_pack"), dict)
                else {}
            )

            if not export_pack:
                raise ValueError(
                    "Sprint81-10 export_pack이 없습니다"
                )
           
            publisher_result = PublisherEngine().build(
                export_pack=export_pack,
            )
            outputs["publisher"] = publisher_result

            final_video_path = str(
                (
                    outputs.get("video_pipeline")
                    if isinstance(outputs.get("video_pipeline"), dict)
                    else {}
                ).get("output_path", "")
                or resolver.resolve_path(project)
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