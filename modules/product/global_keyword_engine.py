from __future__ import annotations

import re
from typing import Dict, List


class GlobalKeywordEngine:
    """
    Sprint 58-1

    쿠팡 상품명에서 TikTok/Douyin 검색용
    한국어·영어·중국어 키워드를 생성합니다.

    현재 단계:
    - AI 없이도 동작
    - 주요 생활용품 카테고리 사전 기반
    - 추후 AI 키워드 생성 결과를 덮어쓸 수 있는 구조
    """

    CATEGORY_RULES = [
        {
            "tokens": [
                "텀블러",
                "보온컵",
                "보냉컵",
                "빨대컵",
                "보온병",
            ],
            "ko": [
                "텀블러",
                "대용량 텀블러",
                "보온 텀블러",
            ],
            "en": [
                "insulated tumbler",
                "large tumbler",
                "straw tumbler",
                "vacuum tumbler",
                "stainless steel tumbler",
            ],
            "zh": [
                "保温杯",
                "大容量保温杯",
                "吸管杯",
                "不锈钢保温杯",
            ],
        },
        {
            "tokens": [
                "선풍기",
                "휴대용 선풍기",
                "손풍기",
                "미니 선풍기",
            ],
            "ko": [
                "휴대용 선풍기",
                "손선풍기",
                "미니 선풍기",
            ],
            "en": [
                "portable fan",
                "handheld fan",
                "mini fan",
                "rechargeable fan",
            ],
            "zh": [
                "手持风扇",
                "便携式风扇",
                "迷你风扇",
                "充电风扇",
            ],
        },
        {
            "tokens": [
                "수납함",
                "정리함",
                "수납박스",
                "옷정리",
            ],
            "ko": [
                "수납함",
                "정리함",
                "수납박스",
            ],
            "en": [
                "storage organizer",
                "storage box",
                "home organizer",
                "closet organizer",
            ],
            "zh": [
                "收纳盒",
                "整理箱",
                "衣柜收纳",
                "家居收纳",
            ],
        },
        {
            "tokens": [
                "청소기",
                "무선청소기",
                "핸디청소기",
                "미니청소기",
            ],
            "ko": [
                "무선 청소기",
                "핸디 청소기",
                "미니 청소기",
            ],
            "en": [
                "cordless vacuum",
                "handheld vacuum",
                "mini vacuum cleaner",
                "portable vacuum",
            ],
            "zh": [
                "无线吸尘器",
                "手持吸尘器",
                "迷你吸尘器",
                "便携式吸尘器",
            ],
        },
        {
            "tokens": [
                "밀폐용기",
                "보관용기",
                "반찬통",
                "냉장고 정리",
            ],
            "ko": [
                "밀폐용기",
                "음식 보관용기",
                "냉장고 정리용기",
            ],
            "en": [
                "food storage container",
                "airtight container",
                "fridge organizer",
                "meal prep container",
            ],
            "zh": [
                "食品保鲜盒",
                "密封保鲜盒",
                "冰箱收纳盒",
                "食品储存盒",
            ],
        },
        {
            "tokens": [
                "건조대",
                "빨래건조대",
                "접이식 건조대",
            ],
            "ko": [
                "빨래 건조대",
                "접이식 건조대",
                "공간절약 건조대",
            ],
            "en": [
                "folding drying rack",
                "clothes drying rack",
                "space saving drying rack",
            ],
            "zh": [
                "折叠晾衣架",
                "衣物晾晒架",
                "节省空间晾衣架",
            ],
        },
        {
            "tokens": [
                "얼음틀",
                "아이스볼",
                "제빙기",
                "얼음통",
            ],
            "ko": [
                "얼음틀",
                "아이스볼 메이커",
                "대용량 얼음틀",
            ],
            "en": [
                "ice cube tray",
                "ice ball maker",
                "large ice tray",
                "silicone ice mold",
            ],
            "zh": [
                "冰格",
                "冰球模具",
                "大容量冰格",
                "硅胶冰模",
            ],
        },
    ]

    REMOVE_WORDS = [
        "무료배송",
        "로켓배송",
        "쿠팡",
        "정품",
        "국내배송",
        "당일배송",
        "사은품",
        "증정",
        "특가",
        "할인",
        "공식",
        "본품",
        "세트",
    ]

    def build(
        self,
        product_name: str,
        category: str = "",
    ) -> Dict[str, List[str]]:
        cleaned_name = self.clean_product_name(
            product_name
        )

        matched_rule = self.find_rule(
            product_name=cleaned_name,
            category=category,
        )

        if matched_rule:
            result = {
                "ko": list(matched_rule["ko"]),
                "en": list(matched_rule["en"]),
                "zh": list(matched_rule["zh"]),
            }
        else:
            fallback = self.extract_core_keyword(
                cleaned_name
            )

            result = {
                "ko": [fallback] if fallback else [],
                "en": [],
                "zh": [],
            }

        result["ko"] = self.dedupe(
            result.get("ko", [])
        )
        result["en"] = self.dedupe(
            result.get("en", [])
        )
        result["zh"] = self.dedupe(
            result.get("zh", [])
        )

        result["tiktok_keywords"] = self.dedupe(
            result["en"] + result["zh"]
        )

        result["douyin_keywords"] = self.dedupe(
            result["zh"]
        )

        result["source_product_name"] = cleaned_name
        result["matched"] = bool(matched_rule)

        return result

    def find_rule(
        self,
        product_name: str,
        category: str = "",
    ):
        text = (
            f"{product_name} {category}"
        ).lower()

        for rule in self.CATEGORY_RULES:
            for token in rule["tokens"]:
                if token.lower() in text:
                    return rule

        return None

    def clean_product_name(
        self,
        product_name: str,
    ) -> str:
        text = str(
            product_name or ""
        )

        for word in self.REMOVE_WORDS:
            text = text.replace(
                word,
                " ",
            )

        text = re.sub(
            r"\[[^\]]*\]",
            " ",
            text,
        )

        text = re.sub(
            r"\([^)]*\)",
            " ",
            text,
        )

        text = re.sub(
            r"\b\d+(?:ml|l|cm|mm|kg|g|개|입|매)\b",
            " ",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"[^\w가-힣一-龥\s]",
            " ",
            text,
        )

        text = " ".join(
            text.split()
        )

        return text[:200]

    def extract_core_keyword(
        self,
        product_name: str,
    ) -> str:
        words = [
            word
            for word in str(
                product_name or ""
            ).split()
            if len(word) >= 2
        ]

        if not words:
            return ""

        return " ".join(
            words[-3:]
        )

    def dedupe(
        self,
        values: List[str],
    ) -> List[str]:
        seen = set()
        result = []

        for value in values or []:
            text = str(
                value or ""
            ).strip()

            key = text.lower()

            if not text or key in seen:
                continue

            seen.add(key)
            result.append(text)

        return result