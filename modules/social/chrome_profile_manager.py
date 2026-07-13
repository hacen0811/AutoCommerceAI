from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


class ChromeProfileManager:
    """
    Sprint69 Chrome Profile Manager

    개인 Chrome 기본 프로필이 아닌 프로젝트 전용 지속 프로필을 사용합니다.
    """

    VERSION = "chrome-profile-manager-69-2"

    def __init__(
        self,
        profile_dir: str | Path = "profiles/tiktok_profile",
    ) -> None:
        self.profile_dir = Path(profile_dir)
        self.profile_dir.mkdir(parents=True, exist_ok=True)

    def launch_context(
        self,
        playwright,
        *,
        headless: bool = False,
        timeout: int = 20,
    ):
        args = [
            "--no-first-run",
            "--no-default-browser-check",
            "--start-maximized",
        ]

        try:
            return playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_dir.resolve()),
                channel="chrome",
                headless=headless,
                viewport={"width": 1440, "height": 1000},
                locale="ko-KR",
                args=args,
                timeout=max(30000, int(timeout or 20) * 1000),
            )
        except Exception as exc:
            raise RuntimeError(
                "TikTok 지속 프로필 Chrome 실행에 실패했습니다. "
                "같은 프로필을 사용하는 Chrome 창이 열려 있다면 닫고 다시 실행해 주세요. "
                f"원인: {exc}"
            ) from exc

    def get_profile_info(self) -> Dict[str, Any]:
        return {
            "version": self.VERSION,
            "profile_dir": str(self.profile_dir),
            "profile_exists": self.profile_dir.exists(),
        }
