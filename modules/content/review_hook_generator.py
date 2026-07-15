from __future__ import annotations

import re
from typing import Any, Dict, List


class ReviewHookGenerator:
    """
    Sprint75-1 Review Hook Rewriter

    역할:
    - ReviewInsight 결과를 쇼핑쇼츠용 한 문장 Hook으로 재작성
    - 긴 OCR 원문을 직접 사용하지 않고 핵심 장점만 요약
    - 상품명 정리
    - 외부 AI API 없이 규칙 기반으로 동작
    """

    VERSION = "review-hook-generator-75-1"

    def generate(
        self,
        review_quotes: Any = None,
        review_insight: Any = None,
        product_name: str = "",
        review_count: int = 0,
    ) -> Dict[str, Any]:
        quotes = review_quotes if isinstance(review_quotes, dict) else {}
        insight = review_insight if isinstance(review_insight, dict) else {}

        product_name = self._clean_product_name(
            product_name
        )

        best_pain = self._first_text(
            insight.get("best_pain_point"),
            insight.get("best_pain"),
            quotes.get("best_pain"),
        )

        best_benefit = self._first_text(
            insight.get("best_benefit"),
            insight.get("best_result"),
            quotes.get("best_benefit"),
        )

        best_quote = self._first_text(
            insight.get("best_quote"),
            quotes.get("best_quote"),
        )

        count = self._safe_int(
            review_count
            or insight.get("review_count")
            or quotes.get("review_count")
        )

        benefit_summary = self._summarize_benefit(
            best_benefit,
            best_quote,
        )

        pain_summary = self._summarize_pain(
            best_pain
        )

        hooks: List[Dict[str, Any]] = []

        if benefit_summary:
            hooks.append(
                self._hook(
                    "review_evidence",
                    self._review_evidence_hook(
                        count=count,
                        benefit=benefit_summary,
                    ),
                    score=98,
                    source="benefit_summary",
                )
            )

            hooks.append(
                self._hook(
                    "result",
                    f"의외로 만족도가 가장 높았던 건 {benefit_summary}이었습니다.",
                    score=95,
                    source="benefit_summary",
                )
            )

        if pain_summary:
            hooks.append(
                self._hook(
                    "problem_question",
                    f"{pain_summary}, 아직도 참고 계세요?",
                    score=92,
                    source="pain_summary",
                )
            )

        if product_name:
            hooks.append(
                self._hook(
                    "product_result",
                    f"{product_name}, 실제 후기를 보면 장점이 더 분명합니다.",
                    score=88,
                    source="product_name",
                )
            )

        if not hooks:
            hooks.append(
                self._hook(
                    "fallback",
                    f"{product_name or '이 제품'}, 왜 이제야 알았을까요?",
                    score=70,
                    source="fallback",
                )
            )

        hooks = self._dedupe_hooks(hooks)
        hooks.sort(
            key=lambda item: item.get("score", 0),
            reverse=True,
        )

        best_hook = hooks[0] if hooks else {}

        print(
            "[Sprint75-1 Hook] Version:",
            self.VERSION,
            flush=True,
        )
        print(
            "[Sprint75-1 Hook] Product:",
            product_name,
            flush=True,
        )
        print(
            "[Sprint75-1 Hook] Best Hook:",
            best_hook.get("text", ""),
            flush=True,
        )

        return {
            "ok": bool(best_hook),
            "version": self.VERSION,
            "status": "generated" if best_hook else "empty",
            "product_name": product_name,
            "review_count": count,
            "best_hook": best_hook.get("text", ""),
            "best_hook_type": best_hook.get("type", ""),
            "best_hook_score": best_hook.get("score", 0),
            "hooks": hooks,
            "source": {
                "best_pain": best_pain,
                "best_benefit": best_benefit,
                "best_quote": best_quote,
                "pain_summary": pain_summary,
                "benefit_summary": benefit_summary,
            },
        }

    def _review_evidence_hook(
        self,
        count: int,
        benefit: str,
    ) -> str:
        if count > 0:
            return (
                f"리뷰 {count}개를 분석했더니 "
                f"가장 많이 나온 장점은 {benefit}이었습니다."
            )

        return (
            f"실사용 후기를 분석했더니 "
            f"가장 많이 나온 장점은 {benefit}이었습니다."
        )

    def _summarize_benefit(
        self,
        benefit: str,
        quote: str,
    ) -> str:
        text = self._clean_text(
            f"{benefit} {quote}"
        )

        rules = (
            (
                ("분리 수납", "섞이지", "지퍼", "메쉬 포켓", "내부 공간"),
                "분리 수납",
            ),
            (
                ("가볍", "이동이 편", "끌기 편", "휴대"),
                "가벼운 이동",
            ),
            (
                ("튼튼", "내구성", "오래 쓸"),
                "튼튼한 내구성",
            ),
            (
                ("깔끔", "세련", "디자인", "예쁘"),
                "깔끔한 디자인",
            ),
            (
                ("수납", "넉넉", "공간"),
                "넉넉한 수납공간",
            ),
            (
                ("설치", "간편", "쉽게"),
                "간편한 설치",
            ),
            (
                ("접착", "고정", "떨어지지"),
                "튼튼한 고정력",
            ),
            (
                ("정리", "깔끔하게"),
                "깔끔한 정리",
            ),
        )

        for keywords, summary in rules:
            if any(
                keyword in text
                for keyword in keywords
            ):
                return summary

        cleaned = self._clean_label(benefit)

        return self._shorten(
            cleaned,
            20,
        )

    def _summarize_pain(
        self,
        pain: str,
    ) -> str:
        text = self._clean_text(pain)

        rules = (
            (
                ("여행 기간", "크기", "몇 인치"),
                "여행 기간에 맞는 크기 고르기",
            ),
            (
                ("짐", "섞", "정리"),
                "여행 짐 정리",
            ),
            (
                ("이동", "불편", "무거"),
                "무거운 짐 이동",
            ),
            (
                ("공간", "좁", "수납"),
                "부족한 수납공간",
            ),
            (
                ("바닥", "흩어", "정리"),
                "바닥에 흩어진 물건 정리",
            ),
        )

        for keywords, summary in rules:
            if any(
                keyword in text
                for keyword in keywords
            ):
                return summary

        return self._shorten(
            self._clean_label(text),
            24,
        )

    def _clean_label(
        self,
        text: str,
    ) -> str:
        text = self._clean_text(text)

        endings = (
            "할 수 있다",
            "수 있다",
            "어렵다",
            "불편하다",
            "좋다",
            "된다",
            "세련됐다",
        )

        for ending in endings:
            if text.endswith(ending):
                text = text[: -len(ending)].strip()

        return text.rstrip(".!? ")

    def _clean_product_name(
        self,
        value: Any,
    ) -> str:
        text = self._clean_text(value)

        if not text:
            return "이 제품"

        text = re.sub(
            r"(?i)(캐리어)\s*(\d{2})인치",
            r"\2인치 \1",
            text,
        )

        words = text.split()
        result: List[str] = []

        for word in words:
            normalized = re.sub(
                r"[^0-9A-Za-z가-힣]",
                "",
                word.lower(),
            )

            if not normalized:
                continue

            if any(
                re.sub(
                    r"[^0-9A-Za-z가-힣]",
                    "",
                    existing.lower(),
                ) == normalized
                for existing in result
            ):
                continue

            result.append(word)

        text = " ".join(result)

        if "24인치" in text and "기내용" in text:
            return "24인치 기내용 캐리어"

        if "20인치" in text and "기내용" in text:
            return "20인치 기내용 캐리어"

        return self._shorten(
            text,
            28,
        )

    def _hook(
        self,
        hook_type: str,
        text: str,
        score: int,
        source: str,
    ) -> Dict[str, Any]:
        cleaned = self._clean_text(text)
        cleaned = self._shorten(
            cleaned,
            76,
        )

        return {
            "type": hook_type,
            "text": cleaned,
            "score": int(score),
            "source": source,
            "length": len(cleaned),
        }

    def _first_text(
        self,
        *values: Any,
    ) -> str:
        for value in values:
            text = self._clean_text(value)

            if text:
                return text

        return ""

    def _clean_text(
        self,
        value: Any,
    ) -> str:
        if isinstance(value, dict):
            for key in (
                "text",
                "quote",
                "content",
                "value",
                "message",
            ):
                candidate = value.get(key)

                if candidate:
                    value = candidate
                    break
            else:
                value = ""

        text = str(value or "")
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"https?://\S+", " ", text)
        text = re.sub(r"[\r\n\t]+", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        return text.strip(" -_/|")

    def _shorten(
        self,
        text: str,
        limit: int,
    ) -> str:
        text = self._clean_text(text)

        if len(text) <= limit:
            return text

        return (
            text[:limit]
            .rstrip(" ,.;:!?\"'“”‘’")
            + "…"
        )

    def _safe_int(
        self,
        value: Any,
    ) -> int:
        try:
            return max(
                0,
                int(value or 0),
            )
        except Exception:
            return 0

    def _dedupe_hooks(
        self,
        hooks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        seen = set()

        for item in hooks:
            text = self._clean_text(
                item.get("text")
            )

            key = re.sub(
                r"[^0-9A-Za-z가-힣]",
                "",
                text.lower(),
            )

            if not key or key in seen:
                continue

            seen.add(key)
            result.append(item)

        return result


def generate_review_hooks(
    review_quotes: Any = None,
    review_insight: Any = None,
    product_name: str = "",
    review_count: int = 0,
) -> Dict[str, Any]:
    return ReviewHookGenerator().generate(
        review_quotes=review_quotes,
        review_insight=review_insight,
        product_name=product_name,
        review_count=review_count,
    )