class ShoppingShortsEngine:
    """
    영상 분석 + 상품정보 + 하센 CapCut 기준을 합쳐
    쇼핑쇼츠 제작 패키지를 생성합니다.
    """

    def generate(self, product_name, keyword="정보", video_intel=None, ocr_result=None):
        video_intel = video_intel or {}
        ocr_result = ocr_result or {}

        hook_frame = video_intel.get("best_hook_frame", {})
        hook_time = hook_frame.get("time", "0")

        subtitle_position = (
            ocr_result.get("recommendation", {}).get("subtitle_position")
            or "중앙 하단 / 하단 40%"
        )
        crop = ocr_result.get("recommendation", {}).get("crop") or "9:16 유지"

        strategy = self._strategy(product_name, keyword, subtitle_position, crop, hook_time)

        return {
            "strategy": strategy,
            "hooks": self._hooks(product_name, keyword),
            "scripts": self._scripts(product_name, keyword, hook_time),
            "thumbnail": self._thumbnail(product_name),
            "platform_copy": self._platform_copy(product_name, keyword),
            "capcut_timeline": self._capcut_timeline(product_name, keyword, subtitle_position, crop, hook_time),
            "upload_check": [
                "쿠팡파트너스 링크 확인",
                "인포크 링크 등록",
                "유튜브 설명란 링크 확인",
                "인스타 프로필 링크 확인",
                "쿠팡파트너스 고지 문구 확인",
                "자막 가림 최종 확인",
            ],
        }

    def _strategy(self, product_name, keyword, subtitle_position, crop, hook_time):
        return {
            "recommended_type": "공감형 + 정보형",
            "reason": f"{product_name}은 생활 불편 해결형 상품이므로 공감형 후킹 후 사용 장면을 보여주는 구조가 적합합니다.",
            "hook_frame": f"{hook_time}초 부근 장면을 첫 컷 후보로 사용",
            "subtitle_position": subtitle_position,
            "crop": crop,
            "audio": {
                "voice": "20 dB",
                "bgm": "8 dB",
                "pop": "7 dB",
                "click": "8 dB",
                "whoosh": "6 dB",
            },
            "cta": f"댓글에 '{keyword}' 남겨주세요 👇",
        }

    def _hooks(self, product_name, keyword):
        return {
            "공감형": [
                f"저도 {product_name} 때문에 스트레스였어요.",
                "이거 은근히 매번 불편하지 않나요?",
                "생활이 조금 쉬워졌어요.",
                f"댓글에 '{keyword}' 남겨주세요 👇",
                "왜 이제 알았지?",
            ],
            "정보형": [
                f"{product_name}, 이런 분께 추천합니다.",
                "핵심은 간편함입니다.",
                "설치보다 중요한 건 사용 후 체감입니다.",
                "작아 보여도 차이가 큽니다.",
                "제품 정보는 프로필 링크에서 확인하세요.",
            ],
            "충격형": [
                "90%가 모르고 지나칩니다.",
                "이걸 몰라서 계속 불편했던 거였어요.",
                "작지만 체감은 큽니다.",
                "한 번 쓰면 다시 예전으로 못 돌아갑니다.",
                "후기가 많은 이유가 있었습니다.",
            ],
        }

    def _scripts(self, product_name, keyword, hook_time):
        return {
            "20초 쇼츠": [
                f"0~2초: {hook_time}초 부근 추천 장면 + '왜 이제 알았지?'",
                f"2~5초: {product_name} 사용 전 불편함",
                "5~10초: 제품 사용 장면",
                "10~15초: 달라진 점 / Before After",
                f"15~20초: 댓글에 '{keyword}' 남겨주세요 👇",
            ],
            "35초 릴스": [
                "0~3초: 공감형 후킹",
                "3~8초: 기존 불편함",
                f"8~15초: {product_name} 사용 장면",
                "15~25초: 장점 2~3개",
                "25~31초: 실제 사용 후 체감",
                f"31~35초: 댓글에 '{keyword}' 남겨주세요 👇",
            ],
        }

    def _thumbnail(self, product_name):
        return [
            "왜 이제 알았지?",
            "90%가 모르는 꿀템",
            "생활이 편해졌어요",
            "이거 진짜 편합니다",
            product_name,
        ]

    def _platform_copy(self, product_name, keyword):
        return {
            "유튜브 제목": f"{product_name}, 왜 이제 알았을까요?",
            "유튜브 설명": "🔗 제품 정보는 영상 아래 설명란 링크 또는 프로필 링크를 확인해주세요.\n\n※ 쿠팡파트너스 활동의 일환으로 일정액의 수수료를 받을 수 있습니다.",
            "유튜브 쇼츠 설명": "🔗 제품 정보는 영상 아래 설명란 링크 또는 프로필 링크를 확인해주세요.",
            "인스타 본문": f"저도 {product_name} 때문에 불편했어요.\n\n생활이 조금 쉬워지는 추천템입니다.\n\n팔로우 하시고 댓글에 '{keyword}' 남겨주세요 👇",
            "고정 댓글": f"댓글에 '{keyword}' 남겨주세요 👇",
            "인포크 설명": f"생활이 조금 쉬워지는 {product_name}\n댓글에 '{keyword}' 남겨주세요 👇",
        }

    def _capcut_timeline(self, product_name, keyword, subtitle_position, crop, hook_time):
        return [
            {
                "time": "0~2초",
                "scene": f"{hook_time}초 추천 프레임",
                "caption": "왜 이제 알았지?",
                "capcut": f"Zoom In / 자막 {subtitle_position} / Pop 7 dB",
            },
            {
                "time": "2~5초",
                "scene": "불편함 장면",
                "caption": "저도 이거 때문에 스트레스였어요",
                "capcut": f"{crop} / BGM 8 dB",
            },
            {
                "time": "5~10초",
                "scene": "제품 사용 장면",
                "caption": "이렇게 쓰면 훨씬 편해요",
                "capcut": "Click 8 dB / 자막 2줄 이하",
            },
            {
                "time": "10~15초",
                "scene": "Before / After",
                "caption": "작지만 체감은 큽니다",
                "capcut": "Slide Up / Whoosh 6 dB",
            },
            {
                "time": "15~20초",
                "scene": "CTA",
                "caption": f"댓글에 '{keyword}' 남겨주세요 👇",
                "capcut": "Bounce / Pop 7 dB",
            },
        ]
