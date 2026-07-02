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
    Sprint 6-4 image-first source engine.

    기본 검색 대상:
    1) Taobao 이미지 검색
    2) 1688 이미지 검색
    3) Taobao 텍스트 검색
    4) 1688 텍스트 검색
    5) TikTok 공개 검색

    Douyin은 기본 파이프라인에서 제외합니다.
    """

    def __init__(self):
        self.out_dir = EXPORTS_DIR / "studio_video_sources"
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def collect(self, product: Dict, max_candidates: int = 18) -> Dict:
        name = product.get("name") or product.get("product_name") or product.get("keyword") or "상품"
        keyword = product.get("keyword") or name
        taobao_kw = product.get("taobao_keyword") or keyword or name

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
                        note=self._platform_note(platform, row.get("search_type", "text")),
                        search_type=row.get("search_type", "text"),
                        image_url=image_url if row.get("search_type") == "image" else "",
                        image_path=image_asset.get("image_path", "") if row.get("search_type") == "image" else "",
                    )
                )
                rank += 1

        candidates = sorted(candidates, key=lambda x: x.score, reverse=True)[:max_candidates]
        for i, c in enumerate(candidates, 1):
            c.rank = i

        best = candidates[:6]
        folder = self.out_dir / self._safe_name(name)
        folder.mkdir(parents=True, exist_ok=True)

        live_collection = self._try_live_collect([asdict(x) for x in candidates])

        manifest = {
            "ok": True,
            "mode": "image-first-taobao-1688",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "product_name": name,
            "keyword": keyword,
            "image_url": image_url,
            "image_asset": image_asset,
            "coupang_product_id": coupang.get("product_id"),
            "summary": (
                "도우인은 기본 검색에서 제외하고, 쿠팡 대표이미지를 기반으로 "
                "타오바오/1688 동일상품 검색을 1순위로 시도합니다."
            ),
            "automation_status": self.automation_status(),
            "image_search": {
                "enabled": bool(image_asset.get("ok")),
                "image_url": image_url,
                "image_path": image_asset.get("image_path", ""),
                "priority": [
                    "taobao_image_upload",
                    "1688_image_upload",
                    "taobao_text_search",
                    "1688_text_search",
                    "tiktok_text_search",
                ],
                "note": image_asset.get("message"),
            },
            "live_collection": live_collection,
            "save_folder": str(folder),
            "best_candidates": [asdict(x) for x in best],
            "candidates": [asdict(x) for x in candidates],
            "how_to_use": [
                "이미지 검색 후보가 1순위입니다.",
                "타오바오/1688 이미지 업로드 결과에서 동일상품을 먼저 확인합니다.",
                "상품 상세의 主图视频/实拍/买家秀/공장실사 영상을 우선 사용합니다.",
                "이미지 검색이 부족하면 텍스트 검색 후보를 보조로 확인합니다.",
            ],
            "next_version_target": "동일상품 자동 클릭 후 主图视频 추출과 다운로드 자동화",
        }

        manifest_path = folder / "video_source_manifest.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
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

    def _build_seed_queries(self, name: str, keyword: str, taobao_kw: str, image_asset: Dict) -> Dict[str, List[Dict]]:
        cn_base = taobao_kw or name
        has_image = bool(image_asset.get("ok"))

        seeds: Dict[str, List[Dict]] = {
            "taobao": [],
            "1688": [],
            "tiktok": [],
        }

        if has_image:
            seeds["taobao"].extend([
                {
                    "title": f"{name} 타오바오 이미지 동일상품 검색",
                    "keyword": name,
                    "purpose": "쿠팡 이미지 기반 동일/유사 상품",
                    "score": 130,
                    "search_type": "image",
                },
                {
                    "title": f"{name} 타오바오 이미지 + 主图视频",
                    "keyword": f"{cn_base} 主图视频",
                    "purpose": "동일상품 상세 대표 영상",
                    "score": 122,
                    "search_type": "image",
                },
            ])
            seeds["1688"].extend([
                {
                    "title": f"{name} 1688 이미지 공급처 검색",
                    "keyword": name,
                    "purpose": "쿠팡 이미지 기반 공급처/공장 후보",
                    "score": 128,
                    "search_type": "image",
                },
                {
                    "title": f"{name} 1688 이미지 + 工厂实拍",
                    "keyword": f"{cn_base} 工厂 实拍",
                    "purpose": "공급처 실사/공장 영상",
                    "score": 118,
                    "search_type": "image",
                },
            ])

        seeds["taobao"].extend([
            {"title": f"{cn_base} 主图视频", "keyword": f"{cn_base} 主图视频", "purpose": "상세/대표 영상", "score": 96, "search_type": "text"},
            {"title": f"{cn_base} 实拍", "keyword": f"{cn_base} 实拍", "purpose": "실사 영상", "score": 93, "search_type": "text"},
            {"title": f"{cn_base} 买家秀", "keyword": f"{cn_base} 买家秀 视频", "purpose": "구매자 사용컷", "score": 87, "search_type": "text"},
            {"title": f"{cn_base} 同款", "keyword": f"{cn_base} 同款", "purpose": "동일/유사 상품", "score": 85, "search_type": "text"},
        ])

        seeds["1688"].extend([
            {"title": f"{cn_base} 批发视频", "keyword": f"{cn_base} 批发 视频", "purpose": "공급처 영상", "score": 90, "search_type": "text"},
            {"title": f"{cn_base} 工厂实拍", "keyword": f"{cn_base} 工厂 实拍", "purpose": "공장/공급처 실사", "score": 86, "search_type": "text"},
        ])

        seeds["tiktok"].extend([
            {"title": f"{name} TikTok 사용 영상", "keyword": f"{name} review", "purpose": "TikTok 공개 리뷰/사용 영상", "score": 72, "search_type": "text"},
        ])

        return seeds

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
                return "타오바오 이미지 검색입니다. 쿠팡 대표이미지로 동일/유사 상품을 먼저 찾습니다."
            return "타오바오는 상품 상세의 主图视频/实拍 영상을 우선 확인하세요."

        if platform == "1688":
            if search_type == "image":
                return "1688 이미지 검색입니다. 쿠팡 대표이미지로 공급처/공장 후보를 먼저 찾습니다."
            return "1688은 공급처 상세 영상과 공장 실사 후보 확인에 유용합니다."

        if platform == "tiktok":
            return "TikTok은 보조 검색입니다. 타오바오/1688 이미지 검색이 우선입니다."

        return ""

    def _safe_name(self, text: str) -> str:
        import re
        text = re.sub(r"[^\w가-힣\s-]", "", str(text))
        text = re.sub(r"\s+", "_", text).strip("_")
        return text[:48] or "video_sources"
