from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List


class VideoRenderer:
    """
    Video Engine 53-4

    역할:
    - FFmpeg/FFprobe 준비 상태 확인
    - 지정 구간을 장면 MP4로 렌더링
    - 파일 크기와 실제 재생시간 검증
    - 비어 있거나 손상된 장면 자동 제외
    - 정상 장면만 최종 쇼츠 MP4로 병합
    """

    RENDERER_VERSION = "video-renderer-53-4"
    MIN_FILE_SIZE = 1024
    MIN_DURATION = 0.1

    def __init__(
        self,
        ffmpeg_path: str | None = None,
        ffprobe_path: str | None = None,
        output_dir: str | Path = "exports/rendered_scenes",
        final_output_dir: str | Path = "exports/videos",
    ):
        self.ffmpeg_path = (
            ffmpeg_path
            or shutil.which("ffmpeg")
            or ""
        )
        self.ffprobe_path = (
            ffprobe_path
            or shutil.which("ffprobe")
            or self._sibling_ffprobe(self.ffmpeg_path)
        )

        self.output_dir = Path(output_dir)
        self.final_output_dir = Path(final_output_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.final_output_dir.mkdir(parents=True, exist_ok=True)

    def check_ready(
        self,
        input_path: str | Path,
    ) -> Dict[str, Any]:
        source = Path(input_path)

        ffmpeg_exists = bool(
            self.ffmpeg_path
            and Path(self.ffmpeg_path).is_file()
        )
        ffprobe_exists = bool(
            self.ffprobe_path
            and Path(self.ffprobe_path).is_file()
        )
        video_exists = source.is_file()

        ok = ffmpeg_exists and ffprobe_exists and video_exists

        if not ffmpeg_exists:
            message = "FFmpeg를 찾을 수 없습니다."
        elif not ffprobe_exists:
            message = "FFprobe를 찾을 수 없습니다."
        elif not video_exists:
            message = f"입력 영상 파일을 찾을 수 없습니다: {source}"
        else:
            message = "렌더링 준비가 완료되었습니다."

        return {
            "ok": ok,
            "renderer_version": self.RENDERER_VERSION,
            "status": "ready" if ok else "not_ready",
            "ffmpeg": ffmpeg_exists,
            "ffmpeg_path": self.ffmpeg_path,
            "ffprobe": ffprobe_exists,
            "ffprobe_path": self.ffprobe_path,
            "video_exists": video_exists,
            "input_path": str(source),
            "message": message,
        }

    def render_scene(
        self,
        input_path: str | Path,
        start: float = 0.0,
        end: float = 3.0,
        output_path: str | Path | None = None,
    ) -> Dict[str, Any]:
        ready = self.check_ready(input_path)

        if not ready["ok"]:
            ready["render_status"] = "failed"
            return ready

        start = max(float(start), 0.0)
        end = max(float(end), 0.0)

        if end <= start:
            return self._failure(
                message="끝 시간은 시작 시간보다 커야 합니다.",
                input_path=input_path,
                start=start,
                end=end,
            )

        source = Path(input_path)
        destination = (
            Path(output_path)
            if output_path
            else self.output_dir
            / f"{source.stem}_{start:.1f}_{end:.1f}.mp4"
        )
        destination.parent.mkdir(parents=True, exist_ok=True)

        self._remove_file(destination)

        command = [
            self.ffmpeg_path,
            "-y",
            "-ss",
            f"{start:.3f}",
            "-i",
            str(source),
            "-t",
            f"{end - start:.3f}",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "20",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(destination),
        ]

        completed = self._run(command)
        media_info = self.probe_media(destination)

        ok = (
            completed.returncode == 0
            and media_info.get("ok", False)
            and media_info.get("file_size", 0) >= self.MIN_FILE_SIZE
            and media_info.get("duration", 0.0) >= self.MIN_DURATION
        )

        if not ok:
            self._remove_file(destination)

        return {
            "ok": ok,
            "renderer_version": self.RENDERER_VERSION,
            "status": "completed" if ok else "failed",
            "render_status": "completed" if ok else "failed",
            "input_path": str(source),
            "output_path": str(destination) if ok else "",
            "start": start,
            "end": end,
            "requested_duration": end - start,
            "actual_duration": media_info.get("duration", 0.0),
            "file_size": media_info.get("file_size", 0),
            "command": command,
            "stderr": self._tail(completed.stderr),
            "message": (
                "영상 구간 자르기와 검증이 완료되었습니다."
                if ok
                else "출력 영상이 비어 있거나 유효하지 않아 제외했습니다."
            ),
        }

    def render_job(
        self,
        job: Dict[str, Any],
    ) -> Dict[str, Any]:
        job = job or {}
        scene = int(job.get("scene") or 1)

        input_path = (
            job.get("video_path")
            or job.get("local_path")
            or job.get("path")
            or ""
        )

        result = self.render_scene(
            input_path=input_path,
            start=job.get("start", 0.0),
            end=job.get("end", 3.0),
            output_path=self.output_dir / f"scene_{scene:02d}.mp4",
        )

        result["scene"] = scene
        result["purpose"] = job.get("purpose", "")

        return result

    def render_jobs(
        self,
        jobs: List[Dict[str, Any]],
        final_output_path: str | Path | None = None,
    ) -> Dict[str, Any]:
        scene_results = [
            self.render_job(job)
            for job in (jobs or [])
        ]

        completed = [
            item
            for item in scene_results
            if item.get("ok")
        ]
        failed = [
            item
            for item in scene_results
            if not item.get("ok")
        ]

        if not completed:
            return {
                "ok": False,
                "renderer_version": self.RENDERER_VERSION,
                "status": "failed",
                "scene_count": len(scene_results),
                "completed_scene_count": 0,
                "failed_scene_count": len(failed),
                "scene_results": scene_results,
                "output_path": "",
                "message": "병합할 정상 장면이 없습니다.",
            }

        merge_result = self.merge_scenes(
            scene_paths=[
                item["output_path"]
                for item in completed
            ],
            output_path=final_output_path,
        )

        return {
            "ok": bool(merge_result.get("ok")),
            "renderer_version": self.RENDERER_VERSION,
            "status": merge_result.get("status", "failed"),
            "scene_count": len(scene_results),
            "completed_scene_count": len(completed),
            "failed_scene_count": len(failed),
            "excluded_scene_count": len(failed),
            "scene_results": scene_results,
            "merge_result": merge_result,
            "output_path": merge_result.get("output_path", ""),
            "message": (
                f"{len(completed)}개 정상 장면을 병합했고 "
                f"{len(failed)}개 장면을 제외했습니다."
                if merge_result.get("ok")
                else merge_result.get("message", "")
            ),
        }

    def merge_scenes(
        self,
        scene_paths: List[str | Path],
        output_path: str | Path | None = None,
    ) -> Dict[str, Any]:
        valid_paths = []

        for path_value in scene_paths:
            path = Path(path_value)
            info = self.probe_media(path)

            if (
                info.get("ok")
                and info.get("file_size", 0) >= self.MIN_FILE_SIZE
                and info.get("duration", 0.0) >= self.MIN_DURATION
            ):
                valid_paths.append(path)

        if not valid_paths:
            return {
                "ok": False,
                "renderer_version": self.RENDERER_VERSION,
                "status": "failed",
                "output_path": "",
                "message": "병합할 유효한 장면 파일이 없습니다.",
            }

        destination = (
            Path(output_path)
            if output_path
            else self.final_output_dir / "shorts.mp4"
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        self._remove_file(destination)

        concat_file = self.output_dir / "concat_list.txt"
        concat_file.write_text(
            "\n".join(
                f"file '{path.resolve().as_posix()}'"
                for path in valid_paths
            ),
            encoding="utf-8",
        )

        command = [
            self.ffmpeg_path,
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
            str(destination),
        ]

        completed = self._run(command)
        media_info = self.probe_media(destination)

        ok = (
            completed.returncode == 0
            and media_info.get("ok", False)
            and media_info.get("file_size", 0) >= self.MIN_FILE_SIZE
            and media_info.get("duration", 0.0) >= self.MIN_DURATION
        )

        if not ok:
            self._remove_file(destination)

        return {
            "ok": ok,
            "renderer_version": self.RENDERER_VERSION,
            "status": "completed" if ok else "failed",
            "scene_count": len(valid_paths),
            "scene_paths": [str(path) for path in valid_paths],
            "output_path": str(destination) if ok else "",
            "duration": media_info.get("duration", 0.0),
            "file_size": media_info.get("file_size", 0),
            "command": command,
            "stderr": self._tail(completed.stderr),
            "message": (
                f"총 {len(valid_paths)}개 장면 병합이 완료되었습니다."
                if ok
                else "최종 영상 검증에 실패했습니다."
            ),
        }

    def probe_media(
        self,
        path: str | Path,
    ) -> Dict[str, Any]:
        media_path = Path(path)

        if not media_path.is_file():
            return {
                "ok": False,
                "duration": 0.0,
                "file_size": 0,
            }

        command = [
            self.ffprobe_path,
            "-v",
            "error",
            "-show_entries",
            "format=duration,size",
            "-of",
            "json",
            str(media_path),
        ]

        completed = self._run(command)

        if completed.returncode != 0:
            return {
                "ok": False,
                "duration": 0.0,
                "file_size": media_path.stat().st_size,
                "stderr": self._tail(completed.stderr),
            }

        try:
            payload = json.loads(completed.stdout or "{}")
            format_info = payload.get("format", {})
            duration = float(format_info.get("duration") or 0.0)
            file_size = int(
                format_info.get("size")
                or media_path.stat().st_size
            )
        except (ValueError, TypeError, json.JSONDecodeError):
            return {
                "ok": False,
                "duration": 0.0,
                "file_size": media_path.stat().st_size,
            }

        return {
            "ok": duration > 0 and file_size > 0,
            "duration": duration,
            "file_size": file_size,
        }

    def _sibling_ffprobe(
        self,
        ffmpeg_path: str,
    ) -> str:
        if not ffmpeg_path:
            return ""

        ffmpeg = Path(ffmpeg_path)
        candidate = ffmpeg.with_name("ffprobe.exe")

        return str(candidate) if candidate.is_file() else ""

    def _remove_file(
        self,
        path: Path,
    ) -> None:
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass

    def _run(
        self,
        command: List[str],
    ) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
        except OSError as exc:
            return subprocess.CompletedProcess(
                args=command,
                returncode=1,
                stdout="",
                stderr=str(exc),
            )

    def _tail(
        self,
        text: str,
        limit: int = 3000,
    ) -> str:
        return (text or "")[-limit:]

    def _failure(
        self,
        message: str,
        input_path: str | Path,
        start: float,
        end: float,
    ) -> Dict[str, Any]:
        return {
            "ok": False,
            "renderer_version": self.RENDERER_VERSION,
            "status": "failed",
            "render_status": "failed",
            "input_path": str(input_path),
            "output_path": "",
            "start": start,
            "end": end,
            "message": message,
        }