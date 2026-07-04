def generate_content_variants(product_name="", profile=None, hook_groups=None):
    """
    Sprint 18-2
    콘텐츠 유형별 쇼츠 패키지 생성기.
    기존 shorts 구조는 유지하고 shorts_variants에 추가하기 위한 데이터 생성.
    """
    profile = profile or {}
    hook_groups = hook_groups or {}

    keyword = profile.get("keyword", "제품")
    problem = profile.get("problem", "매번 불편했던 순간")
    solution = profile.get("solution", "생활 속 불편을 줄여주는 아이템")
    benefit = profile.get("benefit", "생활이 조금 더 편해집니다")
    features = profile.get("features") or ["간편함", "생활 편의"]
    main_feature = features[0] if features else "간편함"

    def first_hook(type_name, fallback):
        hooks = hook_groups.get(type_name) or []
        return hooks[0] if hooks else fallback

    return [
        {
            "type": "공감형",
            "title": f"저도 {product_name} 때문에 불편했어요",
            "hook": first_hook("공감형", f"저도 {product_name} 때문에 스트레스였어요."),
            "script": "\n".join([
                f"[Hook] 저도 {product_name} 때문에 스트레스였어요.",
                f"[Problem] {problem}",
                "[Problem] 그냥 참고 쓰기엔 매번 반복되는 불편함이 있었습니다.",
                f"[Solution] 그래서 찾은 게 바로 {product_name}입니다.",
                f"[Benefit] {benefit}",
                f"[CTA] 댓글에 '{keyword}' 남겨주세요 👇",
            ]),
            "cta": f"댓글에 '{keyword}' 남겨주세요 👇",
            "capcut": [
                "0-3초 / 불편한 상황 클로즈업 / 공감 자막 크게",
                "3-7초 / 반복되는 불편함 보여주기 / 답답한 효과음",
                "7-13초 / 제품 등장 / 밝기 상승 + Pop",
                "13-25초 / 사용 장면 / 핵심 기능 자막",
                "25-35초 / 사용 후 변화 / Before After",
                "35-45초 / CTA / 댓글 유도",
            ],
        },
        {
            "type": "정보형",
            "title": f"{product_name}, 이런 분께 추천합니다",
            "hook": first_hook("정보형", f"{product_name}, 이런 분께 추천합니다."),
            "script": "\n".join([
                f"[Hook] {product_name}, 이런 분께 추천합니다.",
                f"[Info] {problem}",
                f"[Info] 핵심은 {main_feature}입니다.",
                f"[Solution] {solution}",
                f"[Benefit] {benefit}",
                "[CTA] 제품 정보는 프로필 링크에서 확인하세요.",
            ]),
            "cta": "제품 정보는 프로필 링크에서 확인하세요.",
            "capcut": [
                "0-3초 / 제품명 + 추천 대상 / 정보형 자막",
                "3-8초 / 문제 상황 설명 / 차분한 BGM",
                "8-16초 / 핵심 기능 1,2,3 / 체크 효과음",
                "16-28초 / 사용 장면 / 설명 자막",
                "28-38초 / 추천 대상 정리 / 리스트 자막",
                "38-45초 / 프로필 링크 CTA",
            ],
        },
        {
            "type": "충격형",
            "title": f"이걸 몰라서 계속 불편했던 거였어요",
            "hook": first_hook("충격형", "90%가 모르고 지나칩니다."),
            "script": "\n".join([
                "[Hook] 90%가 모르고 지나칩니다.",
                f"[Problem] {problem}",
                "[Twist] 이걸 몰라서 계속 불편했던 거였어요.",
                f"[Solution] 핵심은 {main_feature}입니다.",
                f"[Benefit] {benefit}",
                f"[CTA] 댓글에 '{keyword}' 남겨주세요 👇",
            ]),
            "cta": f"댓글에 '{keyword}' 남겨주세요 👇",
            "capcut": [
                "0-2초 / 강한 숫자 자막 / Hit 효과음",
                "2-6초 / 불편한 장면 빠른 컷 / 긴장감",
                "6-12초 / 반전 문구 / 줌인",
                "12-24초 / 제품 해결 장면 / 속도감",
                "24-36초 / Before After / 효과음 강조",
                "36-45초 / CTA / 댓글 유도",
            ],
        },
        {
            "type": "BeforeAfter형",
            "title": f"{product_name} 사용 전후 차이",
            "hook": first_hook("BeforeAfter형", "Before / After로 보면 더 확실합니다."),
            "script": "\n".join([
                "[Hook] Before / After로 보면 더 확실합니다.",
                f"[Before] {problem}",
                f"[After] {solution}",
                f"[Benefit] {benefit}",
                "[Compare] 차이가 바로 보입니다.",
                f"[CTA] 댓글에 '{keyword}' 남겨주세요 👇",
            ]),
            "cta": f"댓글에 '{keyword}' 남겨주세요 👇",
            "capcut": [
                "0-3초 / Before 화면 / 어두운 톤",
                "3-8초 / 불편한 장면 / 느린 컷",
                "8-15초 / 제품 사용 / 전환 효과",
                "15-28초 / After 화면 / 밝은 톤",
                "28-38초 / 좌우 비교 / Before After 텍스트",
                "38-45초 / CTA / 댓글 유도",
            ],
        },
        {
            "type": "리뷰형",
            "title": f"왜 후기가 많은지 알겠더라고요",
            "hook": first_hook("리뷰형", "왜 후기가 많은지 알겠더라고요."),
            "script": "\n".join([
                "[Hook] 왜 후기가 많은지 알겠더라고요.",
                f"[Review] 처음엔 {product_name}이 그렇게 다를까 싶었습니다.",
                f"[Use] 그런데 직접 써보니 {main_feature}이 체감됐어요.",
                f"[Benefit] {benefit}",
                "[Review] 매일 쓰는 제품일수록 차이가 큽니다.",
                f"[CTA] 댓글에 '{keyword}' 남겨주세요 👇",
            ]),
            "cta": f"댓글에 '{keyword}' 남겨주세요 👇",
            "capcut": [
                "0-3초 / 리뷰형 첫 문장 / 말풍선 자막",
                "3-8초 / 사용 전 의심 / 작게 흔들림 효과",
                "8-18초 / 실제 사용 장면 / 자연스러운 컷",
                "18-30초 / 마음에 든 포인트 / 체크 자막",
                "30-38초 / 추천 이유 정리 / 안정적인 BGM",
                "38-45초 / CTA / 댓글 유도",
            ],
        },
    ]