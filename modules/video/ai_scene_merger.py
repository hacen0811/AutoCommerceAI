from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List


class AISceneMerger:
    """Sprint92-2 AI scene MP4 merger.

    Existing, non-empty scene files are ordered by filename and joined into one
    MP4. The original scene files are never modified. A failed merge returns a
    structured result so the workflow can fall back to the first generated clip.
    """

    VERSION = "ai-scene-merger-92-2"
    OUTPUT_NAME = "ai_product_video.mp4"

    def merge(
        self,
        scene_files: Iterable[Any],
        output_path: Any = "",
    ) -> Dict[str, Any]:
        scenes = self._normalize_scene_files(scene_files)
        result: Dict[str, Any] = {
            "ok": False,
            "ready": False,
            "status": "not_run",
            "version": self.VERSION,
            "scene_count": len(scenes),
            "scene_files": [str(path) for path in scenes],
            "output_path": "",
            "method": "",
            "errors": [],
            "warnings": [],
        }

        if not scenes:
            result["status"] = "no_scene_files"
            result["errors"].append("병합할 장면 파일이 없습니다.")
            return result

        if len(scenes) == 1:
            result.update(
                ok=True,
                ready=True,
                status="single_scene_passthrough",
                output_path=str(scenes[0]),
                method="passthrough",
            )
            return result

        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            result["status"] = "ffmpeg_not_found"
            result["errors"].append("ffmpeg 실행 파일을 찾지 못했습니다.")
            return result

        target = self._resolve_output_path(scenes, output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        concat_file = target.parent / "concat_list.txt"
        concat_file.write_text(
            "\n".join(self._concat_line(path) for path in scenes) + "\n",
            encoding="utf-8",
        )

        copy_command = [
            ffmpeg,
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
            str(target),
        ]
        copy_run = self._run(copy_command)
        if copy_run["ok"] and self._is_valid_output(target):
            result.update(
                ok=True,
                ready=True,
                status="merged",
                output_path=str(target),
                method="concat_copy",
            )
            return result

        result["warnings"].append(
            "무손실 병합에 실패하여 H.264 재인코딩 병합을 시도합니다."
        )
        if copy_run["error"]:
            result["warnings"].append(copy_run["error"])
        target.unlink(missing_ok=True)

        encode_command = [
            ffmpeg,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-map",
            "0:v:0",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-an",
            "-movflags",
            "+faststart",
            str(target),
        ]
        encode_run = self._run(encode_command)
        if encode_run["ok"] and self._is_valid_output(target):
            result.update(
                ok=True,
                ready=True,
                status="merged",
                output_path=str(target),
                method="concat_h264",
            )
            return result

        result["status"] = "merge_failed"
        error = encode_run["error"] or copy_run["error"] or "알 수 없는 FFmpeg 오류"
        result["errors"].append(error)
        target.unlink(missing_ok=True)
        return result

    def _normalize_scene_files(self, values: Iterable[Any]) -> List[Path]:
        unique: Dict[str, Path] = {}
        for value in values or []:
            if not value:
                continue
            path = Path(str(value)).expanduser()
            try:
                resolved = path.resolve()
            except OSError:
                resolved = path
            if path.is_file() and path.stat().st_size > 0:
                unique[str(resolved).lower()] = path
        return sorted(unique.values(), key=lambda path: path.name.lower())

    def _resolve_output_path(self, scenes: List[Path], output_path: Any) -> Path:
        if output_path:
            path = Path(str(output_path)).expanduser()
            if path.suffix.lower() != ".mp4":
                path = path / self.OUTPUT_NAME
            return path
        return scenes[0].parent / self.OUTPUT_NAME

    def _concat_line(self, path: Path) -> str:
        absolute = path.resolve().as_posix().replace("'", "'\\''")
        return f"file '{absolute}'"

    def _run(self, command: List[str]) -> Dict[str, Any]:
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
        except Exception as exc:
            return {
                "ok": False,
                "returncode": -1,
                "error": f"{type(exc).__name__}: {exc}",
            }

        stderr = (completed.stderr or "").strip()
        if len(stderr) > 2000:
            stderr = stderr[-2000:]
        return {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "error": stderr,
        }

    def _is_valid_output(self, path: Path) -> bool:
        return path.is_file() and path.stat().st_size > 1024
