from __future__ import annotations

import re
from typing import Any, Dict, List


class ReviewScriptGenerator:
    """
    Sprint75-1 Review Script Rewriter

    역할:
    - Hook / Pain / Benefit / Evidence를 자연스러운 쇼핑쇼츠 대본으로 재작성
    - 긴 OCR 원문을 그대로 사용하지 않고 핵심 의미만 요약
    - 상품명 정리
    - 외부 AI API 없이 규칙 기반으로 동작
    """

    VERSION = "review-script-generator-76-3"

    def generate(
        self,
        review_hooks: Any = None,
        review_quotes: Any = None,
        review_insight: Any = None,
        product_name: str = "",
        review_count: int = 0,
    ) -> Dict[str, Any]:
        hooks = review_hooks if isinstance(review_hooks, dict) else {}
        quotes = review_quotes if isinstance(review_quotes, dict) else {}
        insight = review_insight if isinstance(review_insight, dict) else {}

        product_name = self._clean_product_name(
            product_name
        )

        count = self._safe_int(
            review_count
            or hooks.get("review_count")
            or insight.get("review_count")
            or quotes.get("review_count")
        )

        best_hook = self._first_text(
            hooks.get("best_hook"),
            self._extract_hook_text(hooks),
        )

        best_pain = self._first_text(
            insight.get("best_pain_point"),
            insight.get("best_pain"),
            quotes.get("best_pain"),
            self._source_value(hooks, "best_pain"),
        )

        best_benefit = self._first_text(
            insight.get("best_benefit"),
            insight.get("best_result"),
            quotes.get("best_benefit"),
            self._source_value(hooks, "best_benefit"),
        )

        best_quote = self._first_text(
            insight.get("best_quote"),
            quotes.get("best_quote"),
            self._source_value(hooks, "best_quote"),
        )

        best_evidence = self._first_text(
            insight.get("best_evidence"),
            quotes.get("best_evidence"),
            self._source_value(hooks, "best_evidence"),
            best_quote,
        )

        pain_summary = self._summarize_pain(
            best_pain
        )

        benefit_summary = self._summarize_benefit(
            best_benefit,
            best_quote,
        )

        evidence_summary = self._summarize_evidence(
            best_evidence,
            benefit_summary,
        )

        best_hook_type = self._first_text(
            hooks.get("best_hook_type"),
            self._extract_hook_type(hooks),
        )

        if not best_hook:
            best_hook = self._make_hook(
                count=count,
                evidence=evidence_summary,
            )

        short_script = self._build_short_script(
            product_name=product_name,
            best_hook=best_hook,
            benefit_summary=benefit_summary,
            evidence_summary=evidence_summary,
            review_count=count,
        )

        medium_script = self._build_medium_script(
            hook_type=best_hook_type,
            product_name=product_name,
            best_hook=best_hook,
            pain_summary=pain_summary,
            benefit_summary=benefit_summary,
            evidence_summary=evidence_summary,
            review_count=count,
        )

        long_script = self._build_long_script(
            product_name=product_name,
            best_hook=best_hook,
            pain_summary=pain_summary,
            benefit_summary=benefit_summary,
            evidence_summary=evidence_summary,
            review_count=count,
        )

        scripts = [
            short_script,
            medium_script,
            long_script,
        ]

        scripts = [
            script
            for script in scripts
            if script.get("text")
        ]

        scripts = self._dedupe_scripts(
            scripts
        )

        scripts.sort(
            key=lambda item: (
                item.get("score", 0),
                -abs(
                    item.get("target_seconds", 20)
                    - 20
                ),
            ),
            reverse=True,
        )

        best_script = (
            medium_script
            if medium_script.get("text")
            else (
                scripts[0]
                if scripts
                else {}
            )
        )

        platform_recommendations = {
            "tiktok": "short",
            "instagram_reels": "medium",
            "youtube_shorts": "long",
        }

        print(
            "[Sprint76-3 Script] Version:",
            self.VERSION,
            flush=True,
        )
        print(
            "[Sprint76-3 Script] Product:",
            product_name,
            flush=True,
        )
        print(
            "[Sprint76-3 Script] Hook Type:",
            best_hook_type,
            flush=True,
        )
        print(
            "[Sprint76-3 Script] Short:",
            short_script.get("estimated_seconds", 0),
            "s",
            "error=",
            short_script.get("duration_error", 0),
            "status=",
            short_script.get("duration_status", ""),
            "compressed=",
            short_script.get("compression_applied", False),
            "expanded=",
            short_script.get("expansion_applied", False),
            flush=True,
        )
        print(
            "[Sprint76-3 Script] Medium:",
            medium_script.get("estimated_seconds", 0),
            "s",
            "error=",
            medium_script.get("duration_error", 0),
            "status=",
            medium_script.get("duration_status", ""),
            "compressed=",
            medium_script.get("compression_applied", False),
            "expanded=",
            medium_script.get("expansion_applied", False),
            flush=True,
        )
        print(
            "[Sprint76-3 Script] Long:",
            long_script.get("estimated_seconds", 0),
            "s",
            "error=",
            long_script.get("duration_error", 0),
            "status=",
            long_script.get("duration_status", ""),
            "compressed=",
            long_script.get("compression_applied", False),
            "expanded=",
            long_script.get("expansion_applied", False),
            flush=True,
        )
        print(
            "[Sprint76-3 Script] Selected:",
            "medium",
            flush=True,
        )
        print(
            "[Sprint76-3 Script] Best Script:",
            best_script.get("text", ""),
            flush=True,
        )

        return {
            "ok": bool(best_script),
            "version": self.VERSION,
            "status": "generated" if best_script else "empty",
            "product_name": product_name,
            "review_count": count,
            "best_hook": best_hook,
            "best_hook_type": best_hook_type,
            "best_script": best_script.get("text", ""),
            "best_script_type": best_script.get("type", ""),
            "best_script_score": best_script.get("score", 0),
            "short_script": short_script.get("text", ""),
            "medium_script": medium_script.get("text", ""),
            "long_script": long_script.get("text", ""),
            "short_script_data": short_script,
            "medium_script_data": medium_script,
            "long_script_data": long_script,
            "platform_recommendations": platform_recommendations,
            "best_script_sections": best_script.get(
                "sections",
                {},
            ),
            "best_script_lines": best_script.get(
                "lines",
                [],
            ),
            "estimated_seconds": best_script.get(
                "estimated_seconds",
                0,
            ),
            "scripts": scripts,
            "script_count": len(scripts),
            "source": {
                "best_pain": best_pain,
                "best_benefit": best_benefit,
                "best_quote": best_quote,
                "best_evidence": best_evidence,
                "pain_summary": pain_summary,
                "benefit_summary": benefit_summary,
                "evidence_summary": evidence_summary,
                "reason_summary": self._reason_sentence(
                    product_name=product_name,
                    evidence_summary=evidence_summary,
                    benefit_summary=benefit_summary,
                ),
            },
        }

    def _build_short_script(
        self,
        product_name: str,
        best_hook: str,
        benefit_summary: str,
        evidence_summary: str,
        review_count: int,
    ) -> Dict[str, Any]:
        sections = {
            "hook": self._sentence(
                self._shorten(
                    best_hook,
                    78,
                )
            ),
            "reason": self._sentence(
                self._reason_sentence(
                    product_name=product_name,
                    evidence_summary=evidence_summary,
                    benefit_summary=benefit_summary,
                )
            ),
            "cta": self._sentence(
                self._short_cta(
                    product_name
                )
            ),
        }

        script = self._script(
            script_type="short_15s",
            sections=sections,
            score=96,
            source="review_quote_short",
            target_seconds=15,
        )

        return self._fit_duration(
            script,
            min_seconds=14,
            max_seconds=17,
        )

    def _build_medium_script(
        self,
        hook_type: str,
        product_name: str,
        best_hook: str,
        pain_summary: str,
        benefit_summary: str,
        evidence_summary: str,
        review_count: int,
    ) -> Dict[str, Any]:
        sections = {
            "hook": self._sentence(
                self._shorten(
                    best_hook,
                    90,
                )
            ),
            "reason": self._sentence(
                self._reason_sentence(
                    product_name=product_name,
                    evidence_summary=evidence_summary,
                    benefit_summary=benefit_summary,
                )
            ),
            "benefit": self._sentence(
                self._benefit_sentence(
                    product_name=product_name,
                    benefit_summary=benefit_summary,
                )
            ),
            "cta": self._sentence(
                self._product_cta(
                    product_name
                )
            ),
        }

        script = self._script(
            script_type="medium_20s",
            sections=sections,
            score=100,
            source="review_quote_reason_benefit_medium",
            target_seconds=20,
        )

        return self._fit_duration(
            script,
            min_seconds=19,
            max_seconds=23,
        )

    def _build_long_script(
        self,
        product_name: str,
        best_hook: str,
        pain_summary: str,
        benefit_summary: str,
        evidence_summary: str,
        review_count: int,
    ) -> Dict[str, Any]:
        sections = {
            "hook": self._sentence(
                self._shorten(
                    best_hook,
                    96,
                )
            ),
            "empathy": self._sentence(
                f"여행 기간에 맞는 크기를 고를 때 {pain_summary} 때문에 고민하게 됩니다"
            ),
            "reason": self._sentence(
                self._reason_sentence(
                    product_name=product_name,
                    evidence_summary=evidence_summary,
                    benefit_summary=benefit_summary,
                )
            ),
            "benefit": self._sentence(
                self._benefit_sentence(
                    product_name=product_name,
                    benefit_summary=benefit_summary,
                )
            ),
            "recommendation": self._sentence(
                self._recommendation_sentence(
                    product_name=product_name,
                    evidence_summary=evidence_summary,
                )
            ),
            "cta": self._sentence(
                self._product_cta(
                    product_name
                )
            ),
        }

        script = self._script(
            script_type="long_30s",
            sections=sections,
            score=94,
            source="review_quote_reason_benefit_long",
            target_seconds=30,
        )

        return self._fit_duration(
            script,
            min_seconds=28,
            max_seconds=33,
        )

    def _reason_sentence(
        self,
        product_name: str,
        evidence_summary: str,
        benefit_summary: str,
    ) -> str:
        evidence = self._clean_text(evidence_summary)
        product = self._clean_text(product_name)

        if (
            "3박 4일" in evidence
            and "24인치" in evidence
        ):
            return (
                "가장 큰 이유는 수납은 넉넉하면서도 "
                "이동할 때 부담이 적기 때문입니다"
            )

        if (
            "2박 3일" in evidence
            and "20인치" in evidence
        ):
            return (
                "필요한 짐은 충분히 담으면서도 "
                "가볍게 이동하기 좋기 때문입니다"
            )

        if "캐리어" in product:
            if "수납" in benefit_summary:
                return (
                    "필요한 짐을 넉넉히 담으면서도 "
                    "정리와 이동이 편하기 때문입니다"
                )
            return "여행 짐을 담고 이동하기 편하기 때문입니다"

        if "슬리퍼" in product:
            return "바닥 공간을 덜 차지하면서 깔끔하게 정리할 수 있기 때문입니다"

        if "텀블러" in product:
            return "휴대하기 편하면서 원하는 온도를 오래 유지하기 때문입니다"

        return f"{benefit_summary}을 실제 사용에서 체감하기 때문입니다"

    def _benefit_sentence(
        self,
        product_name: str,
        benefit_summary: str,
    ) -> str:
        product = self._clean_text(product_name)

        if "캐리어" in product:
            return (
                f"{benefit_summary} 덕분에 "
                "여행 준비와 이동이 편해집니다"
            )

        return f"{benefit_summary} 덕분에 일상에서 사용하기가 훨씬 편해집니다"

    def _recommendation_sentence(
        self,
        product_name: str,
        evidence_summary: str,
    ) -> str:
        evidence = self._clean_text(evidence_summary)
        product = self._clean_text(product_name)

        if (
            "3박 4일" in evidence
            and "24인치" in evidence
        ):
            return "그래서 3박 4일 여행용으로 많이 추천되고 있습니다"

        if (
            "2박 3일" in evidence
            and "20인치" in evidence
        ):
            return "그래서 2박 3일 짧은 여행용으로 잘 맞습니다"

        if "캐리어" in product:
            return "그래서 여행 기간과 짐의 양을 기준으로 선택하기 좋습니다"

        return "그래서 실제 사용 목적에 맞는지 확인하고 선택하는 것이 좋습니다"

    def _compress_evidence(
        self,
        evidence: str,
    ) -> str:
        text = self._clean_text(evidence)

        replacements = (
            (
                "짐이 섞이지 않아 정리하기 편하다",
                "짐 정리가 편하다",
            ),
            (
                "가볍고 이동이 편하다",
                "이동이 편하다",
            ),
            (
                "튼튼해서 오래 사용할 수 있다",
                "튼튼하고 오래 쓴다",
            ),
        )

        for before, after in replacements:
            if before in text:
                return after

        return self._shorten(
            text,
            24,
        ).rstrip("…")

    def _short_cta(
        self,
        product_name: str,
    ) -> str:
        if "캐리어" in product_name:
            return "여행 전에 후기를 확인해 보세요"

        return "구매 전에 후기를 확인해 보세요"

    def _fit_duration(
        self,
        script: Dict[str, Any],
        min_seconds: int,
        max_seconds: int,
    ) -> Dict[str, Any]:
        sections = dict(
            script.get("sections", {})
        )

        compression_applied = False

        priority_order = (
            "result",
            "transition",
            "solution",
            "empathy",
            "evidence",
            "recommendation",
        )

        while (
            script.get("estimated_seconds", 0)
            > max_seconds
            and len(sections) > 3
        ):
            removed = False

            for key in priority_order:
                if key in sections:
                    sections.pop(key)
                    removed = True
                    compression_applied = True
                    break

            if not removed:
                break

            script = self._script(
                script_type=script.get("type", ""),
                sections=sections,
                score=script.get("score", 0),
                source=script.get("source", ""),
                target_seconds=script.get(
                    "target_seconds",
                    max_seconds,
                ),
            )

        if (
            script.get("estimated_seconds", 0)
            > max_seconds
        ):
            sections = {
                key: self._shorten(
                    value,
                    46 if key == "hook" else 40,
                )
                for key, value in sections.items()
            }

            compression_applied = True

            script = self._script(
                script_type=script.get("type", ""),
                sections=sections,
                score=script.get("score", 0),
                source=script.get("source", ""),
                target_seconds=script.get(
                    "target_seconds",
                    max_seconds,
                ),
            )

        estimated = script.get(
            "estimated_seconds",
            0,
        )

        target = script.get(
            "target_seconds",
            0,
        )

        expansion_applied = False

        if estimated < min_seconds:
            # Short처럼 1~3초만 부족한 경우에는 새 문장을 추가하지 않고
            # 기존 CTA를 조금만 확장해 목표 시간을 맞춥니다.
            shortage = min_seconds - estimated

            if (
                shortage <= 3
                and "cta" in sections
            ):
                cta_text = self._clean_text(
                    sections.get("cta", "")
                ).rstrip(".!?")

                suffix = (
                    " 수납 구성도 함께 보세요"
                    if shortage >= 2
                    else " 꼭 확인해 보세요"
                )

                if (
                    suffix.strip() not in cta_text
                    and not (
                        "꼭" in cta_text
                        and "확인해 보세요" in suffix
                    )
                ):
                    sections["cta"] = self._sentence(
                        cta_text + suffix
                    )

                    expansion_applied = True

                    script = self._script(
                        script_type=script.get("type", ""),
                        sections=sections,
                        score=script.get("score", 0),
                        source=script.get("source", ""),
                        target_seconds=target,
                    )

                    estimated = script.get(
                        "estimated_seconds",
                        0,
                    )

            expansion_candidates = (
                (
                    "support",
                    "실사용 후기를 기준으로 선택하면 실패를 줄일 수 있습니다.",
                ),
                (
                    "detail",
                    "수납 구조와 이동 편의성도 함께 확인해 보세요.",
                ),
                (
                    "trust",
                    "구매 전 실제 사용 후기를 비교하는 것이 좋습니다.",
                ),
            )

            for key, sentence in expansion_candidates:
                if estimated >= min_seconds:
                    break

                if key in sections:
                    continue

                sections[key] = self._sentence(
                    sentence
                )

                expansion_applied = True

                script = self._script(
                    script_type=script.get("type", ""),
                    sections=sections,
                    score=script.get("score", 0),
                    source=script.get("source", ""),
                    target_seconds=target,
                )

                estimated = script.get(
                    "estimated_seconds",
                    0,
                )

        if estimated > max_seconds:
            optional_keys = (
                "trust",
                "detail",
                "support",
            )

            for key in optional_keys:
                if estimated <= max_seconds:
                    break

                if key not in sections:
                    continue

                sections.pop(key)

                script = self._script(
                    script_type=script.get("type", ""),
                    sections=sections,
                    score=script.get("score", 0),
                    source=script.get("source", ""),
                    target_seconds=target,
                )

                estimated = script.get(
                    "estimated_seconds",
                    0,
                )

        script["duration_error"] = (
            estimated - target
        )

        script["duration_status"] = (
            "ok"
            if min_seconds <= estimated <= max_seconds
            else "out_of_range"
        )

        script["compression_applied"] = (
            compression_applied
        )

        script["expansion_applied"] = (
            expansion_applied
        )

        return script

    def _build_adaptive_script(
        self,
        hook_type: str,
        product_name: str,
        best_hook: str,
        pain_summary: str,
        benefit_summary: str,
        evidence_summary: str,
        review_count: int,
    ) -> Dict[str, Any]:
        hook = self._sentence(
            self._shorten(
                best_hook,
                76,
            )
        )

        evidence = self._sentence(
            self._evidence_line(
                review_count=review_count,
                evidence=evidence_summary,
            )
        )

        benefit = self._sentence(
            f"{benefit_summary} 덕분에 여행 준비와 짐 정리가 훨씬 편해집니다"
        )

        cta = self._sentence(
            self._product_cta(
                product_name
            )
        )

        if hook_type == "curiosity":
            sections = {
                "hook": hook,
                "reveal": self._sentence(
                    f"실제로 가장 많이 언급된 부분은 {benefit_summary}이었습니다"
                ),
                "evidence": evidence,
                "result": benefit,
                "cta": cta,
            }
            score = 100

        elif hook_type == "problem":
            sections = {
                "hook": hook,
                "solution": self._sentence(
                    f"{self._with_object_particle(product_name)} 사용하면 짐을 나눠 담기 편합니다"
                ),
                "evidence": evidence,
                "result": benefit,
                "cta": cta,
            }
            score = 98

        elif hook_type == "before_after":
            sections = {
                "hook": hook,
                "before": self._sentence(
                    f"사용 전에는 {pain_summary}가 가장 불편했습니다"
                ),
                "after": self._sentence(
                    f"사용 후에는 {benefit_summary}이 가능해졌습니다"
                ),
                "evidence": evidence,
                "cta": cta,
            }
            score = 97

        elif hook_type == "result":
            sections = {
                "hook": hook,
                "reason": self._sentence(
                    f"핵심은 {benefit_summary}입니다"
                ),
                "evidence": evidence,
                "result": benefit,
                "cta": cta,
            }
            score = 96

        else:
            sections = {
                "hook": hook,
                "evidence": evidence,
                "result": benefit,
                "cta": cta,
            }
            score = 99

        return self._script(
            script_type=f"adaptive_{hook_type or 'evidence'}",
            sections=sections,
            score=score,
            source="selected_viral_hook",
        )

    def _product_cta(
        self,
        product_name: str,
    ) -> str:
        if "캐리어" in product_name:
            return "여행 전에 후기와 수납 구성을 꼭 비교해 보세요"

        if "슬리퍼" in product_name:
            return "욕실 정리가 고민이라면 한번 확인해 보세요"

        if "텀블러" in product_name:
            return "보냉력과 사용 후기를 함께 확인해 보세요"

        return (
            f"{self._with_object_particle(product_name)} "
            f"찾고 있다면 후기부터 확인해 보세요"
        )

    def _build_review_evidence_script(
        self,
        product_name: str,
        best_hook: str,
        pain_summary: str,
        benefit_summary: str,
        evidence_summary: str,
        review_count: int,
    ) -> Dict[str, Any]:
        hook = self._sentence(
            self._shorten(
                best_hook,
                76,
            )
        )

        problem = self._sentence(
            f"여행할 때마다 {self._with_subject_particle(pain_summary)} 고민되셨나요?"
        )

        solution = self._sentence(
            f"{self._with_object_particle(product_name)} 확인해 보세요"
        )

        evidence = self._sentence(
            self._evidence_line(
                review_count=review_count,
                evidence=evidence_summary,
            )
        )

        benefit = self._sentence(
            f"{benefit_summary} 덕분에 여행 준비가 훨씬 편해집니다"
        )

        cta = self._sentence(
            f"{self._with_object_particle(product_name)} 찾고 있다면 한번 비교해 보세요"
        )

        return self._script(
            script_type="review_evidence",
            sections={
                "hook": hook,
                "problem": problem,
                "solution": solution,
                "evidence": evidence,
                "benefit": benefit,
                "cta": cta,
            },
            score=98,
            source="rewritten_review_evidence",
        )

    def _build_problem_solution_script(
        self,
        product_name: str,
        pain_summary: str,
        benefit_summary: str,
        evidence_summary: str,
        review_count: int,
    ) -> Dict[str, Any]:
        hook = self._sentence(
            f"{pain_summary}, 아직도 고민하고 계세요?"
        )

        transition = self._sentence(
            "방법은 생각보다 간단합니다"
        )

        solution = self._sentence(
            f"{self._with_instrument_particle(product_name)} 짐을 나눠 담아 보세요"
        )

        benefit = self._sentence(
            f"{benefit_summary}이 가능해져 이동과 정리가 편해집니다"
        )

        evidence = self._sentence(
            self._evidence_line(
                review_count=review_count,
                evidence=evidence_summary,
            )
        )

        cta = self._sentence(
            f"여행용 캐리어를 고르고 있다면 한번 확인해 보세요"
        )

        return self._script(
            script_type="problem_solution",
            sections={
                "hook": hook,
                "transition": transition,
                "solution": solution,
                "benefit": benefit,
                "evidence": evidence,
                "cta": cta,
            },
            score=95,
            source="rewritten_problem_solution",
        )

    def _build_before_after_script(
        self,
        product_name: str,
        pain_summary: str,
        benefit_summary: str,
        review_count: int,
    ) -> Dict[str, Any]:
        hook = self._sentence(
            f"{product_name} 하나 바꿨는데 여행 준비가 달라졌습니다"
        )

        before = self._sentence(
            f"사용 전에는 {pain_summary}가 가장 불편했습니다"
        )

        action = self._sentence(
            f"그런데 {self._with_object_particle(product_name)} 사용한 뒤"
        )

        after = self._sentence(
            f"{benefit_summary}이 가능해져 짐 정리가 훨씬 쉬워졌습니다"
        )

        reaction = self._sentence(
            (
                f"리뷰 {review_count}개에서도 비슷한 만족 반응이 확인됐습니다"
                if review_count > 0
                else "실사용 후기에서도 비슷한 만족 반응이 확인됐습니다"
            )
        )

        cta = self._sentence(
            "여행 전 캐리어를 고르고 있다면 한번 비교해 보세요"
        )

        return self._script(
            script_type="before_after",
            sections={
                "hook": hook,
                "before": before,
                "action": action,
                "after": after,
                "reaction": reaction,
                "cta": cta,
            },
            score=92,
            source="rewritten_before_after",
        )

    def _make_hook(
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

    def _evidence_line(
        self,
        review_count: int,
        evidence: str,
    ) -> str:
        return self._shared_evidence_sentence(
            review_count=review_count,
            evidence=evidence,
            prefix="실제 구매자들의 후기를 보면",
        )

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
                ("가볍", "이동이 편", "끌기 편"),
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
                "넉넉한 수납",
            ),
        )

        for keywords, summary in rules:
            if any(
                keyword in text
                for keyword in keywords
            ):
                return summary

        return "편리한 수납"

    def _summarize_pain(
        self,
        pain: str,
    ) -> str:
        text = self._clean_text(pain)

        rules = (
            (
                ("여행 기간", "크기", "몇 인치"),
                "여행 기간에 맞는 크기 선택",
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
                ("공간", "수납"),
                "부족한 수납공간",
            ),
        )

        for keywords, summary in rules:
            if any(
                keyword in text
                for keyword in keywords
            ):
                return summary

        return "여행 짐 정리"

    def _summarize_evidence(
        self,
        quote: str,
        benefit: str,
    ) -> str:
        text = self._clean_text(quote)

        if not text:
            return f"{benefit}이 만족스럽다"

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

        if any(keyword in text for keyword in ("섞이지", "분리", "지퍼", "메쉬 포켓")):
            return "짐이 섞이지 않아 정리하기 편하다"

        if any(keyword in text for keyword in ("가볍", "이동", "끌기")):
            return "가볍고 이동이 편하다"

        if any(keyword in text for keyword in ("튼튼", "오래", "내구성")):
            return "튼튼해서 오래 사용할 수 있다"

        replacements = (
            ("정도의", ""),
            ("인 것 같네요", "다"),
            ("인 것 같아요", "다"),
            ("것 같네요", "다"),
            ("것 같아요", "다"),
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

    def _shared_evidence_sentence(
        self,
        review_count: int,
        evidence: str,
        prefix: str = "",
    ) -> str:
        clause = self._evidence_clause(evidence)

        if prefix:
            return f"{prefix}, {clause} 의견이 가장 많았습니다"

        if review_count > 0:
            return (
                f"리뷰 {review_count}개를 분석했더니 "
                f"{clause} 후기가 가장 많았습니다"
            )

        return (
            f"실사용 후기를 분석했더니 "
            f"{clause} 후기가 가장 많았습니다"
        )

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

        if "24인치" in text and "기내용" in text:
            return "24인치 기내용 캐리어"

        if "20인치" in text and "기내용" in text:
            return "20인치 기내용 캐리어"

        words = text.split()
        result: List[str] = []
        seen = set()

        for word in words:
            key = re.sub(
                r"[^0-9A-Za-z가-힣]",
                "",
                word.lower(),
            )

            if not key or key in seen:
                continue

            seen.add(key)
            result.append(word)

        return self._shorten(
            " ".join(result),
            28,
        )

    def _script(
        self,
        script_type: str,
        sections: Dict[str, str],
        score: int,
        source: str,
        target_seconds: int = 20,
    ) -> Dict[str, Any]:
        clean_sections = {
            key: self._clean_text(value)
            for key, value in sections.items()
            if self._clean_text(value)
        }

        lines = list(
            clean_sections.values()
        )

        text = " ".join(lines)

        return {
            "type": script_type,
            "text": text,
            "score": int(score),
            "source": source,
            "sections": clean_sections,
            "lines": lines,
            "line_count": len(lines),
            "character_count": len(
                re.sub(
                    r"\s+",
                    "",
                    text,
                )
            ),
            "estimated_seconds": self._estimate_seconds(
                text
            ),
            "target_seconds": int(target_seconds),
        }

    def _extract_hook_text(
        self,
        review_hooks: Dict[str, Any],
    ) -> str:
        hooks = review_hooks.get("hooks")

        if not isinstance(hooks, list):
            return ""

        for item in hooks:
            if not isinstance(item, dict):
                continue

            text = self._clean_text(
                item.get("text")
            )

            if text:
                return text

        return ""

    def _extract_hook_type(
        self,
        review_hooks: Dict[str, Any],
    ) -> str:
        hooks = review_hooks.get("hooks")

        if not isinstance(hooks, list):
            return ""

        for item in hooks:
            if not isinstance(item, dict):
                continue

            hook_type = self._clean_text(
                item.get("type")
            )

            if hook_type:
                return hook_type

        return ""

    def _source_value(
        self,
        review_hooks: Dict[str, Any],
        key: str,
    ) -> str:
        source = review_hooks.get("source")

        if not isinstance(source, dict):
            return ""

        return self._clean_text(
            source.get(key)
        )

    def _has_final_consonant(
        self,
        text: str,
    ) -> bool:
        cleaned = self._clean_text(text)

        if not cleaned:
            return False

        last_char = cleaned[-1]

        if "가" <= last_char <= "힣":
            return (
                (ord(last_char) - ord("가")) % 28
                != 0
            )

        return False

    def _with_subject_particle(
        self,
        text: str,
    ) -> str:
        cleaned = self._clean_text(text)

        particle = (
            "이"
            if self._has_final_consonant(cleaned)
            else "가"
        )

        return f"{cleaned}{particle}"

    def _with_object_particle(
        self,
        text: str,
    ) -> str:
        cleaned = self._clean_text(text)

        particle = (
            "을"
            if self._has_final_consonant(cleaned)
            else "를"
        )

        return f"{cleaned}{particle}"

    def _with_instrument_particle(
        self,
        text: str,
    ) -> str:
        cleaned = self._clean_text(text)

        particle = (
            "으로"
            if self._has_final_consonant(cleaned)
            else "로"
        )

        return f"{cleaned}{particle}"

    def _sentence(
        self,
        text: str,
    ) -> str:
        text = self._clean_text(text)
        text = text.rstrip(" ,;:")

        if not text:
            return ""

        if text.endswith(
            ("…", ".", "!", "?")
        ):
            return text

        return text + "."

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

        if isinstance(
            value,
            (list, tuple),
        ):
            value = " ".join(
                self._clean_text(item)
                for item in value
                if self._clean_text(item)
            )

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

    def _estimate_seconds(
        self,
        text: str,
    ) -> int:
        character_count = len(
            re.sub(
                r"\s+",
                "",
                self._clean_text(text),
            )
        )

        if character_count == 0:
            return 0

        return max(
            5,
            round(
                character_count / 5.2
            ),
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

    def _dedupe_scripts(
        self,
        scripts: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        seen = set()

        for item in scripts:
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


def generate_review_scripts(
    review_hooks: Any = None,
    review_quotes: Any = None,
    review_insight: Any = None,
    product_name: str = "",
    review_count: int = 0,
) -> Dict[str, Any]:
    return ReviewScriptGenerator().generate(
        review_hooks=review_hooks,
        review_quotes=review_quotes,
        review_insight=review_insight,
        product_name=product_name,
        review_count=review_count,
    )