from uuid import uuid4
from pathlib import Path
import json
import shutil

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
from modules.content.review_script_generator import ReviewScriptGenerator
from modules.publisher.publisher_engine import PublisherEngine
from modules.publisher.publisher_orchestrator import PublisherOrchestrator
from modules.publisher.publisher_result_store import PublisherResultStore
from modules.publisher.upload_queue_engine import UploadQueueEngine
from modules.publisher.upload_dispatcher import UploadDispatcher
from modules.publisher.youtube_upload_executor import YouTubeUploadExecutor
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


print("######## WORKFLOW_ENGINE SPRINT86-2 LOADED ########", flush=True)


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

    WORKFLOW_VERSION = "workflow-engine-86-2"

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

    def _run_review_image_ocr(self, image_paths, project):
        """설치된 ReviewImageOCR 공개 메서드를 찾아 안전하게 실행합니다."""
        result = {
            "ok": False,
            "status": "not_run",
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

    def run_project(
        self,
        project,
        sample_count=6,
        review_image_paths=None,
    ):
        review_image_paths = review_image_paths or []
        print(
            "######## RUN_PROJECT SPRINT62 START ########",
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
        }

        # 1. Product Plan
        try:
            product_plan = ProductEngine().build_from_coupang(
                getattr(project, "coupang_url", ""),
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
            )

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
            review_ocr_result = self._run_review_image_ocr(
                resolved_review_image_paths,
                project,
            )
            ocr_reviews = self._normalize_reviews(
                review_ocr_result.get("reviews", []),
                source="review_image_ocr",
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
            merged_reviews = self._merge_reviews(
                coupang_reviews,
                ocr_reviews,
            )

            raw_merged_reviews = list(merged_reviews)

            review_clean_result = ReviewCleaner().clean(
                reviews=raw_merged_reviews,
                source="coupang+review_image_ocr",
            )

            clean_reviews = review_clean_result.get(
                "reviews",
                [],
            )

            if clean_reviews:
                merged_reviews = clean_reviews

            outputs["review_clean"] = review_clean_result

            coupang_count = len(coupang_reviews)
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

            if coupang_count and ocr_count:
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
            product_plan["ocr_reviews"] = ocr_reviews
            product_plan["reviews"] = merged_reviews
            product_plan["review_data"] = merged_reviews
            product_plan["review_count"] = merged_count
            product_plan["review_source"] = merged_source
            product_plan["review_collect_status"] = merged_status
            product_plan["review_ocr"] = review_ocr_result
            product_plan["review_clean"] = review_clean_result
            product_plan["raw_merged_review_count"] = raw_merged_count
            product_plan["clean_review_count"] = merged_count

            outputs["product_plan"] = product_plan
            outputs["review_ocr"] = review_ocr_result
            outputs["review_clean"] = review_clean_result
            outputs["merged_reviews"] = merged_reviews
            outputs["review_image_paths"] = resolved_review_image_paths

            print(
                "[Sprint71-2] Review Merge:",
                {
                    "coupang": coupang_count,
                    "ocr": ocr_count,
                    "merged": merged_count,
                    "source": merged_source,
                    "status": merged_status,
                },
                flush=True,
            )
        except Exception as exc:
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
            )

            outputs["review_scripts"] = review_script_result

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

            publisher_store_result = PublisherResultStore().save(
                orchestrator_result=publisher_orchestrator_result,
                project_id=getattr(project, "id", ""),
                project_name=(
                    getattr(project, "product_name", "")
                    or getattr(project, "title", "")
                    or "project"
                ),
                run_id=job_id,
            )
            outputs["publisher_store"] = publisher_store_result

            print(
                "[Sprint83-3 Store] Stored:",
                bool(publisher_store_result.get("stored")),
                flush=True,
            )
            print(
                "[Sprint83-3 Store] Manifest:",
                publisher_store_result.get("manifest_path", ""),
                flush=True,
            )
            print(
                "[Sprint83-3 Store] Latest:",
                publisher_store_result.get("latest_pointer_path", ""),
                flush=True,
            )

            upload_queue_result = UploadQueueEngine().enqueue(
                store_result=publisher_store_result,
                queue_id=job_id,
            )
            outputs["upload_queue"] = upload_queue_result

            print(
                "[Sprint83-3 Queue] Ready:",
                bool(upload_queue_result.get("queue_ready")),
                flush=True,
            )
            print(
                "[Sprint83-3 Queue] Jobs:",
                upload_queue_result.get("ready_jobs", []),
                flush=True,
            )
            print(
                "[Sprint83-3 Queue] Queue:",
                upload_queue_result.get("queue_path", ""),
                flush=True,
            )
            print(
                "[Sprint83-3 Queue] Latest:",
                upload_queue_result.get("latest_pointer_path", ""),
                flush=True,
            )

            upload_dispatcher_result = UploadDispatcher().dispatch(
                queue_result=upload_queue_result,
                platforms=["youtube_shorts"],
                max_jobs=1,
                persist=False,
            )
            outputs["upload_dispatcher"] = upload_dispatcher_result

            youtube_dispatch_job = (
                upload_dispatcher_result.get("dispatch_jobs", {})
                if isinstance(
                    upload_dispatcher_result.get("dispatch_jobs"),
                    dict,
                )
                else {}
            ).get("youtube_shorts", {})

            if youtube_dispatch_job:
                youtube_upload_result = (
                    YouTubeUploadExecutor().execute(
                        dispatch_job=youtube_dispatch_job,
                        dry_run=False,
                        credentials_file="secrets/youtube_client_secret.json",
                        token_file="secrets/youtube_token.json",
                    )
                )
            else:
                youtube_upload_result = {
                    "ok": False,
                    "version": "youtube-upload-executor-83-2",
                    "status": "dispatch_job_missing",
                    "platform": "youtube_shorts",
                    "dry_run": False,
                    "upload_ready": False,
                    "actual_upload_performed": False,
                    "errors": [
                        "youtube_shorts dispatch job이 없습니다"
                    ],
                    "warnings": [],
                }

            outputs["youtube_upload"] = youtube_upload_result

            youtube_summary = self._build_youtube_upload_summary(
                youtube_upload_result
            )
            outputs["youtube"] = youtube_summary

            youtube_manifest_result = (
                self._persist_youtube_upload_metadata(
                    publisher_store_result,
                    youtube_summary,
                )
            )
            outputs["youtube_manifest"] = youtube_manifest_result

            youtube_project_result = (
                ProjectRepository().update_youtube_upload(
                    project_id=getattr(project, "id", ""),
                    upload_result=youtube_summary,
                    manifest_result=youtube_manifest_result,
                )
            )
            outputs["youtube_project"] = youtube_project_result

            print(
                "[Sprint86-2 Project DB] Saved:",
                bool(youtube_project_result.get("ok")),
                flush=True,
            )
            print(
                "[Sprint86-2 Project DB] Status:",
                youtube_project_result.get("status", ""),
                flush=True,
            )
            print(
                "[Sprint86-2 Project DB] Video ID:",
                youtube_project_result.get("video_id", ""),
                flush=True,
            )
            print(
                "[Sprint86-2 Project DB] Watch URL:",
                youtube_project_result.get("watch_url", ""),
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
                "[Sprint85-1 YouTube] Uploaded At:",
                youtube_summary.get("uploaded_at", ""),
                flush=True,
            )
            print(
                "[Sprint85-1 YouTube Manifest] Saved:",
                bool(youtube_manifest_result.get("ok")),
                flush=True,
            )
            print(
                "[Sprint85-1 YouTube Manifest] Path:",
                youtube_manifest_result.get("manifest_path", ""),
                flush=True,
            )

            print(
                "[Sprint83-3 Dispatcher] Ready:",
                bool(
                    upload_dispatcher_result.get(
                        "dispatch_ready"
                    )
                ),
                flush=True,
            )
            print(
                "[Sprint83-3 Dispatcher] Jobs:",
                upload_dispatcher_result.get(
                    "dispatch_platforms",
                    [],
                ),
                flush=True,
            )
            print(
                "[Sprint83-3 YouTube] Status:",
                youtube_upload_result.get("status", ""),
                flush=True,
            )
            print(
                "[Sprint83-3 YouTube] Dry Run:",
                bool(youtube_upload_result.get("dry_run")),
                flush=True,
            )
            print(
                "[Sprint83-3 YouTube] Ready:",
                bool(
                    youtube_upload_result.get(
                        "upload_ready"
                    )
                ),
                flush=True,
            )
            print(
                "[Sprint83-3 YouTube] Actual Upload:",
                bool(
                    youtube_upload_result.get(
                        "actual_upload_performed"
                    )
                ),
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
            "######## RUN_PROJECT SPRINT86-2 END ########",
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