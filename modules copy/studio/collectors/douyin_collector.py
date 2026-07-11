from __future__ import annotations

from typing import Dict, List
from urllib.parse import quote_plus
from .base_collector import BaseSiteCollector, CollectedVideo


class DouyinCollector(BaseSiteCollector):
    platform = "douyin"

    def search_url(self, keyword: str) -> str:
        return f"https://www.douyin.com/search/{quote_plus(keyword or '')}"

    def collect(self, page, keyword: str, url: str = "", limit: int = 10) -> Dict:
        target_url = url or self.search_url(keyword)
        rows: List[CollectedVideo] = []
        diagnostics = {}

        try:
            page.goto(target_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            page.wait_for_timeout(3000)
            self.slow_scroll(page, 3)

            body = self.body_text(page)
            debug = self.save_debug(page, self.platform)

            items = page.evaluate(r"""
            () => {
                const nodes = Array.from(document.querySelectorAll('a, article, section, li, div[data-e2e], div'));
                const out = [];
                for (const el of nodes.slice(0, 1500)) {
                    const link = el.tagName && el.tagName.toLowerCase() === 'a' ? el : el.querySelector('a');
                    const href = link ? (link.href || link.getAttribute('href') || '') : '';
                    const img = el.querySelector('img');
                    const video = el.querySelector('video');
                    const raw = (el.innerText || el.getAttribute('aria-label') || '').trim();
                    const title = (
                        el.querySelector('h3')?.innerText ||
                        link?.getAttribute('aria-label') ||
                        link?.title ||
                        link?.innerText ||
                        raw.split('\n')[0] ||
                        ''
                    ).trim();
                    const thumb = img ? (img.src || img.getAttribute('data-src') || img.getAttribute('data-original') || '') : (video ? (video.poster || '') : '');
                    if (!href && !title && !thumb) continue;
                    out.push({href, title, raw_text: raw.slice(0, 500), thumbnail: thumb});
                }
                return out;
            }
            """) or []

            for it in items:
                href = self.normalize_url(it.get("href", ""))
                title = (it.get("title") or it.get("raw_text") or "").strip()[:120]
                thumb = it.get("thumbnail", "")
                if "douyin.com" not in href.lower():
                    continue
                if "/user/self" in href.lower():
                    continue
                if self.is_junk_text(title, href):
                    continue
                if len(title) < 2:
                    continue

                score = self.score_item(keyword, title, href, thumb)
                if any(x in href.lower() for x in ["/video/", "modal_id=", "aweme", "/note/"]):
                    score += 20
                rows.append(CollectedVideo(
                    platform=self.platform,
                    title=title,
                    url=href,
                    keyword=keyword,
                    score=min(score, 99),
                    thumbnail=thumb,
                    screenshot=debug.get("screenshot", ""),
                ))

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
            diagnostics = {"platform": self.platform, "requested_url": target_url, "error": str(exc)[:800]}

        final_rows = self.dedupe(rows, limit)
        diagnostics["final_count"] = len(final_rows)
        return {"results": final_rows, "diagnostics": diagnostics}
