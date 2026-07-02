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
            page.wait_for_timeout(3500)
            self.slow_scroll(page, 3)
            body = self.body_text(page)
            debug = self.save_debug(page, self.platform)
            items = page.evaluate(r"""
            () => Array.from(document.querySelectorAll('a, div, article')).slice(0, 1200).map(el => {
                const link = el.tagName?.toLowerCase() === 'a' ? el : el.querySelector('a');
                const href = link ? (link.href || '') : '';
                const img = el.querySelector('img');
                const video = el.querySelector('video');
                const raw = (el.innerText || '').trim();
                const title = (link?.title || link?.getAttribute('aria-label') || raw.split('\n')[0] || '').trim();
                const thumb = img ? (img.src || img.getAttribute('srcset') || '') : (video ? video.poster || '' : '');
                return {href, title, raw_text: raw.slice(0,500), thumbnail: thumb};
            }).filter(x => x.href || x.title || x.thumbnail)
            """) or []
            for it in items:
                href = self.normalize_url(it.get("href", ""))
                title = (it.get("title") or it.get("raw_text") or "").strip()[:120]
                thumb = it.get("thumbnail", "")
                h = href.lower()
                if "tiktok.com" not in h or self.is_junk_text(title, href) or len(title) < 2:
                    continue
                score = self.score_item(keyword, title, href, thumb)
                if "/video/" in h or "/@" in h:
                    score += 25
                rows.append(CollectedVideo(self.platform, title, href, keyword, min(score, 99), thumbnail=thumb, screenshot=debug.get("screenshot", "")))
            diagnostics = {
                "platform": self.platform, "requested_url": target_url, "current_url": page.url,
                "page_title": page.title(), "dom_item_count": len(items), "extracted_count": len(rows),
                "blocked_hint": self.blocked_hint(page, body), **debug, "sample_items": items[:5],
            }
        except Exception as exc:
            diagnostics = {"platform": self.platform, "requested_url": target_url, "error": str(exc)[:800]}
        final_rows = self.dedupe(rows, limit)
        diagnostics["final_count"] = len(final_rows)
        return {"results": final_rows, "diagnostics": diagnostics}
