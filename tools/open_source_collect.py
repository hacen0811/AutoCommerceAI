from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright


BASE_DIR = Path(__file__).resolve().parents[1]
PROFILE_DIR = BASE_DIR / "browser_profile" / "source_sites"
EXPORT_DIR = BASE_DIR / "exports" / "source_candidates"

sys.path.insert(0, str(BASE_DIR))

from modules.source.source_collector import SourceCollector
from modules.source.tiktok_metadata_collector import TikTokMetadataCollector
from modules.studio.network.response_sniffer import ResponseSniffer
from modules.video.video_candidate_selector import (
    VideoCandidateSelector,
)

def detect_platform(url: str) -> str:
    host = urlparse(url).netloc.lower()

    if "taobao" in host or "tmall" in host:
        return "taobao"

    if "1688" in host:
        return "1688"

    if "douyin" in host:
        return "douyin"

    if "tiktok" in host:
        return "tiktok"

    return "unknown"


def safe_int(value) -> int:
    try:
        return max(int(float(value or 0)), 0)
    except (TypeError, ValueError):
        return 0


def calculate_candidate_score(candidate: dict) -> int:
    """
    Sprint 57 조회수·반응 기반 후보 점수.

    반영 순서:
    1. 조회수
    2. 좋아요
    3. 댓글
    4. 공유
    5. 참여율
    """

    views = safe_int(candidate.get("view_count"))
    likes = safe_int(candidate.get("like_count"))
    comments = safe_int(candidate.get("comment_count"))
    shares = safe_int(candidate.get("share_count"))

    if (
        views == 0
        and likes == 0
        and comments == 0
        and shares == 0
    ):
        return safe_int(candidate.get("score"))

    score = 0.0

    # 조회수: 최대 65점
    if views > 0:
        score += min(
            65.0,
            math.log10(views + 1) * 10.5,
        )

    # 좋아요: 최대 15점
    if likes > 0:
        score += min(
            15.0,
            math.log10(likes + 1) * 3.0,
        )

    # 댓글: 최대 7점
    if comments > 0:
        score += min(
            7.0,
            math.log10(comments + 1) * 1.7,
        )

    # 공유: 최대 5점
    if shares > 0:
        score += min(
            5.0,
            math.log10(shares + 1) * 1.2,
        )

    # 참여율: 최대 8점
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


def sort_and_rank_candidates(
    candidates: list,
) -> list:
    cleaned = []

    for candidate in candidates or []:
        if not isinstance(candidate, dict):
            continue

        item = dict(candidate)

        item["view_count"] = safe_int(
            item.get("view_count")
        )
        item["like_count"] = safe_int(
            item.get("like_count")
        )
        item["comment_count"] = safe_int(
            item.get("comment_count")
        )
        item["share_count"] = safe_int(
            item.get("share_count")
        )

        item["score"] = calculate_candidate_score(
            item
        )

        cleaned.append(item)

    cleaned.sort(
        key=lambda item: (
            safe_int(item.get("score")),
            safe_int(item.get("view_count")),
            safe_int(item.get("like_count")),
            safe_int(item.get("comment_count")),
            safe_int(item.get("share_count")),
        ),
        reverse=True,
    )

    for index, item in enumerate(
        cleaned,
        start=1,
    ):
        item["rank"] = index

    return cleaned


def save_candidates(
    platform: str,
    candidates: list,
) -> Path:
    EXPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = EXPORT_DIR / (
        f"{platform}_latest_candidates.json"
    )

    path.write_text(
        json.dumps(
            candidates,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return path


def is_login_or_blocked_page(page) -> bool:
    try:
        current_url = str(page.url or "").lower()
    except Exception:
        current_url = ""

    try:
        title = str(page.title() or "").lower()
    except Exception:
        title = ""

    try:
        body_text = (
            page.locator("body")
            .inner_text(timeout=5000)
            .lower()
        )
    except Exception:
        body_text = ""

    combined = (
        f"{current_url}\n"
        f"{title}\n"
        f"{body_text}"
    )

    blocked_words = [
        "/login",
        "login",
        "log in",
        "sign in",
        "captcha",
        "verify",
        "verification",
        "security check",
        "로그인",
        "인증",
        "验证码",
        "安全验证",
    ]

    return any(
        word in combined
        for word in blocked_words
    )


def wait_for_tiktok_results(
    page,
    timeout_ms: int = 25000,
) -> bool:
    selectors = [
        "a[href*='/video/']",
        "div[data-e2e*='search-card']",
        "div[data-e2e*='video-item']",
        "div[data-e2e*='user-post-item']",
    ]

    for selector in selectors:
        try:
            page.wait_for_selector(
                selector,
                timeout=timeout_ms,
                state="attached",
            )
            return True
        except Exception:
            continue

    return False


def wait_for_other_results(
    page,
    platform: str,
) -> bool:
    selectors = {
        "taobao": (
            "a[href*='item.taobao.com'], "
            "a[href*='detail.tmall.com']"
        ),
        "1688": (
            "a[href*='detail.1688.com']"
        ),
        "douyin": (
            "a[href*='/video/'], "
            "a[href*='/user/']"
        ),
    }

    selector = selectors.get(platform)

    if not selector:
        return False

    try:
        page.wait_for_selector(
            selector,
            timeout=20000,
            state="attached",
        )
        return True
    except Exception:
        return False


def print_page_status(
    page,
    platform: str,
    result_found: bool,
) -> None:
    try:
        page_title = page.title()
    except Exception:
        page_title = ""

    try:
        current_url = page.url
    except Exception:
        current_url = ""

    blocked = is_login_or_blocked_page(page)

    print(
        "[AutoCommerceAI] 플랫폼:",
        platform,
    )
    print(
        "[AutoCommerceAI] 페이지 제목:",
        page_title,
    )
    print(
        "[AutoCommerceAI] 현재 URL:",
        current_url,
    )
    print(
        "[AutoCommerceAI] 검색 결과 DOM:",
        "발견" if result_found else "없음",
    )
    print(
        "[AutoCommerceAI] 로그인/보안 페이지:",
        "감지됨" if blocked else "감지되지 않음",
    )


def scroll_for_more_results(
    page,
    count: int = 5,
) -> None:
    for _ in range(count):
        try:
            page.mouse.wheel(0, 1800)
            page.wait_for_timeout(1500)
        except Exception:
            break


def collect_source_candidates(
    url: str,
) -> list:
    platform = detect_platform(url)

    if platform == "unknown":
        print(
            "[AutoCommerceAI] 지원하지 않는 플랫폼입니다:",
            url,
        )
        return []

    PROFILE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    EXPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with sync_playwright() as playwright:
        context = (
            playwright.chromium
            .launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                headless=False,
                viewport={
                    "width": 1440,
                    "height": 1000,
                },
                args=[
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
        )

        existing_pages = context.pages

        if existing_pages:
            page = existing_pages[0]
        else:
            page = context.new_page()

        sniffer = ResponseSniffer()
        sniffer.start(page)

        try:
            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000,
            )
        except Exception as exc:
            print(
                "[AutoCommerceAI] 페이지 이동 경고:",
                str(exc)[:300],
            )

        try:
            page.wait_for_timeout(4000)
        except Exception:
            pass

        try:
            page.wait_for_load_state(
                "networkidle",
                timeout=12000,
            )
        except Exception:
            pass

        result_found = False

        if platform == "tiktok":
            result_found = wait_for_tiktok_results(
                page=page,
                timeout_ms=25000,
            )

        elif platform in {
            "taobao",
            "1688",
            "douyin",
        }:
            result_found = wait_for_other_results(
                page=page,
                platform=platform,
            )

        print_page_status(
            page=page,
            platform=platform,
            result_found=result_found,
        )

        blocked = is_login_or_blocked_page(page)

        if blocked:
            print(
                "[AutoCommerceAI] 로그인 또는 보안 인증이 필요합니다."
            )
            print(
                "[AutoCommerceAI] 열린 브라우저에서 인증 후 "
                "검색 결과 화면까지 이동해 주세요."
            )

            try:
                input(
                    "[AutoCommerceAI] 검색 결과가 보이면 "
                    "Enter를 누르세요: "
                )
            except KeyboardInterrupt:
                print(
                    "\n[AutoCommerceAI] 사용자가 작업을 취소했습니다."
                )

            try:
                page.wait_for_timeout(2000)
            except Exception:
                pass

            if platform == "tiktok":
                result_found = wait_for_tiktok_results(
                    page=page,
                    timeout_ms=15000,
                )
            else:
                result_found = wait_for_other_results(
                    page=page,
                    platform=platform,
                )

            print_page_status(
                page=page,
                platform=platform,
                result_found=result_found,
            )

        # 스크롤하면서 추가 검색 API 응답과 카드 수집
        scroll_for_more_results(
            page=page,
            count=5,
        )

        # DOM 기반 후보 수집
        candidates = SourceCollector().top(
            page=page,
            platform=platform,
            limit=30,
        )

        network_stats_count = 0
        # TikTok API 통계를 영상 ID 기준으로 병합
        if platform in {"tiktok", "douyin"}:
            try:
                stats_map = sniffer.extract_tiktok_stats()
                network_stats_count = len(stats_map)

                candidates = sniffer.merge_tiktok_stats(
                    candidates
                )

            except Exception as exc:
                print(
                    "[AutoCommerceAI] 네트워크 통계 병합 경고:",
                    str(exc)[:500],
                )

        # TikTok 상세 페이지 메타데이터 수집
        if platform == "tiktok":
            candidates = TikTokMetadataCollector(
                wait_ms=3500,
                max_candidates=12,
            ).enrich(
                page=page,
                candidates=candidates,
            )

        # Sprint 59
        selector = VideoCandidateSelector()

        selected = selector.select(candidates)

        candidates = selected.get("all", [])
        
        saved_path = save_candidates(
            platform=platform,
            candidates=candidates,
        )

        try:
            response_log_path = sniffer.save()
        except Exception as exc:
            response_log_path = ""

            print(
                "[AutoCommerceAI] Response 로그 저장 실패:",
                str(exc)[:300],
            )

        print(
            "[AutoCommerceAI] 네트워크 영상 통계:",
            network_stats_count,
        )
        print(
            "[AutoCommerceAI] 후보 수집 완료:",
            len(candidates),
        )
        print(
            "[AutoCommerceAI] 후보 저장 위치:",
            saved_path,
        )
        print(
            "[AutoCommerceAI] Response 로그 저장 위치:",
            response_log_path,
        )

        if candidates:
            first = candidates[0]

            print(
                "[AutoCommerceAI] 1위 후보 조회수:",
                first.get("view_count", 0),
            )
            print(
                "[AutoCommerceAI] 1위 후보 좋아요:",
                first.get("like_count", 0),
            )
            print(
                "[AutoCommerceAI] 1위 후보 댓글:",
                first.get("comment_count", 0),
            )
            print(
                "[AutoCommerceAI] 1위 후보 공유:",
                first.get("share_count", 0),
            )
            print(
                "[AutoCommerceAI] 1위 후보 점수:",
                first.get(
                    "final_ai_score",
                    first.get("ai_score", first.get("score", 0)),
                ),
            )
            
            print(
                "[AutoCommerceAI] 1위 메타데이터 출처:",
                first.get(
                    "metadata_source",
                    "playwright-dom",
                ),
            )
        try:
            input(
                "[AutoCommerceAI] 확인이 끝나면 "
                "Enter를 눌러 브라우저를 닫습니다: "
            )
        except KeyboardInterrupt:
            pass

        try:
            context.close()
        except Exception:
            pass

        return candidates


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "[AutoCommerceAI] URL이 필요합니다."
        )
        print(
            '예: python .\\tools\\open_source_collect.py '
            '"https://www.tiktok.com/search?q=텀블러"'
        )
        sys.exit(1)

    collect_source_candidates(
        sys.argv[1]
    )


if __name__ == "__main__":
    main()