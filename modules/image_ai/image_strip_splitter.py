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
    Sprint98-6 Image Strip Splitter

    역할:
    - 세로로 이어진 상품 이미지 스트립 1장을 자동 분할
    - 여러 장 직접 업로드도 그대로 지원
    - Streamlit UploadedFile, bytes, 파일 경로를 모두 입력으로 지원
    - 분할 결과를 00_main.png, 01_detail.png ... 형식으로 저장
    - MultiImageCollector와 호환되는 manifest.json 구조 생성
    - 원본 이미지 보존 여부 선택 가능
    """

    VERSION = "image-strip-splitter-98-6"
    SOURCE_VERSION = "image-strip-splitter-98-4"

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
                    "white_gap"
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
        Sprint98-6 하이브리드 세로 스트립 분할.

        분할 기준:
        - 흰색 여백
        - 행별 밝기 변화
        - 행별 색상 변화
        - 행별 에지 밀도 변화
        - 너무 긴 구간 자동 재분할

        쿠팡/타오바오/1688 상세 이미지처럼 흰 여백이 거의 없어도
        장면 경계를 추정해서 여러 구간으로 나눈다.
        """
        width, height = image.size

        if width <= 0 or height <= 0:
            return []

        analysis_width = min(width, 320)
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
        row_color: List[Tuple[float, float, float]] = []
        row_edge: List[float] = []

        previous_gray: List[float] | None = None

        for y in range(analysis_height):
            row = list(
                analysis.crop(
                    (0, y, analysis_width, y + 1)
                ).getdata()
            )

            if not row:
                row_non_white.append(0.0)
                row_brightness.append(255.0)
                row_color.append((255.0, 255.0, 255.0))
                row_edge.append(0.0)
                continue

            non_white = 0
            red_sum = 0.0
            green_sum = 0.0
            blue_sum = 0.0
            gray_values: List[float] = []

            for red, green, blue in row:
                red_sum += red
                green_sum += green
                blue_sum += blue

                if (
                    red < white_threshold
                    or green < white_threshold
                    or blue < white_threshold
                ):
                    non_white += 1

                gray_values.append(
                    0.299 * red + 0.587 * green + 0.114 * blue
                )

            count = max(len(row), 1)

            mean_red = red_sum / count
            mean_green = green_sum / count
            mean_blue = blue_sum / count
            mean_brightness = (
                0.299 * mean_red
                + 0.587 * mean_green
                + 0.114 * mean_blue
            )

            row_non_white.append(non_white / count)
            row_brightness.append(mean_brightness)
            row_color.append((mean_red, mean_green, mean_blue))

            if previous_gray is None:
                edge_value = 0.0
            else:
                edge_value = sum(
                    abs(current - previous)
                    for current, previous in zip(
                        gray_values,
                        previous_gray,
                    )
                ) / count

            row_edge.append(edge_value)
            previous_gray = gray_values

        def smooth(values: List[float], radius: int = 2) -> List[float]:
            if not values:
                return []

            smoothed: List[float] = []

            for index in range(len(values)):
                start = max(0, index - radius)
                end = min(len(values), index + radius + 1)
                window = values[start:end]
                smoothed.append(sum(window) / max(len(window), 1))

            return smoothed

        smooth_non_white = smooth(row_non_white, radius=2)
        smooth_brightness = smooth(row_brightness, radius=2)
        smooth_edge = smooth(row_edge, radius=2)

        content_threshold = max(
            0.003,
            min(float(min_content_ratio or 0.015), 0.025),
        )
        scaled_min_gap = max(
            2,
            int(round(min_gap_height / max(scale_y, 0.001))),
        )
        scaled_min_segment = max(
            8,
            int(round(min_segment_height / max(scale_y, 0.001))),
        )

        boundary_scores = [0.0 for _ in range(analysis_height)]

        # 1) 흰색 여백 감지
        gap_start = None

        for y, ratio in enumerate(smooth_non_white):
            is_gap = ratio < content_threshold

            if is_gap and gap_start is None:
                gap_start = y
            elif not is_gap and gap_start is not None:
                gap_length = y - gap_start

                if gap_length >= scaled_min_gap:
                    center = (gap_start + y) // 2
                    boundary_scores[center] += 8.0

                gap_start = None

        if gap_start is not None:
            gap_length = analysis_height - gap_start

            if gap_length >= scaled_min_gap:
                center = (gap_start + analysis_height) // 2
                boundary_scores[center] += 8.0

        # 2) 행별 밝기/색상/에지 변화 감지
        for y in range(2, analysis_height - 2):
            brightness_change = abs(
                smooth_brightness[y + 1]
                - smooth_brightness[y - 1]
            )

            color_before = row_color[y - 1]
            color_after = row_color[y + 1]
            color_change = sum(
                abs(after - before)
                for before, after in zip(
                    color_before,
                    color_after,
                )
            ) / 3.0

            edge_change = abs(
                smooth_edge[y + 1]
                - smooth_edge[y - 1]
            )

            content_change = abs(
                smooth_non_white[y + 1]
                - smooth_non_white[y - 1]
            )

            score = 0.0

            if brightness_change >= 10:
                score += min(3.0, brightness_change / 12.0)

            if color_change >= 12:
                score += min(3.0, color_change / 15.0)

            if edge_change >= 8:
                score += min(2.5, edge_change / 10.0)

            if content_change >= 0.08:
                score += min(2.5, content_change * 12.0)

            # 아주 밝고 비어 있는 행은 경계 가능성을 추가한다.
            if (
                smooth_brightness[y] >= 247
                and smooth_non_white[y] < content_threshold * 1.5
            ):
                score += 2.0

            boundary_scores[y] += score

        # 3) 후보 경계 추출
        candidates: List[Tuple[float, int]] = []

        for y in range(1, analysis_height - 1):
            score = boundary_scores[y]

            if score < 3.2:
                continue

            if (
                score >= boundary_scores[y - 1]
                and score >= boundary_scores[y + 1]
            ):
                candidates.append((score, y))

        candidates.sort(
            key=lambda item: (-item[0], item[1])
        )

        selected_analysis: List[int] = []
        minimum_distance = max(
            scaled_min_segment,
            int(round(analysis_width * 0.35)),
        )

        for score, y in candidates:
            if y < minimum_distance:
                continue

            if analysis_height - y < minimum_distance:
                continue

            if any(
                abs(y - existing) < minimum_distance
                for existing in selected_analysis
            ):
                continue

            selected_analysis.append(y)

        selected_analysis.sort()

        boundaries = [0]
        boundaries.extend(
            max(
                0,
                min(
                    height,
                    int(round(y * scale_y)),
                ),
            )
            for y in selected_analysis
        )
        boundaries.append(height)
        boundaries = sorted(set(boundaries))

        # 4) 너무 긴 구간은 자동 균등 분할
        preferred_height = max(
            int(width * 1.15),
            min_segment_height * 3,
        )
        maximum_height = max(
            int(width * 2.2),
            preferred_height * 2,
        )

        expanded_boundaries = [boundaries[0]]

        for top, bottom in zip(boundaries, boundaries[1:]):
            segment_height = bottom - top

            if segment_height <= maximum_height:
                expanded_boundaries.append(bottom)
                continue

            piece_count = max(
                2,
                int(round(segment_height / preferred_height)),
            )
            piece_height = segment_height / piece_count

            for piece_index in range(1, piece_count):
                candidate = int(
                    round(top + piece_height * piece_index)
                )

                # 후보 주변에서 가장 낮은 콘텐츠 밀도 또는 가장 큰 변화 지점을 찾는다.
                search_radius = max(
                    min_segment_height,
                    int(width * 0.18),
                )
                search_top = max(
                    top + min_segment_height,
                    candidate - search_radius,
                )
                search_bottom = min(
                    bottom - min_segment_height,
                    candidate + search_radius,
                )

                best_y = candidate
                best_score = float("-inf")

                for original_y in range(search_top, search_bottom + 1):
                    analysis_y = max(
                        0,
                        min(
                            analysis_height - 1,
                            int(round(original_y / scale_y)),
                        ),
                    )

                    density_score = (
                        1.0 - min(
                            1.0,
                            smooth_non_white[analysis_y]
                            / max(content_threshold * 8.0, 0.001),
                        )
                    )
                    change_score = boundary_scores[analysis_y] / 8.0
                    combined = density_score + change_score

                    if combined > best_score:
                        best_score = combined
                        best_y = original_y

                if (
                    best_y - expanded_boundaries[-1]
                    >= min_segment_height
                ):
                    expanded_boundaries.append(best_y)

            expanded_boundaries.append(bottom)

        boundaries = sorted(set(expanded_boundaries))

        # 5) 구간 생성 및 작은 구간 병합
        raw_segments: List[Tuple[int, int]] = []

        for top, bottom in zip(boundaries, boundaries[1:]):
            if bottom - top <= 0:
                continue

            if bottom - top < min_segment_height:
                if raw_segments:
                    previous_top, _ = raw_segments[-1]
                    raw_segments[-1] = (previous_top, bottom)
                continue

            raw_segments.append((top, bottom))

        segments: List[Tuple[int, int]] = []

        for top, bottom in raw_segments:
            segment = image.crop((0, top, width, bottom))

            if self._has_meaningful_content(
                segment,
                white_threshold=white_threshold,
                min_content_ratio=max(
                    0.002,
                    min_content_ratio * 0.35,
                ),
            ):
                segments.append((top, bottom))
            elif segments:
                previous_top, _ = segments[-1]
                segments[-1] = (previous_top, bottom)

        # 스트립 감지는 되었지만 후보가 전혀 없으면
        # 세로 길이를 기준으로 최소 2장 이상 분할한다.
        if len(segments) <= 1 and height >= width * 1.8:
            fallback_height = max(
                int(width * 1.25),
                min_segment_height * 3,
            )
            fallback_count = max(
                2,
                min(
                    20,
                    int(round(height / fallback_height)),
                ),
            )

            fallback_boundaries = [
                int(round(height * index / fallback_count))
                for index in range(fallback_count + 1)
            ]

            segments = []

            for top, bottom in zip(
                fallback_boundaries,
                fallback_boundaries[1:],
            ):
                if bottom - top >= min_segment_height:
                    segments.append((top, bottom))

        return segments or [(0, height)]

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
            "[Sprint98-6 Image Strip] Version:",
            result.get("version", ""),
            flush=True,
        )
        print(
            "[Sprint98-6 Image Strip] Status:",
            result.get("status", ""),
            flush=True,
        )
        print(
            "[Sprint98-6 Image Strip] Inputs:",
            result.get("input_count", 0),
            flush=True,
        )
        print(
            "[Sprint98-6 Image Strip] Strip Detected:",
            result.get("strip_detected", False),
            flush=True,
        )

        for source in result.get("source_summaries", []):
            print(
                "[Sprint98-6 Image Strip] Input Size:",
                f"{source.get('width', 0)}x{source.get('height', 0)}",
                flush=True,
            )
            print(
                "[Sprint98-6 Image Strip] Detected Segments:",
                source.get("segment_count", 0),
                flush=True,
            )

            for index, segment in enumerate(source.get("segments", []), start=1):
                print(
                    f"[Sprint98-6 Image Strip] Segment{index}:",
                    f"y={segment.get('top', 0)}~{segment.get('bottom', 0)}",
                    flush=True,
                )

        print(
            "[Sprint98-6 Image Strip] Saved:",
            result.get("image_count", 0),
            flush=True,
        )
        print(
            "[Sprint98-6 Image Strip] Manifest:",
            result.get("manifest_path", ""),
            flush=True,
        )
        print(
            "[Sprint98-6 Image Strip] Errors:",
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