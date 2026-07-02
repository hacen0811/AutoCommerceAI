from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List

try:
    from config.settings import EXPORTS_DIR
except Exception:
    EXPORTS_DIR = Path("exports")

from modules.studio.collectors.taobao_collector import TaobaoCollector
from modules.studio.collectors.alibaba1688_collector import Alibaba1688Collector
from modules.studio.collectors.tiktok_collector import TikTokCollector


PROFILE_DIR = Path("browser_profile/source_sites").resolve()


class PlaywrightVideoCollector:
    """Sprint 6-4 image-first collector. Douyin is excluded by default."""

    def __init__(self, headless: bool = False, timeout_ms: int = 30000):
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.profile_dir = PROFILE_DIR
        self.out_dir = EXPORTS_DIR / "studio_video_sources_live"
        self.html_dir = self.out_dir / "html"
        self.shot_dir = self.out_dir / "screenshots"
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.html_dir.mkdir(parents=True, exist_ok=True)
        self.shot_dir.mkdir(parents=True, exist_ok=True)

    def status(self) -> Dict:
        try:
            import playwright  # noqa
            installed = True
        except Exception:
            installed = False
        enabled = os.getenv("AUTO_SOURCE_LIVE", "0").strip() == "1"
        return {
            "enabled": enabled,
            "playwright_python_installed": installed,
            "ready": enabled and installed,
            "message": "실제 웹 검색 수집이 켜져 있습니다. 전용 Playwright 프로필을 사용합니다." if enabled and installed else "Playwright 실제 수집이 준비되지 않았습니다.",
            "install_command": "python -m pip install playwright && python -m playwright install chromium",
            "enable_command": "RUN_LIVE_SOURCE.bat 또는 $env:AUTO_SOURCE_LIVE='1'",
            "login_tip": "python tools\\login_source_browser.py 실행 후 전용 브라우저에서 로그인하세요.",
            "profile_dir": str(self.profile_dir),
        }

    def collect(self, candidates: List[Dict], limit_per_platform: int = 6) -> Dict:
        st = self.status()
        started = datetime.now().isoformat(timespec="seconds")
        if not st.get("ready"):
            return {"ok": False, "status": st, "started_at": started, "finished_at": datetime.now().isoformat(timespec="seconds"), "results": [], "errors": [], "diagnostics": [], "message": st.get("message")}

        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:
            return {"ok": False, "status": st, "results": [], "errors": [{"stage": "import_playwright", "error": str(exc)}], "diagnostics": [], "message": "Playwright import 실패"}

        by_platform: Dict[str, List[Dict]] = {}
        for c in candidates or []:
            platform = str(c.get("platform", "")).lower().strip()
            if platform in {"taobao", "1688", "tiktok"}:
                by_platform.setdefault(platform, []).append(c)

        results = []
        errors = []
        diagnostics = []
        self.profile_dir.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as pw:
            context = None
            try:
                context = pw.chromium.launch_persistent_context(
                    user_data_dir=str(self.profile_dir),
                    headless=self.headless,
                    viewport={"width": 1280, "height": 900},
                    locale="ko-KR",
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
                    ),
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-first-run",
                        "--no-default-browser-check",
                    ],
                )

                page = context.pages[0] if context.pages else context.new_page()
                page.set_default_timeout(self.timeout_ms)

                collector_map = {
                    "taobao": TaobaoCollector(self.html_dir, self.shot_dir, self.timeout_ms),
                    "1688": Alibaba1688Collector(self.html_dir, self.shot_dir, self.timeout_ms),
                    "tiktok": TikTokCollector(self.html_dir, self.shot_dir, self.timeout_ms),
                }

                for platform, rows in by_platform.items():
                    collector = collector_map.get(platform)
                    if not collector:
                        continue
                    for row in rows[:2]:
                        keyword = row.get("keyword") or ""
                        url = row.get("search_url") or ""
                        image_path = row.get("image_path") or ""
                        try:
                            pack = collector.collect(page, keyword, url, limit_per_platform, image_path=image_path)
                            results.extend(pack.get("results", []))
                            diagnostics.append(pack.get("diagnostics", {}))
                        except TypeError:
                            pack = collector.collect(page, keyword, url, limit_per_platform)
                            results.extend(pack.get("results", []))
                            diagnostics.append(pack.get("diagnostics", {}))
                        except Exception as exc:
                            errors.append({"platform": platform, "keyword": keyword, "url": url, "error": str(exc)[:800]})
            except Exception as exc:
                errors.append({"stage": "launch_or_collect", "error": str(exc)[:1000]})
            finally:
                if context:
                    try:
                        context.close()
                    except Exception:
                        pass

        seen = set()
        deduped = []
        for r in sorted(results, key=lambda x: x.score, reverse=True):
            key = (r.url or "").split("?")[0].split("#")[0]
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(r)

        out = {
            "ok": bool(deduped),
            "status": st,
            "started_at": started,
            "finished_at": datetime.now().isoformat(timespec="seconds"),
            "results": [asdict(x) for x in deduped[:30]],
            "errors": errors,
            "diagnostics": diagnostics,
            "message": "실제 검색 후보를 수집했습니다." if deduped else "검색 페이지 접근은 시도했지만 후보를 얻지 못했습니다. diagnostics/html/screenshot을 확인하세요.",
        }

        path = self.out_dir / f"live_video_sources_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        out["save_path"] = str(path)
        return out
