from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from modules.image_ai.multi_image_collector import MultiImageCollector
from modules.product.coupang_product_engine import CoupangProductEngine
from modules.product.coupang_review_collector import CoupangReviewCollector
from modules.studio.coupang_metadata_extractor import CoupangMetadataExtractor
from modules.product.search_keyword_engine import SearchKeywordEngine
from modules.product.product_title_engine import ProductTitleEngine


class ProductEngine:
    """
    Product Engine Sprint93-1

    - 쿠팡 URL 분석
    - 쿠팡 상품 메타데이터 추출
    - 쿠팡 대표/상세 이미지 다중 수집
    - 쿠팡 리뷰 자동 수집
    - 프로젝트 payload 생성
    - 타오바오/도우인 검색어 생성
    - 작업 큐 생성

    안전 원칙:
    - 이미지 또는 리뷰 수집 실패 시 기존 파이프라인은 계속 실행
    - 기존 반환 구조 유지
    - Sprint93-1 다중 이미지 필드만 추가
    """

    ENGINE_VERSION = "product-engine-93-1"

    def build_from_coupang(
        self,
        coupang_url,
        product_name="",
        price="",
        category="",
        image_url="",
        partner_url="",
        manual_product_name="",
        project_id="",
        collect_product_images=True,
        max_product_images=40,
    ):
        parsed = CoupangProductEngine().parse(coupang_url)

        clean_coupang_url = (
            parsed.get("clean_url")
            or parsed.get("coupang_url")
            or coupang_url
            or ""
        )

        metadata = CoupangMetadataExtractor().extract(
            coupang_url=clean_coupang_url,
            product_name=product_name,
            price=price,
            category=category,
            image_url=image_url,
            partner_url=partner_url,
            fetch=True,
        )

        resolved_image_url = (
            str(image_url or "").strip()
            or metadata.get("image_url", "")
            or parsed.get("image_url", "")
        )

        resolved_price = (
            str(price or "").strip()
            or str(metadata.get("price", "") or "").strip()
            or str(parsed.get("price", "") or "").strip()
        )

        resolved_category = (
            str(category or "").strip()
            or str(metadata.get("category", "") or "").strip()
            or str(parsed.get("category", "") or "").strip()
        )

        raw_name = (
            manual_product_name
            or product_name
            or metadata.get("product_name")
            or parsed.get("guessed_product_name")
            or ""
        ).strip()

        title_data = ProductTitleEngine().improve(
            (
                product_name
                or metadata.get("product_name")
                or parsed.get("guessed_product_name")
                or ""
            ),
            manual_name=raw_name,
        )

        name = (
            title_data.get("short_title")
            or raw_name
            or "쿠팡 추천상품"
        )

        keyword_data = SearchKeywordEngine().generate(
            title_data.get("clean_title") or name,
            category=resolved_category,
        )

        multi_image_result = self._collect_product_images(
            enabled=collect_product_images,
            coupang_url=clean_coupang_url,
            project_id=project_id,
            product_name=name,
            main_image_url=resolved_image_url,
            max_images=max_product_images,
        )

        product_images = multi_image_result.get("images", [])
        if not isinstance(product_images, list):
            product_images = []

        if product_images:
            first_image_path = str(product_images[0].get("path") or "")
        else:
            first_image_path = ""

        review_result = self._collect_reviews(
            coupang_url=clean_coupang_url,
        )

        reviews = review_result.get("reviews", [])
        if not isinstance(reviews, list):
            reviews = []

        review_count = int(
            review_result.get("review_count", len(reviews))
            or 0
        )
        review_source = review_result.get("source", "coupang_page")
        review_collect_status = review_result.get("status", "empty")
        task_queue = self.task_queue(keyword_data)

        project_payload = {
            "product_name": name,
            "coupang_url": (
                parsed.get("coupang_url")
                or clean_coupang_url
            ),
            "partner_url": (
                str(partner_url or "").strip()
                or parsed.get("partner_url")
                or clean_coupang_url
            ),
            "taobao_url": "",
            "douyin_url": "",
            "image_url": resolved_image_url,
            "product_image_path": first_image_path,
            "product_images": product_images,
            "product_image_count": len(product_images),
            "product_image_dir": multi_image_result.get("output_dir", ""),
            "product_image_manifest": multi_image_result.get("manifest_path", ""),
            "product_image_collect_status": multi_image_result.get("status", "not_run"),
            "price": resolved_price,
            "category": resolved_category,
            "keyword": keyword_data.get("comment_keyword") or "정보",
            "reviews": reviews,
            "review_count": review_count,
            "review_source": review_source,
            "review_collect_status": review_collect_status,
            "data": {
                "product_engine": {
                    "engine_version": self.ENGINE_VERSION,
                    "parsed": parsed,
                    "metadata": metadata,
                    "title": title_data,
                    "keywords": keyword_data,
                    "multi_image_collector": multi_image_result,
                    "product_images": product_images,
                    "product_image_count": len(product_images),
                    "product_image_path": first_image_path,
                    "reviews": reviews,
                    "review_count": review_count,
                    "review_source": review_source,
                    "review_collect_status": review_collect_status,
                    "review_collector": review_result,
                    "task_queue": task_queue,
                    "debug_delivery": {
                        "product_name": name,
                        "coupang_url": clean_coupang_url,
                        "partner_url": (
                            str(partner_url or "").strip()
                            or parsed.get("partner_url")
                            or clean_coupang_url
                        ),
                        "image_url": resolved_image_url,
                        "product_image_count": len(product_images),
                        "product_image_collect_status": multi_image_result.get("status", "not_run"),
                        "review_count": review_count,
                        "review_collect_status": review_collect_status,
                    },
                }
            },
        }

        return {
            "parsed": parsed,
            "metadata": metadata,
            "keywords": keyword_data,
            "multi_image_collector": multi_image_result,
            "product_images": product_images,
            "product_image_count": len(product_images),
            "product_image_path": first_image_path,
            "product_image_dir": multi_image_result.get("output_dir", ""),
            "product_image_manifest": multi_image_result.get("manifest_path", ""),
            "product_image_collect_status": multi_image_result.get("status", "not_run"),
            "reviews": reviews,
            "review_count": review_count,
            "review_source": review_source,
            "review_collect_status": review_collect_status,
            "review_collector": review_result,
            "project_payload": project_payload,
            "task_queue": task_queue,
        }

    def _collect_product_images(
        self,
        enabled: bool,
        coupang_url: str,
        project_id: Any,
        product_name: str,
        main_image_url: str,
        max_images: int,
    ) -> Dict[str, Any]:
        if not enabled:
            return {
                "ok": False,
                "ready": False,
                "version": MultiImageCollector.VERSION,
                "status": "disabled",
                "images": [],
                "image_count": 0,
                "output_dir": "",
                "manifest_path": "",
                "warnings": [],
                "errors": [],
            }

        try:
            return MultiImageCollector().collect(
                coupang_url=coupang_url,
                project_id=project_id,
                product_name=product_name,
                main_image_url=main_image_url,
                max_images=max_images,
                timeout=20,
            )
        except Exception as exc:
            return {
                "ok": False,
                "ready": False,
                "version": MultiImageCollector.VERSION,
                "status": "error",
                "images": [],
                "image_count": 0,
                "output_dir": "",
                "manifest_path": "",
                "warnings": [],
                "errors": [f"{type(exc).__name__}: {exc}"],
            }

    def _collect_reviews(
        self,
        coupang_url: str,
    ) -> Dict[str, Any]:
        try:
            return CoupangReviewCollector().collect(
                coupang_url=coupang_url,
                max_reviews=50,
                timeout=15,
            )
        except Exception as exc:
            return {
                "collector_version": "coupang-review-collector-66-1",
                "ok": False,
                "status": "error",
                "source": "coupang_page",
                "review_count": 0,
                "reviews": [],
                "error": str(exc),
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

        product_name = built.get("project_payload", {}).get(
            "product_name",
            "product",
        )

        safe = "".join(
            character
            for character in product_name
            if character.isalnum() or character in (" ", "_", "-")
        ).strip().replace(" ", "_")

        if not safe:
            safe = "product"

        path = out_dir / f"{safe}_product_plan.json"
        path.write_text(
            json.dumps(
                built,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return str(path)