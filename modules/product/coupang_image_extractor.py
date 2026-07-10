import re


class CoupangImageExtractor:
    def extract(self, url):
        url = (url or "").strip()
        if not url:
            return ""

        return self._extract_with_playwright(url)

    def _extract_with_playwright(self, url):
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0 Safari/537.36"
                    ),
                    locale="ko-KR",
                )

                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(3000)

                image_url = (
                    self._meta_content(page, "meta[property='og:image']")
                    or self._meta_content(page, "meta[name='twitter:image']")
                    or self._first_product_image(page)
                )

                browser.close()
                return self._clean_url(image_url)

        except Exception as e:
            with open("debug_coupang_error.txt", "w", encoding="utf-8") as f:
                f.write(str(e))
            return ""

    def _meta_content(self, page, selector):
        try:
            el = page.query_selector(selector)
            if not el:
                return ""
            return el.get_attribute("content") or ""
        except Exception:
            return ""

    def _first_product_image(self, page):
        selectors = [
            "img.prod-image__detail",
            "img.prod-image__item",
            "img[src*='thumbnail']",
            "img[src*='coupangcdn']",
            "img",
        ]

        for selector in selectors:
            try:
                items = page.query_selector_all(selector)
                for item in items:
                    src = item.get_attribute("src") or item.get_attribute("data-src") or ""
                    src = self._clean_url(src)

                    if self._looks_like_product_image(src):
                        return src
            except Exception:
                continue

        return ""

    def _looks_like_product_image(self, value):
        value = value or ""
        if not value.startswith("http"):
            return False

        blocked = ["logo", "icon", "sprite", "blank", "loading"]
        if any(x in value.lower() for x in blocked):
            return False

        return "coupang" in value.lower() or "coupangcdn" in value.lower()

    def _clean_url(self, value):
        value = (value or "").strip()
        value = value.replace("\\/", "/")
        value = value.replace("&amp;", "&")

        if value.startswith("//"):
            value = "https:" + value

        if value.startswith("http"):
            return value

        return ""