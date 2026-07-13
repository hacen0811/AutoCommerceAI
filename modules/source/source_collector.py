from __future__ import annotations

from modules.source.source_candidate_parser import SourceCandidateParser


class SourceCollector:
    """
    Sprint 57

    현재 열린 Playwright 페이지에서 실제 후보를 수집하고 정리합니다.

    역할:
    - SourceCandidateParser 호출
    - 후보 필드 정리
    - TikTok/Douyin 메타데이터 보존
    - 조회수 기반 순위 정렬

    담당하지 않는 것:
    - 다운로드
    - 최종 후보 채택
    - 영상 분석
    """

    def __init__(self):
        self.parser = SourceCandidateParser()

    def collect(self, page, platform):
        try:
            page.wait_for_load_state(
                "networkidle",
                timeout=10000,
            )
        except Exception:
            pass

        try:
            candidates = self.parser.parse(
                page=page,
                platform=platform,
            )
        except Exception as exc:
            print("[SourceCollector]", exc)
            candidates = []

        return self.post_process(
            candidates=candidates,
            platform=platform,
        )

    def post_process(self, candidates, platform):
        cleaned = []

        for item in candidates:
            if not isinstance(item, dict):
                continue

            title = str(
                item.get("title", "")
            ).strip()

            url = str(
                item.get("url", "")
            ).strip()

            if len(title) < 2:
                continue

            if not url:
                continue

            cleaned.append(
                {
                    "rank": 0,
                    "platform": str(
                        item.get("platform")
                        or platform
                        or ""
                    ),
                    "title": title,
                    "url": url,
                    "thumbnail": item.get(
                        "thumbnail",
                        "",
                    ),
                    "purpose": item.get(
                        "purpose",
                        "실제 검색 결과 후보",
                    ),

                    # 원문 메타데이터
                    "views": item.get(
                        "views",
                        "",
                    ),
                    "likes": item.get(
                        "likes",
                        "",
                    ),
                    "comments": item.get(
                        "comments",
                        "",
                    ),
                    "shares": item.get(
                        "shares",
                        "",
                    ),

                    # 정규화된 메타데이터
                    "view_count": self.safe_int(
                        item.get("view_count", 0)
                    ),
                    "like_count": self.safe_int(
                        item.get("like_count", 0)
                    ),
                    "comment_count": self.safe_int(
                        item.get("comment_count", 0)
                    ),
                    "share_count": self.safe_int(
                        item.get("share_count", 0)
                    ),

                    "score": self.safe_int(
                        item.get("score", 0)
                    ),
                }
            )

        cleaned.sort(
            key=lambda item: (
                item.get("score", 0),
                item.get("view_count", 0),
                item.get("like_count", 0),
                item.get("comment_count", 0),
                item.get("share_count", 0),
            ),
            reverse=True,
        )

        for index, item in enumerate(
            cleaned,
            start=1,
        ):
            item["rank"] = index

        return cleaned

    def top(
        self,
        page,
        platform,
        limit=10,
    ):
        items = self.collect(
            page=page,
            platform=platform,
        )

        try:
            limit = max(
                int(limit),
                1,
            )
        except (TypeError, ValueError):
            limit = 10

        return items[:limit]

    def safe_int(self, value):
        try:
            return max(
                int(value or 0),
                0,
            )
        except (TypeError, ValueError):
            return 0