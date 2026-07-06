from uuid import uuid4
import shutil

from modules.product.product_engine import ProductEngine
from modules.source.source_video_engine import SourceVideoEngine
from modules.source.video_ranker import SourceVideoRanker
from modules.pipeline.real_vision_runner import RealVisionRunner
from modules.content.content_factory import ContentFactory
from modules.editor.auto_editor_engine import AutoEditorEngine
from modules.editor.capcut_project_exporter import CapCutProjectExporter
from modules.workflow.pipeline_state import PipelineState
from modules.video.video_path_resolver import VideoPathResolver
from modules.studio.video_sourcing_engine import VideoSourcingEngine
from modules.video.video_quality_engine import VideoQualityEngine
from modules.video.video_candidate_selector import VideoCandidateSelector
from modules.video.cut_planner import CutPlanner
from modules.project.repository import ProjectRepository
from modules.video.download_utils import (
    latest_downloaded_video,
    project_source_video_dir,
    safe_file_name,
)


class WorkflowEngine:
    """
    One Click Pipeline 핵심 엔진.
    가능한 단계는 계속 진행하고, 실패한 단계는 errors에 기록합니다.
    """

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
            "product_plan": "상품/검색 계획",
            "source_plan": "소스 영상 계획",
            "source_rank": "영상 후보 랭킹",
            "real_vision": "Real Vision 분석",
            "auto_editor": "CapCut 편집안",
            "content_factory": "콘텐츠 생성",
            "capcut_export": "편집 지시서 내보내기",
        }
        return [{"name": name, "label": labels[name], "status": "pending"} for name in self.STEP_NAMES]

    def auto_connect_latest_download(self, project):
        resolver = VideoPathResolver()
        current_video = resolver.resolve_path(project)
        print("[AUTO] current_video =", current_video)

        if current_video and resolver.exists(current_video):
            return {
                "ok": False,
                "message": "이미 연결된 영상이 있습니다.",
                "video_path": current_video,
            }

        latest = latest_downloaded_video()
        print("[AUTO] latest =", latest)

        if not latest:
            return {
                "ok": False,
                "message": "Downloads 최신 영상 없음",
                "video_path": "",
            }

        out_dir = project_source_video_dir(project)
        out_dir.mkdir(parents=True, exist_ok=True)

        project_name = safe_file_name(
            getattr(project, "product_name", "") or getattr(project, "title", ""),
            "project",
        )

        ext = latest.suffix.lower()
        target = out_dir / f"auto_{project_name}{ext}"

        print("[AUTO] copy ->", target)

        try:
            shutil.copy2(str(latest), str(target))
        except PermissionError:
            return {
                "ok": False,
                "message": "기존 영상 파일이 사용 중입니다. 동영상 플레이어나 CapCut을 닫고 다시 시도해주세요.",
                "video_path": str(target),
            }

        ProjectRepository().update_links_and_media(
            getattr(project, "id"),
            video_path=str(target),
        )

        return {
            "ok": True,
            "message": "Downloads 최신 영상을 자동 연결했습니다.",
            "video_path": str(target),
        }

    def run_project(self, project, sample_count=6):
        resolver = VideoPathResolver()
        project = resolver.resolve_project(project)

        auto_connected = self.auto_connect_latest_download(project)

        if auto_connected.get("ok"):
            project = resolver.resolve_project(project)

        job_id = uuid4().hex[:12]
        state = PipelineState()
        state.create(
            job_id,
            getattr(project, "product_name", "") or getattr(project, "title", ""),
            self.steps(),
        )

        outputs = {}

        # 1. Product Plan
        try:
            product_plan = ProductEngine().build_from_coupang(
                getattr(project, "coupang_url", ""),
                product_name=getattr(project, "product_name", ""),
                price=getattr(project, "price", ""),
                category=getattr(project, "category", ""),
                image_url=getattr(project, "image_url", ""),
                partner_url=getattr(project, "partner_url", ""),
            )
            outputs["product_plan"] = product_plan
            state.update_step(job_id, "product_plan", "done", self._compact(product_plan))
        except Exception as exc:
            product_plan = {}
            state.update_step(job_id, "product_plan", "failed", error=exc)

        # 2. Source Plan
        try:
            source_plan = SourceVideoEngine().make_search_plan(project, product_plan=product_plan)
            outputs["source_plan"] = source_plan
            state.update_step(job_id, "source_plan", "done", source_plan)
        except Exception as exc:
            source_plan = {}
            state.update_step(job_id, "source_plan", "failed", error=exc)

        # 3. Source Ranking
        try:
            videos = SourceVideoEngine().list_project_videos(project)
            ranked = SourceVideoRanker().rank(videos, sample_count=4)
            outputs["source_rank"] = ranked
            state.update_step(
                job_id,
                "source_rank",
                "done",
                {
                    "count": len(ranked),
                    "top": ranked[:3],
                    "note": "Sprint 7-4: 랭킹 영상은 후보 표시용이며 Real Vision에 자동 연결하지 않습니다.",
                },
            )
        except Exception as exc:
            ranked = []
            state.update_step(job_id, "source_rank", "failed", error=exc)

        # 3-1. Live Source Collection
        try:
            live_sources = VideoSourcingEngine().collect({
                "name": getattr(project, "product_name", ""),
                "keyword": getattr(project, "keyword", ""),
            })

            outputs["video_sources"] = live_sources

            video_candidates = (
                live_sources.get("best_candidates", [])
                or live_sources.get("candidates", [])
                or live_sources.get("results", [])
            )

            outputs["video_candidates"] = video_candidates

        except Exception as exc:
            outputs["video_sources"] = {
                "ok": False,
                "reason": str(exc),
            }
            outputs["video_candidates"] = []

        # 4. Real Vision
        try:
            current_video = resolver.resolve_path(project)
            print("[AUTO] current_video =", current_video)

            if current_video and resolver.exists(current_video):
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
                    "summary": "현재 프로젝트에 연결된 video_path가 없습니다. 영상 후보를 열어 해당 프로젝트에 영상을 먼저 연결하세요.",
                    "status": {
                        "video_ai": False,
                        "vision_ai": False,
                        "yolo": False,
                        "paddleocr": False,
                        "object_fallback": False,
                    },
                    "project": {
                        "id": getattr(project, "id", None),
                        "product_name": getattr(project, "product_name", ""),
                        "keyword": getattr(project, "keyword", ""),
                        "video_path": current_video,
                    },
                }

            outputs["real_vision"] = real_vision
            state.update_step(
                job_id,
                "real_vision",
                "done" if real_vision.get("ok") else "failed",
                {
                    "summary": real_vision.get("summary"),
                    "status": real_vision.get("status"),
                    "video_path": real_vision.get("project", {}).get("video_path", current_video),
                },
                None if real_vision.get("ok") else real_vision.get("summary"),
            )

        except Exception as exc:
            real_vision = {}
            outputs["real_vision"] = real_vision
            state.update_step(job_id, "real_vision", "failed", error=exc)

        # 4-1. Video Quality
        try:
            current_video = resolver.resolve_path(project)
            quality = VideoQualityEngine().score(current_video, real_vision)
            outputs["video_quality"] = quality
        except Exception as exc:
            outputs["video_quality"] = {
                "ok": False,
                "reason": str(exc),
            }

        # 4-2. AI Candidate Selection
        try:
            video_candidates = outputs.get("video_candidates", [])

            enriched_candidates = []
            for item in video_candidates:
                new_item = dict(item)
                new_item["video_quality"] = outputs.get("video_quality", {})
                new_item["shopping_shorts_fit"] = outputs.get("shopping_shorts_fit", {})
                new_item["real_vision"] = outputs.get("real_vision", {})
                enriched_candidates.append(new_item)

            candidate_selection = VideoCandidateSelector().select(enriched_candidates)
            outputs["candidate_selection"] = candidate_selection

        except Exception as exc:
            outputs["candidate_selection"] = {
                "ok": False,
                "reason": str(exc),
                "top3": [],
                "all": [],
            }

        # 5. Auto Editor
        try:
            editor_plan = AutoEditorEngine().create_plan(
                getattr(project, "product_name", ""),
                getattr(project, "keyword", "정보"),
                vision=real_vision,
                candidate_selection=outputs.get("candidate_selection", {}),
            )

            outputs["auto_editor"] = editor_plan
            state.update_step(
                job_id,
                "auto_editor",
                "done",
                {"timeline_count": len(editor_plan.get("timeline", []))},
            )

        except Exception as exc:
            editor_plan = {}
            state.update_step(job_id, "auto_editor", "failed", error=exc)

        # 6. Content Factory
        try:
            content = {}
            outputs["content_factory"] = content

            state.update_step(
                job_id,
                "content_factory",
                "done",
                {"message": "AI 콘텐츠 팩은 UI 버튼에서 생성합니다."},
            )
        except Exception as exc:
            content = {}
            state.update_step(job_id, "content_factory", "failed", error=exc)

        # 7. CapCut Export
        try:
            export_paths = CapCutProjectExporter().export_plan(project, editor_plan)
            outputs["capcut_export"] = export_paths
            state.update_step(job_id, "capcut_export", "done", export_paths)
        except Exception as exc:
            export_paths = {}
            state.update_step(job_id, "capcut_export", "failed", error=exc)

        final_state = state.load(job_id)

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
            return f"One Click Pipeline {progress}% 완료, 오류 {len(errors)}건이 있습니다. 가능한 단계는 계속 진행했습니다."

        return f"One Click Pipeline {progress}% 완료되었습니다."

    def _compact(self, product_plan):
        return {
            "product": product_plan.get("project_payload", {}).get("product_name"),
            "keyword": product_plan.get("project_payload", {}).get("keyword"),
            "taobao": product_plan.get("keywords", {}).get("taobao_keyword"),
            "douyin": product_plan.get("keywords", {}).get("douyin_keyword"),
        }