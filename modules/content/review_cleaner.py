from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any, Dict, Iterable, List, Optional


class ReviewCleaner:
    """
    Sprint73-1 OCR Review Cleaner

    역할:
    - OCR 깨진 문자와 불필요한 기호 제거
    - 별점/날짜/옵션/도움돼요 등 리뷰 메타 문구 제거
    - 지나치게 짧거나 의미 없는 텍스트 제거
    - 동일·유사 리뷰 중복 제거
    - 기존 dict 리뷰 구조를 최대한 보존
    - 외부 AI API 없이 동작
    """

    VERSION = "review-cleaner-73-1"

    TEXT_KEYS = (
        "content",
        "review",
        "text",
        "body",
        "comment",
        "review_content",
        "headline",
        "title",
        "ocr_text",
        "raw_text",
    )

    META_ONLY_PATTERNS = (
        r"^\s*\d(?:\.\d)?\s*점\s*$",
        r"^\s*[★☆⭐]{1,5}\s*$",
        r"^\s*\d{4}[./-]\d{1,2}[./-]\d{1,2}\s*$",
        r"^\s*\d{1,2}[./-]\d{1,2}\s*$",
        r"^\s*(도움이\s*돼요|도움돼요|신고하기|판매자|작성자)\s*$",
        r"^\s*(옵션|선택 옵션|구매 옵션)\s*[:：]?\s*$",
        r"^\s*(한달사용기|재구매|베스트리뷰|일반리뷰)\s*$",
        r"^\s*(배송|포장|가격|품질)\s*$",
        r"^\s*\d+\s*(명|개)\s*$",
    )

    REMOVE_INLINE_PATTERNS = (
        r"https?://\S+",
        r"www\.\S+",
        r"\b\d{4}[./-]\d{1,2}[./-]\d{1,2}\b",
        r"\b\d{1,2}[./-]\d{1,2}\b",
        r"도움이\s*돼요\s*\d*",
        r"도움돼요\s*\d*",
        r"신고하기",
        r"작성자\s*[:：]?\s*\S+",
        r"판매자\s*[:：]?\s*\S+",
        r"별점\s*[:：]?\s*\d(?:\.\d)?",
        r"[★☆⭐]{2,5}",
    )

    NOISE_TOKENS = {
        "리뷰",
        "상품평",
        "구매후기",
        "후기",
        "사진",
        "동영상",
        "더보기",
        "접기",
        "옵션",
        "선택",
        "도움",
        "신고",
        "작성",
        "구매자",
        "판매자",
    }

    def __init__(
        self,
        min_length: int = 5,
        max_length: int = 500,
        similarity_threshold: float = 0.92,
    ) -> None:
        self.min_length = max(2, int(min_length))
        self.max_length = max(self.min_length, int(max_length))
        self.similarity_threshold = min(
            1.0,
            max(0.70, float(similarity_threshold)),
        )

    def clean(
        self,
        reviews: Any,
        source: str = "",
    ) -> Dict[str, Any]:
        items = self._to_items(reviews)
        cleaned_items: List[Dict[str, Any]] = []
        seen_keys: List[str] = []

        stats = {
            "input_count": len(items),
            "empty_removed": 0,
            "short_removed": 0,
            "meta_removed": 0,
            "noise_removed": 0,
            "duplicate_removed": 0,
            "trimmed_count": 0,
        }

        for index, item in enumerate(items):
            raw_text = self._extract_text(item)
            text = self.clean_text(raw_text)

            if not text:
                stats["empty_removed"] += 1
                continue

            if self._is_meta_only(text):
                stats["meta_removed"] += 1
                continue

            if len(text) < self.min_length:
                stats["short_removed"] += 1
                continue

            if self._is_noise_only(text):
                stats["noise_removed"] += 1
                continue

            if len(text) > self.max_length:
                text = text[: self.max_length].rstrip()
                stats["trimmed_count"] += 1

            duplicate_key = self._duplicate_key(text)

            if self._is_duplicate(duplicate_key, seen_keys):
                stats["duplicate_removed"] += 1
                continue

            seen_keys.append(duplicate_key)

            cleaned = dict(item) if isinstance(item, dict) else {}
            cleaned.update(
                {
                    "content": text,
                    "text": text,
                    "clean_text": text,
                    "raw_text": raw_text,
                    "source": (
                        cleaned.get("source")
                        or source
                        or "unknown"
                    ),
                    "original_index": index,
                    "cleaner_version": self.VERSION,
                }
            )
            cleaned_items.append(cleaned)

        stats["output_count"] = len(cleaned_items)
        stats["removed_count"] = (
            stats["input_count"] - stats["output_count"]
        )

        return {
            "ok": bool(cleaned_items),
            "version": self.VERSION,
            "status": "cleaned" if cleaned_items else "empty",
            "source": source or "mixed",
            "input_count": stats["input_count"],
            "review_count": len(cleaned_items),
            "reviews": cleaned_items,
            "texts": [
                item["clean_text"]
                for item in cleaned_items
            ],
            "stats": stats,
            "warnings": (
                []
                if cleaned_items
                else ["정제 후 사용할 수 있는 리뷰가 없습니다."]
            ),
        }

    def clean_text(self, value: Any) -> str:
        text = str(value or "")
        text = text.replace("\x00", " ")
        text = text.replace("\ufeff", " ")
        text = text.replace("\u200b", " ")
        text = re.sub(r"<[^>]+>", " ", text)

        for pattern in self.REMOVE_INLINE_PATTERNS:
            text = re.sub(
                pattern,
                " ",
                text,
                flags=re.IGNORECASE,
            )

        # OCR에서 반복되는 구분선·아이콘·깨진 특수문자를 제거합니다.
        text = re.sub(r"[|¦｜]+", " ", text)
        text = re.sub(r"[_=~`^]{2,}", " ", text)
        text = re.sub(r"[•·●○■□◆◇▶▷►※]+", " ", text)
        text = re.sub(r"[�]+", " ", text)

        # 한글, 영문, 숫자, 일반 문장부호만 남깁니다.
        text = re.sub(
            r"[^0-9A-Za-z가-힣ㄱ-ㅎㅏ-ㅣ\s.,!?%()\-+/:'\"&]",
            " ",
            text,
        )

        # OCR 반복 문자 축약: ㅋㅋㅋㅋ -> ㅋㅋ, !!!! -> !!
        text = re.sub(r"(ㅋ|ㅎ|ㅠ|ㅜ)\1{2,}", r"\1\1", text)
        text = re.sub(r"([!?.,])\1{2,}", r"\1\1", text)

        # 문자 사이가 과도하게 띄어진 OCR 문장은 보수적으로 복원합니다.
        text = re.sub(
            r"(?<=[가-힣])\s+(?=[가-힣](?:\s|$))",
            " ",
            text,
        )

        text = re.sub(r"\s+", " ", text).strip()
        text = text.strip(" -_/|,.;:")

        return text

    def _to_items(self, reviews: Any) -> List[Any]:
        if reviews is None:
            return []

        if isinstance(reviews, str):
            return self._split_multiline_text(reviews)

        if isinstance(reviews, dict):
            for key in (
                "reviews",
                "items",
                "data",
                "results",
                "review_list",
                "texts",
            ):
                value = reviews.get(key)
                if isinstance(value, (list, tuple)):
                    return list(value)

            return [reviews]

        if isinstance(reviews, (list, tuple, set)):
            result: List[Any] = []
            for item in reviews:
                if isinstance(item, str) and "\n" in item:
                    result.extend(self._split_multiline_text(item))
                else:
                    result.append(item)
            return result

        return []

    def _split_multiline_text(self, text: str) -> List[str]:
        lines = [
            line.strip()
            for line in re.split(r"[\r\n]+", str(text or ""))
            if line.strip()
        ]
        return lines or ([text] if text.strip() else [])

    def _extract_text(self, item: Any) -> str:
        if isinstance(item, str):
            return item

        if not isinstance(item, dict):
            return ""

        parts: List[str] = []

        for key in self.TEXT_KEYS:
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                parts.append(value.strip())

        # 같은 문구가 여러 키에 반복된 경우 한 번만 합칩니다.
        return " ".join(dict.fromkeys(parts))

    def _is_meta_only(self, text: str) -> bool:
        return any(
            re.fullmatch(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
            for pattern in self.META_ONLY_PATTERNS
        )

    def _is_noise_only(self, text: str) -> bool:
        words = re.findall(r"[0-9A-Za-z가-힣]+", text)
        if not words:
            return True

        meaningful = [
            word
            for word in words
            if word.lower() not in self.NOISE_TOKENS
            and not word.isdigit()
        ]

        # 문자가 거의 없거나 메타 단어만 남은 경우 제거합니다.
        alpha_count = len(
            re.findall(r"[A-Za-z가-힣]", text)
        )
        return not meaningful or alpha_count < 3

    def _duplicate_key(self, text: str) -> str:
        key = text.lower()
        key = re.sub(r"[^0-9a-z가-힣]", "", key)
        return key

    def _is_duplicate(
        self,
        key: str,
        seen_keys: Iterable[str],
    ) -> bool:
        if not key:
            return True

        for seen in seen_keys:
            if key == seen:
                return True

            # 매우 짧은 문장은 유사도 오탐 가능성이 커서 완전 일치만 봅니다.
            if min(len(key), len(seen)) < 15:
                continue

            ratio = SequenceMatcher(
                None,
                key,
                seen,
            ).ratio()

            if ratio >= self.similarity_threshold:
                return True

        return False


def clean_reviews(
    reviews: Any,
    source: str = "",
    min_length: int = 5,
) -> Dict[str, Any]:
    """간단 호출용 함수입니다."""
    return ReviewCleaner(
        min_length=min_length
    ).clean(
        reviews=reviews,
        source=source,
    )