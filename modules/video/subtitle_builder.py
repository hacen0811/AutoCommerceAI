from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


class SubtitleBuilder:
    """
    Sprint 56-1 Subtitle Builder

    역할:
    - AI 콘텐츠 팩에서 자막 후보 추출
    - timeline / cut_plan / captions 구조 지원
    - 시작·종료 시간을 초 단위로 정규화
    - 빈 자막 자동 제외
    - 의미 단위 중심으로 최대 2줄 정리
    - 한국어 조사와 어미가 부자연스럽게 분리되지 않도록 보호
    - SubtitleEngine에 전달할 표준 자막 리스트 생성
    """

    BUILDER_VERSION = "subtitle-builder-56-1"

    DEFAULT_MAX_CHARS_PER_LINE = 16
    DEFAULT_MAX_LINES = 2

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
        "또",
        "때문에",
        "덕분에",
        "사용하면",
        "붙이면",
        "누르면",
        "열면",
        "넣으면",
        "정리하면",
        "확인하면",
        "필요하면",
        "추천드려요",
        "추천합니다",
        "사용해보세요",
        "확인해보세요",
    )

    PROTECTED_ENDINGS = (
        "은",
        "는",
        "이",
        "가",
        "을",
        "를",
        "에",
        "에서",
        "와",
        "과",
        "도",
        "만",
        "의",
        "로",
        "으로",
        "에게",
        "보다",
        "처럼",
        "까지",
        "부터",
        "하고",
        "하며",
        "해서",
        "하면",
        "하면요",
        "인데",
        "인데요",
        "입니다",
        "됩니다",
        "있어요",
        "없어요",
        "해요",
        "예요",
        "이에요",
    )

    SENTENCE_PATTERN = re.compile(r"[,.!?…。！？]+")

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
                max_lines=self.DEFAULT_MAX_LINES,
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
        2. 문장부호 뒤 분리
        3. 접속사·전환 표현 앞 분리
        4. 띄어쓰기 위치 기준 분리
        5. 마지막으로 글자 수 기준 분리
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

        first, second = self._rebalance_lines(
            first=first,
            second=second,
            max_chars_per_line=max_chars_per_line,
        )

        return self._join_two_lines(
            first,
            second,
            max_lines=max_lines,
        )

    def _find_semantic_split(
        self,
        text: str,
        max_chars_per_line: int,
    ) -> Optional[int]:
        text_length = len(text)
        midpoint = text_length / 2

        candidates: List[Tuple[float, int]] = []

        for match in self.SENTENCE_PATTERN.finditer(text):
            position = match.end()

            if 2 <= position <= text_length - 2:
                score = abs(position - midpoint)

                if position <= max_chars_per_line + 4:
                    score -= 6

                candidates.append((score, position))

        for word in self.SEMANTIC_BREAK_WORDS:
            start = 0

            while True:
                position = text.find(word, start)

                if position < 0:
                    break

                if 2 <= position <= text_length - 2:
                    score = abs(position - midpoint) + 2

                    if position <= max_chars_per_line + 4:
                        score -= 5

                    candidates.append((score, position))

                start = position + len(word)

        for match in re.finditer(r"\s+", text):
            position = match.start()

            if 2 <= position <= text_length - 2:
                score = abs(position - midpoint) + 5

                if position <= max_chars_per_line + 2:
                    score -= 3

                if self._is_protected_split(text, position):
                    score += 20

                candidates.append((score, position))

        if not candidates:
            return self._fallback_split_index(
                text,
                max_chars_per_line,
            )

        candidates.sort(key=lambda item: item[0])

        for _, position in candidates:
            if not self._is_protected_split(text, position):
                return position

        return self._fallback_split_index(
            text,
            max_chars_per_line,
        )

    def _fallback_split_index(
        self,
        text: str,
        max_chars_per_line: int,
    ) -> Optional[int]:
        """
        띄어쓰기가 거의 없는 문장도 최대 2줄로 나눌 수 있도록 처리합니다.
        """
        if len(text) <= max_chars_per_line:
            return None

        target = min(
            max_chars_per_line,
            max(len(text) // 2, 1),
        )

        for offset in range(0, 7):
            positions = (
                target + offset,
                target - offset,
            )

            for position in positions:
                if position <= 1 or position >= len(text):
                    continue

                if self._is_protected_split(text, position):
                    continue

                return position

        return target

    def _is_protected_split(
        self,
        text: str,
        position: int,
    ) -> bool:
        left = text[:position].rstrip()
        right = text[position:].lstrip()

        if not left or not right:
            return True

        if left.endswith(self.PROTECTED_ENDINGS):
            return True

        if right.startswith(self.PROTECTED_ENDINGS):
            return True

        return False

    def _rebalance_lines(
        self,
        first: str,
        second: str,
        max_chars_per_line: int,
    ) -> Tuple[str, str]:
        """
        한쪽 줄이 지나치게 길거나 짧으면 공백 단위로 균형을 조정합니다.
        """
        first = self._normalize_spaces(first)
        second = self._normalize_spaces(second)

        combined = f"{first} {second}".strip()

        if (
            len(first) <= max_chars_per_line + 4
            and len(second) <= max_chars_per_line + 4
        ):
            return first, second

        spaces = [
            match.start()
            for match in re.finditer(r"\s+", combined)
        ]

        if not spaces:
            return first, second

        midpoint = len(combined) / 2

        valid_positions = [
            position
            for position in spaces
            if not self._is_protected_split(combined, position)
        ]

        if not valid_positions:
            return first, second

        best_position = min(
            valid_positions,
            key=lambda position: abs(position - midpoint),
        )

        balanced_first = combined[:best_position].strip()
        balanced_second = combined[best_position:].strip()

        if not balanced_first or not balanced_second:
            return first, second

        return balanced_first, balanced_second

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

        lines: List[str] = []

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