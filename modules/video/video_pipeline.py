from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Dict

from modules.video.subtitle_pipeline import SubtitlePipeline


print(
    "######## VIDEO_PIPELINE SPRINT131-9 IMAGE MOTION FINAL LOCK LOADED ########",
    flush=True,
)


class VideoPipeline:
    """
    Sprint131-9 Image Motion Final Lock

    핵심:
    - VideoComposer / VideoRenderer 재렌더링을 실행하지 않음
    - exports/videos/<project_id>_image_motion.mp4를 최종 원본으로 사용
    - 해당 원본을 <project_id>_merged.mp4로 동기화
    - 실제 대본 자막만 <project_id>_final.mp4에 적용
    """

    PIPELINE_VERSION = "video-pipeline-131-9"

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
        project_id = self._project_id(
            project=project,
            content_pack=content_pack,
        )

        image_motion_path = (
            self.merged_dir / f"{project_id}_image_motion.mp4"
        )
        merged_output = (
            self.merged_dir / f"{project_id}_merged.mp4"
        )
        final_output = (
            self.merged_dir / f"{project_id}_final.mp4"
        )

        result: Dict[str, Any] = {
            "ok": False,
            "pipeline_version": self.PIPELINE_VERSION,
            "status": "planned",
            "composer": {
                "ok": image_motion_path.is_file(),
                "composer_version": "bypassed-by-video-pipeline-131-9",
                "project_id": project_id,
                "source_video_paths": [str(image_motion_path)],
                "message": "이미지 모션 완성본을 직접 사용합니다.",
            },
            "render": {},
            "subtitle": {},
            "source_path": str(image_motion_path),
            "output_path": "",
        }

        if not image_motion_path.is_file():
            result["status"] = "image_motion_missing"
            result["message"] = (
                f"이미지 모션 영상을 찾을 수 없습니다: {image_motion_path}"
            )
            print(
                "[Sprint131-9 Video Pipeline] IMAGE MOTION MISSING:",
                image_motion_path,
                flush=True,
            )
            return result

        if not render:
            result["ok"] = True
            result["status"] = "plan_only"
            result["output_path"] = str(image_motion_path)
            result["message"] = "이미지 모션 최종 입력 계획만 생성했습니다."
            return result

        try:
            if (
                not merged_output.exists()
                or image_motion_path.resolve() != merged_output.resolve()
            ):
                shutil.copy2(image_motion_path, merged_output)
        except OSError as exc:
            result["status"] = "merged_sync_failed"
            result["message"] = (
                f"이미지 모션 영상을 merged 파일로 복사하지 못했습니다: {exc}"
            )
            return result

        merged_ok = (
            merged_output.is_file()
            and merged_output.stat().st_size > 1024
        )

        result["render"] = {
            "ok": merged_ok,
            "renderer_version": "bypassed-by-video-pipeline-131-9",
            "status": "completed" if merged_ok else "failed",
            "input_path": str(image_motion_path),
            "output_path": str(merged_output) if merged_ok else "",
            "message": (
                "VideoComposer 재렌더링 없이 이미지 모션 영상을 "
                "merged 영상으로 동기화했습니다."
            ),
        }

        print(
            "[Sprint131-9 Video Pipeline] FINAL SOURCE:",
            image_motion_path,
            flush=True,
        )
        print(
            "[Sprint131-9 Video Pipeline] MERGED OUTPUT:",
            merged_output,
            flush=True,
        )

        if not merged_ok:
            result["status"] = "merged_sync_failed"
            result["message"] = "merged 영상 생성에 실패했습니다."
            return result

        if not apply_subtitles:
            result["ok"] = True
            result["status"] = "render_completed"
            result["output_path"] = str(merged_output)
            result["message"] = (
                "이미지 모션 영상을 자막 없이 최종 영상으로 반환합니다."
            )
            return result

        subtitle_result = self.subtitle_pipeline.render(
            input_path=merged_output,
            content_pack=content_pack,
            output_path=final_output,
        )
        result["subtitle"] = subtitle_result

        if not subtitle_result.get("ok"):
            # 연출 문구를 잘못 입히는 것보다 자막 없는 정상 이미지 모션을 반환합니다.
            result["ok"] = True
            result["status"] = "image_motion_completed_subtitle_skipped"
            result["output_path"] = str(merged_output)
            result["message"] = (
                "이미지 모션 영상은 정상입니다. 실제 대본 자막을 찾지 못해 "
                "연출 문구를 사용하지 않고 자막 적용을 건너뛰었습니다."
            )
            print(
                "[Sprint131-9 Video Pipeline] SUBTITLE SKIPPED:",
                subtitle_result.get("message", ""),
                flush=True,
            )
            return result

        result["ok"] = True
        result["status"] = "completed"
        result["output_path"] = subtitle_result.get(
            "output_path",
            str(final_output),
        )
        result["message"] = (
            "전체 이미지 모션 영상에 실제 대본 자막 적용이 완료되었습니다."
        )

        print(
            "[Sprint131-9 Video Pipeline] FINAL VIDEO:",
            result["output_path"],
            flush=True,
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
        content_pack: Dict[str, Any],
    ) -> str:
        candidates = []

        if project is not None:
            if isinstance(project, dict):
                candidates.extend(
                    [
                        project.get("id"),
                        project.get("project_id"),
                        project.get("name"),
                    ]
                )
            else:
                candidates.extend(
                    [
                        getattr(project, "id", None),
                        getattr(project, "project_id", None),
                        getattr(project, "name", None),
                    ]
                )

        candidates.extend(
            [
                content_pack.get("project_id"),
                content_pack.get("id"),
            ]
        )

        project_data = content_pack.get("project") or {}
        if isinstance(project_data, dict):
            candidates.extend(
                [
                    project_data.get("id"),
                    project_data.get("project_id"),
                    project_data.get("name"),
                ]
            )

        project_id = next(
            (
                str(value).strip()
                for value in candidates
                if value not in (None, "")
                and str(value).strip()
            ),
            "default",
        )

        return (
            project_id
            .replace(" ", "_")
            .replace("/", "_")
            .replace("\\", "_")
        )