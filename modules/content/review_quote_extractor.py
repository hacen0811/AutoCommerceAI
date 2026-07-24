from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, Iterable, List


class ReviewQuoteSelector:
    """
    Sprint73-2 Representative Review Quote Selector

    역할:
    - 정제된 리뷰에서 대표 불편, 대표 장점, 대표 감탄, 대표 추천 문장을 추출
    - 외부 AI API 없이 키워드 점수 기반으로 동작
    - ReviewInsightEngine 입력 전에 대표 인용구를 보조 정보로 제공
    """

    VERSION = "review-quote-selector-73-2"

    PAIN_WORDS = (
        "불편", "아쉽", "힘들", "어렵", "귀찮", "번거", "문제",
        "떨어", "흔들", "약하", "작다", "좁다", "비싸", "냄새",
        "미끄", "정리", "바닥", "공간", "손상", "구멍",
    )

    BENEFIT_WORDS = (
        "좋", "편하", "깔끔", "만족", "튼튼", "강하", "쉽",
        "정리", "넓", "공간", "예쁘", "실용", "안전", "빠르",
        "잘 붙", "안 떨어", "무타공", "설치",
    )

    EMOTION_WORDS = (
        "정말", "너무", "진짜", "대박", "최고", "완전",
        "생각보다", "만족", "감동", "놀랐", "추천",
    )

    RECOMMEND_WORDS = (
        "추천", "재구매", "사세요", "강추", "구매", "쓸만",
        "가성비", "필수", "잘 샀", "후회 없",
    )

    META_WORDS = {
        "배송", "포장", "옵션", "판매자", "도움이", "신고하기",
    }

    def select(
        self,
        reviews: Any,
        product_name: str = "",
        top_n: int = 5,
    ) -> Dict[str, Any]:
        items = self._normalize_reviews(reviews)

        if not items:
            return {
                "ok": False,
                "version": self.VERSION,
                "status": "empty",
                "review_count": 0,
                "best_pain": "",
                "best_benefit": "",
                "best_emotion": "",
                "best_recommendation": "",
                "best_quote": "",
                "top_quotes": [],
                "keyword_summary": [],
            }

        scored = []

        for index, item in enumerate(items):
            text = item["text"]
            scores = {
                "pain": self._category_score(
                    text,
                    self.PAIN_WORDS,
                ),
                "benefit": self._category_score(
                    text,
                    self.BENEFIT_WORDS,
                ),
                "emotion": self._category_score(
                    text,
                    self.EMOTION_WORDS,
                ),
                "recommendation": self._category_score(
                    text,
                    self.RECOMMEND_WORDS,
                ),
            }

            base_score = self._base_score(text)
            total_score = (
                base_score
                + max(scores.values()) * 4
                + sum(scores.values())
            )

            scored.append(
                {
                    "index": index,
                    "text": text,
                    "source": item.get("source", "unknown"),
                    "scores": scores,
                    "base_score": round(base_score, 2),
                    "total_score": round(total_score, 2),
                }
            )

        best_pain = self._best_for(scored, "pain")
        best_benefit = self._best_for(scored, "benefit")
        best_emotion = self._best_for(scored, "emotion")
        best_recommendation = self._best_for(
            scored,
            "recommendation",
        )

        ranked = sorted(
            scored,
            key=lambda item: item["total_score"],
            reverse=True,
        )

        best_quote = (
            best_benefit
            or best_emotion
            or best_recommendation
            or (ranked[0]["text"] if ranked else "")
        )

        top_quotes = []
        seen = set()

        for item in ranked:
            text = item["text"]
            key = re.sub(r"\s+", "", text.lower())

            if key in seen:
                continue

            seen.add(key)
            top_quotes.append(item)

            if len(top_quotes) >= max(1, int(top_n)):
                break

        return {
            "ok": bool(best_quote),
            "version": self.VERSION,
            "status": "selected" if best_quote else "empty",
            "product_name": product_name,
            "review_count": len(items),
            "best_pain": best_pain,
            "best_benefit": best_benefit,
            "best_emotion": best_emotion,
            "best_recommendation": best_recommendation,
            "best_quote": best_quote,
            "top_quotes": top_quotes,
            "keyword_summary": self._keyword_summary(items),
        }

    def _normalize_reviews(self, reviews: Any) -> List[Dict[str, str]]:
        if reviews is None:
            return []

        if isinstance(reviews, dict):
            for key in (
                "reviews",
                "items",
                "results",
                "data",
                "texts",
            ):
                value = reviews.get(key)
                if isinstance(value, list):
                    reviews = value
                    break
            else:
                reviews = [reviews]

        if isinstance(reviews, str):
            reviews = [reviews]

        if not isinstance(reviews, (list, tuple, set)):
            return []

        result = []

        for item in reviews:
            if isinstance(item, str):
                text = item
                source = "unknown"
            elif isinstance(item, dict):
                text = (
                    item.get("clean_text")
                    or item.get("content")
                    or item.get("review_text")
                    or item.get("text")
                    or item.get("body")
                    or item.get("comment")
                    or ""
                )
                source = item.get("source") or "unknown"
            else:
                continue

            text = self._clean_text(text)

            if len(text) < 5:
                continue

            result.append(
                {
                    "text": text,
                    "source": source,
                }
            )

        return result

    def _clean_text(self, value: Any) -> str:
        text = str(value or "")
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"https?://\S+", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _base_score(self, text: str) -> float:
        length = len(text)
        score = 0.0

        if 12 <= length <= 90:
            score += 8.0
        elif 8 <= length <= 140:
            score += 5.0
        else:
            score += 1.0

        if any(mark in text for mark in (".", "!", "?", "요", "다")):
            score += 2.0

        if any(word in text for word in self.META_WORDS):
            score -= 3.0

        if re.search(r"(.)\1{4,}", text):
            score -= 2.0

        return score

    def _category_score(
        self,
        text: str,
        keywords: Iterable[str],
    ) -> int:
        lowered = text.lower()
        return sum(
            1
            for keyword in keywords
            if keyword.lower() in lowered
        )

    def _best_for(
        self,
        scored: List[Dict[str, Any]],
        category: str,
    ) -> str:
        candidates = [
            item
            for item in scored
            if item["scores"].get(category, 0) > 0
        ]

        if not candidates:
            return ""

        best = max(
            candidates,
            key=lambda item: (
                item["scores"].get(category, 0),
                item["total_score"],
                -abs(len(item["text"]) - 45),
            ),
        )

        return best["text"]

    def _keyword_summary(
        self,
        items: List[Dict[str, str]],
    ) -> List[Dict[str, Any]]:
        counter = Counter()

        for item in items:
            words = re.findall(
                r"[가-힣A-Za-z]{2,}",
                item["text"],
            )

            for word in words:
                if word in self.META_WORDS:
                    continue
                counter[word] += 1

        return [
            {
                "keyword": word,
                "count": count,
            }
            for word, count in counter.most_common(10)
        ]


def select_review_quotes(
    reviews: Any,
    product_name: str = "",
    top_n: int = 5,
) -> Dict[str, Any]:
    return ReviewQuoteSelector().select(
        reviews=reviews,
        product_name=product_name,
        top_n=top_n,
    )
