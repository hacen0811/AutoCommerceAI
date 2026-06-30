from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except Exception as e:
    print('Playwright가 설치되어 있지 않습니다.')
    print('먼저 INSTALL_LIVE_SOURCE.bat를 실행하세요.')
    print(e)
    raise SystemExit(1)

user_data_dir = Path('browser_profile/source_login').resolve()
user_data_dir.mkdir(parents=True, exist_ok=True)

print('브라우저 프로필:', user_data_dir)
print('열리는 브라우저에서 필요한 사이트에 로그인/접속 확인 후 창을 닫으세요.')

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=str(user_data_dir),
        headless=False,
        viewport={'width': 1280, 'height': 900},
        locale='ko-KR',
    )
    page = context.new_page()
    page.goto('https://www.douyin.com/search/%E5%8E%A8%E6%88%BF%20%E6%94%B6%E7%BA%B3', wait_until='domcontentloaded', timeout=30000)
    print('브라우저가 열렸습니다. 로그인이 필요하면 직접 로그인하세요.')
    try:
        page.wait_for_timeout(300000)
    finally:
        context.close()
