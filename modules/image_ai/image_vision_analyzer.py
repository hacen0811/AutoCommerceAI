from __future__ import annotations

import hashlib
import json
import math
import statistics
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


class ImageVisionAnalyzer:
    """
    Sprint93-2 Image Vision Analyzer

    역할:
    - Sprint93-1 MultiImageCollector가 저장한 상품 이미지를 읽음
    - 이미지 크기, 화면비, 선명도, 밝기, 대비, 정보량을 분석
    - 대표컷/상세컷/세로 상세페이지/확대컷에 적합한 용도를 추천
    - 분석 결과를 vision_analysis.json으로 저장

    안전 원칙:
    - Pillow가 없거나 일부 이미지가 손상되어도 전체 분석을 중단하지 않음
    - 원본 이미지를 변경하지 않음
    - 외부 API 호출 없이 로컬에서 동작
    """

    VERSION = "image-vision-analyzer-93-2"

    SUPPORTED_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".bmp",
        ".gif",
    }

    def analyze(
        self,
        images: Any = None,
        manifest_path: Any = "",
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
            "manifest_path": str(manifest_path or "").strip(),
            "output_dir": "",
            "analysis_path": "",
            "input_count": 0,
            "analyzed_count": 0,
            "failed_count": 0,
            "images": [],
            "summary": {},
            "warnings": [],
            "errors": [],
            "elapsed_seconds": 0.0,
        }

        normalized_images = self._resolve_images(
            images=images,
            manifest_path=manifest_path,
        )
        result["input_count"] = len(normalized_images)

        resolved_output_dir = self._resolve_output_dir(
            output_dir=output_dir,
            manifest_path=manifest_path,
            images=normalized_images,
            project_id=project_id,
        )
        resolved_output_dir.mkdir(parents=True, exist_ok=True)
        result["output_dir"] = str(resolved_output_dir)

        if not normalized_images:
            result["status"] = "no_images"
            result["warnings"].append("분석할 상품 이미지가 없습니다")
            result["elapsed_seconds"] = round(time.time() - started_at, 3)
            if save_result:
                self._save_result(result, resolved_output_dir)
            return result

        try:
            from PIL import Image, ImageFilter, ImageStat
        except Exception as exc:
            result["status"] = "pillow_missing"
            result["errors"].append(
                f"Pillow import 실패: {type(exc).__name__}: {exc}"
            )
            result["elapsed_seconds"] = round(time.time() - started_at, 3)
            if save_result:
                self._save_result(result, resolved_output_dir)
            return result

        analyzed: List[Dict[str, Any]] = []
        failed_count = 0

        for index, item in enumerate(normalized_images, start=1):
            path = Path(str(item.get("path") or "")).expanduser()

            if not path.is_file():
                failed_count += 1
                analyzed.append(
                    self._failed_item(
                        item=item,
                        index=index,
                        status="file_missing",
                        error=f"이미지 파일이 없습니다: {path}",
                    )
                )
                continue

            if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                failed_count += 1
                analyzed.append(
                    self._failed_item(
                        item=item,
                        index=index,
                        status="unsupported_extension",
                        error=f"지원하지 않는 확장자입니다: {path.suffix}",
                    )
                )
                continue

            try:
                analyzed_item = self._analyze_one(
                    item=item,
                    index=index,
                    image_module=Image,
                    image_filter=ImageFilter,
                    image_stat=ImageStat,
                )
                analyzed.append(analyzed_item)
            except Exception as exc:
                failed_count += 1
                analyzed.append(
                    self._failed_item(
                        item=item,
                        index=index,
                        status="analysis_failed",
                        error=f"{type(exc).__name__}: {exc}",
                    )
                )

        successful = [
            item
            for item in analyzed
            if item.get("ok")
        ]

        result["images"] = analyzed
        result["analyzed_count"] = len(successful)
        result["failed_count"] = failed_count
        result["summary"] = self._build_summary(successful)
        result["ok"] = bool(successful)
        result["ready"] = bool(successful)
        result["status"] = (
            "analyzed"
            if successful and failed_count == 0
            else "partial"
            if successful
            else "failed"
        )
        result["elapsed_seconds"] = round(time.time() - started_at, 3)

        if save_result:
            self._save_result(result, resolved_output_dir)

        return result

    def _resolve_images(
        self,
        images: Any,
        manifest_path: Any,
    ) -> List[Dict[str, Any]]:
        items: List[Any] = []

        if isinstance(images, dict):
            nested = images.get("images")
            if isinstance(nested, list):
                items.extend(nested)
            elif images.get("path"):
                items.append(images)
        elif isinstance(images, (list, tuple, set)):
            items.extend(images)
        elif isinstance(images, (str, Path)) and str(images).strip():
            path = Path(str(images)).expanduser()
            if path.is_dir():
                items.extend(sorted(path.iterdir()))
            else:
                items.append(path)

        manifest_value = str(manifest_path or "").strip()
        if manifest_value:
            path = Path(manifest_value).expanduser()
            if path.is_file():
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    manifest_images = (
                        data.get("images", [])
                        if isinstance(data, dict)
                        else []
                    )
                    if isinstance(manifest_images, list):
                        items.extend(manifest_images)
                except Exception:
                    pass

        normalized: List[Dict[str, Any]] = []
        seen = set()

        for position, item in enumerate(items, start=1):
            if isinstance(item, dict):
                copied = dict(item)
                path_value = (
                    copied.get("path")
                    or copied.get("file_path")
                    or copied.get("image_path")
                    or copied.get("saved_path")
                    or ""
                )
            else:
                copied = {}
                path_value = item

            if not path_value:
                continue

            path = Path(str(path_value)).expanduser()
            dedupe_key = str(path).lower()

            if dedupe_key in seen:
                continue

            seen.add(dedupe_key)
            copied["path"] = str(path)
            copied.setdefault("source_index", position)
            normalized.append(copied)

        return normalized

    def _resolve_output_dir(
        self,
        output_dir: Any,
        manifest_path: Any,
        images: List[Dict[str, Any]],
        project_id: Any,
    ) -> Path:
        if str(output_dir or "").strip():
            return Path(str(output_dir)).expanduser()

        manifest_value = str(manifest_path or "").strip()
        if manifest_value:
            manifest = Path(manifest_value).expanduser()
            if manifest.parent:
                return manifest.parent

        if images:
            first_path = Path(str(images[0].get("path") or "")).expanduser()
            if first_path.parent:
                return first_path.parent

        project_key = str(project_id or "unknown").strip() or "unknown"
        return Path("assets") / "product_images" / f"project_{project_key}"

    def _analyze_one(
        self,
        item: Dict[str, Any],
        index: int,
        image_module: Any,
        image_filter: Any,
        image_stat: Any,
    ) -> Dict[str, Any]:
        path = Path(str(item.get("path") or "")).expanduser()

        with image_module.open(path) as opened:
            frame_count = int(getattr(opened, "n_frames", 1) or 1)
            opened.seek(0)
            rgb = opened.convert("RGB")
            width, height = rgb.size

            sample = rgb.copy()
            sample.thumbnail((512, 512))

            grayscale = sample.convert("L")
            gray_stat = image_stat.Stat(grayscale)
            mean_brightness = float(gray_stat.mean[0])
            std_contrast = float(gray_stat.stddev[0])

            edges = grayscale.filter(image_filter.FIND_EDGES)
            edge_stat = image_stat.Stat(edges)
            edge_mean = float(edge_stat.mean[0])

            histogram = grayscale.histogram()
            entropy = self._entropy(histogram)

            sharpness = self._sharpness_score(
                grayscale=grayscale,
                image_filter=image_filter,
                image_stat=image_stat,
            )

        file_size = int(path.stat().st_size)
        aspect_ratio = round(width / height, 4) if height else 0.0
        orientation = self._orientation(width, height)
        layout_type = self._layout_type(width, height)
        brightness_label = self._brightness_label(mean_brightness)
        contrast_label = self._contrast_label(std_contrast)
        sharpness_label = self._sharpness_label(sharpness)

        quality_score, quality_breakdown = self._quality_score(
            width=width,
            height=height,
            file_size=file_size,
            brightness=mean_brightness,
            contrast=std_contrast,
            entropy=entropy,
            sharpness=sharpness,
            edge_mean=edge_mean,
        )

        recommended_uses = self._recommended_uses(
            orientation=orientation,
            layout_type=layout_type,
            width=width,
            height=height,
            quality_score=quality_score,
            sharpness=sharpness,
            source_type=str(item.get("type") or ""),
        )

        visual_tags = self._visual_tags(
            orientation=orientation,
            layout_type=layout_type,
            brightness_label=brightness_label,
            contrast_label=contrast_label,
            sharpness_label=sharpness_label,
            width=width,
            height=height,
            frame_count=frame_count,
        )

        return {
            "ok": True,
            "status": "analyzed",
            "index": index,
            "path": str(path),
            "filename": path.name,
            "type": str(item.get("type") or item.get("original_type") or "unknown"),
            "source": str(item.get("source") or "unknown"),
            "url": str(item.get("url") or ""),
            "sha256": self._sha256(path),
            "format": path.suffix.lower().lstrip("."),
            "file_size_bytes": file_size,
            "width": width,
            "height": height,
            "megapixels": round((width * height) / 1_000_000, 3),
            "aspect_ratio": aspect_ratio,
            "orientation": orientation,
            "layout_type": layout_type,
            "frame_count": frame_count,
            "brightness": round(mean_brightness, 3),
            "brightness_label": brightness_label,
            "contrast": round(std_contrast, 3),
            "contrast_label": contrast_label,
            "edge_density": round(edge_mean, 3),
            "entropy": round(entropy, 3),
            "sharpness": round(sharpness, 3),
            "sharpness_label": sharpness_label,
            "quality_score": quality_score,
            "quality_breakdown": quality_breakdown,
            "visual_tags": visual_tags,
            "recommended_uses": recommended_uses,
            "primary_use": recommended_uses[0] if recommended_uses else "detail",
            "warnings": self._item_warnings(
                width=width,
                height=height,
                brightness=mean_brightness,
                contrast=std_contrast,
                sharpness=sharpness,
                file_size=file_size,
            ),
            "errors": [],
        }

    def _failed_item(
        self,
        item: Dict[str, Any],
        index: int,
        status: str,
        error: str,
    ) -> Dict[str, Any]:
        return {
            "ok": False,
            "status": status,
            "index": index,
            "path": str(item.get("path") or ""),
            "filename": Path(str(item.get("path") or "")).name,
            "type": str(item.get("type") or item.get("original_type") or "unknown"),
            "source": str(item.get("source") or "unknown"),
            "quality_score": 0.0,
            "visual_tags": [],
            "recommended_uses": [],
            "primary_use": "",
            "warnings": [],
            "errors": [error],
        }

    def _entropy(self, histogram: Iterable[int]) -> float:
        values = [int(value) for value in histogram]
        total = sum(values)
        if total <= 0:
            return 0.0

        entropy = 0.0
        for value in values:
            if value <= 0:
                continue
            probability = value / total
            entropy -= probability * math.log2(probability)
        return entropy

    def _sharpness_score(
        self,
        grayscale: Any,
        image_filter: Any,
        image_stat: Any,
    ) -> float:
        blurred = grayscale.filter(image_filter.GaussianBlur(radius=2))
        difference = self._difference_image(
            grayscale,
            blurred,
        )
        stat = image_stat.Stat(difference)
        return float(stat.mean[0])

    def _difference_image(self, image_a: Any, image_b: Any) -> Any:
        from PIL import ImageChops
        return ImageChops.difference(image_a, image_b)

    def _quality_score(
        self,
        width: int,
        height: int,
        file_size: int,
        brightness: float,
        contrast: float,
        entropy: float,
        sharpness: float,
        edge_mean: float,
    ) -> Tuple[float, Dict[str, float]]:
        long_side = max(width, height)
        short_side = min(width, height)

        resolution_score = min(100.0, (long_side / 1600.0) * 70.0 + (short_side / 900.0) * 30.0)
        brightness_score = max(0.0, 100.0 - abs(brightness - 145.0) * 0.9)
        contrast_score = min(100.0, max(0.0, contrast * 2.2))
        entropy_score = min(100.0, max(0.0, entropy / 8.0 * 100.0))
        sharpness_score = min(100.0, max(0.0, sharpness * 9.0))
        edge_score = min(100.0, max(0.0, edge_mean * 3.0))
        size_score = min(100.0, max(0.0, file_size / 350_000.0 * 100.0))

        breakdown = {
            "resolution": round(resolution_score, 2),
            "brightness": round(brightness_score, 2),
            "contrast": round(contrast_score, 2),
            "information": round(entropy_score, 2),
            "sharpness": round(sharpness_score, 2),
            "edge_detail": round(edge_score, 2),
            "file_size": round(size_score, 2),
        }

        score = (
            resolution_score * 0.28
            + brightness_score * 0.12
            + contrast_score * 0.12
            + entropy_score * 0.12
            + sharpness_score * 0.20
            + edge_score * 0.08
            + size_score * 0.08
        )
        return round(min(100.0, max(0.0, score)), 2), breakdown

    def _orientation(self, width: int, height: int) -> str:
        if width <= 0 or height <= 0:
            return "unknown"
        ratio = width / height
        if 0.92 <= ratio <= 1.08:
            return "square"
        return "landscape" if ratio > 1.0 else "portrait"

    def _layout_type(self, width: int, height: int) -> str:
        if width <= 0 or height <= 0:
            return "unknown"

        ratio = height / width
        if ratio >= 3.0:
            return "long_detail_page"
        if ratio >= 1.55:
            return "vertical_detail"
        if ratio <= 0.68:
            return "wide_banner"
        if 0.9 <= ratio <= 1.1:
            return "square_product"
        return "standard_product"

    def _brightness_label(self, value: float) -> str:
        if value < 65:
            return "dark"
        if value < 115:
            return "slightly_dark"
        if value < 205:
            return "balanced"
        return "bright"

    def _contrast_label(self, value: float) -> str:
        if value < 25:
            return "low"
        if value < 55:
            return "medium"
        return "high"

    def _sharpness_label(self, value: float) -> str:
        if value < 2.0:
            return "soft"
        if value < 5.5:
            return "normal"
        return "sharp"

    def _recommended_uses(
        self,
        orientation: str,
        layout_type: str,
        width: int,
        height: int,
        quality_score: float,
        sharpness: float,
        source_type: str,
    ) -> List[str]:
        uses: List[str] = []

        if (
            quality_score >= 65
            and source_type == "main"
            and layout_type in {"square_product", "standard_product"}
        ):
            uses.extend(["opening", "hero", "thumbnail"])

        if layout_type == "long_detail_page":
            uses.extend(["detail_page_crop", "feature_extraction"])

        if layout_type == "vertical_detail":
            uses.extend(["vertical_scene", "feature_extraction"])

        if orientation == "portrait":
            uses.append("shorts_scene")

        if orientation in {"square", "landscape"} and quality_score >= 55:
            uses.append("product_closeup")

        if sharpness >= 5.5 and min(width, height) >= 700:
            uses.append("detail_closeup")

        if quality_score >= 70:
            uses.append("veo_reference")

        if not uses:
            uses.append("detail")

        deduped: List[str] = []
        for value in uses:
            if value not in deduped:
                deduped.append(value)
        return deduped

    def _visual_tags(
        self,
        orientation: str,
        layout_type: str,
        brightness_label: str,
        contrast_label: str,
        sharpness_label: str,
        width: int,
        height: int,
        frame_count: int,
    ) -> List[str]:
        tags = [
            orientation,
            layout_type,
            f"brightness_{brightness_label}",
            f"contrast_{contrast_label}",
            f"sharpness_{sharpness_label}",
        ]

        if min(width, height) >= 1080:
            tags.append("high_resolution")
        elif min(width, height) < 500:
            tags.append("low_resolution")

        if frame_count > 1:
            tags.append("animated")

        return tags

    def _item_warnings(
        self,
        width: int,
        height: int,
        brightness: float,
        contrast: float,
        sharpness: float,
        file_size: int,
    ) -> List[str]:
        warnings: List[str] = []

        if min(width, height) < 500:
            warnings.append("해상도가 낮아 확대 장면에 부적합할 수 있습니다")
        if brightness < 55:
            warnings.append("이미지가 너무 어둡습니다")
        if brightness > 225:
            warnings.append("이미지가 너무 밝습니다")
        if contrast < 18:
            warnings.append("대비가 낮아 제품 경계가 흐릴 수 있습니다")
        if sharpness < 1.5:
            warnings.append("선명도가 낮습니다")
        if file_size < 25_000:
            warnings.append("파일 용량이 매우 작습니다")

        return warnings

    def _build_summary(
        self,
        items: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not items:
            return {
                "best_image": {},
                "best_opening_image": {},
                "best_veo_reference": {},
                "average_quality_score": 0.0,
                "orientation_counts": {},
                "layout_counts": {},
                "recommended_use_counts": {},
            }

        quality_scores = [
            float(item.get("quality_score") or 0.0)
            for item in items
        ]

        orientation_counts: Dict[str, int] = {}
        layout_counts: Dict[str, int] = {}
        use_counts: Dict[str, int] = {}

        for item in items:
            orientation = str(item.get("orientation") or "unknown")
            layout = str(item.get("layout_type") or "unknown")
            orientation_counts[orientation] = orientation_counts.get(orientation, 0) + 1
            layout_counts[layout] = layout_counts.get(layout, 0) + 1

            for use in item.get("recommended_uses", []):
                use_counts[use] = use_counts.get(use, 0) + 1

        best_image = max(
            items,
            key=lambda item: float(item.get("quality_score") or 0.0),
        )

        opening_candidates = [
            item
            for item in items
            if "opening" in item.get("recommended_uses", [])
        ]
        veo_candidates = [
            item
            for item in items
            if "veo_reference" in item.get("recommended_uses", [])
        ]

        best_opening = max(
            opening_candidates or items,
            key=lambda item: float(item.get("quality_score") or 0.0),
        )
        best_veo = max(
            veo_candidates or items,
            key=lambda item: float(item.get("quality_score") or 0.0),
        )

        return {
            "best_image": self._summary_item(best_image),
            "best_opening_image": self._summary_item(best_opening),
            "best_veo_reference": self._summary_item(best_veo),
            "average_quality_score": round(statistics.mean(quality_scores), 2),
            "minimum_quality_score": round(min(quality_scores), 2),
            "maximum_quality_score": round(max(quality_scores), 2),
            "orientation_counts": orientation_counts,
            "layout_counts": layout_counts,
            "recommended_use_counts": use_counts,
        }

    def _summary_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "path": str(item.get("path") or ""),
            "filename": str(item.get("filename") or ""),
            "type": str(item.get("type") or ""),
            "quality_score": float(item.get("quality_score") or 0.0),
            "orientation": str(item.get("orientation") or ""),
            "layout_type": str(item.get("layout_type") or ""),
            "primary_use": str(item.get("primary_use") or ""),
            "recommended_uses": list(item.get("recommended_uses") or []),
        }

    def _sha256(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _save_result(
        self,
        result: Dict[str, Any],
        output_dir: Path,
    ) -> None:
        analysis_path = output_dir / "vision_analysis.json"
        result["analysis_path"] = str(analysis_path)
        analysis_path.write_text(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )