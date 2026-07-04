class VideoMixPlanner:
    """
    Sprint 14
    AI 추천 TOP3를 자동으로 편집 역할에 배치
    """

    def build(self, candidate_selection):
        top3 = candidate_selection.get("top3", [])

        result = {
            "ok": True,
            "segments": []
        }

        roles = [
            "hook",
            "demo",
            "cta",
        ]

        for role, item in zip(roles, top3):
            result["segments"].append({
                "role": role,
                "title": item.get("title"),
                "platform": item.get("platform"),
                "ai_score": item.get("ai_score"),
                "reasons": item.get("ai_reasons", []),
            })

        return result