from __future__ import annotations

import json
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


class ImageTagger:
    """
    Sprint93-3 Image Tagger

    역할:
    - Sprint93-2 vision_analysis.json 또는 분석 결과 dict를 입력받음
    - 이미지의 구조 정보, 수집 타입, 파일명, OCR 텍스트를 기반으로 의미 태그 생성
    - Scene Planner가 사용할 primary_tag, semantic_tags, scene_roles 생성
    - 결과를 image_tags.json으로 저장

    중요:
    - 외부 AI API를 호출하지 않음
    - wheel, handle, storage 같은 제품 부위 태그는 OCR/파일명/메타데이터에
      근거가 있을 때만 생성
    - 근거 없는 태그를 임의로 확정하지 않음
    """

    VERSION = "image-tagger-93-3"

    TAG_PRIORITY = [
        "hero",
        "usage",
        "lifestyle",
        "comparison",
        "before_after",
        "size",
        "feature",
        "storage",
        "wheel",
        "handle",
        "material",
        "installation",
        "components",
        "detail",
        "thumbnail",
        "cta",
        "product",
    ]

    KEYWORD_TAGS: Dict[str, Tuple[str, ...]] = {
        "wheel": (
            "바퀴",
            "휠",
            "캐스터",
            "wheel",
            "caster",
            "rolling",
            "롤링",
        ),
        "handle": (
            "손잡이",
            "핸들",
            "그립",
            "handle",
            "grip",
        ),
        "storage": (
            "수납",
            "보관",
            "용량",
            "공간",
            "내부",
            "포켓",
            "storage",
            "capacity",
            "interior",
            "pocket",
        ),
        "size": (
            "사이즈",
            "크기",
            "치수",
            "높이",
            "폭",
            "길이",
            "cm",
            "mm",
            "inch",
            "인치",
            "size",
            "dimension",
        ),
        "comparison": (
            "비교",
            "vs",
            "차이",
            "대비",
            "compare",
            "comparison",
        ),
        "before_after": (
            "전후",
            "비포",
            "애프터",
            "before",
            "after",
        ),
        "usage": (
            "사용",
            "사용법",
            "활용",
            "이렇게",
            "usage",
            "use",
            "how to",
        ),
        "lifestyle": (
            "생활",
            "집",
            "주방",
            "욕실",
            "거실",
            "침실",
            "여행",
            "외출",
            "lifestyle",
            "home",
            "travel",
        ),
        "installation": (
            "설치",
            "조립",
            "부착",
            "고정",
            "무타공",
            "install",
            "assembly",
            "mount",
        ),
        "components": (
            "구성품",
            "구성",
            "세트",
            "포함",
            "패키지",
            "components",
            "package",
            "included",
        ),
        "material": (
            "소재",
            "재질",
            "원단",
            "스틸",
            "알루미늄",
            "플라스틱",
            "material",
            "fabric",
            "steel",
            "aluminum",
        ),
        "feature": (
            "기능",
            "특징",
            "장점",
            "포인트",
            "feature",
            "benefit",
        ),
        "cta": (
            "구매",
            "주문",
            "할인",
            "쿠폰",
            "지금",
            "추천",
            "buy",
            "order",
            "discount",
            "coupon",
        ),
    }

    def tag(
        self,
        vision_result: Any = None,
        vision_analysis_path: Any = "",
        output_dir: Any = "",
        product_name: str = "",
        project_id: Any = "",
        save_result: bool = True,
    ) -> Dict[str, Any]:
        started_at = time.time()

        result: Dict[str, Any] = {
            "ok": False,
            "ready": False,
            "version": self.VERSION,
            "status": "not_run",
            "project_id": str(project_id or ""),
            "product_name": str(product_name or "").strip(),
            "vision_analysis_path": str(vision_analysis_path or "").strip(),
            "output_dir": "",
            "tag_manifest_path": "",
            "input_count": 0,
            "tagged_count": 0,
            "images": [],
            "summary": {},
            "warnings": [],
            "errors": [],
            "elapsed_seconds": 0.0,
        }

        vision_data = self._resolve_vision_result(
            vision_result=vision_result,
            vision_analysis_path=vision_analysis_path,
        )

        images = (
            vision_data.get("images", [])
            if isinstance(vision_data, dict)
            else []
        )
        images = images if isinstance(images, list) else []
        result["input_count"] = len(images)

        resolved_output_dir = self._resolve_output_dir(
            output_dir=output_dir,
            vision_analysis_path=vision_analysis_path,
            vision_data=vision_data,
            project_id=project_id,
        )
        resolved_output_dir.mkdir(parents=True, exist_ok=True)
        result["output_dir"] = str(resolved_output_dir)

        if not images:
            result["status"] = "no_images"
            result["warnings"].append("태깅할 Vision 분석 이미지가 없습니다")
            result["elapsed_seconds"] = round(time.time() - started_at, 3)
            if save_result:
                self._save_result(result, resolved_output_dir)
            return result

        tagged_images: List[Dict[str, Any]] = []

        for position, image in enumerate(images, start=1):
            if not isinstance(image, dict):
                continue

            if not image.get("ok"):
                failed = dict(image)
                failed.setdefault("semantic_tags", [])
                failed.setdefault("scene_roles", [])
                failed.setdefault("primary_tag", "")
                failed.setdefault("tag_confidence", 0.0)
                failed.setdefault("tag_evidence", {})
                tagged_images.append(failed)
                continue

            tagged_images.append(
                self._tag_one(
                    image=image,
                    position=position,
                    total_count=len(images),
                    product_name=product_name,
                )
            )

        successful = [
            item for item in tagged_images
            if item.get("ok") and item.get("semantic_tags")
        ]

        result["images"] = tagged_images
        result["tagged_count"] = len(successful)
        result["summary"] = self._build_summary(successful)
        result["ok"] = bool(successful)
        result["ready"] = bool(successful)
        result["status"] = "tagged" if successful else "failed"
        result["elapsed_seconds"] = round(time.time() - started_at, 3)

        if save_result:
            self._save_result(result, resolved_output_dir)

        return result

    def _resolve_vision_result(
        self,
        vision_result: Any,
        vision_analysis_path: Any,
    ) -> Dict[str, Any]:
        if isinstance(vision_result, dict):
            return dict(vision_result)

        path_value = str(vision_analysis_path or "").strip()
        if not path_value and isinstance(vision_result, (str, Path)):
            path_value = str(vision_result)

        if not path_value:
            return {}

        path = Path(path_value).expanduser()
        if not path.is_file():
            return {}

        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            return loaded if isinstance(loaded, dict) else {}
        except Exception:
            return {}

    def _resolve_output_dir(
        self,
        output_dir: Any,
        vision_analysis_path: Any,
        vision_data: Dict[str, Any],
        project_id: Any,
    ) -> Path:
        if str(output_dir or "").strip():
            return Path(str(output_dir)).expanduser()

        data_output = str(vision_data.get("output_dir") or "").strip()
        if data_output:
            return Path(data_output).expanduser()

        analysis_path = str(vision_analysis_path or "").strip()
        if analysis_path:
            return Path(analysis_path).expanduser().parent

        project_key = str(project_id or "unknown").strip() or "unknown"
        return Path("assets") / "product_images" / f"project_{project_key}"

    def _tag_one(
        self,
        image: Dict[str, Any],
        position: int,
        total_count: int,
        product_name: str,
    ) -> Dict[str, Any]:
        tagged = dict(image)

        evidence_text = self._collect_evidence_text(
            image=image,
            product_name=product_name,
        )

        scores: Dict[str, float] = {}
        evidence: Dict[str, List[str]] = {}

        def add_score(tag: str, value: float, reason: str) -> None:
            scores[tag] = scores.get(tag, 0.0) + value
            evidence.setdefault(tag, []).append(reason)

        image_type = str(image.get("type") or "").lower()
        source = str(image.get("source") or "").lower()
        layout_type = str(image.get("layout_type") or "")
        orientation = str(image.get("orientation") or "")
        primary_use = str(image.get("primary_use") or "")
        recommended_uses = list(image.get("recommended_uses") or [])
        quality_score = float(image.get("quality_score") or 0.0)

        if image_type in {"main", "representative", "thumbnail"}:
            add_score("hero", 80.0, f"type={image_type}")
            add_score("product", 30.0, f"type={image_type}")

        if position == 1:
            add_score("hero", 35.0, "first_image")
            add_score("thumbnail", 20.0, "first_image")

        if "opening" in recommended_uses:
            add_score("hero", 45.0, "recommended_use=opening")

        if "thumbnail" in recommended_uses:
            add_score("thumbnail", 40.0, "recommended_use=thumbnail")

        if "product_closeup" in recommended_uses:
            add_score("detail", 32.0, "recommended_use=product_closeup")

        if "detail_closeup" in recommended_uses:
            add_score("detail", 48.0, "recommended_use=detail_closeup")

        if "feature_extraction" in recommended_uses:
            add_score("feature", 36.0, "recommended_use=feature_extraction")

        if primary_use == "detail":
            add_score("detail", 22.0, "primary_use=detail")

        if layout_type in {"long_detail_page", "vertical_detail"}:
            add_score("feature", 28.0, f"layout={layout_type}")
            add_score("detail", 18.0, f"layout={layout_type}")

        if orientation == "portrait":
            add_score("usage", 8.0, "portrait_scene_candidate")

        if quality_score >= 70:
            add_score("product", 16.0, "high_quality")

        if source in {"detail", "detail_page", "coupang_detail"}:
            add_score("detail", 20.0, f"source={source}")

        for tag, keywords in self.KEYWORD_TAGS.items():
            matched = self._matched_keywords(evidence_text, keywords)
            if matched:
                keyword_score = min(90.0, 36.0 + len(matched) * 14.0)
                add_score(
                    tag,
                    keyword_score,
                    "keywords=" + ",".join(matched[:5]),
                )

        digit_density = self._digit_density(evidence_text)
        if digit_density >= 0.06 and self._contains_measurement(evidence_text):
            add_score("size", 38.0, "measurement_text")

        if total_count >= 2 and position == total_count:
            add_score("cta", 8.0, "last_image_candidate")

        if not scores:
            add_score("product", 20.0, "fallback")

        semantic_tags = [
            tag
            for tag, score in sorted(
                scores.items(),
                key=lambda item: (
                    -item[1],
                    self._priority_index(item[0]),
                ),
            )
            if score >= 18.0
        ]

        if "hero" in semantic_tags and "product" not in semantic_tags:
            semantic_tags.append("product")

        semantic_tags = self._dedupe(semantic_tags)
        primary_tag = semantic_tags[0] if semantic_tags else "product"

        scene_roles = self._scene_roles(
            semantic_tags=semantic_tags,
            recommended_uses=recommended_uses,
            quality_score=quality_score,
        )

        top_score = max(scores.values()) if scores else 0.0
        confidence = round(min(100.0, top_score), 2)

        tagged["semantic_tags"] = semantic_tags
        tagged["primary_tag"] = primary_tag
        tagged["scene_roles"] = scene_roles
        tagged["tag_confidence"] = confidence
        tagged["tag_scores"] = {
            key: round(value, 2)
            for key, value in sorted(
                scores.items(),
                key=lambda item: -item[1],
            )
        }
        tagged["tag_evidence"] = evidence
        tagged["tagger_version"] = self.VERSION

        return tagged

    def _collect_evidence_text(
        self,
        image: Dict[str, Any],
        product_name: str,
    ) -> str:
        values: List[str] = [
            str(product_name or ""),
            str(image.get("filename") or ""),
            str(image.get("path") or ""),
            str(image.get("type") or ""),
            str(image.get("source") or ""),
            str(image.get("alt") or ""),
            str(image.get("title") or ""),
            str(image.get("caption") or ""),
            str(image.get("ocr_text") or ""),
            str(image.get("text") or ""),
            str(image.get("description") or ""),
        ]

        metadata = image.get("metadata")
        if isinstance(metadata, dict):
            values.extend(str(value) for value in metadata.values())

        return " ".join(values).lower()

    def _matched_keywords(
        self,
        text: str,
        keywords: Iterable[str],
    ) -> List[str]:
        matched: List[str] = []
        for keyword in keywords:
            normalized = str(keyword).lower().strip()
            if normalized and normalized in text:
                matched.append(normalized)
        return self._dedupe(matched)

    def _contains_measurement(self, text: str) -> bool:
        return bool(
            re.search(
                r"\b\d+(?:\.\d+)?\s*(?:cm|mm|m|kg|g|l|ml|inch)\b",
                text,
                flags=re.IGNORECASE,
            )
            or re.search(r"\d+\s*(?:인치|센티|밀리)", text)
        )

    def _digit_density(self, text: str) -> float:
        if not text:
            return 0.0
        digits = sum(character.isdigit() for character in text)
        return digits / max(1, len(text))

    def _scene_roles(
        self,
        semantic_tags: List[str],
        recommended_uses: List[str],
        quality_score: float,
    ) -> List[str]:
        roles: List[str] = []

        tag_set = set(semantic_tags)
        use_set = set(recommended_uses)

        if "hero" in tag_set:
            roles.extend(["opening", "hook"])

        if tag_set.intersection(
            {"usage", "lifestyle", "installation"}
        ):
            roles.extend(["problem", "demonstration"])

        if tag_set.intersection(
            {"feature", "detail", "wheel", "handle", "storage", "material"}
        ):
            roles.extend(["feature", "proof"])

        if tag_set.intersection(
            {"comparison", "before_after", "size"}
        ):
            roles.extend(["comparison", "decision"])

        if "components" in tag_set:
            roles.append("package")

        if "cta" in tag_set:
            roles.append("closing")

        if "thumbnail" in tag_set:
            roles.append("thumbnail")

        if "veo_reference" in use_set and quality_score >= 65:
            roles.append("veo_reference")

        if not roles:
            roles.append("supporting")

        return self._dedupe(roles)

    def _priority_index(self, tag: str) -> int:
        try:
            return self.TAG_PRIORITY.index(tag)
        except ValueError:
            return len(self.TAG_PRIORITY)

    def _dedupe(self, values: Iterable[str]) -> List[str]:
        result: List[str] = []
        for value in values:
            if value and value not in result:
                result.append(value)
        return result

    def _build_summary(
        self,
        images: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        tag_counts: Counter[str] = Counter()
        role_counts: Counter[str] = Counter()

        for image in images:
            tag_counts.update(image.get("semantic_tags") or [])
            role_counts.update(image.get("scene_roles") or [])

        best_by_tag: Dict[str, Dict[str, Any]] = {}

        for tag in tag_counts:
            candidates = [
                image
                for image in images
                if tag in (image.get("semantic_tags") or [])
            ]
            if not candidates:
                continue

            best = max(
                candidates,
                key=lambda image: (
                    float(
                        (image.get("tag_scores") or {}).get(tag, 0.0)
                    ),
                    float(image.get("quality_score") or 0.0),
                ),
            )

            best_by_tag[tag] = {
                "path": str(best.get("path") or ""),
                "filename": str(best.get("filename") or ""),
                "primary_tag": str(best.get("primary_tag") or ""),
                "quality_score": float(best.get("quality_score") or 0.0),
                "tag_confidence": float(best.get("tag_confidence") or 0.0),
            }

        return {
            "tag_counts": dict(tag_counts.most_common()),
            "scene_role_counts": dict(role_counts.most_common()),
            "available_tags": list(tag_counts.keys()),
            "best_by_tag": best_by_tag,
            "hero_count": tag_counts.get("hero", 0),
            "detail_count": tag_counts.get("detail", 0),
            "usage_count": tag_counts.get("usage", 0),
            "veo_reference_count": role_counts.get("veo_reference", 0),
        }

    def _save_result(
        self,
        result: Dict[str, Any],
        output_dir: Path,
    ) -> None:
        path = output_dir / "image_tags.json"
        result["tag_manifest_path"] = str(path)
        path.write_text(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )