import re
from typing import Any, Dict, List


class ReviewTextCleaner:
    CLEANER_VERSION = "review-text-cleaner-71-1"

    def clean_reviews(
        self,
        reviews: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        source_reviews = reviews or []
        cleaned_reviews: List[Dict[str, Any]] = []

        grouped = self._group_by_image(source_reviews)

        for image_path, items in grouped.items():
            texts = [
                self._extract_text(item)
                for item in items
            ]

            texts = [
                text
                for text in texts
                if text
            ]

            merged_lines = self._merge_fragments(texts)

            for text in merged_lines:
                cleaned_text = self._clean_text(text)

                if not self._is_valid_review(cleaned_text):
                    continue

                cleaned_reviews.append(
                    {
                        "content": cleaned_text,
                        "text": cleaned_text,
                        "review_text": cleaned_text,
                        "source": "review_image_ocr_cleaned",
                        "image_path": image_path,
                        "cleaner_version": self.CLEANER_VERSION,
                    }
                )

        cleaned_reviews = self._deduplicate(
            cleaned_reviews
        )

        return {
            "ok": bool(cleaned_reviews),
            "version": self.CLEANER_VERSION,
            "source_count": len(source_reviews),
            "cleaned_count": len(cleaned_reviews),
            "reviews": cleaned_reviews,
        }

    def _group_by_image(
        self,
        reviews: List[Dict[str, Any]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        grouped: Dict[str, List[Dict[str, Any]]] = {}

        for review in reviews:
            if not isinstance(review, dict):
                continue

            image_path = str(
                review.get("image_path")
                or "unknown"
            )

            grouped.setdefault(
                image_path,
                [],
            ).append(review)

        return grouped

    def _extract_text(
        self,
        review: Dict[str, Any],
    ) -> str:
        text = (
            review.get("content")
            or review.get("review_text")
            or review.get("text")
            or ""
        )

        return " ".join(
            str(text).strip().split()
        )

    def _merge_fragments(
        self,
        lines: List[str],
    ) -> List[str]:
        merged: List[str] = []
        buffer = ""

        for line in lines:
            line = line.strip()

            if not line:
                continue

            if not buffer:
                buffer = line
                continue

            if self._looks_incomplete(buffer):
                buffer = f"{buffer} {line}"
                continue

            merged.append(buffer)
            buffer = line

        if buffer:
            merged.append(buffer)

        return merged

    def _looks_incomplete(
        self,
        text: str,
    ) -> bool:
        text = text.strip()

        if len(text) < 18:
            return True

        complete_endings = (
            ".",
            "!",
            "?",
            "습니다",
            "했어요",
            "좋아요",
            "같아요",
            "됩니다",
            "였어요",
            "네요",
            "입니다",
        )

        return not text.endswith(
            complete_endings
        )

    def _clean_text(
        self,
        text: str,
    ) -> str:
        text = str(text or "")

        replacements = {
            "되/습니다": "되었습니다",
            "이/습니다": "이었습니다",
            "있없습니다": "있었습니다",
            "들없습니다": "들었습니다",
            "좋앞습니다": "좋았습니다",
            "높앞습니다": "높았습니다",
            "안고": "않고",
            "안는": "않는",
            "햇습니다": "했습니다",
            "보엿습니다": "보였습니다",
            "느낌이없습니다": "느낌이었습니다",
            "제름": "제품",
            "청스도구": "청소도구",
            "정든된": "정돈된",
            "구퍼하게": "구매하게",
            "정리활": "정리할",
            "사용활": "사용할",
            "청소활": "청소할",
            "부착활": "부착할",
        }

        for before, after in replacements.items():
            text = text.replace(
                before,
                after,
            )

        text = re.sub(
            r"[|;/]+",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        text = text.strip(
            " .,-_=+|;:/"
        )

        return text

    def _is_valid_review(
        self,
        text: str,
    ) -> bool:
        if len(text) < 18:
            return False

        ignored = (
            "디자인 아주 마음에 들어요",
            "편리성 아주 편리해요",
            "크기 적당해요",
            "견고함 아주 견고해요",
            "도움이 돼요",
            "신고하기",
            "내돈내산 후기",
        )

        if any(
            phrase in text
            for phrase in ignored
        ):
            return False

        korean_count = len(
            re.findall(
                r"[가-힣]",
                text,
            )
        )

        if korean_count < 8:
            return False

        return True

    def _deduplicate(
        self,
        reviews: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        seen = set()
        result: List[Dict[str, Any]] = []

        for review in reviews:
            text = str(
                review.get("content")
                or ""
            ).strip()

            key = re.sub(
                r"\s+",
                "",
                text.lower(),
            )

            if not key:
                continue

            if key in seen:
                continue

            seen.add(key)
            result.append(review)

        return result