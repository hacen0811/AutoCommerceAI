from __future__ import annotations

import os
import re
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List

try:
    from config.settings import EXPORTS_DIR
except Exception:  # pragma: no cover
    EXPORTS_DIR = Path("exports")


@dataclass
class LiveVideoResult:
    platform: str
    title: str
    url: str
    keyword: str
    score: int
    source: str = "playwright-dom"
    thumbnail: str = ""
    screenshot: str = ""
    note: str = "실제 검색 화면 DOM에서 수집된 후보입니다. 로그인/차단 상태에 따라 결과가 비어 있을 수 있습니다."


class PlaywrightVideoCollector:
    """Live DOM collector for Douyin/Taobao/1688.

    It is intentionally safe: if a site blocks access or Playwright is missing,
    the app returns diagnostics instead of crashing.
    """

    def __init__(self, headless: bool = False, timeout_ms: int = 18000):
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.out_dir = EXPORTS_DIR / "studio_video_sources_live"
        self.shot_dir = self.out_dir / "screenshots"
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.shot_dir.mkdir(parents=True, exist_ok=True)
        self.profile_dir = Path("browser_profile/source_sites").resolve()

    def status(self) -> Dict:
        try:
            import playwright  # noqa: F401
            installed = True
        except Exception:
            installed = False
        enabled = os.getenv("AUTO_SOURCE_LIVE", "0").strip() == "1"
        return {
            "enabled": enabled,
            "playwright_python_installed": installed,
            "ready": enabled and installed,
            "message": self._status_message(enabled, installed),
            "install_command": "python -m pip install playwright && python -m playwright install chromium",
            "enable_command": "RUN_LIVE_SOURCE.bat 또는 화면의 실제 웹 수집 체크박스 사용",
            "login_tip": "LOGIN_SOURCE_BROWSER.bat로 브라우저를 열어 로그인한 뒤 다시 실행하세요.",
            "profile_dir": str(self.profile_dir),
        }

    def _status_message(self, enabled: bool, installed: bool) -> str:
        if not installed:
            return "Playwright가 설치되지 않았습니다. INSTALL_PLAYWRIGHT.bat 또는 python -m pip install playwright 실행이 필요합니다."
        if not enabled:
            return "Playwright는 설치되어 있지만 실제 웹 수집은 꺼져 있습니다. 화면 체크박스 또는 RUN_LIVE_SOURCE.bat로 켤 수 있습니다."
        return "실제 웹 검색 수집이 켜져 있습니다. 사이트 로그인/차단 여부에 따라 결과가 달라질 수 있습니다."

    def collect(self, candidates: List[Dict], limit_per_platform: int = 5) -> Dict:
        st = self.status()
        if not st.get("ready"):
            return {"ok": False, "status": st, "results": [], "message": st.get("message")}

        try:
            from playwright.sync_api import sync_playwright
        except Exception as e:
            st["error"] = str(e)
            return {"ok": False, "status": st, "results": [], "message": "Playwright import 실패"}

        by_platform: Dict[str, List[Dict]] = {}
        for c in candidates:
            platform = c.get("platform", "unknown")
            if platform in {"douyin", "taobao", "1688"}:
                by_platform.setdefault(platform, []).append(c)

        results: List[LiveVideoResult] = []
        errors: List[Dict] = []
        diagnostics: List[Dict] = []
        started = datetime.now().isoformat(timespec="seconds")

        with sync_playwright() as pw:
            self.profile_dir.mkdir(parents=True, exist_ok=True)
            context = pw.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_dir),
                headless=self.headless,
                viewport={"width": 1280, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
                ),
                locale="ko-KR",
            )
            page = context.new_page()
            page.set_default_timeout(self.timeout_ms)

            for platform, rows in by_platform.items():
                for row in rows[:2]:
                    url = row.get("search_url") or ""
                    keyword = row.get("keyword") or ""
                    if not url:
                        continue
                    shot = str(self.shot_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{platform}.png")
                    try:
                        page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                        page.wait_for_timeout(3500)
                        try:
                            page.screenshot(path=shot, full_page=True)
                        except Exception:
                            shot = ""
                        title = page.title()
                        current_url = page.url
                        body_text = ""
                        try:
                            body_text = page.locator("body").inner_text(timeout=5000)[:5000]
                        except Exception:
                            pass
                        anchors = page.locator("a").evaluate_all(
                            """els => els.slice(0, 220).map(a => {
                                const img = a.querySelector('img');
                                const parent = a.closest('div, li, section, article') || a;
                                const text = (a.innerText || a.getAttribute('aria-label') || a.title || '').trim();
                                const parentText = (parent.innerText || '').trim();

                                return {
                                            text: text,
                                    href: a.href || '',
                                    img: img ? (img.src || img.getAttribute('data-src') || img.getAttribute('data-original') || '') : '',
                                    thumbnail_url: img ? (img.src || img.getAttribute('data-src') || img.getAttribute('data-original') || '') : '',
                                    title: text || parentText.split('\\n')[0] || '',
                                    raw_text: parentText,
                                    author: '',
                                    duration: '',
                                    views: '',
                                    likes: '',
                                    platform_hint: location.hostname
                                };
                        })"""
)
                                  
                        extracted = self._score_links(platform, keyword, anchors, body_text, shot, limit_per_platform)
                        results.extend(extracted)
                        diagnostics.append({
                            "platform": platform,
                            "keyword": keyword,
                            "requested_url": url,
                            "current_url": current_url,
                            "page_title": title,
                            "anchor_count": len(anchors),
                            "extracted_count": len(extracted),
                            "screenshot": shot,
                            "blocked_hint": self._blocked_hint(body_text, current_url),
                        })
                    except Exception as e:
                        errors.append({"platform": platform, "keyword": keyword, "url": url, "error": str(e)[:500], "screenshot": shot})
            context.close()

        deduped = self._dedupe(results)
        out = {
            "ok": bool(deduped),
            "status": st,
            "started_at": started,
            "finished_at": datetime.now().isoformat(timespec="seconds"),
            "results": [asdict(x) for x in deduped],
            "errors": errors,
            "diagnostics": diagnostics,
            "message": "실제 검색 후보를 수집했습니다." if deduped else "검색 페이지 접근은 시도했지만 후보를 얻지 못했습니다. 로그인/차단/지역 제한일 수 있습니다.",
        }
        path = self.out_dir / f"live_video_sources_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        out["save_path"] = str(path)
        return out

    def _blocked_hint(self, text: str, url: str) -> str:
        t = (text or "")[:3000]
        if any(x in t for x in ["登录", "扫码", "验证", "安全", "captcha", "로봇", "로그인"]):
            return "로그인/보안 인증이 필요할 수 있습니다. LOGIN_SOURCE_BROWSER.bat로 로그인 후 재시도하세요."
        if "login" in (url or "").lower():
            return "로그인 페이지로 이동했습니다."
        return ""

    def _score_links(self, platform: str, keyword: str, anchors: List[Dict], body_text: str, screenshot: str, limit: int) -> List[LiveVideoResult]:
        rows: List[LiveVideoResult] = []
        key_tokens = [t for t in re.split(r"\s+", keyword) if len(t) >= 2]
        for a in anchors:
            text = (a.get("text") or "").strip()
            href = (a.get("href") or "").strip()
            img = (a.get("img") or "").strip()
            if not self._allowed_link(platform, href):
                continue
            if self._junk_link(platform, href, text):
                continue
            score = 55
            lower_href = href.lower()
            score += sum(5 for t in key_tokens if t and (t in text or t in href))
            if any(w in text for w in ["视频", "实拍", "开箱", "推荐", "好物", "후기", "리뷰", "사용", "수납"]):
                score += 18
            if any(w in lower_href for w in ["video", "aweme", "item", "detail", "offer", "product"]):
                score += 12
            if img:
                score += 5
            title = text[:100] or f"{platform} 후보 링크"
            rows.append(LiveVideoResult(platform=platform, title=title, url=href, keyword=keyword, score=min(score, 99), thumbnail=img, screenshot=screenshot))
        rows.sort(key=lambda r: r.score, reverse=True)
        return rows[:limit]

    def _allowed_link(self, platform: str, href: str) -> bool:
        if not href or href.startswith("javascript") or href.startswith("mailto:"):
            return False
        h = href.lower()
        if platform == "douyin":
            return "douyin.com" in h and any(x in h for x in ["/video/", "/note/", "/user/", "modal_id=", "aweme"])
        if platform == "taobao":
            return any(d in h for d in ["item.taobao.com", "detail.tmall.com", "world.taobao.com/item"])
        if platform == "1688":
            return "1688.com" in h and ("offer/" in h or "detail" in h)
        return False

    def _junk_link(self, platform: str, href: str, text: str) -> bool:
        h = href.lower()
        junk = ["login", "passport", "buyer", "seller", "cart", "order", "trade", "member", "help", "notice", "feedback", "download"]
        if any(j in h for j in junk):
            return True
        if platform == "douyin" and ("/search/" in h and "/video/" not in h and "modal_id=" not in h):
            return True
        if len((text or "").strip()) <= 1 and not any(x in h for x in ["item", "offer", "video", "aweme"]):
            return True
        return False

    def _dedupe(self, rows: List[LiveVideoResult]) -> List[LiveVideoResult]:
        seen = set()
        out = []
        for r in sorted(rows, key=lambda x: x.score, reverse=True):
            key = re.sub(r"[?#].*$", "", r.url)
            if key in seen:
                continue
            seen.add(key)
            out.append(r)
        return out[:30]
