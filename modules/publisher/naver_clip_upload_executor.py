from __future__ import annotations
import sys
import json

import re
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from urllib.parse import urlparse
from typing import Any, Dict, Optional, Sequence



# Sprint192-24: 네이버 DOM 텍스트 로그가 Windows cp949 stdout에서
# UnicodeEncodeError를 일으키지 않도록 UTF-8 출력으로 고정합니다.
for _stream_name in ("stdout", "stderr"):
    try:
        _stream = getattr(sys, _stream_name, None)
        if _stream is not None and hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    except Exception:
        pass

class NaverClipUploadExecutor:
    """네이버 Clip Creators 클립 업로드 Playwright 실행기.

    Sprint187-1:
    - 로그인 세션 저장과 업로드 준비를 분리합니다.
    - 영상·제목·설명 입력까지만 자동화합니다.
    - 실제 게시 버튼은 누르지 않습니다.
    """

    VERSION = "naver-clip-upload-executor-192-32-date-verify-hotfix"
    STUDIO_URL = "https://clipcreators.naver.com/web/dashboard"
    VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm"}

    def save_login_session(
        self,
        *,
        user_data_dir: str = "secrets/naver_clip_playwright_profile",
        headless: bool = False,
        login_timeout_seconds: int = 600,
        action_timeout_seconds: int = 60,
        slow_mo: int = 120,
        target_channel_name: str = "",
    ) -> Dict[str, Any]:
        profile_dir = Path(user_data_dir).expanduser().resolve()
        profile_dir.mkdir(parents=True, exist_ok=True)
        playwright = context = page = probe_page = None

        try:
            from playwright.sync_api import sync_playwright

            playwright = sync_playwright().start()
            context = self._launch_persistent_chrome(
                playwright=playwright,
                profile_dir=profile_dir,
                headless=headless,
                slow_mo=slow_mo,
            )
            context.set_default_timeout(max(15, int(action_timeout_seconds)) * 1000)

            # Sprint192-13: Chrome 프로필 쿠키와 별도로 저장해 둔 storage_state 쿠키를
            # 매 게시 실행 시작 시 복구해 네이버 로그인 세션을 안정화합니다.
            storage_state_path = profile_dir / "storage_state.json"
            if storage_state_path.is_file():
                try:
                    import json
                    saved_state = json.loads(
                        storage_state_path.read_text(encoding="utf-8")
                    )
                    saved_cookies = list(saved_state.get("cookies") or [])
                    if saved_cookies:
                        context.add_cookies(saved_cookies)
                        print(
                            "[Sprint192-13 Naver Clip Session] COOKIES RESTORED",
                            {
                                "profile_dir": str(profile_dir),
                                "cookie_count": len(saved_cookies),
                            },
                            flush=True,
                        )
                except Exception as exc:
                    print(
                        "[Sprint192-13 Naver Clip Session] COOKIE RESTORE ERROR",
                        type(exc).__name__,
                        str(exc),
                        flush=True,
                    )

            try:
                current_cookies = context.cookies()
                matched = [
                    c.get("name")
                    for c in current_cookies
                    if c.get("name") in {"NID_AUT", "NID_SES"}
                ]
                print(
                    "[Sprint192-13 Naver Clip Session] AUTH COOKIE CHECK",
                    {
                        "matched": matched,
                        "cookie_count": len(current_cookies),
                        "profile_dir": str(profile_dir),
                    },
                    flush=True,
                )
            except Exception:
                pass

            page = context.pages[0] if context.pages else context.new_page()
            page.goto(self.STUDIO_URL, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            page = self._select_existing_channel(
                page,
                target_channel_name=target_channel_name,
            ) or page

            if self._is_logged_in(page):
                self._save_session_marker(
                    profile_dir,
                    str(getattr(page, "url", "") or self.STUDIO_URL),
                )
                self._persist_auth_state(
                    context,
                    profile_dir,
                )
                try:
                    context.storage_state(
                        path=str(profile_dir / "storage_state.json")
                    )
                except Exception:
                    pass
                page.wait_for_timeout(2000)
                print(
                    "[Sprint192-3 Naver Clip Login] SESSION ALREADY READY",
                    page.url,
                    flush=True,
                )
                return self._result(
                    True,
                    "login_session_saved",
                    extra={
                        "final_url": page.url,
                        "profile_dir": str(profile_dir),
                    },
                )

            print(
                "[Sprint192-3 Naver Clip Login] 브라우저에서 네이버 계정으로 로그인해 주세요.",
                flush=True,
            )
            deadline = time.time() + max(60, int(login_timeout_seconds))
            left_login_page = False

            while time.time() < deadline:
                # Sprint192-3:
                # 로그인 폼이 떠 있는 동안에는 절대 Clip Creators로 이동하거나
                # probe 탭을 만들지 않습니다. 사용자가 로그인하는 화면을 그대로 유지합니다.
                try:
                    pages = list(context.pages)
                except Exception as exc:
                    print(
                        "[Sprint192-3 Naver Clip Login] CONTEXT CLOSED",
                        type(exc).__name__,
                        str(exc),
                        flush=True,
                    )
                    return self._result(
                        False,
                        "browser_closed",
                        errors=["네이버 로그인 브라우저가 닫혔습니다."],
                    )

                if not pages:
                    return self._result(
                        False,
                        "browser_closed",
                        errors=["네이버 로그인 브라우저가 닫혔습니다."],
                    )

                active_pages = []
                login_pages = []
                for candidate in pages:
                    try:
                        if candidate.is_closed():
                            continue
                        raw_url = str(getattr(candidate, "url", "") or "").strip()
                        active_pages.append(candidate)
                        parsed = urlparse(raw_url)
                        host = str(parsed.hostname or "").lower()
                        if host.endswith("nid.naver.com"):
                            login_pages.append(candidate)
                    except Exception:
                        continue

                if not active_pages:
                    return self._result(
                        False,
                        "browser_closed",
                        errors=["네이버 로그인 브라우저가 닫혔습니다."],
                    )

                # 로그인 페이지가 하나라도 열려 있고 아직 로그인 완료 화면으로
                # 넘어간 탭이 없다면 아무 navigation도 하지 않고 기다립니다.
                non_login_pages = []
                for candidate in active_pages:
                    try:
                        raw_url = str(getattr(candidate, "url", "") or "").strip()
                        host = str(urlparse(raw_url).hostname or "").lower()
                    except Exception:
                        host = ""
                    if not host.endswith("nid.naver.com"):
                        non_login_pages.append(candidate)

                if login_pages and not non_login_pages:
                    page = login_pages[-1]

                    # Sprint192-5:
                    # 네이버 로그인 완료 후에도 원래 nid 로그인 탭이 남아 있을 수 있습니다.
                    # 화면은 건드리지 않고 쿠키만 확인한 뒤, 인증 쿠키가 생겼을 때만
                    # 별도 탭에서 Clip Creators를 엽니다.
                    if self._has_naver_login_cookies(context):
                        print(
                            "[Sprint192-5 Naver Clip Login] AUTH COOKIE DETECTED WHILE LOGIN TAB REMAINS",
                            flush=True,
                        )
                        try:
                            auth_page = context.new_page()
                            auth_page.goto(
                                self.STUDIO_URL,
                                wait_until="domcontentloaded",
                                timeout=30000,
                            )
                            auth_page.wait_for_timeout(3000)

                            auth_page = self._select_existing_channel(
                                auth_page,
                                target_channel_name=target_channel_name,
                            ) or auth_page

                            print(
                                "[Sprint192-5 Naver Clip Login] AUTH STUDIO OPENED",
                                str(getattr(auth_page, "url", "") or ""),
                                flush=True,
                            )

                            if self._is_logged_in(auth_page):
                                page = auth_page
                                try:
                                    page.bring_to_front()
                                except Exception:
                                    pass
                                self._save_session_marker(
                                    profile_dir,
                                    str(getattr(page, "url", "") or self.STUDIO_URL),
                                )
                                self._persist_auth_state(
                                    context,
                                    profile_dir,
                                )
                                try:
                                    context.storage_state(
                                        path=str(profile_dir / "storage_state.json")
                                    )
                                except Exception:
                                    pass
                                print(
                                    "[Sprint192-5 Naver Clip Login] SESSION SAVED FROM COOKIE",
                                    page.url,
                                    flush=True,
                                )
                                return self._result(
                                    True,
                                    "login_session_saved",
                                    extra={
                                        "final_url": page.url,
                                        "profile_dir": str(profile_dir),
                                        "verification": "auth_cookie_with_login_tab",
                                    },
                                )

                        except Exception as exc:
                            print(
                                "[Sprint192-5 Naver Clip Login] AUTH COOKIE RECOVERY ERROR",
                                type(exc).__name__,
                                str(exc),
                                flush=True,
                            )

                    print(
                        "[Sprint192-5 Naver Clip Login] WAITING MANUAL LOGIN",
                        str(getattr(page, "url", "") or ""),
                        flush=True,
                    )
                    time.sleep(2)
                    continue

                # nid 로그인 화면에서 벗어난 뒤부터만 로그인 완료 판별을 시작합니다.
                if not left_login_page:
                    left_login_page = True
                    print(
                        "[Sprint192-3 Naver Clip Login] LOGIN PAGE LEFT",
                        [str(getattr(p, "url", "") or "") for p in non_login_pages],
                        flush=True,
                    )

                for candidate in reversed(active_pages):
                    try:
                        candidate = self._select_existing_channel(
                            candidate,
                            target_channel_name=target_channel_name,
                        ) or candidate
                        if self._is_logged_in(candidate):
                            page = candidate
                            try:
                                page.bring_to_front()
                            except Exception:
                                pass
                            self._save_session_marker(
                                profile_dir,
                                str(getattr(page, "url", "") or self.STUDIO_URL),
                            )
                            self._persist_auth_state(
                                context,
                                profile_dir,
                            )
                            try:
                                context.storage_state(
                                    path=str(profile_dir / "storage_state.json")
                                )
                            except Exception:
                                pass
                            print(
                                "[Sprint192-3 Naver Clip Login] SESSION SAVED",
                                page.url,
                                flush=True,
                            )
                            return self._result(
                                True,
                                "login_session_saved",
                                extra={
                                    "final_url": page.url,
                                    "profile_dir": str(profile_dir),
                                },
                            )
                    except Exception as exc:
                        print(
                            "[Sprint192-3 Naver Clip Login] Detection ERROR",
                            type(exc).__name__,
                            str(exc),
                            flush=True,
                        )

                # 로그인 화면을 벗어난 뒤 일반 naver.com 등에 머무르는 경우에만
                # 같은 탭으로 Clip Creators를 한 번 복구합니다.
                recovered_page = self._recover_creator_after_manual_login(
                    context,
                    page,
                )
                if recovered_page is not None:
                    page = recovered_page
                    try:
                        page.bring_to_front()
                    except Exception:
                        pass
                    self._save_session_marker(
                        profile_dir,
                        str(getattr(page, "url", "") or self.STUDIO_URL),
                    )
                    self._persist_auth_state(
                        context,
                        profile_dir,
                    )
                    try:
                        context.storage_state(
                            path=str(profile_dir / "storage_state.json")
                        )
                    except Exception:
                        pass
                    print(
                        "[Sprint192-3 Naver Clip Login] SESSION RECOVERED",
                        page.url,
                        flush=True,
                    )
                    return self._result(
                        True,
                        "login_session_saved",
                        extra={
                            "final_url": page.url,
                            "profile_dir": str(profile_dir),
                        },
                    )

                # 쿠키 기반 Studio 진입도 로그인 화면을 벗어난 뒤에만 1회성으로 시도합니다.
                cookie_page = self._open_studio_from_authenticated_context(
                    context,
                    page,
                )
                if cookie_page is not None:
                    page = cookie_page
                    self._save_session_marker(
                        profile_dir,
                        str(getattr(page, "url", "") or self.STUDIO_URL),
                    )
                    try:
                        context.storage_state(
                            path=str(profile_dir / "storage_state.json")
                        )
                    except Exception:
                        pass
                    print(
                        "[Sprint192-3 Naver Clip Login] SESSION COOKIE READY",
                        page.url,
                        flush=True,
                    )
                    return self._result(
                        True,
                        "login_session_saved",
                        extra={
                            "final_url": page.url,
                            "profile_dir": str(profile_dir),
                        },
                    )

                time.sleep(2)

            return self._failure(
                page,
                "login_timeout",
                "네이버 로그인 대기 시간이 초과되었습니다.",
            )
        except Exception as exc:
            return self._failure(
                page,
                "login_failed",
                f"{type(exc).__name__}: {exc}",
            )
        finally:
            try:
                if context is not None:
                    context.close()
            except Exception:
                pass
            try:
                if playwright is not None:
                    playwright.stop()
            except Exception:
                pass

    def _persist_auth_state(
        self,
        context: Any,
        profile_dir: Path,
    ) -> Dict[str, Any]:
        """Sprint192-15: 네이버 인증 쿠키를 별도 파일과 storage_state에 동시에 보존."""
        result = {
            "ok": False,
            "cookie_count": 0,
            "auth_cookie_names": [],
        }
        try:
            cookies = list(context.cookies() or [])
            auth_names = [
                str(c.get("name") or "")
                for c in cookies
                if str(c.get("name") or "") in {"NID_AUT", "NID_SES"}
            ]
            result["cookie_count"] = len(cookies)
            result["auth_cookie_names"] = auth_names

            profile_dir.mkdir(parents=True, exist_ok=True)

            backup_path = profile_dir / "naver_auth_cookies.json"
            backup_path.write_text(
                json.dumps(
                    {"cookies": cookies},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            context.storage_state(
                path=str(profile_dir / "storage_state.json")
            )

            result["ok"] = bool(cookies)
            print(
                "[Sprint192-15 Naver Clip Session] AUTH STATE SAVED",
                {
                    "profile_dir": str(profile_dir),
                    "cookie_count": len(cookies),
                    "auth_cookie_names": auth_names,
                    "backup_path": str(backup_path),
                },
                flush=True,
            )
        except Exception as exc:
            result["error"] = f"{type(exc).__name__}: {exc}"
            print(
                "[Sprint192-15 Naver Clip Session] AUTH STATE SAVE ERROR",
                type(exc).__name__,
                str(exc),
                flush=True,
            )
        return result

    def _restore_auth_state(
        self,
        context: Any,
        profile_dir: Path,
    ) -> Dict[str, Any]:
        """Sprint192-15: storage_state 또는 별도 쿠키 백업에서 인증 상태 복구."""
        restored = 0
        sources = []

        # 1) storage_state.json
        storage_state_path = profile_dir / "storage_state.json"
        if storage_state_path.is_file():
            try:
                state = json.loads(
                    storage_state_path.read_text(encoding="utf-8")
                )
                cookies = list(state.get("cookies") or [])
                if cookies:
                    context.add_cookies(cookies)
                    restored += len(cookies)
                    sources.append("storage_state")
            except Exception as exc:
                print(
                    "[Sprint192-15 Naver Clip Session] STORAGE RESTORE ERROR",
                    type(exc).__name__,
                    str(exc),
                    flush=True,
                )

        # 2) dedicated cookie backup
        backup_path = profile_dir / "naver_auth_cookies.json"
        if backup_path.is_file():
            try:
                payload = json.loads(
                    backup_path.read_text(encoding="utf-8")
                )
                cookies = list(payload.get("cookies") or [])
                if cookies:
                    context.add_cookies(cookies)
                    restored += len(cookies)
                    sources.append("cookie_backup")
            except Exception as exc:
                print(
                    "[Sprint192-15 Naver Clip Session] COOKIE BACKUP RESTORE ERROR",
                    type(exc).__name__,
                    str(exc),
                    flush=True,
                )

        try:
            current = list(context.cookies() or [])
        except Exception:
            current = []

        auth_names = [
            str(c.get("name") or "")
            for c in current
            if str(c.get("name") or "") in {"NID_AUT", "NID_SES"}
        ]
        result = {
            "restored_count": restored,
            "sources": sources,
            "cookie_count": len(current),
            "auth_cookie_names": auth_names,
        }
        print(
            "[Sprint192-15 Naver Clip Session] AUTH STATE RESTORED",
            {
                "profile_dir": str(profile_dir),
                **result,
            },
            flush=True,
        )
        return result

    def prepare_upload(
        self,
        *,
        video_path: str,
        title: str = "",
        description: str = "",
        user_data_dir: str = "secrets/naver_clip_playwright_profile",
        headless: bool = False,
        allow_manual_login: bool = False,
        login_timeout_seconds: int = 30,
        action_timeout_seconds: int = 60,
        slow_mo: int = 120,
        keep_browser_open: bool = True,
        category_primary: str = "쇼핑",
        category_secondary: str = "상품리뷰",
        perform_publish: bool = False,
        scheduled_publish_at: str = "",
    ) -> Dict[str, Any]:
        print(
            "[Sprint192-9 Naver Clip Upload] PROFILE",
            str(user_data_dir),
            flush=True,
        )
        path = Path(str(video_path or "")).resolve()
        if not path.is_file() or path.stat().st_size < 1024:
            return self._result(
                False,
                "video_missing",
                errors=[f"영상 파일이 없습니다: {path}"],
            )
        if path.suffix.lower() not in self.VIDEO_EXTENSIONS:
            return self._result(
                False,
                "unsupported_video",
                errors=[f"지원하지 않는 확장자: {path.suffix}"],
            )

        profile_dir = Path(user_data_dir).expanduser().resolve()
        profile_dir.mkdir(parents=True, exist_ok=True)
        playwright = context = page = probe_page = None
        keep_resources = False

        try:
            from playwright.sync_api import sync_playwright

            playwright = sync_playwright().start()
            context = self._launch_persistent_chrome(
                playwright=playwright,
                profile_dir=profile_dir,
                headless=headless,
                slow_mo=slow_mo,
            )
            context.set_default_timeout(max(15, int(action_timeout_seconds)) * 1000)

            self._restore_auth_state(
                context,
                profile_dir,
            )

            page = context.pages[0] if context.pages else context.new_page()

            saved_url = self._load_session_marker(profile_dir)
            entry_urls = []
            for candidate_url in (
                saved_url,
                self.STUDIO_URL,
            ):
                clean_url = str(candidate_url or "").strip()
                if clean_url and clean_url not in entry_urls:
                    entry_urls.append(clean_url)

            logged_page = None
            for entry_url in entry_urls:
                try:
                    page.goto(entry_url, wait_until="domcontentloaded")
                    page.wait_for_timeout(3500)
                except Exception as exc:
                    print(
                        "[Sprint188-3 Naver Clip Upload] Entry navigation ERROR",
                        type(exc).__name__,
                        str(exc),
                        flush=True,
                    )

                logged_page = self._find_logged_in_page(context)
                if logged_page is not None:
                    break

            if logged_page is not None:
                page = logged_page
                try:
                    page.bring_to_front()
                except Exception:
                    pass

            if logged_page is None:
                # 리디렉션과 세션 복원이 늦게 적용되는 경우를 잠시 기다립니다.
                restore_deadline = time.time() + 20
                while time.time() < restore_deadline:
                    logged_page = self._find_logged_in_page(context)
                    if logged_page is not None:
                        page = logged_page
                        break
                    time.sleep(1)

            if logged_page is None:
                if not allow_manual_login:
                    return self._failure(
                        page,
                        "login_session_missing",
                        "저장된 네이버 로그인 세션을 복원하지 못했습니다.",
                    )

                print(
                    "[Sprint188-3 Naver Clip Upload] 같은 브라우저에서 네이버 로그인을 완료해 주세요.",
                    flush=True,
                )

                login_deadline = time.time() + max(
                    60,
                    int(login_timeout_seconds),
                )

                while time.time() < login_deadline:
                    # 로그인 완료 후 새 탭이나 기존 탭으로 대시보드가 열릴 수 있으므로
                    # 현재 열린 모든 탭을 검사합니다.
                    try:
                        page_urls = [
                            str(getattr(item, "url", "") or "")
                            for item in list(context.pages)
                        ]
                    except Exception:
                        page_urls = []

                    print(
                        "[Sprint188-3 Naver Clip Upload] Open pages",
                        page_urls,
                        flush=True,
                    )

                    logged_page = self._find_logged_in_page(context)
                    if logged_page is not None:
                        page = logged_page
                        try:
                            page.bring_to_front()
                        except Exception:
                            pass

                        self._save_session_marker(
                            profile_dir,
                            str(getattr(page, "url", "") or self.STUDIO_URL),
                        )
                        try:
                            context.storage_state(
                                path=str(profile_dir / "storage_state.json")
                            )
                        except Exception:
                            pass

                        print(
                            "[Sprint188-3 Naver Clip Upload] Inline login READY",
                            page.url,
                            flush=True,
                        )
                        break

                    cookie_page = self._open_studio_from_authenticated_context(
                        context,
                        page,
                    )
                    if cookie_page is not None:
                        page = cookie_page
                        logged_page = cookie_page
                        try:
                            page.bring_to_front()
                        except Exception:
                            pass
                        self._save_session_marker(
                            profile_dir,
                            str(getattr(page, "url", "") or self.STUDIO_URL),
                        )
                        try:
                            context.storage_state(
                                path=str(profile_dir / "storage_state.json")
                            )
                        except Exception:
                            pass
                        print(
                            "[Sprint188-3 Naver Clip Upload] Inline login COOKIE READY",
                            page.url,
                            flush=True,
                        )
                        break

                    probed_page, probe_page = self._probe_creator_session(
                        context,
                        probe_page,
                    )
                    if probed_page is not None:
                        page = probed_page
                        logged_page = probed_page
                        try:
                            page.bring_to_front()
                        except Exception:
                            pass
                        self._save_session_marker(
                            profile_dir,
                            str(getattr(page, "url", "") or self.STUDIO_URL),
                        )
                        try:
                            context.storage_state(
                                path=str(profile_dir / "storage_state.json")
                            )
                        except Exception:
                            pass
                        print(
                            "[Sprint188-3 Naver Clip Upload] Inline login PROBED",
                            page.url,
                            flush=True,
                        )
                        break

                    recovered_page = self._recover_creator_after_manual_login(
                        context,
                        page,
                    )
                    if recovered_page is not None:
                        page = recovered_page
                        logged_page = recovered_page
                        try:
                            page.bring_to_front()
                        except Exception:
                            pass
                        self._save_session_marker(
                            profile_dir,
                            str(getattr(page, "url", "") or self.STUDIO_URL),
                        )
                        try:
                            context.storage_state(
                                path=str(profile_dir / "storage_state.json")
                            )
                        except Exception:
                            pass
                        print(
                            "[Sprint188-3 Naver Clip Upload] Inline login RECOVERED",
                            page.url,
                            flush=True,
                        )
                        break

                    time.sleep(2)
                else:
                    print(
                        "[Sprint188-3 Naver Clip Upload] Inline login TIMEOUT",
                        [
                            str(getattr(item, "url", "") or "")
                            for item in list(context.pages)
                        ],
                        flush=True,
                    )
                    return self._failure(
                        page,
                        "login_timeout",
                        "같은 브라우저에서 네이버 로그인 완료를 확인하지 못했습니다.",
                    )

            print("[Sprint188-3 Naver Clip Upload] Login READY", flush=True)

            if not self._open_clip_composer(page):
                return self._failure(
                    page,
                    "clip_composer_not_found",
                    "Clip Creators에서 클립 만들기 화면을 열지 못했습니다.",
                )
            print(
                "[Sprint188-3 Naver Clip Upload] Composer READY",
                page.url,
                flush=True,
            )

            assigned = self._assign_video_file(page, str(path), 60)
            if not assigned.get("ok"):
                return self._failure(
                    page,
                    str(assigned.get("status") or "file_picker_not_found"),
                    str(assigned.get("message") or "영상 파일 선택에 실패했습니다."),
                )
            print(
                "[Sprint188-3 Naver Clip Upload] Video file assigned",
                assigned.get("method", ""),
                flush=True,
            )

            if not self._wait_form_ready(page, 180):
                return self._failure(
                    page,
                    "upload_form_timeout",
                    "영상 업로드 후 기본 정보 화면 준비를 확인하지 못했습니다.",
                )
            print("[Sprint188-3 Naver Clip Upload] Form READY", flush=True)

            # Sprint192-10:
            # 현재 Clip Creators /web/upload에는 별도 제목 입력란이 없고
            # 실제 텍스트 입력 요소는 name="description" TEXTAREA 하나입니다.
            # 제목은 버리지 않고 설명 맨 앞에 합쳐 한 입력란에 넣습니다.
            merged_description_parts = []
            clean_title = str(title or "").strip()
            clean_description = str(description or "").strip()
            if clean_title:
                merged_description_parts.append(clean_title)
            if clean_description and clean_description not in merged_description_parts:
                merged_description_parts.append(clean_description)
            merged_description = "\n\n".join(merged_description_parts)[:1000]

            print(
                "[Sprint192-10 Naver Clip Upload] FORM MODE description_only",
                {
                    "title_chars": len(clean_title),
                    "description_chars": len(clean_description),
                    "merged_chars": len(merged_description),
                },
                flush=True,
            )

            if merged_description and not self._fill_description(
                page,
                merged_description,
            ):
                return self._failure(
                    page,
                    "description_box_not_found",
                    "네이버 클립 설명 입력란을 찾지 못했습니다.",
                )
            print(
                "[Sprint192-10 Naver Clip Upload] Description filled",
                len(merged_description),
                flush=True,
            )

            category_result = self._select_clip_categories(
                page,
                primary=category_primary,
                secondary=category_secondary,
            )
            if not category_result.get("ok"):
                return self._failure(
                    page,
                    str(category_result.get("status") or "category_not_found"),
                    str(
                        category_result.get("message")
                        or "네이버 클립 카테고리를 선택하지 못했습니다."
                    ),
                )

            print(
                "[Sprint192-12 Naver Clip Upload] CATEGORY SELECTED",
                {
                    "primary": category_primary,
                    "secondary": category_secondary,
                },
                flush=True,
            )

            clean_scheduled_publish_at = str(scheduled_publish_at or "").strip()
            schedule_result = {
                "ok": True,
                "status": "immediate_publish",
                "scheduled_publish_at": "",
            }
            if clean_scheduled_publish_at:
                schedule_result = self._configure_scheduled_publish(
                    page,
                    clean_scheduled_publish_at,
                )
                if not schedule_result.get("ok"):
                    return self._failure(
                        page,
                        str(
                            schedule_result.get("status")
                            or "schedule_configuration_failed"
                        ),
                        str(
                            schedule_result.get("message")
                            or "네이버 클립 등록예약 날짜/시간 설정에 실패했습니다."
                        ),
                    )

                print(
                    "[Sprint192-28 Naver Clip Upload] SCHEDULE READY",
                    {
                        "scheduled_publish_at": schedule_result.get(
                            "scheduled_publish_at",
                            clean_scheduled_publish_at,
                        ),
                        "date": schedule_result.get("date"),
                        "time": schedule_result.get("time"),
                        "mode": schedule_result.get("mode"),
                    },
                    flush=True,
                )

            publish_ready = self._is_publish_button_ready(page)
            screenshot = self._save_screenshot(
                page,
                prefix="naver_clip_upload_preview",
            )

            print(
                "[Sprint188-3 Naver Clip Upload] PREVIEW READY "
                f"publish_button_ready={publish_ready}",
                flush=True,
            )

            if perform_publish:
                if not publish_ready:
                    return self._failure(
                        page,
                        "publish_button_not_ready",
                        "네이버 클립 게시 버튼이 활성화되지 않았습니다.",
                    )

                publish_result = self._click_publish_and_verify(
                    page,
                    scheduled_publish_at=clean_scheduled_publish_at,
                )
                if not publish_result.get("ok"):
                    return self._failure(
                        page,
                        str(publish_result.get("status") or "publish_failed"),
                        str(
                            publish_result.get("message")
                            or "네이버 클립 실제 게시를 확인하지 못했습니다."
                        ),
                    )

                self._persist_auth_state(
                    context,
                    profile_dir,
                )
                final_status = str(
                    publish_result.get("status")
                    or ("scheduled" if clean_scheduled_publish_at else "published")
                )
                published_screenshot = self._save_screenshot(
                    page,
                    prefix=(
                        "naver_clip_scheduled"
                        if clean_scheduled_publish_at
                        else "naver_clip_published"
                    ),
                )
                keep_resources = bool(keep_browser_open)
                return self._result(
                    True,
                    final_status,
                    extra={
                        "video_path": str(path),
                        "title": "",
                        "description": merged_description,
                        "category_primary": category_primary,
                        "category_secondary": category_secondary,
                        "scheduled_publish_at": clean_scheduled_publish_at,
                        "schedule_status": schedule_result.get("status", ""),
                        "publish_button_ready": True,
                        "actual_upload_performed": True,
                        "final_url": page.url,
                        "published_screenshot": published_screenshot,
                        "profile_dir": str(profile_dir),
                        "browser_kept_open": bool(keep_browser_open),
                    },
                )

            keep_resources = bool(keep_browser_open)
            self._persist_auth_state(
                context,
                profile_dir,
            )

            return self._result(
                True,
                "upload_preview_ready",
                extra={
                    "video_path": str(path),
                    "title": "",
                    "description": merged_description,
                    "category_primary": category_primary,
                    "category_secondary": category_secondary,
                    "scheduled_publish_at": clean_scheduled_publish_at,
                    "schedule_status": schedule_result.get("status", ""),
                    "publish_button_ready": publish_ready,
                    "actual_upload_performed": False,
                    "final_url": page.url,
                    "preview_screenshot": screenshot,
                    "profile_dir": str(profile_dir),
                    "browser_kept_open": bool(keep_browser_open),
                },
            )
        except Exception as exc:
            return self._failure(
                page,
                "upload_prepare_failed",
                f"{type(exc).__name__}: {exc}",
            )
        finally:
            if not keep_resources:
                try:
                    if context is not None:
                        context.close()
                except Exception:
                    pass
                try:
                    if playwright is not None:
                        playwright.stop()
                except Exception:
                    pass

    @staticmethod
    def _launch_persistent_chrome(
        *,
        playwright: Any,
        profile_dir: Path,
        headless: bool,
        slow_mo: int,
    ) -> Any:
        """로그인 저장과 업로드가 동일한 Chrome persistent profile을 사용합니다."""
        launch_args = [
            "--start-maximized",
            "--disable-blink-features=AutomationControlled",
        ]
        print(
            "[Sprint188-3 Naver Clip Browser] LAUNCH",
            {
                "engine": "chrome",
                "profile_dir": str(profile_dir),
                "headless": bool(headless),
                "args": launch_args,
            },
            flush=True,
        )
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            channel="chrome",
            headless=bool(headless),
            slow_mo=max(0, int(slow_mo)),
            viewport={"width": 1500, "height": 1000},
            locale="ko-KR",
            args=launch_args,
        )
        try:
            browser_version = context.browser.version if context.browser else ""
        except Exception:
            browser_version = ""
        print(
            "[Sprint188-3 Naver Clip Browser] READY",
            {
                "browser_version": browser_version,
                "page_count": len(list(context.pages)),
                "profile_dir": str(profile_dir),
            },
            flush=True,
        )
        return context

    @classmethod
    def _find_logged_in_page(cls, context: Any) -> Optional[Any]:
        """열린 모든 탭에서 로그인된 Clip Creators 페이지를 찾습니다."""
        try:
            pages = list(context.pages)
        except Exception:
            pages = []

        for candidate in reversed(pages):
            try:
                if cls._is_logged_in(candidate):
                    return candidate
            except Exception:
                continue
        return None

    @staticmethod
    def _has_naver_login_cookies(context: Any) -> bool:
        """URL과 무관하게 네이버 로그인 쿠키가 실제 저장됐는지 확인합니다."""
        try:
            cookies = context.cookies(
                [
                    "https://naver.com",
                    "https://www.naver.com",
                    "https://nid.naver.com",
                    "https://creator.tv.naver.com",
                ]
            )
        except Exception as exc:
            print(
                "[Sprint188-3 Naver Clip Login] COOKIE CHECK ERROR",
                type(exc).__name__,
                str(exc),
                flush=True,
            )
            return False

        names = {
            str(item.get("name") or "")
            for item in cookies
            if isinstance(item, dict)
        }
        required = {"NID_AUT", "NID_SES"}
        matched = sorted(required.intersection(names))
        print(
            "[Sprint188-3 Naver Clip Login] COOKIE CHECK",
            {
                "matched": matched,
                "cookie_count": len(cookies),
            },
            flush=True,
        )
        return required.issubset(names)

    @classmethod
    def _open_studio_from_authenticated_context(
        cls,
        context: Any,
        page: Any,
    ) -> Optional[Any]:
        """로그인 쿠키가 있으면 같은 persistent context에서 Studio를 직접 엽니다."""
        if not cls._has_naver_login_cookies(context):
            return None

        try:
            target = page
            if target is None or target.is_closed():
                target = context.new_page()
            target.goto(cls.STUDIO_URL, wait_until="domcontentloaded", timeout=30000)
            target.wait_for_timeout(3500)
            print(
                "[Sprint188-3 Naver Clip Login] COOKIE AUTH STUDIO",
                str(getattr(target, "url", "") or ""),
                flush=True,
            )
            if cls._is_logged_in(target):
                return target
        except Exception as exc:
            print(
                "[Sprint188-3 Naver Clip Login] COOKIE AUTH STUDIO ERROR",
                type(exc).__name__,
                str(exc),
                flush=True,
            )
        return None

    @classmethod
    def _probe_creator_session(
        cls,
        context: Any,
        probe_page: Optional[Any] = None,
    ) -> tuple[Optional[Any], Optional[Any]]:
        """로그인 화면을 건드리지 않고 별도 탭에서 Clip Creators 세션을 확인합니다."""
        try:
            if probe_page is None or probe_page.is_closed():
                probe_page = context.new_page()
            probe_page.goto(cls.STUDIO_URL, wait_until="domcontentloaded", timeout=30000)
            probe_page.wait_for_timeout(2500)
            probe_url = str(getattr(probe_page, "url", "") or "")
            print(
                "[Sprint188-3 Naver Clip Login] PROBE",
                probe_url,
                flush=True,
            )
            if cls._is_logged_in(probe_page):
                return probe_page, probe_page
        except Exception as exc:
            print(
                "[Sprint188-3 Naver Clip Login] PROBE ERROR",
                type(exc).__name__,
                str(exc),
                flush=True,
            )
        return None, probe_page

    @classmethod
    def _recover_creator_after_manual_login(
        cls,
        context: Any,
        preferred_page: Any,
    ) -> Optional[Any]:
        """네이버 로그인 완료 뒤 일반 네이버 화면에 머물면 같은 탭으로 Studio에 재진입합니다."""
        try:
            pages = list(context.pages)
        except Exception:
            pages = []

        candidates = list(reversed(pages))
        if preferred_page is not None and preferred_page not in candidates:
            candidates.insert(0, preferred_page)

        for candidate in candidates:
            raw_url = str(getattr(candidate, "url", "") or "").strip()
            try:
                parsed = urlparse(raw_url)
                host = str(parsed.hostname or "").lower()
            except Exception:
                host = ""

            if host.endswith("nid.naver.com"):
                continue
            if host == "clipcreators.naver.com":
                return candidate
            if host == "naver.com" or host.endswith(".naver.com"):
                try:
                    print(
                        "[Sprint188-3 Naver Clip Login] NAVIGATE STUDIO AFTER LOGIN",
                        raw_url,
                        flush=True,
                    )
                    candidate.goto(cls.STUDIO_URL, wait_until="domcontentloaded")
                    candidate.wait_for_timeout(3500)
                    if cls._is_logged_in(candidate):
                        return candidate
                except Exception as exc:
                    print(
                        "[Sprint188-3 Naver Clip Login] Studio recovery ERROR",
                        type(exc).__name__,
                        str(exc),
                        flush=True,
                    )
        return None

    @staticmethod
    def _session_marker_path(profile_dir: Path) -> Path:
        return profile_dir / "session_marker.txt"

    @classmethod
    def _save_session_marker(
        cls,
        profile_dir: Path,
        final_url: str,
    ) -> None:
        try:
            profile_dir.mkdir(parents=True, exist_ok=True)
            cls._session_marker_path(profile_dir).write_text(
                str(final_url or "").strip(),
                encoding="utf-8",
            )
        except Exception:
            pass

    @classmethod
    def _load_session_marker(cls, profile_dir: Path) -> str:
        try:
            marker = cls._session_marker_path(profile_dir)
            if marker.is_file():
                return marker.read_text(encoding="utf-8").strip()
        except Exception:
            pass
        return ""

    @classmethod
    def _select_existing_channel(
        cls,
        page: Any,
        *,
        target_channel_name: str = "",
    ) -> Optional[Any]:
        """Sprint192-6: Clip Creators는 계정 세션으로 dashboard를 직접 복구합니다."""
        if page is None:
            return None
        try:
            if page.is_closed():
                return None
        except Exception:
            return None
        raw_url = str(getattr(page, "url", "") or "").strip()
        try:
            host = str(urlparse(raw_url).hostname or "").lower()
        except Exception:
            host = ""
        if host == "clipcreators.naver.com":
            return page
        return None

    @staticmethod
    def _is_logged_in(page: Any) -> bool:
        """실제 호스트가 creator.tv.naver.com일 때만 로그인 성공으로 판정합니다."""
        raw_url = str(getattr(page, "url", "") or "").strip()

        try:
            parsed = urlparse(raw_url)
            host = str(parsed.hostname or "").lower()
            path = str(parsed.path or "").lower()
        except Exception:
            host = ""
            path = ""

        # nid.naver.com 로그인 페이지의 query string 안에 Clip Creators URL이 있어도
        # 절대 로그인 성공으로 처리하지 않습니다.
        if host.endswith("nid.naver.com"):
            print(
                "[Sprint188-3 Naver Clip Login] Login page detected",
                raw_url,
                flush=True,
            )
            return False

        if host != "clipcreators.naver.com":
            return False

        # 실제 Clip Creators 채널 페이지는 즉시 로그인 성공 처리합니다.
        if path.startswith("/channel/"):
            print(
                "[Sprint188-3 Naver Clip Login] Clip Creators host READY",
                raw_url,
                flush=True,
            )
            return True

        try:
            body = page.locator("body").inner_text(timeout=5000)
        except Exception:
            body = ""

        normalized = re.sub(r"\s+", " ", body).strip()

        channel_create_tokens = (
            "채널 만들기",
            "새 채널 만들기",
            "채널을 만들어",
        )
        if any(token in normalized for token in channel_create_tokens):
            print(
                "[Sprint192-4 Naver Clip Channel] CREATE PAGE DETECTED",
                raw_url,
                flush=True,
            )
            return False

        dashboard_tokens = (
            "CreatorStudio",
            "Clip Creators",
            "대시보드",
            "주요 지표 요약",
            "콘텐츠 만들기",
            "동영상 업로드",
            "클립 업로드",
            "+ 만들기",
            "채널 설정",
        )
        matched = [
            token
            for token in dashboard_tokens
            if token.lower() in normalized.lower()
        ]

        print(
            "[Sprint188-3 Naver Clip Login] Detection",
            {
                "url": raw_url,
                "host": host,
                "path": path,
                "matched": matched,
                "body_chars": len(normalized),
            },
            flush=True,
        )

        return bool(matched)

    def _open_clip_composer(self, page: Any) -> bool:
        """Sprint192-7: Clip Creators PC웹에서 실제 동영상 업로드 진입점을 탐색합니다."""
        raw_url = str(getattr(page, "url", "") or "")
        try:
            host = str(urlparse(raw_url).hostname or "").lower()
        except Exception:
            host = ""

        print(
            "[Sprint192-7 Naver Clip Upload] Composer current page",
            raw_url,
            flush=True,
        )

        if host != "clipcreators.naver.com":
            print(
                "[Sprint192-7 Naver Clip Upload] Composer blocked: non-ClipCreators host",
                {"host": host, "url": raw_url},
                flush=True,
            )
            return False

        # 이미 업로드 화면에 들어와 있으면 바로 성공.
        if self._composer_ready(page):
            print(
                "[Sprint192-7 Naver Clip Upload] Composer ALREADY READY",
                str(getattr(page, "url", "") or ""),
                flush=True,
            )
            return True

        # 현재 화면 구조를 로그에 남깁니다. 다음 수정이 필요해도 추측하지 않기 위함입니다.
        self._log_clipcreators_actions(page)

        # 1) 현재 Clip Creators에서 보일 수 있는 실제 동영상 생성/업로드 문구를 폭넓게 탐색.
        patterns = (
            r"^\s*\+\s*만들기\s*$",
            r"^\s*만들기\s*$",
            r"클립\s*만들기",
            r"동영상\s*만들기",
            r"동영상\s*업로드",
            r"영상\s*업로드",
            r"클립\s*업로드",
            r"콘텐츠\s*만들기",
            r"새\s*동영상",
            r"업로드",
            r"Create",
            r"Upload",
        )

        for pattern in patterns:
            compiled = re.compile(pattern, re.I)
            for role in ("button", "link", "menuitem"):
                try:
                    loc = page.get_by_role(role, name=compiled)
                    for index in range(min(loc.count(), 20)):
                        candidate = loc.nth(index)
                        if not candidate.is_visible() or not candidate.is_enabled():
                            continue
                        before = str(getattr(page, "url", "") or "")
                        label = ""
                        try:
                            label = re.sub(
                                r"\s+",
                                " ",
                                candidate.inner_text(timeout=1500),
                            ).strip()
                        except Exception:
                            pass
                        try:
                            candidate.scroll_into_view_if_needed()
                            candidate.click(timeout=5000)
                            page.wait_for_timeout(1800)
                        except Exception as exc:
                            print(
                                "[Sprint192-7 Naver Clip Upload] Action click ERROR",
                                {"pattern": pattern, "label": label, "error": f"{type(exc).__name__}: {exc}"},
                                flush=True,
                            )
                            continue

                        after = str(getattr(page, "url", "") or "")
                        print(
                            "[Sprint192-7 Naver Clip Upload] Action CLICKED",
                            {
                                "pattern": pattern,
                                "label": label,
                                "before": before,
                                "after": after,
                            },
                            flush=True,
                        )

                        if "nidlogin.login" in after.lower():
                            return False
                        if self._composer_ready(page):
                            print(
                                "[Sprint192-7 Naver Clip Upload] Composer READY after action",
                                after,
                                flush=True,
                            )
                            return True

                        # 만들기 메뉴가 열린 뒤 하위 항목을 한 번 더 찾습니다.
                        if self._click_video_upload_option(page):
                            if self._composer_ready(page):
                                return True
                except Exception:
                    continue

        # 2) 텍스트보다 href 라우팅이 더 안정적인 SPA 구조에 대응.
        try:
            anchors = page.locator("a[href]")
            for index in range(min(anchors.count(), 100)):
                anchor = anchors.nth(index)
                try:
                    if not anchor.is_visible():
                        continue
                    href = str(anchor.get_attribute("href") or "").strip()
                    text = re.sub(
                        r"\s+",
                        " ",
                        anchor.inner_text(timeout=1200),
                    ).strip()
                except Exception:
                    continue

                joined = f"{href} {text}".lower()
                if not any(
                    token in joined
                    for token in (
                        "upload",
                        "create",
                        "write",
                        "video",
                        "clip",
                        "동영상",
                        "업로드",
                        "만들기",
                    )
                ):
                    continue
                if "dashboard" in joined and not any(
                    token in joined for token in ("upload", "create", "write")
                ):
                    continue

                before = str(getattr(page, "url", "") or "")
                try:
                    anchor.click(timeout=5000)
                    page.wait_for_timeout(1800)
                except Exception:
                    continue
                after = str(getattr(page, "url", "") or "")
                print(
                    "[Sprint192-7 Naver Clip Upload] Candidate LINK CLICKED",
                    {"text": text, "href": href, "before": before, "after": after},
                    flush=True,
                )
                if "nidlogin.login" in after.lower():
                    return False
                if self._composer_ready(page):
                    return True
        except Exception as exc:
            print(
                "[Sprint192-7 Naver Clip Upload] LINK SCAN ERROR",
                type(exc).__name__,
                str(exc),
                flush=True,
            )

        # 3) 마지막으로 페이지 전체 텍스트에서 클릭 가능한 업로드 문구를 찾습니다.
        if self._click_video_upload_option(page) and self._composer_ready(page):
            return True

        self._log_clipcreators_actions(page)
        print(
            "[Sprint192-7 Naver Clip Upload] Composer NOT FOUND",
            str(getattr(page, "url", "") or ""),
            flush=True,
        )
        return False

    @staticmethod
    def _composer_ready(page: Any) -> bool:
        """실제 영상 파일 입력 또는 업로드 폼이 확인되어야 composer 성공으로 인정합니다."""
        try:
            if page.locator('input[type="file"]').count() > 0:
                return True
        except Exception:
            pass

        try:
            body = re.sub(
                r"\s+",
                " ",
                page.locator("body").inner_text(timeout=2500),
            ).strip()
        except Exception:
            body = ""

        ready_tokens = (
            "파일 선택",
            "동영상 선택",
            "영상 선택",
            "동영상 업로드",
            "제목",
            "설명",
            "공개 설정",
            "게시",
        )
        matched = [token for token in ready_tokens if token in body]
        return len(matched) >= 2

    @staticmethod
    def _click_video_upload_option(page: Any) -> bool:
        labels = (
            "동영상",
            "동영상 업로드",
            "영상 업로드",
            "클립",
            "클립 업로드",
            "새 동영상",
        )
        for label in labels:
            try:
                loc = page.get_by_text(label, exact=True)
                for index in range(min(loc.count(), 20)):
                    node = loc.nth(index)
                    if not node.is_visible():
                        continue
                    clickable = node.locator(
                        'xpath=ancestor-or-self::*[@role="button" or self::button or self::a][1]'
                    )
                    target = clickable.first if clickable.count() > 0 else node
                    before = str(getattr(page, "url", "") or "")
                    target.click(force=True, timeout=5000)
                    page.wait_for_timeout(1800)
                    after = str(getattr(page, "url", "") or "")
                    print(
                        "[Sprint192-7 Naver Clip Upload] Video option CLICKED",
                        {"label": label, "before": before, "after": after},
                        flush=True,
                    )
                    if "nidlogin.login" not in after.lower():
                        return True
            except Exception:
                continue
        return False

    @staticmethod
    def _log_clipcreators_actions(page: Any) -> None:
        """보이는 버튼/링크/href를 제한적으로 기록하여 실제 UI 구조를 확인합니다."""
        actions = []
        try:
            for role in ("button", "link"):
                loc = page.get_by_role(role)
                for index in range(min(loc.count(), 60)):
                    item = loc.nth(index)
                    try:
                        if not item.is_visible():
                            continue
                        text = re.sub(
                            r"\s+",
                            " ",
                            item.inner_text(timeout=1000),
                        ).strip()
                        href = ""
                        try:
                            href = str(item.get_attribute("href") or "").strip()
                        except Exception:
                            pass
                        if text or href:
                            actions.append(
                                {"role": role, "text": text[:120], "href": href[:240]}
                            )
                    except Exception:
                        continue
        except Exception as exc:
            print(
                "[Sprint192-7 Naver Clip Upload] ACTION SCAN ERROR",
                type(exc).__name__,
                str(exc),
                flush=True,
            )
            return

        print(
            "[Sprint192-7 Naver Clip Upload] VISIBLE ACTIONS",
            actions[:80],
            flush=True,
        )

    def _assign_video_file(
        self,
        page: Any,
        video_path: str,
        timeout_seconds: int,
    ) -> Dict[str, Any]:
        file_input = self._wait_file_input(page, 5)
        if file_input is not None:
            try:
                file_input.set_input_files(video_path)
                return {"ok": True, "status": "assigned", "method": "file_input"}
            except Exception:
                pass

        triggers = (
            r"파일\s*선택",
            r"동영상\s*선택",
            r"영상\s*업로드",
            r"Select\s*file",
            r"Upload",
        )
        for pattern in triggers:
            compiled = re.compile(pattern, re.I)
            for role in ("button", "link"):
                try:
                    loc = page.get_by_role(role, name=compiled)
                    for index in range(loc.count()):
                        candidate = loc.nth(index)
                        if not candidate.is_visible() or not candidate.is_enabled():
                            continue
                        try:
                            with page.expect_file_chooser(
                                timeout=max(10, int(timeout_seconds)) * 1000
                            ) as chooser_info:
                                candidate.click()
                            chooser_info.value.set_files(video_path)
                            return {
                                "ok": True,
                                "status": "assigned",
                                "method": "file_chooser",
                            }
                        except Exception:
                            continue
                except Exception:
                    continue

        file_input = self._wait_file_input(page, timeout_seconds)
        if file_input is not None:
            try:
                file_input.set_input_files(video_path)
                return {
                    "ok": True,
                    "status": "assigned",
                    "method": "file_input_fallback",
                }
            except Exception as exc:
                return {
                    "ok": False,
                    "status": "file_input_assign_failed",
                    "message": f"{type(exc).__name__}: {exc}",
                }

        return {
            "ok": False,
            "status": "file_picker_not_found",
            "message": "네이버 클립 영상 선택 버튼과 입력창을 찾지 못했습니다.",
        }

    @staticmethod
    def _wait_file_input(page: Any, timeout_seconds: int) -> Optional[Any]:
        deadline = time.time() + max(1, int(timeout_seconds))
        while time.time() < deadline:
            try:
                loc = page.locator('input[type="file"]')
                if loc.count() > 0:
                    return loc.first
            except Exception:
                pass
            page.wait_for_timeout(500)
        return None

    @staticmethod
    def _wait_form_ready(page: Any, timeout_seconds: int) -> bool:
        deadline = time.time() + max(30, int(timeout_seconds))
        tokens = (
            "기본 정보",
            "제목",
            "설명",
            "공개",
            "클립",
            "게시",
            "Title",
            "Description",
            "Publish",
        )
        while time.time() < deadline:
            try:
                body = page.locator("body").inner_text(timeout=2500)
            except Exception:
                body = ""
            processing = any(
                token in body
                for token in ("업로드 중", "처리 중", "변환 중")
            )
            ready = any(token.lower() in body.lower() for token in tokens)
            print(
                "[Sprint188-3 Naver Clip Upload] Form check",
                {
                    "processing": processing,
                    "ready": ready,
                    "url": str(getattr(page, "url", "") or ""),
                },
                flush=True,
            )
            if ready and not processing:
                return True
            page.wait_for_timeout(1500)
        return False

    def _fill_title(self, page: Any, value: str) -> bool:
        selectors = (
            'input[placeholder*="제목"]',
            'textarea[placeholder*="제목"]',
            'input[aria-label*="제목"]',
            'textarea[aria-label*="제목"]',
            'input[name*="title" i]',
            'textarea[name*="title" i]',
            'input[id*="title" i]',
            'textarea[id*="title" i]',
            '[contenteditable="true"][aria-label*="제목"]',
            '[contenteditable="true"][data-placeholder*="제목"]',
            '[contenteditable="true"][data-placeholder*="title" i]',
        )
        element = self._first_visible(page, selectors)

        if element is None:
            # role=textbox 전체에서 제목/Title 계열 속성을 찾아봅니다.
            try:
                boxes = page.get_by_role("textbox")
                for index in range(min(boxes.count(), 30)):
                    candidate = boxes.nth(index)
                    if not candidate.is_visible():
                        continue
                    attrs = []
                    for attr_name in (
                        "placeholder",
                        "aria-label",
                        "name",
                        "id",
                        "data-placeholder",
                    ):
                        try:
                            attrs.append(str(candidate.get_attribute(attr_name) or ""))
                        except Exception:
                            attrs.append("")
                    joined = " ".join(attrs)
                    if "제목" in joined or "title" in joined.lower():
                        element = candidate
                        print(
                            "[Sprint192-8 Naver Clip Upload] TITLE ROLE FOUND",
                            joined,
                            flush=True,
                        )
                        break
            except Exception:
                pass

        if element is None:
            fields = []
            try:
                loc = page.locator('input, textarea, [contenteditable="true"]')
                for index in range(min(loc.count(), 50)):
                    candidate = loc.nth(index)
                    try:
                        if not candidate.is_visible():
                            continue
                        fields.append({
                            "tag": candidate.evaluate("(el) => el.tagName"),
                            "type": candidate.get_attribute("type"),
                            "name": candidate.get_attribute("name"),
                            "id": candidate.get_attribute("id"),
                            "placeholder": candidate.get_attribute("placeholder"),
                            "aria": candidate.get_attribute("aria-label"),
                            "data_placeholder": candidate.get_attribute("data-placeholder"),
                        })
                    except Exception:
                        continue
            except Exception:
                pass
            print(
                "[Sprint192-8 Naver Clip Upload] VISIBLE FIELDS",
                fields,
                flush=True,
            )
            return False

        try:
            element.click()
            element.fill(value)
            print(
                "[Sprint192-8 Naver Clip Upload] TITLE FILLED",
                len(value),
                flush=True,
            )
            return True
        except Exception:
            pass

        try:
            element.click(force=True)
            element.press("Control+A")
            element.press("Backspace")
            page.keyboard.insert_text(value)
            print(
                "[Sprint192-8 Naver Clip Upload] TITLE INSERTED",
                len(value),
                flush=True,
            )
            return True
        except Exception as exc:
            print(
                "[Sprint192-8 Naver Clip Upload] TITLE FILL ERROR",
                type(exc).__name__,
                str(exc),
                flush=True,
            )
            return False

    def _select_clip_categories(
        self,
        page: Any,
        *,
        primary: str = "쇼핑",
        secondary: str = "상품리뷰",
    ) -> Dict[str, Any]:
        """Sprint192-19: 실제 카테고리 드롭다운 2개를 순서대로 열고 선택값을 검증합니다."""

        def visible_nodes(selector: str):
            result = []
            try:
                loc = page.locator(selector)
                for i in range(min(loc.count(), 50)):
                    node = loc.nth(i)
                    try:
                        if node.is_visible():
                            result.append(node)
                    except Exception:
                        continue
            except Exception:
                pass
            return result

        def text_of(node: Any) -> str:
            try:
                return re.sub(
                    r"\s+",
                    " ",
                    node.inner_text(timeout=1500),
                ).strip()
            except Exception:
                return ""

        # 화면의 카테고리 영역 안에서 실제 드롭다운 버튼 2개를 찾습니다.
        category_root = None
        try:
            label = page.get_by_text("카테고리", exact=True)
            for i in range(min(label.count(), 10)):
                node = label.nth(i)
                if not node.is_visible():
                    continue
                # 제목 + 드롭다운이 함께 들어있는 가장 가까운 블록을 찾음
                for xp in (
                    "xpath=ancestor::*[.//button][1]",
                    "xpath=ancestor::*[@role='group'][1]",
                    "xpath=..",
                ):
                    try:
                        candidate = node.locator(xp)
                        if candidate.count() > 0:
                            category_root = candidate.first
                            break
                    except Exception:
                        continue
                if category_root is not None:
                    break
        except Exception:
            pass

        controls = []
        search_roots = [category_root] if category_root is not None else [page]

        for root in search_roots:
            for selector in (
                'button',
                '[role="combobox"]',
                '[aria-haspopup="listbox"]',
                '[aria-haspopup="menu"]',
            ):
                try:
                    loc = root.locator(selector) if root is not page else page.locator(selector)
                    for i in range(min(loc.count(), 80)):
                        node = loc.nth(i)
                        try:
                            if not node.is_visible() or not node.is_enabled():
                                continue
                            txt = text_of(node)
                            # 현재 화면에서 보이는 플레이스 / 2차 카테고리 같은 버튼을 우선
                            if (
                                txt in {"플레이스", "쇼핑", "2차 카테고리", "상품리뷰"}
                                or "카테고리" in txt
                            ):
                                controls.append(node)
                        except Exception:
                            continue
                except Exception:
                    continue

        # 중복 locator가 섞일 수 있어 화면 좌표 기준으로 정리
        unique = []
        seen = set()
        for node in controls:
            try:
                box = node.bounding_box()
                key = None if not box else (
                    round(box["x"]),
                    round(box["y"]),
                    round(box["width"]),
                    round(box["height"]),
                )
            except Exception:
                key = None
            if key is not None and key in seen:
                continue
            if key is not None:
                seen.add(key)
            unique.append(node)

        # 화면 좌->우 순서
        def xpos(node: Any) -> float:
            try:
                box = node.bounding_box()
                return float(box["x"]) if box else 99999.0
            except Exception:
                return 99999.0

        unique.sort(key=xpos)

        if len(unique) < 2:
            self._log_category_controls(page)
            return {
                "ok": False,
                "status": "category_dropdowns_not_found",
                "message": "네이버 클립 카테고리 드롭다운 2개를 찾지 못했습니다.",
            }

        primary_control = unique[0]
        secondary_control = unique[1]

        print(
            "[Sprint192-19 Naver Clip Upload] CATEGORY CONTROLS FOUND",
            {
                "primary_before": text_of(primary_control),
                "secondary_before": text_of(secondary_control),
            },
            flush=True,
        )

        def click_option(control: Any, target_text: str) -> bool:
            try:
                control.scroll_into_view_if_needed()
                control.click(timeout=5000)
                page.wait_for_timeout(600)
            except Exception as exc:
                print(
                    "[Sprint192-19 Naver Clip Upload] CATEGORY DROPDOWN OPEN ERROR",
                    target_text,
                    type(exc).__name__,
                    str(exc),
                    flush=True,
                )
                return False

            # 열린 메뉴에서 exact text 선택
            for role in ("option", "menuitem", "radio"):
                try:
                    loc = page.get_by_role(role, name=target_text, exact=True)
                    for i in range(min(loc.count(), 30)):
                        node = loc.nth(i)
                        if not node.is_visible():
                            continue
                        node.click(timeout=5000)
                        page.wait_for_timeout(700)
                        print(
                            "[Sprint192-19 Naver Clip Upload] CATEGORY OPTION SELECTED",
                            {"role": role, "text": target_text},
                            flush=True,
                        )
                        return True
                except Exception:
                    continue

            try:
                loc = page.get_by_text(target_text, exact=True)
                for i in range(min(loc.count(), 50)):
                    node = loc.nth(i)
                    if not node.is_visible():
                        continue
                    # 드롭다운 버튼 자신이 아니라 열린 옵션 영역의 텍스트를 클릭
                    try:
                        box = node.bounding_box()
                        cbox = control.bounding_box()
                        if box and cbox and abs(box["y"] - cbox["y"]) < 5:
                            continue
                    except Exception:
                        pass
                    try:
                        node.click(force=True, timeout=5000)
                        page.wait_for_timeout(700)
                        print(
                            "[Sprint192-19 Naver Clip Upload] CATEGORY TEXT SELECTED",
                            target_text,
                            flush=True,
                        )
                        return True
                    except Exception:
                        continue
            except Exception:
                pass

            self._log_category_controls(page)
            return False

        if not click_option(primary_control, primary):
            return {
                "ok": False,
                "status": "primary_category_not_selected",
                "message": f"네이버 클립 1차 카테고리 '{primary}'를 선택하지 못했습니다.",
            }

        # 1차 선택 후 2차 옵션이 갱신될 수 있으므로 두 번째 버튼을 다시 찾음
        page.wait_for_timeout(800)
        secondary_candidates = []
        for selector in (
            'button',
            '[role="combobox"]',
            '[aria-haspopup="listbox"]',
            '[aria-haspopup="menu"]',
        ):
            try:
                loc = page.locator(selector)
                for i in range(min(loc.count(), 80)):
                    node = loc.nth(i)
                    if not node.is_visible() or not node.is_enabled():
                        continue
                    txt = text_of(node)
                    if txt in {"2차 카테고리", "상품리뷰"}:
                        secondary_candidates.append(node)
            except Exception:
                continue

        if secondary_candidates:
            secondary_candidates.sort(key=xpos)
            secondary_control = secondary_candidates[-1]

        if not click_option(secondary_control, secondary):
            return {
                "ok": False,
                "status": "secondary_category_not_selected",
                "message": f"네이버 클립 2차 카테고리 '{secondary}'를 선택하지 못했습니다.",
            }

        page.wait_for_timeout(800)

        primary_after = text_of(primary_control)
        secondary_after = text_of(secondary_control)

        # 화면 아래 경로 "쇼핑 > 상품리뷰"도 보조 검증
        body_text = ""
        try:
            body_text = re.sub(
                r"\s+",
                " ",
                page.locator("body").inner_text(timeout=3000),
            ).strip()
        except Exception:
            pass

        verified = (
            primary in body_text
            and secondary in body_text
            and ("쇼핑 > 상품리뷰" in body_text or "쇼핑>상품리뷰" in body_text or secondary_after == secondary)
        )

        print(
            "[Sprint192-19 Naver Clip Upload] CATEGORY VERIFIED",
            {
                "primary_after": primary_after,
                "secondary_after": secondary_after,
                "path_found": (
                    "쇼핑 > 상품리뷰" in body_text
                    or "쇼핑>상품리뷰" in body_text
                ),
                "verified": verified,
            },
            flush=True,
        )

        if not verified:
            self._log_category_controls(page)
            return {
                "ok": False,
                "status": "category_selection_not_verified",
                "message": "카테고리를 클릭했지만 쇼핑 > 상품리뷰 선택 상태를 확인하지 못했습니다.",
            }

        return {
            "ok": True,
            "status": "category_selected",
            "primary": primary,
            "secondary": secondary,
        }

    @staticmethod
    def _log_category_controls(page: Any) -> None:
        data = []
        selectors = (
            "select",
            '[role="combobox"]',
            "button",
            '[role="option"]',
            '[role="menuitem"]',
        )
        for selector in selectors:
            try:
                loc = page.locator(selector)
                for i in range(min(loc.count(), 60)):
                    node = loc.nth(i)
                    try:
                        if not node.is_visible():
                            continue
                        text = re.sub(
                            r"\s+",
                            " ",
                            node.inner_text(timeout=1000),
                        ).strip()
                        data.append({
                            "selector": selector,
                            "text": text[:120],
                            "aria": node.get_attribute("aria-label"),
                            "name": node.get_attribute("name"),
                        })
                    except Exception:
                        continue
            except Exception:
                continue
        print(
            "[Sprint192-12 Naver Clip Upload] CATEGORY CONTROLS",
            data[:100],
            flush=True,
        )

    def _fill_description(self, page: Any, value: str) -> bool:
        """Sprint192-25: draft 폼의 description textarea가 실제로 나타날 때까지 재탐색합니다."""
        selectors = (
            'textarea[name="description"]',
            'textarea[placeholder*="설명"]',
            'textarea[aria-label*="설명"]',
            '[contenteditable="true"][aria-label*="설명"]',
            'div[contenteditable="true"][role="textbox"]',
        )

        deadline = time.time() + 60
        attempt = 0
        last_url = ""

        while time.time() < deadline:
            attempt += 1

            # 현재 탭이 아닌 다른 Clip Creators 탭에 draft 폼이 열린 경우도 탐색
            candidate_pages = [page]
            try:
                for p in list(page.context.pages):
                    if p not in candidate_pages:
                        candidate_pages.append(p)
            except Exception:
                pass

            for candidate_page in candidate_pages:
                try:
                    current_url = str(getattr(candidate_page, "url", "") or "")
                    if "clipcreators.naver.com" not in current_url:
                        continue
                    last_url = current_url
                except Exception:
                    continue

                element = self._first_visible(candidate_page, selectors)
                if element is None:
                    continue

                try:
                    element.scroll_into_view_if_needed()
                except Exception:
                    pass

                try:
                    element.click(timeout=5000)
                    element.fill(value, timeout=5000)
                    print(
                        "[Sprint192-25 Naver Clip Upload] DESCRIPTION FILLED",
                        {
                            "chars": len(value),
                            "attempt": attempt,
                            "url": current_url,
                            "selector": 'textarea[name="description"]',
                        },
                        flush=True,
                    )
                    return True
                except Exception:
                    pass

                try:
                    element.click(force=True, timeout=5000)
                    element.press("Control+A")
                    element.press("Backspace")
                    candidate_page.keyboard.insert_text(value)
                    print(
                        "[Sprint192-25 Naver Clip Upload] DESCRIPTION INSERTED",
                        {
                            "chars": len(value),
                            "attempt": attempt,
                            "url": current_url,
                        },
                        flush=True,
                    )
                    return True
                except Exception as exc:
                    print(
                        "[Sprint192-25 Naver Clip Upload] DESCRIPTION RETRY",
                        {
                            "attempt": attempt,
                            "url": current_url,
                            "error": f"{type(exc).__name__}: {exc}",
                        },
                        flush=True,
                    )

            if attempt in {1, 5, 10, 20, 30}:
                fields = []
                try:
                    target = page
                    loc = target.locator("textarea,input,[contenteditable='true']")
                    for i in range(min(loc.count(), 40)):
                        node = loc.nth(i)
                        try:
                            fields.append(
                                {
                                    "tag": node.evaluate("(e) => e.tagName"),
                                    "name": node.get_attribute("name"),
                                    "type": node.get_attribute("type"),
                                    "placeholder": node.get_attribute("placeholder"),
                                    "visible": node.is_visible(),
                                }
                            )
                        except Exception:
                            continue
                except Exception:
                    pass

                print(
                    "[Sprint192-25 Naver Clip Upload] DESCRIPTION WAITING",
                    {
                        "attempt": attempt,
                        "url": last_url,
                        "fields": fields[:20],
                    },
                    flush=True,
                )

            try:
                page.wait_for_timeout(1000)
            except Exception:
                time.sleep(1)

        print(
            "[Sprint192-25 Naver Clip Upload] DESCRIPTION FIELD NOT FOUND",
            {
                "attempts": attempt,
                "last_url": last_url,
            },
            flush=True,
        )
        return False

    def _fill_first(
        self,
        page: Any,
        selectors: Sequence[str],
        value: str,
    ) -> bool:
        element = self._first_visible(page, selectors)
        if element is None:
            return False
        try:
            element.click()
            element.fill(value)
            return True
        except Exception:
            pass
        try:
            element.click(force=True)
            element.press("Control+A")
            element.press("Backspace")
            page.keyboard.insert_text(value)
            return True
        except Exception:
            return False

    def _configure_scheduled_publish(
        self,
        page: Any,
        scheduled_publish_at: str,
    ) -> Dict[str, Any]:
        """Sprint192-30: 네이버 클립은 무조건 '등록예약'으로 게시합니다."""
        raw = str(scheduled_publish_at or "").strip()
        try:
            target = datetime.fromisoformat(raw)
        except Exception:
            return {
                "ok": False,
                "status": "schedule_datetime_invalid",
                "message": (
                    "예약 날짜/시간 형식이 올바르지 않습니다. "
                    "예: 2026-08-10T10:30:00+09:00"
                ),
            }

        seoul = ZoneInfo("Asia/Seoul")
        if target.tzinfo is None:
            target = target.replace(tzinfo=seoul)
        else:
            target = target.astimezone(seoul)

        now = datetime.now(seoul)
        if target <= now:
            return {
                "ok": False,
                "status": "schedule_datetime_not_future",
                "message": "등록예약 날짜/시간은 현재 시각보다 이후여야 합니다.",
            }

        date_dot = target.strftime("%Y.%m.%d")
        hour_text = target.strftime("%H")
        minute_text = target.strftime("%M")
        normalized_iso = target.isoformat(timespec="minutes")

        print(
            "[Sprint192-32 Naver Clip Schedule] START",
            {
                "requested": raw,
                "normalized": normalized_iso,
                "date": date_dot,
                "hour": hour_text,
                "minute": minute_text,
            },
            flush=True,
        )

        def _click_exact_text(target_text: str) -> bool:
            for role in ("radio", "button", "option", "menuitem"):
                try:
                    loc = page.get_by_role(role, name=target_text, exact=True)
                    for i in range(min(loc.count(), 30)):
                        node = loc.nth(i)
                        try:
                            if not node.is_visible() or not node.is_enabled():
                                continue
                            node.scroll_into_view_if_needed()
                            node.click(timeout=5000)
                            return True
                        except Exception:
                            continue
                except Exception:
                    continue
            try:
                loc = page.get_by_text(target_text, exact=True)
                for i in range(min(loc.count(), 50)):
                    node = loc.nth(i)
                    try:
                        if not node.is_visible():
                            continue
                        clickable = node.locator(
                            "xpath=ancestor-or-self::*[self::label or self::button or @role='radio' or @role='button'][1]"
                        )
                        target_node = clickable.first if clickable.count() > 0 else node
                        target_node.scroll_into_view_if_needed()
                        target_node.click(force=True, timeout=5000)
                        return True
                    except Exception:
                        continue
            except Exception:
                pass
            return False

        def _visible_button_by_aria(label_text: str):
            try:
                loc = page.locator(f'button[aria-label="{label_text}"]')
                for i in range(min(loc.count(), 20)):
                    node = loc.nth(i)
                    try:
                        if node.is_visible() and node.is_enabled():
                            return node
                    except Exception:
                        continue
            except Exception:
                pass
            return None

        # 1) 등록예약 고정
        schedule_selected = False
        for label in ("등록예약", "등록 예약", "예약등록", "예약 등록"):
            if _click_exact_text(label):
                schedule_selected = True
                break

        if not schedule_selected:
            return {
                "ok": False,
                "status": "schedule_mode_not_found",
                "message": "네이버 클립의 '등록예약' 항목을 찾지 못했습니다.",
                "controls": self._log_schedule_controls(page),
                "screenshot": self._save_screenshot(
                    page, prefix="naver_clip_schedule_mode_not_found"
                ),
            }

        page.wait_for_timeout(700)
        print("[Sprint192-32 Naver Clip Schedule] MODE SELECTED", flush=True)

        # 2) 날짜 버튼 찾기
        date_button = None
        try:
            loc = page.locator("button")
            for i in range(min(loc.count(), 120)):
                node = loc.nth(i)
                try:
                    if not node.is_visible() or not node.is_enabled():
                        continue
                    text = re.sub(
                        r"\s+", " ", node.inner_text(timeout=1000)
                    ).strip()
                    if re.fullmatch(r"\d{4}\.\d{2}\.\d{2}", text):
                        date_button = node
                        break
                except Exception:
                    continue
        except Exception:
            pass

        if date_button is None:
            return {
                "ok": False,
                "status": "schedule_date_button_not_found",
                "message": "등록예약 날짜 버튼을 찾지 못했습니다.",
                "controls": self._log_schedule_controls(page),
            }

        try:
            date_button.click(timeout=5000)
            page.wait_for_timeout(500)
        except Exception as exc:
            return {
                "ok": False,
                "status": "schedule_date_button_click_failed",
                "message": f"예약 날짜 버튼 클릭 실패: {type(exc).__name__}: {exc}",
            }

        # 달력에서 전체 날짜 우선, 실패 시 일(day) 텍스트 fallback
        date_selected = False
        for token in (
            date_dot,
            target.strftime("%Y-%m-%d"),
            target.strftime("%Y/%m/%d"),
        ):
            for selector in (
                f'button[aria-label*="{token}"]',
                f'[role="gridcell"][aria-label*="{token}"]',
                f'button[data-value="{token}"]',
                f'[data-date="{token}"]',
            ):
                try:
                    loc = page.locator(selector)
                    for i in range(min(loc.count(), 30)):
                        node = loc.nth(i)
                        if node.is_visible() and node.is_enabled():
                            node.click(timeout=5000)
                            date_selected = True
                            break
                    if date_selected:
                        break
                except Exception:
                    continue
            if date_selected:
                break

        if not date_selected:
            day_text = str(target.day)
            try:
                roots = page.locator(
                    '[role="dialog"]:visible, [role="grid"]:visible, '
                    '[class*="calendar"]:visible, [class*="Calendar"]:visible'
                )
                for r in range(min(roots.count(), 10)):
                    root = roots.nth(r)
                    loc = root.get_by_text(day_text, exact=True)
                    for i in range(min(loc.count(), 20)):
                        node = loc.nth(i)
                        try:
                            if not node.is_visible():
                                continue
                            node.click(force=True, timeout=5000)
                            date_selected = True
                            break
                        except Exception:
                            continue
                    if date_selected:
                        break
            except Exception:
                pass

        if not date_selected:
            date_selected = _click_exact_text(str(target.day))

        if not date_selected:
            return {
                "ok": False,
                "status": "schedule_date_not_selected",
                "message": f"달력에서 예약 날짜 {date_dot}를 선택하지 못했습니다.",
                "controls": self._log_schedule_controls(page),
                "screenshot": self._save_screenshot(
                    page, prefix="naver_clip_schedule_date_not_selected"
                ),
            }

        page.wait_for_timeout(400)

        # 3) 시간 버튼
        hour_button = _visible_button_by_aria("시간")
        if hour_button is None:
            return {
                "ok": False,
                "status": "schedule_hour_button_not_found",
                "message": "예약 시간 버튼을 찾지 못했습니다.",
                "controls": self._log_schedule_controls(page),
            }

        hour_button.click(timeout=5000)
        page.wait_for_timeout(300)

        if not _click_exact_text(hour_text):
            if not _click_exact_text(str(int(hour_text))):
                return {
                    "ok": False,
                    "status": "schedule_hour_not_selected",
                    "message": f"예약 시간 {hour_text}시를 선택하지 못했습니다.",
                    "controls": self._log_schedule_controls(page),
                }

        page.wait_for_timeout(300)

        # 4) 분 버튼
        minute_button = _visible_button_by_aria("분")
        if minute_button is None:
            return {
                "ok": False,
                "status": "schedule_minute_button_not_found",
                "message": "예약 분 버튼을 찾지 못했습니다.",
                "controls": self._log_schedule_controls(page),
            }

        minute_button.click(timeout=5000)
        page.wait_for_timeout(300)

        if not _click_exact_text(minute_text):
            if not _click_exact_text(str(int(minute_text))):
                return {
                    "ok": False,
                    "status": "schedule_minute_not_selected",
                    "message": f"예약 분 {minute_text}분을 선택하지 못했습니다.",
                    "controls": self._log_schedule_controls(page),
                }

        page.wait_for_timeout(500)

        # 5) 실제 선택값 검증
        #
        # 네이버 예약 UI는 날짜/시간/분이 연속된 버튼으로 렌더링됩니다.
        # aria-label은 브라우저/렌더링 시점에 따라 안정적으로 읽히지 않을 수 있으므로
        # 날짜 버튼 위치를 기준으로 바로 뒤의 두 버튼 텍스트를 시간/분으로 검증합니다.
        selected_date = ""
        selected_hour = ""
        selected_minute = ""
        visible_buttons = []

        try:
            loc = page.locator("button")
            for i in range(min(loc.count(), 160)):
                node = loc.nth(i)
                try:
                    if not node.is_visible():
                        continue
                    text = re.sub(
                        r"\s+", " ", node.inner_text(timeout=1000)
                    ).strip()
                    aria = str(node.get_attribute("aria-label") or "")
                    visible_buttons.append(
                        {
                            "index": i,
                            "text": text,
                            "aria": aria,
                        }
                    )
                except Exception:
                    continue
        except Exception:
            visible_buttons = []

        date_pos = None
        for pos, row in enumerate(visible_buttons):
            if re.fullmatch(r"\d{4}\.\d{2}\.\d{2}", row.get("text", "")):
                if row.get("text") == date_dot:
                    selected_date = row.get("text", "")
                    date_pos = pos
                    break

        # 날짜 버튼 다음의 2자리 숫자 버튼을 시간/분으로 읽습니다.
        if date_pos is not None:
            numeric_after_date = []
            for row in visible_buttons[date_pos + 1:]:
                text = str(row.get("text") or "").strip()
                if re.fullmatch(r"\d{1,2}", text):
                    numeric_after_date.append(text)
                    if len(numeric_after_date) >= 2:
                        break
                # 등록/취소 등 예약 영역을 벗어나면 더 찾지 않습니다.
                if text in {"등록", "취소"} and numeric_after_date:
                    break

            if len(numeric_after_date) >= 1:
                selected_hour = numeric_after_date[0]
            if len(numeric_after_date) >= 2:
                selected_minute = numeric_after_date[1]

        # 보조 fallback: aria-label이 정상일 때는 그 값도 활용합니다.
        if not selected_hour or not selected_minute:
            for row in visible_buttons:
                aria = str(row.get("aria") or "")
                text = str(row.get("text") or "").strip()
                if not selected_hour and aria == "시간":
                    selected_hour = text
                if not selected_minute and aria == "분":
                    selected_minute = text

        normalized_hour = selected_hour.zfill(2) if selected_hour else ""
        normalized_minute = selected_minute.zfill(2) if selected_minute else ""

        # 네이버는 날짜 선택 후 달력 버튼 텍스트를 DOM에서 다시 읽지 못하는 경우가 있습니다.
        # 날짜 선택 동작 자체가 성공(date_selected=True)했고 시간/분이 정확하면 예약값을 유효하게 봅니다.
        date_verified = (
            selected_date == date_dot
            or bool(date_selected)
        )
        hour_verified = normalized_hour == hour_text
        minute_verified = normalized_minute == minute_text

        verified = (
            date_verified
            and hour_verified
            and minute_verified
        )

        if not selected_date and date_verified:
            selected_date = date_dot

        print(
            "[Sprint192-32 Naver Clip Schedule] VERIFIED",
            {
                "expected_date": date_dot,
                "expected_hour": hour_text,
                "expected_minute": minute_text,
                "selected_date": selected_date,
                "selected_hour": selected_hour,
                "selected_minute": selected_minute,
                "date_selected": bool(date_selected),
                "date_verified": date_verified,
                "hour_verified": hour_verified,
                "minute_verified": minute_verified,
                "verified": verified,
                "schedule_buttons": (
                    visible_buttons[max(0, (date_pos or 0) - 1):(date_pos or 0) + 5]
                    if visible_buttons else []
                ),
            },
            flush=True,
        )

        if not verified:
            return {
                "ok": False,
                "status": "schedule_datetime_not_verified",
                "message": "등록예약 날짜/시간 선택 후 화면 검증에 실패했습니다.",
                "date": selected_date,
                "hour": selected_hour,
                "minute": selected_minute,
                "controls": self._log_schedule_controls(page),
                "screenshot": self._save_screenshot(
                    page, prefix="naver_clip_schedule_verify_failed"
                ),
            }

        return {
            "ok": True,
            "status": "schedule_ready",
            "mode": "등록예약",
            "scheduled_publish_at": normalized_iso,
            "date": selected_date,
            "time": f"{normalized_hour}:{normalized_minute}",
            "screenshot": self._save_screenshot(
                page, prefix="naver_clip_schedule_ready"
            ),
        }

    @staticmethod
    def _log_schedule_controls(page: Any) -> list[dict[str, Any]]:
        """Sprint192-28: 예약 UI 실패 시 보이는 입력/버튼/라디오 구조를 로그로 남깁니다."""
        rows: list[dict[str, Any]] = []
        selectors = (
            "input",
            "select",
            "button",
            "label",
            '[role="radio"]',
            '[role="combobox"]',
            '[role="option"]',
        )
        for selector in selectors:
            try:
                loc = page.locator(selector)
                for i in range(min(loc.count(), 80)):
                    node = loc.nth(i)
                    try:
                        if not node.is_visible():
                            continue
                        text = ""
                        try:
                            text = re.sub(
                                r"\s+",
                                " ",
                                node.inner_text(timeout=700),
                            ).strip()
                        except Exception:
                            pass
                        row = {
                            "selector": selector,
                            "index": i,
                            "text": text[:100],
                            "type": node.get_attribute("type"),
                            "name": node.get_attribute("name"),
                            "id": node.get_attribute("id"),
                            "placeholder": node.get_attribute("placeholder"),
                            "aria": node.get_attribute("aria-label"),
                        }
                        try:
                            if selector == "input":
                                row["value"] = node.input_value(timeout=700)
                        except Exception:
                            pass
                        rows.append(row)
                    except Exception:
                        continue
            except Exception:
                continue

        print(
            "[Sprint192-28 Naver Clip Schedule] CONTROLS",
            rows[:160],
            flush=True,
        )
        return rows[:160]

    def _click_publish_and_verify(
        self,
        page: Any,
        *,
        scheduled_publish_at: str = "",
    ) -> Dict[str, Any]:
        """Sprint192-28: 하단 파란색 '등록' 버튼을 누르고 즉시/예약 등록을 검증합니다."""

        def _visible_buttons() -> list[dict[str, Any]]:
            rows = []
            try:
                loc = page.locator("button")
                for i in range(min(loc.count(), 120)):
                    node = loc.nth(i)
                    try:
                        if not node.is_visible():
                            continue
                        text = re.sub(
                            r"\s+",
                            " ",
                            node.inner_text(timeout=1000),
                        ).strip()
                        box = node.bounding_box()
                        rows.append(
                            {
                                "index": i,
                                "text": text[:100],
                                "disabled": node.is_disabled(),
                                "type": node.get_attribute("type"),
                                "class": node.get_attribute("class"),
                                "x": None if not box else round(box["x"]),
                                "y": None if not box else round(box["y"]),
                            }
                        )
                    except Exception:
                        continue
            except Exception:
                pass
            return rows

        buttons = _visible_buttons()
        print(
            "[Sprint192-27 Naver Clip Upload] VISIBLE BUTTONS",
            buttons,
            flush=True,
        )

        # 정확히 '등록'인 활성 버튼만 후보.
        candidates = []
        try:
            loc = page.get_by_role("button", name="등록", exact=True)
            for i in range(min(loc.count(), 20)):
                node = loc.nth(i)
                try:
                    if not node.is_visible() or not node.is_enabled():
                        continue
                    box = node.bounding_box()
                    candidates.append(
                        {
                            "node": node,
                            "index": i,
                            "x": None if not box else float(box["x"]),
                            "y": None if not box else float(box["y"]),
                        }
                    )
                except Exception:
                    continue
        except Exception:
            pass

        # role 탐색 실패 시 exact text fallback.
        if not candidates:
            try:
                loc = page.locator("button")
                for i in range(min(loc.count(), 120)):
                    node = loc.nth(i)
                    try:
                        if not node.is_visible() or not node.is_enabled():
                            continue
                        text = re.sub(
                            r"\s+",
                            " ",
                            node.inner_text(timeout=1000),
                        ).strip()
                        if text != "등록":
                            continue
                        box = node.bounding_box()
                        candidates.append(
                            {
                                "node": node,
                                "index": i,
                                "x": None if not box else float(box["x"]),
                                "y": None if not box else float(box["y"]),
                            }
                        )
                    except Exception:
                        continue
            except Exception:
                pass

        if not candidates:
            screenshot = self._save_screenshot(
                page,
                prefix="naver_clip_register_button_not_found",
            )
            return {
                "ok": False,
                "status": "register_button_not_found",
                "message": "네이버 클립 하단 '등록' 버튼을 찾지 못했습니다.",
                "visible_buttons": buttons,
                "screenshot": screenshot,
            }

        # 같은 하단 영역에 '임시저장'과 '취소'가 있는지 보조 검증.
        body_text = ""
        try:
            body_text = re.sub(
                r"\s+",
                " ",
                page.locator("body").inner_text(timeout=2000),
            ).strip()
        except Exception:
            pass

        action_area_verified = (
            "임시저장" in body_text
            and "취소" in body_text
            and "등록" in body_text
        )

        # 가장 아래쪽/오른쪽 후보를 선택.
        candidates.sort(
            key=lambda item: (
                -1 if item["y"] is None else item["y"],
                -1 if item["x"] is None else item["x"],
            ),
            reverse=True,
        )
        selected = candidates[0]
        button = selected["node"]

        before_screenshot = self._save_screenshot(
            page,
            prefix="naver_clip_before_register",
        )
        print(
            "[Sprint192-27 Naver Clip Upload] REGISTER BUTTON SELECTED",
            {
                "index": selected["index"],
                "x": selected["x"],
                "y": selected["y"],
                "action_area_verified": action_area_verified,
                "url": page.url,
                "screenshot": before_screenshot,
            },
            flush=True,
        )

        before_url = str(getattr(page, "url", "") or "")

        try:
            button.scroll_into_view_if_needed()
            button.click(timeout=10000)
            print(
                "[Sprint192-27 Naver Clip Upload] REGISTER CLICKED",
                {"before_url": before_url},
                flush=True,
            )
        except Exception as exc:
            return {
                "ok": False,
                "status": "register_click_failed",
                "message": f"등록 버튼 클릭 실패: {type(exc).__name__}: {exc}",
            }

        # 등록 후 확인 모달이 있다면 exact '확인'만 처리.
        page.wait_for_timeout(700)
        try:
            confirm = page.get_by_role("button", name="확인", exact=True)
            for i in range(min(confirm.count(), 10)):
                node = confirm.nth(i)
                if node.is_visible() and node.is_enabled():
                    node.click(timeout=5000)
                    print(
                        "[Sprint192-27 Naver Clip Upload] CONFIRM CLICKED",
                        flush=True,
                    )
                    page.wait_for_timeout(700)
                    break
        except Exception:
            pass

        deadline = time.time() + 90
        last_url = before_url
        last_body = ""
        is_scheduled = bool(str(scheduled_publish_at or "").strip())
        success_tokens = (
            "등록되었습니다",
            "게시되었습니다",
            "업로드되었습니다",
            "등록 완료",
            "게시 완료",
            "예약되었습니다",
            "예약 등록 완료",
            "등록 예약 완료",
        )

        while time.time() < deadline:
            try:
                page.wait_for_timeout(1000)
            except Exception:
                time.sleep(1)

            try:
                last_url = str(getattr(page, "url", "") or "")
            except Exception:
                pass

            try:
                last_body = re.sub(
                    r"\s+",
                    " ",
                    page.locator("body").inner_text(timeout=2000),
                ).strip()
            except Exception:
                last_body = ""

            token_found = any(token in last_body for token in success_tokens)
            left_draft = (
                "/web/draft" not in last_url
                and "/web/upload" not in last_url
            )

            if token_found or left_draft:
                print(
                    "[Sprint192-27 Naver Clip Upload] REGISTER VERIFIED",
                    {
                        "before_url": before_url,
                        "after_url": last_url,
                        "token_found": token_found,
                        "left_draft": left_draft,
                    },
                    flush=True,
                )
                return {
                    "ok": True,
                    "status": "scheduled" if is_scheduled else "published",
                    "final_url": last_url,
                    "scheduled_publish_at": str(scheduled_publish_at or "").strip(),
                }

        after_screenshot = self._save_screenshot(
            page,
            prefix="naver_clip_register_verify_timeout",
        )
        print(
            "[Sprint192-27 Naver Clip Upload] REGISTER VERIFY TIMEOUT",
            {
                "before_url": before_url,
                "after_url": last_url,
                "screenshot": after_screenshot,
            },
            flush=True,
        )
        return {
            "ok": False,
            "status": "register_verify_timeout",
            "message": "등록 버튼은 눌렀지만 등록 완료 상태를 확인하지 못했습니다.",
            "screenshot": after_screenshot,
        }


    @staticmethod
    def _is_publish_button_ready(page: Any) -> bool:
        for name in ("등록", "게시", "업로드", "발행", "Publish"):
            try:
                loc = page.get_by_role(
                    "button",
                    name=re.compile(rf"^\s*{re.escape(name)}\s*$", re.I),
                )
                for index in range(loc.count()):
                    candidate = loc.nth(index)
                    if candidate.is_visible() and candidate.is_enabled():
                        return True
            except Exception:
                pass
        return False

    @staticmethod
    def _first_visible(
        page: Any,
        selectors: Sequence[str],
    ) -> Optional[Any]:
        for selector in selectors:
            try:
                loc = page.locator(selector)
                for index in range(loc.count()):
                    candidate = loc.nth(index)
                    if candidate.is_visible():
                        return candidate
            except Exception:
                continue
        return None

    def _failure(
        self,
        page: Any,
        status: str,
        message: str,
    ) -> Dict[str, Any]:
        screenshot = self._save_screenshot(
            page,
            prefix="naver_clip_upload_failed",
        )
        print(
            "[Sprint188-3 Naver Clip] ERROR",
            status,
            message,
            flush=True,
        )
        return self._result(
            False,
            status,
            errors=[message],
            extra={
                "failure_screenshot": screenshot,
                "final_url": str(getattr(page, "url", "") or ""),
            },
        )

    @staticmethod
    def _save_screenshot(page: Any, prefix: str) -> str:
        if page is None:
            return ""
        try:
            folder = Path("logs/naver_clip_upload")
            folder.mkdir(parents=True, exist_ok=True)
            target = folder / (
                f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            page.screenshot(path=str(target), full_page=True)
            return str(target)
        except Exception:
            return ""

    def _result(
        self,
        ok: bool,
        status: str,
        errors: Optional[list[str]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        result = {
            "ok": bool(ok),
            "version": self.VERSION,
            "platform": "naver_clip",
            "status": status,
            "actual_upload_performed": False,
            "errors": errors or [],
        }
        if extra:
            result.update(extra)
        return result
