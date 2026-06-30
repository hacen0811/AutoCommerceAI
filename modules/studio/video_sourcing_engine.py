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
except Exception:  # pragma: no cover
    EXPORTS_DIR = Path("exports")


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


class VideoSourcingEngine:
    """Create practical Taobao/1688/Douyin video-source candidates.

    v3.9 목표는 '검색 URL만 제공'에서 한 단계 더 나아가 쇼츠 제작에 쓸
    후보 목록, 추천 점수, 저장 폴더, 다음 작업을 한 번에 만들어주는 것입니다.
    도우인/타오바오는 로그인/지역/봇 차단이 잦기 때문에, 실제 자동 수집은
    Playwright 설치 및 로그인 세션이 준비된 경우에만 확장하도록 안전하게 설계했습니다.
    """

    def __init__(self):
        self.out_dir = EXPORTS_DIR / "studio_video_sources"
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def collect(self, product: Dict, max_candidates: int = 18) -> Dict:
        name = product.get("name") or product.get("keyword") or "상품"
        keyword = product.get("keyword") or name
        taobao_kw = product.get("taobao_keyword") or name
        douyin_kw = product.get("douyin_keyword") or name
        coupang = product.get("coupang", {}) or {}

        seeds = self._build_seed_queries(name, keyword, taobao_kw, douyin_kw)
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
                        search_url=self._platform_url(platform, row["keyword"]),
                        note=self._platform_note(platform),
                    )
                )
                rank += 1

        candidates = sorted(candidates, key=lambda x: x.score, reverse=True)[:max_candidates]
        for i, c in enumerate(candidates, 1):
            c.rank = i

        best = candidates[:5]
        folder = self.out_dir / self._safe_name(name)
        folder.mkdir(parents=True, exist_ok=True)
        live_collection = self._try_live_collect([asdict(x) for x in candidates])

        manifest = {
            "ok": True,
            "mode": "candidate-search-plus-live-ready",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "product_name": name,
            "keyword": keyword,
            "coupang_product_id": coupang.get("product_id"),
            "summary": "타오바오/1688/도우인 영상 후보를 추천하고, Playwright 설정 시 실제 검색 결과 수집까지 시도합니다.",
            "automation_status": self.automation_status(),
            "live_collection": live_collection,
            "save_folder": str(folder),
            "best_candidates": [asdict(x) for x in best],
            "candidates": [asdict(x) for x in candidates],
            "how_to_use": [
                "TOP 후보 URL을 클릭합니다.",
                "상품 사용 장면이 있는 세로 영상 또는 상세 영상 위주로 확인합니다.",
                "다운로드 가능한 영상은 videos/source_candidates 폴더에 저장합니다.",
                "저장한 영상을 원본 영상에 업로드하면 Vision/CapCut/대본 생성이 이어집니다.",
            ],
            "next_version_target": "수집된 실제 후보 미리보기/선택/다운로드 자동화",
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

    def _build_seed_queries(self, name: str, keyword: str, taobao_kw: str, douyin_kw: str) -> Dict[str, List[Dict]]:
        cn_base = taobao_kw or name
        kr_base = douyin_kw or name
        return {
            "douyin": [
                {"title": f"{kr_base} 실사용 영상", "keyword": f"{kr_base} 使用 视频", "purpose": "사용 장면", "score": 98},
                {"title": f"{kr_base} 추천/후기", "keyword": f"{kr_base} 推荐 好物", "purpose": "후기형 쇼츠", "score": 94},
                {"title": f"{kr_base} 언박싱", "keyword": f"{kr_base} 开箱", "purpose": "언박싱", "score": 88},
                {"title": f"{kr_base} 비교", "keyword": f"{kr_base} 对比", "purpose": "Before/After", "score": 84},
                {"title": f"{kr_base} 꿀팁", "keyword": f"{kr_base} 技巧", "purpose": "생활꿀팁형", "score": 80},
            ],
            "taobao": [
                {"title": f"{cn_base} 主图视频", "keyword": f"{cn_base} 主图视频", "purpose": "상세/대표 영상", "score": 96},
                {"title": f"{cn_base} 实拍", "keyword": f"{cn_base} 实拍", "purpose": "실사 영상", "score": 93},
                {"title": f"{cn_base} 买家秀", "keyword": f"{cn_base} 买家秀 视频", "purpose": "구매자 사용컷", "score": 87},
                {"title": f"{cn_base} 同款", "keyword": f"{cn_base} 同款", "purpose": "동일/유사 상품", "score": 85},
                {"title": f"{cn_base} 爆款", "keyword": f"{cn_base} 爆款 视频", "purpose": "인기 상품 영상", "score": 82},
            ],
            "1688": [
                {"title": f"{cn_base} 批发视频", "keyword": f"{cn_base} 批发 视频", "purpose": "공급처 영상", "score": 90},
                {"title": f"{cn_base} 工厂实拍", "keyword": f"{cn_base} 工厂 实拍", "purpose": "공장/공급처 실사", "score": 86},
                {"title": f"{cn_base} 现货", "keyword": f"{cn_base} 现货 视频", "purpose": "재고/판매 영상", "score": 78},
            ],
        }

    def _platform_url(self, platform: str, keyword: str) -> str:
        q = quote_plus(keyword)
        if platform == "douyin":
            return f"https://www.douyin.com/search/{q}"
        if platform == "taobao":
            return f"https://s.taobao.com/search?q={q}"
        if platform == "1688":
            return f"https://s.1688.com/selloffer/offer_search.htm?keywords={q}"
        return ""

    def _platform_note(self, platform: str) -> str:
        if platform == "douyin":
            return "도우인은 로그인/지역 제한이 있을 수 있습니다. 세로 실사용 영상 후보를 우선 확인하세요."
        if platform == "taobao":
            return "타오바오는 상품 상세의 主图视频/实拍 영상을 우선 확인하세요."
        if platform == "1688":
            return "1688은 공급처 상세 영상과 공장 실사 후보 확인에 유용합니다."
        return ""

    def _safe_name(self, text: str) -> str:
        import re
        text = re.sub(r"[^\w가-힣\s-]", "", str(text))
        text = re.sub(r"\s+", "_", text).strip("_")
        return text[:48] or "video_sources"
