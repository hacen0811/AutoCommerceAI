from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass
class SocialComment:
    text: str
    comment_id: str = ""
    parent_comment_id: str = ""
    like_count: int = 0
    reply_count: int = 0
    author: str = ""
    created_at: str = ""
    platform: str = ""
    video_url: str = ""
    source: str = "public_page"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SocialCommentResult:
    collector_version: str
    ok: bool = False
    status: str = "empty"
    platform: str = ""
    video_url: str = ""
    comment_count: int = 0
    comments: List[Dict[str, Any]] = field(default_factory=list)
    error: str = ""
    debug_path: str = ""
    screenshot_path: str = ""
    final_url: str = ""
    source: str = "social_public_page"
    response_count: int = 0
    network_comment_count: int = 0
    filtered_duplicate_count: int = 0
    filtered_invalid_count: int = 0
    manual_verification_required: bool = False
    manual_verification_resolved: bool = False
    manual_verification_waited_seconds: int = 0
    profile_mode: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["comment_count"] = len(data.get("comments") or [])
        return data
