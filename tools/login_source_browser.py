from pathlib import Path
from playwright.sync_api import sync_playwright

profile = Path("browser_profile/source_sites").resolve()
profile.mkdir(parents=True, exist_ok=True)
print("로그인 브라우저를 엽니다.")
print("도우인/타오바오/1688에 필요한 경우 로그인한 뒤 브라우저를 닫으세요.")
print("프로필 저장 위치:", profile)
with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=str(profile),
        headless=False,
        viewport={"width": 1280, "height": 900},
        locale="ko-KR",
    )
    page = context.new_page()
    page.goto("https://www.douyin.com/", wait_until="domcontentloaded", timeout=30000)
    input("로그인을 마쳤으면 Enter를 누르세요... ")
    context.close()
