from typing import List, Dict


class CutPlanner:
    """
    Sprint 27
    AI Cut Planner 2.0

    후보영상(candidate) 기반 추천
    - Video Quality 반영
    - Shopping Shorts 적합도 반영
    - confidence 생성
    - 추천 이유(reason) 생성
    """

    def build(self, content_pack: Dict) -> List[Dict]:

        timeline = (
            content_pack.get("edit_assistant", {})
            .get("timeline", [])
        )

        candidates = (
            content_pack.get("selected_sources", [])
        )

        video_quality = (
            content_pack.get("video_quality", {})
        )

        suitability = video_quality.get(
            "suitability_score",
            70
        )

        plans = []

        for idx, item in enumerate(timeline, start=1):

            candidate = {}

            if candidates:
                candidate = candidates[
                    (idx - 1) % len(candidates)
                ]

            confidence = self._confidence(
                candidate,
                video_quality,
            )

            start, end = self._recommend_time(
                confidence,
                idx,
            )

            plans.append(
                {
                    "scene": idx,
                    "purpose": f"Scene {idx}",

                    "candidate": candidate.get(
                        "platform",
                        "현재 연결 영상",
                    ),

                    "query": candidate.get(
                        "query",
                        "",
                    ),

                    "url": candidate.get(
                        "url",
                        "",
                    ),

                    "start": start,
                    "end": end,

                    "confidence": confidence,

                    "effect": item.get(
                        "sfx",
                        "",
                    ),

                    "zoom": item.get(
                        "zoom",
                        "",
                    ),

                    "subtitle": item.get(
                        "subtitle_animation",
                        "",
                    ),

                    "reason": self._reason(
                        candidate,
                        confidence,
                        suitability,
                    ),
                }
            )

        return plans

    def _confidence(
        self,
        candidate,
        video_quality,
    ):

        score = 0.55

        candidate_score = candidate.get("score")

        if isinstance(candidate_score, (int, float)):
            score += candidate_score / 200

        quality = video_quality.get("score")

        if isinstance(quality, (int, float)):
            score += quality / 400

        return round(min(score, 0.99), 2)

    def _recommend_time(
        self,
        confidence,
        scene,
    ):

        if confidence >= 0.9:
            return "00.0", "05.0"

        if confidence >= 0.8:
            return "01.0", "05.5"

        if confidence >= 0.7:
            return "02.0", "06.0"

        return "03.0", "06.5"

    def _reason(
        self,
        candidate,
        confidence,
        suitability,
    ):

        reasons = []

        if candidate.get("platform"):
            reasons.append(candidate["platform"])

        if candidate.get("query"):
            reasons.append(candidate["query"])

        reasons.append(f"적합도 {suitability}")

        reasons.append(f"Confidence {confidence}")

        if confidence >= 0.9:
            reasons.append("대표 후킹 컷 추천")

        elif confidence >= 0.8:
            reasons.append("상품 노출 추천")

        else:
            reasons.append("보조 컷 추천")

        return " / ".join(reasons)