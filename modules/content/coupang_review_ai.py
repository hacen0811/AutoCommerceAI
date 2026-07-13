from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List


class CoupangReviewAI:
    """
    Sprint65 Coupang Review AI

    역할:
    - 쿠팡 리뷰 데이터 정규화
    - 고객 불편 요소 분석
    - 제품 장점 분석
    - 구매 이유 분석
    - 쇼핑쇼츠 후킹 생성
    - 쇼핑쇼츠 대본 생성
    - 부정 표현과 긍정형 부정 문장 구분
    """

    VERSION = "coupang-review-ai-65-2"

    NEGATIVE_KEYWORDS = {
        "불편": 4,
        "아쉽": 3,
        "별로": 4,
        "약하": 3,
        "작아": 2,
        "작은": 2,
        "좁아": 2,
        "냄새": 3,
        "소음": 3,
        "무거": 2,
        "불량": 5,
        "고장": 5,
        "떨어": 3,
        "흔들": 3,
        "미끄": 3,
        "어려": 3,
        "힘들": 3,
        "번거": 4,
        "귀찮": 4,
        "파손": 5,
        "비싸": 3,
        "접착력이 약": 4,
        "고정이 안": 4,
        "설치가 어렵": 4,
        "크기가 작": 3,
    }

    POSITIVE_KEYWORDS = {
        "좋아": 3,
        "좋네": 3,
        "만족": 4,
        "편해": 4,
        "편리": 4,
        "간편": 4,
        "튼튼": 4,
        "깔끔": 4,
        "예뻐": 3,
        "이뻐": 3,
        "가성비": 4,
        "추천": 4,
        "잘돼": 3,
        "잘 되": 3,
        "빠르": 2,
        "쉬워": 4,
        "쉽게": 3,
        "강력": 3,
        "실용": 4,
        "유용": 4,
        "정리": 3,
        "공간": 3,
        "접착력도 좋아": 5,
        "접착력이 좋아": 5,
        "잘 고정": 5,
        "튼튼하게 고정": 5,
        "떨어지지 않": 5,
        "흔들리지 않": 5,
        "미끄러지지 않": 5,
        "구멍을 뚫지 않": 4,
        "무타공": 4,
        "설치가 간편": 5,
        "설치가 쉽": 5,
    }

    PURCHASE_KEYWORDS = {
        "구매": 3,
        "주문": 3,
        "필요": 3,
        "찾다가": 4,
        "검색": 2,
        "추천": 2,
        "재구매": 5,
        "선물": 3,
        "아이": 2,
        "부모님": 2,
        "남편": 2,
        "아내": 2,
        "집": 2,
        "욕실": 3,
        "현관": 3,
        "주방": 3,
        "사무실": 2,
        "차량": 2,
        "정리": 3,
        "수납": 3,
        "공간": 3,
    }

    POSITIVE_NEGATION_PATTERNS = [
        r"떨어지지\s*않",
        r"안\s*떨어",
        r"떨어질\s*걱정이\s*없",
        r"흔들리지\s*않",
        r"안\s*흔들",
        r"미끄러지지\s*않",
        r"안\s*미끄",
        r"고장\s*나지\s*않",
        r"고장이\s*없",
        r"불편하지\s*않",
        r"어렵지\s*않",
        r"힘들지\s*않",
        r"번거롭지\s*않",
        r"귀찮지\s*않",
        r"냄새가\s*나지\s*않",
        r"냄새가\s*없",
        r"소음이\s*없",
        r"파손되지\s*않",
        r"구멍을\s*뚫지\s*않",
    ]

    NEGATIVE_NEGATION_PATTERNS = [
        r"좋지\s*않",
        r"좋지는\s*않",
        r"편하지\s*않",
        r"편리하지\s*않",
        r"간편하지\s*않",
        r"튼튼하지\s*않",
        r"깔끔하지\s*않",
        r"예쁘지\s*않",
        r"이쁘지\s*않",
        r"추천하지\s*않",
        r"만족하지\s*않",
        r"잘\s*되지\s*않",
        r"쉽지\s*않",
        r"실용적이지\s*않",
        r"유용하지\s*않",
        r"고정이\s*잘\s*되지\s*않",
        r"접착력이\s*좋지\s*않",
    ]

    STOP_WORDS = {
        "그냥",
        "정말",
        "진짜",
        "너무",
        "조금",
        "약간",
        "제품",
        "상품",
        "사용",
        "구매",
        "주문",
        "배송",
        "쿠팡",
        "리뷰",
        "같아요",
        "입니다",
        "있어요",
        "없어요",
        "했어요",
        "좋아요",
        "좋습니다",
    }

    def analyze(
        self,
        reviews: Any,
        product_name: str = "",
    ) -> Dict[str, Any]:
        normalized_reviews = self._normalize_reviews(reviews)

        if not normalized_reviews:
            return self._empty_result(product_name)

        negative_points = self._extract_ranked_sentences(
            reviews=normalized_reviews,
            keyword_scores=self.NEGATIVE_KEYWORDS,
            sentiment="negative",
        )

        positive_points = self._extract_ranked_sentences(
            reviews=normalized_reviews,
            keyword_scores=self.POSITIVE_KEYWORDS,
            sentiment="positive",
        )

        purchase_reasons = self._extract_ranked_sentences(
            reviews=normalized_reviews,
            keyword_scores=self.PURCHASE_KEYWORDS,
            sentiment="purchase",
        )

        common_keywords = self._extract_common_keywords(
            normalized_reviews
        )

        main_problem = self._pick_problem_summary(
            negative_points
        )

        main_benefit = self._pick_summary(
            positive_points,
            fallback="설치가 간편하고 공간을 깔끔하게 정리할 수 있다",
        )

        main_purchase_reason = self._pick_summary(
            purchase_reasons,
            fallback="생활 속 정리 불편을 해결하기 위해 구매했다",
        )

        hooks = self._generate_hooks(
            product_name=product_name,
            main_problem=main_problem,
            main_benefit=main_benefit,
        )

        script = self._generate_script(
            product_name=product_name,
            main_problem=main_problem,
            main_benefit=main_benefit,
            main_purchase_reason=main_purchase_reason,
        )

        warnings: List[str] = []

        if not negative_points:
            warnings.append(
                "명확한 부정 리뷰가 없어 제품 사용 전 예상 불편을 활용했습니다."
            )

        return {
            "ok": True,
            "version": self.VERSION,
            "product_name": product_name,
            "review_count": len(normalized_reviews),
            "negative_points": negative_points[:5],
            "positive_points": positive_points[:5],
            "purchase_reasons": purchase_reasons[:5],
            "common_keywords": common_keywords[:10],
            "main_problem": main_problem,
            "main_benefit": main_benefit,
            "main_purchase_reason": main_purchase_reason,
            "hooks": hooks,
            "best_hook": hooks[0] if hooks else "",
            "script": script,
            "script_text": script.get("full_text", ""),
            "warnings": warnings,
        }

    def _normalize_reviews(
        self,
        reviews: Any,
    ) -> List[str]:
        if reviews is None:
            return []

        if isinstance(reviews, str):
            text = self._clean_text(reviews)
            return [text] if text else []

        if isinstance(reviews, dict):
            for key in (
                "reviews",
                "items",
                "data",
                "results",
                "review_list",
            ):
                value = reviews.get(key)

                if value:
                    return self._normalize_reviews(value)

            text = self._review_dict_to_text(reviews)
            return [text] if text else []

        if not isinstance(reviews, list):
            return []

        normalized: List[str] = []

        for item in reviews:
            if isinstance(item, str):
                text = self._clean_text(item)

            elif isinstance(item, dict):
                text = self._review_dict_to_text(item)

            else:
                text = ""

            if text and len(text) >= 5:
                normalized.append(text)

        return normalized

    def _review_dict_to_text(
        self,
        review: Dict[str, Any],
    ) -> str:
        values: List[str] = []

        for key in (
            "content",
            "review",
            "text",
            "body",
            "comment",
            "review_content",
            "headline",
            "title",
        ):
            value = review.get(key)

            if isinstance(value, str) and value.strip():
                values.append(value.strip())

        return self._clean_text(
            " ".join(values)
        )

    def _clean_text(
        self,
        text: str,
    ) -> str:
        text = str(text or "")
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"https?://\S+", " ", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def _split_sentences(
        self,
        text: str,
    ) -> List[str]:
        sentences = re.split(
            r"(?<=[.!?。！？])\s+|\n+",
            text,
        )

        result: List[str] = []

        for sentence in sentences:
            sentence = sentence.strip(
                " \t\r\n-•"
            )

            if 5 <= len(sentence) <= 150:
                result.append(sentence)

        if not result and text:
            result.append(text[:150])

        return result

    def _extract_ranked_sentences(
        self,
        reviews: List[str],
        keyword_scores: Dict[str, int],
        sentiment: str,
    ) -> List[Dict[str, Any]]:
        ranked: List[Dict[str, Any]] = []
        seen = set()

        for review in reviews:
            for sentence in self._split_sentences(review):
                if sentiment == "negative":
                    if self._is_positive_negation(sentence):
                        continue

                if sentiment == "positive":
                    if self._is_negative_negation(sentence):
                        continue

                score = 0
                matched_keywords: List[str] = []

                lowered = sentence.lower()

                for keyword, weight in keyword_scores.items():
                    if keyword.lower() in lowered:
                        score += weight
                        matched_keywords.append(keyword)

                if sentiment == "positive":
                    if self._is_positive_negation(sentence):
                        score += 5
                        matched_keywords.append(
                            "긍정형 부정 표현"
                        )

                if sentiment == "negative":
                    if self._is_negative_negation(sentence):
                        score += 5
                        matched_keywords.append(
                            "부정형 표현"
                        )

                if score <= 0:
                    continue

                normalized_key = re.sub(
                    r"\s+",
                    "",
                    sentence,
                )[:80]

                if normalized_key in seen:
                    continue

                seen.add(normalized_key)

                ranked.append(
                    {
                        "text": sentence,
                        "score": round(float(score), 1),
                        "keywords": list(
                            dict.fromkeys(matched_keywords)
                        ),
                    }
                )

        ranked.sort(
            key=lambda item: (
                item.get("score", 0),
                len(item.get("keywords", [])),
                len(item.get("text", "")),
            ),
            reverse=True,
        )

        return ranked

    def _is_positive_negation(
        self,
        sentence: str,
    ) -> bool:
        normalized = re.sub(
            r"\s+",
            " ",
            sentence,
        ).lower()

        return any(
            re.search(pattern, normalized)
            for pattern in self.POSITIVE_NEGATION_PATTERNS
        )

    def _is_negative_negation(
        self,
        sentence: str,
    ) -> bool:
        normalized = re.sub(
            r"\s+",
            " ",
            sentence,
        ).lower()

        return any(
            re.search(pattern, normalized)
            for pattern in self.NEGATIVE_NEGATION_PATTERNS
        )

    def _extract_common_keywords(
        self,
        reviews: List[str],
    ) -> List[Dict[str, Any]]:
        counter: Counter[str] = Counter()

        for review in reviews:
            words = re.findall(
                r"[가-힣]{2,}|[A-Za-z]{3,}",
                review,
            )

            for word in words:
                word = word.strip().lower()

                if word in self.STOP_WORDS:
                    continue

                if len(word) < 2:
                    continue

                counter[word] += 1

        return [
            {
                "keyword": keyword,
                "count": count,
            }
            for keyword, count in counter.most_common(15)
        ]

    def _pick_problem_summary(
        self,
        items: List[Dict[str, Any]],
    ) -> str:
        if not items:
            return "욕실 슬리퍼가 바닥에 흩어져 정리가 불편하다"

        return self._pick_summary(
            items,
            fallback="욕실 슬리퍼가 바닥에 흩어져 정리가 불편하다",
        )

    def _pick_summary(
        self,
        items: List[Dict[str, Any]],
        fallback: str,
    ) -> str:
        if not items:
            return fallback

        text = str(
            items[0].get("text", "")
        ).strip()

        if not text:
            return fallback

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        if len(text) > 70:
            text = text[:67].rstrip() + "..."

        return text

    def _generate_hooks(
        self,
        product_name: str,
        main_problem: str,
        main_benefit: str,
    ) -> List[str]:
        name = product_name.strip() or "이 제품"

        problem_hook = self._normalize_problem_for_hook(
            main_problem
        )

        benefit_hook = self._normalize_benefit_for_hook(
            main_benefit
        )

        hooks = [
            f"{problem_hook} 불편하셨다면, 이거 한번 보세요.",
            f"바닥에 흩어진 슬리퍼, {name} 하나로 정리했습니다.",
            f"벽에 구멍 없이 슬리퍼를 깔끔하게 정리하는 방법입니다.",
            f"왜 이제 샀을까요? {benefit_hook}",
            f"실제 구매자들이 만족한 이유가 있었습니다.",
        ]

        return [
            self._limit_text(hook, 70)
            for hook in hooks
        ]

    def _normalize_problem_for_hook(
        self,
        text: str,
    ) -> str:
        text = re.sub(
            r"[.!?]+$",
            "",
            str(text or "").strip(),
        )

        replacements = {
            "불편했는데": "불편해서",
            "불편합니다": "불편해서",
            "불편해요": "불편해서",
            "불편하다": "불편해서",
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return text

    def _normalize_benefit_for_hook(
        self,
        text: str,
    ) -> str:
        text = re.sub(
            r"[.!?]+$",
            "",
            str(text or "").strip(),
        )

        return text

    def _generate_script(
        self,
        product_name: str,
        main_problem: str,
        main_benefit: str,
        main_purchase_reason: str,
    ) -> Dict[str, Any]:
        name = product_name.strip() or "이 제품"

        problem_text = re.sub(
            r"[.!?]+$",
            "",
            main_problem.strip(),
        )

        benefit_text = re.sub(
            r"[.!?]+$",
            "",
            main_benefit.strip(),
        )

        purchase_text = re.sub(
            r"[.!?]+$",
            "",
            main_purchase_reason.strip(),
        )

        hook = (
            "바닥에 흩어진 슬리퍼 때문에 "
            "욕실이 지저분해 보이셨나요?"
        )

        problem = (
            f"실제 구매자 리뷰에서도 "
            f"{problem_text}는 불편이 확인됐습니다."
        )

        solution = (
            f"{name}는 벽에 구멍을 뚫지 않고 "
            f"슬리퍼를 깔끔하게 정리할 수 있습니다."
        )

        proof = (
            f"구매자들은 {benefit_text}고 평가했고, "
            "접착력과 고정력도 만족스럽다는 반응을 보였습니다."
        )

        purchase_reason = (
            f"특히 {purchase_text}는 이유로 "
            "선택한 구매자가 많았습니다."
        )

        cta = (
            "욕실 공간을 간단하게 정리하고 싶다면 "
            "아래 링크에서 확인해 보세요."
        )

        full_text = " ".join(
            [
                hook,
                problem,
                solution,
                proof,
                purchase_reason,
                cta,
            ]
        )

        return {
            "hook": hook,
            "problem": problem,
            "solution": solution,
            "proof": proof,
            "purchase_reason": purchase_reason,
            "cta": cta,
            "full_text": full_text,
            "estimated_seconds": self._estimate_seconds(
                full_text
            ),
        }

    def _estimate_seconds(
        self,
        text: str,
    ) -> float:
        clean_length = len(
            re.sub(r"\s+", "", text)
        )

        seconds = clean_length / 5.2

        return round(
            max(10.0, min(seconds, 60.0)),
            1,
        )

    def _limit_text(
        self,
        text: str,
        max_length: int,
    ) -> str:
        text = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        if len(text) <= max_length:
            return text

        return text[: max_length - 3].rstrip() + "..."

    def _empty_result(
        self,
        product_name: str,
    ) -> Dict[str, Any]:
        name = product_name.strip() or "이 제품"

        fallback_hook = (
            f"바닥에 흩어진 슬리퍼, "
            f"{name} 하나로 정리했습니다."
        )

        fallback_script = self._generate_script(
            product_name=name,
            main_problem="욕실 슬리퍼가 바닥에 흩어져 정리가 불편하다",
            main_benefit="설치가 간편하고 공간 정리가 깔끔하다",
            main_purchase_reason="욕실 공간을 효율적으로 활용하기 위해 구매했다",
        )

        return {
            "ok": False,
            "version": self.VERSION,
            "product_name": product_name,
            "review_count": 0,
            "negative_points": [],
            "positive_points": [],
            "purchase_reasons": [],
            "common_keywords": [],
            "main_problem": (
                "욕실 슬리퍼가 바닥에 흩어져 "
                "정리가 불편하다"
            ),
            "main_benefit": (
                "설치가 간편하고 "
                "공간 정리가 깔끔하다"
            ),
            "main_purchase_reason": (
                "욕실 공간을 효율적으로 "
                "활용하기 위해 구매했다"
            ),
            "hooks": [fallback_hook],
            "best_hook": fallback_hook,
            "script": fallback_script,
            "script_text": fallback_script.get(
                "full_text",
                "",
            ),
            "warnings": [
                "분석할 쿠팡 리뷰가 없어 기본 대본을 생성했습니다."
            ],
        }