def generate_hooks(product_name="", profile=None):
    """
    Sprint 18-1
    콘텐츠 유형별 쇼핑쇼츠 후킹 생성기.
    """
    profile = profile or {}

    keyword = profile.get("keyword", "제품")
    problem = profile.get("problem", "매번 불편했던 순간")
    benefit = profile.get("benefit", "생활이 조금 더 편해집니다")
    features = profile.get("features") or ["간편함", "생활 편의"]

    main_feature = features[0] if features else "간편함"

    return {
        "공감형": [
            f"저도 {product_name} 때문에 스트레스였어요.",
            "이거 은근히 매번 불편하지 않나요?",
            f"{benefit}",
            f"댓글에 '{keyword}' 남겨주세요 👇",
            "왜 이제 알았지?",
        ],
        "정보형": [
            f"{product_name}, 이런 분께 추천합니다.",
            f"핵심은 {main_feature}입니다.",
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
        "BeforeAfter형": [
            "Before",
            f"{problem}",
            "After",
            f"{main_feature} 하나로 훨씬 편해졌습니다.",
            "차이가 바로 보입니다.",
        ],
        "리뷰형": [
            "왜 후기가 많은지 알겠더라고요.",
            "직접 써보니 생각보다 훨씬 편했습니다.",
            "매일 쓰는 제품일수록 차이가 큽니다.",
            f"특히 {main_feature}이 마음에 들었습니다.",
            "이건 진짜 추천할 만합니다.",
        ],
    }