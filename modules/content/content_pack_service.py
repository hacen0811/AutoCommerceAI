from app.ui.product_analyzer import analyze_product
from app.ui.hook_generator import generate_hooks
from app.ui.content_variant_generator import generate_content_variants
from app.ui.content_ranker import rank_content_variants


def normalize_text(value, default=""):
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def build_hooks(product_name, profile):
    keyword = profile.get("keyword", "제품")

    return [
        f"{product_name}, 왜 이제 알았지?",
        f"아직도 불편하게 쓰고 계세요?",
        f"이거 하나로 생활이 조금 편해집니다.",
        f"매일 쓰는 {keyword}, 작은 차이가 큽니다.",
    ]


def build_script(product_name, profile):
    keyword = profile.get("keyword", "제품")

    return [
        f"아직도 {keyword} 때문에 불편하셨다면",
        f"오늘은 {product_name}을 소개할게요.",
        "매일 쓰는 제품일수록 작은 차이가 크게 느껴집니다.",
        "사용하기 쉽고, 정리도 편해서 생활이 조금 더 편해집니다.",
        f"제품 정보가 궁금하시면 댓글에 '{keyword}' 남겨주세요 👇",
    ]


def build_capcut_timeline(product_name, hooks, profile):
    keyword = profile.get("keyword", "제품")
    main_hook = hooks[0] if hooks else f"{product_name}, 왜 이제 알았지?"

    return [
        {
            "scene": 1,
            "time": "0~3초",
            "role": "후킹",
            "text": main_hook,
            "edit": "큰 자막 + 빠른 줌인 + Pop 효과음",
        },
        {
            "scene": 2,
            "time": "3~10초",
            "role": "문제 공감",
            "text": f"아직도 {keyword} 때문에 불편하셨다면",
            "edit": "불편한 장면 짧게 컷 분리",
        },
        {
            "scene": 3,
            "time": "10~20초",
            "role": "제품 등장",
            "text": f"{product_name} 등장",
            "edit": "제품 클로즈업 + 밝은 전환",
        },
        {
            "scene": 4,
            "time": "20~38초",
            "role": "장점 설명",
            "text": "편해지는 포인트를 2~3개로 나눠 보여주세요.",
            "edit": "장점마다 노란색 강조 자막",
        },
        {
            "scene": 5,
            "time": "마지막 3~5초",
            "role": "CTA",
            "text": f"댓글에 '{keyword}' 남겨주세요 👇",
            "edit": "댓글 키워드 + 링크 안내",
        },
    ]


def build_ai_content_pack(project, selected_sources, latest_result=None):
    """
    Sprint 28 content pack service.
    기존 AI 생성 흐름을 content_pack_service.py로 분리합니다.
    """

    latest_result = latest_result or {}
    selected_sources = [s for s in (selected_sources or []) if isinstance(s, dict)]
    primary = selected_sources[0] if selected_sources else {}

    project_name = normalize_text(
        getattr(project, "product_name", "") or getattr(project, "title", ""),
        "선택 상품",
    )

    source_query = normalize_text(
        primary.get("query") or primary.get("title") or project_name,
        project_name,
    )

    content_product_name = project_name
    source_url = normalize_text(primary.get("url"), "")
    platform = normalize_text(primary.get("platform"), "source")

    profile = analyze_product(content_product_name, source_query)
    hook_groups = generate_hooks(content_product_name, profile)

    hooks = build_hooks(content_product_name, profile)
    script = build_script(content_product_name, profile)
    capcut_timeline = build_capcut_timeline(content_product_name, hooks, profile)

    shorts_variants = generate_content_variants(
        content_product_name,
        profile,
        hook_groups,
    )

    shorts_variants = rank_content_variants(
        profile,
        shorts_variants,
    )

    selected_variant = None
    if shorts_variants:
        selected_variant = next(
            (v for v in shorts_variants if v.get("recommended")),
            shorts_variants[0],
        )

    active_content = selected_variant or {
        "title": f"{content_product_name}, 왜 이제 알았지?",
        "hook": hooks[0] if hooks else "왜 이제 알았지?",
        "script": script,
        "cta": f"댓글에 '{profile.get('keyword', '제품')}' 남겨주세요 👇",
        "capcut": capcut_timeline,
    }

    pack = {
        "version": "sprint-28-content-pack-service",
        "project_id": getattr(project, "id", ""),
        "project_name": content_product_name,
        "primary_source": primary,
        "selected_sources": selected_sources,
        "selected_variant": active_content,
        "content_strategy": {
            "main_angle": "실전 쇼핑쇼츠 문제 해결형",
            "structure": "Hook → Problem → Solution → Benefit → CTA",
            "target": "생활 속 불편을 빠르게 해결하고 싶은 사용자",
            "selling_points": profile.get("features", []),
            "recommended_format": "40~50초 쇼츠 / 릴스",
        },
        "shorts": {
            "titles": [
                f"{content_product_name}, 왜 이제 알았지?",
                f"불편함 줄여주는 {content_product_name}",
                f"생활이 편해지는 추천템 {content_product_name}",
            ],
            "thumbnail_phrases": [
                "왜 이제 알았지?",
                "이거 하나로 끝",
                "생활이 편해집니다",
            ],
            "hooks": hooks,
            "hook_groups": hook_groups,
            "script": script,
            "cta": f"댓글에 '{profile.get('keyword', '제품')}' 남겨주세요 👇",
            "capcut_timeline": capcut_timeline,
        },
        "shorts_variants": shorts_variants,
        "thumbnail": {
            "size": "9:16",
            "main_text": active_content.get("hook", "왜 이제 알았지?"),
            "sub_text": content_product_name,
            "layout": "제품 크게 + 왼쪽 상단 후킹 문구 + 하단 짧은 설명",
            "image_prompt": f"9:16 vertical shopping shorts thumbnail, clean Korean ecommerce style, product concept: {content_product_name}, bright home background, large bold Korean text area, realistic product-focused composition",
        },
        "inpock": {
            "size": "1000x1000",
            "title": content_product_name,
            "main_text": active_content.get("hook", "생활이 편해지는 추천템"),
            "sub_text": "제품 정보는 링크에서 확인",
            "image_prompt": f"1000x1000 square product promo image for Inpock link page, clean Korean shopping design, product concept: {content_product_name}, white background, neat layout, space for Korean title text",
        },
        "upload_bundle": {
            "youtube_title": active_content.get(
                "title",
                f"{content_product_name} 추천템 #shorts",
            ),
            "youtube_desc": "🔗 제품 정보는 영상 아래 설명란 링크 또는 프로필 링크를 확인해주세요.\n\n쿠팡파트너스 활동을 통해 일정액의 수수료를 제공받을 수 있습니다.",
            "instagram_body": f"왜 이제 알았지 싶은 생활템 ✨\n\n{content_product_name}처럼 매일 쓰는 제품은 작은 차이가 크게 느껴지더라고요.\n\n제품 정보가 궁금하시면 댓글에 '{profile.get('keyword', '제품')}' 남겨주세요 👇",
            "hashtags": [
                "#쇼핑쇼츠",
                "#생활용품추천",
                "#살림템",
                "#쿠팡추천",
                "#shorts",
                "#릴스",
            ],
            "source_url": source_url,
            "platform": platform,
        },
    }

    return pack