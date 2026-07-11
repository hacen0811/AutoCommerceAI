from __future__ import annotations

from typing import Dict, List
from urllib.parse import quote_plus

from .base_collector import BaseSiteCollector, CollectedVideo


class TikTokCollector(BaseSiteCollector):
    platform = "tiktok"

    def search_url(self, keyword: str) -> str:
        return f"https://www.tiktok.com/search?q={quote_plus(keyword or '')}"

    def collect(self, page, keyword: str, url: str = "", limit: int = 10) -> Dict:
        target_url = url or self.search_url(keyword)
        rows: List[CollectedVideo] = []
        diagnostics = {}

        try:
            page.goto(target_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            page.wait_for_timeout(5000)
            self.slow_scroll(page, 4)

            body = self.body_text(page)
            debug = self.save_debug(page, self.platform)

            items = page.evaluate(
                r"""
                () => {
                    const anchors = Array.from(document.querySelectorAll("a[href*='/video/']"));

                    return anchors.slice(0, 80).map((a) => {
                        const card =
                            a.closest("div[data-e2e]") ||
                            a.closest("article") ||
                            a.closest("div") ||
                            a;

                        const img = card.querySelector("img") || a.querySelector("img");
                        const video = card.querySelector("video") || a.querySelector("video");

                        const raw = (card.innerText || a.innerText || "").trim();
                        const title =
                            a.getAttribute("title") ||
                            a.getAttribute("aria-label") ||
                            raw.split("\\n").find(Boolean) ||
                            "";

                        const thumb =
                            (img && (img.src || img.getAttribute("src") || img.getAttribute("data-src"))) ||
                            (video && (video.poster || "")) ||
                            "";

                        const statText = raw.slice(0, 500);

                        return {
                            href: a.href || "",
                            title: title.trim(),
                            raw_text: raw.slice(0, 500),
                            thumbnail: thumb,
                            stat_text: statText,
                        };
                    });
                }
                """
            ) or []

            for it in items:
                href = self.normalize_url(it.get("href", ""))
                title = (it.get("title") or it.get("raw_text") or "").strip()[:140]
                thumb = it.get("thumbnail", "") or ""
                raw_text = it.get("raw_text", "") or ""

                if not href or "/video/" not in href.lower():
                    continue

                if "tiktok.com" not in href.lower():
                    continue

                if self.is_junk_text(title, href):
                    continue

                if len(title) < 2:
                    title = f"TikTok 후보 - {keyword}"

                score = self.score_item(keyword, title, href, thumb)
                score += 25

                views = self.extract_metric(raw_text, ["views", "view", "조회", "회"])
                likes = self.extract_metric(raw_text, ["likes", "like", "좋아요"])

                rows.append(
                    CollectedVideo(
                        platform=self.platform,
                        title=title,
                        url=href,
                        keyword=keyword,
                        score=min(score, 99),
                        thumbnail=thumb,
                        screenshot=debug.get("screenshot", ""),
                        views=views,
                        likes=likes,
                        note="TikTok 검색 결과의 실제 /video/ 링크에서 수집한 후보입니다.",
                    )
                )

            diagnostics = {
                "platform": self.platform,
                "requested_url": target_url,
                "current_url": page.url,
                "page_title": page.title(),
                "dom_item_count": len(items),
                "extracted_count": len(rows),
                "blocked_hint": self.blocked_hint(page, body),
                **debug,
                "sample_items": items[:5],
            }

        except Exception as exc:
            diagnostics = {
                "platform": self.platform,
                "requested_url": target_url,
                "error": str(exc)[:800],
            }

        final_rows = self.dedupe(rows, limit)
        diagnostics["final_count"] = len(final_rows)

        return {
            "results": final_rows,
            "diagnostics": diagnostics,
        }

    def extract_metric(self, text: str, hints=None) -> str:
        text = str(text or "")
        hints = hints or []

        lines = [x.strip() for x in text.splitlines() if x.strip()]

        for line in lines:
            lower = line.lower()

            if hints and not any(h in lower for h in hints):
                continue

            for token in line.split():
                if any(ch.isdigit() for ch in token):
                    return token[:30]

        return ""