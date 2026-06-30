from playwright.sync_api import sync_playwright

print("Playwright 테스트 시작")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://example.com", wait_until="domcontentloaded", timeout=15000)
    print("페이지 제목:", page.title())
    browser.close()
print("Playwright 정상 작동")
