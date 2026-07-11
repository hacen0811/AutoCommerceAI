from modules.video.vision_score_engine import VisionScoreEngine


class SmartCutEngine:
    """
    SmartCut 2.0
    - 기존 video_ai 기반 추천 유지
    - YOLO/PaddleOCR 결과가 있으면 점수에 통합
    """

    def build(self, ai_result, product_name="", keyword="정보", yolo=None, ocr=None):
        if not ai_result or not ai_result.get("ok"):
            return self.empty(product_name, keyword)

        scored = VisionScoreEngine().score_frames(ai_result, yolo or {}, ocr or {})
        frames = scored.get("frames", [])

        if not frames:
            return self.empty(product_name, keyword)

        hook = frames[0]
        thumb_candidates = scored.get("thumbnail_candidates", [])[:5]
        delete_candidates = scored.get("delete_candidates", [])[:5]
        zoom_candidates = scored.get("zoom_candidates", [])[:5]

        return {
            "version": "2.0",
            "hook_cut": {
                "time": hook.get("time"),
                "frame": hook.get("frame"),
                "score": hook.get("score"),
                "reason": hook.get("reason"),
                "capcut": "0~2초에 배치 / Zoom In / 후킹 자막 / Pop 7 dB",
            },
            "thumbnail_candidates": [
                {
                    "rank": i + 1,
                    "time": item.get("time"),
                    "frame": item.get("frame"),
                    "score": item.get("score"),
                    "reason": item.get("reason"),
                }
                for i, item in enumerate(thumb_candidates)
            ],
            "delete_candidates": [
                {
                    "time": item.get("time"),
                    "reason": item.get("reason"),
                    "score": item.get("score"),
                    "action": "삭제 또는 짧게 컷",
                }
                for item in delete_candidates
            ],
            "zoom_candidates": [
                {
                    "time": item.get("time"),
                    "reason": item.get("reason"),
                    "score": item.get("score"),
                    "action": "105~115% Zoom In",
                }
                for item in zoom_candidates
            ],
            "scene_changes": ai_result.get("scene_changes", []),
            "scored_frames": frames,
            "timeline": self._timeline(hook, zoom_candidates, product_name, keyword),
            "capcut_summary": self._summary(product_name, keyword),
        }

    def empty(self, product_name="", keyword="정보"):
        return {
            "version": "2.0",
            "hook_cut": {},
            "thumbnail_candidates": [],
            "delete_candidates": [],
            "zoom_candidates": [],
            "scene_changes": [],
            "scored_frames": [],
            "timeline": self._default_timeline(product_name, keyword),
            "capcut_summary": "영상 분석 데이터가 없어 기본 쇼핑쇼츠 타임라인을 사용합니다.",
        }

    def _timeline(self, hook, zoom_candidates, product_name, keyword):
        zoom_time = zoom_candidates[0].get("time") if zoom_candidates else "5~10"
        hook_time = hook.get("time", 0)
        return [
            {
                "time": "0~2초",
                "role": "후킹",
                "source_time": hook_time,
                "guide": f"{hook_time}초 장면을 첫 컷으로 사용",
                "caption": "왜 이제 알았지?",
                "capcut": "Zoom In / Bounce / Pop 7 dB",
            },
            {
                "time": "2~5초",
                "role": "공감",
                "source_time": "문제 장면",
                "guide": f"{product_name} 사용 전 불편함을 보여주세요.",
                "caption": "저도 이거 때문에 스트레스였어요",
                "capcut": "BGM 8 dB / 자막 2줄 이하",
            },
            {
                "time": "5~10초",
                "role": "사용",
                "source_time": zoom_time,
                "guide": f"{zoom_time}초 부근 선명한 장면을 사용하세요.",
                "caption": "이렇게 쓰면 훨씬 편해요",
                "capcut": "Click 8 dB / 105~115% 확대",
            },
            {
                "time": "10~15초",
                "role": "효과",
                "source_time": "Before/After",
                "guide": "달라진 점을 짧게 보여주세요.",
                "caption": "작지만 체감은 큽니다",
                "capcut": "Slide Up / Whoosh 6 dB",
            },
            {
                "time": "15~20초",
                "role": "CTA",
                "source_time": "마지막 사용 장면",
                "guide": "댓글 키워드와 링크 안내를 넣으세요.",
                "caption": f"댓글에 '{keyword}' 남겨주세요 👇",
                "capcut": "Bounce / Pop 7 dB",
            },
        ]

    def _default_timeline(self, product_name="", keyword="정보"):
        return [
            {"time": "0~2초", "role": "후킹", "guide": "가장 강한 장면", "caption": "왜 이제 알았지?", "capcut": "Zoom In"},
            {"time": "2~5초", "role": "공감", "guide": "불편함", "caption": f"저도 {product_name} 때문에 스트레스였어요", "capcut": "BGM 8 dB"},
            {"time": "5~10초", "role": "사용", "guide": "제품 사용", "caption": "이렇게 쓰면 훨씬 편해요", "capcut": "Click 8 dB"},
            {"time": "10~15초", "role": "효과", "guide": "Before/After", "caption": "작지만 체감은 큽니다", "capcut": "Whoosh 6 dB"},
            {"time": "15~20초", "role": "CTA", "guide": "댓글/링크", "caption": f"댓글에 '{keyword}' 남겨주세요 👇", "capcut": "Pop 7 dB"},
        ]

    def _summary(self, product_name, keyword):
        return (
            f"{product_name} 쇼핑쇼츠는 첫 2초 후킹, 5~10초 사용 장면, 15~20초 CTA 구조를 추천합니다. "
            f"CTA는 댓글에 '{keyword}' 남겨주세요 형태가 적합합니다."
        )
