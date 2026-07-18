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

    VERSION = "review-insight-engine-76-2a"

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

    GENERAL_PAIN_PATTERNS = {
        "짐을 정리하고 분리 수납하기 어렵다": [
            "물건들이 섞",
            "분리하기",
            "수납이 부족",
            "정리가 어렵",
            "짐 정리",
        ],
        "여행 중 짐을 이동하기 불편하다": [
            "이동할 때 불편",
            "들고 다니기",
            "무거워",
            "이동이 불편",
            "끌기 불편",
        ],
        "여행 기간에 맞는 크기를 고르기 어렵다": [
            "크기 고민",
            "몇 인치",
            "24인치",
            "20인치",
            "여행 기간",
        ],
        "내부 수납공간 활용이 아쉽다": [
            "내부 공간",
            "수납공간",
            "공간이 부족",
            "수납이 아쉽",
        ],
    }

    GENERAL_BENEFIT_PATTERNS = {
        "내부 공간을 나눠 깔끔하게 분리 수납할 수 있다": [
            "지퍼로 완전히 닫",
            "물건들이 섞이지",
            "분리하기 좋",
            "메쉬 포켓",
            "내부 공간 구성",
        ],
        "가볍고 이동이 편하다": [
            "가볍고",
            "이동까지 편",
            "이동이 편",
            "끌기 편",
            "휴대가 편",
        ],
        "여행 짐을 넉넉하게 수납할 수 있다": [
            "수납이 넉넉",
            "짐이 많이",
            "공간이 알차",
            "24인치가 딱",
        ],
        "튼튼해서 오래 사용할 수 있다": [
            "튼튼",
            "오래 쓸",
            "내구성",
            "질리지 않고",
        ],
        "디자인이 깔끔하고 세련됐다": [
            "깔끔하고 세련",
            "디자인",
            "색상",
            "예쁘",
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
        social_comments: Any = None,
        product_name: str = "",
    ) -> Dict[str, Any]:
        normalized_reviews = self._normalize_reviews(
            reviews
        )

        normalized_social = self._normalize_reviews(
            social_comments
        )

        if normalized_social:
            normalized_reviews.extend(
                normalized_social
            )

        if not normalized_reviews:
            return self._empty_result(
                product_name
            )

        selector_result = self._select_smart_reviews(
            normalized_reviews,
            product_name=product_name,
        )

        selected_reviews = selector_result.get(
            "selected_reviews",
            [],
        )

        if selected_reviews:
            normalized_reviews = selected_reviews

        pain_pattern_map = {
            **self.PAIN_PATTERNS,
            **self.GENERAL_PAIN_PATTERNS,
        }

        benefit_pattern_map = {
            **self.BENEFIT_PATTERNS,
            **self.GENERAL_BENEFIT_PATTERNS,
        }

        pain_points = self._extract_pattern_insights(
            reviews=normalized_reviews,
            pattern_map=pain_pattern_map,
            insight_type="pain",
        )

        benefits = self._extract_pattern_insights(
            reviews=normalized_reviews,
            pattern_map=benefit_pattern_map,
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

        sentence_evidence = self._build_sentence_evidence(
            normalized_reviews,
            product_name=product_name,
        )

        best_evidence = sentence_evidence.get(
            "best_evidence",
            {},
        )

        pain_points = self._apply_pain_fallbacks(
            pain_points,
            benefits,
            normalized_reviews,
            product_name=product_name,
        )

        benefits = self._apply_benefit_fallbacks(
            benefits,
            normalized_reviews,
            product_name=product_name,
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

        best_benefit = self._align_benefit_with_evidence(
            best_benefit=best_benefit,
            evidence_text=best_evidence.get(
                "text",
                "",
            ),
        )

        best_buy_reason = self._first_label(
            buy_reasons,
            "욕실 슬리퍼를 정리하기 위해",
        )

        best_persona = self._first_label(
            personas,
            "욕실 정리를 중요하게 생각하는 사람",
        )

        print(
            "[Sprint76-2A Insight] Version:",
            self.VERSION,
            flush=True,
        )
        print(
            "[Sprint76-2A Insight] Raw Reviews:",
            selector_result.get("raw_review_count", 0),
            flush=True,
        )
        print(
            "[Sprint76-2A Insight] Selected Reviews:",
            selector_result.get("selected_review_count", 0),
            flush=True,
        )
        print(
            "[Sprint76-2A Insight] Filter Stats:",
            selector_result.get("filter_stats", {}),
            flush=True,
        )
        print(
            "[Sprint76-2A Insight] Input Reviews:",
            len(normalized_reviews),
            flush=True,
        )
        print(
            "[Sprint76-2A Insight] Sentence Count:",
            sentence_evidence.get("sentence_count", 0),
            flush=True,
        )
        print(
            "[Sprint76-2A Insight] Best Evidence:",
            repr(best_evidence.get("text", "")),
            flush=True,
        )
        print(
            "[Sprint76-2A Insight] Evidence Score:",
            best_evidence.get("evidence_score", 0),
            flush=True,
        )
        print(
            "[Sprint76-2A Insight] Best Pain:",
            repr(best_pain),
            flush=True,
        )
        print(
            "[Sprint76-2A Insight] Best Benefit:",
            repr(best_benefit),
            flush=True,
        )

        return {
            "ok": True,
            "version": self.VERSION,
            "product_name": product_name,
            "review_count": len(normalized_reviews),
            "raw_review_count": selector_result.get(
                "raw_review_count",
                len(normalized_reviews),
            ),
            "selected_review_count": selector_result.get(
                "selected_review_count",
                len(normalized_reviews),
            ),
            "social_comment_count": len(normalized_social),
            "smart_selector": selector_result,
            "evidence_top5": sentence_evidence.get(
                "evidence_top5",
                [],
            ),
            "sentence_evidence": sentence_evidence,
            "pain_top3": selector_result.get(
                "pain_top3",
                [],
            ),
            "benefit_top3": selector_result.get(
                "benefit_top3",
                [],
            ),
            "emotion_top3": selector_result.get(
                "emotion_top3",
                [],
            ),
            "pain_points": pain_points[:5],
            "benefits": benefits[:5],
            "buy_reasons": buy_reasons[:5],
            "personas": personas[:5],
            "common_keywords": common_keywords[:10],
            "best_pain_point": best_pain,
            "best_benefit": best_benefit,
            "best_buy_reason": best_buy_reason,
            "best_persona": best_persona,
            "best_quote": best_evidence.get("text", ""),
            "best_evidence": best_evidence,
            "ranked_reviews": normalized_reviews[:5],
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
    ) -> List[Dict[str, Any]]:
        if reviews is None:
            return []

        if isinstance(reviews, str):
            text = self._clean_text(reviews)
            return [
                self._build_review_item(
                    text=text,
                    quality_score=70.0,
                    source="text",
                )
            ] if text else []

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

            if not text:
                return []

            return [
                self._build_review_item(
                    text=text,
                    quality_score=self._safe_float(
                        reviews.get("quality_score"),
                        70.0,
                    ),
                    source=str(
                        reviews.get("source")
                        or reviews.get("ocr_engine")
                        or "dict"
                    ),
                )
            ]

        if not isinstance(reviews, list):
            return []

        result: List[Dict[str, Any]] = []

        for item in reviews:
            if isinstance(item, str):
                text = self._clean_text(item)

                review_item = self._build_review_item(
                    text=text,
                    quality_score=70.0,
                    source="text",
                )

            elif isinstance(item, dict):
                text = self._review_dict_to_text(item)

                review_item = self._build_review_item(
                    text=text,
                    quality_score=self._safe_float(
                        item.get("quality_score"),
                        70.0,
                    ),
                    source=str(
                        item.get("source")
                        or item.get("ocr_engine")
                        or "dict"
                    ),
                )

                review_item["image_index"] = item.get(
                    "image_index"
                )
                review_item["paragraph_index"] = item.get(
                    "paragraph_index"
                )

            else:
                continue

            if review_item["text"] and len(
                review_item["text"]
            ) >= 5:
                result.append(review_item)

        return self._merge_similar_reviews(result)

    def _build_review_item(
        self,
        text: str,
        quality_score: float,
        source: str,
    ) -> Dict[str, Any]:
        cleaned = self._clean_text(text)
        experience_score = self._experience_score(
            cleaned
        )
        specificity_score = self._specificity_score(
            cleaned
        )
        evidence_score = round(
            quality_score * 0.60
            + experience_score * 0.25
            + specificity_score * 0.15,
            1,
        )

        return {
            "text": cleaned,
            "quality_score": round(
                max(0.0, min(100.0, quality_score)),
                1,
            ),
            "experience_score": experience_score,
            "specificity_score": specificity_score,
            "evidence_score": evidence_score,
            "source": source,
        }

    def _safe_float(
        self,
        value: Any,
        fallback: float,
    ) -> float:
        try:
            return float(value)
        except Exception:
            return fallback

    def _experience_score(
        self,
        text: str,
    ) -> float:
        score = 35.0

        patterns = {
            r"\d+\s*(일|주|개월|달|년)": 22.0,
            r"(며칠|몇주|한달|두달|세달|오래|계속)\s*(사용|써|쓰)": 18.0,
            r"(사용해보니|써보니|붙여보니|설치해보니)": 16.0,
            r"(매일|매번|꾸준히|계속)\s*(사용|쓰)": 14.0,
            r"(아직도|지금도)\s*(안|잘|튼튼|멀쩡)": 14.0,
            r"(재구매|다시\s*살|또\s*살|추천)": 10.0,
        }

        for pattern, weight in patterns.items():
            if re.search(pattern, text):
                score += weight

        if len(text) >= 60:
            score += 8.0
        elif len(text) >= 35:
            score += 5.0

        return round(
            max(0.0, min(100.0, score)),
            1,
        )

    def _specificity_score(
        self,
        text: str,
    ) -> float:
        score = 30.0

        if re.search(r"\d", text):
            score += 15.0

        concrete_words = (
            "접착",
            "설치",
            "고정",
            "수납",
            "공간",
            "욕실",
            "벽",
            "슬리퍼",
            "건조",
            "물기",
            "떨어",
            "무타공",
        )

        score += min(
            sum(
                7.0
                for word in concrete_words
                if word in text
            ),
            42.0,
        )

        if re.search(
            r"(좋아요|만족합니다|추천합니다)$",
            text,
        ) and len(text) < 20:
            score -= 18.0

        return round(
            max(0.0, min(100.0, score)),
            1,
        )

    def _merge_similar_reviews(
        self,
        reviews: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []

        for review in sorted(
            reviews,
            key=lambda item: (
                item.get("evidence_score", 0),
                len(item.get("text", "")),
            ),
            reverse=True,
        ):
            text = review.get("text", "")
            tokens = self._token_set(text)

            duplicate = False

            for existing in result:
                existing_tokens = self._token_set(
                    existing.get("text", "")
                )

                union = tokens | existing_tokens
                overlap = (
                    len(tokens & existing_tokens)
                    / max(len(union), 1)
                )

                if overlap >= 0.72:
                    duplicate = True
                    break

            if not duplicate:
                result.append(review)

        return result

    def _token_set(
        self,
        text: str,
    ) -> set[str]:
        return {
            token
            for token in re.findall(
                r"[가-힣A-Za-z0-9]{2,}",
                text.lower(),
            )
            if token not in self.STOP_WORDS
        }

    def _select_smart_reviews(
        self,
        reviews: List[Dict[str, Any]],
        product_name: str = "",
        limit: int = 30,
    ) -> Dict[str, Any]:
        scored: List[Dict[str, Any]] = []

        filter_stats = {
            "rejected_irrelevant": 0,
            "rejected_low_trust": 0,
            "rejected_duplicate": 0,
            "accepted": 0,
        }

        product_tokens = self._product_tokens(
            product_name
        )

        for review in reviews:
            item = dict(review)
            text = self._clean_text(
                item.get("text", "")
            )

            if not text:
                continue

            relevance_score = self._relevance_score(
                text,
                product_tokens,
            )

            trust_score = self._trust_score(
                item
            )

            evidence_score = self._evidence_strength(
                item
            )

            emotion = self._emotion_label(
                text
            )

            final_score = round(
                relevance_score * 0.35
                + trust_score * 0.30
                + evidence_score * 0.35,
                1,
            )

            item.update(
                {
                    "relevance_score": relevance_score,
                    "trust_score": trust_score,
                    "evidence_strength": evidence_score,
                    "selector_score": final_score,
                    "emotion": emotion,
                }
            )

            if relevance_score < 32:
                filter_stats[
                    "rejected_irrelevant"
                ] += 1
                continue

            if trust_score < 35:
                filter_stats[
                    "rejected_low_trust"
                ] += 1
                continue

            scored.append(item)

        scored.sort(
            key=lambda item: (
                item.get("selector_score", 0),
                item.get("evidence_strength", 0),
                item.get("quality_score", 0),
                len(item.get("text", "")),
            ),
            reverse=True,
        )

        selected: List[Dict[str, Any]] = []

        for item in scored:
            if self._is_semantic_duplicate(
                item,
                selected,
            ):
                filter_stats[
                    "rejected_duplicate"
                ] += 1
                continue

            selected.append(item)

            if len(selected) >= limit:
                break

        filter_stats["accepted"] = len(
            selected
        )

        evidence_top5 = [
            self._selector_summary(item)
            for item in selected[:5]
        ]

        pain_candidates = [
            item
            for item in selected
            if self._contains_pain_signal(
                item.get("text", "")
            )
        ]

        benefit_candidates = [
            item
            for item in selected
            if self._contains_benefit_signal(
                item.get("text", "")
            )
        ]

        emotion_candidates = sorted(
            selected,
            key=lambda item: (
                self._emotion_strength(
                    item.get("text", "")
                ),
                item.get("selector_score", 0),
            ),
            reverse=True,
        )

        return {
            "ok": bool(selected),
            "version": "smart-review-selector-76-1",
            "raw_review_count": len(reviews),
            "selected_review_count": len(selected),
            "selected_reviews": selected,
            "filter_stats": filter_stats,
            "evidence_top5": evidence_top5,
            "pain_top3": [
                self._selector_summary(item)
                for item in pain_candidates[:3]
            ],
            "benefit_top3": [
                self._selector_summary(item)
                for item in benefit_candidates[:3]
            ],
            "emotion_top3": [
                self._selector_summary(item)
                for item in emotion_candidates[:3]
            ],
        }

    def _selector_summary(
        self,
        item: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "text": item.get("text", ""),
            "selector_score": item.get(
                "selector_score",
                0,
            ),
            "relevance_score": item.get(
                "relevance_score",
                0,
            ),
            "trust_score": item.get(
                "trust_score",
                0,
            ),
            "evidence_strength": item.get(
                "evidence_strength",
                0,
            ),
            "quality_score": item.get(
                "quality_score",
                0,
            ),
            "emotion": item.get(
                "emotion",
                "neutral",
            ),
            "source": item.get(
                "source",
                "",
            ),
        }

    def _product_tokens(
        self,
        product_name: str,
    ) -> set[str]:
        text = self._clean_text(
            product_name
        ).lower()

        tokens = {
            token
            for token in re.findall(
                r"[가-힣A-Za-z0-9]{2,}",
                text,
            )
            if token not in self.STOP_WORDS
        }

        category_aliases = {
            "캐리어": {
                "여행",
                "짐",
                "수납",
                "바퀴",
                "손잡이",
                "지퍼",
                "기내용",
                "24인치",
                "20인치",
            },
            "슬리퍼": {
                "욕실",
                "정리",
                "바닥",
                "벽",
                "무타공",
                "접착",
                "건조",
            },
            "텀블러": {
                "보냉",
                "보온",
                "빨대",
                "물병",
                "음료",
                "얼음",
            },
        }

        for category, aliases in category_aliases.items():
            if category in text:
                tokens.add(category)
                tokens.update(aliases)

        return tokens

    def _relevance_score(
        self,
        text: str,
        product_tokens: set[str],
    ) -> float:
        if not text:
            return 0.0

        if not product_tokens:
            return 65.0

        review_tokens = self._token_set(
            text
        )

        overlap = review_tokens & product_tokens

        score = 28.0

        score += min(
            len(overlap) * 12.0,
            48.0,
        )

        if any(
            token in text.lower()
            for token in product_tokens
        ):
            score += 12.0

        if len(text) >= 30:
            score += 7.0

        return round(
            max(
                0.0,
                min(100.0, score),
            ),
            1,
        )

    def _trust_score(
        self,
        item: Dict[str, Any],
    ) -> float:
        quality = self._safe_float(
            item.get("quality_score"),
            70.0,
        )

        experience = self._safe_float(
            item.get("experience_score"),
            self._experience_score(
                item.get("text", "")
            ),
        )

        source = str(
            item.get("source")
            or ""
        ).lower()

        source_bonus = 0.0

        if "coupang" in source:
            source_bonus = 8.0
        elif "ocr" in source:
            source_bonus = 5.0
        elif "social" in source:
            source_bonus = 2.0

        return round(
            max(
                0.0,
                min(
                    100.0,
                    quality * 0.58
                    + experience * 0.34
                    + source_bonus,
                ),
            ),
            1,
        )

    def _evidence_strength(
        self,
        item: Dict[str, Any],
    ) -> float:
        text = self._clean_text(
            item.get("text", "")
        )

        specificity = self._safe_float(
            item.get("specificity_score"),
            self._specificity_score(text),
        )

        score = specificity * 0.60

        if re.search(
            r"\d+\s*(일|주|개월|달|년|박)",
            text,
        ):
            score += 15.0

        if any(
            word in text
            for word in (
                "사용해보니",
                "써보니",
                "설치해보니",
                "직접",
                "실제로",
                "아직도",
                "재구매",
            )
        ):
            score += 12.0

        if len(text) >= 45:
            score += 8.0

        return round(
            max(
                0.0,
                min(100.0, score),
            ),
            1,
        )

    def _is_semantic_duplicate(
        self,
        candidate: Dict[str, Any],
        selected: List[Dict[str, Any]],
    ) -> bool:
        candidate_tokens = self._token_set(
            candidate.get("text", "")
        )

        if not candidate_tokens:
            return True

        for existing in selected:
            existing_tokens = self._token_set(
                existing.get("text", "")
            )

            union = (
                candidate_tokens
                | existing_tokens
            )

            similarity = (
                len(
                    candidate_tokens
                    & existing_tokens
                )
                / max(
                    len(union),
                    1,
                )
            )

            if similarity >= 0.68:
                return True

        return False

    def _contains_pain_signal(
        self,
        text: str,
    ) -> bool:
        signals = (
            "불편",
            "아쉽",
            "걱정",
            "어렵",
            "부족",
            "무거",
            "좁",
            "섞",
            "문제",
            "단점",
        )

        return any(
            signal in text
            for signal in signals
        )

    def _contains_benefit_signal(
        self,
        text: str,
    ) -> bool:
        signals = (
            "편하",
            "좋",
            "만족",
            "깔끔",
            "튼튼",
            "가볍",
            "넉넉",
            "추천",
            "정리",
            "수납",
        )

        return any(
            signal in text
            for signal in signals
        )

    def _emotion_label(
        self,
        text: str,
    ) -> str:
        if any(
            word in text
            for word in (
                "최고",
                "정말 만족",
                "아주 만족",
                "추천",
                "재구매",
                "대만족",
            )
        ):
            return "strong_positive"

        if any(
            word in text
            for word in (
                "만족",
                "좋아요",
                "편해",
                "깔끔",
                "예뻐",
            )
        ):
            return "positive"

        if any(
            word in text
            for word in (
                "불편",
                "아쉽",
                "별로",
                "단점",
                "실망",
            )
        ):
            return "negative"

        return "neutral"

    def _emotion_strength(
        self,
        text: str,
    ) -> int:
        score = 0

        strong_words = (
            "정말",
            "진짜",
            "아주",
            "최고",
            "대만족",
            "추천",
            "재구매",
            "실망",
        )

        score += sum(
            2
            for word in strong_words
            if word in text
        )

        score += min(
            text.count("!")
            + text.count("?"),
            3,
        )

        return score

    def _build_sentence_evidence(
        self,
        reviews: List[Dict[str, Any]],
        product_name: str = "",
    ) -> Dict[str, Any]:
        product_tokens = self._product_tokens(
            product_name
        )

        candidates: List[Dict[str, Any]] = []

        for review_index, review in enumerate(
            reviews
        ):
            review_text = self._clean_text(
                review.get("text", "")
            )

            for sentence_index, sentence in enumerate(
                self._split_sentences(review_text)
            ):
                scored = self._score_evidence_sentence(
                    sentence=sentence,
                    review=review,
                    product_tokens=product_tokens,
                )

                if scored.get("score", 0) < 48:
                    continue

                scored["review_index"] = review_index
                scored["sentence_index"] = sentence_index
                candidates.append(scored)

        candidates.sort(
            key=lambda item: (
                item.get("score", 0),
                item.get("feature_score", 0),
                item.get("relevance_score", 0),
                -abs(len(item.get("text", "")) - 48),
            ),
            reverse=True,
        )

        unique: List[Dict[str, Any]] = []

        for candidate in candidates:
            if self._sentence_duplicate(
                candidate.get("text", ""),
                unique,
            ):
                continue

            unique.append(candidate)

            if len(unique) >= 5:
                break

        best = (
            dict(unique[0])
            if unique
            else self._select_best_evidence(
                reviews
            )
        )

        return {
            "ok": bool(best),
            "version": "evidence-sentence-extractor-76-2a",
            "sentence_count": len(candidates),
            "best_evidence": best,
            "evidence_top5": unique,
        }

    def _split_sentences(
        self,
        text: str,
    ) -> List[str]:
        text = self._clean_text(text)

        if not text:
            return []

        # OCR 숫자 노이즈와 소실된 종결어미 복원
        text = re.sub(
            r"추천드립니\s*[0-9ⅠIl|]*\s*(?=\d+\s*박)",
            "추천드립니다. ",
            text,
        )

        text = re.sub(
            r"만족스러운\s*선택이었어요\s*(?=튼튼)",
            "만족스러운 선택이었어요. ",
            text,
        )

        text = re.sub(
            r"([가-힣])(?=(한쪽은|다른 한쪽은|자잘한|제가 고른|튼튼하고|덕분에|2\s*박|3\s*박))",
            r"\1. ",
            text,
        )

        text = re.sub(
            r"([.!?])(?=[가-힣A-Za-z0-9])",
            r"\1 ",
            text,
        )

        raw_parts = re.split(
            r"(?<=[.!?])\s+|(?<=다)\s+(?=[가-힣])|(?<=요)\s+(?=[가-힣])",
            text,
        )

        result: List[str] = []

        for part in raw_parts:
            sentence = self._repair_evidence_sentence(
                part
            )

            if len(sentence) < 10:
                continue

            # 문장이 지나치게 길면 접속부 기준으로 한 번 더 분리
            sub_parts = re.split(
                r"\s+(?=덕분에|하지만|다만|그리고|또한|특히|2\s*박|3\s*박)",
                sentence,
            )

            for sub_part in sub_parts:
                cleaned = self._repair_evidence_sentence(
                    sub_part
                )

                if 10 <= len(cleaned) <= 120:
                    result.append(cleaned)

        if not result and len(text) >= 10:
            result.append(
                self._repair_evidence_sentence(
                    text[:120]
                )
            )

        return result

    def _repair_evidence_sentence(
        self,
        sentence: str,
    ) -> str:
        text = self._clean_text(sentence)

        replacements = (
            ("알차요한쪽은", "알차요. 한쪽은"),
            ("더라고요자잘한", "더라고요. 자잘한"),
            ("은색은사진", "은색은 사진"),
            ("아주만족스러운선택", "아주 만족스러운 선택"),
            ("가법고", "가볍고"),
            ("으 로", "으로"),
            ("추천드립니", "추천드립니다"),
            ("그 r 기 다년다요", ""),
        )

        for before, after in replacements:
            text = text.replace(
                before,
                after,
            )

        text = re.sub(
            r"\s+[0-9ⅠIl|]\s+(?=\d+\s*박)",
            ". ",
            text,
        )

        text = re.sub(
            r"\s+([,.!?])",
            r"\1",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        ).strip(" .,-_/|")

        if text and not text.endswith(
            (".", "!", "?")
        ):
            text += "."

        return text

    def _score_evidence_sentence(
        self,
        sentence: str,
        review: Dict[str, Any],
        product_tokens: set[str],
    ) -> Dict[str, Any]:
        text = self._clean_text(sentence)

        relevance_score = self._relevance_score(
            text,
            product_tokens,
        )

        specificity_score = self._specificity_score(
            text
        )

        experience_score = self._experience_score(
            text
        )

        quality_score = self._safe_float(
            review.get("quality_score"),
            70.0,
        )

        feature_words = (
            "지퍼",
            "분리",
            "수납",
            "메쉬",
            "포켓",
            "바퀴",
            "손잡이",
            "24인치",
            "20인치",
            "가볍",
            "튼튼",
            "이동",
            "공간",
        )

        feature_score = min(
            sum(
                14.0
                for word in feature_words
                if word in text
            ),
            70.0,
        )

        score = round(
            relevance_score * 0.25
            + specificity_score * 0.20
            + experience_score * 0.15
            + quality_score * 0.20
            + feature_score * 0.20,
            1,
        )

        if 18 <= len(text) <= 85:
            score += 10.0
        elif len(text) > 110:
            score -= 18.0

        if re.search(
            r"\d+\s*(일|주|개월|달|년|박|인치)",
            text,
        ):
            score += 9.0

        if any(
            word in text
            for word in (
                "섞이지",
                "분리하기 좋",
                "편했",
                "유용",
                "딱 적당",
                "이동이 편",
            )
        ):
            score += 9.0

        # 구체적 기능 없이 만족·추천만 있는 문장 감점
        if (
            any(
                word in text
                for word in (
                    "만족",
                    "추천",
                    "좋아요",
                )
            )
            and feature_score == 0
        ):
            score -= 12.0

        score = round(
            max(
                0.0,
                min(100.0, score),
            ),
            1,
        )

        return {
            "text": text,
            "score": score,
            "evidence_score": score,
            "relevance_score": relevance_score,
            "specificity_score": specificity_score,
            "experience_score": experience_score,
            "quality_score": quality_score,
            "feature_score": feature_score,
            "emotion": self._emotion_label(text),
        }

    def _sentence_duplicate(
        self,
        sentence: str,
        selected: List[Dict[str, Any]],
    ) -> bool:
        tokens = self._token_set(
            sentence
        )

        if not tokens:
            return True

        for item in selected:
            existing_tokens = self._token_set(
                item.get("text", "")
            )

            union = tokens | existing_tokens

            similarity = (
                len(tokens & existing_tokens)
                / max(len(union), 1)
            )

            if similarity >= 0.60:
                return True

        return False

    def _align_benefit_with_evidence(
        self,
        best_benefit: str,
        evidence_text: str,
    ) -> str:
        evidence = self._clean_text(
            evidence_text
        )

        if any(
            word in evidence
            for word in (
                "섞이지",
                "분리",
                "지퍼",
                "메쉬 포켓",
            )
        ):
            return (
                "내부 공간을 나눠 깔끔하게 "
                "분리 수납할 수 있다"
            )

        if any(
            word in evidence
            for word in (
                "24인치",
                "20인치",
                "2박",
                "3박",
                "출장",
            )
        ):
            return (
                "여행 기간에 맞는 크기와 "
                "수납공간을 활용할 수 있다"
            )

        if any(
            word in evidence
            for word in (
                "가볍",
                "이동",
                "바퀴",
                "손잡이",
            )
        ):
            return "가볍고 이동이 편하다"

        if any(
            word in evidence
            for word in (
                "튼튼",
                "오래",
                "내구성",
            )
        ):
            return "튼튼해서 오래 사용할 수 있다"

        return best_benefit

    def _select_best_evidence(
        self,
        reviews: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not reviews:
            return {
                "text": "",
                "quality_score": 0.0,
                "experience_score": 0.0,
                "specificity_score": 0.0,
                "evidence_score": 0.0,
            }

        ranked = sorted(
            reviews,
            key=lambda item: (
                float(item.get("evidence_score", 0)),
                float(item.get("experience_score", 0)),
                len(item.get("text", "")),
            ),
            reverse=True,
        )

        return dict(ranked[0])

    def _review_dict_to_text(
        self,
        review: Dict[str, Any],
    ) -> str:
        # OCR 리뷰는 content / text / review_text에 같은 문장이
        # 반복 저장되므로 첫 번째 본문 값만 사용합니다.
        primary_keys = (
            "content",
            "review_text",
            "review",
            "text",
            "body",
            "comment",
            "review_content",
        )

        primary_text = ""

        for key in primary_keys:
            value = review.get(key)

            if isinstance(value, str) and value.strip():
                primary_text = value.strip()
                break

        title_text = ""

        for key in (
            "headline",
            "title",
        ):
            value = review.get(key)

            if isinstance(value, str) and value.strip():
                candidate = value.strip()

                if (
                    candidate
                    and candidate != primary_text
                    and candidate not in primary_text
                ):
                    title_text = candidate
                    break

        if title_text and primary_text:
            return self._clean_text(
                f"{title_text}. {primary_text}"
            )

        return self._clean_text(
            primary_text or title_text
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
        reviews: List[Dict[str, Any]],
        pattern_map: Dict[str, List[str]],
        insight_type: str,
    ) -> List[Dict[str, Any]]:
        scored: Dict[str, Dict[str, Any]] = {}

        for review_index, review_item in enumerate(reviews):
            review = review_item.get("text", "")
            lowered = review.lower()
            review_weight = max(
                0.5,
                float(review_item.get("evidence_score", 70.0)) / 70.0,
            )

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
                    score += self._pattern_weight(pattern) * review_weight

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
                            "quality_score": review_item.get("quality_score", 0),
                            "experience_score": review_item.get("experience_score", 0),
                            "evidence_score": review_item.get("evidence_score", 0),
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
        reviews: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        counter: Counter[str] = Counter()

        for review_item in reviews:
            review = review_item.get("text", "")
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
        reviews: List[Dict[str, Any]],
        product_name: str = "",
    ) -> List[Dict[str, Any]]:
        if pain_points:
            return pain_points

        combined_text = " ".join(
            item.get("text", "")
            for item in reviews
        ).lower()

        product_text = str(product_name or "").lower()

        if (
            "캐리어" in product_text
            or "여행" in combined_text
            or "24인치" in combined_text
            or "20인치" in combined_text
        ):
            return [
                self._inferred_item(
                    "여행 짐을 정리하고 이동하기 불편하다",
                    4.5,
                ),
                self._inferred_item(
                    "여행 기간에 맞는 수납 크기를 고르기 어렵다",
                    3.8,
                ),
            ]

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
        reviews: List[Dict[str, Any]],
        product_name: str = "",
    ) -> List[Dict[str, Any]]:
        if benefits:
            return benefits

        combined_text = " ".join(
            item.get("text", "")
            for item in reviews
        ).lower()

        product_text = str(product_name or "").lower()

        if (
            "캐리어" in product_text
            or "여행" in combined_text
            or "24인치" in combined_text
            or "20인치" in combined_text
        ):
            return [
                self._inferred_item(
                    "내부 공간을 나눠 깔끔하게 분리 수납할 수 있다",
                    4.5,
                ),
                self._inferred_item(
                    "튼튼하고 가벼워 여행 중 이동이 편하다",
                    4.2,
                ),
            ]

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
            "raw_review_count": 0,
            "selected_review_count": 0,
            "smart_selector": {
                "ok": False,
                "version": "smart-review-selector-76-1",
                "raw_review_count": 0,
                "selected_review_count": 0,
                "selected_reviews": [],
                "filter_stats": {},
                "evidence_top5": [],
                "pain_top3": [],
                "benefit_top3": [],
                "emotion_top3": [],
            },
            "evidence_top5": [],
            "sentence_evidence": {
                "ok": False,
                "version": "evidence-sentence-extractor-76-2a",
                "sentence_count": 0,
                "best_evidence": {},
                "evidence_top5": [],
            },
            "pain_top3": [],
            "benefit_top3": [],
            "emotion_top3": [],
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
            "best_quote": "",
            "best_evidence": {},
            "ranked_reviews": [],
            "content_angle": {
                "type": "problem_solution",
                "name": "문제 해결형",
                "reason": "리뷰가 없어 기본 문제 해결 구조를 사용합니다.",
            },
            "warnings": [
                "분석할 리뷰가 없어 기본 인사이트를 생성했습니다."
            ],
        }