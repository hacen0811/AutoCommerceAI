from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Dict

from modules.video.subtitle_pipeline import SubtitlePipeline


print("######## VIDEO_PIPELINE SPRINT154 FINAL SOURCE LOCK LOADED ########", flush=True)


class VideoPipeline:
    PIPELINE_VERSION = "video-pipeline-154-final-source-lock"

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
        self.subtitle_pipeline = SubtitlePipeline(work_dir=self.subtitle_dir)

    def run(self, content_pack, project=None, render=True, apply_subtitles=True):
        content_pack = content_pack or {}
        project_id = self._project_id(project, content_pack)
        image_motion_path = self.merged_dir / f"{project_id}_image_motion.mp4"
        merged_output = self.merged_dir / f"{project_id}_merged.mp4"
        final_output = self.merged_dir / f"{project_id}_final.mp4"

        result = {
            "ok": False,
            "pipeline_version": self.PIPELINE_VERSION,
            "status": "planned",
            "source_path": str(image_motion_path),
            "output_path": "",
            "subtitle": {},
        }
        if not image_motion_path.is_file():
            result["status"] = "image_motion_missing"
            result["message"] = f"이미지 모션 영상을 찾을 수 없습니다: {image_motion_path}"
            return result
        if not render:
            result.update(ok=True, status="plan_only", output_path=str(image_motion_path))
            return result

        try:
            shutil.copy2(image_motion_path, merged_output)
        except OSError as exc:
            result["status"] = "merged_sync_failed"
            result["message"] = str(exc)
            return result

        if not apply_subtitles:
            result.update(ok=True, status="render_completed", output_path=str(merged_output))
            return result

        subtitle_result = self.subtitle_pipeline.render(
            input_path=merged_output,
            content_pack=content_pack,
            output_path=final_output,
        )
        result["subtitle"] = subtitle_result
        if not subtitle_result.get("ok"):
            result.update(
                ok=True,
                status="image_motion_completed_subtitle_skipped",
                output_path=str(merged_output),
                message="Locked Script 자막이 없어 자막 없는 영상으로 반환했습니다. 장면 연출문은 사용하지 않았습니다.",
            )
            print("[Sprint154 Video Pipeline] SUBTITLE SKIPPED:", subtitle_result.get("message", ""), flush=True)
            return result

        result.update(
            ok=True,
            status="completed",
            output_path=subtitle_result.get("output_path", str(final_output)),
            message="Locked Script 자막이 적용된 최종 영상이 완성되었습니다.",
        )
        print("[Sprint154 Video Pipeline] FINAL VIDEO:", result["output_path"], flush=True)
        return result

    def plan(self, content_pack, project=None):
        return self.run(content_pack, project, render=False, apply_subtitles=False)

    def render(self, content_pack, project=None, apply_subtitles=True):
        return self.run(content_pack, project, render=True, apply_subtitles=apply_subtitles)

    def _project_id(self, project, content_pack):
        candidates = []
        if project is not None:
            if isinstance(project, dict):
                candidates += [project.get("id"), project.get("project_id"), project.get("name")]
            else:
                candidates += [getattr(project, "id", None), getattr(project, "project_id", None), getattr(project, "name", None)]
        candidates += [content_pack.get("project_id"), content_pack.get("id")]
        project_data = content_pack.get("project") or {}
        if isinstance(project_data, dict):
            candidates += [project_data.get("id"), project_data.get("project_id"), project_data.get("name")]
        value = next((str(v).strip() for v in candidates if v not in (None, "") and str(v).strip()), "default")
        return value.replace(" ", "_").replace("/", "_").replace("\\", "_")
