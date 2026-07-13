from __future__ import annotations

import html
import json
import os
import re
import ssl
from pathlib import Path
from typing import Any, Dict, List
from urllib.request import Request, urlopen


class CoupangReviewCollector:
    """
    Sprint67-2 Coupang Review Collector

    수집 순서:
    1. 일반 HTTP 요청 시도
    2. 리뷰가 없거나 접근이 제한되면 Playwright 실행
    3. 시스템 Chrome을 일반 launch 방식으로 실행
    4. 독립 browser context 생성
    5. 쿠팡 상품평 영역으로 이동
    6. DOM과 HTML에서 리뷰 문구 수집

    안전 원칙:
    - 리뷰 수집 실패 시 기존 파이프라인 중단 금지
    - 항상 같은 반환 구조 유지
    - ProductEngine 기존 반환 구조 유지
    """

    COLLECTOR_VERSION = "coupang-review-collector-67-2"

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/avif,image/webp,*/*;q=0.8"
        ),
        "Accept-Language": (
            "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
        ),
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Referer": "https://www.coupang.com/",
    }

    REVIEW_SELECTORS = [
        ".sdp-review__article__list__review__content",
        (
            ".sdp-review__article__list__review__content"
            ".js_reviewArticleContent"
        ),
        "[class*='review__content']",
        "[class*='review-content']",
        "[data-review-content]",
        "article [class*='content']",
    ]

    REVIEW_KEYS = (
        "reviewContent",
        "reviewText",
        "reviewTitle",
        "content",
        "headline",
        "comment",
    )

    def __init__(self):
        self.debug_dir = Path(
            "exports/debug/coupang_review"
        )

        self.debug_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def collect(
        self,
        coupang_url: str,
        max_reviews: int = 50,
        timeout: int = 15,
    ) -> Dict[str, Any]:
        url = str(coupang_url or "").strip()

        result = self._empty_result()

        if not url:
            result["status"] = "missing_url"
            result["error"] = "쿠팡 URL이 없습니다."
            return result

        if "coupang" not in url.lower():
            result["status"] = "unsupported_url"
            result["error"] = "쿠팡 상품 URL이 아닙니다."
            return result

        try:
            page_html = self._download_html(
                url=url,
                timeout=timeout,
            )

            if page_html:
                reviews = self._extract_reviews(
                    page_html=page_html,
                    max_reviews=max_reviews,
                )

                if reviews:
                    result.update(
                        {
                            "ok": True,
                            "status": "collected",
                            "source": "coupang_http",
                            "review_count": len(reviews),
                            "reviews": reviews,
                            "error": "",
                        }
                    )

                    return result

            return self._collect_with_browser_context(
                url=url,
                max_reviews=max_reviews,
                timeout=timeout,
            )

        except Exception as exc:
            result["status"] = "error"
            result["error"] = str(exc)
            return result

    def _empty_result(
        self,
    ) -> Dict[str, Any]:
        return {
            "collector_version": self.COLLECTOR_VERSION,
            "ok": False,
            "status": "empty",
            "source": "coupang_page",
            "review_count": 0,
            "reviews": [],
            "error": "",
            "debug_path": "",
            "screenshot_path": "",
            "final_url": "",
            "attempt": 0,
            "page_title": "",
            "http_status": None,
            "fallback_reason": "",
            "pipeline_action": "continue_without_reviews",
        }

    def _collect_with_browser_context(
        self,
        url: str,
        max_reviews: int,
        timeout: int,
    ) -> Dict[str, Any]:
        result = self._empty_result()
        result["source"] = "coupang_playwright_new_context"

        try:
            from playwright.sync_api import (
                sync_playwright,
            )
        except Exception as exc:
            result["status"] = "playwright_unavailable"
            result["error"] = (
                "Playwright를 불러오지 못했습니다: "
                f"{exc}"
            )
            return result

        browser = None
        context = None

        try:
            headless = self._resolve_headless_mode()

            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    channel="chrome",
                    headless=headless,
                    args=[
                        (
                            "--disable-blink-features="
                            "AutomationControlled"
                        ),
                        "--no-first-run",
                        "--no-default-browser-check",
                        "--start-maximized",
                    ],
                )

                context = browser.new_context(
                    viewport={
                        "width": 1440,
                        "height": 1000,
                    },
                    locale="ko-KR",
                    timezone_id="Asia/Seoul",
                    user_agent=(
                        self.DEFAULT_HEADERS[
                            "User-Agent"
                        ]
                    ),
                    extra_http_headers={
                        "Accept-Language": (
                            self.DEFAULT_HEADERS[
                                "Accept-Language"
                            ]
                        ),
                        "Referer": (
                            self.DEFAULT_HEADERS[
                                "Referer"
                            ]
                        ),
                    },
                )

                last_status = "blocked"
                last_error = (
                    "쿠팡에서 현재 브라우저 접근을 제한했습니다."
                )

                for attempt in range(1, 3):
                    result["attempt"] = attempt
                    page = context.new_page()

                    try:
                        page.set_default_timeout(
                            max(
                                15000,
                                timeout * 1000,
                            )
                        )

                        try:
                            main_response = page.goto(
                                "https://www.coupang.com/",
                                wait_until="domcontentloaded",
                                timeout=max(
                                    30000,
                                    timeout * 2000,
                                ),
                            )

                            if main_response is not None:
                                result["http_status"] = (
                                    main_response.status
                                )
                        except Exception:
                            pass

                        page.wait_for_timeout(2500)

                        product_response = page.goto(
                            url,
                            wait_until="domcontentloaded",
                            timeout=max(
                                30000,
                                timeout * 2000,
                            ),
                        )

                        if product_response is not None:
                            result["http_status"] = (
                                product_response.status
                            )

                        if result.get("http_status") in {401, 403, 429}:
                            try:
                                result["final_url"] = page.url or url
                                result["page_title"] = page.title() or ""
                            except Exception:
                                pass

                            self._save_debug(
                                page=page,
                                prefix=(
                                    f"attempt_{attempt}_http_"
                                    f"{result.get('http_status')}"
                                ),
                                result=result,
                            )

                            last_status = "blocked"
                            last_error = (
                                "쿠팡 서버가 HTTP "
                                f"{result.get('http_status')} 응답으로 "
                                "접근을 제한했습니다."
                            )
                            result["fallback_reason"] = (
                                "coupang_http_access_denied"
                            )
                            break

                        page.wait_for_timeout(4000)

                        result["final_url"] = (
                            page.url or url
                        )

                        try:
                            result["page_title"] = (
                                page.title() or ""
                            )
                        except Exception:
                            result["page_title"] = ""

                        body_text = self._read_body_text(
                            page
                        )

                        if self._is_login_page(
                            result["final_url"],
                            body_text,
                        ):
                            self._save_debug(
                                page=page,
                                prefix=(
                                    f"attempt_{attempt}_"
                                    "login_redirect"
                                ),
                                result=result,
                            )

                            last_status = "login_redirect"
                            last_error = (
                                "쿠팡 로그인 페이지로 "
                                "이동되었습니다."
                            )
                            continue

                        if self._is_blocked_page(
                            body_text
                        ):
                            self._save_debug(
                                page=page,
                                prefix=(
                                    f"attempt_{attempt}_blocked"
                                ),
                                result=result,
                            )

                            last_status = "blocked"
                            last_error = (
                                "쿠팡에서 현재 브라우저 "
                                "접근을 제한했습니다."
                            )
                            result["fallback_reason"] = (
                                "coupang_access_denied_page"
                            )
                            break

                        self._open_review_section(
                            page
                        )

                        reviews = self._extract_from_page(
                            page=page,
                            max_reviews=max_reviews,
                        )

                        if not reviews:
                            page_html = page.content()

                            reviews = self._extract_reviews(
                                page_html=page_html,
                                max_reviews=max_reviews,
                            )

                        self._save_debug(
                            page=page,
                            prefix=f"attempt_{attempt}_result",
                            result=result,
                        )

                        if reviews:
                            result.update(
                                {
                                    "ok": True,
                                    "status": "collected",
                                    "source": (
                                        "coupang_playwright_"
                                        "new_context"
                                    ),
                                    "review_count": len(reviews),
                                    "reviews": reviews,
                                    "error": "",
                                }
                            )
                            return result

                        last_status = "no_public_reviews"
                        last_error = (
                            "상품 페이지는 열렸지만 "
                            "리뷰 문구를 찾지 못했습니다."
                        )

                    except Exception as exc:
                        last_status = "playwright_error"
                        last_error = str(exc)

                        try:
                            self._save_debug(
                                page=page,
                                prefix=(
                                    f"attempt_{attempt}_error"
                                ),
                                result=result,
                            )
                        except Exception:
                            pass

                    finally:
                        try:
                            page.close()
                        except Exception:
                            pass

                    if attempt < 2:
                        try:
                            context.clear_cookies()
                        except Exception:
                            pass

                result["status"] = last_status
                result["error"] = last_error
                return result

        except Exception as exc:
            error_path = (
                self.debug_dir
                / "coupang_review_error.txt"
            )

            try:
                error_path.write_text(
                    str(exc),
                    encoding="utf-8",
                )

                result["debug_path"] = str(
                    error_path
                )
            except Exception:
                pass

            result["status"] = (
                "playwright_error"
            )
            result["error"] = str(exc)

            return result

        finally:
            try:
                if context is not None:
                    context.close()
            except Exception:
                pass

            try:
                if browser is not None:
                    browser.close()
            except Exception:
                pass

    def _resolve_headless_mode(
        self,
    ) -> bool:
        """
        기본값은 실제 브라우저 창 표시입니다.

        환경변수:
        COUPANG_REVIEW_HEADLESS=1
        로 설정하면 창 없이 실행됩니다.
        """

        value = str(
            os.environ.get(
                "COUPANG_REVIEW_HEADLESS",
                "0",
            )
        ).strip().lower()

        return value in {
            "1",
            "true",
            "yes",
            "on",
        }

    def _read_body_text(
        self,
        page,
    ) -> str:
        try:
            return (
                page.locator("body")
                .inner_text(timeout=5000)
            )
        except Exception:
            return ""

    def _is_login_page(
        self,
        final_url: str,
        body_text: str,
    ) -> bool:
        lowered_url = str(
            final_url or ""
        ).lower()

        lowered_body = str(
            body_text or ""
        ).lower()

        if "login" in lowered_url:
            return True

        login_words = (
            "로그인이 필요",
            "로그인해 주세요",
            "회원 로그인",
        )

        return any(
            word in lowered_body
            for word in login_words
        )

    def _is_blocked_page(
        self,
        body_text: str,
    ) -> bool:
        lowered = str(
            body_text or ""
        ).lower()

        blocked_words = (
            "access denied",
            "접근이 제한",
            "비정상적인 접근",
            "서비스에 접속할 수 없습니다",
            "요청을 처리할 수 없습니다",
            "잠시 후 다시 시도",
        )

        return any(
            word in lowered
            for word in blocked_words
        )

    def _open_review_section(
        self,
        page,
    ) -> None:
        review_tab_selectors = [
            "a[href='#productReview']",
            "a[href*='productReview']",
            "button:has-text('상품평')",
            "a:has-text('상품평')",
            "button:has-text('리뷰')",
            "a:has-text('리뷰')",
        ]

        clicked = False

        for selector in review_tab_selectors:
            try:
                locator = page.locator(
                    selector
                ).first

                if locator.count() < 1:
                    continue

                locator.scroll_into_view_if_needed(
                    timeout=4000
                )

                page.wait_for_timeout(500)

                locator.click(
                    timeout=5000,
                    force=True,
                )

                clicked = True
                page.wait_for_timeout(3000)
                break

            except Exception:
                continue

        if not clicked:
            try:
                page.evaluate(
                    """
                    () => {
                        const selectors = [
                            '#productReview',
                            '[id*="productReview"]',
                            '[class*="review"]'
                        ];

                        for (const selector of selectors) {
                            const target =
                                document.querySelector(
                                    selector
                                );

                            if (target) {
                                target.scrollIntoView({
                                    behavior: 'instant',
                                    block: 'start'
                                });
                                return true;
                            }
                        }

                        return false;
                    }
                    """
                )
            except Exception:
                pass

        for _ in range(8):
            try:
                page.mouse.wheel(
                    0,
                    900,
                )

                page.wait_for_timeout(
                    700
                )
            except Exception:
                break

        self._click_more_buttons(
            page
        )

    def _click_more_buttons(
        self,
        page,
    ) -> None:
        selectors = [
            "button:has-text('더보기')",
            "a:has-text('더보기')",
            (
                ".sdp-review__article__list"
                "__review__content__more"
            ),
        ]

        for selector in selectors:
            try:
                locator = page.locator(
                    selector
                )

                count = min(
                    locator.count(),
                    20,
                )

                for index in range(
                    count
                ):
                    try:
                        locator.nth(
                            index
                        ).click(
                            timeout=1000,
                            force=True,
                        )
                    except Exception:
                        continue

            except Exception:
                continue

        try:
            page.wait_for_timeout(1000)
        except Exception:
            pass

    def _extract_from_page(
        self,
        page,
        max_reviews: int,
    ) -> List[Dict[str, Any]]:
        candidates: List[
            Dict[str, Any]
        ] = []

        for selector in self.REVIEW_SELECTORS:
            try:
                locator = page.locator(
                    selector
                )

                count = min(
                    locator.count(),
                    max_reviews * 4,
                )

                for index in range(
                    count
                ):
                    try:
                        text = (
                            locator.nth(index)
                            .inner_text(
                                timeout=2000
                            )
                        )
                    except Exception:
                        continue

                    text = self._clean_text(
                        text
                    )

                    if self._looks_like_review(
                        text
                    ):
                        candidates.append(
                            {
                                "text": text,
                                "rating": None,
                                "source": (
                                    "playwright_dom"
                                ),
                            }
                        )

            except Exception:
                continue

        return self._normalize_reviews(
            candidates,
            max_reviews=max_reviews,
        )

    def _save_debug(
        self,
        page,
        prefix: str,
        result: Dict[str, Any],
    ) -> None:
        html_path = (
            self.debug_dir
            / f"{prefix}_coupang_review.html"
        )

        screenshot_path = (
            self.debug_dir
            / f"{prefix}_coupang_review.png"
        )

        try:
            html_path.write_text(
                page.content(),
                encoding="utf-8",
            )

            result["debug_path"] = str(
                html_path
            )
        except Exception:
            pass

        try:
            page.screenshot(
                path=str(
                    screenshot_path
                ),
                full_page=False,
            )

            result["screenshot_path"] = (
                str(screenshot_path)
            )
        except Exception:
            pass

    def _download_html(
        self,
        url: str,
        timeout: int,
    ) -> str:
        html_text = (
            self._download_with_requests(
                url=url,
                timeout=timeout,
            )
        )

        if html_text:
            return html_text

        return self._download_with_urllib(
            url=url,
            timeout=timeout,
        )

    def _download_with_requests(
        self,
        url: str,
        timeout: int,
    ) -> str:
        try:
            import requests

            response = requests.get(
                url,
                headers=self.DEFAULT_HEADERS,
                timeout=timeout,
                allow_redirects=True,
            )

            if response.status_code != 200:
                return ""

            response.encoding = (
                response.apparent_encoding
                or response.encoding
                or "utf-8"
            )

            return response.text or ""

        except Exception:
            return ""

    def _download_with_urllib(
        self,
        url: str,
        timeout: int,
    ) -> str:
        try:
            request = Request(
                url,
                headers=self.DEFAULT_HEADERS,
                method="GET",
            )

            ssl_context = (
                ssl.create_default_context()
            )

            with urlopen(
                request,
                timeout=timeout,
                context=ssl_context,
            ) as response:
                raw = response.read()

            return raw.decode(
                "utf-8",
                errors="ignore",
            )

        except Exception:
            return ""

    def _extract_reviews(
        self,
        page_html: str,
        max_reviews: int,
    ) -> List[Dict[str, Any]]:
        candidates: List[
            Dict[str, Any]
        ] = []

        candidates.extend(
            self._extract_from_json_patterns(
                page_html
            )
        )

        candidates.extend(
            self._extract_from_html_patterns(
                page_html
            )
        )

        return self._normalize_reviews(
            candidates,
            max_reviews=max_reviews,
        )

    def _extract_from_json_patterns(
        self,
        page_html: str,
    ) -> List[Dict[str, Any]]:
        reviews: List[
            Dict[str, Any]
        ] = []

        key_pattern = "|".join(
            re.escape(key)
            for key in self.REVIEW_KEYS
        )

        patterns = [
            (
                rf'"(?:{key_pattern})"\s*:\s*'
                rf'"((?:\\.|[^"\\])*)"'
            ),
            (
                rf"'(?:{key_pattern})'\s*:\s*"
                rf"'((?:\\.|[^'\\])*)'"
            ),
        ]

        for pattern in patterns:
            matches = re.findall(
                pattern,
                page_html,
                flags=re.IGNORECASE,
            )

            for matched_text in matches:
                decoded_text = (
                    self._decode_json_text(
                        matched_text
                    )
                )

                if self._looks_like_review(
                    decoded_text
                ):
                    reviews.append(
                        {
                            "text": decoded_text,
                            "rating": None,
                            "source": "page_json",
                        }
                    )

        return reviews

    def _extract_from_html_patterns(
        self,
        page_html: str,
    ) -> List[Dict[str, Any]]:
        reviews: List[
            Dict[str, Any]
        ] = []

        patterns = [
            (
                r'<div[^>]+class="[^"]*'
                r'sdp-review__article__list__review'
                r'__content[^"]*"[^>]*>(.*?)</div>'
            ),
            (
                r'<div[^>]+class="[^"]*'
                r'review-content[^"]*"[^>]*>'
                r'(.*?)</div>'
            ),
            (
                r'<span[^>]+class="[^"]*'
                r'review[^"]*content[^"]*"[^>]*>'
                r'(.*?)</span>'
            ),
        ]

        for pattern in patterns:
            matches = re.findall(
                pattern,
                page_html,
                flags=(
                    re.IGNORECASE
                    | re.DOTALL
                ),
            )

            for matched_html in matches:
                clean_text = (
                    self._strip_html(
                        matched_html
                    )
                )

                if self._looks_like_review(
                    clean_text
                ):
                    reviews.append(
                        {
                            "text": clean_text,
                            "rating": None,
                            "source": "page_html",
                        }
                    )

        return reviews

    def _decode_json_text(
        self,
        value: str,
    ) -> str:
        text = str(value or "")

        try:
            text = json.loads(
                f'"{text}"'
            )
        except Exception:
            text = (
                text.replace(
                    "\\n",
                    " ",
                )
                .replace(
                    "\\r",
                    " ",
                )
                .replace(
                    "\\t",
                    " ",
                )
                .replace(
                    '\\"',
                    '"',
                )
                .replace(
                    "\\/",
                    "/",
                )
            )

        return self._clean_text(
            text
        )

    def _strip_html(
        self,
        value: str,
    ) -> str:
        text = re.sub(
            r"<br\s*/?>",
            " ",
            str(value or ""),
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"<[^>]+>",
            " ",
            text,
        )

        return self._clean_text(
            text
        )

    def _clean_text(
        self,
        value: str,
    ) -> str:
        text = html.unescape(
            str(value or "")
        )

        text = re.sub(
            r"\\u([0-9a-fA-F]{4})",
            self._unicode_replacer,
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    def _unicode_replacer(
        self,
        match: re.Match,
    ) -> str:
        try:
            return chr(
                int(
                    match.group(1),
                    16,
                )
            )
        except Exception:
            return match.group(0)

    def _looks_like_review(
        self,
        text: str,
    ) -> bool:
        clean = str(
            text or ""
        ).strip()

        if len(clean) < 8:
            return False

        if len(clean) > 2000:
            return False

        lowered = clean.lower()

        blocked_values = (
            "javascript",
            "stylesheet",
            "http://",
            "https://",
            "productid",
            "vendoritemid",
            "imageurl",
            "개인정보처리방침",
            "이용약관",
        )

        if any(
            blocked in lowered
            for blocked in blocked_values
        ):
            return False

        korean_count = len(
            re.findall(
                r"[가-힣]",
                clean,
            )
        )

        if korean_count < 3:
            return False

        return True

    def _normalize_reviews(
        self,
        reviews: List[Dict[str, Any]],
        max_reviews: int,
    ) -> List[Dict[str, Any]]:
        normalized: List[
            Dict[str, Any]
        ] = []

        seen = set()

        safe_max = max(
            1,
            min(
                int(
                    max_reviews or 50
                ),
                200,
            ),
        )

        for review in reviews:
            if not isinstance(
                review,
                dict,
            ):
                continue

            text = self._clean_text(
                review.get(
                    "text",
                    "",
                )
            )

            if not self._looks_like_review(
                text
            ):
                continue

            duplicate_key = re.sub(
                r"[^가-힣a-zA-Z0-9]",
                "",
                text,
            ).lower()

            if not duplicate_key:
                continue

            if duplicate_key in seen:
                continue

            seen.add(
                duplicate_key
            )

            normalized.append(
                {
                    "text": text,
                    "rating": review.get(
                        "rating"
                    ),
                    "source": (
                        review.get(
                            "source"
                        )
                        or "coupang_page"
                    ),
                }
            )

            if len(normalized) >= safe_max:
                break

        return normalized