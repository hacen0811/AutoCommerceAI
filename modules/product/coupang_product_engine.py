import re
from urllib.parse import urlparse, parse_qs, urlunparse, unquote


class CoupangProductEngine:
    def parse(self, url):
        url = (url or "").strip()
        parsed = urlparse(url)
        query = parse_qs(parsed.query)

        product_id = ""
        vendor_item_id = ""

        m = re.search(r"/vp/products/(\d+)", parsed.path)
        if m:
            product_id = m.group(1)

        if "vendorItemId" in query:
            vendor_item_id = query["vendorItemId"][0]

        clean_query = f"vendorItemId={vendor_item_id}" if vendor_item_id else ""
        clean_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", clean_query, ""))

        guessed_name = self.guess_name(url, product_id)

        return {
            "original_url": url,
            "clean_url": clean_url,
            "product_id": product_id,
            "vendor_item_id": vendor_item_id,
            "platform": "쿠팡" if "coupang.com" in parsed.netloc else "기타",
            "guessed_product_name": guessed_name,
            "keyword": self.keyword(guessed_name),
            "note": "쿠팡은 자동 접근을 차단할 수 있어 상품명/가격/이미지는 직접 보완 입력을 우선합니다.",
        }

    def guess_name(self, url, product_id=""):
        text = unquote(url or "")
        for key in ["q=", "keyword=", "searchKeyword="]:
            if key in text:
                value = text.split(key, 1)[1].split("&", 1)[0].replace("+", " ").strip()
                if value:
                    return value
        return f"쿠팡상품 {product_id}" if product_id else "쿠팡 추천상품"

    def keyword(self, name):
        if "방충" in name or "모기" in name:
            return "방충망"
        if "얼음" in name or "아이스" in name:
            return "얼음"
        if "수전" in name:
            return "수전"
        if "장갑" in name:
            return "장갑"
        parts = [p for p in re.split(r"\s+", name or "") if p]
        return parts[-1] if parts else "정보"
