import json
import math
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class ViralPatternEngine:
    """
    Sprint 62 Viral Pattern Engine

    역할
    - 영상 후보의 조회수, 좋아요, 댓글, 공유 수치를 정규화
    - 제목/설명에서 후킹 패턴과 쇼핑형 표현 감지
    - 후보마다 viral_pattern_score 부여
    - 상위 바이럴 패턴과 대표 후보 반환
    - 필요 시 분석 결과를 JSON으로 저장

    외부 AI API 없이 동작합니다.
    """

    ENGINE_VERSION = "viral-pattern-engine-62-1"

    HOOK_PATTERNS = {
        "problem_solution": [
            "문제",
            "해결",
            "불편",
            "고민",
            "걱정",
            "스트레스",
            "困扰",
            "解决",
            "烦恼",
            "problem",
            "solution",
            "fix",
        ],
        "curiosity": [
            "왜",
            "이유",
            "비밀",
            "몰랐",
            "처음",
            "대체",
            "정체",
            "到底",
            "为什么",
            "秘密",
            "竟然",
            "原来",
            "why",
            "secret",
            "didn't know",
        ],
        "before_after": [
            "전후",
            "비포",
            "애프터",
            "바꾸기 전",
            "바꾼 후",
            "before",
            "after",
            "前后",
            "使用前",
            "使用后",
        ],
        "demonstration": [
            "사용법",
            "직접",
            "테스트",
            "실험",
            "보여드",
            "시연",
            "测评",
            "实测",
            "演示",
            "使用方法",
            "test",
            "demo",
            "how to",
        ],
        "surprise": [
            "헉",
            "대박",
            "놀랍",
            "충격",
            "미쳤",
            "반전",
            "没想到",
            "惊了",
            "震惊",
            "绝了",
            "wow",
            "amazing",
            "shocking",
        ],
        "social_proof": [
            "후기",
            "리뷰",
            "인기",
            "판매",
            "재구매",
            "추천",
            "爆款",
            "热卖",
            "回购",
            "推荐",
            "review",
            "best seller",
            "viral",
        ],
        "urgency": [
            "지금",
            "품절",
            "마감",
            "한정",
            "서두르",
            "오늘만",
            "限时",
            "抢购",
            "售罄",
            "马上",
            "now",
            "limited",
            "sold out",
        ],
        "comparison": [
            "비교",
            "차이",
            "대신",
            "vs",
            "뭐가 더",
            "区别",
            "对比",
            "哪个好",
            "compare",
            "versus",
        ],
    }

    SHOPPING_KEYWORDS = [
        "구매",
        "추천",
        "가격",
        "가성비",
        "할인",
        "장바구니",
        "링크",
        "제품",
        "상품",
        "리뷰",
        "사용",
        "필수템",
        "꿀템",
        "购买",
        "推荐",
        "价格",
        "优惠",
        "商品",
        "好物",
        "必备",
        "同款",
        "buy",
        "price",
        "deal",
        "product",
        "shop",
        "must have",
    ]

    CTA_KEYWORDS = [
        "확인",
        "클릭",
        "링크",
        "구매",
        "장바구니",
        "프로필",
        "댓글",
        "点击",
        "链接",
        "购买",
        "下单",
        "购物车",
        "click",
        "link",
        "buy",
        "order",
        "shop now",
    ]

    def analyze(
        self,
        candidates: Optional[List[Dict[str, Any]]] = None,
        project: Any = None,
        product_plan: Optional[Dict[str, Any]] = None,
        save_db: bool = False,
        top_n: int = 5,
    ) -> Dict[str, Any]:
        candidates = candidates or []
        product_plan = product_plan or {}

        clean_candidates = [
            dict(item)
            for item in candidates
            if isinstance(item, dict)
        ]

        if not clean_candidates:
            result = self._empty_result()
            if save_db:
                result["saved_path"] = self._save_result(
                    result=result,
                    project=project,
                )
            return result

        metrics = [
            self._extract_metrics(item)
            for item in clean_candidates
        ]

        max_views = max(
            [m["views"] for m in metrics] + [1]
        )
        max_likes = max(
            [m["likes"] for m in metrics] + [1]
        )
        max_comments = max(
            [m["comments"] for m in metrics] + [1]
        )
        max_shares = max(
            [m["shares"] for m in metrics] + [1]
        )

        analyzed = []

        for index, item in enumerate(
            clean_candidates,
            start=1,
        ):
            metric = metrics[index - 1]
            text = self._candidate_text(item)

            pattern_scores = self._detect_patterns(text)
            primary_pattern = self._primary_pattern(
                pattern_scores
            )

            social_score = self._social_score(
                metric=metric,
                max_views=max_views,
                max_likes=max_likes,
                max_comments=max_comments,
                max_shares=max_shares,
            )

            engagement_score = self._engagement_score(metric)
            hook_score = self._hook_score(pattern_scores)
            shopping_score = self._keyword_score(
                text,
                self.SHOPPING_KEYWORDS,
                max_score=100.0,
            )
            cta_score = self._keyword_score(
                text,
                self.CTA_KEYWORDS,
                max_score=100.0,
            )
            title_score = self._title_quality_score(text)
            existing_quality = self._existing_quality_score(item)
            fit_score = self._existing_fit_score(item)

            viral_score = (
               social_score * 0.20
               + engagement_score * 0.30
               + hook_score * 0.20
               + shopping_score * 0.10
               + cta_score * 0.15
               + title_score * 0.05
            )

            viral_score = round(
                max(0.0, min(100.0, viral_score)),
                2,
            )

            new_item = dict(item)
            new_item["viral_pattern_score"] = viral_score
            new_item["viral_score"] = viral_score
            new_item["viral_pattern_type"] = primary_pattern
            new_item["hook_type"] = primary_pattern
            new_item["viral_pattern"] = {
                "engine_version": self.ENGINE_VERSION,
                "score": viral_score,
                "primary_pattern": primary_pattern,
                "pattern_scores": pattern_scores,
                "social_score": round(social_score, 2),
                "engagement_score": round(
                    engagement_score,
                    2,
                ),
                "hook_score": round(hook_score, 2),
                "shopping_score": round(
                    shopping_score,
                    2,
                ),
                "cta_score": round(cta_score, 2),
                "title_score": round(title_score, 2),
                "existing_quality_score": round(
                    existing_quality,
                    2,
                ),
                "shopping_fit_score": round(
                    fit_score,
                    2,
                ),
                "metrics": metric,
            }

            analyzed.append(new_item)

        analyzed.sort(
            key=lambda x: (
                self._to_number(
                    x.get("viral_pattern_score")
                ),
                self._to_number(
                    x.get("views")
                    or x.get("view_count")
                    or x.get("play_count")
                ),
            ),
            reverse=True,
        )

        for rank, item in enumerate(
            analyzed,
            start=1,
        ):
            item["viral_rank"] = rank
            if isinstance(
                item.get("viral_pattern"),
                dict,
            ):
                item["viral_pattern"]["rank"] = rank

        top_candidates = analyzed[: max(1, int(top_n))]
        pattern_summary = self._pattern_summary(analyzed)
        best_candidate = (
            top_candidates[0]
            if top_candidates
            else {}
        )

        best_pattern = {
            "pattern_type": best_candidate.get(
                "viral_pattern_type",
                "unknown",
            ),
            "viral_pattern_score": best_candidate.get(
                "viral_pattern_score",
                0.0,
            ),
            "title": best_candidate.get(
                "title",
                "",
            ),
            "url": best_candidate.get(
                "url",
                "",
            ),
            "platform": best_candidate.get(
                "platform",
                "",
            ),
            "rank": best_candidate.get(
                "viral_rank",
                0,
            ),
        }

        result = {
            "ok": True,
            "engine_version": self.ENGINE_VERSION,
            "candidate_count": len(analyzed),
            "top_candidates": top_candidates,
            "all_candidates": analyzed,
            "pattern_summary": pattern_summary,
            "best_pattern": best_pattern,
            "generated_at": datetime.now().isoformat(
                timespec="seconds"
            ),
        }

        if save_db:
            result["saved_path"] = self._save_result(
                result=result,
                project=project,
            )

        return result

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "ok": True,
            "engine_version": self.ENGINE_VERSION,
            "candidate_count": 0,
            "top_candidates": [],
            "all_candidates": [],
            "pattern_summary": [],
            "best_pattern": {},
            "generated_at": datetime.now().isoformat(
                timespec="seconds"
            ),
        }

    def _extract_metrics(
        self,
        item: Dict[str, Any],
    ) -> Dict[str, float]:
        stats = item.get("stats")
        if not isinstance(stats, dict):
            stats = {}

        metrics = item.get("metrics")
        if not isinstance(metrics, dict):
            metrics = {}

        views = self._first_number(
            item,
            stats,
            metrics,
            keys=[
                "views",
                "view_count",
                "play_count",
                "plays",
                "playCount",
                "digg_count",
            ],
        )

        likes = self._first_number(
            item,
            stats,
            metrics,
            keys=[
                "likes",
                "like_count",
                "digg_count",
                "diggCount",
            ],
        )

        comments = self._first_number(
            item,
            stats,
            metrics,
            keys=[
                "comments",
                "comment_count",
                "commentCount",
            ],
        )

        shares = self._first_number(
            item,
            stats,
            metrics,
            keys=[
                "shares",
                "share_count",
                "shareCount",
                "reposts",
            ],
        )

        return {
            "views": views,
            "likes": likes,
            "comments": comments,
            "shares": shares,
        }

    def _first_number(
        self,
        *sources: Dict[str, Any],
        keys: List[str],
    ) -> float:
        for source in sources:
            if not isinstance(source, dict):
                continue

            for key in keys:
                if key not in source:
                    continue

                value = self._to_number(source.get(key))
                if value > 0:
                    return value

        return 0.0

    def _to_number(self, value: Any) -> float:
        if value is None:
            return 0.0

        if isinstance(value, bool):
            return float(value)

        if isinstance(value, (int, float)):
            try:
                return float(value)
            except Exception:
                return 0.0

        text = str(value).strip().lower()
        if not text:
            return 0.0

        text = text.replace(",", "").replace(" ", "")

        multiplier = 1.0

        suffix_map = {
            "k": 1_000.0,
            "천": 1_000.0,
            "만": 10_000.0,
            "w": 10_000.0,
            "m": 1_000_000.0,
            "백만": 1_000_000.0,
            "억": 100_000_000.0,
        }

        for suffix, factor in suffix_map.items():
            if text.endswith(suffix):
                multiplier = factor
                text = text[: -len(suffix)]
                break

        text = re.sub(r"[^0-9.\-]", "", text)

        try:
            return float(text) * multiplier
        except Exception:
            return 0.0

    def _candidate_text(
        self,
        item: Dict[str, Any],
    ) -> str:
        parts = [
            item.get("title", ""),
            item.get("description", ""),
            item.get("caption", ""),
            item.get("text", ""),
            item.get("author", ""),
            item.get("keyword", ""),
            item.get("purpose", ""),
        ]

        return " ".join(
            str(part)
            for part in parts
            if part
        ).lower()

    def _detect_patterns(
        self,
        text: str,
    ) -> Dict[str, float]:
        scores = {}

        for pattern_name, keywords in (
            self.HOOK_PATTERNS.items()
        ):
            hit_count = sum(
                1
                for keyword in keywords
                if keyword.lower() in text
            )

            if hit_count <= 0:
                score = 0.0
            else:
                score = min(
                    100.0,
                    42.0 + (hit_count - 1) * 18.0,
                )

            scores[pattern_name] = round(
                score,
                2,
            )

        return scores

    def _primary_pattern(
        self,
        pattern_scores: Dict[str, float],
    ) -> str:
        if not pattern_scores:
            return "general_product_demo"

        name, score = max(
            pattern_scores.items(),
            key=lambda x: x[1],
        )

        if score <= 0:
            return "general_product_demo"

        return name

    def _social_score(
        self,
        metric: Dict[str, float],
        max_views: float,
        max_likes: float,
        max_comments: float,
        max_shares: float,
    ) -> float:
        view_score = self._log_normalize(
            metric["views"],
            max_views,
        )
        like_score = self._log_normalize(
            metric["likes"],
            max_likes,
        )
        comment_score = self._log_normalize(
            metric["comments"],
            max_comments,
        )
        share_score = self._log_normalize(
            metric["shares"],
            max_shares,
        )

        return (
            view_score * 0.45
            + like_score * 0.25
            + comment_score * 0.10
            + share_score * 0.20
        )

    def _log_normalize(
        self,
        value: float,
        maximum: float,
    ) -> float:
        value = max(0.0, value)
        maximum = max(1.0, maximum)

        if value <= 0:
            return 0.0

        return min(
            100.0,
            100.0
            * math.log1p(value)
            / math.log1p(maximum),
        )

    def _engagement_score(
        self,
        metric: Dict[str, float],
    ) -> float:

        views = metric["views"]

        if views <= 0:
            return 30.0

        likes = metric["likes"]
        comments = metric["comments"]
        shares = metric["shares"]

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

    def _hook_score(
        self,
        pattern_scores: Dict[str, float],
    ) -> float:
        if not pattern_scores:
            return 0.0

        ordered = sorted(
            pattern_scores.values(),
            reverse=True,
        )

        best = ordered[0] if ordered else 0.0
        second = ordered[1] if len(ordered) > 1 else 0.0

        return min(
            100.0,
            best * 0.75 + second * 0.25,
        )

    def _keyword_score(
        self,
        text: str,
        keywords: List[str],
        max_score: float = 100.0,
    ) -> float:
        hits = sum(
            1
            for keyword in keywords
            if keyword.lower() in text
        )

        if hits <= 0:
            return 0.0

        return min(
            max_score,
            35.0 + hits * 15.0,
        )

    def _title_quality_score(
        self,
        text: str,
    ) -> float:
        if not text:
            return 0.0

        score = 30.0
        length = len(text)

        if 12 <= length <= 180:
            score += 25.0
        elif length > 0:
            score += 10.0

        if re.search(r"[?!？！]", text):
            score += 12.0

        if re.search(r"\d", text):
            score += 8.0

        if any(
            token in text
            for token in [
                "왜",
                "비밀",
                "추천",
                "후기",
                "비교",
                "why",
                "secret",
                "review",
                "推荐",
                "实测",
            ]
        ):
            score += 15.0

        return min(100.0, score)

    def _existing_quality_score(
        self,
        item: Dict[str, Any],
    ) -> float:
        quality = item.get("video_quality")

        if isinstance(quality, dict):
            for key in [
                "score",
                "quality_score",
                "suitability_score",
                "total_score",
            ]:
                value = self._to_number(
                    quality.get(key)
                )
                if value > 0:
                    return min(100.0, value)

        for key in [
            "video_quality_score",
            "quality_score",
        ]:
            value = self._to_number(item.get(key))
            if value > 0:
                return min(100.0, value)

        return 50.0

    def _existing_fit_score(
        self,
        item: Dict[str, Any],
    ) -> float:
        fit_sources = [
            item.get("shopping_shorts_fit"),
            item.get("shopping_fit"),
        ]

        for source in fit_sources:
            if not isinstance(source, dict):
                continue

            for key in [
                "fit_score",
                "score",
                "shopping_fit_score",
                "total_score",
            ]:
                value = self._to_number(
                    source.get(key)
                )
                if value > 0:
                    return min(100.0, value)

        for key in [
            "shopping_fit_score",
            "fit_score",
        ]:
            value = self._to_number(item.get(key))
            if value > 0:
                return min(100.0, value)

        return 50.0

    def _pattern_summary(
        self,
        candidates: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        counter = Counter(
            item.get(
                "viral_pattern_type",
                "general_product_demo",
            )
            for item in candidates
        )

        score_map: Dict[str, List[float]] = {}

        for item in candidates:
            pattern = item.get(
                "viral_pattern_type",
                "general_product_demo",
            )
            score_map.setdefault(pattern, []).append(
                self._to_number(
                    item.get("viral_pattern_score")
                )
            )

        summary = []

        for pattern, count in counter.most_common():
            values = score_map.get(pattern, [])
            average = (
                sum(values) / len(values)
                if values
                else 0.0
            )

            summary.append(
                {
                    "pattern_type": pattern,
                    "count": count,
                    "average_score": round(
                        average,
                        2,
                    ),
                }
            )

        summary.sort(
            key=lambda x: (
                x["average_score"],
                x["count"],
            ),
            reverse=True,
        )

        return summary

    def _save_result(
        self,
        result: Dict[str, Any],
        project: Any = None,
    ) -> str:
        project_id = getattr(
            project,
            "id",
            None,
        )

        if project_id in [None, ""]:
            project_id = "default"

        output_dir = Path(
            "exports"
        ) / "viral_patterns"
        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = (
            output_dir
            / f"project_{project_id}_viral_pattern.json"
        )

        payload = dict(result)

        try:
            output_path.write_text(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                ),
                encoding="utf-8",
            )
        except Exception as exc:
            print(
                "[Sprint62] ViralPattern save ERROR:",
                repr(exc),
                flush=True,
            )
            return ""

        return str(output_path)