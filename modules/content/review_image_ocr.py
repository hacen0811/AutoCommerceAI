from pathlib import Path
from typing import Any, Dict, List, Tuple
import re


class ReviewImageOCR:
    """
    Sprint74-2 OCR 후처리 고도화 버전

    역할:
    - PaddleOCR 3.x predict() API 사용
    - 한국어 OCR 결과 rec_texts / rec_scores 처리
    - 제목 / UI 문구 / OCR 노이즈 자동 제거
    - 잘린 문장 자동 병합
    - 리뷰 문단 단위 재구성
    - 리뷰별 Quality Score 계산
    - PaddleOCR 실패 시 Tesseract 백업
    - 기존 Workflow 반환 구조 유지
    """

    OCR_VERSION = "review-image-ocr-74-2"

    MIN_CONFIDENCE = 0.60
    MIN_REVIEW_LENGTH = 12
    MIN_QUALITY_SCORE = 55

    def __init__(self) -> None:
        self._paddle_ocr = None

    def extract_many(
        self,
        image_paths: List[str],
    ) -> Dict[str, Any]:
        reviews: List[Dict[str, Any]] = []
        errors: List[str] = []
        image_results: List[Dict[str, Any]] = []

        engine_counts = {
            "paddleocr": 0,
            "tesseract": 0,
        }

        quality_stats = {
            "accepted_count": 0,
            "rejected_low_confidence": 0,
            "rejected_short": 0,
            "rejected_broken": 0,
            "rejected_title": 0,
            "rejected_noise": 0,
            "rejected_low_quality": 0,
            "merged_line_count": 0,
            "paragraph_count": 0,
        }

        for image_index, image_path in enumerate(
            image_paths or [],
            start=1,
        ):
            try:
                text, engine_name = self._extract_text(
                    image_path,
                    quality_stats=quality_stats,
                )

                paragraphs = self._postprocess_text(
                    text,
                    quality_stats=quality_stats,
                )

                engine_counts[engine_name] = (
                    engine_counts.get(engine_name, 0) + 1
                )

                image_results.append(
                    {
                        "image_path": str(image_path),
                        "image_index": image_index,
                        "engine": engine_name,
                        "paragraph_count": len(paragraphs),
                        "line_count": sum(
                            paragraph.get("line_count", 0)
                            for paragraph in paragraphs
                        ),
                        "raw_text": text,
                    }
                )

                for paragraph_index, paragraph in enumerate(
                    paragraphs,
                    start=1,
                ):
                    review_text = paragraph["text"]
                    quality_score = paragraph["quality_score"]

                    reviews.append(
                        {
                            "content": review_text,
                            "text": review_text,
                            "review_text": review_text,
                            "source": "coupang_review_image",
                            "ocr_engine": engine_name,
                            "image_path": str(image_path),
                            "image_index": image_index,
                            "paragraph_index": paragraph_index,
                            "line_count": paragraph["line_count"],
                            "quality_score": quality_score,
                            "quality_grade": self._quality_grade(
                                quality_score
                            ),
                        }
                    )

            except Exception as exc:
                error_message = f"{image_path}: {exc}"
                errors.append(error_message)

                image_results.append(
                    {
                        "image_path": str(image_path),
                        "image_index": image_index,
                        "engine": "failed",
                        "paragraph_count": 0,
                        "line_count": 0,
                        "error": str(exc),
                    }
                )

        reviews = self._deduplicate_reviews(reviews)
        reviews.sort(
            key=lambda item: (
                float(item.get("quality_score", 0)),
                len(str(item.get("content") or "")),
            ),
            reverse=True,
        )

        quality_stats["paragraph_count"] = len(reviews)

        if reviews:
            status = "collected"
        elif errors:
            status = "failed"
        else:
            status = "empty"

        quality_scores = [
            float(review.get("quality_score", 0))
            for review in reviews
        ]

        average_quality_score = (
            round(
                sum(quality_scores) / len(quality_scores),
                1,
            )
            if quality_scores
            else 0.0
        )

        print(
            "[Sprint74-2 OCR] Version:",
            self.OCR_VERSION,
            flush=True,
        )
        print(
            "[Sprint74-2 OCR] Reviews:",
            len(reviews),
            flush=True,
        )
        print(
            "[Sprint74-2 OCR] Engine Counts:",
            engine_counts,
            flush=True,
        )
        print(
            "[Sprint74-2 OCR] Average Quality:",
            average_quality_score,
            flush=True,
        )
        print(
            "[Sprint74-2 OCR] Quality Stats:",
            quality_stats,
            flush=True,
        )

        return {
            "ok": bool(reviews),
            "status": status,
            "version": self.OCR_VERSION,
            "image_count": len(image_paths or []),
            "review_count": len(reviews),
            "reviews": reviews,
            "engine_counts": engine_counts,
            "average_quality_score": average_quality_score,
            "quality_stats": quality_stats,
            "image_results": image_results,
            "errors": errors,
        }

    def _extract_text(
        self,
        image_path: str,
        quality_stats: Dict[str, int],
    ) -> Tuple[str, str]:
        path = Path(image_path)

        if not path.exists():
            raise FileNotFoundError(
                f"이미지 파일이 없습니다: {path}"
            )

        errors: List[str] = []

        try:
            text = self._extract_with_paddle(
                path,
                quality_stats=quality_stats,
            )

            if text.strip():
                return text, "paddleocr"

            errors.append(
                "PaddleOCR 결과가 비어 있습니다."
            )

        except Exception as exc:
            errors.append(f"PaddleOCR: {exc}")

        try:
            text = self._extract_with_tesseract(path)

            if text.strip():
                return text, "tesseract"

            errors.append(
                "Tesseract 결과가 비어 있습니다."
            )

        except Exception as exc:
            errors.append(f"Tesseract: {exc}")

        raise RuntimeError(
            "사용 가능한 OCR 엔진이 없거나 "
            "텍스트를 인식하지 못했습니다. "
            + " | ".join(errors)
        )

    def _extract_with_paddle(
        self,
        path: Path,
        quality_stats: Dict[str, int],
    ) -> str:
        try:
            from paddleocr import PaddleOCR
        except Exception as exc:
            raise RuntimeError(
                "PaddleOCR 미설치"
            ) from exc

        if self._paddle_ocr is None:
            self._paddle_ocr = PaddleOCR(
                lang="korean",
                enable_mkldnn=False,
            )

        result = self._paddle_ocr.predict(
            str(path)
        )

        texts: List[str] = []

        for page in result or []:
            res = self._extract_page_result(page)

            rec_texts = res.get(
                "rec_texts",
                [],
            )

            rec_scores = res.get(
                "rec_scores",
                [],
            )

            for index, raw_text in enumerate(
                rec_texts
            ):
                score = self._score_at(
                    rec_scores,
                    index,
                )

                text = self._normalize_text(
                    raw_text
                )

                if score < self.MIN_CONFIDENCE:
                    quality_stats[
                        "rejected_low_confidence"
                    ] = quality_stats.get(
                        "rejected_low_confidence",
                        0,
                    ) + 1
                    continue

                if len(text) < 2:
                    quality_stats[
                        "rejected_short"
                    ] = quality_stats.get(
                        "rejected_short",
                        0,
                    ) + 1
                    continue

                if self._is_severely_broken(text):
                    quality_stats[
                        "rejected_broken"
                    ] = quality_stats.get(
                        "rejected_broken",
                        0,
                    ) + 1
                    continue

                texts.append(text)

                quality_stats[
                    "accepted_count"
                ] = quality_stats.get(
                    "accepted_count",
                    0,
                ) + 1

        return "\n".join(texts)

    def _extract_page_result(
        self,
        page: Any,
    ) -> Dict[str, Any]:
        if isinstance(page, dict):
            res = page.get("res")

            if isinstance(res, dict):
                return res

            return page

        try:
            page_data = dict(page)
        except Exception:
            page_data = {}

        res = page_data.get("res")

        if isinstance(res, dict):
            return res

        return page_data

    def _score_at(
        self,
        scores: Any,
        index: int,
    ) -> float:
        try:
            return float(scores[index])
        except Exception:
            return 0.0

    def _extract_with_tesseract(
        self,
        path: Path,
    ) -> str:
        try:
            import pytesseract
            from PIL import (
                Image,
                ImageEnhance,
                ImageFilter,
            )
        except Exception as exc:
            raise RuntimeError(
                "pytesseract 또는 Pillow 미설치"
            ) from exc

        try:
            languages = pytesseract.get_languages(
                config=""
            )
        except Exception as exc:
            raise RuntimeError(
                "Tesseract 프로그램을 찾을 수 없습니다."
            ) from exc

        if "kor" in languages:
            language = (
                "kor+eng"
                if "eng" in languages
                else "kor"
            )
        elif "eng" in languages:
            language = "eng"
        else:
            raise RuntimeError(
                "Tesseract 언어팩이 없습니다."
            )

        with Image.open(path) as image:
            image = image.convert("L")

            image = ImageEnhance.Contrast(
                image
            ).enhance(1.8)

            image = image.filter(
                ImageFilter.SHARPEN
            )

            width, height = image.size

            if width < 1400:
                ratio = 1400 / max(
                    width,
                    1,
                )

                image = image.resize(
                    (
                        int(width * ratio),
                        int(height * ratio),
                    )
                )

            configs = [
                "--oem 3 --psm 6",
                "--oem 3 --psm 11",
            ]

            results: List[str] = []

            for config in configs:
                text = pytesseract.image_to_string(
                    image,
                    lang=language,
                    config=config,
                )

                text = self._normalize_text(
                    text
                )

                if text:
                    results.append(text)

            if not results:
                return ""

            return max(
                results,
                key=self._text_quality_score,
            )

    def _postprocess_text(
        self,
        raw_text: str,
        quality_stats: Dict[str, int],
    ) -> List[Dict[str, Any]]:
        cleaned_lines: List[str] = []

        for raw_line in str(
            raw_text or ""
        ).splitlines():
            line = self._clean_single_line(
                raw_line
            )

            if not line:
                quality_stats[
                    "rejected_noise"
                ] = quality_stats.get(
                    "rejected_noise",
                    0,
                ) + 1
                continue

            if self._is_title_line(line):
                quality_stats[
                    "rejected_title"
                ] = quality_stats.get(
                    "rejected_title",
                    0,
                ) + 1
                continue

            if self._is_ui_or_metadata_line(line):
                quality_stats[
                    "rejected_noise"
                ] = quality_stats.get(
                    "rejected_noise",
                    0,
                ) + 1
                continue

            if self._is_severely_broken(line):
                quality_stats[
                    "rejected_broken"
                ] = quality_stats.get(
                    "rejected_broken",
                    0,
                ) + 1
                continue

            cleaned_lines.append(line)

        cleaned_lines = self._deduplicate(
            cleaned_lines
        )

        paragraphs = self._rebuild_paragraphs(
            cleaned_lines,
            quality_stats=quality_stats,
        )

        results: List[Dict[str, Any]] = []

        for paragraph in paragraphs:
            text = paragraph["text"]
            score = self._review_quality_score(
                text
            )

            if (
                len(text) < self.MIN_REVIEW_LENGTH
                or score < self.MIN_QUALITY_SCORE
            ):
                quality_stats[
                    "rejected_low_quality"
                ] = quality_stats.get(
                    "rejected_low_quality",
                    0,
                ) + 1
                continue

            results.append(
                {
                    "text": text,
                    "line_count": paragraph[
                        "line_count"
                    ],
                    "quality_score": score,
                }
            )

        return results

    def _clean_single_line(
        self,
        value: Any,
    ) -> str:
        text = self._normalize_text(value)

        text = text.replace("…", "...")
        text = text.replace("ㆍ", "·")

        text = re.sub(
            r"^[|·•■□▪▫▶▷►▻◆◇★☆✓✔☑☐\-_+=~]+",
            "",
            text,
        )

        text = re.sub(
            r"[|·•■□▪▫▶▷►▻◆◇★☆✓✔☑☐\-_+=~]+$",
            "",
            text,
        )

        text = re.sub(
            r"([!?.,ㅋㅎㅠㅜ])\1{3,}",
            r"\1\1",
            text,
        )

        text = re.sub(
            r"[^\w가-힣A-Za-z0-9\s.,!?%&()/+\-:'\"·]",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        return text.strip(
            " |·•-_=+"
        )

    def _is_title_line(
        self,
        text: str,
    ) -> bool:
        compact = re.sub(
            r"\s+",
            "",
            text,
        )

        title_patterns = [
            r"^\d{1,2}[.)\-:]?(마무리요약|총평|요약|결론|장점|단점|사용후기|구매후기)$",
            r"^\d{1,2}[.)\-:]\s*.{1,18}$",
            r"^(마무리요약|총평|최종평가|한줄평|사용후기|구매후기|제품후기|리뷰요약)$",
            r"^\[?(장점|단점|총평|결론|요약)\]?$",
        ]

        return any(
            re.fullmatch(
                pattern,
                compact,
                flags=re.IGNORECASE,
            )
            for pattern in title_patterns
        )

    def _is_ui_or_metadata_line(
        self,
        text: str,
    ) -> bool:
        exact_ignored = {
            "디자인",
            "편리성",
            "크기",
            "견고함",
            "아주 마음에 들어요",
            "마음에 들어요",
            "보통이에요",
            "별로예요",
            "도움이 돼요",
            "신고하기",
            "상품평",
            "사진",
            "동영상",
            "베스트",
            "best",
            "리뷰",
        }

        contains_ignored = {
            "판매자",
            "구매일",
            "작성일",
            "도움이 돼요",
            "신고하기",
            "쿠팡에서 구매",
            "명에게 도움",
            "리뷰어",
            "별점",
            "옵션",
            "색상",
            "사이즈",
            "배송",
            "재구매",
            "후기 작성",
        }

        lowered = text.lower().strip()

        if lowered in exact_ignored:
            return True

        if any(
            word in lowered
            for word in contains_ignored
        ):
            return True

        if re.fullmatch(
            r"[\d\s./:\-]+",
            text,
        ):
            return True

        if re.fullmatch(
            r"[★☆⭐\s]{2,}",
            text,
        ):
            return True

        if re.fullmatch(
            r"(좋아요|도움돼요|신고|공유)\s*\d*",
            text,
            flags=re.IGNORECASE,
        ):
            return True

        digit_count = sum(
            character.isdigit()
            for character in text
        )

        if (
            digit_count
            and digit_count
            >= len(text) * 0.7
        ):
            return True

        visible_count = len(
            re.findall(
                r"[가-힣A-Za-z0-9]",
                text,
            )
        )

        if visible_count < 2:
            return True

        return False

    def _rebuild_paragraphs(
        self,
        lines: List[str],
        quality_stats: Dict[str, int],
    ) -> List[Dict[str, Any]]:
        if not lines:
            return []

        paragraphs: List[Dict[str, Any]] = []
        buffer: List[str] = []

        for line in lines:
            if not buffer:
                buffer.append(line)
                continue

            previous = buffer[-1]

            if self._should_merge_lines(
                previous,
                line,
                buffer,
            ):
                buffer.append(line)

                quality_stats[
                    "merged_line_count"
                ] = quality_stats.get(
                    "merged_line_count",
                    0,
                ) + 1
            else:
                paragraph = self._finalize_paragraph(
                    buffer
                )

                if paragraph:
                    paragraphs.append(paragraph)

                buffer = [line]

        paragraph = self._finalize_paragraph(buffer)

        if paragraph:
            paragraphs.append(paragraph)

        return paragraphs

    def _should_merge_lines(
        self,
        previous: str,
        current: str,
        buffer: List[str],
    ) -> bool:
        previous = previous.strip()
        current = current.strip()

        if not previous or not current:
            return False

        previous_ends_sentence = bool(
            re.search(
                r"[.!?]$",
                previous,
            )
        )

        current_starts_continuation = bool(
            re.match(
                r"^(그리고|그래서|하지만|그런데|또한|다만|특히|그래도|때문에|이라서|해서|하고|하며|거나|지만|는데|면서|부터|까지|보다|처럼|정도|부분|경우|제품|사용|설치|접착|공간|내부)",
                current,
            )
        )

        previous_looks_cut = bool(
            re.search(
                r"(은|는|이|가|을|를|에|의|와|과|도|만|로|으로|에서|하고|하며|거나|지만|는데|면서|부분|경우|정도|조금|너무|정말|아주|다소)$",
                previous,
            )
        )

        current_looks_fragment = not bool(
            re.match(
                r"^[가-힣A-Z][^.!?]{2,}[.!?]$",
                current,
            )
        )

        total_length = len(
            " ".join(buffer + [current])
        )

        if total_length > 450:
            return False

        if not previous_ends_sentence:
            return True

        if previous_looks_cut:
            return True

        if current_starts_continuation:
            return True

        if len(current) < 18 and current_looks_fragment:
            return True

        return False

    def _finalize_paragraph(
        self,
        lines: List[str],
    ) -> Dict[str, Any]:
        if not lines:
            return {}

        text = " ".join(
            line.strip()
            for line in lines
            if line.strip()
        )

        text = re.sub(
            r"\s+([,.!?])",
            r"\1",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        text = self._repair_sentence_spacing(
            text
        )

        return {
            "text": text,
            "line_count": len(lines),
        }

    def _repair_sentence_spacing(
        self,
        text: str,
    ) -> str:
        text = re.sub(
            r"([.!?])(?=[가-힣A-Za-z])",
            r"\1 ",
            text,
        )

        text = re.sub(
            r"([가-힣])([A-Za-z])",
            r"\1 \2",
            text,
        )

        text = re.sub(
            r"([A-Za-z])([가-힣])",
            r"\1 \2",
            text,
        )

        return re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

    def _review_quality_score(
        self,
        value: Any,
    ) -> int:
        text = str(value or "").strip()

        if not text:
            return 0

        total_count = max(
            len(
                re.sub(
                    r"\s+",
                    "",
                    text,
                )
            ),
            1,
        )

        korean_count = len(
            re.findall(
                r"[가-힣]",
                text,
            )
        )

        english_count = len(
            re.findall(
                r"[A-Za-z]",
                text,
            )
        )

        digit_count = len(
            re.findall(
                r"\d",
                text,
            )
        )

        punctuation_count = len(
            re.findall(
                r"[^\w\s가-힣]",
                text,
            )
        )

        korean_ratio = (
            korean_count / total_count
        )

        punctuation_ratio = (
            punctuation_count / total_count
        )

        score = 35.0

        if len(text) >= 30:
            score += 18
        elif len(text) >= 18:
            score += 10
        elif len(text) >= 12:
            score += 4
        else:
            score -= 20

        score += min(
            korean_ratio * 35,
            30,
        )

        if re.search(
            r"[.!?]$",
            text,
        ):
            score += 5

        if re.search(
            r"(좋|만족|추천|편리|깔끔|설치|사용|아쉽|불편|장점|단점|공간|접착|튼튼|수납|정리)",
            text,
        ):
            score += 8

        if punctuation_ratio > 0.18:
            score -= 15

        if english_count > korean_count:
            score -= 15

        if digit_count >= total_count * 0.45:
            score -= 20

        if re.search(
            r"([ㅋㅎㅠㅜ!?.,])\1{2,}",
            text,
        ):
            score -= 12

        if self._is_severely_broken(text):
            score -= 40

        return int(
            max(
                0,
                min(
                    100,
                    round(score),
                ),
            )
        )

    def _quality_grade(
        self,
        score: float,
    ) -> str:
        if score >= 90:
            return "S"

        if score >= 80:
            return "A"

        if score >= 70:
            return "B"

        if score >= 60:
            return "C"

        return "D"

    def _normalize_text(
        self,
        value: Any,
    ) -> str:
        text = str(value or "")

        text = re.sub(
            r"[\r\t]+",
            " ",
            text,
        )

        text = re.sub(
            r"[ ]+",
            " ",
            text,
        )

        return text.strip()

    def _text_quality_score(
        self,
        value: Any,
    ) -> float:
        text = str(value or "")

        if not text:
            return -1000.0

        korean_count = len(
            re.findall(
                r"[가-힣]",
                text,
            )
        )

        english_count = len(
            re.findall(
                r"[A-Za-z]",
                text,
            )
        )

        digit_count = len(
            re.findall(
                r"[0-9]",
                text,
            )
        )

        question_count = text.count("?")
        replacement_count = text.count("�")

        return (
            korean_count * 3.0
            + english_count * 0.3
            + digit_count * 0.1
            - question_count * 2.5
            - replacement_count * 5.0
        )

    def _is_severely_broken(
        self,
        value: Any,
    ) -> bool:
        text = str(value or "")

        if not text:
            return True

        korean_count = len(
            re.findall(
                r"[가-힣]",
                text,
            )
        )

        question_count = text.count("?")
        replacement_count = text.count("�")

        mojibake_markers = (
            "由",
            "媛",
            "湲",
            "留",
            "諛",
            "異",
            "議",
            "怨",
            "洹",
            "蹂",
            "쒕",
            "듬땲",
            "以꾩",
            "몄튂",
            "꾧",
        )

        mojibake_count = sum(
            text.count(marker)
            for marker in mojibake_markers
        )

        corruption_count = (
            question_count
            + replacement_count
            + mojibake_count
        )

        if corruption_count == 0:
            return False

        if (
            korean_count == 0
            and corruption_count >= 2
        ):
            return True

        if corruption_count >= max(
            4,
            len(text) * 0.18,
        ):
            return True

        return False

    def _deduplicate(
        self,
        lines: List[str],
    ) -> List[str]:
        seen = set()
        result: List[str] = []

        for line in lines:
            key = self._dedup_key(line)

            if not key:
                continue

            if key in seen:
                continue

            seen.add(key)
            result.append(line)

        return result

    def _dedup_key(
        self,
        value: Any,
    ) -> str:
        text = str(value or "").lower()

        text = re.sub(
            r"[^가-힣a-z0-9]",
            "",
            text,
        )

        return text

    def _deduplicate_reviews(
        self,
        reviews: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []

        for review in reviews:
            text = str(
                review.get("content")
                or review.get("text")
                or ""
            ).strip()

            key = self._dedup_key(text)

            if not key:
                continue

            duplicate_index = None

            for index, existing in enumerate(
                result
            ):
                existing_text = str(
                    existing.get("content")
                    or ""
                )

                existing_key = self._dedup_key(
                    existing_text
                )

                if (
                    key == existing_key
                    or (
                        len(key) >= 20
                        and (
                            key in existing_key
                            or existing_key in key
                        )
                    )
                ):
                    duplicate_index = index
                    break

            if duplicate_index is None:
                result.append(review)
                continue

            existing_score = float(
                result[duplicate_index].get(
                    "quality_score",
                    0,
                )
            )

            current_score = float(
                review.get(
                    "quality_score",
                    0,
                )
            )

            if current_score > existing_score:
                result[duplicate_index] = review

        return result