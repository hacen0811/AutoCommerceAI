import json
from pathlib import Path

from modules.product.coupang_product_engine import CoupangProductEngine
from modules.product.search_keyword_engine import SearchKeywordEngine
from modules.product.product_title_engine import ProductTitleEngine


class ProductEngine:
    """
    Product Engine 2.0
    - 쿠팡 URL 분석
    - 프로젝트 payload 생성
    - 타오바오/도우인 검색어 생성
    - 작업 큐 생성
    """

    def build_from_coupang(self, coupang_url, product_name="", price="", category="", image_url="", partner_url="", manual_product_name=""):
        parsed = CoupangProductEngine().parse(coupang_url)

        raw_name = (manual_product_name or product_name or parsed.get("guessed_product_name") or "").strip()
        title_data = ProductTitleEngine().improve(product_name or parsed.get("guessed_product_name") or "", manual_name=raw_name)
        name = title_data.get("short_title") or raw_name or "쿠팡 추천상품"

        keyword_data = SearchKeywordEngine().generate(title_data.get("clean_title") or name, category=category)

        project_payload = {
            "product_name": name,
            "coupang_url": parsed.get("clean_url") or coupang_url,
            "partner_url": partner_url.strip(),
            "taobao_url": "",
            "douyin_url": "",
            "image_url": image_url.strip(),
            "price": price.strip(),
            "category": category.strip(),
            "keyword": keyword_data.get("comment_keyword") or "정보",
            "data": {
                "product_engine": {
                    "parsed": parsed,
                    "title": title_data,
                    "keywords": keyword_data,
                    "task_queue": self.task_queue(keyword_data),
                }
            }
        }

        return {
            "parsed": parsed,
            "keywords": keyword_data,
            "project_payload": project_payload,
            "task_queue": self.task_queue(keyword_data),
        }

    def task_queue(self, keyword_data):
        return [
            {
                "step": 1,
                "title": "쿠팡파트너스 링크 생성",
                "status": "대기",
                "memo": "쿠팡 원본 링크를 파트너스 링크로 변환",
            },
            {
                "step": 2,
                "title": "타오바오 영상/이미지 검색",
                "status": "대기",
                "query": keyword_data.get("taobao_keyword", ""),
            },
            {
                "step": 3,
                "title": "도우인 영상 검색",
                "status": "대기",
                "query": keyword_data.get("douyin_keyword", ""),
            },
            {
                "step": 4,
                "title": "원본 영상 업로드",
                "status": "대기",
                "memo": "다운로드한 원본 영상을 영상관리에서 업로드",
            },
            {
                "step": 5,
                "title": "Real Vision Runner 실행",
                "status": "대기",
                "memo": "후킹컷/썸네일/자막위치/CapCut 편집안 생성",
            },
            {
                "step": 6,
                "title": "Content Factory 생성",
                "status": "대기",
                "memo": "쇼츠/릴스/인포크/블로그 문구 생성",
            },
        ]

    def save_plan(self, built):
        out_dir = Path("exports/product_plans")
        out_dir.mkdir(parents=True, exist_ok=True)
        product_name = built.get("project_payload", {}).get("product_name", "product")
        safe = "".join(c for c in product_name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        if not safe:
            safe = "product"
        path = out_dir / f"{safe}_product_plan.json"
        path.write_text(json.dumps(built, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path)
