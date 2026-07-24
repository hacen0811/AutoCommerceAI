from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from modules.video.subtitle_engine import SubtitleEngine


print(
    "######## SUBTITLE_PIPELINE SPRINT131-10 REAL SCRIPT TEXT ONLY LOADED ########",
    flush=True,
)


class SubtitlePipeline:
    """
    Sprint131-10 Real Script Text Only

    허용:
    - subtitle
    - subtitle_text
    - scene_subtitle
    - scene_subtitles
    - subtitles

    차단:
    - caption
    - text
    - scene_goal
    - visual_direction
    - motion_prompt
    - purpose
    - reason
    - edit_note

    즉, 명시적인 실제 자막 필드만 영상에 적용합니다.
    """

    PIPELINE_VERSION = "subtitle-pipeline-131-10"

    ALLOWED_TEXT_KEYS = (
        "subtitle",
        "subtitle_text",
        "scene_subtitle",
    )

    BLOCKED_KEYS = {
        "caption",
        "text",
        "scene_goal",
        "visual_direction",
        "motion_prompt",
        "image_prompt",
        "negative_prompt",
        "purpose",
        "reason",
        "edit_note",
        "camera",
        "transition",
        "animation",
    }

    BLOCKED_STYLE_TOKENS = {
        "bounce",
        "fade",
        "pop",
        "slide",
        "zoom",
        "static",
        "cut",
        "wipe",
        "dissolve",
        "flash",
        "none",
        "low",
        "medium",
        "high",
    }

    def __init__(
        self,
        work_dir: str | Path = "exports/subtitle_pipeline",
    ):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)

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

        subtitles = self._extract_script_subtitles(
            content_pack or {}
        )

        build_result = {
            "ok": bool(subtitles),
            "builder_version": "script-subtitle-extractor-131-9",
            "subtitle_count": len(subtitles),
            "subtitles": subtitles,
            "blocked_fallback_fields": sorted(self.BLOCKED_KEYS),
        }

        print(
            "[Sprint131-10 Subtitle] SCRIPT SUBTITLE COUNT:",
            len(subtitles),
            flush=True,
        )

        for index, item in enumerate(subtitles, start=1):
            print(
                f"[Sprint131-10 Subtitle] {index:02d}:",
                item.get("text", ""),
                flush=True,
            )

        if not subtitles:
            return self._failure(
                message=(
                    "명시적인 실제 대본 자막(subtitle/scene_subtitle)을 "
                    "찾지 못했습니다. 장면연출 문구는 사용하지 않습니다."
                ),
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
                text=subtitle["text"],
                start=subtitle["start"],
                end=subtitle["end"],
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
                    "message": f"{position}번째 실제 대본 자막 적용 중 실패했습니다.",
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
                f"실제 대본 자막 {len(subtitles)}개 적용이 완료되었습니다."
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
        normalized = self._normalize_subtitle_list(
            subtitles or []
        )

        if not normalized:
            return self._failure(
                message="직접 전달된 실제 자막 목록이 비어 있습니다.",
            )

        pack = {"subtitles": normalized}
        return self.render(
            input_path=input_path,
            content_pack=pack,
            output_path=output_path,
        )

    def _extract_script_subtitles(
        self,
        content_pack: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        # 우선순위 1: 명시적인 최상위 자막 목록
        for key in (
            "scene_subtitles",
            "subtitles",
            "script_subtitles",
            "narration_subtitles",
        ):
            value = content_pack.get(key)
            normalized = self._normalize_subtitle_list(value)
            if normalized:
                return normalized

        # 우선순위 2: timeline / cut_plan / scenes의 명시적 subtitle 필드
        for key in (
            "timeline",
            "cut_plan",
            "scenes",
            "scene_plan",
        ):
            value = content_pack.get(key)
            normalized = self._normalize_subtitle_list(value)
            if normalized:
                return normalized

        # 우선순위 3: 자주 사용되는 결과 묶음 내부만 제한적으로 확인
        for parent_key in (
            "script_result",
            "review_script_result",
            "content_result",
            "platform_script",
            "final_script",
            "script",
        ):
            parent = content_pack.get(parent_key)
            if not isinstance(parent, dict):
                continue

            for key in (
                "scene_subtitles",
                "subtitles",
                "script_subtitles",
                "narration_subtitles",
                "timeline",
                "scenes",
            ):
                normalized = self._normalize_subtitle_list(
                    parent.get(key)
                )
                if normalized:
                    return normalized

        return []

    def _normalize_subtitle_list(
        self,
        value: Any,
    ) -> List[Dict[str, Any]]:
        if not isinstance(value, (list, tuple)):
            return []

        result: List[Dict[str, Any]] = []
        cursor = 0.0

        for item in value:
            if isinstance(item, str):
                # 문자열 목록은 scene_subtitles/subtitles에서만 전달되는 경우를 지원
                text = item.strip()
                if not text:
                    continue
                start = cursor
                end = start + 3.0
            elif isinstance(item, dict):
                if any(
                    blocked in item
                    and not any(
                        allowed in item
                        for allowed in self.ALLOWED_TEXT_KEYS
                    )
                    for blocked in self.BLOCKED_KEYS
                ):
                    # 연출 데이터만 있고 명시적 자막 필드가 없으면 제외
                    if not any(
                        item.get(key)
                        for key in self.ALLOWED_TEXT_KEYS
                    ):
                        continue

                text = ""
                for key in self.ALLOWED_TEXT_KEYS:
                    candidate = item.get(key)
                    if candidate not in (None, ""):
                        text = str(candidate).strip()
                        break

                if not text:
                    continue

                if not self._is_real_script_text(text):
                    continue

                start = self._time_value(
                    item.get("start"),
                    default=cursor,
                )
                end = self._time_value(
                    item.get("end"),
                    default=start + self._duration_value(item),
                )
                if end <= start:
                    end = start + self._duration_value(item)
            else:
                continue

            if not text:
                continue

            if not self._is_real_script_text(text):
                continue

            result.append(
                {
                    "text": text,
                    "start": round(start, 3),
                    "end": round(end, 3),
                }
            )
            cursor = end

        return result

    def _is_real_script_text(
        self,
        text: Any,
    ) -> bool:
        value = str(text or "").strip()

        if not value:
            return False

        normalized = (
            value.lower()
            .replace("_", "")
            .replace("-", "")
            .replace(" ", "")
        )

        blocked = {
            token.replace("_", "").replace("-", "").replace(" ", "")
            for token in self.BLOCKED_STYLE_TOKENS
        }

        if normalized in blocked:
            print(
                "[Sprint131-10 Subtitle] BLOCKED STYLE TOKEN:",
                value,
                flush=True,
            )
            return False

        if len(value) < 4:
            return False

        # 실제 대사는 최소한 한글, 숫자 또는 문장부호를 포함해야 합니다.
        has_korean = any("가" <= ch <= "힣" for ch in value)
        has_digit = any(ch.isdigit() for ch in value)
        has_sentence_mark = any(ch in value for ch in ".?!…")

        if not (has_korean or has_digit or has_sentence_mark):
            return False

        return True

    def _duration_value(
        self,
        item: Dict[str, Any],
    ) -> float:
        value = item.get("duration")

        try:
            duration = float(value)
            return max(duration, 0.3)
        except (TypeError, ValueError):
            return 3.0

    def _time_value(
        self,
        value: Any,
        default: float,
    ) -> float:
        if isinstance(value, (int, float)):
            return max(float(value), 0.0)

        text = str(value or "").strip()

        if not text:
            return default

        try:
            if ":" not in text:
                return max(float(text), 0.0)

            parts = text.split(":")
            if len(parts) == 2:
                return max(
                    float(parts[0]) * 60 + float(parts[1]),
                    0.0,
                )
            if len(parts) == 3:
                return max(
                    float(parts[0]) * 3600
                    + float(parts[1]) * 60
                    + float(parts[2]),
                    0.0,
                )
        except (TypeError, ValueError):
            return default

        return default

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