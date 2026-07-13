from __future__ import annotations

from typing import Any, Dict, List

from modules.pipeline.real_vision_runner import RealVisionRunner
from modules.video.product_relevance_engine import (
    ProductRelevanceEngine,
)


class BatchAnalyzer:
    """
    Sprint 59 Batch Analyzer

    역할:
    - 소스 영상 후보를 프로젝트에 하나씩 임시 연결
    - RealVisionRunner로 영상 분석
    - ProductRelevanceEngine으로 상품 일치도 계산
    - 기존 project.video_path는 분석 후 원상 복구
    - 저장소 DB는 직접 변경하지 않음
    """

    ANALYZER_VERSION = "batch-analyzer-59-2"

    def analyze(
        self,
        project,
        video_items: List[Dict[str, Any]],
        limit: int = 5,
        sample_count: int = 6,
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []

        original_video = getattr(
            project,
            "video_path",
            "",
        )

        product_name = (
            getattr(project, "product_name", "")
            or getattr(project, "title", "")
            or ""
        )

        project_keyword = (
            getattr(project, "keyword", "")
            or ""
        )

        runner = RealVisionRunner()
        relevance_engine = ProductRelevanceEngine()

        try:
            for item in (video_items or [])[:limit]:
                if not isinstance(item, dict):
                    continue

                try:
                    video_path = (
                        item.get("path")
                        or item.get("video_path")
                        or item.get("local_path")
                        or ""
                    )

                    project.video_path = video_path

                    real_vision = runner.run(
                        project,
                        sample_count=sample_count,
                        use_yolo=True,
                        use_paddle=True,
                    )

                    candidate_keyword = (
                        item.get("keyword")
                        or item.get("search_query")
                        or item.get("query")
                        or project_keyword
                    )

                    product_relevance = (
                        relevance_engine.analyze(
                            candidate=item,
                            product_name=product_name,
                            keyword=candidate_keyword,
                            real_vision=real_vision,
                        )
                    )

                    enriched_source = dict(item)

                    enriched_source["real_vision"] = (
                        real_vision
                    )

                    enriched_source[
                        "product_relevance"
                    ] = product_relevance

                    results.append(
                        {
                            "analyzer_version": (
                                self.ANALYZER_VERSION
                            ),
                            "source": enriched_source,
                            "summary": real_vision.get(
                                "summary"
                            ),
                            "status": real_vision.get(
                                "status",
                                {},
                            ),
                            "smart_cut": real_vision.get(
                                "smart_cut",
                                {},
                            ),
                            "caption_safe": (
                                real_vision.get(
                                    "caption_safe",
                                    {},
                                )
                            ),
                            "product_relevance": (
                                product_relevance
                            ),
                            "real_vision": real_vision,
                            "ok": bool(
                                real_vision.get(
                                    "ok",
                                    False,
                                )
                            ),
                        }
                    )

                except Exception as exc:
                    results.append(
                        {
                            "analyzer_version": (
                                self.ANALYZER_VERSION
                            ),
                            "source": dict(item),
                            "product_relevance": {
                                "version": (
                                    ProductRelevanceEngine
                                    .ENGINE_VERSION
                                ),
                                "score": 0,
                                "grade": "very_low",
                                "matched_keywords": [],
                                "title_match": False,
                                "ocr_match": False,
                                "visual_match": False,
                                "text_score": 0,
                                "vision_score": 0,
                                "reason": (
                                    "영상 분석 중 오류가 발생해 "
                                    "상품 일치도를 계산하지 못했습니다."
                                ),
                            },
                            "ok": False,
                            "error": str(exc),
                        }
                    )

        finally:
            project.video_path = original_video

        return results