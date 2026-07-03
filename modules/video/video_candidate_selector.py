class VideoCandidateSelector:
    def select(self, candidates):
        candidates = candidates or []

        scored = []
        for item in candidates:
            score = self._score_candidate(item)
            new_item = dict(item)

            new_item["ai_score"] = score
            new_item["final_ai_score"] = score
            new_item["ai_recommendation"] = self._recommendation(score)

            scored.append(new_item)

        scored.sort(key=lambda x: x.get("final_ai_score", x.get("ai_score", 0)), reverse=True)

        return {
            "ok": True,
            "count": len(scored),
            "best": scored[0] if scored else None,
            "top3": scored[:3],
            "all": scored,
        }

    def _score_candidate(self, item):
        score = 0

        # 1. 기존 검색 기반 점수
        base_score = item.get("score", 0)
        if isinstance(base_score, (int, float)):
            score += min(base_score, 100) * 0.35

        # 2. 플랫폼 가산점
        platform = str(item.get("platform", "")).lower()
        if platform == "taobao":
            score += 12
        elif platform == "1688":
            score += 10
        elif platform == "tiktok":
            score += 5

        # 3. 텍스트 기반 쇼핑 영상 힌트
        purpose = str(item.get("purpose", ""))
        title = str(item.get("title", ""))
        keyword = str(item.get("keyword", ""))

        text = f"{purpose} {title} {keyword}"

        if "主图视频" in text:
            score += 10

        if "实拍" in text:
            score += 10

        if "买家秀" in text:
            score += 8

        if "安装" in text or "사용" in text:
            score += 7

        if "同款" in text:
            score += 5

        if "review" in text.lower():
            score += 4

        # 4. Video Quality 점수 반영
        video_quality = item.get("video_quality") or {}
        quality_score = video_quality.get("score")

        if isinstance(quality_score, (int, float)):
            score += min(quality_score, 100) * 0.25

        # 5. 쇼핑쇼츠 적합도 반영
        shopping_fit = (
            item.get("shopping_shorts_fit")
            or item.get("shopping_fit")
            or item.get("shorts_fit")
            or {}
        )

        fit_score = shopping_fit.get("score")
        if isinstance(fit_score, (int, float)):
            score += min(fit_score, 100) * 0.25

        # 6. Real Vision 결과 반영
        real_vision = item.get("real_vision") or {}

        if real_vision.get("ok"):
            score += 5

        summary = str(real_vision.get("summary", ""))

        if "product" in summary.lower() or "상품" in summary:
            score += 5

        if "hand" in summary.lower() or "손" in summary:
            score += 3

        if "demo" in summary.lower() or "사용" in summary:
            score += 4

        return round(min(score, 100), 1)

    def _recommendation(self, score):
        if score >= 90:
            return "최우선 후보"
        if score >= 80:
            return "우선 후보"
        if score >= 70:
            return "검토 후보"
        if score >= 60:
            return "보조 후보"
        return "낮은 우선순위"