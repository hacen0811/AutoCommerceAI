class HookSelector:
    def select(self, product_name, keyword="정보", smart_cut=None, ocr_result=None):
        smart_cut = smart_cut or {}
        ocr_result = ocr_result or {}

        subtitle_position = ocr_result.get("recommendation", {}).get("subtitle_position", "중앙 하단 / 하단 40%")
        hook_cut = smart_cut.get("hook_cut", {})
        hook_time = hook_cut.get("time", "0")

        hooks = [
            {
                "hook": "왜 이제 알았지?",
                "type": "궁금증형",
                "score": 96,
                "reason": f"{hook_time}초 추천 프레임과 함께 쓰기 좋은 짧은 후킹",
            },
            {
                "hook": f"저도 {product_name} 때문에 스트레스였어요.",
                "type": "공감형",
                "score": 94,
                "reason": "생활 불편 해결형 상품에 적합",
            },
            {
                "hook": "90%가 모르고 지나칩니다.",
                "type": "충격형",
                "score": 90,
                "reason": "썸네일과 첫 장면 임팩트가 있을 때 적합",
            },
            {
                "hook": "생활이 조금 쉬워졌어요.",
                "type": "공감형",
                "score": 88,
                "reason": "하센 스타일과 자연스럽게 맞음",
            },
            {
                "hook": f"댓글에 '{keyword}' 남겨주세요 👇",
                "type": "CTA",
                "score": 82,
                "reason": "댓글 유도용 후반부 문구",
            },
        ]

        return {
            "recommended": hooks[0],
            "hooks": hooks,
            "subtitle_position": subtitle_position,
            "guide": f"자막 위치는 {subtitle_position} 기준으로 배치하세요.",
        }
