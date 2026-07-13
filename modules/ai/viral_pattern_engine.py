from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


PATTERN_DB_PATH = Path("exports/viral_patterns/hook_pattern_db.json")


class ViralPatternEngine:
    """
    Sprint 62
    AI Viral Pattern Engine 1.0

    역할:
    - 영상 후보의 제목, 설명, 통계, 쇼핑 적합도 분석
    - 후킹 유형 자동 분류
    - 후보별 바이럴 점수 계산
    - 성공 패턴 요약
    - Pattern DB 누적 저장

    현재 버전은 외부 AI API 없이 동작하는 규칙 기반 엔진입니다.
    이후 AI 모델, OCR, 장면 분석 결과를 연결할 수 있습니다.
    """

    ENGINE_VERSION = "viral-pattern-engine-62-1"

    def analyze(
        self,
        candidates: List[Dict[str, Any]] | None = None,
        project: Any = None,
        product_plan: Dict[str, Any] | None = None,
        save_db: bool = True,
    ) -> Dict[str, Any]:
        candidates = candidates or []
        product_plan = product_plan or {}

        analyzed_candidates: List[Dict[str, Any]] = []

        for item in candidates:
            if not isinstance(item, dict):
                continue
            analyzed_candidates.append(self._analyze_candidate(item))

        analyzed_candidates.sort(
            key=lambda row: row.get("viral_pattern_score", 0),
            reverse=True,
        )

        pattern_summary = self._build_pattern_summary(analyzed_candidates)

        result = {
            "ok": True,
            "engine_version": self.ENGINE_VERSION,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "project": self._project_payload(project),
            "product": self._product_payload(
                project=project,
                product_plan=product_plan,
            ),
            "candidate_count": len(analyzed_candidates),
            "top_candidates": analyzed_candidates[:10],
            "all_candidates": analyzed_candidates,
            "pattern_summary": pattern_summary,
            "best_pattern": pattern_summary[0] if pattern_summary else {},
        }

        if save_db:
            result["pattern_db"] = self._save_pattern_db(result)

        return result

    def _analyze_candidate(self, item: Dict[str, Any]) -> Dict[str, Any]:
        candidate = dict(item)
        text = self._candidate_text(candidate)
        hook_type = self._detect_hook_type(text)
        cta_type = self._detect_cta_type(text)

        stats = candidate.get("stats", {}) or {}

        views = self._safe_int(
            candidate.get("views")
            or candidate.get("view_count")
            or candidate.get("play_count")
            or stats.get("views")
        )
        likes = self._safe_int(
            candidate.get("likes")
            or candidate.get("like_count")
            or stats.get("likes")
        )
        comments = self._safe_int(
            candidate.get("comments")
            or candidate.get("comment_count")
            or stats.get("comments")
        )
        shares = self._safe_int(
            candidate.get("shares")
            or candidate.get("share_count")
            or stats.get("shares")
        )

        shopping_fit = self._extract_score(
            candidate.get("shopping_fit")
            or candidate.get("shopping_shorts_fit")
            or {}
        )
        video_quality = self._extract_score(candidate.get("video_quality") or {})
        real_vision = self._extract_score(candidate.get("real_vision") or {})
        engagement_score = self._engagement_score(
            views=views,
            likes=likes,
            comments=comments,
            shares=shares,
        )
        hook_score = self._hook_score(hook_type)
        cta_score = self._cta_score(cta_type)
        social_score = self._social_score(views)

        viral_pattern_score = round(
            social_score * 0.20
            + engagement_score * 0.30
            + hook_score * 0.20
            + shopping_fit * 0.10
            + video_quality * 0.05
            + cta_score * 0.15,
            2,
        )

        candidate.update(
            {
                "viral_engine_version": self.ENGINE_VERSION,
                "hook_type": hook_type,
                "cta_type": cta_type,
                "viral_metrics": {
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "shares": shares,
                },
                "viral_score_breakdown": {
                    "social": social_score,
                    "engagement": engagement_score,
                    "hook": hook_score,
                    "shopping_fit": shopping_fit,
                    "video_quality": video_quality,
                    "real_vision": real_vision,
                    "cta": cta_score,
                },
                "viral_pattern_score": viral_pattern_score,
                "viral_recommended": viral_pattern_score >= 60,
                "viral_reasons": self._build_reasons(
                    hook_type=hook_type,
                    cta_type=cta_type,
                    views=views,
                    engagement_score=engagement_score,
                    shopping_fit=shopping_fit,
                    video_quality=video_quality,
                ),
            }
        )
        return candidate

    def _build_pattern_summary(
        self,
        candidates: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        buckets: Dict[str, Dict[str, Any]] = {}

        for item in candidates:
            hook_type = item.get("hook_type", "general")
            bucket = buckets.setdefault(
                hook_type,
                {
                    "hook_type": hook_type,
                    "count": 0,
                    "total_views": 0,
                    "total_score": 0.0,
                    "recommended_count": 0,
                },
            )
            bucket["count"] += 1
            bucket["total_views"] += item.get("viral_metrics", {}).get("views", 0)
            bucket["total_score"] += item.get("viral_pattern_score", 0)
            if item.get("viral_recommended"):
                bucket["recommended_count"] += 1

        summary: List[Dict[str, Any]] = []

        for bucket in buckets.values():
            count = max(bucket.get("count", 0), 1)
            summary.append(
                {
                    "hook_type": bucket.get("hook_type"),
                    "count": bucket.get("count", 0),
                    "avg_views": round(bucket.get("total_views", 0) / count, 2),
                    "avg_viral_score": round(bucket.get("total_score", 0) / count, 2),
                    "recommended_count": bucket.get("recommended_count", 0),
                }
            )

        summary.sort(
            key=lambda row: (
                row.get("avg_viral_score", 0),
                row.get("avg_views", 0),
            ),
            reverse=True,
        )
        return summary

    def _save_pattern_db(self, result: Dict[str, Any]) -> Dict[str, Any]:
        PATTERN_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

        current_db = {
            "version": "hook-pattern-db-62-1",
            "updated_at": "",
            "patterns": {},
            "history": [],
        }

        if PATTERN_DB_PATH.exists():
            try:
                loaded = json.loads(PATTERN_DB_PATH.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    current_db.update(loaded)
            except Exception:
                pass

        patterns = current_db.setdefault("patterns", {})

        for row in result.get("pattern_summary", []):
            hook_type = row.get("hook_type", "general")
            previous = patterns.get(hook_type, {})
            previous_count = self._safe_int(previous.get("count"))
            new_count = self._safe_int(row.get("count"))
            total_count = previous_count + new_count

            previous_avg_views = self._safe_float(previous.get("avg_views"))
            new_avg_views = self._safe_float(row.get("avg_views"))
            previous_avg_score = self._safe_float(previous.get("avg_viral_score"))
            new_avg_score = self._safe_float(row.get("avg_viral_score"))

            combined_avg_views = (
                previous_avg_views * previous_count + new_avg_views * new_count
            ) / max(total_count, 1)
            combined_avg_score = (
                previous_avg_score * previous_count + new_avg_score * new_count
            ) / max(total_count, 1)

            patterns[hook_type] = {
                "count": total_count,
                "avg_views": round(combined_avg_views, 2),
                "avg_viral_score": round(combined_avg_score, 2),
                "recommended_count": self._safe_int(
                    previous.get("recommended_count")
                )
                + self._safe_int(row.get("recommended_count")),
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

        history = current_db.setdefault("history", [])
        history.append(
            {
                "created_at": result.get("created_at"),
                "project": result.get("project"),
                "product": result.get("product"),
                "candidate_count": result.get("candidate_count", 0),
                "best_pattern": result.get("best_pattern", {}),
            }
        )

        current_db["history"] = history[-100:]
        current_db["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        PATTERN_DB_PATH.write_text(
            json.dumps(current_db, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return {
            "ok": True,
            "path": str(PATTERN_DB_PATH),
            "pattern_count": len(patterns),
            "history_count": len(current_db.get("history", [])),
        }

    def _candidate_text(self, item: Dict[str, Any]) -> str:
        values = [
            item.get("title"),
            item.get("caption"),
            item.get("description"),
            item.get("purpose"),
            item.get("note"),
            item.get("keyword"),
        ]
        return " ".join(
            str(value)
            for value in values
            if value is not None
        ).lower()

    def _detect_hook_type(self, text: str) -> str:
        patterns = {
            "question": ["왜", "어떻게", "알고 계셨", "이거 아세요", "?"],
            "problem_solution": ["불편", "문제", "고민", "해결", "더 이상", "없이"],
            "comparison": ["비교", "전후", "vs", "차이", "바꾸기 전", "바꾼 후"],
            "surprise": ["대박", "충격", "몰랐", "처음 알았", "이게 된다고"],
            "empathy": ["공감", "직장인", "주부", "육아", "매일", "저만 그런가요"],
            "benefit": ["편해", "삶의 질", "추천", "필수템", "꿀템", "생활템"],
        }

        for hook_type, keywords in patterns.items():
            if any(keyword in text for keyword in keywords):
                return hook_type
        return "general"

    def _detect_cta_type(self, text: str) -> str:
        if any(keyword in text for keyword in ["댓글", "남겨주세요", "키워드"]):
            return "comment"
        if any(keyword in text for keyword in ["링크", "구매", "확인하세요", "프로필"]):
            return "link"
        if any(keyword in text for keyword in ["팔로우", "구독", "좋아요"]):
            return "follow"
        return "none"

    def _hook_score(self, hook_type: str) -> float:
        scores = {
            "problem_solution": 92,
            "question": 88,
            "surprise": 86,
            "comparison": 84,
            "empathy": 82,
            "benefit": 80,
            "general": 65,
        }
        return float(scores.get(hook_type, 65))

    def _cta_score(self, cta_type: str) -> float:
        scores = {
            "comment": 85,
            "link": 80,
            "follow": 75,
            "none": 50,
        }
        return float(scores.get(cta_type, 50))

    def _social_score(self, views: int) -> float:
        if views >= 10_000_000:
            return 100.0
        if views >= 3_000_000:
            return 95.0
        if views >= 1_000_000:
            return 90.0
        if views >= 500_000:
            return 82.0
        if views >= 100_000:
            return 72.0
        if views >= 10_000:
            return 60.0
        if views > 0:
            return 45.0
        return 30.0

    def _engagement_score(
        self,
        views: int,
        likes: int,
        comments: int,
        shares: int,
    ) -> float:

        if views <= 0:
            return 30.0

        like_rate = likes / views
        comment_rate = comments / views
        share_rate = shares / views

        like_score = min(
            like_rate / 0.10 * 100,
            100,
        )

        comment_score = min(
            comment_rate / 0.01 * 100,
            100,
        )

        share_score = min(
            share_rate / 0.02 * 100,
            100,
        )

        score = (
            like_score * 0.45
            + comment_score * 0.25
            + share_score * 0.30
        )

        return round(score, 2)
    
    def _build_reasons(
        self,
        hook_type: str,
        cta_type: str,
        views: int,
        engagement_score: float,
        shopping_fit: float,
        video_quality: float,
    ) -> List[str]:
        reasons: List[str] = []

        if hook_type != "general":
            reasons.append(f"{hook_type} 후킹 패턴 감지")
        if views >= 100_000:
            reasons.append("조회수 검증 후보")
        if engagement_score >= 60:
            reasons.append("참여율 우수")
        if shopping_fit >= 70:
            reasons.append("쇼핑쇼츠 적합도 우수")
        if video_quality >= 70:
            reasons.append("영상 품질 양호")
        if cta_type != "none":
            reasons.append(f"{cta_type} CTA 감지")

        return reasons or ["기본 바이럴 패턴 점수 적용"]

    def _extract_score(self, value: Any) -> float:
        if isinstance(value, dict):
            for key in (
                "fit_score",
                "score",
                "quality_score",
                "suitability_score",
                "final_score",
                "vision_score",
            ):
                if value.get(key) is not None:
                    return self._clamp_score(value.get(key))

            for nested_key in ("result", "summary", "analysis"):
                nested = value.get(nested_key)
                if isinstance(nested, dict):
                    score = self._extract_score(nested)
                    if score > 0:
                        return score

        return self._clamp_score(value)

    def _project_payload(self, project: Any) -> Dict[str, Any]:
        if project is None:
            return {}
        return {
            "id": getattr(project, "id", None),
            "product_name": getattr(project, "product_name", ""),
            "title": getattr(project, "title", ""),
            "keyword": getattr(project, "keyword", ""),
        }

    def _product_payload(
        self,
        project: Any,
        product_plan: Dict[str, Any],
    ) -> Dict[str, Any]:
        payload = (
            product_plan.get("project_payload", {})
            if isinstance(product_plan, dict)
            else {}
        )
        return {
            "product_name": payload.get("product_name")
            or getattr(project, "product_name", ""),
            "keyword": payload.get("keyword") or getattr(project, "keyword", ""),
            "category": payload.get("category") or getattr(project, "category", ""),
        }

    def _clamp_score(self, value: Any) -> float:
        return max(min(self._safe_float(value), 100.0), 0.0)

    def _safe_int(self, value: Any) -> int:
        try:
            return max(int(float(value or 0)), 0)
        except (TypeError, ValueError):
            return 0

    def _safe_float(self, value: Any) -> float:
        try:
            return max(float(value or 0), 0.0)
        except (TypeError, ValueError):
            return 0.0