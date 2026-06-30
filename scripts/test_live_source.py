from pathlib import Path
import sys

print('Python:', sys.version)
print('Project folder:', Path.cwd())
try:
    import playwright  # noqa
    print('Playwright Python: OK')
except Exception as e:
    print('Playwright Python: NOT INSTALLED')
    print(e)
    print('\n실행하세요: python -m pip install playwright')
    raise SystemExit(1)

try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://example.com', wait_until='domcontentloaded', timeout=15000)
        print('Chromium launch: OK')
        print('Page title:', page.title())
        browser.close()
except Exception as e:
    print('Chromium launch: FAIL')
    print(e)
    print('\n실행하세요: python -m playwright install chromium')
    raise SystemExit(1)

print('\nLive Source 준비 완료')
