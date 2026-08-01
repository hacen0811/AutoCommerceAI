from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple


print(
    "######## SUBTITLE_BUILDER SPRINT154 LOCKED SCRIPT CTA FINAL LOADED ########",
    flush=True,
)


class SubtitleBuilder:
    """
    Sprint153-1 Locked Script Only Subtitle Builder

    핵심:
    - 실제 잠금 대본만 자막으로 사용
    - review_scripts.scene_subtitles[].subtitle 최우선
    - locked_script / best_script는 안전한 대체 경로
    - scene_goal, visual_direction, image_prompt 등 연출 문구는 사용 금지
    - CTA는 마지막 자막에 한 번만 유지
    - 전체 자막 길이는 target_duration_seconds에 맞춰 자동 배분
    """

    VERSION = "subtitle-builder-154-locked-script-cta-final"

    DIRECTOR_KEYS = {
        "scene_goal",
        "visual_direction",
        "scene_direction",
        "camera_direction",
        "image_prompt",
        "negative_prompt",
        "must_show",
        "prompt",
        "description",
        "visual_prompt",
        "director_text",
    }

    CTA_PATTERNS = (
        "궁금하시면 클릭",
        "클릭!",
        "클릭해",
        "링크",
        "구매하러",
        "확인하세요",
        "설명에서 확인",
        "프로필",
    )

    def build_result(
        self,
        content_pack: Dict[str, Any],
    ) -> Dict[str, Any]:
        pack = content_pack if isinstance(content_pack, dict) else {}

        target_duration = self._to_float(
            pack.get("target_duration_seconds"),
            default=25.0,
        )
        target_duration = max(3.0, target_duration)

        texts, source = self._extract_locked_subtitle_texts(pack)
        texts = self._normalize_texts(texts)
        texts = self._move_cta_to_end_once(texts)

        if not texts:
            result = {
                "ok": False,
                "version": self.VERSION,
                "status": "locked_script_missing",
                "subtitle_source": source or "none",
                "target_duration_seconds": target_duration,
                "subtitle_count": 0,
                "subtitles": [],
                "errors": [
                    "실제 잠금 대본 자막을 찾지 못했습니다.",
                ],
            }
            self._log_result(result)
            return result

        subtitles = self._build_timeline(
            texts=texts,
            total_duration=target_duration,
        )

        result = {
            "ok": bool(subtitles),
            "version": self.VERSION,
            "status": "built" if subtitles else "failed",
            "subtitle_source": source,
            "target_duration_seconds": target_duration,
            "subtitle_count": len(subtitles),
            "subtitles": subtitles,
            "director_text_blocked": True,
            "cta_last_only": True,
            "errors": [],
        }
        self._log_result(result)
        return result

    def build(
        self,
        content_pack: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        return list(
            self.build_result(content_pack).get("subtitles") or []
        )

    def _extract_locked_subtitle_texts(
        self,
        pack: Dict[str, Any],
    ) -> Tuple[List[str], str]:
        review_scripts = (
            pack.get("review_scripts")
            if isinstance(pack.get("review_scripts"), dict)
            else {}
        )

        # 1순위: WorkflowEngine이 잠근 실제 장면별 대본
        scene_subtitles = review_scripts.get("scene_subtitles") or []
        extracted = []

        if isinstance(scene_subtitles, list):
            ordered_items = sorted(
                (
                    item
                    for item in scene_subtitles
                    if isinstance(item, dict)
                ),
                key=lambda item: self._to_int(
                    item.get("order"),
                    default=999999,
                ),
            )

            for item in ordered_items:
                text = self._clean_text(
                    item.get("subtitle")
                    or item.get("dialogue")
                    or ""
                )
                if text:
                    extracted.append(text)

        if extracted:
            return extracted, "review_scripts.scene_subtitles"

        # 2순위: 원클릭 UI에서 전달된 잠금 대본 원문
        locked_script = self._clean_text(pack.get("locked_script"))
        if locked_script:
            return (
                self._split_script(locked_script),
                "content_pack.locked_script",
            )

        # 3순위: 승인 완료 대본
        for key in (
            "best_script",
            "original_best_script",
            "short_script",
            "medium_script",
            "long_script",
        ):
            script = self._clean_text(review_scripts.get(key))
            if script:
                return (
                    self._split_script(script),
                    f"review_scripts.{key}",
                )

        script_approval = (
            pack.get("script_approval")
            if isinstance(pack.get("script_approval"), dict)
            else {}
        )
        approved_script = self._clean_text(
            script_approval.get("best_script")
            or pack.get("approved_script_text")
        )
        if approved_script:
            return (
                self._split_script(approved_script),
                "script_approval.best_script",
            )

        # 의도적으로 timeline/scenes/director 데이터는 읽지 않습니다.
        return [], "none"

    def _split_script(self, value: str) -> List[str]:
        text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
        parts = re.split(r"(?<=[.!?。！？])\s+|\n+", text)

        cleaned = [
            self._clean_text(part)
            for part in parts
            if self._clean_text(part)
        ]
        return cleaned or ([self._clean_text(text)] if self._clean_text(text) else [])

    def _normalize_texts(
        self,
        texts: List[str],
    ) -> List[str]:
        normalized = []
        seen = set()

        for value in texts or []:
            text = self._clean_text(value)
            if not text:
                continue

            marker = re.sub(r"\s+", "", text).lower()
            if not marker or marker in seen:
                continue

            seen.add(marker)
            normalized.append(text)

        return normalized

    def _move_cta_to_end_once(
        self,
        texts: List[str],
    ) -> List[str]:
        if not texts:
            return []

        normal_texts = []
        cta_text = ""

        for text in texts:
            if self._is_cta(text):
                cta_text = text
            else:
                normal_texts.append(text)

        if cta_text:
            normal_texts.append(cta_text)

        return normal_texts

    def _is_cta(self, text: str) -> bool:
        normalized = re.sub(r"\s+", "", str(text or "")).lower()
        return any(
            re.sub(r"\s+", "", pattern).lower() in normalized
            for pattern in self.CTA_PATTERNS
        )

    def _build_timeline(
        self,
        texts: List[str],
        total_duration: float,
    ) -> List[Dict[str, Any]]:
        if not texts:
            return []

        weights = []
        for index, text in enumerate(texts):
            # 글자 수 기반으로 읽는 시간을 분배하되 지나친 편차는 제한합니다.
            compact_length = len(re.sub(r"\s+", "", text))
            weight = max(1.0, min(3.0, compact_length / 18.0))

            if index == 0:
                weight = max(weight, 1.20)
            if index == len(texts) - 1 and self._is_cta(text):
                weight = max(weight, 1.25)

            weights.append(weight)

        weight_sum = sum(weights) or 1.0
        raw_durations = [
            total_duration * weight / weight_sum
            for weight in weights
        ]

        # 각 자막이 너무 짧게 지나가지 않게 최소 시간을 보장합니다.
        minimum = 1.20
        if minimum * len(texts) <= total_duration:
            durations = [max(minimum, value) for value in raw_durations]
            scale = total_duration / (sum(durations) or total_duration)
            durations = [value * scale for value in durations]
        else:
            durations = raw_durations

        subtitles = []
        cursor = 0.0

        for index, (text, duration) in enumerate(
            zip(texts, durations),
            start=1,
        ):
            start = round(cursor, 3)
            end = (
                round(total_duration, 3)
                if index == len(texts)
                else round(cursor + duration, 3)
            )

            if end <= start:
                end = round(start + 0.1, 3)

            subtitles.append(
                {
                    "index": index,
                    "text": text,
                    "start": start,
                    "end": end,
                    "duration": round(end - start, 3),
                    "source": "locked_user_script",
                    "is_cta": self._is_cta(text),
                }
            )
            cursor = end

        return subtitles

    def _clean_text(self, value: Any) -> str:
        text = str(value or "")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def _to_float(
        value: Any,
        default: float,
    ) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    @staticmethod
    def _to_int(
        value: Any,
        default: int,
    ) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return int(default)

    def _log_result(
        self,
        result: Dict[str, Any],
    ) -> None:
        print(
            "[Sprint154 Subtitle Builder] Version:",
            result.get("version", self.VERSION),
            flush=True,
        )
        print(
            "[Sprint154 Subtitle Builder] Status:",
            result.get("status", ""),
            flush=True,
        )
        print(
            "[Sprint154 Subtitle Builder] Source:",
            result.get("subtitle_source", ""),
            flush=True,
        )
        print(
            "[Sprint154 Subtitle Builder] Count:",
            result.get("subtitle_count", 0),
            flush=True,
        )
        print(
            "[Sprint154 Subtitle Builder] Director Text Blocked:",
            result.get("director_text_blocked", True),
            flush=True,
        )
        print(
            "[Sprint154 Subtitle Builder] CTA Last Only:",
            result.get("cta_last_only", True),
            flush=True,
        )
