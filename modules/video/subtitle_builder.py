from __future__ import annotations

import re
from typing import Any, Dict, List


class SubtitleBuilder:
    """
    Sprint 55-1 Subtitle Builder

    역할:
    - AI 콘텐츠 팩에서 자막 후보 추출
    - timeline / cut_plan / captions 구조 지원
    - 시작·종료 시간을 초 단위로 정규화
    - 빈 자막 자동 제외
    - 긴 자막을 의미 단위로 최대 2줄 정리
    - SubtitleEngine에 전달할 표준 자막 리스트 생성
    """

    BUILDER_VERSION = "subtitle-builder-55-1"

    # 세로형 쇼츠 기준 한 줄 권장 길이
    DEFAULT_MAX_CHARS_PER_LINE = 16

    # 자연스러운 줄바꿈 위치로 우선 사용하는 표현
    SEMANTIC_BREAK_WORDS = (
        "그래서",
        "하지만",
        "그런데",
        "그리고",
        "그러면",
        "이제",
        "바로",
        "특히",
        "사실",
        "결국",
        "대신",
        "때문에",
        "덕분에",
        "사용하면",
        "놓으면",
        "누르면",
        "열면",
        "닫으면",
        "정리하면",
        "확인하면",
        "필요하면",
        "추천드려요",
        "추천합니다",
        "사용해보세요",
        "확인해보세요",
    )

    def build(
        self,
        content_pack: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        content_pack = content_pack or {}

        items = (
            self._timeline_items(content_pack)
            or self._cut_plan_items(content_pack)
            or self._caption_items(content_pack)
        )

        subtitles: List[Dict[str, Any]] = []

        for index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                continue

            raw_text = self._extract_text(item)

            if not raw_text:
                continue

            formatted_text = self._format_subtitle_text(
                raw_text,
                max_chars_per_line=self.DEFAULT_MAX_CHARS_PER_LINE,
                max_lines=2,
            )

            if not formatted_text:
                continue

            start = self._time_value(
                item.get("start")
                or item.get("start_time")
                or item.get("from")
                or item.get("begin"),
                default=float(index - 1) * 3.0,
            )

            end = self._time_value(
                item.get("end")
                or item.get("end_time")
                or item.get("to")
                or item.get("finish"),
                default=start + 3.0,
            )

            if end <= start:
                end = start + 3.0

            subtitles.append(
                {
                    "index": index,
                    "start": start,
                    "end": end,
                    "duration": end - start,
                    "text": formatted_text,
                    "raw_text": raw_text,
                    "line_count": len(formatted_text.splitlines()),
                    "scene": (
                        item.get("scene")
                        or item.get("index")
                        or index
                    ),
                    "source": item,
                }
            )

        return subtitles

    def build_result(
        self,
        content_pack: Dict[str, Any],
    ) -> Dict[str, Any]:
        subtitles = self.build(content_pack)

        return {
            "ok": bool(subtitles),
            "builder_version": self.BUILDER_VERSION,
            "subtitle_count": len(subtitles),
            "subtitles": subtitles,
            "message": (
                f"총 {len(subtitles)}개 자막을 생성했습니다."
                if subtitles
                else "사용 가능한 자막을 찾지 못했습니다."
            ),
        }

    def _timeline_items(
        self,
        content_pack: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        direct = content_pack.get("timeline")

        if isinstance(direct, list):
            return direct

        edit = content_pack.get("edit_assistant") or {}

        for key in ("timeline", "scene_plan", "scenes"):
            value = edit.get(key)

            if isinstance(value, list):
                return value

        shorts = content_pack.get("shorts") or {}

        for key in ("timeline", "scene_plan", "scenes"):
            value = shorts.get(key)

            if isinstance(value, list):
                return value

        return []

    def _cut_plan_items(
        self,
        content_pack: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        cut_plan = content_pack.get("cut_plan")

        if isinstance(cut_plan, list):
            return cut_plan

        return []

    def _caption_items(
        self,
        content_pack: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        captions = content_pack.get("captions") or {}

        if isinstance(captions, list):
            raw_items = captions

        elif isinstance(captions, dict):
            raw_items = (
                captions.get("items")
                or captions.get("captions")
                or captions.get("subtitles")
                or []
            )

        else:
            raw_items = []

        normalized: List[Dict[str, Any]] = []

        for index, item in enumerate(raw_items, start=1):
            if isinstance(item, dict):
                normalized.append(item)
                continue

            text = str(item or "").strip()

            if not text:
                continue

            start = float(index - 1) * 3.0

            normalized.append(
                {
                    "scene": index,
                    "start": start,
                    "end": start + 3.0,
                    "text": text,
                }
            )

        return normalized

    def _extract_text(
        self,
        item: Dict[str, Any],
    ) -> str:
        for key in (
            "subtitle",
            "caption",
            "text",
            "script",
            "line",
            "narration",
            "voiceover",
            "message",
        ):
            value = item.get(key)

            if isinstance(value, str) and value.strip():
                return self._normalize_spaces(value)

        return ""

    def _format_subtitle_text(
        self,
        text: str,
        max_chars_per_line: int = 16,
        max_lines: int = 2,
    ) -> str:
        """
        자막을 의미 단위 중심으로 최대 2줄로 정리합니다.

        우선순위:
        1. 기존 줄바꿈 존중
        2. 문장부호 뒤에서 분리
        3. 접속어·조건 표현 앞에서 분리
        4. 띄어쓰기 기준으로 길이 균형 분리
        """
        text = self._normalize_spaces(text)

        if not text:
            return ""

        existing_lines = [
            self._normalize_spaces(line)
            for line in re.split(r"[\r\n]+", text)
            if self._normalize_spaces(line)
        ]

        if len(existing_lines) >= 2:
            first = existing_lines[0]
            second = " ".join(existing_lines[1:])

            return self._join_two_lines(
                first,
                second,
                max_lines=max_lines,
            )

        if len(text) <= max_chars_per_line:
            return text

        split_index = self._find_semantic_split(
            text=text,
            max_chars_per_line=max_chars_per_line,
        )

        if split_index is None:
            return text

        first = text[:split_index].strip()
        second = text[split_index:].strip()

        if not first or not second:
            return text

        return self._join_two_lines(
            first,
            second,
            max_lines=max_lines,
        )

    def _find_semantic_split(
        self,
        text: str,
        max_chars_per_line: int,
    ) -> int | None:
        text_length = len(text)
        midpoint = text_length / 2

        candidates: List[tuple[float, int]] = []

        # 쉼표, 마침표, 물음표 등 문장부호 뒤
        for match in re.finditer(r"[,.!?。！？,，]\s*", text):
            position = match.end()

            if 2 <= position <= text_length - 2:
                score = abs(position - midpoint)

                # 권장 길이를 크게 벗어나지 않는 지점 우선
                if position <= max_chars_per_line + 4:
                    score -= 5

                candidates.append((score, position))

        # 의미 전환 표현 앞
        for word in self.SEMANTIC_BREAK_WORDS:
            start = 0

            while True:
                position = text.find(word, start)

                if position < 0:
                    break

                if 2 <= position <= text_length - 2:
                    score = abs(position - midpoint) + 2

                    if position <= max_chars_per_line + 4:
                        score -= 4

                    candidates.append((score, position))

                start = position + len(word)

        # 띄어쓰기 위치
        for match in re.finditer(r"\s+", text):
            position = match.start()

            if 2 <= position <= text_length - 2:
                score = abs(position - midpoint) + 5

                if position <= max_chars_per_line + 2:
                    score -= 3

                candidates.append((score, position))

        if not candidates:
            return self._fallback_split_index(
                text,
                max_chars_per_line,
            )

        candidates.sort(key=lambda item: item[0])
        return candidates[0][1]

    def _fallback_split_index(
        self,
        text: str,
        max_chars_per_line: int,
    ) -> int | None:
        """
        띄어쓰기가 거의 없는 문장도 두 줄로 나눌 수 있도록 처리합니다.
        """
        if len(text) <= max_chars_per_line:
            return None

        target = min(
            max_chars_per_line,
            max(len(text) // 2, 1),
        )

        # 조사나 어미 중간이 아닌 위치를 약하게 탐색
        protected_endings = (
            "은",
            "는",
            "이",
            "가",
            "을",
            "를",
            "에",
            "의",
            "와",
            "과",
            "도",
            "로",
            "으로",
        )

        for offset in range(0, 5):
            for position in (
                target + offset,
                target - offset,
            ):
                if position <= 1 or position >= len(text):
                    continue

                left = text[:position]

                if any(
                    left.endswith(ending)
                    for ending in protected_endings
                ):
                    continue

                return position

        return target

    def _join_two_lines(
        self,
        first: str,
        second: str,
        max_lines: int,
    ) -> str:
        first = self._normalize_spaces(first)
        second = self._normalize_spaces(second)

        if not second or max_lines <= 1:
            return first

        return f"{first}\n{second}"

    def _normalize_spaces(
        self,
        value: str,
    ) -> str:
        text = str(value or "")

        # 기존 줄바꿈은 보존하고 각 줄 내부 공백만 정리
        lines = []

        for line in re.split(r"[\r\n]+", text):
            cleaned = re.sub(r"[ \t]+", " ", line).strip()

            if cleaned:
                lines.append(cleaned)

        return "\n".join(lines)

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

            parts = [
                float(part)
                for part in text.split(":")
            ]

            if len(parts) == 2:
                minutes, seconds = parts

                return max(
                    (minutes * 60) + seconds,
                    0.0,
                )

            if len(parts) == 3:
                hours, minutes, seconds = parts

                return max(
                    (hours * 3600)
                    + (minutes * 60)
                    + seconds,
                    0.0,
                )

        except (TypeError, ValueError):
            return default

        return default