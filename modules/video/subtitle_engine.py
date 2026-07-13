from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List


class SubtitleEngine:
    """
    Sprint 54-6 Subtitle Engine

    역할:
    - 여러 자막을 ASS 파일 하나로 생성
    - FFmpeg를 한 번만 실행해 모든 자막 삽입
    - 긴 자막 자동 줄바꿈
    - 글자 수에 따른 폰트 크기 자동 조절
    - 세로 영상 자막 안전영역 유지
    """

    ENGINE_VERSION = "subtitle-engine-54-6"

    def __init__(
        self,
        ffmpeg_path: str | None = None,
        work_dir: str | Path = "exports/subtitles",
    ):
        self.ffmpeg_path = (
            ffmpeg_path
            or shutil.which("ffmpeg")
            or ""
        )

        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def check_ready(
        self,
        input_path: str | Path,
    ) -> Dict[str, Any]:
        source = Path(input_path)

        ffmpeg_exists = bool(self.ffmpeg_path)
        video_exists = source.is_file()
        ok = ffmpeg_exists and video_exists

        if not ffmpeg_exists:
            message = "FFmpeg를 찾을 수 없습니다."
        elif not video_exists:
            message = (
                f"입력 영상 파일을 찾을 수 없습니다: {source}"
            )
        else:
            message = "자막 렌더링 준비가 완료되었습니다."

        return {
            "ok": ok,
            "engine_version": self.ENGINE_VERSION,
            "status": "ready" if ok else "not_ready",
            "ffmpeg": ffmpeg_exists,
            "ffmpeg_path": self.ffmpeg_path,
            "video_exists": video_exists,
            "input_path": str(source),
            "message": message,
        }

    def burn_subtitle(
        self,
        input_path: str | Path,
        text: str,
        start: float = 0.0,
        end: float = 3.0,
        output_path: str | Path | None = None,
        font_name: str = "Malgun Gothic",
        font_size: int = 72,
        margin_v: int = 300,
        max_chars_per_line: int = 15,
    ) -> Dict[str, Any]:
        """
        기존 단일 자막 호출과의 호환성을 유지합니다.
        """
        return self.burn_subtitles(
            input_path=input_path,
            subtitles=[
                {
                    "index": 1,
                    "text": text,
                    "start": start,
                    "end": end,
                }
            ],
            output_path=output_path,
            font_name=font_name,
            font_size=font_size,
            margin_v=margin_v,
            max_chars_per_line=max_chars_per_line,
        )

    def burn_subtitles(
        self,
        input_path: str | Path,
        subtitles: List[Dict[str, Any]],
        output_path: str | Path | None = None,
        font_name: str = "Malgun Gothic",
        font_size: int = 72,
        margin_v: int = 300,
        max_chars_per_line: int = 15,
    ) -> Dict[str, Any]:
        ready = self.check_ready(input_path)

        if not ready["ok"]:
            return ready

        source = Path(input_path)

        normalized = self._normalize_subtitles(
            subtitles=subtitles,
            requested_font_size=font_size,
            max_chars_per_line=max_chars_per_line,
        )

        if not normalized:
            return {
                "ok": False,
                "engine_version": self.ENGINE_VERSION,
                "status": "failed",
                "input_path": str(source),
                "output_path": "",
                "message": "적용할 수 있는 자막이 없습니다.",
            }

        destination = (
            Path(output_path)
            if output_path
            else self.work_dir / f"{source.stem}_subtitle.mp4"
        )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        ass_path = (
            self.work_dir
            / f"{source.stem}_subtitles.ass"
        )

        ass_path.write_text(
            self._build_ass(
                subtitles=normalized,
                font_name=font_name,
                default_font_size=font_size,
                margin_v=margin_v,
            ),
            encoding="utf-8-sig",
        )

        if destination.exists():
            destination.unlink()

        subtitle_filter = (
            "subtitles="
            + self._escape_filter_path(
                ass_path.resolve()
            )
        )

        command = [
            self.ffmpeg_path,
            "-y",
            "-i",
            str(source),
            "-vf",
            subtitle_filter,
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "20",
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            str(destination),
        ]

        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

        ok = (
            completed.returncode == 0
            and destination.is_file()
            and destination.stat().st_size > 1024
        )

        if not ok and destination.exists():
            destination.unlink()

        return {
            "ok": ok,
            "engine_version": self.ENGINE_VERSION,
            "status": "completed" if ok else "failed",
            "input_path": str(source),
            "output_path": (
                str(destination)
                if ok
                else ""
            ),
            "ass_path": str(ass_path),
            "subtitle_count": len(normalized),
            "subtitles": normalized,
            "font_name": font_name,
            "margin_v": margin_v,
            "max_chars_per_line": max_chars_per_line,
            "command": command,
            "stderr": (
                completed.stderr
                or ""
            )[-3000:],
            "message": (
                f"총 {len(normalized)}개의 자막을 한 번에 적용했습니다."
                if ok
                else "자막 포함 영상 생성에 실패했습니다."
            ),
        }

    def _normalize_subtitles(
        self,
        subtitles: List[Dict[str, Any]],
        requested_font_size: int,
        max_chars_per_line: int,
    ) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []

        for index, subtitle in enumerate(
            subtitles or [],
            start=1,
        ):
            if not isinstance(subtitle, dict):
                continue

            text = str(
                subtitle.get("text")
                or ""
            ).strip()

            if not text:
                continue

            try:
                start = max(
                    float(
                        subtitle.get("start")
                        or 0.0
                    ),
                    0.0,
                )
            except (TypeError, ValueError):
                start = 0.0

            try:
                end = max(
                    float(
                        subtitle.get("end")
                        or start + 3.0
                    ),
                    0.0,
                )
            except (TypeError, ValueError):
                end = start + 3.0

            if end <= start:
                end = start + 3.0

            wrapped_text = (
                self._wrap_subtitle_text(
                    text=text,
                    max_chars_per_line=max_chars_per_line,
                    max_lines=3,
                )
            )

            adjusted_font_size = (
                self._adjust_font_size(
                    text=text,
                    requested_font_size=requested_font_size,
                )
            )

            normalized.append(
                {
                    "index": (
                        subtitle.get("index")
                        or index
                    ),
                    "start": start,
                    "end": end,
                    "text": text,
                    "wrapped_text": wrapped_text,
                    "font_size": adjusted_font_size,
                }
            )

        return normalized

    def _build_ass(
        self,
        subtitles: List[Dict[str, Any]],
        font_name: str,
        default_font_size: int,
        margin_v: int,
    ) -> str:
        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{default_font_size},&H00FFFFFF,&H000000FF,&H00000000,&H78000000,-1,0,0,0,100,100,0,0,1,5,1,2,100,100,{margin_v},1
Style: Default,{font_name},80,&H00FFFFFF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,6,2,2,100,100,250,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        dialogue_lines: List[str] = []

        for subtitle in subtitles:
            start = self._ass_time(
                subtitle["start"]
            )
            end = self._ass_time(
                subtitle["end"]
            )

            font_size = int(
                subtitle.get("font_size")
                or default_font_size
            )

            safe_text = self._escape_ass_text(
                subtitle.get("wrapped_text")
                or subtitle.get("text")
                or ""
            )

            styled_text = (
                rf"{{\fs{font_size}}}"
                + safe_text
            )

            dialogue_lines.append(
                f"Dialogue: 0,{start},{end},Default,,0,0,0,,{styled_text}"
            )

        return (
            header
            + "\n".join(dialogue_lines)
            + "\n"
        )

    def _adjust_font_size(
        self,
        text: str,
        requested_font_size: int,
    ) -> int:
        length = len(
            str(text)
            .replace(" ", "")
            .replace("\n", "")
        )

        requested = max(
            int(requested_font_size),
            36,
        )

        if length <= 15:
            return min(requested, 72)

        if length <= 28:
            return min(requested, 62)

        if length <= 42:
            return min(requested, 54)

        return min(requested, 48)

    def _wrap_subtitle_text(
        self,
        text: str,
        max_chars_per_line: int = 15,
        max_lines: int = 3,
    ) -> str:
        normalized = " ".join(
            str(text or "")
            .replace("\r", " ")
            .replace("\n", " ")
            .split()
        )

        if not normalized:
            return ""

        max_chars = max(
            int(max_chars_per_line),
            8,
        )

        max_lines = max(
            int(max_lines),
            1,
        )

        words = normalized.split(" ")

        lines: List[str] = []
        current = ""

        for word in words:
            candidate = (
                f"{current} {word}".strip()
                if current
                else word
            )

            if len(candidate) <= max_chars:
                current = candidate
                continue

            if current:
                lines.append(current)
                current = ""

            if len(word) <= max_chars:
                current = word
                continue

            chunks = [
                word[position:position + max_chars]
                for position in range(
                    0,
                    len(word),
                    max_chars,
                )
            ]

            for chunk in chunks:
                if len(lines) < max_lines - 1:
                    lines.append(chunk)
                else:
                    current = (
                        f"{current} {chunk}".strip()
                        if current
                        else chunk
                    )

        if current:
            lines.append(current)

        if len(lines) > max_lines:
            merged_last_line = " ".join(
                lines[max_lines - 1:]
            )

            lines = (
                lines[:max_lines - 1]
                + [merged_last_line]
            )

        return "\n".join(lines)

    def _ass_time(
        self,
        seconds: float,
    ) -> str:
        total = max(
            float(seconds),
            0.0,
        )

        hours = int(total // 3600)
        minutes = int(
            (total % 3600) // 60
        )
        secs = total % 60

        return (
            f"{hours}:"
            f"{minutes:02d}:"
            f"{secs:05.2f}"
        )

    def _escape_ass_text(
        self,
        text: str,
    ) -> str:
        return (
            str(text)
            .replace("\\", r"\\")
            .replace("{", r"\{")
            .replace("}", r"\}")
            .replace("\r\n", r"\N")
            .replace("\n", r"\N")
            .replace("\r", r"\N")
        )

    def _escape_filter_path(
        self,
        path: Path,
    ) -> str:
        text = path.as_posix()
        text = text.replace(":", r"\:")
        text = text.replace("'", r"\'")

        return f"'{text}'"