from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence


class ImagePoolBuilder:
    """
    Sprint102-1 Image Pool Builder

    역할:
    - ImageTagger / VisionAnalyzer / MultiImageCollector 결과에서 이미지 목록 수집
    - 이미지별 메타데이터를 정규화
    - hero / usage / detail / feature / review / comparison / cta 풀로 분류
    - 파일명, 태그, 역할, OCR, 설명, 출처를 함께 사용해 점수 계산
    - 기존 입력 객체를 변경하지 않고 독립 결과 반환
    """

    VERSION = "image-pool-builder-102-1"

    POOL_TYPES = (
        "hero",
        "usage",
        "detail",
        "feature",
        "review",
        "comparison",
        "cta",
    )

    _PATH_KEYS = (
        "path",
        "image_path",
        "file_path",
        "local_path",
        "saved_path",
        "output_path",
        "frame",
        "src",
        "url",
    )

    _LIST_KEYS = (
        "images",
        "items",
        "results",
        "tags",
        "tagged_images",
        "analyzed_images",
        "product_images",
        "main_images",
        "detail_images",
        "review_images",
        "ocr_images",
        "candidates",
    )

    _ROLE_KEYWORDS = {
        "hero": (
            "hero", "main", "primary", "대표", "메인", "썸네일",
            "front", "clean", "product shot", "packshot",
        ),
        "usage": (
            "usage", "use", "using", "lifestyle", "사용", "실사용",
            "사용중", "착용", "설치", "세척", "조리", "시연", "action",
        ),
        "detail": (
            "detail", "closeup", "close-up", "macro", "zoom", "확대",
            "디테일", "근접", "재질", "텍스처", "texture", "edge",
        ),
        "feature": (
            "feature", "benefit", "function", "기능", "장점", "특징",
            "수납", "방수", "내구", "접이", "미끄럼", "항균", "tpu",
        ),
        "review": (
            "review", "리뷰", "후기", "고객", "평점", "별점",
            "ocr", "testimonial", "comment",
        ),
        "comparison": (
            "comparison", "compare", "before", "after", "versus", "vs",
            "비교", "전후", "기존", "차이", "before after",
        ),
        "cta": (
            "cta", "purchase", "buy", "구매", "마무리", "엔딩",
            "ending", "final", "offer", "상품정보",
        ),
    }

    _SOURCE_BONUS = {
        "main": {"hero": 18, "cta": 10},
        "detail": {"detail": 16, "feature": 12, "usage": 4},
        "review": {"review": 22, "comparison": 4},
        "ocr": {"review": 20, "feature": 4},
        "usage": {"usage": 20, "feature": 5},
    }

    def build(
        self,
        tag_result: Any = None,
        vision_result: Any = None,
        image_input: Any = None,
        manifest_path: Any = "",
        review_images: Any = None,
        output_dir: Any = "",
        product_name: Any = "",
        project_id: Any = "",
        save_result: bool = True,
        max_per_pool: int = 50,
    ) -> Dict[str, Any]:
        result = self._empty_result(product_name=product_name, project_id=project_id)

        try:
            sources: List[tuple[str, Any]] = [
                ("tag", tag_result),
                ("vision", vision_result),
                ("input", image_input),
                ("review", review_images),
            ]

            manifest = self._load_json(manifest_path)
            if manifest:
                sources.append(("manifest", manifest))

            records: List[Dict[str, Any]] = []
            seen_paths: set[str] = set()

            for source_name, payload in sources:
                for item in self._extract_records(payload, source_name):
                    normalized = self._normalize_record(item, source_name)
                    path_key = self._path_key(normalized.get("path", ""))
                    if not path_key or path_key in seen_paths:
                        continue
                    seen_paths.add(path_key)
                    records.append(normalized)

            pools: Dict[str, List[Dict[str, Any]]] = {
                pool_type: [] for pool_type in self.POOL_TYPES
            }

            for index, record in enumerate(records, start=1):
                scored = self._score_record(record, index=index)
                record["pool_scores"] = {
                    key: scored[key]["score"] for key in self.POOL_TYPES
                }
                record["primary_pool"] = max(
                    self.POOL_TYPES,
                    key=lambda key: scored[key]["score"],
                )

                for pool_type in self.POOL_TYPES:
                    candidate = dict(record)
                    candidate.update(scored[pool_type])
                    candidate["type"] = pool_type
                    pools[pool_type].append(candidate)

            for pool_type in self.POOL_TYPES:
                pools[pool_type] = sorted(
                    pools[pool_type],
                    key=lambda item: (
                        float(item.get("score", 0)),
                        float(item.get("quality_score", 0)),
                        -int(item.get("source_index", 0)),
                    ),
                    reverse=True,
                )[: max(1, int(max_per_pool or 50))]

            non_empty_pool_count = sum(bool(items) for items in pools.values())
            top_candidates = {
                pool_type: (items[0] if items else {})
                for pool_type, items in pools.items()
            }

            result.update(
                ok=bool(records),
                ready=bool(records and non_empty_pool_count),
                status="built" if records else "empty",
                image_count=len(records),
                pool_count=non_empty_pool_count,
                images=records,
                image_pool=pools,
                pool_counts={pool_type: len(items) for pool_type, items in pools.items()},
                top_candidates=top_candidates,
            )

            if save_result:
                result["image_pool_path"] = self._save_result(
                    result=result,
                    output_dir=output_dir,
                    project_id=project_id,
                )

        except Exception as exc:
            result.update(
                ok=False,
                ready=False,
                status="failed",
                errors=[f"{type(exc).__name__}: {exc}"],
            )

        return result

    def _empty_result(self, product_name: Any = "", project_id: Any = "") -> Dict[str, Any]:
        return {
            "ok": False,
            "ready": False,
            "version": self.VERSION,
            "status": "not_run",
            "project_id": str(project_id or ""),
            "product_name": str(product_name or ""),
            "image_count": 0,
            "pool_count": 0,
            "images": [],
            "image_pool": {pool_type: [] for pool_type in self.POOL_TYPES},
            "pool_counts": {pool_type: 0 for pool_type in self.POOL_TYPES},
            "top_candidates": {pool_type: {} for pool_type in self.POOL_TYPES},
            "image_pool_path": "",
            "warnings": [],
            "errors": [],
        }

    def _extract_records(self, payload: Any, source_name: str) -> Iterable[Dict[str, Any]]:
        if payload is None:
            return []

        if isinstance(payload, (str, Path)):
            text = str(payload).strip()
            if not text:
                return []
            loaded = self._load_json(text)
            if loaded:
                return self._extract_records(loaded, source_name)
            return [{"path": text, "source": source_name}]

        if isinstance(payload, Sequence) and not isinstance(payload, (str, bytes, bytearray)):
            output: List[Dict[str, Any]] = []
            for item in payload:
                output.extend(self._extract_records(item, source_name))
            return output

        if not isinstance(payload, Mapping):
            return []

        direct_path = self._first_value(payload, self._PATH_KEYS)
        if direct_path:
            return [dict(payload)]

        output: List[Dict[str, Any]] = []
        for key in self._LIST_KEYS:
            value = payload.get(key)
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
                child_source = self._infer_source_from_key(key, source_name)
                for item in value:
                    output.extend(self._extract_records(item, child_source))

        if output:
            return output

        for key, value in payload.items():
            if isinstance(value, Mapping):
                output.extend(self._extract_records(value, self._infer_source_from_key(key, source_name)))
        return output

    def _normalize_record(self, item: Mapping[str, Any], source_name: str) -> Dict[str, Any]:
        path = str(self._first_value(item, self._PATH_KEYS) or "").strip()
        role_values = self._collect_text_values(
            item,
            (
                "role", "roles", "type", "image_type", "category",
                "tag", "tags", "label", "labels", "purpose",
                "scene_role", "recommended_role",
            ),
        )
        description_values = self._collect_text_values(
            item,
            (
                "description", "caption", "summary", "reason",
                "analysis", "visual_summary", "ocr_text", "text",
                "content", "alt", "title",
            ),
        )

        width = self._as_number(item.get("width") or item.get("image_width") or item.get("w"))
        height = self._as_number(item.get("height") or item.get("image_height") or item.get("h"))
        quality_score = self._as_number(
            item.get("quality_score")
            or item.get("score")
            or item.get("confidence")
            or item.get("visual_score")
        )

        source_type = self._infer_source_type(
            source_name=source_name,
            path=path,
            role_text=" ".join(role_values),
        )

        return {
            "path": path,
            "filename": Path(path).name if path else "",
            "source": source_name,
            "source_type": source_type,
            "roles": role_values,
            "description": " ".join(description_values).strip(),
            "width": width,
            "height": height,
            "quality_score": quality_score,
            "exists": Path(path).exists() if path and not self._is_url(path) else False,
            "raw": dict(item),
        }

    def _score_record(self, record: Dict[str, Any], index: int) -> Dict[str, Dict[str, Any]]:
        combined = self._normalize_text(
            " ".join(
                (
                    str(record.get("path", "")),
                    str(record.get("filename", "")),
                    " ".join(str(value) for value in record.get("roles", [])),
                    str(record.get("description", "")),
                )
            )
        )
        source_type = str(record.get("source_type", ""))
        quality_score = float(record.get("quality_score", 0) or 0)
        width = float(record.get("width", 0) or 0)
        height = float(record.get("height", 0) or 0)

        output: Dict[str, Dict[str, Any]] = {}
        for pool_type in self.POOL_TYPES:
            score = 30.0
            reasons: List[str] = []

            for keyword in self._ROLE_KEYWORDS[pool_type]:
                normalized_keyword = self._normalize_text(keyword)
                if normalized_keyword and normalized_keyword in combined:
                    score += 12.0
                    reasons.append(f"키워드 일치: {keyword}")

            source_bonus = self._SOURCE_BONUS.get(source_type, {}).get(pool_type, 0)
            if source_bonus:
                score += float(source_bonus)
                reasons.append(f"출처 가산점: {source_type}")

            if quality_score:
                quality_bonus = min(20.0, quality_score / 5.0)
                score += quality_bonus
                reasons.append(f"품질 점수 반영: {quality_score:g}")

            if width and height:
                ratio = width / height if height else 0
                if 0.72 <= ratio <= 1.35:
                    score += 4.0
                    reasons.append("제품 중심 구도에 적합")
                if pool_type in ("usage", "comparison") and ratio >= 1.0:
                    score += 3.0
                    reasons.append("상황 장면 구도에 적합")
                if pool_type in ("hero", "cta") and 0.75 <= ratio <= 1.1:
                    score += 3.0
                    reasons.append("대표 이미지 구도에 적합")

            if record.get("exists"):
                score += 3.0
                reasons.append("로컬 파일 확인")

            if pool_type == "cta" and source_type == "main":
                score += 5.0
            if pool_type == "review" and record.get("description"):
                score += min(8.0, len(str(record.get("description"))) / 40.0)
            if pool_type == "detail" and source_type == "detail":
                score += 4.0

            score = round(max(0.0, min(100.0, score)), 2)
            output[pool_type] = {
                "score": score,
                "reason": "; ".join(reasons[:5]) or "기본 이미지 후보",
                "source_index": index,
            }

        return output

    def _save_result(self, result: Dict[str, Any], output_dir: Any, project_id: Any) -> str:
        base_dir = Path(str(output_dir or "").strip() or "exports/image_pool")
        if str(project_id or "").strip() and not str(output_dir or "").strip():
            base_dir = base_dir / f"project_{project_id}"
        base_dir.mkdir(parents=True, exist_ok=True)

        output_path = base_dir / "image_pool_102_1.json"
        output_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return str(output_path)

    @staticmethod
    def _first_value(mapping: Mapping[str, Any], keys: Sequence[str]) -> Any:
        for key in keys:
            value = mapping.get(key)
            if value not in (None, "", [], {}):
                return value
        return ""

    @staticmethod
    def _collect_text_values(mapping: Mapping[str, Any], keys: Sequence[str]) -> List[str]:
        output: List[str] = []
        for key in keys:
            value = mapping.get(key)
            if isinstance(value, str) and value.strip():
                output.append(value.strip())
            elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
                output.extend(str(item).strip() for item in value if str(item).strip())
        return output

    @staticmethod
    def _infer_source_from_key(key: str, fallback: str) -> str:
        lowered = key.lower()
        if "review" in lowered or "리뷰" in lowered:
            return "review"
        if "ocr" in lowered:
            return "ocr"
        if "main" in lowered or "hero" in lowered:
            return "main"
        if "detail" in lowered:
            return "detail"
        if "usage" in lowered or "lifestyle" in lowered:
            return "usage"
        return fallback

    @staticmethod
    def _infer_source_type(source_name: str, path: str, role_text: str) -> str:
        text = f"{source_name} {path} {role_text}".lower()
        if any(token in text for token in ("review", "리뷰", "후기")):
            return "review"
        if "ocr" in text:
            return "ocr"
        if any(token in text for token in ("usage", "lifestyle", "사용", "실사용")):
            return "usage"
        if any(token in text for token in ("detail", "상세", "closeup", "close-up")):
            return "detail"
        if any(token in text for token in ("main", "hero", "대표", "메인")):
            return "main"
        return "unknown"

    @staticmethod
    def _load_json(path_or_value: Any) -> Dict[str, Any]:
        if isinstance(path_or_value, Mapping):
            return dict(path_or_value)
        text = str(path_or_value or "").strip()
        if not text:
            return {}
        path = Path(text)
        if not path.is_file():
            return {}
        try:
            loaded = json.loads(path.read_text(encoding="utf-8-sig"))
            return dict(loaded) if isinstance(loaded, Mapping) else {}
        except (OSError, UnicodeError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _path_key(path: Any) -> str:
        return str(path or "").strip().replace("\\", "/").lower()

    @staticmethod
    def _normalize_text(value: Any) -> str:
        text = str(value or "").lower()
        text = re.sub(r"[_\-./\\]+", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def _as_number(value: Any) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _is_url(value: str) -> bool:
        return value.startswith(("http://", "https://"))


__all__ = ["ImagePoolBuilder"]