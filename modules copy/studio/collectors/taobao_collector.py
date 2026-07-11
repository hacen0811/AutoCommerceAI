from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List
from datetime import datetime



@dataclass
class CapturedMedia:
    url: str
    media_type: str
    content_type: str = ""
    status: int = 0
    source: str = "network-response"
    captured_at: str = ""
    note: str = ""


class ResponseSniffer:
    """
    Sprint 53
    Playwright response 감시용 네트워크 스니퍼.

    목적:
    - DOM에서 video 태그를 못 찾는 경우
    - 네트워크 응답에서 mp4 / m3u8 / video API 후보를 잡는다.
    """

    VIDEO_HINTS = [
        ".mp4",
        ".webm",
        ".mov",
        ".m3u8",
        "video",
        "aweme",
        "play",
        "stream",
        "media",
    ]

    JUNK_HINTS = [
        ".css",
        ".js",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".woff",
        ".ttf",
        "analytics",
        "tracking",
        "log",
        "beacon",
    ]

    def __init__(self):
        self.items: List[CapturedMedia] = []
        self.errors: List[str] = []
        self.started_at = datetime.now().isoformat(timespec="seconds")

    def attach(self, page):
        page.on("response", self._handle_response)
        return self

    def _handle_response(self, response):
        try:
            url = response.url or ""
            lower = url.lower()

            if not url:
                return

            if any(x in lower for x in self.JUNK_HINTS):
                return

            content_type = ""
            try:
                content_type = response.headers.get("content-type", "")
            except Exception:
                content_type = ""

            content_lower = content_type.lower()

            is_media = (
                any(x in lower for x in self.VIDEO_HINTS)
                or "video" in content_lower
                or "mpegurl" in content_lower
                or "octet-stream" in content_lower
            )

            if not is_media:
                return

            self.items.append(
                CapturedMedia(
                    url=url,
                    media_type=self.detect_media_type(url, content_type),
                    content_type=content_type,
                    status=getattr(response, "status", 0),
                    captured_at=datetime.now().isoformat(timespec="seconds"),
                    note="Playwright response에서 감지된 영상/미디어 후보입니다.",
                )
            )

        except Exception as exc:
            self.errors.append(str(exc)[:300])

    def detect_media_type(self, url: str, content_type: str = "") -> str:
        lower = (url or "").lower()
        ct = (content_type or "").lower()

        if ".mp4" in lower or "mp4" in ct:
            return "mp4"

        if ".m3u8" in lower or "mpegurl" in ct:
            return "m3u8"

        if ".webm" in lower or "webm" in ct:
            return "webm"

        if ".mov" in lower or "quicktime" in ct:
            return "mov"

        if "video" in lower or "video" in ct:
            return "video-api"

        if "aweme" in lower:
            return "aweme"

        return "media"

    def results(self, limit: int = 30) -> List[Dict]:
        seen = set()
        out = []

        for item in self.items:
            key = item.url.split("#")[0]

            if key in seen:
                continue

            seen.add(key)
            out.append(asdict(item))

            if len(out) >= limit:
                break

        return out

    def summary(self) -> Dict:
        return {
            "ok": bool(self.items),
            "started_at": self.started_at,
            "captured_count": len(self.items),
            "unique_count": len(self.results(999)),
            "errors": self.errors[:5],
        }