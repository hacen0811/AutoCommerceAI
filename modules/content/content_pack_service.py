import streamlit as st

from modules.content.product_analyzer import analyze_product
from modules.content.hook_generator import generate_hooks
from modules.content.content_variant_generator import generate_content_variants
from modules.content.content_ranker import rank_content_variants


def normalize_text(value, default=""):
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def first_value(*values, default=""):
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, (int, float)):
            return str(value)
    return default


def project_value(project, names, default=""):
    for name in names:
        if isinstance(project, dict):
            value = project.get(name)
        else:
            value = getattr(project, name, None)

        if value:
            return value

    return default


def get_source_value(source, names, default=""):
    if not isinstance(source, dict):
        return default

    for name in names:
        value = source.get(name)
        if value:
            return value

    return default


def build_hooks(product_name, profile):
    keyword = profile.get("keyword", "제품")

    return [
        f"{product_name}, 왜 이제 알았지?",
        f"아직도 {keyword} 때문에 불편하셨나요?",
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


def build_captions(product_name, profile):
    keyword = profile.get("keyword", "제품")

    return [
        f"{product_name}, 왜 이제 알았지?",
        f"아직도 {keyword} 때문에 불편하셨다면",
        "생활 속 작은 불편함을 줄여줍니다.",
        "매일 쓰는 제품일수록 차이가 느껴집니다.",
        f"댓글에 '{keyword}' 남겨주세요 👇",
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


def normalize_selected_sources(selected_sources):
    normalized = []

    for index, source in enumerate(selected_sources or [], start=1):
        if not isinstance(source, dict):
            continue

        query = first_value(
            source.get("query"),
            source.get("keyword"),
            source.get("search_query"),
            source.get("title"),
            default="",
        )

        url = first_value(
            source.get("url"),
            source.get("search_url"),
            source.get("video_url"),
            source.get("play_url"),
            default="",
        )

        normalized.append(
            {
                **source,
                "rank": source.get("rank", index),
                "platform": first_value(source.get("platform"), default="source"),
                "query": query,
                "keyword": query,
                "url": url,
                "search_url": first_value(source.get("search_url"), url, default=""),
                "video_url": first_value(source.get("video_url"), url, default=""),
                "title": first_value(source.get("title"), query, default=f"후보 {index}"),
                "score": source.get("score", 0),
                "reason": source.get("reason", source.get("purpose", "")),
                "video_path": source.get("video_path", ""),
                "image_url": source.get("image_url", ""),
                "image_path": source.get("image_path", ""),
            }
        )

    return normalized


def build_ai_content_pack(project, selected_sources, latest_result=None):
    """
    Sprint 51 content pack service.

    역할:
    후보 채택 데이터(selected_sources)를 기반으로 AI 콘텐츠 팩을 생성합니다.
    이후 ContentFactory.apply_edit_assistant()에서 CutPlanner,
    CapCut Export, CapCut Draft가 연결됩니다.
    """

    latest_result = latest_result or {}
    outputs = latest_result.get("outputs", {}) if isinstance(latest_result, dict) else {}

    selected_sources = normalize_selected_sources(selected_sources)
    primary = selected_sources[0] if selected_sources else {}

    project_name = normalize_text(
        project_value(project, ["product_name", "title", "name"], ""),
        "선택 상품",
    )

    partner_url = normalize_text(
        project_value(project, ["partner_url", "coupang_partner_url"], ""),
        "",
    )

    source_query = normalize_text(
        get_source_value(primary, ["query", "keyword", "title"], project_name),
        project_name,
    )

    source_url = normalize_text(
        get_source_value(primary, ["video_url", "url", "search_url"], ""),
        "",
    )

    platform = normalize_text(
        get_source_value(primary, ["platform"], "source"),
        "source",
    )

    profile = analyze_product(project_name, source_query)
    keyword = normalize_text(profile.get("keyword"), source_query)

    hook_groups = generate_hooks(project_name, profile)
    hooks = build_hooks(project_name, profile)
    script = build_script(project_name, profile)
    captions = build_captions(project_name, profile)
    capcut_timeline = build_capcut_timeline(project_name, hooks, profile)

    shorts_variants = generate_content_variants(
        project_name,
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
        "title": f"{project_name}, 왜 이제 알았지?",
        "hook": hooks[0] if hooks else "왜 이제 알았지?",
        "script": script,
        "cta": f"댓글에 '{keyword}' 남겨주세요 👇",
        "capcut": capcut_timeline,
    }

    active_script = active_content.get("script") or script
    if isinstance(active_script, str):
        active_script = [active_script]

    active_hook = active_content.get("hook") or hooks[0]

    pack = {
        "version": "sprint-51-content-pack-service",
        "project_id": project_value(project, ["id", "project_id"], ""),
        "project_name": project_name,
        "product_name": project_name,
        "keyword": keyword,
        "primary_source": primary,
        "selected_sources": selected_sources,
        "source_debug": {
            "source_query": source_query,
            "source_url": source_url,
            "platform": platform,
            "selected_count": len(selected_sources),
        },
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
                active_content.get("title", f"{project_name}, 왜 이제 알았지?"),
                f"불편함 줄여주는 {project_name}",
                f"생활이 편해지는 추천템 {project_name}",
            ],
            "thumbnail_phrases": [
                "왜 이제 알았지?",
                "이거 하나로 끝",
                "생활이 편해집니다",
            ],
            "hooks": hooks,
            "hook_groups": hook_groups,
            "script": active_script,
            "scripts": {
                "main": active_script,
                "hook": active_hook,
                "cta": active_content.get("cta", f"댓글에 '{keyword}' 남겨주세요 👇"),
            },
            "captions": captions,
            "cta": active_content.get("cta", f"댓글에 '{keyword}' 남겨주세요 👇"),
            "capcut_timeline": active_content.get("capcut", capcut_timeline),
        },
        "scripts": {
            "main": active_script,
            "hook": active_hook,
            "cta": active_content.get("cta", f"댓글에 '{keyword}' 남겨주세요 👇"),
        },
        "captions": {
            "items": captions,
            "safe_area": "하단 40~50%",
            "font": "Noto Serif KR Bold",
            "max_lines": 2,
        },
        "shorts_variants": shorts_variants,
        "thumbnail": {
            "size": "9:16",
            "main_text": active_hook,
            "sub_text": project_name,
            "layout": "제품 크게 + 왼쪽 상단 후킹 문구 + 하단 짧은 설명",
            "image_prompt": (
                f"9:16 vertical shopping shorts thumbnail, clean Korean ecommerce style, "
                f"product concept: {project_name}, bright home background, "
                f"large bold Korean text area, realistic product-focused composition"
            ),
        },
        "inpock": {
            "size": "1000x1000",
            "title": project_name,
            "main_text": active_hook,
            "sub_text": "제품 정보는 링크에서 확인",
            "button": "제품 보러가기",
            "link": partner_url or "쿠팡파트너스 링크를 입력하세요.",
            "image_prompt": (
                f"1000x1000 square product promo image for Inpock link page, "
                f"clean Korean shopping design, product concept: {project_name}, "
                f"white background, neat layout, space for Korean title text"
            ),
        },
        "upload_bundle": {
            "youtube_title": active_content.get(
                "title",
                f"{project_name} 추천템 #shorts",
            ),
            "youtube_desc": (
                "🔗 제품 정보는 영상 아래 설명란 링크 또는 프로필 링크를 확인해주세요.\n\n"
                "※ 쿠팡파트너스 활동의 일환으로 일정액의 수수료를 받을 수 있습니다."
            ),
            "instagram_body": (
                f"왜 이제 알았지 싶은 생활템 ✨\n\n"
                f"{project_name}처럼 매일 쓰는 제품은 작은 차이가 크게 느껴지더라고요.\n\n"
                f"제품 정보가 궁금하시면 댓글에 '{keyword}' 남겨주세요 👇"
            ),
            "hashtags": [
                "#쇼핑쇼츠",
                "#생활용품추천",
                "#살림템",
                "#쿠팡추천",
                "#shorts",
                "#릴스",
            ],
            "fixed_comment": f"댓글에 '{keyword}' 남겨주세요 👇",
            "partner_notice": "※ 쿠팡파트너스 활동의 일환으로 일정액의 수수료를 받을 수 있습니다.",
            "source_url": source_url,
            "platform": platform,
        },
        "latest_outputs": outputs,
    }

    return pack