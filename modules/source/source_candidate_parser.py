from urllib.parse import urljoin


class SourceCandidateParser:
    """
    Sprint 52-1
    Playwright page에서 실제 후보 카드 정보를 추출합니다.

    역할:
    - 검색어 생성 아님
    - 다운로드 아님
    - HTML/DOM에서 title, url, thumbnail 후보만 수집
    """

    def parse(self, page, platform=""):
        platform = str(platform or "").lower().strip()

        if platform in ["douyin", "tiktok"]:
            return self.parse_tiktok(page)

        if platform == "taobao":
            return self.parse_taobao(page)

        if platform == "1688":
            return self.parse_1688(page)

        return []

    def parse_tiktok(self, page):
        items = []

        cards = page.locator("a[href*='/video/']")
        count = min(cards.count(), 30)

        for i in range(count):
            try:
                card = cards.nth(i)
                href = card.get_attribute("href") or ""
                title = (
                    card.get_attribute("title")
                    or card.inner_text(timeout=1000)
                    or ""
                )

                img = card.locator("img").first
                thumbnail = ""
                if img.count():
                    thumbnail = (
                        img.get_attribute("src")
                        or img.get_attribute("data-src")
                        or ""
                    )

                items.append(
                    self.clean_candidate(
                        platform="tiktok",
                        rank=len(items) + 1,
                        title=title,
                        url=href,
                        thumbnail=thumbnail,
                    )
                )
            except Exception:
                continue

        return self.dedupe(items)

    def parse_taobao(self, page):
        items = []

        links = page.locator("a[href*='item.taobao.com'], a[href*='detail.tmall.com']")
        count = min(links.count(), 40)

        for i in range(count):
            try:
                link = links.nth(i)
                href = link.get_attribute("href") or ""
                title = (
                    link.get_attribute("title")
                    or link.inner_text(timeout=1000)
                    or ""
                )

                img = link.locator("img").first
                thumbnail = ""
                if img.count():
                    thumbnail = (
                        img.get_attribute("src")
                        or img.get_attribute("data-src")
                        or img.get_attribute("data-ks-lazyload")
                        or ""
                    )

                items.append(
                    self.clean_candidate(
                        platform="taobao",
                        rank=len(items) + 1,
                        title=title,
                        url=href,
                        thumbnail=thumbnail,
                    )
                )
            except Exception:
                continue

        return self.dedupe(items)

    def parse_1688(self, page):
        items = []

        links = page.locator("a[href*='detail.1688.com']")
        count = min(links.count(), 40)

        for i in range(count):
            try:
                link = links.nth(i)
                href = link.get_attribute("href") or ""
                title = (
                    link.get_attribute("title")
                    or link.inner_text(timeout=1000)
                    or ""
                )

                img = link.locator("img").first
                thumbnail = ""
                if img.count():
                    thumbnail = (
                        img.get_attribute("src")
                        or img.get_attribute("data-src")
                        or ""
                    )

                items.append(
                    self.clean_candidate(
                        platform="1688",
                        rank=len(items) + 1,
                        title=title,
                        url=href,
                        thumbnail=thumbnail,
                    )
                )
            except Exception:
                continue

        return self.dedupe(items)

    def clean_candidate(self, platform, rank, title, url, thumbnail):
        title = self.clean_text(title)
        url = self.normalize_url(url)
        thumbnail = self.normalize_url(thumbnail)

        return {
            "rank": rank,
            "platform": platform,
            "title": title,
            "url": url,
            "thumbnail": thumbnail,
            "score": 0,
            "purpose": "실제 검색 결과 후보",
        }

    def clean_text(self, text):
        text = str(text or "")
        text = " ".join(text.split())
        return text[:160]

    def normalize_url(self, url):
        url = str(url or "").strip()

        if not url:
            return ""

        if url.startswith("//"):
            return "https:" + url

        if url.startswith("/"):
            return urljoin("https://www.tiktok.com", url)

        return url

    def dedupe(self, items):
        seen = set()
        result = []

        for item in items:
            url = item.get("url") or ""
            title = item.get("title") or ""

            key = url or title
            if not key:
                continue

            if key in seen:
                continue

            seen.add(key)
            item["rank"] = len(result) + 1
            result.append(item)

        return result