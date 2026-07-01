from uuid import uuid4

from modules.product.product_engine import ProductEngine
from modules.source.source_video_engine import SourceVideoEngine
from modules.source.video_ranker import SourceVideoRanker
from modules.pipeline.real_vision_runner import RealVisionRunner
from modules.ai.content_factory import ContentFactory
from modules.editor.auto_editor_engine import AutoEditorEngine
from modules.editor.capcut_project_exporter import CapCutProjectExporter
from modules.workflow.pipeline_state import PipelineState
from modules.video.video_path_resolver import VideoPathResolver
from modules.studio.video_sourcing_engine import VideoSourcingEngine

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

    def run_project(self, project, sample_count=6):
        resolver = VideoPathResolver()
        project = resolver.resolve_project(project)
        job_id = uuid4().hex[:12]
        state = PipelineState()
        state.create(job_id, getattr(project, "product_name", "") or getattr(project, "title", ""), self.steps())

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
                {"count": len(ranked), "top": ranked[:3]},
            )
        except Exception as exc:
            ranked = []
            state.update_step(job_id, "source_rank", "failed", error=exc)
    
        try:
            live_sources = VideoSourcingEngine().collect({
                "name": getattr(project, "product_name", ""),
                "keyword": getattr(project, "keyword", ""), })
            outputs["video_sources"] = live_sources
        except Exception:
            pass

        # 4. Real Vision
        try:
            # 등록된 소스 영상 1위가 있으면 임시로 사용하되, 없으면 DB에 저장된 원본 영상을 유지
            original_video = resolver.resolve_path(project)
            if ranked and ranked[0].get("path") and resolver.exists(ranked[0].get("path")):
                project.video_path = ranked[0].get("path")
            else:
                project.video_path = original_video
            real_vision = RealVisionRunner().run(project, sample_count=sample_count, use_yolo=True, use_paddle=True)
            project.video_path = original_video
            outputs["real_vision"] = real_vision
            state.update_step(job_id, "real_vision", "done" if real_vision.get("ok") else "failed", {
                "summary": real_vision.get("summary"),
                "status": real_vision.get("status"),
            }, None if real_vision.get("ok") else real_vision.get("summary"))
        except Exception as exc:
            real_vision = {}
            state.update_step(job_id, "real_vision", "failed", error=exc)

        # 5. Auto Editor
        try:
            if real_vision.get("auto_editor"):
                editor_plan = real_vision.get("auto_editor")
            else:
                editor_plan = AutoEditorEngine().create_plan(
                    getattr(project, "product_name", ""),
                    getattr(project, "keyword", "정보"),
                )
            outputs["auto_editor"] = editor_plan
            state.update_step(job_id, "auto_editor", "done", {"timeline_count": len(editor_plan.get("timeline", []))})
        except Exception as exc:
            editor_plan = {}
            state.update_step(job_id, "auto_editor", "failed", error=exc)

        # 6. Content Factory
        try:
            content = ContentFactory().build(project)
            outputs["content_factory"] = content
            state.update_step(job_id, "content_factory", "done", {"sections": list(content.keys())})
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
