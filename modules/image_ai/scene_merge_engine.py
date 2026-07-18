from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence


class SceneMergeEngine:
    """
    Sprint93-7 Scene Merge Engine

    역할:
    - director_manifest.json 또는 Director 결과를 입력받음
    - 장면별 생성 영상 경로를 순서대로 수집
    - ffprobe로 영상 정보를 검사
    - FFmpeg로 9:16 / 1080x1920 / 30fps 기준 정규화 후 병합
    - 모든 장면에 오디오가 있으면 오디오까지 병합
    - 일부 장면에 오디오가 없으면 영상만 안전하게 병합
    - final_short.mp4 및 scene_merge_report.json 생성

    기본 장면 영상 탐색 순서:
    1) scene["generated_video_path"]
    2) scene["video_path"]
    3) scene["output_video_path"]
    4) scenes_dir / scene_XX.mp4
    """

    VERSION = "scene-merge-engine-93-7"

    DEFAULT_WIDTH = 1080
    DEFAULT_HEIGHT = 1920
    DEFAULT_FPS = 30
    DEFAULT_CRF = 20
    DEFAULT_PRESET = "medium"

    REPORT_FILENAME = "scene_merge_report.json"
    DEFAULT_OUTPUT_FILENAME = "final_short.mp4"

    def merge(
        self,
        director_manifest: Any = None,
        director_manifest_path: Any = "",
        scenes_dir: Any = "",
        output_path: Any = "",
        output_dir: Any = "",
        project_id: Any = "",
        ffmpeg_path: Any = "ffmpeg",
        ffprobe_path: Any = "ffprobe",
        width: Any = DEFAULT_WIDTH,
        height: Any = DEFAULT_HEIGHT,
        fps: Any = DEFAULT_FPS,
        crf: Any = DEFAULT_CRF,
        preset: str = DEFAULT_PRESET,
        execute: bool = True,
        overwrite: bool = True,
    ) -> Dict[str, Any]:
        started_at = time.time()

        result: Dict[str, Any] = {
            "ok": False,
            "ready": False,
            "version": self.VERSION,
            "status": "not_run",
            "project_id": str(project_id or ""),
            "director_manifest_path": str(
                director_manifest_path or ""
            ).strip(),
            "scenes_dir": str(scenes_dir or "").strip(),
            "output_path": "",
            "report_path": "",
            "scene_count": 0,
            "valid_scene_count": 0,
            "missing_scene_count": 0,
            "audio_mode": "unknown",
            "target_width": 0,
            "target_height": 0,
            "target_fps": 0,
            "ffmpeg_command": [],
            "scenes": [],
            "warnings": [],
            "errors": [],
            "elapsed_seconds": 0.0,
        }

        manifest = self._resolve_manifest(
            value=director_manifest,
            path_value=director_manifest_path,
        )

        scenes = (
            manifest.get("scenes", [])
            if isinstance(manifest, dict)
            else []
        )
        scenes = scenes if isinstance(scenes, list) else []

        result["scene_count"] = len(scenes)

        target_width = self._positive_int(width, self.DEFAULT_WIDTH)
        target_height = self._positive_int(height, self.DEFAULT_HEIGHT)
        target_fps = self._positive_int(fps, self.DEFAULT_FPS)
        target_crf = self._bounded_int(crf, self.DEFAULT_CRF, 0, 51)

        result["target_width"] = target_width
        result["target_height"] = target_height
        result["target_fps"] = target_fps

        resolved_output_path = self._resolve_output_path(
            output_path=output_path,
            output_dir=output_dir,
            manifest=manifest,
            director_manifest_path=director_manifest_path,
            project_id=project_id,
        )
        resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
        result["output_path"] = str(resolved_output_path)

        report_path = resolved_output_path.parent / self.REPORT_FILENAME
        result["report_path"] = str(report_path)

        if not scenes:
            result["status"] = "no_scenes"
            result["errors"].append("병합할 장면 정보가 없습니다")
            result["elapsed_seconds"] = round(time.time() - started_at, 3)
            self._save_report(result, report_path)
            return result

        scene_records = self._resolve_scene_records(
            scenes=scenes,
            scenes_dir=scenes_dir,
            manifest=manifest,
        )
        result["scenes"] = scene_records

        valid_records = [
            record
            for record in scene_records
            if record.get("exists")
        ]
        missing_records = [
            record
            for record in scene_records
            if not record.get("exists")
        ]

        result["valid_scene_count"] = len(valid_records)
        result["missing_scene_count"] = len(missing_records)

        if missing_records:
            for record in missing_records:
                result["errors"].append(
                    f"{record.get('scene_id')}: 장면 영상 없음 - "
                    f"{record.get('resolved_video_path')}"
                )

            result["status"] = "missing_scene_videos"
            result["elapsed_seconds"] = round(time.time() - started_at, 3)
            self._save_report(result, report_path)
            return result

        ffmpeg_bin = self._resolve_binary(ffmpeg_path)
        ffprobe_bin = self._resolve_binary(ffprobe_path)

        if execute and not ffmpeg_bin:
            result["status"] = "ffmpeg_not_found"
            result["errors"].append("FFmpeg 실행 파일을 찾을 수 없습니다")
            result["elapsed_seconds"] = round(time.time() - started_at, 3)
            self._save_report(result, report_path)
            return result

        probed_records: List[Dict[str, Any]] = []

        for record in valid_records:
            metadata = self._probe_video(
                video_path=Path(record["resolved_video_path"]),
                ffprobe_bin=ffprobe_bin,
            )
            record.update(metadata)
            probed_records.append(record)

        all_have_audio = bool(probed_records) and all(
            bool(record.get("has_audio"))
            for record in probed_records
        )

        result["audio_mode"] = (
            "preserve_all"
            if all_have_audio
            else "video_only"
        )

        if not all_have_audio:
            result["warnings"].append(
                "일부 장면에 오디오가 없어 영상만 병합합니다"
            )

        command = self._build_ffmpeg_command(
            ffmpeg_bin=ffmpeg_bin or str(ffmpeg_path or "ffmpeg"),
            records=probed_records,
            output_path=resolved_output_path,
            width=target_width,
            height=target_height,
            fps=target_fps,
            crf=target_crf,
            preset=str(preset or self.DEFAULT_PRESET).strip(),
            include_audio=all_have_audio,
            overwrite=overwrite,
        )
        result["ffmpeg_command"] = command

        if not execute:
            result["ok"] = True
            result["ready"] = True
            result["status"] = "command_ready"
            result["elapsed_seconds"] = round(time.time() - started_at, 3)
            self._save_report(result, report_path)
            return result

        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        result["ffmpeg_returncode"] = process.returncode
        result["ffmpeg_stdout"] = process.stdout[-4000:]
        result["ffmpeg_stderr"] = process.stderr[-8000:]

        output_exists = (
            resolved_output_path.is_file()
            and resolved_output_path.stat().st_size > 0
        )

        result["ok"] = process.returncode == 0 and output_exists
        result["ready"] = result["ok"]
        result["status"] = "merged" if result["ok"] else "merge_failed"

        if not result["ok"]:
            result["errors"].append(
                "FFmpeg 장면 병합에 실패했습니다"
            )

        if output_exists:
            final_probe = self._probe_video(
                video_path=resolved_output_path,
                ffprobe_bin=ffprobe_bin,
            )
            result["final_video"] = final_probe
            result["final_video"]["path"] = str(resolved_output_path)
            result["final_video"]["size_bytes"] = (
                resolved_output_path.stat().st_size
            )

        result["elapsed_seconds"] = round(time.time() - started_at, 3)
        self._save_report(result, report_path)

        return result

    def _resolve_manifest(
        self,
        value: Any,
        path_value: Any,
    ) -> Dict[str, Any]:
        if isinstance(value, dict):
            return dict(value)

        resolved_path = str(path_value or "").strip()

        if not resolved_path and isinstance(value, (str, Path)):
            resolved_path = str(value)

        if not resolved_path:
            return {}

        path = Path(resolved_path).expanduser()

        if not path.is_file():
            return {}

        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            return loaded if isinstance(loaded, dict) else {}
        except Exception:
            return {}

    def _resolve_output_path(
        self,
        output_path: Any,
        output_dir: Any,
        manifest: Dict[str, Any],
        director_manifest_path: Any,
        project_id: Any,
    ) -> Path:
        if str(output_path or "").strip():
            return Path(str(output_path)).expanduser()

        if str(output_dir or "").strip():
            return (
                Path(str(output_dir)).expanduser()
                / self.DEFAULT_OUTPUT_FILENAME
            )

        manifest_output = str(
            manifest.get("merge_output_path") or ""
        ).strip()
        if manifest_output:
            return Path(manifest_output).expanduser()

        manifest_dir = str(
            manifest.get("output_dir") or ""
        ).strip()
        if manifest_dir:
            return (
                Path(manifest_dir).expanduser()
                / self.DEFAULT_OUTPUT_FILENAME
            )

        manifest_path = str(director_manifest_path or "").strip()
        if manifest_path:
            return (
                Path(manifest_path).expanduser().parent
                / self.DEFAULT_OUTPUT_FILENAME
            )

        project_key = (
            str(
                project_id
                or manifest.get("project_id")
                or "unknown"
            ).strip()
            or "unknown"
        )

        return (
            Path("exports")
            / "videos"
            / f"project_{project_key}_final.mp4"
        )

    def _resolve_scene_records(
        self,
        scenes: Sequence[Dict[str, Any]],
        scenes_dir: Any,
        manifest: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        resolved_base = self._resolve_scenes_dir(
            scenes_dir=scenes_dir,
            manifest=manifest,
        )

        records: List[Dict[str, Any]] = []

        sorted_scenes = sorted(
            [
                scene
                for scene in scenes
                if isinstance(scene, dict)
            ],
            key=lambda scene: int(
                scene.get("scene_index") or 999999
            ),
        )

        for index, scene in enumerate(sorted_scenes, start=1):
            scene_id = str(
                scene.get("scene_id") or f"scene_{index:02d}"
            ).strip()

            candidates = [
                scene.get("generated_video_path"),
                scene.get("video_path"),
                scene.get("output_video_path"),
            ]

            resolved_path = ""

            for candidate in candidates:
                candidate_text = str(candidate or "").strip()
                if candidate_text:
                    resolved_path = candidate_text
                    break

            if not resolved_path:
                resolved_path = str(
                    resolved_base / f"{scene_id}.mp4"
                )

            path = Path(resolved_path).expanduser()

            records.append(
                {
                    "scene_id": scene_id,
                    "scene_index": int(
                        scene.get("scene_index") or index
                    ),
                    "scene_type": str(
                        scene.get("scene_type") or ""
                    ),
                    "transition": str(
                        scene.get("transition") or "cut"
                    ),
                    "expected_duration_seconds": float(
                        scene.get("duration_seconds") or 0.0
                    ),
                    "resolved_video_path": str(path),
                    "exists": path.is_file(),
                }
            )

        return records

    def _resolve_scenes_dir(
        self,
        scenes_dir: Any,
        manifest: Dict[str, Any],
    ) -> Path:
        if str(scenes_dir or "").strip():
            return Path(str(scenes_dir)).expanduser()

        manifest_scenes_dir = str(
            manifest.get("scenes_dir") or ""
        ).strip()
        if manifest_scenes_dir:
            return Path(manifest_scenes_dir).expanduser()

        output_dir = str(
            manifest.get("output_dir") or ""
        ).strip()
        if output_dir:
            return Path(output_dir).expanduser()

        return Path("exports") / "ai_scenes"

    def _probe_video(
        self,
        video_path: Path,
        ffprobe_bin: str,
    ) -> Dict[str, Any]:
        base = {
            "probe_ok": False,
            "duration_seconds": 0.0,
            "width": 0,
            "height": 0,
            "fps": 0.0,
            "has_audio": False,
        }

        if not ffprobe_bin or not video_path.is_file():
            return base

        command = [
            ffprobe_bin,
            "-v",
            "error",
            "-show_entries",
            (
                "format=duration:"
                "stream=index,codec_type,width,height,"
                "r_frame_rate,avg_frame_rate"
            ),
            "-of",
            "json",
            str(video_path),
        ]

        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        if process.returncode != 0:
            return base

        try:
            payload = json.loads(process.stdout or "{}")
        except Exception:
            return base

        streams = payload.get("streams") or []
        format_data = payload.get("format") or {}

        video_stream = next(
            (
                stream
                for stream in streams
                if stream.get("codec_type") == "video"
            ),
            {},
        )

        has_audio = any(
            stream.get("codec_type") == "audio"
            for stream in streams
        )

        fps_value = self._parse_fraction(
            video_stream.get("avg_frame_rate")
            or video_stream.get("r_frame_rate")
        )

        try:
            duration = float(format_data.get("duration") or 0.0)
        except Exception:
            duration = 0.0

        return {
            "probe_ok": bool(video_stream),
            "duration_seconds": round(duration, 3),
            "width": int(video_stream.get("width") or 0),
            "height": int(video_stream.get("height") or 0),
            "fps": round(fps_value, 3),
            "has_audio": has_audio,
        }

    def _build_ffmpeg_command(
        self,
        ffmpeg_bin: str,
        records: Sequence[Dict[str, Any]],
        output_path: Path,
        width: int,
        height: int,
        fps: int,
        crf: int,
        preset: str,
        include_audio: bool,
        overwrite: bool,
    ) -> List[str]:
        command: List[str] = [ffmpeg_bin]

        command.append("-y" if overwrite else "-n")

        for record in records:
            command.extend(
                ["-i", str(record["resolved_video_path"])]
            )

        filter_parts: List[str] = []
        concat_inputs: List[str] = []

        for index, _record in enumerate(records):
            video_label = f"v{index}"

            filter_parts.append(
                (
                    f"[{index}:v]"
                    f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                    f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
                    f"fps={fps},"
                    "format=yuv420p,"
                    "setsar=1,"
                    "setpts=PTS-STARTPTS"
                    f"[{video_label}]"
                )
            )

            concat_inputs.append(f"[{video_label}]")

            if include_audio:
                audio_label = f"a{index}"
                filter_parts.append(
                    (
                        f"[{index}:a]"
                        "aresample=async=1:first_pts=0,"
                        "aformat=sample_fmts=fltp:"
                        "sample_rates=48000:"
                        "channel_layouts=stereo,"
                        "asetpts=PTS-STARTPTS"
                        f"[{audio_label}]"
                    )
                )
                concat_inputs.append(f"[{audio_label}]")

        if include_audio:
            filter_parts.append(
                "".join(concat_inputs)
                + f"concat=n={len(records)}:v=1:a=1"
                + "[vout][aout]"
            )
        else:
            filter_parts.append(
                "".join(concat_inputs)
                + f"concat=n={len(records)}:v=1:a=0"
                + "[vout]"
            )

        command.extend(
            [
                "-filter_complex",
                ";".join(filter_parts),
                "-map",
                "[vout]",
            ]
        )

        if include_audio:
            command.extend(
                [
                    "-map",
                    "[aout]",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "192k",
                ]
            )
        else:
            command.append("-an")

        command.extend(
            [
                "-c:v",
                "libx264",
                "-preset",
                preset,
                "-crf",
                str(crf),
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(output_path),
            ]
        )

        return command

    def _resolve_binary(
        self,
        value: Any,
    ) -> str:
        raw = str(value or "").strip()

        if not raw:
            return ""

        direct = Path(raw).expanduser()

        if direct.is_file():
            return str(direct)

        located = shutil.which(raw)
        return located or ""

    def _save_report(
        self,
        result: Dict[str, Any],
        report_path: Path,
    ) -> None:
        report_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        report_path.write_text(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

    def _positive_int(
        self,
        value: Any,
        default: int,
    ) -> int:
        try:
            parsed = int(value)
        except Exception:
            parsed = default

        return parsed if parsed > 0 else default

    def _bounded_int(
        self,
        value: Any,
        default: int,
        minimum: int,
        maximum: int,
    ) -> int:
        try:
            parsed = int(value)
        except Exception:
            parsed = default

        return max(minimum, min(maximum, parsed))

    def _parse_fraction(
        self,
        value: Any,
    ) -> float:
        text = str(value or "").strip()

        if not text:
            return 0.0

        if "/" not in text:
            try:
                return float(text)
            except Exception:
                return 0.0

        numerator_text, denominator_text = text.split("/", 1)

        try:
            numerator = float(numerator_text)
            denominator = float(denominator_text)
        except Exception:
            return 0.0

        if denominator == 0:
            return 0.0

        return numerator / denominator