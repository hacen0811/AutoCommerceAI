from playwright.sync_api import sync_playwright
from modules.social import TikTokSessionManager


def main():
    with sync_playwright() as playwright:
        context = None

        try:
            manager = TikTokSessionManager()

            context, page = manager.open(
                playwright,
                headless=False,
                timeout=30,
            )

            page.goto(
                "https://www.tiktok.com/",
                wait_until="domcontentloaded",
                timeout=60000,
            )

            print("TikTok 화면이 열렸습니다.")
            print("로그인을 완료한 뒤 PowerShell에서 Enter를 누르세요.")

            input()

        except Exception as exc:
            print("ERROR:", exc)

        finally:
            if context is not None:
                try:
                    context.close()
                except Exception:
                    pass


if __name__ == "__main__":
    main()