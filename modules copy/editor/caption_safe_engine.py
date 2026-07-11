class CaptionSafeEngine:
    def build(self, vision_result=None, ocr_result=None):
        vision_result = vision_result or {}
        ocr_result = ocr_result or {}

        guide = vision_result.get("guide") or ocr_result.get("recommendation") or {}
        subtitle = guide.get("subtitle_position", "중앙 하단 / 하단 40%")
        crop = guide.get("crop", "9:16 유지")
        blur = guide.get("blur", "필요 시 수동 확인")

        danger_zones = []

        risk = vision_result.get("risk") or ocr_result.get("risk") or {}
        for key, val in risk.items():
            level = val.get("level") if isinstance(val, dict) else ""
            if level in ["높음", "중간"]:
                danger_zones.append({"zone": key, "level": level})

        return {
            "safe_subtitle_position": subtitle,
            "crop": crop,
            "blur": blur,
            "danger_zones": danger_zones,
            "capcut_rule": [
                f"하센 자막 위치: {subtitle}",
                f"크롭: {crop}",
                f"블러: {blur}",
                "자막은 2줄 이하",
                "영상 하단 UI 가림을 피하기 위해 최종 미리보기 확인",
            ],
            "audio_rule": {
                "voice": "20 dB",
                "bgm": "8 dB",
                "pop": "7 dB",
                "click": "8 dB",
                "whoosh": "6 dB",
            },
        }
