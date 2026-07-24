from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

try:
    from PIL import Image, ImageFilter, ImageOps, ImageStat
except ImportError:  # pragma: no cover
    Image = None
    ImageFilter = None
    ImageOps = None
    ImageStat = None


class ImageExtractor:
    """
    Sprint108-1 Review Image Pool Merge

    핵심 역할
    ----------
    - 여러 상품 이미지를 원본 해상도로 선별합니다.
    - 로컬 Vision 지표 + OCR 텍스트 + 파일명 + 이미지 순서를 함께 사용합니다.
    - hero / usage / feature / detail / comparison / review / benefit / cta 역할을 분류합니다.
    - 외부 API 없이 동작하며 OCR 엔진이 없으면 Vision 기반으로 안전하게 계속합니다.
    - 기존 ImageExtractor 호출 방식과 반환 키를 유지합니다.
    """

    VERSION = "image-role-classifier-108-1"
    MANIFEST_NAME = "image_role_classifier_manifest.json"
    SUPPORTED_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

    ROLE_PRIORITY = {
        "hero": 0,
        "usage": 1,
        "benefit": 2,
        "feature": 3,
        "detail": 4,
        "comparison": 5,
        "review": 6,
        "cta": 7,
        "product": 8,
    }

    ROLE_LIMITS = {
        "hero": 1,
        "usage": 2,
        "benefit": 2,
        "feature": 2,
        "detail": 3,
        "comparison": 1,
        "review": 2,
        "cta": 1,
    }

    OCR_KEYWORDS = {
        "review": (
            "리뷰", "후기", "평점", "구매평", "사용후기", "고객", "만족", "추천",
            "별점", "도움돼요", "재구매", "내돈내산", "솔직후기", "구매자",
            "실사용", "써보니", "사용해보니", "좋았어요", "만족해요", "편했어요",
            "아쉬워요", "배송", "포토리뷰", "베스트리뷰", "상품평", "작성자",
        ),
        "comparison": (
            "비교", "vs", "차이", "기존", "타사", "일반", "before", "after",
            "전", "후", "변화", "대비", "더 넓", "더 강", "몇 배",
        ),
        "cta": (
            "구매", "주문", "지금", "특가", "할인", "쿠폰", "무료배송", "바로가기",
            "선택", "장바구니", "오늘만", "한정", "혜택", "가격", "원",
        ),
        "benefit": (
            "편리", "간편", "깔끔", "정리", "절약", "안심", "쾌적", "해결",
            "효과", "장점", "좋아요", "추천", "넉넉", "튼튼", "위생", "안전",
            "공간활용", "삶의 질", "걱정 없이", "한 번에", "더 쉽게", "더 편하게",
            "시간 절약", "공간 절약", "부담 없이", "오래 사용", "간단하게",
            "정돈", "효율", "실용적", "편안", "쏙", "넉넉하게", "걱정 끝",
        ),
        "feature": (
            "기능", "특징", "소재", "재질", "사이즈", "크기", "용량", "무게",
            "내열", "방수", "항균", "미끄럼", "회전", "접이", "분리", "설치",
            "구성", "스펙", "cm", "mm", "kg", "ml", "리터",
        ),
        "usage": (
            "사용", "사용법", "설치", "착용", "조립", "보관", "세척", "활용",
            "방법", "이렇게", "간단", "손쉽게", "주방", "욕실", "거실", "차량",
        ),
        "detail": (
            "디테일", "확대", "마감", "부분", "내부", "표면", "질감", "구조",
            "바퀴", "손잡이", "버튼", "고정", "모서리", "봉제", "뚜껑",
        ),
        "hero": (
            "신제품", "대표", "프리미엄", "베스트", "시그니처", "완성", "선택",
        ),
    }

    FILENAME_KEYWORDS = {
        "hero": ("main", "hero", "대표", "메인", "썸네일"),
        "usage": ("usage", "use", "사용", "활용", "설치"),
        "feature": ("feature", "기능", "특징", "spec"),
        "detail": ("detail", "디테일", "확대"),
        "comparison": ("compare", "comparison", "비교", "before", "after", "vs"),
        "review": ("review", "리뷰", "후기"),
        "benefit": ("benefit", "장점", "효과"),
        "cta": ("cta", "구매", "주문", "할인", "price"),
    }

    def __init__(
        self,
        *,
        max_images: int = 10,
        min_images: int = 2,
        min_width: int = 220,
        min_height: int = 180,
        min_area: int = 70_000,
        min_score: float = 38.0,
        duplicate_distance: int = 7,
        enable_ocr: bool = True,
    ) -> None:
        self.max_images = max(1, int(max_images))
        self.min_images = max(1, int(min_images))
        self.min_width = max(64, int(min_width))
        self.min_height = max(64, int(min_height))
        self.min_area = max(4096, int(min_area))
        self.min_score = float(min_score)
        self.duplicate_distance = max(0, int(duplicate_distance))
        self.enable_ocr = bool(enable_ocr)
        self._ocr_engine_name = "disabled"
        self._pytesseract = None

    def extract(
        self,
        source_images: Any,
        output_dir: Any,
        *,
        project_id: Any = "",
        product_name: Any = "",
        max_images: Optional[int] = None,
        clean_output: bool = True,
    ) -> Dict[str, Any]:
        return self.select_from_candidates(
            candidate_images=source_images,
            output_dir=output_dir,
            project_id=project_id,
            product_name=product_name,
            max_images=max_images,
            clean_output=clean_output,
        )

    def select_from_candidates(
        self,
        candidate_images: Any,
        output_dir: Any,
        *,
        project_id: Any = "",
        product_name: Any = "",
        max_images: Optional[int] = None,
        clean_output: bool = True,
    ) -> Dict[str, Any]:
        source_records = self._normalize_source_records(candidate_images)
        review_records = self._discover_review_image_records(project_id)
        source_records = self._merge_source_records(
            source_records,
            review_records,
        )
        out_dir = Path(output_dir)
        limit = max(1, int(max_images or self.max_images))

        result: Dict[str, Any] = {
            "ok": False,
            "ready": False,
            "version": self.VERSION,
            "status": "empty",
            "project_id": str(project_id or ""),
            "product_name": str(product_name or ""),
            "output_dir": str(out_dir),
            "manifest_path": str(out_dir / self.MANIFEST_NAME),
            "source_count": len(source_records),
            "product_source_count": sum(
                1 for record in source_records
                if str(record.get("source_type") or "product") != "review_image"
            ),
            "review_source_count": sum(
                1 for record in source_records
                if str(record.get("source_type") or "product") == "review_image"
            ),
            "candidate_count": 0,
            "selected_count": 0,
            "rejected_count": 0,
            "images": [],
            "rejections": [],
            "role_counts": {},
            "role_sequence": [],
            "ocr_engine": "disabled",
            "warnings": [],
            "errors": [],
        }

        if Image is None or np is None:
            result["status"] = "dependency_missing"
            result["errors"].append("Pillow 또는 NumPy를 불러올 수 없습니다.")
            return result

        valid = [
            record for record in source_records
            if self._is_supported_image(Path(record["path"]))
        ]
        if not valid:
            result["status"] = "no_candidate_images"
            result["warnings"].append("사용 가능한 상품 이미지가 없습니다.")
            return result

        try:
            if clean_output and out_dir.exists():
                self._clear_generated_files(out_dir)
            out_dir.mkdir(parents=True, exist_ok=True)

            ranked: List[Dict[str, Any]] = []
            rejected: List[Dict[str, Any]] = []

            for order, source_record in enumerate(valid):
                path = Path(source_record["path"])
                try:
                    with Image.open(path) as opened:
                        image = ImageOps.exif_transpose(opened).convert("RGB")

                    metrics = self._measure_image(image)
                    width, height = image.size
                    short_side = min(width, height)
                    long_side = max(width, height)
                    aspect_long = long_side / max(1, short_side)
                    area = width * height
                    score = self._quality_score(metrics)

                    score += min(12.0, short_side / 80.0)
                    score += min(8.0, area / 250_000.0)
                    if aspect_long > 3.2:
                        score -= 24.0
                    if metrics["text_like_ratio"] > 0.82:
                        score -= 12.0

                    ocr_text = self._clean_text(
                        source_record.get("ocr_text")
                        or source_record.get("text")
                        or self._read_ocr(image)
                    )
                    vision_labels = self._normalize_labels(
                        source_record.get("vision_labels")
                        or source_record.get("labels")
                        or source_record.get("tags")
                    )

                    reason = ""
                    if short_side < 64:
                        reason = f"short_side_too_small:{short_side}"
                    elif aspect_long > 4.5:
                        reason = f"extreme_aspect_ratio:{aspect_long:.2f}"
                    elif score < 24.0:
                        reason = f"selector_score_low:{score:.2f}"

                    source_type = str(
                        source_record.get("source_type") or "product"
                    )
                    if source_type == "review_image":
                        score += 18.0

                    record = {
                        "source_path": str(path),
                        "path": str(path),
                        "output_path": "",
                        "width": width,
                        "height": height,
                        "score": round(float(score), 2),
                        "image_type": "product",
                        "source_type": source_type,
                        "photo_ratio": round(metrics["photo_ratio"], 4),
                        "text_like_ratio": round(metrics["text_like_ratio"], 4),
                        "sharpness": round(metrics["sharpness"], 4),
                        "colorfulness": round(metrics["colorfulness"], 4),
                        "bright_ratio": round(metrics["bright_ratio"], 4),
                        "dark_ratio": round(metrics["dark_ratio"], 4),
                        "edge_density": round(metrics["edge_density"], 4),
                        "center_activity": round(metrics["center_activity"], 4),
                        "top_text_density": round(metrics["top_text_density"], 4),
                        "bottom_text_density": round(metrics["bottom_text_density"], 4),
                        "left_right_split": round(metrics["left_right_split"], 4),
                        "panel_count": int(metrics["panel_count"]),
                        "ocr_text": ocr_text,
                        "ocr_length": len(ocr_text),
                        "vision_labels": vision_labels,
                        "fingerprint": self._perceptual_hash(image),
                        "source_order": order,
                        "_image": image,
                    }

                    if reason:
                        rejected.append(self._reject(record, reason))
                    else:
                        ranked.append(record)

                except Exception as exc:
                    rejected.append({
                        "path": str(path),
                        "reason": f"read_error:{type(exc).__name__}:{exc}",
                    })

            result["candidate_count"] = len(ranked)
            result["ocr_engine"] = self._ocr_engine_name

            ranked.sort(
                key=lambda item: (
                    -float(item.get("score", 0.0)),
                    int(item.get("source_order", 0)),
                )
            )

            selected: List[Dict[str, Any]] = []
            hashes: List[str] = []

            # 리뷰 이미지는 최대 2장만 예약하여 상품 이미지 구성을 보존합니다.
            review_ranked = [
                item for item in ranked
                if str(item.get("source_type") or "product") == "review_image"
            ]
            product_ranked = [
                item for item in ranked
                if str(item.get("source_type") or "product") != "review_image"
            ]
            ordered_groups = (
                review_ranked[: min(2, limit)],
                product_ranked,
                review_ranked[min(2, limit):],
            )

            for group in ordered_groups:
                for item in group:
                    if len(selected) >= limit:
                        break
                    fingerprint = str(item.get("fingerprint") or "")
                    is_duplicate = any(
                        self._hamming_distance(fingerprint, existing)
                        <= self.duplicate_distance
                        for existing in hashes
                        if fingerprint and existing
                    )
                    if is_duplicate:
                        rejected.append(self._reject(item, "visual_duplicate"))
                        continue

                    selected.append(item)
                    hashes.append(fingerprint)
                if len(selected) >= limit:
                    break

            selected.sort(key=lambda item: int(item.get("source_order", 0)))
            self._calculate_role_scores(selected)
            self._assign_roles(selected)
            self._stabilize_role_distribution(selected)

            selected.sort(
                key=lambda item: (
                    self.ROLE_PRIORITY.get(
                        str(item.get("image_type") or "product"), 8
                    ),
                    int(item.get("source_order", 0)),
                )
            )

            saved: List[Dict[str, Any]] = []
            role_counts: Counter[str] = Counter()

            for index, item in enumerate(selected, start=1):
                image = item.pop("_image", None)
                if image is None:
                    rejected.append(self._reject(item, "missing_image_data"))
                    continue

                role = str(item.get("image_type") or "product")
                role_counts[role] += 1
                output_path = out_dir / f"selected_{index:02d}_{role}.png"

                # 원본 해상도 그대로 저장합니다.
                image.save(output_path, format="PNG", optimize=True)

                item["output_path"] = str(output_path)
                item["path"] = str(output_path)
                item["file"] = output_path.name
                item["role_order"] = index
                item["role_confidence"] = round(
                    float(item.get("role_confidence", 0.0)), 3
                )
                item["role_reason"] = list(item.get("role_reason", []))[:6]
                saved.append(item)

            result["role_counts"] = dict(role_counts)
            result["role_sequence"] = [
                str(item.get("image_type") or "product") for item in saved
            ]
            result["images"] = saved
            result["selected_count"] = len(saved)
            result["rejections"] = rejected
            result["rejected_count"] = len(rejected)
            result["ok"] = bool(saved)
            result["ready"] = len(saved) >= self.min_images
            result["status"] = "selected" if saved else "no_qualified_images"

            if self.enable_ocr and self._ocr_engine_name == "unavailable":
                result["warnings"].append(
                    "OCR 엔진을 찾지 못해 Vision·파일명·순서 기반으로 분류했습니다."
                )

            self._write_manifest(out_dir / self.MANIFEST_NAME, result)
            return result

        except Exception as exc:
            result["status"] = "error"
            result["errors"].append(f"{type(exc).__name__}: {exc}")
            return result

    def _calculate_role_scores(self, items: List[Dict[str, Any]]) -> None:
        count = len(items)
        for index, item in enumerate(items):
            scores = {role: 0.0 for role in self.ROLE_PRIORITY}
            reasons: Dict[str, List[str]] = {
                role: [] for role in self.ROLE_PRIORITY
            }

            width = max(1, int(item.get("width", 1)))
            height = max(1, int(item.get("height", 1)))
            vertical_ratio = height / width
            text_ratio = float(item.get("text_like_ratio", 0.0))
            photo_ratio = float(item.get("photo_ratio", 0.0))
            sharpness = float(item.get("sharpness", 0.0))
            center_activity = float(item.get("center_activity", 0.0))
            split = float(item.get("left_right_split", 0.0))
            panel_count = int(item.get("panel_count", 1))
            top_text_density = float(item.get("top_text_density", 0.0))
            source_order = int(item.get("source_order", index))
            position = source_order / max(1, count - 1)
            ocr_text = str(item.get("ocr_text") or "")
            filename = Path(str(item.get("source_path") or "")).stem.lower()
            labels_text = " ".join(item.get("vision_labels") or []).lower()
            source_type = str(item.get("source_type") or "product")

            if source_type == "review_image":
                scores["review"] += 30.0
                reasons["review"].append("review_image_source")
                scores["hero"] -= 20.0
                scores["cta"] -= 20.0

            # 파일명 신호
            for role, keywords in self.FILENAME_KEYWORDS.items():
                hits = sum(1 for keyword in keywords if keyword.lower() in filename)
                if hits:
                    scores[role] += 3.2 + hits * 1.6
                    reasons[role].append(f"filename:{hits}")

            # OCR 신호
            normalized_text = re.sub(r"\s+", "", ocr_text.lower())
            for role, keywords in self.OCR_KEYWORDS.items():
                hits = sum(
                    1 for keyword in keywords
                    if re.sub(r"\s+", "", keyword.lower()) in normalized_text
                )
                if hits:
                    scores[role] += min(10.0, 2.4 + hits * 1.55)
                    reasons[role].append(f"ocr:{hits}")

            # Vision label 신호
            for role, keywords in self.OCR_KEYWORDS.items():
                hits = sum(1 for keyword in keywords if keyword.lower() in labels_text)
                if hits:
                    scores[role] += min(7.0, 2.0 + hits * 1.2)
                    reasons[role].append(f"vision_label:{hits}")

            # hero: 첫 이미지, 중앙 집중, 사진 비율이 높은 대표 컷
            if source_order == 0:
                scores["hero"] += 8.0
                reasons["hero"].append("first_image")
            if center_activity >= 0.34:
                scores["hero"] += 2.2
                reasons["hero"].append("center_subject")
            if photo_ratio >= 0.52 and text_ratio <= 0.25:
                scores["hero"] += 2.2
                reasons["hero"].append("clean_product_photo")

            # usage: 세로형 생활 장면, 사진 정보량, 적당한 텍스트
            if vertical_ratio >= 1.25:
                scores["usage"] += 2.0
                reasons["usage"].append("vertical_scene")
            if photo_ratio >= 0.48 and center_activity >= 0.22:
                scores["usage"] += 2.6
                reasons["usage"].append("scene_activity")
            if 0.08 <= text_ratio <= 0.42:
                scores["usage"] += 1.0

            # feature: 텍스트와 사진이 함께 있고 선명도가 높은 설명 컷
            if 0.15 <= text_ratio <= 0.62:
                scores["feature"] += 2.4
                reasons["feature"].append("mixed_text_photo")
            if sharpness >= 0.22:
                scores["feature"] += 1.8
                reasons["feature"].append("sharp_information")
            if panel_count >= 2:
                scores["feature"] += 1.2

            # detail: 확대 질감/부분 컷. 텍스트가 너무 많지 않고 에지가 높음
            if sharpness >= 0.30 and text_ratio <= 0.38:
                scores["detail"] += 3.2
                reasons["detail"].append("sharp_closeup")
            if photo_ratio >= 0.42 and center_activity >= 0.28:
                scores["detail"] += 1.3

            # comparison: 좌우 분할 또는 다중 패널
            if split >= 0.16:
                scores["comparison"] += 4.0
                reasons["comparison"].append("left_right_difference")
            if panel_count >= 2:
                scores["comparison"] += min(4.0, panel_count * 1.2)
                reasons["comparison"].append(f"panels:{panel_count}")

            # review: 쿠팡 후기 캡처의 문장·별점·작성정보·레이아웃을 함께 판별
            review_sentence_hits = len(
                re.findall(
                    r"(?:했어요|해요|됩니다|좋아요|만족|추천|편해요|아쉬워요|"
                    r"써보니|사용해보니|구매했|배송|재구매|마음에\s*들|"
                    r"잘\s*쓰고|좋네요|괜찮아요|유용해요|안심돼)",
                    ocr_text,
                )
            )
            star_hits = len(
                re.findall(
                    r"(?:★|☆|별점|평점|[1-5]\s*(?:점|/\s*5))",
                    ocr_text,
                )
            )
            date_hits = len(
                re.findall(
                    r"(?:20\d{2}[.\-/년]\s*\d{1,2}[.\-/월]\s*\d{1,2}일?|"
                    r"\d{1,2}[.\-/월]\s*\d{1,2}일|"
                    r"\d+\s*(?:일|개월)\s*사용)",
                    ocr_text,
                )
            )
            reviewer_meta_hits = len(
                re.findall(
                    r"(?:구매자|작성자|실구매자|베스트리뷰|포토리뷰|상품평|"
                    r"도움이\s*돼요|도움돼요|옵션|사이즈|색상|배송)",
                    ocr_text,
                )
            )
            masked_name_hits = len(
                re.findall(
                    r"(?:[가-힣A-Za-z0-9]{1,6}\*{1,4}|\*{2,}[가-힣A-Za-z0-9]{0,3})",
                    ocr_text,
                )
            )
            line_count = len(
                [line for line in ocr_text.splitlines() if line.strip()]
            )

            review_layout_score = 0.0
            if 0.28 <= text_ratio <= 0.90:
                review_layout_score += 1.8
            if top_text_density >= 0.05:
                review_layout_score += 1.0
            if line_count >= 3:
                review_layout_score += 1.0
            if line_count >= 6:
                review_layout_score += 0.8
            if panel_count >= 2 and text_ratio >= 0.22:
                review_layout_score += 0.8
            if vertical_ratio >= 1.15 and text_ratio >= 0.30:
                review_layout_score += 0.7

            if len(ocr_text) >= 30:
                scores["review"] += 2.6
                reasons["review"].append("long_ocr")
            if len(ocr_text) >= 75:
                scores["review"] += 1.8
                reasons["review"].append("very_long_ocr")
            if review_layout_score:
                scores["review"] += review_layout_score
                reasons["review"].append(
                    f"review_layout:{review_layout_score:.1f}"
                )
            if review_sentence_hits:
                scores["review"] += min(
                    6.8, 2.0 + review_sentence_hits * 1.25
                )
                reasons["review"].append(
                    f"review_sentences:{review_sentence_hits}"
                )
            if star_hits:
                scores["review"] += min(5.0, 2.5 + star_hits * 1.2)
                reasons["review"].append(f"star_rating:{star_hits}")
            if date_hits:
                scores["review"] += min(3.5, 1.8 + date_hits)
                reasons["review"].append(f"review_date:{date_hits}")
            if reviewer_meta_hits:
                scores["review"] += min(
                    4.0, 1.6 + reviewer_meta_hits * 0.9
                )
                reasons["review"].append(
                    f"review_metadata:{reviewer_meta_hits}"
                )
            if masked_name_hits:
                scores["review"] += min(
                    2.5, 1.0 + masked_name_hits * 0.5
                )
                reasons["review"].append(
                    f"masked_reviewer_name:{masked_name_hits}"
                )
            if source_order >= max(2, count // 2) and len(ocr_text) >= 40:
                scores["review"] += 1.0
                reasons["review"].append("late_review_position")

            # 사진 중심 상세 컷이 단순히 글자가 많다는 이유로 review가 되는 것을 방지
            if text_ratio < 0.18 and not (
                star_hits or date_hits or reviewer_meta_hits
            ):
                scores["review"] -= 2.0
            if len(ocr_text) < 20 and not (
                star_hits or reviewer_meta_hits
            ):
                scores["review"] -= 1.6

            # benefit: 제품 기능 설명보다 사용자가 얻는 결과·효과 표현을 우선 판별
            benefit_phrase_hits = len(
                re.findall(
                    r"(?:더\s*(?:편|쉽|깔끔|넓|안전)|"
                    r"(?:시간|공간|비용)\s*(?:절약|활용)|"
                    r"(?:걱정|불편|번거로움)\s*(?:없이|끝)|"
                    r"(?:한\s*번에|간단하게|손쉽게|쾌적하게|효율적으로))",
                    ocr_text,
                )
            )
            feature_unit_hits = len(
                re.findall(r"\b\d+(?:\.\d+)?\s*(?:cm|mm|kg|g|ml|l)\b", normalized_text)
            )

            if 0.10 <= text_ratio <= 0.58 and photo_ratio >= 0.30:
                scores["benefit"] += 2.4
                reasons["benefit"].append("benefit_layout")
            if 0.30 <= position <= 0.90:
                scores["benefit"] += 1.1
            if benefit_phrase_hits:
                scores["benefit"] += min(6.0, 2.0 + benefit_phrase_hits * 1.4)
                reasons["benefit"].append(
                    f"benefit_phrases:{benefit_phrase_hits}"
                )
            if len(ocr_text) >= 18 and len(ocr_text) <= 160:
                scores["benefit"] += 1.0
                reasons["benefit"].append("concise_benefit_copy")
            if feature_unit_hits == 0 and len(ocr_text) >= 20:
                scores["benefit"] += 0.8
            elif feature_unit_hits >= 2:
                scores["benefit"] -= 1.4

            # cta: 마지막 이미지, 텍스트/가격/혜택 신호
            if source_order == count - 1:
                scores["cta"] += 6.0
                reasons["cta"].append("last_image")
            if position >= 0.78:
                scores["cta"] += 1.5
            if text_ratio >= 0.22:
                scores["cta"] += 1.0

            # 기본 product 점수
            scores["product"] = 1.0 + photo_ratio

            item["role_scores"] = {
                role: round(score, 3) for role, score in scores.items()
            }
            item["_role_reasons"] = reasons

    def _assign_roles(self, items: List[Dict[str, Any]]) -> None:
        if not items:
            return

        used_counts: Counter[str] = Counter()

        # 리뷰 업로드 원본은 최대 2장까지 review 역할로 우선 고정합니다.
        forced_review_indexes = [
            i for i, item in enumerate(items)
            if str(item.get("source_type") or "product") == "review_image"
        ][: self.ROLE_LIMITS["review"]]
        for index in forced_review_indexes:
            self._set_role(items[index], "review")
            used_counts["review"] += 1

        remaining = [
            i for i in range(len(items))
            if i not in forced_review_indexes
        ]
        if not remaining:
            return

        # Hero는 리뷰 이미지를 제외한 후보 중 hero 점수가 가장 높은 한 장입니다.
        hero_index = max(
            remaining,
            key=lambda i: (
                float(items[i]["role_scores"].get("hero", 0.0)),
                -int(items[i].get("source_order", 0)),
            ),
        )
        self._set_role(items[hero_index], "hero")
        used_counts["hero"] += 1
        remaining.remove(hero_index)

        # CTA는 명확한 신호가 있을 때만 한 장 배정합니다.
        if remaining:
            cta_index = max(
                remaining,
                key=lambda i: float(items[i]["role_scores"].get("cta", 0.0)),
            )
            if float(items[cta_index]["role_scores"].get("cta", 0.0)) >= 6.0:
                self._set_role(items[cta_index], "cta")
                used_counts["cta"] += 1
                remaining.remove(cta_index)

        # 나머지는 점수가 높은 역할을 선택하되 역할별 상한을 둡니다.
        for index in remaining:
            item = items[index]
            ranked_roles = sorted(
                (
                    (role, float(score))
                    for role, score in item["role_scores"].items()
                    if role not in {"hero", "cta", "product", "review"}
                ),
                key=lambda pair: pair[1],
                reverse=True,
            )

            assigned = "detail"
            for role, score in ranked_roles:
                if score < 2.4:
                    continue
                if used_counts[role] >= self.ROLE_LIMITS.get(role, 99):
                    continue
                assigned = role
                break

            self._set_role(item, assigned)
            used_counts[assigned] += 1

    def _stabilize_role_distribution(self, items: List[Dict[str, Any]]) -> None:
        """detail 쏠림을 줄이고 실제 신호가 있는 빈 역할을 복구합니다."""
        if len(items) < 4:
            return

        counts = Counter(str(item.get("image_type") or "product") for item in items)

        # detail이 3장보다 많으면 다른 역할의 강한 차선 후보로 전환합니다.
        while counts["detail"] > self.ROLE_LIMITS["detail"]:
            detail_items = [
                item for item in items if item.get("image_type") == "detail"
            ]
            best_change = None

            for item in detail_items:
                scores = item.get("role_scores", {})
                detail_score = float(scores.get("detail", 0.0))
                for role in (
                    "comparison", "review", "benefit", "usage", "feature"
                ):
                    if counts[role] >= self.ROLE_LIMITS[role]:
                        continue
                    role_score = float(scores.get(role, 0.0))
                    threshold = 3.0 if role in {"comparison", "review"} else 2.6
                    if role_score < threshold:
                        continue
                    gain = role_score - detail_score
                    candidate = (gain, role_score, item, role)
                    if best_change is None or candidate[:2] > best_change[:2]:
                        best_change = candidate

            if best_change is None:
                break

            _, _, item, role = best_change
            counts["detail"] -= 1
            counts[role] += 1
            self._set_role(item, role)

        # 충분한 이미지가 있으면 review / benefit / feature 누락을 보완합니다.
        if len(items) >= 6:
            minimum_targets = (
                ("review", 3.8),
                ("benefit", 3.6),
                ("feature", 2.8),
            )
            for target_role, threshold in minimum_targets:
                if counts[target_role] > 0:
                    continue

                candidates = [
                    item for item in items
                    if item.get("image_type") not in {"hero", "cta"}
                ]
                if not candidates:
                    continue

                best = max(
                    candidates,
                    key=lambda item: float(
                        item.get("role_scores", {}).get(target_role, 0.0)
                    ),
                )
                best_score = float(
                    best.get("role_scores", {}).get(target_role, 0.0)
                )
                old_role = str(best.get("image_type") or "product")
                old_score = float(
                    best.get("role_scores", {}).get(old_role, 0.0)
                )

                # 억지 분류 방지: 절대 점수와 기존 역할 대비 근접도를 함께 확인
                score_margin = 2.2 if target_role == "review" else 1.6
                if (
                    best_score >= threshold
                    and best_score >= old_score - score_margin
                    and counts[old_role] > 1
                ):
                    counts[old_role] -= 1
                    counts[target_role] += 1
                    self._set_role(best, target_role)

    def _set_role(self, item: Dict[str, Any], role: str) -> None:
        scores = item.get("role_scores", {})
        ordered = sorted(
            (float(value) for value in scores.values()), reverse=True
        )
        top = float(scores.get(role, 0.0))
        second = ordered[1] if len(ordered) > 1 else 0.0
        confidence = 0.45 + min(0.45, top / 20.0) + min(0.10, max(0.0, top - second) / 20.0)

        item["image_type"] = role
        item["role_confidence"] = min(0.98, confidence)
        item["role_reason"] = list(
            item.get("_role_reasons", {}).get(role, [])
        )
        item.pop("_role_reasons", None)

    def _measure_image(self, image: "Image.Image") -> Dict[str, float]:
        width, height = image.size
        sample = image.copy()
        sample.thumbnail((512, 512), Image.Resampling.LANCZOS)
        arr = np.asarray(sample, dtype=np.float32) / 255.0
        gray = arr.mean(axis=2)

        gx = np.abs(np.diff(gray, axis=1))
        gy = np.abs(np.diff(gray, axis=0))
        edge_density = float(
            (gx > 0.12).mean() * 0.5 + (gy > 0.12).mean() * 0.5
        )

        bright_ratio = float((gray > 0.88).mean())
        dark_ratio = float((gray < 0.28).mean())
        text_like_ratio = min(
            1.0,
            edge_density
            * (0.7 + bright_ratio)
            * (0.8 + dark_ratio * 2.0),
        )

        channel_std = arr.std(axis=(0, 1))
        colorfulness = float(channel_std.mean() * 4.0)
        luma_std = float(gray.std())
        photo_ratio = min(
            1.0,
            luma_std * 3.2 + colorfulness * 0.55 + edge_density * 0.7,
        )

        if ImageFilter is not None and ImageStat is not None:
            edges = sample.convert("L").filter(ImageFilter.FIND_EDGES)
            sharpness = min(
                1.0,
                float(ImageStat.Stat(edges).var[0] / 1500.0),
            )
        else:
            sharpness = min(1.0, edge_density)

        sample_h, sample_w = gray.shape
        y1, y2 = int(sample_h * 0.2), int(sample_h * 0.8)
        x1, x2 = int(sample_w * 0.2), int(sample_w * 0.8)
        center = gray[y1:y2, x1:x2]
        center_activity = float(center.std()) if center.size else 0.0

        top = gray[: max(1, int(sample_h * 0.28))]
        bottom = gray[int(sample_h * 0.72):]
        top_text_density = self._region_edge_density(top)
        bottom_text_density = self._region_edge_density(bottom)

        mid = sample_w // 2
        left = gray[:, :mid]
        right = gray[:, mid:]
        if left.size and right.size:
            common_w = min(left.shape[1], right.shape[1])
            split = float(
                np.mean(np.abs(left[:, :common_w] - right[:, :common_w]))
            )
        else:
            split = 0.0

        panel_count = self._estimate_panel_count(gray)

        return {
            "width": float(width),
            "height": float(height),
            "area": float(width * height),
            "aspect": float(width / max(1, height)),
            "photo_ratio": photo_ratio,
            "text_like_ratio": text_like_ratio,
            "sharpness": sharpness,
            "colorfulness": min(1.0, colorfulness),
            "bright_ratio": bright_ratio,
            "dark_ratio": dark_ratio,
            "edge_density": edge_density,
            "center_activity": min(1.0, center_activity * 3.0),
            "top_text_density": top_text_density,
            "bottom_text_density": bottom_text_density,
            "left_right_split": min(1.0, split),
            "panel_count": panel_count,
        }

    @staticmethod
    def _region_edge_density(region: "np.ndarray") -> float:
        if region.size == 0 or min(region.shape) < 2:
            return 0.0
        gx = np.abs(np.diff(region, axis=1))
        gy = np.abs(np.diff(region, axis=0))
        return float(
            (gx > 0.12).mean() * 0.5 + (gy > 0.12).mean() * 0.5
        )

    @staticmethod
    def _estimate_panel_count(gray: "np.ndarray") -> int:
        height, width = gray.shape
        if width < 20:
            return 1
        column_change = np.mean(np.abs(np.diff(gray, axis=1)), axis=0)
        threshold = max(0.10, float(column_change.mean() + column_change.std()))
        separators = np.where(column_change > threshold)[0]
        if len(separators) < 2:
            return 1

        groups = 1
        last = int(separators[0])
        for value in separators[1:]:
            value = int(value)
            if value - last > max(8, width // 8):
                groups += 1
            last = value
        return min(4, max(1, groups))

    def _quality_score(self, metrics: Dict[str, float]) -> float:
        width = metrics["width"]
        height = metrics["height"]
        area = metrics["area"]
        aspect = metrics["aspect"]

        size_score = min(1.0, area / 500_000.0) * 24.0
        dimension_score = min(
            1.0, min(width / 720.0, height / 540.0)
        ) * 14.0
        photo_score = metrics["photo_ratio"] * 30.0
        sharpness_score = metrics["sharpness"] * 12.0
        color_score = metrics["colorfulness"] * 8.0
        text_penalty = metrics["text_like_ratio"] * 18.0

        aspect_penalty = 0.0
        if aspect > 3.2 or aspect < 0.20:
            aspect_penalty = 28.0
        elif aspect > 2.2 or aspect < 0.32:
            aspect_penalty = 12.0

        return max(
            0.0,
            min(
                100.0,
                size_score
                + dimension_score
                + photo_score
                + sharpness_score
                + color_score
                - text_penalty
                - aspect_penalty,
            ),
        )

    def _read_ocr(self, image: "Image.Image") -> str:
        if not self.enable_ocr:
            self._ocr_engine_name = "disabled"
            return ""

        if self._pytesseract is None:
            try:
                import pytesseract  # type: ignore
                self._pytesseract = pytesseract
                self._ocr_engine_name = "pytesseract"
            except Exception:
                self._pytesseract = False
                self._ocr_engine_name = "unavailable"

        if not self._pytesseract:
            return ""

        try:
            sample = image.copy()
            sample.thumbnail((1400, 1800), Image.Resampling.LANCZOS)
            text = self._pytesseract.image_to_string(
                sample,
                lang="kor+eng",
                config="--psm 6",
            )
            return str(text or "")
        except Exception:
            try:
                text = self._pytesseract.image_to_string(
                    image,
                    lang="eng",
                    config="--psm 6",
                )
                return str(text or "")
            except Exception:
                return ""

    @staticmethod
    def _clean_text(value: Any) -> str:
        text = str(value or "")
        text = text.replace("\x00", " ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()[:4000]

    @staticmethod
    def _normalize_labels(value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, str):
            candidates = re.split(r"[,|;/\n]+", value)
        elif isinstance(value, dict):
            candidates = list(value.keys())
        elif isinstance(value, Iterable):
            candidates = list(value)
        else:
            candidates = [value]
        result = []
        seen = set()
        for item in candidates:
            if isinstance(item, dict):
                item = (
                    item.get("label")
                    or item.get("name")
                    or item.get("tag")
                    or item.get("text")
                )
            text = str(item or "").strip()
            key = text.lower()
            if text and key not in seen:
                seen.add(key)
                result.append(text)
        return result[:80]

    def _normalize_source_records(self, value: Any) -> List[Dict[str, Any]]:
        if value is None:
            return []

        if isinstance(value, (str, Path)):
            candidates: Sequence[Any] = [value]
        elif isinstance(value, dict):
            nested = (
                value.get("images")
                or value.get("image_paths")
                or value.get("files")
            )
            candidates = nested if nested is not None else [value]
        elif isinstance(value, Iterable):
            candidates = list(value)
        else:
            candidates = [value]

        records: List[Dict[str, Any]] = []
        seen = set()

        for item in candidates:
            metadata: Dict[str, Any] = {}
            if isinstance(item, dict):
                metadata = dict(item)
                path_value = (
                    item.get("source_path")
                    or item.get("original_path")
                    or item.get("path")
                    or item.get("file_path")
                    or item.get("output_path")
                    or item.get("image_path")
                    or item.get("file")
                )
            else:
                path_value = item

            if not path_value:
                continue

            path = Path(str(path_value))
            key = str(path).lower()
            if key in seen:
                continue
            seen.add(key)

            metadata["path"] = str(path)
            records.append(metadata)

        return records

    def _discover_review_image_records(self, project_id: Any) -> List[Dict[str, Any]]:
        project_text = str(project_id or "").strip()
        if not project_text:
            return []

        project_names = [
            f"project_{project_text}",
            project_text,
        ]
        roots = [
            Path("assets") / "review_images",
            Path.cwd() / "assets" / "review_images",
        ]

        records: List[Dict[str, Any]] = []
        seen = set()
        for root in roots:
            for project_name in project_names:
                folder = root / project_name
                if not folder.is_dir():
                    continue
                for path in sorted(folder.rglob("*")):
                    if not self._is_supported_image(path):
                        continue
                    key = str(path.resolve()).lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    records.append({
                        "path": str(path),
                        "source_type": "review_image",
                        "vision_labels": ["review", "customer_review"],
                    })
        return records

    @staticmethod
    def _merge_source_records(
        product_records: List[Dict[str, Any]],
        review_records: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        merged: List[Dict[str, Any]] = []
        seen = set()
        for record in [*product_records, *review_records]:
            path = Path(str(record.get("path") or ""))
            if not str(path):
                continue
            try:
                key = str(path.resolve()).lower()
            except Exception:
                key = str(path).lower()
            if key in seen:
                continue
            seen.add(key)
            merged.append(dict(record))
        return merged

    def _perceptual_hash(self, image: "Image.Image") -> str:
        gray = ImageOps.grayscale(image).resize(
            (16, 16), Image.Resampling.LANCZOS
        )
        arr = np.asarray(gray, dtype=np.float32)
        blocks = arr.reshape(8, 2, 8, 2).mean(axis=(1, 3))
        median = float(np.median(blocks))
        bits = (blocks >= median).flatten()
        value = 0
        for bit in bits:
            value = (value << 1) | int(bool(bit))
        return f"{value:016x}"

    @staticmethod
    def _hamming_distance(left: str, right: str) -> int:
        try:
            return (int(left, 16) ^ int(right, 16)).bit_count()
        except Exception:
            return 64

    @staticmethod
    def _reject(record: Dict[str, Any], reason: str) -> Dict[str, Any]:
        clean = {
            key: value
            for key, value in record.items()
            if key not in {"_image", "_role_reasons"}
        }
        clean["reason"] = str(reason)
        return clean

    def _is_supported_image(self, path: Path) -> bool:
        return (
            path.is_file()
            and path.suffix.lower() in self.SUPPORTED_SUFFIXES
        )

    def _clear_generated_files(self, output_dir: Path) -> None:
        for pattern in ("extract_*.png", "selected_*.png"):
            for path in output_dir.glob(pattern):
                try:
                    path.unlink()
                except OSError:
                    pass

        manifest = output_dir / self.MANIFEST_NAME
        if manifest.exists():
            try:
                manifest.unlink()
            except OSError:
                pass

    @staticmethod
    def _write_manifest(path: Path, result: Dict[str, Any]) -> None:
        path.write_text(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )


ProductImageExtractor = ImageExtractor