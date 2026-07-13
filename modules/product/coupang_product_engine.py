from __future__ import annotations

import re
from urllib.parse import (
    parse_qs,
    urlencode,
    unquote,
    urlparse,
    urlunparse,
)


class CoupangProductEngine:
    """
    Coupang Product Engine - Sprint66 Fix

    역할:
    - 쿠팡 상품 URL 정리
    - HTTPS 강제 유지
    - productId 추출
    - itemId 보존
    - vendorItemId 보존
    - 불필요한 추적 파라미터 제거

    중요:
    쿠팡 상품 접근 시 다음 조합을 유지한다.
    productId + itemId + vendorItemId
    """

    ENGINE_VERSION = "coupang-product-engine-66-1"

    def parse(
        self,
        url,
    ):
        original_url = str(
            url or ""
        ).strip()

        normalized_url = self._normalize_url(
            original_url
        )

        parsed = urlparse(
            normalized_url
        )

        query = parse_qs(
            parsed.query
        )

        product_id = self._find_product_id(
            parsed.path
        )

        item_id = self._first(
            query.get("itemId")
            or query.get("itemid")
        )

        vendor_item_id = self._first(
            query.get("vendorItemId")
            or query.get("vendoritemid")
        )

        clean_url = self._build_clean_url(
            parsed=parsed,
            item_id=item_id,
            vendor_item_id=vendor_item_id,
        )

        guessed_name = self.guess_name(
            original_url,
            product_id,
        )

        host = str(
            parsed.netloc or ""
        ).lower()

        is_coupang = (
            "coupang.com" in host
        )

        return {
            "engine_version": self.ENGINE_VERSION,
            "original_url": original_url,
            "coupang_url": clean_url,
            "partner_url": clean_url,
            "clean_url": clean_url,
            "product_id": product_id,
            "item_id": item_id,
            "vendor_item_id": vendor_item_id,
            "platform": (
                "쿠팡"
                if is_coupang
                else "기타"
            ),
            "product_name": guessed_name,
            "guessed_product_name": guessed_name,
            "image_url": "",
            "keyword": self.keyword(
                guessed_name
            ),
            "note": (
                "쿠팡 상품 접근 안정성을 위해 "
                "HTTPS와 itemId, vendorItemId를 "
                "보존합니다."
            ),
        }

    def _normalize_url(
        self,
        url: str,
    ) -> str:
        value = str(
            url or ""
        ).strip()

        if not value:
            return ""

        if value.startswith("//"):
            value = (
                "https:"
                + value
            )

        if not re.match(
            r"^https?://",
            value,
            flags=re.IGNORECASE,
        ):
            value = (
                "https://"
                + value.lstrip("/")
            )

        parsed = urlparse(
            value
        )

        scheme = "https"

        host = str(
            parsed.netloc or ""
        ).strip()

        return urlunparse(
            (
                scheme,
                host,
                parsed.path,
                "",
                parsed.query,
                "",
            )
        )

    def _build_clean_url(
        self,
        parsed,
        item_id: str,
        vendor_item_id: str,
    ) -> str:
        clean_query = {}

        if item_id:
            clean_query["itemId"] = (
                item_id
            )

        if vendor_item_id:
            clean_query[
                "vendorItemId"
            ] = vendor_item_id

        encoded_query = urlencode(
            clean_query
        )

        return urlunparse(
            (
                "https",
                parsed.netloc,
                parsed.path,
                "",
                encoded_query,
                "",
            )
        )

    def _find_product_id(
        self,
        path: str,
    ) -> str:
        match = re.search(
            r"/(?:vp/)?products/(\d+)",
            str(path or ""),
            flags=re.IGNORECASE,
        )

        return (
            match.group(1)
            if match
            else ""
        )

    def _first(
        self,
        values,
    ) -> str:
        if not values:
            return ""

        return str(
            values[0] or ""
        ).strip()

    def guess_name(
        self,
        url,
        product_id="",
    ):
        text = unquote(
            str(url or "")
        )

        for key in [
            "q=",
            "keyword=",
            "searchKeyword=",
        ]:
            if key not in text:
                continue

            value = (
                text.split(
                    key,
                    1,
                )[1]
                .split(
                    "&",
                    1,
                )[0]
                .replace(
                    "+",
                    " ",
                )
                .strip()
            )

            if value:
                return value

        if product_id:
            return (
                f"쿠팡상품 {product_id}"
            )

        return "쿠팡 추천상품"

    def keyword(
        self,
        name,
    ):
        text = str(
            name or ""
        )

        if (
            "방충" in text
            or "모기" in text
        ):
            return "방충망"

        if (
            "얼음" in text
            or "아이스" in text
        ):
            return "얼음"

        if "수전" in text:
            return "수전"

        if "장갑" in text:
            return "장갑"

        parts = [
            part
            for part in re.split(
                r"\s+",
                text,
            )
            if part
        ]

        return (
            parts[-1]
            if parts
            else "정보"
        )