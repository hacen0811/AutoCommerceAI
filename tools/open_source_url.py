import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parents[1]
PROFILE_DIR = BASE_DIR / "browser_profile" / "source_sites"


def open_source_url(url):
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    print("[AutoCommerceAI] URL 브라우저 실행")
    print("전용 프로필:", PROFILE_DIR)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            viewport={"width": 1280, "height": 900},
            locale="ko-KR",
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
            ],
        )

        page = context.pages[0] if context.pages else context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=45000)

        while context.pages:
            time.sleep(1)

        context.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("URL이 필요합니다.")
        sys.exit(1)

    open_source_url(sys.argv[1])