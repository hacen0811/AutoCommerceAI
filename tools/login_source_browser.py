from pathlib import Path
from playwright.sync_api import sync_playwright
import time

PROFILE_DIR = Path("browser_profile/source_sites").resolve()

LOGIN_URLS = [
    ("TikTok", "https://www.tiktok.com/"),
    ("Douyin", "https://www.douyin.com/"),
    ("Taobao", "https://login.taobao.com/"),
    ("1688", "https://login.1688.com/"),
]

def main() -> None:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    print("[AutoCommerceAI] 로그인 브라우저 실행")
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

        first_page = context.pages[0] if context.pages else context.new_page()

        for index, (name, url) in enumerate(LOGIN_URLS):
            page = first_page if index == 0 else context.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                print(f"[OK] {name}: {url}")
            except Exception as exc:
                print(f"[WARN] {name} 열기 실패: {exc}")

        print("로그인/확인이 끝났다면 브라우저를 직접 닫으세요.")
        print("브라우저가 닫히면 세션 저장 후 종료됩니다.")

        while context.pages:
            time.sleep(1)

        context.close()

if __name__ == "__main__":
    main()