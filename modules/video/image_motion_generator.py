from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


class ImageMotionGenerator:
    """
    Sprint131-2 Image Motion Generator

    역할:
    - 정지 상품 이미지를 세로형 MP4 영상으로 변환
    - AIImageDirector의 recommended_motion을 장면별로 우선 적용
    - motion_plan / scene item / 단일 motion 입력을 모두 지원
    - 추천 모션이 없을 때만 기존 순환 모션을 안전하게 사용
    - 동일 모션 연속 사용 방지
    - FFmpeg 기반으로 동작
    - 원본 이미지는 변경하지 않음
    """

    VERSION = "image-motion-generator-131-2"

    WIDTH = 1080
    HEIGHT = 1920
    FPS = 30
    DEFAULT_DURATION = 6.0

    MOTIONS = (
        "zoom_in",
        "pan_left",
        "zoom_out",
        "pan_right",
        "tilt_up",
        "dolly_in",
        "tilt_down",
        "ken_burns",
    )

    MOTION_ALIASES = {
        "slow_zoom_in": "zoom_in",
        "slow_zoom": "zoom_in",
        "push_in": "dolly_in",
        "dolly_zoom_in": "dolly_in",
        "slide_left": "pan_left",
        "slide_right": "pan_right",
        "move_left": "pan_left",
        "move_right": "pan_right",
        "vertical_up": "tilt_up",
        "vertical_down": "tilt_down",
        "kb": "ken_burns",
        "kenburns": "ken_burns",
    }

    def __init__(
        self,
        ffmpeg_path: Any = "",
        width: int = WIDTH,
        height: int = HEIGHT,
        fps: int = FPS,
    ) -> None:
        self.ffmpeg_path = self._resolve_ffmpeg(ffmpeg_path)
        self.width = max(2, int(width or self.WIDTH))
        self.height = max(2, int(height or self.HEIGHT))
        self.fps = max(1, int(fps or self.FPS))

        self._last_motion = ""

    def generate(
        self,
        image_path: Any,
        output_path: Any,
        duration: Any = DEFAULT_DURATION,
        motion: Any = "",
        scene_index: Any = 0,
        overwrite: bool = True,
    ) -> Dict[str, Any]:
        source = Path(str(image_path or "")).expanduser()
        target = Path(str(output_path or "")).expanduser()

        result: Dict[str, Any] = {
            "ok": False,
            "ready": False,
            "status": "not_run",
            "version": self.VERSION,
            "image_path": str(source),
            "output_path": str(target),
            "motion": "",
            "duration": 0.0,
            "fps": self.fps,
            "width": self.width,
            "height": self.height,
            "errors": [],
            "warnings": [],
        }

        if not self.ffmpeg_path:
            result["status"] = "ffmpeg_not_found"
            result["errors"].append("ffmpeg 실행 파일을 찾지 못했습니다.")
            return result

        if not source.is_file():
            result["status"] = "image_not_found"
            result["errors"].append(
                f"이미지 파일을 찾을 수 없습니다: {source}"
            )
            return result

        try:
            if source.stat().st_size <= 0:
                result["status"] = "empty_image"
                result["errors"].append(
                    f"이미지 파일이 비어 있습니다: {source}"
                )
                return result
        except OSError as exc:
            result["status"] = "image_stat_failed"
            result["errors"].append(
                f"{type(exc).__name__}: {exc}"
            )
            return result

        seconds = self._normalize_duration(duration)
        selected_motion = self.select_motion(
            scene_index=scene_index,
            requested_motion=motion,
        )

        result["duration"] = seconds
        result["motion"] = selected_motion

        if not str(target):
            result["status"] = "invalid_output_path"
            result["errors"].append("출력 영상 경로가 없습니다.")
            return result

        if target.suffix.lower() != ".mp4":
            target = target / f"scene_{int(scene_index) + 1:02d}.mp4"
            result["output_path"] = str(target)

        target.parent.mkdir(parents=True, exist_ok=True)

        if target.exists() and not overwrite:
            if self._is_valid_output(target):
                result.update(
                    ok=True,
                    ready=True,
                    status="existing",
                    output_path=str(target),
                )
                return result

            result["status"] = "invalid_existing_output"
            result["errors"].append(
                f"기존 출력 영상이 유효하지 않습니다: {target}"
            )
            return result

        target.unlink(missing_ok=True)

        frame_count = max(1, round(seconds * self.fps))
        video_filter = self._build_video_filter(
            motion=selected_motion,
            frame_count=frame_count,
        )

        command = [
            self.ffmpeg_path,
            "-y",
            "-loop",
            "1",
            "-i",
            str(source),
            "-vf",
            video_filter,
            "-frames:v",
            str(frame_count),
            "-r",
            str(self.fps),
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

        run_result = self._run(command)

        if run_result["ok"] and self._is_valid_output(target):
            self._last_motion = selected_motion

            result.update(
                ok=True,
                ready=True,
                status="generated",
                output_path=str(target),
                returncode=run_result["returncode"],
            )

            print(
                "[Sprint131-2 Image Motion] Version:",
                self.VERSION,
                flush=True,
            )
            print(
                "[Sprint131-2 Image Motion] Status: generated",
                flush=True,
            )
            print(
                "[Sprint131-2 Image Motion] Motion:",
                selected_motion,
                flush=True,
            )
            print(
                "[Sprint131-2 Image Motion] Image:",
                source,
                flush=True,
            )
            print(
                "[Sprint131-2 Image Motion] Output:",
                target,
                flush=True,
            )

            return result

        target.unlink(missing_ok=True)

        result["status"] = "generation_failed"
        result["returncode"] = run_result["returncode"]
        result["errors"].append(
            run_result["error"] or "알 수 없는 FFmpeg 오류"
        )

        print(
            "[Sprint131-2 Image Motion] Status: generation_failed",
            flush=True,
        )
        print(
            "[Sprint131-2 Image Motion] ERROR:",
            result["errors"][-1],
            flush=True,
        )

        return result

    def generate_many(
        self,
        image_paths: Iterable[Any],
        output_dir: Any,
        duration: Any = DEFAULT_DURATION,
        start_index: int = 0,
        overwrite: bool = True,
        motion_plan: Any = None,
        motions: Any = None,
        scene_items: Any = None,
    ) -> Dict[str, Any]:
        images = self._normalize_images(image_paths)
        target_dir = Path(str(output_dir or "")).expanduser()
        resolved_motion_plan = self._normalize_motion_plan(
            motion_plan=motion_plan,
            motions=motions,
            scene_items=scene_items,
        )

        result: Dict[str, Any] = {
            "ok": False,
            "ready": False,
            "status": "not_run",
            "version": self.VERSION,
            "image_count": len(images),
            "generated_count": 0,
            "failed_count": 0,
            "scene_files": [],
            "motion_plan_count": len(resolved_motion_plan),
            "motion_plan_used_count": 0,
            "items": [],
            "errors": [],
            "warnings": [],
        }

        if not images:
            result["status"] = "no_images"
            result["errors"].append("영상으로 변환할 이미지가 없습니다.")
            return result

        if not str(target_dir):
            result["status"] = "invalid_output_dir"
            result["errors"].append("출력 폴더가 없습니다.")
            return result

        target_dir.mkdir(parents=True, exist_ok=True)

        self._last_motion = ""

        for offset, image_path in enumerate(images):
            scene_index = int(start_index) + offset
            output_path = (
                target_dir / f"scene_{scene_index + 1:02d}.mp4"
            )

            motion_item = self._resolve_motion_plan_item(
                plan=resolved_motion_plan,
                offset=offset,
                scene_index=scene_index,
            )
            requested_motion = motion_item.get("recommended_motion") or ""
            item_duration = motion_item.get("duration") or duration

            item = self.generate(
                image_path=image_path,
                output_path=output_path,
                duration=item_duration,
                motion=requested_motion,
                scene_index=scene_index,
                overwrite=overwrite,
            )
            item["scene_id"] = motion_item.get("scene_id") or (
                f"scene_{scene_index + 1:02d}"
            )
            item["motion_source"] = (
                motion_item.get("motion_source")
                or ("motion_plan" if requested_motion else "fallback_cycle")
            )
            item["motion_speed"] = motion_item.get("motion_speed") or ""
            item["motion_reason"] = motion_item.get("motion_reason") or ""
            item["camera_style"] = motion_item.get("camera_style") or ""

            if requested_motion:
                result["motion_plan_used_count"] += 1
            result["items"].append(item)

            if item.get("ok") and item.get("output_path"):
                result["generated_count"] += 1
                result["scene_files"].append(item["output_path"])
            else:
                result["failed_count"] += 1
                for error in item.get("errors") or []:
                    result["errors"].append(
                        f"{image_path}: {error}"
                    )

        result["ok"] = result["generated_count"] > 0
        result["ready"] = result["generated_count"] > 0

        if result["generated_count"] == len(images):
            result["status"] = "generated"
        elif result["generated_count"] > 0:
            result["status"] = "partial"
        else:
            result["status"] = "failed"

        print(
            "[Sprint131-2 Image Motion] Version:",
            self.VERSION,
            flush=True,
        )
        print(
            "[Sprint131-2 Image Motion] Status:",
            result["status"],
            flush=True,
        )
        print(
            "[Sprint131-2 Image Motion] Image Count:",
            result["image_count"],
            flush=True,
        )
        print(
            "[Sprint131-2 Image Motion] Generated Count:",
            result["generated_count"],
            flush=True,
        )
        print(
            "[Sprint131-2 Image Motion] Failed Count:",
            result["failed_count"],
            flush=True,
        )
        print(
            "[Sprint131-2 Image Motion] Motions:",
            [
                item.get("motion")
                for item in result["items"]
                if item.get("motion")
            ],
            flush=True,
        )
        print(
            "[Sprint131-2 Image Motion] Motion Plan Used:",
            result["motion_plan_used_count"],
            "/",
            result["motion_plan_count"],
            flush=True,
        )
        print(
            "[Sprint131-2 Image Motion] Errors:",
            result["errors"],
            flush=True,
        )

        return result

    def select_motion(
        self,
        scene_index: Any = 0,
        requested_motion: Any = "",
    ) -> str:
        requested = self._normalize_motion_name(requested_motion)

        if requested in self.MOTIONS:
            selected = requested
        else:
            try:
                index = int(scene_index or 0)
            except (TypeError, ValueError):
                index = 0

            selected = self.MOTIONS[index % len(self.MOTIONS)]

        if (
            selected == self._last_motion
            and len(self.MOTIONS) > 1
        ):
            current_index = self.MOTIONS.index(selected)
            selected = self.MOTIONS[
                (current_index + 1) % len(self.MOTIONS)
            ]

        return selected

    def _normalize_motion_name(self, value: Any) -> str:
        motion = self._clean_text(value).lower().replace("-", "_").replace(" ", "_")
        if motion in self.MOTION_ALIASES:
            motion = self.MOTION_ALIASES[motion]
        return motion

    def _normalize_motion_plan(
        self,
        motion_plan: Any = None,
        motions: Any = None,
        scene_items: Any = None,
    ) -> List[Dict[str, Any]]:
        source = motion_plan

        if isinstance(source, dict):
            for key in ("motion_plan", "scenes", "items"):
                value = source.get(key)
                if isinstance(value, list):
                    source = value
                    break

        if not isinstance(source, list) or not source:
            source = scene_items if isinstance(scene_items, list) else None

        if not isinstance(source, list) or not source:
            if isinstance(motions, (list, tuple)):
                source = [
                    {
                        "scene_index": index,
                        "recommended_motion": motion,
                        "motion_source": "motions_argument",
                    }
                    for index, motion in enumerate(motions)
                ]
            elif motions:
                source = [
                    {
                        "scene_index": 0,
                        "recommended_motion": motions,
                        "motion_source": "motions_argument",
                    }
                ]
            else:
                source = []

        normalized: List[Dict[str, Any]] = []

        for index, raw_item in enumerate(source):
            if isinstance(raw_item, str):
                raw_item = {
                    "scene_index": index,
                    "recommended_motion": raw_item,
                }

            if not isinstance(raw_item, dict):
                continue

            motion = self._normalize_motion_name(
                raw_item.get("recommended_motion")
                or raw_item.get("motion")
                or raw_item.get("camera_motion")
                or raw_item.get("motion_type")
            )

            item = {
                "scene_id": self._clean_text(raw_item.get("scene_id")),
                "scene_index": self._to_int(
                    raw_item.get("scene_index"),
                    default=index,
                ),
                "recommended_motion": motion,
                "motion_speed": self._clean_text(
                    raw_item.get("motion_speed")
                    or raw_item.get("speed")
                ),
                "motion_reason": self._clean_text(
                    raw_item.get("motion_reason")
                    or raw_item.get("reason")
                ),
                "camera_style": self._clean_text(
                    raw_item.get("camera_style")
                ),
                "motion_source": self._clean_text(
                    raw_item.get("motion_source")
                ) or "motion_plan",
                "duration": raw_item.get("duration")
                or raw_item.get("scene_duration")
                or raw_item.get("duration_seconds"),
            }
            normalized.append(item)

        return normalized

    def _resolve_motion_plan_item(
        self,
        plan: List[Dict[str, Any]],
        offset: int,
        scene_index: int,
    ) -> Dict[str, Any]:
        for item in plan:
            if self._to_int(item.get("scene_index"), default=-1) == scene_index:
                return dict(item)

        if 0 <= offset < len(plan):
            return dict(plan[offset])

        return {}

    def _to_int(self, value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return int(default)

    def _build_video_filter(
        self,
        motion: str,
        frame_count: int,
    ) -> str:
        denominator = max(1, frame_count - 1)
        size = f"{self.width}x{self.height}"

        base_filter = (
            f"scale={self.width}:{self.height}:"
            "force_original_aspect_ratio=increase,"
            f"crop={self.width}:{self.height}"
        )

        expressions = {
            "zoom_in": {
                "z": f"1+0.12*on/{denominator}",
                "x": "(iw-iw/zoom)/2",
                "y": "(ih-ih/zoom)/2",
            },
            "zoom_out": {
                "z": f"1.12-0.12*on/{denominator}",
                "x": "(iw-iw/zoom)/2",
                "y": "(ih-ih/zoom)/2",
            },
            "pan_left": {
                "z": "1.12",
                "x": f"(iw-iw/zoom)*(1-on/{denominator})",
                "y": "(ih-ih/zoom)/2",
            },
            "pan_right": {
                "z": "1.12",
                "x": f"(iw-iw/zoom)*on/{denominator}",
                "y": "(ih-ih/zoom)/2",
            },
            "tilt_up": {
                "z": "1.12",
                "x": "(iw-iw/zoom)/2",
                "y": f"(ih-ih/zoom)*(1-on/{denominator})",
            },
            "tilt_down": {
                "z": "1.12",
                "x": "(iw-iw/zoom)/2",
                "y": f"(ih-ih/zoom)*on/{denominator}",
            },
            "dolly_in": {
                "z": f"1+0.18*on/{denominator}",
                "x": "(iw-iw/zoom)/2",
                "y": "(ih-ih/zoom)/2",
            },
            "ken_burns": {
                "z": f"1.04+0.10*on/{denominator}",
                "x": f"(iw-iw/zoom)*on/{denominator}",
                "y": f"(ih-ih/zoom)*(1-on/{denominator})",
            },
        }

        config = expressions.get(
            motion,
            expressions["zoom_in"],
        )

        zoompan_filter = (
            "zoompan="
            f"z='{config['z']}':"
            f"x='{config['x']}':"
            f"y='{config['y']}':"
            f"d={frame_count}:"
            f"s={size}:"
            f"fps={self.fps}"
        )

        return (
            f"{base_filter},"
            f"{zoompan_filter},"
            "setsar=1,"
            "format=yuv420p"
        )

    def _normalize_images(
        self,
        values: Iterable[Any],
    ) -> List[Path]:
        unique: Dict[str, Path] = {}

        for value in values or []:
            if not value:
                continue

            path = Path(str(value)).expanduser()

            try:
                resolved_key = str(path.resolve()).lower()
            except OSError:
                resolved_key = str(path).lower()

            try:
                if path.is_file() and path.stat().st_size > 0:
                    unique[resolved_key] = path
            except OSError:
                continue

        return list(unique.values())

    def _normalize_duration(self, value: Any) -> float:
        try:
            duration = float(value)
        except (TypeError, ValueError):
            duration = self.DEFAULT_DURATION

        return min(30.0, max(1.0, duration))

    def _resolve_ffmpeg(self, value: Any) -> Optional[str]:
        explicit = self._clean_text(value)

        if explicit:
            path = Path(explicit).expanduser()
            if path.is_file():
                return str(path)

        return shutil.which("ffmpeg")

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

        if len(stderr) > 3000:
            stderr = stderr[-3000:]

        return {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "error": stderr,
        }

    def _is_valid_output(self, path: Path) -> bool:
        try:
            return path.is_file() and path.stat().st_size > 1024
        except OSError:
            return False

    def _clean_text(self, value: Any) -> str:
        return str(value or "").strip()