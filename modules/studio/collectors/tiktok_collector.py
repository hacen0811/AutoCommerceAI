from __future__ import annotations

import re
from typing import Any, Dict, List
from urllib.parse import quote_plus

from .base_collector import BaseSiteCollector, CollectedVideo


class TikTokCollector(BaseSiteCollector):
    """
    Sprint 58 TikTok Collector

    역할:
    - TikTok 검색 결과 화면에서 영상 후보 수집
    - 검색 결과 영상 URL만 허용
    - 검색어와 관련 없는 추천·인기 영상 제외
    - 상품 관련성 60%, 반응 통계 40%로 후보 점수 계산
    - 조회수, 좋아요, 댓글, 공유 수집
    """

    platform = "tiktok"
    COLLECTOR_VERSION = "tiktok-collector-58-2"

    def search_url(self, keyword: str) -> str:
        return (
            "https://www.tiktok.com/search"
            f"?q={quote_plus(keyword or '')}"
        )

    def collect(
        self,
        page,
        keyword: str,
        url: str = "",
        limit: int = 10,
    ) -> Dict:
        keyword = str(keyword or "").strip()
        target_url = url or self.search_url(keyword)

        rows: List[CollectedVideo] = []
        diagnostics: Dict[str, Any] = {}

        rejected_unrelated = 0
        rejected_invalid_url = 0
        rejected_junk = 0

        try:
            page.goto(
                target_url,
                wait_until="domcontentloaded",
                timeout=self.timeout_ms,
            )

            page.wait_for_timeout(4000)
            self.slow_scroll(page, 4)
            page.wait_for_timeout(1500)

            body = self.body_text(page)
            debug = self.save_debug(
                page,
                self.platform,
            )

            items = page.evaluate(
                r"""
                () => {
                    const parseCandidate = (el) => {
                        const link =
                            el.tagName?.toLowerCase() === "a"
                                ? el
                                : el.querySelector(
                                    'a[href*="/video/"]'
                                );

                        const href = link
                            ? (
                                link.href
                                || link.getAttribute("href")
                                || ""
                            )
                            : "";

                        const img = el.querySelector("img");
                        const video = el.querySelector("video");

                        const raw = (
                            el.innerText
                            || el.textContent
                            || ""
                        )
                            .replace(/\u00a0/g, " ")
                            .trim();

                        const title = (
                            link?.title
                            || link?.getAttribute("aria-label")
                            || img?.alt
                            || raw.split("\n")[0]
                            || ""
                        ).trim();

                        const thumbnail = img
                            ? (
                                img.currentSrc
                                || img.src
                                || img.getAttribute("src")
                                || img.getAttribute("srcset")
                                || ""
                            )
                            : (
                                video
                                    ? (video.poster || "")
                                    : ""
                            );

                        const textParts = raw
                            .split("\n")
                            .map(value => value.trim())
                            .filter(Boolean);

                        const findValue = (patterns) => {
                            for (const pattern of patterns) {
                                const match = raw.match(pattern);

                                if (match && match[1]) {
                                    return match[1].trim();
                                }
                            }

                            return "";
                        };

                        const viewPatterns = [
                            /([\d,.]+(?:\.\d+)?\s*[KMB]?)\s*(?:views?|조회수?)/i,
                            /(?:views?|조회수?)\s*([\d,.]+(?:\.\d+)?\s*[KMB]?)/i
                        ];

                        const likePatterns = [
                            /([\d,.]+(?:\.\d+)?\s*[KMB]?)\s*(?:likes?|좋아요)/i,
                            /(?:likes?|좋아요)\s*([\d,.]+(?:\.\d+)?\s*[KMB]?)/i
                        ];

                        const commentPatterns = [
                            /([\d,.]+(?:\.\d+)?\s*[KMB]?)\s*(?:comments?|댓글)/i,
                            /(?:comments?|댓글)\s*([\d,.]+(?:\.\d+)?\s*[KMB]?)/i
                        ];

                        const sharePatterns = [
                            /([\d,.]+(?:\.\d+)?\s*[KMB]?)\s*(?:shares?|공유)/i,
                            /(?:shares?|공유)\s*([\d,.]+(?:\.\d+)?\s*[KMB]?)/i
                        ];

                        let viewText = findValue(viewPatterns);
                        let likeText = findValue(likePatterns);
                        let commentText = findValue(
                            commentPatterns
                        );
                        let shareText = findValue(
                            sharePatterns
                        );

                        const numericParts = textParts.filter(
                            value =>
                                /^[\d,.]+(?:\.\d+)?\s*[KMB]?$/i
                                    .test(value)
                        );

                        if (
                            !viewText
                            && numericParts.length >= 1
                        ) {
                            viewText = numericParts[0];
                        }

                        const selectors = {
                            views: [
                                '[data-e2e="video-views"]',
                                '[data-e2e*="video-views"]',
                                '[data-e2e*="view-count"]',
                                '[data-e2e*="views"]'
                            ],
                            likes: [
                                '[data-e2e="like-count"]',
                                '[data-e2e*="like-count"]',
                                '[data-e2e*="likes"]'
                            ],
                            comments: [
                                '[data-e2e="comment-count"]',
                                '[data-e2e*="comment-count"]',
                                '[data-e2e*="comments"]'
                            ],
                            shares: [
                                '[data-e2e="share-count"]',
                                '[data-e2e*="share-count"]',
                                '[data-e2e*="shares"]'
                            ]
                        };

                        const readSelectorText = (list) => {
                            for (const selector of list) {
                                const node = el.querySelector(
                                    selector
                                );

                                if (!node) {
                                    continue;
                                }

                                const value = (
                                    node.innerText
                                    || node.textContent
                                    || node.getAttribute(
                                        "aria-label"
                                    )
                                    || ""
                                ).trim();

                                if (value) {
                                    return value;
                                }
                            }

                            return "";
                        };

                        viewText = (
                            readSelectorText(selectors.views)
                            || viewText
                        );

                        likeText = (
                            readSelectorText(selectors.likes)
                            || likeText
                        );

                        commentText = (
                            readSelectorText(
                                selectors.comments
                            )
                            || commentText
                        );

                        shareText = (
                            readSelectorText(selectors.shares)
                            || shareText
                        );

                        return {
                            href,
                            title,
                            raw_text: raw.slice(0, 1500),
                            thumbnail,
                            view_text: viewText,
                            like_text: likeText,
                            comment_text: commentText,
                            share_text: shareText
                        };
                    };

                    /*
                    검색 결과 카드 중심으로 수집합니다.

                    마지막 a[href*="/video/"]는
                    TikTok UI 구조 변경 시 검색 결과를 놓치지 않기 위한
                    최소 fallback입니다.
                    */
                    const selectors = [
                        'div[data-e2e*="search-card"]',
                        'div[data-e2e*="search-video-item"]',
                        'div[data-e2e*="video-item"]',
                        'div[data-e2e*="user-post-item"]',
                        'article a[href*="/video/"]',
                        'a[href*="/video/"]'
                    ];

                    const nodes = [];

                    for (const selector of selectors) {
                        document
                            .querySelectorAll(selector)
                            .forEach(node => nodes.push(node));
                    }

                    const uniqueNodes = Array.from(
                        new Set(nodes)
                    ).slice(0, 1000);

                    return uniqueNodes
                        .map(parseCandidate)
                        .filter(item => {
                            const href = (
                                item.href
                                || ""
                            ).toLowerCase();

                            return (
                                href.includes("tiktok.com")
                                && href.includes("/video/")
                            );
                        });
                }
                """
            ) or []

            for item in items:
                href = self.normalize_url(
                    item.get("href", "")
                )

                href_lower = href.lower()

                if (
                    "tiktok.com" not in href_lower
                    or "/video/" not in href_lower
                ):
                    rejected_invalid_url += 1
                    continue

                raw_text = str(
                    item.get("raw_text")
                    or ""
                ).strip()

                title = str(
                    item.get("title")
                    or raw_text
                    or ""
                ).strip()[:300]

                thumbnail = str(
                    item.get("thumbnail")
                    or ""
                ).strip()

                if self.is_junk_text(
                    title,
                    href,
                ):
                    rejected_junk += 1
                    continue

                if len(title) < 2:
                    rejected_junk += 1
                    continue

                relevance = self._keyword_relevance(
                    keyword=keyword,
                    title=title,
                    raw_text=raw_text,
                    href=href,
                )

                
                #검색어가 있는데 직접 일치 단서가 전혀 없으면
                #TikTok 추천·인기 영상으로 보고 제외합니다.
                
                if (
                    keyword
                    and relevance["matched_count"] <= 0
                ):
                    rejected_unrelated += 1
                    continue

                view_text = str(
                    item.get("view_text")
                    or ""
                ).strip()

                like_text = str(
                    item.get("like_text")
                    or ""
                ).strip()

                comment_text = str(
                    item.get("comment_text")
                    or ""
                ).strip()

                share_text = str(
                    item.get("share_text")
                    or ""
                ).strip()

                view_count = self.parse_count(
                    view_text
                )
                like_count = self.parse_count(
                    like_text
                )
                comment_count = self.parse_count(
                    comment_text
                )
                share_count = self.parse_count(
                    share_text
                )

                relevance_score = self.score_item(
                    keyword=keyword,
                    title=title,
                    href=href,
                    thumb=thumbnail,
                )

                relevance_score = max(
                    relevance_score,
                    relevance["score"],
                )

                metadata_score = self.engagement_score(
                    view_count=view_count,
                    like_count=like_count,
                    comment_count=comment_count,
                    share_count=share_count,
                )

                if metadata_score > 0:
                    final_score = round(
                        relevance_score * 0.60
                        + metadata_score * 0.40
                    )
                else:
                    final_score = round(
                        relevance_score
                    )

                matched_text = ", ".join(
                    relevance["matched_tokens"][:5]
                )

                note_parts = [
                    "TikTok 검색 결과 후보",
                    "상품 관련성 60%·반응 통계 40% 반영",
                ]

                if matched_text:
                    note_parts.append(
                        f"일치 검색어: {matched_text}"
                    )

                note_parts.append(
                    f"collector={self.COLLECTOR_VERSION}"
                )

                rows.append(
                    CollectedVideo(
                        platform=self.platform,
                        title=title,
                        url=href,
                        keyword=keyword,
                        score=min(
                            max(
                                int(final_score),
                                0,
                            ),
                            99,
                        ),
                        thumbnail=thumbnail,
                        screenshot=debug.get(
                            "screenshot",
                            "",
                        ),
                        views=view_text,
                        likes=like_text,
                        comments=comment_text,
                        shares=share_text,
                        view_count=view_count,
                        like_count=like_count,
                        comment_count=comment_count,
                        share_count=share_count,
                        note=" / ".join(note_parts),
                    )
                )

            diagnostics = {
                "platform": self.platform,
                "collector_version": (
                    self.COLLECTOR_VERSION
                ),
                "requested_keyword": keyword,
                "requested_url": target_url,
                "current_url": page.url,
                "page_title": page.title(),
                "dom_item_count": len(items),
                "extracted_count": len(rows),
                "rejected_unrelated_count": (
                    rejected_unrelated
                ),
                "rejected_invalid_url_count": (
                    rejected_invalid_url
                ),
                "rejected_junk_count": (
                    rejected_junk
                ),
                "metadata_count": sum(
                    1
                    for row in rows
                    if (
                        row.view_count > 0
                        or row.like_count > 0
                        or row.comment_count > 0
                        or row.share_count > 0
                    )
                ),
                "blocked_hint": self.blocked_hint(
                    page,
                    body,
                ),
                **debug,
                "sample_items": items[:5],
            }

        except Exception as exc:
            diagnostics = {
                "platform": self.platform,
                "collector_version": (
                    self.COLLECTOR_VERSION
                ),
                "requested_keyword": keyword,
                "requested_url": target_url,
                "error": str(exc)[:800],
            }

        final_rows = self.dedupe(
            rows,
            limit,
        )

        diagnostics["final_count"] = len(
            final_rows
        )

        return {
            "results": final_rows,
            "diagnostics": diagnostics,
        }

    def _keyword_relevance(
        self,
        keyword: str,
        title: str,
        raw_text: str,
        href: str,
    ) -> Dict[str, Any]:
        """
        검색어가 영상 제목·설명·해시태그에 실제로 포함되는지 확인합니다.

        지나치게 짧은 조사·수식어는 제외하고,
        완전 검색어 또는 의미 있는 토큰 일치를 사용합니다.
        """

        keyword_normalized = self._normalize_text(
            keyword
        )

        target_text = self._normalize_text(
            f"{title} {raw_text} {href}"
        )

        tokens = self._keyword_tokens(
            keyword
        )

        matched_tokens = [
            token
            for token in tokens
            if token in target_text
        ]

        full_match = bool(
            keyword_normalized
            and keyword_normalized in target_text
        )

        matched_count = len(
            matched_tokens
        )

        token_count = len(tokens)

        if full_match:
            score = 95

        elif token_count > 0:
            match_ratio = (
                matched_count / token_count
            )

            if match_ratio >= 0.75:
                score = 90

            elif match_ratio >= 0.50:
                score = 80

            elif matched_count >= 2:
                score = 72

            elif matched_count == 1:
                score = 62

            else:
                score = 0

        else:
            score = 0

        return {
            "score": score,
            "full_match": full_match,
            "matched_count": matched_count,
            "token_count": token_count,
            "matched_tokens": matched_tokens,
        }

    def _keyword_tokens(
        self,
        keyword: str,
    ) -> List[str]:
        normalized = self._normalize_text(
            keyword
        )

        if not normalized:
            return []

        stopwords = {
            "추천",
            "영상",
            "사용",
            "리뷰",
            "후기",
            "제품",
            "상품",
            "좋은",
            "인기",
            "최고",
            "신상",
            "video",
            "review",
            "tiktok",
            "douyin",
            "使用",
            "测评",
            "推薦",
            "推荐",
            "好物",
            "视频",
            "教程",
            "效果",
            "开箱",
        }

        raw_tokens = re.findall(
            r"[가-힣]{2,}|[a-z0-9]{2,}|[\u3400-\u9fff]{2,}",
            normalized,
        )

        tokens: List[str] = []
        seen = set()

        for token in raw_tokens:
            token = token.strip()

            if not token:
                continue

            if token in stopwords:
                continue

            if token in seen:
                continue

            seen.add(token)
            tokens.append(token)

        
        #검색어가 모두 일반 단어라 제거된 경우에는
        #원래 토큰을 최소한 유지합니다.
        
        if not tokens:
            fallback_tokens = re.findall(
                r"[가-힣]{2,}|[a-z0-9]{2,}|[\u3400-\u9fff]{2,}",
                normalized,
            )

            for token in fallback_tokens:
                if token in seen:
                    continue

                seen.add(token)
                tokens.append(token)

        return tokens

    def _normalize_text(
        self,
        value: Any,
    ) -> str:
        text = str(
            value or ""
        ).lower()

        text = text.replace(
            "#",
            " ",
        )

        text = re.sub(
            r"[^0-9a-z가-힣\u3400-\u9fff]+",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()