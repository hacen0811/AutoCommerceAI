from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Dict, List

from modules.video.subtitle_builder import SubtitleBuilder
from modules.video.subtitle_engine import SubtitleEngine


class SubtitlePipeline:
    """
    Sprint 54-3 Subtitle Pipeline

    역할:
    - AI 콘텐츠 팩에서 자막 목록 생성
    - SubtitleEngine으로 자막을 순서대로 영상에 적용
    - 최종 자막 포함 MP4 생성
    """

    PIPELINE_VERSION = "subtitle-pipeline-54-3"

    def __init__(
        self,
        work_dir: str | Path = "exports/subtitle_pipeline",
    ):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)

        self.builder = SubtitleBuilder()
        self.engine = SubtitleEngine(
            work_dir=self.work_dir / "ass",
        )

    def render(
        self,
        input_path: str | Path,
        content_pack: Dict[str, Any],
        output_path: str | Path | None = None,
    ) -> Dict[str, Any]:
        source = Path(input_path)

        if not source.is_file():
            return self._failure(
                message=f"입력 영상 파일을 찾을 수 없습니다: {source}",
            )

        build_result = self.builder.build_result(content_pack)
        subtitles = build_result.get("subtitles") or []

        if not subtitles:
            return self._failure(
                message="적용할 자막을 찾지 못했습니다.",
                build_result=build_result,
            )

        destination = (
            Path(output_path)
            if output_path
            else source.with_name(f"{source.stem}_subtitles.mp4")
        )
        destination.parent.mkdir(parents=True, exist_ok=True)

        temp_dir = self.work_dir / source.stem
        temp_dir.mkdir(parents=True, exist_ok=True)

        current_input = source
        step_results: List[Dict[str, Any]] = []

        for position, subtitle in enumerate(subtitles, start=1):
            is_last = position == len(subtitles)

            step_output = (
                destination
                if is_last
                else temp_dir / f"step_{position:03d}.mp4"
            )

            result = self.engine.burn_subtitle(
                input_path=current_input,
                text=subtitle.get("text", ""),
                start=subtitle.get("start", 0.0),
                end=subtitle.get("end", 3.0),
                output_path=step_output,
            )

            result["subtitle_index"] = position
            result["subtitle_data"] = subtitle
            step_results.append(result)

            if not result.get("ok"):
                self._cleanup_temp_files(temp_dir)
                return {
                    "ok": False,
                    "pipeline_version": self.PIPELINE_VERSION,
                    "status": "failed",
                    "input_path": str(source),
                    "output_path": "",
                    "subtitle_count": len(subtitles),
                    "completed_count": position - 1,
                    "failed_index": position,
                    "build_result": build_result,
                    "step_results": step_results,
                    "message": (
                        f"{position}번째 자막 적용 중 실패했습니다."
                    ),
                }

            current_input = Path(result["output_path"])

        output_ok = (
            destination.is_file()
            and destination.stat().st_size > 1024
        )

        self._cleanup_temp_files(
            temp_dir,
            keep=destination,
        )

        return {
            "ok": output_ok,
            "pipeline_version": self.PIPELINE_VERSION,
            "status": "completed" if output_ok else "failed",
            "input_path": str(source),
            "output_path": str(destination) if output_ok else "",
            "subtitle_count": len(subtitles),
            "completed_count": len(step_results),
            "build_result": build_result,
            "step_results": step_results,
            "message": (
                f"총 {len(subtitles)}개 자막 적용이 완료되었습니다."
                if output_ok
                else "최종 자막 영상 생성에 실패했습니다."
            ),
        }

    def render_from_subtitles(
        self,
        input_path: str | Path,
        subtitles: List[Dict[str, Any]],
        output_path: str | Path | None = None,
    ) -> Dict[str, Any]:
        """
        표준 자막 리스트를 직접 전달하는 보조 메서드입니다.
        """

        pack = {
            "timeline": [
                {
                    "start": item.get("start", 0.0),
                    "end": item.get("end", 3.0),
                    "subtitle": (
                        item.get("text")
                        or item.get("subtitle")
                        or ""
                    ),
                }
                for item in (subtitles or [])
            ]
        }

        return self.render(
            input_path=input_path,
            content_pack=pack,
            output_path=output_path,
        )

    def _cleanup_temp_files(
        self,
        temp_dir: Path,
        keep: Path | None = None,
    ) -> None:
        if not temp_dir.exists():
            return

        keep_resolved = (
            keep.resolve()
            if keep and keep.exists()
            else None
        )

        for path in temp_dir.glob("*.mp4"):
            try:
                if (
                    keep_resolved is not None
                    and path.resolve() == keep_resolved
                ):
                    continue

                path.unlink()
            except OSError:
                pass

        try:
            if not any(temp_dir.iterdir()):
                temp_dir.rmdir()
        except OSError:
            pass

    def _failure(
        self,
        message: str,
        build_result: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        return {
            "ok": False,
            "pipeline_version": self.PIPELINE_VERSION,
            "status": "failed",
            "output_path": "",
            "build_result": build_result or {},
            "step_results": [],
            "message": message,
        }