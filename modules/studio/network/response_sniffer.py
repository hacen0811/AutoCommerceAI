from __future__ import annotations

import json
import re
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class ResponseSniffer:
    """
    Sprint68-2 Response Sniffer

    기존 기능:
    - Playwright response 이벤트 연결
    - TikTok/Douyin 영상 통계 추출
    - 후보 JSON과 영상 ID 기준 통계 병합

    Sprint68-2 추가:
    - comment/reply 응답 URL 수집
    - TikTok/Douyin 댓글 본문 추출
    - 댓글 좋아요/답글 수/작성자 추출
    """

    VERSION = "sprint68-2-response-sniffer-3.0"

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
        "comment",
        "comments",
        "reply",
        "reply_list",
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

    COMMENT_TEXT_KEYS = [
        "text",
        "content",
        "comment_text",
        "commentText",
        "reply_text",
        "replyText",
    ]

    COMMENT_LIKE_KEYS = [
        "digg_count",
        "diggCount",
        "like_count",
        "likeCount",
        "likes",
    ]

    COMMENT_REPLY_KEYS = [
        "reply_comment_total",
        "replyCommentTotal",
        "reply_count",
        "replyCount",
        "replies",
    ]

    AUTHOR_KEYS = [
        "nickname",
        "unique_id",
        "uniqueId",
        "username",
        "short_id",
        "shortId",
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

    def attach(self, page):
        self.start(page)
        return self

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

    def _build_item(self, response, body, body_type, headers):
        return {
            "captured_at": datetime.now().isoformat(timespec="seconds"),
            "url": response.url,
            "status": response.status,
            "method": self._safe_method(response),
            "content_type": self._content_type(headers),
            "headers": headers,
            "body_type": body_type,
            "body": self._trim_body(body),
        }

    def _handle_response(self, response) -> None:
        if not self.enabled:
            return
        try:
            if not self._match_url(response.url):
                return

            headers = self._safe_headers(response)
            content_type = self._content_type(headers)
            body = None
            body_type = "empty"

            try:
                if "json" in content_type.lower():
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

            self._record(
                self._build_item(
                    response,
                    body,
                    body_type,
                    headers,
                )
            )
        except Exception:
            return

    async def _handle_response_async(self, response) -> None:
        if not self.enabled:
            return
        try:
            if not self._match_url(response.url):
                return

            headers = self._safe_headers(response)
            content_type = self._content_type(headers)
            body = None
            body_type = "empty"

            try:
                if "json" in content_type.lower():
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

            self._record(
                self._build_item(
                    response,
                    body,
                    body_type,
                    headers,
                )
            )
        except Exception:
            return

    def latest(self, limit: int = 20) -> List[Dict[str, Any]]:
        return list(self.responses)[-limit:]

    def all(self) -> List[Dict[str, Any]]:
        return list(self.responses)

    def extract_tiktok_stats(self) -> Dict[str, Dict[str, int]]:
        stats_map: Dict[str, Dict[str, int]] = {}

        for item in self.responses:
            body = item.get("body")
            if not isinstance(body, dict):
                continue
            try:
                self._walk_tiktok_data(body, stats_map)
            except Exception:
                continue

        return stats_map

    def extract_tiktok_comments(
        self,
        max_comments: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        수집된 response JSON에서 댓글 본문을 추출합니다.

        반환:
        [
            {
                "text": "...",
                "like_count": 0,
                "reply_count": 0,
                "author": "",
                "created_at": "",
                "video_id": "",
                "source": "playwright-network-response"
            }
        ]
        """
        comments: List[Dict[str, Any]] = []

        for item in self.responses:
            body = item.get("body")
            url = str(item.get("url") or "").lower()

            if not isinstance(body, (dict, list)):
                continue

            if not any(
                token in url
                for token in ("comment", "reply", "aweme", "item")
            ):
                continue

            try:
                self._walk_comment_data(
                    body,
                    comments,
                    inherited_video_id="",
                )
            except Exception:
                continue

        return self._normalize_comments(
            comments,
            max_comments=max_comments,
        )

    def merge_tiktok_stats(
        self,
        candidates: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        stats_map = self.extract_tiktok_stats()
        merged: List[Dict[str, Any]] = []

        for candidate in candidates or []:
            if not isinstance(candidate, dict):
                continue

            item = dict(candidate)
            video_id = self.extract_video_id(item.get("url", ""))
            stats = stats_map.get(video_id, {})

            if stats:
                item["view_count"] = max(
                    self.safe_int(item.get("view_count", 0)),
                    self.safe_int(stats.get("view_count", 0)),
                )
                item["like_count"] = max(
                    self.safe_int(item.get("like_count", 0)),
                    self.safe_int(stats.get("like_count", 0)),
                )
                item["comment_count"] = max(
                    self.safe_int(item.get("comment_count", 0)),
                    self.safe_int(stats.get("comment_count", 0)),
                )
                item["share_count"] = max(
                    self.safe_int(item.get("share_count", 0)),
                    self.safe_int(stats.get("share_count", 0)),
                )
                item["views"] = str(item["view_count"])
                item["likes"] = str(item["like_count"])
                item["comments"] = str(item["comment_count"])
                item["shares"] = str(item["share_count"])
                item["metadata_source"] = "playwright-network-response"
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
                self._walk_tiktok_data(child, result)
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
                "view_count": max(current["view_count"], stats["view_count"]),
                "like_count": max(current["like_count"], stats["like_count"]),
                "comment_count": max(current["comment_count"], stats["comment_count"]),
                "share_count": max(current["share_count"], stats["share_count"]),
            }

        for child in node.values():
            if isinstance(child, (dict, list)):
                self._walk_tiktok_data(child, result)

    def _walk_comment_data(
        self,
        node: Any,
        result: List[Dict[str, Any]],
        inherited_video_id: str,
    ) -> None:
        if isinstance(node, list):
            for child in node:
                self._walk_comment_data(
                    child,
                    result,
                    inherited_video_id,
                )
            return

        if not isinstance(node, dict):
            return

        video_id = self._find_video_id(node) or inherited_video_id
        text = self._find_comment_text(node)

        if self._looks_like_comment_node(node, text):
            result.append(
                {
                    "text": text,
                    "like_count": self._first_number(
                        [node],
                        self.COMMENT_LIKE_KEYS,
                    ),
                    "reply_count": self._first_number(
                        [node],
                        self.COMMENT_REPLY_KEYS,
                    ),
                    "author": self._find_author(node),
                    "created_at": str(
                        node.get("create_time")
                        or node.get("createTime")
                        or node.get("created_at")
                        or ""
                    ),
                    "video_id": video_id,
                    "source": "playwright-network-response",
                }
            )

        for child in node.values():
            if isinstance(child, (dict, list)):
                self._walk_comment_data(
                    child,
                    result,
                    video_id,
                )

    def _find_comment_text(self, node: Dict[str, Any]) -> str:
        for key in self.COMMENT_TEXT_KEYS:
            value = node.get(key)
            if not isinstance(value, str):
                continue
            text = re.sub(r"\s+", " ", value).strip()
            if text:
                return text
        return ""

    def _looks_like_comment_node(
        self,
        node: Dict[str, Any],
        text: str,
    ) -> bool:
        if len(text) < 2 or len(text) > 1000:
            return False

        lowered = text.lower()
        blocked = (
            "http://",
            "https://",
            "javascript",
            "privacy policy",
            "이용약관",
            "개인정보처리방침",
        )
        if any(word in lowered for word in blocked):
            return False

        comment_signals = (
            "cid",
            "comment_id",
            "commentId",
            "reply_id",
            "replyId",
            "reply_comment_total",
            "reply_count",
            "digg_count",
            "user",
        )

        return any(key in node for key in comment_signals)

    def _find_author(self, node: Dict[str, Any]) -> str:
        user = node.get("user")
        if isinstance(user, dict):
            for key in self.AUTHOR_KEYS:
                value = user.get(key)
                if value:
                    return str(value)

        for key in self.AUTHOR_KEYS:
            value = node.get(key)
            if value:
                return str(value)

        return ""

    def _normalize_comments(
        self,
        comments: List[Dict[str, Any]],
        max_comments: int,
    ) -> List[Dict[str, Any]]:
        output: List[Dict[str, Any]] = []
        seen = set()
        safe_max = max(1, min(int(max_comments or 100), 500))

        for comment in comments:
            text = re.sub(
                r"\s+",
                " ",
                str(comment.get("text") or ""),
            ).strip()

            key = re.sub(
                r"[^0-9a-zA-Z가-힣\u4e00-\u9fff]",
                "",
                text,
            ).lower()

            if not key or key in seen:
                continue

            seen.add(key)
            item = dict(comment)
            item["text"] = text
            item["like_count"] = self.safe_int(
                item.get("like_count")
            )
            item["reply_count"] = self.safe_int(
                item.get("reply_count")
            )
            output.append(item)

            if len(output) >= safe_max:
                break

        return output

    def _find_video_id(self, node: Dict[str, Any]) -> str:
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

    def _find_stats(self, node: Dict[str, Any]) -> Dict[str, int]:
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
            "view_count": self._first_number(sources, self.VIEW_KEYS),
            "like_count": self._first_number(sources, self.LIKE_KEYS),
            "comment_count": self._first_number(sources, self.COMMENT_KEYS),
            "share_count": self._first_number(sources, self.SHARE_KEYS),
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
                value = self.safe_int(source.get(key))
                if value > 0:
                    return value
        return 0

    def _has_stats(self, stats: Dict[str, int]) -> bool:
        return any(self.safe_int(value) > 0 for value in stats.values())

    def _looks_like_video_id(self, value: Any) -> bool:
        text = str(value or "").strip()
        return bool(re.fullmatch(r"\d{15,25}", text))

    def extract_video_id(self, url: str) -> str:
        match = re.search(r"/video/(\d+)", str(url or ""))
        return match.group(1) if match else ""

    def safe_int(self, value: Any) -> int:
        if value is None or isinstance(value, bool):
            return 0
        try:
            return max(int(float(value)), 0)
        except (TypeError, ValueError):
            return 0

    def save(self) -> Path:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        stats = self.extract_tiktok_stats()
        comments = self.extract_tiktok_comments()

        payload = {
            "version": self.VERSION,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "count": len(self.responses),
            "tiktok_stats_count": len(stats),
            "tiktok_stats": stats,
            "tiktok_comment_count": len(comments),
            "tiktok_comments": comments,
            "items": list(self.responses),
        }

        self.log_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return self.log_path
