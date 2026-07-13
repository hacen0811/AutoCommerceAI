from __future__ import annotations

import math
import re
from urllib.parse import urljoin


class SourceCandidateParser:
    """
    Sprint 57

    Playwright 페이지의 실제 검색 결과 DOM에서 후보를 추출합니다.

    TikTok:
    - 영상 URL
    - 제목
    - 썸네일
    - 조회수
    - 좋아요
    - 댓글
    - 공유 수
    - 메타데이터 기반 점수

    Taobao / 1688:
    - 기존 후보 수집 동작 유지
    """

    def parse(self, page, platform=""):
        platform = str(platform or "").lower().strip()

        if platform in ["douyin", "tiktok"]:
            return self.parse_tiktok(page)

        if platform == "taobao":
            return self.parse_taobao(page)

        if platform == "1688":
            return self.parse_1688(page)

        return []

    def parse_tiktok(self, page):
        items = []

        try:
            raw_items = page.evaluate(
                r"""
                () => {
                    const selectors = [
                        'div[data-e2e*="search-card"]',
                        'div[data-e2e*="video-item"]',
                        'div[data-e2e*="user-post-item"]',
                        'article',
                        'a[href*="/video/"]'
                    ];

                    const nodes = [];

                    for (const selector of selectors) {
                        document
                            .querySelectorAll(selector)
                            .forEach(node => nodes.push(node));
                    }

                    const uniqueNodes = Array.from(new Set(nodes));

                    const readText = (root, selectors) => {
                        for (const selector of selectors) {
                            const node = root.querySelector(selector);

                            if (!node) {
                                continue;
                            }

                            const text = (
                                node.innerText
                                || node.textContent
                                || node.getAttribute("aria-label")
                                || ""
                            ).trim();

                            if (text) {
                                return text;
                            }
                        }

                        return "";
                    };

                    const findNumber = (raw, labels) => {
                        for (const label of labels) {
                            const afterPattern = new RegExp(
                                "([\\d,.]+(?:\\.\\d+)?\\s*[KMB]?)\\s*"
                                + label,
                                "i"
                            );

                            const beforePattern = new RegExp(
                                label
                                + "\\s*([\\d,.]+(?:\\.\\d+)?\\s*[KMB]?)",
                                "i"
                            );

                            const afterMatch = raw.match(afterPattern);

                            if (afterMatch && afterMatch[1]) {
                                return afterMatch[1].trim();
                            }

                            const beforeMatch = raw.match(beforePattern);

                            if (beforeMatch && beforeMatch[1]) {
                                return beforeMatch[1].trim();
                            }
                        }

                        return "";
                    };

                    return uniqueNodes
                        .slice(0, 1200)
                        .map(node => {
                            const link =
                                node.matches?.('a[href*="/video/"]')
                                    ? node
                                    : node.querySelector(
                                        'a[href*="/video/"]'
                                    );

                            const href = link
                                ? (
                                    link.href
                                    || link.getAttribute("href")
                                    || ""
                                )
                                : "";

                            if (!href) {
                                return null;
                            }

                            const raw = (
                                node.innerText
                                || node.textContent
                                || ""
                            )
                                .replace(/\u00a0/g, " ")
                                .trim();

                            const img =
                                node.querySelector("img")
                                || link.querySelector("img");

                            const video =
                                node.querySelector("video")
                                || link.querySelector("video");

                            const title = (
                                link.getAttribute("title")
                                || link.getAttribute("aria-label")
                                || img?.getAttribute("alt")
                                || raw.split("\n")[0]
                                || ""
                            ).trim();

                            const thumbnail = img
                                ? (
                                    img.currentSrc
                                    || img.src
                                    || img.getAttribute("src")
                                    || img.getAttribute("data-src")
                                    || img.getAttribute("srcset")
                                    || ""
                                )
                                : (
                                    video
                                        ? (video.poster || "")
                                        : ""
                                );

                            let views = readText(node, [
                                '[data-e2e*="video-views"]',
                                '[data-e2e*="view-count"]',
                                '[data-e2e*="views"]',
                                '[aria-label*="view"]',
                                '[aria-label*="조회"]'
                            ]);

                            let likes = readText(node, [
                                '[data-e2e*="like-count"]',
                                '[data-e2e*="likes"]',
                                '[aria-label*="like"]',
                                '[aria-label*="좋아요"]'
                            ]);

                            let comments = readText(node, [
                                '[data-e2e*="comment-count"]',
                                '[data-e2e*="comments"]',
                                '[aria-label*="comment"]',
                                '[aria-label*="댓글"]'
                            ]);

                            let shares = readText(node, [
                                '[data-e2e*="share-count"]',
                                '[data-e2e*="shares"]',
                                '[aria-label*="share"]',
                                '[aria-label*="공유"]'
                            ]);

                            if (!views) {
                                views = findNumber(
                                    raw,
                                    [
                                        "views?",
                                        "조회수?",
                                        "播放量"
                                    ]
                                );
                            }

                            if (!likes) {
                                likes = findNumber(
                                    raw,
                                    [
                                        "likes?",
                                        "좋아요",
                                        "点赞"
                                    ]
                                );
                            }

                            if (!comments) {
                                comments = findNumber(
                                    raw,
                                    [
                                        "comments?",
                                        "댓글",
                                        "评论"
                                    ]
                                );
                            }

                            if (!shares) {
                                shares = findNumber(
                                    raw,
                                    [
                                        "shares?",
                                        "공유",
                                        "分享"
                                    ]
                                );
                            }

                            const lines = raw
                                .split("\n")
                                .map(value => value.trim())
                                .filter(Boolean);

                            const numericLines = lines.filter(
                                value =>
                                    /^[\d,.]+(?:\.\d+)?\s*[KMB]?$/i.test(
                                        value
                                    )
                            );

                            if (!views && numericLines.length > 0) {
                                views = numericLines[0];
                            }

                            return {
                                href,
                                title,
                                thumbnail,
                                raw_text: raw.slice(0, 1000),
                                views,
                                likes,
                                comments,
                                shares
                            };
                        })
                        .filter(Boolean);
                }
                """
            ) or []

        except Exception as exc:
            print("[SourceCandidateParser.parse_tiktok]", exc)
            raw_items = []

        for raw_item in raw_items:
            try:
                href = self.normalize_url(
                    raw_item.get("href", "")
                )

                if not href:
                    continue

                if "/video/" not in href.lower():
                    continue

                title = self.clean_text(
                    raw_item.get("title")
                    or raw_item.get("raw_text")
                    or ""
                )

                thumbnail = self.normalize_url(
                    raw_item.get("thumbnail", "")
                )

                views = self.clean_metric_text(
                    raw_item.get("views")
                )

                likes = self.clean_metric_text(
                    raw_item.get("likes")
                )

                comments = self.clean_metric_text(
                    raw_item.get("comments")
                )

                shares = self.clean_metric_text(
                    raw_item.get("shares")
                )

                view_count = self.parse_count(views)
                like_count = self.parse_count(likes)
                comment_count = self.parse_count(comments)
                share_count = self.parse_count(shares)

                score = self.calculate_engagement_score(
                    view_count=view_count,
                    like_count=like_count,
                    comment_count=comment_count,
                    share_count=share_count,
                )

                items.append(
                    self.clean_candidate(
                        platform="tiktok",
                        rank=len(items) + 1,
                        title=title,
                        url=href,
                        thumbnail=thumbnail,
                        score=score,
                        views=views,
                        likes=likes,
                        comments=comments,
                        shares=shares,
                        view_count=view_count,
                        like_count=like_count,
                        comment_count=comment_count,
                        share_count=share_count,
                    )
                )

            except Exception:
                continue

        return self.dedupe(items)

    def parse_taobao(self, page):
        items = []

        links = page.locator(
            "a[href*='item.taobao.com'], "
            "a[href*='detail.tmall.com']"
        )

        count = min(links.count(), 40)

        for i in range(count):
            try:
                link = links.nth(i)
                href = link.get_attribute("href") or ""

                title = (
                    link.get_attribute("title")
                    or link.inner_text(timeout=1000)
                    or ""
                )

                img = link.locator("img").first
                thumbnail = ""

                if img.count():
                    thumbnail = (
                        img.get_attribute("src")
                        or img.get_attribute("data-src")
                        or img.get_attribute("data-ks-lazyload")
                        or ""
                    )

                items.append(
                    self.clean_candidate(
                        platform="taobao",
                        rank=len(items) + 1,
                        title=title,
                        url=href,
                        thumbnail=thumbnail,
                    )
                )

            except Exception:
                continue

        return self.dedupe(items)

    def parse_1688(self, page):
        items = []

        links = page.locator(
            "a[href*='detail.1688.com']"
        )

        count = min(links.count(), 40)

        for i in range(count):
            try:
                link = links.nth(i)
                href = link.get_attribute("href") or ""

                title = (
                    link.get_attribute("title")
                    or link.inner_text(timeout=1000)
                    or ""
                )

                img = link.locator("img").first
                thumbnail = ""

                if img.count():
                    thumbnail = (
                        img.get_attribute("src")
                        or img.get_attribute("data-src")
                        or ""
                    )

                items.append(
                    self.clean_candidate(
                        platform="1688",
                        rank=len(items) + 1,
                        title=title,
                        url=href,
                        thumbnail=thumbnail,
                    )
                )

            except Exception:
                continue

        return self.dedupe(items)

    def clean_candidate(
        self,
        platform,
        rank,
        title,
        url,
        thumbnail,
        score=0,
        views="",
        likes="",
        comments="",
        shares="",
        view_count=0,
        like_count=0,
        comment_count=0,
        share_count=0,
    ):
        title = self.clean_text(title)
        url = self.normalize_url(url)
        thumbnail = self.normalize_url(thumbnail)

        return {
            "rank": rank,
            "platform": platform,
            "title": title,
            "url": url,
            "thumbnail": thumbnail,
            "views": views,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "view_count": int(view_count or 0),
            "like_count": int(like_count or 0),
            "comment_count": int(comment_count or 0),
            "share_count": int(share_count or 0),
            "score": int(score or 0),
            "purpose": "실제 검색 결과 후보",
        }

    def clean_text(self, text):
        text = str(text or "")
        text = " ".join(text.split())

        return text[:200]

    def clean_metric_text(self, value):
        value = str(value or "").strip()
        value = " ".join(value.split())

        return value[:50]

    def parse_count(self, value):
        if value is None:
            return 0

        if isinstance(value, bool):
            return 0

        if isinstance(value, int):
            return max(value, 0)

        if isinstance(value, float):
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
            r"(\d+(?:\.\d+)?)"
            r"([kmbw万億亿천만억]?)",
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

        return max(
            int(number * multiplier),
            0,
        )

    def calculate_engagement_score(
        self,
        view_count=0,
        like_count=0,
        comment_count=0,
        share_count=0,
    ):
        views = max(int(view_count or 0), 0)
        likes = max(int(like_count or 0), 0)
        comments = max(int(comment_count or 0), 0)
        shares = max(int(share_count or 0), 0)

        if (
            views == 0
            and likes == 0
            and comments == 0
            and shares == 0
        ):
            return 0

        score = 0.0

        if views > 0:
            score += min(
                65.0,
                math.log10(views + 1) * 10.5,
            )

        if likes > 0:
            score += min(
                15.0,
                math.log10(likes + 1) * 3.0,
            )

        if comments > 0:
            score += min(
                7.0,
                math.log10(comments + 1) * 1.7,
            )

        if shares > 0:
            score += min(
                5.0,
                math.log10(shares + 1) * 1.2,
            )

        if views > 0:
            engagement_rate = (
                likes
                + comments * 3
                + shares * 4
            ) / views

            score += min(
                8.0,
                engagement_rate * 100.0,
            )

        return int(
            min(
                max(round(score), 0),
                99,
            )
        )

    def normalize_url(self, url):
        url = str(url or "").strip()

        if not url:
            return ""

        if url.startswith("//"):
            return "https:" + url

        if url.startswith("/"):
            return urljoin(
                "https://www.tiktok.com",
                url,
            )

        return url

    def dedupe(self, items):
        seen = set()
        result = []

        sorted_items = sorted(
            items,
            key=lambda item: (
                int(item.get("score", 0) or 0),
                int(item.get("view_count", 0) or 0),
                int(item.get("like_count", 0) or 0),
                int(item.get("comment_count", 0) or 0),
            ),
            reverse=True,
        )

        for item in sorted_items:
            url = item.get("url") or ""
            title = item.get("title") or ""

            key = re.sub(
                r"[?#].*$",
                "",
                url or title,
            )

            if not key:
                continue

            if key in seen:
                continue

            seen.add(key)

            item["rank"] = len(result) + 1
            result.append(item)

        return result