from __future__ import annotations

import re
from collections import Counter
from difflib import SequenceMatcher
from typing import Any, Dict, Iterable, List


class ReviewQualityAnalyzer:
    """
    Sprint116-1 Review Quality Analyzer

    역할:
    - 정제된 리뷰의 신뢰도·구체성·실사용성·관련성 평가
    - 광고성·상투성·과장성·중복 가능성 감점
    - 직접 입력 과정에서 문단 단위로 잘린 리뷰를 후기 단위로 재결합
    - 고품질 리뷰만 ReviewInsightEngine으로 전달
    - 외부 AI API 없이 규칙 기반으로 동작
    """

    VERSION = "review-quality-analyzer-116-1"

    GENERIC_PHRASES = (
        "좋아요",
        "좋습니다",
        "만족합니다",
        "추천합니다",
        "최고입니다",
        "잘 쓸게요",
        "배송 빨라요",
        "가성비 좋아요",
    )

    EXPERIENCE_PATTERNS = (
        r"(직접|실제로)\s*(사용|써|착용|들고|걸고)",
        r"(사용해\s*보니|써\s*보니|착용해\s*보니|써봤는데)",
        r"\d+\s*(일|주|개월|달|년|시간|분)\s*(동안|정도)?",
        r"(출퇴근|등하굣길|산책|캠핑|여행|야외|사무실|대중교통)",
        r"(아직|지금도|하루\s*종일|오래)\s*(사용|써|켜|걸)",
    )

    SPECIFIC_PATTERNS = (
        r"\d+\s*(g|kg|mah|시간|단계|단|인치|퍼센트|%)",
        r"(배터리|풍속|풍량|무게|소음|충전|디스플레이|모터|각도)",
        r"(장점|단점|아쉬운|불편|다만|하지만)",
        r"(목에\s*걸|손이\s*자유|주머니|포켓|책상|스트랩)",
    )

    PROMOTIONAL_PATTERNS = (
        r"(강력\s*추천|적극\s*추천|무조건\s*추천)",
        r"(최고의\s*선택|완벽한\s*제품|필수템|필수\s*아이템)",
        r"(압도적|극강|일품|삼박자|스마트한\s*솔루션)",
        r"(누구나|남녀노소|어린아이부터\s*어르신까지)",
    )

    NEGATIVE_SIGNAL_PATTERNS = (
        r"(아쉽|불편|거슬|소음|무겁|약하|부족|단점|걱정)",
        r"(최고\s*단계|강풍).{0,20}(소리|소음|모터)",
    )

    RATING_PREFIXES = (
        "디자인:",
        "소음:",
        "편리성:",
        "바람 세기:",
        "마감 품질:",
    )

    def __init__(
        self,
        accept_threshold: float = 52.0,
        duplicate_threshold: float = 0.90,
        max_selected: int = 30,
    ) -> None:
        self.accept_threshold = float(accept_threshold)
        self.duplicate_threshold = float(duplicate_threshold)
        self.max_selected = max(1, int(max_selected))

    def analyze(
        self,
        reviews: Any,
        product_name: str = "",
    ) -> Dict[str, Any]:
        normalized = self._normalize_items(reviews)
        coalesced = self._coalesce_fragmented_reviews(normalized)

        scored: List[Dict[str, Any]] = []
        stats = {
            "input_count": len(normalized),
            "coalesced_count": len(coalesced),
            "accepted": 0,
            "rejected_low_score": 0,
            "rejected_duplicate": 0,
            "generic_count": 0,
            "promotional_count": 0,
            "negative_signal_count": 0,
        }

        product_tokens = self._token_set(product_name)

        for index, item in enumerate(coalesced):
            text = self._clean_text(item.get("text", ""))
            if not text:
                continue

            experience_score = self._experience_score(text)
            specificity_score = self._specificity_score(text)
            relevance_score = self._relevance_score(text, product_tokens)
            balance_score = self._balance_score(text)
            generic_penalty = self._generic_penalty(text)
            promotional_penalty = self._promotional_penalty(text)

            if generic_penalty > 0:
                stats["generic_count"] += 1
            if promotional_penalty > 0:
                stats["promotional_count"] += 1
            if re.search("|".join(self.NEGATIVE_SIGNAL_PATTERNS), text):
                stats["negative_signal_count"] += 1

            quality_score = round(
                experience_score * 0.30
                + specificity_score * 0.30
                + relevance_score * 0.20
                + balance_score * 0.20
                - generic_penalty
                - promotional_penalty,
                1,
            )
            quality_score = max(0.0, min(100.0, quality_score))

            enriched = dict(item)
            enriched.update(
                {
                    "text": text,
                    "content": text,
                    "clean_text": text,
                    "quality_score": quality_score,
                    "experience_score": experience_score,
                    "specificity_score": specificity_score,
                    "relevance_score": relevance_score,
                    "balance_score": balance_score,
                    "generic_penalty": generic_penalty,
                    "promotional_penalty": promotional_penalty,
                    "quality_status": (
                        "accepted"
                        if quality_score >= self.accept_threshold
                        else "rejected_low_score"
                    ),
                    "quality_rank": 0,
                    "quality_analyzer_version": self.VERSION,
                    "quality_index": index,
                }
            )

            if quality_score < self.accept_threshold:
                stats["rejected_low_score"] += 1
                continue

            scored.append(enriched)

        scored.sort(
            key=lambda item: (
                item.get("quality_score", 0),
                item.get("specificity_score", 0),
                item.get("experience_score", 0),
                len(item.get("text", "")),
            ),
            reverse=True,
        )

        selected: List[Dict[str, Any]] = []
        for item in scored:
            if self._is_duplicate(item, selected):
                stats["rejected_duplicate"] += 1
                continue

            selected.append(item)
            if len(selected) >= self.max_selected:
                break

        for rank, item in enumerate(selected, start=1):
            item["quality_rank"] = rank

        stats["accepted"] = len(selected)

        average_score = round(
            sum(item.get("quality_score", 0) for item in selected)
            / max(len(selected), 1),
            1,
        )

        print(
            "[Sprint116-1 Review Quality] Version:",
            self.VERSION,
            flush=True,
        )
        print(
            "[Sprint116-1 Review Quality] Input:",
            len(normalized),
            "Coalesced:",
            len(coalesced),
            "Accepted:",
            len(selected),
            flush=True,
        )
        print(
            "[Sprint116-1 Review Quality] Stats:",
            stats,
            flush=True,
        )
        print(
            "[Sprint116-1 Review Quality] Average Score:",
            average_score,
            flush=True,
        )

        return {
            "ok": bool(selected),
            "version": self.VERSION,
            "status": "analyzed" if selected else "empty",
            "input_count": len(normalized),
            "coalesced_count": len(coalesced),
            "selected_count": len(selected),
            "average_score": average_score,
            "reviews": selected,
            "selected_reviews": selected,
            "top_reviews": selected[:5],
            "stats": stats,
            "warnings": (
                []
                if selected
                else ["품질 기준을 통과한 리뷰가 없습니다."]
            ),
        }

    def _normalize_items(self, reviews: Any) -> List[Dict[str, Any]]:
        if reviews is None:
            return []

        if isinstance(reviews, dict):
            for key in ("reviews", "items", "data", "results", "selected_reviews"):
                value = reviews.get(key)
                if isinstance(value, list):
                    return self._normalize_items(value)
            reviews = [reviews]

        if isinstance(reviews, str):
            reviews = [reviews]

        if not isinstance(reviews, (list, tuple)):
            return []

        result: List[Dict[str, Any]] = []
        for index, item in enumerate(reviews):
            if isinstance(item, str):
                text = item
                payload: Dict[str, Any] = {}
            elif isinstance(item, dict):
                payload = dict(item)
                text = ""
                for key in (
                    "clean_text",
                    "content",
                    "review_text",
                    "review",
                    "text",
                    "body",
                    "comment",
                ):
                    value = item.get(key)
                    if isinstance(value, str) and value.strip():
                        text = value
                        break
            else:
                continue

            text = self._clean_text(text)
            if not text:
                continue

            payload["text"] = text
            payload["content"] = text
            payload.setdefault("original_index", index)
            result.append(payload)

        return result

    def _coalesce_fragmented_reviews(
        self,
        items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if len(items) <= 1:
            return items

        ordered = sorted(
            items,
            key=lambda item: int(item.get("original_index", 0) or 0),
        )

        has_rating_lines = any(
            any(prefix in item.get("text", "") for prefix in self.RATING_PREFIXES)
            for item in ordered
        )

        if not has_rating_lines:
            return ordered

        grouped: List[Dict[str, Any]] = []
        buffer: List[str] = []
        sources: List[str] = []
        start_index = 0

        for item in ordered:
            text = self._clean_text(item.get("text", ""))
            if not text:
                continue

            if not buffer:
                start_index = int(item.get("original_index", 0) or 0)

            buffer.append(text)
            source = str(item.get("source") or "")
            if source:
                sources.append(source)

            boundary = (
                "마감 품질:" in text
                or len(" ".join(buffer)) >= 1600
            )

            if boundary:
                merged_text = " ".join(buffer)
                grouped.append(
                    {
                        "text": merged_text,
                        "content": merged_text,
                        "clean_text": merged_text,
                        "source": sources[0] if sources else "manual_review_text",
                        "original_index": start_index,
                        "fragment_count": len(buffer),
                        "coalesced": True,
                    }
                )
                buffer = []
                sources = []

        if buffer:
            merged_text = " ".join(buffer)
            grouped.append(
                {
                    "text": merged_text,
                    "content": merged_text,
                    "clean_text": merged_text,
                    "source": sources[0] if sources else "manual_review_text",
                    "original_index": start_index,
                    "fragment_count": len(buffer),
                    "coalesced": True,
                }
            )

        return grouped or ordered

    def _experience_score(self, text: str) -> float:
        score = 28.0
        for pattern in self.EXPERIENCE_PATTERNS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                score += 12.0

        if len(text) >= 180:
            score += 12.0
        elif len(text) >= 80:
            score += 7.0

        return round(max(0.0, min(100.0, score)), 1)

    def _specificity_score(self, text: str) -> float:
        score = 24.0
        for pattern in self.SPECIFIC_PATTERNS:
            matches = re.findall(pattern, text, flags=re.IGNORECASE)
            score += min(len(matches) * 8.0, 24.0)

        unique_numbers = len(set(re.findall(r"\d+(?:\.\d+)?", text)))
        score += min(unique_numbers * 5.0, 20.0)

        if len(text) >= 160:
            score += 12.0

        return round(max(0.0, min(100.0, score)), 1)

    def _relevance_score(
        self,
        text: str,
        product_tokens: set[str],
    ) -> float:
        if not product_tokens:
            return 72.0

        text_tokens = self._token_set(text)
        overlap = text_tokens & product_tokens
        score = 38.0 + min(len(overlap) * 11.0, 44.0)

        if any(token in text.lower() for token in product_tokens):
            score += 10.0

        return round(max(0.0, min(100.0, score)), 1)

    def _balance_score(self, text: str) -> float:
        score = 45.0

        if re.search(r"(다만|하지만|아쉬운|단점|거슬|보통)", text):
            score += 25.0

        if re.search(r"(좋|만족|편리|추천|시원|가볍)", text):
            score += 12.0

        if re.search(r"(상황|실내|실외|야외|대중교통|도서관|사무실)", text):
            score += 10.0

        return round(max(0.0, min(100.0, score)), 1)

    def _generic_penalty(self, text: str) -> float:
        stripped = re.sub(r"\s+", " ", text).strip()
        if len(stripped) <= 25 and any(
            phrase in stripped for phrase in self.GENERIC_PHRASES
        ):
            return 28.0

        generic_hits = sum(
            1 for phrase in self.GENERIC_PHRASES if phrase in stripped
        )
        return min(generic_hits * 2.0, 10.0)

    def _promotional_penalty(self, text: str) -> float:
        hits = sum(
            1
            for pattern in self.PROMOTIONAL_PATTERNS
            if re.search(pattern, text)
        )
        return min(hits * 4.0, 20.0)

    def _is_duplicate(
        self,
        candidate: Dict[str, Any],
        selected: Iterable[Dict[str, Any]],
    ) -> bool:
        candidate_key = self._duplicate_key(candidate.get("text", ""))
        if not candidate_key:
            return True

        for existing in selected:
            existing_key = self._duplicate_key(existing.get("text", ""))
            if candidate_key == existing_key:
                return True

            if min(len(candidate_key), len(existing_key)) < 40:
                continue

            ratio = SequenceMatcher(
                None,
                candidate_key,
                existing_key,
            ).ratio()
            if ratio >= self.duplicate_threshold:
                return True

        return False

    def _duplicate_key(self, text: str) -> str:
        return re.sub(r"[^0-9a-z가-힣]", "", text.lower())

    def _token_set(self, text: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[가-힣A-Za-z0-9]{2,}", str(text).lower())
            if token not in {
                "제품",
                "상품",
                "사용",
                "구매",
                "후기",
                "정말",
                "아주",
                "너무",
                "좋아요",
                "만족",
            }
        }

    def _clean_text(self, value: Any) -> str:
        text = str(value or "")
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"https?://\S+", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()


def analyze_review_quality(
    reviews: Any,
    product_name: str = "",
) -> Dict[str, Any]:
    return ReviewQualityAnalyzer().analyze(
        reviews=reviews,
        product_name=product_name,
    )