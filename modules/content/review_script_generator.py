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

    VERSION = "review-script-generator-81-9"

    def _build_analysis_bundle(
        self,
        hooks: Dict[str, Any],
        quotes: Dict[str, Any],
        insight: Dict[str, Any],
        product_name: str,
        review_count: int,
    ) -> Dict[str, Any]:
        count = self._safe_int(
            review_count
            or hooks.get("review_count")
            or insight.get("review_count")
            or quotes.get("review_count")
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

        product_strategy = self._classify_product_strategy(
            product_name=product_name,
            review_quotes=quotes,
            review_insight=insight,
        )

        product_type = self._first_text(
            product_strategy.get("product_type"),
            "general",
        )

        shorts_strategy = self._first_text(
            product_strategy.get("shorts_strategy"),
            "review_evidence",
        )

        target_customer_result = self._classify_target_customer(
            product_name=product_name,
            product_type=product_type,
            review_quotes=quotes,
            review_insight=insight,
        )

        target_customer = self._first_text(
            target_customer_result.get("target_customer"),
            "일반 구매자",
        )

        target_reason = self._first_text(
            target_customer_result.get("target_reason"),
            "실제 사용 목적과 후기 내용을 기준으로 선정했습니다",
        )

        review_type_result = self._classify_review_types(
            review_quotes=quotes,
            review_insight=insight,
            evidence_summary=evidence_summary,
            benefit_summary=benefit_summary,
        )

        dominant_review_type = self._first_text(
            review_type_result.get("dominant_type"),
            "general",
        )

        common_pattern = self._extract_common_pattern(
            review_quotes=quotes,
            review_insight=insight,
            evidence_summary=evidence_summary,
            benefit_summary=benefit_summary,
            pain_summary=pain_summary,
            dominant_review_type=dominant_review_type,
        )

        before_after_story = self._build_before_after_story(
            product_name=product_name,
            pain_summary=pain_summary,
            benefit_summary=benefit_summary,
            evidence_summary=evidence_summary,
            dominant_review_type=dominant_review_type,
        )

        inferred_psychology = self._classify_purchase_psychology(
            product_name=product_name,
            pain_summary=pain_summary,
            evidence_summary=evidence_summary,
            dominant_review_type=dominant_review_type,
        )

        hook_psychology_type = self._first_text(
            hooks.get("psychology_type"),
            self._source_value(hooks, "psychology_type"),
        )

        psychology_result = dict(inferred_psychology)

        strategy_psychology = {
            "comparison": "comparison",
            "problem_solution": "empathy",
            "convenience_experience": "recommendation",
            "performance_proof": "mistake_prevention",
            "seasonal_empathy": "empathy",
        }.get(
            shorts_strategy,
            "",
        )

        if hook_psychology_type:
            psychology_result["dominant_type"] = hook_psychology_type
            psychology_result["dominant_label"] = {
                "comparison": "비교형",
                "anxiety": "불안형",
                "mistake_prevention": "실수방지형",
                "empathy": "공감형",
                "recommendation": "추천형",
            }.get(
                hook_psychology_type,
                psychology_result.get("dominant_label", "공감형"),
            )
            psychology_result["source"] = "review_hook_generator"
        elif strategy_psychology:
            psychology_result["dominant_type"] = strategy_psychology
            psychology_result["dominant_label"] = {
                "comparison": "비교형",
                "anxiety": "불안형",
                "mistake_prevention": "실수방지형",
                "empathy": "공감형",
                "recommendation": "추천형",
            }.get(
                strategy_psychology,
                psychology_result.get("dominant_label", "공감형"),
            )
            psychology_result["source"] = "product_strategy"
        else:
            psychology_result["source"] = "review_script_generator"

        psychology_story = self._build_psychology_story(
            product_name=product_name,
            pain_summary=pain_summary,
            evidence_summary=evidence_summary,
            psychology_type=self._first_text(
                psychology_result.get("dominant_type"),
                "empathy",
            ),
        )

        strategy_bridge = self._strategy_bridge_sentence(
            product_type=product_type,
            shorts_strategy=shorts_strategy,
            product_name=product_name,
            dominant_review_type=dominant_review_type,
        )

        target_bridge = self._target_customer_sentence(
            target_customer=target_customer,
            product_type=product_type,
            product_name=product_name,
            evidence_summary=evidence_summary,
        )

        return {
            "review_count": count,
            "best_pain": best_pain,
            "best_benefit": best_benefit,
            "best_quote": best_quote,
            "best_evidence": best_evidence,
            "pain_summary": pain_summary,
            "benefit_summary": benefit_summary,
            "evidence_summary": evidence_summary,
            "product_strategy": product_strategy,
            "product_type": product_type,
            "shorts_strategy": shorts_strategy,
            "target_customer_result": target_customer_result,
            "target_customer": target_customer,
            "target_reason": target_reason,
            "review_type_result": review_type_result,
            "dominant_review_type": dominant_review_type,
            "common_pattern": common_pattern,
            "before_after_story": before_after_story,
            "psychology_result": psychology_result,
            "psychology_story": psychology_story,
            "hook_psychology_type": hook_psychology_type,
            "strategy_bridge": strategy_bridge,
            "target_bridge": target_bridge,
            "bridge_library_version": "bridge-library-80-2a",
        }

    def _build_story_context(
        self,
        product_name: str,
        product_type: str,
        shorts_strategy: str,
        dominant_review_type: str,
        psychology_type: str,
        pain_summary: str,
        benefit_summary: str,
        evidence_summary: str,
        before_after_story: Dict[str, str],
        psychology_story: Dict[str, str],
    ) -> Dict[str, str]:
        """Build one reusable story context from existing analysis results."""
        product = self._clean_text(product_name)
        product_type_text = self._clean_text(product_type)
        strategy = self._clean_text(shorts_strategy)
        review_type = self._clean_text(dominant_review_type)
        psychology = self._clean_text(psychology_type)

        problem = self._first_text(
            psychology_story.get("problem"),
            before_after_story.get("before"),
            pain_summary,
        )
        emotion = self._first_text(
            psychology_story.get("empathy"),
            "비슷한 고민 때문에 결정을 미루는 분들이 많습니다",
        )
        decision = self._first_text(
            before_after_story.get("choice"),
            f"그래서 실제 후기와 사용 목적을 기준으로 {self._with_object_particle(product)} 선택했습니다",
        )
        change = self._first_text(
            before_after_story.get("after"),
            f"사용 후에는 {benefit_summary}을 실제로 체감할 수 있었습니다",
        )
        result = self._first_text(
            before_after_story.get("recommendation"),
            self._recommendation_sentence(
                product_name=product,
                evidence_summary=evidence_summary,
                dominant_review_type=review_type,
            ),
        )

        if product_type_text == "travel" and "3박 4일" in evidence_summary:
            problem = "3박 4일 여행인데 20인치와 24인치 중 어떤 크기를 골라야 할지 고민하게 됩니다"
            emotion = "너무 작으면 짐이 부족하고 너무 크면 이동이 부담스러울 수 있습니다"
        elif product_type_text == "household":
            emotion = "매일 반복되는 작은 불편이라도 쌓이면 공간을 쓰는 일이 번거로워집니다"
        elif product_type_text == "kitchen":
            emotion = "자주 쓰는 제품일수록 준비와 정리가 불편하면 손이 잘 가지 않게 됩니다"
        elif product_type_text == "electronics":
            emotion = "비슷한 기능처럼 보여도 실제 사용감과 성능 차이는 분명할 수 있습니다"
        elif product_type_text == "seasonal":
            emotion = "필요한 시기가 닥친 뒤 준비하면 같은 불편을 다시 겪기 쉽습니다"

        if psychology == "mistake_prevention":
            emotion = self._first_text(
                psychology_story.get("risk"),
                emotion,
            )
        elif psychology == "recommendation":
            result = self._first_text(
                before_after_story.get("recommendation"),
                result,
            )

        arc_type = {
            "comparison": "compare_decide_result",
            "problem_solution": "problem_decide_change",
            "convenience_experience": "friction_use_result",
            "performance_proof": "doubt_proof_result",
            "seasonal_empathy": "timing_prepare_result",
        }.get(strategy, "review_story")

        return {
            "version": "story-library-81-1",
            "arc_type": arc_type,
            "problem": self._clean_text(problem),
            "emotion": self._clean_text(emotion),
            "decision": self._clean_text(decision),
            "change": self._clean_text(change),
            "result": self._clean_text(result),
        }

    def _build_emotion_curve(
        self,
        story_context: Dict[str, str],
        psychology_type: str,
        product_type: str,
        shorts_strategy: str,
    ) -> Dict[str, str]:
        """Build one reusable emotion curve from the existing story context."""
        psychology = self._clean_text(psychology_type)
        product_type_text = self._clean_text(product_type)
        strategy = self._clean_text(shorts_strategy)

        hook = {
            "comparison": "궁금증",
            "anxiety": "불안",
            "mistake_prevention": "경계",
            "empathy": "공감",
            "recommendation": "기대",
        }.get(psychology, "궁금증")

        empathy = self._first_text(
            story_context.get("emotion"),
            "비슷한 고민을 하는 분들이 많습니다",
        )
        tension = self._first_text(
            story_context.get("problem"),
            "기준 없이 고르면 구매 후 아쉬움이 남을 수 있습니다",
        )
        relief = self._first_text(
            story_context.get("change"),
            "직접 사용해 보니 고민했던 불편이 줄었습니다",
        )
        satisfaction = self._first_text(
            story_context.get("result"),
            "실제 사용 목적에 잘 맞는 선택이었습니다",
        )

        if psychology == "comparison":
            tension = "비슷해 보여도 기준 없이 고르면 실제 사용에서 차이가 크게 느껴질 수 있습니다"
        elif psychology == "mistake_prevention":
            tension = "한 번 잘못 고르면 다시 사야 하는 불편과 비용이 생길 수 있습니다"
        elif psychology == "anxiety":
            tension = "구매 전에는 내 사용 목적에 맞을지 쉽게 확신하기 어렵습니다"
        elif psychology == "recommendation":
            satisfaction = self._first_text(
                story_context.get("result"),
                "실사용자들이 추천하는 이유를 충분히 확인할 수 있습니다",
            )

        if product_type_text == "seasonal" or strategy == "seasonal_empathy":
            tension = "필요한 시기를 놓치면 같은 불편을 다시 겪기 쉽습니다"

        return {
            "version": "emotion-curve-81-2",
            "curve_type": f"{hook}_공감_긴장_해결_안도_만족",
            "hook": hook,
            "empathy": self._clean_text(empathy),
            "tension": self._clean_text(tension),
            "decision": self._clean_text(story_context.get("decision", "")),
            "relief": self._clean_text(relief),
            "satisfaction": self._clean_text(satisfaction),
        }

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

        bundle = self._build_analysis_bundle(
            hooks=hooks,
            quotes=quotes,
            insight=insight,
            product_name=product_name,
            review_count=review_count,
        )

        count = bundle["review_count"]
        best_pain = bundle["best_pain"]
        best_benefit = bundle["best_benefit"]
        best_quote = bundle["best_quote"]
        best_evidence = bundle["best_evidence"]
        pain_summary = bundle["pain_summary"]
        benefit_summary = bundle["benefit_summary"]
        evidence_summary = bundle["evidence_summary"]
        product_strategy = bundle["product_strategy"]
        product_type = bundle["product_type"]
        shorts_strategy = bundle["shorts_strategy"]
        target_customer_result = bundle["target_customer_result"]
        target_customer = bundle["target_customer"]
        target_reason = bundle["target_reason"]
        review_type_result = bundle["review_type_result"]
        dominant_review_type = bundle["dominant_review_type"]
        common_pattern = bundle["common_pattern"]
        before_after_story = bundle["before_after_story"]
        psychology_result = bundle["psychology_result"]
        psychology_story = bundle["psychology_story"]
        hook_psychology_type = bundle["hook_psychology_type"]
        strategy_bridge = bundle["strategy_bridge"]
        target_bridge = bundle["target_bridge"]
        psychology_type = self._first_text(
            psychology_result.get("dominant_type"),
            "empathy",
        )

        best_hook = self._first_text(
            hooks.get("best_hook"),
            self._extract_hook_text(hooks),
        )

        best_hook_type = self._first_text(
            hooks.get("best_hook_type"),
            self._extract_hook_type(hooks),
        )

        evidence_hook = self._make_hook(
            count=count,
            evidence=evidence_summary,
        )

        strategy_bridge = self._strategy_bridge_sentence(
            product_type=product_type,
            shorts_strategy=shorts_strategy,
            product_name=product_name,
            dominant_review_type=dominant_review_type,
        )

        target_bridge = self._target_customer_sentence(
            target_customer=target_customer,
            product_type=product_type,
            product_name=product_name,
            evidence_summary=evidence_summary,
        )

        if not best_hook:
            best_hook = self._make_hook(
                count=count,
                evidence=evidence_summary,
            )

        story_context = self._build_story_context(
            product_name=product_name,
            product_type=product_type,
            shorts_strategy=shorts_strategy,
            dominant_review_type=dominant_review_type,
            psychology_type=psychology_type,
            pain_summary=pain_summary,
            benefit_summary=benefit_summary,
            evidence_summary=evidence_summary,
            before_after_story=before_after_story,
            psychology_story=psychology_story,
        )

        emotion_curve = self._build_emotion_curve(
            story_context=story_context,
            psychology_type=psychology_type,
            product_type=product_type,
            shorts_strategy=shorts_strategy,
        )

        short_script = self._build_short_script(
            product_name=product_name,
            best_hook=best_hook,
            evidence_hook=evidence_hook,
            benefit_summary=benefit_summary,
            evidence_summary=evidence_summary,
            common_pattern=common_pattern,
            dominant_review_type=dominant_review_type,
            before_after_story=before_after_story,
            psychology_story=psychology_story,
            strategy_bridge=strategy_bridge,
            target_bridge=target_bridge,
            review_count=count,
            product_type=product_type,
            shorts_strategy=shorts_strategy,
            psychology_type=psychology_type,
            story_context=story_context,
            emotion_curve=emotion_curve,
        )

        medium_script = self._build_medium_script(
            hook_type=best_hook_type,
            product_name=product_name,
            best_hook=best_hook,
            evidence_hook=evidence_hook,
            pain_summary=pain_summary,
            benefit_summary=benefit_summary,
            evidence_summary=evidence_summary,
            common_pattern=common_pattern,
            dominant_review_type=dominant_review_type,
            before_after_story=before_after_story,
            psychology_story=psychology_story,
            strategy_bridge=strategy_bridge,
            target_bridge=target_bridge,
            review_count=count,
            product_type=product_type,
            shorts_strategy=shorts_strategy,
            psychology_type=psychology_type,
            story_context=story_context,
            emotion_curve=emotion_curve,
        )

        long_script = self._build_long_script(
            product_name=product_name,
            best_hook=best_hook,
            evidence_hook=evidence_hook,
            pain_summary=pain_summary,
            benefit_summary=benefit_summary,
            evidence_summary=evidence_summary,
            common_pattern=common_pattern,
            dominant_review_type=dominant_review_type,
            before_after_story=before_after_story,
            psychology_story=psychology_story,
            strategy_bridge=strategy_bridge,
            target_bridge=target_bridge,
            review_count=count,
            product_type=product_type,
            shorts_strategy=shorts_strategy,
            psychology_type=psychology_type,
            story_context=story_context,
            emotion_curve=emotion_curve,
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

        scripts = [
            self._score_script_quality(
                script=script,
                story_context=story_context,
                emotion_curve=emotion_curve,
                review_count=count,
            )
            for script in scripts
        ]

        scripts = [
            self._apply_story_quality_gate(
                script=script,
            )
            for script in scripts
        ]

        script_by_type = {
            script.get("type", ""): script
            for script in scripts
        }
        short_script = script_by_type.get(
            short_script.get("type", ""),
            short_script,
        )
        medium_script = script_by_type.get(
            medium_script.get("type", ""),
            medium_script,
        )
        long_script = script_by_type.get(
            long_script.get("type", ""),
            long_script,
        )

        scripts.sort(
            key=lambda item: (
                bool(item.get("quality_gate_passed", False)),
                item.get("quality_score", 0),
                item.get("retention_score", 0),
                item.get("natural_score", 0),
                item.get("score", 0),
                -abs(item.get("duration_error", 0)),
            ),
            reverse=True,
        )

        best_script = (
            scripts[0]
            if scripts
            else {}
        )

        narrative_optimization = self._optimize_selected_narrative(
            script=best_script,
        )
        optimized_script = narrative_optimization.get(
            "optimized_text",
            best_script.get("text", ""),
        )

        platform_adaptation = self._adapt_script_for_platforms(
            optimized_script=optimized_script,
            product_name=product_name,
            product_type=product_type,
            shorts_strategy=shorts_strategy,
        )
        platform_scripts = platform_adaptation.get("platform_scripts", {})

        cta_optimization = self._optimize_platform_ctas(
            platform_scripts=platform_scripts,
            product_name=product_name,
            product_type=product_type,
            shorts_strategy=shorts_strategy,
            review_count=count,
        )
        optimized_platform_scripts = cta_optimization.get(
            "optimized_platform_scripts",
            platform_scripts,
        )

        hook_variation = self._build_hook_variations(
            original_hook=best_hook,
            product_name=product_name,
            product_type=product_type,
            shorts_strategy=shorts_strategy,
            psychology_type=psychology_type,
            target_customer=target_customer,
            pain_summary=pain_summary,
            evidence_summary=evidence_summary,
            review_count=count,
        )

        validation_result = self._validate_final_script(
            best_script=best_script,
            optimized_script=optimized_script,
            optimized_platform_scripts=optimized_platform_scripts,
            hook_variation=hook_variation,
            cta_optimization=cta_optimization,
            story_context=story_context,
            emotion_curve=emotion_curve,
            review_count=count,
        )

        platform_recommendations = {
            "tiktok": "short",
            "instagram_reels": "medium",
            "youtube_shorts": "long",
        }

        print(
            "[Sprint81-9 Script] Version:",
            self.VERSION,
            flush=True,
        )
        print(
            "[Sprint81-9 Script] Analysis Bundle:",
            "built_once",
            flush=True,
        )
        print(
            "[Sprint81-9 Script] Bundle Keys:",
            sorted(bundle.keys()),
            flush=True,
        )
        print(
            "[Sprint81-9 Script] Bridge Library:",
            "bridge-library-80-2a",
            flush=True,
        )
        print(
            "[Sprint81-9 Script] Bridge Psychology:",
            psychology_type,
            flush=True,
        )
        print(
            "[Sprint81-9 Script] Product:",
            product_name,
            flush=True,
        )
        print(
            "[Sprint81-9 Script] Product Type:",
            product_type,
            flush=True,
        )
        print(
            "[Sprint81-9 Script] Shorts Strategy:",
            shorts_strategy,
            flush=True,
        )
        print(
            "[Sprint81-9 Script] Strategy Reason:",
            product_strategy.get("strategy_reason", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Script] Strategy Bridge:",
            strategy_bridge,
            flush=True,
        )
        print(
            "[Sprint81-9 Script] Target Customer:",
            target_customer,
            flush=True,
        )
        print(
            "[Sprint81-9 Script] Target Reason:",
            target_reason,
            flush=True,
        )
        print(
            "[Sprint81-9 Script] Target Confidence:",
            target_customer_result.get("confidence", 0),
            flush=True,
        )
        print(
            "[Sprint81-9 Script] Target Bridge:",
            target_bridge,
            flush=True,
        )
        print(
            "[Sprint81-9 Script] Hook Type:",
            best_hook_type,
            flush=True,
        )
        print(
            "[Sprint81-9 Script] Dominant Review Type:",
            review_type_result.get("dominant_type", ""),
            review_type_result.get("dominant_label", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Script] Review Type Scores:",
            review_type_result.get("scores", {}),
            flush=True,
        )
        print(
            "[Sprint81-9 Script] Before:",
            before_after_story.get("before", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Script] Choice:",
            before_after_story.get("choice", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Script] After:",
            before_after_story.get("after", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Script] Psychology Type:",
            psychology_result.get("dominant_type", ""),
            psychology_result.get("dominant_label", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Script] Psychology Scores:",
            psychology_result.get("scores", {}),
            flush=True,
        )
        print(
            "[Sprint81-9 Script] Problem:",
            psychology_story.get("problem", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Script] Empathy:",
            psychology_story.get("empathy", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Story] Version:",
            story_context.get("version", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Story] Built:",
            bool(story_context),
            flush=True,
        )
        print(
            "[Sprint81-9 Story] Arc:",
            story_context.get("arc_type", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Story] Problem:",
            story_context.get("problem", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Story] Emotion:",
            story_context.get("emotion", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Story] Decision:",
            story_context.get("decision", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Story] Change:",
            story_context.get("change", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Story] Result:",
            story_context.get("result", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Emotion] Version:",
            emotion_curve.get("version", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Emotion] Built:",
            bool(emotion_curve),
            flush=True,
        )
        print(
            "[Sprint81-9 Emotion] Curve:",
            emotion_curve.get("curve_type", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Emotion] Hook:",
            emotion_curve.get("hook", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Emotion] Empathy:",
            emotion_curve.get("empathy", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Emotion] Tension:",
            emotion_curve.get("tension", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Emotion] Relief:",
            emotion_curve.get("relief", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Emotion] Satisfaction:",
            emotion_curve.get("satisfaction", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Script] Short:",
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
            "[Sprint81-9 Script] Medium:",
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
            "[Sprint81-9 Script] Long:",
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
        for label, script in (
            ("Short", short_script),
            ("Medium", medium_script),
            ("Long", long_script),
        ):
            print(
                f"[Sprint81-9 Score] {label}:",
                {
                    "story": script.get("story_score", 0),
                    "emotion": script.get("emotion_score", 0),
                    "natural": script.get("natural_score", 0),
                    "evidence": script.get("evidence_score", 0),
                    "retention": script.get("retention_score", 0),
                    "quality": script.get("quality_score", 0),
                },
                flush=True,
            )
        print(
            "[Sprint81-9 Score] Version:",
            "story-score-engine-81-3",
            flush=True,
        )
        print(
            "[Sprint81-9 Score] Selected Quality:",
            best_script.get("quality_score", 0),
            flush=True,
        )
        print(
            "[Sprint81-9 Gate] Version:",
            "story-quality-gate-81-4",
            flush=True,
        )
        print(
            "[Sprint81-9 Gate] Selected Passed:",
            best_script.get("quality_gate_passed", False),
            flush=True,
        )
        print(
            "[Sprint81-9 Gate] Selected Status:",
            best_script.get("quality_gate_status", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Gate] Weak Dimensions:",
            best_script.get("quality_gate_weak_dimensions", []),
            flush=True,
        )
        print(
            "[Sprint81-9 Gate] Improvement Priority:",
            best_script.get("quality_gate_improvement_priority", []),
            flush=True,
        )
        print(
            "[Sprint81-9 Optimizer] Version:",
            narrative_optimization.get("version", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Optimizer] Applied:",
            narrative_optimization.get("applied", False),
            flush=True,
        )
        print(
            "[Sprint81-9 Optimizer] Changes:",
            narrative_optimization.get("changes", []),
            flush=True,
        )
        print(
            "[Sprint81-9 Optimizer] Score:",
            narrative_optimization.get("optimization_score", 0),
            flush=True,
        )
        print(
            "[Sprint81-9 Optimizer] Script:",
            optimized_script,
            flush=True,
        )
        print(
            "[Sprint81-9 Platform] Version:",
            platform_adaptation.get("version", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Platform] Built:",
            bool(platform_scripts),
            flush=True,
        )
        print(
            "[Sprint81-9 Platform] Score:",
            platform_adaptation.get("adaptation_score", 0),
            flush=True,
        )
        for platform_name in (
            "tiktok",
            "instagram_reels",
            "youtube_shorts",
        ):
            platform_data = platform_scripts.get(platform_name, {})
            print(
                f"[Sprint81-9 Platform] {platform_name}:",
                platform_data.get("script", ""),
                flush=True,
            )
        print(
            "[Sprint81-9 CTA] Version:",
            cta_optimization.get("version", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 CTA] Built:",
            cta_optimization.get("built", False),
            flush=True,
        )
        print(
            "[Sprint81-9 CTA] Score:",
            cta_optimization.get("cta_score", 0),
            flush=True,
        )
        for platform_name in (
            "tiktok",
            "instagram_reels",
            "youtube_shorts",
        ):
            cta_data = cta_optimization.get("platform_cta", {}).get(platform_name, {})
            print(
                f"[Sprint81-9 CTA] {platform_name}:",
                cta_data.get("selected_cta", ""),
                flush=True,
            )
        print(
            "[Sprint81-9 Hook] Version:",
            hook_variation.get("version", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Hook] Built:",
            hook_variation.get("built", False),
            flush=True,
        )
        print(
            "[Sprint81-9 Hook] Count:",
            hook_variation.get("hook_count", 0),
            flush=True,
        )
        print(
            "[Sprint81-9 Hook] Selected Type:",
            hook_variation.get("selected_hook_type", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Hook] Selected Score:",
            hook_variation.get("selected_hook_score", 0),
            flush=True,
        )
        print(
            "[Sprint81-9 Hook] Selected:",
            hook_variation.get("selected_hook", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Validator] Version:",
            validation_result.get("version", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Validator] Built:",
            validation_result.get("built", False),
            flush=True,
        )
        print(
            "[Sprint81-9 Validator] Passed:",
            validation_result.get("passed", False),
            flush=True,
        )
        print(
            "[Sprint81-9 Validator] Final Score:",
            validation_result.get("final_quality_score", 0),
            flush=True,
        )
        print(
            "[Sprint81-9 Validator] Warnings:",
            validation_result.get("warnings", []),
            flush=True,
        )
        print(
            "[Sprint81-9 Validator] Improvement Priority:",
            validation_result.get("improvement_priority", []),
            flush=True,
        )
        print(
            "[Sprint81-9 Script] Selected:",
            best_script.get("type", ""),
            flush=True,
        )
        print(
            "[Sprint81-9 Script] Best Script:",
            best_script.get("text", ""),
            flush=True,
        )

        return {
            "ok": bool(best_script),
            "version": self.VERSION,
            "status": "generated" if best_script else "empty",
            "product_name": product_name,
            "review_count": count,
            "product_type": product_type,
            "shorts_strategy": shorts_strategy,
            "product_strategy": product_strategy,
            "analysis_bundle_version": "analysis-bundle-80-1",
            "bridge_library_version": "bridge-library-80-2a",
            "story_library_version": "story-library-81-1",
            "story_context": story_context,
            "emotion_curve_version": "emotion-curve-81-2",
            "emotion_curve": emotion_curve,
            "score_engine_version": "story-score-engine-81-3",
            "quality_gate_version": "story-quality-gate-81-4",
            "narrative_optimizer_version": "narrative-optimizer-81-5",
            "optimized_script": optimized_script,
            "optimization_applied": narrative_optimization.get("applied", False),
            "optimization_changes": narrative_optimization.get("changes", []),
            "optimization_score": narrative_optimization.get("optimization_score", 0),
            "narrative_optimization": narrative_optimization,
            "platform_adapter_version": "platform-adaptation-engine-81-6",
            "platform_adaptation_score": platform_adaptation.get(
                "adaptation_score",
                0,
            ),
            "platform_adaptation": platform_adaptation,
            "platform_scripts": platform_scripts,
            "tiktok_script": platform_scripts.get("tiktok", {}).get("script", ""),
            "instagram_script": platform_scripts.get("instagram_reels", {}).get("script", ""),
            "youtube_script": platform_scripts.get("youtube_shorts", {}).get("script", ""),
            "cta_optimizer_version": "cta-optimization-engine-81-7",
            "cta_library": cta_optimization.get("cta_library", {}),
            "platform_cta": cta_optimization.get("platform_cta", {}),
            "selected_cta": cta_optimization.get("selected_cta", {}),
            "cta_score": cta_optimization.get("cta_score", 0),
            "cta_optimization": cta_optimization,
            "optimized_platform_scripts": optimized_platform_scripts,
            "optimized_tiktok_script": optimized_platform_scripts.get("tiktok", {}).get("script", ""),
            "optimized_instagram_script": optimized_platform_scripts.get("instagram_reels", {}).get("script", ""),
            "optimized_youtube_script": optimized_platform_scripts.get("youtube_shorts", {}).get("script", ""),
            "hook_variation_version": "hook-variation-engine-81-8",
            "hook_variations": hook_variation.get("hook_variations", []),
            "hook_count": hook_variation.get("hook_count", 0),
            "selected_hook": hook_variation.get("selected_hook", best_hook),
            "selected_hook_type": hook_variation.get("selected_hook_type", best_hook_type),
            "selected_hook_score": hook_variation.get("selected_hook_score", 0),
            "hook_variation": hook_variation,
            "final_validator_version": "final-script-validator-81-9",
            "validation_result": validation_result,
            "validation_passed": validation_result.get("passed", False),
            "validation_scores": validation_result.get("scores", {}),
            "validation_warnings": validation_result.get("warnings", []),
            "validation_improvement_priority": validation_result.get(
                "improvement_priority",
                [],
            ),
            "final_quality_score": validation_result.get(
                "final_quality_score",
                0,
            ),
            "quality_gate_passed": best_script.get("quality_gate_passed", False),
            "quality_gate_status": best_script.get("quality_gate_status", ""),
            "quality_gate_weak_dimensions": best_script.get(
                "quality_gate_weak_dimensions",
                [],
            ),
            "quality_gate_improvement_priority": best_script.get(
                "quality_gate_improvement_priority",
                [],
            ),
            "quality_gate_results": {
                script.get("type", ""): {
                    "passed": script.get("quality_gate_passed", False),
                    "status": script.get("quality_gate_status", ""),
                    "weak_dimensions": script.get(
                        "quality_gate_weak_dimensions",
                        [],
                    ),
                    "improvement_priority": script.get(
                        "quality_gate_improvement_priority",
                        [],
                    ),
                }
                for script in scripts
            },
            "best_quality_score": best_script.get("quality_score", 0),
            "best_story_score": best_script.get("story_score", 0),
            "best_emotion_score": best_script.get("emotion_score", 0),
            "best_natural_score": best_script.get("natural_score", 0),
            "best_evidence_score": best_script.get("evidence_score", 0),
            "best_retention_score": best_script.get("retention_score", 0),
            "script_quality_scores": {
                script.get("type", ""): {
                    "story_score": script.get("story_score", 0),
                    "emotion_score": script.get("emotion_score", 0),
                    "natural_score": script.get("natural_score", 0),
                    "evidence_score": script.get("evidence_score", 0),
                    "retention_score": script.get("retention_score", 0),
                    "quality_score": script.get("quality_score", 0),
                }
                for script in scripts
            },
            "bridge_psychology_type": psychology_type,
            "analysis_bundle_keys": sorted(bundle.keys()),
            "target_customer": target_customer,
            "target_reason": target_reason,
            "target_customer_result": target_customer_result,
            "best_hook": best_hook,
            "best_hook_type": best_hook_type,
            "evidence_hook": evidence_hook,
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
                "review_type": review_type_result,
                "dominant_review_type": dominant_review_type,
                "common_pattern": common_pattern,
                "before_after_story": before_after_story,
                "purchase_psychology": psychology_result,
                "hook_psychology_type": hook_psychology_type,
                "product_strategy": product_strategy,
                "strategy_bridge": strategy_bridge,
                "target_customer": target_customer,
                "target_reason": target_reason,
                "target_bridge": target_bridge,
                "target_customer_result": target_customer_result,
                "analysis_bundle_version": "analysis-bundle-80-1",
                "bridge_library_version": "bridge-library-80-2a",
                "story_library_version": "story-library-81-1",
                "story_context": story_context,
                "emotion_curve_version": "emotion-curve-81-2",
                "emotion_curve": emotion_curve,
                "bridge_psychology_type": psychology_type,
                "analysis_bundle_reused_for": [
                    "short_script",
                    "medium_script",
                    "long_script",
                ],
                "psychology_story": psychology_story,
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
        evidence_hook: str,
        benefit_summary: str,
        evidence_summary: str,
        common_pattern: str,
        dominant_review_type: str,
        before_after_story: Dict[str, str],
        psychology_story: Dict[str, str],
        strategy_bridge: str,
        target_bridge: str,
        review_count: int,
        product_type: str,
        shorts_strategy: str,
        psychology_type: str,
        story_context: Dict[str, str],
        emotion_curve: Dict[str, str],
    ) -> Dict[str, Any]:
        sections = {
            "problem": self._sentence(
                story_context.get(
                    "problem",
                    psychology_story.get(
                        "problem",
                        before_after_story.get("before", ""),
                    ),
                )
            ),
            "hook": self._sentence(
                self._shorten(
                    best_hook,
                    72,
                )
            ),
            "target": self._sentence(
                target_bridge
            ),
            "strategy": self._sentence(
                strategy_bridge
            ),
            "evidence": self._sentence(
                self._shorten(
                    evidence_hook,
                    88,
                )
            ),
            "after": self._sentence(
                emotion_curve.get(
                    "relief",
                    story_context.get(
                        "change",
                        before_after_story.get(
                            "after",
                            benefit_summary,
                        ),
                    ),
                )
            ),
            "cta": self._sentence(
                self._short_cta(
                    product_name
                )
            ),
        }

        sections = self._apply_bridge_library(
            sections=sections,
            script_length="short",
            product_type=product_type,
            shorts_strategy=shorts_strategy,
            psychology_type=psychology_type,
        )

        script = self._script(
            script_type="short_18s",
            sections=sections,
            score=96,
            source="purchase_psychology_short",
            target_seconds=18,
        )

        return self._fit_duration(
            script,
            min_seconds=16,
            max_seconds=21,
        )

    def _build_medium_script(
        self,
        hook_type: str,
        product_name: str,
        best_hook: str,
        evidence_hook: str,
        pain_summary: str,
        benefit_summary: str,
        evidence_summary: str,
        common_pattern: str,
        dominant_review_type: str,
        before_after_story: Dict[str, str],
        psychology_story: Dict[str, str],
        strategy_bridge: str,
        target_bridge: str,
        review_count: int,
        product_type: str,
        shorts_strategy: str,
        psychology_type: str,
        story_context: Dict[str, str],
        emotion_curve: Dict[str, str],
    ) -> Dict[str, Any]:
        sections = {
            "hook": self._sentence(
                self._shorten(
                    best_hook,
                    76,
                )
            ),
            "empathy": self._sentence(
                emotion_curve.get(
                    "empathy",
                    story_context.get(
                        "emotion",
                        psychology_story.get(
                            "empathy",
                            "한 번쯤 같은 고민을 하게 됩니다",
                        ),
                    ),
                )
            ),
            "target": self._sentence(
                target_bridge
            ),
            "strategy": self._sentence(
                strategy_bridge
            ),
            "evidence": self._sentence(
                self._shorten(
                    evidence_hook,
                    96,
                )
            ),
            "choice": self._sentence(
                story_context.get(
                    "decision",
                    before_after_story.get(
                        "choice",
                        "",
                    ),
                )
            ),
            "after": self._sentence(
                emotion_curve.get(
                    "relief",
                    story_context.get(
                        "change",
                        before_after_story.get(
                            "after",
                            benefit_summary,
                        ),
                    ),
                )
            ),
            "recommendation": self._sentence(
                emotion_curve.get(
                    "satisfaction",
                    story_context.get(
                        "result",
                        before_after_story.get(
                            "recommendation",
                            "",
                        ),
                    ),
                )
            ),
            "cta": self._sentence(
                self._product_cta(
                    product_name
                )
            ),
        }

        sections = self._apply_bridge_library(
            sections=sections,
            script_length="medium",
            product_type=product_type,
            shorts_strategy=shorts_strategy,
            psychology_type=psychology_type,
        )

        script = self._script(
            script_type="medium_47s",
            sections=sections,
            score=100,
            source="purchase_psychology_medium",
            target_seconds=47,
        )

        return self._fit_duration(
            script,
            min_seconds=43,
            max_seconds=50,
        )

    def _build_long_script(
        self,
        product_name: str,
        best_hook: str,
        evidence_hook: str,
        pain_summary: str,
        benefit_summary: str,
        evidence_summary: str,
        common_pattern: str,
        dominant_review_type: str,
        before_after_story: Dict[str, str],
        psychology_story: Dict[str, str],
        strategy_bridge: str,
        target_bridge: str,
        review_count: int,
        product_type: str,
        shorts_strategy: str,
        psychology_type: str,
        story_context: Dict[str, str],
        emotion_curve: Dict[str, str],
    ) -> Dict[str, Any]:
        sections = {
            "hook": self._sentence(
                self._shorten(
                    best_hook,
                    80,
                )
            ),
            "problem": self._sentence(
                story_context.get(
                    "problem",
                    psychology_story.get(
                        "problem",
                        before_after_story.get("before", ""),
                    ),
                )
            ),
            "empathy": self._sentence(
                emotion_curve.get(
                    "empathy",
                    story_context.get(
                        "emotion",
                        psychology_story.get(
                            "empathy",
                            "비슷한 고민을 하는 분들이 많습니다",
                        ),
                    ),
                )
            ),
            "risk": self._sentence(
                emotion_curve.get(
                    "tension",
                    psychology_story.get(
                        "risk",
                        "",
                    ),
                )
            ),
            "target": self._sentence(
                target_bridge
            ),
            "strategy": self._sentence(
                strategy_bridge
            ),
            "evidence": self._sentence(
                self._shorten(
                    evidence_hook,
                    102,
                )
            ),
            "common_pattern": self._sentence(
                self._common_pattern_sentence(
                    common_pattern
                )
            ),
            "choice": self._sentence(
                story_context.get(
                    "decision",
                    before_after_story.get(
                        "choice",
                        "",
                    ),
                )
            ),
            "after": self._sentence(
                emotion_curve.get(
                    "relief",
                    story_context.get(
                        "change",
                        before_after_story.get(
                            "after",
                            benefit_summary,
                        ),
                    ),
                )
            ),
            "recommendation": self._sentence(
                emotion_curve.get(
                    "satisfaction",
                    story_context.get(
                        "result",
                        before_after_story.get(
                            "recommendation",
                            "",
                        ),
                    ),
                )
            ),
            "cta": self._sentence(
                self._product_cta(
                    product_name
                )
            ),
        }

        sections = self._apply_bridge_library(
            sections=sections,
            script_length="long",
            product_type=product_type,
            shorts_strategy=shorts_strategy,
            psychology_type=psychology_type,
        )

        script = self._script(
            script_type="long_46s",
            sections=sections,
            score=95,
            source="purchase_psychology_long",
            target_seconds=46,
        )

        return self._fit_duration(
            script,
            min_seconds=41,
            max_seconds=50,
        )

    def _classify_product_strategy(
        self,
        product_name: str,
        review_quotes: Dict[str, Any],
        review_insight: Dict[str, Any],
    ) -> Dict[str, Any]:
        product = self._clean_text(product_name)
        combined = self._clean_text(
            " ".join(
                [
                    product,
                    self._clean_text(review_insight.get("best_pain")),
                    self._clean_text(review_insight.get("best_pain_point")),
                    self._clean_text(review_insight.get("best_benefit")),
                    self._clean_text(review_insight.get("best_evidence")),
                    self._clean_text(review_quotes.get("best_quote")),
                ]
            )
        )

        product_rules = (
            (
                "travel",
                ("캐리어", "여행", "파우치", "보스턴백", "목베개", "여권"),
                "comparison",
                "여행용품은 구매 전에 크기와 용도 비교가 가장 많이 발생합니다",
            ),
            (
                "household",
                ("거치대", "정리함", "욕실", "청소", "수납함", "슬리퍼", "생활"),
                "problem_solution",
                "생활용품은 일상 불편을 바로 해결하는 흐름이 효과적입니다",
            ),
            (
                "kitchen",
                ("텀블러", "프라이팬", "냄비", "도마", "칼", "주방", "보관용기"),
                "convenience_experience",
                "주방용품은 사용 전후의 편의성 체험을 보여주는 것이 효과적입니다",
            ),
            (
                "electronics",
                ("충전기", "이어폰", "스피커", "청소기", "전자", "전동", "배터리"),
                "performance_proof",
                "전자제품은 기능과 성능을 실제 사용 증거로 검증하는 흐름이 효과적입니다",
            ),
            (
                "seasonal",
                ("방충망", "선풍기", "제습", "쿨링", "난방", "겨울", "여름", "계절"),
                "seasonal_empathy",
                "계절상품은 지금 겪는 불편에 공감하는 후킹이 효과적입니다",
            ),
        )

        for product_type, keywords, strategy, reason in product_rules:
            if any(
                keyword in combined
                for keyword in keywords
            ):
                return {
                    "product_type": product_type,
                    "shorts_strategy": strategy,
                    "strategy_reason": reason,
                    "matched_keywords": [
                        keyword
                        for keyword in keywords
                        if keyword in combined
                    ],
                }

        return {
            "product_type": "general",
            "shorts_strategy": "review_evidence",
            "strategy_reason": "제품 유형이 명확하지 않아 실제 후기 증거 중심 전략을 사용합니다",
            "matched_keywords": [],
        }

    def _strategy_bridge_sentence(
        self,
        product_type: str,
        shorts_strategy: str,
        product_name: str,
        dominant_review_type: str,
    ) -> str:
        strategy = self._clean_text(shorts_strategy)
        product = self._clean_text(product_name)
        review_type = self._clean_text(dominant_review_type)

        if strategy == "comparison":
            return "선택 기준은 여행 기간과 실제로 담을 짐의 양입니다"

        if strategy == "problem_solution":
            return "핵심은 매일 반복되는 불편을 간단하게 줄여주는지입니다"

        if strategy == "convenience_experience":
            return "직접 써보면 준비와 정리에 걸리는 시간이 확실히 줄어듭니다"

        if strategy == "performance_proof":
            return "광고 문구보다 실제 사용에서 성능이 유지되는지가 더 중요합니다"

        if strategy == "seasonal_empathy":
            return "필요한 계절이 오기 전에 미리 준비하면 불편을 줄일 수 있습니다"

        if review_type == "storage":
            return "실제 선택 기준은 수납공간과 내부 정리 방식입니다"

        return f"{product}를 고를 때는 실제 후기에서 반복되는 장점을 확인해야 합니다"

    def _classify_target_customer(
        self,
        product_name: str,
        product_type: str,
        review_quotes: Dict[str, Any],
        review_insight: Dict[str, Any],
    ) -> Dict[str, Any]:
        product = self._clean_text(product_name)
        product_type_text = self._clean_text(product_type)

        combined = self._clean_text(
            " ".join(
                [
                    product,
                    self._clean_text(review_insight.get("best_evidence")),
                    self._clean_text(review_insight.get("best_pain")),
                    self._clean_text(review_insight.get("best_pain_point")),
                    self._clean_text(review_insight.get("best_benefit")),
                    self._clean_text(review_quotes.get("best_quote")),
                    self._clean_text(review_quotes.get("best_benefit")),
                ]
            )
        )

        for source in (review_quotes, review_insight):
            for key in (
                "top_quotes",
                "reviews",
                "selected_reviews",
                "top_evidence",
            ):
                values = source.get(key)

                if not isinstance(values, list):
                    continue

                for item in values[:20]:
                    combined += " " + self._clean_text(item)

        combined = self._clean_text(combined)

        if product_type_text == "travel":
            if (
                "3박 4일" in combined
                or "3박4일" in combined
            ):
                return {
                    "target_customer": "3박 4일 여행객",
                    "target_reason": "후기 핵심 문장이 3박 4일 여행 기준으로 반복됐습니다",
                    "target_type": "trip_duration",
                    "confidence": 96,
                }

            if (
                "2박 3일" in combined
                or "2박3일" in combined
            ):
                return {
                    "target_customer": "2박 3일 단기 여행객",
                    "target_reason": "후기에서 짧은 여행 기간과 휴대성이 반복 언급됐습니다",
                    "target_type": "short_trip",
                    "confidence": 92,
                }

            return {
                "target_customer": "여행 기간에 맞는 캐리어를 찾는 분",
                "target_reason": "후기에서 크기와 여행 기간 비교가 가장 많이 나타났습니다",
                "target_type": "travel_general",
                "confidence": 84,
            }

        if product_type_text == "household":
            targets = []

            if any(
                keyword in combined
                for keyword in (
                    "자취",
                    "원룸",
                    "좁은 공간",
                )
            ):
                targets.append("자취생")

            if any(
                keyword in combined
                for keyword in (
                    "신혼",
                    "부부",
                    "새집",
                )
            ):
                targets.append("신혼부부")

            if any(
                keyword in combined
                for keyword in (
                    "욕실",
                    "정리",
                    "바닥",
                    "흩어",
                )
            ):
                targets.append("욕실 정리가 필요한 분")

            if not targets:
                targets = ["생활공간을 깔끔하게 정리하고 싶은 분"]

            return {
                "target_customer": "·".join(targets[:3]),
                "target_reason": "후기에서 공간 정리와 일상 불편 해결 요구가 반복됐습니다",
                "target_type": "household_problem",
                "confidence": 88,
            }

        if product_type_text == "kitchen":
            targets = []

            if any(
                keyword in combined
                for keyword in (
                    "직장",
                    "회사",
                    "출근",
                    "사무실",
                )
            ):
                targets.append("직장인")

            if any(
                keyword in combined
                for keyword in (
                    "학생",
                    "학교",
                    "강의",
                )
            ):
                targets.append("학생")

            if any(
                keyword in combined
                for keyword in (
                    "운전",
                    "차량",
                    "차 안",
                )
            ):
                targets.append("운전자")

            if not targets:
                targets = ["사용 편의성을 중요하게 보는 분"]

            return {
                "target_customer": "·".join(targets[:3]),
                "target_reason": "후기에서 휴대성과 반복 사용 편의가 주요 만족 이유로 나타났습니다",
                "target_type": "daily_convenience",
                "confidence": 86,
            }

        if product_type_text == "electronics":
            return {
                "target_customer": "성능과 실제 사용 후기를 꼼꼼히 비교하는 분",
                "target_reason": "전자제품은 기능과 성능 검증 후 구매하는 경향이 강합니다",
                "target_type": "performance_buyer",
                "confidence": 85,
            }

        if product_type_text == "seasonal":
            return {
                "target_customer": "계절 불편을 미리 해결하려는 분",
                "target_reason": "후기에서 특정 계절의 반복 불편과 해결 필요가 나타났습니다",
                "target_type": "seasonal_need",
                "confidence": 87,
            }

        return {
            "target_customer": "실제 후기를 기준으로 제품을 선택하는 분",
            "target_reason": "제품 유형이 명확하지 않아 후기 기반 일반 타깃을 사용합니다",
            "target_type": "general_review_buyer",
            "confidence": 70,
        }

    def _target_customer_sentence(
        self,
        target_customer: str,
        product_type: str,
        product_name: str,
        evidence_summary: str,
    ) -> str:
        target = self._clean_text(target_customer)
        product_type_text = self._clean_text(product_type)
        evidence = self._clean_text(evidence_summary)

        if (
            product_type_text == "travel"
            and "3박 4일" in evidence
        ):
            return "특히 3박 4일 여행을 준비하는 분이라면 이 기준이 가장 중요합니다"

        if product_type_text == "travel":
            return f"{target}이라면 여행 기간과 짐의 양을 먼저 확인해야 합니다"

        if product_type_text == "household":
            return f"{target}이라면 매일 반복되는 정리 불편을 줄이는지가 중요합니다"

        if product_type_text == "kitchen":
            return f"{target}이라면 휴대성과 사용 편의성을 함께 확인하는 것이 좋습니다"

        if product_type_text == "electronics":
            return f"{target}이라면 광고보다 실제 사용 성능을 먼저 확인해야 합니다"

        if product_type_text == "seasonal":
            return f"{target}이라면 필요한 계절이 오기 전에 준비하는 것이 좋습니다"

        return f"{target}이라면 실제 후기에서 반복되는 장점을 먼저 확인해 보세요"

    def _classify_purchase_psychology(
        self,
        product_name: str,
        pain_summary: str,
        evidence_summary: str,
        dominant_review_type: str,
    ) -> Dict[str, Any]:
        product = self._clean_text(product_name)
        pain = self._clean_text(pain_summary)
        evidence = self._clean_text(evidence_summary)
        review_type = self._clean_text(dominant_review_type)

        scores = {
            "anxiety": 0,
            "empathy": 0,
            "mistake_prevention": 0,
            "comparison": 0,
            "recommendation": 0,
        }

        if any(
            keyword in pain
            for keyword in (
                "어렵",
                "고민",
                "불편",
                "부담",
                "걱정",
            )
        ):
            scores["anxiety"] += 4
            scores["empathy"] += 3

        if any(
            keyword in evidence
            for keyword in (
                "적당",
                "맞",
                "크기",
                "인치",
            )
        ):
            scores["comparison"] += 5
            scores["mistake_prevention"] += 4

        if review_type in (
            "storage",
            "mobility",
            "durability",
            "value",
            "design",
        ):
            scores["recommendation"] += 2

        if "캐리어" in product:
            scores["comparison"] += 3
            scores["mistake_prevention"] += 2

        priority = {
            "comparison": 5,
            "mistake_prevention": 4,
            "anxiety": 3,
            "empathy": 2,
            "recommendation": 1,
        }

        dominant_type = max(
            scores,
            key=lambda key: (
                scores.get(key, 0),
                priority.get(key, 0),
            ),
        )

        labels = {
            "anxiety": "불안형",
            "empathy": "공감형",
            "mistake_prevention": "실수방지형",
            "comparison": "비교형",
            "recommendation": "추천형",
        }

        return {
            "dominant_type": dominant_type,
            "dominant_label": labels.get(
                dominant_type,
                "공감형",
            ),
            "scores": scores,
        }

    def _build_psychology_story(
        self,
        product_name: str,
        pain_summary: str,
        evidence_summary: str,
        psychology_type: str,
    ) -> Dict[str, str]:
        product = self._clean_text(product_name)
        pain = self._clean_text(pain_summary)
        evidence = self._clean_text(evidence_summary)
        psychology = self._clean_text(psychology_type)

        if (
            "캐리어" in product
            and "3박 4일" in evidence
            and "24인치" in evidence
        ):
            base = {
                "problem": "3박 4일 여행인데 20인치를 살지 24인치를 살지 고민하게 됩니다",
                "empathy": "너무 작으면 짐이 부족하고 너무 크면 이동이 부담스러울 수 있습니다",
                "risk": "크기를 잘못 고르면 여행 내내 수납과 이동이 불편해질 수 있습니다",
            }
        else:
            base = {
                "problem": f"{pain}, 구매 전에 가장 먼저 고민하게 되는 부분입니다",
                "empathy": "비슷한 고민 때문에 결정을 미루는 분들이 많습니다",
                "risk": "사용 목적과 맞지 않으면 구매 후 만족도가 떨어질 수 있습니다",
            }

        type_overrides = {
            "anxiety": {
                "empathy": "잘못 선택할까 걱정돼 쉽게 결정하기 어렵습니다",
            },
            "mistake_prevention": {
                "risk": "기준 없이 선택하면 같은 제품을 다시 사게 될 수도 있습니다",
            },
            "comparison": {
                "empathy": "비슷해 보여도 실제 사용에서는 크기와 구성이 크게 다릅니다",
            },
            "recommendation": {
                "empathy": "실사용자의 공통 의견을 보면 선택 기준이 더 분명해집니다",
            },
        }

        base.update(
            type_overrides.get(
                psychology,
                {},
            )
        )

        return base

    def _build_before_after_story(
        self,
        product_name: str,
        pain_summary: str,
        benefit_summary: str,
        evidence_summary: str,
        dominant_review_type: str,
    ) -> Dict[str, str]:
        product = self._clean_text(product_name)
        pain = self._clean_text(pain_summary)
        review_type = self._clean_text(dominant_review_type)
        evidence = self._clean_text(evidence_summary)

        before_map = {
            "storage": "여행 전에는 짐이 많아질수록 수납과 정리가 가장 고민이었습니다",
            "mobility": "여행 전에는 무거운 짐을 오래 끌고 이동하는 것이 가장 부담이었습니다",
            "durability": "구매 전에는 자주 사용해도 오래 버틸 수 있을지가 가장 걱정됐습니다",
            "value": "구매 전에는 가격과 필요한 기능 사이에서 선택하기가 어려웠습니다",
            "design": "구매 전에는 실용성과 디자인을 함께 만족시키는 제품을 찾기 어려웠습니다",
        }

        choice_map = {
            "storage": f"그래서 수납공간과 내부 구성을 기준으로 {self._with_object_particle(product)} 선택했습니다",
            "mobility": f"그래서 바퀴 움직임과 무게를 기준으로 {self._with_object_particle(product)} 선택했습니다",
            "durability": f"그래서 마감과 내구성을 기준으로 {self._with_object_particle(product)} 선택했습니다",
            "value": f"그래서 가격 대비 구성과 기능을 비교해 {self._with_object_particle(product)} 선택했습니다",
            "design": f"그래서 실용성과 디자인을 함께 보고 {self._with_object_particle(product)} 선택했습니다",
        }

        after_map = {
            "storage": "사용 후에는 필요한 짐을 넉넉히 담으면서도 내부 정리가 한결 쉬워졌습니다",
            "mobility": "사용 후에는 바퀴가 부드럽게 움직여 장거리 이동 부담이 줄었습니다",
            "durability": "사용 후에는 단단한 마감 덕분에 반복해서 써도 안정감이 느껴졌습니다",
            "value": "사용 후에는 필요한 기능을 충분히 활용하면서 구매 부담도 줄었습니다",
            "design": "사용 후에는 깔끔한 디자인과 실용성을 함께 만족할 수 있었습니다",
        }

        recommendation_map = {
            "storage": "짐이 많거나 내부 정리를 중요하게 보는 분께 특히 잘 맞습니다",
            "mobility": "공항이나 이동 구간이 길어 바퀴 사용감을 중요하게 보는 분께 잘 맞습니다",
            "durability": "한 번 구매해 오래 사용하려는 분께 잘 맞습니다",
            "value": "예산 안에서 필요한 기능을 놓치고 싶지 않은 분께 잘 맞습니다",
            "design": "실용성과 깔끔한 디자인을 함께 원하는 분께 잘 맞습니다",
        }

        before = before_map.get(
            review_type,
            f"사용 전에는 {pain} 때문에 선택이 쉽지 않았습니다",
        )
        choice = choice_map.get(
            review_type,
            f"그래서 실제 후기와 사용 목적을 기준으로 {self._with_object_particle(product)} 선택했습니다",
        )
        after = after_map.get(
            review_type,
            f"사용 후에는 {benefit_summary}을 실제로 체감할 수 있었습니다",
        )
        recommendation = recommendation_map.get(
            review_type,
            self._recommendation_sentence(
                product_name=product,
                evidence_summary=evidence,
                dominant_review_type=review_type,
            ),
        )

        if (
            "3박 4일" in evidence
            and "24인치" in evidence
            and review_type == "storage"
        ):
            choice = (
                "그래서 3박 4일 여행에 필요한 짐의 양을 기준으로 "
                f"{self._with_object_particle(product)} 선택했습니다"
            )

        return {
            "before": before,
            "choice": choice,
            "after": after,
            "recommendation": recommendation,
        }

    def _classify_review_types(
        self,
        review_quotes: Dict[str, Any],
        review_insight: Dict[str, Any],
        evidence_summary: str,
        benefit_summary: str,
    ) -> Dict[str, Any]:
        texts: List[str] = []

        for source in (review_quotes, review_insight):
            for key in (
                "best_quote",
                "best_evidence",
                "best_benefit",
                "best_result",
                "common_pattern",
                "review_common_pattern",
            ):
                value = self._clean_text(source.get(key))
                if value:
                    texts.append(value)

            for key in (
                "top_quotes",
                "reviews",
                "selected_reviews",
                "top_evidence",
                "evidence_candidates",
            ):
                values = source.get(key)
                if not isinstance(values, list):
                    continue

                for item in values[:30]:
                    value = self._clean_text(item)
                    if value:
                        texts.append(value)

        texts.extend(
            [
                self._clean_text(evidence_summary),
                self._clean_text(benefit_summary),
            ]
        )

        category_keywords = {
            "storage": (
                "수납",
                "많이 들어",
                "넉넉",
                "공간",
                "분리",
                "지퍼",
                "포켓",
                "정리",
            ),
            "mobility": (
                "바퀴",
                "부드럽",
                "이동",
                "가볍",
                "끌기",
                "손잡이",
                "회전",
            ),
            "durability": (
                "튼튼",
                "내구",
                "마감",
                "견고",
                "오래",
                "단단",
            ),
            "value": (
                "가성비",
                "가격 대비",
                "저렴",
                "가격",
                "합리",
                "이 가격",
            ),
            "design": (
                "디자인",
                "색상",
                "예쁘",
                "깔끔",
                "고급",
                "세련",
            ),
        }

        scores = {
            category: 0
            for category in category_keywords
        }

        matches = {
            category: []
            for category in category_keywords
        }

        for text in texts:
            normalized = self._clean_text(text)

            if not normalized:
                continue

            for category, keywords in category_keywords.items():
                matched = [
                    keyword
                    for keyword in keywords
                    if keyword in normalized
                ]

                if not matched:
                    continue

                scores[category] += len(matched)
                matches[category].extend(matched)

        priority = {
            "storage": 5,
            "mobility": 4,
            "durability": 3,
            "value": 2,
            "design": 1,
        }

        dominant_type = max(
            scores,
            key=lambda category: (
                scores.get(category, 0),
                priority.get(category, 0),
            ),
        )

        if scores.get(dominant_type, 0) <= 0:
            dominant_type = "general"

        labels = {
            "storage": "수납형",
            "mobility": "이동형",
            "durability": "내구형",
            "value": "가성비형",
            "design": "디자인형",
            "general": "일반형",
        }

        return {
            "dominant_type": dominant_type,
            "dominant_label": labels.get(
                dominant_type,
                "일반형",
            ),
            "scores": scores,
            "matches": {
                category: sorted(set(values))
                for category, values in matches.items()
            },
            "source_count": len(texts),
        }

    def _extract_common_pattern(
        self,
        review_quotes: Dict[str, Any],
        review_insight: Dict[str, Any],
        evidence_summary: str,
        benefit_summary: str,
        pain_summary: str,
        dominant_review_type: str,
    ) -> str:
        candidates: List[str] = []

        for source in (review_insight, review_quotes):
            for key in (
                "common_pattern",
                "review_common_pattern",
                "common_opinion",
                "pattern_summary",
                "best_reason",
                "reason_summary",
            ):
                value = self._clean_text(
                    source.get(key)
                )
                if value:
                    candidates.append(value)

            for key in (
                "top_evidence",
                "selected_evidence",
                "evidence_candidates",
                "top_quotes",
                "reviews",
            ):
                values = source.get(key)

                if isinstance(values, list):
                    for item in values[:12]:
                        cleaned = self._clean_text(item)
                        if cleaned:
                            candidates.append(cleaned)

        combined = " ".join(candidates)
        combined = self._clean_text(combined)

        evidence = self._clean_text(evidence_summary)
        benefit = self._clean_text(benefit_summary)
        pain = self._clean_text(pain_summary)
        dominant_type = self._clean_text(dominant_review_type)

        type_patterns = {
            "storage": (
                "고객들이 공통으로 말한 점은 "
                "생각보다 짐이 많이 들어가고 내부 정리가 편하다는 것입니다"
            ),
            "mobility": (
                "고객들이 공통으로 말한 점은 "
                "바퀴 움직임이 부드럽고 이동할 때 부담이 적다는 것입니다"
            ),
            "durability": (
                "고객들이 공통으로 말한 점은 "
                "마감이 단단하고 오래 사용하기 좋다는 것입니다"
            ),
            "value": (
                "고객들이 공통으로 말한 점은 "
                "가격 대비 구성과 사용 만족도가 높다는 것입니다"
            ),
            "design": (
                "고객들이 공통으로 말한 점은 "
                "디자인이 깔끔하고 실제 모습도 만족스럽다는 것입니다"
            ),
        }

        if dominant_type in type_patterns:
            return type_patterns[dominant_type]

        if (
            "24인치" in evidence
            and "3박 4일" in evidence
        ):
            features: List[str] = []

            if any(
                keyword in combined
                for keyword in (
                    "수납",
                    "많이 들어",
                    "넉넉",
                    "공간",
                )
            ) or "수납" in benefit:
                features.append("생각보다 짐이 많이 들어간다")

            if any(
                keyword in combined
                for keyword in (
                    "바퀴",
                    "부드럽",
                    "이동",
                    "가볍",
                    "끌기",
                )
            ):
                features.append("이동이 편하다")

            if not features:
                features = [
                    "필요한 짐을 넉넉히 담을 수 있다",
                    "이동할 때 부담이 적다",
                ]

            if len(features) >= 2:
                return (
                    "고객들이 공통으로 말한 점은 "
                    "생각보다 짐이 많이 들어가고 이동이 편하다는 것입니다"
                )

            return (
                "고객들이 공통으로 말한 점은 "
                f"{features[0]}는 것입니다"
            )

        if (
            "20인치" in evidence
            and "2박 3일" in evidence
        ):
            return (
                "고객들이 공통으로 말한 점은 "
                "짧은 여행에 필요한 짐은 충분히 담고 이동은 가볍다는 것입니다"
            )

        if "수납" in benefit:
            return (
                "고객들이 공통으로 말한 점은 "
                "수납공간이 넉넉하고 정리하기 편하다는 것입니다"
            )

        if "이동" in benefit:
            return (
                "고객들이 공통으로 말한 점은 "
                "가볍고 이동하기 편하다는 것입니다"
            )

        if pain:
            return (
                f"고객들이 공통으로 말한 점은 "
                f"{pain}에 대한 부담을 줄여준다는 것입니다"
            )

        return (
            f"고객들이 공통으로 말한 점은 "
            f"{benefit}을 실제 사용에서 체감한다는 것입니다"
        )

    def _common_pattern_sentence(
        self,
        common_pattern: str,
    ) -> str:
        text = self._clean_text(common_pattern)

        if not text:
            return "여러 후기에서 비슷한 만족 이유가 반복해서 확인됐습니다"

        return self._shorten(
            text,
            76,
        ).rstrip("…")

    def _reason_sentence(
        self,
        product_name: str,
        evidence_summary: str,
        benefit_summary: str,
        dominant_review_type: str = "",
    ) -> str:
        evidence = self._clean_text(evidence_summary)
        product = self._clean_text(product_name)
        review_type = self._clean_text(dominant_review_type)

        type_reasons = {
            "storage": "가장 큰 이유는 필요한 짐을 넉넉하게 담고도 내부 정리가 편하기 때문입니다",
            "mobility": "가장 큰 이유는 바퀴 움직임이 부드럽고 오래 끌어도 부담이 적기 때문입니다",
            "durability": "가장 큰 이유는 마감이 단단하고 반복 사용에도 안정감이 있기 때문입니다",
            "value": "가장 큰 이유는 가격 대비 필요한 기능과 구성이 충분하기 때문입니다",
            "design": "가장 큰 이유는 실용성을 유지하면서도 디자인이 깔끔하기 때문입니다",
        }

        if review_type in type_reasons:
            return type_reasons[review_type]

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
        dominant_review_type: str = "",
    ) -> str:
        product = self._clean_text(product_name)
        review_type = self._clean_text(dominant_review_type)

        type_benefits = {
            "storage": "넉넉한 수납과 분리 정리 덕분에 여행 준비가 편해집니다",
            "mobility": "부드러운 이동감 덕분에 공항이나 장거리 이동이 편해집니다",
            "durability": "튼튼한 마감 덕분에 여러 번 사용해도 안정적으로 쓸 수 있습니다",
            "value": "가격 대비 구성이 좋아 부담을 줄이면서 필요한 기능을 챙길 수 있습니다",
            "design": "깔끔한 디자인 덕분에 실용성과 외관 만족을 함께 챙길 수 있습니다",
        }

        if review_type in type_benefits:
            return type_benefits[review_type]

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
        dominant_review_type: str = "",
    ) -> str:
        evidence = self._clean_text(evidence_summary)
        product = self._clean_text(product_name)
        review_type = self._clean_text(dominant_review_type)

        type_recommendations = {
            "storage": "짐이 많거나 수납 구성을 중요하게 보는 분께 잘 맞습니다",
            "mobility": "이동이 많고 바퀴 사용감을 중요하게 보는 분께 잘 맞습니다",
            "durability": "한 번 구매해 오래 사용하려는 분께 잘 맞습니다",
            "value": "예산 안에서 실용적인 구성을 찾는 분께 잘 맞습니다",
            "design": "깔끔한 디자인과 실용성을 함께 원하는 분께 잘 맞습니다",
        }

        if review_type in type_recommendations:
            return type_recommendations[review_type]

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

        script_type = self._clean_text(script.get("type", ""))

        if script_type.startswith("short_"):
            priority_order = (
                "strategy",
                "target",
                "problem",
                "recommendation",
                "choice",
                "support",
                "detail",
                "trust",
                "common_pattern",
                "risk",
            )
        elif script_type.startswith("long_"):
            priority_order = (
                "risk",
                "common_pattern",
                "target",
                "strategy",
                "recommendation",
                "support",
                "detail",
                "trust",
            )
        else:
            priority_order = (
                "risk",
                "common_pattern",
                "recommendation",
                "support",
                "detail",
                "trust",
                "strategy",
                "target",
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
                key: self._shorten_natural(
                    value,
                    46 if key == "hook" else 42,
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

    def _apply_bridge_library(
        self,
        sections: Dict[str, str],
        script_length: str,
        product_type: str,
        shorts_strategy: str,
        psychology_type: str,
    ) -> Dict[str, str]:
        """
        Sprint80-2 Bridge Library

        기존 섹션의 의미와 키는 유지하면서 다음 문장 첫머리에
        짧은 연결 표현을 붙여 대본 흐름을 자연스럽게 만듭니다.
        """
        cleaned_sections = {
            key: self._sentence(value)
            for key, value in sections.items()
            if self._clean_text(value)
        }

        if len(cleaned_sections) <= 1:
            return cleaned_sections

        result: Dict[str, str] = {}
        used_bridges: List[str] = []
        previous_key = ""

        for current_key, sentence in cleaned_sections.items():
            text = self._clean_text(sentence)

            if not result:
                result[current_key] = self._sentence(text)
                previous_key = current_key
                continue

            bridge = self._select_bridge(
                previous_key=previous_key,
                current_key=current_key,
                script_length=script_length,
                product_type=product_type,
                shorts_strategy=shorts_strategy,
                psychology_type=psychology_type,
                sentence=text,
                used_bridges=used_bridges,
            )

            if bridge:
                text = self._join_bridge_sentence(
                    bridge=bridge,
                    sentence=text,
                )
                used_bridges.append(bridge)

            result[current_key] = self._sentence(text)
            previous_key = current_key

        return result

    def _select_bridge(
        self,
        previous_key: str,
        current_key: str,
        script_length: str,
        product_type: str,
        shorts_strategy: str,
        psychology_type: str,
        sentence: str,
        used_bridges: List[str],
    ) -> str:
        text = self._clean_text(sentence)

        if not text or self._starts_with_bridge(text):
            return ""

        semantic_starters = {
            "strategy": ("선택 기준은", "핵심은", "실제 선택 기준은"),
            "after": ("사용 후에는", "사용하고 나니", "써보니"),
            "cta": ("여행 전에", "구매 전에", "선택 전에"),
            "evidence": ("실제 구매 후기", "실제 후기를", "후기에서"),
            "recommendation": ("짐이", "이동이", "한 번 구매", "예산 안에서", "실용성과"),
        }

        if text.startswith(semantic_starters.get(current_key, ())):
            return ""

        pair_library = {
            ("hook", "problem"): ("실제로", "그런데"),
            ("hook", "empathy"): ("막상 고르려면", "특히"),
            ("problem", "empathy"): ("그래서", "실제로"),
            ("empathy", "risk"): ("문제는", "더 중요한 건"),
            ("problem", "target"): ("특히", "그래서"),
            ("empathy", "target"): ("특히", "이럴 때"),
            ("risk", "target"): ("그래서", "이럴수록"),
            ("target", "strategy"): ("결국", "여기서 볼 건"),
            ("strategy", "evidence"): ("실제 후기를 보면", "그리고"),
            ("target", "evidence"): ("실제 후기를 보면", "무엇보다"),
            ("evidence", "common_pattern"): ("여러 후기를 함께 보면", "공통적으로"),
            ("evidence", "choice"): ("그래서", "이 기준으로"),
            ("common_pattern", "choice"): ("그래서", "결국"),
            ("choice", "after"): ("직접 써보니", "사용해 보니"),
            ("evidence", "after"): ("실제로 사용해 보면", "그 결과"),
            ("after", "recommendation"): ("그래서", "이런 이유로"),
            ("recommendation", "cta"): ("구매 전에는", "마지막으로"),
            ("after", "cta"): ("구매 전에는", "마지막으로"),
            ("evidence", "cta"): ("구매 전에는", "결론적으로"),
        }

        current_library = {
            "target": ("특히", "이럴 때"),
            "strategy": ("핵심은", "결국"),
            "evidence": ("실제 후기를 보면", "무엇보다"),
            "choice": ("그래서", "이 기준으로"),
            "after": ("직접 써보니", "그 결과"),
            "recommendation": ("그래서", "이런 이유로"),
            "cta": ("구매 전에는", "마지막으로"),
        }

        candidates = list(
            pair_library.get(
                (previous_key, current_key),
                current_library.get(current_key, ()),
            )
        )

        contextual = self._context_bridge_candidates(
            current_key=current_key,
            product_type=product_type,
            shorts_strategy=shorts_strategy,
            psychology_type=psychology_type,
        )

        candidates = contextual + candidates
        candidates = [
            item
            for item in candidates
            if item and item not in used_bridges[-2:]
        ]

        if not candidates:
            return ""

        if script_length == "short":
            candidates = [
                item
                for item in candidates
                if len(item) <= 8
            ] or candidates

        seed = sum(
            ord(char)
            for char in (
                previous_key
                + current_key
                + product_type
                + psychology_type
                + text[:12]
            )
        )

        return candidates[seed % len(candidates)]

    def _context_bridge_candidates(
        self,
        current_key: str,
        product_type: str,
        shorts_strategy: str,
        psychology_type: str,
    ) -> List[str]:
        candidates: List[str] = []

        psychology_map = {
            "comparison": {
                "strategy": "비교해 보면",
                "evidence": "기준을 잡고 보면",
                "choice": "이 기준으로",
            },
            "mistake_prevention": {
                "risk": "놓치기 쉬운 건",
                "strategy": "실패를 줄이려면",
                "evidence": "구매 전에 확인할 건",
            },
            "anxiety": {
                "empathy": "그럴 수밖에 없는 게",
                "target": "이럴수록",
                "evidence": "안심하려면",
            },
            "empathy": {
                "empathy": "비슷한 고민이 생기는 이유는",
                "target": "특히",
                "after": "직접 써보면",
            },
            "recommendation": {
                "evidence": "실사용자 의견을 보면",
                "recommendation": "그래서",
                "cta": "선택 전에",
            },
        }

        product_map = {
            "travel": {
                "strategy": "여행 기준으로 보면",
                "choice": "짐의 양을 기준으로",
            },
            "household": {
                "strategy": "매일 쓰는 만큼",
                "after": "생활 속에서 써보면",
            },
            "kitchen": {
                "strategy": "자주 쓰는 제품이라",
                "after": "직접 사용해 보면",
            },
            "electronics": {
                "evidence": "성능은 실제 사용에서",
                "strategy": "스펙보다 중요한 건",
            },
            "seasonal": {
                "target": "필요한 시기가 오기 전에",
                "strategy": "계절 불편을 줄이려면",
            },
        }

        strategy_map = {
            "comparison": {
                "strategy": "비교할 때는",
                "choice": "이 기준으로",
            },
            "problem_solution": {
                "strategy": "해결 기준은",
                "after": "불편을 줄이고 나면",
            },
            "convenience_experience": {
                "after": "직접 써보면",
                "recommendation": "사용감까지 보면",
            },
            "performance_proof": {
                "evidence": "실제 성능을 보면",
                "choice": "검증된 기준으로",
            },
            "seasonal_empathy": {
                "target": "특히 이 계절에는",
                "strategy": "미리 준비하면",
            },
        }

        for mapping, key in (
            (psychology_map, psychology_type),
            (product_map, product_type),
            (strategy_map, shorts_strategy),
        ):
            bridge = mapping.get(key, {}).get(current_key, "")
            if bridge:
                candidates.append(bridge)

        return candidates

    def _starts_with_bridge(
        self,
        sentence: str,
    ) -> bool:
        text = self._clean_text(sentence)
        starters = (
            "그래서",
            "그런데",
            "그리고",
            "특히",
            "결국",
            "실제로",
            "무엇보다",
            "문제는",
            "핵심은",
            "이럴 때",
            "이럴수록",
            "직접 써보",
            "사용해 보",
            "구매 전",
            "마지막으로",
            "공통적으로",
            "여러 후기를",
            "실제 후기를",
            "실사용자",
            "선택 전에",
            "선택 기준은",
            "사용 후에는",
            "여행 전에",
            "후기에서",
            "실제 구매 후기",
        )
        return text.startswith(starters)

    def _join_bridge_sentence(
        self,
        bridge: str,
        sentence: str,
    ) -> str:
        bridge_text = self._clean_text(bridge).rstrip(" ,.!?")
        sentence_text = self._clean_text(sentence).lstrip(" ,")

        if not bridge_text or not sentence_text:
            return sentence_text

        if sentence_text.startswith(bridge_text):
            return sentence_text

        sentence_text = sentence_text[0].lower() + sentence_text[1:] if sentence_text[:1].isascii() else sentence_text

        comma_bridges = (
            "문제는",
            "핵심은",
            "여기서 볼 건",
            "더 중요한 건",
            "놓치기 쉬운 건",
            "스펙보다 중요한 건",
            "해결 기준은",
        )

        separator = ", " if bridge_text in comma_bridges else " "
        return f"{bridge_text}{separator}{sentence_text}"

    def _score_script_quality(
        self,
        script: Dict[str, Any],
        story_context: Dict[str, Any],
        emotion_curve: Dict[str, Any],
        review_count: int,
    ) -> Dict[str, Any]:
        result = dict(script)
        text = self._clean_text(result.get("text", ""))
        sections = result.get("sections", {})
        if not isinstance(sections, dict):
            sections = {}

        story_keys = ("problem", "emotion", "decision", "change", "result")
        story_values = [
            self._clean_text(story_context.get(key, ""))
            for key in story_keys
        ]
        story_present = sum(
            1 for value in story_values
            if value and self._meaning_overlap(text, value)
        )
        story_score = min(100, 55 + story_present * 9)
        if any(key in sections for key in ("choice", "after", "recommendation")):
            story_score = min(100, story_score + 6)

        emotion_keys = ("empathy", "tension", "relief", "satisfaction")
        emotion_present = sum(
            1
            for key in emotion_keys
            if self._meaning_overlap(
                text,
                self._clean_text(emotion_curve.get(key, "")),
            )
        )
        emotion_score = min(100, 58 + emotion_present * 9)
        if "?" in text:
            emotion_score = min(100, emotion_score + 6)

        sentence_count = max(1, len(result.get("lines", [])))
        duplicate_penalty = self._repetition_penalty(text)
        fragment_penalty = 18 if "…" in text else 0
        natural_score = max(0, min(100, 96 - duplicate_penalty - fragment_penalty))
        if sentence_count >= 6:
            natural_score = min(100, natural_score + 2)

        evidence_markers = (
            "후기", "구매자", "리뷰", "실제", "가장 많이 나온 말",
        )
        evidence_hits = sum(1 for marker in evidence_markers if marker in text)
        evidence_score = min(100, 62 + evidence_hits * 7)
        if review_count > 0 and str(review_count) in text:
            evidence_score = min(100, evidence_score + 10)

        duration_status = result.get("duration_status", "")
        duration_error = abs(self._safe_int(result.get("duration_error", 0)))
        duration_score = 100 if duration_status == "ok" else max(40, 100 - duration_error * 5)
        hook_score = 100 if result.get("lines") and ("?" in result["lines"][0] or len(result["lines"][0]) <= 42) else 84
        retention_score = round(
            hook_score * 0.35
            + emotion_score * 0.25
            + natural_score * 0.20
            + duration_score * 0.20
        )

        quality_score = round(
            story_score * 0.24
            + emotion_score * 0.20
            + natural_score * 0.22
            + evidence_score * 0.16
            + retention_score * 0.18
        )

        result.update({
            "score_engine_version": "story-score-engine-81-3",
            "story_score": int(story_score),
            "emotion_score": int(emotion_score),
            "natural_score": int(natural_score),
            "evidence_score": int(evidence_score),
            "retention_score": int(retention_score),
            "quality_score": int(quality_score),
            "quality_grade": self._quality_grade(quality_score),
        })
        return result

    def _validate_final_script(
        self,
        best_script: Dict[str, Any],
        optimized_script: str,
        optimized_platform_scripts: Dict[str, Any],
        hook_variation: Dict[str, Any],
        cta_optimization: Dict[str, Any],
        story_context: Dict[str, str],
        emotion_curve: Dict[str, str],
        review_count: int,
    ) -> Dict[str, Any]:
        """Validate the final script package without changing selected outputs."""
        script_text = self._clean_text(
            optimized_script or best_script.get("text", "")
        )
        warnings: List[str] = []
        improvement_priority: List[str] = []

        sentences = [
            self._clean_text(item)
            for item in re.split(r"(?<=[.!?])\s+", script_text)
            if self._clean_text(item)
        ]
        normalized_sentences = [
            re.sub(r"[^0-9A-Za-z가-힣]", "", item)
            for item in sentences
        ]
        duplicate_count = max(
            0,
            len(normalized_sentences) - len(set(normalized_sentences)),
        )
        repetition_score = max(0, 100 - duplicate_count * 25)
        if duplicate_count:
            warnings.append("반복 문장이 감지되었습니다")
            improvement_priority.append("repetition")

        natural_score = self._safe_int(best_script.get("natural_score"))
        if natural_score <= 0:
            natural_score = 85 if script_text else 0
        if natural_score < 80:
            warnings.append("문장 자연스러움 점검이 필요합니다")
            improvement_priority.append("natural")

        selected_hook = self._clean_text(
            hook_variation.get("selected_hook")
        )
        hook_score = self._safe_int(
            hook_variation.get("selected_hook_score")
        )
        if not selected_hook:
            hook_score = 0
            warnings.append("선택된 후킹이 없습니다")
            improvement_priority.append("hook")
        elif hook_score < 60:
            warnings.append("후킹 점수가 낮습니다")
            improvement_priority.append("hook")

        cta_score = self._safe_int(cta_optimization.get("cta_score"))
        platform_cta = cta_optimization.get("platform_cta", {})
        if not isinstance(platform_cta, dict) or len(platform_cta) < 3:
            cta_score = min(cta_score, 50)
            warnings.append("플랫폼별 CTA가 충분하지 않습니다")
            improvement_priority.append("cta")

        story_fields = ("problem", "emotion", "decision", "change", "result")
        story_present = sum(
            1 for key in story_fields if self._clean_text(story_context.get(key))
        )
        story_score = round(story_present / len(story_fields) * 100)
        if story_score < 80:
            warnings.append("스토리 구조 일부가 비어 있습니다")
            improvement_priority.append("story")

        emotion_fields = ("hook", "empathy", "tension", "relief", "satisfaction")
        emotion_present = sum(
            1 for key in emotion_fields if self._clean_text(emotion_curve.get(key))
        )
        emotion_score = round(emotion_present / len(emotion_fields) * 100)
        if emotion_score < 80:
            warnings.append("감정선 일부가 비어 있습니다")
            improvement_priority.append("emotion")

        required_platforms = ("tiktok", "instagram_reels", "youtube_shorts")
        platform_present = 0
        for platform in required_platforms:
            item = optimized_platform_scripts.get(platform, {})
            platform_text = (
                item.get("script", "")
                if isinstance(item, dict)
                else item
            )
            if self._clean_text(platform_text):
                platform_present += 1
        platform_score = round(platform_present / len(required_platforms) * 100)
        if platform_score < 100:
            warnings.append("일부 플랫폼 대본이 비어 있습니다")
            improvement_priority.append("platform")

        evidence_score = self._safe_int(best_script.get("evidence_score"))
        if review_count <= 0:
            evidence_score = min(evidence_score, 60)
            warnings.append("후기 근거 수가 부족합니다")
            improvement_priority.append("evidence")

        retention_score = self._safe_int(best_script.get("retention_score"))
        quality_score = self._safe_int(best_script.get("quality_score"))
        scores = {
            "story": story_score,
            "emotion": emotion_score,
            "hook": hook_score,
            "cta": cta_score,
            "natural": natural_score,
            "platform": platform_score,
            "retention": retention_score,
            "evidence": evidence_score,
            "repetition": repetition_score,
            "base_quality": quality_score,
        }

        weights = {
            "story": 0.14,
            "emotion": 0.12,
            "hook": 0.12,
            "cta": 0.10,
            "natural": 0.14,
            "platform": 0.10,
            "retention": 0.10,
            "evidence": 0.10,
            "repetition": 0.08,
        }
        final_quality_score = round(
            sum(scores[key] * weight for key, weight in weights.items())
        )
        passed = bool(script_text) and final_quality_score >= 80 and not any(
            scores.get(key, 0) < 60
            for key in ("story", "emotion", "hook", "cta", "natural", "platform")
        )

        priority_order = (
            "hook", "natural", "story", "emotion", "cta",
            "platform", "evidence", "retention", "repetition",
        )
        improvement_priority = [
            key for key in priority_order if key in set(improvement_priority)
        ]

        return {
            "version": "final-script-validator-81-9",
            "built": bool(script_text),
            "passed": passed,
            "status": "pass" if passed else "review",
            "final_quality_score": final_quality_score,
            "scores": scores,
            "warnings": warnings,
            "improvement_priority": improvement_priority,
            "sentence_count": len(sentences),
            "duplicate_sentence_count": duplicate_count,
            "platform_count": platform_present,
            "review_count": self._safe_int(review_count),
        }

    def _build_hook_variations(
        self,
        original_hook: str,
        product_name: str,
        product_type: str,
        shorts_strategy: str,
        psychology_type: str,
        target_customer: str,
        pain_summary: str,
        evidence_summary: str,
        review_count: int,
    ) -> Dict[str, Any]:
        """Create and score reusable hook variations without changing the base script."""
        original = self._clean_text(original_hook)
        product = self._clean_text(product_name)
        product_type_text = self._clean_text(product_type)
        strategy = self._clean_text(shorts_strategy)
        psychology = self._clean_text(psychology_type)
        target = self._clean_text(target_customer)
        pain = self._clean_text(pain_summary)
        evidence = self._clean_text(evidence_summary)
        count = self._safe_int(review_count)

        if product_type_text == "travel" and "24인치" in evidence:
            comparison = "20인치와 24인치, 어떤 걸 골라야 할까요?"
            mistake = "3박 4일 여행에 캐리어 크기를 잘못 고르면 짐 정리가 더 힘들어집니다"
            empathy = "3박 4일 여행인데 캐리어 크기 때문에 고민하고 계신가요?"
            curiosity = "3박 4일 여행에는 왜 24인치가 많이 선택될까요?"
        else:
            comparison = f"비슷해 보이는 {product}, 무엇을 기준으로 골라야 할까요?"
            mistake = f"{product}를 기준 없이 고르면 구매 후 아쉬움이 남을 수 있습니다"
            empathy = f"{pain} 때문에 제품 선택을 미루고 계신가요?"
            curiosity = f"{product} 후기에서 가장 많이 나온 선택 기준은 무엇일까요?"

        review_hook = (
            f"구매 후기 {count}개에서 가장 많이 언급된 기준을 확인했습니다"
            if count > 0
            else f"실제 후기에서 반복된 {product} 선택 기준을 확인했습니다"
        )
        target_hook = (
            f"{target}이라면 이 선택 기준부터 확인해야 합니다"
            if target
            else f"{product}를 찾는 분이라면 이 기준부터 확인해 보세요"
        )

        candidates = [
            ("original", original),
            ("curiosity", curiosity),
            ("comparison", comparison),
            ("mistake_prevention", mistake),
            ("empathy", empathy),
            ("review_evidence", review_hook),
            ("target_specific", target_hook),
        ]

        type_bonus = {
            "comparison": 8 if strategy == "comparison" or psychology == "comparison" else 3,
            "mistake_prevention": 8 if psychology == "mistake_prevention" else 4,
            "empathy": 8 if psychology == "empathy" else 4,
            "review_evidence": 7 if count > 0 else 3,
            "target_specific": 6 if target else 2,
            "curiosity": 6,
            "original": 5,
        }

        hook_variations: List[Dict[str, Any]] = []
        seen = set()
        for hook_type, hook_text in candidates:
            cleaned = self._clean_text(hook_text)
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)

            length = len(cleaned)
            length_score = 24 if 18 <= length <= 52 else 18 if length <= 70 else 10
            question_score = 12 if cleaned.endswith("?") or "까요" in cleaned else 7
            specificity_score = 0
            if product and product in cleaned:
                specificity_score += 8
            if any(token in cleaned for token in ("3박 4일", "24인치", "후기", str(count) if count else "__none__")):
                specificity_score += 8
            relevance_score = 30
            score = min(
                100,
                20 + length_score + question_score + specificity_score + type_bonus.get(hook_type, 0),
            )
            hook_variations.append(
                {
                    "type": hook_type,
                    "text": cleaned,
                    "score": score,
                    "length": length,
                    "source": "hook_variation_engine",
                }
            )

        hook_variations.sort(
            key=lambda item: (
                item.get("score", 0),
                item.get("type") == psychology,
                -item.get("length", 0),
            ),
            reverse=True,
        )
        selected = hook_variations[0] if hook_variations else {
            "type": "original",
            "text": original,
            "score": 0,
        }

        return {
            "version": "hook-variation-engine-81-8",
            "built": bool(hook_variations),
            "hook_count": len(hook_variations),
            "hook_variations": hook_variations,
            "selected_hook": selected.get("text", original),
            "selected_hook_type": selected.get("type", "original"),
            "selected_hook_score": selected.get("score", 0),
            "selection_basis": {
                "product_type": product_type_text,
                "shorts_strategy": strategy,
                "psychology_type": psychology,
                "review_count": count,
            },
        }

    def _adapt_script_for_platforms(
        self,
        optimized_script: str,
        product_name: str,
        product_type: str,
        shorts_strategy: str,
    ) -> Dict[str, Any]:
        """Adapt one optimized narrative for TikTok, Reels, and Shorts."""
        base = self._clean_text(optimized_script)
        product = self._clean_text(product_name)

        if not base:
            return {
                "version": "platform-adaptation-engine-81-6",
                "built": False,
                "adaptation_score": 0,
                "platform_scripts": {},
            }

        sentences = [
            self._clean_text(item)
            for item in re.split(r"(?<=[.!?])\s+", base)
            if self._clean_text(item)
        ]
        hook = sentences[0] if sentences else base
        body = " ".join(sentences[1:]).strip()

        def replace_last_cta(text: str, cta: str) -> str:
            parts = [
                self._clean_text(item)
                for item in re.split(r"(?<=[.!?])\s+", text)
                if self._clean_text(item)
            ]
            if not parts:
                return self._sentence(cta)
            if parts[-1].endswith(("보세요.", "확인해 보세요.", "비교해 보세요.", "선택해 보세요.")):
                parts[-1] = self._sentence(cta)
            else:
                parts.append(self._sentence(cta))
            return self._clean_text(" ".join(parts))

        tiktok_hook = self._shorten(hook, 58).rstrip("…")
        tiktok_body = self._shorten(body, 330).rstrip("…")
        tiktok_text = self._clean_text(
            " ".join(item for item in (tiktok_hook, tiktok_body) if item)
        )
        tiktok_text = replace_last_cta(
            tiktok_text,
            "구매 전에는 프로필 링크에서 후기와 구성을 확인해 보세요",
        )

        reels_text = replace_last_cta(
            base,
            "나중에 비교할 수 있도록 저장해 두고 프로필 링크도 확인해 보세요",
        )

        youtube_text = replace_last_cta(
            base,
            "제품 정보와 실제 후기는 설명란 링크에서 확인해 보세요",
        )

        platform_scripts = {
            "tiktok": {
                "platform": "tiktok",
                "script": tiktok_text,
                "hook_style": "fast_curiosity",
                "cta_style": "profile_link",
                "estimated_seconds": self._estimate_seconds(tiktok_text),
            },
            "instagram_reels": {
                "platform": "instagram_reels",
                "script": reels_text,
                "hook_style": "empathy_save",
                "cta_style": "save_and_profile",
                "estimated_seconds": self._estimate_seconds(reels_text),
            },
            "youtube_shorts": {
                "platform": "youtube_shorts",
                "script": youtube_text,
                "hook_style": "search_explanation",
                "cta_style": "description_link",
                "estimated_seconds": self._estimate_seconds(youtube_text),
            },
        }

        complete_count = sum(
            1
            for item in platform_scripts.values()
            if item.get("script") and item.get("cta_style")
        )
        adaptation_score = min(100, 70 + complete_count * 10)

        return {
            "version": "platform-adaptation-engine-81-6",
            "built": complete_count == 3,
            "adaptation_score": adaptation_score,
            "source": "optimized_script",
            "product_name": product,
            "product_type": self._clean_text(product_type),
            "shorts_strategy": self._clean_text(shorts_strategy),
            "platform_scripts": platform_scripts,
        }


    def _optimize_platform_ctas(
        self,
        platform_scripts: Dict[str, Any],
        product_name: str,
        product_type: str,
        shorts_strategy: str,
        review_count: int,
    ) -> Dict[str, Any]:
        """Select and apply platform-appropriate CTAs without changing the narrative body."""
        product = self._clean_text(product_name)
        product_type_text = self._clean_text(product_type)
        strategy = self._clean_text(shorts_strategy)
        count = self._safe_int(review_count)

        cta_library = {
            "profile_link": "프로필 링크에서 제품 정보와 후기를 확인해 보세요",
            "save_profile": "나중에 비교할 수 있도록 저장해 두고 프로필 링크도 확인해 보세요",
            "description_link": "제품 정보와 실제 후기는 설명란 링크에서 확인해 보세요",
            "comment_question": "어떤 기준이 가장 궁금한지 댓글로 남겨주세요",
            "follow_more": "비슷한 제품 비교가 필요하다면 팔로우해 두세요",
            "review_check": "구매 전에는 실제 후기와 구성을 꼭 확인해 보세요",
        }

        platform_preferences = {
            "tiktok": ("profile_link", "comment_question", "follow_more"),
            "instagram_reels": ("save_profile", "profile_link", "comment_question"),
            "youtube_shorts": ("description_link", "comment_question", "follow_more"),
        }

        selected_cta: Dict[str, str] = {}
        platform_cta: Dict[str, Any] = {}
        optimized: Dict[str, Any] = {}

        for platform_name, source_data in platform_scripts.items():
            preferences = platform_preferences.get(
                platform_name,
                ("review_check",),
            )
            cta_key = preferences[0]
            if count <= 0 and "review_check" in cta_library:
                cta_key = "review_check"
            elif product_type_text == "travel" and platform_name == "instagram_reels":
                cta_key = "save_profile"
            elif strategy == "performance_proof" and platform_name == "youtube_shorts":
                cta_key = "description_link"

            cta_text = cta_library[cta_key]
            selected_cta[platform_name] = cta_text
            original_script = self._clean_text(source_data.get("script", ""))
            final_script = self._replace_or_append_cta(original_script, cta_text)

            natural_score = 100 if final_script else 0
            conversion_score = {
                "profile_link": 96,
                "save_profile": 94,
                "description_link": 96,
                "comment_question": 88,
                "follow_more": 84,
                "review_check": 86,
            }.get(cta_key, 80)
            platform_fit_score = 100 if cta_key == preferences[0] else 92
            total_score = round(
                natural_score * 0.35
                + conversion_score * 0.35
                + platform_fit_score * 0.30
            )

            platform_cta[platform_name] = {
                "cta_key": cta_key,
                "selected_cta": cta_text,
                "natural_score": natural_score,
                "conversion_score": conversion_score,
                "platform_fit_score": platform_fit_score,
                "cta_score": total_score,
            }
            optimized[platform_name] = {
                **dict(source_data),
                "script": final_script,
                "selected_cta": cta_text,
                "cta_key": cta_key,
                "cta_score": total_score,
                "cta_optimizer_version": "cta-optimization-engine-81-7",
                "estimated_seconds": self._estimate_seconds(final_script),
            }

        scores = [
            item.get("cta_score", 0)
            for item in platform_cta.values()
        ]
        cta_score = round(sum(scores) / len(scores)) if scores else 0

        return {
            "version": "cta-optimization-engine-81-7",
            "built": len(optimized) == 3,
            "product_name": product,
            "product_type": product_type_text,
            "shorts_strategy": strategy,
            "review_count": count,
            "cta_library": cta_library,
            "platform_cta": platform_cta,
            "selected_cta": selected_cta,
            "cta_score": cta_score,
            "optimized_platform_scripts": optimized,
        }

    def _replace_or_append_cta(
        self,
        script_text: str,
        cta_text: str,
    ) -> str:
        text = self._clean_text(script_text)
        cta = self._sentence(cta_text)
        if not text:
            return cta

        parts = [
            self._clean_text(item)
            for item in re.split(r"(?<=[.!?])\s+", text)
            if self._clean_text(item)
        ]
        if not parts:
            return cta

        cta_markers = (
            "확인해 보세요",
            "비교해 보세요",
            "저장해",
            "프로필 링크",
            "설명란 링크",
            "댓글로",
            "팔로우",
        )
        if any(marker in parts[-1] for marker in cta_markers):
            parts[-1] = cta
        else:
            parts.append(cta)
        return self._clean_text(" ".join(parts))

    def _optimize_selected_narrative(
        self,
        script: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Polish only the already-selected script without changing its meaning."""
        original = self._clean_text(script.get("text", ""))
        if not original:
            return {
                "version": "narrative-optimizer-81-5",
                "applied": False,
                "original_text": "",
                "optimized_text": "",
                "changes": [],
                "optimization_score": 0,
            }

        optimized = original
        changes: List[str] = []

        phrase_replacements = (
            ("막상 고르려면 너무 작으면", "막상 고르려니, 너무 작으면"),
            ("실제 구매 후기", "구매 후기"),
            ("가장 많이 나온 말은", "가장 많이 언급된 내용은"),
            ("사용 후에는 필요한", "사용해 보니 필요한"),
            ("실제로 실제", "실제로"),
            ("특히 특히", "특히"),
            ("그래서 그래서", "그래서"),
        )
        for before, after in phrase_replacements:
            if before in optimized:
                optimized = optimized.replace(before, after)
                changes.append(f"표현 자연화: {before}")

        sentences = [
            self._clean_text(item)
            for item in re.findall(r"[^.!?]+[.!?]?", optimized)
            if self._clean_text(item)
        ]

        deduped: List[str] = []
        for sentence in sentences:
            normalized = re.sub(r"[.!?]+$", "", sentence).strip()
            if any(
                re.sub(r"[.!?]+$", "", previous).strip() == normalized
                for previous in deduped
            ):
                changes.append("중복 문장 제거")
                continue
            deduped.append(sentence)

        balanced: List[str] = []
        for sentence in deduped:
            clean = self._clean_text(sentence)
            if len(clean) > 92 and "," in clean:
                left, right = clean.split(",", 1)
                left = left.strip()
                right = right.strip()
                if len(left) >= 18 and len(right) >= 18:
                    punctuation = "?" if clean.endswith("?") else "."
                    balanced.append(self._sentence(left))
                    balanced.append(self._sentence(right.rstrip(".!?")) if punctuation == "." else right)
                    changes.append("긴 문장 호흡 분리")
                    continue
            balanced.append(sentence)

        optimized = " ".join(balanced)
        optimized = re.sub(r"\s+", " ", optimized).strip()
        optimized = re.sub(r"\.\s*\.", ".", optimized)

        original_repetition = self._repetition_penalty(original)
        optimized_repetition = self._repetition_penalty(optimized)
        rhythm_penalty = sum(
            max(0, len(self._clean_text(item)) - 88) // 8
            for item in re.findall(r"[^.!?]+[.!?]?", optimized)
        )
        optimization_score = max(
            0,
            min(
                100,
                96
                - optimized_repetition
                - rhythm_penalty
                + min(4, len(set(changes))),
            ),
        )

        applied = optimized != original
        if not applied:
            changes = []

        return {
            "version": "narrative-optimizer-81-5",
            "applied": applied,
            "original_text": original,
            "optimized_text": optimized,
            "changes": list(dict.fromkeys(changes)),
            "original_repetition_penalty": original_repetition,
            "optimized_repetition_penalty": optimized_repetition,
            "optimization_score": int(optimization_score),
            "selected_script_type": self._clean_text(script.get("type", "")),
            "quality_gate_status": self._clean_text(
                script.get("quality_gate_status", "")
            ),
        }

    def _apply_story_quality_gate(
        self,
        script: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate existing Story Score results without rebuilding the script."""
        result = dict(script)

        thresholds = {
            "quality": 85,
            "story": 80,
            "emotion": 75,
            "natural": 85,
            "evidence": 75,
            "retention": 85,
        }

        score_fields = {
            "quality": "quality_score",
            "story": "story_score",
            "emotion": "emotion_score",
            "natural": "natural_score",
            "evidence": "evidence_score",
            "retention": "retention_score",
        }

        scores = {
            name: self._safe_int(result.get(field, 0))
            for name, field in score_fields.items()
        }

        weak_dimensions = [
            name
            for name, minimum in thresholds.items()
            if scores.get(name, 0) < minimum
        ]

        duration_ok = result.get("duration_status", "") == "ok"
        if not duration_ok:
            weak_dimensions.append("duration")

        priority_labels = {
            "quality": "전체 완성도",
            "story": "스토리 흐름",
            "emotion": "감정 곡선",
            "natural": "문장 자연스러움",
            "evidence": "후기 근거",
            "retention": "시청 유지력",
            "duration": "목표 영상 길이",
        }

        scored_weaknesses = [
            (
                name,
                thresholds[name] - scores.get(name, 0),
            )
            for name in weak_dimensions
            if name in thresholds
        ]
        scored_weaknesses.sort(
            key=lambda item: (
                item[1],
                item[0],
            ),
            reverse=True,
        )

        improvement_priority = [
            priority_labels.get(name, name)
            for name, _ in scored_weaknesses
        ]
        if "duration" in weak_dimensions:
            improvement_priority.append(priority_labels["duration"])

        passed = not weak_dimensions
        if passed:
            status = "pass"
        elif scores.get("quality", 0) >= 80 and duration_ok:
            status = "review"
        else:
            status = "revise"

        result.update({
            "quality_gate_version": "story-quality-gate-81-4",
            "quality_gate_passed": passed,
            "quality_gate_status": status,
            "quality_gate_thresholds": thresholds,
            "quality_gate_scores": scores,
            "quality_gate_weak_dimensions": weak_dimensions,
            "quality_gate_improvement_priority": improvement_priority,
        })
        return result

    def _meaning_overlap(self, text: str, sentence: str) -> bool:
        source = self._clean_text(text)
        target = self._clean_text(sentence)
        if not source or not target:
            return False
        tokens = [
            token
            for token in re.findall(r"[가-힣A-Za-z0-9]+", target)
            if len(token) >= 2
        ]
        if not tokens:
            return False
        matched = sum(1 for token in set(tokens) if token in source)
        return matched >= max(1, min(3, len(set(tokens)) // 3))

    def _repetition_penalty(self, text: str) -> int:
        normalized = self._clean_text(text)
        connectors = (
            "특히", "그래서", "실제로", "사용 후에는",
            "선택 기준은", "확인해 보세요",
        )
        penalty = 0
        for connector in connectors:
            count = normalized.count(connector)
            if count > 1:
                penalty += (count - 1) * 7
        sentences = [
            self._clean_text(item)
            for item in re.split(r"[.!?]+", normalized)
            if self._clean_text(item)
        ]
        seen = set()
        for sentence in sentences:
            key = sentence[:24]
            if key in seen:
                penalty += 12
            seen.add(key)
        return min(45, penalty)

    def _quality_grade(self, score: int) -> str:
        if score >= 92:
            return "S"
        if score >= 85:
            return "A"
        if score >= 75:
            return "B"
        if score >= 65:
            return "C"
        return "D"

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

    def _shorten_natural(
        self,
        text: str,
        limit: int,
    ) -> str:
        text = self._clean_text(text).rstrip(".!?… ")

        if len(text) <= limit:
            return self._sentence(text)

        clipped = text[:limit].rstrip(" ,.;:!?\"'“”‘’")
        last_space = clipped.rfind(" ")

        if last_space >= max(12, int(limit * 0.62)):
            clipped = clipped[:last_space].rstrip(" ,.;:!?\"'“”‘’")

        endings = (
            ("선택했", "선택했습니다"),
            ("중요합", "중요합니다"),
            ("맞습", "맞습니다"),
            ("편해졌", "편해졌습니다"),
            ("확인해", "확인해 보세요"),
        )

        for fragment, ending in endings:
            if clipped.endswith(fragment):
                clipped = clipped[: -len(fragment)] + ending
                break

        return self._sentence(clipped)

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