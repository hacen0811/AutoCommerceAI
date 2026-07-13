from __future__ import annotations

import time
from typing import Any, Dict


class CaptchaDetector:
    """
    Sprint69 CAPTCHA Detector

    CAPTCHA를 우회하지 않습니다.
    화면의 인증 문구를 감지하고 사용자의 직접 해결을 기다립니다.
    """

    VERSION = "captcha-detector-69-2"

    KEYWORDS = (
        "verify to continue",
        "click to continue",
        "drag the puzzle",
        "complete the puzzle",
        "captcha",
        "security verification",
        "확인하려면 클릭",
        "인증을 완료",
        "보안 확인",
        "그림을 맞춰",
        "퍼즐",
        "验证",
        "请完成验证",
        "滑动",
        "拼图",
        "安全验证",
    )

    def detect(self, page) -> Dict[str, Any]:
        title = ""
        body = ""

        try:
            title = str(page.title() or "")
        except Exception:
            pass

        try:
            body = str(page.locator("body").inner_text(timeout=5000) or "")
        except Exception:
            pass

        lowered = f"{title}\n{body}".lower()
        matched = [
            keyword
            for keyword in self.KEYWORDS
            if keyword.lower() in lowered
        ]

        return {
            "version": self.VERSION,
            "detected": bool(matched),
            "matched_keywords": matched,
            "page_title": title,
        }

    def is_clear(self, page) -> bool:
        return not self.detect(page).get("detected", False)

    def wait_until_clear(
        self,
        page,
        *,
        timeout_seconds: int = 120,
        poll_seconds: float = 2.0,
    ) -> Dict[str, Any]:
        first = self.detect(page)

        if not first.get("detected"):
            return {
                "version": self.VERSION,
                "required": False,
                "resolved": True,
                "waited_seconds": 0,
                "matched_keywords": [],
                "error": "",
            }

        started = time.time()

        while True:
            waited = int(time.time() - started)

            if waited >= max(1, int(timeout_seconds or 120)):
                return {
                    "version": self.VERSION,
                    "required": True,
                    "resolved": False,
                    "waited_seconds": waited,
                    "matched_keywords": first.get("matched_keywords", []),
                    "error": "사용자 인증 대기 시간이 초과되었습니다.",
                }

            try:
                if page.is_closed():
                    return {
                        "version": self.VERSION,
                        "required": True,
                        "resolved": False,
                        "waited_seconds": waited,
                        "matched_keywords": first.get("matched_keywords", []),
                        "error": "인증 대기 중 페이지가 닫혔습니다.",
                    }
            except Exception:
                return {
                    "version": self.VERSION,
                    "required": True,
                    "resolved": False,
                    "waited_seconds": waited,
                    "matched_keywords": first.get("matched_keywords", []),
                    "error": "인증 페이지 상태를 확인하지 못했습니다.",
                }

            time.sleep(max(0.5, float(poll_seconds or 2.0)))

            current = self.detect(page)
            if not current.get("detected"):
                return {
                    "version": self.VERSION,
                    "required": True,
                    "resolved": True,
                    "waited_seconds": int(time.time() - started),
                    "matched_keywords": first.get("matched_keywords", []),
                    "error": "",
                }
