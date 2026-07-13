from __future__ import annotations

from typing import Any, Dict, List


class VideoCandidateRanker:
    """
    Sprint 60 Video Candidate Ranker

    역할:
    - Sprint 59 VideoCandidateSelector 결과를 입력으로 사용
    - 반응 점수, 화질, 쇼핑쇼츠 적합도, Real Vision 결과를 종합
    - 쇼핑쇼츠에 부적합한 후보는 감점
    - 최종 TOP3와 VideoComposer 추천 후보를 반환

    기존 후보 필드는 보존하고 다음 필드만 추가한다.
    - final_rank_score
    - rank_score_breakdown
    - rank_reasons
    - rank_warnings
    - composer_recommended
    - final_rank
    """

    RANKER_VERSION = "video-candidate-ranker-60-1"

    WEIGHTS = {
        "candidate_score": 0.35,
        "video_quality": 0.20,
        "shopping_fit": 0.25,
        "real_vision": 0.15,
        "scene_value": 0.05,
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

            weighted_score = (
                candidate_score * self.WEIGHTS["candidate_score"]
                + quality_score * self.WEIGHTS["video_quality"]
                + shopping_score * self.WEIGHTS["shopping_fit"]
                + vision_score * self.WEIGHTS["real_vision"]
                + scene_score * self.WEIGHTS["scene_value"]
            )

            penalty, warnings = self._penalty(item)
            final_score = max(
                min(weighted_score - penalty, 100.0),
                0.0,
            )

            reasons = self._reasons(
                item=item,
                candidate_score=candidate_score,
                quality_score=quality_score,
                shopping_score=shopping_score,
                vision_score=vision_score,
                scene_score=scene_score,
            )

            item["final_rank_score"] = round(
                final_score,
                1,
            )
            item["rank_score_breakdown"] = {
                "candidate_score": round(candidate_score, 1),
                "video_quality": round(quality_score, 1),
                "shopping_fit": round(shopping_score, 1),
                "real_vision": round(vision_score, 1),
                "scene_value": round(scene_score, 1),
                "penalty": round(penalty, 1),
            }
            item["rank_reasons"] = reasons[:8]
            item["rank_warnings"] = warnings[:6]
            item["ranker_version"] = self.RANKER_VERSION
            item["composer_recommended"] = False

            ranked.append(item)

        ranked.sort(
            key=lambda item: (
                self._safe_float(
                    item.get("final_rank_score")
                ),
                self._safe_float(
                    item.get(
                        "final_ai_score",
                        item.get(
                            "ai_score",
                            item.get("score", 0),
                        ),
                    )
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

        for index, item in enumerate(ranked, start=1):
            item["final_rank"] = index
            item["composer_recommended"] = (
                index == 1
                and item.get("final_rank_score", 0) >= 45
            )

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
            "composer_candidate": (
                ranked[0]
                if ranked
                and ranked[0].get("composer_recommended")
                else None
            ),
            "ranker_version": self.RANKER_VERSION,
            "weights": dict(self.WEIGHTS),
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

    def _nested_score(
        self,
        item: Dict[str, Any],
        key: str,
    ) -> float:
        value = item.get(key)

        if isinstance(value, dict):
            for score_key in (
                "score",
                "quality_score",
                "suitability_score",
                "final_score",
            ):
                if value.get(score_key) is not None:
                    return self._clamp_score(
                        value.get(score_key)
                    )

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
    ) -> tuple[float, List[str]]:
        penalty = 0.0
        warnings: List[str] = []
        text = self._candidate_text(item)

        duration = self._safe_float(
            item.get(
                "duration",
                item.get(
                    "duration_seconds",
                    item.get("video_duration", 0),
                ),
            )
        )

        if duration > 0 and duration < 4:
            penalty += 18
            warnings.append("영상 길이가 4초 미만")

        elif duration > 180:
            penalty += 12
            warnings.append("영상 길이가 3분 초과")

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

        if not (
            item.get("url")
            or item.get("video_url")
            or item.get("play_url")
            or item.get("path")
            or item.get("video_path")
        ):
            penalty += 30
            warnings.append("사용 가능한 영상 경로가 없음")

        return min(penalty, 80.0), warnings

    def _reasons(
        self,
        item: Dict[str, Any],
        candidate_score: float,
        quality_score: float,
        shopping_score: float,
        vision_score: float,
        scene_score: float,
    ) -> List[str]:
        reasons: List[str] = []

        if candidate_score >= 70:
            reasons.append("후보 반응 점수 우수")
        elif candidate_score >= 45:
            reasons.append("후보 반응 점수 양호")

        if quality_score >= 80:
            reasons.append("영상 화질 우수")
        elif quality_score >= 60:
            reasons.append("영상 화질 사용 가능")

        if shopping_score >= 80:
            reasons.append("쇼핑쇼츠 적합도 우수")
        elif shopping_score >= 60:
            reasons.append("쇼핑쇼츠 활용 가능")

        if vision_score >= 75:
            reasons.append("제품 사용 장면 확인")
        elif vision_score >= 50:
            reasons.append("제품 노출 확인")

        if scene_score >= 75:
            reasons.append("편집 가치가 높은 장면")

        views = self._safe_int(
            item.get("view_count")
        )

        if views >= 1_000_000:
            reasons.append("조회수 100만 이상")
        elif views >= 100_000:
            reasons.append("조회수 10만 이상")

        if str(
            item.get("metadata_source", "")
        ) == "tiktok-video-detail":
            reasons.append("TikTok 상세 통계 확인")

        return reasons or ["기본 종합 점수 적용"]

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
            return max(
                int(float(value or 0)),
                0,
            )
        except (TypeError, ValueError):
            return 0

    def _safe_float(
        self,
        value: Any,
    ) -> float:
        try:
            return max(
                float(value or 0),
                0.0,
            )
        except (TypeError, ValueError):
            return 0.0

