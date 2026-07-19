from __future__ import annotations

import hashlib
import io
import json
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from PIL import Image, ImageChops, ImageStat


class ImageStripSplitter:
    """
    Sprint105-1 Smart Image Strip Engine

    역할:
    - 세로로 이어진 상품 이미지 스트립 1장을 자동 분할
    - 여러 장 직접 업로드도 그대로 지원
    - Streamlit UploadedFile, bytes, 파일 경로를 모두 입력으로 지원
    - 분할 결과를 00_main.png, 01_detail.png ... 형식으로 저장
    - MultiImageCollector와 호환되는 manifest.json 구조 생성
    - 원본 이미지 보존 여부 선택 가능
    """

    VERSION = "smart-image-strip-105-1"
    SOURCE_VERSION = "image-strip-splitter-98-6"

    IMAGE_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".bmp",
    }

    def process(
        self,
        uploaded_images: Any,
        project_id: Any = "",
        product_name: str = "",
        output_dir: Any = "",
        max_images: int = 40,
        split_strip: bool = True,
        white_threshold: int = 245,
        min_gap_height: int = 12,
        min_segment_height: int = 40,
        min_segment_width: int = 40,
        min_content_ratio: float = 0.015,
        preserve_original: bool = False,
        clear_previous: bool = True,
    ) -> Dict[str, Any]:
        started_at = time.time()
        max_images = max(1, min(int(max_images or 40), 100))

        result = self._empty_result(
            project_id=project_id,
            product_name=product_name,
        )

        resolved_output_dir = self._resolve_output_dir(
            output_dir=output_dir,
            project_id=project_id,
            product_name=product_name,
        )
        resolved_output_dir.mkdir(parents=True, exist_ok=True)

        result["output_dir"] = str(resolved_output_dir)

        inputs = self._normalize_inputs(uploaded_images)
        result["input_count"] = len(inputs)

        if not inputs:
            result["status"] = "input_missing"
            result["errors"].append("업로드된 이미지가 없습니다")
            return self._write_manifest(result, resolved_output_dir, started_at)

        if clear_previous:
            self._clear_previous_images(resolved_output_dir)

        saved_images: List[Dict[str, Any]] = []
        seen_hashes = set()
        source_summaries: List[Dict[str, Any]] = []

        for input_index, source in enumerate(inputs):
            if len(saved_images) >= max_images:
                break

            try:
                source_name, source_bytes = self._read_source(source, input_index)
                image = self._open_image(source_bytes)
            except Exception as exc:
                result["warnings"].append(
                    f"입력 이미지 읽기 실패 #{input_index + 1}: "
                    f"{type(exc).__name__}: {exc}"
                )
                continue

            width, height = image.size
            is_strip = bool(
                split_strip
                and len(inputs) == 1
                and self._looks_like_vertical_strip(image)
            )

            segments: List[Tuple[int, int]] = [(0, height)]
            split_method = "single_image"

            if is_strip:
                segments = self._find_segments(
                    image=image,
                    white_threshold=white_threshold,
                    min_gap_height=min_gap_height,
                    min_segment_height=min_segment_height,
                    min_content_ratio=min_content_ratio,
                )
                split_method = (
                    "photo_block"
                    if len(segments) > 1
                    else "strip_fallback_single"
                )

            source_summary = {
                "input_index": input_index,
                "source_name": source_name,
                "width": width,
                "height": height,
                "detected_as_strip": is_strip,
                "split_method": split_method,
                "segment_count": len(segments),
                "segments": [
                    {"top": top, "bottom": bottom, "height": bottom - top}
                    for top, bottom in segments
                ],
            }
            source_summaries.append(source_summary)

            if preserve_original:
                original_path = (
                    resolved_output_dir
                    / "_original"
                    / f"{input_index:02d}_{self._safe_name(source_name)}.png"
                )
                original_path.parent.mkdir(parents=True, exist_ok=True)
                image.save(original_path, format="PNG")

            for segment_index, (top, bottom) in enumerate(segments):
                if len(saved_images) >= max_images:
                    break

                segment = image.crop((0, top, width, bottom))
                segment = self._trim_outer_whitespace(
                    segment,
                    white_threshold=white_threshold,
                )

                segment_width, segment_height = segment.size

                if (
                    segment_width < min_segment_width
                    or segment_height < min_segment_height
                ):
                    result["warnings"].append(
                        f"너무 작은 분할 영역 제외: "
                        f"{segment_width}x{segment_height}"
                    )
                    continue

                if not self._has_meaningful_content(
                    segment,
                    white_threshold=white_threshold,
                    min_content_ratio=min_content_ratio,
                ):
                    result["warnings"].append(
                        f"내용이 거의 없는 분할 영역 제외: "
                        f"{source_name} #{segment_index + 1}"
                    )
                    continue

                encoded = self._encode_png(segment)
                digest = hashlib.sha256(encoded).hexdigest()

                if digest in seen_hashes:
                    result["duplicate_count"] += 1
                    continue

                seen_hashes.add(digest)

                index = len(saved_images)
                image_type = "main" if index == 0 else "detail"
                filename = (
                    "00_main.png"
                    if index == 0
                    else f"{index:02d}_detail.png"
                )
                target = resolved_output_dir / filename
                target.write_bytes(encoded)

                saved_images.append(
                    {
                        "index": index,
                        "type": image_type,
                        "url": "",
                        "path": str(target),
                        "filename": filename,
                        "extension": ".png",
                        "content_type": "image/png",
                        "size_bytes": len(encoded),
                        "sha256": digest,
                        "source": "manual_image_strip"
                        if is_strip
                        else "manual_multi_upload",
                        "source_name": source_name,
                        "source_index": input_index,
                        "segment_index": segment_index,
                        "crop_top": top,
                        "crop_bottom": bottom,
                        "width": segment_width,
                        "height": segment_height,
                    }
                )

        result["images"] = saved_images
        result["image_count"] = len(saved_images)
        result["main_image_count"] = sum(
            1 for item in saved_images if item.get("type") == "main"
        )
        result["detail_image_count"] = sum(
            1 for item in saved_images if item.get("type") == "detail"
        )
        result["option_image_count"] = 0
        result["candidate_count"] = sum(
            item.get("segment_count", 0)
            for item in source_summaries
        )
        result["source_summaries"] = source_summaries
        result["split_count"] = len(saved_images)
        result["strip_detected"] = any(
            item.get("detected_as_strip")
            for item in source_summaries
        )
        result["ok"] = bool(saved_images)
        result["ready"] = bool(saved_images)
        result["status"] = (
            "split"
            if result["strip_detected"] and saved_images
            else "imported"
            if saved_images
            else "empty"
        )

        if not saved_images:
            result["errors"].append("저장된 이미지가 없습니다")

        return self._write_manifest(result, resolved_output_dir, started_at)

    def _empty_result(
        self,
        project_id: Any,
        product_name: str,
    ) -> Dict[str, Any]:
        return {
            "ok": False,
            "ready": False,
            "version": self.VERSION,
            "source_version": self.SOURCE_VERSION,
            "status": "not_run",
            "source": "manual_image_upload",
            "coupang_url": "",
            "final_url": "",
            "http_status": None,
            "page_title": "",
            "project_id": str(project_id or ""),
            "product_name": str(product_name or "").strip(),
            "profile_dir": "",
            "output_dir": "",
            "manifest_path": "",
            "debug_html_path": "",
            "screenshot_path": "",
            "input_count": 0,
            "image_count": 0,
            "main_image_count": 0,
            "detail_image_count": 0,
            "option_image_count": 0,
            "thumbnail_count": 0,
            "detail_candidate_count": 0,
            "candidate_count": 0,
            "download_failed_count": 0,
            "split_count": 0,
            "duplicate_count": 0,
            "strip_detected": False,
            "images": [],
            "source_summaries": [],
            "warnings": [],
            "errors": [],
            "elapsed_seconds": 0.0,
        }

    def _normalize_inputs(self, uploaded_images: Any) -> List[Any]:
        if uploaded_images is None:
            return []

        if isinstance(uploaded_images, (str, Path, bytes, bytearray)):
            return [uploaded_images]

        if hasattr(uploaded_images, "getvalue") or hasattr(
            uploaded_images,
            "read",
        ):
            return [uploaded_images]

        if isinstance(uploaded_images, Sequence):
            return [
                item
                for item in uploaded_images
                if item is not None
            ]

        if isinstance(uploaded_images, Iterable):
            return [
                item
                for item in uploaded_images
                if item is not None
            ]

        return [uploaded_images]

    def _read_source(
        self,
        source: Any,
        index: int,
    ) -> Tuple[str, bytes]:
        if isinstance(source, Path):
            return source.name, source.read_bytes()

        if isinstance(source, str):
            path = Path(source).expanduser()
            return path.name, path.read_bytes()

        if isinstance(source, (bytes, bytearray)):
            return f"uploaded_{index + 1}.png", bytes(source)

        name = str(
            getattr(source, "name", "")
            or f"uploaded_{index + 1}.png"
        )

        if hasattr(source, "getvalue"):
            data = source.getvalue()
            return name, bytes(data)

        if hasattr(source, "read"):
            try:
                current_position = source.tell()
            except Exception:
                current_position = None

            data = source.read()

            if current_position is not None:
                try:
                    source.seek(current_position)
                except Exception:
                    pass

            return name, bytes(data)

        raise TypeError(
            f"지원하지 않는 이미지 입력 형식입니다: {type(source).__name__}"
        )

    def _open_image(self, data: bytes) -> Image.Image:
        image = Image.open(io.BytesIO(data))
        image.load()

        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")

        if image.mode == "RGBA":
            background = Image.new("RGB", image.size, "white")
            background.paste(image, mask=image.getchannel("A"))
            image = background

        return image

    def _looks_like_vertical_strip(self, image: Image.Image) -> bool:
        width, height = image.size

        if width <= 0 or height <= 0:
            return False

        return height >= width * 1.2 and height >= 300

    def _find_segments(
        self,
        image: Image.Image,
        white_threshold: int,
        min_gap_height: int,
        min_segment_height: int,
        min_content_ratio: float,
    ) -> List[Tuple[int, int]]:
        """
        Sprint105-1 사진 블록 중심 세로 스트립 분할.

        기존처럼 작은 밝기 변화마다 경계를 만드는 대신 다음 순서로 처리한다.
        1) 축소 이미지의 행별 사진성(photo-likeness)을 계산한다.
        2) 연속된 사진성 구간을 사진 블록 후보로 만든다.
        3) 짧은 텍스트/여백 구간은 인접 사진 블록에 병합한다.
        4) 지나치게 긴 블록만 안전한 저밀도 지점에서 재분할한다.
        5) 작은 아이콘·버튼·얇은 설명 조각은 독립 세그먼트로 만들지 않는다.

        반환 형식은 기존과 동일한 (top, bottom) 목록이므로 WorkflowEngine 및
        manifest 구조와의 호환성을 유지한다.
        """
        width, height = image.size

        if width <= 0 or height <= 0:
            return []

        analysis_width = min(width, 360)
        analysis_height = max(
            1,
            int(round(height * analysis_width / max(width, 1))),
        )
        analysis = image.resize(
            (analysis_width, analysis_height),
            Image.Resampling.BILINEAR,
        ).convert("RGB")
        scale_y = height / max(analysis_height, 1)

        row_non_white: List[float] = []
        row_brightness: List[float] = []
        row_variance: List[float] = []
        row_saturation: List[float] = []
        row_horizontal_detail: List[float] = []

        for y in range(analysis_height):
            row = list(analysis.crop((0, y, analysis_width, y + 1)).getdata())
            if not row:
                row_non_white.append(0.0)
                row_brightness.append(255.0)
                row_variance.append(0.0)
                row_saturation.append(0.0)
                row_horizontal_detail.append(0.0)
                continue

            gray_values: List[float] = []
            saturation_values: List[float] = []
            non_white = 0
            horizontal_detail = 0.0
            previous_gray: float | None = None

            for red, green, blue in row:
                gray = 0.299 * red + 0.587 * green + 0.114 * blue
                gray_values.append(gray)
                maximum = max(red, green, blue)
                minimum = min(red, green, blue)
                saturation_values.append(
                    0.0 if maximum <= 0 else (maximum - minimum) / maximum
                )

                if min(red, green, blue) < white_threshold:
                    non_white += 1

                if previous_gray is not None:
                    horizontal_detail += abs(gray - previous_gray)
                previous_gray = gray

            count = max(len(row), 1)
            mean_gray = sum(gray_values) / count
            variance = sum(
                (value - mean_gray) ** 2 for value in gray_values
            ) / count

            row_non_white.append(non_white / count)
            row_brightness.append(mean_gray)
            row_variance.append(variance ** 0.5)
            row_saturation.append(sum(saturation_values) / count)
            row_horizontal_detail.append(
                horizontal_detail / max(count - 1, 1)
            )

        def smooth(values: List[float], radius: int) -> List[float]:
            if not values:
                return []
            prefix = [0.0]
            for value in values:
                prefix.append(prefix[-1] + value)
            result: List[float] = []
            for index in range(len(values)):
                left = max(0, index - radius)
                right = min(len(values), index + radius + 1)
                result.append(
                    (prefix[right] - prefix[left]) / max(right - left, 1)
                )
            return result

        smooth_non_white = smooth(row_non_white, radius=3)
        smooth_brightness = smooth(row_brightness, radius=3)
        smooth_variance = smooth(row_variance, radius=4)
        smooth_saturation = smooth(row_saturation, radius=4)
        smooth_detail = smooth(row_horizontal_detail, radius=3)

        scaled_min_gap = max(
            2,
            int(round(min_gap_height / max(scale_y, 0.001))),
        )
        scaled_min_segment = max(
            10,
            int(round(min_segment_height / max(scale_y, 0.001))),
        )

        # 제품 사진은 일반적으로 충분한 면적, 색 변화, 질감 중 둘 이상을 가진다.
        photo_scores: List[float] = []
        for index in range(analysis_height):
            density = smooth_non_white[index]
            variance = smooth_variance[index]
            saturation = smooth_saturation[index]
            detail = smooth_detail[index]
            brightness = smooth_brightness[index]

            score = 0.0
            score += min(3.0, density * 5.0)
            score += min(2.5, variance / 18.0)
            score += min(2.0, saturation * 7.0)
            score += min(2.5, detail / 10.0)

            # 거의 흰 여백은 사진 점수를 강하게 낮춘다.
            if density < max(0.008, min_content_ratio * 0.55):
                score -= 4.0
            if brightness >= 250 and density < 0.03:
                score -= 2.0

            photo_scores.append(score)

        smooth_photo_scores = smooth(photo_scores, radius=5)
        active_threshold = 2.15
        active_rows = [score >= active_threshold for score in smooth_photo_scores]

        # 짧은 비활성 구간은 사진 속 텍스트/여백일 가능성이 크므로 메운다.
        maximum_internal_gap = max(
            scaled_min_gap * 4,
            int(round(analysis_width * 0.16)),
        )
        gap_start: int | None = None
        for y, active in enumerate(active_rows + [True]):
            if not active and gap_start is None:
                gap_start = y
            elif active and gap_start is not None:
                gap_end = y
                left_active = gap_start > 0 and active_rows[gap_start - 1]
                right_active = gap_end < analysis_height and (
                    active_rows[gap_end] if gap_end < analysis_height else False
                )
                if (
                    left_active
                    and right_active
                    and gap_end - gap_start <= maximum_internal_gap
                ):
                    for fill_y in range(gap_start, gap_end):
                        active_rows[fill_y] = True
                gap_start = None

        # 짧은 활성 조각은 아이콘/버튼일 가능성이 높으므로 제거한다.
        minimum_photo_run = max(
            scaled_min_segment,
            int(round(analysis_width * 0.42)),
        )
        run_start: int | None = None
        for y, active in enumerate(active_rows + [False]):
            if active and run_start is None:
                run_start = y
            elif not active and run_start is not None:
                if y - run_start < minimum_photo_run:
                    for remove_y in range(run_start, y):
                        active_rows[remove_y] = False
                run_start = None

        candidate_blocks: List[Tuple[int, int]] = []
        block_start: int | None = None
        for y, active in enumerate(active_rows + [False]):
            if active and block_start is None:
                block_start = y
            elif not active and block_start is not None:
                if y - block_start >= minimum_photo_run:
                    candidate_blocks.append((block_start, y))
                block_start = None

        # 인접한 사진 블록 사이의 짧은 설명문은 한 장면으로 병합한다.
        merged_blocks: List[Tuple[int, int]] = []
        merge_gap = max(
            scaled_min_gap * 6,
            int(round(analysis_width * 0.32)),
        )
        for top, bottom in candidate_blocks:
            if not merged_blocks:
                merged_blocks.append((top, bottom))
                continue

            previous_top, previous_bottom = merged_blocks[-1]
            gap = top - previous_bottom

            if gap <= merge_gap:
                gap_density = (
                    sum(smooth_non_white[previous_bottom:top]) / max(gap, 1)
                    if gap > 0
                    else 0.0
                )
                # 짧고 내용이 적은 간격은 사진 내부 설명 영역으로 판단한다.
                if gap_density < 0.22:
                    merged_blocks[-1] = (previous_top, bottom)
                    continue

            merged_blocks.append((top, bottom))

        # 원본 좌표로 변환하면서 약간의 문맥 여백을 포함한다.
        padding = max(4, int(round(width * 0.025)))
        original_blocks: List[Tuple[int, int]] = []
        for top, bottom in merged_blocks:
            original_top = max(0, int(round(top * scale_y)) - padding)
            original_bottom = min(
                height,
                int(round(bottom * scale_y)) + padding,
            )
            if original_bottom - original_top >= min_segment_height:
                original_blocks.append((original_top, original_bottom))

        # 너무 긴 사진 블록만 저밀도 지점에서 재분할한다.
        preferred_height = max(int(width * 1.35), min_segment_height * 4)
        maximum_height = max(int(width * 2.6), preferred_height * 2)
        refined_blocks: List[Tuple[int, int]] = []

        for top, bottom in original_blocks:
            block_height = bottom - top
            if block_height <= maximum_height:
                refined_blocks.append((top, bottom))
                continue

            piece_count = max(2, int(round(block_height / preferred_height)))
            cut_points = [top]

            for piece_index in range(1, piece_count):
                expected = int(round(top + block_height * piece_index / piece_count))
                search_radius = max(min_segment_height, int(width * 0.22))
                search_top = max(top + min_segment_height, expected - search_radius)
                search_bottom = min(bottom - min_segment_height, expected + search_radius)
                best_y = expected
                best_value = float("inf")

                for original_y in range(search_top, search_bottom + 1):
                    analysis_y = max(
                        0,
                        min(
                            analysis_height - 1,
                            int(round(original_y / max(scale_y, 0.001))),
                        ),
                    )
                    value = (
                        smooth_non_white[analysis_y] * 2.2
                        + max(0.0, smooth_photo_scores[analysis_y]) * 0.35
                    )
                    if value < best_value:
                        best_value = value
                        best_y = original_y

                if best_y - cut_points[-1] >= min_segment_height:
                    cut_points.append(best_y)

            cut_points.append(bottom)
            for split_top, split_bottom in zip(cut_points, cut_points[1:]):
                if split_bottom - split_top >= min_segment_height:
                    refined_blocks.append((split_top, split_bottom))

        # 사진 블록 검출 실패 시 기존처럼 무작정 잘게 자르지 않고,
        # 큰 세로 이미지일 때만 폭 기준의 안전한 폴백을 사용한다.
        if not refined_blocks and height >= width * 1.8:
            fallback_height = max(int(width * 1.5), min_segment_height * 5)
            fallback_count = max(2, min(12, int(round(height / fallback_height))))
            fallback_boundaries = [
                int(round(height * index / fallback_count))
                for index in range(fallback_count + 1)
            ]
            refined_blocks = [
                (top, bottom)
                for top, bottom in zip(
                    fallback_boundaries,
                    fallback_boundaries[1:],
                )
                if bottom - top >= min_segment_height
            ]

        # 최종 의미 있는 콘텐츠 검사 및 지나치게 작은 높이 제거.
        final_segments: List[Tuple[int, int]] = []
        minimum_final_height = max(min_segment_height, int(width * 0.55))
        for top, bottom in refined_blocks:
            if bottom - top < minimum_final_height:
                continue
            segment = image.crop((0, top, width, bottom))
            if self._has_meaningful_content(
                segment,
                white_threshold=white_threshold,
                min_content_ratio=max(0.004, min_content_ratio * 0.45),
            ):
                final_segments.append((top, bottom))

        return final_segments or [(0, height)]

    def _trim_outer_whitespace(
        self,
        image: Image.Image,
        white_threshold: int,
    ) -> Image.Image:
        rgb = image.convert("RGB")
        white = Image.new("RGB", rgb.size, (255, 255, 255))
        difference = ImageChops.difference(rgb, white).convert("L")

        mask = difference.point(
            lambda value: 255
            if value > max(1, 255 - white_threshold)
            else 0
        )
        box = mask.getbbox()

        if not box:
            return image

        left, top, right, bottom = box
        padding = 4

        left = max(0, left - padding)
        top = max(0, top - padding)
        right = min(image.width, right + padding)
        bottom = min(image.height, bottom + padding)

        return image.crop((left, top, right, bottom))

    def _has_meaningful_content(
        self,
        image: Image.Image,
        white_threshold: int,
        min_content_ratio: float,
    ) -> bool:
        sample = image.copy()
        sample.thumbnail((240, 240))
        rgb = sample.convert("RGB")

        pixels = list(rgb.getdata())

        if not pixels:
            return False

        non_white = sum(
            1
            for red, green, blue in pixels
            if min(red, green, blue) < white_threshold
        )

        ratio = non_white / len(pixels)
        return ratio >= min_content_ratio

    def _encode_png(self, image: Image.Image) -> bytes:
        buffer = io.BytesIO()
        image.save(
            buffer,
            format="PNG",
            optimize=True,
        )
        return buffer.getvalue()

    def _resolve_output_dir(
        self,
        output_dir: Any,
        project_id: Any,
        product_name: str,
    ) -> Path:
        if str(output_dir or "").strip():
            return Path(str(output_dir)).expanduser()

        project_value = str(project_id or "").strip()

        if project_value:
            folder_name = f"project_{self._safe_name(project_value)}"
        else:
            product_value = self._safe_name(product_name) or "manual"
            folder_name = f"product_{product_value}"

        # 현재 Sprint97 파이프라인 경로와 동일하게 사용
        return Path("assets") / "products" / folder_name

    def _clear_previous_images(self, output_dir: Path) -> None:
        for child in output_dir.iterdir():
            if not child.is_file():
                continue

            if child.name == "manifest.json":
                try:
                    child.unlink()
                except Exception:
                    pass
                continue

            if child.suffix.lower() in self.IMAGE_EXTENSIONS:
                try:
                    child.unlink()
                except Exception:
                    pass

    def _write_manifest(
        self,
        result: Dict[str, Any],
        output_dir: Path,
        started_at: float,
    ) -> Dict[str, Any]:
        result["elapsed_seconds"] = round(
            time.time() - started_at,
            3,
        )

        manifest_path = output_dir / "manifest.json"
        result["manifest_path"] = str(manifest_path)

        manifest_path.write_text(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        print(
            "[Sprint105-1 Smart Strip] Version:",
            result.get("version", ""),
            flush=True,
        )
        print(
            "[Sprint105-1 Smart Strip] Status:",
            result.get("status", ""),
            flush=True,
        )
        print(
            "[Sprint105-1 Smart Strip] Inputs:",
            result.get("input_count", 0),
            flush=True,
        )
        print(
            "[Sprint105-1 Smart Strip] Strip Detected:",
            result.get("strip_detected", False),
            flush=True,
        )

        for source in result.get("source_summaries", []):
            print(
                "[Sprint105-1 Smart Strip] Input Size:",
                f"{source.get('width', 0)}x{source.get('height', 0)}",
                flush=True,
            )
            print(
                "[Sprint105-1 Smart Strip] Detected Segments:",
                source.get("segment_count", 0),
                flush=True,
            )

            for index, segment in enumerate(source.get("segments", []), start=1):
                print(
                    f"[Sprint105-1 Smart Strip] Segment{index}:",
                    f"y={segment.get('top', 0)}~{segment.get('bottom', 0)}",
                    flush=True,
                )

        print(
            "[Sprint105-1 Smart Strip] Saved:",
            result.get("image_count", 0),
            flush=True,
        )
        print(
            "[Sprint105-1 Smart Strip] Manifest:",
            result.get("manifest_path", ""),
            flush=True,
        )
        print(
            "[Sprint105-1 Smart Strip] Errors:",
            result.get("errors", []),
            flush=True,
        )

        return result

    def _safe_name(self, value: Any) -> str:
        text = str(value or "").strip()

        safe = "".join(
            character
            for character in text
            if character.isalnum() or character in ("-", "_")
        )

        return safe[:80]