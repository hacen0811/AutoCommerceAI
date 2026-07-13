from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Set


class ProductRelevanceEngine:
    """
    Sprint 59 Product Relevance Engine

    역할:
    - 프로젝트 상품명과 검색어를 기준으로 상품 핵심 토큰 생성
    - 후보 영상의 제목, 설명, 해시태그, OCR, 객체 분석 결과 비교
    - 텍스트 일치도와 Vision 분석 결과를 결합
    - 기존 후보 구조를 변경하지 않고 product_relevance만 추가

    출력 예시:
    {
        "score": 86,
        "grade": "high",
        "matched_keywords": ["청소", "브러쉬"],
        "title_match": True,
        "ocr_match": True,
        "visual_match": True,
        "text_score": 90,
        "vision_score": 75,
        "reason": "상품명 핵심어와 영상 제목·OCR가 일치합니다."
    }
    """

    ENGINE_VERSION = "product-relevance-engine-59-1"

    STOPWORDS = {
        "추천",
        "상품",
        "제품",
        "영상",
        "리뷰",
        "후기",
        "사용",
        "방법",
        "효과",
        "신상",
        "인기",
        "최고",
        "좋은",
        "생활",
        "용품",
        "쇼핑",
        "쇼츠",
        "틱톡",
        "도우인",
        "쿠팡",
        "파트너스",
        "video",
        "review",
        "product",
        "tiktok",
        "douyin",
        "best",
        "good",
        "new",
        "使用",
        "测评",
        "推荐",
        "好物",
        "视频",
        "教程",
        "效果",
        "开箱",
        "同款",
    }

    PRODUCT_VISUAL_WORDS = {
        "product",
        "item",
        "object",
        "상품",
        "제품",
        "물건",
        "도구",
        "기기",
        "용품",
    }

    HAND_VISUAL_WORDS = {
        "hand",
        "hands",
        "person",
        "손",
        "사람",
        "사용자",
    }

    DEMO_VISUAL_WORDS = {
        "demo",
        "using",
        "usage",
        "use",
        "action",
        "사용",
        "시연",
        "작동",
        "설치",
        "청소",
    }

    def analyze(
        self,
        candidate: Dict[str, Any],
        product_name: str = "",
        keyword: str = "",
        real_vision: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        candidate = candidate or {}
        real_vision = (
            real_vision
            or candidate.get("real_vision")
            or {}
        )

        source_tokens = self._build_source_tokens(
            product_name=product_name,
            keyword=keyword,
            candidate=candidate,
        )

        title_text = self._candidate_title_text(
            candidate
        )

        vision_text = self._vision_text(
            real_vision
        )

        title_matches = self._matched_tokens(
            source_tokens,
            title_text,
        )

        vision_matches = self._matched_tokens(
            source_tokens,
            vision_text,
        )

        title_score = self._token_match_score(
            source_tokens,
            title_matches,
        )

        vision_keyword_score = self._token_match_score(
            source_tokens,
            vision_matches,
        )

        visual_signals = self._visual_signals(
            real_vision
        )

        vision_score = min(
            vision_keyword_score * 0.65
            + visual_signals["score"] * 0.35,
            100,
        )

        has_vision = self._has_vision_data(
            real_vision
        )

        if has_vision:
            final_score = (
                title_score * 0.65
                + vision_score * 0.35
            )
        else:
            final_score = title_score

        matched_keywords = self._unique(
            title_matches + vision_matches
        )

        title_match = bool(title_matches)
        ocr_match = bool(
            self._matched_tokens(
                source_tokens,
                self._ocr_text(real_vision),
            )
        )

        visual_match = bool(
            visual_signals["product_visible"]
            or visual_signals["usage_visible"]
        )

        score = round(
            min(max(final_score, 0), 100),
            1,
        )

        return {
            "version": self.ENGINE_VERSION,
            "score": score,
            "grade": self._grade(score),
            "matched_keywords": matched_keywords,
            "source_keywords": source_tokens,
            "title_match": title_match,
            "ocr_match": ocr_match,
            "visual_match": visual_match,
            "product_visible": visual_signals[
                "product_visible"
            ],
            "hand_visible": visual_signals[
                "hand_visible"
            ],
            "usage_visible": visual_signals[
                "usage_visible"
            ],
            "text_score": round(title_score, 1),
            "vision_score": round(vision_score, 1),
            "reason": self._reason(
                score=score,
                title_match=title_match,
                ocr_match=ocr_match,
                visual_match=visual_match,
                matched_keywords=matched_keywords,
                has_vision=has_vision,
            ),
        }

    def apply(
        self,
        candidate: Dict[str, Any],
        product_name: str = "",
        keyword: str = "",
        real_vision: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        item = dict(candidate or {})

        item["product_relevance"] = self.analyze(
            candidate=item,
            product_name=product_name,
            keyword=keyword,
            real_vision=real_vision,
        )

        return item

    def _build_source_tokens(
        self,
        product_name: str,
        keyword: str,
        candidate: Dict[str, Any],
    ) -> List[str]:
        candidate_keyword = (
            candidate.get("keyword")
            or candidate.get("search_query")
            or candidate.get("query")
            or ""
        )

        text = " ".join(
            [
                str(product_name or ""),
                str(keyword or ""),
                str(candidate_keyword or ""),
            ]
        )

        return self._tokens(text)

    def _candidate_title_text(
        self,
        candidate: Dict[str, Any],
    ) -> str:
        values = [
            candidate.get("title"),
            candidate.get("description"),
            candidate.get("purpose"),
            candidate.get("raw_text"),
            candidate.get("caption"),
            candidate.get("hashtags"),
            candidate.get("note"),
        ]

        return self._normalize_text(
            " ".join(
                self._flatten_text(values)
            )
        )

    def _vision_text(
        self,
        real_vision: Dict[str, Any],
    ) -> str:
        values: List[Any] = [
            real_vision.get("summary"),
            real_vision.get("video_ai"),
            real_vision.get("vision_ai"),
            real_vision.get("yolo"),
            real_vision.get("paddleocr"),
            real_vision.get("object_ai"),
            real_vision.get("smart_cut"),
        ]

        return self._normalize_text(
            " ".join(
                self._flatten_text(values)
            )
        )

    def _ocr_text(
        self,
        real_vision: Dict[str, Any],
    ) -> str:
        values = [
            real_vision.get("paddleocr"),
            real_vision.get("vision_ai"),
        ]

        return self._normalize_text(
            " ".join(
                self._flatten_text(values)
            )
        )

    def _visual_signals(
        self,
        real_vision: Dict[str, Any],
    ) -> Dict[str, Any]:
        text = self._vision_text(
            real_vision
        )

        product_visible = self._contains_any(
            text,
            self.PRODUCT_VISUAL_WORDS,
        )

        hand_visible = self._contains_any(
            text,
            self.HAND_VISUAL_WORDS,
        )

        usage_visible = self._contains_any(
            text,
            self.DEMO_VISUAL_WORDS,
        )

        status = real_vision.get("status") or {}

        yolo_ok = bool(
            isinstance(status, dict)
            and status.get("yolo")
        )

        object_ok = bool(
            isinstance(status, dict)
            and status.get("object_fallback")
        )

        score = 0.0

        if product_visible:
            score += 45

        if hand_visible:
            score += 20

        if usage_visible:
            score += 25

        if yolo_ok or object_ok:
            score += 10

        return {
            "score": min(score, 100),
            "product_visible": product_visible,
            "hand_visible": hand_visible,
            "usage_visible": usage_visible,
        }

    def _matched_tokens(
        self,
        source_tokens: List[str],
        target_text: str,
    ) -> List[str]:
        normalized_target = self._normalize_text(
            target_text
        )

        return [
            token
            for token in source_tokens
            if token and token in normalized_target
        ]

    def _token_match_score(
        self,
        source_tokens: List[str],
        matched_tokens: List[str],
    ) -> float:
        if not source_tokens:
            return 0.0

        matched_count = len(
            set(matched_tokens)
        )

        ratio = matched_count / len(
            set(source_tokens)
        )

        if ratio >= 0.80:
            return 100.0

        if ratio >= 0.60:
            return 90.0

        if ratio >= 0.40:
            return 78.0

        if ratio >= 0.25:
            return 65.0

        if matched_count >= 1:
            return 52.0

        return 0.0

    def _tokens(
        self,
        value: Any,
    ) -> List[str]:
        normalized = self._normalize_text(
            value
        )

        raw_tokens = re.findall(
            r"[가-힣]{2,}|[a-z0-9]{2,}|[\u3400-\u9fff]{2,}",
            normalized,
        )

        tokens: List[str] = []
        seen: Set[str] = set()

        for token in raw_tokens:
            token = token.strip()

            if not token:
                continue

            if token in self.STOPWORDS:
                continue

            if token in seen:
                continue

            seen.add(token)
            tokens.append(token)

        if not tokens:
            for token in raw_tokens:
                if token in seen:
                    continue

                seen.add(token)
                tokens.append(token)

        return tokens

    def _flatten_text(
        self,
        values: Iterable[Any],
    ) -> List[str]:
        output: List[str] = []

        for value in values:
            if value is None:
                continue

            if isinstance(value, dict):
                output.extend(
                    self._flatten_text(
                        value.values()
                    )
                )
                continue

            if isinstance(value, (list, tuple, set)):
                output.extend(
                    self._flatten_text(
                        value
                    )
                )
                continue

            text = str(value).strip()

            if text:
                output.append(text)

        return output

    def _normalize_text(
        self,
        value: Any,
    ) -> str:
        text = str(
            value or ""
        ).lower()

        text = text.replace(
            "#",
            " ",
        )

        text = re.sub(
            r"[^0-9a-z가-힣\u3400-\u9fff]+",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    def _contains_any(
        self,
        text: str,
        words: Set[str],
    ) -> bool:
        return any(
            word in text
            for word in words
        )

    def _has_vision_data(
        self,
        real_vision: Dict[str, Any],
    ) -> bool:
        if not isinstance(real_vision, dict):
            return False

        if real_vision.get("ok"):
            return True

        return any(
            bool(real_vision.get(key))
            for key in [
                "summary",
                "video_ai",
                "vision_ai",
                "yolo",
                "paddleocr",
                "object_ai",
            ]
        )

    def _grade(
        self,
        score: float,
    ) -> str:
        if score >= 85:
            return "very_high"

        if score >= 70:
            return "high"

        if score >= 50:
            return "medium"

        if score >= 30:
            return "low"

        return "very_low"

    def _reason(
        self,
        score: float,
        title_match: bool,
        ocr_match: bool,
        visual_match: bool,
        matched_keywords: List[str],
        has_vision: bool,
    ) -> str:
        keyword_text = ", ".join(
            matched_keywords[:5]
        )

        if score >= 85:
            if keyword_text:
                return (
                    "상품 핵심어와 영상 제목·분석 결과가 "
                    f"높게 일치합니다: {keyword_text}"
                )

            return (
                "영상의 상품 노출과 사용 장면이 "
                "높은 수준으로 확인됩니다."
            )

        if score >= 70:
            return (
                "상품 핵심어 또는 영상 사용 장면이 "
                "비교적 잘 일치합니다."
            )

        if title_match or ocr_match:
            return (
                "상품 관련 텍스트는 확인되지만 "
                "시각적 일치 여부를 추가 확인해야 합니다."
            )

        if visual_match:
            return (
                "상품 또는 사용 장면은 감지됐지만 "
                "상품명 직접 일치는 확인되지 않았습니다."
            )

        if not has_vision:
            return (
                "Real Vision 결과가 없어 제목과 검색어만으로 "
                "상품 일치도를 계산했습니다."
            )

        return (
            "상품명·검색어와 영상 분석 결과의 "
            "직접 일치도가 낮습니다."
        )

    def _unique(
        self,
        values: List[str],
    ) -> List[str]:
        result: List[str] = []
        seen: Set[str] = set()

        for value in values:
            if not value or value in seen:
                continue

            seen.add(value)
            result.append(value)

        return result