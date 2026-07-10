import json
import sys
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parents[1]
PROFILE_DIR = BASE_DIR / "browser_profile" / "source_sites"
EXPORT_DIR = BASE_DIR / "exports" / "source_candidates"

sys.path.insert(0, str(BASE_DIR))

from modules.source.source_collector import SourceCollector
from modules.studio.network.response_sniffer import ResponseSniffer


def detect_platform(url):
    host = urlparse(url).netloc.lower()

    if "taobao" in host or "tmall" in host:
        return "taobao"

    if "1688" in host:
        return "1688"

    if "tiktok" in host or "douyin" in host:
        return "tiktok"

    return "unknown"


def save_candidates(platform, candidates):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    path = EXPORT_DIR / f"{platform}_latest_candidates.json"
    path.write_text(
        json.dumps(candidates, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return path


def collect_source_candidates(url):
    platform = detect_platform(url)

    if platform == "unknown":
        print("[AutoCommerceAI] 지원하지 않는 플랫폼입니다:", url)
        return []

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            viewport={"width": 1440, "height": 1000},
            args=[
                "--no-first-run",
                "--no-default-browser-check",
            ],
        )

        page = context.new_page()

        sniffer = ResponseSniffer()
        sniffer.start(page)

        page.goto(url, wait_until="domcontentloaded", timeout=60000)

        try:
            page.wait_for_timeout(5000)
        except Exception:
            pass

        candidates = SourceCollector().top(
            page=page,
            platform=platform,
            limit=30,
        )

        saved_path = save_candidates(platform, candidates)
        response_log_path = sniffer.save()

        print("[AutoCommerceAI] 후보 수집 완료:", len(candidates))
        print("[AutoCommerceAI] 후보 저장 위치:", saved_path)
        print("[AutoCommerceAI] Response 로그 저장 위치:", response_log_path)

        return candidates


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[AutoCommerceAI] URL이 필요합니다.")
        sys.exit(1)

    collect_source_candidates(sys.argv[1])