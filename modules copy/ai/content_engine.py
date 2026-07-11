class AIContentEngine:
    def generate(self, product_name, keyword="정보"):
        hooks = [
            f"저도 {product_name} 때문에 고민했어요.",
            "왜 이제 알았지?",
            "90%가 모르고 지나칩니다.",
            f"댓글에 '{keyword}' 남겨주세요 👇",
            "생활이 조금 쉬워졌어요.",
        ]

        scripts = {
            "20초 쇼츠": [
                f"0~3초: {hooks[0]}",
                "3~7초: 기존 불편함 보여주기",
                f"7~13초: {product_name} 사용 장면",
                "13~17초: Before / After",
                f"17~20초: 댓글에 '{keyword}' 남겨주세요 👇",
            ],
            "35초 릴스": [
                f"0~3초: {hooks[1]}",
                "3~8초: 문제 상황",
                "8~15초: 제품 등장",
                "15~25초: 사용 장면",
                "25~31초: 장점 정리",
                f"31~35초: 댓글에 '{keyword}' 남겨주세요 👇",
            ],
        }

        return {
            "score": 88,
            "hooks": hooks,
            "scripts": scripts,
            "thumbnails": ["왜 이제 알았지?", "생활이 편해졌어요", "90%가 모르는 꿀템"],
            "youtube_title": f"{product_name}, 왜 이제 알았을까요?",
            "youtube_desc": "🔗 제품 정보는 영상 아래 설명란 링크 또는 프로필 링크를 확인해주세요.",
            "instagram_body": f"{hooks[0]}\n\n팔로우 하시고 댓글에 '{keyword}' 남겨주세요 👇",
        }
