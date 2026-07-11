from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from urllib.parse import quote_plus
import json
import shutil

try:
    from config.settings import EXPORTS_DIR
except Exception:
    EXPORTS_DIR = Path("exports")

from modules.studio.image_asset_resolver import ImageAssetResolver


@dataclass
class VideoCandidate:
    rank: int
    platform: str
    title: str
    keyword: str
    purpose: str
    score: int
    search_url: str
    download_status: str = "수동 확인 필요"
    note: str = "공식 API/로그인 제한이 있어 현재는 후보 URL과 선택 기준을 제공합니다."
    search_type: str = "text"
    image_url: str = ""
    image_path: str = ""


class VideoSourcingEngine:
    """
    Sprint 49

    SearchKeywordEngine에서 생성한
    taobao_top10 / source_1688_top10 / douyin_top10을 그대로 사용한다.

    역할 분리:
    - SearchKeywordEngine: 검색어 품질 담당
    - VideoSourcingEngine: 검색 링크 후보 생성 담당
    """

    def __init__(self):
        self.out_dir = EXPORTS_DIR / "studio_video_sources"
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def collect(self, product: Dict, max_candidates: int = 30) -> Dict:
        name = (
            product.get("name")
            or product.get("product_name")
            or product.get("title")
            or product.get("keyword")
            or "상품"
        )

        keyword = product.get("keyword") or name

        taobao_kw = (
            product.get("taobao_keyword")
            or product.get("search_keyword")
            or product.get("main_keyword")
            or name
            or keyword
        )

        image_url = (
            product.get("image_url")
            or product.get("thumbnail")
            or product.get("product_image")
            or product.get("coupang_image_url")
            or ""
        )

        image_path = product.get("image_path") or ""
        coupang = product.get("coupang", {}) or {}

        image_asset = ImageAssetResolver().resolve(
            image_url=image_url,
            image_path=image_path,
            name=name,
        )

        seeds = self._build_seed_queries(
            product=product,
            name=name,
            keyword=keyword,
            taobao_kw=taobao_kw,
            image_asset=image_asset,
        )

        candidates: List[VideoCandidate] = []
        rank = 1

        for platform, rows in seeds.items():
            for row in rows:
                candidates.append(
                    VideoCandidate(
                        rank=rank,
                        platform=platform,
                        title=row["title"],
                        keyword=row["keyword"],
                        purpose=row["purpose"],
                        score=row["score"],
                        search_url=self._platform_url(
                            platform=platform,
                            keyword=row["keyword"],
                            search_type=row.get("search_type", "text"),
                        ),
                        note=self._platform_note(
                            platform,
                            row.get("search_type", "text"),
                        ),
                        search_type=row.get("search_type", "text"),
                        image_url=image_url if row.get("search_type") == "image" else "",
                        image_path=image_asset.get("image_path", "") if row.get("search_type") == "image" else "",
                    )
                )
                rank += 1

        candidates = self._dedupe_candidates(candidates)
        candidates = sorted(candidates, key=lambda x: x.score, reverse=True)[:max_candidates]

        for i, c in enumerate(candidates, 1):
            c.rank = i

        best = candidates[:6]

        folder = self.out_dir / self._safe_name(name)
        folder.mkdir(parents=True, exist_ok=True)

        live_collection = self._try_live_collect([asdict(x) for x in candidates])

        manifest = {
            "ok": True,
            "mode": "sprint49-keyword-top10-links",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "product_name": name,
            "keyword": keyword,
            "taobao_keyword": taobao_kw,
            "image_url": image_url,
            "image_asset": image_asset,
            "coupang_product_id": coupang.get("product_id"),
            "summary": (
                "SearchKeywordEngine의 타오바오/1688/도우인 Top10 검색어를 그대로 사용해 "
                "여러 플랫폼 검색 후보 링크를 생성합니다."
            ),
            "automation_status": self.automation_status(),
            "image_search": {
                "enabled": bool(image_asset.get("ok")),
                "image_url": image_url,
                "image_path": image_asset.get("image_path", ""),
                "priority": [
                    "taobao_image_upload",
                    "1688_image_upload",
                    "taobao_top10_text_search",
                    "1688_top10_text_search",
                    "douyin_top10_text_search",
                ],
                "note": image_asset.get("message"),
            },
            "live_collection": live_collection,
            "save_folder": str(folder),
            "best_candidates": [asdict(x) for x in best],
            "candidates": [asdict(x) for x in candidates],
            "how_to_use": [
                "이미지 검색 후보가 있으면 동일상품 확인용으로 먼저 사용합니다.",
                "그다음 타오바오 Top10 검색 링크를 확인합니다.",
                "1688 Top10은 공급처/공장/도매 후보 확인용입니다.",
                "도우인 Top10은 사용 장면·리뷰·바이럴 영상 참고용입니다.",
                "검색어에 实拍을 강제로 붙이지 않고, SearchKeywordEngine 결과를 그대로 사용합니다.",
            ],
            "next_version_target": "검색 결과 상품 상세 자동 클릭 후 主图视频/리뷰 영상 추출",
        }

        manifest_path = folder / "video_source_manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        manifest["manifest_path"] = str(manifest_path)
        return manifest

    def automation_status(self) -> Dict:
        try:
            from modules.studio.playwright_video_collector import PlaywrightVideoCollector

            return PlaywrightVideoCollector().status()
        except Exception as e:
            playwright = shutil.which("playwright") is not None
            return {
                "enabled": False,
                "playwright_cli_found": playwright,
                "browser_automation_ready": False,
                "message": f"Playwright 상태 확인 중 오류: {e}",
                "install_command": "python -m pip install playwright && python -m playwright install chromium",
                "enable_command": "set AUTO_SOURCE_LIVE=1",
            }

    def _try_live_collect(self, candidates: List[Dict]) -> Dict:
        try:
            from modules.studio.playwright_video_collector import PlaywrightVideoCollector

            return PlaywrightVideoCollector(headless=False).collect(candidates)
        except Exception as e:
            return {
                "ok": False,
                "results": [],
                "message": f"실제 웹 수집은 실행되지 않았습니다: {e}",
                "status": self.automation_status(),
            }

    def _build_seed_queries(
        self,
        product: Dict,
        name: str,
        keyword: str,
        taobao_kw: str,
        image_asset: Dict,
    ) -> Dict[str, List[Dict]]:
        has_image = bool(image_asset.get("ok"))

        seeds: Dict[str, List[Dict]] = {
            "taobao": [],
            "1688": [],
            "tiktok": [],
        }

        #if has_image:
            #seeds["taobao"].append(
                #{
                    #"title": f"{name} 타오바오 이미지 동일상품 검색",
                    #"keyword": name,
                    #"purpose": "쿠팡/업로드 이미지 기반 동일·유사 상품",
                    #"score": 130,
                    #"search_type": "image",
                #}
            #)

            #seeds["1688"].append(
                #{
                    #"title": f"{name} 1688 이미지 공급처 검색",
                    #"keyword": name,
                    #"purpose": "이미지 기반 공급처/공장 후보",
                    #"score": 128,
                    #"search_type": "image",
                #}
            #)

        taobao_rows = self._normalize_keyword_rows(
            product.get("taobao_top10"),
            fallback_keyword=product.get("taobao_keyword") or taobao_kw,
            platform="taobao",
        )

        source_1688_rows = self._normalize_keyword_rows(
            product.get("taobao_top10"),
            fallback_keyword=product.get("taobao_keyword") or taobao_kw,
            platform="1688",
        )

        douyin_rows = self._normalize_keyword_rows(
            product.get("douyin_top10"),
            fallback_keyword=product.get("douyin_keyword") or taobao_kw,
            platform="tiktok",
        )

        for row in taobao_rows:
            seeds["taobao"].append(
                {
                    "title": f"타오바오 {row['query']}",
                    "keyword": row["query"],
                    "purpose": row["purpose"],
                    "score": row["score"],
                    "search_type": "text",
                }
            )

        for row in source_1688_rows:
            seeds["1688"].append(
                {
                    "title": f"1688 {row['query']}",
                    "keyword": row["query"],
                    "purpose": row["purpose"],
                    "score": row["score"],
                    "search_type": "text",
                }
            )

        for row in douyin_rows:
            seeds["tiktok"].append(
                {
                    "title": f"도우인/TikTok {row['query']}",
                    "keyword": row["query"],
                    "purpose": row["purpose"],
                    "score": row["score"],
                    "search_type": "text",
                }
            )

        return seeds

    def _normalize_keyword_rows(
        self,
        rows,
        fallback_keyword: str,
        platform: str,
    ) -> List[Dict]:
        normalized: List[Dict] = []

        if isinstance(rows, list):
            for i, item in enumerate(rows):
                if not isinstance(item, dict):
                    continue

                query = str(item.get("query") or item.get("keyword") or "").strip()
                if not query:
                    continue

                normalized.append(
                    {
                        "rank": item.get("rank") or i + 1,
                        "query": self._clean_query(query),
                        "purpose": item.get("purpose") or "검색 후보",
                        "score": int(item.get("score") or max(50, 96 - i * 3)),
                    }
                )

        if normalized:
            return self._dedupe_rows(normalized)

        fallback_keyword = self._clean_query(fallback_keyword)

        if not fallback_keyword:
            return []

        if platform == "taobao":
            suffixes = ["", "家用", "多功能", "推荐", "开箱", "使用", "视频", "同款", "收纳", "新款"]
        elif platform == "1688":
            suffixes = ["批发", "厂家", "源头工厂", "一件代发", "跨境", "现货", "供应商", "新款", "家用", "多功能"]
        else:
            suffixes = ["使用", "测评", "推荐", "好物", "神器", "对比", "开箱", "效果", "视频", "教程"]

        for i, suffix in enumerate(suffixes):
            query = f"{fallback_keyword} {suffix}".strip()
            normalized.append(
                {
                    "rank": i + 1,
                    "query": self._clean_query(query),
                    "purpose": self._purpose(suffix),
                    "score": 90 - i * 3,
                }
            )

        return self._dedupe_rows(normalized)

    def _clean_query(self, query: str) -> str:
        query = str(query or "").strip()

        remove_words = [
            "实拍",
            "實拍",
            "실拍",
            "상세페이지",
            "대표이미지",
            "이미지",
        ]

        for word in remove_words:
            query = query.replace(word, " ")

        query = query.replace("+", " ")
        query = re_sub_spaces(query)
        return query

    def _dedupe_rows(self, rows: List[Dict]) -> List[Dict]:
        seen = set()
        result = []

        for row in rows:
            query = row.get("query", "").strip()
            if not query:
                continue
            if query in seen:
                continue

            seen.add(query)
            result.append(row)

        return result

    def _dedupe_candidates(self, candidates: List[VideoCandidate]) -> List[VideoCandidate]:
        seen = set()
        result = []

        for item in candidates:
            key = (item.platform, item.search_type, item.keyword, item.search_url)
            if key in seen:
                continue
            seen.add(key)
            result.append(item)

        return result

    def _platform_url(self, platform: str, keyword: str, search_type: str = "text") -> str:
        q = quote_plus(keyword or "")

        if platform == "taobao":
            if search_type == "image":
                return "https://s.taobao.com/search?tab=image"
            return f"https://s.taobao.com/search?q={q}"

        if platform == "1688":
            if search_type == "image":
                return "https://s.1688.com/selloffer/offer_search.htm"
            return f"https://s.1688.com/selloffer/offer_search.htm?keywords={q}"

        if platform == "tiktok":
            return f"https://www.tiktok.com/search?q={q}"

        return ""

    def _platform_note(self, platform: str, search_type: str = "text") -> str:
        if platform == "taobao":
            if search_type == "image":
                return "타오바오 이미지 검색입니다. 업로드한 대표 이미지로 동일/유사 상품을 먼저 찾습니다."
            return "타오바오 텍스트 검색입니다. 상품 상세의 대표 영상/리뷰 영상 후보를 확인하세요."

        if platform == "1688":
            if search_type == "image":
                return "1688 이미지 검색입니다. 업로드한 대표 이미지로 공급처/공장 후보를 먼저 찾습니다."
            return "1688 텍스트 검색입니다. 공급처/공장/도매 후보 확인에 유용합니다."

        if platform == "tiktok":
            return "도우인/TikTok 보조 검색입니다. 사용 장면·리뷰·바이럴 참고용입니다."

        return ""

    def _purpose(self, suffix):
        return {
            "": "기본 검색",
            "家用": "생활 사용 장면",
            "多功能": "기능 설명",
            "推荐": "추천 영상",
            "开箱": "언박싱",
            "使用": "사용 장면",
            "视频": "영상 후보",
            "同款": "동일/유사 상품",
            "收纳": "정리 장면",
            "新款": "신상품 후보",
            "批发": "도매 후보",
            "厂家": "제조사 후보",
            "源头工厂": "소스 공장 후보",
            "一件代发": "위탁/대행 후보",
            "跨境": "해외판매 후보",
            "现货": "재고 보유 후보",
            "供应商": "공급업체 후보",
            "测评": "리뷰 영상",
            "好物": "쇼핑쇼츠 후보",
            "神器": "후킹 강한 영상",
            "对比": "Before/After",
            "效果": "효과 장면",
            "教程": "사용법/튜토리얼",
        }.get(suffix, "검색 후보")

    def _safe_name(self, text: str) -> str:
        text = re_sub_safe_filename(text)
        return text[:48] or "video_sources"


def re_sub_spaces(text: str) -> str:
    import re

    text = re.sub(r"\s+", " ", str(text or ""))
    return text.strip()


def re_sub_safe_filename(text: str) -> str:
    import re

    text = re.sub(r"[^\w가-힣\s-]", "", str(text or ""))
    text = re.sub(r"\s+", "_", text).strip("_")
    return text