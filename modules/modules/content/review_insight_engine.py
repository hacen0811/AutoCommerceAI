from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List, Tuple

from .review_quality_analyzer import ReviewQualityAnalyzer


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

    VERSION = "review-insight-engine-128-1"

    PAIN_PATTERNS = {
        "사용 중 무게감이 부담될 수 있다": [
            "무겁",
            "무게감",
            "목이 아프",
            "손목이 아프",
            "들고 있기 힘들",
        ],
        "소음이 신경 쓰일 수 있다": [
            "소음",
            "시끄럽",
            "소리가 크",
            "귀에 거슬",
        ],
        "성능이나 세기가 기대보다 아쉽다": [
            "약하",
            "세기가 아쉽",
            "성능이 아쉽",
            "바람이 약",
            "효과가 약",
        ],
        "사용 시간이 짧아 자주 충전해야 한다": [
            "배터리가 짧",
            "사용 시간이 짧",
            "자주 충전",
            "충전이 번거",
        ],
        "크기나 공간 활용이 불편하다": [
            "공간이 좁",
            "자리 차지",
            "부피가 크",
            "보관이 불편",
            "수납이 어렵",
        ],
        "설치나 조립이 어렵고 번거롭다": [
            "설치가 어렵",
            "설치가 힘들",
            "설치가 번거",
            "조립이 어렵",
            "조립이 힘들",
        ],
        "고정력이나 내구성이 걱정된다": [
            "고정이 안",
            "잘 떨어",
            "흔들",
            "부서",
            "내구성이 아쉽",
        ],
        "세척과 관리가 번거롭다": [
            "세척이 어렵",
            "세척이 번거",
            "관리하기 어렵",
            "물때",
            "곰팡이",
        ],
        "가격 대비 만족도가 아쉽다": [
            "가격이 비싸",
            "가성비가 아쉽",
            "가격 대비",
            "돈이 아깝",
        ],
    }

    BENEFIT_PATTERNS = {
        "휴대하기 편하고 다양한 장소에서 사용할 수 있다": [
            "휴대하기 좋",
            "휴대가 편",
            "들고 다니기 좋",
            "외출할 때",
            "어디서나",
            "다양한 장소",
        ],
        "성능과 사용 효과가 만족스럽다": [
            "성능이 좋",
            "효과가 좋",
            "바람이 세",
            "시원",
            "잘 잘리",
            "흡수력이 좋",
        ],
        "설치나 조립이 간편하다": [
            "설치가 간편",
            "설치가 쉽",
            "조립이 쉽",
            "붙이기만",
            "바로 사용",
        ],
        "가볍고 사용하기 편하다": [
            "가볍",
            "사용하기 편",
            "손에 잘 잡",
            "착용감이 좋",
            "이동이 편",
        ],
        "공간을 효율적으로 활용할 수 있다": [
            "공간 활용",
            "자리 차지하지",
            "정리가 깔끔",
            "수납하기 좋",
            "분리 수납",
        ],
        "튼튼하고 오래 사용할 수 있다": [
            "튼튼",
            "내구성",
            "오래 쓸",
            "견고",
            "마감이 좋",
        ],
        "세척과 관리가 편하다": [
            "세척이 쉽",
            "관리하기 편",
            "물로 씻",
            "위생적",
            "건조가 잘",
        ],
        "디자인이 깔끔하고 만족스럽다": [
            "디자인",
            "깔끔",
            "세련",
            "예쁘",
            "색상이 좋",
        ],
        "여러 용도로 활용할 수 있다": [
            "다용도",
            "여러 용도",
            "탁상용",
            "핸디",
            "목걸이",
            "각도 조절",
        ],
    }

    GENERAL_PAIN_PATTERNS = {
        "사용 목적에 맞는 크기나 사양을 고르기 어렵다": [
            "크기 고민",
            "사이즈 고민",
            "몇 인치",
            "용량 고민",
            "선택이 어렵",
        ],
        "제품을 이동하거나 보관하기 불편하다": [
            "이동이 불편",
            "들고 다니기 불편",
            "보관이 불편",
            "정리하기 어렵",
        ],
        "구성이나 수납공간 활용이 아쉽다": [
            "내부 공간",
            "수납공간",
            "공간이 부족",
            "구성이 아쉽",
        ],
    }

    GENERAL_BENEFIT_PATTERNS = {
        "구성과 공간을 효율적으로 활용할 수 있다": [
            "분리하기 좋",
            "내부 공간 구성",
            "수납이 넉넉",
            "공간이 알차",
            "정리하기 좋",
        ],
        "이동과 휴대가 편하다": [
            "가볍고",
            "이동이 편",
            "끌기 편",
            "휴대가 편",
            "들고 다니기 좋",
        ],
        "튼튼해서 오래 사용할 수 있다": [
            "튼튼",
            "오래 쓸",
            "내구성",
            "견고",
        ],
        "디자인과 마감이 만족스럽다": [
            "깔끔하고 세련",
            "디자인",
            "색상",
            "예쁘",
            "마감",
        ],
    }

    BUY_REASON_PATTERNS = {
        "일상에서 겪는 불편을 줄이기 위해": [
            "불편해서",
            "힘들어서",
            "필요해서",
            "해결하려고",
        ],
        "휴대와 이동이 편한 제품을 원해서": [
            "휴대",
            "이동",
            "외출",
            "여행",
            "들고 다니",
        ],
        "공간을 효율적으로 활용하기 위해": [
            "공간 활용",
            "정리",
            "수납",
            "자리 차지",
        ],
        "사용과 관리가 간편한 제품을 원해서": [
            "간편",
            "쉽게",
            "세척",
            "관리",
            "설치",
        ],
        "성능과 내구성이 좋은 제품을 원해서": [
            "성능",
            "효과",
            "튼튼",
            "내구성",
            "고정력",
        ],
        "디자인이 마음에 들어서": [
            "디자인",
            "색상",
            "예뻐서",
            "깔끔",
            "세련",
        ],
    }

    PERSONA_PATTERNS = {
        "외출과 이동이 잦은 사람": [
            "외출",
            "여행",
            "출퇴근",
            "휴대",
            "이동",
        ],
        "공간 활용과 정리를 중요하게 생각하는 사람": [
            "정리",
            "수납",
            "깔끔",
            "공간 활용",
        ],
        "사용 편의성을 중요하게 생각하는 사람": [
            "간편",
            "편리",
            "쉽게",
            "사용하기 편",
        ],
        "성능과 내구성을 중요하게 생각하는 사람": [
            "성능",
            "효과",
            "튼튼",
            "내구성",
        ],
        "위생과 관리를 중요하게 생각하는 사람": [
            "위생",
            "세척",
            "관리",
            "건조",
        ],
        "디자인과 마감을 중요하게 생각하는 사람": [
            "디자인",
            "색상",
            "예쁘",
            "마감",
        ],
    }

    PAIN_SIGNAL_PATTERNS = {
        "general": (
            "불편",
            "힘들",
            "아쉽",
            "걱정",
            "부족",
            "번거",
            "어렵",
            "문제",
            "단점",
            "실망",
            "부담",
            "귀찮",
        ),
        "fan": (
            "덥",
            "더위",
            "시원하지",
            "바람이 약",
            "풍량이 약",
            "무겁",
            "목이 아프",
            "소음",
            "시끄럽",
            "배터리가 짧",
            "충전이 자주",
            "오래 못",
        ),
        "carrier": (
            "짐이 섞",
            "수납이 부족",
            "이동이 불편",
            "무겁",
            "바퀴가 잘 안",
            "손잡이가 불편",
            "크기 고민",
            "몇 인치",
        ),
        "cutting_board": (
            "미끄럽",
            "칼자국",
            "냄새",
            "세척이 어렵",
            "물때",
            "휘어",
            "변색",
        ),
        "laundry": (
            "빨래가 섞",
            "분리하기 어렵",
            "이동이 불편",
            "공간이 부족",
            "정리가 안",
            "바퀴가 불편",
        ),
        "storage": (
            "정리가 안",
            "찾기 어렵",
            "수납이 부족",
            "공간이 좁",
            "꺼내기 불편",
            "쌓기 어렵",
        ),
        "slipper_rack": (
            "바닥에 흩어",
            "물기가 안 마",
            "정리가 안",
            "떨어질까",
            "접착력이 약",
            "벽 손상",
        ),
        "tumbler": (
            "보온이 짧",
            "보냉이 짧",
            "새",
            "세척이 어렵",
            "무겁",
            "뚜껑이 불편",
        ),
    }

    PAIN_CAUSE_PATTERNS = (
        r"(.+?)(?:해서|하니|하다 보니|때문에|라서|여서)\s*(.+)",
        r"(.+?)(?:지만|는데|으나)\s*(.+)",
    )

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

        review_quality = ReviewQualityAnalyzer().analyze(
            reviews=normalized_reviews,
            product_name=product_name,
        )

        quality_reviews = review_quality.get(
            "selected_reviews",
            [],
        )

        if quality_reviews:
            normalized_reviews = quality_reviews

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

        pain_sentence_result = self._build_pain_sentence_evidence(
            normalized_reviews,
            product_name=product_name,
        )

        best_pain_evidence = pain_sentence_result.get(
            "best_pain_evidence",
            {},
        )

        pain_points = self._apply_pain_fallbacks(
            pain_points,
            benefits,
            normalized_reviews,
            product_name=product_name,
            pain_sentence_result=pain_sentence_result,
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
            "사용 중 불편한 점이 있다",
        )

        if best_pain_evidence.get("summary"):
            pattern_score = self._safe_float(
                pain_points[0].get("score") if pain_points else 0,
                0.0,
            )
            pain_evidence_score = self._safe_float(
                best_pain_evidence.get("pain_score"),
                0.0,
            )

            if (
                not pain_points
                or pain_points[0].get("inferred")
                or pain_evidence_score >= pattern_score + 8.0
            ):
                best_pain = best_pain_evidence.get(
                    "summary",
                    best_pain,
                )

        best_benefit = self._first_label(
            benefits,
            "제품의 장점을 활용할 수 있다",
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
            "일상에서 겪는 불편을 줄이기 위해",
        )

        best_persona = self._first_label(
            personas,
            "제품의 편의성과 성능을 중요하게 생각하는 사람",
        )

        print(
            "[Sprint116-1 Insight Bridge] Review Quality:",
            {
                "input": review_quality.get("input_count", 0),
                "coalesced": review_quality.get("coalesced_count", 0),
                "selected": review_quality.get("selected_count", 0),
                "average_score": review_quality.get("average_score", 0),
            },
            flush=True,
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
            "[Sprint118-1 Pain Evidence] Best Sentence:",
            repr(best_pain_evidence.get("text", "")),
            flush=True,
        )
        print(
            "[Sprint118-1 Pain Evidence] Summary:",
            repr(best_pain_evidence.get("summary", "")),
            flush=True,
        )
        print(
            "[Sprint118-1 Pain Evidence] Score:",
            best_pain_evidence.get("pain_score", 0),
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
            "review_quality": review_quality,
            "quality_top5": review_quality.get("top_reviews", []),
            "smart_selector": selector_result,
            "evidence_top5": sentence_evidence.get(
                "evidence_top5",
                [],
            ),
            "sentence_evidence": sentence_evidence,
            "pain_sentence_evidence": pain_sentence_result,
            "best_pain_evidence": best_pain_evidence,
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
            "성능",
            "효과",
            "무게",
            "소음",
            "배터리",
            "충전",
            "휴대",
            "설치",
            "조립",
            "고정",
            "수납",
            "공간",
            "세척",
            "관리",
            "내구성",
            "디자인",
            "마감",
            "크기",
            "용량",
            "각도",
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
                "인치",
            },
            "선풍기": {
                "바람",
                "시원",
                "목걸이",
                "핸디",
                "탁상용",
                "배터리",
                "충전",
                "소음",
            },
            "도마": {
                "칼질",
                "미끄럼",
                "세척",
                "항균",
                "냄새",
                "주방",
                "칼자국",
            },
            "빨래바구니": {
                "세탁",
                "빨래",
                "수납",
                "바구니",
                "이동",
                "바퀴",
                "분리",
            },
            "정리함": {
                "수납",
                "정리",
                "공간",
                "서랍",
                "투명창",
                "적층",
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

    def _pain_signals_for_category(
        self,
        category: str,
    ) -> Tuple[str, ...]:
        general = tuple(
            self.PAIN_SIGNAL_PATTERNS.get(
                "general",
                (),
            )
        )
        category_signals = tuple(
            self.PAIN_SIGNAL_PATTERNS.get(
                category,
                (),
            )
        )
        return tuple(
            dict.fromkeys(
                general + category_signals
            )
        )

    def _build_pain_sentence_evidence(
        self,
        reviews: List[Dict[str, Any]],
        product_name: str = "",
    ) -> Dict[str, Any]:
        category = self._category_from_context(
            product_name,
            reviews,
        )
        signals = self._pain_signals_for_category(
            category
        )

        candidates: List[Dict[str, Any]] = []

        for review_index, review in enumerate(reviews):
            review_text = self._clean_text(
                review.get("text", "")
            )

            for sentence_index, sentence in enumerate(
                self._split_sentences(review_text)
            ):
                candidate = self._score_pain_sentence(
                    sentence=sentence,
                    review=review,
                    category=category,
                    signals=signals,
                )

                if candidate.get("pain_score", 0) < 42:
                    continue

                candidate["review_index"] = review_index
                candidate["sentence_index"] = sentence_index
                candidates.append(candidate)

        candidates.sort(
            key=lambda item: (
                item.get("pain_score", 0),
                item.get("explicit_signal_count", 0),
                item.get("quality_score", 0),
                -abs(len(item.get("text", "")) - 46),
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

        best = dict(unique[0]) if unique else {}

        return {
            "ok": bool(best),
            "version": "pain-sentence-evidence-128-1",
            "category": category,
            "candidate_count": len(candidates),
            "best_pain_evidence": best,
            "pain_top5": unique,
        }

    def _score_pain_sentence(
        self,
        sentence: str,
        review: Dict[str, Any],
        category: str,
        signals: Tuple[str, ...],
    ) -> Dict[str, Any]:
        text = self._clean_text(sentence)
        lowered = text.lower()

        matched_signals = [
            signal
            for signal in signals
            if signal in lowered
        ]

        explicit_signal_count = len(
            matched_signals
        )

        category_signals = tuple(
            self.PAIN_SIGNAL_PATTERNS.get(
                category,
                (),
            )
        )
        category_signal_count = sum(
            1
            for signal in category_signals
            if signal in lowered
        )

        quality_score = self._safe_float(
            review.get("quality_score"),
            70.0,
        )
        experience_score = self._experience_score(
            text
        )
        specificity_score = self._specificity_score(
            text
        )

        score = 0.0
        score += min(
            explicit_signal_count * 16.0,
            48.0,
        )
        score += min(
            category_signal_count * 10.0,
            24.0,
        )
        score += quality_score * 0.12
        score += experience_score * 0.08
        score += specificity_score * 0.08

        if any(
            ending in lowered
            for ending in (
                "힘들어서",
                "불편해서",
                "아쉬웠",
                "걱정됐",
                "부담됐",
                "어려웠",
                "번거로웠",
            )
        ):
            score += 12.0

        if any(
            phrase in lowered
            for phrase in (
                "기존 제품",
                "여러 종류",
                "매번",
                "계속",
                "자주",
                "오래",
            )
        ):
            score += 6.0

        # Strongly positive promotional sentences should not become pain.
        positive_only = any(
            phrase in lowered
            for phrase in (
                "만족도 최고",
                "정말 만족",
                "추천드립니다",
                "추천드려요",
                "아주 좋아",
            )
        ) and not matched_signals

        if positive_only:
            score -= 35.0

        if len(text) < 12:
            score -= 15.0
        elif len(text) > 110:
            score -= 10.0

        summary = self._summarize_pain_sentence(
            text,
            category=category,
            matched_signals=matched_signals,
        )

        return {
            "text": text,
            "summary": summary,
            "pain_score": round(
                max(0.0, min(100.0, score)),
                1,
            ),
            "matched_signals": matched_signals,
            "explicit_signal_count": explicit_signal_count,
            "category_signal_count": category_signal_count,
            "quality_score": quality_score,
            "experience_score": experience_score,
            "specificity_score": specificity_score,
            "category": category,
        }

    def _summarize_pain_sentence(
        self,
        sentence: str,
        category: str,
        matched_signals: List[str],
    ) -> str:
        text = self._clean_text(sentence).strip(" .!?")

        # Remove promotional tail after the actual problem statement.
        text = re.split(
            r"(?:그래서|그런데 이번|하지만 이번|이 제품은|사용해보니|써보니)",
            text,
            maxsplit=1,
        )[0].strip(" ,.")

        # Prefer the causal/problem clause when a long review sentence
        # contains both the pain and a later positive product assessment.
        for pattern in self.PAIN_CAUSE_PATTERNS:
            match = re.match(pattern, text)
            if not match:
                continue

            first = self._clean_text(match.group(1))
            second = self._clean_text(match.group(2))

            first_has_pain = any(
                signal in first.lower()
                for signal in self._pain_signals_for_category(category)
            )
            second_has_pain = any(
                signal in second.lower()
                for signal in self._pain_signals_for_category(category)
            )

            if first_has_pain and not second_has_pain:
                text = first
                break

            if second_has_pain:
                text = second
                break

        replacements = (
            ("정말 힘들어서", "힘들었다"),
            ("너무 힘들어서", "힘들었다"),
            ("불편해서", "불편했다"),
            ("걱정돼서", "걱정됐다"),
            ("아쉬워서", "아쉬웠다"),
            ("번거로워서", "번거로웠다"),
            ("어려워서", "어려웠다"),
            ("부담스러워서", "부담스러웠다"),
        )

        for before, after in replacements:
            if text.endswith(before):
                text = text[: -len(before)] + after

        # Category-specific natural summaries for common raw review wording.
        lowered = text.lower()

        if category == "fan":
            if "더위" in lowered or "덥" in lowered:
                return "여름철 외출할 때 더위를 견디기 힘들었다"
            if "바람이 약" in lowered or "풍량이 약" in lowered:
                return "기존 휴대용 선풍기는 바람이 약해 충분히 시원하지 않았다"
            if "무겁" in lowered or "목이 아프" in lowered:
                return "오래 착용하면 무게가 부담될 수 있었다"
            if "소음" in lowered or "시끄럽" in lowered:
                return "가까이에서 사용할 때 소음이 신경 쓰일 수 있었다"
            if "배터리" in lowered or "충전" in lowered:
                return "사용 시간이 짧아 자주 충전해야 하는 점이 불편했다"

        if category == "carrier":
            if "크기" in lowered or "인치" in lowered:
                return "여행 목적에 맞는 캐리어 크기를 고르기 어려웠다"
            if "이동" in lowered or "바퀴" in lowered:
                return "짐이 많을 때 캐리어를 편하게 이동하기 어려웠다"
            if "수납" in lowered or "섞" in lowered:
                return "여행 짐을 나누어 깔끔하게 수납하기 어려웠다"

        if category == "cutting_board":
            if "미끄럽" in lowered:
                return "칼질할 때 도마가 미끄러워 불편했다"
            if "칼자국" in lowered or "냄새" in lowered:
                return "칼자국과 냄새가 남아 위생 관리가 걱정됐다"
            if "세척" in lowered:
                return "사용 후 세척과 관리가 번거로웠다"

        if category == "laundry":
            if "섞" in lowered or "분리" in lowered:
                return "빨래를 종류별로 나누어 보관하기 어려웠다"
            if "이동" in lowered or "바퀴" in lowered:
                return "쌓인 빨래를 세탁실까지 옮기기 불편했다"
            if "공간" in lowered or "정리" in lowered:
                return "세탁물이 쌓이면 공간이 쉽게 어수선해졌다"

        if category == "storage":
            if "찾기 어렵" in lowered:
                return "수납한 물건을 필요할 때 바로 찾기 어려웠다"
            if "공간" in lowered or "수납" in lowered:
                return "한정된 공간을 효율적으로 활용하기 어려웠다"
            if "정리" in lowered:
                return "물건이 섞여 깔끔하게 정리하기 어려웠다"

        if category == "slipper_rack":
            if "바닥" in lowered or "흩어" in lowered:
                return "욕실 슬리퍼가 바닥에 흩어져 정리가 불편했다"
            if "물기" in lowered or "건조" in lowered:
                return "젖은 슬리퍼의 물기와 위생 관리가 걱정됐다"
            if "접착" in lowered or "떨어" in lowered:
                return "거치대가 떨어질까 봐 고정력이 걱정됐다"

        if category == "tumbler":
            if "보온" in lowered or "보냉" in lowered:
                return "음료 온도가 오래 유지되지 않아 아쉬웠다"
            if "세척" in lowered:
                return "뚜껑과 내부를 깨끗하게 세척하기 번거로웠다"
            if "무겁" in lowered:
                return "음료를 담으면 무게가 부담될 수 있었다"

        # Keep a concise, review-grounded sentence for unknown products.
        text = re.sub(
            r"^(저는|제가|개인적으로|솔직히)\s*",
            "",
            text,
        )
        text = re.sub(
            r"\s+",
            " ",
            text,
        ).strip(" ,.")

        if len(text) > 65:
            text = text[:65].rstrip(" ,.")

        if text and not text.endswith(
            ("다", "요")
        ):
            text += " 불편했다"

        return text or "사용 중 불편한 점이 있었다"

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
            "version": "evidence-sentence-extractor-128-1",
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
            "성능",
            "효과",
            "바람",
            "시원",
            "배터리",
            "충전",
            "소음",
            "무게",
            "휴대",
            "각도",
            "탁상용",
            "핸디",
            "목걸이",
            "설치",
            "조립",
            "고정",
            "수납",
            "분리",
            "공간",
            "세척",
            "관리",
            "내구성",
            "디자인",
            "마감",
            "바퀴",
            "손잡이",
            "크기",
            "용량",
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
        evidence = self._clean_text(evidence_text)

        mappings = (
            (
                ("목걸이", "핸디", "탁상용", "각도 조절"),
                "여러 형태와 장소에서 다양하게 활용할 수 있다",
            ),
            (
                ("바람", "시원", "냉각", "풍량"),
                "성능과 사용 효과가 만족스럽다",
            ),
            (
                ("휴대", "외출", "들고 다니", "가볍"),
                "휴대하기 편하고 다양한 장소에서 사용할 수 있다",
            ),
            (
                ("분리", "수납", "지퍼", "포켓"),
                "구성과 공간을 효율적으로 활용할 수 있다",
            ),
            (
                ("바퀴", "손잡이", "이동"),
                "이동과 휴대가 편하다",
            ),
            (
                ("세척", "관리", "위생", "건조"),
                "세척과 관리가 편하다",
            ),
            (
                ("튼튼", "오래", "내구성", "견고"),
                "튼튼해서 오래 사용할 수 있다",
            ),
            (
                ("디자인", "색상", "세련", "마감"),
                "디자인과 마감이 만족스럽다",
            ),
        )

        for signals, label in mappings:
            if any(signal in evidence for signal in signals):
                return label

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

    def _category_from_context(
        self,
        product_name: str,
        reviews: List[Dict[str, Any]],
    ) -> str:
        product_text = self._clean_text(product_name).lower()
        review_text = " ".join(
            self._clean_text(item.get("text", "")).lower()
            for item in reviews
        )

        categories = (
            ("fan", ("선풍기", "목걸이형", "핸디팬", "손선풍기", "서큘레이터")),
            ("carrier", ("캐리어", "여행가방", "수하물", "기내용")),
            ("cutting_board", ("도마", "칼질", "항균도마")),
            ("laundry", ("빨래바구니", "세탁바구니", "런드리")),
            ("storage", ("정리함", "수납함", "서랍", "트롤리")),
            ("slipper_rack", ("슬리퍼 거치대", "슬리퍼걸이", "욕실 슬리퍼")),
            ("tumbler", ("텀블러", "보온병", "물병")),
        )

        for category, signals in categories:
            if any(signal in product_text for signal in signals):
                return category

        for category, signals in categories:
            match_count = sum(
                1 for signal in signals
                if signal in review_text
            )
            if match_count >= 2:
                return category

        return "general"

    def _review_based_pain(
        self,
        reviews: List[Dict[str, Any]],
    ) -> str:
        pain_signals = (
            "불편",
            "힘들",
            "아쉽",
            "걱정",
            "무겁",
            "시끄럽",
            "약하",
            "부족",
            "번거",
            "어렵",
            "짧",
            "뜨겁",
            "미끄럽",
        )

        for review in reviews:
            for sentence in self._split_sentences(
                review.get("text", "")
            ):
                if any(signal in sentence for signal in pain_signals):
                    return sentence.rstrip(".!?")

        return ""

    def _review_based_benefit(
        self,
        reviews: List[Dict[str, Any]],
    ) -> str:
        benefit_signals = (
            "편하",
            "좋",
            "만족",
            "시원",
            "가볍",
            "튼튼",
            "깔끔",
            "유용",
            "잘 되",
            "추천",
            "효과",
        )

        for review in reviews:
            for sentence in self._split_sentences(
                review.get("text", "")
            ):
                if any(signal in sentence for signal in benefit_signals):
                    return sentence.rstrip(".!?")

        return ""

    def _apply_pain_fallbacks(
        self,
        pain_points: List[Dict[str, Any]],
        benefits: List[Dict[str, Any]],
        reviews: List[Dict[str, Any]],
        product_name: str = "",
        pain_sentence_result: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        if pain_points:
            return pain_points

        pain_sentence_result = pain_sentence_result or {}
        best_pain_evidence = pain_sentence_result.get(
            "best_pain_evidence",
            {},
        )
        review_summary = self._clean_text(
            best_pain_evidence.get("summary", "")
        )

        if review_summary:
            item = self._inferred_item(
                review_summary,
                max(
                    4.8,
                    self._safe_float(
                        best_pain_evidence.get("pain_score"),
                        48.0,
                    ) / 10.0,
                ),
            )
            item["source"] = "review_pain_sentence"
            item["evidence"] = [
                {
                    "text": best_pain_evidence.get("text", ""),
                    "pain_score": best_pain_evidence.get("pain_score", 0),
                    "matched_signals": best_pain_evidence.get(
                        "matched_signals",
                        [],
                    ),
                }
            ]
            return [item]

        review_pain = self._review_based_pain(reviews)
        if review_pain:
            return [self._inferred_item(review_pain, 4.8)]

        category = self._category_from_context(
            product_name,
            reviews,
        )

        category_fallbacks = {
            "fan": (
                "더운 날 외출할 때 시원함을 유지하기 어렵다",
                "장시간 사용하면 무게나 소음이 부담될 수 있다",
            ),
            "carrier": (
                "여행 짐을 정리하고 이동하기 불편하다",
                "여행 목적에 맞는 크기와 수납 구성을 고르기 어렵다",
            ),
            "cutting_board": (
                "칼질할 때 도마가 미끄럽거나 관리가 번거로울 수 있다",
                "칼자국과 냄새가 남아 위생 관리가 걱정된다",
            ),
            "laundry": (
                "빨래를 종류별로 나누고 이동하기 불편하다",
                "세탁물이 쌓이면 공간이 쉽게 어수선해진다",
            ),
            "storage": (
                "물건을 분류하고 필요한 물건을 바로 찾기 어렵다",
                "수납공간을 효율적으로 활용하기 어렵다",
            ),
            "slipper_rack": (
                "슬리퍼가 바닥에 흩어져 정리가 불편하다",
                "물기와 위생 관리가 걱정된다",
            ),
            "tumbler": (
                "외출 중 음료의 온도를 오래 유지하기 어렵다",
                "세척과 휴대가 번거로울 수 있다",
            ),
            "general": (
                "기존 제품을 사용하면서 불편한 점이 있다",
                "사용 목적에 맞는 제품을 고르기 어렵다",
            ),
        }

        labels = category_fallbacks[category]
        return [
            self._inferred_item(labels[0], 3.8),
            self._inferred_item(labels[1], 3.2),
        ]

    def _apply_benefit_fallbacks(
        self,
        benefits: List[Dict[str, Any]],
        reviews: List[Dict[str, Any]],
        product_name: str = "",
    ) -> List[Dict[str, Any]]:
        if benefits:
            return benefits

        review_benefit = self._review_based_benefit(reviews)
        if review_benefit:
            return [self._inferred_item(review_benefit, 4.8)]

        category = self._category_from_context(
            product_name,
            reviews,
        )

        category_fallbacks = {
            "fan": (
                "휴대하기 편하고 필요한 곳에서 시원하게 사용할 수 있다",
                "목걸이형·핸디형·탁상용 등 여러 방식으로 활용할 수 있다",
            ),
            "carrier": (
                "짐을 깔끔하게 정리하고 편하게 이동할 수 있다",
                "여행 목적에 맞게 수납공간을 활용할 수 있다",
            ),
            "cutting_board": (
                "안정적으로 칼질하고 세척과 관리가 편하다",
                "주방에서 위생적으로 오래 사용할 수 있다",
            ),
            "laundry": (
                "빨래를 종류별로 나누고 편하게 이동할 수 있다",
                "세탁 공간을 깔끔하게 정리할 수 있다",
            ),
            "storage": (
                "물건을 분류해 깔끔하게 수납할 수 있다",
                "공간을 효율적으로 활용하고 필요한 물건을 쉽게 찾을 수 있다",
            ),
            "slipper_rack": (
                "슬리퍼를 깔끔하게 정리하고 건조할 수 있다",
                "욕실 공간을 효율적으로 활용할 수 있다",
            ),
            "tumbler": (
                "음료의 온도를 오래 유지하며 편하게 휴대할 수 있다",
                "일상과 외출에서 반복해서 활용하기 좋다",
            ),
            "general": (
                "사용 편의성과 활용성을 높일 수 있다",
                "일상에서 겪는 불편을 줄이는 데 도움이 된다",
            ),
        }

        labels = category_fallbacks[category]
        return [
            self._inferred_item(labels[0], 3.8),
            self._inferred_item(labels[1], 3.2),
        ]

    def _apply_buy_reason_fallbacks(
        self,
        buy_reasons: List[Dict[str, Any]],
        pain_points: List[Dict[str, Any]],
        benefits: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if buy_reasons:
            return buy_reasons

        labels = " ".join(
            item.get("label", "")
            for item in pain_points + benefits
        )

        reasons: List[Dict[str, Any]] = []

        mapping = (
            (("휴대", "이동", "외출"), "휴대와 이동이 편한 제품을 원해서"),
            (("정리", "수납", "공간"), "공간을 효율적으로 활용하기 위해"),
            (("세척", "관리", "위생"), "사용과 관리가 간편한 제품을 원해서"),
            (("성능", "효과", "시원"), "성능과 사용 효과가 좋은 제품을 원해서"),
            (("튼튼", "내구성", "고정"), "오래 사용할 수 있는 제품을 원해서"),
            (("디자인", "색상", "마감"), "디자인과 마감이 마음에 들어서"),
        )

        for signals, reason in mapping:
            if any(signal in labels for signal in signals):
                reasons.append(self._inferred_item(reason, 3.8))

        if not reasons:
            reasons.append(
                self._inferred_item(
                    "일상에서 겪는 불편을 줄이기 위해",
                    3.0,
                )
            )

        return reasons

    def _apply_persona_fallbacks(
        self,
        personas: List[Dict[str, Any]],
        pain_points: List[Dict[str, Any]],
        benefits: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if personas:
            return personas

        labels = " ".join(
            item.get("label", "")
            for item in pain_points + benefits
        )

        result: List[Dict[str, Any]] = []

        mapping = (
            (("휴대", "이동", "외출", "여행"), "외출과 이동이 잦은 사람"),
            (("정리", "수납", "공간"), "공간 활용과 정리를 중요하게 생각하는 사람"),
            (("세척", "관리", "위생"), "위생과 관리를 중요하게 생각하는 사람"),
            (("성능", "효과", "시원"), "제품 성능과 사용 효과를 중요하게 생각하는 사람"),
            (("튼튼", "내구성", "고정"), "내구성과 안정성을 중요하게 생각하는 사람"),
            (("디자인", "색상", "마감"), "디자인과 마감을 중요하게 생각하는 사람"),
        )

        for signals, persona in mapping:
            if any(signal in labels for signal in signals):
                result.append(self._inferred_item(persona, 3.8))

        if not result:
            result.append(
                self._inferred_item(
                    "제품의 편의성과 성능을 중요하게 생각하는 사람",
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
                    "기존 제품을 사용하면서 불편한 점이 있다",
                    3.0,
                )
            ],
            "benefits": [
                self._inferred_item(
                    "사용 편의성과 활용성을 높일 수 있다",
                    3.0,
                )
            ],
            "buy_reasons": [
                self._inferred_item(
                    "일상에서 겪는 불편을 줄이기 위해",
                    3.0,
                )
            ],
            "personas": [
                self._inferred_item(
                    "제품의 편의성과 성능을 중요하게 생각하는 사람",
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
                "version": "evidence-sentence-extractor-128-1",
                "sentence_count": 0,
                "best_evidence": {},
                "evidence_top5": [],
            },
            "pain_sentence_evidence": {
                "ok": False,
                "version": "pain-sentence-evidence-128-1",
                "category": "general",
                "candidate_count": 0,
                "best_pain_evidence": {},
                "pain_top5": [],
            },
            "best_pain_evidence": {},
            "pain_top3": [],
            "benefit_top3": [],
            "emotion_top3": [],
            "best_pain_point": "기존 제품을 사용하면서 불편한 점이 있다",
            "best_benefit": "사용 편의성과 활용성을 높일 수 있다",
            "best_buy_reason": "일상에서 겪는 불편을 줄이기 위해",
            "best_persona": "제품의 편의성과 성능을 중요하게 생각하는 사람",
            "best_quote": "",
            "best_evidence": {},
            "ranked_reviews": [],
            "content_angle": {
                "type": "problem_solution",
                "name": "문제 해결형",
                "reason": "리뷰가 없어 일반적인 문제 해결 구조를 사용합니다.",
            },
            "warnings": [
                "분석할 리뷰가 없어 일반 인사이트를 생성했습니다."
            ],
        }