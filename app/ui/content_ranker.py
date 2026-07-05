def rank_content_variants(profile=None, variants=None):
    """
    Sprint 19-1
    콘텐츠 유형 추천 엔진.
    기존 variants에 score, rank, recommended를 추가한다.
    """
    profile = profile or {}
    variants = variants or []

    category = profile.get("category", "")
    features = profile.get("features") or []

    weights = {
        "공감형": 80,
        "정보형": 75,
        "충격형": 70,
        "BeforeAfter형": 78,
        "리뷰형": 72,
    }

    if "수납" in category or "정리" in category:
        weights["공감형"] += 16
        weights["BeforeAfter형"] += 15
        weights["정보형"] += 10

    if "신발" in category:
        weights["BeforeAfter형"] += 18
        weights["공감형"] += 12

    if "생활 편의" in features:
        weights["공감형"] += 4

    ranked = []

    for variant in variants:
        item = dict(variant)

        score = weights.get(item.get("type"), 70)

        item["score"] = score

        ranked.append(item)

    ranked.sort(
        key=lambda x: x["score"],
        reverse=True,
    )

    for idx, item in enumerate(ranked, start=1):
        item["rank"] = idx
        item["recommended"] = idx == 1

    return ranked

def apply_selected_variant(self, content_pack):
    shorts = content_pack.get("shorts", {})
    titles = shorts.get("titles", [])
    hooks = shorts.get("hooks", [])
    script = shorts.get("script", [])

    selected_variant = content_pack.get("selected_variant") or {}

    if not selected_variant:
        selected_variant = {
            "title": titles[0] if titles else "",
            "hook": hooks[0] if hooks else "",
            "script": script,
            "cta": "",
        }

    content_pack["selected_variant"] = selected_variant

    title = active_content.get("title", "")
    hook = active_content.get("hook", "")
    cta = active_content.get("cta", "")

    if title:
        content_pack.setdefault("upload", {})
        content_pack["upload"]["youtube_title"] = title

    if hook:
        content_pack.setdefault("thumbnail", {})
        content_pack["thumbnail"]["main_text"] = hook

        content_pack.setdefault("inpock", {})
        content_pack["inpock"]["main_text"] = hook

    if cta:
        content_pack.setdefault("upload", {})
        instagram_body = content_pack["upload"].get("instagram_body", "")
        if cta not in instagram_body:
            content_pack["upload"]["instagram_body"] = instagram_body + "\n\n" + cta

    return content_pack