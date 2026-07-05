from typing import List, Dict


class CutPlanner:
    """
    Sprint 26
    AI Cut Planner 1.0

    현재는 기본 추천 로직을 제공하고,
    이후 Vision/OCR/Video Quality와 연동 예정.
    """

    def build(self, content_pack: Dict) -> List[Dict]:
        timeline = (
            content_pack.get("edit_assistant", {})
            .get("timeline", [])
        )

        plans = []

        for idx, item in enumerate(timeline, start=1):

            plans.append(
                {
                    "scene": idx,
                    "purpose": f"Scene {idx}",
                    "candidate": "현재 연결 영상",
                    "start": "00.0",
                    "end": "03.0",
                    "effect": item.get("sfx", ""),
                    "zoom": item.get("zoom", ""),
                    "subtitle": item.get("subtitle_animation", ""),
                    "reason": "대표 콘텐츠 기준 추천",
                }
            )

        return plans