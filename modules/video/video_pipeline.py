from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from modules.video.video_composer import VideoComposer
from modules.video.video_renderer import VideoRenderer
from modules.video.subtitle_pipeline import SubtitlePipeline


class VideoPipeline:
    """
    Video Engine Pipeline 54-4

    흐름:
    1. VideoComposer로 편집 작업 계획 생성
    2. VideoRenderer로 장면별 MP4 생성
    3. 장면 병합
    4. SubtitlePipeline으로 전체 자막 적용
    5. 최종 자막 포함 MP4 반환
    """

    PIPELINE_VERSION = "video-pipeline-54-4"

    def __init__(
        self,
        render_dir: str | Path = "exports/rendered_scenes",
        merged_dir: str | Path = "exports/videos",
        subtitle_dir: str | Path = "exports/subtitle_pipeline",
    ):
        self.render_dir = Path(render_dir)
        self.merged_dir = Path(merged_dir)
        self.subtitle_dir = Path(subtitle_dir)

        self.render_dir.mkdir(parents=True, exist_ok=True)
        self.merged_dir.mkdir(parents=True, exist_ok=True)
        self.subtitle_dir.mkdir(parents=True, exist_ok=True)

        self.renderer = VideoRenderer(
            output_dir=self.render_dir,
            final_output_dir=self.merged_dir,
        )

        self.subtitle_pipeline = SubtitlePipeline(
            work_dir=self.subtitle_dir,
        )

    def run(
        self,
        content_pack: Dict[str, Any],
        project: Any = None,
        render: bool = True,
        apply_subtitles: bool = True,
    ) -> Dict[str, Any]:
        content_pack = content_pack or {}

        composer_result = VideoComposer().compose(
            content_pack=content_pack,
            project=project,
        )

        jobs = composer_result.get("valid_jobs") or []

        result = {
            "ok": False,
            "pipeline_version": self.PIPELINE_VERSION,
            "status": "planned",
            "composer": composer_result,
            "render": {},
            "subtitle": {},
            "output_path": "",
        }

        if not composer_result.get("jobs"):
            result["status"] = "no_jobs"
            result["message"] = "편집 작업 계획이 없습니다."
            return result

        if not jobs:
            result["status"] = "no_valid_jobs"
            result["message"] = (
                "연결된 실제 영상 파일이 없어 렌더링할 수 없습니다."
            )
            return result

        if not render:
            result["ok"] = True
            result["status"] = "plan_only"
            result["message"] = "영상 편집 작업 계획만 생성했습니다."
            return result

        project_id = self._project_id(
            project=project,
            composer_result=composer_result,
        )

        merged_output = (
            self.merged_dir
            / f"{project_id}_merged.mp4"
        )

        render_result = self.renderer.render_jobs(
            jobs=jobs,
            final_output_path=merged_output,
        )

        result["render"] = render_result

        if not render_result.get("ok"):
            result["status"] = "render_failed"
            result["message"] = render_result.get(
                "message",
                "장면 렌더링 또는 병합에 실패했습니다.",
            )
            return result

        merged_path = render_result.get("output_path", "")

        if not apply_subtitles:
            result["ok"] = True
            result["status"] = "render_completed"
            result["output_path"] = merged_path
            result["message"] = (
                "자막 없이 최종 영상 렌더링이 완료되었습니다."
            )
            return result

        final_output = (
            self.merged_dir
            / f"{project_id}_final.mp4"
        )

        subtitle_result = self.subtitle_pipeline.render(
            input_path=merged_path,
            content_pack=content_pack,
            output_path=final_output,
        )

        result["subtitle"] = subtitle_result

        if not subtitle_result.get("ok"):
            result["ok"] = True
            result["status"] = "render_completed_subtitle_failed"
            result["output_path"] = merged_path
            result["message"] = (
                "영상 렌더링은 완료했지만 자막 적용에 실패했습니다. "
                "자막 없는 병합 영상을 반환합니다."
            )
            return result

        result["ok"] = True
        result["status"] = "completed"
        result["output_path"] = subtitle_result.get(
            "output_path",
            str(final_output),
        )
        result["message"] = (
            "장면 렌더링, 병합, 자막 적용까지 완료되었습니다."
        )

        return result

    def plan(
        self,
        content_pack: Dict[str, Any],
        project: Any = None,
    ) -> Dict[str, Any]:
        return self.run(
            content_pack=content_pack,
            project=project,
            render=False,
            apply_subtitles=False,
        )

    def render(
        self,
        content_pack: Dict[str, Any],
        project: Any = None,
        apply_subtitles: bool = True,
    ) -> Dict[str, Any]:
        return self.run(
            content_pack=content_pack,
            project=project,
            render=True,
            apply_subtitles=apply_subtitles,
        )

    def _project_id(
        self,
        project: Any,
        composer_result: Dict[str, Any],
    ) -> str:
        project_id = composer_result.get("project_id")

        if not project_id and project is not None:
            if isinstance(project, dict):
                project_id = (
                    project.get("id")
                    or project.get("project_id")
                    or project.get("name")
                )
            else:
                project_id = (
                    getattr(project, "id", None)
                    or getattr(project, "project_id", None)
                    or getattr(project, "name", None)
                )

        project_id = str(project_id or "default")

        return (
            project_id
            .replace(" ", "_")
            .replace("/", "_")
            .replace("\\", "_")
        )