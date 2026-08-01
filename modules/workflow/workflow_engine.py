from uuid import uuid4
from pathlib import Path
import hashlib
import json
import mimetypes
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
from modules.publisher.instagram_upload_executor import InstagramUploadExecutor
from modules.video.ai_video_engine import AIVideoEngine
from modules.video.gemini_veo_provider import GeminiVeoProvider
from modules.video.ai_scene_merger import AISceneMerger
from modules.video.image_motion_generator import ImageMotionGenerator
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

print("######## WORKFLOW_ENGINE SPRINT152-2 NETWORK RETRY SCENE ISOLATION LOADED ########", flush=True)


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

    WORKFLOW_VERSION = "workflow-engine-152-2-network-retry-scene-isolation"
    

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
            scene["max_generation_attempts"] = 3
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
                prompt_item["max_generation_attempts"] = 3
                prompt_item["regenerate_failed_scene_only"] = True
                prompt_item["multiple_candidate_generation"] = False

        director_result["version"] = "ai-image-director-151-1-product-dna-2"
        director_result["product_dna_version"] = "product-dna-2-151-1"
        director_result["product_dna_2"] = locks
        director_result["product_dna_2_required_fields"] = list(required_order)
        director_result["physics_validator_version"] = "vision-physics-contract-151-1"
        director_result["physics_validation_required"] = True
        director_result["initial_generation_count"] = 1
        director_result["max_generation_attempts"] = 3
        director_result["regenerate_failed_scenes_only"] = True
        director_result["generate_multiple_candidates"] = False
        director_result["cost_policy_locked"] = True
        director_result["product_dna_2_prompt_count"] = prompt_count

        print("[Sprint151-1 Product DNA 2.0] Applied:", True, flush=True)
        print("[Sprint151-1 Product DNA 2.0] Prompt Count:", prompt_count, flush=True)
        print("[Sprint151-1 Product DNA 2.0] Fields:", list(required_order), flush=True)
        print("[Sprint151-1 Vision Physics] Enabled:", True, flush=True)
        print("[Sprint151-1 Cost Policy] Initial Images Per Scene:", 1, flush=True)
        print("[Sprint151-1 Cost Policy] Max Attempts Per Failed Scene:", 3, flush=True)
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

        if selected_image_count <= 0:
            closed_loop_ok = False
            closed_loop_ready = False
            resolved_status = "blocked_no_generated_images"
            result["empty_generation_blocked"] = True
            result["errors"].append(
                "Gemini 생성 이미지가 0장이므로 다음 영상 제작 단계 진입을 차단했습니다."
            )
            print(
                "[Sprint152-2 Empty Generation Guard] Blocked: True",
                flush=True,
            )
        else:
            print(
                "[Sprint152-2 Empty Generation Guard] Blocked: False",
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
    ):
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

        if str(locked_script or "").strip() and not supplied_scene_images:
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

        # Sprint132-2 Viral Collector Bridge
        # 상품명과 핵심 키워드로 공개 바이럴 후보 메타데이터를 수집합니다.
        # 수집 결과는 outputs에 저장하고 Story Intelligence의 product_info 및
        # analysis_bundle에 전달합니다. StoryIntelligenceEngine의 기존 공개
        # 메서드 시그니처는 변경하지 않습니다.
        viral_keywords = []
        for viral_keyword_value in (
            getattr(project, "keyword", ""),
            getattr(project, "category", ""),
            project_data.get("keyword", "") if isinstance(project_data, dict) else "",
            project_data.get("category", "") if isinstance(project_data, dict) else "",
        ):
            if isinstance(viral_keyword_value, (list, tuple, set)):
                viral_keywords.extend(
                    str(item or "").strip()
                    for item in viral_keyword_value
                    if str(item or "").strip()
                )
            else:
                viral_keyword_text = str(viral_keyword_value or "").strip()
                if viral_keyword_text:
                    viral_keywords.extend(
                        item.strip()
                        for item in re.split(r"[,|/\n]+", viral_keyword_text)
                        if item.strip()
                    )

        viral_platforms = ["youtube"]
        viral_search_limit = 10
        viral_top_k = 5
        if isinstance(project_data, dict):
            configured_platforms = project_data.get("viral_platforms")
            if isinstance(configured_platforms, str):
                configured_platforms = [
                    item.strip().lower()
                    for item in re.split(r"[,|/\n]+", configured_platforms)
                    if item.strip()
                ]
            if isinstance(configured_platforms, (list, tuple, set)):
                supported_platforms = {"youtube", "tiktok", "instagram"}
                selected_platforms = [
                    str(item or "").strip().lower()
                    for item in configured_platforms
                    if str(item or "").strip().lower() in supported_platforms
                ]
                if selected_platforms:
                    viral_platforms = selected_platforms
            try:
                viral_search_limit = max(1, min(30, int(
                    project_data.get("viral_search_limit", viral_search_limit)
                )))
            except Exception:
                viral_search_limit = 10
            try:
                viral_top_k = max(1, min(20, int(
                    project_data.get("viral_top_k", viral_top_k)
                )))
            except Exception:
                viral_top_k = 5

        viral_collection_result = {
            "ok": False,
            "ready": False,
            "version": getattr(ViralCollector, "VERSION", "viral-collector-132-1"),
            "status": "not_run",
            "product_name": product_name_for_director,
            "keywords": viral_keywords,
            "platforms": viral_platforms,
            "query_count": 0,
            "candidate_count": 0,
            "selected_count": 0,
            "output_path": "",
            "videos": [],
            "warnings": [],
            "errors": [],
        }

        try:
            viral_collection_result = ViralCollector(
                output_root=Path("assets") / "viral",
                search_limit=viral_search_limit,
                top_k=viral_top_k,
            ).collect(
                product_name=product_name_for_director,
                keywords=viral_keywords,
                platforms=viral_platforms,
                project_id=project_id_for_director,
                save=True,
            )
        except Exception as exc:
            viral_collection_result.update(
                status="failed",
                errors=[f"{type(exc).__name__}: {exc}"],
            )

        outputs["viral_collection"] = viral_collection_result
        print(
            "[Sprint132-2 Viral Collector] Version:",
            viral_collection_result.get("version", ""),
            flush=True,
        )
        print(
            "[Sprint132-2 Viral Collector] Status:",
            viral_collection_result.get("status", ""),
            flush=True,
        )
        print(
            "[Sprint132-2 Viral Collector] Candidates:",
            viral_collection_result.get("candidate_count", 0),
            flush=True,
        )
        print(
            "[Sprint132-2 Viral Collector] Selected:",
            viral_collection_result.get("selected_count", 0),
            flush=True,
        )
        print(
            "[Sprint132-2 Viral Collector] Output:",
            viral_collection_result.get("output_path", ""),
            flush=True,
        )
        print(
            "[Sprint132-2 Viral Collector] Errors:",
            viral_collection_result.get("errors", []),
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

        # Sprint150-6: 장면 환경을 현관/실내/베란다/욕실로 다양화합니다.
        scene_plan_result = self._sprint151_1_apply_scene_director(
            scene_plan_result
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

        # Sprint141-6: 생성 → Vision 검증 → 재생성 Closed Loop 단일 실행 진입점 연결
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
        print("[Sprint150-6 Vision Closed Loop] Max Attempts:", 4, flush=True)
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
        short_motion_scene_count = 10
        short_scene_duration = 2.5
        target_motion_scene_count = (
            short_motion_scene_count
            if fresh_product_images or director_scene_count > 0
            else 0
        )
        print(
            "[Sprint150-5 Short Motion] Render Scene Count:",
            target_motion_scene_count,
            flush=True,
        )
        print(
            "[Sprint150-5 Short Motion] Seconds Per Scene:",
            short_scene_duration,
            flush=True,
        )
        print(
            "[Sprint150-5 Short Motion] Target Duration:",
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
            elif fresh_product_images:
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

        if motion_image_paths:
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
