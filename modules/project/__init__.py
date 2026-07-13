from __future__ import annotations

from typing import Any, Dict, Optional

from .captcha_detector import CaptchaDetector
from .chrome_profile_manager import ChromeProfileManager


class TikTokSessionManager:
    """
    Sprint69 TikTok Session Manager

    - 프로젝트 전용 지속 Chrome 프로필
    - CAPTCHA 감지
    - 사용자 직접 인증
    - 인증 완료 후 자동 재개
    """

    VERSION = "tiktok-session-manager-69-2"

    def __init__(
        self,
        profile_manager: Optional[ChromeProfileManager] = None,
        captcha_detector: Optional[CaptchaDetector] = None,
    ) -> None:
        self.profile_manager = profile_manager or ChromeProfileManager()
        self.captcha_detector = captcha_detector or CaptchaDetector()

    def open(
        self,
        playwright,
        *,
        headless: bool = False,
        timeout: int = 20,
    ):
        context = self.profile_manager.launch_context(
            playwright,
            headless=headless,
            timeout=timeout,
        )

        pages = list(context.pages or [])
        page = pages[-1] if pages else context.new_page()
        page.set_default_timeout(max(15000, int(timeout or 20) * 1000))
        return context, page

    def wait_for_manual_verification(
        self,
        page,
        *,
        max_wait_seconds: int = 120,
        poll_seconds: float = 2.0,
    ) -> Dict[str, Any]:
        first = self.captcha_detector.detect(page)

        if first.get("detected"):
            print(
                "\n[TikTok] 사용자 인증이 필요합니다.\n"
                "열린 Chrome 창에서 클릭 또는 퍼즐 인증을 직접 완료해 주세요.\n"
                f"최대 {max_wait_seconds}초 동안 자동으로 기다립니다.\n",
                flush=True,
            )

        result = self.captcha_detector.wait_until_clear(
            page,
            timeout_seconds=max_wait_seconds,
            poll_seconds=poll_seconds,
        )
        result["version"] = self.VERSION
        return result

