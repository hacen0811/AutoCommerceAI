from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List
from datetime import datetime


@dataclass
class CollectedVideo:
    platform: str
    title: str
    url: str
    keyword: str
    score: int
    source: str = "playwright-dom"
    thumbnail: str = ""
    screenshot: str = ""
    views: str = ""
    likes: str = ""
    duration: str = ""
    note: str = "실제 검색 화면 DOM에서 수집된 후보입니다."


class BaseSiteCollector:
    platform = "base"

    def __init__(self, html_dir: Path, shot_dir: Path, timeout_ms: int = 30000):
        self.html_dir = html_dir
        self.shot_dir = shot_dir
        self.timeout_ms = timeout_ms
        self.html_dir.mkdir(parents=True, exist_ok=True)
        self.shot_dir.mkdir(parents=True, exist_ok=True)

    def save_debug(self, page, platform: str) -> Dict:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = self.html_dir / f"{ts}_{platform}.html"
        shot_path = self.shot_dir / f"{ts}_{platform}.png"

        try:
            html_path.write_text(page.content(), encoding="utf-8")
        except Exception:
            html_path = Path("")

        try:
            page.screenshot(path=str(shot_path), full_page=True)
        except Exception:
            shot_path = Path("")

        return {
            "html": str(html_path) if html_path else "",
            "screenshot": str(shot_path) if shot_path else "",
        }

    def slow_scroll(self, page, count: int = 3) -> None:
        for _ in range(count):
            try:
                page.mouse.wheel(0, 2200)
                page.wait_for_timeout(1800)
            except Exception:
                break

    def body_text(self, page) -> str:
        try:
            return page.locator("body").inner_text(timeout=6000)[:8000]
        except Exception:
            return ""

    def blocked_hint(self, page, body_text: str = "") -> str:
        try:
            url = page.url.lower()
            title = page.title().lower()
        except Exception:
            url = ""
            title = ""
        t = f"{url}\n{title}\n{body_text}".lower()
        if any(x in t for x in ["captcha", "verify", "verification", "安全", "验证", "扫码", "登录", "login", "로봇", "로그인", "punish", "x5sec"]):
            return "로그인/보안 인증/캡차가 필요할 수 있습니다."
        return ""

    def normalize_url(self, href: str) -> str:
        return (href or "").strip()

    def is_junk_text(self, text: str, href: str = "") -> bool:
        t = (text or "").lower()
        h = (href or "").lower()
        junk = [
            "get app", "download", "open app", "login", "sign in", "signup",
            "协议", "用户协议", "隐私", "privacy", "service", "客服", "帮助",
            "about", "广告", "sponsor", "promotion", "client", "客户端",
            "精选", "terms", "policy", "cookie", "copyright",
        ]
        return any(x in t or x in h for x in junk)

    def score_item(self, keyword: str, title: str, href: str, thumb: str = "") -> int:
        text = f"{title}\n{href}"
        key_tokens = [t for t in re.split(r"\s+", keyword or "") if len(t) >= 2]
        score = 20
        if thumb:
            score += 20
        score += sum(10 for t in key_tokens if t in text)
        if any(w in text for w in ["视频", "实拍", "开箱", "推荐", "好物", "후기", "리뷰", "사용", "수납", "정리", "収納", "主图视频", "买家秀"]):
            score += 25
        if any(w in href.lower() for w in ["video", "aweme", "item", "detail", "offer", "product"]):
            score += 30
        return min(score, 99)

    def dedupe(self, rows: List[CollectedVideo], limit: int = 10) -> List[CollectedVideo]:
        seen = set()
        out = []
        for r in sorted(rows, key=lambda x: x.score, reverse=True):
            key = re.sub(r"[?#].*$", "", r.url)
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(r)
        return out[:limit]

    def to_dicts(self, rows: List[CollectedVideo]) -> List[Dict]:
        return [asdict(x) for x in rows]
