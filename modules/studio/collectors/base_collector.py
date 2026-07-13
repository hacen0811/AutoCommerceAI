from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union


@dataclass
class CollectedVideo:
    platform: str
    title: str
    url: str
    keyword: str
    score: int

    source: str = "playwright-dom"
    thumbnail: str = ""
    screenshot: str = ""
    video_path: str = ""

    downloaded: bool = False
    download_error: str = ""

    # 기존 필드 호환용 원문
    views: str = ""
    likes: str = ""
    comments: str = ""
    shares: str = ""
    duration: str = ""

    # Sprint 57: 정규화된 실제 메타데이터
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0

    note: str = "실제 검색 화면 DOM에서 수집한 후보입니다."


class BaseSiteCollector:
    platform = "base"

    def __init__(
        self,
        html_dir: Path,
        shot_dir: Path,
        timeout_ms: int = 30000,
    ):
        self.html_dir = html_dir
        self.shot_dir = shot_dir
        self.timeout_ms = timeout_ms

        self.html_dir.mkdir(parents=True, exist_ok=True)
        self.shot_dir.mkdir(parents=True, exist_ok=True)

    def save_debug(self, page, platform: str) -> Dict:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        html_path = self.html_dir / f"{ts}_{platform}.html"
        shot_path = self.shot_dir / f"{ts}_{platform}.png"

        html_saved = False
        screenshot_saved = False

        try:
            html_path.write_text(
                page.content(),
                encoding="utf-8",
            )
            html_saved = True
        except Exception:
            pass

        try:
            page.screenshot(
                path=str(shot_path),
                full_page=True,
            )
            screenshot_saved = True
        except Exception:
            pass

        return {
            "html": str(html_path) if html_saved else "",
            "screenshot": str(shot_path) if screenshot_saved else "",
        }

    def slow_scroll(self, page, count: int = 3) -> None:
        for _ in range(max(0, count)):
            try:
                page.mouse.wheel(0, 2200)
                page.wait_for_timeout(1800)
            except Exception:
                break

    def body_text(self, page) -> str:
        try:
            return page.locator("body").inner_text(
                timeout=6000
            )[:8000]
        except Exception:
            return ""

    def blocked_hint(
        self,
        page,
        body_text: str = "",
    ) -> str:
        try:
            url = str(page.url or "").lower()
            title = str(page.title() or "").lower()
        except Exception:
            url = ""
            title = ""

        combined = f"{url}\n{title}\n{body_text}".lower()

        blocked_words = [
            "captcha",
            "verify",
            "verification",
            "security check",
            "login",
            "log in",
            "sign in",
            "punish",
            "x5sec",
            "验证码",
            "安全验证",
            "登录",
            "로그인",
            "인증",
        ]

        if any(word in combined for word in blocked_words):
            return "로그인 또는 보안 인증이 필요한 상태일 수 있습니다."

        return ""

    def normalize_url(self, href: str) -> str:
        return str(href or "").strip()

    def is_junk_text(
        self,
        text: str,
        href: str = "",
    ) -> bool:
        text_lower = str(text or "").lower()
        href_lower = str(href or "").lower()

        junk_words = [
            "get app",
            "download app",
            "open app",
            "login",
            "log in",
            "sign in",
            "sign up",
            "signup",
            "privacy",
            "service",
            "about",
            "sponsor",
            "promotion",
            "client",
            "terms",
            "policy",
            "cookie",
            "copyright",
            "앱 다운로드",
            "로그인",
            "회원가입",
            "개인정보",
            "이용약관",
        ]

        return any(
            word in text_lower or word in href_lower
            for word in junk_words
        )

    def parse_count(
        self,
        value: Union[str, int, float, None],
    ) -> int:
        """
        TikTok/Douyin 숫자 표기를 정수로 변환합니다.

        예:
        1,234   -> 1234
        1.2K    -> 1200
        3.5M    -> 3500000
        1.1B    -> 1100000000
        12만    -> 120000
        1.5억   -> 150000000
        3.2w    -> 32000
        1.4万   -> 14000
        2亿     -> 200000000
        """

        if value is None:
            return 0

        if isinstance(value, bool):
            return 0

        if isinstance(value, int):
            return max(value, 0)

        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return 0
            return max(int(value), 0)

        text = str(value).strip().lower()

        if not text:
            return 0

        text = (
            text.replace(",", "")
            .replace(" ", "")
            .replace("views", "")
            .replace("view", "")
            .replace("likes", "")
            .replace("like", "")
            .replace("comments", "")
            .replace("comment", "")
            .replace("shares", "")
            .replace("share", "")
            .replace("조회수", "")
            .replace("조회", "")
            .replace("좋아요", "")
            .replace("댓글", "")
            .replace("공유", "")
            .replace("播放量", "")
            .replace("点赞", "")
            .replace("评论", "")
            .replace("分享", "")
            .strip()
        )

        match = re.search(
            r"(-?\d+(?:\.\d+)?)\s*([kmbw万億亿천만억]?)",
            text,
            flags=re.IGNORECASE,
        )

        if not match:
            digits = re.sub(r"[^\d]", "", text)
            return int(digits) if digits else 0

        try:
            number = float(match.group(1))
        except (TypeError, ValueError):
            return 0

        suffix = (match.group(2) or "").lower()

        multipliers = {
            "": 1,
            "k": 1_000,
            "천": 1_000,
            "w": 10_000,
            "万": 10_000,
            "만": 10_000,
            "m": 1_000_000,
            "b": 1_000_000_000,
            "億": 100_000_000,
            "亿": 100_000_000,
            "억": 100_000_000,
        }

        multiplier = multipliers.get(suffix, 1)

        return max(int(number * multiplier), 0)

    def engagement_score(
        self,
        view_count: int = 0,
        like_count: int = 0,
        comment_count: int = 0,
        share_count: int = 0,
    ) -> int:
        """
        Sprint 57 후보 점수.

        조회수를 가장 크게 반영하고,
        좋아요·댓글·공유 반응을 보조 지표로 사용합니다.
        """

        views = max(int(view_count or 0), 0)
        likes = max(int(like_count or 0), 0)
        comments = max(int(comment_count or 0), 0)
        shares = max(int(share_count or 0), 0)

        score = 0.0

        # 조회수: 최대 60점
        if views > 0:
            score += min(
                60.0,
                math.log10(views + 1) * 10.0,
            )

        # 절대 반응 수: 최대 25점
        if likes > 0:
            score += min(
                15.0,
                math.log10(likes + 1) * 3.0,
            )

        if comments > 0:
            score += min(
                6.0,
                math.log10(comments + 1) * 1.5,
            )

        if shares > 0:
            score += min(
                4.0,
                math.log10(shares + 1),
            )

        # 참여율: 최대 10점
        if views > 0:
            engagement_rate = (
                likes
                + comments * 3
                + shares * 4
            ) / views

            score += min(
                10.0,
                engagement_rate * 100.0,
            )

        return int(min(max(round(score), 0), 99))

    def score_item(
        self,
        keyword: str,
        title: str,
        href: str,
        thumb: str = "",
    ) -> int:
        """
        제목·URL 기반 기본 관련도 점수입니다.

        TikTok/Douyin에서 실제 메타데이터가 있으면
        engagement_score 결과와 함께 사용합니다.
        """

        text = f"{title}\n{href}".lower()

        key_tokens = [
            token.lower()
            for token in re.split(r"\s+", keyword or "")
            if len(token.strip()) >= 2
        ]

        score = 20

        if thumb:
            score += 20

        score += sum(
            10
            for token in key_tokens
            if token in text
        )

        shopping_words = [
            "review",
            "recommend",
            "product",
            "shopping",
            "usage",
            "how to use",
            "before",
            "after",
            "리뷰",
            "추천",
            "제품",
            "상품",
            "사용법",
            "사용",
            "비교",
            "전후",
            "测评",
            "推荐",
            "好物",
            "使用",
            "对比",
        ]

        if any(word in text for word in shopping_words):
            score += 25

        if any(
            word in str(href or "").lower()
            for word in [
                "video",
                "aweme",
                "item",
                "detail",
                "offer",
                "product",
            ]
        ):
            score += 30

        return min(score, 99)

    def dedupe(
        self,
        rows: List[CollectedVideo],
        limit: int = 10,
    ) -> List[CollectedVideo]:
        seen = set()
        output: List[CollectedVideo] = []

        sorted_rows = sorted(
            rows,
            key=lambda row: (
                int(row.score or 0),
                int(row.view_count or 0),
                int(row.like_count or 0),
                int(row.comment_count or 0),
            ),
            reverse=True,
        )

        for row in sorted_rows:
            key = re.sub(
                r"[?#].*$",
                "",
                str(row.url or ""),
            )

            if not key or key in seen:
                continue

            seen.add(key)
            output.append(row)

            if len(output) >= limit:
                break

        return output

    def to_dicts(
        self,
        rows: List[CollectedVideo],
    ) -> List[Dict]:
        return [asdict(row) for row in rows]