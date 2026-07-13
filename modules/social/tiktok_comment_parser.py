from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List

from .social_comment_models import SocialComment


class TikTokCommentParser:
    VERSION = "tiktok-comment-parser-69-2"

    COMMENT_CONTAINERS = (
        "[data-e2e='comment-level-1']",
        "[data-e2e='comment-item']",
        "[class*='CommentItem']",
        "[class*='comment-item']",
    )

    TEXT_SELECTORS = (
        "[data-e2e='comment-level-1'] p",
        "[data-e2e='comment-item'] p",
        "[class*='CommentText']",
        "[class*='comment-text']",
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
                                platform="tiktok",
                                video_url=video_url,
                                source="tiktok_dom",
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
            text = self._first_text(
                payload,
                ("text", "comment_text", "commentText", "reply_text", "replyText"),
            )

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
                            ("digg_count", "diggCount", "like_count", "likeCount", "likes"),
                        ),
                        reply_count=self._first_int(
                            payload,
                            (
                                "reply_comment_total",
                                "replyCommentTotal",
                                "reply_count",
                                "replyCount",
                                "replies",
                            ),
                        ),
                        author=self._extract_author(payload),
                        created_at=str(
                            payload.get("create_time")
                            or payload.get("createTime")
                            or payload.get("created_at")
                            or ""
                        ),
                        platform="tiktok",
                        video_url=video_url,
                        source="tiktok_response",
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
                or user.get("uniqueId")
                or user.get("username")
                or ""
            )
        return str(payload.get("author") or payload.get("nickname") or "")

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
            "privacy policy",
            "이용약관",
            "개인정보처리방침",
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
