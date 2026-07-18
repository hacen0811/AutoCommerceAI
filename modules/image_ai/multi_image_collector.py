from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List
from urllib.parse import urlparse


class MultiImageCollector:
    """
    Sprint93-1A Multi Image Collector

    역할:
    - Playwright persistent context로 쿠팡 상품 페이지 접속
    - 기존 Chrome 프로필을 재사용
    - 왼쪽 썸네일을 순서대로 클릭해 큰 상품 이미지를 수집
    - 상세페이지를 스크롤하며 상세 이미지를 수집
    - 중복 URL/중복 파일/아이콘성 이미지를 제거
    - 기존 Sprint93-1 반환 구조와 manifest.json 형식을 유지

    환경변수:
    - COUPANG_IMAGE_PROFILE_DIR
      기본값: secrets/coupang_playwright_profile
    - COUPANG_IMAGE_HEADLESS
      기본값: 0 (실제 Chrome 창 표시)
    - COUPANG_IMAGE_KEEP_BROWSER_OPEN
      기본값: 0
    """

    VERSION = "multi-image-collector-93-1a"
    SOURCE_VERSION = "multi-image-collector-93-1"

    IMAGE_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".gif",
        ".bmp",
    }

    BLOCKED_HINTS = (
        "sprite",
        "icon",
        "logo",
        "badge",
        "favicon",
        "loading",
        "blank",
        "transparent",
        "tracking",
        "pixel",
        "review-profile",
        "vendorlogo",
        "event",
        "banner",
        "advertise",
    )

    DETAIL_HINTS = (
        "detail",
        "vendor_inventory",
        "product-description",
        "productdetail",
        "desc",
    )

    THUMBNAIL_SELECTORS = (
        "ul.prod-image__items li",
        ".prod-image__items li",
        "li.prod-image__item",
        "[class*='prod-image'] li",
        "[class*='thumbnail'] li",
        "[class*='thumb'] li",
    )

    MAIN_IMAGE_SELECTORS = (
        "img.prod-image__detail",
        ".prod-image__detail img",
        "#repImageContainer img",
        "[class*='prod-image__detail']",
        "[class*='product-image'] img",
        "meta[property='og:image']",
    )

    DETAIL_CONTAINER_SELECTORS = (
        "#productDetail",
        "#product-description",
        ".product-detail",
        ".product-description",
        "[class*='product-detail']",
        "[class*='product-description']",
        "[class*='vendor-item-content']",
    )

    def collect(
        self,
        coupang_url: str,
        project_id: Any = "",
        product_name: str = "",
        main_image_url: str = "",
        max_images: int = 40,
        timeout: int = 20,
        html: str = "",
    ) -> Dict[str, Any]:
        del html  # Sprint93-1 호환용 인자. 93-1A는 Playwright DOM을 사용합니다.

        started_at = time.time()
        clean_url = str(coupang_url or "").strip()
        max_images = max(1, min(int(max_images or 40), 100))

        result = self._empty_result(
            coupang_url=clean_url,
            project_id=project_id,
            product_name=product_name,
        )

        if not clean_url:
            result["status"] = "url_missing"
            result["errors"].append("coupang_url이 없습니다")
            return result

        if "coupang" not in clean_url.lower():
            result["status"] = "unsupported_url"
            result["errors"].append("쿠팡 상품 URL이 아닙니다")
            return result

        output_dir = self._output_dir(
            project_id=project_id,
            product_name=product_name,
            coupang_url=clean_url,
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        self._clear_previous_images(output_dir)

        result["output_dir"] = str(output_dir)
        result["profile_dir"] = str(self._profile_dir())

        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:
            result["status"] = "playwright_unavailable"
            result["errors"].append(
                f"Playwright를 불러오지 못했습니다: {type(exc).__name__}: {exc}"
            )
            return self._write_manifest(result, output_dir, started_at)

        context = None
        page = None

        try:
            with sync_playwright() as playwright:
                context = self._launch_context(
                    playwright=playwright,
                    timeout=timeout,
                )

                pages = list(context.pages or [])
                page = pages[-1] if pages else context.new_page()
                page.set_default_timeout(max(15000, int(timeout or 20) * 1000))

                response = page.goto(
                    clean_url,
                    wait_until="domcontentloaded",
                    timeout=max(30000, int(timeout or 20) * 2000),
                )

                if response is not None:
                    result["http_status"] = response.status

                page.wait_for_timeout(3500)
                result["final_url"] = str(page.url or clean_url)

                try:
                    result["page_title"] = str(page.title() or "")
                except Exception:
                    result["page_title"] = ""

                body_text = self._body_text(page)

                if self._is_blocked_page(body_text):
                    result["status"] = "blocked"
                    result["errors"].append(
                        "쿠팡에서 브라우저 접근을 제한했습니다. 열린 Chrome에서 페이지를 확인해 주세요."
                    )
                    self._save_debug(page, output_dir, result, "blocked")
                    return self._write_manifest(result, output_dir, started_at)

                candidates: List[Dict[str, Any]] = []

                if main_image_url:
                    normalized = self._normalize_url(main_image_url)
                    if normalized:
                        candidates.append(
                            {
                                "url": normalized,
                                "type": "main",
                                "source": "resolved_main_image",
                                "priority": 1200,
                            }
                        )

                thumbnail_candidates = self._collect_thumbnail_images(
                    page=page,
                    max_images=max_images,
                )
                candidates.extend(thumbnail_candidates)
                result["thumbnail_count"] = len(thumbnail_candidates)

                dom_main = self._current_main_image_url(page)
                if dom_main:
                    candidates.append(
                        {
                            "url": dom_main,
                            "type": "main",
                            "source": "main_dom",
                            "priority": 1100,
                        }
                    )

                detail_candidates = self._collect_detail_images(
                    page=page,
                    max_images=max_images,
                )
                candidates.extend(detail_candidates)
                result["detail_candidate_count"] = len(detail_candidates)

                candidates.extend(self._collect_page_image_candidates(page))
                candidates = self._dedupe_candidates(candidates)
                candidates = [
                    item
                    for item in candidates
                    if self._is_allowed_url(item.get("url", ""))
                ]
                candidates.sort(
                    key=lambda item: (
                        0 if item.get("type") == "main" else 1,
                        -int(item.get("priority") or 0),
                    )
                )
                candidates = candidates[:max_images]
                result["candidate_count"] = len(candidates)

                saved_images: List[Dict[str, Any]] = []
                seen_hashes = set()
                failed_count = 0

                for candidate in candidates:
                    if len(saved_images) >= max_images:
                        break

                    image_type = str(candidate.get("type") or "detail")
                    if not saved_images:
                        image_type = "main"
                    elif image_type == "main":
                        image_type = "option"

                    try:
                        downloaded = self._download_with_context(
                            context=context,
                            url=str(candidate.get("url") or ""),
                            output_dir=output_dir,
                            index=len(saved_images),
                            image_type=image_type,
                            timeout=timeout,
                        )

                        digest = downloaded.get("sha256", "")
                        if digest and digest in seen_hashes:
                            try:
                                Path(downloaded["path"]).unlink(missing_ok=True)
                            except Exception:
                                pass
                            continue

                        if digest:
                            seen_hashes.add(digest)

                        downloaded.update(
                            {
                                "source": candidate.get("source", "playwright_dom"),
                                "priority": int(candidate.get("priority") or 0),
                                "original_type": candidate.get("type", "detail"),
                            }
                        )
                        saved_images.append(downloaded)

                    except Exception as exc:
                        failed_count += 1
                        result["warnings"].append(
                            "이미지 다운로드 실패: "
                            f"{candidate.get('url', '')} | "
                            f"{type(exc).__name__}: {exc}"
                        )

                if saved_images:
                    saved_images[0]["type"] = "main"
                    for item in saved_images[1:]:
                        if item.get("type") == "main":
                            item["type"] = "option"

                result["images"] = saved_images
                result["image_count"] = len(saved_images)
                result["main_image_count"] = sum(
                    1 for item in saved_images if item.get("type") == "main"
                )
                result["detail_image_count"] = sum(
                    1 for item in saved_images if item.get("type") == "detail"
                )
                result["option_image_count"] = sum(
                    1 for item in saved_images if item.get("type") == "option"
                )
                result["download_failed_count"] = failed_count
                result["ok"] = bool(saved_images)
                result["ready"] = bool(saved_images)
                result["status"] = "collected" if saved_images else "empty"

                self._save_debug(page, output_dir, result, "result")
                return self._write_manifest(result, output_dir, started_at)

        except Exception as exc:
            result["status"] = "playwright_error"
            result["errors"].append(f"{type(exc).__name__}: {exc}")

            if page is not None:
                try:
                    self._save_debug(page, output_dir, result, "error")
                except Exception:
                    pass

            return self._write_manifest(result, output_dir, started_at)

        finally:
            keep_open = self._env_flag(
                "COUPANG_IMAGE_KEEP_BROWSER_OPEN",
                default=False,
            )
            if not keep_open and context is not None:
                try:
                    context.close()
                except Exception:
                    pass

    def _empty_result(
        self,
        coupang_url: str,
        project_id: Any,
        product_name: str,
    ) -> Dict[str, Any]:
        return {
            "ok": False,
            "ready": False,
            "version": self.VERSION,
            "source_version": self.SOURCE_VERSION,
            "status": "not_run",
            "source": "coupang_playwright_persistent_context",
            "coupang_url": str(coupang_url or ""),
            "final_url": "",
            "http_status": None,
            "page_title": "",
            "project_id": str(project_id or ""),
            "product_name": str(product_name or "").strip(),
            "profile_dir": "",
            "output_dir": "",
            "manifest_path": "",
            "debug_html_path": "",
            "screenshot_path": "",
            "image_count": 0,
            "main_image_count": 0,
            "detail_image_count": 0,
            "option_image_count": 0,
            "thumbnail_count": 0,
            "detail_candidate_count": 0,
            "candidate_count": 0,
            "download_failed_count": 0,
            "images": [],
            "warnings": [],
            "errors": [],
            "elapsed_seconds": 0.0,
        }

    def _profile_dir(self) -> Path:
        raw = str(
            os.environ.get(
                "COUPANG_IMAGE_PROFILE_DIR",
                "secrets/coupang_playwright_profile",
            )
        ).strip()
        profile_dir = Path(raw).expanduser()
        profile_dir.mkdir(parents=True, exist_ok=True)
        return profile_dir

    def _launch_context(self, playwright, timeout: int):
        profile_dir = self._profile_dir()
        headless = self._env_flag(
            "COUPANG_IMAGE_HEADLESS",
            default=False,
        )

        return playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            channel="chrome",
            headless=headless,
            viewport={"width": 1440, "height": 1000},
            locale="ko-KR",
            timezone_id="Asia/Seoul",
            accept_downloads=False,
            ignore_https_errors=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
                "--start-maximized",
                "--disable-notifications",
            ],
            timeout=max(30000, int(timeout or 20) * 2000),
        )

    def _collect_thumbnail_images(
        self,
        page,
        max_images: int,
    ) -> List[Dict[str, Any]]:
        collected: List[Dict[str, Any]] = []
        thumbnail_locator = None

        for selector in self.THUMBNAIL_SELECTORS:
            try:
                locator = page.locator(selector)
                count = locator.count()
                if count > 0:
                    thumbnail_locator = locator
                    break
            except Exception:
                continue

        if thumbnail_locator is None:
            return collected

        count = min(thumbnail_locator.count(), max_images)

        for index in range(count):
            item = thumbnail_locator.nth(index)

            try:
                item.scroll_into_view_if_needed(timeout=3000)
                page.wait_for_timeout(250)

                thumbnail_url = self._read_image_url_from_locator(item)

                try:
                    item.hover(timeout=2000)
                    page.wait_for_timeout(400)
                except Exception:
                    pass

                try:
                    item.click(timeout=3000, force=True)
                    page.wait_for_timeout(700)
                except Exception:
                    pass

                main_url = self._current_main_image_url(page)
                chosen_url = main_url or thumbnail_url

                if chosen_url:
                    collected.append(
                        {
                            "url": chosen_url,
                            "type": "main" if index == 0 else "option",
                            "source": "thumbnail_click",
                            "priority": 1150 - index,
                            "thumbnail_index": index,
                            "thumbnail_url": thumbnail_url,
                        }
                    )

            except Exception:
                continue

        return collected

    def _current_main_image_url(self, page) -> str:
        script = """
        (selectors) => {
            const read = (el) => {
                if (!el) return "";
                if (el.tagName && el.tagName.toLowerCase() === "meta") {
                    return el.getAttribute("content") || "";
                }
                const candidates = [
                    el.currentSrc,
                    el.src,
                    el.getAttribute && el.getAttribute("data-src"),
                    el.getAttribute && el.getAttribute("data-original"),
                    el.getAttribute && el.getAttribute("data-lazy-src"),
                    el.getAttribute && el.getAttribute("src")
                ];
                return candidates.find(Boolean) || "";
            };

            for (const selector of selectors) {
                const el = document.querySelector(selector);
                const value = read(el);
                if (value) return value;
            }
            return "";
        }
        """
        try:
            value = page.evaluate(script, list(self.MAIN_IMAGE_SELECTORS))
            return self._normalize_url(value)
        except Exception:
            return ""

    def _collect_detail_images(
        self,
        page,
        max_images: int,
    ) -> List[Dict[str, Any]]:
        self._scroll_detail_area(page)

        script = """
        (selectors) => {
            const roots = [];
            for (const selector of selectors) {
                document.querySelectorAll(selector).forEach(el => roots.push(el));
            }

            if (!roots.length) {
                roots.push(document.body);
            }

            const seen = new Set();
            const rows = [];

            const push = (value, source) => {
                if (!value || typeof value !== "string") return;
                value = value.trim();
                if (!value || value.startsWith("data:")) return;
                if (seen.has(value)) return;
                seen.add(value);
                rows.push({url: value, source});
            };

            for (const root of roots) {
                root.querySelectorAll("img").forEach(img => {
                    push(img.currentSrc, "detail_currentSrc");
                    push(img.src, "detail_src");
                    push(img.getAttribute("data-src"), "detail_data_src");
                    push(img.getAttribute("data-original"), "detail_data_original");
                    push(img.getAttribute("data-lazy-src"), "detail_lazy_src");

                    const srcset =
                        img.getAttribute("srcset") ||
                        img.getAttribute("data-srcset") ||
                        "";
                    srcset.split(",").forEach(part => {
                        push(part.trim().split(/\\s+/)[0], "detail_srcset");
                    });
                });

                root.querySelectorAll("[style*='background-image']").forEach(el => {
                    const style = el.getAttribute("style") || "";
                    const match = style.match(/url\\([\"']?([^\"')]+)[\"']?\\)/i);
                    if (match) push(match[1], "detail_background");
                });
            }

            return rows;
        }
        """

        try:
            rows = page.evaluate(script, list(self.DETAIL_CONTAINER_SELECTORS))
        except Exception:
            rows = []

        result: List[Dict[str, Any]] = []

        for index, row in enumerate(rows[: max_images * 4]):
            if not isinstance(row, dict):
                continue

            url = self._normalize_url(row.get("url"))
            if not url:
                continue

            result.append(
                {
                    "url": url,
                    "type": "detail",
                    "source": row.get("source", "detail_dom"),
                    "priority": 800 - index,
                }
            )

        return result

    def _collect_page_image_candidates(self, page) -> List[Dict[str, Any]]:
        script = """
        () => Array.from(document.images).map((img, index) => ({
            url:
                img.currentSrc ||
                img.src ||
                img.getAttribute("data-src") ||
                img.getAttribute("data-original") ||
                "",
            width: img.naturalWidth || 0,
            height: img.naturalHeight || 0,
            index
        }))
        """

        try:
            rows = page.evaluate(script)
        except Exception:
            rows = []

        candidates = []

        for row in rows:
            if not isinstance(row, dict):
                continue

            width = int(row.get("width") or 0)
            height = int(row.get("height") or 0)

            if width and height and (width < 180 or height < 180):
                continue

            url = self._normalize_url(row.get("url"))
            if not url:
                continue

            candidates.append(
                {
                    "url": url,
                    "type": self._infer_type(url, "detail"),
                    "source": "page_dom",
                    "priority": 300 + min(width, 1000) // 20,
                }
            )

        return candidates

    def _scroll_detail_area(self, page) -> None:
        try:
            page.evaluate(
                """
                () => {
                    const candidates = [
                        document.querySelector("#productDetail"),
                        document.querySelector("#product-description"),
                        document.querySelector(".product-detail"),
                        document.querySelector("[class*='product-detail']")
                    ].filter(Boolean);

                    const target = candidates[0];
                    if (target) {
                        target.scrollIntoView({behavior: "instant", block: "start"});
                    }
                }
                """
            )
        except Exception:
            pass

        stable_rounds = 0
        previous_height = 0

        for _ in range(18):
            try:
                current_height = int(
                    page.evaluate(
                        "() => Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)"
                    )
                    or 0
                )

                page.mouse.wheel(0, 1200)
                page.wait_for_timeout(500)

                if current_height == previous_height:
                    stable_rounds += 1
                else:
                    stable_rounds = 0

                previous_height = current_height

                if stable_rounds >= 3:
                    break
            except Exception:
                break

    def _read_image_url_from_locator(self, locator) -> str:
        script = """
        (el) => {
            const img =
                (el.tagName && el.tagName.toLowerCase() === "img")
                ? el
                : el.querySelector("img");

            if (!img) return "";

            return (
                img.currentSrc ||
                img.src ||
                img.getAttribute("data-src") ||
                img.getAttribute("data-original") ||
                img.getAttribute("data-lazy-src") ||
                ""
            );
        }
        """

        try:
            return self._normalize_url(locator.evaluate(script))
        except Exception:
            return ""

    def _download_with_context(
        self,
        context,
        url: str,
        output_dir: Path,
        index: int,
        image_type: str,
        timeout: int,
    ) -> Dict[str, Any]:
        response = context.request.get(
            url,
            headers={
                "Accept": (
                    "image/avif,image/webp,image/apng,image/svg+xml,"
                    "image/*,*/*;q=0.8"
                ),
                "Referer": "https://www.coupang.com/",
            },
            timeout=max(15000, int(timeout or 20) * 1000),
            fail_on_status_code=False,
        )

        if not response.ok:
            raise ValueError(f"HTTP {response.status}")

        content_type = str(
            response.headers.get("content-type")
            or response.headers.get("Content-Type")
            or ""
        ).split(";")[0].strip().lower()

        if content_type and not content_type.startswith("image/"):
            raise ValueError(f"이미지 응답이 아닙니다: {content_type}")

        data = response.body()

        if len(data) < 2048:
            raise ValueError(f"이미지 파일이 너무 작습니다: {len(data)} bytes")

        extension = self._extension(url, content_type)
        prefix = "00_main" if index == 0 else f"{index:02d}_{image_type}"
        target = output_dir / f"{prefix}{extension}"
        target.write_bytes(data)

        digest = hashlib.sha256(data).hexdigest()

        return {
            "index": index,
            "type": image_type,
            "url": url,
            "path": str(target),
            "filename": target.name,
            "extension": extension,
            "content_type": content_type,
            "size_bytes": len(data),
            "sha256": digest,
        }

    def _normalize_url(self, value: Any) -> str:
        url = str(value or "").strip().strip("\"'")
        if not url or url.startswith("data:"):
            return ""

        url = url.replace("\\/", "/").replace("&amp;", "&")

        if url.startswith("//"):
            url = "https:" + url

        return url

    def _dedupe_candidates(
        self,
        candidates: Iterable[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        deduped: Dict[str, Dict[str, Any]] = {}

        for candidate in candidates:
            url = str(candidate.get("url") or "").strip()
            if not url:
                continue

            key = self._canonical_url(url)
            current = deduped.get(key)

            if (
                current is None
                or int(candidate.get("priority") or 0)
                > int(current.get("priority") or 0)
            ):
                deduped[key] = dict(candidate)

        return list(deduped.values())

    def _canonical_url(self, url: str) -> str:
        parsed = urlparse(url)
        return (
            f"{parsed.scheme.lower()}://"
            f"{parsed.netloc.lower()}"
            f"{parsed.path}"
        ).rstrip("/")

    def _is_allowed_url(self, url: str) -> bool:
        lowered = str(url or "").lower()

        if not lowered.startswith(("http://", "https://")):
            return False

        if any(hint in lowered for hint in self.BLOCKED_HINTS):
            return False

        parsed = urlparse(lowered)
        suffix = Path(parsed.path).suffix.lower()

        if suffix and suffix not in self.IMAGE_EXTENSIONS:
            return False

        return True

    def _infer_type(self, url: str, default: str) -> str:
        lowered = str(url or "").lower()

        if any(hint in lowered for hint in self.DETAIL_HINTS):
            return "detail"

        return default

    def _extension(self, url: str, content_type: str) -> str:
        suffix = Path(urlparse(url).path).suffix.lower()

        if suffix in self.IMAGE_EXTENSIONS:
            return ".jpg" if suffix == ".jpeg" else suffix

        guessed = mimetypes.guess_extension(content_type or "") or ".jpg"

        if guessed == ".jpe":
            guessed = ".jpg"

        return guessed if guessed in self.IMAGE_EXTENSIONS else ".jpg"

    def _body_text(self, page) -> str:
        try:
            return page.locator("body").inner_text(timeout=5000)
        except Exception:
            return ""

    def _is_blocked_page(self, body_text: str) -> bool:
        lowered = str(body_text or "").lower()

        blocked_words = (
            "access denied",
            "접근이 제한",
            "비정상적인 접근",
            "서비스에 접속할 수 없습니다",
            "요청을 처리할 수 없습니다",
            "잠시 후 다시 시도",
        )

        return any(word in lowered for word in blocked_words)

    def _save_debug(
        self,
        page,
        output_dir: Path,
        result: Dict[str, Any],
        label: str,
    ) -> None:
        debug_dir = output_dir / "_debug"
        debug_dir.mkdir(parents=True, exist_ok=True)

        html_path = debug_dir / f"{label}_page.html"
        screenshot_path = debug_dir / f"{label}_page.png"

        try:
            html_path.write_text(
                page.content(),
                encoding="utf-8",
            )
            result["debug_html_path"] = str(html_path)
        except Exception:
            pass

        try:
            page.screenshot(
                path=str(screenshot_path),
                full_page=False,
            )
            result["screenshot_path"] = str(screenshot_path)
        except Exception:
            pass

    def _write_manifest(
        self,
        result: Dict[str, Any],
        output_dir: Path,
        started_at: float,
    ) -> Dict[str, Any]:
        result["elapsed_seconds"] = round(time.time() - started_at, 3)

        manifest_path = output_dir / "manifest.json"
        result["manifest_path"] = str(manifest_path)

        manifest_path.write_text(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        print(
            "[Sprint93-1A Multi Image] Version:",
            result.get("version", ""),
            flush=True,
        )
        print(
            "[Sprint93-1A Multi Image] Status:",
            result.get("status", ""),
            flush=True,
        )
        print(
            "[Sprint93-1A Multi Image] Thumbnails:",
            result.get("thumbnail_count", 0),
            flush=True,
        )
        print(
            "[Sprint93-1A Multi Image] Details:",
            result.get("detail_candidate_count", 0),
            flush=True,
        )
        print(
            "[Sprint93-1A Multi Image] Saved:",
            result.get("image_count", 0),
            flush=True,
        )
        print(
            "[Sprint93-1A Multi Image] Manifest:",
            result.get("manifest_path", ""),
            flush=True,
        )
        print(
            "[Sprint93-1A Multi Image] Errors:",
            result.get("errors", []),
            flush=True,
        )

        return result

    def _clear_previous_images(self, output_dir: Path) -> None:
        for child in output_dir.iterdir():
            if not child.is_file():
                continue

            if child.name == "manifest.json":
                try:
                    child.unlink()
                except Exception:
                    pass
                continue

            if child.suffix.lower() in self.IMAGE_EXTENSIONS:
                try:
                    child.unlink()
                except Exception:
                    pass

    def _output_dir(
        self,
        project_id: Any,
        product_name: str,
        coupang_url: str,
    ) -> Path:
        project_value = str(project_id or "").strip()

        if project_value:
            folder_name = f"project_{self._safe_name(project_value)}"
        else:
            name = self._safe_name(product_name)
            digest = hashlib.sha1(
                coupang_url.encode("utf-8", errors="ignore")
            ).hexdigest()[:10]
            folder_name = f"product_{name or digest}_{digest}"

        return Path("assets") / "product_images" / folder_name

    def _safe_name(self, value: Any) -> str:
        text = str(value or "").strip()
        safe = "".join(
            character
            for character in text
            if character.isalnum() or character in ("-", "_")
        )
        return safe[:80]

    def _env_flag(self, name: str, default: bool) -> bool:
        fallback = "1" if default else "0"
        value = str(os.environ.get(name, fallback)).strip().lower()
        return value in {"1", "true", "yes", "on"}