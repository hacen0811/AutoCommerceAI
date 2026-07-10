from modules.source.source_candidate_parser import SourceCandidateParser


class SourceCollector:
    """
    Sprint 52-1

    역할
    -----------------
    검색 페이지에서 실제 후보를 수집한다.

    담당
    - Playwright page 사용
    - Parser 호출
    - 후보 정리
    - 상위 후보 반환

    담당하지 않는 것
    - 다운로드
    - AI 점수
    - 후보 선택
    """

    def __init__(self):
        self.parser = SourceCandidateParser()

    def collect(self, page, platform):
        """
        현재 열린 Playwright page에서 후보 수집
        """

        try:
            page.wait_for_load_state("networkidle", timeout=10000)
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
            candidates,
            platform,
        )

    def post_process(self, candidates, platform):
        cleaned = []

        for item in candidates:

            if not isinstance(item, dict):
                continue

            title = str(item.get("title", "")).strip()

            if len(title) < 2:
                continue

            cleaned.append(
                {
                    "rank": len(cleaned) + 1,
                    "platform": platform,
                    "title": title,
                    "url": item.get("url", ""),
                    "thumbnail": item.get("thumbnail", ""),
                    "purpose": item.get(
                        "purpose",
                        "실제 검색 결과",
                    ),
                    "score": item.get("score", 0),
                }
            )

        return cleaned

    def top(self, page, platform, limit=10):
        """
        상위 N개만 반환
        """

        items = self.collect(page, platform)

        return items[:limit]