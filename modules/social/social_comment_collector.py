from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List

from modules.studio.network.response_sniffer import ResponseSniffer

from .douyin_comment_parser import DouyinCommentParser
from .social_comment_models import SocialCommentResult
from .tiktok_comment_parser import TikTokCommentParser
from .tiktok_session_manager import TikTokSessionManager


class SocialCommentCollector:
    """
    Sprint69 Social Comment Collector
    """

    COLLECTOR_VERSION = "social-comment-collector-69-2"

    def __init__(self) -> None:
        self.output_dir = Path("exports/social_comments")
        self.debug_dir = Path("exports/debug/social_comments")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.debug_dir.mkdir(parents=True, exist_ok=True)

        self.parsers = {
            "tiktok": TikTokCommentParser(),
            "douyin": DouyinCommentParser(),
        }
        self.tiktok_session = TikTokSessionManager()

    def collect(
        self,
        video_url: str,
        platform: str = "",
        max_comments: int = 50,
        timeout: int = 20,
        verification_wait_seconds: int = 120,
    ) -> Dict[str, Any]:
        url = str(video_url or "").strip()
        resolved_platform = self._resolve_platform(url, platform)

        result = SocialCommentResult(
            collector_version=self.COLLECTOR_VERSION,
            platform=resolved_platform,
            video_url=url,
            profile_mode=(
                "persistent_tiktok_profile"
                if resolved_platform == "tiktok"
                else "temporary_context"
            ),
        ).to_dict()

        if not url:
            result["status"] = "missing_url"
            result["error"] = "영상 URL이 없습니다."
            return result

        if resolved_platform not in self.parsers:
            result["status"] = "unsupported_platform"
            result["error"] = "TikTok 또는 Douyin URL이 아닙니다."
            return result

        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:
            result["status"] = "playwright_unavailable"
            result["error"] = f"Playwright를 불러오지 못했습니다: {exc}"
            return result

        context = None
        browser = None
        page = None
        sniffer = None

        try:
            headless = self._resolve_headless_mode()

            with sync_playwright() as playwright:
                if resolved_platform == "tiktok":
                    context, page = self.tiktok_session.open(
                        playwright,
                        headless=headless,
                        timeout=timeout,
                    )
                else:
                    browser = playwright.chromium.launch(
                        channel="chrome",
                        headless=headless,
                        args=["--no-first-run", "--no-default-browser-check"],
                    )
                    context = browser.new_context(
                        viewport={"width": 1440, "height": 1000},
                        locale="ko-KR",
                    )
                    page = context.new_page()

                page.set_default_timeout(max(15000, int(timeout or 20) * 1000))

                sniffer = ResponseSniffer(
                    log_path=self.debug_dir / f"{resolved_platform}_response_log.json",
                    keywords=[
                        "api",
                        "aweme",
                        "item",
                        "comment",
                        "comments",
                        "reply",
                        "reply_list",
                    ],
                    max_items=500,
                )
                sniffer.start(page)

                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=max(30000, int(timeout or 20) * 1000),
                )
                time.sleep(4)

                if resolved_platform == "tiktok":
                    verification = self.tiktok_session.wait_for_manual_verification(
                        page,
                        max_wait_seconds=verification_wait_seconds,
                    )
                    result["manual_verification_required"] = verification.get(
                        "required", False
                    )
                    result["manual_verification_resolved"] = verification.get(
                        "resolved", False
                    )
                    result["manual_verification_waited_seconds"] = verification.get(
                        "waited_seconds", 0
                    )
                    result["captcha_keywords"] = verification.get(
                        "matched_keywords", []
                    )

                    if verification.get("required") and not verification.get("resolved"):
                        self._save_debug(
                            page,
                            f"{resolved_platform}_verification_pending",
                            result,
                        )
                        result["status"] = "manual_verification_required"
                        result["error"] = verification.get(
                            "error",
                            "TikTok 사용자 인증이 완료되지 않았습니다.",
                        )
                        return result

                    time.sleep(2)

                result["final_url"] = str(page.url or url)
                self._open_comment_area(page, resolved_platform)
                time.sleep(3)

                network_comments = []
                if resolved_platform == "tiktok":
                    try:
                        network_comments = sniffer.extract_tiktok_comments(
                            max_comments=max_comments
                        )
                    except Exception:
                        network_comments = []

                parser = self.parsers[resolved_platform]
                comments = self._filter_network_comments(
                    network_comments,
                    resolved_platform,
                    url,
                    max_comments,
                )

                if not comments:
                    payloads = [
                        item.get("body")
                        for item in sniffer.all()
                        if isinstance(item.get("body"), (dict, list))
                    ]
                    comments = parser.parse_payloads(
                        payloads,
                        video_url=url,
                        max_comments=max_comments,
                    )

                if not comments:
                    comments = parser.parse_dom(
                        page,
                        video_url=url,
                        max_comments=max_comments,
                    )

                sniffer_path = sniffer.save()
                result["response_log_path"] = str(sniffer_path)
                result["response_count"] = len(sniffer.all())
                result["network_comment_count"] = len(network_comments)

                if comments:
                    result.update(
                        {
                            "ok": True,
                            "status": "collected",
                            "source": (
                                f"{resolved_platform}_network_response"
                                if network_comments
                                else f"{resolved_platform}_public_page"
                            ),
                            "comments": comments,
                            "comment_count": len(comments),
                            "error": "",
                        }
                    )
                else:
                    result["status"] = "no_public_comments"
                    result["error"] = (
                        "인증 이후에도 실제 댓글 응답과 공개 댓글을 찾지 못했습니다."
                    )

                self._save_debug(page, f"{resolved_platform}_result", result)
                return result

        except Exception as exc:
            result["status"] = "playwright_error"
            result["error"] = str(exc)

            if sniffer is not None:
                try:
                    result["response_count"] = len(sniffer.all())
                    result["response_log_path"] = str(sniffer.save())
                except Exception:
                    pass

            self._save_error(exc, resolved_platform)
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

    def collect_many(
        self,
        candidates: Iterable[Dict[str, Any]],
        project_id: Any,
        max_comments_per_video: int = 30,
        max_videos: int = 6,
        timeout: int = 20,
        verification_wait_seconds: int = 120,
    ) -> Dict[str, Any]:
        normalized_candidates = list(candidates or [])[: max(1, int(max_videos or 6))]
        items: List[Dict[str, Any]] = []

        for candidate in normalized_candidates:
            if not isinstance(candidate, dict):
                continue

            item_result = self.collect(
                video_url=str(candidate.get("url") or "").strip(),
                platform=str(candidate.get("platform") or "").strip(),
                max_comments=max_comments_per_video,
                timeout=timeout,
                verification_wait_seconds=verification_wait_seconds,
            )
            item_result["rank"] = candidate.get("rank")
            item_result["title"] = candidate.get("title", "")
            items.append(item_result)

        all_comments: List[Dict[str, Any]] = []
        seen = set()

        for item in items:
            for comment in item.get("comments") or []:
                key = str(comment.get("comment_id") or "").strip()
                if not key:
                    key = self._comment_text_key(comment.get("text", ""))
                if not key or key in seen:
                    continue
                seen.add(key)
                all_comments.append(comment)

        status = "collected" if all_comments else "no_public_comments"
        if any(
            item.get("status") == "manual_verification_required"
            for item in items
        ):
            status = "manual_verification_required"

        result = {
            "collector_version": self.COLLECTOR_VERSION,
            "ok": bool(all_comments),
            "status": status,
            "project_id": project_id,
            "video_count": len(items),
            "comment_count": len(all_comments),
            "items": items,
            "comments": all_comments,
        }

        output_path = self.save_project_result(project_id, result)
        result["output_path"] = str(output_path)
        return result

    def save_project_result(
        self,
        project_id: Any,
        result: Dict[str, Any],
    ) -> Path:
        safe_project_id = re.sub(
            r"[^0-9a-zA-Z_-]",
            "_",
            str(project_id or "unknown"),
        )
        output_path = self.output_dir / f"project_{safe_project_id}_comments.json"
        output_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return output_path

    def _filter_network_comments(
        self,
        items: Any,
        platform: str,
        video_url: str,
        max_comments: int,
    ) -> List[Dict[str, Any]]:
        if not isinstance(items, list):
            return []

        output = []
        seen = set()
        safe_max = max(1, min(int(max_comments or 50), 200))

        for item in items:
            if not isinstance(item, dict):
                continue

            text = str(item.get("text") or "").strip()
            comment_id = str(
                item.get("comment_id")
                or item.get("cid")
                or item.get("commentId")
                or ""
            ).strip()

            # ResponseSniffer가 영상 desc를 댓글로 반환해도 여기서 제거합니다.
            if not comment_id or len(text) < 2:
                continue

            key = comment_id or self._comment_text_key(text)
            if not key or key in seen:
                continue

            seen.add(key)
            normalized = dict(item)
            normalized["comment_id"] = comment_id
            normalized["platform"] = platform
            normalized["video_url"] = video_url
            normalized["source"] = f"{platform}_network_response"
            output.append(normalized)

            if len(output) >= safe_max:
                break

        return output

    def _comment_text_key(self, text: Any) -> str:
        return re.sub(
            r"[^0-9a-zA-Z가-힣\u4e00-\u9fff]",
            "",
            str(text or ""),
        ).lower()

    def _resolve_platform(self, url: str, platform: str) -> str:
        requested = str(platform or "").strip().lower()
        if requested in self.parsers:
            return requested

        lowered = str(url or "").lower()
        if "tiktok.com" in lowered:
            return "tiktok"
        if "douyin.com" in lowered:
            return "douyin"
        return ""

    def _resolve_headless_mode(self) -> bool:
        value = str(os.environ.get("SOCIAL_COMMENT_HEADLESS", "0")).strip().lower()
        return value in {"1", "true", "yes", "on"}

    def _open_comment_area(self, page, platform: str) -> None:
        selectors = {
            "tiktok": (
                "[data-e2e='browse-comment']",
                "button:has-text('댓글')",
                "button:has-text('Comments')",
                "[data-e2e='comment-icon']",
            ),
            "douyin": (
                "button:has-text('评论')",
                "[class*='comment']",
            ),
        }.get(platform, ())

        for selector in selectors:
            try:
                locator = page.locator(selector).first
                if locator.count() < 1:
                    continue
                locator.click(timeout=3000)
                time.sleep(1.5)
                break
            except Exception:
                continue

        for _ in range(8):
            try:
                page.mouse.wheel(0, 700)
                time.sleep(0.8)
            except Exception:
                break

    def _save_debug(
        self,
        page,
        prefix: str,
        result: Dict[str, Any],
    ) -> None:
        html_path = self.debug_dir / f"{prefix}.html"
        screenshot_path = self.debug_dir / f"{prefix}.png"

        try:
            html_path.write_text(page.content(), encoding="utf-8")
            result["debug_path"] = str(html_path)
        except Exception:
            pass

        try:
            page.screenshot(path=str(screenshot_path), full_page=False)
            result["screenshot_path"] = str(screenshot_path)
        except Exception:
            pass

    def _save_error(self, exc: Exception, platform: str) -> None:
        try:
            path = self.debug_dir / f"{platform or 'unknown'}_error.txt"
            path.write_text(str(exc), encoding="utf-8")
        except Exception:
            pass
