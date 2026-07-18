import re
from urllib.parse import urlparse, parse_qs


def analyze_coupang_url(url: str) -> dict:
    url = (url or "").strip()

    result = {
        "is_valid": False,
        "url": url,
        "product_id": "",
        "item_id": "",
        "vendor_item_id": "",
        "message": "쿠팡 링크를 입력해주세요.",
    }

    if not url:
        return result

    parsed = urlparse(url)

    if "coupang.com" not in parsed.netloc:
        result["message"] = "쿠팡 링크가 아닙니다."
        return result

    match = re.search(r"/vp/products/(\d+)", parsed.path)
    if match:
        result["product_id"] = match.group(1)

    query = parse_qs(parsed.query)
    result["item_id"] = query.get("itemId", [""])[0]
    result["vendor_item_id"] = query.get("vendorItemId", [""])[0]

    if result["product_id"]:
        result["is_valid"] = True
        result["message"] = "쿠팡 상품 링크 형식이 확인되었습니다."
    else:
        result["message"] = "상품 ID를 찾지 못했습니다."

    return result