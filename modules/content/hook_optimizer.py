from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List


class HookOptimizer:
    VERSION = "hook-optimizer-95-5"

    TYPE_ALIASES = {
        "reviewevidence": "review_evidence",
        "review_evidence": "review_evidence",
        "review": "review_evidence",
        "evidence": "review_evidence",
        "curiosity": "curiosity",
        "question": "curiosity",
        "psychology": "psychology",
        "problem": "problem",
        "pain": "problem",
        "beforeafter": "before_after",
        "before_after": "before_after",
        "result": "result",
        "benefit": "result",
        "fallback": "fallback",
        "unknown": "unknown",
    }

    TYPE_PRIORITY = {
        "review_evidence": 6,
        "curiosity": 5,
        "psychology": 4,
        "problem": 3,
        "before_after": 2,
        "result": 1,
        "fallback": 0,
        "unknown": 0,
    }

    def apply_to_review_hooks(
        self,
        review_hooks: Any = None,
        review_insight: Any = None,
        product_name: str = "",
        review_count: int = 0,
    ) -> Dict[str, Any]:
        hooks = dict(review_hooks) if isinstance(review_hooks, dict) else {}
        insight = review_insight if isinstance(review_insight, dict) else {}

        candidates = hooks.get("hooks", [])
        if not isinstance(candidates, list):
            candidates = []

        ranking: List[Dict[str, Any]] = []
        rejected_count = 0

        for item in candidates:
            if not isinstance(item, dict):
                rejected_count += 1
                continue

            text = self._clean(item.get("text"))
            hook_type = self._normalize_type(item.get("type") or "unknown")

            if not text or self._is_broken_text(text):
                rejected_count += 1
                continue

            if self._is_meta_review_text(text):
                rejected_count += 1
                continue

            score = self._score(
                text=text,
                hook_type=hook_type,
                product_name=product_name,
                review_count=review_count,
                evidence=insight.get("best_evidence"),
                pain=(
                    insight.get("best_pain_point")
                    or insight.get("best_pain")
                ),
                benefit=insight.get("best_benefit"),
                source_score=item.get("score"),
            )

            ranking.append(
                {
                    "rank": 0,
                    "type": hook_type,
                    "text": text,
                    "score": score,
                    "source_score": self._safe_float(item.get("score")),
                    "length": len(text),
                    "quality_ok": score >= 60.0,
                }
            )

        fallback_text = self._clean(hooks.get("best_hook"))
        fallback_type = self._normalize_type(
            hooks.get("best_hook_type", "fallback")
        )

        if (
            not ranking
            and fallback_text
            and not self._is_broken_text(fallback_text)
        ):
            fallback_score = self._score(
                text=fallback_text,
                hook_type=fallback_type,
                product_name=product_name,
                review_count=review_count,
                evidence=insight.get("best_evidence"),
                pain=(
                    insight.get("best_pain_point")
                    or insight.get("best_pain")
                ),
                benefit=insight.get("best_benefit"),
                source_score=hooks.get("best_hook_score"),
            )

            ranking.append(
                {
                    "rank": 1,
                    "type": fallback_type,
                    "text": fallback_text,
                    "score": fallback_score,
                    "source_score": self._safe_float(
                        hooks.get("best_hook_score")
                    ),
                    "length": len(fallback_text),
                    "quality_ok": fallback_score >= 60.0,
                    "generated_fallback": False,
                }
            )

        if not ranking:
            generated_text = self._build_safe_fallback(
                product_name=product_name,
                review_count=review_count,
            )
            generated_score = self._score(
                text=generated_text,
                hook_type="review_evidence",
                product_name=product_name,
                review_count=review_count,
                evidence="",
                pain="",
                benefit="",
                source_score=0,
            )
            ranking.append(
                {
                    "rank": 1,
                    "type": "review_evidence",
                    "text": generated_text,
                    "score": generated_score,
                    "source_score": 0.0,
                    "length": len(generated_text),
                    "quality_ok": generated_score >= 60.0,
                    "generated_fallback": True,
                }
            )

        ranking.sort(
            key=lambda x: (
                x.get("score", 0),
                self.TYPE_PRIORITY.get(x.get("type", ""), 0),
                -x.get("length", 0),
            ),
            reverse=True,
        )

        for index, item in enumerate(ranking, start=1):
            item["rank"] = index

        for item in ranking:
            original_text = self._clean(item.get("text"))
            naturalized_text = self._naturalize_hook(
                text=original_text,
                hook_type=item.get("type", ""),
                product_name=product_name,
                pain=(
                    insight.get("best_pain_point")
                    or insight.get("best_pain")
                ),
                benefit=insight.get("best_benefit"),
            )
            item["original_text"] = original_text
            item["text"] = naturalized_text
            item["length"] = len(naturalized_text)
            item["naturalized"] = naturalized_text != original_text

        best = ranking[0] if ranking else {}

        result = {
            "ok": bool(best),
            "ready": bool(best),
            "version": self.VERSION,
            "status": "optimized" if best else "empty",
            "best_hook": best.get("text", ""),
            "best_hook_type": best.get("type", ""),
            "best_hook_score": best.get("score", 0),
            "candidate_count": len(ranking),
            "rejected_count": rejected_count,
            "ranking": ranking,
            "top_hooks": ranking[:3],
            "quality_ok": bool(best) and best.get("score", 0) >= 60.0,
            "semantic_filter": "product_relevance",
        }

        print(
            "[Sprint95-5 Hook Optimizer] Version:",
            self.VERSION,
            flush=True,
        )
        print(
            "[Sprint95-5 Hook Optimizer] Candidates:",
            len(ranking),
            flush=True,
        )
        print(
            "[Sprint95-5 Hook Optimizer] Rejected:",
            rejected_count,
            flush=True,
        )
        print(
            "[Sprint95-5 Hook Optimizer] Best Score:",
            best.get("score", 0),
            flush=True,
        )
        print(
            "[Sprint95-5 Hook Optimizer] Best Type:",
            best.get("type", ""),
            flush=True,
        )
        print(
            "[Sprint95-5 Hook Optimizer] Selected:",
            best.get("text", ""),
            flush=True,
        )

        if best:
            hooks["original_best_hook"] = hooks.get("best_hook", "")
            hooks["original_best_hook_type"] = hooks.get(
                "best_hook_type",
                "",
            )
            hooks["original_best_hook_score"] = hooks.get(
                "best_hook_score",
                0,
            )
            hooks["best_hook"] = best.get("text", "")
            hooks["best_hook_type"] = best.get("type", "")
            hooks["best_hook_score"] = best.get("score", 0)
            hooks["optimized"] = True

        hooks["hook_optimizer"] = result
        return hooks

    def _naturalize_hook(
        self,
        text: Any,
        hook_type: Any = "",
        product_name: Any = "",
        pain: Any = "",
        benefit: Any = "",
    ) -> str:
        original = self._clean(text)
        if not original:
            return original

        normalized = self._remove_awkward_comma_sentence(original)
        normalized = self._replace_cliche_ending(
            text=normalized,
            hook_type=hook_type,
            product_name=product_name,
            pain=pain,
            benefit=benefit,
        )
        normalized = self._remove_repeated_phrase(normalized)
        normalized = self._normalize_question_punctuation(normalized)

        if self._is_broken_text(normalized):
            return original

        return normalized or original

    def _remove_awkward_comma_sentence(self, text: str) -> str:
        normalized = self._clean(text)

        comma_patterns = (
            r"^(.+?)[,，]\s*아직도\s+고민하고\s+계세요\?$",
            r"^(.+?)[,，]\s*아직도\s+고민되세요\?$",
            r"^(.+?)[,，]\s*계속\s+고민하고\s+계세요\?$",
            r"^(.+?)[,，]\s*고민하고\s+계신가요\?$",
        )

        for pattern in comma_patterns:
            match = re.match(pattern, normalized)
            if match:
                problem = self._to_natural_condition(match.group(1))
                return f"{problem} 이유가 뭘까요?"

        normalized = re.sub(r"\s*[,，]\s*", ", ", normalized)

        if (
            normalized.count(",") == 1
            and normalized.endswith("?")
        ):
            left, right = [
                part.strip()
                for part in normalized.split(",", 1)
            ]
            if self._is_cliche_question(right):
                condition = self._to_natural_condition(left)
                return f"{condition} 이유가 뭘까요?"

        return normalized

    def _replace_cliche_ending(
        self,
        text: str,
        hook_type: Any,
        product_name: Any,
        pain: Any,
        benefit: Any,
    ) -> str:
        normalized = self._clean(text)

        cliche_patterns = (
            r"(?:,\s*)?아직도\s+고민하고\s+계세요\?$",
            r"(?:,\s*)?아직도\s+고민되세요\?$",
            r"(?:,\s*)?아직도\s+사용하고\s+계세요\?$",
            r"(?:,\s*)?아직도\s+모르셨나요\?$",
            r"(?:,\s*)?알고\s+계셨나요\?$",
            r"(?:,\s*)?혹시\s+이런\s+경험\s+있으세요\?$",
            r"(?:,\s*)?꼭\s+보세요[.!]?$",
            r"(?:,\s*)?놓치지\s+마세요[.!]?$",
        )

        for pattern in cliche_patterns:
            if re.search(pattern, normalized):
                stem = re.sub(pattern, "", normalized).strip(" ,.!?")
                return self._build_natural_question(
                    stem=stem,
                    hook_type=hook_type,
                    product_name=product_name,
                    pain=pain,
                    benefit=benefit,
                )

        return normalized

    def _build_natural_question(
        self,
        stem: Any,
        hook_type: Any,
        product_name: Any,
        pain: Any,
        benefit: Any,
    ) -> str:
        base = self._clean(stem)
        pain_text = self._clean(pain)
        benefit_text = self._clean(benefit)
        name = self._clean(product_name)
        normalized_type = self._normalize_type(hook_type)

        if base:
            condition = self._to_natural_condition(base)
            if normalized_type in {"problem", "before_after"}:
                return f"{condition} 이유가 뭘까요?"
            if normalized_type in {"curiosity", "psychology"}:
                return f"{condition} 무엇이 달라질까요?"
            if normalized_type == "review_evidence":
                return f"{condition} 실제 후기는 어땠을까요?"
            return f"{condition} 어떻게 바꿀 수 있을까요?"

        if pain_text:
            condition = self._to_natural_condition(pain_text)
            return f"{condition} 어떻게 해결할 수 있을까요?"

        if benefit_text:
            subject = self._strip_sentence_ending(benefit_text)
            return f"{subject}, 실제로 얼마나 달라질까요?"

        if name and not self._is_broken_text(name):
            return f"{name}, 구매 전에 무엇부터 확인해야 할까요?"

        return "구매 전에 무엇부터 확인해야 할까요?"

    def _to_natural_condition(self, text: Any) -> str:
        phrase = self._strip_sentence_ending(self._clean(text))
        phrase = phrase.strip(" ,.!?")

        replacements = (
            (r"해\s*보인다$", "해 보이는"),
            (r"해보인다$", "해 보이는"),
            (r"보인다$", "보이는"),
            (r"불편하다$", "불편한"),
            (r"어렵다$", "어려운"),
            (r"복잡하다$", "복잡한"),
            (r"부족하다$", "부족한"),
            (r"지저분하다$", "지저분한"),
            (r"귀찮다$", "귀찮은"),
            (r"걱정된다$", "걱정되는"),
            (r"고민된다$", "고민되는"),
            (r"필요하다$", "필요한"),
            (r"좋다$", "좋은"),
            (r"나쁘다$", "나쁜"),
            (r"크다$", "큰"),
            (r"작다$", "작은"),
            (r"많다$", "많은"),
            (r"적다$", "적은"),
        )

        for pattern, replacement in replacements:
            if re.search(pattern, phrase):
                phrase = re.sub(pattern, replacement, phrase)
                break

        if phrase.endswith(("한", "는", "은", "운", "인", "된", "보이는")):
            return phrase

        if phrase.endswith("다"):
            phrase = phrase[:-1]

        return phrase

    def _remove_repeated_phrase(self, text: str) -> str:
        normalized = self._clean(text)

        normalized = re.sub(
            r"\b가장\s+많이\s+나온\s+(?:후기|리뷰)(?:는|가)?\s+가장\s+",
            "후기에서 가장 ",
            normalized,
        )
        normalized = re.sub(
            r"\b(후기|리뷰)\s+(후기|리뷰)\b",
            r"\1",
            normalized,
        )
        normalized = re.sub(
            r"\b(가장)\s+\1\b",
            r"\1",
            normalized,
        )

        return normalized

    def _normalize_question_punctuation(self, text: str) -> str:
        normalized = self._clean(text)
        normalized = re.sub(r"\?{2,}", "?", normalized)
        normalized = re.sub(r"\s+([?.!,])", r"\1", normalized)
        normalized = re.sub(r"([?.!,])\1+", r"\1", normalized)
        return normalized.strip()

    def _is_cliche_question(self, text: Any) -> bool:
        normalized = self._clean(text)
        return any(
            pattern in normalized
            for pattern in (
                "아직도 고민하고 계세요",
                "아직도 고민되세요",
                "계속 고민하고 계세요",
                "고민하고 계신가요",
                "아직도 사용하고 계세요",
                "아직도 모르셨나요",
                "알고 계셨나요",
                "혹시 이런 경험 있으세요",
                "꼭 보세요",
                "놓치지 마세요",
            )
        )

    def _strip_sentence_ending(self, text: Any) -> str:
        normalized = self._clean(text).strip(" ,.!?")
        normalized = re.sub(
            r"(?:입니다|이에요|예요|합니다|됩니다|있습니다|없습니다)$",
            "",
            normalized,
        )
        return normalized.strip()

    def _score(
        self,
        text: str,
        hook_type: str,
        product_name: Any,
        review_count: Any,
        evidence: Any,
        pain: Any,
        benefit: Any,
        source_score: Any,
    ) -> float:
        score = 0.0
        length = len(text)

        if 18 <= length <= 42:
            score += 28
        elif 12 <= length <= 55:
            score += 23
        elif length <= 70:
            score += 15
        else:
            score += 6

        count = self._safe_int(review_count)
        if count and str(count) in text:
            score += 10

        if any(
            word in text
            for word in ("후기", "리뷰", "구매자", "실제", "사용자")
        ):
            score += 9

        if hook_type == "review_evidence":
            score += 8

        if text.endswith("?"):
            score += 6

        if any(
            word in text
            for word in (
                "왜",
                "무엇",
                "어떤",
                "의외로",
                "이것",
                "가장",
                "정말",
                "결국",
            )
        ):
            score += 8

        if hook_type in {"curiosity", "psychology"}:
            score += 5

        if any(
            word in text
            for word in (
                "고민",
                "불편",
                "후회",
                "걱정",
                "어렵",
                "복잡",
                "정리",
                "찾기",
                "수납",
                "공간",
                "내구성",
                "크기",
                "무게",
                "이동",
                "사용",
                "편리",
            )
        ):
            score += 10

        if hook_type in {"problem", "before_after"}:
            score += 4

        product_tokens = [
            token
            for token in self._clean(product_name).split()
            if len(token) >= 2
        ]
        if any(token in text for token in product_tokens):
            score += 8

        evidence_overlap = self._keyword_overlap(
            text,
            evidence,
            limit=10,
        )
        pain_overlap = self._keyword_overlap(
            text,
            pain,
            limit=8,
        )
        benefit_overlap = self._keyword_overlap(
            text,
            benefit,
            limit=8,
        )

        score += min(8, evidence_overlap * 2)
        score += min(6, pain_overlap * 2)
        score += min(4, benefit_overlap * 2)

        if text.count(",") <= 1:
            score += 4

        if len(text.split()) <= 12:
            score += 4

        source = self._safe_float(source_score)
        score += min(8.0, max(0.0, source / 12.5))

        if length > 70:
            score -= 12
        elif length < 10:
            score -= 12

        if text.count("가장") > 1:
            score -= 4

        if any(
            word in text
            for word in ("무조건", "100%", "완벽", "기적", "역대급")
        ):
            score -= 8

        if self._is_meta_review_text(text):
            score -= 45

        if self._has_awkward_period_expression(text):
            score -= 12

        if self._has_repetition(text):
            score -= 7

        if self._is_broken_text(text):
            score -= 40

        return round(max(0.0, min(100.0, score)), 1)

    def _normalize_type(self, value: Any) -> str:
        text = self._clean(value).lower()
        text = unicodedata.normalize("NFKC", text)
        compact = re.sub(r"[^a-z0-9_]+", "", text)
        compact = compact.replace("__", "_")

        if compact in self.TYPE_ALIASES:
            return self.TYPE_ALIASES[compact]

        no_underscore = compact.replace("_", "")
        if no_underscore in self.TYPE_ALIASES:
            return self.TYPE_ALIASES[no_underscore]

        return "unknown"

    def _keyword_overlap(
        self,
        text: str,
        value: Any,
        limit: int,
    ) -> int:
        source = self._clean(value)
        if not source:
            return 0

        keywords = re.findall(
            r"[0-9A-Za-z가-힣]{2,}",
            source,
        )

        unique: List[str] = []
        for keyword in keywords:
            if keyword not in unique:
                unique.append(keyword)

        return sum(
            1
            for keyword in unique[:limit]
            if keyword in text
        )

    def _is_broken_text(self, text: str) -> bool:
        if not text:
            return True

        replacement_count = text.count("�")
        question_marks = text.count("?")
        korean_chars = len(re.findall(r"[가-힣]", text))
        ascii_chars = len(re.findall(r"[A-Za-z0-9]", text))

        mojibake_chars = len(
            re.findall(
                r"[媛쒕遺꾩꽍덈뜑紐⑤뱺臾쇨굔援щℓ吏곹썑꾧린瑜곗딄퀬理쒖냼二ъ슜蹂꾨씪媛롮븯듬땲由щ럭]",
                text,
            )
        )

        hanja_like = len(
            re.findall(r"[一-龥]", text)
        )

        if replacement_count > 0:
            return True

        if mojibake_chars >= 2:
            return True

        if hanja_like >= 2 and korean_chars < 8:
            return True

        if question_marks >= 2 and korean_chars < max(4, ascii_chars // 2):
            return True

        if question_marks >= 4:
            return True

        return False

    def _build_safe_fallback(
        self,
        product_name: Any,
        review_count: Any,
    ) -> str:
        name = self._clean(product_name)
        count = self._safe_int(review_count)

        if not name or self._is_broken_text(name):
            name = "이 제품"

        if count > 0:
            return (
                f"{name} 후기 {count}개에서 가장 많이 나온 "
                "선택 기준은 무엇일까요?"
            )

        return f"{name}, 구매 전에 가장 먼저 확인할 점은 무엇일까요?"

    def _is_meta_review_text(self, text: str) -> bool:
        normalized = self._clean(text)

        meta_patterns = (
            "구매 직후 후기를",
            "구매 직후 리뷰를",
            "후기를 쓰지 않고",
            "리뷰를 쓰지 않고",
            "사용해 본 후 후기를",
            "사용해 본 뒤 후기를",
            "사용 후 후기를",
            "리뷰 작성",
            "후기 작성",
            "체험단",
            "배송 후기",
            "포장 후기",
        )

        if any(pattern in normalized for pattern in meta_patterns):
            return True

        has_review_word = any(
            word in normalized
            for word in ("후기", "리뷰")
        )
        has_writing_word = any(
            word in normalized
            for word in ("쓰다", "썼", "작성", "남기")
        )
        has_timing_word = any(
            word in normalized
            for word in ("구매 직후", "며칠 후", "몇 주 후", "한 달 후")
        )

        return has_review_word and has_writing_word and has_timing_word

    def _has_awkward_period_expression(self, text: str) -> bool:
        normalized = self._clean(text)

        awkward_patterns = (
            r"\d+주\s+\d+달",
            r"최소\s*\d+주\s*\d+달",
            r"\d+주\s*\d+개월",
        )

        return any(
            re.search(pattern, normalized)
            for pattern in awkward_patterns
        )

    def _has_repetition(self, text: str) -> bool:
        tokens = re.findall(
            r"[0-9A-Za-z가-힣]{2,}",
            text,
        )
        if len(tokens) < 4:
            return False

        return len(tokens) - len(set(tokens)) >= 2

    def _clean(self, value: Any) -> str:
        text = str(value or "")
        text = unicodedata.normalize("NFKC", text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"https?://\S+", " ", text)
        text = re.sub(r"[\r\n\t]+", " ", text)
        text = re.sub(r"\s+", " ", text)

        spacing_fixes = {
            "모든물건": "모든 물건",
            "구매직후": "구매 직후",
            "사용해본": "사용해 본",
            "써본": "써 본",
            "후기를쓰": "후기를 쓰",
            "리뷰를쓰": "리뷰를 쓰",
            "한달": "한 달",
            "두달": "두 달",
            "세달": "세 달",
        }
        for wrong, correct in spacing_fixes.items():
            text = text.replace(wrong, correct)

        text = re.sub(
            r"(\d+)주\s+(\d+)달",
            r"\1주에서 \2달",
            text,
        )
        return text.strip()

    def _safe_int(self, value: Any) -> int:
        try:
            return max(0, int(value or 0))
        except Exception:
            return 0

    def _safe_float(self, value: Any) -> float:
        try:
            return float(value or 0)
        except Exception:
            return 0.0


def optimize_review_hooks(
    review_hooks: Any = None,
    review_insight: Any = None,
    product_name: str = "",
    review_count: int = 0,
) -> Dict[str, Any]:
    return HookOptimizer().apply_to_review_hooks(
        review_hooks=review_hooks,
        review_insight=review_insight,
        product_name=product_name,
        review_count=review_count,
    )