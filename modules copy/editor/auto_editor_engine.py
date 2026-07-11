class AutoEditorEngine:
    def create_plan(self, product_name, keyword, smart_cut=None, vision=None, shorts=None, candidate_selection=None):
        vision = vision or {}
        smart_cut = smart_cut or vision.get("auto_editor") or vision.get("smart_cut") or {}
        shorts = shorts or {}
        candidate_selection = candidate_selection or {}

        guide = vision.get("guide", {})
        subtitle = guide.get("subtitle_position", "중앙 하단 / 하단 40%")
        crop = guide.get("crop", "9:16 유지")
        blur = guide.get("blur", "필요 시 수동 확인")

        base_timeline = (
            smart_cut.get("timeline")
            or shorts.get("capcut_timeline")
            or self.ai_mix_timeline(product_name, keyword, candidate_selection)
            or self.default_timeline(product_name, keyword)
        )

        timeline = self.merge_ai_candidate_info(base_timeline, candidate_selection)

        return {
            "summary": f"{product_name} 영상은 20초 쇼핑쇼츠 기준으로 편집합니다. 자막은 {subtitle}, 크롭은 {crop}를 우선 적용하세요.",
            "capcut_preset": {
                "ratio": "9:16",
                "voice": "20 dB",
                "bgm": "8 dB",
                "pop": "7 dB",
                "click": "8 dB",
                "whoosh": "6 dB",
                "font": "Pretendard 또는 기본 고딕",
                "font_size": "46",
                "stroke": "6",
                "shadow": "60%",
                "subtitle_position": subtitle,
                "crop": crop,
                "blur": blur,
            },
            "timeline": timeline,
            "export_checklist": [
                "9:16 비율 확인",
                "중국어 자막/워터마크 가림 확인",
                "하센 자막이 쇼츠/릴스 UI에 가리지 않는지 확인",
                "AI 음성 20 dB",
                "BGM 8 dB",
                "효과음 Pop 7 dB / Click 8 dB / Whoosh 6 dB",
                "쿠팡파트너스 고지 문구 확인",
                "최종 영상 저장",
            ],
        }

    def merge_ai_candidate_info(self, timeline, candidate_selection):
        best = candidate_selection.get("best") or {}
        top3 = candidate_selection.get("top3") or []

        if not timeline:
            return []

        enriched = []

        for index, cut in enumerate(timeline):
            new_cut = dict(cut)

            candidate = top3[index] if index < len(top3) else best

            if candidate:
                new_cut["candidate_title"] = candidate.get("title", "")
                new_cut["candidate_platform"] = candidate.get("platform", "")
                new_cut["ai_score"] = candidate.get("ai_score")
                new_cut["final_ai_score"] = candidate.get("final_ai_score", candidate.get("ai_score"))
                new_cut["ai_recommendation"] = candidate.get("ai_recommendation", "")
                new_cut["ai_reasons"] = candidate.get("ai_reasons", [])

            enriched.append(new_cut)

        return enriched

    def ai_mix_timeline(self, product_name, keyword, candidate_selection):
        top3 = candidate_selection.get("top3", [])

        if not top3:
            return []

        hook = top3[0] if len(top3) >= 1 else {}
        demo = top3[1] if len(top3) >= 2 else hook
        cta = top3[2] if len(top3) >= 3 else demo

        return [
            {
                "time": "0~2초",
                "role": "후킹",
                "caption": "왜 이제 알았지?",
                "source": hook.get("title", ""),
                "ai_score": hook.get("ai_score"),
                "capcut": "Zoom In / Pop 7 dB",
            },
            {
                "time": "2~5초",
                "role": "공감",
                "caption": f"저도 {product_name} 때문에 스트레스였어요",
                "source": hook.get("title", ""),
                "ai_score": hook.get("ai_score"),
                "capcut": "BGM 8 dB",
            },
            {
                "time": "5~10초",
                "role": "사용",
                "caption": "이렇게 쓰면 훨씬 편해요",
                "source": demo.get("title", ""),
                "ai_score": demo.get("ai_score"),
                "capcut": "Click 8 dB",
            },
            {
                "time": "10~15초",
                "role": "효과",
                "caption": "작지만 체감은 큽니다",
                "source": demo.get("title", ""),
                "ai_score": demo.get("ai_score"),
                "capcut": "Whoosh 6 dB",
            },
            {
                "time": "15~20초",
                "role": "CTA",
                "caption": f"댓글에 '{keyword}' 남겨주세요 👇",
                "source": cta.get("title", ""),
                "ai_score": cta.get("ai_score"),
                "capcut": "Bounce / Pop 7 dB",
            },
        ]

    def default_timeline(self, product_name, keyword):
        return [
            {"time": "0~2초", "role": "후킹", "caption": "왜 이제 알았지?", "capcut": "Zoom In / Pop 7 dB"},
            {"time": "2~5초", "role": "공감", "caption": f"저도 {product_name} 때문에 스트레스였어요", "capcut": "BGM 8 dB"},
            {"time": "5~10초", "role": "사용", "caption": "이렇게 쓰면 훨씬 편해요", "capcut": "Click 8 dB"},
            {"time": "10~15초", "role": "효과", "caption": "작지만 체감은 큽니다", "capcut": "Whoosh 6 dB"},
            {"time": "15~20초", "role": "CTA", "caption": f"댓글에 '{keyword}' 남겨주세요 👇", "capcut": "Bounce / Pop 7 dB"},
        ]