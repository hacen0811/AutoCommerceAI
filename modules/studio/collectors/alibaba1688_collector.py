from __future__ import annotations

from typing import Dict, List
from urllib.parse import quote_plus
from .base_collector import BaseSiteCollector, CollectedVideo


class Alibaba1688Collector(BaseSiteCollector):
    platform = "1688"

    def search_url(self, keyword: str) -> str:
        return f"https://s.1688.com/selloffer/offer_search.htm?keywords={quote_plus(keyword or '')}"

    def collect(self, page, keyword: str, url: str = "", limit: int = 10, image_path: str = "") -> Dict:
        target_url = url or self.search_url(keyword)
        rows: List[CollectedVideo] = []
        diagnostics = {}

        try:
            page.goto(target_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            page.wait_for_timeout(3000)

            upload_attempt = self._try_upload_image(page, image_path) if image_path else {
                "attempted": False,
                "ok": False,
                "message": "image_path 없음",
            }

            page.wait_for_timeout(2500)
            self.slow_scroll(page, 3)

            body = self.body_text(page)
            debug = self.save_debug(page, self.platform)
            items = self._extract_items(page)

            for it in items:
                href = self.normalize_url(it.get("href", ""))
                title = (it.get("title") or it.get("raw_text") or "").strip()[:120]
                thumb = it.get("thumbnail", "")
                h = href.lower()
                joined = f"{title}\n{it.get('raw_text','')}"

                if "1688.com" not in h:
                    continue
                if self.is_junk_text(title, href):
                    continue
                if len(title) < 2:
                    continue
                if any(x in joined for x in ["采集", "下载器", "摄影服务", "反馈", "客服"]):
                    continue

                score = self.score_item(keyword, title, href, thumb)
                if any(x in joined for x in ["工厂", "实拍", "视频", "批发", "供应", "现货"]):
                    score += 30
                if "offer" in h or "detail" in h:
                    score += 25
                if upload_attempt.get("ok"):
                    score += 10

                rows.append(CollectedVideo(
                    platform=self.platform,
                    title=title,
                    url=href,
                    keyword=keyword,
                    score=min(score, 99),
                    thumbnail=thumb,
                    screenshot=debug.get("screenshot", ""),
                    note="1688 이미지/텍스트 검색 후보입니다. 공급처 상세영상과 공장 실사를 우선 확인하세요.",
                ))

            diagnostics = {
                "platform": self.platform,
                "requested_url": target_url,
                "current_url": page.url,
                "page_title": page.title(),
                "image_upload": upload_attempt,
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

    def _try_upload_image(self, page, image_path: str) -> Dict:
        selectors = [
            "input[type=file]",
            "input[accept*='image']",
        ]
        for selector in selectors:
            try:
                loc = page.locator(selector)
                if loc.count() > 0:
                    loc.first.set_input_files(image_path)
                    page.wait_for_timeout(5000)
                    return {"attempted": True, "ok": True, "selector": selector, "message": "이미지 파일 업로드 시도 완료"}
            except Exception as exc:
                last = str(exc)[:300]
        return {"attempted": True, "ok": False, "message": f"이미지 업로드 input을 찾지 못했습니다. {locals().get('last', '')}"}

    def _extract_items(self, page) -> List[Dict]:
        try:
            return page.evaluate(r"""
            () => {
                const nodes = Array.from(document.querySelectorAll('a, div, li, article'));
                const out = [];
                for (const el of nodes.slice(0, 1800)) {
                    const link = el.tagName && el.tagName.toLowerCase() === 'a' ? el : el.querySelector('a');
                    const href = link ? (link.href || link.getAttribute('href') || '') : '';
                    const img = el.querySelector('img');
                    const raw = (el.innerText || el.getAttribute('aria-label') || '').trim();
                    const title = (
                        el.querySelector('[title]')?.getAttribute('title') ||
                        link?.title ||
                        link?.innerText ||
                        raw.split('\n')[0] ||
                        ''
                    ).trim();
                    const thumb = img ? (img.src || img.getAttribute('data-src') || img.getAttribute('data-original') || img.getAttribute('srcset') || '') : '';
                    if (!href && !title && !thumb) continue;
                    out.push({href, title, raw_text: raw.slice(0, 700), thumbnail: thumb});
                }
                return out;
            }
            """) or []
        except Exception:
            return []
