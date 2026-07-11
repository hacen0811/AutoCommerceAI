from __future__ import annotations

import json
import re
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class ResponseSniffer:
    """
    Sprint 57 Response Sniffer

    역할:
    - Playwright response 이벤트 연결
    - API 응답 URL, 상태, 헤더, 본문 저장
    - TikTok/Douyin 영상 통계 추출
    - 후보 JSON과 영상 ID 기준으로 통계 병합
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

    VIDEO_ID_KEYS = [
        "aweme_id",
        "awemeId",
        "item_id",
        "itemId",
        "video_id",
        "videoId",
        "id",
    ]

    VIEW_KEYS = [
        "playCount",
        "play_count",
        "viewCount",
        "view_count",
        "views",
    ]

    LIKE_KEYS = [
        "diggCount",
        "digg_count",
        "likeCount",
        "like_count",
        "likes",
    ]

    COMMENT_KEYS = [
        "commentCount",
        "comment_count",
        "comments",
    ]

    SHARE_KEYS = [
        "shareCount",
        "share_count",
        "shares",
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
        if not page:
            return

        self.enabled = True
        page.on("response", self._handle_response)

    async def start_async(self, page) -> None:
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

        return any(
            keyword.lower() in lower_url
            for keyword in self.keywords
        )

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

    def _content_type(
        self,
        headers: Dict[str, Any],
    ) -> str:
        return (
            headers.get("content-type")
            or headers.get("Content-Type")
            or ""
        )

    def _trim_body(self, body: Any) -> Any:
        if (
            isinstance(body, str)
            and len(body) > self.max_body_chars
        ):
            return (
                body[: self.max_body_chars]
                + "\n...[TRIMMED]"
            )

        return body

    def _record(self, item: Dict[str, Any]) -> None:
        self.responses.append(item)

    def _handle_response(self, response) -> None:
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
                if (
                    "application/json" in content_type
                    or "json" in content_type
                ):
                    body = response.json()
                    body_type = "json"
                else:
                    text = response.text()

                    try:
                        body = json.loads(text)
                        body_type = "json"
                    except Exception:
                        body = text
                        body_type = "text"

            except Exception as exc:
                body = f"BODY_READ_FAILED: {exc}"
                body_type = "error"

            item = {
                "captured_at": datetime.now().isoformat(
                    timespec="seconds"
                ),
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

    async def _handle_response_async(
        self,
        response,
    ) -> None:
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
                if (
                    "application/json" in content_type
                    or "json" in content_type
                ):
                    body = await response.json()
                    body_type = "json"
                else:
                    text = await response.text()

                    try:
                        body = json.loads(text)
                        body_type = "json"
                    except Exception:
                        body = text
                        body_type = "text"

            except Exception as exc:
                body = f"BODY_READ_FAILED: {exc}"
                body_type = "error"

            item = {
                "captured_at": datetime.now().isoformat(
                    timespec="seconds"
                ),
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

    def latest(
        self,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        items = list(self.responses)

        return items[-limit:]

    def all(self) -> List[Dict[str, Any]]:
        return list(self.responses)

    def extract_tiktok_stats(self):
        """
        Response 로그에서 TikTok/Douyin 영상 통계를 추출한다.

        반환:
        {
            "7535737080740203784": {
                "view_count": ...,
                "like_count": ...,
                "comment_count": ...,
                "share_count": ...
            }
        }
        """

        stats_map: Dict[str, Dict[str, int]] = {}

        for item in self.responses:
            body = item.get("body")

            if not isinstance(body, dict):
                continue

            try:
               self._walk_tiktok_data(
                    body,
                    stats_map,
               )
            except Exception:
                continue

        return stats_map

    def merge_tiktok_stats(
        self,
        candidates: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        후보 URL의 영상 ID와 API 응답 통계를 병합합니다.
        """

        stats_map = self.extract_tiktok_stats()
        merged: List[Dict[str, Any]] = []

        for candidate in candidates or []:
            if not isinstance(candidate, dict):
                continue

            item = dict(candidate)

            video_id = self.extract_video_id(
                item.get("url", "")
            )

            stats = stats_map.get(
                video_id,
                {},
            )

            if stats:
                item["view_count"] = max(
                    self.safe_int(
                        item.get("view_count", 0)
                    ),
                    self.safe_int(
                        stats.get("view_count", 0)
                    ),
                )

                item["like_count"] = max(
                    self.safe_int(
                        item.get("like_count", 0)
                    ),
                    self.safe_int(
                        stats.get("like_count", 0)
                    ),
                )

                item["comment_count"] = max(
                    self.safe_int(
                        item.get("comment_count", 0)
                    ),
                    self.safe_int(
                        stats.get("comment_count", 0)
                    ),
                )

                item["share_count"] = max(
                    self.safe_int(
                        item.get("share_count", 0)
                    ),
                    self.safe_int(
                        stats.get("share_count", 0)
                    ),
                )

                item["views"] = str(
                    item["view_count"]
                )

                item["likes"] = str(
                    item["like_count"]
                )

                item["comments"] = str(
                    item["comment_count"]
                )

                item["shares"] = str(
                    item["share_count"]
                )

                item["metadata_source"] = (
                    "playwright-network-response"
                )
            else:
                item["metadata_source"] = (
                    item.get("metadata_source")
                    or "playwright-dom"
                )

            merged.append(item)

        return merged

    def _walk_tiktok_data(
        self,
        node: Any,
        result: Dict[str, Dict[str, int]],
    ) -> None:
        if isinstance(node, list):
            for child in node:
                self._walk_tiktok_data(
                    child,
                    result,
                )

            return

        if not isinstance(node, dict):
            return

        video_id = self._find_video_id(node)
        stats = self._find_stats(node)

        if video_id and self._has_stats(stats):
            current = result.get(
                video_id,
                {
                    "view_count": 0,
                    "like_count": 0,
                    "comment_count": 0,
                    "share_count": 0,
                },
            )

            result[video_id] = {
                "view_count": max(
                    current["view_count"],
                    stats["view_count"],
                ),
                "like_count": max(
                    current["like_count"],
                    stats["like_count"],
                ),
                "comment_count": max(
                    current["comment_count"],
                    stats["comment_count"],
                ),
                "share_count": max(
                    current["share_count"],
                    stats["share_count"],
                ),
            }

        for child in node.values():
            if isinstance(
                child,
                (dict, list),
            ):
                self._walk_tiktok_data(
                    child,
                    result,
                )

    def _find_video_id(
        self,
        node: Dict[str, Any],
    ) -> str:
        for key in self.VIDEO_ID_KEYS:
            value = node.get(key)

            if self._looks_like_video_id(value):
                return str(value)

        video = node.get("video")

        if isinstance(video, dict):
            for key in self.VIDEO_ID_KEYS:
                value = video.get(key)

                if self._looks_like_video_id(value):
                    return str(value)

        return ""

    def _find_stats(
        self,
        node: Dict[str, Any],
    ) -> Dict[str, int]:
        sources = [node]

        for key in [
            "stats",
            "statistics",
            "statsV2",
            "statisticsV2",
            "authorStats",
        ]:
            value = node.get(key)

            if isinstance(value, dict):
                sources.append(value)

        return {
            "view_count": self._first_number(
                sources,
                self.VIEW_KEYS,
            ),
            "like_count": self._first_number(
                sources,
                self.LIKE_KEYS,
            ),
            "comment_count": self._first_number(
                sources,
                self.COMMENT_KEYS,
            ),
            "share_count": self._first_number(
                sources,
                self.SHARE_KEYS,
            ),
        }

    def _first_number(
        self,
        sources: List[Dict[str, Any]],
        keys: List[str],
    ) -> int:
        for source in sources:
            for key in keys:
                if key not in source:
                    continue

                value = self.safe_int(
                    source.get(key)
                )

                if value > 0:
                    return value

        return 0

    def _has_stats(
        self,
        stats: Dict[str, int],
    ) -> bool:
        return any(
            self.safe_int(value) > 0
            for value in stats.values()
        )

    def _looks_like_video_id(
        self,
        value: Any,
    ) -> bool:
        text = str(value or "").strip()

        return bool(
            re.fullmatch(
                r"\d{15,25}",
                text,
            )
        )

    def extract_video_id(
        self,
        url: str,
    ) -> str:
        match = re.search(
            r"/video/(\d+)",
            str(url or ""),
        )

        return match.group(1) if match else ""

    def safe_int(
        self,
        value: Any,
    ) -> int:
        if value is None:
            return 0

        if isinstance(value, bool):
            return 0

        try:
            return max(
                int(float(value)),
                0,
            )
        except (TypeError, ValueError):
            return 0

    def save(self) -> Path:
        self.log_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        stats = self.extract_tiktok_stats()

        payload = {
            "version": "sprint57-response-sniffer-2.0",
            "saved_at": datetime.now().isoformat(
                timespec="seconds"
            ),
            "count": len(self.responses),
            "tiktok_stats_count": len(stats),
            "tiktok_stats": stats,
            "items": list(self.responses),
        }

        self.log_path.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return self.log_path