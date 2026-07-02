from __future__ import annotations

import re
from typing import Dict, List
from urllib.parse import quote_plus

from .base_collector import BaseSiteCollector, CollectedVideo


class TaobaoCollector(BaseSiteCollector):
    """
    Sprint 6-6 Taobao click-flow collector.

    핵심 변경:
    - 검색결과 href 파싱 후 page.goto(href) 방식 제거
    - 검색결과의 실제 a[href] 상품카드 Locator를 클릭
    - context.expect_page()로 새 탭 상세페이지 수신
    - 상세페이지에서 video/source/mp4/主图视频 힌트 추출
    """

    platform = "taobao"

    def search_url(self, keyword: str) -> str:
        return f"https://s.taobao.com/search?q={quote_plus(keyword or '')}"

    def collect(self, page, keyword: str, url: str = "", limit: int = 10, image_path: str = "") -> Dict:
        target_url = url or self.search_url(keyword)
        rows: List[CollectedVideo] = []
        diagnostics: Dict = {
            "platform": self.platform,
            "requested_url": target_url,
            "click_flow": True,
            "click_method": "locator_click_expect_page",
        }

        try:
            page.goto(target_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            page.wait_for_timeout(3000)

            upload_attempt = self._try_upload_image(page, image_path) if image_path else {
                "attempted": False,
                "ok": False,
                "message": "image_path 없음",
            }

            page.wait_for_timeout(4000)
            self.slow_scroll(page, 2)

            body = self.body_text(page)
            search_debug = self.save_debug(page, "taobao_search_click_flow")

            product_cards = self._extract_product_cards(page, keyword)
            detail_logs = []

            # href를 직접 page.goto 하지 않고, 검색결과의 실제 상품카드를 클릭합니다.
            for card in product_cards[:5]:
                try:
                    detail_pack = self._open_detail_by_card_click(page, keyword, card)
                    rows.extend(detail_pack.get("results", []))
                    detail_logs.append(detail_pack.get("diagnostics", {}))

                    if len(rows) >= limit:
                        break

                    # 상세 탭은 닫고 검색 페이지는 유지하는 구조입니다.
                    page.wait_for_timeout(800)

                except Exception as exc:
                    detail_logs.append({
                        "href": card.get("href", ""),
                        "title": card.get("title", ""),
                        "locator_index": card.get("locator_index"),
                        "error": str(exc)[:500],
                    })

            # 상세페이지에서 후보가 하나도 안 잡히면 상품 카드 fallback을 제한적으로만 반환
            if not rows:
                for card in product_cards[:min(5, limit)]:
                    rows.append(
                        CollectedVideo(
                            platform=self.platform,
                            title=f"상세 확인 필요 - {card.get('title', '')[:90]}",
                            url=card.get("href", ""),
                            keyword=keyword,
                            score=min(card.get("score", 70), 88),
                            thumbnail=card.get("thumbnail", ""),
                            screenshot=search_debug.get("screenshot", ""),
                            note="타오바오 상품 카드입니다. 자동 클릭 상세 진입 실패 또는 영상 미감지 상태입니다.",
                        )
                    )

            diagnostics.update({
                "current_url": page.url,
                "page_title": self._safe_title(page),
                "image_upload": upload_attempt,
                "product_card_count": len(product_cards),
                "detail_checked_count": len(detail_logs),
                "extracted_count": len(rows),
                "blocked_hint": self.blocked_hint(page, body),
                **search_debug,
                "sample_product_cards": product_cards[:5],
                "detail_logs": detail_logs,
            })

        except Exception as exc:
            diagnostics.update({
                "error": str(exc)[:800],
            })

        final_rows = self.dedupe(rows, limit)
        diagnostics["final_count"] = len(final_rows)
        return {"results": final_rows, "diagnostics": diagnostics}

    def _try_upload_image(self, page, image_path: str) -> Dict:
        click_selectors = [
            "button:has-text('图片')",
            "button:has-text('图片搜索')",
            "[aria-label*='图片']",
            "[aria-label*='相机']",
            "[class*='camera']",
            "[class*='image']",
            "[class*='photo']",
        ]

        for selector in click_selectors:
            try:
                loc = page.locator(selector)
                if loc.count() > 0:
                    loc.first.click(timeout=1500)
                    page.wait_for_timeout(1000)
                    break
            except Exception:
                pass

        last = ""
        for selector in ["input[type=file]", "input[accept*='image']", "input[accept*='png']", "input[accept*='jpg']"]:
            try:
                loc = page.locator(selector)
                if loc.count() > 0:
                    loc.first.set_input_files(image_path)
                    page.wait_for_timeout(7000)
                    return {
                        "attempted": True,
                        "ok": True,
                        "selector": selector,
                        "message": "이미지 파일 업로드 시도 완료",
                    }
            except Exception as exc:
                last = str(exc)[:300]

        return {
            "attempted": True,
            "ok": False,
            "message": f"이미지 업로드 input을 찾지 못했습니다. {last}",
        }

    def _extract_product_cards(self, page, keyword: str) -> List[Dict]:
        """
        검색결과에서 클릭 가능한 a[href]의 locator_index를 함께 저장합니다.
        이후 page.locator("a[href]").nth(locator_index).click()으로 실제 카드 클릭을 수행합니다.
        """
        try:
            items = page.evaluate(r"""
            () => {
                const out = [];
                const anchors = Array.from(document.querySelectorAll('a[href]')).slice(0, 2200);

                anchors.forEach((a, index) => {
                    const href = a.href || a.getAttribute('href') || '';
                    const container =
                        a.closest('li') ||
                        a.closest('article') ||
                        a.closest('[class*=item]') ||
                        a.closest('[class*=Item]') ||
                        a.closest('[class*=card]') ||
                        a.closest('[class*=Card]') ||
                        a.parentElement ||
                        a;

                    const img = container.querySelector('img') || a.querySelector('img');
                    const raw = (container.innerText || a.innerText || a.getAttribute('aria-label') || '').trim();
                    const title = (
                        container.querySelector('[title]')?.getAttribute('title') ||
                        a.title ||
                        a.innerText ||
                        raw.split('\n')[0] ||
                        ''
                    ).trim();

                    const thumb = img ? (
                        img.src ||
                        img.getAttribute('data-src') ||
                        img.getAttribute('data-original') ||
                        img.getAttribute('srcset') ||
                        ''
                    ) : '';

                    const lower = href.toLowerCase();
                    const isItem = lower.includes('item') || lower.includes('detail') || lower.includes('auction');
                    const hasPrice = /¥|￥|\d+\.\d+/.test(raw);
                    const hasSales = /人付款|人已买|销量|购买|评价|订单|已售/.test(raw);
                    const hasProductImage = !!thumb;

                    out.push({
                        href,
                        title,
                        raw_text: raw.slice(0, 900),
                        thumbnail: thumb,
                        locator_index: index,
                        is_item: isItem,
                        has_price: hasPrice,
                        has_sales: hasSales,
                        has_product_image: hasProductImage
                    });
                });

                return out;
            }
            """) or []
        except Exception:
            return []

        out: List[Dict] = []
        for it in items:
            href = self.normalize_url(it.get("href", ""))
            title = (it.get("title") or it.get("raw_text") or "").strip()[:140]
            thumb = it.get("thumbnail", "")
            raw = it.get("raw_text", "")
            h = href.lower()
            joined = f"{title}\n{raw}"

            if not any(x in h for x in ["taobao.com", "tmall.com"]):
                continue
            if not any(x in h for x in ["item", "detail", "auction"]):
                continue
            if self.is_junk_text(title, href):
                continue
            if len(title) < 2:
                continue

            if any(x in joined for x in [
                "视频制作", "剪辑", "拍摄服务", "图片批量下载", "采集", "摄影服务",
                "反馈", "教程", "课程", "AI", "ai官网", "低价引流", "客服",
                "详情页设计", "产品拍摄", "白底图", "模特拍摄", "主图拍摄",
                "电商主图", "页面设计", "海报设计", "抠图", "修图",
            ]):
                continue

            if not (it.get("has_price") or it.get("has_sales") or it.get("has_product_image")):
                continue

            score = self.score_item(keyword, title, href, thumb)

            if any(x in joined for x in ["收纳", "整理", "抽拉", "滑轨", "置物架", "厨房", "橱柜", "柜", "架", "篮", "盒"]):
                score += 35
            if it.get("has_price"):
                score += 10
            if it.get("has_sales"):
                score += 10
            if thumb:
                score += 10

            out.append({
                "href": href,
                "title": title,
                "thumbnail": thumb,
                "raw_text": raw,
                "locator_index": it.get("locator_index"),
                "score": min(score, 99),
            })

        seen = set()
        deduped = []
        for it in sorted(out, key=lambda x: x.get("score", 0), reverse=True):
            key = it.get("href", "").split("?")[0].split("#")[0]
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(it)

        return deduped[:12]

    def _open_detail_by_card_click(self, page, keyword: str, card: Dict) -> Dict:
        rows: List[CollectedVideo] = []
        diagnostics = {
            "href": card.get("href", ""),
            "card_title": card.get("title", ""),
            "locator_index": card.get("locator_index"),
            "ok": False,
            "opened_by": "card_click",
        }

        locator_index = card.get("locator_index")
        if locator_index is None:
            diagnostics["error"] = "locator_index 없음"
            return {"results": rows, "diagnostics": diagnostics}

        detail_page = None
        try:
            card_link = page.locator("a[href]").nth(int(locator_index))
            card_link.scroll_into_view_if_needed(timeout=5000)
            page.wait_for_timeout(500)

            print(f"[TAOBAO] 상품카드 클릭 시도 index={locator_index} title={card.get('title', '')[:60]}")

            with page.context.expect_page(timeout=15000) as popup:
                card_link.click(timeout=8000, force=True)

            detail_page = popup.value
            detail_page.wait_for_load_state("domcontentloaded", timeout=self.timeout_ms)
            detail_page.wait_for_timeout(5000)
            self.slow_scroll(detail_page, 1)

            detail_url = detail_page.url
            print(f"[TAOBAO] 새 탭 상세페이지 진입 성공: {detail_url}")

            body = self.body_text(detail_page)
            debug = self.save_debug(detail_page, "taobao_detail_click_flow")
            data = self._extract_detail_video_data(detail_page)

            title = (data.get("title") or card.get("title") or "타오바오 상세 영상 후보").strip()[:120]
            base_score = card.get("score", 75)

            for v in data.get("videos", []):
                src = (v.get("src") or "").strip()
                poster = (v.get("poster") or card.get("thumbnail") or "").strip()
                if not src:
                    continue
                rows.append(CollectedVideo(
                    platform=self.platform,
                    title=f"主图视频 후보 - {title}",
                    url=src,
                    keyword=keyword,
                    score=min(base_score + 45, 99),
                    thumbnail=poster,
                    screenshot=debug.get("screenshot", ""),
                    note=f"타오바오 상품 상세 새 탭에서 직접 감지한 영상 후보입니다. type={v.get('type', '')}",
                ))

            if not rows and data.get("hints"):
                thumb = card.get("thumbnail", "")
                if data["hints"] and data["hints"][0].get("poster"):
                    thumb = data["hints"][0].get("poster")
                rows.append(CollectedVideo(
                    platform=self.platform,
                    title=f"상세페이지 영상 확인 필요 - {title}",
                    url=detail_page.url,
                    keyword=keyword,
                    score=min(base_score + 25, 96),
                    thumbnail=thumb,
                    screenshot=debug.get("screenshot", ""),
                    note="상세페이지에서 视频/主图/实拍/买家秀 힌트를 발견했습니다. 클릭형 영상일 수 있어 수동 확인이 필요합니다.",
                ))

            if not rows:
                rows.append(CollectedVideo(
                    platform=self.platform,
                    title=f"동일상품 상세 확인 - {title}",
                    url=detail_page.url,
                    keyword=keyword,
                    score=min(base_score, 88),
                    thumbnail=card.get("thumbnail", ""),
                    screenshot=debug.get("screenshot", ""),
                    note="상품카드 클릭으로 상세페이지 진입은 성공했지만 영상이 자동 감지되지는 않았습니다.",
                ))

            diagnostics.update({
                "ok": bool(rows),
                "current_url": detail_page.url,
                "page_title": self._safe_title(detail_page),
                "blocked_hint": self.blocked_hint(detail_page, body),
                "video_tag_count": data.get("video_tag_count", 0),
                "source_tag_count": data.get("source_tag_count", 0),
                "mp4_count": data.get("mp4_count", 0),
                "video_hint_count": len(data.get("hints", [])),
                "image_count": len(data.get("images", [])),
                "title": title,
                **debug,
            })

        except Exception as exc:
            diagnostics.update({
                "error": str(exc)[:800],
            })
            print(f"[TAOBAO] 상품카드 클릭/새 탭 진입 실패: {exc}")

        finally:
            try:
                if detail_page and not detail_page.is_closed():
                    detail_page.close()
            except Exception:
                pass
            try:
                page.bring_to_front()
            except Exception:
                pass

        return {"results": rows, "diagnostics": diagnostics}

    def _extract_detail_video_data(self, page) -> Dict:
        """상세페이지에서 video/source/mp4/主图视频 후보를 최대한 넓게 추출합니다."""
        data = page.evaluate(r"""
        () => {
            const title =
                document.querySelector('h1')?.innerText ||
                document.querySelector('[class*="title"]')?.innerText ||
                document.querySelector('[class*="Title"]')?.innerText ||
                document.title ||
                '';

            const videos = Array.from(document.querySelectorAll('video')).map(v => ({
                src: v.currentSrc || v.src || v.getAttribute('src') || '',
                poster: v.poster || v.getAttribute('poster') || '',
                type: 'video'
            }));

            const sourceVideos = Array.from(document.querySelectorAll('source')).map(s => ({
                src: s.src || s.getAttribute('src') || '',
                poster: '',
                type: 'source'
            }));

            const hints = Array.from(document.querySelectorAll('a, div, button, span')).slice(0, 2200).map(el => {
                const raw = (el.innerText || el.getAttribute('aria-label') || el.title || '').trim();
                const link = el.tagName?.toLowerCase() === 'a' ? el : el.querySelector('a');
                const href = link ? (link.href || link.getAttribute('href') || '') : '';
                const img = el.querySelector('img');
                return {
                    text: raw.slice(0, 200),
                    href,
                    poster: img ? (img.src || img.getAttribute('data-src') || img.getAttribute('data-original') || '') : ''
                };
            }).filter(x => {
                const t = (x.text + ' ' + x.href).toLowerCase();
                return t.includes('视频') || t.includes('video') || t.includes('主图') || t.includes('实拍') || t.includes('买家秀');
            });

            const images = Array.from(document.querySelectorAll('img')).slice(0, 40).map(img => ({
                src: img.src || img.getAttribute('data-src') || img.getAttribute('data-original') || '',
                alt: img.alt || ''
            })).filter(x => x.src);

            return {
                title,
                videos,
                sourceVideos,
                hints,
                images,
                html: document.documentElement.innerHTML
            };
        }
        """) or {}

        candidates: List[Dict] = []

        for v in data.get("videos", []):
            src = (v.get("src") or "").strip()
            if src:
                candidates.append({
                    "src": self.normalize_url(src),
                    "poster": v.get("poster", ""),
                    "type": "video",
                })

        for v in data.get("sourceVideos", []):
            src = (v.get("src") or "").strip()
            if src:
                candidates.append({
                    "src": self.normalize_url(src),
                    "poster": v.get("poster", ""),
                    "type": "source",
                })

        html = data.get("html") or ""
        mp4s = re.findall(r"https?:[^\"'\\<>\s]+?\.mp4[^\"'\\<>\s]*", html)
        for src in mp4s:
            candidates.append({
                "src": self.normalize_url(src),
                "poster": "",
                "type": "html_mp4",
            })

        # 주석/이스케이프된 JSON 안의 mp4 대응
        escaped_mp4s = re.findall(r"https?:\\/\\/[^\"'<>\s]+?\.mp4[^\"'<>\s]*", html)
        for src in escaped_mp4s:
            candidates.append({
                "src": self.normalize_url(src.replace("\\/", "/")),
                "poster": "",
                "type": "escaped_html_mp4",
            })

        unique: List[Dict] = []
        seen = set()
        for item in candidates:
            src = item.get("src", "")
            if not src or src in seen:
                continue
            seen.add(src)
            unique.append(item)

        return {
            "title": data.get("title", ""),
            "videos": unique,
            "hints": data.get("hints", []),
            "images": data.get("images", []),
            "video_tag_count": len(data.get("videos", [])),
            "source_tag_count": len(data.get("sourceVideos", [])),
            "mp4_count": len(mp4s) + len(escaped_mp4s),
        }

    def _safe_title(self, page) -> str:
        try:
            return page.title()
        except Exception:
            return ""

