from pathlib import Path
from modules.video.ai_analyzer import VideoAIAnalyzer
from modules.video.vision_ai_engine import VisionAIEngine


class SourceVideoRanker:
    """
    여러 원본 영상 후보를 빠르게 점수화합니다.
    실제 YOLO/PaddleOCR 전 단계의 빠른 필터링 용도입니다.
    """

    def rank(self, video_items, sample_count=6):
        ranked = []
        for item in video_items or []:
            video_path = item.get("path", "")
            if not Path(video_path).exists():
                continue

            video_ai = VideoAIAnalyzer().analyze(video_path, sample_count=sample_count)
            vision = VisionAIEngine().analyze(video_path, sample_count=min(sample_count, 6), use_ocr=False)

            score = self.score(video_ai, vision)
            ranked.append({
                **item,
                "score": score,
                "grade": self.grade(score),
                "reason": self.reason(video_ai, vision, score),
                "video_ai": {
                    "duration": video_ai.get("duration"),
                    "width": video_ai.get("width"),
                    "height": video_ai.get("height"),
                    "orientation": video_ai.get("orientation"),
                },
                "recommend": "Real Vision Runner 후보" if score >= 75 else "보조 후보" if score >= 60 else "사용 주의",
            })

        return sorted(ranked, key=lambda x: x.get("score", 0), reverse=True)

    def score(self, video_ai, vision):
        if not video_ai.get("ok"):
            return 0

        score = 50
        width = int(video_ai.get("width") or 0)
        height = int(video_ai.get("height") or 0)
        duration = float(video_ai.get("duration") or 0)

        if height > width:
            score += 15
        if 8 <= duration <= 60:
            score += 10

        top_frames = video_ai.get("top_frames", []) or []
        if top_frames:
            score += min(15, int(top_frames[0].get("score", 0) / 10))

        risk = vision.get("risk", {}) or {}
        bottom = risk.get("bottom_caption", {}).get("level", "없음")
        if bottom in ["높음", "중간"]:
            score -= 10

        return max(0, min(100, int(score)))

    def grade(self, score):
        if score >= 85:
            return "★★★★★"
        if score >= 75:
            return "★★★★"
        if score >= 60:
            return "★★★"
        if score >= 40:
            return "★★"
        return "★"

    def reason(self, video_ai, vision, score):
        reasons = []
        if video_ai.get("orientation") and "세로" in str(video_ai.get("orientation")):
            reasons.append("세로형 영상")
        else:
            reasons.append("크롭 필요 가능성")
        if score >= 75:
            reasons.append("쇼츠 후보로 적합")
        else:
            reasons.append("추가 검토 필요")
        return " / ".join(reasons)
