from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List

from .social_comment_models import SocialComment


class DouyinCommentParser:
    VERSION = "douyin-comment-parser-69-2"

    TEXT_SELECTORS = (
        "[data-e2e='comment-item']",
        "[class*='comment-item'] [class*='text']",
        "[class*='CommentItem'] [class*='content']",
        "[class*='comment'] p",
    )

    COMMENT_ID_KEYS = (
        "cid",
        "comment_id",
        "commentId",
        "reply_id",
        "replyId",
    )

    def parse_dom(self, page, video_url: str, max_comments: int) -> List[Dict[str, Any]]:
        comments: List[SocialComment] = []

        for selector in self.TEXT_SELECTORS:
            try:
                locator = page.locator(selector)
                count = min(locator.count(), max(1, int(max_comments or 50)) * 3)

                for index in range(count):
                    try:
                        text = locator.nth(index).inner_text(timeout=1500)
                    except Exception:
                        continue

                    text = self._clean_text(text)
                    if self._looks_like_comment(text):
                        comments.append(
                            SocialComment(
                                text=text,
                                platform="douyin",
                                video_url=video_url,
                                source="douyin_dom",
                            )
                        )
            except Exception:
                continue

        return self._normalize(comments, max_comments)

    def parse_payloads(
        self,
        payloads: Iterable[Any],
        video_url: str,
        max_comments: int,
    ) -> List[Dict[str, Any]]:
        comments: List[SocialComment] = []

        for payload in payloads:
            self._walk_payload(payload, video_url, comments)

        return self._normalize(comments, max_comments)

    def _walk_payload(
        self,
        payload: Any,
        video_url: str,
        output: List[SocialComment],
    ) -> None:
        if isinstance(payload, dict):
            comment_id = self._comment_id(payload)
            text = self._first_text(payload, ("text", "content", "comment_text"))

            if comment_id and self._looks_like_comment(text):
                output.append(
                    SocialComment(
                        text=text,
                        comment_id=comment_id,
                        parent_comment_id=str(
                            payload.get("parent_comment_id")
                            or payload.get("parentCommentId")
                            or ""
                        ),
                        like_count=self._first_int(
                            payload,
                            ("digg_count", "like_count", "likes"),
                        ),
                        reply_count=self._first_int(
                            payload,
                            ("reply_comment_total", "reply_count", "replies"),
                        ),
                        author=self._extract_author(payload),
                        created_at=str(
                            payload.get("create_time")
                            or payload.get("created_at")
                            or ""
                        ),
                        platform="douyin",
                        video_url=video_url,
                        source="douyin_response",
                    )
                )

            for value in payload.values():
                self._walk_payload(value, video_url, output)

        elif isinstance(payload, list):
            for item in payload:
                self._walk_payload(item, video_url, output)

    def _comment_id(self, payload: Dict[str, Any]) -> str:
        for key in self.COMMENT_ID_KEYS:
            value = payload.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
        return ""

    def _extract_author(self, payload: Dict[str, Any]) -> str:
        user = payload.get("user")
        if isinstance(user, dict):
            return str(
                user.get("nickname")
                or user.get("unique_id")
                or user.get("short_id")
                or ""
            )
        return str(payload.get("nickname") or payload.get("author") or "")

    def _first_text(self, payload: Dict[str, Any], keys) -> str:
        for key in keys:
            value = payload.get(key)
            if isinstance(value, str):
                cleaned = self._clean_text(value)
                if cleaned:
                    return cleaned
        return ""

    def _first_int(self, payload: Dict[str, Any], keys) -> int:
        for key in keys:
            value = payload.get(key)
            try:
                if value is not None:
                    return max(0, int(value))
            except Exception:
                continue
        return 0

    def _clean_text(self, value: Any) -> str:
        return re.sub(r"\s+", " ", str(value or "")).strip()

    def _looks_like_comment(self, text: str) -> bool:
        clean = self._clean_text(text)
        if len(clean) < 2 or len(clean) > 1000:
            return False

        blocked = (
            "http://",
            "https://",
            "javascript",
            "隐私政策",
            "用户协议",
        )
        lowered = clean.lower()
        return not any(word in lowered for word in blocked)

    def _normalize(
        self,
        comments: List[SocialComment],
        max_comments: int,
    ) -> List[Dict[str, Any]]:
        output: List[Dict[str, Any]] = []
        seen = set()
        safe_max = max(1, min(int(max_comments or 50), 200))

        for comment in comments:
            text = self._clean_text(comment.text)
            normalized_text = re.sub(
                r"[^0-9a-zA-Z가-힣\u4e00-\u9fff]",
                "",
                text,
            ).lower()
            key = comment.comment_id or normalized_text

            if not key or key in seen:
                continue

            seen.add(key)
            comment.text = text
            output.append(comment.to_dict())

            if len(output) >= safe_max:
                break

        return output
