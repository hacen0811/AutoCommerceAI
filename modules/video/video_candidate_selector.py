from __future__ import annotations

import math
from typing import Any, Dict, List


class VideoCandidateSelector:
    """
    Sprint 58 Video Candidate Selector

    역할:
    - 기존 검색 점수, 화질, 쇼핑쇼츠 적합도 유지
    - TikTok/Douyin 상세 메타데이터 통계 반영
    - 조회수, 좋아요, 댓글, 공유를 후보 점수에 반영
    - 기존 반환 구조(best/top3/all) 유지
    """

    SELECTOR_VERSION = "video-candidate-selector-58-1"

    def select(
        self,
        candidates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        candidates = candidates or []

        scored: List[Dict[str, Any]] = []

        for item in candidates:
            if not isinstance(item, dict):
                continue

            new_item = dict(item)
            score = self._score_candidate(new_item)

            new_item["ai_score"] = score
            new_item["final_ai_score"] = score
            new_item["ai_recommendation"] = (
                self._recommendation(score)
            )
            new_item["ai_reasons"] = self._reasons(
                new_item
            )
            new_item["selector_version"] = (
                self.SELECTOR_VERSION
            )

            scored.append(new_item)

        scored.sort(
            key=lambda x: (
                self._safe_float(
                    x.get(
                        "final_ai_score",
                        x.get("ai_score", 0),
                    )
                ),
                self._safe_int(
                    x.get("view_count", 0)
                ),
                self._safe_int(
                    x.get("like_count", 0)
                ),
                self._safe_int(
                    x.get("comment_count", 0)
                ),
            ),
            reverse=True,
        )

        return {
            "ok": True,
            "count": len(scored),
            "best": scored[0] if scored else None,
            "top3": scored[:3],
            "all": scored,
            "selector_version": self.SELECTOR_VERSION,
        }

    def _score_candidate(
        self,
        item: Dict[str, Any],
    ) -> float:
        score = 0.0

        base_score = self._safe_float(
            item.get("score", 0)
        )

        if base_score > 0:
            score += min(base_score, 100) * 0.25

        platform = str(
            item.get("platform", "")
        ).lower()

        if platform == "taobao":
            score += 12
        elif platform == "1688":
            score += 10
        elif platform in {
            "tiktok",
            "douyin",
        }:
            score += 5

        purpose = str(
            item.get("purpose", "")
        )
        title = str(
            item.get("title", "")
        )
        keyword = str(
            item.get("keyword", "")
        )

        text = f"{purpose} {title} {keyword}"

        if "主图视频" in text:
            score += 10

        if "实拍" in text:
            score += 10

        if "买家秀" in text:
            score += 8

        if (
            "安装" in text
            or "사용" in text
        ):
            score += 7

        if "同款" in text:
            score += 5

        if "review" in text.lower():
            score += 4

        video_quality = (
            item.get("video_quality")
            or {}
        )

        if isinstance(video_quality, dict):
            quality_score = self._safe_float(
                video_quality.get("score", 0)
            )

            if quality_score > 0:
                score += min(
                    quality_score,
                    100,
                ) * 0.20

        shopping_fit = (
            item.get("shopping_shorts_fit")
            or item.get("shopping_fit")
            or item.get("shorts_fit")
            or {}
        )

        if isinstance(shopping_fit, dict):
            fit_score = self._safe_float(
                shopping_fit.get("score", 0)
            )

            if fit_score > 0:
                score += min(
                    fit_score,
                    100,
                ) * 0.20

        real_vision = (
            item.get("real_vision")
            or {}
        )

        if isinstance(real_vision, dict):
            if real_vision.get("ok"):
                score += 5

            summary = str(
                real_vision.get("summary", "")
            )

            summary_lower = summary.lower()

            if (
                "product" in summary_lower
                or "상품" in summary
            ):
                score += 5

            if (
                "hand" in summary_lower
                or "손" in summary
            ):
                score += 3

            if (
                "demo" in summary_lower
                or "사용" in summary
            ):
                score += 4

        if platform in {
            "tiktok",
            "douyin",
        }:
            score += self._social_score(item)

        return round(
            min(score, 100),
            1,
        )

    def _social_score(
        self,
        item: Dict[str, Any],
    ) -> float:
        """
        TikTok/Douyin 반응 통계 점수.

        최대 30점:
        - 조회수 최대 14점
        - 좋아요 최대 8점
        - 댓글 최대 4점
        - 공유 최대 4점
        """

        view_count = self._stat_value(
            item,
            "view_count",
            "views",
            "play_count",
            "playCount",
        )

        like_count = self._stat_value(
            item,
            "like_count",
            "likes",
            "digg_count",
            "diggCount",
        )

        comment_count = self._stat_value(
            item,
            "comment_count",
            "comments",
            "commentCount",
        )

        share_count = self._stat_value(
            item,
            "share_count",
            "shares",
            "shareCount",
        )

        score = 0.0

        score += self._log_score(
            value=view_count,
            target=1_000_000,
            maximum=14,
        )

        score += self._log_score(
            value=like_count,
            target=100_000,
            maximum=8,
        )

        score += self._log_score(
            value=comment_count,
            target=2_000,
            maximum=4,
        )

        score += self._log_score(
            value=share_count,
            target=10_000,
            maximum=4,
        )

        if view_count > 0:
            like_rate = (
                like_count / view_count
            )

            comment_rate = (
                comment_count / view_count
            )

            share_rate = (
                share_count / view_count
            )

            if like_rate >= 0.08:
                score += 2
            elif like_rate >= 0.04:
                score += 1

            if comment_rate >= 0.001:
                score += 1

            if share_rate >= 0.003:
                score += 1

        return min(
            score,
            30,
        )

    def _log_score(
        self,
        value: int,
        target: int,
        maximum: float,
    ) -> float:
        if value <= 0:
            return 0.0

        if target <= 0:
            return 0.0

        ratio = math.log10(
            value + 1
        ) / math.log10(
            target + 1
        )

        return min(
            max(ratio, 0.0) * maximum,
            maximum,
        )

    def _stat_value(
        self,
        item: Dict[str, Any],
        *keys: str,
    ) -> int:
        for key in keys:
            value = self._safe_int(
                item.get(key)
            )

            if value > 0:
                return value

        stats = item.get("stats")

        if isinstance(stats, dict):
            for key in keys:
                value = self._safe_int(
                    stats.get(key)
                )

                if value > 0:
                    return value

        return 0

    def _reasons(
        self,
        item: Dict[str, Any],
    ) -> List[str]:
        reasons: List[str] = []

        base_score = self._safe_float(
            item.get("score", 0)
        )

        if base_score >= 80:
            reasons.append("검색 점수 우수")

        platform = str(
            item.get("platform", "")
        ).lower()

        if platform == "taobao":
            reasons.append("타오바오 후보")

        elif platform == "1688":
            reasons.append("1688 후보")

        elif platform == "tiktok":
            reasons.append("TikTok 반응 데이터 반영")

        elif platform == "douyin":
            reasons.append("Douyin 반응 데이터 반영")

        text = (
            f"{item.get('purpose', '')} "
            f"{item.get('title', '')} "
            f"{item.get('keyword', '')}"
        )

        if "主图视频" in text:
            reasons.append("상품 메인 영상 후보")

        if "实拍" in text:
            reasons.append("실제 촬영 영상")

        if "买家秀" in text:
            reasons.append("구매자 사용 장면")

        if (
            "安装" in text
            or "사용" in text
        ):
            reasons.append("사용/설치 장면 포함")

        if "review" in text.lower():
            reasons.append("리뷰형 영상 후보")

        video_quality = (
            item.get("video_quality")
            or {}
        )

        if isinstance(video_quality, dict):
            quality_score = self._safe_float(
                video_quality.get("score", 0)
            )

            if quality_score >= 85:
                reasons.append("화질 우수")

            elif quality_score >= 70:
                reasons.append("화질 양호")

        shopping_fit = (
            item.get("shopping_shorts_fit")
            or item.get("shopping_fit")
            or item.get("shorts_fit")
            or {}
        )

        if isinstance(shopping_fit, dict):
            fit_score = self._safe_float(
                shopping_fit.get("score", 0)
            )

            if fit_score >= 85:
                reasons.append(
                    "쇼핑쇼츠 적합도 높음"
                )

            elif fit_score >= 70:
                reasons.append(
                    "쇼핑쇼츠 활용 가능"
                )

        real_vision = (
            item.get("real_vision")
            or {}
        )

        if isinstance(real_vision, dict):
            summary = str(
                real_vision.get("summary", "")
            )

            summary_lower = summary.lower()

            if real_vision.get("ok"):
                reasons.append(
                    "Real Vision 분석 완료"
                )

            if (
                "product" in summary_lower
                or "상품" in summary
            ):
                reasons.append("상품 노출 확인")

            if (
                "hand" in summary_lower
                or "손" in summary
            ):
                reasons.append(
                    "손/사용 장면 확인"
                )

            if (
                "demo" in summary_lower
                or "사용" in summary
            ):
                reasons.append(
                    "제품 사용 장면 확인"
                )

        if platform in {
            "tiktok",
            "douyin",
        }:
            self._append_social_reasons(
                item,
                reasons,
            )

        metadata_source = str(
            item.get("metadata_source", "")
        )

        if metadata_source == (
            "tiktok-video-detail"
        ):
            reasons.append(
                "TikTok 상세 통계 확인"
            )

        if not reasons:
            reasons.append("기본 후보")

        return reasons[:8]

    def _append_social_reasons(
        self,
        item: Dict[str, Any],
        reasons: List[str],
    ) -> None:
        view_count = self._stat_value(
            item,
            "view_count",
            "views",
            "play_count",
            "playCount",
        )

        like_count = self._stat_value(
            item,
            "like_count",
            "likes",
            "digg_count",
            "diggCount",
        )

        comment_count = self._stat_value(
            item,
            "comment_count",
            "comments",
            "commentCount",
        )

        share_count = self._stat_value(
            item,
            "share_count",
            "shares",
            "shareCount",
        )

        if view_count >= 1_000_000:
            reasons.append("조회수 100만 이상")

        elif view_count >= 100_000:
            reasons.append("조회수 10만 이상")

        elif view_count >= 10_000:
            reasons.append("조회수 1만 이상")

        if like_count >= 100_000:
            reasons.append("좋아요 10만 이상")

        elif like_count >= 10_000:
            reasons.append("좋아요 1만 이상")

        if comment_count >= 1_000:
            reasons.append("댓글 반응 높음")

        if share_count >= 10_000:
            reasons.append("공유 반응 매우 높음")

        elif share_count >= 1_000:
            reasons.append("공유 반응 높음")

        if view_count > 0:
            like_rate = (
                like_count / view_count
            )

            if like_rate >= 0.08:
                reasons.append(
                    "조회수 대비 좋아요 비율 우수"
                )

    def _recommendation(
        self,
        score: float,
    ) -> str:
        if score >= 90:
            return "최우선 후보"

        if score >= 80:
            return "우선 후보"

        if score >= 70:
            return "검토 후보"

        if score >= 60:
            return "보조 후보"

        return "낮은 우선순위"

    def _safe_int(
        self,
        value: Any,
    ) -> int:
        if value is None:
            return 0

        if isinstance(value, bool):
            return 0

        if isinstance(value, str):
            value = (
                value.strip()
                .replace(",", "")
                .replace("회", "")
                .replace("개", "")
            )

            if not value:
                return 0

            multiplier = 1

            lower_value = value.lower()

            if lower_value.endswith("k"):
                multiplier = 1_000
                value = value[:-1]

            elif lower_value.endswith("m"):
                multiplier = 1_000_000
                value = value[:-1]

            elif value.endswith("만"):
                multiplier = 10_000
                value = value[:-1]

            elif value.endswith("억"):
                multiplier = 100_000_000
                value = value[:-1]

            try:
                return max(
                    int(float(value) * multiplier),
                    0,
                )

            except (TypeError, ValueError):
                return 0

        try:
            return max(
                int(float(value)),
                0,
            )

        except (TypeError, ValueError):
            return 0

    def _safe_float(
        self,
        value: Any,
    ) -> float:
        if value is None:
            return 0.0

        if isinstance(value, bool):
            return 0.0

        try:
            return max(
                float(value),
                0.0,
            )

        except (TypeError, ValueError):
            return 0.0