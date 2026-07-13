from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List, Tuple


class ReviewInsightEngine:
    """
    Sprint65-3 Review Insight Engine

    역할:
    - 리뷰 문장에서 고객 불편 추출
    - 제품 장점 추출
    - 구매 이유 추출
    - 예상 고객 유형 추출
    - 리뷰 문장을 쇼핑 콘텐츠용 구조 데이터로 변환

    외부 AI API 없이 실행되는 규칙 기반 엔진입니다.
    """

    VERSION = "review-insight-engine-65-3"

    PAIN_PATTERNS = {
        "슬리퍼가 바닥에 흩어져 있다": [
            "슬리퍼가 바닥",
            "바닥에 슬리퍼",
            "슬리퍼가 흩어",
            "슬리퍼가 굴러",
        ],
        "욕실이 지저분해 보인다": [
            "보기 싫",
            "지저분",
            "깔끔하지 않",
            "정리가 안",
        ],
        "슬리퍼 보관이 불편하다": [
            "보관이 불편",
            "둘 곳이 없",
            "놓을 곳이 없",
            "보관할 곳",
        ],
        "욕실 공간이 좁다": [
            "공간이 좁",
            "좁은 욕실",
            "자리 차지",
            "공간 부족",
        ],
        "벽에 구멍을 뚫기 부담스럽다": [
            "구멍 뚫",
            "못을 박",
            "타공",
            "벽 손상",
        ],
        "접착력이 약할까 걱정된다": [
            "접착력이 약",
            "떨어질까",
            "떨어질까 봐",
            "고정이 안",
        ],
        "설치가 어렵고 번거롭다": [
            "설치가 어렵",
            "설치가 힘들",
            "설치가 번거",
            "조립이 어렵",
        ],
        "물기가 잘 마르지 않는다": [
            "물기가 안 마",
            "건조가 안",
            "축축",
            "곰팡이",
        ],
    }

    BENEFIT_PATTERNS = {
        "슬리퍼를 깔끔하게 정리할 수 있다": [
            "깔끔하게 정리",
            "정리가 깔끔",
            "정리돼",
            "정리되",
        ],
        "벽에 걸어 공간을 효율적으로 활용할 수 있다": [
            "공간 활용",
            "자리 차지하지",
            "벽에 걸",
            "공간이 넓",
        ],
        "무타공으로 설치할 수 있다": [
            "무타공",
            "구멍을 뚫지",
            "못 없이",
            "벽 손상 없이",
        ],
        "설치가 간편하다": [
            "설치가 간편",
            "설치가 쉽",
            "쉽게 설치",
            "붙이기만",
        ],
        "접착력과 고정력이 좋다": [
            "접착력이 좋",
            "잘 떨어지지",
            "튼튼하게 고정",
            "고정력이 좋",
        ],
        "욕실이 깔끔해 보인다": [
            "욕실이 깔끔",
            "보기 좋",
            "인테리어",
            "디자인이 예쁘",
            "예뻐",
            "이뻐",
        ],
        "슬리퍼 건조와 위생 관리에 도움이 된다": [
            "건조",
            "물 빠짐",
            "물기가 마",
            "위생",
            "곰팡이 방지",
        ],
        "다양한 공간에서 사용할 수 있다": [
            "욕실뿐 아니라",
            "현관",
            "베란다",
            "다용도",
            "여러 곳",
        ],
    }

    BUY_REASON_PATTERNS = {
        "욕실 슬리퍼를 정리하기 위해": [
            "슬리퍼 정리",
            "욕실 정리",
            "정리하려고",
            "정리 때문에",
        ],
        "욕실 공간을 효율적으로 활용하기 위해": [
            "공간 활용",
            "공간이 좁",
            "자리 차지",
            "좁은 욕실",
        ],
        "벽을 손상하지 않고 설치하기 위해": [
            "무타공",
            "구멍을 뚫지",
            "벽 손상",
            "못 없이",
        ],
        "욕실을 깔끔하게 꾸미기 위해": [
            "깔끔한 욕실",
            "인테리어",
            "보기 싫",
            "예뻐서",
            "디자인",
        ],
        "슬리퍼를 위생적으로 보관하기 위해": [
            "건조",
            "물기",
            "곰팡이",
            "위생",
            "축축",
        ],
        "설치가 간편한 제품을 원해서": [
            "설치가 간편",
            "설치가 쉽",
            "붙이기만",
            "간단하게 설치",
        ],
        "접착력과 고정력이 좋은 제품을 원해서": [
            "접착력이 좋",
            "튼튼",
            "잘 고정",
            "떨어지지",
        ],
    }

    PERSONA_PATTERNS = {
        "아이 있는 가정": [
            "아이",
            "아기",
            "유아",
            "어린이",
            "자녀",
        ],
        "신혼부부": [
            "신혼",
            "신혼집",
            "새집",
            "집들이",
        ],
        "원룸 거주자": [
            "원룸",
            "작은 집",
            "좁은 집",
            "자취",
        ],
        "욕실 정리를 중요하게 생각하는 사람": [
            "정리",
            "깔끔",
            "인테리어",
            "정돈",
        ],
        "벽 손상을 원하지 않는 사람": [
            "무타공",
            "구멍",
            "못 없이",
            "벽 손상",
        ],
        "간편한 설치를 원하는 사람": [
            "설치가 쉽",
            "설치가 간편",
            "붙이기만",
            "간단",
        ],
        "욕실 위생을 중요하게 생각하는 사람": [
            "위생",
            "건조",
            "곰팡이",
            "물기",
        ],
        "공간 활용이 필요한 사람": [
            "공간 활용",
            "좁은 욕실",
            "공간 부족",
            "자리 차지",
        ],
    }

    NEGATION_PATTERNS = [
        r"떨어지지\s*않",
        r"안\s*떨어",
        r"흔들리지\s*않",
        r"안\s*흔들",
        r"불편하지\s*않",
        r"어렵지\s*않",
        r"힘들지\s*않",
        r"번거롭지\s*않",
        r"냄새가\s*없",
        r"소음이\s*없",
        r"구멍을\s*뚫지\s*않",
    ]

    STOP_WORDS = {
        "정말",
        "진짜",
        "너무",
        "아주",
        "조금",
        "약간",
        "그냥",
        "제품",
        "상품",
        "사용",
        "구매",
        "주문",
        "배송",
        "리뷰",
        "쿠팡",
        "같아요",
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

        pain_points = self._extract_pattern_insights(
            reviews=normalized_reviews,
            pattern_map=self.PAIN_PATTERNS,
            insight_type="pain",
        )

        benefits = self._extract_pattern_insights(
            reviews=normalized_reviews,
            pattern_map=self.BENEFIT_PATTERNS,
            insight_type="benefit",
        )

        buy_reasons = self._extract_pattern_insights(
            reviews=normalized_reviews,
            pattern_map=self.BUY_REASON_PATTERNS,
            insight_type="buy_reason",
        )

        personas = self._extract_pattern_insights(
            reviews=normalized_reviews,
            pattern_map=self.PERSONA_PATTERNS,
            insight_type="persona",
        )

        common_keywords = self._extract_common_keywords(
            normalized_reviews
        )

        pain_points = self._apply_pain_fallbacks(
            pain_points,
            benefits,
            normalized_reviews,
        )

        benefits = self._apply_benefit_fallbacks(
            benefits,
            normalized_reviews,
        )

        buy_reasons = self._apply_buy_reason_fallbacks(
            buy_reasons,
            pain_points,
            benefits,
        )

        personas = self._apply_persona_fallbacks(
            personas,
            pain_points,
            benefits,
        )

        best_pain = self._first_label(
            pain_points,
            "욕실 슬리퍼가 바닥에 흩어져 정리가 불편하다",
        )

        best_benefit = self._first_label(
            benefits,
            "슬리퍼를 벽에 걸어 깔끔하게 정리할 수 있다",
        )

        best_buy_reason = self._first_label(
            buy_reasons,
            "욕실 슬리퍼를 정리하기 위해",
        )

        best_persona = self._first_label(
            personas,
            "욕실 정리를 중요하게 생각하는 사람",
        )

        return {
            "ok": True,
            "version": self.VERSION,
            "product_name": product_name,
            "review_count": len(normalized_reviews),
            "pain_points": pain_points[:5],
            "benefits": benefits[:5],
            "buy_reasons": buy_reasons[:5],
            "personas": personas[:5],
            "common_keywords": common_keywords[:10],
            "best_pain_point": best_pain,
            "best_benefit": best_benefit,
            "best_buy_reason": best_buy_reason,
            "best_persona": best_persona,
            "content_angle": self._select_content_angle(
                best_pain=best_pain,
                best_benefit=best_benefit,
                best_persona=best_persona,
            ),
            "warnings": [],
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

        result: List[str] = []

        for item in reviews:
            if isinstance(item, str):
                text = self._clean_text(item)

            elif isinstance(item, dict):
                text = self._review_dict_to_text(item)

            else:
                text = ""

            if text and len(text) >= 5:
                result.append(text)

        return result

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

    def _extract_pattern_insights(
        self,
        reviews: List[str],
        pattern_map: Dict[str, List[str]],
        insight_type: str,
    ) -> List[Dict[str, Any]]:
        scored: Dict[str, Dict[str, Any]] = {}

        for review_index, review in enumerate(reviews):
            lowered = review.lower()

            for label, patterns in pattern_map.items():
                matched_patterns: List[str] = []
                score = 0

                for pattern in patterns:
                    if pattern.lower() not in lowered:
                        continue

                    if (
                        insight_type == "pain"
                        and self._is_positive_negation_context(
                            lowered,
                            pattern.lower(),
                        )
                    ):
                        continue

                    matched_patterns.append(pattern)
                    score += self._pattern_weight(pattern)

                if score <= 0:
                    continue

                if label not in scored:
                    scored[label] = {
                        "label": label,
                        "score": 0.0,
                        "count": 0,
                        "matched_patterns": [],
                        "evidence": [],
                    }

                scored[label]["score"] += score
                scored[label]["count"] += 1

                scored[label]["matched_patterns"].extend(
                    matched_patterns
                )

                if len(scored[label]["evidence"]) < 3:
                    scored[label]["evidence"].append(
                        {
                            "review_index": review_index,
                            "text": review[:180],
                        }
                    )

        result = list(scored.values())

        for item in result:
            unique_patterns = list(
                dict.fromkeys(
                    item.get("matched_patterns", [])
                )
            )

            item["matched_patterns"] = unique_patterns

            item["score"] = round(
                float(item.get("score", 0))
                + float(item.get("count", 0)) * 1.5
                + len(unique_patterns) * 0.5,
                1,
            )

        result.sort(
            key=lambda item: (
                item.get("score", 0),
                item.get("count", 0),
                len(item.get("matched_patterns", [])),
            ),
            reverse=True,
        )

        return result

    def _pattern_weight(
        self,
        pattern: str,
    ) -> float:
        length = len(pattern.replace(" ", ""))

        if length >= 8:
            return 4.0

        if length >= 5:
            return 3.0

        return 2.0

    def _is_positive_negation_context(
        self,
        text: str,
        matched_pattern: str,
    ) -> bool:
        position = text.find(matched_pattern)

        if position < 0:
            return False

        start = max(0, position - 15)
        end = min(
            len(text),
            position + len(matched_pattern) + 20,
        )

        context = text[start:end]

        return any(
            re.search(pattern, context)
            for pattern in self.NEGATION_PATTERNS
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
                normalized = word.strip().lower()

                if normalized in self.STOP_WORDS:
                    continue

                if len(normalized) < 2:
                    continue

                counter[normalized] += 1

        return [
            {
                "keyword": keyword,
                "count": count,
            }
            for keyword, count in counter.most_common(15)
        ]

    def _apply_pain_fallbacks(
        self,
        pain_points: List[Dict[str, Any]],
        benefits: List[Dict[str, Any]],
        reviews: List[str],
    ) -> List[Dict[str, Any]]:
        if pain_points:
            return pain_points

        inferred: List[Tuple[str, float]] = []

        benefit_labels = {
            item.get("label", "")
            for item in benefits
        }

        if "슬리퍼를 깔끔하게 정리할 수 있다" in benefit_labels:
            inferred.append(
                (
                    "슬리퍼가 바닥에 흩어져 정리가 불편하다",
                    4.5,
                )
            )

        if "무타공으로 설치할 수 있다" in benefit_labels:
            inferred.append(
                (
                    "벽에 구멍을 뚫기 부담스럽다",
                    4.0,
                )
            )

        if "접착력과 고정력이 좋다" in benefit_labels:
            inferred.append(
                (
                    "접착력이 약해 떨어질까 걱정된다",
                    3.5,
                )
            )

        if "슬리퍼 건조와 위생 관리에 도움이 된다" in benefit_labels:
            inferred.append(
                (
                    "바닥에 놓인 슬리퍼의 물기와 위생이 걱정된다",
                    3.5,
                )
            )

        if not inferred:
            inferred.append(
                (
                    "욕실 슬리퍼가 바닥에 흩어져 정리가 불편하다",
                    3.0,
                )
            )

        return [
            {
                "label": label,
                "score": score,
                "count": 0,
                "matched_patterns": [],
                "evidence": [],
                "inferred": True,
            }
            for label, score in inferred
        ]

    def _apply_benefit_fallbacks(
        self,
        benefits: List[Dict[str, Any]],
        reviews: List[str],
    ) -> List[Dict[str, Any]]:
        if benefits:
            return benefits

        return [
            {
                "label": "슬리퍼를 벽에 걸어 깔끔하게 정리할 수 있다",
                "score": 3.0,
                "count": 0,
                "matched_patterns": [],
                "evidence": [],
                "inferred": True,
            },
            {
                "label": "설치가 간편하다",
                "score": 2.5,
                "count": 0,
                "matched_patterns": [],
                "evidence": [],
                "inferred": True,
            },
        ]

    def _apply_buy_reason_fallbacks(
        self,
        buy_reasons: List[Dict[str, Any]],
        pain_points: List[Dict[str, Any]],
        benefits: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if buy_reasons:
            return buy_reasons

        result: List[Dict[str, Any]] = []

        pain_labels = {
            item.get("label", "")
            for item in pain_points
        }

        benefit_labels = {
            item.get("label", "")
            for item in benefits
        }

        if any(
            "정리" in label
            for label in pain_labels | benefit_labels
        ):
            result.append(
                self._inferred_item(
                    "욕실 슬리퍼를 정리하기 위해",
                    4.0,
                )
            )

        if any(
            "공간" in label
            for label in pain_labels | benefit_labels
        ):
            result.append(
                self._inferred_item(
                    "욕실 공간을 효율적으로 활용하기 위해",
                    3.5,
                )
            )

        if any(
            "무타공" in label or "구멍" in label
            for label in pain_labels | benefit_labels
        ):
            result.append(
                self._inferred_item(
                    "벽을 손상하지 않고 설치하기 위해",
                    3.5,
                )
            )

        if not result:
            result.append(
                self._inferred_item(
                    "욕실을 깔끔하게 정리하기 위해",
                    3.0,
                )
            )

        return result

    def _apply_persona_fallbacks(
        self,
        personas: List[Dict[str, Any]],
        pain_points: List[Dict[str, Any]],
        benefits: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if personas:
            return personas

        result: List[Dict[str, Any]] = [
            self._inferred_item(
                "욕실 정리를 중요하게 생각하는 사람",
                4.0,
            )
        ]

        combined_labels = [
            item.get("label", "")
            for item in pain_points + benefits
        ]

        if any(
            "공간" in label or "좁" in label
            for label in combined_labels
        ):
            result.append(
                self._inferred_item(
                    "공간 활용이 필요한 사람",
                    3.5,
                )
            )

        if any(
            "무타공" in label or "구멍" in label
            for label in combined_labels
        ):
            result.append(
                self._inferred_item(
                    "벽 손상을 원하지 않는 사람",
                    3.5,
                )
            )

        if any(
            "건조" in label
            or "위생" in label
            or "물기" in label
            for label in combined_labels
        ):
            result.append(
                self._inferred_item(
                    "욕실 위생을 중요하게 생각하는 사람",
                    3.0,
                )
            )

        return result

    def _inferred_item(
        self,
        label: str,
        score: float,
    ) -> Dict[str, Any]:
        return {
            "label": label,
            "score": score,
            "count": 0,
            "matched_patterns": [],
            "evidence": [],
            "inferred": True,
        }

    def _first_label(
        self,
        items: List[Dict[str, Any]],
        fallback: str,
    ) -> str:
        if not items:
            return fallback

        label = str(
            items[0].get("label", "")
        ).strip()

        return label or fallback

    def _select_content_angle(
        self,
        best_pain: str,
        best_benefit: str,
        best_persona: str,
    ) -> Dict[str, Any]:
        pain_text = best_pain.lower()
        benefit_text = best_benefit.lower()
        persona_text = best_persona.lower()

        if (
            "바닥" in pain_text
            or "지저분" in pain_text
            or "정리" in pain_text
        ):
            return {
                "type": "problem_solution",
                "name": "문제 해결형",
                "reason": "고객 불편과 해결 전후가 명확합니다.",
            }

        if (
            "접착" in pain_text
            or "고정" in benefit_text
            or "떨어" in pain_text
        ):
            return {
                "type": "demonstration",
                "name": "실험·시연형",
                "reason": "접착력과 고정력을 영상으로 보여주기 좋습니다.",
            }

        if (
            "인테리어" in benefit_text
            or "예쁘" in benefit_text
            or "깔끔" in benefit_text
        ):
            return {
                "type": "before_after",
                "name": "전후 비교형",
                "reason": "설치 전후의 공간 변화가 분명합니다.",
            }

        if (
            "아이" in persona_text
            or "위생" in persona_text
        ):
            return {
                "type": "empathy",
                "name": "공감형",
                "reason": "특정 고객의 생활 불편에 공감시키기 좋습니다.",
            }

        return {
            "type": "problem_solution",
            "name": "문제 해결형",
            "reason": "제품의 구매 이유를 가장 직관적으로 전달할 수 있습니다.",
        }

    def _empty_result(
        self,
        product_name: str,
    ) -> Dict[str, Any]:
        return {
            "ok": False,
            "version": self.VERSION,
            "product_name": product_name,
            "review_count": 0,
            "pain_points": [
                self._inferred_item(
                    "욕실 슬리퍼가 바닥에 흩어져 정리가 불편하다",
                    3.0,
                )
            ],
            "benefits": [
                self._inferred_item(
                    "슬리퍼를 벽에 걸어 깔끔하게 정리할 수 있다",
                    3.0,
                )
            ],
            "buy_reasons": [
                self._inferred_item(
                    "욕실 슬리퍼를 정리하기 위해",
                    3.0,
                )
            ],
            "personas": [
                self._inferred_item(
                    "욕실 정리를 중요하게 생각하는 사람",
                    3.0,
                )
            ],
            "common_keywords": [],
            "best_pain_point": (
                "욕실 슬리퍼가 바닥에 흩어져 "
                "정리가 불편하다"
            ),
            "best_benefit": (
                "슬리퍼를 벽에 걸어 "
                "깔끔하게 정리할 수 있다"
            ),
            "best_buy_reason": (
                "욕실 슬리퍼를 정리하기 위해"
            ),
            "best_persona": (
                "욕실 정리를 중요하게 생각하는 사람"
            ),
            "content_angle": {
                "type": "problem_solution",
                "name": "문제 해결형",
                "reason": "리뷰가 없어 기본 문제 해결 구조를 사용합니다.",
            },
            "warnings": [
                "분석할 리뷰가 없어 기본 인사이트를 생성했습니다."
            ],
        }