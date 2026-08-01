from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from modules.video.subtitle_builder import SubtitleBuilder
from modules.video.subtitle_engine import SubtitleEngine


print("######## SUBTITLE_PIPELINE SPRINT154 LOCKED SCRIPT ONLY LOADED ########", flush=True)


class SubtitlePipeline:
    PIPELINE_VERSION = "subtitle-pipeline-154-locked-script-only"

    def __init__(self, work_dir: str | Path = "exports/subtitle_pipeline"):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.builder = SubtitleBuilder()
        self.engine = SubtitleEngine(work_dir=self.work_dir / "ass")

    def render(
        self,
        input_path: str | Path,
        content_pack: Dict[str, Any],
        output_path: str | Path | None = None,
    ) -> Dict[str, Any]:
        source = Path(input_path)
        if not source.is_file():
            return self._failure(f"입력 영상 파일을 찾을 수 없습니다: {source}")

        build_result = self.builder.build_result(content_pack)
        subtitles = list(build_result.get("subtitles") or [])
        if not build_result.get("ok") or not subtitles:
            return self._failure(
                "실제 Locked Script 자막을 찾지 못했습니다. 장면 연출문은 사용하지 않습니다.",
                build_result,
            )

        destination = Path(output_path) if output_path else source.with_name(
            f"{source.stem}_subtitles.mp4"
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp_dir = self.work_dir / source.stem
        temp_dir.mkdir(parents=True, exist_ok=True)

        current_input = source
        step_results: List[Dict[str, Any]] = []
        for position, subtitle in enumerate(subtitles, start=1):
            step_output = destination if position == len(subtitles) else temp_dir / f"step_{position:03d}.mp4"
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
                self._cleanup(temp_dir)
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
                    "message": f"{position}번째 자막 적용 중 실패했습니다.",
                }
            current_input = Path(result["output_path"])

        output_ok = destination.is_file() and destination.stat().st_size > 1024
        self._cleanup(temp_dir, destination)
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
            "message": "Locked Script 자막 적용이 완료되었습니다." if output_ok else "최종 자막 영상 생성에 실패했습니다.",
        }

    def render_from_subtitles(self, input_path, subtitles, output_path=None):
        pack = {
            "review_scripts": {
                "scene_subtitles": [
                    {
                        "order": index,
                        "subtitle": item.get("text") or item.get("subtitle") or "",
                    }
                    for index, item in enumerate(subtitles or [], start=1)
                ]
            }
        }
        return self.render(input_path, pack, output_path)

    def _cleanup(self, temp_dir: Path, keep: Path | None = None):
        if not temp_dir.exists():
            return
        keep_resolved = keep.resolve() if keep and keep.exists() else None
        for path in temp_dir.glob("*.mp4"):
            try:
                if keep_resolved is not None and path.resolve() == keep_resolved:
                    continue
                path.unlink()
            except OSError:
                pass
        try:
            if not any(temp_dir.iterdir()):
                temp_dir.rmdir()
        except OSError:
            pass

    def _failure(self, message, build_result=None):
        return {
            "ok": False,
            "pipeline_version": self.PIPELINE_VERSION,
            "status": "failed",
            "output_path": "",
            "build_result": build_result or {},
            "step_results": [],
            "message": message,
        }
