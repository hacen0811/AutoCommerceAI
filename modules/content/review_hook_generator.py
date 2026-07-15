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

    VERSION = "review-hook-generator-76-3"

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

        best_evidence = self._first_text(
            insight.get("best_evidence"),
            quotes.get("best_evidence"),
            best_quote,
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

        evidence_summary = self._summarize_evidence(
            best_evidence,
            benefit_summary,
        )

        pain_summary = self._summarize_pain(
            best_pain
        )

        hooks: List[Dict[str, Any]] = []

        hook_candidates = [
            (
                "problem",
                f"{pain_summary}, 아직도 고민하고 계세요?",
                "pain_summary",
            ),
            (
                "review_evidence",
                self._review_evidence_hook(
                    count=count,
                    evidence=evidence_summary,
                ),
                "best_evidence",
            ),
            (
                "curiosity",
                self._curiosity_hook(
                    benefit_summary
                ),
                "benefit_summary",
            ),
            (
                "result",
                self._result_hook(
                    product_name=product_name,
                    benefit=benefit_summary,
                ),
                "benefit_summary",
            ),
            (
                "before_after",
                self._before_after_hook(
                    pain=pain_summary,
                    benefit=benefit_summary,
                ),
                "pain_and_benefit",
            ),
        ]

        for hook_type, hook_text_value, source in hook_candidates:
            viral_score = self._viral_score(
                hook_type=hook_type,
                text=hook_text_value,
                count=count,
                benefit=benefit_summary,
                pain=pain_summary,
            )

            hooks.append(
                self._hook(
                    hook_type,
                    hook_text_value,
                    score=viral_score,
                    source=source,
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
        type_priority = {
            "review_evidence": 6,
            "curiosity": 5,
            "before_after": 3,
            "problem": 2,
            "result": 1,
        }

        hooks.sort(
            key=lambda item: (
                item.get("score", 0),
                type_priority.get(
                    item.get("type", ""),
                    0,
                ),
                -item.get("length", 0),
            ),
            reverse=True,
        )

        best_hook = hooks[0] if hooks else {}

        print(
            "[Sprint76-3 Hook] Version:",
            self.VERSION,
            flush=True,
        )
        print(
            "[Sprint76-3 Hook] Product:",
            product_name,
            flush=True,
        )
        print(
            "[Sprint76-3 Hook] Best Hook:",
            best_hook.get("text", ""),
            flush=True,
        )

        print(
            "[Sprint76-3 Hook] Generated:",
            len(hooks),
            flush=True,
        )

        for item in hooks:
            print(
                "[Sprint76-3 Hook] Score:",
                item.get("type"),
                item.get("score"),
                repr(item.get("text", "")),
                flush=True,
            )

        print(
            "[Sprint76-3 Hook] Selected:",
            best_hook.get("type", ""),
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
            "top_hooks": hooks[:3],
            "hook_scores": {
                item.get("type", ""): item.get("score", 0)
                for item in hooks
            },
            "source": {
                "best_pain": best_pain,
                "best_benefit": best_benefit,
                "best_quote": best_quote,
                "best_evidence": best_evidence,
                "pain_summary": pain_summary,
                "benefit_summary": benefit_summary,
                "evidence_summary": evidence_summary,
            },
        }

    def _review_evidence_hook(
        self,
        count: int,
        evidence: str,
    ) -> str:
        quote = self._quote_style_evidence(evidence)

        if count > 0:
            return (
                f"실제 구매 후기 {count}개에서 가장 많이 나온 말은 "
                f'"{quote}"였습니다.'
            )

        return (
            f"실제 구매 후기에서 가장 많이 나온 말은 "
            f'"{quote}"였습니다.'
        )

    def _curiosity_hook(
        self,
        benefit: str,
    ) -> str:
        if benefit == "깔끔한 디자인":
            return "예뻐서 산 줄 알았는데, 만족한 이유는 따로 있었습니다."

        return (
            f"의외로 가장 만족도가 높았던 건 "
            f"{benefit}이었습니다."
        )

    def _result_hook(
        self,
        product_name: str,
        benefit: str,
    ) -> str:
        if "캐리어" in product_name:
            return (
                f"캐리어 하나 바꿨는데 "
                f"여행 준비가 훨씬 편해졌습니다."
            )

        return (
            f"{product_name} 하나 바꿨는데 "
            f"{benefit}이 확실히 달라졌습니다."
        )

    def _before_after_hook(
        self,
        pain: str,
        benefit: str,
    ) -> str:
        return (
            f"예전에는 {pain}가 고민이었는데, "
            f"지금은 {benefit}으로 훨씬 편해졌습니다."
        )

    def _viral_score(
        self,
        hook_type: str,
        text: str,
        count: int,
        benefit: str,
        pain: str,
    ) -> int:
        cleaned = self._clean_text(text)
        score = 52

        length = len(cleaned)

        if 26 <= length <= 50:
            score += 14
        elif 20 <= length <= 64:
            score += 10
        elif length <= 76:
            score += 5
        else:
            score -= 6

        if count > 0 and str(count) in cleaned:
            score += 7

        curiosity_words = (
            "의외로",
            "따로",
            "가장",
            "왜",
        )

        if any(
            word in cleaned
            for word in curiosity_words
        ):
            score += 9

        if benefit and benefit in cleaned:
            score += 7

        if pain and pain in cleaned:
            score += 4

        type_bonus = {
            "review_evidence": 28,
            "curiosity": 12,
            "before_after": 8,
            "problem": 6,
            "result": 5,
        }

        score += type_bonus.get(
            hook_type,
            0,
        )

        if cleaned.endswith("?"):
            score += 2

        # 과장·중복 가능성이 높은 긴 문장은 감점
        if cleaned.count("가장") > 1:
            score -= 3

        if len(cleaned) > 68:
            score -= 4

        return max(
            0,
            min(
                99,
                int(score),
            ),
        )

    def _summarize_evidence(
        self,
        evidence: str,
        fallback_benefit: str,
    ) -> str:
        text = self._clean_text(evidence)

        if not text:
            return f"{fallback_benefit}이 만족스럽다"

        text = re.sub(r"\b3\s*박\s*4\s*일\b", "3박 4일", text)
        text = re.sub(r"\b(\d{2})\s*인치\b", r"\1인치", text)

        if (
            "3박 4일" in text
            and "24인치" in text
            and any(word in text for word in ("적당", "딱", "알맞"))
        ):
            return "3박 4일 여행에는 24인치가 딱 적당하다"

        if (
            "2박 3일" in text
            and "20인치" in text
            and any(word in text for word in ("적당", "딱", "알맞"))
        ):
            return "2박 3일 여행에는 20인치가 딱 적당하다"

        replacements = (
            ("정도의", ""),
            ("인 것 같네요", "다"),
            ("인 것 같아요", "다"),
            ("것 같네요", "다"),
            ("것 같아요", "다"),
            ("했습니다", "했다"),
            ("좋았습니다", "좋다"),
        )

        for before, after in replacements:
            text = text.replace(before, after)

        text = re.sub(r"\s+", " ", text).strip()
        text = text.rstrip(".!? ")

        return self._shorten(text, 38).rstrip("…")

    def _evidence_clause(
        self,
        evidence: str,
    ) -> str:
        text = self._clean_text(evidence).rstrip(".!? ")

        if not text:
            return "실사용 만족도가 높다는"

        if text.endswith("하다"):
            return text[:-2] + "하다는"
        if text.endswith("이다"):
            return text[:-2] + "이라는"
        if text.endswith("다"):
            return text[:-1] + "다는"

        return text + "라는"

    def _quote_style_evidence(
        self,
        evidence: str,
    ) -> str:
        text = self._clean_text(evidence).rstrip(".!? ")

        replacements = (
            ("딱 적당하다", "딱 적당해요"),
            ("적당하다", "적당해요"),
            ("편하다", "편해요"),
            ("좋다", "좋아요"),
            ("만족스럽다", "만족스러워요"),
            ("튼튼하다", "튼튼해요"),
            ("가볍다", "가벼워요"),
        )

        for before, after in replacements:
            if text.endswith(before):
                text = text[: -len(before)] + after
                break

        if not text.endswith(("요", "니다", "죠")):
            if text.endswith("다"):
                text = text[:-1] + "요"

        return self._shorten(text, 40).rstrip("…")

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