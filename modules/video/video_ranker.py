from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple


class VideoCandidateRanker:
    """
    Sprint 63-1 Video Candidate Ranker

    역할:
    - Sprint 59 VideoCandidateSelector 결과를 입력으로 사용
    - Sprint 62 ViralPatternEngine 분석 결과를 적극 반영
    - 조회수, 좋아요, 댓글, 공유 기반 Social Viral 점수 계산
    - Hook, CTA, 자막, 편집, 감정, 유지율, 트렌드 점수 반영
    - 쇼핑쇼츠에 부적합한 후보 감점
    - 최종 TOP3와 VideoComposer 추천 후보 반환

    기존 후보 필드는 보존하고 다음 필드를 추가한다.
    - final_rank_score
    - rank_score_breakdown
    - viral_score_breakdown
    - social_score_breakdown
    - rank_reasons
    - rank_warnings
    - composer_recommended
    - viral_priority
    - final_rank
    """

    RANKER_VERSION = "video-candidate-ranker-63-1"

    # 전체 가중치 합계 = 1.00
    #
    # Sprint 63에서는 Viral Pattern과 실제 Social 반응을
    # 최종 점수의 45%로 적극 반영한다.
    WEIGHTS = {
        "candidate_score": 0.10,
        "video_quality": 0.10,
        "shopping_fit": 0.20,
        "real_vision": 0.10,
        "scene_value": 0.05,
        "viral_pattern": 0.30,
        "social_viral": 0.15,
    }

    # Viral Pattern 내부 세부 가중치
    VIRAL_WEIGHTS = {
        "base_score": 0.20,
        "hook_score": 0.25,
        "cta_score": 0.12,
        "caption_score": 0.08,
        "editing_score": 0.12,
        "retention_score": 0.13,
        "emotion_score": 0.05,
        "trend_score": 0.05,
    }

    def rank(
        self,
        candidates: List[Dict[str, Any]],
        top_n: int = 3,
    ) -> Dict[str, Any]:
        candidates = candidates or []
        ranked: List[Dict[str, Any]] = []

        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue

            item = dict(candidate)

            candidate_score = self._candidate_score(item)

            quality_score = self._nested_score(
                item,
                "video_quality",
            )

            shopping_score = self._first_nested_score(
                item,
                [
                    "shopping_shorts_fit",
                    "shopping_fit",
                    "shorts_fit",
                ],
            )

            vision_score = self._real_vision_score(item)
            scene_score = self._scene_value_score(item)

            viral_result = self._viral_pattern_result(item)
            viral_pattern_score = viral_result["score"]
            viral_breakdown = viral_result["breakdown"]

            social_result = self._social_viral_result(item)
            social_viral_score = social_result["score"]
            social_breakdown = social_result["breakdown"]

            weighted_score = (
                candidate_score
                * self.WEIGHTS["candidate_score"]

                + quality_score
                * self.WEIGHTS["video_quality"]

                + shopping_score
                * self.WEIGHTS["shopping_fit"]

                + vision_score
                * self.WEIGHTS["real_vision"]

                + scene_score
                * self.WEIGHTS["scene_value"]

                + viral_pattern_score
                * self.WEIGHTS["viral_pattern"]

                + social_viral_score
                * self.WEIGHTS["social_viral"]
            )

            penalty, warnings = self._penalty(item)

            # Viral Pattern이 매우 강한 후보에는 소폭 보너스
            viral_bonus = self._viral_bonus(
                viral_pattern_score=viral_pattern_score,
                hook_score=viral_breakdown.get(
                    "hook_score",
                    0,
                ),
                social_score=social_viral_score,
            )

            final_score = max(
                min(
                    weighted_score
                    + viral_bonus
                    - penalty,
                    100.0,
                ),
                0.0,
            )

            reasons = self._reasons(
                item=item,
                candidate_score=candidate_score,
                quality_score=quality_score,
                shopping_score=shopping_score,
                vision_score=vision_score,
                scene_score=scene_score,
                viral_pattern_score=viral_pattern_score,
                social_viral_score=social_viral_score,
                viral_breakdown=viral_breakdown,
                social_breakdown=social_breakdown,
            )

            item["final_rank_score"] = round(
                final_score,
                1,
            )

            item["rank_score_breakdown"] = {
                "candidate_score": round(
                    candidate_score,
                    1,
                ),
                "video_quality": round(
                    quality_score,
                    1,
                ),
                "shopping_fit": round(
                    shopping_score,
                    1,
                ),
                "real_vision": round(
                    vision_score,
                    1,
                ),
                "scene_value": round(
                    scene_score,
                    1,
                ),
                "viral_pattern": round(
                    viral_pattern_score,
                    1,
                ),
                "social_viral": round(
                    social_viral_score,
                    1,
                ),
                "viral_bonus": round(
                    viral_bonus,
                    1,
                ),
                "penalty": round(
                    penalty,
                    1,
                ),
                "weighted_score_before_adjustment": round(
                    weighted_score,
                    1,
                ),
            }

            item["viral_score_breakdown"] = {
                key: round(
                    self._safe_float(value),
                    1,
                )
                for key, value in viral_breakdown.items()
            }

            item["social_score_breakdown"] = {
                key: round(
                    self._safe_float(value),
                    4,
                )
                for key, value in social_breakdown.items()
            }

            item["viral_pattern_score"] = round(
                viral_pattern_score,
                1,
            )
            item["social_viral_score"] = round(
                social_viral_score,
                1,
            )

            item["viral_priority"] = round(
                self._viral_priority_score(
                    viral_pattern_score=viral_pattern_score,
                    social_viral_score=social_viral_score,
                    hook_score=viral_breakdown.get(
                        "hook_score",
                        0,
                    ),
                    shopping_score=shopping_score,
                ),
                1,
            )

            item["rank_reasons"] = reasons[:12]
            item["rank_warnings"] = warnings[:8]
            item["ranker_version"] = self.RANKER_VERSION
            item["composer_recommended"] = False

            ranked.append(item)

        # 최종 점수가 가장 중요하며,
        # 동점에서는 Viral Priority가 높은 후보를 우선한다.
        ranked.sort(
            key=lambda item: (
                self._safe_float(
                    item.get("final_rank_score")
                ),
                self._safe_float(
                    item.get("viral_priority")
                ),
                self._safe_float(
                    item.get("viral_pattern_score")
                ),
                self._safe_float(
                    item.get("social_viral_score")
                ),
                self._safe_int(
                    item.get("share_count")
                ),
                self._safe_int(
                    item.get("view_count")
                ),
                self._safe_int(
                    item.get("like_count")
                ),
            ),
            reverse=True,
        )

        composer_candidate = None

        for index, item in enumerate(
            ranked,
            start=1,
        ):
            item["final_rank"] = index

            is_usable = not self._has_blocking_warning(
                item
            )

            item["composer_recommended"] = (
                index == 1
                and is_usable
                and self._safe_float(
                    item.get("final_rank_score")
                ) >= 30
            )

            if item["composer_recommended"]:
                composer_candidate = item

        # 1위가 경로 문제 등으로 Composer 사용 불가하면
        # 다음 순위 중 사용 가능한 최고 후보를 선택한다.
        if composer_candidate is None:
            for item in ranked:
                if (
                    self._safe_float(
                        item.get("final_rank_score")
                    ) >= 30
                    and not self._has_blocking_warning(item)
                ):
                    item["composer_recommended"] = True
                    composer_candidate = item
                    break

        safe_top_n = max(
            self._safe_int(top_n),
            1,
        )

        top_items = ranked[:safe_top_n]

        return {
            "ok": True,
            "count": len(ranked),
            "best": ranked[0] if ranked else None,
            "top3": ranked[:3],
            "top": top_items,
            "all": ranked,
            "composer_candidate": composer_candidate,
            "ranker_version": self.RANKER_VERSION,
            "weights": dict(self.WEIGHTS),
            "viral_weights": dict(
                self.VIRAL_WEIGHTS
            ),
        }

    def _candidate_score(
        self,
        item: Dict[str, Any],
    ) -> float:
        value = (
            item.get("final_ai_score")
            if item.get("final_ai_score") is not None
            else item.get("ai_score")
        )

        if value is None:
            value = item.get("score", 0)

        return self._clamp_score(value)

    def _viral_pattern_result(
        self,
        item: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        ViralPatternEngine 결과 구조가 달라도
        최대한 안전하게 점수를 읽는다.

        지원 구조 예:
        item["viral_pattern"]
        item["viral_pattern_analysis"]
        item["viral_analysis"]
        item["pattern_analysis"]

        또는 후보 최상위:
        item["viral_pattern_score"]
        item["hook_score"]
        item["cta_score"]
        """

        viral_data: Dict[str, Any] = {}

        for key in (
            "viral_pattern",
            "viral_pattern_analysis",
            "viral_analysis",
            "pattern_analysis",
            "viral",
        ):
            value = item.get(key)

            if isinstance(value, dict):
                viral_data.update(value)

        nested_scores = viral_data.get(
            "scores"
        )

        if isinstance(nested_scores, dict):
            viral_data.update(nested_scores)

        base_score = self._first_score_value(
            sources=[viral_data, item],
            keys=[
                "viral_pattern_score",
                "viral_score",
                "pattern_score",
                "score",
                "final_score",
            ],
        )

        hook_score = self._first_score_value(
            sources=[viral_data, item],
            keys=[
                "hook_score",
                "hook_strength",
                "opening_score",
            ],
        )

        cta_score = self._first_score_value(
            sources=[viral_data, item],
            keys=[
                "cta_score",
                "cta_strength",
                "conversion_score",
            ],
        )

        caption_score = self._first_score_value(
            sources=[viral_data, item],
            keys=[
                "caption_score",
                "subtitle_score",
                "text_style_score",
            ],
        )

        editing_score = self._first_score_value(
            sources=[viral_data, item],
            keys=[
                "editing_score",
                "edit_score",
                "cut_score",
                "cut_style_score",
            ],
        )

        retention_score = self._first_score_value(
            sources=[viral_data, item],
            keys=[
                "retention_score",
                "watch_score",
                "completion_score",
                "engagement_score",
            ],
        )

        emotion_score = self._first_score_value(
            sources=[viral_data, item],
            keys=[
                "emotion_score",
                "emotional_score",
                "reaction_score",
            ],
        )

        trend_score = self._first_score_value(
            sources=[viral_data, item],
            keys=[
                "trend_score",
                "trend_fit_score",
                "freshness_score",
            ],
        )

        # Sprint 62에서는 viral_pattern_score만 존재할 수 있다.
        # 세부 점수가 없을 때는 기본 점수를 안전하게 대체값으로 사용한다.
        fallback_score = base_score

        if hook_score <= 0:
            hook_score = fallback_score

        if cta_score <= 0:
            cta_score = fallback_score

        if caption_score <= 0:
            caption_score = fallback_score

        if editing_score <= 0:
            editing_score = fallback_score

        if retention_score <= 0:
            retention_score = fallback_score

        if emotion_score <= 0:
            emotion_score = fallback_score

        if trend_score <= 0:
            trend_score = fallback_score

        breakdown = {
            "base_score": base_score,
            "hook_score": hook_score,
            "cta_score": cta_score,
            "caption_score": caption_score,
            "editing_score": editing_score,
            "retention_score": retention_score,
            "emotion_score": emotion_score,
            "trend_score": trend_score,
        }

        if all(
            self._safe_float(value) <= 0
            for value in breakdown.values()
        ):
            return {
                "score": 0.0,
                "breakdown": breakdown,
            }

        weighted_score = sum(
            self._safe_float(
                breakdown.get(key)
            )
            * weight
            for key, weight in self.VIRAL_WEIGHTS.items()
        )

        return {
            "score": self._clamp_score(
                weighted_score
            ),
            "breakdown": breakdown,
        }

    def _social_viral_result(
        self,
        item: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        조회수, 좋아요, 댓글, 공유를 활용해
        실제 반응 기반 Social Viral 점수를 계산한다.

        절대 수치뿐 아니라 조회수 대비 반응률을 함께 사용한다.
        """

        views = self._first_int_value(
            item,
            [
                "view_count",
                "views",
                "play_count",
                "playCount",
                "digg_view_count",
            ],
        )

        likes = self._first_int_value(
            item,
            [
                "like_count",
                "likes",
                "digg_count",
                "diggCount",
            ],
        )

        comments = self._first_int_value(
            item,
            [
                "comment_count",
                "comments",
                "commentCount",
            ],
        )

        shares = self._first_int_value(
            item,
            [
                "share_count",
                "shares",
                "shareCount",
            ],
        )

        saves = self._first_int_value(
            item,
            [
                "save_count",
                "saves",
                "collect_count",
                "collectCount",
            ],
        )

        view_score = self._log_scale_score(
            views,
            target=1_000_000,
        )

        like_volume_score = self._log_scale_score(
            likes,
            target=100_000,
        )

        comment_volume_score = self._log_scale_score(
            comments,
            target=5_000,
        )

        share_volume_score = self._log_scale_score(
            shares,
            target=10_000,
        )

        if views > 0:
            like_rate = likes / views
            comment_rate = comments / views
            share_rate = shares / views
            save_rate = saves / views
        else:
            like_rate = 0.0
            comment_rate = 0.0
            share_rate = 0.0
            save_rate = 0.0

        # 쇼츠 플랫폼에서 강한 반응률을 100점 기준으로 환산
        like_rate_score = self._rate_score(
            like_rate,
            excellent_rate=0.10,
        )

        comment_rate_score = self._rate_score(
            comment_rate,
            excellent_rate=0.01,
        )

        share_rate_score = self._rate_score(
            share_rate,
            excellent_rate=0.02,
        )

        save_rate_score = self._rate_score(
            save_rate,
            excellent_rate=0.02,
        )

        # 공유는 강한 바이럴 신호이므로 높은 비중 적용
        social_score = (
            view_score * 0.22
            + like_volume_score * 0.08
            + comment_volume_score * 0.05
            + share_volume_score * 0.10
            + like_rate_score * 0.20
            + comment_rate_score * 0.12
            + share_rate_score * 0.18
            + save_rate_score * 0.05
        )

        breakdown = {
            "views": views,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "saves": saves,
            "view_score": view_score,
            "like_volume_score": like_volume_score,
            "comment_volume_score": comment_volume_score,
            "share_volume_score": share_volume_score,
            "like_rate": like_rate,
            "comment_rate": comment_rate,
            "share_rate": share_rate,
            "save_rate": save_rate,
            "like_rate_score": like_rate_score,
            "comment_rate_score": comment_rate_score,
            "share_rate_score": share_rate_score,
            "save_rate_score": save_rate_score,
        }

        return {
            "score": self._clamp_score(
                social_score
            ),
            "breakdown": breakdown,
        }

    def _viral_bonus(
        self,
        viral_pattern_score: float,
        hook_score: float,
        social_score: float,
    ) -> float:
        bonus = 0.0

        if viral_pattern_score >= 80:
            bonus += 3.0
        elif viral_pattern_score >= 65:
            bonus += 1.5

        if hook_score >= 85:
            bonus += 2.0
        elif hook_score >= 70:
            bonus += 1.0

        if social_score >= 80:
            bonus += 2.0
        elif social_score >= 65:
            bonus += 1.0

        return min(bonus, 7.0)

    def _viral_priority_score(
        self,
        viral_pattern_score: float,
        social_viral_score: float,
        hook_score: float,
        shopping_score: float,
    ) -> float:
        score = (
            viral_pattern_score * 0.40
            + social_viral_score * 0.25
            + self._clamp_score(
                hook_score
            ) * 0.20
            + shopping_score * 0.15
        )

        return self._clamp_score(score)

    def _nested_score(
        self,
        item: Dict[str, Any],
        key: str,
    ) -> float:
        value = item.get(key)

        if isinstance(value, dict):
            for score_key in (
                "score",
                "fit_score",
                "quality_score",
                "suitability_score",
                "final_score",
            ):
                if value.get(score_key) is not None:
                    return self._clamp_score(
                        value.get(score_key)
                    )

        if isinstance(
            value,
            (int, float, str),
        ):
            return self._clamp_score(value)

        return 0.0

    def _first_nested_score(
        self,
        item: Dict[str, Any],
        keys: List[str],
    ) -> float:
        for key in keys:
            score = self._nested_score(
                item,
                key,
            )

            if score > 0:
                return score

        return 0.0

    def _real_vision_score(
        self,
        item: Dict[str, Any],
    ) -> float:
        vision = item.get("real_vision") or {}

        if not isinstance(vision, dict):
            return 0.0

        for key in (
            "score",
            "vision_score",
            "confidence",
            "suitability_score",
        ):
            if vision.get(key) is not None:
                value = self._safe_float(
                    vision.get(key)
                )

                if key == "confidence" and value <= 1:
                    value *= 100

                return self._clamp_score(value)

        score = 0.0

        if vision.get("ok"):
            score += 35

        summary = str(
            vision.get("summary", "")
        )

        lower = summary.lower()

        if (
            "product" in lower
            or "상품" in summary
            or "제품" in summary
        ):
            score += 25

        if (
            "hand" in lower
            or "손" in summary
        ):
            score += 15

        if (
            "demo" in lower
            or "use" in lower
            or "사용" in summary
        ):
            score += 20

        if (
            "before" in lower
            or "after" in lower
            or "비포" in summary
            or "애프터" in summary
        ):
            score += 5

        return self._clamp_score(score)

    def _scene_value_score(
        self,
        item: Dict[str, Any],
    ) -> float:
        text = self._candidate_text(item)
        score = 40.0

        positive_words = {
            "사용": 18,
            "시연": 18,
            "설치": 15,
            "리뷰": 12,
            "언박싱": 14,
            "비교": 14,
            "before": 15,
            "after": 15,
            "demo": 18,
            "review": 12,
            "unboxing": 14,
            "实拍": 18,
            "买家秀": 15,
            "安装": 15,
            "使用": 18,
            "测评": 14,
            "对比": 14,
        }

        for word, value in positive_words.items():
            if word.lower() in text:
                score += value

        negative_words = {
            "슬라이드": 25,
            "사진모음": 25,
            "밈": 20,
            "meme": 20,
            "talking": 10,
            "reaction": 10,
            "直播": 12,
            "纯文字": 25,
            "图文": 20,
        }

        for word, value in negative_words.items():
            if word.lower() in text:
                score -= value

        return self._clamp_score(score)

    def _penalty(
        self,
        item: Dict[str, Any],
    ) -> Tuple[float, List[str]]:
        penalty = 0.0
        warnings: List[str] = []
        text = self._candidate_text(item)

        duration = self._safe_float(
            item.get(
                "duration",
                item.get(
                    "duration_seconds",
                    item.get(
                        "video_duration",
                        0,
                    ),
                ),
            )
        )

        if 0 < duration < 4:
            penalty += 18
            warnings.append(
                "영상 길이가 4초 미만"
            )

        elif duration > 180:
            penalty += 12
            warnings.append(
                "영상 길이가 3분 초과"
            )

        bad_signals = {
            "slideshow": (
                25,
                "슬라이드쇼 후보",
            ),
            "watermark_heavy": (
                20,
                "워터마크가 과도함",
            ),
            "face_only": (
                18,
                "얼굴 위주 영상",
            ),
            "text_only": (
                25,
                "텍스트 위주 영상",
            ),
            "is_live": (
                15,
                "라이브 영상",
            ),
            "blocked": (
                40,
                "차단 또는 재생 불가",
            ),
        }

        for key, (
            value,
            message,
        ) in bad_signals.items():
            if self._truthy(item.get(key)):
                penalty += value
                warnings.append(message)

        keyword_penalties = {
            "纯文字": (
                25,
                "중국어 텍스트 영상 가능성",
            ),
            "图文": (
                20,
                "이미지 슬라이드 가능성",
            ),
            "meme": (
                15,
                "밈 영상 가능성",
            ),
            "reaction": (
                10,
                "리액션 위주 가능성",
            ),
        }

        for keyword, (
            value,
            message,
        ) in keyword_penalties.items():
            if keyword.lower() in text:
                penalty += value
                warnings.append(message)

        if not self._has_video_source(item):
            penalty += 30
            warnings.append(
                "사용 가능한 영상 경로가 없음"
            )

        return min(
            penalty,
            80.0,
        ), warnings

    def _reasons(
        self,
        item: Dict[str, Any],
        candidate_score: float,
        quality_score: float,
        shopping_score: float,
        vision_score: float,
        scene_score: float,
        viral_pattern_score: float,
        social_viral_score: float,
        viral_breakdown: Dict[str, Any],
        social_breakdown: Dict[str, Any],
    ) -> List[str]:
        reasons: List[str] = []

        if viral_pattern_score >= 80:
            reasons.append(
                "바이럴 패턴 점수 매우 우수"
            )
        elif viral_pattern_score >= 60:
            reasons.append(
                "바이럴 패턴 활용 가치 높음"
            )

        hook_score = self._safe_float(
            viral_breakdown.get("hook_score")
        )

        if hook_score >= 85:
            reasons.append(
                "첫 장면 후킹 강도 매우 높음"
            )
        elif hook_score >= 65:
            reasons.append(
                "후킹 구조가 양호함"
            )

        cta_score = self._safe_float(
            viral_breakdown.get("cta_score")
        )

        if cta_score >= 75:
            reasons.append(
                "구매 유도 CTA 구조 우수"
            )

        editing_score = self._safe_float(
            viral_breakdown.get(
                "editing_score"
            )
        )

        if editing_score >= 75:
            reasons.append(
                "바이럴 편집 패턴 우수"
            )

        retention_score = self._safe_float(
            viral_breakdown.get(
                "retention_score"
            )
        )

        if retention_score >= 75:
            reasons.append(
                "시청 유지 가능성이 높음"
            )

        if social_viral_score >= 80:
            reasons.append(
                "실제 바이럴 반응 매우 우수"
            )
        elif social_viral_score >= 60:
            reasons.append(
                "실제 반응 지표 양호"
            )

        share_rate = self._safe_float(
            social_breakdown.get("share_rate")
        )

        if share_rate >= 0.01:
            reasons.append(
                "조회수 대비 공유율이 높음"
            )

        comment_rate = self._safe_float(
            social_breakdown.get(
                "comment_rate"
            )
        )

        if comment_rate >= 0.005:
            reasons.append(
                "조회수 대비 댓글 반응이 높음"
            )

        if candidate_score >= 70:
            reasons.append(
                "후보 반응 점수 우수"
            )
        elif candidate_score >= 45:
            reasons.append(
                "후보 반응 점수 양호"
            )

        if quality_score >= 80:
            reasons.append(
                "영상 화질 우수"
            )
        elif quality_score >= 60:
            reasons.append(
                "영상 화질 사용 가능"
            )

        if shopping_score >= 80:
            reasons.append(
                "쇼핑쇼츠 적합도 우수"
            )
        elif shopping_score >= 60:
            reasons.append(
                "쇼핑쇼츠 활용 가능"
            )

        if vision_score >= 75:
            reasons.append(
                "제품 사용 장면 확인"
            )
        elif vision_score >= 50:
            reasons.append(
                "제품 노출 확인"
            )

        if scene_score >= 75:
            reasons.append(
                "편집 가치가 높은 장면"
            )

        views = self._safe_int(
            social_breakdown.get(
                "views",
                item.get("view_count"),
            )
        )

        if views >= 1_000_000:
            reasons.append(
                "조회수 100만 이상"
            )
        elif views >= 100_000:
            reasons.append(
                "조회수 10만 이상"
            )

        if str(
            item.get("metadata_source", "")
        ) == "tiktok-video-detail":
            reasons.append(
                "TikTok 상세 통계 확인"
            )

        return reasons or [
            "기본 종합 점수 적용"
        ]

    def _has_video_source(
        self,
        item: Dict[str, Any],
    ) -> bool:
        return bool(
            item.get("url")
            or item.get("video_url")
            or item.get("play_url")
            or item.get("download_url")
            or item.get("path")
            or item.get("video_path")
            or item.get("local_path")
        )

    def _has_blocking_warning(
        self,
        item: Dict[str, Any],
    ) -> bool:
        if not self._has_video_source(item):
            return True

        if self._truthy(item.get("blocked")):
            return True

        return False

    def _first_score_value(
        self,
        sources: List[Dict[str, Any]],
        keys: List[str],
    ) -> float:
        for source in sources:
            if not isinstance(source, dict):
                continue

            for key in keys:
                value = source.get(key)

                if value is not None:
                    score = self._clamp_score(
                        value
                    )

                    if score > 0:
                        return score

        return 0.0

    def _first_int_value(
        self,
        item: Dict[str, Any],
        keys: List[str],
    ) -> int:
        for key in keys:
            value = item.get(key)

            if value is not None:
                parsed = self._safe_int(value)

                if parsed > 0:
                    return parsed

        stats = item.get("stats")

        if isinstance(stats, dict):
            for key in keys:
                value = stats.get(key)

                if value is not None:
                    parsed = self._safe_int(value)

                    if parsed > 0:
                        return parsed

        statistics = item.get("statistics")

        if isinstance(statistics, dict):
            for key in keys:
                value = statistics.get(key)

                if value is not None:
                    parsed = self._safe_int(value)

                    if parsed > 0:
                        return parsed

        return 0

    def _log_scale_score(
        self,
        value: int,
        target: int,
    ) -> float:
        value = max(
            self._safe_int(value),
            0,
        )

        target = max(
            self._safe_int(target),
            1,
        )

        if value <= 0:
            return 0.0

        score = (
            math.log10(value + 1)
            / math.log10(target + 1)
            * 100
        )

        return self._clamp_score(score)

    def _rate_score(
        self,
        rate: float,
        excellent_rate: float,
    ) -> float:
        rate = max(
            self._safe_float(rate),
            0.0,
        )

        excellent_rate = max(
            self._safe_float(excellent_rate),
            0.000001,
        )

        return self._clamp_score(
            rate
            / excellent_rate
            * 100
        )

    def _candidate_text(
        self,
        item: Dict[str, Any],
    ) -> str:
        values = [
            item.get("title", ""),
            item.get("purpose", ""),
            item.get("keyword", ""),
            item.get("description", ""),
            item.get("caption", ""),
            item.get("note", ""),
            item.get("pattern_type", ""),
            item.get("hook_type", ""),
            item.get("cta_type", ""),
        ]

        return " ".join(
            str(value)
            for value in values
            if value is not None
        ).lower()

    def _clamp_score(
        self,
        value: Any,
    ) -> float:
        return max(
            min(
                self._safe_float(value),
                100.0,
            ),
            0.0,
        )

    def _truthy(
        self,
        value: Any,
    ) -> bool:
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.strip().lower() in {
                "1",
                "true",
                "yes",
                "y",
                "on",
            }

        return bool(value)

    def _safe_int(
        self,
        value: Any,
    ) -> int:
        try:
            if isinstance(value, str):
                cleaned = (
                    value.strip()
                    .replace(",", "")
                    .replace("회", "")
                    .replace("개", "")
                )

                if not cleaned:
                    return 0

                value = cleaned

            return max(
                int(float(value or 0)),
                0,
            )

        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            return 0

    def _safe_float(
        self,
        value: Any,
    ) -> float:
        try:
            if isinstance(value, str):
                cleaned = (
                    value.strip()
                    .replace(",", "")
                    .replace("%", "")
                )

                if not cleaned:
                    return 0.0

                value = cleaned

            return max(
                float(value or 0),
                0.0,
            )

        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            return 0.0