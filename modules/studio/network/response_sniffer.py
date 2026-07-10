from __future__ import annotations

import json
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class ResponseSniffer:
    """
    Playwright page response 수집기.

    역할:
    - page.on("response") 연결
    - API 응답 URL / status / method / headers / body 수집
    - JSON 응답 우선 저장
    - 최근 N개만 유지
    - response_log.json 저장
    """

    DEFAULT_KEYWORDS = [
        "api",
        "search",
        "mtop",
        "detail",
        "item",
        "recommend",
        "feed",
        "aweme",
        "video",
        "goods",
        "product",
    ]

    def __init__(
        self,
        log_path: str | Path = "exports/network/response_log.json",
        max_items: int = 300,
        keywords: Optional[List[str]] = None,
        max_body_chars: int = 200_000,
    ):
        self.log_path = Path(log_path)
        self.max_items = max_items
        self.keywords = keywords or self.DEFAULT_KEYWORDS
        self.max_body_chars = max_body_chars
        self.responses = deque(maxlen=max_items)
        self.enabled = False

    def start(self, page) -> None:
        """
        Playwright page에 response listener 연결.
        """
        if not page:
            return

        self.enabled = True
        page.on("response", self._handle_response)

    async def start_async(self, page) -> None:
        """
        async Playwright용 시작 함수.
        """
        if not page:
            return

        self.enabled = True
        page.on("response", self._handle_response_async)

    def stop(self) -> None:
        self.enabled = False

    def _match_url(self, url: str) -> bool:
        if not url:
            return False

        lower_url = url.lower()
        return any(keyword.lower() in lower_url for keyword in self.keywords)

    def _safe_headers(self, response) -> Dict[str, Any]:
        try:
            return dict(response.headers)
        except Exception:
            return {}

    def _safe_method(self, response) -> str:
        try:
            return response.request.method
        except Exception:
            return ""

    def _content_type(self, headers: Dict[str, Any]) -> str:
        return (
            headers.get("content-type")
            or headers.get("Content-Type")
            or ""
        )

    def _trim_body(self, body: Any) -> Any:
        if isinstance(body, str) and len(body) > self.max_body_chars:
            return body[: self.max_body_chars] + "\n...[TRIMMED]"

        return body

    def _record(self, item: Dict[str, Any]) -> None:
        self.responses.append(item)
        self.save()

    def _handle_response(self, response) -> None:
        """
        sync Playwright response handler.
        """
        if not self.enabled:
            return

        try:
            url = response.url

            if not self._match_url(url):
                return

            headers = self._safe_headers(response)
            content_type = self._content_type(headers)

            body = None
            body_type = "empty"

            try:
                if "application/json" in content_type or "json" in content_type:
                    body = response.json()
                    body_type = "json"
                else:
                    body = response.text()
                    body_type = "text"
            except Exception as e:
                body = f"BODY_READ_FAILED: {e}"
                body_type = "error"

            item = {
                "captured_at": datetime.now().isoformat(timespec="seconds"),
                "url": url,
                "status": response.status,
                "method": self._safe_method(response),
                "content_type": content_type,
                "headers": headers,
                "body_type": body_type,
                "body": self._trim_body(body),
            }

            self._record(item)

        except Exception:
            return

    async def _handle_response_async(self, response) -> None:
        """
        async Playwright response handler.
        """
        if not self.enabled:
            return

        try:
            url = response.url

            if not self._match_url(url):
                return

            headers = self._safe_headers(response)
            content_type = self._content_type(headers)

            body = None
            body_type = "empty"

            try:
                if "application/json" in content_type or "json" in content_type:
                    body = await response.json()
                    body_type = "json"
                else:
                    body = await response.text()
                    body_type = "text"
            except Exception as e:
                body = f"BODY_READ_FAILED: {e}"
                body_type = "error"

            item = {
                "captured_at": datetime.now().isoformat(timespec="seconds"),
                "url": url,
                "status": response.status,
                "method": self._safe_method(response),
                "content_type": content_type,
                "headers": headers,
                "body_type": body_type,
                "body": self._trim_body(body),
            }

            self._record(item)

        except Exception:
            return

    def latest(self, limit: int = 20) -> List[Dict[str, Any]]:
        items = list(self.responses)
        return items[-limit:]

    def all(self) -> List[Dict[str, Any]]:
        return list(self.responses)

    def save(self) -> Path:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "version": "sprint53-response-sniffer-1.0",
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "count": len(self.responses),
            "items": list(self.responses),
        }

        self.log_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return self.log_path