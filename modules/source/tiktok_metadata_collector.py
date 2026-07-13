from __future__ import annotations

from typing import Any, Dict, List

from modules.studio.network.response_sniffer import ResponseSniffer


class TikTokMetadataCollector:
    """
    Sprint 58

    TikTok 후보 영상 상세 페이지를 순회하며
    네트워크 응답에서 실제 통계를 수집합니다.

    수집 항목:
    - view_count
    - like_count
    - comment_count
    - share_count

    입력:
    - Playwright page
    - 후보 dict 목록

    출력:
    - 메타데이터가 병합된 후보 dict 목록
    """

    def __init__(
        self,
        wait_ms: int = 3500,
        max_candidates: int = 20,
    ):
        self.wait_ms = max(int(wait_ms or 3500), 1000)
        self.max_candidates = max(
            int(max_candidates or 20),
            1,
        )

    def enrich(
        self,
        page,
        candidates: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if not page:
            return self._copy_candidates(candidates)

        output = self._copy_candidates(candidates)

        for index, candidate in enumerate(
            output[: self.max_candidates],
            start=1,
        ):
            url = str(
                candidate.get("url")
                or ""
            ).strip()

            if not self._is_tiktok_video_url(url):
                continue

            print(
                "[TikTokMetadataCollector] 상세 통계 수집:",
                index,
                url,
            )

            stats = self.collect_one(
                page=page,
                url=url,
            )

            self._merge_stats(
                candidate=candidate,
                stats=stats,
            )

        return output

    def collect_one(
        self,
        page,
        url: str,
    ) -> Dict[str, int]:
        sniffer = ResponseSniffer(
            max_items=100,
        )

        sniffer.start(page)

        try:
            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000,
            )
        except Exception as exc:
            print(
                "[TikTokMetadataCollector] 페이지 이동 경고:",
                str(exc)[:300],
            )

        try:
            page.wait_for_timeout(
                self.wait_ms
            )
        except Exception:
            pass

        try:
            page.wait_for_load_state(
                "networkidle",
                timeout=10000,
            )
        except Exception:
            pass

        try:
            page.mouse.wheel(
                0,
                700,
            )
            page.wait_for_timeout(1000)
        except Exception:
            pass

        video_id = sniffer.extract_video_id(
            url
        )

        stats_map = sniffer.extract_tiktok_stats()

        stats = stats_map.get(
            video_id,
            {},
        )

        if stats:
            return self._normalize_stats(
                stats
            )

        dom_stats = self._extract_dom_stats(
            page
        )

        if self._has_stats(dom_stats):
            return dom_stats

        return {
            "view_count": 0,
            "like_count": 0,
            "comment_count": 0,
            "share_count": 0,
        }

    def _extract_dom_stats(
        self,
        page,
    ) -> Dict[str, int]:
        try:
            values = page.evaluate(
                r"""
                () => {
                    const read = (selectors) => {
                        for (const selector of selectors) {
                            const node = document.querySelector(
                                selector
                            );

                            if (!node) {
                                continue;
                            }

                            const value = (
                                node.innerText
                                || node.textContent
                                || node.getAttribute("aria-label")
                                || ""
                            ).trim();

                            if (value) {
                                return value;
                            }
                        }

                        return "";
                    };

                    return {
                        views: read([
                            '[data-e2e="video-views"]',
                            '[data-e2e*="view-count"]',
                            '[data-e2e*="play-count"]'
                        ]),
                        likes: read([
                            '[data-e2e="like-count"]',
                            '[data-e2e*="browse-like-count"]',
                            '[data-e2e*="like-count"]'
                        ]),
                        comments: read([
                            '[data-e2e="comment-count"]',
                            '[data-e2e*="browse-comment-count"]',
                            '[data-e2e*="comment-count"]'
                        ]),
                        shares: read([
                            '[data-e2e="share-count"]',
                            '[data-e2e*="browse-share-count"]',
                            '[data-e2e*="share-count"]'
                        ])
                    };
                }
                """
            ) or {}

        except Exception:
            values = {}

        return {
            "view_count": self._parse_count(
                values.get("views")
            ),
            "like_count": self._parse_count(
                values.get("likes")
            ),
            "comment_count": self._parse_count(
                values.get("comments")
            ),
            "share_count": self._parse_count(
                values.get("shares")
            ),
        }

    def _merge_stats(
        self,
        candidate: Dict[str, Any],
        stats: Dict[str, int],
    ) -> None:
        current_views = self._safe_int(
            candidate.get("view_count")
        )
        current_likes = self._safe_int(
            candidate.get("like_count")
        )
        current_comments = self._safe_int(
            candidate.get("comment_count")
        )
        current_shares = self._safe_int(
            candidate.get("share_count")
        )

        candidate["view_count"] = max(
            current_views,
            self._safe_int(
                stats.get("view_count")
            ),
        )

        candidate["like_count"] = max(
            current_likes,
            self._safe_int(
                stats.get("like_count")
            ),
        )

        candidate["comment_count"] = max(
            current_comments,
            self._safe_int(
                stats.get("comment_count")
            ),
        )

        candidate["share_count"] = max(
            current_shares,
            self._safe_int(
                stats.get("share_count")
            ),
        )

        candidate["views"] = str(
            candidate["view_count"]
        )
        candidate["likes"] = str(
            candidate["like_count"]
        )
        candidate["comments"] = str(
            candidate["comment_count"]
        )
        candidate["shares"] = str(
            candidate["share_count"]
        )

        if self._has_stats(stats):
            candidate["metadata_source"] = (
                "tiktok-video-detail"
            )
        else:
            candidate["metadata_source"] = (
                candidate.get("metadata_source")
                or "playwright-dom"
            )

    def _normalize_stats(
        self,
        stats: Dict[str, Any],
    ) -> Dict[str, int]:
        return {
            "view_count": self._safe_int(
                stats.get("view_count")
            ),
            "like_count": self._safe_int(
                stats.get("like_count")
            ),
            "comment_count": self._safe_int(
                stats.get("comment_count")
            ),
            "share_count": self._safe_int(
                stats.get("share_count")
            ),
        }

    def _copy_candidates(
        self,
        candidates: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        output = []

        for candidate in candidates or []:
            if isinstance(candidate, dict):
                output.append(
                    dict(candidate)
                )

        return output

    def _is_tiktok_video_url(
        self,
        url: str,
    ) -> bool:
        lower_url = str(
            url or ""
        ).lower()

        return (
            "tiktok.com" in lower_url
            and "/video/" in lower_url
        )

    def _has_stats(
        self,
        stats: Dict[str, Any],
    ) -> bool:
        return any(
            self._safe_int(value) > 0
            for value in stats.values()
        )

    def _safe_int(
        self,
        value: Any,
    ) -> int:
        try:
            return max(
                int(float(value or 0)),
                0,
            )
        except (TypeError, ValueError):
            return 0

    def _parse_count(
        self,
        value: Any,
    ) -> int:
        if value is None:
            return 0

        if isinstance(value, bool):
            return 0

        if isinstance(value, (int, float)):
            return self._safe_int(value)

        text = str(
            value or ""
        ).strip().lower()

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
            .strip()
        )

        multipliers = {
            "k": 1_000,
            "m": 1_000_000,
            "b": 1_000_000_000,
            "w": 10_000,
            "만": 10_000,
            "억": 100_000_000,
            "万": 10_000,
            "亿": 100_000_000,
        }

        suffix = text[-1:] if text else ""
        multiplier = multipliers.get(
            suffix,
            1,
        )

        if suffix in multipliers:
            text = text[:-1]

        try:
            return max(
                int(float(text) * multiplier),
                0,
            )
        except (TypeError, ValueError):
            return 0