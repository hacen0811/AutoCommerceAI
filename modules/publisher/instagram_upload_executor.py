from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
import time
from typing import Any, Dict, List, Optional, Sequence


class InstagramUploadExecutor:
    """
    Sprint90-2 Instagram Playwright Upload Executor

    역할:
    - UploadDispatcher의 instagram_reels dispatch job을 입력으로 받음
    - 영상 경로와 캡션을 검증하고 Instagram 웹 업로드를 실행
    - Playwright persistent context로 로그인 세션을 재사용
    - 로그인되지 않은 경우 브라우저를 열어 수동 로그인을 허용
    - 공유 완료 여부와 게시물 URL을 가능한 범위에서 확인
    - 원본 dispatch job, queue 파일, Project DB는 직접 변경하지 않음

    주의:
    - Instagram 웹 UI는 수시로 변경될 수 있으므로 여러 선택자를 순차 사용함
    - 기본값은 dry_run=True이며 실제 업로드는 dry_run=False일 때만 수행함
    """

    VERSION = "instagram-playwright-upload-executor-90-2a"
    SOURCE_VERSION = "upload-dispatcher-83-1"
    PLATFORM = "instagram_reels"
    EXECUTOR_NAME = "InstagramUploadExecutor"
    INSTAGRAM_URL = "https://www.instagram.com/"
    CREATE_URL = "https://www.instagram.com/create/select/"

    VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm"}

    def execute(
        self,
        dispatch_job: Any = None,
        *,
        dry_run: bool = True,
        user_data_dir: Any = "secrets/instagram_playwright_profile",
        headless: bool = False,
        allow_manual_login: bool = True,
        login_timeout_seconds: int = 300,
        action_timeout_seconds: int = 60,
        slow_mo: int = 100,
        keep_browser_open: bool = False,
    ) -> Dict[str, Any]:
        source = dispatch_job if isinstance(dispatch_job, dict) else {}
        validation = self._validate_dispatch_job(source)

        if not validation["valid"]:
            result = self._result(
                ok=False,
                status="invalid_dispatch_job",
                dry_run=dry_run,
                upload_ready=False,
                source=source,
                errors=validation["errors"],
                warnings=validation["warnings"],
            )
            self._print_result(result)
            return result

        normalized = self._normalize_upload_payload(source)
        checks = self._build_checks(normalized)
        errors = [name for name, passed in checks.items() if not passed]
        warnings = list(validation["warnings"])

        if errors:
            result = self._result(
                ok=False,
                status="incomplete",
                dry_run=dry_run,
                upload_ready=False,
                source=source,
                normalized=normalized,
                checks=checks,
                errors=errors,
                warnings=warnings,
            )
            self._print_result(result)
            return result

        if dry_run:
            result = self._result(
                ok=True,
                status="dry_run_ready",
                dry_run=True,
                upload_ready=True,
                source=source,
                normalized=normalized,
                checks=checks,
                errors=[],
                warnings=warnings,
            )
            self._print_result(result)
            return result

        profile_dir = Path(self._clean_text(user_data_dir)).expanduser()
        profile_dir.mkdir(parents=True, exist_ok=True)

        browser = None
        context = None
        page = None

        try:
            from playwright.sync_api import sync_playwright

            browser = sync_playwright().start()
            context = browser.chromium.launch_persistent_context(
                user_data_dir=str(profile_dir),
                headless=bool(headless),
                slow_mo=max(0, int(slow_mo)),
                viewport={"width": 1440, "height": 1000},
                locale="ko-KR",
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--start-maximized",
                ],
            )
            context.set_default_timeout(
                max(10, int(action_timeout_seconds)) * 1000
            )
            page = context.pages[0] if context.pages else context.new_page()

            page.goto(
                self.INSTAGRAM_URL,
                wait_until="domcontentloaded",
            )

            login_status = self._ensure_logged_in(
                page=page,
                allow_manual_login=allow_manual_login,
                timeout_seconds=login_timeout_seconds,
            )
            if not login_status["ok"]:
                return self._result_and_print(
                    ok=False,
                    status=login_status["status"],
                    dry_run=False,
                    upload_ready=False,
                    source=source,
                    normalized=normalized,
                    checks=checks,
                    errors=login_status.get("errors", []),
                    warnings=warnings,
                    extra={
                        "profile_dir": str(profile_dir),
                        "login_detected": False,
                    },
                )

            upload_result = self._upload_reel(
                page=page,
                normalized=normalized,
            )

            result = self._result(
                ok=bool(upload_result.get("ok")),
                status=str(upload_result.get("status") or "upload_failed"),
                dry_run=False,
                upload_ready=bool(upload_result.get("ok")),
                source=source,
                normalized=normalized,
                checks=checks,
                errors=list(upload_result.get("errors") or []),
                warnings=warnings + list(upload_result.get("warnings") or []),
                extra={
                    "post_url": self._clean_text(upload_result.get("post_url")),
                    "uploaded_at": (
                        self._utc_now() if upload_result.get("ok") else ""
                    ),
                    "actual_upload_performed": bool(upload_result.get("ok")),
                    "profile_dir": str(profile_dir),
                    "login_detected": True,
                    "final_url": self._clean_text(upload_result.get("final_url")),
                },
            )
            self._print_result(result)
            return result

        except ModuleNotFoundError as exc:
            return self._result_and_print(
                ok=False,
                status="dependency_missing",
                dry_run=False,
                upload_ready=False,
                source=source,
                normalized=normalized,
                checks=checks,
                errors=[
                    "Playwright가 설치되지 않았습니다",
                    str(exc),
                ],
                warnings=warnings,
            )
        except Exception as exc:
            screenshot_path = self._save_failure_screenshot(page)
            return self._result_and_print(
                ok=False,
                status="upload_failed",
                dry_run=False,
                upload_ready=False,
                source=source,
                normalized=normalized,
                checks=checks,
                errors=[str(exc)],
                warnings=warnings,
                extra={"failure_screenshot": screenshot_path},
            )
        finally:
            if not keep_browser_open:
                try:
                    if context is not None:
                        context.close()
                except Exception:
                    pass
                try:
                    if browser is not None:
                        browser.stop()
                except Exception:
                    pass

    def run(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        return self.execute(*args, **kwargs)

    def upload(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        kwargs["dry_run"] = False
        return self.execute(*args, **kwargs)

    def _validate_dispatch_job(self, source: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []

        if not source:
            return {
                "valid": False,
                "errors": ["dispatch job이 비어 있습니다"],
                "warnings": [],
            }

        platform = self._clean_text(source.get("platform"))
        if platform != self.PLATFORM:
            errors.append(
                f"플랫폼이 {self.PLATFORM}이 아닙니다: {platform or 'empty'}"
            )

        executor = self._clean_text(source.get("executor"))
        if executor and executor != self.EXECUTOR_NAME:
            warnings.append(f"executor 값이 다릅니다: {executor}")

        dispatch_status = self._clean_text(source.get("dispatch_status"))
        if dispatch_status != "ready":
            errors.append("dispatch_status가 ready가 아닙니다")

        if not isinstance(source.get("payload"), dict):
            errors.append("payload가 딕셔너리가 아닙니다")

        dispatcher_version = self._clean_text(source.get("dispatcher_version"))
        if dispatcher_version and dispatcher_version != self.SOURCE_VERSION:
            warnings.append(
                f"Dispatcher 버전이 다릅니다: {dispatcher_version}"
            )

        return {
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
        }

    def _normalize_upload_payload(self, source: Dict[str, Any]) -> Dict[str, Any]:
        payload = source.get("payload")
        payload = payload if isinstance(payload, dict) else {}

        caption = self._first_text(
            payload.get("caption"),
            payload.get("description"),
            payload.get("text"),
            (payload.get("snippet") or {}).get("description")
            if isinstance(payload.get("snippet"), dict)
            else "",
        )

        hashtags = payload.get("hashtags")
        hashtags = hashtags if isinstance(hashtags, (list, tuple, set)) else []
        hashtag_text = " ".join(
            self._normalize_hashtag(item) for item in hashtags
            if self._normalize_hashtag(item)
        )
        if hashtag_text and hashtag_text not in caption:
            caption = f"{caption}\n\n{hashtag_text}".strip()

        video_path = self._first_text(
            payload.get("video_path"),
            payload.get("media_path"),
            source.get("video_path"),
        )

        return {
            "platform": self.PLATFORM,
            "video_path": video_path,
            "caption": self._shorten(caption, 2200),
            "share_to_feed": bool(payload.get("share_to_feed", True)),
            "cover_image_path": self._clean_text(
                payload.get("cover_image_path")
            ),
            "scheduled_at": self._first_text(
                source.get("scheduled_at"),
                payload.get("scheduled_at"),
                payload.get("schedule_at"),
            ),
            "job_id": self._clean_text(source.get("job_id")),
            "queue_id": self._clean_text(source.get("queue_id")),
        }

    def _build_checks(self, normalized: Dict[str, Any]) -> Dict[str, bool]:
        video_path = Path(normalized.get("video_path") or "")
        return {
            "video_path_present": bool(normalized.get("video_path")),
            "video_file_exists": video_path.is_file(),
            "video_extension_supported": (
                video_path.suffix.lower() in self.VIDEO_EXTENSIONS
            ),
            "caption_within_limit": len(normalized.get("caption") or "") <= 2200,
        }

    def _ensure_logged_in(
        self,
        *,
        page: Any,
        allow_manual_login: bool,
        timeout_seconds: int,
    ) -> Dict[str, Any]:
        if self._is_logged_in(page):
            return {"ok": True, "status": "logged_in"}

        if not allow_manual_login:
            return {
                "ok": False,
                "status": "login_required",
                "errors": ["Instagram 로그인이 필요합니다"],
            }

        print(
            "[Sprint90-2 Instagram] 브라우저에서 로그인해 주세요.",
            flush=True,
        )
        deadline = time.time() + max(30, int(timeout_seconds))
        while time.time() < deadline:
            if self._is_logged_in(page):
                return {"ok": True, "status": "manual_login_completed"}
            time.sleep(2)

        return {
            "ok": False,
            "status": "login_timeout",
            "errors": ["Instagram 로그인 대기 시간이 초과되었습니다"],
        }

    def _is_logged_in(self, page: Any) -> bool:
        current_url = self._clean_text(getattr(page, "url", ""))
        if "/accounts/login" in current_url:
            return False

        login_inputs = page.locator(
            'input[name="username"], input[name="password"]'
        )
        if login_inputs.count() > 0:
            return False

        selectors = [
            'a[href="/direct/inbox/"]',
            'a[href="/explore/"]',
            'svg[aria-label="Home"]',
            'svg[aria-label="홈"]',
            'span:has-text("프로필")',
            'span:has-text("Profile")',
        ]
        return any(self._locator_visible(page, selector) for selector in selectors)

    def _upload_reel(self, *, page: Any, normalized: Dict[str, Any]) -> Dict[str, Any]:
        page.goto(self.CREATE_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)

        file_input = page.locator('input[type="file"]')
        if file_input.count() == 0:
            self._click_first(
                page,
                [
                    'text="만들기"',
                    'text="Create"',
                    'span:has-text("만들기")',
                    'span:has-text("Create")',
                ],
            )
            page.wait_for_timeout(1000)
            file_input = page.locator('input[type="file"]')

        if file_input.count() == 0:
            return {
                "ok": False,
                "status": "file_input_not_found",
                "errors": ["Instagram 영상 선택 입력창을 찾지 못했습니다"],
                "final_url": page.url,
            }

        file_input.first.set_input_files(normalized["video_path"])
        page.wait_for_timeout(1500)

        self._click_optional(
            page,
            [
                'button:has-text("확인")',
                'div[role="button"]:has-text("확인")',
                'button:has-text("OK")',
                'div[role="button"]:has-text("OK")',
            ],
        )

        # 영상 미리보기와 편집 화면이 준비될 때까지 기다린 뒤 첫 번째 다음 클릭
        if not self._wait_and_click_next(page, timeout_seconds=90):
            return {
                "ok": False,
                "status": "first_next_not_found",
                "errors": ["첫 번째 다음 버튼을 찾지 못했습니다"],
                "final_url": page.url,
                "failure_screenshot": self._save_failure_screenshot(page),
            }

        # 자르기/편집 다음 단계가 열릴 때까지 기다린 뒤 두 번째 다음 클릭
        if not self._wait_and_click_next(page, timeout_seconds=90):
            return {
                "ok": False,
                "status": "second_next_not_found",
                "errors": ["두 번째 다음 버튼을 찾지 못했습니다"],
                "final_url": page.url,
                "failure_screenshot": self._save_failure_screenshot(page),
            }
        page.wait_for_timeout(1500)

        caption_box = self._first_locator(
            page,
            [
                'div[aria-label="문구를 입력하세요..."][contenteditable="true"]',
                'div[aria-label="Write a caption..."][contenteditable="true"]',
                'div[role="textbox"][contenteditable="true"]',
                'textarea[aria-label*="caption" i]',
            ],
        )
        if caption_box is not None and normalized.get("caption"):
            caption_box.click()
            caption_box.fill(normalized["caption"])

        if not self._click_first(
            page,
            [
                'div[role="button"]:has-text("공유")',
                'button:has-text("공유")',
                'div[role="button"]:has-text("Share")',
                'button:has-text("Share")',
            ],
        ):
            return {
                "ok": False,
                "status": "share_button_not_found",
                "errors": ["공유 버튼을 찾지 못했습니다"],
                "final_url": page.url,
            }

        completion = self._wait_for_upload_completion(page, timeout_seconds=180)
        completion["final_url"] = page.url
        return completion

    def _wait_for_upload_completion(
        self,
        page: Any,
        timeout_seconds: int,
    ) -> Dict[str, Any]:
        deadline = time.time() + max(30, int(timeout_seconds))
        success_texts = (
            "게시물이 공유되었습니다",
            "릴스가 공유되었습니다",
            "Your post has been shared",
            "Your reel has been shared",
        )

        while time.time() < deadline:
            body_text = ""
            try:
                body_text = page.locator("body").inner_text(timeout=2000)
            except Exception:
                pass

            if any(text in body_text for text in success_texts):
                return {
                    "ok": True,
                    "status": "uploaded",
                    "post_url": self._extract_instagram_post_url(page),
                    "errors": [],
                    "warnings": [],
                }

            if "/reel/" in self._clean_text(page.url) or "/p/" in self._clean_text(page.url):
                return {
                    "ok": True,
                    "status": "uploaded",
                    "post_url": self._clean_text(page.url),
                    "errors": [],
                    "warnings": [],
                }
            time.sleep(2)

        return {
            "ok": False,
            "status": "upload_confirmation_timeout",
            "post_url": self._extract_instagram_post_url(page),
            "errors": ["Instagram 공유 완료를 확인하지 못했습니다"],
            "warnings": [],
        }

    def _extract_instagram_post_url(self, page: Any) -> str:
        current_url = self._clean_text(getattr(page, "url", ""))
        if "/reel/" in current_url or "/p/" in current_url:
            return current_url

        for selector in ('a[href*="/reel/"]', 'a[href*="/p/"]'):
            try:
                locator = page.locator(selector)
                if locator.count() > 0:
                    href = self._clean_text(locator.first.get_attribute("href"))
                    if href.startswith("/"):
                        return f"https://www.instagram.com{href}"
                    if href:
                        return href
            except Exception:
                continue
        return ""

    def _wait_and_click_next(self, page: Any, timeout_seconds: int) -> bool:
        deadline = time.time() + max(15, int(timeout_seconds))
        selectors = [
            'div[role="button"]:has-text("다음")',
            'button:has-text("다음")',
            '[role="button"][aria-label="다음"]',
            '[aria-label="다음"]',
            'div[role="button"]:has-text("Next")',
            'button:has-text("Next")',
            '[role="button"][aria-label="Next"]',
            '[aria-label="Next"]',
        ]

        while time.time() < deadline:
            # 접근성 role 기반 탐색을 우선 사용한다.
            for name in ("다음", "Next"):
                try:
                    locator = page.get_by_role(
                        "button",
                        name=re.compile(rf"^\s*{re.escape(name)}\s*$", re.I),
                    )
                    for index in range(locator.count()):
                        candidate = locator.nth(index)
                        if candidate.is_visible() and candidate.is_enabled():
                            candidate.click()
                            return True
                except Exception:
                    pass

            try:
                if self._click_first(page, selectors):
                    return True
            except Exception:
                pass

            # 일부 UI는 텍스트가 span에 있고 상위 요소가 클릭 대상이다.
            for text in ("다음", "Next"):
                try:
                    text_locator = page.get_by_text(text, exact=True)
                    for index in range(text_locator.count()):
                        candidate = text_locator.nth(index)
                        if not candidate.is_visible():
                            continue
                        clickable = candidate.locator(
                            'xpath=ancestor-or-self::*[@role="button" or self::button][1]'
                        )
                        if clickable.count() > 0 and clickable.first.is_enabled():
                            clickable.first.click()
                            return True
                except Exception:
                    pass

            page.wait_for_timeout(1000)

        return False

    def _click_first(self, page: Any, selectors: Sequence[str]) -> bool:
        locator = self._first_locator(page, selectors)
        if locator is None:
            return False
        locator.click()
        return True

    def _click_optional(self, page: Any, selectors: Sequence[str]) -> bool:
        try:
            return self._click_first(page, selectors)
        except Exception:
            return False

    def _first_locator(self, page: Any, selectors: Sequence[str]) -> Optional[Any]:
        for selector in selectors:
            try:
                locator = page.locator(selector)
                count = locator.count()
                for index in range(count):
                    candidate = locator.nth(index)
                    if candidate.is_visible():
                        return candidate
            except Exception:
                continue
        return None

    def _locator_visible(self, page: Any, selector: str) -> bool:
        try:
            locator = page.locator(selector)
            return locator.count() > 0 and locator.first.is_visible()
        except Exception:
            return False

    def _save_failure_screenshot(self, page: Any) -> str:
        if page is None:
            return ""
        try:
            folder = Path("logs/instagram_upload")
            folder.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = folder / f"instagram_upload_failed_{stamp}.png"
            page.screenshot(path=str(path), full_page=True)
            return str(path)
        except Exception:
            return ""

    def _result_and_print(self, **kwargs: Any) -> Dict[str, Any]:
        result = self._result(**kwargs)
        self._print_result(result)
        return result

    def _result(
        self,
        *,
        ok: bool,
        status: str,
        dry_run: bool,
        upload_ready: bool,
        source: Dict[str, Any],
        normalized: Optional[Dict[str, Any]] = None,
        checks: Optional[Dict[str, bool]] = None,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        result = {
            "ok": bool(ok),
            "version": self.VERSION,
            "source_version": self._clean_text(source.get("dispatcher_version")),
            "status": status,
            "platform": self.PLATFORM,
            "executor": self.EXECUTOR_NAME,
            "dry_run": bool(dry_run),
            "upload_ready": bool(upload_ready),
            "actual_upload_performed": False,
            "job_id": self._clean_text(source.get("job_id")),
            "queue_id": self._clean_text(source.get("queue_id")),
            "video_path": self._clean_text(
                (normalized or {}).get("video_path")
                or source.get("video_path")
            ),
            "caption": self._clean_text((normalized or {}).get("caption")),
            "normalized": normalized or {},
            "checks": checks or {},
            "errors": errors or [],
            "warnings": warnings or [],
        }
        if isinstance(extra, dict):
            result.update(extra)
        return result

    def _print_result(self, result: Dict[str, Any]) -> None:
        print("[Sprint90-2 Instagram] Version:", self.VERSION, flush=True)
        print("[Sprint90-2 Instagram] Status:", result.get("status"), flush=True)
        print("[Sprint90-2 Instagram] Ready:", bool(result.get("upload_ready")), flush=True)
        print("[Sprint90-2 Instagram] Dry Run:", bool(result.get("dry_run")), flush=True)
        print(
            "[Sprint90-2 Instagram] Actual Upload:",
            bool(result.get("actual_upload_performed")),
            flush=True,
        )
        print("[Sprint90-2 Instagram] Post URL:", result.get("post_url", ""), flush=True)
        if result.get("errors"):
            print("[Sprint90-2 Instagram] ERROR:", result.get("errors"), flush=True)

    def _normalize_hashtag(self, value: Any) -> str:
        text = self._clean_text(value).replace("#", "")
        text = re.sub(r"\s+", "", text)
        return f"#{text}" if text else ""

    def _first_text(self, *values: Any) -> str:
        for value in values:
            text = self._clean_text(value)
            if text:
                return text
        return ""

    def _shorten(self, value: Any, limit: int) -> str:
        text = self._clean_text(value)
        return text if len(text) <= limit else text[:limit].rstrip()

    def _clean_text(self, value: Any) -> str:
        if value is None:
            return ""
        text = str(value).replace("\x00", "")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
    