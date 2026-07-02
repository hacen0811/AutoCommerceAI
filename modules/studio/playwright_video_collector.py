from __future__ import annotations

import json
import os
import re
import urllib.request
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlparse

try:
    from config.settings import EXPORTS_DIR
except Exception:
    EXPORTS_DIR = Path("exports")

from modules.studio.collectors.taobao_collector import TaobaoCollector
from modules.studio.collectors.alibaba1688_collector import Alibaba1688Collector
from modules.studio.collectors.tiktok_collector import TikTokCollector


PROFILE_DIR = Path("browser_profile/source_sites").resolve()


class PlaywrightVideoCollector:
    """Playwright live source collector + basic mp4 downloader."""

    def __init__(self, headless: bool = False, timeout_ms: int = 30000):
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.profile_dir = PROFILE_DIR

        self.out_dir = EXPORTS_DIR / "studio_video_sources_live"
        self.html_dir = self.out_dir / "html"
        self.shot_dir = self.out_dir / "screenshots"
        self.video_dir = EXPORTS_DIR / "videos"

        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.html_dir.mkdir(parents=True, exist_ok=True)
        self.shot_dir.mkdir(parents=True, exist_ok=True)
        self.video_dir.mkdir(parents=True, exist_ok=True)

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
            "message": "실제 웹 검색 수집이 켜져 있습니다. 전용 Playwright 프로필을 사용합니다."
            if enabled and installed
            else "Playwright 실제 수집이 준비되지 않았습니다.",
            "install_command": "python -m pip install playwright && python -m playwright install chromium",
            "enable_command": "RUN_LIVE_SOURCE.bat 또는 $env:AUTO_SOURCE_LIVE='1'",
            "login_tip": "python tools\\login_source_browser.py 실행 후 전용 브라우저에서 로그인하세요.",
            "profile_dir": str(self.profile_dir),
            "video_dir": str(self.video_dir),
        }

    def _is_direct_video_url(self, url: str) -> bool:
        u = (url or "").lower()
        return ".mp4" in u or ".mov" in u or ".webm" in u or ".m3u8" in u

    def _safe_filename(self, text: str, fallback: str = "video") -> str:
        text = (text or fallback).strip()
        text = re.sub(r"[\\/:*?\"<>|]+", "_", text)
        text = re.sub(r"\s+", "_", text)
        text = text[:80].strip("_")
        return text or fallback

    def _extension_from_url(self, url: str) -> str:
        u = (url or "").lower()
        if ".webm" in u:
            return ".webm"
        if ".mov" in u:
            return ".mov"
        if ".m3u8" in u:
            return ".m3u8"
        return ".mp4"

    def _download_video_url(self, url: str, title: str = "", platform: str = "") -> Dict:
        if not url:
            return {
                "ok": False,
                "path": "",
                "error": "URL 없음",
            }

        if ".m3u8" in url.lower():
            return {
                "ok": False,
                "path": "",
                "error": "m3u8 스트리밍 URL은 현재 직접 저장 대상이 아닙니다.",
            }

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = self._safe_filename(title or platform or "video")
        ext = self._extension_from_url(url)
        path = self.video_dir / f"{ts}_{platform}_{name}{ext}"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
            ),
            "Referer": "https://www.taobao.com/",
        }

        try:
            req = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(req, timeout=40) as response:
                content_type = response.headers.get("Content-Type", "")
                data = response.read()

            if not data or len(data) < 1024:
                return {
                    "ok": False,
                    "path": "",
                    "error": "다운로드 데이터가 너무 작습니다.",
                }

            path.write_bytes(data)

            return {
                "ok": True,
                "path": str(path),
                "error": "",
                "bytes": len(data),
                "content_type": content_type,
            }

        except Exception as exc:
            return {
                "ok": False,
                "path": "",
                "error": str(exc)[:800],
            }

    def _download_result_videos(self, rows: List) -> List:
        for row in rows:
            try:
                url = getattr(row, "url", "") or ""
                title = getattr(row, "title", "") or ""
                platform = getattr(row, "platform", "") or ""

                if not self._is_direct_video_url(url):
                    setattr(row, "downloaded", False)
                    setattr(row, "download_error", "직접 영상 URL이 아니라 다운로드 생략")
                    continue

                result = self._download_video_url(url, title=title, platform=platform)

                setattr(row, "downloaded", bool(result.get("ok")))
                setattr(row, "video_path", result.get("path", ""))
                setattr(row, "download_error", result.get("error", ""))

                if result.get("ok"):
                    old_note = getattr(row, "note", "") or ""
                    setattr(row, "note", old_note + f" / 자동 다운로드 완료: {result.get('path')}")

            except Exception as exc:
                try:
                    setattr(row, "downloaded", False)
                    setattr(row, "download_error", str(exc)[:800])
                except Exception:
                    pass

        return rows

    def collect(self, candidates: List[Dict], limit_per_platform: int = 6) -> Dict:
        st = self.status()
        started = datetime.now().isoformat(timespec="seconds")

        if not st.get("ready"):
            return {
                "ok": False,
                "status": st,
                "started_at": started,
                "finished_at": datetime.now().isoformat(timespec="seconds"),
                "results": [],
                "errors": [],
                "diagnostics": [],
                "message": st.get("message"),
            }

        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:
            return {
                "ok": False,
                "status": st,
                "results": [],
                "errors": [{"stage": "import_playwright", "error": str(exc)}],
                "diagnostics": [],
                "message": "Playwright import 실패",
            }

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
                        keyword = row.get("keyword") or row.get("query") or ""
                        url = row.get("search_url") or row.get("url") or ""
                        image_path = row.get("image_path") or ""

                        try:
                            pack = collector.collect(
                                page,
                                keyword,
                                url,
                                limit_per_platform,
                                image_path=image_path,
                            )
                            results.extend(pack.get("results", []))
                            diagnostics.append(pack.get("diagnostics", {}))

                        except TypeError:
                            pack = collector.collect(page, keyword, url, limit_per_platform)
                            results.extend(pack.get("results", []))
                            diagnostics.append(pack.get("diagnostics", {}))

                        except Exception as exc:
                            errors.append({
                                "platform": platform,
                                "keyword": keyword,
                                "url": url,
                                "error": str(exc)[:800],
                            })

            except Exception as exc:
                errors.append({
                    "stage": "launch_or_collect",
                    "error": str(exc)[:1000],
                })

            finally:
                if context:
                    try:
                        context.close()
                    except Exception:
                        pass

        downloaded_results = self._download_result_videos(results)

        seen = set()
        deduped = []

        for r in sorted(downloaded_results, key=lambda x: x.score, reverse=True):
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
            "download_summary": {
                "video_dir": str(self.video_dir),
                "downloaded_count": sum(1 for x in deduped if getattr(x, "downloaded", False)),
                "direct_video_count": sum(1 for x in deduped if self._is_direct_video_url(getattr(x, "url", ""))),
            },
            "message": "실제 검색 후보를 수집하고 영상 다운로드를 시도했습니다."
            if deduped
            else "검색 페이지 접근은 시도했지만 후보를 얻지 못했습니다. diagnostics/html/screenshot을 확인하세요.",
        }

        path = self.out_dir / f"live_video_sources_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

        out["save_path"] = str(path)
        return out