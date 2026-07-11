import json
import re
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlunparse


class _MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
        self.title = ""
        self._in_title = False
        self.scripts = []
        self._in_script = False
        self._script_buf = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if tag.lower() == "title":
            self._in_title = True

        if tag.lower() == "meta":
            key = attrs.get("property") or attrs.get("name") or attrs.get("itemprop")
            val = attrs.get("content")
            if key and val:
                self.meta[key.lower()] = unescape(val).strip()

        if tag.lower() == "script":
            script_type = (attrs.get("type") or "").lower()
            if "ld+json" in script_type:
                self._in_script = True
                self._script_buf = []

    def handle_data(self, data):
        if self._in_title:
            self.title += data

        if self._in_script:
            self._script_buf.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self._in_title = False

        if tag.lower() == "script" and self._in_script:
            self.scripts.append("".join(self._script_buf).strip())
            self._in_script = False
            self._script_buf = []


class CoupangMetadataExtractor:
    """
    Sprint 47-2
    쿠팡 메타데이터 추출기.

    기존 urlopen 방식은 쿠팡에서 403이 발생하므로,
    프로젝트의 Playwright persistent profile을 재사용합니다.

    사용 프로필:
    browser_profile/source_sites
    """

    def __init__(self):
        self.profile_dir = Path("browser_profile/source_sites")
        self.debug_dir = Path("exports/debug")
        self.debug_dir.mkdir(parents=True, exist_ok=True)

    def extract(
        self,
        coupang_url="",
        product_name="",
        price="",
        category="",
        image_url="",
        partner_url="",
        fetch=True,
    ):
        url = (coupang_url or "").strip()
        parsed = urlparse(url) if url else None
        query = parse_qs(parsed.query) if parsed else {}

        product_id = self._find_product_id(url)
        item_id = self._first(query.get("itemId"))
        vendor_item_id = self._first(query.get("vendorItemId"))
        clean_url = self._clean_url(parsed) if parsed else url

        base = {
            "ok": True,
            "source": "manual+url",
            "clean_url": clean_url or url,
            "product_id": product_id,
            "item_id": item_id,
            "vendor_item_id": vendor_item_id,
            "product_name": (product_name or "").strip(),
            "price": (price or "").strip(),
            "category": (category or "").strip(),
            "image_url": (image_url or "").strip(),
            "partner_url": (partner_url or "").strip(),
            "description": "",
            "features": [],
            "auto_fetched": False,
            "fetch_status": "not_requested",
            "fetch_error": "",
            "memo": "쿠팡이 차단하면 입력값과 URL 식별값으로 안전하게 생성합니다.",
        }

        if not url or not fetch:
            return base

        fetched = self._fetch_public_metadata(url)

        base["fetch_status"] = fetched.get("status", "unknown")
        base["fetch_error"] = fetched.get("error", "")

        if fetched.get("ok"):
            base["auto_fetched"] = True
            base["source"] = "manual+url+playwright_profile"

            if not base["product_name"] and fetched.get("title"):
                base["product_name"] = self._clean_title(fetched.get("title"))

            if not base["image_url"] and fetched.get("image_url"):
                base["image_url"] = fetched.get("image_url")

            if not base["price"] and fetched.get("price"):
                base["price"] = fetched.get("price")

            if not base["description"] and fetched.get("description"):
                base["description"] = fetched.get("description")

            if fetched.get("features"):
                base["features"] = fetched.get("features")[:8]

            base["raw_meta_keys"] = fetched.get("raw_meta_keys", [])[:30]
            base["memo"] = "Playwright 로그인 브라우저 프로필로 쿠팡 메타데이터를 읽었습니다."

        return base

    def _fetch_public_metadata(self, url):
        context = None

        try:
            from playwright.sync_api import sync_playwright

            self.profile_dir.mkdir(parents=True, exist_ok=True)

            with sync_playwright() as pw:
                context = pw.chromium.launch_persistent_context(
                    user_data_dir=str(self.profile_dir),
                    headless=True,
                    viewport={"width": 1280, "height": 900},
                    locale="ko-KR",
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/125.0 Safari/537.36"
                    ),
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-first-run",
                        "--no-default-browser-check",
                    ],
                )

                page = context.pages[0] if context.pages else context.new_page()
                page.set_default_timeout(15000)

                page.goto(url, wait_until="domcontentloaded", timeout=20000)
                page.wait_for_timeout(3000)

                html = page.content()

                debug_path = self.debug_dir / "debug_coupang_playwright.html"
                debug_path.write_text(html, encoding="utf-8")

                meta_result = self._parse_html_metadata(html)

                if not meta_result.get("image_url"):
                    fallback_image = self._extract_image_from_page(page)
                    if fallback_image:
                        meta_result["image_url"] = fallback_image

                meta_result["status"] = "playwright_ok"
                meta_result["debug_path"] = str(debug_path)
                return meta_result

        except Exception as e:
            error_path = self.debug_dir / "debug_coupang_playwright_error.txt"
            error_path.write_text(str(e), encoding="utf-8")

            return {
                "ok": False,
                "status": "playwright_failed",
                "error": str(e),
            }

        finally:
            try:
                if context:
                    context.close()
            except Exception:
                pass

    def _parse_html_metadata(self, html):
        parser = _MetaParser()

        try:
            parser.feed(html or "")
        except Exception:
            pass

        meta = parser.meta

        title = (
            meta.get("og:title")
            or meta.get("twitter:title")
            or parser.title.strip()
        )

        desc = (
            meta.get("og:description")
            or meta.get("description")
            or meta.get("twitter:description")
            or ""
        )

        image = (
            meta.get("og:image")
            or meta.get("twitter:image")
            or meta.get("image")
            or ""
        )

        price = meta.get("product:price:amount") or meta.get("price") or ""

        features = self._extract_feature_candidates(html)

        for script in parser.scripts[:10]:
            data = self._try_json(script)

            for obj in self._walk_json(data):
                if not isinstance(obj, dict):
                    continue

                typ = obj.get("@type") or obj.get("type")
                typ_text = " ".join(typ) if isinstance(typ, list) else str(typ or "")

                if "Product" in typ_text or obj.get("name") or obj.get("offers"):
                    title = title or obj.get("name") or ""
                    image = image or self._first_json(obj.get("image"))
                    desc = desc or obj.get("description") or ""

                    offers = obj.get("offers")
                    if isinstance(offers, dict):
                        price = price or str(offers.get("price") or "")

                    if isinstance(obj.get("brand"), dict):
                        features.append("브랜드: " + str(obj["brand"].get("name", "")))

        image = self._clean_image_url(image)

        return {
            "ok": bool(title or image or desc or price or features),
            "title": self._squash(title),
            "description": self._squash(desc),
            "image_url": image,
            "price": self._squash(price),
            "features": [self._squash(x) for x in features if self._squash(x)],
            "raw_meta_keys": sorted(meta.keys()),
        }

    def _extract_image_from_page(self, page):
        selectors = [
            "meta[property='og:image']",
            "meta[name='twitter:image']",
            "img.prod-image__detail",
            "img.prod-image__item",
            "img[src*='coupangcdn']",
            "img[src*='thumbnail']",
            "img",
        ]

        for selector in selectors:
            try:
                if selector.startswith("meta"):
                    el = page.query_selector(selector)
                    if el:
                        value = el.get_attribute("content") or ""
                        value = self._clean_image_url(value)
                        if value:
                            return value
                else:
                    items = page.query_selector_all(selector)
                    for item in items:
                        value = (
                            item.get_attribute("src")
                            or item.get_attribute("data-src")
                            or item.get_attribute("data-original")
                            or ""
                        )
                        value = self._clean_image_url(value)
                        if self._looks_like_product_image(value):
                            return value
            except Exception:
                continue

        return ""

    def _looks_like_product_image(self, value):
        value = (value or "").lower()

        if not value.startswith("http"):
            return False

        blocked = ["logo", "icon", "sprite", "blank", "loading", "banner"]

        if any(x in value for x in blocked):
            return False

        return "coupang" in value or "coupangcdn" in value

    def _clean_image_url(self, value):
        value = str(value or "").strip()
        value = value.replace("\\/", "/")
        value = value.replace("&amp;", "&")

        if value.startswith("//"):
            value = "https:" + value

        if value.startswith("http"):
            return value

        return ""

    def _extract_feature_candidates(self, html):
        text = re.sub(r"<script[\s\S]*?</script>", " ", html or "", flags=re.I)
        text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
        text = re.sub(r"<[^>]+>", "\n", text)
        text = unescape(text)

        rows = []

        for line in text.splitlines():
            s = self._squash(line)

            if 8 <= len(s) <= 90 and any(
                k in s for k in ["무료배송", "쿠팡", "로켓", "상품", "구매", "리뷰", "할인", "배송"]
            ):
                if s not in rows:
                    rows.append(s)

            if len(rows) >= 8:
                break

        return rows

    def _try_json(self, text):
        try:
            return json.loads(text)
        except Exception:
            return None

    def _walk_json(self, data):
        if isinstance(data, dict):
            yield data
            for v in data.values():
                yield from self._walk_json(v)

        elif isinstance(data, list):
            for x in data:
                yield from self._walk_json(x)

    def _first_json(self, value):
        if isinstance(value, list):
            return str(value[0]) if value else ""
        return str(value or "")

    def _clean_title(self, title):
        title = self._squash(title)
        title = re.sub(r"\s*[-|]\s*쿠팡.*$", "", title)
        return title.strip()

    def _squash(self, text):
        return re.sub(r"\s+", " ", str(text or "")).strip()

    def _find_product_id(self, text):
        m = re.search(r"/products/(\d+)", text or "")
        return m.group(1) if m else ""

    def _first(self, values):
        if not values:
            return ""
        return str(values[0])

    def _clean_url(self, parsed):
        if not parsed:
            return ""
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))