from playwright.sync_api import sync_playwright


def download_html(url: str) -> dict:
    result = {
        "success": False,
        "status_code": None,
        "html": "",
        "message": "",
    }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/137.0 Safari/537.36"
                ),
                locale="ko-KR",
            )

            response = page.goto(url, wait_until="domcontentloaded", timeout=30000)

            if response:
                result["status_code"] = response.status

            page.wait_for_timeout(3000)

            html = page.content()
            browser.close()

            if html:
                result["success"] = True
                result["html"] = html
                result["message"] = "Playwright HTML 다운로드 성공"
            else:
                result["message"] = "HTML 내용이 비어 있습니다."

    except Exception as e:
        result["message"] = str(e)

    return result