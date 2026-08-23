from __future__ import annotations
import json
import hashlib

import html
import os
import re
import shutil
import socket
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List


class ShoppingVideoSourceFinder:
    VERSION = "shopping-video-source-finder-196-3cl-reference-title-product-query"

    ALIASES = {
        "두피마사지기": ("scalp massager", "头皮按摩器"),
        "전동두피마사지기": ("electric scalp massager", "电动头皮按摩器"),
        "틈새수납장": ("slim storage cabinet", "夹缝收纳柜"),
        "밀폐용기": ("airtight food container", "密封保鲜盒"),
        "미니고데기": ("mini hair straightener", "迷你直发器"),
        "샤워기필터": ("shower filter", "淋浴过滤器"),
        "변기세정제": ("toilet cleaner", "马桶清洁剂"),
        "빨래건조대": ("clothes drying rack", "晾衣架"),
        "야채탈수기": ("salad spinner", "蔬菜脱水器"),
        "진공포장기": ("vacuum sealer", "真空封口机"),
        "신발정리대": ("shoe organizer", "鞋子收纳架"),
        "신발정리함": ("shoe organizer", "鞋子收纳架"),
        "신발 정리함": ("shoe organizer", "鞋子收纳架"),
        "신발수납장": ("shoe storage cabinet", "鞋柜"),
        "신발 수납장": ("shoe storage cabinet", "鞋柜"),
        "틈새신발수납장": ("slim shoe storage cabinet", "窄缝鞋柜"),
        "틈새 신발수납장": ("slim shoe storage cabinet", "窄缝鞋柜"),
        "회전수전": ("rotating faucet extender", "旋转水龙头"),
        "수전필터": ("faucet filter", "水龙头过滤器"),
        "틈새청소솔": ("crevice cleaning brush", "缝隙清洁刷"),
        "전동청소솔": ("electric cleaning brush", "电动清洁刷"),
        "창틀청소솔": ("window track cleaning brush", "窗槽清洁刷"),
        "배수구클리너": ("drain cleaner tool", "下水道清洁器"),
        "배수구거름망": ("sink drain strainer", "水槽过滤网"),
        "욕실스퀴지": ("bathroom squeegee", "浴室刮水器"),
        "문틈방충망": ("door gap insect screen", "门缝防虫网"),
        "틈막이": ("door gap seal", "门缝密封条"),
        "모기퇴치기": ("mosquito repellent device", "驱蚊器"),
        "초파리트랩": ("fruit fly trap", "果蝇诱捕器"),
        "제습제": ("moisture absorber", "除湿盒"),
        "신발건조기": ("shoe dryer", "烘鞋器"),
        "채소다지기": ("vegetable chopper", "切菜器"),
        "기름튐방지": ("oil splatter guard", "防油溅挡板"),
        "실리콘덮개": ("silicone stretch lids", "硅胶保鲜盖"),
        "싱크대정리대": ("sink organizer rack", "水槽收纳架"),
        "냉장고정리용기": ("fridge organizer bins", "冰箱收纳盒"),
        "미니블렌더": ("portable mini blender", "便携榨汁杯"),
        "전동와인오프너": ("electric wine opener", "电动开瓶器"),
        "압축수납팩": ("vacuum storage bags", "真空压缩袋"),
        "압축수납함": ("compression storage box", "压缩收纳箱"),
        "회전정리대": ("lazy susan organizer", "旋转收纳盘"),
        "서랍정리함": ("drawer organizer", "抽屉收纳盒"),
        "케이블정리함": ("cable organizer box", "电线收纳盒"),
        "옷걸이정리": ("hanger organizer", "衣架收纳"),
        "보풀제거기": ("fabric shaver", "毛球修剪器"),
        "휴대용스팀다리미": ("portable garment steamer", "手持挂烫机"),
        "세탁볼": ("laundry washing ball", "洗衣球"),
        "운동화세탁망": ("shoe laundry bag", "洗鞋袋"),
        "미니청소기": ("mini vacuum cleaner", "迷你吸尘器"),
        "차량용청소기": ("car vacuum cleaner", "车载吸尘器"),
        "무선에어건": ("cordless air duster", "无线吹尘器"),
        "탁상용선풍기": ("desk fan", "桌面风扇"),
        "휴대용선풍기": ("portable handheld fan", "手持风扇"),
        "목걸이선풍기": ("neck fan", "挂脖风扇"),
        "무선충전거치대": ("wireless charging stand", "无线充电支架"),
        "멀티탭정리함": ("power strip organizer box", "插线板收纳盒"),
        "속눈썹고데기": ("heated eyelash curler", "电热睫毛夹"),
    }

    PROFILE_ROOT = Path("browser_profiles") / "shopping_source_search"
    SHARED_SOURCE_PROFILE = Path("browser_profile") / "source_sites"

    @classmethod
    def _keywords(cls, product_name: str) -> Dict[str, str]:
        name = str(product_name or "").strip()
        en, zh = cls.ALIASES.get(name, ("", ""))
        return {"ko": name, "en": en, "zh": zh}

    @classmethod
    def _product_image_cache_path(cls) -> Path:
        path = Path("exports") / "shopping_discovery"
        path.mkdir(parents=True, exist_ok=True)
        return path / "product_images.json"

    @classmethod
    def lookup_naver_product_image(cls, product_name: str) -> Dict[str, Any]:
        """
        Sprint196-3AK
        NAVER 이미지 검색의 실제 썸네일/원본 후보를 대표 상품사진으로 사용합니다.

        3AH 문제:
        search.pstatic.net/common, spthumb 계열을 제외했는데,
        NAVER 검색 결과의 실제 썸네일이 바로 이 프록시 URL을 많이 사용합니다.
        따라서 정상 상품사진까지 전부 걸러져 image_url=None이 될 수 있었습니다.
        """
        product_name = str(product_name or "").strip()
        if not product_name:
            return {"ok": False, "product": "", "image_url": "", "status": "empty_product"}

        cache_path = cls._product_image_cache_path()
        cache: Dict[str, Any] = {}
        try:
            if cache_path.is_file():
                loaded = json.loads(cache_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    cache = loaded
        except Exception:
            cache = {}

        # 기존 정상 캐시는 재사용합니다.
        cached = cache.get(product_name)
        if isinstance(cached, dict) and str(cached.get("image_url") or "").startswith("http"):
            return {
                "ok": True,
                "product": product_name,
                "image_url": str(cached.get("image_url") or ""),
                "source": str(cached.get("source") or "naver_image_cache"),
                "status": "cached",
            }

        query_url = "https://search.naver.com/search.naver?" + urllib.parse.urlencode({
            "where": "image",
            "sm": "tab_jum",
            "query": product_name,
        })

        req = urllib.request.Request(
            query_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/151.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.7",
                "Referer": "https://www.naver.com/",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                body = response.read().decode("utf-8", errors="replace")

            candidates: List[str] = []

            # JSON/SSR 데이터 후보. NAVER는 배포 시 필드명이 달라질 수 있어 여러 키를 받습니다.
            patterns = [
                r'"originalUrl"\s*:\s*"([^"]+)"',
                r'"originalImageUrl"\s*:\s*"([^"]+)"',
                r'"imageUrl"\s*:\s*"([^"]+)"',
                r'"image_url"\s*:\s*"([^"]+)"',
                r'"thumbnail"\s*:\s*"([^"]+)"',
                r'"thumbnailUrl"\s*:\s*"([^"]+)"',
                r'"thumbUrl"\s*:\s*"([^"]+)"',
                r'"src"\s*:\s*"(https?:\\?/\\?/[^"]+)"',
            ]

            for pattern in patterns:
                for raw in re.findall(pattern, body, flags=re.I):
                    url = html.unescape(str(raw or ""))
                    url = url.replace("\\/", "/").replace("\\u0026", "&")
                    if url.startswith("http"):
                        candidates.append(url)

            # DOM img 후보.
            for raw in re.findall(
                r'<img[^>]+(?:src|data-src|data-lazy-src|data-original)="(https?://[^"]+)"',
                body,
                flags=re.I,
            ):
                candidates.append(html.unescape(str(raw or "")).replace("\\/", "/"))

            # NAVER 검색 프록시 URL은 정상 상품 이미지이므로 허용합니다.
            # 로고/아이콘/광고 스프라이트만 제외합니다.
            image_url = ""
            seen = set()
            for url in candidates:
                url = str(url or "").strip()
                if not url.startswith("http"):
                    continue
                low = url.lower()
                if any(x in low for x in (
                    "favicon",
                    "/logo",
                    "sstatic.net/static",
                    "searchad",
                    "icon_",
                    "sprite",
                    "banner",
                )):
                    continue
                key = url.split("#")[0]
                if key in seen:
                    continue
                seen.add(key)

                # 실제 이미지 CDN/프록시를 우선 사용.
                if any(host in low for host in (
                    "pstatic.net",
                    "naver.net",
                    "naver.com",
                    "shopping-phinf.pstatic.net",
                    "shop-phinf.pstatic.net",
                )):
                    image_url = url
                    break

            # CDN 우선 후보가 없으면 첫 일반 http 이미지 사용.
            if not image_url:
                for url in candidates:
                    url = str(url or "").strip()
                    if url.startswith("http"):
                        low = url.lower()
                        if not any(x in low for x in ("favicon", "/logo", "sprite", "banner")):
                            image_url = url
                            break

            if not image_url:
                result = {
                    "ok": False,
                    "product": product_name,
                    "image_url": "",
                    "status": "image_not_found",
                    "search_url": query_url,
                    "candidate_count": len(candidates),
                }
            else:
                result = {
                    "ok": True,
                    "product": product_name,
                    "image_url": image_url,
                    "source": "naver_image_search",
                    "status": "ready",
                    "candidate_count": len(candidates),
                }

            cache[product_name] = result
            try:
                cache_path.write_text(
                    json.dumps(cache, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            except Exception:
                pass

            return result

        except Exception as exc:
            return {
                "ok": False,
                "product": product_name,
                "image_url": "",
                "status": "image_lookup_error",
                "error": f"{type(exc).__name__}: {exc}",
                "search_url": query_url,
            }


    @classmethod
    def enrich_product_images_from_naver_shopping(
        cls,
        discovery_result: Dict[str, Any],
        *,
        max_items: int = 20,
    ) -> Dict[str, Any]:
        """
        Sprint196-3AL
        NAVER 이미지검색 HTML이 아니라 NAVER 쇼핑 검색 결과 화면에서
        각 후보 상품의 실제 상품 카드 이미지를 직접 읽습니다.

        - 한 번의 실제 Chrome context만 사용
        - 상품별 NAVER 쇼핑 검색 -> 첫 유효 상품 카드 이미지 추출
        - 기존 discovery 점수/순위/TikTok 로직은 변경하지 않음
        """
        from playwright.sync_api import sync_playwright

        result = dict(discovery_result or {})
        source_items = [dict(x or {}) for x in list(result.get("items") or [])]
        if not source_items:
            result["items"] = []
            return result

        profile = (Path("browser_profile") / "naver_product_image_lookup").resolve()
        profile.mkdir(parents=True, exist_ok=True)

        pw = None
        context = None
        page = None

        def _clean_url(value: Any) -> str:
            url = str(value or "").strip()
            if url.startswith("//"):
                url = "https:" + url
            return url

        def _valid_image(url: str) -> bool:
            low = str(url or "").lower()
            if not low.startswith("http"):
                return False
            if any(x in low for x in (
                "favicon", "logo", "sprite", "banner",
                "data:image", "icon_", "sstatic.net/static",
            )):
                return False
            return True

        try:
            pw = sync_playwright().start()
            context = pw.chromium.launch_persistent_context(
                user_data_dir=str(profile),
                channel="chrome",
                headless=False,
                viewport={"width": 1365, "height": 900},
                locale="en-US",
                timezone_id="America/Los_Angeles",
                args=[
                    "--start-maximized",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-session-crashed-bubble",
                    "--lang=en-US",
                ],
                timeout=15000,
            )
            try:
                context.set_extra_http_headers({
                    "Accept-Language": "en-US,en;q=0.9",
                })
            except Exception:
                pass
            try:
                context.set_default_timeout(3500)
                context.set_default_navigation_timeout(12000)
            except Exception:
                pass

            pages = list(context.pages or [])
            page = pages[0] if pages else context.new_page()
            for extra in pages[1:]:
                try:
                    extra.close()
                except Exception:
                    pass

            enriched = []
            for row_index, row in enumerate(source_items[:max_items]):
                product_name = str(row.get("product") or "").strip()
                existing = str(
                    row.get("image_url")
                    or row.get("thumbnail")
                    or row.get("product_image")
                    or ""
                ).strip()

                if _valid_image(existing):
                    row["image_url"] = existing
                    row["image_source"] = str(row.get("image_source") or "discovery_existing")
                    row["image_status"] = "existing"
                    enriched.append(row)
                    continue

                if not product_name:
                    row["image_status"] = "empty_product"
                    enriched.append(row)
                    continue

                target = "https://search.shopping.naver.com/search/all?" + urllib.parse.urlencode({
                    "query": product_name,
                })

                try:
                    print("[Sprint196-3AL Naver Product Image] SEARCH", product_name, flush=True)
                    try:
                        page.goto(target, wait_until="domcontentloaded", timeout=12000)
                    except Exception as nav_exc:
                        print(
                            "[Sprint196-3AL Naver Product Image] NAV_WARN",
                            product_name,
                            type(nav_exc).__name__,
                            str(nav_exc)[:180],
                            flush=True,
                        )
                    try:
                        page.wait_for_timeout(1300)
                    except Exception:
                        pass

                    # NAVER shopping cards change class names often.
                    # Prefer image elements inside product-like links/cards.
                    candidates = page.evaluate(
                        """
                        () => {
                            const out = [];
                            const imgs = Array.from(document.images || []);
                            for (const img of imgs) {
                                const src =
                                    img.currentSrc ||
                                    img.src ||
                                    img.getAttribute('data-src') ||
                                    img.getAttribute('data-original') ||
                                    '';
                                if (!src) continue;

                                const a = img.closest('a[href]');
                                const card = img.closest(
                                    'li, article, div[class*="product"], div[class*="item"], div[class*="adProduct"]'
                                );
                                const text = String(
                                    (a && (a.innerText || a.getAttribute('title'))) ||
                                    (card && card.innerText) ||
                                    img.alt ||
                                    ''
                                ).trim();

                                out.push({
                                    src: String(src),
                                    alt: String(img.alt || ''),
                                    text: text.slice(0, 500),
                                    width: Number(img.naturalWidth || img.width || 0),
                                    height: Number(img.naturalHeight || img.height || 0),
                                    href: String(a ? a.href : '')
                                });
                            }
                            return out;
                        }
                        """
                    ) or []

                    best_url = ""
                    product_compact = re.sub(r"\s+", "", product_name).lower()

                    # First pass: product text/alt matching.
                    scored = []
                    for cand in candidates:
                        url = _clean_url(cand.get("src"))
                        if not _valid_image(url):
                            continue
                        w = int(cand.get("width") or 0)
                        h = int(cand.get("height") or 0)
                        if w and h and (w < 80 or h < 80):
                            continue

                        text_blob = " ".join([
                            str(cand.get("text") or ""),
                            str(cand.get("alt") or ""),
                        ])
                        compact = re.sub(r"\s+", "", text_blob).lower()

                        score = 0
                        if product_compact and product_compact in compact:
                            score += 100
                        for token in re.findall(r"[0-9A-Za-z가-힣]{2,}", product_name):
                            if token.lower() in compact:
                                score += 12
                        if "shopping-phinf.pstatic.net" in url.lower() or "shop-phinf.pstatic.net" in url.lower():
                            score += 30
                        if "pstatic.net" in url.lower():
                            score += 15
                        if w >= 150 and h >= 150:
                            score += 8

                        scored.append((score, url))

                    if scored:
                        scored.sort(key=lambda x: x[0], reverse=True)
                        best_url = scored[0][1]

                    row["image_url"] = best_url
                    row["image_source"] = "naver_shopping_dom" if best_url else ""
                    row["image_status"] = "ready" if best_url else "shopping_image_not_found"

                    print("[Sprint196-3AL Naver Product Image] RESULT", {
                        "product": product_name,
                        "ok": bool(best_url),
                        "candidate_count": len(candidates),
                    }, flush=True)

                except Exception as exc:
                    row["image_url"] = ""
                    row["image_source"] = ""
                    row["image_status"] = "shopping_image_error"
                    row["image_error"] = f"{type(exc).__name__}: {exc}"
                    print(
                        "[Sprint196-3AL Naver Product Image] ERROR",
                        product_name,
                        type(exc).__name__,
                        str(exc)[:200],
                        flush=True,
                    )

                enriched.append(row)

            # Preserve rows beyond max_items untouched.
            if len(source_items) > max_items:
                enriched.extend(source_items[max_items:])

            result["items"] = enriched
            result["product_images_enriched"] = True
            result["product_image_mode"] = "naver_shopping_dom"
            result["product_image_count"] = sum(
                1 for row in enriched if _valid_image(str(row.get("image_url") or ""))
            )
            return result

        finally:
            if context is not None:
                try:
                    context.close()
                except Exception:
                    pass
            if pw is not None:
                try:
                    pw.stop()
                except Exception:
                    pass

    @classmethod
    def enrich_product_images(cls, discovery_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        발견된 상품 후보 각각에 대표 이미지 URL을 추가합니다.
        기존 discovery 점수/순위는 변경하지 않습니다.
        """
        result = dict(discovery_result or {})
        rows = []
        for source_row in list(result.get("items") or []):
            row = dict(source_row or {})
            existing = (
                row.get("image_url")
                or row.get("thumbnail")
                or row.get("product_image")
                or ""
            )
            if existing:
                row["image_url"] = str(existing)
                row["image_source"] = str(row.get("image_source") or "discovery_existing")
            else:
                found = cls.lookup_naver_product_image(str(row.get("product") or ""))
                row["image_url"] = str(found.get("image_url") or "")
                row["image_source"] = str(found.get("source") or "")
                row["image_status"] = str(found.get("status") or "")
            rows.append(row)

        result["items"] = rows
        result["product_images_enriched"] = True
        result["product_image_count"] = sum(
            1 for row in rows if str(row.get("image_url") or "").startswith("http")
        )
        return result

    @classmethod
    def _profile_dir(cls, platform: str) -> Path:
        path = cls.PROFILE_ROOT / str(platform)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def _launch_context(cls, playwright, platform: str):
        kwargs = dict(
            user_data_dir=str(cls._profile_dir(platform)),
            headless=False,
            viewport={"width": 1365, "height": 900},
            locale="ko-KR",
            args=["--start-maximized"],
        )
        # Prefer installed Chrome so login/session behavior matches the user's browser.
        try:
            return playwright.chromium.launch_persistent_context(channel="chrome", **kwargs)
        except Exception:
            return playwright.chromium.launch_persistent_context(**kwargs)

    @classmethod
    def _open_persistent_login_browser(
        cls,
        *,
        platform: str,
        url: str,
    ) -> Dict[str, Any]:
        import subprocess
        import sys
        import textwrap

        platform = str(platform or "").strip().lower()
        profile_dir = cls._profile_dir(platform).resolve()

        # Sprint196-3V:
        # - about:blank 다중 탭/창 정리
        # - 로그인 브라우저는 한 번만 열고 타깃 페이지 1개만 유지
        # - 기존 쇼츠 persistent profile만 사용
        helper = textwrap.dedent(
            f"""
            from playwright.sync_api import sync_playwright
            from pathlib import Path
            import traceback
            import time

            profile = Path({str(profile_dir)!r})
            target = {url!r}
            p = None
            c = None

            try:
                p = sync_playwright().start()
                kw = dict(
                    user_data_dir=str(profile),
                    headless=False,
                    viewport={{"width": 1365, "height": 900}},
                    locale="ko-KR",
                    args=[
                        "--start-maximized",
                        "--no-first-run",
                        "--disable-session-crashed-bubble",
                    ],
                )

                try:
                    c = p.chromium.launch_persistent_context(channel="chrome", **kw)
                except Exception:
                    c = p.chromium.launch_persistent_context(**kw)

                pages = list(c.pages or [])

                # 기존 복원/빈 탭이 여러 개면 첫 탭 하나만 남깁니다.
                if pages:
                    page = pages[0]
                    for extra in pages[1:]:
                        try:
                            if str(extra.url or "").strip().lower() in ("", "about:blank"):
                                extra.close()
                        except Exception:
                            pass
                else:
                    page = c.new_page()

                # 한 개의 탭에서만 샤오홍슈로 이동합니다.
                nav_ok = False
                try:
                    page.goto(target, wait_until="commit", timeout=15000)
                    nav_ok = True
                except Exception as nav_exc:
                    print("LOGIN_BROWSER_NAV_WARN", type(nav_exc).__name__, str(nav_exc), flush=True)

                if not nav_ok or str(page.url or "").strip().lower() in ("", "about:blank"):
                    try:
                        page.evaluate("(u) => window.location.replace(u)", target)
                        time.sleep(1.0)
                    except Exception as eval_exc:
                        print("LOGIN_BROWSER_NAV_FALLBACK_WARN", type(eval_exc).__name__, str(eval_exc), flush=True)

                # 혹시 다시 생긴 빈 탭도 정리합니다.
                for extra in list(c.pages or []):
                    try:
                        if extra is page:
                            continue
                        if str(extra.url or "").strip().lower() in ("", "about:blank"):
                            extra.close()
                    except Exception:
                        pass

                try:
                    page.bring_to_front()
                except Exception:
                    pass

                print("LOGIN_BROWSER_READY", target, "=>", page.url, flush=True)
                print("로그인 완료 후 이 콘솔에서 Enter를 누르세요.", flush=True)

                input()

            except Exception as exc:
                print("LOGIN_BROWSER_FATAL", type(exc).__name__, str(exc), flush=True)
                traceback.print_exc()
                try:
                    input("오류 확인 후 Enter...")
                except Exception:
                    pass
            finally:
                if c is not None:
                    try:
                        c.close()
                    except Exception:
                        pass
                if p is not None:
                    try:
                        p.stop()
                    except Exception:
                        pass
            """
        )

        flags = 0
        if sys.platform.startswith("win"):
            flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)

        subprocess.Popen(
            [sys.executable, "-c", helper],
            creationflags=flags,
        )

        return {
            "ok": True,
            "status": "login_browser_opened",
            "platform": platform,
            "url": url,
            "profile": str(profile_dir),
        }

    @classmethod
    def open_tiktok_login_browser(
        cls,
        product_name: str = "",
    ) -> Dict[str, Any]:
        kw = cls._keywords(product_name)
        query = kw["en"] or kw["ko"] or "shopping"
        url = "https://www.tiktok.com/search?" + urllib.parse.urlencode({"q": query})
        return cls._open_persistent_login_browser(
            platform="tiktok",
            url=url,
        )

    @staticmethod
    def _resolve_chrome_executable() -> str:
        candidates = [
            shutil.which("chrome") or "",
            shutil.which("chrome.exe") or "",
            str(Path(os.environ.get("PROGRAMFILES", "")) / "Google/Chrome/Application/chrome.exe"),
            str(Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google/Chrome/Application/chrome.exe"),
            str(Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe"),
        ]
        for raw in candidates:
            value = str(raw or "").strip()
            if value and Path(value).is_file():
                return value
        return ""

    @classmethod
    def _open_xhs_chrome_direct(
        cls,
        url: str,
    ) -> Dict[str, Any]:
        """
        Sprint196-3C:
        샤오홍슈 로그인/인증 창은 Playwright page.goto() 대신
        Chrome 시작 명령 자체에 target URL을 전달합니다.
        이 방식은 브라우저가 about:blank에서 멈추는 문제를 피합니다.
        """
        chrome = cls._resolve_chrome_executable()
        profile_dir = cls._profile_dir("xiaohongshu")

        if not chrome:
            return {
                "ok": False,
                "status": "chrome_executable_not_found",
                "platform": "xiaohongshu",
                "url": url,
                "profile": str(profile_dir),
            }

        cmd = [
            chrome,
            f"--user-data-dir={str(profile_dir.resolve())}",
            "--new-window",
            url,
        ]
        try:
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=False,
            )
            return {
                "ok": True,
                "status": "xhs_chrome_direct_opened",
                "platform": "xiaohongshu",
                "url": url,
                "profile": str(profile_dir),
                "chrome": chrome,
            }
        except Exception as exc:
            return {
                "ok": False,
                "status": "xhs_chrome_direct_failed",
                "platform": "xiaohongshu",
                "url": url,
                "profile": str(profile_dir),
                "error": f"{type(exc).__name__}: {exc}",
            }

    @classmethod
    def _open_xhs_login_via_windows(
        cls,
        url: str,
    ) -> Dict[str, Any]:
        """
        Sprint196-3E
        최초 1회 샤오홍슈 로그인용.
        사용자가 PowerShell에서 실제 성공한 것과 동일하게
        Windows Chrome + 전용 user-data-dir + target URL 조합을 사용합니다.
        """
        import subprocess
        import os

        profile_dir = cls._profile_dir("xiaohongshu").resolve()
        candidates = [
            Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
            Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
        ]
        chrome = next((p for p in candidates if str(p) and p.is_file()), None)
        if chrome is None:
            return {
                "ok": False,
                "status": "chrome_executable_not_found",
                "platform": "xiaohongshu",
                "profile": str(profile_dir),
                "url": url,
            }

        # cmd /c start behaves closest to the tested PowerShell invocation
        # and detaches Chrome from Streamlit cleanly.
        cmd = [
            "cmd", "/c", "start", "",
            str(chrome),
            f"--user-data-dir={str(profile_dir)}",
            "--new-window",
            url,
        ]
        try:
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )
            return {
                "ok": True,
                "status": "xhs_first_login_browser_opened",
                "platform": "xiaohongshu",
                "profile": str(profile_dir),
                "url": url,
                "chrome": str(chrome),
            }
        except Exception as exc:
            return {
                "ok": False,
                "status": "xhs_first_login_browser_failed",
                "platform": "xiaohongshu",
                "profile": str(profile_dir),
                "url": url,
                "error": f"{type(exc).__name__}: {exc}",
            }

    @classmethod
    def open_xiaohongshu_login_browser(
        cls,
        product_name: str = "",
    ) -> Dict[str, Any]:
        kw = cls._keywords(product_name)
        query = kw["zh"] or kw["ko"] or "好物"
        url = "https://www.xiaohongshu.com/search_result?" + urllib.parse.urlencode({
            "keyword": query,
            "source": "web_search_result_notes",
        })
        return cls._open_xhs_login_via_windows(url)

    @classmethod
    def open_login_browser(
        cls,
        platform: str,
        product_name: str = "",
    ) -> Dict[str, Any]:
        # Backward-compatible router.
        platform = str(platform or "").strip().lower()
        if platform == "tiktok":
            return cls.open_tiktok_login_browser(product_name)
        if platform in {"xiaohongshu", "xhs"}:
            return cls.open_xiaohongshu_login_browser(product_name)
        return {
            "ok": False,
            "status": "unsupported_platform",
            "platform": platform,
        }

    @staticmethod
    def _dedupe(rows: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        out, seen = [], set()
        for row in rows:
            url = str(row.get("url") or "").split("?")[0].rstrip("/")
            if not url:
                continue
            key = url.lower()
            if key in seen:
                continue
            seen.add(key)
            row = dict(row)
            row["url"] = url
            out.append(row)
            if len(out) >= limit:
                break
        return out

    @classmethod
    def _collect_tiktok(cls, page, product_name: str, limit: int) -> List[Dict[str, Any]]:
        kw = cls._keywords(product_name)
        query = kw["en"] or kw["ko"]
        url = "https://www.tiktok.com/search?" + urllib.parse.urlencode({"q": query})
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3500)
        for _ in range(5):
            page.mouse.wheel(0, 1100)
            page.wait_for_timeout(650)

        rows = []
        anchors = page.locator("a[href*='/video/']")
        count = min(anchors.count(), max(limit * 5, 40))
        for i in range(count):
            try:
                a = anchors.nth(i)
                href = a.get_attribute("href") or ""
                if href.startswith("/"):
                    href = "https://www.tiktok.com" + href
                if "tiktok.com/" not in href or "/video/" not in href:
                    continue
                title = (a.get_attribute("aria-label") or a.inner_text(timeout=800) or "").strip()
                rows.append({
                    "platform": "TikTok",
                    "title": re.sub(r"\s+", " ", title)[:240],
                    "url": href,
                    "product": product_name,
                    "source": "direct_platform_search",
                })
            except Exception:
                continue
        return cls._dedupe(rows, limit)

    @classmethod
    def _xhs_diagnostics(cls, page, product_name: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "product": str(product_name or ""),
            "url": "",
            "title": "",
            "body_preview": "",
            "anchor_counts": {},
            "initial_state_exists": False,
            "initial_state_type": "",
            "search_keys": [],
            "feeds_kind": "",
            "feeds_count": 0,
            "feed_sample": [],
            "errors": [],
        }
        try:
            result["url"] = str(page.url or "")
        except Exception as exc:
            result["errors"].append(f"url:{type(exc).__name__}:{exc}")
        try:
            result["title"] = str(page.title() or "")
        except Exception as exc:
            result["errors"].append(f"title:{type(exc).__name__}:{exc}")
        try:
            body = page.locator("body").inner_text(timeout=2000)
            result["body_preview"] = re.sub(r"\s+", " ", str(body or ""))[:1000]
        except Exception as exc:
            result["errors"].append(f"body:{type(exc).__name__}:{exc}")

        selectors = {
            "cover": "a.cover",
            "explore": "a[href*='/explore/']",
            "discovery_item": "a[href*='/discovery/item/']",
            "note_item": "[class*='note-item']",
            "section": "section",
        }
        for key, selector in selectors.items():
            try:
                result["anchor_counts"][key] = int(page.locator(selector).count())
            except Exception as exc:
                result["anchor_counts"][key] = -1
                result["errors"].append(f"{key}:{type(exc).__name__}:{exc}")

        try:
            state_diag = page.evaluate(
                """
                () => {
                    const root = window.__INITIAL_STATE__;
                    const out = {
                        exists: !!root,
                        type: root === null ? "null" : typeof root,
                        rootKeys: [],
                        searchKeys: [],
                        feedsKind: "",
                        feedsCount: 0,
                        feedSample: []
                    };
                    if (!root) return out;
                    try { out.rootKeys = Object.keys(root).slice(0, 60); } catch (e) {}
                    let search = null;
                    try { search = root.search || null; } catch (e) {}
                    if (!search) return out;
                    try { out.searchKeys = Object.keys(search).slice(0, 60); } catch (e) {}
                    let raw = null;
                    try { raw = search.feeds; } catch (e) {}
                    if (Array.isArray(raw)) {
                        out.feedsKind = "array";
                        out.feedsCount = raw.length;
                        out.feedSample = raw.slice(0, 3);
                        return out;
                    }
                    if (raw && Array.isArray(raw._value)) {
                        out.feedsKind = "_value_array";
                        out.feedsCount = raw._value.length;
                        out.feedSample = raw._value.slice(0, 3);
                        return out;
                    }
                    if (raw && raw.value && Array.isArray(raw.value)) {
                        out.feedsKind = "value_array";
                        out.feedsCount = raw.value.length;
                        out.feedSample = raw.value.slice(0, 3);
                        return out;
                    }
                    if (raw) {
                        out.feedsKind = typeof raw;
                        try {
                            out.feedSample = [{keys:Object.keys(raw).slice(0,30)}];
                        } catch (e) {}
                    } else {
                        out.feedsKind = "missing";
                    }
                    return out;
                }
                """
            ) or {}
            result["initial_state_exists"] = bool(state_diag.get("exists"))
            result["initial_state_type"] = str(state_diag.get("type") or "")
            result["search_keys"] = list(state_diag.get("searchKeys") or [])
            result["feeds_kind"] = str(state_diag.get("feedsKind") or "")
            result["feeds_count"] = int(state_diag.get("feedsCount") or 0)
            result["feed_sample"] = list(state_diag.get("feedSample") or [])[:3]
            result["root_keys"] = list(state_diag.get("rootKeys") or [])
        except Exception as exc:
            result["errors"].append(f"initial_state:{type(exc).__name__}:{exc}")

        return result

    @classmethod
    def _collect_xhs(cls, page, product_name: str, limit: int) -> List[Dict[str, Any]]:
        """
        Sprint196-3K
        샤오홍슈 이동은 load 이벤트 대기 없이 JS location.assign()만 사용합니다.
        """
        kw = cls._keywords(product_name)
        query = kw["zh"] or kw["ko"]
        target = "https://www.xiaohongshu.com/search_result?" + urllib.parse.urlencode({
            "keyword": query,
            "source": "web_search_result_notes",
        })

        try:
            current = str(page.url or "")
        except Exception:
            current = ""

        if "xiaohongshu.com/search_result" not in current:
            try:
                page.evaluate("(target) => { window.location.assign(target); }", target)
            except Exception:
                try:
                    page.evaluate("(target) => { window.location.href = target; }", target)
                except Exception:
                    pass

        deadline = time.time() + 15.0
        while time.time() < deadline:
            try:
                current = str(page.url or "")
                if "xiaohongshu.com/" in current and current != "about:blank":
                    break
            except Exception:
                pass
            time.sleep(0.35)

        try:
            page.wait_for_timeout(2200)
        except Exception:
            pass

        for _ in range(5):
            try:
                page.mouse.wheel(0, 950)
                page.wait_for_timeout(500)
            except Exception:
                break

        rows: List[Dict[str, Any]] = []

        try:
            state_rows = page.evaluate(
                """
                () => {
                    const root = window.__INITIAL_STATE__ || {};
                    const search = root.search || {};
                    const raw = search.feeds;
                    let feeds = [];
                    if (Array.isArray(raw)) feeds = raw;
                    else if (raw && Array.isArray(raw._value)) feeds = raw._value;
                    else if (raw && raw.value && Array.isArray(raw.value)) feeds = raw.value;

                    const out = [];
                    for (const item of feeds || []) {
                        if (!item || !item.noteCard) continue;
                        const card = item.noteCard || {};
                        const id = String(item.id || card.noteId || card.id || "").trim();
                        if (!id) continue;
                        out.push({
                            id,
                            token: String(item.xsecToken || item.xsec_token || "").trim(),
                            type: String(card.type || "").toLowerCase(),
                            title: String(card.displayTitle || card.title || "").trim()
                        });
                    }
                    return out;
                }
                """
            ) or []

            ordered = [
                x for x in state_rows
                if str(x.get("type") or "").lower() == "video"
            ] + [
                x for x in state_rows
                if str(x.get("type") or "").lower() not in {"video", "normal"}
            ]

            for item in ordered:
                note_id = str(item.get("id") or "").strip()
                if not note_id:
                    continue
                token = str(item.get("token") or "").strip()
                href = f"https://www.xiaohongshu.com/explore/{note_id}"
                if token:
                    href += "?" + urllib.parse.urlencode({
                        "xsec_token": token,
                        "xsec_source": "pc_search",
                    })
                rows.append({
                    "platform": "샤오홍슈",
                    "title": str(item.get("title") or "")[:240],
                    "url": href,
                    "product": product_name,
                    "source": "xhs_no_wait_initial_state",
                    "note_type": str(item.get("type") or ""),
                })
        except Exception:
            pass

        if not rows:
            try:
                anchors = page.locator(
                    "a.cover, a[href*='/explore/'], a[href*='/discovery/item/']"
                )
                count = min(anchors.count(), max(int(limit) * 8, 80))
                for i in range(count):
                    try:
                        a = anchors.nth(i)
                        href = str(a.get_attribute("href") or "").strip()
                        if href.startswith("/"):
                            href = "https://www.xiaohongshu.com" + href
                        if "xiaohongshu.com/" not in href:
                            continue
                        title = str(
                            a.get_attribute("title")
                            or a.get_attribute("aria-label")
                            or a.inner_text(timeout=500)
                            or ""
                        ).strip()
                        rows.append({
                            "platform": "샤오홍슈",
                            "title": re.sub(r"\s+", " ", title)[:240],
                            "url": href,
                            "product": product_name,
                            "source": "xhs_no_wait_dom",
                        })
                    except Exception:
                        continue
            except Exception:
                pass

        return cls._dedupe(rows, int(limit))

    @staticmethod
    def _chrome_executable() -> str:
        candidates = [
            Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
            Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
        ]
        for candidate in candidates:
            if str(candidate) and candidate.is_file():
                return str(candidate)
        return ""

    @staticmethod
    def _port_open(port: int) -> bool:
        try:
            with socket.create_connection(("127.0.0.1", int(port)), timeout=0.4):
                return True
        except Exception:
            return False

    @classmethod
    def _launch_debug_chrome(
        cls,
        platform: str,
        url: str,
        port: int,
    ) -> Dict[str, Any]:
        chrome = cls._chrome_executable()
        profile = cls._profile_dir(platform).resolve()

        if not chrome:
            return {
                "ok": False,
                "status": "chrome_not_found",
                "platform": platform,
                "profile": str(profile),
                "url": url,
                "port": int(port),
            }

        if cls._port_open(port):
            return {
                "ok": True,
                "status": "already_running",
                "platform": platform,
                "profile": str(profile),
                "url": url,
                "port": int(port),
            }

        cmd = [
            chrome,
            f"--user-data-dir={str(profile)}",
            f"--remote-debugging-port={int(port)}",
            "--remote-allow-origins=*",
            "--new-window",
            url,
        ]

        try:
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )
        except Exception as exc:
            return {
                "ok": False,
                "status": "launch_failed",
                "platform": platform,
                "profile": str(profile),
                "url": url,
                "port": int(port),
                "error": f"{type(exc).__name__}: {exc}",
            }

        deadline = time.time() + 15.0
        while time.time() < deadline:
            if cls._port_open(port):
                return {
                    "ok": True,
                    "status": "started",
                    "platform": platform,
                    "profile": str(profile),
                    "url": url,
                    "port": int(port),
                }
            time.sleep(0.35)

        return {
            "ok": False,
            "status": "debug_port_not_ready",
            "platform": platform,
            "profile": str(profile),
            "url": url,
            "port": int(port),
        }

    @classmethod
    def _connect_platform_page(
        cls,
        playwright,
        platform: str,
        product_name: str,
    ):
        kw = cls._keywords(product_name)

        if platform == "tiktok":
            query = kw["en"] or kw["ko"]
            target = "https://www.tiktok.com/search?" + urllib.parse.urlencode({"q": query})
            port = 9222

            launch = cls._launch_debug_chrome(platform, target, port)
            if not launch.get("ok"):
                raise RuntimeError(f"{platform}_debug_chrome_failed:{launch}")

            browser = playwright.chromium.connect_over_cdp(
                f"http://127.0.0.1:{int(port)}",
                timeout=15000,
            )

            contexts = list(browser.contexts or [])
            if not contexts:
                raise RuntimeError(f"{platform}_cdp_no_context")

            context = contexts[0]
            pages = list(context.pages or [])
            page = pages[-1] if pages else context.new_page()
        else:
            # Sprint196-3T: Xiaohongshu uses the Shorts app's own persistent profile.
            # No 9222/9223/CDP path is used for XHS.
            query = kw["zh"] or kw["ko"]
            target = "https://www.xiaohongshu.com/search_result?" + urllib.parse.urlencode({
                "keyword": query,
                "source": "web_search_result_notes",
            })
            kwargs = dict(
                user_data_dir=str(cls._profile_dir("xiaohongshu")),
                headless=False,
                viewport={"width": 1365, "height": 900},
                locale="ko-KR",
                args=["--start-maximized"],
                timeout=10000,
            )
            try:
                context = playwright.chromium.launch_persistent_context(channel="chrome", **kwargs)
            except Exception:
                context = playwright.chromium.launch_persistent_context(**kwargs)
            browser = context
            pages = list(context.pages or [])
            page = pages[-1] if pages else context.new_page()
            launch = {
                "ok": True,
                "status": "shorts_persistent_profile",
                "platform": "xiaohongshu",
                "profile": str(cls._profile_dir("xiaohongshu").resolve()),
                "url": target,
            }

        deadline = time.time() + 15.0
        while time.time() < deadline:
            try:
                current = str(page.url or "")
                if current and current != "about:blank":
                    break
            except Exception:
                pass
            time.sleep(0.35)

        return browser, context, page, launch

    @classmethod
    def open_xhs_live_session(
        cls,
        product_name: str = "",
    ) -> Dict[str, Any]:
        """
        Sprint196-3X
        쇼츠 전용 샤오홍슈 프로필을 실제 설치된 Chrome으로 직접 엽니다.
        Playwright launch_persistent_context를 로그인 단계에서 사용하지 않습니다.
        9222/9223/CDP도 사용하지 않습니다.
        """
        import subprocess

        kw = cls._keywords(product_name)
        query = kw["zh"] or kw["ko"] or "好物"
        target = "https://www.xiaohongshu.com/search_result?" + urllib.parse.urlencode({
            "keyword": query,
            "source": "web_search_result_notes",
        })

        chrome = cls._chrome_executable()
        profile = cls._profile_dir("xiaohongshu").resolve()

        if not chrome:
            return {
                "ok": False,
                "status": "chrome_not_found",
                "profile": str(profile),
                "url": target,
                "message": "설치된 Chrome 실행 파일을 찾지 못했습니다.",
            }

        cmd = [
            chrome,
            f"--user-data-dir={str(profile)}",
            "--start-maximized",
            "--no-first-run",
            "--disable-session-crashed-bubble",
            "--new-window",
            target,
        ]

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )
            result = {
                "ok": True,
                "status": "chrome_launched",
                "mode": "shorts_real_chrome_profile",
                "profile": str(profile),
                "url": target,
                "pid": int(proc.pid),
                "message": (
                    "쇼츠 전용 샤오홍슈 Chrome을 열었습니다. "
                    "로그인을 완료한 뒤 이 Chrome 창을 닫고 수집 버튼을 누르세요."
                ),
            }
            print("[Sprint196-3X XHS Login] OPEN", result, flush=True)
            return result
        except Exception as exc:
            result = {
                "ok": False,
                "status": "chrome_launch_failed",
                "mode": "shorts_real_chrome_profile",
                "profile": str(profile),
                "url": target,
                "error": f"{type(exc).__name__}: {exc}",
            }
            print("[Sprint196-3X XHS Login] ERROR", result, flush=True)
            return result

    @classmethod
    def collect_xhs_live_session(
        cls,
        product_name: str,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Sprint196-3T
        쇼츠 전용 browser_profiles/shopping_source_search/xiaohongshu 프로필을
        Playwright persistent context로 직접 열어 수집합니다.
        9222/9223/CDP 연결은 사용하지 않습니다.
        """
        print("[Sprint196-3Y XHS Collect] ENTER", {"product": product_name}, flush=True)

        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:
            return {
                "ok": False,
                "status": "playwright_missing",
                "items": [],
                "count": 0,
                "error": f"{type(exc).__name__}: {exc}",
                "summary": "Playwright를 불러오지 못했습니다.",
            }

        profile = cls._profile_dir("xiaohongshu").resolve()
        kw = cls._keywords(product_name)
        query = kw["zh"] or kw["ko"]
        target = "https://www.xiaohongshu.com/search_result?" + urllib.parse.urlencode({
            "keyword": query,
            "source": "web_search_result_notes",
        })

        pw = None
        context = None
        try:
            pw = sync_playwright().start()
            kwargs = dict(
                user_data_dir=str(profile),
                headless=False,
                viewport={"width": 1365, "height": 900},
                locale="ko-KR",
                args=[
                    "--start-maximized",
                    "--no-first-run",
                    "--disable-session-crashed-bubble",
                ],
                timeout=10000,
            )
            context = pw.chromium.launch_persistent_context(
                channel="chrome",
                **kwargs,
            )

            try:
                context.set_default_timeout(2500)
                context.set_default_navigation_timeout(6000)
            except Exception:
                pass

            # Sprint196-3Y:
            # persistent context가 자동 생성한 about:blank를 수집 탭으로 재사용하지 않습니다.
            # 새 탭 1개를 만든 뒤 그 탭에서만 샤오홍슈 검색으로 이동합니다.
            existing_pages = list(context.pages or [])
            page = context.new_page()

            print("[Sprint196-3Y XHS Collect] PROFILE_OPEN", {
                "profile": str(profile),
                "existing_pages": len(existing_pages),
            }, flush=True)

            nav_ok = False
            try:
                page.goto(target, wait_until="commit", timeout=6000)
                nav_ok = True
                print("[Sprint196-3Y XHS Collect] NAV_COMMIT", str(page.url or "")[:180], flush=True)
            except Exception as exc:
                print("[Sprint196-3Y XHS Collect] NAV_WARN", type(exc).__name__, str(exc)[:220], flush=True)

            if (not nav_ok) or str(page.url or "").strip().lower() in ("", "about:blank"):
                try:
                    page.evaluate("(u) => window.location.replace(u)", target)
                    print("[Sprint196-3Y XHS Collect] NAV_FALLBACK", flush=True)
                except Exception as exc:
                    print("[Sprint196-3Y XHS Collect] NAV_FALLBACK_WARN", type(exc).__name__, str(exc)[:220], flush=True)

            try:
                page.wait_for_timeout(1800)
            except Exception:
                pass

            # 이동이 끝난 뒤 남아 있는 about:blank 탭만 닫습니다.
            for extra in list(context.pages or []):
                if extra is page:
                    continue
                try:
                    if str(extra.url or "").strip().lower() in ("", "about:blank"):
                        extra.close()
                except Exception:
                    pass

            try:
                page.bring_to_front()
            except Exception:
                pass

            rows: List[Dict[str, Any]] = []

            # INITIAL_STATE 우선 수집
            try:
                state_rows = page.evaluate(
                    """
                    () => {
                        const root = window.__INITIAL_STATE__ || {};
                        const search = root.search || {};
                        const raw = search.feeds;
                        let feeds = [];
                        if (Array.isArray(raw)) feeds = raw;
                        else if (raw && Array.isArray(raw._value)) feeds = raw._value;
                        else if (raw && raw.value && Array.isArray(raw.value)) feeds = raw.value;
                        const out = [];
                        for (const item of feeds || []) {
                            if (!item || !item.noteCard) continue;
                            const card = item.noteCard || {};
                            const id = String(item.id || card.noteId || card.id || "").trim();
                            if (!id) continue;
                            out.push({
                                id,
                                token: String(item.xsecToken || item.xsec_token || "").trim(),
                                type: String(card.type || "").toLowerCase(),
                                title: String(card.displayTitle || card.title || "").trim()
                            });
                        }
                        return out;
                    }
                    """
                ) or []

                for item in state_rows:
                    note_id = str(item.get("id") or "").strip()
                    if not note_id:
                        continue
                    token = str(item.get("token") or "").strip()
                    href = f"https://www.xiaohongshu.com/explore/{note_id}"
                    if token:
                        href += "?" + urllib.parse.urlencode({
                            "xsec_token": token,
                            "xsec_source": "pc_search",
                        })
                    rows.append({
                        "platform": "샤오홍슈",
                        "title": str(item.get("title") or "")[:240],
                        "url": href,
                        "product": product_name,
                        "source": "xhs_profile_state",
                        "note_type": str(item.get("type") or ""),
                    })
            except Exception as exc:
                print("[Sprint196-3Y XHS Collect] STATE_WARN", type(exc).__name__, str(exc)[:180], flush=True)

            # DOM fallback
            if not rows:
                try:
                    dom_rows = page.evaluate(
                        """
                        () => Array.from(document.querySelectorAll(
                            "a.cover, a[href*='/explore/'], a[href*='/discovery/item/']"
                        )).slice(0, 40).map(a => ({
                            href: String(a.href || a.getAttribute('href') || ''),
                            title: String(
                                a.getAttribute('title') ||
                                a.getAttribute('aria-label') ||
                                a.textContent || ''
                            ).replace(/\\s+/g, ' ').trim()
                        }))
                        """
                    ) or []
                    for item in dom_rows:
                        href = str(item.get("href") or "").strip()
                        if href.startswith("/"):
                            href = "https://www.xiaohongshu.com" + href
                        if "xiaohongshu.com/" not in href:
                            continue
                        rows.append({
                            "platform": "샤오홍슈",
                            "title": str(item.get("title") or "")[:240],
                            "url": href,
                            "product": product_name,
                            "source": "xhs_profile_dom",
                            "note_type": "",
                        })
                except Exception as exc:
                    print("[Sprint196-3Y XHS Collect] DOM_WARN", type(exc).__name__, str(exc)[:180], flush=True)

            rows = cls._dedupe(rows, int(limit))

            try:
                current_url = str(page.url or "")
            except Exception:
                current_url = ""
            try:
                title = str(page.title() or "")
            except Exception:
                title = ""

            print("[Sprint196-3Y XHS Collect] RETURN", {"count": len(rows), "url": current_url[:160]}, flush=True)

            return {
                "ok": bool(rows),
                "status": "ready" if rows else "no_results",
                "items": rows,
                "count": len(rows),
                "current_url": current_url,
                "title": title,
                "diagnostics": {
                    "mode": "shorts_persistent_profile",
                    "profile": str(profile),
                    "remote_debugging": False,
                },
                "summary": (
                    f"쇼츠 전용 샤오홍슈 프로필에서 {len(rows)}개 후보를 수집했습니다."
                    if rows else
                    "쇼츠 전용 샤오홍슈 프로필을 열었지만 검색 후보를 찾지 못했습니다."
                ),
            }

        except Exception as exc:
            msg = f"{type(exc).__name__}: {exc}"
            print("[Sprint196-3Y XHS Collect] ERROR", msg[:400], flush=True)
            if "user data directory is already in use" in str(exc).lower() or "processsingleton" in str(exc).lower():
                status = "xhs_profile_in_use"
                summary = "샤오홍슈 로그인 브라우저가 아직 열려 있습니다. 로그인 창과 함께 열린 콘솔에서 Enter를 눌러 닫은 뒤 다시 수집하세요."
            else:
                status = "xhs_profile_error"
                summary = "쇼츠 전용 샤오홍슈 프로필로 실제 Chrome을 자동 제어하지 못했습니다."
            return {
                "ok": False,
                "status": status,
                "items": [],
                "count": 0,
                "error": msg,
                "diagnostics": {
                    "mode": "shorts_persistent_profile",
                    "profile": str(profile),
                    "remote_debugging": False,
                },
                "summary": summary,
            }
        finally:
            if context is not None:
                try:
                    context.close()
                except Exception:
                    pass
            if pw is not None:
                try:
                    pw.stop()
                except Exception:
                    pass

    @classmethod
    def _live_session_marker(cls) -> Path:
        path = Path("exports") / "shopping_source_session"
        path.mkdir(parents=True, exist_ok=True)
        return path / "live_session.json"

    @classmethod
    def _write_live_session_marker(cls, payload: Dict[str, Any]) -> None:
        try:
            cls._live_session_marker().write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )
        except Exception:
            pass

    @classmethod
    def open_tiktok_xhs_login_browser(
        cls,
        product_name: str = "",
    ) -> Dict[str, Any]:
        """
        Sprint196-3AG
        샤오홍슈는 보류하고 TikTok 전용 살아있는 세션만 엽니다.
        기존 메서드명은 UI/호출 호환을 위해 유지합니다.
        """
        import subprocess
        import sys
        import textwrap

        # Sprint196-3AX:
        # TikTok 상품 검색은 로그인된 사용자 계정 프로필을 사용하지 않습니다.
        # 개인 피드/내 계정 영상이 검색 후보로 섞이지 않도록 전용 공개 검색 프로필을 사용합니다.
        profile = (Path("browser_profile") / "tiktok_public_search").resolve()
        profile.mkdir(parents=True, exist_ok=True)
        kw = cls._keywords(product_name)
        tiktok_q = kw["en"] or kw["ko"] or product_name
        tiktok_url = "https://www.tiktok.com/search?" + urllib.parse.urlencode({"q": tiktok_q})

        marker = cls._live_session_marker().resolve()
        try:
            marker.unlink(missing_ok=True)
        except Exception:
            pass

        helper = textwrap.dedent(
            f"""
            from playwright.sync_api import sync_playwright
            from pathlib import Path
            import json, time, traceback
            from urllib.parse import quote

            profile = Path({str(profile)!r})
            marker = Path({str(marker)!r})
            command_file = marker.parent / "command.json"
            result_file = marker.parent / "result.json"
            tiktok_url = {tiktok_url!r}

            p = None
            context = None
            try:
                p = sync_playwright().start()
                context = p.chromium.launch_persistent_context(
                    user_data_dir=str(profile),
                    channel="chrome",
                    headless=False,
                    viewport={{"width": 1365, "height": 900}},
                    locale="ko-KR",
                    args=[
                        "--start-maximized",
                        "--no-first-run",
                        "--no-default-browser-check",
                        "--disable-session-crashed-bubble",
                    ],
                    timeout=15000,
                )

                pages = list(context.pages or [])
                first = None
                for pg in pages:
                    try:
                        if "tiktok.com" in str(pg.url or "").lower():
                            first = pg
                            break
                    except Exception:
                        pass
                if first is None:
                    first = pages[0] if pages else context.new_page()

                # TikTok 1개 탭만 유지합니다. 샤오홍슈 및 복원 탭은 이번 모드에서 사용하지 않습니다.
                for pg in list(context.pages or []):
                    if pg is first:
                        continue
                    try:
                        pg.close()
                    except Exception:
                        pass

                try:
                    first.goto(tiktok_url, wait_until="commit", timeout=12000)
                except Exception:
                    try:
                        first.evaluate("(u) => window.location.replace(u)", tiktok_url)
                    except Exception:
                        pass
                try:
                    first.bring_to_front()
                except Exception:
                    pass

                import os
                payload = {{
                    "ok": True,
                    "status": "tiktok_live_browser_ready",
                    "profile": str(profile),
                    "tiktok_url": str(first.url or tiktok_url),
                    "pid": os.getpid(),
                    "started_at": time.time(),
                    "heartbeat": time.time(),
                }}
                marker.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                print("[Sprint196-3AI Helper] READY", payload, flush=True)
                print("TikTok 창을 닫지 말고 쇼츠 화면에서 후보 수집 버튼을 누르세요.", flush=True)

                last_command_id = None
                while True:
                    try:
                        alive_pages = [pg for pg in list(context.pages or []) if not pg.is_closed()]
                    except Exception:
                        alive_pages = []
                    if not alive_pages:
                        break

                    # 살아있는 helper인지 메인 Streamlit이 판별할 수 있도록 heartbeat 갱신
                    try:
                        marker_state = json.loads(marker.read_text(encoding="utf-8")) if marker.is_file() else {{}}
                        marker_state.update({{
                            "ok": True,
                            "status": "tiktok_live_browser_ready",
                            "pid": os.getpid(),
                            "heartbeat": time.time(),
                            "tiktok_url": str(first.url or tiktok_url),
                        }})
                        marker.write_text(
                            json.dumps(marker_state, ensure_ascii=False, indent=2),
                            encoding="utf-8",
                        )
                    except Exception:
                        pass

                    try:
                        if command_file.is_file():
                            cmd = json.loads(command_file.read_text(encoding="utf-8"))
                            command_id = str(cmd.get("id") or "")
                            if command_id and command_id != last_command_id:
                                last_command_id = command_id
                                product = str(cmd.get("product") or "")
                                tq = str(cmd.get("tiktok_query") or product)
                                limit = int(cmd.get("limit") or 10)
                                tt = next((pg for pg in list(context.pages or []) if "tiktok.com" in str(pg.url or "").lower()), first)
                                tt_target = "https://www.tiktok.com/search?q=" + quote(tq)

                                try:
                                    tt.goto(tt_target, wait_until="commit", timeout=12000)
                                except Exception:
                                    try:
                                        tt.evaluate("(u) => window.location.replace(u)", tt_target)
                                    except Exception:
                                        pass
                                try:
                                    tt.wait_for_timeout(2500)
                                except Exception:
                                    pass
                                try:
                                    for _ in range(4):
                                        tt.mouse.wheel(0, 1000)
                                        tt.wait_for_timeout(450)
                                except Exception:
                                    pass

                                out = []
                                try:
                                    anchors = tt.locator("a[href*='/video/']")
                                    n = min(anchors.count(), max(limit * 5, 40))
                                    seen = set()
                                    for i in range(n):
                                        try:
                                            a = anchors.nth(i)
                                            href = str(a.get_attribute("href") or "").strip()
                                            if href.startswith("/"):
                                                href = "https://www.tiktok.com" + href
                                            clean = href.split("?")[0].rstrip("/")
                                            if "/video/" not in clean or clean in seen:
                                                continue
                                            seen.add(clean)
                                            title = str(
                                                a.get_attribute("aria-label")
                                                or a.get_attribute("title")
                                                or a.inner_text(timeout=350)
                                                or ""
                                            ).strip()
                                            out.append({{
                                                "platform": "TikTok",
                                                "title": title[:240],
                                                "url": clean,
                                                "product": product,
                                                "source": "tiktok_live_saved_session",
                                            }})
                                            if len(out) >= limit:
                                                break
                                        except Exception:
                                            pass
                                except Exception:
                                    pass

                                payload = {{
                                    "ok": bool(out),
                                    "id": command_id,
                                    "product": product,
                                    "items": out,
                                    "counts": {{"tiktok": len(out), "xiaohongshu": 0}},
                                    "summary": f"{{product}} 관련 TikTok 영상 후보 {{len(out)}}개를 수집했습니다." if out else f"{{product}} 관련 TikTok 영상 후보를 찾지 못했습니다.",
                                }}
                                result_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                                print("[Sprint196-3AI Helper] COLLECT READY", payload["counts"], flush=True)
                    except Exception as cmd_exc:
                        print("[Sprint196-3AI Helper] COMMAND ERROR", type(cmd_exc).__name__, str(cmd_exc), flush=True)
                    time.sleep(0.7)

            except Exception as exc:
                payload = {{"ok": False, "status": "tiktok_live_browser_error", "error": f"{{type(exc).__name__}}: {{exc}}"}}
                try:
                    marker.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                except Exception:
                    pass
                print("[Sprint196-3AI Helper] ERROR", payload, flush=True)
                traceback.print_exc()
                try:
                    input("오류 확인 후 Enter...")
                except Exception:
                    pass
            finally:
                try:
                    marker.unlink(missing_ok=True)
                except Exception:
                    pass
                if context is not None:
                    try:
                        context.close()
                    except Exception:
                        pass
                if p is not None:
                    try:
                        p.stop()
                    except Exception:
                        pass
            """
        )

        flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0) if sys.platform.startswith("win") else 0
        proc = subprocess.Popen([sys.executable, "-c", helper], creationflags=flags)
        result = {
            "ok": True,
            "status": "tiktok_live_browser_starting",
            "profile": str(profile),
            "marker": str(marker),
            "pid": int(proc.pid),
            "message": "TikTok을 열고 있습니다. 로그인 상태를 확인한 뒤 창을 닫지 말고 수집 버튼을 누르세요.",
        }
        print("[Sprint196-3AI Login] START", result, flush=True)
        return result


    @classmethod
    def _collect_from_page(
        cls,
        page,
        *,
        platform: str,
        product_name: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        found: List[Dict[str, Any]] = []

        if platform == "tiktok":
            try:
                for _ in range(4):
                    page.mouse.wheel(0, 1000)
                    page.wait_for_timeout(450)
            except Exception:
                pass

            try:
                anchors = page.locator("a[href*='/video/']")
                count = min(anchors.count(), max(int(limit) * 5, 40))
                for i in range(count):
                    try:
                        a = anchors.nth(i)
                        href = str(a.get_attribute("href") or "").strip()
                        if href.startswith("/"):
                            href = "https://www.tiktok.com" + href
                        if "tiktok.com/" not in href or "/video/" not in href:
                            continue
                        title = str(
                            a.get_attribute("aria-label")
                            or a.get_attribute("title")
                            or a.inner_text(timeout=350)
                            or ""
                        ).strip()
                        found.append({
                            "platform": "TikTok",
                            "title": re.sub(r"\s+", " ", title)[:240],
                            "url": href,
                            "product": product_name,
                            "source": "saved_login_profile_dom",
                        })
                    except Exception:
                        continue
            except Exception:
                pass

        else:
            try:
                for _ in range(5):
                    page.mouse.wheel(0, 1000)
                    page.wait_for_timeout(450)
            except Exception:
                pass

            try:
                state_rows = page.evaluate(
                    """
                    () => {
                        const root = window.__INITIAL_STATE__ || {};
                        const search = root.search || {};
                        const raw = search.feeds;
                        let feeds = [];
                        if (Array.isArray(raw)) feeds = raw;
                        else if (raw && Array.isArray(raw._value)) feeds = raw._value;
                        else if (raw && raw.value && Array.isArray(raw.value)) feeds = raw.value;
                        const out = [];
                        for (const item of feeds || []) {
                            if (!item || !item.noteCard) continue;
                            const card = item.noteCard || {};
                            const id = String(item.id || card.noteId || card.id || "").trim();
                            if (!id) continue;
                            out.push({
                                id,
                                token: String(item.xsecToken || item.xsec_token || "").trim(),
                                type: String(card.type || "").toLowerCase(),
                                title: String(card.displayTitle || card.title || "").trim()
                            });
                        }
                        return out;
                    }
                    """
                ) or []
                for item in state_rows:
                    note_id = str(item.get("id") or "").strip()
                    if not note_id:
                        continue
                    token = str(item.get("token") or "").strip()
                    href = f"https://www.xiaohongshu.com/explore/{note_id}"
                    if token:
                        href += "?" + urllib.parse.urlencode({
                            "xsec_token": token,
                            "xsec_source": "pc_search",
                        })
                    found.append({
                        "platform": "샤오홍슈",
                        "title": str(item.get("title") or "")[:240],
                        "url": href,
                        "product": product_name,
                        "source": "saved_login_profile_state",
                        "note_type": str(item.get("type") or ""),
                    })
            except Exception:
                pass

            if not found:
                try:
                    anchors = page.locator(
                        "a.cover, a[href*='/explore/'], a[href*='/discovery/item/']"
                    )
                    count = min(anchors.count(), max(int(limit) * 5, 40))
                    for i in range(count):
                        try:
                            a = anchors.nth(i)
                            href = str(a.get_attribute("href") or "").strip()
                            if href.startswith("/"):
                                href = "https://www.xiaohongshu.com" + href
                            if "xiaohongshu.com/" not in href:
                                continue
                            title = str(
                                a.get_attribute("title")
                                or a.get_attribute("aria-label")
                                or a.inner_text(timeout=350)
                                or ""
                            ).strip()
                            found.append({
                                "platform": "샤오홍슈",
                                "title": re.sub(r"\s+", " ", title)[:240],
                                "url": href,
                                "product": product_name,
                                "source": "saved_login_profile_dom",
                            })
                        except Exception:
                            continue
                except Exception:
                    pass

        return cls._dedupe(found, int(limit))

    @staticmethod
    def _image_ahash_from_bytes(data: bytes, size: int = 16) -> str:
        """
        Lightweight perceptual average hash.
        Pillow가 설치되어 있을 때만 사용합니다.
        """
        try:
            from PIL import Image
            import io

            with Image.open(io.BytesIO(data)) as im:
                im = im.convert("L").resize((size, size))
                pixels = list(im.getdata())
            avg = sum(pixels) / max(1, len(pixels))
            return "".join("1" if px >= avg else "0" for px in pixels)
        except Exception:
            return ""

    @staticmethod
    def _hash_similarity(hash_a: str, hash_b: str) -> float:
        if not hash_a or not hash_b or len(hash_a) != len(hash_b):
            return 0.0
        same = sum(1 for a, b in zip(hash_a, hash_b) if a == b)
        return round((same / len(hash_a)) * 100.0, 1)

    @classmethod
    def _download_image_bytes(cls, url: str, timeout: int = 8) -> bytes:
        url = str(url or "").strip()
        if not url.startswith("http"):
            return b""
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/151.0.0.0 Safari/537.36"
                    ),
                    "Referer": "https://search.shopping.naver.com/",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read()
        except Exception:
            return b""

    @classmethod
    def _selected_product_reference(cls, product_name: str = "") -> Dict[str, Any]:
        path = Path("exports") / "shopping_discovery" / "selected_product_reference.json"
        try:
            if not path.is_file():
                return {}
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return {}
            if product_name and str(data.get("product") or "") != str(product_name):
                return {}
            return data
        except Exception:
            return {}

    @staticmethod
    def _trim_reference_product_area(data: bytes) -> bytes:
        """
        NAVER 대표이미지가 흰 배경 상품컷인 경우,
        거의 흰 배경을 제거해 실제 상품 영역 위주로 잘라냅니다.
        실패하면 원본 바이트를 그대로 반환합니다.
        """
        try:
            from PIL import Image
            import io

            with Image.open(io.BytesIO(data)) as src:
                im = src.convert("RGB")

            # 너무 큰 이미지는 비교용으로 축소.
            im.thumbnail((900, 900))

            px = im.load()
            w, h = im.size
            xs, ys = [], []

            # near-white 배경과 아주 밝은 회색 배경을 제외.
            for y in range(h):
                for x in range(w):
                    r, g, b = px[x, y]
                    mx, mn = max(r, g, b), min(r, g, b)
                    near_white = (r >= 238 and g >= 238 and b >= 238)
                    pale_neutral = (mx >= 232 and (mx - mn) <= 10)
                    if not (near_white or pale_neutral):
                        xs.append(x)
                        ys.append(y)

            if not xs or not ys:
                return data

            left, top, right, bottom = min(xs), min(ys), max(xs), max(ys)

            # 너무 작은 잡티만 잡혔으면 crop하지 않음.
            box_w = right - left + 1
            box_h = bottom - top + 1
            if box_w < max(20, int(w * 0.12)) or box_h < max(20, int(h * 0.12)):
                return data

            pad_x = max(6, int(box_w * 0.08))
            pad_y = max(6, int(box_h * 0.08))
            left = max(0, left - pad_x)
            top = max(0, top - pad_y)
            right = min(w, right + pad_x + 1)
            bottom = min(h, bottom + pad_y + 1)

            crop = im.crop((left, top, right, bottom))
            buf = io.BytesIO()
            crop.save(buf, format="PNG")
            return buf.getvalue()
        except Exception:
            return data

    @staticmethod
    def _dhash_from_bytes(data: bytes, size: int = 16) -> str:
        """Difference hash: 배경 밝기 변화보다 형태/윤곽 변화에 조금 더 민감합니다."""
        try:
            from PIL import Image
            import io

            with Image.open(io.BytesIO(data)) as im:
                im = im.convert("L").resize((size + 1, size))
                vals = list(im.getdata())

            bits = []
            row_w = size + 1
            for y in range(size):
                row = vals[y * row_w:(y + 1) * row_w]
                for x in range(size):
                    bits.append("1" if row[x] > row[x + 1] else "0")
            return "".join(bits)
        except Exception:
            return ""

    @staticmethod
    def _color_histogram_from_bytes(data: bytes, bins: int = 8) -> list[float]:
        """저해상도 RGB 색 분포. 배경 영향 완화를 위해 중앙 crop 후 계산."""
        try:
            from PIL import Image
            import io

            with Image.open(io.BytesIO(data)) as im:
                im = im.convert("RGB")
                w, h = im.size
                if w > 30 and h > 30:
                    mx = int(w * 0.08)
                    my = int(h * 0.08)
                    im = im.crop((mx, my, w - mx, h - my))
                im.thumbnail((160, 160))

                hist = [0.0] * (bins * 3)
                count = 0
                for r, g, b in im.getdata():
                    hist[min(bins - 1, r * bins // 256)] += 1
                    hist[bins + min(bins - 1, g * bins // 256)] += 1
                    hist[bins * 2 + min(bins - 1, b * bins // 256)] += 1
                    count += 1

            denom = max(1, count)
            return [v / denom for v in hist]
        except Exception:
            return []

    @staticmethod
    def _hist_similarity(hist_a: list[float], hist_b: list[float]) -> float:
        if not hist_a or not hist_b or len(hist_a) != len(hist_b):
            return 0.0
        # histogram intersection. 채널당 합이 1이므로 전체합 최대 3.
        intersection = sum(min(a, b) for a, b in zip(hist_a, hist_b))
        return round(max(0.0, min(100.0, intersection / 3.0 * 100.0)), 1)

    @staticmethod
    def _video_frame_crops(frame_bytes: bytes) -> list[tuple[str, bytes]]:
        """
        영상 전체 프레임 하나만 비교하지 않고,
        전체/중앙/좌우/상하/3x3 중앙 주변 crop을 함께 만듭니다.
        손·사람·배경이 넓게 잡혀도 제품이 들어 있는 crop을 찾기 위한 장치입니다.
        """
        try:
            from PIL import Image
            import io

            with Image.open(io.BytesIO(frame_bytes)) as src:
                im = src.convert("RGB")

            w, h = im.size
            if w < 80 or h < 80:
                return [("full", frame_bytes)]

            crops = []

            def add(name, box):
                l, t, r, b = box
                l = max(0, min(w - 1, int(l)))
                t = max(0, min(h - 1, int(t)))
                r = max(l + 1, min(w, int(r)))
                b = max(t + 1, min(h, int(b)))
                crop = im.crop((l, t, r, b))
                if crop.size[0] < 40 or crop.size[1] < 40:
                    return
                buf = io.BytesIO()
                crop.save(buf, format="JPEG", quality=88)
                crops.append((name, buf.getvalue()))

            add("full", (0, 0, w, h))
            add("center80", (w*0.10, h*0.10, w*0.90, h*0.90))
            add("center60", (w*0.20, h*0.20, w*0.80, h*0.80))
            add("left70", (0, h*0.12, w*0.70, h*0.88))
            add("right70", (w*0.30, h*0.12, w, h*0.88))
            add("top70", (w*0.12, 0, w*0.88, h*0.70))
            add("bottom70", (w*0.12, h*0.30, w*0.88, h))

            # 3x3 중 중앙 주변 5개.
            cw, ch = w * 0.55, h * 0.55
            centers = [
                ("grid_c", 0.50, 0.50),
                ("grid_l", 0.32, 0.50),
                ("grid_r", 0.68, 0.50),
                ("grid_t", 0.50, 0.34),
                ("grid_b", 0.50, 0.66),
            ]
            for name, cx, cy in centers:
                add(name, (
                    w*cx - cw/2, h*cy - ch/2,
                    w*cx + cw/2, h*cy + ch/2,
                ))

            return crops or [("full", frame_bytes)]
        except Exception:
            return [("full", frame_bytes)]

    @classmethod
    def _visual_similarity_product_focused(
        cls,
        reference_bytes: bytes,
        frame_bytes: bytes,
    ) -> Dict[str, Any]:
        """
        상품영역 중심 1차 유사도.
        - NAVER reference는 흰 배경 trim
        - TikTok frame은 여러 crop을 비교
        - dHash(형태) + aHash(전체 톤/형태) + 색 histogram을 조합
        """
        ref = cls._trim_reference_product_area(reference_bytes)
        ref_d = cls._dhash_from_bytes(ref)
        ref_a = cls._image_ahash_from_bytes(ref)
        ref_h = cls._color_histogram_from_bytes(ref)

        best = {
            "score": 0.0,
            "crop": "",
            "dhash": 0.0,
            "ahash": 0.0,
            "color": 0.0,
        }

        for crop_name, crop_bytes in cls._video_frame_crops(frame_bytes):
            d = cls._hash_similarity(ref_d, cls._dhash_from_bytes(crop_bytes))
            a = cls._hash_similarity(ref_a, cls._image_ahash_from_bytes(crop_bytes))
            c = cls._hist_similarity(ref_h, cls._color_histogram_from_bytes(crop_bytes))

            # 형태를 가장 중요하게 보고 색은 보조.
            score = round((d * 0.50) + (a * 0.30) + (c * 0.20), 1)
            if score > best["score"]:
                best = {
                    "score": score,
                    "crop": crop_name,
                    "dhash": d,
                    "ahash": a,
                    "color": c,
                }

        return best

    @staticmethod
    def _validate_tiktok_candidate_page(page, expected_url: str) -> Dict[str, Any]:
        expected = str(expected_url or "").strip()
        current = str(getattr(page, "url", "") or "").strip()
        out = {"ok": False, "expected_url": expected, "current_url": current, "reason": ""}
        def vid(url):
            m = re.search(r"/video/(\d+)", str(url or ""))
            return m.group(1) if m else ""
        if "/video/" not in expected:
            out["reason"] = "candidate_not_video_url"; return out
        if "/video/" not in current:
            out["reason"] = "redirected_to_account_home_or_feed"; return out
        if vid(expected) and vid(current) and vid(expected) != vid(current):
            out["reason"] = "redirected_to_other_video"; return out
        try: count = page.locator("video").count()
        except Exception: count = 0
        if count < 1:
            out["reason"] = "video_element_missing"; return out
        out["ok"] = True; out["reason"] = "verified_candidate_video"
        return out

    @classmethod
    def compare_tiktok_candidates_with_reference(
        cls,
        product_name: str,
        items: List[Dict[str, Any]],
        *,
        max_candidates: int = 10,
        frames_per_video: int = 4,
    ) -> List[Dict[str, Any]]:
        """
        Sprint196-3AM
        선택된 NAVER 상품 대표이미지와 TikTok 후보 영상의 실제 화면 프레임을 비교합니다.

        중요:
        - TikTok 수집 로직 자체는 변경하지 않습니다.
        - 후보 URL을 새 Playwright context에서 열어 프레임 screenshot만 추출합니다.
        - 외부 AI/API 없이 로컬 perceptual hash로 1차 시각 유사도를 계산합니다.
        - URL/제목 점수와 시각 점수를 분리해서 보존합니다.
        """
        rows = [dict(x or {}) for x in list(items or [])]
        reference = cls._selected_product_reference(product_name)
        reference_url = str(reference.get("image_url") or "").strip()

        if not reference_url.startswith("http"):
            for row in rows:
                row["visual_match_score"] = None
                row["visual_match_status"] = "reference_image_missing"
            return rows

        ref_bytes = cls._download_image_bytes(reference_url)
        ref_hash = cls._image_ahash_from_bytes(ref_bytes)
        if not ref_hash:
            for row in rows:
                row["visual_match_score"] = None
                row["visual_match_status"] = "reference_image_decode_failed"
            return rows

        profile = (Path("browser_profile") / "source_sites").resolve()
        profile.mkdir(parents=True, exist_ok=True)

        from playwright.sync_api import sync_playwright

        pw = None
        context = None
        page = None

        try:
            pw = sync_playwright().start()
            context = pw.chromium.launch_persistent_context(
                user_data_dir=str(profile),
                channel="chrome",
                headless=False,
                viewport={"width": 900, "height": 900},
                locale="ko-KR",
                args=[
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-session-crashed-bubble",
                ],
                timeout=15000,
            )
            try:
                context.set_default_timeout(3500)
                context.set_default_navigation_timeout(12000)
            except Exception:
                pass

            pages = list(context.pages or [])
            page = pages[0] if pages else context.new_page()
            for extra in pages[1:]:
                try:
                    extra.close()
                except Exception:
                    pass

            analyzed = []
            for idx_row, row in enumerate(rows):
                if idx_row >= max_candidates:
                    analyzed.append(row)
                    continue

                url = str(row.get("url") or "").strip()
                if not url.startswith("http"):
                    row["visual_match_score"] = None
                    row["visual_match_status"] = "invalid_url"
                    analyzed.append(row)
                    continue

                best_score = 0.0
                frame_scores = []

                try:
                    print("[Sprint196-3AM Visual Match] OPEN", idx_row + 1, url[:160], flush=True)
                    try:
                        page.goto(url, wait_until="domcontentloaded", timeout=12000)
                    except Exception as nav_exc:
                        print(
                            "[Sprint196-3AM Visual Match] NAV_WARN",
                            idx_row + 1,
                            type(nav_exc).__name__,
                            str(nav_exc)[:180],
                            flush=True,
                        )

                    try:
                        page.wait_for_timeout(1800)
                    except Exception:
                        pass

                    _verified_3ap = cls._validate_tiktok_candidate_page(page, url)
                    row["candidate_page_verified"] = bool(_verified_3ap.get("ok"))
                    row["candidate_page_status"] = _verified_3ap.get("reason")
                    row["candidate_actual_url"] = _verified_3ap.get("current_url")
                    if not _verified_3ap.get("ok"):
                        row["visual_match_score"] = None
                        row["visual_match_status"] = "candidate_page_not_verified"
                        row["visual_match_label"] = "분석 제외"
                        row["auto_use"] = "제외 후보"
                        row["match_label"] = "후보 영상 검증 실패"
                        analyzed.append(row)
                        print("[Sprint196-3AP Candidate Verify] SKIP", {
                            "rank": idx_row + 1,
                            "reason": _verified_3ap.get("reason"),
                            "actual": str(_verified_3ap.get("current_url") or "")[:160],
                        }, flush=True)
                        continue

                    video = page.locator("video").first
                    try:
                        video.wait_for(state="attached", timeout=3500)
                    except Exception:
                        pass

                    # Four spaced moments. If seeking is blocked, screenshots still sample
                    # the visible video while playback advances.
                    for frame_index in range(max(1, int(frames_per_video))):
                        try:
                            if frame_index > 0:
                                page.wait_for_timeout(850)
                            try:
                                if video.count():
                                    shot = video.screenshot(timeout=3000)
                                else:
                                    shot = page.screenshot(timeout=3000)
                            except Exception:
                                shot = page.screenshot(timeout=3000)

                            focused = cls._visual_similarity_product_focused(
                                ref_bytes,
                                shot,
                            )
                            score = float(focused.get("score") or 0.0)
                            if score:
                                frame_scores.append(score)
                                best_score = max(best_score, score)
                                if score >= float(row.get("visual_match_score") or 0):
                                    row["visual_best_crop"] = focused.get("crop")
                                    row["visual_shape_score"] = focused.get("dhash")
                                    row["visual_ahash_score"] = focused.get("ahash")
                                    row["visual_color_score"] = focused.get("color")
                        except Exception:
                            continue

                    row["visual_match_score"] = round(best_score, 1)
                    row["visual_frame_scores"] = frame_scores
                    row["visual_match_status"] = "analyzed" if frame_scores else "frame_capture_failed"

                    # Conservative 1차 분류. Exact identity 확정이 아니라 우선순위 판별용.
                    if best_score >= 74:
                        visual_label = "시각 일치 유력"
                        visual_bonus = 40
                    elif best_score >= 62:
                        visual_label = "시각 유사 후보"
                        visual_bonus = 24
                    elif best_score >= 52:
                        visual_label = "시각 검토 필요"
                        visual_bonus = 10
                    elif best_score > 0:
                        visual_label = "시각 유사도 낮음"
                        visual_bonus = 0
                    else:
                        visual_label = "시각 분석 실패"
                        visual_bonus = 0

                    row["visual_match_label"] = visual_label
                    base_score = float(row.get("match_score") or row.get("score") or 0)
                    row["text_match_score"] = base_score
                    row["final_match_score"] = round(min(100.0, base_score + visual_bonus), 1)

                    if best_score >= 74:
                        row["auto_use"] = "검토 우선"
                        row["match_label"] = "시각 일치 유력"
                    elif best_score >= 62:
                        row["auto_use"] = "검토 후보"
                        row["match_label"] = "시각 유사 후보"
                    elif best_score >= 52:
                        row["auto_use"] = "수동 확인"
                        row["match_label"] = "시각 검토 필요"

                    print("[Sprint196-3AM Visual Match] RESULT", {
                        "rank": idx_row + 1,
                        "visual": best_score,
                        "frames": frame_scores,
                    }, flush=True)

                except Exception as exc:
                    row["visual_match_score"] = None
                    row["visual_match_status"] = "visual_match_error"
                    row["visual_match_error"] = f"{type(exc).__name__}: {exc}"
                    print(
                        "[Sprint196-3AM Visual Match] ERROR",
                        idx_row + 1,
                        type(exc).__name__,
                        str(exc)[:200],
                        flush=True,
                    )

                analyzed.append(row)

            analyzed.sort(
                key=lambda x: (
                    float(x.get("visual_match_score") or 0),
                    float(x.get("final_match_score") or x.get("match_score") or x.get("score") or 0),
                ),
                reverse=True,
            )
            for i, row in enumerate(analyzed, 1):
                row["visual_rank"] = i
            return analyzed

        except Exception as exc:
            print(
                "[Sprint196-3AM Visual Match] SESSION_ERROR",
                type(exc).__name__,
                str(exc)[:300],
                flush=True,
            )
            for row in rows:
                row["visual_match_score"] = None
                row["visual_match_status"] = "session_error"
                row["visual_match_error"] = f"{type(exc).__name__}: {exc}"
            return rows

        finally:
            if context is not None:
                try:
                    context.close()
                except Exception:
                    pass
            if pw is not None:
                try:
                    pw.stop()
                except Exception:
                    pass

    @classmethod
    def promote_tiktok_candidate(cls, product_name: str, candidate: Dict[str, Any]) -> Dict[str, Any]:
        row = dict(candidate or {})
        url = str(row.get("url") or "").strip()
        if "/video/" not in url:
            return {"ok": False, "error": "candidate_not_video_url"}
        payload = {
            "ok": True, "mode": "tiktok_discovery",
            "seed_product": str(product_name or ""),
            "candidate_url": url,
            "creator": str(row.get("creator") or row.get("account") or ""),
            "title": str(row.get("title") or ""),
            "visual_match_score": row.get("visual_match_score"),
            "candidate_page_verified": row.get("candidate_page_verified"),
            "status": "promoted_for_product_identification",
        }
        out = Path("exports")/"shopping_discovery"/"promoted_tiktok_product_candidate.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return payload

    @classmethod
    def open_exact_tiktok_candidate(cls, candidate_url: str) -> Dict[str, Any]:
        """
        Sprint196-3AT
        Open exactly one collected TikTok /video/{id} URL in a dedicated viewer profile.
        Do not rely on the user's default browser/link handling.
        The helper stays alive while the Chrome window is open.
        """
        import subprocess
        import sys
        import textwrap

        url = str(candidate_url or "").strip()
        match = re.search(r"/video/(\d+)", url)
        if not match or "tiktok.com/" not in url.lower():
            return {
                "ok": False,
                "status": "invalid_candidate_url",
                "url": url,
            }

        expected_video_id = match.group(1)
        profile = (Path("browser_profile") / "tiktok_candidate_viewer").resolve()
        profile.mkdir(parents=True, exist_ok=True)

        helper_code = textwrap.dedent(
            f"""
            from playwright.sync_api import sync_playwright
            from pathlib import Path
            import re
            import time

            target = {url!r}
            expected_video_id = {expected_video_id!r}
            profile = Path({str(profile)!r})
            status_file = Path("exports") / "shopping_discovery" / "tiktok_candidate_viewer_status.json"
            status_file.parent.mkdir(parents=True, exist_ok=True)

            p = sync_playwright().start()
            c = None
            try:
                c = p.chromium.launch_persistent_context(
                    user_data_dir=str(profile),
                    channel="chrome",
                    headless=False,
                    viewport={{"width": 1280, "height": 900}},
                    locale="ko-KR",
                    args=[
                        "--start-maximized",
                        "--no-first-run",
                        "--no-default-browser-check",
                        "--disable-session-crashed-bubble",
                    ],
                    timeout=15000,
                )

                pages = list(c.pages or [])
                page = pages[0] if pages else c.new_page()
                for extra in pages[1:]:
                    try:
                        extra.close()
                    except Exception:
                        pass

                try:
                    page.goto(target, wait_until="domcontentloaded", timeout=15000)
                except Exception as exc:
                    print("[Sprint196-3AT Viewer] NAV_WARN", type(exc).__name__, str(exc), flush=True)

                try:
                    page.wait_for_timeout(1800)
                except Exception:
                    pass

                actual = str(page.url or "")
                m = re.search(r"/video/(\\d+)", actual)
                actual_video_id = m.group(1) if m else ""

                payload = {{
                    "expected_video_id": expected_video_id,
                    "actual_video_id": actual_video_id,
                    "actual_url": actual,
                    "exact_match": bool(actual_video_id and actual_video_id == expected_video_id),
                }}
                print("[Sprint196-3AU Viewer] OPENED", payload, flush=True)
                try:
                    import json
                    status_file.write_text(
                        json.dumps(payload, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                except Exception as status_exc:
                    print("[Sprint196-3AU Viewer] STATUS_WRITE_ERROR", type(status_exc).__name__, str(status_exc), flush=True)

                # Keep this dedicated viewer alive until the user closes it.
                while True:
                    try:
                        alive = [pg for pg in list(c.pages or []) if not pg.is_closed()]
                    except Exception:
                        alive = []
                    if not alive:
                        break
                    time.sleep(0.5)
            finally:
                if c is not None:
                    try:
                        c.close()
                    except Exception:
                        pass
                try:
                    p.stop()
                except Exception:
                    pass
            """
        )

        try:
            flags = 0
            if sys.platform.startswith("win"):
                flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)

            proc = subprocess.Popen(
                [sys.executable, "-c", helper_code],
                cwd=str(Path.cwd()),
                creationflags=flags,
            )
            return {
                "ok": True,
                "status": "candidate_viewer_started",
                "url": url,
                "expected_video_id": expected_video_id,
                "pid": proc.pid,
                "profile": str(profile),
            }
        except Exception as exc:
            return {
                "ok": False,
                "status": "candidate_viewer_start_failed",
                "url": url,
                "error": f"{type(exc).__name__}: {exc}",
            }

    @staticmethod
    def _run_process_3bb(args: List[str], timeout: int = 120) -> Dict[str, Any]:
        try:
            proc = subprocess.run(
                args,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
            )
            return {
                "ok": proc.returncode == 0,
                "returncode": proc.returncode,
                "stdout": proc.stdout or "",
                "stderr": proc.stderr or "",
            }
        except Exception as exc:
            return {
                "ok": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"{type(exc).__name__}: {exc}",
            }

    @classmethod
    def _probe_video_duration_3bb(cls, video_path: Path) -> float:
        result = cls._run_process_3bb(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(video_path),
            ],
            timeout=30,
        )
        if not result.get("ok"):
            return 0.0
        try:
            return max(0.0, float(str(result.get("stdout") or "").strip()))
        except Exception:
            return 0.0

    @classmethod
    def acquire_selected_tiktok_sources(
        cls,
        source_pool: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Sprint196-3BD
        yt-dlp TikTok extractor를 사용하지 않습니다.

        2026-08 현재 TikTok webpage extractor가 정상 URL에서도
        Unexpected response를 반환하는 경우가 있어,
        실제 Chrome에서 후보 영상을 연 뒤 그 페이지가 요청한
        video/mp4 CDN URL을 Playwright 네트워크에서 직접 잡아 저장합니다.

        선택/검색/소스풀 로직은 변경하지 않습니다.
        """
        from playwright.sync_api import sync_playwright

        pool = dict(source_pool or {})
        items = [dict(x or {}) for x in list(pool.get("items") or [])]
        product = str(pool.get("product") or "tiktok").strip() or "tiktok"

        safe_product = re.sub(r'[\\/:*?"<>|]+', "_", product).strip(" ._") or "tiktok"
        out_dir = Path("exports") / "shopping_tiktok_sources" / safe_product
        out_dir.mkdir(parents=True, exist_ok=True)

        profile = (Path("browser_profile") / "tiktok_media_capture").resolve()
        profile.mkdir(parents=True, exist_ok=True)

        pw = None
        context = None
        page = None
        outputs = []

        def _looks_like_media(url: str, content_type: str = "") -> bool:
            low = str(url or "").lower()
            ct = str(content_type or "").lower()
            if "video/" in ct:
                return True
            media_tokens = (
                ".mp4", "mime_type=video", "mime_type%3dvideo",
                "video/tos", "playwm", "playaddr", "download_addr",
            )
            return any(token in low for token in media_tokens)

        try:
            pw = sync_playwright().start()
            context = pw.chromium.launch_persistent_context(
                user_data_dir=str(profile),
                channel="chrome",
                headless=False,
                viewport={"width": 1280, "height": 900},
                locale="ko-KR",
                args=[
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-session-crashed-bubble",
                    "--autoplay-policy=no-user-gesture-required",
                ],
                timeout=15000,
            )
            try:
                context.set_default_timeout(4500)
                context.set_default_navigation_timeout(15000)
            except Exception:
                pass

            pages = list(context.pages or [])
            page = pages[0] if pages else context.new_page()
            for extra in pages[1:]:
                try:
                    extra.close()
                except Exception:
                    pass

            for index, row in enumerate(items, 1):
                url = str(row.get("url") or "").strip()
                video_id = str(row.get("video_id") or "").strip() or f"{index:02d}"
                creator = str(row.get("creator") or "").strip()

                if not url.startswith("http") or "/video/" not in url:
                    outputs.append({
                        **row,
                        "acquire_ok": False,
                        "acquire_status": "invalid_url",
                        "local_path": "",
                        "duration": 0,
                        "segment_candidates": [],
                    })
                    continue

                media_urls = []

                def _on_response_3bd(response):
                    try:
                        ct = str(response.headers.get("content-type") or "")
                        rurl = str(response.url or "")
                        if _looks_like_media(rurl, ct) and rurl not in media_urls:
                            media_urls.append(rurl)
                    except Exception:
                        pass

                page.on("response", _on_response_3bd)

                print("[Sprint196-3BD Browser Acquire] OPEN", {
                    "index": index,
                    "video_id": video_id,
                    "creator": creator,
                    "url": url[:160],
                }, flush=True)

                local_path = ""
                error = ""
                actual_url = ""

                try:
                    try:
                        page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    except Exception as nav_exc:
                        print(
                            "[Sprint196-3BD Browser Acquire] NAV_WARN",
                            type(nav_exc).__name__,
                            str(nav_exc)[:240],
                            flush=True,
                        )

                    try:
                        page.wait_for_timeout(2200)
                    except Exception:
                        pass

                    actual_url = str(page.url or "")
                    expected_match = re.search(r"/video/(\d+)", url)
                    actual_match = re.search(r"/video/(\d+)", actual_url)
                    expected_id = expected_match.group(1) if expected_match else ""
                    actual_id = actual_match.group(1) if actual_match else ""

                    if not actual_id or (expected_id and actual_id != expected_id):
                        raise RuntimeError(
                            f"candidate_redirect_mismatch expected={expected_id} actual={actual_id} url={actual_url}"
                        )

                    video = page.locator("video").first
                    try:
                        video.wait_for(state="attached", timeout=5000)
                    except Exception:
                        pass

                    # DOM currentSrc/source 후보도 수집
                    try:
                        dom_sources = page.evaluate(
                            """
                            () => {
                                const out = [];
                                for (const v of Array.from(document.querySelectorAll('video'))) {
                                    if (v.currentSrc) out.push(v.currentSrc);
                                    if (v.src) out.push(v.src);
                                    for (const s of Array.from(v.querySelectorAll('source'))) {
                                        if (s.src) out.push(s.src);
                                    }
                                    try { v.play(); } catch (e) {}
                                }
                                return [...new Set(out)];
                            }
                            """
                        ) or []
                        for candidate in dom_sources:
                            candidate = str(candidate or "")
                            if candidate.startswith("http") and candidate not in media_urls:
                                media_urls.append(candidate)
                    except Exception:
                        pass

                    # 실제 영상 요청이 발생하도록 조금 재생
                    try:
                        page.wait_for_timeout(2500)
                    except Exception:
                        pass

                    # 가장 최근에 잡힌 media URL부터 시도
                    last_download_error = ""
                    for media_url in reversed(media_urls):
                        if not str(media_url).startswith("http"):
                            continue
                        try:
                            response = context.request.get(
                                media_url,
                                headers={
                                    "Referer": url,
                                    "Accept": "*/*",
                                },
                                timeout=30000,
                            )
                            if not response.ok:
                                last_download_error = f"HTTP {response.status}"
                                continue
                            body = response.body()
                            if not body or len(body) < 50_000:
                                last_download_error = f"media_body_too_small:{len(body) if body else 0}"
                                continue

                            target = out_dir / f"{index:02d}_{video_id}.mp4"
                            target.write_bytes(body)
                            local_path = str(target)
                            break
                        except Exception as media_exc:
                            last_download_error = f"{type(media_exc).__name__}: {media_exc}"
                            continue

                    if not local_path:
                        raise RuntimeError(
                            "browser_media_capture_failed"
                            + (f": {last_download_error}" if last_download_error else "")
                            + f" media_candidates={len(media_urls)}"
                        )

                except Exception as exc:
                    error = f"{type(exc).__name__}: {exc}"
                finally:
                    try:
                        page.remove_listener("response", _on_response_3bd)
                    except Exception:
                        pass

                duration = cls._probe_video_duration_3bb(Path(local_path)) if local_path else 0.0
                segments = []
                if duration >= 3.0:
                    seg_start = 1.0 if duration >= 5.0 else 0.0
                    stop = max(seg_start, duration - 1.0)
                    seg_index = 1
                    while seg_start + 2.0 <= stop and seg_index <= 8:
                        seg_end = min(seg_start + 3.0, stop)
                        segments.append({
                            "segment_id": f"{video_id}_{seg_index:02d}",
                            "start": round(seg_start, 2),
                            "end": round(seg_end, 2),
                            "duration": round(seg_end - seg_start, 2),
                            "status": "basic_candidate",
                        })
                        seg_start += 3.0
                        seg_index += 1

                item_out = {
                    **row,
                    "acquire_ok": bool(local_path),
                    "acquire_status": "ready" if local_path else "browser_capture_failed",
                    "local_path": local_path,
                    "duration": round(duration, 3),
                    "segment_candidates": segments,
                    "actual_url": actual_url,
                    "media_candidate_count": len(media_urls),
                    "download_error": error,
                    "acquire_mode": "playwright_browser_media_capture",
                }
                outputs.append(item_out)

                print("[Sprint196-3BD Browser Acquire] RESULT", {
                    "index": index,
                    "video_id": video_id,
                    "ok": bool(local_path),
                    "duration": round(duration, 2),
                    "media_candidates": len(media_urls),
                    "error": error[:180],
                }, flush=True)

            ready = [x for x in outputs if x.get("acquire_ok")]
            payload = {
                "ok": bool(ready),
                "status": "ready" if ready else "no_downloaded_sources",
                "product": product,
                "count": len(ready),
                "requested_count": len(items),
                "items": outputs,
                "output_dir": str(out_dir),
                "acquire_mode": "playwright_browser_media_capture",
                "summary": (
                    f"선택한 {len(items)}개 중 {len(ready)}개 TikTok 영상을 "
                    "실제 Chrome 미디어 요청에서 작업 소스로 확보했습니다."
                ),
            }

            manifest = out_dir / "source_manifest.json"
            try:
                manifest.write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2, default=str),
                    encoding="utf-8",
                )
                payload["manifest_path"] = str(manifest)
            except Exception:
                pass
            return payload

        except Exception as exc:
            return {
                "ok": False,
                "status": "browser_acquire_session_failed",
                "product": product,
                "count": 0,
                "requested_count": len(items),
                "items": outputs,
                "summary": "TikTok 브라우저 미디어 확보 세션을 시작하지 못했습니다.",
                "error": f"{type(exc).__name__}: {exc}",
            }
        finally:
            if context is not None:
                try:
                    context.close()
                except Exception:
                    pass
            if pw is not None:
                try:
                    pw.stop()
                except Exception:
                    pass

    @classmethod
    def _extract_frame_png_3be(
        cls,
        video_path: Path,
        at_seconds: float,
        out_path: Path,
    ) -> bool:
        result = cls._run_process_3bb(
            [
                "ffmpeg",
                "-y",
                "-ss", f"{max(0.0, float(at_seconds)):.3f}",
                "-i", str(video_path),
                "-frames:v", "1",
                "-vf", "scale='min(540,iw)':-2",
                str(out_path),
            ],
            timeout=40,
        )
        return bool(result.get("ok") and out_path.is_file())

    @staticmethod
    def _frame_quality_metrics_3be(image_path: Path) -> Dict[str, float]:
        """
        OCR 없이 사용하는 1차 품질 휴리스틱.
        - motion은 별도 프레임 차이로 계산
        - 상/하단 edge density가 중앙보다 지나치게 높으면 박힌 자막/워터마크 위험 증가
        - 밝기/대비가 너무 낮으면 사용 점수 감소
        """
        try:
            from PIL import Image, ImageFilter, ImageStat, ImageChops

            with Image.open(image_path) as src:
                im = src.convert("L")
            w, h = im.size
            if w < 40 or h < 40:
                return {}

            top = im.crop((0, 0, w, max(1, int(h * 0.24))))
            middle = im.crop((0, int(h * 0.28), w, max(int(h * 0.29), int(h * 0.72))))
            bottom = im.crop((0, int(h * 0.76), w, h))

            def edge_density(part):
                edge = part.filter(ImageFilter.FIND_EDGES)
                stat = ImageStat.Stat(edge)
                return float(stat.mean[0]) / 255.0

            stat = ImageStat.Stat(im)
            brightness = float(stat.mean[0]) / 255.0
            contrast = float(stat.stddev[0]) / 128.0

            top_edge = edge_density(top)
            middle_edge = edge_density(middle)
            bottom_edge = edge_density(bottom)
            overlay_ratio = max(top_edge, bottom_edge) / max(0.01, middle_edge)

            return {
                "brightness": round(brightness, 4),
                "contrast": round(contrast, 4),
                "top_edge": round(top_edge, 4),
                "middle_edge": round(middle_edge, 4),
                "bottom_edge": round(bottom_edge, 4),
                "overlay_ratio": round(overlay_ratio, 4),
            }
        except Exception:
            return {}

    @staticmethod
    def _frame_motion_3be(path_a: Path, path_b: Path) -> float:
        try:
            from PIL import Image, ImageChops, ImageStat
            with Image.open(path_a) as a0:
                a = a0.convert("L").resize((240, 426))
            with Image.open(path_b) as b0:
                b = b0.convert("L").resize((240, 426))
            diff = ImageChops.difference(a, b)
            mean = float(ImageStat.Stat(diff).mean[0]) / 255.0
            return round(mean, 4)
        except Exception:
            return 0.0

    @classmethod
    def analyze_acquired_tiktok_segments(
        cls,
        acquired_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Sprint196-3BE
        확보된 TikTok 원본의 기본 3초 후보 구간을 자동 평가합니다.

        목표:
        - 자막/워터마크가 화면 상/하단에 강하게 박힌 구간은 위험 표시
        - 너무 정적이거나 너무 어두운 구간은 후순위
        - 움직임과 화면 품질이 적당한 구간을 자동추천
        - OCR은 사용하지 않음
        """
        payload = dict(acquired_payload or {})
        items = [dict(x or {}) for x in list(payload.get("items") or [])]
        product = str(payload.get("product") or "tiktok")
        safe_product = re.sub(r'[\\/:*?"<>|]+', "_", product).strip(" ._") or "tiktok"
        base_dir = Path("exports") / "shopping_tiktok_sources" / safe_product
        analysis_dir = base_dir / "segment_analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)

        analyzed_items = []
        all_segments = []

        for item_idx, item in enumerate(items, 1):
            local_path = Path(str(item.get("local_path") or ""))
            segments = [dict(x or {}) for x in list(item.get("segment_candidates") or [])]
            analyzed_segments = []

            if not item.get("acquire_ok") or not local_path.is_file():
                item["analyzed_segments"] = []
                analyzed_items.append(item)
                continue

            for seg_idx, seg in enumerate(segments, 1):
                start = float(seg.get("start") or 0.0)
                end = float(seg.get("end") or start)
                if end <= start:
                    continue

                mid = (start + end) / 2.0
                p1 = analysis_dir / f"{item_idx:02d}_{seg_idx:02d}_a.png"
                p2 = analysis_dir / f"{item_idx:02d}_{seg_idx:02d}_b.png"
                p3 = analysis_dir / f"{item_idx:02d}_{seg_idx:02d}_m.png"

                ok1 = cls._extract_frame_png_3be(local_path, start + 0.25, p1)
                ok2 = cls._extract_frame_png_3be(local_path, max(start + 0.5, end - 0.25), p2)
                ok3 = cls._extract_frame_png_3be(local_path, mid, p3)

                metrics = cls._frame_quality_metrics_3be(p3) if ok3 else {}
                motion = cls._frame_motion_3be(p1, p2) if ok1 and ok2 else 0.0
                text_metrics = cls._textlike_density_3bh(p3) if ok3 else {}

                overlay_ratio = float(metrics.get("overlay_ratio") or 0.0)
                brightness = float(metrics.get("brightness") or 0.0)
                contrast = float(metrics.get("contrast") or 0.0)
                textlike_ratio = float(text_metrics.get("textlike_ratio") or 0.0)
                textlike_peak = float(text_metrics.get("textlike_peak") or 0.0)
                center_density = float(text_metrics.get("center_density") or 0.0)

                # 3BH: 상/하단뿐 아니라 중앙/상단 박힌 글자도 더 강하게 제외.
                if (
                    overlay_ratio >= 2.0
                    or textlike_ratio >= 1.55
                    or textlike_peak >= 0.20
                    or center_density >= 0.16
                ):
                    overlay_risk = "높음"
                elif (
                    overlay_ratio >= 1.40
                    or textlike_ratio >= 1.30
                    or textlike_peak >= 0.15
                    or center_density >= 0.12
                ):
                    overlay_risk = "보통"
                else:
                    overlay_risk = "낮음"

                # 100점 기준. '좋은 장면' 우선순위용 휴리스틱.
                score = 55.0

                # 적당한 motion 선호. 너무 정적이거나 극단적인 변화는 감점.
                if 0.035 <= motion <= 0.22:
                    score += 25
                elif 0.018 <= motion < 0.035 or 0.22 < motion <= 0.32:
                    score += 12
                elif motion < 0.010:
                    score -= 18
                else:
                    score -= 5

                if 0.22 <= brightness <= 0.90:
                    score += 8
                else:
                    score -= 10

                if contrast >= 0.20:
                    score += 7
                else:
                    score -= 5

                if overlay_risk == "높음":
                    score -= 28
                elif overlay_risk == "보통":
                    score -= 12
                else:
                    score += 5

                score = round(max(0.0, min(100.0, score)), 1)
                # 3BG: 실제 완성본에서 '보통' 위험 구간에도 박힌 글자가 남아 엄격화.
                recommended = bool(score >= 60 and overlay_risk == "낮음")

                signature = cls._segment_similarity_signature_3bh(
                    local_path,
                    start,
                    end,
                    analysis_dir,
                    f"{item_idx:02d}_{seg_idx:02d}",
                )

                row = {
                    **seg,
                    "video_id": item.get("video_id"),
                    "creator": item.get("creator"),
                    "local_path": str(local_path),
                    "quality_score": score,
                    "motion_score": motion,
                    "overlay_risk": overlay_risk,
                    "overlay_ratio": round(overlay_ratio, 3),
                    "textlike_ratio": round(textlike_ratio, 3),
                    "textlike_peak": round(textlike_peak, 3),
                    "center_text_density": round(center_density, 3),
                    "brightness": round(brightness, 3),
                    "contrast": round(contrast, 3),
                    "recommended": recommended,
                    "preview_frame": str(p3) if p3.is_file() else "",
                    "visual_signature": signature,
                    "analysis_status": "ready",
                }
                analyzed_segments.append(row)
                all_segments.append(row)

            item["analyzed_segments"] = analyzed_segments
            item["recommended_segment_count"] = sum(
                1 for x in analyzed_segments if x.get("recommended")
            )
            analyzed_items.append(item)

        all_segments.sort(
            key=lambda x: (
                bool(x.get("recommended")),
                float(x.get("quality_score") or 0),
            ),
            reverse=True,
        )

        # Sprint196-3BH:
        # 1) 같은 video_id는 1개만
        # 2) 서로 다른 게시물이어도 실제 화면이 지나치게 비슷하면 중복 제외
        # 3) overlay 위험 '낮음'만 자동편집 후보
        selected = []
        per_video_count_3bp = {}
        for seg in all_segments:
            if not seg.get("recommended"):
                continue
            if str(seg.get("overlay_risk") or "") != "낮음":
                continue

            vid = str(seg.get("video_id") or "")
            if not vid:
                continue

            # 동일 제품 원본이 적을 때 장면 부족을 막기 위해,
            # 같은 영상에서도 화면이 다른 구간은 최대 3개까지 허용.
            if int(per_video_count_3bp.get(vid, 0)) >= 3:
                continue

            duplicate_visual = False
            best_similarity = 0.0
            for picked in selected:
                sim = cls._segment_similarity_3bh(
                    dict(seg.get("visual_signature") or {}),
                    dict(picked.get("visual_signature") or {}),
                )
                best_similarity = max(best_similarity, sim)
                if sim >= 0.84:
                    duplicate_visual = True
                    break

            seg["visual_duplicate_similarity"] = round(best_similarity, 4)
            seg["visual_duplicate"] = duplicate_visual
            if duplicate_visual:
                seg["recommended"] = False
                seg["analysis_status"] = "excluded_visual_duplicate"
                continue

            selected.append(seg)
            per_video_count_3bp[vid] = int(per_video_count_3bp.get(vid, 0)) + 1
            if len(selected) >= 8:
                break

        result = {
            "ok": bool(all_segments),
            "status": "ready" if all_segments else "no_segments",
            "product": product,
            "items": analyzed_items,
            "segments": all_segments,
            "recommended_segments": selected,
            "segment_count": len(all_segments),
            "recommended_count": len(selected),
            "summary": (
                f"기본 구간 {len(all_segments)}개를 분석해 "
                f"자동편집 우선 후보 {len(selected)}개를 골랐습니다."
            ),
        }

        manifest = base_dir / "usable_segment_manifest.json"
        try:
            manifest.write_text(
                json.dumps(result, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )
            result["manifest_path"] = str(manifest)
        except Exception:
            pass

        return result

    @classmethod
    def build_recommended_tiktok_clips(
        cls,
        segment_analysis: Dict[str, Any],
        *,
        max_clips: int = 8,
    ) -> Dict[str, Any]:
        """
        Sprint196-3BF
        3BE에서 추천한 구간을 실제 MP4 클립으로 잘라 기존 쇼핑쇼츠
        editor_clip_sources가 바로 사용할 수 있는 경로 목록으로 만듭니다.

        기존 쇼핑 렌더러는 변경하지 않습니다.
        생성된 clip_paths만 기존 sprint193_29_loaded_clip_paths에 연결합니다.
        """
        payload = dict(segment_analysis or {})
        product = str(payload.get("product") or "tiktok").strip() or "tiktok"
        segments = [
            dict(x or {})
            for x in list(payload.get("recommended_segments") or [])
            if bool(x.get("recommended"))
        ][: max(1, int(max_clips))]

        safe_product = re.sub(r'[\\/:*?"<>|]+', "_", product).strip(" ._") or "tiktok"
        out_dir = (
            Path("assets")
            / "gemini_clips"
            / f"tiktok_auto_{safe_product}"
        )
        out_dir.mkdir(parents=True, exist_ok=True)

        # 이전 자동생성 클립만 정리. 다른 프로젝트/기존 Gemini 폴더는 건드리지 않음.
        for old in out_dir.glob("scene_*.mp4"):
            try:
                old.unlink()
            except Exception:
                pass

        built = []
        for index, seg in enumerate(segments, 1):
            source_path = Path(str(seg.get("local_path") or ""))
            start = float(seg.get("start") or 0.0)
            end = float(seg.get("end") or start)
            duration = max(0.0, end - start)
            if not source_path.is_file() or duration < 0.35:
                continue

            output = out_dir / f"scene_{index:02d}.mp4"

            # 정확한 컷 + H.264/yuv420p + 원본 오디오 제거.
            result = cls._run_process_3bb(
                [
                    "ffmpeg",
                    "-y",
                    "-ss", f"{start:.3f}",
                    "-i", str(source_path),
                    "-t", f"{duration:.3f}",
                    "-an",
                    "-c:v", "libx264",
                    "-preset", "veryfast",
                    "-crf", "20",
                    "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart",
                    str(output),
                ],
                timeout=90,
            )

            if not result.get("ok") or not output.is_file():
                built.append({
                    **seg,
                    "clip_ok": False,
                    "clip_path": "",
                    "clip_error": str(result.get("stderr") or "")[-1200:],
                })
                continue

            clip_duration = cls._probe_video_duration_3bb(output)
            built.append({
                **seg,
                "clip_ok": True,
                "clip_path": str(output),
                "clip_duration": round(clip_duration, 3),
                "scene_index": index,
            })

        ready = [x for x in built if x.get("clip_ok")]
        clip_paths = [str(x.get("clip_path")) for x in ready]

        result_payload = {
            "ok": bool(clip_paths),
            "status": "ready" if clip_paths else "no_clips_built",
            "product": product,
            "count": len(clip_paths),
            "clip_paths": clip_paths,
            "items": built,
            "output_dir": str(out_dir),
            "source_mode": "tiktok_recommended_segments",
            "summary": (
                f"추천 장면 {len(clip_paths)}개를 실제 쇼핑쇼츠용 MP4 클립으로 만들었습니다."
            ),
        }

        manifest = out_dir / "tiktok_auto_clip_manifest.json"
        try:
            manifest.write_text(
                json.dumps(
                    result_payload,
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                ),
                encoding="utf-8",
            )
            result_payload["manifest_path"] = str(manifest)
        except Exception:
            pass

        print("[Sprint196-3BF Clip Build] READY", {
            "product": product,
            "count": len(clip_paths),
            "paths": clip_paths,
        }, flush=True)

        return result_payload

    @staticmethod
    def _frame_perceptual_hash_3bh(image_path: Path) -> str:
        try:
            from PIL import Image
            with Image.open(image_path) as src:
                im = src.convert("L").resize((16, 16))
            pixels = list(im.getdata())
            avg = sum(pixels) / max(1, len(pixels))
            bits = "".join("1" if p >= avg else "0" for p in pixels)
            return f"{int(bits, 2):064x}"
        except Exception:
            return ""

    @staticmethod
    def _hamming_similarity_3bh(hash_a: str, hash_b: str) -> float:
        try:
            if not hash_a or not hash_b:
                return 0.0
            a = int(hash_a, 16)
            b = int(hash_b, 16)
            distance = (a ^ b).bit_count()
            total_bits = max(len(hash_a), len(hash_b)) * 4
            return max(0.0, 1.0 - (distance / max(1, total_bits)))
        except Exception:
            return 0.0

    @staticmethod
    def _textlike_density_3bh(image_path: Path) -> Dict[str, float]:
        """
        OCR 없이 화면 전체의 '박힌 글자 같은' 고대비 미세 구조를 더 강하게 탐지.
        중앙/상단 텍스트도 잡기 위해 세로 5개 band와 중앙영역을 각각 측정.
        """
        try:
            from PIL import Image, ImageFilter, ImageOps, ImageStat
            with Image.open(image_path) as src:
                gray = src.convert("L")
            w, h = gray.size
            if w < 80 or h < 120:
                return {}

            # 작은 글자 윤곽이 잘 드러나도록 대비 강화 + edges
            eq = ImageOps.autocontrast(gray)
            edges = eq.filter(ImageFilter.FIND_EDGES)

            bands = []
            for i in range(5):
                y0 = int(h * i / 5)
                y1 = int(h * (i + 1) / 5)
                part = edges.crop((0, y0, w, max(y0 + 1, y1)))
                bands.append(float(ImageStat.Stat(part).mean[0]) / 255.0)

            center = edges.crop(
                (int(w * 0.10), int(h * 0.18), int(w * 0.90), int(h * 0.82))
            )
            center_density = float(ImageStat.Stat(center).mean[0]) / 255.0

            peak = max(bands) if bands else 0.0
            medianish = sorted(bands)[len(bands)//2] if bands else 0.0
            textlike_ratio = peak / max(0.01, medianish)

            return {
                "band0": round(bands[0], 4),
                "band1": round(bands[1], 4),
                "band2": round(bands[2], 4),
                "band3": round(bands[3], 4),
                "band4": round(bands[4], 4),
                "center_density": round(center_density, 4),
                "textlike_ratio": round(textlike_ratio, 4),
                "textlike_peak": round(peak, 4),
            }
        except Exception:
            return {}

    @classmethod
    def _segment_similarity_signature_3bh(
        cls,
        local_path: Path,
        start: float,
        end: float,
        out_dir: Path,
        prefix: str,
    ) -> Dict[str, Any]:
        """
        시작/중간/끝 3장 perceptual hash를 만들어 실제 화면 유사도 비교용 signature 생성.
        """
        times = [
            start + min(0.2, max(0.0, (end-start) * 0.1)),
            (start + end) / 2.0,
            max(start, end - min(0.2, max(0.0, (end-start) * 0.1))),
        ]
        hashes = []
        frames = []
        for i, sec in enumerate(times, 1):
            p = out_dir / f"{prefix}_sim_{i}.png"
            if cls._extract_frame_png_3be(local_path, sec, p):
                h = cls._frame_perceptual_hash_3bh(p)
                if h:
                    hashes.append(h)
                frames.append(str(p))
        return {
            "hashes": hashes,
            "frames": frames,
        }

    @classmethod
    def _segment_similarity_3bh(
        cls,
        sig_a: Dict[str, Any],
        sig_b: Dict[str, Any],
    ) -> float:
        ha = list(sig_a.get("hashes") or [])
        hb = list(sig_b.get("hashes") or [])
        if not ha or not hb:
            return 0.0
        sims = []
        for a in ha:
            for b in hb:
                sims.append(cls._hamming_similarity_3bh(a, b))
        if not sims:
            return 0.0
        # strongest visual resemblance matters for repeated shot detection
        return round(max(sims), 4)

    @staticmethod
    def _parse_tiktok_view_count_3bk(text: str) -> int:
        """
        TikTok 검색 카드의 표시 텍스트 맨 앞 조회수 토큰을 숫자로 변환합니다.
        예: 85.9K -> 85900, 1.2M -> 1200000, 1434 -> 1434
        숫자를 확실히 읽지 못하면 0을 반환합니다.
        """
        raw = re.sub(r"\s+", " ", str(text or "")).strip()
        if not raw:
            return 0

        m = re.match(
            r"^\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*([KMBkmb]?)\b",
            raw,
        )
        if not m:
            return 0

        try:
            value = float(m.group(1).replace(",", ""))
        except Exception:
            return 0

        suffix = str(m.group(2) or "").upper()
        multiplier = {
            "": 1,
            "K": 1_000,
            "M": 1_000_000,
            "B": 1_000_000_000,
        }.get(suffix, 1)

        try:
            return max(0, int(round(value * multiplier)))
        except Exception:
            return 0

    @classmethod
    def _english_tiktok_keyword_3br(cls, product_name: str) -> str:
        """
        Korean product name -> concise English TikTok shopping search phrase.
        Existing ALIASES are preferred. Unknown products use cached OpenAI translation
        when an API key is available, with a small compositional fallback.
        """
        name = re.sub(r"\s+", " ", str(product_name or "")).strip()
        if not name:
            return ""

        alias_en = str((cls.ALIASES.get(name) or ("", ""))[0] or "").strip()
        if alias_en:
            return alias_en

        cache_path = Path("exports") / "shopping_discovery" / "tiktok_english_keywords.json"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache = {}
        try:
            if cache_path.is_file():
                loaded = json.loads(cache_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    cache = loaded
            cached = str(cache.get(name) or "").strip()
            if cached:
                # Sprint196-3CK:
                # 과거 캐시에 한글 검색어가 잘못 저장된 경우 그대로 반환하지 않습니다.
                # 실제 영문이 포함되고 한글이 없는 값만 English cache로 인정합니다.
                if re.search(r"[A-Za-z]", cached) and not re.search(r"[가-힣]", cached):
                    return cached
                try:
                    cache.pop(name, None)
                    cache_path.write_text(
                        json.dumps(cache, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                except Exception:
                    pass
        except Exception:
            cache = {}

        # Common shopping nouns: useful even without an API key.
        token_map = [
            ("틈새수납장", "slim narrow storage cabinet"),
            ("틈새 수납장", "slim narrow storage cabinet"),
            ("야채탈수기", "salad spinner"),
            ("두피마사지기", "scalp massager"),
            ("변기솔", "toilet brush"),
            ("욕실청소솔", "bathroom cleaning brush"),
            ("전동청소브러시", "electric cleaning brush"),
            ("수납장", "storage cabinet"),
            ("수납함", "storage organizer"),
            ("정리함", "storage organizer"),
            ("선반", "storage shelf"),
        ]
        for ko, en in token_map:
            if ko in name:
                # Exact/common compound matches are preferable.
                if name == ko or ko in {"틈새수납장", "틈새 수납장", "야채탈수기", "두피마사지기", "변기솔"}:
                    try:
                        cache[name] = en
                        cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
                    except Exception:
                        pass
                    return en

        api_key = cls._openai_key_3bq()
        if api_key:
            try:
                import urllib.request
                prompt = (
                    "Translate this Korean shopping product/category into the most natural concise "
                    "English phrase people would type into TikTok to find overseas product demo videos. "
                    "Return ONLY the English search phrase, 2 to 6 words, no quotes, no explanation.\n"
                    f"Korean product: {name}"
                )
                body = json.dumps({
                    "model": str(os.getenv("OPENAI_TRANSLATION_MODEL", "gpt-5.6-luna") or "gpt-5.6-luna"),
                    "input": prompt,
                    "reasoning": {"effort": "low"},
                }, ensure_ascii=False).encode("utf-8")
                req = urllib.request.Request(
                    "https://api.openai.com/v1/responses",
                    data=body,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data = json.loads(resp.read().decode("utf-8"))

                out_text = str(data.get("output_text") or "").strip()
                if not out_text:
                    chunks = []
                    for item in list(data.get("output") or []):
                        if not isinstance(item, dict):
                            continue
                        for part in list(item.get("content") or []):
                            if isinstance(part, dict) and isinstance(part.get("text"), str):
                                chunks.append(part.get("text"))
                    out_text = " ".join(chunks).strip()

                out_text = re.sub(r"[^A-Za-z0-9 &+/-]+", " ", out_text)
                out_text = re.sub(r"\s+", " ", out_text).strip()
                if 2 <= len(out_text) <= 80 and re.search(r"[A-Za-z]", out_text):
                    cache[name] = out_text
                    cache_path.write_text(
                        json.dumps(cache, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                    return out_text
            except Exception as exc:
                print("[Sprint196-3BR English Keyword] WARN", type(exc).__name__, str(exc)[:240], flush=True)

        # Last fallback: return empty rather than Korean, because this mode is overseas-only.
        return ""

    @classmethod
    def _chinese_tiktok_keyword_3bs(cls, product_name: str) -> str:
        name = re.sub(r"\s+", " ", str(product_name or "")).strip()
        if not name:
            return ""

        alias_zh = str((cls.ALIASES.get(name) or ("", ""))[1] or "").strip()
        if alias_zh:
            return alias_zh

        common = {
            "틈새수납장": "夹缝收纳柜",
            "틈새 수납장": "夹缝收纳柜",
            "야채탈수기": "蔬菜甩干器",
            "두피마사지기": "头皮按摩器",
            "변기솔": "马桶刷",
            "욕실청소솔": "浴室清洁刷",
            "전동청소브러시": "电动清洁刷",
            "수납장": "收纳柜",
            "수납함": "收纳盒",
            "정리함": "收纳盒",
            "선반": "置物架",
        }
        if name in common:
            return common[name]

        api_key = cls._openai_key_3bq()
        if not api_key:
            return ""

        cache_path = Path("exports") / "shopping_discovery" / "tiktok_chinese_keywords.json"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache = {}
        try:
            if cache_path.is_file():
                loaded = json.loads(cache_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    cache = loaded
            cached = str(cache.get(name) or "").strip()
            if cached:
                return cached
        except Exception:
            cache = {}

        try:
            import urllib.request
            prompt = (
                "Translate this Korean shopping product/category into the concise Simplified Chinese "
                "phrase used to search short-form product demo videos. Return ONLY Chinese, 2-8 Chinese "
                "characters/words, no explanation.\nKorean product: " + name
            )
            body = json.dumps({
                "model": str(os.getenv("OPENAI_TRANSLATION_MODEL", "gpt-5.6-luna") or "gpt-5.6-luna"),
                "input": prompt,
                "reasoning": {"effort": "low"},
            }, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(
                "https://api.openai.com/v1/responses",
                data=body,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            out = str(data.get("output_text") or "").strip()
            if not out:
                chunks = []
                for item in list(data.get("output") or []):
                    if isinstance(item, dict):
                        for part in list(item.get("content") or []):
                            if isinstance(part, dict) and isinstance(part.get("text"), str):
                                chunks.append(part["text"])
                out = "".join(chunks).strip()
            out = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9 ]+", "", out).strip()
            if out and re.search(r"[\u4e00-\u9fff]", out):
                cache[name] = out
                cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
                return out
        except Exception as exc:
            print("[Sprint196-3BS Chinese Keyword] WARN", type(exc).__name__, str(exc)[:220], flush=True)
        return ""

    @classmethod
    def _tiktok_query_variants_3bn(cls, product_name: str) -> List[str]:
        """
        Sprint196-3BS:
        Overseas sourcing uses English + Simplified Chinese only.
        Korean queries are never sent to TikTok.
        """
        en = cls._english_tiktok_keyword_3br(product_name)
        zh = cls._chinese_tiktok_keyword_3bs(product_name)

        variants = []
        if en:
            variants.extend([
                en,
                f"{en} product demo",
                f"{en} tiktok shop",
            ])
        if zh:
            variants.extend([
                zh,
                f"{zh} 好物",
                f"{zh} 使用",
            ])

        out = []
        seen = set()
        for q in variants:
            q = re.sub(r"\s+", " ", str(q or "")).strip()
            key = q.casefold()
            if q and key not in seen:
                seen.add(key)
                out.append(q)
        return out[:6]


    @classmethod
    def _indexed_tiktok_fill_3bo(
        cls,
        product_name: str,
        *,
        existing_items: List[Dict[str, Any]],
        target_count: int,
    ) -> Dict[str, Any]:
        """
        Sprint196-3BO
        TikTok 웹 검색이 약 15개에서 고정되는 경우,
        검색엔진에 인덱싱된 TikTok /video/ URL을 보조 후보로 합칩니다.

        - TikTok URL만 허용
        - /video/{id} 고유 ID 중복 제거
        - 기존 TikTok 웹 검색 후보를 우선 보존
        - 최대 target_count까지만 채움
        """
        existing = [dict(x or {}) for x in list(existing_items or [])]
        seen = {
            str(x.get("video_id") or "").strip()
            for x in existing
            if str(x.get("video_id") or "").strip()
        }

        variants = cls._tiktok_query_variants_3bn(product_name)
        rows_added = []
        errors = []

        # 사이트 제한 검색어를 여러 개 사용.
        queries = []
        for q in variants:
            q = str(q or "").strip()
            if not q:
                continue
            queries.extend([
                f'site:tiktok.com/@ "{q}" "/video/"',
                f'site:tiktok.com "{q}" TikTok video',
            ])

        dedup_queries = []
        for q in queries:
            if q not in dedup_queries:
                dedup_queries.append(q)

        for query in dedup_queries[:8]:
            if len(existing) + len(rows_added) >= int(target_count):
                break

            try:
                search_rows, search_errors = cls._search(
                    query,
                    count=max(20, int(target_count)),
                )
                errors.extend(search_errors)
            except Exception as exc:
                errors.append(f"{type(exc).__name__}: {exc}")
                continue

            for raw in list(search_rows or []):
                url = str((raw or {}).get("url") or "").strip()
                if "tiktok.com/" not in url.lower():
                    continue

                # 검색엔진 redirect/query를 제거하고 실제 TikTok URL을 찾음.
                video_match = re.search(
                    r"https?://(?:www\.)?tiktok\.com/@([^/?#]+)/video/(\d+)",
                    url,
                    flags=re.I,
                )
                if not video_match:
                    # URL 텍스트 자체가 직접 TikTok 주소가 아닐 때 제목/본문에는
                    # 정확한 video id가 없으므로 무리하게 후보를 만들지 않음.
                    continue

                creator = video_match.group(1)
                video_id = video_match.group(2)
                if video_id in seen:
                    continue
                seen.add(video_id)

                clean = f"https://www.tiktok.com/@{creator}/video/{video_id}"
                title = re.sub(
                    r"\s+",
                    " ",
                    str((raw or {}).get("title") or ""),
                ).strip()[:240]
                views = cls._parse_tiktok_view_count_3bk(title)

                rows_added.append({
                    "platform": "TikTok",
                    "title": title,
                    "view_count": views,
                    "view_count_text": f"{views:,}" if views > 0 else "",
                    "url": clean,
                    "video_id": video_id,
                    "creator": creator,
                    "product": product_name,
                    "source": "indexed_tiktok_fill_3bo",
                    "candidate_url_verified": True,
                    "candidate_url_source": "indexed_search_exact_tiktok_video_url",
                    "search_query": query,
                })

                if len(existing) + len(rows_added) >= int(target_count):
                    break

        return {
            "items": rows_added,
            "added_count": len(rows_added),
            "errors": errors,
            "queries": dedup_queries[:8],
        }

    @staticmethod
    def _looks_korean_content_3bp(item: Dict[str, Any]) -> bool:
        """
        해외 소스 우선 모드:
        제목/설명/계정 텍스트에 한글이 실질적으로 포함되면 한국 콘텐츠로 보고 제외.
        URL/creator 자체만으로 국적을 추측하지 않습니다.
        """
        text = " ".join([
            str(item.get("title") or ""),
            str(item.get("description") or ""),
        ]).strip()
        if not text:
            return False
        hangul = re.findall(r"[가-힣]", text)
        letters = re.findall(r"[A-Za-z가-힣]", text)
        if not letters:
            return False
        # 한글이 2자 이상이거나 문자 중 한글 비율이 8% 이상이면 제외.
        return len(hangul) >= 2 or (len(hangul) / max(1, len(letters))) >= 0.08

    @classmethod
    def _same_product_expansion_queries_3bp(
        cls,
        product_name: str,
        items: List[Dict[str, Any]],
    ) -> List[str]:
        """
        1차 결과의 제목/해시태그/계정에서 실제 TikTok에 쓰인 표현을 추출해
        동일 제품 2차 검색어를 만듭니다.
        """
        base_kw = cls._keywords(product_name)
        base_en = str(base_kw.get("en") or "").strip()
        stop = {
            "tiktok", "viral", "video", "fyp", "foryou", "foryoupage",
            "shop", "shopping", "review", "reviews", "amazon", "temu",
            "product", "products", "gadget", "gadgets", "home", "use",
            "using", "this", "that", "with", "from", "your", "you",
        }

        scored = {}
        for item in list(items or []):
            title = str(item.get("title") or "").lower()
            # hashtag words + normal latin words
            words = re.findall(r"#?([a-z][a-z0-9_-]{3,})", title)
            for word in words:
                w = word.strip("#_-").lower()
                if not w or w in stop or w.isdigit():
                    continue
                scored[w] = scored.get(w, 0) + 1

        top_words = [
            w for w, _ in sorted(scored.items(), key=lambda kv: (-kv[1], kv[0]))
        ][:8]

        queries = []
        if base_en:
            queries.append(base_en)
        if len(top_words) >= 2:
            queries.append(" ".join(top_words[:3]))
        if base_en and top_words:
            queries.append(f"{base_en} {top_words[0]}")
        if len(top_words) >= 4:
            queries.append(" ".join(top_words[1:4]))

        out = []
        for q in queries:
            q = re.sub(r"\s+", " ", str(q or "")).strip()
            if q and q.lower() not in {x.lower() for x in out}:
                out.append(q)
        return out[:4]


    @staticmethod
    def _openai_key_3bq() -> str:
        key = str(os.getenv("OPENAI_API_KEY", "") or "").strip()
        if key:
            return key
        # 기존 앱에서 사용하는 로컬 키 파일 후보를 조용히 탐색.
        candidates = [
            Path("secrets") / "openai_api_key.txt",
            Path("secrets") / "openai_localization_api_key.txt",
            Path("secrets") / "openai_localization_key.txt",
        ]
        for p in candidates:
            try:
                if p.is_file():
                    value = p.read_text(encoding="utf-8").strip()
                    if value:
                        return value
            except Exception:
                pass
        return ""

    @classmethod
    def _extract_audio_sample_3bq(cls, video_path: Path, out_path: Path, max_seconds: float = 20.0) -> bool:
        result = cls._run_process_3bb(
            [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-t", f"{float(max_seconds):.1f}",
                "-vn",
                "-ac", "1",
                "-ar", "16000",
                "-c:a", "mp3",
                str(out_path),
            ],
            timeout=60,
        )
        return bool(result.get("ok") and out_path.is_file() and out_path.stat().st_size > 500)

    @staticmethod
    def _transcribe_audio_openai_3bq(audio_path: Path, api_key: str) -> Dict[str, Any]:
        """
        OpenAI transcription endpoint를 사용해 실제 영상 음성의 언어를 판정합니다.
        실패하면 한국 영상으로 단정하지 않고 unknown 처리합니다.
        """
        import urllib.request
        import uuid

        boundary = "----OpenAIFormBoundary" + uuid.uuid4().hex
        audio_bytes = audio_path.read_bytes()
        parts = []

        def add_field(name: str, value: str):
            parts.append(
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                f"{value}\r\n".encode("utf-8")
            )

        parts.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="file"; filename="{audio_path.name}"\r\n'
                f"Content-Type: audio/mpeg\r\n\r\n"
            ).encode("utf-8")
            + audio_bytes
            + b"\r\n"
        )
        add_field("model", "gpt-4o-mini-transcribe")
        add_field("response_format", "verbose_json")
        parts.append(f"--{boundary}--\r\n".encode("utf-8"))
        body = b"".join(parts)

        req = urllib.request.Request(
            "https://api.openai.com/v1/audio/transcriptions",
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            return {
                "ok": False,
                "language": "",
                "text": "",
                "error": f"{type(exc).__name__}: {exc}",
            }

        return {
            "ok": True,
            "language": str(data.get("language") or "").strip().lower(),
            "text": str(data.get("text") or "").strip(),
            "error": "",
        }

    @classmethod
    def _make_frame_contact_sheet_3bq(cls, video_path: Path, duration: float, out_path: Path) -> bool:
        """
        영상 3지점 프레임을 1장으로 합쳐 박힌 한국어 자막 여부를 한 번에 판정.
        """
        try:
            from PIL import Image
        except Exception:
            return False

        times = []
        if duration > 0:
            times = [
                max(0.0, duration * 0.18),
                max(0.0, duration * 0.50),
                max(0.0, duration * 0.82),
            ]
        else:
            times = [0.3, 1.0, 1.8]

        frames = []
        temp_paths = []
        try:
            for i, sec in enumerate(times, 1):
                p = out_path.parent / f"{out_path.stem}_{i}.png"
                temp_paths.append(p)
                if cls._extract_frame_png_3be(video_path, sec, p):
                    with Image.open(p) as src:
                        frames.append(src.convert("RGB").copy())

            if not frames:
                return False

            width = max(im.width for im in frames)
            resized = []
            for im in frames:
                if im.width != width:
                    h = int(im.height * width / max(1, im.width))
                    im = im.resize((width, h))
                resized.append(im)
            total_h = sum(im.height for im in resized)
            sheet = Image.new("RGB", (width, total_h))
            y = 0
            for im in resized:
                sheet.paste(im, (0, y))
                y += im.height
            sheet.save(out_path, format="JPEG", quality=82)
            return True
        except Exception:
            return False
        finally:
            for p in temp_paths:
                try:
                    p.unlink()
                except Exception:
                    pass

    @staticmethod
    def _detect_korean_text_openai_3bq(image_path: Path, api_key: str) -> Dict[str, Any]:
        import base64
        import urllib.request

        try:
            image_b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
        except Exception as exc:
            return {"ok": False, "korean_text": False, "confidence": 0.0, "error": str(exc)}

        prompt = (
            "Inspect these three frames from one short-form video. "
            "Ignore TikTok interface buttons or app UI. "
            "Decide whether the VIDEO CONTENT itself contains persistent or prominent Korean-language "
            "subtitles/captions/overlaid Korean text. Product packaging with a tiny amount of Korean text "
            "does not count. Return JSON only: "
            '{"korean_text":true|false,"confidence":0.0-1.0,"reason":"short reason"}'
        )

        body = json.dumps({
            "model": str(os.getenv("OPENAI_VISION_MODEL", "gpt-5.6-luna") or "gpt-5.6-luna"),
            "input": [{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{image_b64}",
                    },
                ],
            }],
            "reasoning": {"effort": "low"},
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            return {"ok": False, "korean_text": False, "confidence": 0.0, "error": f"{type(exc).__name__}: {exc}"}

        text = str(data.get("output_text") or "").strip()
        if not text:
            chunks = []
            for item in list(data.get("output") or []):
                if not isinstance(item, dict):
                    continue
                for part in list(item.get("content") or []):
                    if isinstance(part, dict) and isinstance(part.get("text"), str):
                        chunks.append(part.get("text"))
            text = "\n".join(chunks).strip()

        try:
            cleaned = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", text, flags=re.I | re.S).strip()
            parsed = json.loads(cleaned)
        except Exception:
            parsed = {}

        return {
            "ok": bool(parsed),
            "korean_text": bool(parsed.get("korean_text")),
            "confidence": float(parsed.get("confidence") or 0.0),
            "reason": str(parsed.get("reason") or ""),
            "error": "" if parsed else "invalid_json",
        }

    @classmethod
    def analyze_korean_content_in_acquired_sources(
        cls,
        acquired_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Sprint196-3BQ
        실제 확보된 TikTok 영상의 '한국어 자막 또는 한국어 나레이션'으로 한국 콘텐츠를 판정합니다.

        판정 규칙:
        - 한국어 음성이 명확하면 제외
        - 박힌 한국어 자막이 confidence >= 0.70이면 제외
        - 둘 다 불명확/분석 실패면 보수적으로 유지
        """
        payload = dict(acquired_payload or {})
        items = [dict(x or {}) for x in list(payload.get("items") or [])]
        api_key = cls._openai_key_3bq()

        if not api_key:
            return {
                "ok": False,
                "status": "openai_key_missing",
                "items": items,
                "kept_items": items,
                "excluded_items": [],
                "kept_count": len(items),
                "excluded_count": 0,
                "summary": "한국어 자막/나레이션 판정을 위한 OpenAI API Key가 없습니다. 영상은 제외하지 않았습니다.",
            }

        product = str(payload.get("product") or "tiktok")
        safe_product = re.sub(r'[\\/:*?"<>|]+', "_", product).strip(" ._") or "tiktok"
        analysis_dir = Path("exports") / "shopping_tiktok_sources" / safe_product / "language_analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)

        analyzed = []
        kept = []
        excluded = []

        for i, item in enumerate(items, 1):
            local_path = Path(str(item.get("local_path") or ""))
            if not item.get("acquire_ok") or not local_path.is_file():
                item["language_filter_status"] = "not_acquired"
                analyzed.append(item)
                continue

            duration = float(item.get("duration") or cls._probe_video_duration_3bb(local_path) or 0.0)
            audio_path = analysis_dir / f"{i:02d}_{item.get('video_id')}_audio.mp3"
            sheet_path = analysis_dir / f"{i:02d}_{item.get('video_id')}_frames.jpg"

            voice = {"ok": False, "language": "", "text": "", "error": ""}
            if cls._extract_audio_sample_3bq(local_path, audio_path):
                voice = cls._transcribe_audio_openai_3bq(audio_path, api_key)

            visual = {"ok": False, "korean_text": False, "confidence": 0.0, "error": ""}
            if cls._make_frame_contact_sheet_3bq(local_path, duration, sheet_path):
                visual = cls._detect_korean_text_openai_3bq(sheet_path, api_key)

            language = str(voice.get("language") or "").lower()
            transcript = str(voice.get("text") or "")
            voice_korean = (
                language in {"ko", "kor", "korean"}
                or (len(re.findall(r"[가-힣]", transcript)) >= 4)
            )
            text_korean = bool(
                visual.get("korean_text")
                and float(visual.get("confidence") or 0.0) >= 0.70
            )
            exclude = bool(voice_korean or text_korean)

            item.update({
                "language_filter_status": "excluded_korean" if exclude else "kept",
                "korean_voice": voice_korean,
                "voice_language": language,
                "voice_transcript_preview": transcript[:160],
                "korean_text_overlay": text_korean,
                "korean_text_confidence": round(float(visual.get("confidence") or 0.0), 3),
                "korean_text_reason": str(visual.get("reason") or ""),
                "language_analysis_error": " | ".join(
                    [x for x in [str(voice.get("error") or ""), str(visual.get("error") or "")] if x]
                ),
            })
            analyzed.append(item)
            (excluded if exclude else kept).append(item)

            print("[Sprint196-3BQ Korean Filter]", {
                "video_id": item.get("video_id"),
                "voice_language": language,
                "korean_voice": voice_korean,
                "korean_text": text_korean,
                "excluded": exclude,
            }, flush=True)

        result = {
            "ok": True,
            "status": "ready",
            "product": product,
            "items": analyzed,
            "kept_items": kept,
            "excluded_items": excluded,
            "kept_count": len(kept),
            "excluded_count": len(excluded),
            "summary": f"실제 영상 {len(analyzed)}개 중 한국어 자막/나레이션 영상 {len(excluded)}개를 제외했습니다.",
        }

        manifest = analysis_dir / "language_filter_manifest.json"
        try:
            manifest.write_text(
                json.dumps(result, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )
            result["manifest_path"] = str(manifest)
        except Exception:
            pass
        return result

    @classmethod
    def _same_product_reference_queries_3by(
        cls,
        product_name: str,
        reference_item: Dict[str, Any],
    ) -> List[str]:
        """
        Sprint196-3CL
        2차 검색어는 일반 카테고리명(shoe organizer)보다
        사용자가 1차에서 고른 기준 영상의 실제 제품 표현을 우선합니다.

        근거:
        - 3CJ 진단에서 2차 수집/중복제거는 정상
        - 문제는 2차 query가 너무 넓어 다른 신발수납 제품이 많이 섞이는 것
        """
        base_en = re.sub(
            r"\s+",
            " ",
            str(cls._english_tiktok_keyword_3br(product_name) or ""),
        ).strip()
        base_zh = re.sub(
            r"\s+",
            " ",
            str(cls._chinese_tiktok_keyword_3bs(product_name) or ""),
        ).strip()

        title = re.sub(
            r"\s+",
            " ",
            str((reference_item or {}).get("title") or ""),
        ).strip()
        title_low = title.lower()

        # 기준 영상 제목에서 실제 제품형 phrase를 먼저 찾습니다.
        # 긴 문장 전체를 검색어로 쓰지 않고, 검증된 짧은 상품 표현만 생성합니다.
        phrase_candidates = []

        phrase_rules = [
            (r"\bultra[\s-]*slim\s+(?:metal\s+)?shoe\s+cabinet\b", "ultra slim shoe cabinet"),
            (r"\bslim\s+metal\s+shoe\s+cabinet\b", "slim metal shoe cabinet"),
            (r"\bslim\s+shoe\s+(?:storage\s+)?cabinet\b", "slim shoe cabinet"),
            (r"\bnarrow\s+shoe\s+(?:storage\s+)?cabinet\b", "narrow shoe cabinet"),
            (r"\bflip(?:-out)?\s+shoe\s+cabinet\b", "flip shoe cabinet"),
            (r"\bpull[-\s]?out\s+shoe\s+cabinet\b", "pull out shoe cabinet"),
            (r"\brattan\s+shoe\s+cabinet\b", "rattan shoe cabinet"),
            (r"\bmetal\s+shoe\s+cabinet\b", "metal shoe cabinet"),
            (r"\bshoe\s+storage\s+cabinet\b", "shoe storage cabinet"),
            (r"\bshoe\s+cabinet\b", "shoe cabinet"),
        ]
        for pattern, phrase in phrase_rules:
            if re.search(pattern, title_low, flags=re.I):
                phrase_candidates.append(phrase)

        # 구조 단어가 title/hashtag에 있으면 조합형 검색어를 추가합니다.
        structure_words = []
        structure_map = [
            ("ultra slim", ["ultra slim", "ultraslim"]),
            ("slim", ["slim"]),
            ("narrow", ["narrow"]),
            ("metal", ["metal"]),
            ("rattan", ["rattan"]),
            ("flip", ["flip", "flip-out", "flipout"]),
            ("pull out", ["pull out", "pull-out", "pullout"]),
            ("3 drawer", ["3 drawer", "3-drawer"]),
            ("2 drawer", ["2 drawer", "2-drawer"]),
        ]
        for canonical, needles in structure_map:
            if any(needle in title_low for needle in needles):
                if canonical not in structure_words:
                    structure_words.append(canonical)

        if structure_words:
            # "slim metal shoe cabinet", "ultra slim shoe cabinet" 같은
            # 짧은 형태를 만듭니다.
            descriptors = []
            for w in structure_words:
                if w not in descriptors:
                    descriptors.append(w)
            compact = " ".join(descriptors[:3] + ["shoe", "cabinet"])
            compact = re.sub(r"\s+", " ", compact).strip()
            if compact and compact not in phrase_candidates:
                phrase_candidates.insert(0, compact)

        # 기준 영상이 generic title이면 1차 수동검색어/상품명에서 너무 넓지 않은
        # shoe cabinet 계열 fallback만 사용합니다.
        if not phrase_candidates:
            if "shoe" in base_en.lower() and "cabinet" in base_en.lower():
                phrase_candidates.append(base_en)
            else:
                phrase_candidates.extend([
                    "slim shoe cabinet",
                    "narrow shoe cabinet",
                ])

        # 중국어는 제품 특성이 확인되면 더 구체적으로 보강합니다.
        zh_queries = []
        if "slim" in structure_words or "ultra slim" in structure_words or "narrow" in structure_words:
            zh_queries.extend(["超薄鞋柜", "窄缝鞋柜"])
        if "metal" in structure_words:
            zh_queries.append("超薄金属鞋柜")
        if "flip" in structure_words:
            zh_queries.append("翻斗鞋柜")
        if base_zh:
            zh_queries.append(base_zh)

        queries = []

        # 1) 기준 영상 기반 구체 제품 표현 우선
        for phrase in phrase_candidates[:4]:
            queries.append(phrase)
            queries.append(f"{phrase} exact same")

        # 2) 중국어 구체 검색
        for q in zh_queries[:4]:
            queries.append(q)
            queries.append(f"{q} 同款")

        # 3) 마지막 fallback으로만 일반 base_en
        if base_en and base_en.casefold() not in {q.casefold() for q in queries}:
            queries.append(base_en)

        out = []
        seen = set()
        for q in queries:
            q = re.sub(r"\s+", " ", str(q or "")).strip()
            key = q.casefold()
            if q and key not in seen:
                seen.add(key)
                out.append(q)

        print("[Sprint196-3CL Second Queries]", {
            "product": product_name,
            "base_en": base_en,
            "base_zh": base_zh,
            "reference_title_preview": title[:180],
            "structure_words": structure_words,
            "phrase_candidates": phrase_candidates,
            "queries": out[:8],
        }, flush=True)

        return out[:8]

    @classmethod
    def _same_product_openai_3cb(
        cls,
        reference_sheet: Path,
        candidate_sheet: Path,
        api_key: str,
        product_reference_image: Path | None = None,
    ) -> Dict[str, Any]:
        """
        기준 TikTok 영상과 후보 TikTok 영상에서 각각 3프레임을 보고
        '같은 카테고리'가 아니라 '동일한 물리적 제품/모델'인지 엄격하게 판정합니다.
        """
        import base64
        import urllib.request

        try:
            ref_b64 = base64.b64encode(reference_sheet.read_bytes()).decode("ascii")
            cand_b64 = base64.b64encode(candidate_sheet.read_bytes()).decode("ascii")
        except Exception as exc:
            return {
                "ok": False,
                "same_product": False,
                "confidence": 0.0,
                "reason": f"image_read_failed:{exc}",
            }

        product_b64 = ""
        try:
            if product_reference_image is not None and product_reference_image.is_file():
                product_b64 = base64.b64encode(
                    product_reference_image.read_bytes()
                ).decode("ascii")
        except Exception:
            product_b64 = ""

        _image_role_text_3cd = (
            (
                "Image 1 is the clean PRODUCT REFERENCE image captured from the shopping product page. "
                "Image 2 is three frames from the REFERENCE TikTok video chosen by the user. "
                "Image 3 is three frames from a CANDIDATE TikTok video. "
            )
            if product_b64
            else (
                "Image 1 is three frames from the REFERENCE video chosen by the user. "
                "Image 2 is three frames from a CANDIDATE video. "
            )
        )
        prompt = (
            "You are doing strict product identity matching for short-form shopping videos. "
            + _image_role_text_3cd
            + "Decide whether the candidate shows the SAME physical product/model, not merely the same category. "
            "Match distinctive structure, number/position of drawers or tiers, handle shape, wheels/legs, "
            "proportions, openings, edge geometry and visible hardware. "
            "Different color is allowed only when the structure/model is otherwise clearly identical. "
            "If important structural details differ, answer false. "
            "If the product is too hidden to verify, answer false. "
            "Ignore people, room, captions, TikTok UI and camera angle. "
            "Return JSON only with keys: "
            '{"same_product":true|false,"confidence":0.0-1.0,'
            '"reason":"short concrete reason","matched_features":["feature1","feature2"]}.'
        )

        body = json.dumps(
            {
                "model": str(
                    os.getenv("OPENAI_VISION_MODEL", "gpt-5.6-luna")
                    or "gpt-5.6-luna"
                ),
                "input": [
                    {
                        "role": "user",
                        "content": (
                            [{"type": "input_text", "text": prompt}]
                            + (
                                [{
                                    "type": "input_image",
                                    "image_url": f"data:image/jpeg;base64,{product_b64}",
                                }]
                                if product_b64 else []
                            )
                            + [
                                {
                                    "type": "input_image",
                                    "image_url": f"data:image/jpeg;base64,{ref_b64}",
                                },
                                {
                                    "type": "input_image",
                                    "image_url": f"data:image/jpeg;base64,{cand_b64}",
                                },
                            ]
                        ),
                    }
                ],
                "reasoning": {"effort": "low"},
            },
            ensure_ascii=False,
        ).encode("utf-8")

        req = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            return {
                "ok": False,
                "same_product": False,
                "confidence": 0.0,
                "reason": f"{type(exc).__name__}: {exc}",
            }

        parsed = cls._json_from_openai_output_3cb(data)
        if not parsed:
            return {
                "ok": False,
                "same_product": False,
                "confidence": 0.0,
                "reason": "invalid_json",
            }

        return {
            "ok": True,
            "same_product": bool(parsed.get("same_product")),
            "confidence": max(
                0.0,
                min(1.0, float(parsed.get("confidence") or 0.0)),
            ),
            "reason": str(parsed.get("reason") or ""),
            "matched_features": list(parsed.get("matched_features") or [])[:8],
        }

    @classmethod
    def _capture_tiktok_frames_3cb(
        cls,
        page,
        url: str,
        *,
        frame_count: int = 3,
    ) -> Dict[str, Any]:
        out = {
            "ok": False,
            "url": str(url or ""),
            "frames": [],
            "error": "",
        }
        try:
            try:
                page.goto(
                    str(url or ""),
                    wait_until="domcontentloaded",
                    timeout=15000,
                )
            except Exception as nav_exc:
                print(
                    "[Sprint196-3CB Visual] NAV_WARN",
                    type(nav_exc).__name__,
                    str(nav_exc)[:220],
                    flush=True,
                )

            try:
                page.wait_for_timeout(1700)
            except Exception:
                pass

            verified = cls._validate_tiktok_candidate_page(page, str(url or ""))
            if not verified.get("ok"):
                out["error"] = str(verified.get("reason") or "candidate_not_verified")
                return out

            video = page.locator("video").first
            frames = []
            for i in range(max(1, int(frame_count))):
                try:
                    if i > 0:
                        page.wait_for_timeout(900)
                    if video.count():
                        shot = video.screenshot(timeout=3500)
                    else:
                        shot = page.screenshot(timeout=3500)
                    if shot:
                        frames.append(shot)
                except Exception:
                    continue

            out["frames"] = frames
            out["ok"] = bool(frames)
            if not frames:
                out["error"] = "frame_capture_failed"
            return out
        except Exception as exc:
            out["error"] = f"{type(exc).__name__}: {exc}"
            return out

    @staticmethod
    def _frames_to_sheet_3cb(
        frames: List[bytes],
        out_path: Path,
    ) -> bool:
        try:
            from PIL import Image
            import io

            images = []
            for raw in list(frames or []):
                try:
                    with Image.open(io.BytesIO(raw)) as im:
                        images.append(im.convert("RGB").copy())
                except Exception:
                    continue
            if not images:
                return False

            target_w = min(480, max(im.width for im in images))
            resized = []
            for im in images[:3]:
                ratio = target_w / max(1, im.width)
                h = max(1, int(im.height * ratio))
                resized.append(im.resize((target_w, h)))

            total_h = sum(im.height for im in resized)
            sheet = Image.new("RGB", (target_w, total_h))
            y = 0
            for im in resized:
                sheet.paste(im, (0, y))
                y += im.height
            out_path.parent.mkdir(parents=True, exist_ok=True)
            sheet.save(out_path, format="JPEG", quality=84)
            return True
        except Exception:
            return False

    @classmethod
    def _local_reference_frame_score_3cb(
        cls,
        reference_frames: List[bytes],
        candidate_frames: List[bytes],
    ) -> Dict[str, Any]:
        """
        OpenAI 판정이 실패할 때만 쓰는 보수적 로컬 fallback.
        여러 기준 프레임 x 후보 프레임에서 상품 중심 crop 유사도를 비교합니다.
        """
        scores = []
        for ref in list(reference_frames or []):
            for cand in list(candidate_frames or []):
                try:
                    focused = cls._visual_similarity_product_focused(ref, cand)
                    score = float(focused.get("score") or 0.0)
                    if score > 0:
                        scores.append(score)
                except Exception:
                    continue

        scores.sort(reverse=True)
        best = scores[0] if scores else 0.0
        second = scores[1] if len(scores) > 1 else 0.0
        top3 = scores[:3]
        mean_top3 = sum(top3) / len(top3) if top3 else 0.0

        # strict fallback: one lucky frame match alone is not enough
        same = bool(best >= 78.0 and second >= 72.0 and mean_top3 >= 73.0)
        confidence = min(0.92, max(0.0, mean_top3 / 100.0))
        return {
            "same_product": same,
            "confidence": confidence,
            "best": round(best, 1),
            "second": round(second, 1),
            "mean_top3": round(mean_top3, 1),
        }

    @classmethod
    def filter_same_product_candidates_by_reference_video_3cb(
        cls,
        reference_item: Dict[str, Any],
        items: List[Dict[str, Any]],
        *,
        max_candidates: int = 40,
        product_reference_image_path: str = "",
    ) -> Dict[str, Any]:
        """
        Sprint196-3CB
        1차에서 사용자가 고른 '기준 TikTok 영상' 자체를 시각 기준으로 사용합니다.
        2차 검색 결과를 제목점수만 믿지 않고 실제 영상 프레임으로 동일제품 판정합니다.

        우선순위:
        1) OpenAI vision strict identity 판정
        2) 실패한 후보에 한해서만 local perceptual fallback
        """
        from playwright.sync_api import sync_playwright

        reference = dict(reference_item or {})
        rows = [dict(x or {}) for x in list(items or [])]
        ref_url = str(reference.get("url") or "").strip()
        if not ref_url.startswith("http"):
            return {
                "ok": False,
                "status": "reference_url_missing",
                "items": rows,
                "kept_items": rows,
                "excluded_items": [],
                "input_count": len(rows),
                "kept_count": len(rows),
                "excluded_count": 0,
                "summary": "기준 영상 URL이 없어 동일제품 시각 판정을 건너뛰었습니다.",
            }

        profile = (
            Path("browser_profile") / "tiktok_same_product_visual_3cb"
        ).resolve()
        profile.mkdir(parents=True, exist_ok=True)
        out_dir = (
            Path("exports")
            / "shopping_discovery"
            / "same_product_visual_3cb"
        )
        out_dir.mkdir(parents=True, exist_ok=True)

        api_key = cls._openai_key_3bq()

        pw = None
        context = None
        page = None
        try:
            pw = sync_playwright().start()
            context = pw.chromium.launch_persistent_context(
                user_data_dir=str(profile),
                channel="chrome",
                headless=False,
                viewport={"width": 1000, "height": 900},
                locale="en-US",
                args=[
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-session-crashed-bubble",
                    "--autoplay-policy=no-user-gesture-required",
                    "--lang=en-US",
                ],
                timeout=15000,
            )
            try:
                context.set_default_timeout(4500)
                context.set_default_navigation_timeout(15000)
            except Exception:
                pass

            pages = list(context.pages or [])
            page = pages[0] if pages else context.new_page()
            for extra in pages[1:]:
                try:
                    extra.close()
                except Exception:
                    pass

            ref_capture = cls._capture_tiktok_frames_3cb(
                page,
                ref_url,
                frame_count=3,
            )
            if not ref_capture.get("ok"):
                return {
                    "ok": False,
                    "status": "reference_frame_capture_failed",
                    "items": rows,
                    "kept_items": rows,
                    "excluded_items": [],
                    "input_count": len(rows),
                    "kept_count": len(rows),
                    "excluded_count": 0,
                    "summary": (
                        "기준 영상 프레임을 확보하지 못해 동일제품 시각 판정을 건너뛰었습니다. "
                        f"({ref_capture.get('error')})"
                    ),
                }

            ref_frames = list(ref_capture.get("frames") or [])
            ref_id = str(reference.get("video_id") or "reference")
            ref_sheet = out_dir / f"reference_{ref_id}.jpg"
            ref_sheet_ok = cls._frames_to_sheet_3cb(ref_frames, ref_sheet)

            _product_reference_3cd = Path(
                str(product_reference_image_path or "")
            )
            _product_reference_ok_3cd = _product_reference_3cd.is_file()
            print("[Sprint196-3CD Product Reference]", {
                "enabled": _product_reference_ok_3cd,
                "path": str(_product_reference_3cd) if _product_reference_ok_3cd else "",
            }, flush=True)

            analyzed = []
            kept = []
            excluded = []

            for idx, raw in enumerate(rows[: max(1, int(max_candidates))], 1):
                row = dict(raw or {})
                url = str(row.get("url") or "").strip()
                capture = cls._capture_tiktok_frames_3cb(
                    page,
                    url,
                    frame_count=3,
                )
                cand_frames = list(capture.get("frames") or [])

                local = cls._local_reference_frame_score_3cb(
                    ref_frames,
                    cand_frames,
                )

                ai = {
                    "ok": False,
                    "same_product": False,
                    "confidence": 0.0,
                    "reason": "",
                    "matched_features": [],
                }
                candidate_sheet = out_dir / (
                    f"{idx:02d}_{str(row.get('video_id') or idx)}.jpg"
                )
                sheet_ok = (
                    bool(cand_frames)
                    and cls._frames_to_sheet_3cb(cand_frames, candidate_sheet)
                )
                if api_key and ref_sheet_ok and sheet_ok:
                    ai = cls._same_product_openai_3cb(
                        ref_sheet,
                        candidate_sheet,
                        api_key,
                        product_reference_image=(
                            _product_reference_3cd
                            if _product_reference_ok_3cd
                            else None
                        ),
                    )

                if ai.get("ok"):
                    same = bool(
                        ai.get("same_product")
                        and float(ai.get("confidence") or 0.0) >= 0.68
                    )
                    confidence = float(ai.get("confidence") or 0.0)
                    method = "openai_vision"
                    reason = str(ai.get("reason") or "")
                else:
                    same = bool(local.get("same_product"))
                    confidence = float(local.get("confidence") or 0.0)
                    method = "local_fallback"
                    reason = (
                        "OpenAI 판정 실패/미사용. "
                        f"로컬 유사도 best={local.get('best')}, "
                        f"second={local.get('second')}, "
                        f"mean_top3={local.get('mean_top3')}"
                    )

                row.update({
                    "same_product_visual": same,
                    "same_product_confidence": round(confidence, 3),
                    "same_product_method": (
                        f"{method}+product_image"
                        if _product_reference_ok_3cd and method == "openai_vision"
                        else method
                    ),
                    "same_product_reason": reason,
                    "product_reference_used": _product_reference_ok_3cd,
                    "same_product_features": list(
                        ai.get("matched_features") or []
                    ),
                    "same_product_local_best": local.get("best"),
                    "same_product_local_second": local.get("second"),
                    "same_product_local_mean_top3": local.get("mean_top3"),
                    "same_product_capture_ok": bool(capture.get("ok")),
                    "same_product_capture_error": str(
                        capture.get("error") or ""
                    ),
                })
                analyzed.append(row)
                (kept if same else excluded).append(row)

                print("[Sprint196-3CB Same Product]", {
                    "rank": idx,
                    "video_id": row.get("video_id"),
                    "same": same,
                    "confidence": round(confidence, 3),
                    "method": method,
                    "local": local.get("mean_top3"),
                }, flush=True)

            # Preserve any rows beyond max_candidates as not-yet-analyzed, but do not
            # auto-keep them as same product.
            for raw in rows[max(1, int(max_candidates)):]:
                row = dict(raw or {})
                row["same_product_visual"] = False
                row["same_product_method"] = "not_analyzed"
                row["same_product_reason"] = "max_candidates 초과"
                analyzed.append(row)
                excluded.append(row)

            kept.sort(
                key=lambda x: (
                    float(x.get("same_product_confidence") or 0.0),
                    int(x.get("view_count") or 0),
                ),
                reverse=True,
            )
            for i, row in enumerate(kept, 1):
                row["screen_rank"] = i

            result = {
                "ok": True,
                "status": "ready",
                "items": analyzed,
                "kept_items": kept,
                "excluded_items": excluded,
                "input_count": len(rows),
                "kept_count": len(kept),
                "excluded_count": len(excluded),
                "reference_video_id": ref_id,
                "reference_video_url": ref_url,
                "product_reference_used": _product_reference_ok_3cd,
                "product_reference_image_path": (
                    str(_product_reference_3cd)
                    if _product_reference_ok_3cd else ""
                ),
                "summary": (
                    f"2차 후보 {len(rows)}개를 기준 영상과 실제 프레임 비교해 "
                    f"동일제품 후보 {len(kept)}개를 남겼습니다."
                ),
            }
            try:
                manifest = out_dir / "latest_same_product_visual.json"
                manifest.write_text(
                    json.dumps(
                        result,
                        ensure_ascii=False,
                        indent=2,
                        default=str,
                    ),
                    encoding="utf-8",
                )
                result["manifest_path"] = str(manifest)
            except Exception:
                pass

            return result
        except Exception as exc:
            return {
                "ok": False,
                "status": "visual_filter_error",
                "items": rows,
                "kept_items": rows,
                "excluded_items": [],
                "input_count": len(rows),
                "kept_count": len(rows),
                "excluded_count": 0,
                "summary": (
                    "동일제품 시각 판정 중 오류가 발생해 기존 2차 후보를 유지했습니다. "
                    f"{type(exc).__name__}: {exc}"
                ),
            }
        finally:
            if context is not None:
                try:
                    context.close()
                except Exception:
                    pass
            if pw is not None:
                try:
                    pw.stop()
                except Exception:
                    pass

    @classmethod
    def _collect_visible_tiktok_video_anchors_3ch(cls, page) -> List[Dict[str, Any]]:
        """
        TikTok 검색 화면에 실제로 보이는 /video/{id} 링크를 직접 수집합니다.
        TikTok의 search-card class/data-e2e 이름이 바뀌어도 영상 링크 자체는 보존되는 점을 사용합니다.
        """
        try:
            rows = page.evaluate(
                """
                () => {
                    const out = [];
                    const seen = new Set();
                    const anchors = Array.from(
                        document.querySelectorAll('a[href*="/video/"]')
                    );

                    for (const a of anchors) {
                        const href = String(
                            a.href || a.getAttribute('href') || ''
                        ).trim();
                        const m = href.match(/\\/video\\/(\\d+)/);
                        if (!m) continue;

                        const videoId = m[1];
                        if (seen.has(videoId)) continue;

                        const rect = a.getBoundingClientRect();
                        const style = window.getComputedStyle(a);
                        if (
                            rect.width < 20 ||
                            rect.height < 20 ||
                            style.display === 'none' ||
                            style.visibility === 'hidden'
                        ) continue;

                        seen.add(videoId);

                        const cm = href.match(
                            /tiktok\\.com\\/@([^/]+)\\/video\\//
                        );

                        const card =
                            a.closest('[data-e2e="search-card-video-container"]') ||
                            a.closest('[data-e2e="search-video-item"]') ||
                            a.closest('[data-e2e="search-item"]') ||
                            a.parentElement;

                        const text = String(
                            (card && card.innerText) ||
                            a.getAttribute('aria-label') ||
                            a.getAttribute('title') ||
                            ''
                        ).trim();

                        out.push({
                            url: href,
                            video_id: videoId,
                            creator: cm ? cm[1] : '',
                            title: text.slice(0, 300),
                        });
                    }
                    return out;
                }
                """
            ) or []
            return [
                dict(x or {})
                for x in rows
                if str((x or {}).get("video_id") or "").isdigit()
            ]
        except Exception as exc:
            print(
                "[Sprint196-3CH Visible Anchor] WARN",
                type(exc).__name__,
                str(exc)[:200],
                flush=True,
            )
            return []

    @classmethod
    def _tiktok_search_dom_diagnostics_3ci(cls, page) -> Dict[str, Any]:
        """
        Sprint196-3CI diagnostics only.
        Does not change candidate collection/filtering.
        Captures what TikTok actually renders on the current page.
        """
        try:
            return dict(page.evaluate(
                """
                () => {
                    const hrefs = Array.from(
                        document.querySelectorAll('a[href*="/video/"]')
                    ).map(a => String(a.href || a.getAttribute('href') || '').trim());

                    const ids = [];
                    const seen = new Set();
                    for (const href of hrefs) {
                        const m = href.match(/\\/video\\/(\\d+)/);
                        if (!m || seen.has(m[1])) continue;
                        seen.add(m[1]);
                        ids.push(m[1]);
                    }

                    const visibleIds = [];
                    const visibleSeen = new Set();
                    for (const a of Array.from(
                        document.querySelectorAll('a[href*="/video/"]')
                    )) {
                        const href = String(a.href || a.getAttribute('href') || '').trim();
                        const m = href.match(/\\/video\\/(\\d+)/);
                        if (!m || visibleSeen.has(m[1])) continue;
                        const rect = a.getBoundingClientRect();
                        const style = window.getComputedStyle(a);
                        const visible = (
                            rect.width >= 20 &&
                            rect.height >= 20 &&
                            style.display !== 'none' &&
                            style.visibility !== 'hidden'
                        );
                        if (!visible) continue;
                        visibleSeen.add(m[1]);
                        visibleIds.push(m[1]);
                    }

                    const selectors = {
                        search_card_video_container:
                            document.querySelectorAll('[data-e2e="search-card-video-container"]').length,
                        search_video_item:
                            document.querySelectorAll('[data-e2e="search-video-item"]').length,
                        search_item:
                            document.querySelectorAll('[data-e2e="search-item"]').length,
                        div_item_container:
                            document.querySelectorAll('div[class*="DivItemContainer"]').length,
                    };

                    return {
                        url: location.href,
                        title: document.title,
                        all_video_anchor_count: hrefs.length,
                        unique_video_id_count: ids.length,
                        visible_unique_video_id_count: visibleIds.length,
                        unique_video_ids: ids.slice(0, 120),
                        visible_video_ids: visibleIds.slice(0, 120),
                        selector_counts: selectors,
                    };
                }
                """
            ) or {})
        except Exception as exc:
            return {
                "error": f"{type(exc).__name__}: {exc}",
            }

    @classmethod
    def collect_direct(cls, product_name: str, per_platform: int = 10, reference_item: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Sprint196-3AJ
        helper/command/marker 구조를 사용하지 않습니다.
        영상 수집 버튼을 누르면 실제 Chrome TikTok 창을 즉시 열고,
        저장된 로그인 프로필로 상품을 검색한 뒤 후보를 직접 수집합니다.
        수집 완료 후 해당 자동수집 Chrome만 닫습니다.
        """
        from playwright.sync_api import sync_playwright

        # Sprint196-3BR:
        # Personal/logged-in TikTok profile is NOT used for overseas sourcing.
        # A fresh dedicated overseas profile prevents own-account feed contamination.
        profile = (Path("browser_profile") / "tiktok_overseas_search_3br").resolve()
        profile.mkdir(parents=True, exist_ok=True)

        # NAVER decides only the product/category. TikTok receives English text only.
        kw = cls._keywords(product_name)
        if reference_item:
            query_variants_3bn = cls._same_product_reference_queries_3by(
                product_name,
                dict(reference_item or {}),
            )
            _search_stage_3by = "same_product_2nd"
        else:
            query_variants_3bn = cls._tiktok_query_variants_3bn(product_name)
            _search_stage_3by = "product_discovery_1st"

        if not query_variants_3bn:
            return {
                "ok": False,
                "product": product_name,
                "items": [],
                "counts": {"tiktok": 0, "xiaohongshu": 0},
                "errors": ["overseas_english_keyword_missing"],
                "source_mode": "tiktok_overseas_en_zh_dedicated_profile",
                "summary": (
                    f"{product_name}의 해외 TikTok 검색용 영문 키워드를 만들지 못했습니다. "
                    "수동 TikTok 검색란에 영문 검색어를 입력해 주세요."
                ),
            }
        query = query_variants_3bn[0]
        # Sprint196-3CK:
        # /search?q=... 진입 후 Videos 탭 클릭은 비동기 navigation을 추가로 발생시켜
        # Page.evaluate 시 execution context destroyed가 발생했습니다.
        # 처음부터 TikTok video 전용 URL로 직접 진입합니다.
        target = "https://www.tiktok.com/search/video?" + urllib.parse.urlencode({"q": query})

        print("[Sprint196-3AJ Collect] ENTER", {
            "product": product_name,
            "profile": str(profile),
            "target": target,
        }, flush=True)

        pw = None
        context = None
        page = None

        try:
            pw = sync_playwright().start()
            context = pw.chromium.launch_persistent_context(
                user_data_dir=str(profile),
                channel="chrome",
                headless=False,
                viewport={"width": 1365, "height": 900},
                locale="en-US",
                timezone_id="America/Los_Angeles",
                args=[
                    "--start-maximized",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-session-crashed-bubble",
                    "--lang=en-US",
                ],
                timeout=15000,
            )
            try:
                context.set_extra_http_headers({
                    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.7",
                })
            except Exception:
                pass
            try:
                context.set_default_timeout(4000)
                context.set_default_navigation_timeout(15000)
            except Exception:
                pass

            pages = list(context.pages or [])
            page = pages[0] if pages else context.new_page()

            # 중복 복원 탭은 정리하되 첫 페이지는 절대 닫지 않습니다.
            for extra in pages[1:]:
                try:
                    extra.close()
                except Exception:
                    pass

            # Sprint196-3BV:
            # TikTok can redirect a fresh browser from /search?q=... back to the home/feed.
            # First try the exact search URL. If it lands on home/feed, submit the query
            # through TikTok's own search input instead of treating the feed as a result.
            try:
                page.goto(target, wait_until="domcontentloaded", timeout=18000)
            except Exception as nav_exc:
                print(
                    "[Sprint196-3BV Search Entry] DIRECT_NAV_WARN",
                    type(nav_exc).__name__,
                    str(nav_exc)[:240],
                    flush=True,
                )

            try:
                page.bring_to_front()
            except Exception:
                pass

            try:
                page.wait_for_timeout(2500)
            except Exception:
                pass

            current_url = ""
            try:
                current_url = str(page.url or "")
            except Exception:
                pass

            if "tiktok.com/search" not in current_url.lower():
                _search_box_3bv = None
                _search_selectors_3bv = [
                    'input[data-e2e="search-user-input"]',
                    'input[type="search"]',
                    'input[placeholder*="Search"]',
                    'input[placeholder*="검색"]',
                ]
                for _sel3bv in _search_selectors_3bv:
                    try:
                        _loc3bv = page.locator(_sel3bv).first
                        if _loc3bv.count() > 0 and _loc3bv.is_visible(timeout=800):
                            _search_box_3bv = _loc3bv
                            break
                    except Exception:
                        continue

                if _search_box_3bv is not None:
                    try:
                        _search_box_3bv.click()
                        _search_box_3bv.fill(query)
                        _search_box_3bv.press("Enter")
                        page.wait_for_timeout(3000)
                    except Exception as _search_input_exc_3bv:
                        print(
                            "[Sprint196-3BV Search Entry] INPUT_WARN",
                            type(_search_input_exc_3bv).__name__,
                            str(_search_input_exc_3bv)[:240],
                            flush=True,
                        )

                try:
                    current_url = str(page.url or "")
                except Exception:
                    current_url = ""

            print("[Sprint196-3BV Search Entry]", {
                "query": query,
                "target": target,
                "actual_url": current_url[:220],
                "profile": str(profile),
            }, flush=True)

            # Sprint196-3CK:
            # target 자체가 /search/video 이므로 Videos 탭을 다시 클릭하지 않습니다.
            # 3CJ에서 확인된 execution context destroyed navigation race를 제거합니다.
            _video_tab_clicked_3by = False
            try:
                page.wait_for_url(
                    re.compile(r"https://www\.tiktok\.com/search/video\?"),
                    timeout=8000,
                )
            except Exception:
                pass
            try:
                page.wait_for_load_state("domcontentloaded", timeout=5000)
            except Exception:
                pass
            try:
                page.wait_for_timeout(1200)
            except Exception:
                pass

            try:
                current_url = str(page.url or "")
            except Exception:
                current_url = ""

            print("[Sprint196-3CK Video Route Stable]", {
                "url": current_url[:220],
                "stage": _search_stage_3by,
            }, flush=True)

            # Sprint196-3BW:
            # 검색 성공 후 TikTok 추천/홈 피드 탭이 같이 열려 있으면 닫고,
            # 실제 /search 탭 하나만 남깁니다. 이후 수집도 이 page에서만 진행합니다.
            try:
                _all_pages_3bw = [pg for pg in list(context.pages or []) if not pg.is_closed()]
                _search_pages_3bw = []
                for _pg3bw in _all_pages_3bw:
                    try:
                        _url3bw = str(_pg3bw.url or "")
                    except Exception:
                        _url3bw = ""
                    if "tiktok.com/search" in _url3bw.lower():
                        _search_pages_3bw.append(_pg3bw)

                if _search_pages_3bw:
                    # 현재 page가 검색 탭이면 유지, 아니면 첫 검색 탭으로 전환.
                    if page not in _search_pages_3bw:
                        page = _search_pages_3bw[0]

                    for _pg3bw in list(context.pages or []):
                        if _pg3bw is page:
                            continue
                        try:
                            _url3bw = str(_pg3bw.url or "")
                        except Exception:
                            _url3bw = ""
                        # TikTok 홈/추천/빈 탭만 닫습니다. 다른 사이트 탭은 건드리지 않음.
                        _low3bw = _url3bw.lower()
                        if (
                            "tiktok.com" in _low3bw
                            and "tiktok.com/search" not in _low3bw
                        ) or _low3bw in {"", "about:blank"}:
                            try:
                                _pg3bw.close()
                            except Exception:
                                pass

                    try:
                        page.bring_to_front()
                    except Exception:
                        pass
                    try:
                        current_url = str(page.url or "")
                    except Exception:
                        current_url = ""

                print("[Sprint196-3BW Tab Cleanup]", {
                    "search_tab_found": bool(_search_pages_3bw),
                    "remaining_pages": len([pg for pg in list(context.pages or []) if not pg.is_closed()]),
                    "active_url": current_url[:220],
                }, flush=True)
            except Exception as _tab_cleanup_exc_3bw:
                print(
                    "[Sprint196-3BW Tab Cleanup] WARN",
                    type(_tab_cleanup_exc_3bw).__name__,
                    str(_tab_cleanup_exc_3bw)[:220],
                    flush=True,
                )

            # 저장 로그인이 풀린 경우 사용자에게 명확히 안내.
            low_url = current_url.lower()
            if "/login" in low_url or "login?" in low_url:
                return {
                    "ok": False,
                    "product": product_name,
                    "items": [],
                    "counts": {"tiktok": 0, "xiaohongshu": 0},
                    "errors": ["tiktok_login_required"],
                    "source_mode": "tiktok_overseas_en_zh_dedicated_profile",
                    "summary": (
                        "TikTok 로그인 세션이 필요합니다. 지금 열린 TikTok 창에서 로그인한 뒤 "
                        "창을 닫고 다시 영상 수집 버튼을 눌러주세요."
                    ),
                    "current_url": current_url,
                }

            # 충분한 카드가 생기도록 스크롤.
            try:
                for _ in range(6):
                    page.mouse.wheel(0, 1100)
                    page.wait_for_timeout(500)
            except Exception:
                pass

            found = []
            try:
                # Sprint196-3AX:
                # 검색 결과 페이지가 아니거나 서버 오류 상태면 후보를 만들지 않습니다.
                current_url = str(page.url or "")
                low_current = current_url.lower()
                if "tiktok.com/search" not in low_current:
                    return {
                        "ok": False,
                        "product": product_name,
                        "items": [],
                        "counts": {"tiktok": 0, "xiaohongshu": 0},
                        "errors": ["tiktok_not_on_search_page"],
                        "source_mode": "tiktok_overseas_en_zh_dedicated_profile",
                        "current_url": current_url,
                        "summary": "TikTok 검색 결과 페이지가 열리지 않아 후보를 수집하지 않았습니다.",
                    }

                page_text = ""
                try:
                    page_text = str(page.locator("body").inner_text(timeout=2500) or "")
                except Exception:
                    page_text = ""

                low_text = page_text.lower()
                server_error_terms = [
                    "server error",
                    "something went wrong",
                    "try again",
                    "서버 오류",
                    "문제가 발생",
                    "다시 시도",
                ]
                if any(term in low_text for term in server_error_terms):
                    print("[Sprint196-3AX Search] SERVER_ERROR_PAGE", {
                        "product": product_name,
                        "url": current_url[:180],
                    }, flush=True)
                    return {
                        "ok": False,
                        "product": product_name,
                        "items": [],
                        "counts": {"tiktok": 0, "xiaohongshu": 0},
                        "errors": ["tiktok_search_server_error"],
                        "source_mode": "tiktok_overseas_en_zh_dedicated_profile",
                        "current_url": current_url,
                        "summary": (
                            "TikTok 검색 페이지에 서버 오류가 표시되어 잘못된 영상을 수집하지 않았습니다. "
                            "잠시 후 다시 검색해 주세요."
                        ),
                    }

                # Sprint196-3BJ:
                # TikTok 검색은 초기 화면에 약 10~15개 카드만 렌더되는 경우가 많습니다.
                # 최대 per_platform개를 확보할 때까지 검색 결과 페이지를 아래로 스크롤하며
                # 새로 로딩된 '검색 결과 카드'만 누적합니다.
                search_rows = []
                search_row_map = {}
                scroll_diagnostics_3bm = []
                previous_count = 0
                stagnant_rounds = 0
                max_scroll_rounds = 24

                for scroll_round in range(max_scroll_rounds):
                    batch_rows = page.evaluate(
                        """
                        () => {
                            const out = [];
                            const seen = new Set();
                            const selectors = [
                                '[data-e2e="search-card-video-container"]',
                                '[data-e2e="search-video-item"]',
                                '[data-e2e="search-item"]',
                                'div[class*="DivItemContainer"]'
                            ];
                            const cards = [];
                            for (const sel of selectors) {
                                for (const el of document.querySelectorAll(sel)) {
                                    if (!cards.includes(el)) cards.push(el);
                                }
                            }

                            for (const card of cards) {
                                const links = Array.from(card.querySelectorAll('a[href*="/video/"]'));
                                if (!links.length) continue;

                                let a = null;
                                for (const link of links) {
                                    const href = String(link.href || link.getAttribute('href') || '').trim();
                                    if (/\\/video\\/\\d+/.test(href)) {
                                        a = link;
                                        break;
                                    }
                                }
                                if (!a) continue;

                                const href = String(a.href || a.getAttribute('href') || '').trim();
                                const m = href.match(/\\/video\\/(\\d+)/);
                                if (!m) continue;

                                const videoId = m[1];
                                if (seen.has(videoId)) continue;
                                seen.add(videoId);

                                let creator = '';
                                const creatorFromVideo = href.match(/tiktok\\.com\\/@([^/]+)\\/video\\//);
                                if (creatorFromVideo) creator = creatorFromVideo[1];

                                const text = String(
                                    card.innerText ||
                                    a.getAttribute('aria-label') ||
                                    a.getAttribute('title') ||
                                    ''
                                ).trim();

                                out.push({
                                    url: href,
                                    video_id: videoId,
                                    creator,
                                    title: text.slice(0, 300),
                                });
                            }
                            return out;
                        }
                        """
                    ) or []

                    # Sprint196-3CH: TikTok 카드 셀렉터가 일부 영상만 잡는 경우,
                    # 현재 화면에 실제 보이는 /video/ 링크를 추가 수집합니다.
                    _fallback_rows_3ch = cls._collect_visible_tiktok_video_anchors_3ch(page)
                    _batch_map_3ch = {
                        str((x or {}).get("video_id") or ""): dict(x or {})
                        for x in list(batch_rows or [])
                        if str((x or {}).get("video_id") or "")
                    }
                    for _x3ch in _fallback_rows_3ch:
                        _vid3ch = str((_x3ch or {}).get("video_id") or "")
                        if _vid3ch and _vid3ch not in _batch_map_3ch:
                            _batch_map_3ch[_vid3ch] = dict(_x3ch or {})
                    batch_rows = list(_batch_map_3ch.values())

                    for row in batch_rows:
                        vid = str((row or {}).get("video_id") or "").strip()
                        if vid and vid not in search_row_map:
                            search_row_map[vid] = dict(row or {})

                    search_rows = list(search_row_map.values())

                    _diag_round_3bm = {
                        "round": scroll_round + 1,
                        "cards_now": len(batch_rows),
                        "unique_total": len(search_rows),
                        "target": int(per_platform),
                        "stagnant_rounds_before": stagnant_rounds,
                    }
                    scroll_diagnostics_3bm.append(_diag_round_3bm)
                    print("[Sprint196-3BL Scroll]", _diag_round_3bm, flush=True)

                    if len(search_rows) >= int(per_platform):
                        break

                    if len(search_rows) <= previous_count:
                        stagnant_rounds += 1
                    else:
                        stagnant_rounds = 0
                    previous_count = len(search_rows)

                    # TikTok은 lazy-load가 늦을 수 있어 5회 연속 증가 없음까지 기다립니다.
                    if stagnant_rounds >= 5:
                        break

                    try:
                        # Sprint196-3BL:
                        # TikTok 검색 결과는 단순 body.scrollHeight 이동만으로
                        # 다음 batch가 로드되지 않는 경우가 있습니다.
                        # 마지막 검색카드를 화면에 붙인 뒤 wheel + End 키를 섞어
                        # 실제 사용자 스크롤과 비슷하게 추가 로딩을 유도합니다.
                        page.evaluate(
                            """
                            () => {
                                const cards = Array.from(
                                    document.querySelectorAll('a[href*="/video/"]')
                                );
                                const last = cards[cards.length - 1];
                                if (last) {
                                    last.scrollIntoView({behavior: 'instant', block: 'end'});
                                }
                                const scroller =
                                    document.scrollingElement ||
                                    document.documentElement ||
                                    document.body;
                                if (scroller) {
                                    scroller.scrollBy(0, Math.max(window.innerHeight * 1.8, 1400));
                                }
                            }
                            """
                        )

                        for _wheel3bl in range(3):
                            page.mouse.wheel(0, 2200)
                            page.wait_for_timeout(450)

                        try:
                            page.keyboard.press("End")
                        except Exception:
                            pass

                        # TikTok lazy-load/network 응답 시간을 충분히 줍니다.
                        page.wait_for_timeout(2200)

                    except Exception as scroll_exc:
                        print(
                            "[Sprint196-3BL Scroll] WARN",
                            type(scroll_exc).__name__,
                            str(scroll_exc)[:220],
                            flush=True,
                        )
                        break

                seen_ids = set()
                for item in search_rows:
                    href = str(item.get("url") or "").strip()
                    clean = href.split("?")[0].rstrip("/")
                    m = re.search(r"/video/(\d+)", clean)
                    if not m:
                        continue

                    video_id = m.group(1)
                    if video_id in seen_ids:
                        continue
                    seen_ids.add(video_id)

                    creator = str(item.get("creator") or "").strip()
                    _title3bk = re.sub(r"\s+", " ", str(item.get("title") or ""))[:240]
                    _views3bk = cls._parse_tiktok_view_count_3bk(_title3bk)
                    found.append({
                        "platform": "TikTok",
                        "title": _title3bk,
                        "view_count": _views3bk,
                        "view_count_text": (
                            f"{_views3bk:,}" if _views3bk > 0 else ""
                        ),
                        "url": clean,
                        "video_id": video_id,
                        "creator": creator,
                        "product": product_name,
                        "source": "tiktok_search_result_card_strict",
                        "candidate_url_verified": True,
                        "candidate_url_source": "tiktok_search_result_card_strict",
                        "search_query": query,
                    })
                    if len(found) >= int(per_platform):
                        break

                print("[Sprint196-3BL Search Cards]", {
                    "raw_cards": len(search_rows),
                    "accepted": len(found),
                    "product": product_name,
                    "search_url": current_url[:160],
                }, flush=True)

                # Sprint196-3BN:
                # 첫 검색이 15개 안팎에서 끝나도, 추가 검색어 변형으로 후보를 확장합니다.
                # 각 검색에서도 '검색 결과 카드 내부 /video/' 규칙만 사용합니다.
                _multi_query_diag_3bn = [{
                    "query": query,
                    "found_total": len(found),
                    "new_unique": len(found),
                }]
                _seen_multi_ids_3bn = {
                    str(x.get("video_id") or "")
                    for x in found
                    if str(x.get("video_id") or "")
                }

                for _query3bn in query_variants_3bn[1:]:
                    if len(found) >= int(per_platform):
                        break

                    _target3bn = "https://www.tiktok.com/search/video?" + urllib.parse.urlencode(
                        {"q": _query3bn}
                    )
                    try:
                        page.goto(_target3bn, wait_until="domcontentloaded", timeout=15000)
                    except Exception as _nav3bn:
                        print(
                            "[Sprint196-3BN MultiQuery] NAV_WARN",
                            _query3bn,
                            type(_nav3bn).__name__,
                            str(_nav3bn)[:180],
                            flush=True,
                        )

                    try:
                        page.wait_for_url(
                            re.compile(r"https://www\.tiktok\.com/search/video\?"),
                            timeout=7000,
                        )
                    except Exception:
                        pass
                    try:
                        page.wait_for_load_state("domcontentloaded", timeout=5000)
                    except Exception:
                        pass
                    try:
                        page.wait_for_timeout(1400)
                    except Exception:
                        pass

                    _before3bn = len(found)
                    _query_map3bn = {}

                    # 각 검색어에서는 최대 8회까지만 스크롤해 시간 폭증 방지.
                    for _round3bn in range(8):
                        _rows3bn = page.evaluate(
                            """
                            () => {
                                const out = [];
                                const seen = new Set();
                                const selectors = [
                                    '[data-e2e="search-card-video-container"]',
                                    '[data-e2e="search-video-item"]',
                                    '[data-e2e="search-item"]'
                                ];
                                const cards = [];
                                for (const sel of selectors) {
                                    for (const el of document.querySelectorAll(sel)) {
                                        if (!cards.includes(el)) cards.push(el);
                                    }
                                }
                                for (const card of cards) {
                                    const links = Array.from(card.querySelectorAll('a[href*="/video/"]'));
                                    if (!links.length) continue;
                                    let a = null;
                                    for (const link of links) {
                                        const href = String(link.href || link.getAttribute('href') || '').trim();
                                        if (/\\/video\\/\\d+/.test(href)) { a = link; break; }
                                    }
                                    if (!a) continue;
                                    const href = String(a.href || a.getAttribute('href') || '').trim();
                                    const m = href.match(/\\/video\\/(\\d+)/);
                                    if (!m) continue;
                                    const videoId = m[1];
                                    if (seen.has(videoId)) continue;
                                    seen.add(videoId);
                                    let creator = '';
                                    const cm = href.match(/tiktok\\.com\\/@([^/]+)\\/video\\//);
                                    if (cm) creator = cm[1];
                                    const text = String(
                                        card.innerText ||
                                        a.getAttribute('aria-label') ||
                                        a.getAttribute('title') ||
                                        ''
                                    ).trim();
                                    out.push({
                                        url: href,
                                        video_id: videoId,
                                        creator,
                                        title: text.slice(0, 300),
                                    });
                                }
                                return out;
                            }
                            """
                        ) or []

                        _fallback_rows_3ch = cls._collect_visible_tiktok_video_anchors_3ch(page)
                        _rows_map_3ch = {
                            str((x or {}).get("video_id") or ""): dict(x or {})
                            for x in list(_rows3bn or [])
                            if str((x or {}).get("video_id") or "")
                        }
                        for _x3ch in _fallback_rows_3ch:
                            _vid3ch = str((_x3ch or {}).get("video_id") or "")
                            if _vid3ch and _vid3ch not in _rows_map_3ch:
                                _rows_map_3ch[_vid3ch] = dict(_x3ch or {})
                        _rows3bn = list(_rows_map_3ch.values())

                        for _row3bn in _rows3bn:
                            _vid3bn = str((_row3bn or {}).get("video_id") or "").strip()
                            if _vid3bn:
                                _query_map3bn[_vid3bn] = dict(_row3bn or {})

                        if len(_query_map3bn) >= 15 or len(found) >= int(per_platform):
                            break

                        try:
                            page.evaluate(
                                """
                                () => {
                                    const els = Array.from(
                                        document.querySelectorAll('a[href*="/video/"]')
                                    );
                                    const last = els[els.length - 1];
                                    if (last) last.scrollIntoView({behavior:'instant', block:'end'});
                                    window.scrollBy(0, Math.max(window.innerHeight * 1.8, 1400));
                                }
                                """
                            )
                            page.mouse.wheel(0, 2600)
                            page.wait_for_timeout(1200)
                        except Exception:
                            break

                    for _row3bn in _query_map3bn.values():
                        _href3bn = str(_row3bn.get("url") or "").strip()
                        _clean3bn = _href3bn.split("?")[0].rstrip("/")
                        _m3bn = re.search(r"/video/(\d+)", _clean3bn)
                        if not _m3bn:
                            continue
                        _vid3bn = _m3bn.group(1)
                        if _vid3bn in _seen_multi_ids_3bn:
                            continue
                        _seen_multi_ids_3bn.add(_vid3bn)

                        _title3bn = re.sub(
                            r"\s+", " ", str(_row3bn.get("title") or "")
                        )[:240]
                        _views3bn = cls._parse_tiktok_view_count_3bk(_title3bn)

                        found.append({
                            "platform": "TikTok",
                            "title": _title3bn,
                            "view_count": _views3bn,
                            "view_count_text": f"{_views3bn:,}" if _views3bn > 0 else "",
                            "url": _clean3bn,
                            "video_id": _vid3bn,
                            "creator": str(_row3bn.get("creator") or "").strip(),
                            "product": product_name,
                            "source": "tiktok_multi_query_search_card_strict",
                            "candidate_url_verified": True,
                            "candidate_url_source": "tiktok_multi_query_search_card_strict",
                            "search_query": _query3bn,
                        })
                        if len(found) >= int(per_platform):
                            break

                    _multi_query_diag_3bn.append({
                        "query": _query3bn,
                        "new_unique": len(found) - _before3bn,
                        "found_total": len(found),
                    })

                    print("[Sprint196-3BN MultiQuery]", _multi_query_diag_3bn[-1], flush=True)

                # 3BM 화면 진단에서도 검색어별 확장 결과를 볼 수 있게 저장.
                try:
                    scroll_diagnostics_3bm.extend([
                        {
                            "round": f"Q{i+1}",
                            "cards_now": int(row.get("new_unique") or 0),
                            "unique_total": int(row.get("found_total") or 0),
                            "target": int(per_platform),
                            "stagnant_rounds_before": 0,
                            "query": str(row.get("query") or ""),
                        }
                        for i, row in enumerate(_multi_query_diag_3bn)
                    ])
                except Exception:
                    pass

            except Exception as dom_exc:
                print(
                    "[Sprint196-3AX Collect] DOM_WARN",
                    type(dom_exc).__name__,
                    str(dom_exc)[:240],
                    flush=True,
                )

            # Sprint196-3BO:
            # TikTok 웹 UI가 약 15개에서 고정되면 검색엔진 인덱스의 정확한
            # TikTok /video/ 주소로 부족한 후보를 보충합니다.
            _indexed_fill_3bo = {
                "items": [],
                "added_count": 0,
                "errors": [],
                "queries": [],
            }
            if False and len(found) < int(per_platform):
                _indexed_fill_3bo = cls._indexed_tiktok_fill_3bo(
                    product_name,
                    existing_items=found,
                    target_count=int(per_platform),
                )
                found.extend(list(_indexed_fill_3bo.get("items") or []))
                print("[Sprint196-3BO Indexed Fill]", {
                    "web_count": len(found) - int(_indexed_fill_3bo.get("added_count") or 0),
                    "indexed_added": int(_indexed_fill_3bo.get("added_count") or 0),
                    "total": len(found),
                    "target": int(per_platform),
                }, flush=True)

            # Sprint196-3BQ:
            # 제목/검색카드의 한글로는 한국 영상 여부를 판단하지 않습니다.
            # TikTok UI 한글/혼합 텍스트 오판을 막고, 실제 확보 영상의
            # 자막 + 나레이션을 분석한 뒤 제외합니다.
            _before_foreign_filter_3bp = len(found)
            _korean_excluded_3bp = 0

            # 1차 결과에서 실제 사용된 영문 표현을 뽑아 동일 제품 2차 확장 검색.
            _same_product_queries_3bp = cls._same_product_expansion_queries_3bp(
                product_name,
                found,
            )
            _seen_expand_ids_3bp = {
                str(x.get("video_id") or "")
                for x in found
                if str(x.get("video_id") or "")
            }
            _same_product_added_3bp = 0

            # 첫 검색과 겹치는 query는 건너뛰고, 확장 검색은 최대 4개.
            for _expand_query_3bp in _same_product_queries_3bp:
                if len(found) >= int(per_platform):
                    break
                if _expand_query_3bp.lower() in {
                    str(q or "").lower() for q in query_variants_3bn
                }:
                    continue

                _expand_target_3bp = (
                    "https://www.tiktok.com/search/video?"
                    + urllib.parse.urlencode({"q": _expand_query_3bp})
                )
                try:
                    page.goto(
                        _expand_target_3bp,
                        wait_until="domcontentloaded",
                        timeout=15000,
                    )
                except Exception as _expand_nav_exc_3bp:
                    print(
                        "[Sprint196-3BP SameProduct] NAV_WARN",
                        _expand_query_3bp,
                        type(_expand_nav_exc_3bp).__name__,
                        str(_expand_nav_exc_3bp)[:160],
                        flush=True,
                    )
                try:
                    page.wait_for_url(
                        re.compile(r"https://www\.tiktok\.com/search/video\?"),
                        timeout=7000,
                    )
                except Exception:
                    pass
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=5000)
                except Exception:
                    pass
                try:
                    page.wait_for_timeout(1400)
                except Exception:
                    pass

                _expand_rows_3bp = page.evaluate(
                    """
                    () => {
                        const out = [];
                        const seen = new Set();
                        const selectors = [
                            '[data-e2e="search-card-video-container"]',
                            '[data-e2e="search-video-item"]',
                            '[data-e2e="search-item"]'
                        ];
                        const cards = [];
                        for (const sel of selectors) {
                            for (const el of document.querySelectorAll(sel)) {
                                if (!cards.includes(el)) cards.push(el);
                            }
                        }
                        for (const card of cards) {
                            const links = Array.from(card.querySelectorAll('a[href*="/video/"]'));
                            let a = null;
                            for (const link of links) {
                                const href = String(link.href || link.getAttribute('href') || '').trim();
                                if (/\\/video\\/\\d+/.test(href)) { a = link; break; }
                            }
                            if (!a) continue;
                            const href = String(a.href || a.getAttribute('href') || '').trim();
                            const m = href.match(/\\/video\\/(\\d+)/);
                            if (!m || seen.has(m[1])) continue;
                            seen.add(m[1]);
                            const cm = href.match(/tiktok\\.com\\/@([^/]+)\\/video\\//);
                            const text = String(card.innerText || '').trim();
                            out.push({
                                url: href,
                                video_id: m[1],
                                creator: cm ? cm[1] : '',
                                title: text.slice(0, 300),
                            });
                        }
                        return out;
                    }
                    """
                ) or []

                _fallback_rows_3ch = cls._collect_visible_tiktok_video_anchors_3ch(page)
                _expand_map_3ch = {
                    str((x or {}).get("video_id") or ""): dict(x or {})
                    for x in list(_expand_rows_3bp or [])
                    if str((x or {}).get("video_id") or "")
                }
                for _x3ch in _fallback_rows_3ch:
                    _vid3ch = str((_x3ch or {}).get("video_id") or "")
                    if _vid3ch and _vid3ch not in _expand_map_3ch:
                        _expand_map_3ch[_vid3ch] = dict(_x3ch or {})
                _expand_rows_3bp = list(_expand_map_3ch.values())

                for _expand_row_3bp in _expand_rows_3bp:
                    _expand_vid_3bp = str(
                        (_expand_row_3bp or {}).get("video_id") or ""
                    ).strip()
                    if (
                        not _expand_vid_3bp
                        or _expand_vid_3bp in _seen_expand_ids_3bp
                    ):
                        continue

                    _expand_title_3bp = re.sub(
                        r"\s+",
                        " ",
                        str((_expand_row_3bp or {}).get("title") or ""),
                    )[:240]
                    _candidate_3bp = {
                        "platform": "TikTok",
                        "title": _expand_title_3bp,
                        "view_count": cls._parse_tiktok_view_count_3bk(
                            _expand_title_3bp
                        ),
                        "url": str(
                            (_expand_row_3bp or {}).get("url") or ""
                        ).split("?")[0].rstrip("/"),
                        "video_id": _expand_vid_3bp,
                        "creator": str(
                            (_expand_row_3bp or {}).get("creator") or ""
                        ).strip(),
                        "product": product_name,
                        "source": "same_product_expansion_3bp",
                        "candidate_url_verified": True,
                        "candidate_url_source": "tiktok_same_product_expansion",
                        "search_query": _expand_query_3bp,
                    }
                    # 3BQ: 제목만으로 한국 영상 판정 금지.
                    _seen_expand_ids_3bp.add(_expand_vid_3bp)
                    found.append(_candidate_3bp)
                    _same_product_added_3bp += 1
                    if len(found) >= int(per_platform):
                        break

            print("[Sprint196-3BP SameProduct]", {
                "queries": _same_product_queries_3bp,
                "added": _same_product_added_3bp,
                "korean_excluded": _korean_excluded_3bp,
                "total": len(found),
            }, flush=True)

            # Sprint196-3CI diagnostics only:
            # 현재 TikTok DOM이 실제로 몇 개의 /video/ 링크와 video_id를 가지고 있는지 기록합니다.
            _dom_diag_3ci = cls._tiktok_search_dom_diagnostics_3ci(page)
            _found_ids_3ci = [
                str((x or {}).get("video_id") or "").strip()
                for x in list(found or [])
                if str((x or {}).get("video_id") or "").strip()
            ]
            print("[Sprint196-3CI DOM DIAG]", _dom_diag_3ci, flush=True)
            print("[Sprint196-3CI FOUND BEFORE FILTER]", {
                "count": len(found),
                "unique_video_ids": list(dict.fromkeys(_found_ids_3ci))[:120],
            }, flush=True)

            # Sprint196-3BT:
            # 브라우저 DOM 단계에서 이미 /video/{id}를 확인해 video_id를 저장합니다.
            # 여기서 URL을 다시 파싱하다가 전체 후보가 0개가 되는 회귀를 제거합니다.
            _verified_found_3aq = []
            _seen_video_ids_3aq = set()
            _filter_diag_3bt = {
                "input_found": len(found),
                "missing_video_id": 0,
                "duplicate_video_id": 0,
                "accepted": 0,
            }

            for _row3aq in found:
                _row3aq = dict(_row3aq or {})
                _url3aq = str(_row3aq.get("url") or "").strip()
                _video_id3aq = str(_row3aq.get("video_id") or "").strip()

                if not _video_id3aq:
                    _m3aq = re.search(r"/video/(\d+)", _url3aq)
                    if _m3aq:
                        _video_id3aq = _m3aq.group(1)

                if not _video_id3aq or not _video_id3aq.isdigit():
                    _filter_diag_3bt["missing_video_id"] += 1
                    continue
                if _video_id3aq in _seen_video_ids_3aq:
                    _filter_diag_3bt["duplicate_video_id"] += 1
                    continue

                _seen_video_ids_3aq.add(_video_id3aq)
                _creator3bt = str(_row3aq.get("creator") or "").strip().lstrip("@")
                if _creator3bt:
                    _url3aq = f"https://www.tiktok.com/@{_creator3bt}/video/{_video_id3aq}"

                _row3aq["url"] = _url3aq
                _row3aq["video_id"] = _video_id3aq
                _row3aq["candidate_url_verified"] = True
                _row3aq["candidate_url_source"] = str(
                    _row3aq.get("candidate_url_source")
                    or "tiktok_search_result_card_dom_verified_id"
                )
                _verified_found_3aq.append(_row3aq)
                _filter_diag_3bt["accepted"] += 1

            print("[Sprint196-3CH Candidate Filter]", {
                **_filter_diag_3bt,
                "product": product_name,
                "search_url": current_url[:160],
            }, flush=True)
            print("[Sprint196-3CI AFTER FILTER]", {
                "count": len(_verified_found_3aq),
                "video_ids": [
                    str((x or {}).get("video_id") or "")
                    for x in list(_verified_found_3aq or [])
                ][:120],
            }, flush=True)

            _source_counts_3bx = {}
            for _row3bx in _verified_found_3aq:
                _src3bx = str(_row3bx.get("source") or "unknown")
                _source_counts_3bx[_src3bx] = int(_source_counts_3bx.get(_src3bx, 0)) + 1

            print("[Sprint196-3BX Strict Search Cards]", {
                "verified": len(_verified_found_3aq),
                "sources": _source_counts_3bx,
                "product": product_name,
            }, flush=True)

            ranked = cls.rank_tiktok_candidates(product_name, _verified_found_3aq)
            print("[Sprint196-3AJ Collect] RETURN", {
                "count": len(ranked),
                "url": current_url[:180],
            }, flush=True)

            return {
                "ok": bool(ranked),
                "product": product_name,
                "items": ranked,
                "counts": {"tiktok": len(ranked), "xiaohongshu": 0},
                "errors": [],
                "source_mode": "tiktok_overseas_en_zh_dedicated_profile",
                "current_url": current_url,
                "scroll_diagnostics": list(scroll_diagnostics_3bm),
                "scroll_final_unique": len(_verified_found_3aq) if '_verified_found_3aq' in locals() else len(found),
                "scroll_target": int(per_platform),
                "candidate_filter_diagnostics": dict(_filter_diag_3bt),
                "dom_diagnostics_3ci": dict(_dom_diag_3ci),
                "found_video_ids_before_filter_3ci": list(
                    dict.fromkeys(_found_ids_3ci)
                ),
                "verified_video_ids_after_filter_3ci": [
                    str((x or {}).get("video_id") or "")
                    for x in list(_verified_found_3aq or [])
                ],
                "strict_source_counts": dict(_source_counts_3bx),
                "query_variants": list(query_variants_3bn),
                "search_stage": _search_stage_3by,
                "reference_video_id": str((reference_item or {}).get("video_id") or ""),
                "reference_video_url": str((reference_item or {}).get("url") or ""),
                "english_search_keyword": str(query_variants_3bn[0] if query_variants_3bn else ""),
                "indexed_fill_added": int(_indexed_fill_3bo.get("added_count") or 0),
                "indexed_fill_queries": list(_indexed_fill_3bo.get("queries") or []),
                "indexed_fill_errors": list(_indexed_fill_3bo.get("errors") or []),
                "same_product_queries": list(_same_product_queries_3bp),
                "same_product_added": int(_same_product_added_3bp),
                "korean_excluded": int(_korean_excluded_3bp),
                "summary": (
                    f"{product_name} 관련 TikTok 후보 {len(ranked)}개를 수집·정리했습니다."
                    if ranked else
                    f"{product_name} 관련 TikTok 영상 후보를 찾지 못했습니다."
                ),
            }

        except Exception as exc:
            msg = f"{type(exc).__name__}: {exc}"
            print("[Sprint196-3AJ Collect] ERROR", msg[:400], flush=True)

            profile_busy = (
                "processsingleton" in msg.lower()
                or "user data directory is already in use" in msg.lower()
                or "target page, context or browser has been closed" in msg.lower()
            )
            return {
                "ok": False,
                "product": product_name,
                "items": [],
                "counts": {"tiktok": 0, "xiaohongshu": 0},
                "errors": [msg],
                "source_mode": "tiktok_overseas_en_zh_dedicated_profile",
                "summary": (
                    "이전 TikTok 자동수집 Chrome이 아직 열려 있습니다. 그 창을 닫은 뒤 다시 영상 수집을 눌러주세요."
                    if profile_busy
                    else "TikTok 자동 검색을 시작하지 못했습니다."
                ),
            }
        finally:
            if context is not None:
                try:
                    context.close()
                except Exception:
                    pass
            if pw is not None:
                try:
                    pw.stop()
                except Exception:
                    pass

    @classmethod
    def rank_tiktok_candidates(cls, product_name: str, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        URL/제목 기반의 1차 자동 선별입니다.
        실제 동일 상품 판정은 영상 프레임 분석 전이므로 '확정'이 아니라 가능성 등급으로 표시합니다.
        """
        kw = cls._keywords(product_name)
        phrases = [str(product_name or ""), str(kw.get("ko") or ""), str(kw.get("en") or "")]
        tokens = set()
        for phrase in phrases:
            for token in re.findall(r"[0-9A-Za-z가-힣]{2,}", phrase.lower()):
                if token not in {"the", "and", "for", "with", "video"}:
                    tokens.add(token)

        ranked = []
        seen_video = set()
        seen_title = set()
        for idx, raw in enumerate(items):
            row = dict(raw)
            url = str(row.get("url") or "").split("?")[0].rstrip("/")
            title = re.sub(r"\s+", " ", str(row.get("title") or "")).strip()
            video_id_match = re.search(r"/video/(\d+)", url)
            video_id = video_id_match.group(1) if video_id_match else url.lower()
            if not video_id or video_id in seen_video:
                continue
            seen_video.add(video_id)

            norm_title = re.sub(r"[^0-9a-z가-힣]+", "", title.lower())
            duplicate_title = bool(norm_title and norm_title in seen_title)
            if norm_title:
                seen_title.add(norm_title)

            if not int(row.get("view_count") or 0):
                _views3bk = cls._parse_tiktok_view_count_3bk(title)
                row["view_count"] = _views3bk
                row["view_count_text"] = f"{_views3bk:,}" if _views3bk > 0 else ""

            title_lower = title.lower()
            hits = sorted([tok for tok in tokens if tok in title_lower])
            exact_phrase = any(p and len(p) >= 3 and p.lower() in title_lower for p in phrases)
            score = 30
            if exact_phrase:
                score += 45
            score += min(30, len(hits) * 12)
            if title:
                score += 5
            if duplicate_title:
                score -= 35
            score = max(0, min(100, score))

            if duplicate_title:
                grade = "중복 제외"
                usable = False
            elif score >= 70:
                grade = "동일상품 가능성 높음"
                usable = True
            elif score >= 45:
                grade = "확인 필요"
                usable = True
            else:
                grade = "관련성 낮음"
                usable = False

            creator_match = re.search(r"tiktok\.com/@([^/]+)/video/", url, re.I)
            row.update({
                "url": url,
                "video_id": video_id,
                "creator": creator_match.group(1) if creator_match else "",
                "match_score": score,
                "match_grade": grade,
                "matched_keywords": hits,
                "auto_usable": usable,
                "duplicate_title": duplicate_title,
                "source_rank": idx + 1,
            })
            ranked.append(row)

        # Sprint196-3BK:
        # 관련성/사용가능 판정은 기존 그대로 유지하고,
        # 그 안에서 조회수가 높은 TikTok 영상을 먼저 보여줍니다.
        ranked.sort(
            key=lambda x: (
                bool(x.get("auto_usable")),
                int(x.get("view_count") or 0),
                int(x.get("match_score") or 0),
            ),
            reverse=True,
        )
        for i, row in enumerate(ranked, 1):
            row["screen_rank"] = i
        return ranked

    @classmethod
    def _bing(cls, query: str, count: int = 12) -> List[Dict[str, str]]:
        url = "https://www.bing.com/search?" + urllib.parse.urlencode(
            {"q": query, "count": max(10, int(count)), "setlang": "en-US"}
        )
        req = urllib.request.Request(
            url, headers={"User-Agent": cls.USER_AGENT, "Accept-Language": "en-US,en;q=0.8"}
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            body = response.read().decode("utf-8", errors="replace")
        rows = []
        for block in re.findall(r'<li[^>]+class="[^"]*\bb_algo\b[^"]*"[^>]*>(.*?)</li>', body, re.I | re.S):
            m = re.search(r'<h2[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', block, re.I | re.S)
            if not m:
                continue
            href = html.unescape(m.group(1)).strip()
            title = re.sub(r"<[^>]+>", "", html.unescape(m.group(2)))
            if href.startswith("http"):
                rows.append({"url": href, "title": re.sub(r"\s+", " ", title).strip()})
        return rows


    @classmethod
    def _duckduckgo(cls, query: str, count: int = 12) -> List[Dict[str, str]]:
        url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
        req = urllib.request.Request(
            url,
            headers={"User-Agent": cls.USER_AGENT, "Accept-Language": "en-US,en;q=0.8"},
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            body = response.read().decode("utf-8", errors="replace")
        rows = []
        for href, title in re.findall(
            r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
            body,
            flags=re.I | re.S,
        ):
            href = html.unescape(href)
            if "uddg=" in href:
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                href = urllib.parse.unquote((qs.get("uddg") or [href])[0])
            clean_title = re.sub(r"<[^>]+>", "", html.unescape(title))
            clean_title = re.sub(r"\s+", " ", clean_title).strip()
            if href.startswith("http"):
                rows.append({"url": href, "title": clean_title, "query": query})
            if len(rows) >= count:
                break
        return rows

    @classmethod
    def _search(cls, query: str, count: int = 12) -> tuple[List[Dict[str, str]], List[str]]:
        errors = []
        try:
            rows = cls._bing(query, count)
            if rows:
                return rows, errors
        except Exception as exc:
            errors.append(f"bing:{type(exc).__name__}:{exc}")

        try:
            rows = cls._duckduckgo(query, count)
            return rows, errors
        except Exception as exc:
            errors.append(f"duckduckgo:{type(exc).__name__}:{exc}")

        return [], errors

    @staticmethod
    def _platform_match(platform: str, url: str) -> bool:
        low = str(url or "").lower()
        if platform == "tiktok":
            return "tiktok.com/" in low and (
                "/video/" in low or "/@" in low
            )
        if platform == "xiaohongshu":
            return (
                "xiaohongshu.com/explore/" in low
                or "xiaohongshu.com/discovery/item/" in low
                or "xhslink.com/" in low
            )
        return False

    @classmethod
    def find(cls, product_name: str, per_platform: int = 10) -> Dict[str, Any]:
        """
        Sprint196-3Z
        TikTok/샤오홍슈의 인덱싱된 검색 결과를 검색엔진 결과에서 찾습니다.
        브라우저 로그인, persistent profile, CDP, live session을 사용하지 않습니다.
        """
        kw = cls._keywords(product_name)
        ko, en, zh = kw["ko"], kw["en"], kw["zh"]

        queries = {
            "tiktok": [
                f'site:tiktok.com/@ "{en or ko}"',
                f'site:tiktok.com/@ "{ko}"',
            ],
            "xiaohongshu": [
                f'site:xiaohongshu.com/explore "{zh or ko}"',
                f'site:xiaohongshu.com/explore "{ko}"',
            ],
        }

        items: List[Dict[str, Any]] = []
        errors: List[str] = []
        seen = set()

        for platform, platform_queries in queries.items():
            for query in platform_queries:
                rows, errs = cls._search(query, count=max(12, int(per_platform) * 2))
                errors.extend([f"{platform}:{x}" for x in errs])
                for row in rows:
                    url = str(row.get("url") or "").strip()
                    if not cls._platform_match(platform, url):
                        continue
                    key = url.split("?")[0].rstrip("/").lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    items.append({
                        "platform": "TikTok" if platform == "tiktok" else "샤오홍슈",
                        "title": str(row.get("title") or "").strip(),
                        "url": url,
                        "query": query,
                        "product": ko,
                        "source": "indexed_search",
                    })

        tiktok = [x for x in items if x["platform"] == "TikTok"][:int(per_platform)]
        xhs = [x for x in items if x["platform"] == "샤오홍슈"][:int(per_platform)]
        selected = tiktok + xhs

        return {
            "ok": bool(selected),
            "version": cls.VERSION,
            "product": ko,
            "items": selected,
            "counts": {"tiktok": len(tiktok), "xiaohongshu": len(xhs)},
            "errors": errors,
            "source_mode": "indexed_search",
            "summary": (
                f"{ko} 관련 인덱싱된 영상 후보 {len(selected)}개 발견"
                if selected else
                f"{ko} 관련 인덱싱된 영상 후보를 찾지 못했습니다."
            ),
        }

