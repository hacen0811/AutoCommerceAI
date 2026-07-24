from uuid import uuid4
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
from modules.review.review_analyzer import ReviewAnalyzer
from modules.review.review_insight import ReviewInsight
from modules.project.repository import ProjectRepository
from modules.video.download_utils import (
    latest_downloaded_video,
    project_source_video_dir,
    safe_file_name,
)


print("######## WORKFLOW_ENGINE SPRINT72-3 LOADED ########", flush=True)


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

    WORKFLOW_VERSION = "workflow-engine-72-3"

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

    def run_project(
        self,
        project,
        sample_count=6,
        **kwargs,
    ):
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

        # 10-1. Review Analyzer + Review Insight
        product_plan_data = (
            outputs.get("product_plan")
            if isinstance(
                outputs.get("product_plan"),
                dict,
            )
            else {}
        )

        merged_reviews = (
            product_plan_data.get("reviews")
            or product_plan_data.get("review_data")
            or []
        )
        print(
            "[UTF8 TRACE PRODUCT_PLAN reviews]",
            repr(product_plan_data.get("reviews")),
            flush=True,
        )

        if not isinstance(merged_reviews, list):
            merged_reviews = []

        outputs["merged_reviews"] = merged_reviews

        try:
            review_analyzer_result = ReviewAnalyzer().analyze(
                merged_reviews
            )

            outputs["review_analyzer"] = review_analyzer_result

            quote_result = (
                outputs.get("review_quote")
                or outputs.get("review_quotes")
                or outputs.get("review_ai")
                or {}
            )

            review_insight_result = ReviewInsight().build(
                analyzer_result=review_analyzer_result,
                quote_result=quote_result,
                reviews=merged_reviews,
            )

            outputs["review_insight"] = review_insight_result

            print(
                "[Sprint72-3] ReviewAnalyzer:",
                bool(review_analyzer_result.get("ok")),
                flush=True,
            )
            print(
                "[Sprint72-3] Analyzer Version:",
                review_analyzer_result.get(
                    "analyzer_version",
                    "",
                ),
                flush=True,
            )
            print(
                "[Sprint72-3] ReviewInsight:",
                bool(review_insight_result.get("ok")),
                flush=True,
            )
            print(
                "[Sprint72-3] Insight Version:",
                review_insight_result.get(
                    "insight_version",
                    "",
                ),
                flush=True,
            )
            print(
                "[Sprint72-3] Review Count:",
                review_insight_result.get(
                    "review_count",
                    0,
                ),
                flush=True,
            )
            print(
                "[Sprint72-3] Best Pain:",
                review_insight_result.get(
                    "best_pain",
                    "",
                ),
                flush=True,
            )
            print(
                "[Sprint72-3] Best Benefit:",
                review_insight_result.get(
                    "best_benefit",
                    "",
                ),
                flush=True,
            )
            print(
                "[Sprint72-3] Confidence:",
                review_insight_result.get(
                    "confidence_score",
                    0,
                ),
                flush=True,
            )

        except Exception as exc:
            outputs["review_analyzer"] = {
                "ok": False,
                "analyzer_version": "review-analyzer-72-1",
                "review_count": len(merged_reviews),
                "error": str(exc),
            }

            outputs["review_insight"] = {
                "ok": False,
                "insight_version": "review-insight-72-1",
                "review_count": len(merged_reviews),
                "error": str(exc),
            }

            print(
                "[Sprint72-3] Review Pipeline ERROR:",
                repr(exc),
                flush=True,
            )

        # 11. Content Factory
        try:
            content_pack = {
                "project": project,
                "project_id": getattr(
                    project,
                    "id",
                    "",
                ),
                "project_name": (
                    getattr(
                        project,
                        "product_name",
                        "",
                    )
                    or getattr(
                        project,
                        "title",
                        "",
                    )
                    or "선택 상품"
                ),
                "product_name": getattr(
                    project,
                    "product_name",
                    "",
                ),
                "reviews": merged_reviews,
                "review_data": merged_reviews,
                "coupang_reviews": (
                    product_plan_data.get(
                        "coupang_reviews"
                    )
                    or product_plan_data.get(
                        "reviews"
                    )
                    or []
                ),
                "ocr_reviews": product_plan_data.get(
                    "ocr_reviews",
                    [],
                ),
                "review_count": len(merged_reviews),
                "review_source": product_plan_data.get(
                    "review_source",
                    "none",
                ),
                "review_collect_status": product_plan_data.get(
                    "review_collect_status",
                    "empty",
                ),
                "review_analyzer": outputs.get(
                    "review_analyzer",
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
                "real_vision": outputs.get(
                    "real_vision",
                    {},
                ),
                "video_quality": outputs.get(
                    "video_quality",
                    {},
                ),
                "shopping_shorts_fit": outputs.get(
                    "shopping_shorts_fit",
                    {},
                ),
                "shopping_fit": outputs.get(
                    "shopping_shorts_fit",
                    {},
                ),
                "viral_pattern": outputs.get(
                    "viral_pattern",
                    {},
                ),
                "auto_editor": outputs.get(
                    "auto_editor",
                    {},
                ),
            }

            content_factory_result = (
                ContentFactory().apply_edit_assistant(
                    content_pack,
                    project=project,
                )
            )

            if not isinstance(
                content_factory_result,
                dict,
            ):
                content_factory_result = {
                    "ok": bool(content_factory_result),
                    "raw_result": content_factory_result,
                }

            content_factory_result["reviews"] = (
                merged_reviews
            )
            content_factory_result["review_count"] = len(
                merged_reviews
            )
            content_factory_result["review_analyzer"] = (
                outputs.get(
                    "review_analyzer",
                    {},
                )
            )
            content_factory_result["review_insight"] = (
                outputs.get(
                    "review_insight",
                    {},
                )
            )

            outputs["content_factory"] = (
                content_factory_result
            )
            outputs["video_pipeline"] = (
                content_factory_result.get(
                    "video_pipeline",
                    {},
                )
            )

            print(
                "[Sprint72-3] Content Factory:",
                bool(content_factory_result),
                flush=True,
            )
            print(
                "[Sprint72-3] Content Review Count:",
                len(merged_reviews),
                flush=True,
            )
            print(
                "[Sprint72-3] Video Pipeline:",
                bool(
                    content_factory_result.get(
                        "video_pipeline"
                    )
                ),
                flush=True,
            )
            print(
                "[Sprint72-3] Final Video:",
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
                    "review_count": len(
                        merged_reviews
                    ),
                    "video_pipeline": bool(
                        content_factory_result.get(
                            "video_pipeline"
                        )
                    ),
                    "output_path": (
                        content_factory_result.get(
                            "video_pipeline",
                            {},
                        ).get(
                            "output_path",
                            "",
                        )
                    ),
                },
            )

        except Exception as exc:
            outputs["content_factory"] = {}
            outputs["video_pipeline"] = {}

            print(
                "[Sprint72-3] Content Factory ERROR:",
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

        final_state = state.load(job_id)

        print(
            "######## RUN_PROJECT SPRINT62 END ########",
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
