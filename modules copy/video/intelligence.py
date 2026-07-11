from pathlib import Path


class VideoIntelligence:
    """
    X 4.0 Starter:
    실제 OCR/객체인식 전 단계.
    OpenCV 프레임 분석 결과를 바탕으로
    자막/워터마크/컷 편집 판단 가이드를 강화합니다.
    """

    def inspect(self, ai_result):
        if not ai_result or not ai_result.get("ok"):
            return self.empty(ai_result.get("error", "분석 데이터 없음") if ai_result else "분석 데이터 없음")

        width = ai_result.get("width", 0)
        height = ai_result.get("height", 0)
        top_frames = ai_result.get("top_frames", [])
        scene_changes = ai_result.get("scene_changes", [])

        subtitle_risk = self.subtitle_risk(width, height)
        watermark_risk = self.watermark_risk(width, height)
        best_hook = top_frames[0] if top_frames else {}
        best_thumb = top_frames[1] if len(top_frames) > 1 else best_hook

        return {
            "ok": True,
            "subtitle_risk": subtitle_risk,
            "watermark_risk": watermark_risk,
            "best_hook_frame": best_hook,
            "best_thumbnail_frame": best_thumb,
            "scene_change_count": len(scene_changes),
            "capcut_actions": self.capcut_actions(subtitle_risk, watermark_risk),
            "shopping_shorts_timeline": self.shopping_timeline(ai_result, best_hook),
            "edit_summary": self.summary(subtitle_risk, watermark_risk, best_hook),
            "next_step": [
                "추천 후킹 프레임을 첫 0~2초에 배치",
                "중국어 자막/워터마크가 보이면 크롭 또는 블러",
                "하센 자막은 안전영역 기준으로 중앙 하단 배치",
                "최종 업로드 전 릴스/쇼츠 UI에서 자막 가림 확인",
            ],
        }

    def empty(self, message):
        return {
            "ok": False,
            "error": message,
            "subtitle_risk": {},
            "watermark_risk": {},
            "best_hook_frame": {},
            "best_thumbnail_frame": {},
            "scene_change_count": 0,
            "capcut_actions": [],
            "shopping_shorts_timeline": [],
            "edit_summary": "영상 분석 데이터가 필요합니다.",
            "next_step": [],
        }

    def subtitle_risk(self, width, height):
        # 실제 OCR 전까지는 쇼핑 영상에서 흔한 하단/상단 자막 위험을 기준으로 가이드 제공
        return {
            "bottom_caption_probability": "높음",
            "top_caption_probability": "중간",
            "recommended_subtitle_position": "하단 자막이 있으면 45~50%, 없으면 하단 40%",
            "capcut_note": "CapCut에서 중국어 자막이 하단에 보이면 하센 자막을 조금 위로 올리세요.",
        }

    def watermark_risk(self, width, height):
        return {
            "right_side_logo_probability": "중간",
            "bottom_corner_logo_probability": "중간",
            "crop_recommendation": "가장자리 워터마크는 105~115% 확대 크롭 우선 검토",
            "blur_recommendation": "상품을 가리지 않는 로고만 블러 처리",
        }

    def capcut_actions(self, subtitle_risk, watermark_risk):
        return [
            {
                "action": "자막 위치",
                "value": subtitle_risk.get("recommended_subtitle_position"),
                "reason": "타오바오/도우인 영상은 하단 중국어 자막 가능성이 높음",
            },
            {
                "action": "크롭",
                "value": watermark_risk.get("crop_recommendation"),
                "reason": "워터마크가 가장자리에 있을 가능성",
            },
            {
                "action": "블러",
                "value": watermark_risk.get("blur_recommendation"),
                "reason": "로고/워터마크가 남아 있을 경우",
            },
            {
                "action": "BGM",
                "value": "8 dB",
                "reason": "정보형 쇼핑쇼츠 기본값",
            },
            {
                "action": "AI 음성",
                "value": "20 dB",
                "reason": "CapCut 최대 볼륨 기준",
            },
        ]

    def shopping_timeline(self, ai_result, best_hook):
        duration = ai_result.get("duration", 20) or 20
        hook_time = best_hook.get("time", 0)
        return [
            {
                "time": "0~2초",
                "role": "후킹",
                "guide": f"{hook_time}초 근처 추천 프레임을 첫 장면으로 사용",
                "capcut": "Zoom In + Bounce 자막",
            },
            {
                "time": "2~5초",
                "role": "문제 공감",
                "guide": "불편한 상황 또는 사용 전 장면",
                "capcut": "자막 1줄, BGM 8 dB",
            },
            {
                "time": "5~12초",
                "role": "제품 사용",
                "guide": "제품이 가장 잘 보이는 장면 연결",
                "capcut": "Click 8 dB / Pop 7 dB",
            },
            {
                "time": "12~17초",
                "role": "효과/장점",
                "guide": "Before/After 또는 핵심 장점",
                "capcut": "Slide Up 자막",
            },
            {
                "time": "17~20초",
                "role": "CTA",
                "guide": "댓글 키워드 + 링크 안내",
                "capcut": "Pop 7 dB + CTA 강조",
            },
        ]

    def summary(self, subtitle_risk, watermark_risk, best_hook):
        time = best_hook.get("time", "-")
        return (
            f"추천 후킹 프레임은 {time}초 부근입니다. "
            "하단 중국어 자막 가능성이 있으므로 하센 자막은 45~50% 위치를 우선 검토하세요. "
            "워터마크가 가장자리에 있으면 105~115% 확대 크롭을 먼저 적용하는 것이 좋습니다."
        )
