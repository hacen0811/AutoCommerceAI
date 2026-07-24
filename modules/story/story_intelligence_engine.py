from __future__ import annotations

from collections import Counter
import re
import unicodedata
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from .story_templates import StoryTemplateManager


class StoryIntelligenceEngine:
    """
    Sprint99-1 Product Story Intelligence Engine

    역할:
    - 제품 정보, 리뷰 인사이트, Vision 결과, 이미지 태그를 한 번에 분석
    - 제품 유형과 핵심 판매 포인트를 추론
    - 쇼핑 쇼츠에 적합한 Story Type과 Emotion Curve를 결정
    - 6개 장면의 목적(Scene Goal)과 권장 이미지 역할(Image Role)을 생성
    - 외부 API 호출 없이 기존 분석 결과만 재사용
    - 기존 입력이 일부 없어도 안전하게 기본 Story Plan 생성
    """

    VERSION = "story-intelligence-engine-120-2"
    SCENE_COUNT = 6

    STORY_TEMPLATES: Dict[str, Dict[str, Any]] = {
        "problem_solution": {
            "emotion_curve": [
                "hook",
                "empathy",
                "tension",
                "solution",
                "proof",
                "satisfaction",
            ],
            "scene_goals": [
                {
                    "goal": "시청자의 시선을 즉시 멈춘다",
                    "purpose": "hook",
                    "preferred_roles": ["hero", "problem", "lifestyle"],
                },
                {
                    "goal": "제품이 해결하는 불편을 공감시킨다",
                    "purpose": "pain",
                    "preferred_roles": ["problem", "lifestyle", "usage"],
                },
                {
                    "goal": "핵심 기능을 명확하게 보여준다",
                    "purpose": "feature",
                    "preferred_roles": ["feature", "detail", "comparison"],
                },
                {
                    "goal": "실제 사용 방식과 변화를 보여준다",
                    "purpose": "usage",
                    "preferred_roles": ["usage", "lifestyle", "before_after"],
                },
                {
                    "goal": "리뷰·구조·세부 정보로 신뢰를 만든다",
                    "purpose": "proof",
                    "preferred_roles": ["review", "detail", "size", "package"],
                },
                {
                    "goal": "완성된 결과와 구매 행동을 연결한다",
                    "purpose": "cta",
                    "preferred_roles": ["hero", "lifestyle", "best_feature"],
                },
            ],
        },
        "comparison": {
            "emotion_curve": [
                "curiosity",
                "confusion",
                "comparison",
                "clarity",
                "confidence",
                "decision",
            ],
            "scene_goals": [
                {
                    "goal": "선택 고민을 질문으로 제시한다",
                    "purpose": "hook",
                    "preferred_roles": ["comparison", "hero", "text"],
                },
                {
                    "goal": "두 선택지의 차이를 직관적으로 보여준다",
                    "purpose": "comparison",
                    "preferred_roles": ["comparison", "size", "option"],
                },
                {
                    "goal": "핵심 기준별 장단점을 보여준다",
                    "purpose": "feature",
                    "preferred_roles": ["feature", "detail", "comparison"],
                },
                {
                    "goal": "실제 사용 상황에 맞는 선택 기준을 설명한다",
                    "purpose": "usage",
                    "preferred_roles": ["usage", "lifestyle", "size"],
                },
                {
                    "goal": "후기나 수치로 선택 근거를 강화한다",
                    "purpose": "proof",
                    "preferred_roles": ["review", "text", "detail"],
                },
                {
                    "goal": "추천 대상을 정리하고 결정을 돕는다",
                    "purpose": "cta",
                    "preferred_roles": ["hero", "comparison", "best_feature"],
                },
            ],
        },
        "review_evidence": {
            "emotion_curve": [
                "curiosity",
                "trust",
                "empathy",
                "proof",
                "relief",
                "confidence",
            ],
            "scene_goals": [
                {
                    "goal": "실제 후기의 강한 한 문장으로 시작한다",
                    "purpose": "hook",
                    "preferred_roles": ["review", "text", "hero"],
                },
                {
                    "goal": "후기에서 반복된 불편을 공감시킨다",
                    "purpose": "pain",
                    "preferred_roles": ["problem", "review", "lifestyle"],
                },
                {
                    "goal": "제품이 해결한 핵심 변화를 보여준다",
                    "purpose": "solution",
                    "preferred_roles": ["feature", "usage", "before_after"],
                },
                {
                    "goal": "실제 사용 장면으로 후기 내용을 증명한다",
                    "purpose": "usage",
                    "preferred_roles": ["usage", "lifestyle", "detail"],
                },
                {
                    "goal": "반복 후기와 세부 정보를 근거로 제시한다",
                    "purpose": "proof",
                    "preferred_roles": ["review", "detail", "text"],
                },
                {
                    "goal": "누구에게 적합한지 정리하며 마무리한다",
                    "purpose": "cta",
                    "preferred_roles": ["hero", "best_feature", "lifestyle"],
                },
            ],
        },
        "demonstration": {
            "emotion_curve": [
                "surprise",
                "interest",
                "tension",
                "demonstration",
                "proof",
                "satisfaction",
            ],
            "scene_goals": [
                {
                    "goal": "결과나 움직임을 먼저 보여준다",
                    "purpose": "hook",
                    "preferred_roles": ["usage", "before_after", "hero"],
                },
                {
                    "goal": "사용 전 문제 상태를 짧게 보여준다",
                    "purpose": "pain",
                    "preferred_roles": ["problem", "before_after", "lifestyle"],
                },
                {
                    "goal": "제품의 작동 방식이나 구조를 보여준다",
                    "purpose": "feature",
                    "preferred_roles": ["feature", "detail", "usage"],
                },
                {
                    "goal": "제품을 직접 사용하는 과정을 보여준다",
                    "purpose": "usage",
                    "preferred_roles": ["usage", "lifestyle", "feature"],
                },
                {
                    "goal": "전후 차이나 세부 결과로 효과를 확인한다",
                    "purpose": "proof",
                    "preferred_roles": ["before_after", "detail", "comparison"],
                },
                {
                    "goal": "완성된 결과를 다시 보여주며 마무리한다",
                    "purpose": "cta",
                    "preferred_roles": ["hero", "lifestyle", "best_feature"],
                },
            ],
        },
        "benefit_first": {
            "emotion_curve": [
                "desire",
                "interest",
                "understanding",
                "trust",
                "relief",
                "satisfaction",
            ],
            "scene_goals": [
                {
                    "goal": "가장 매력적인 결과를 먼저 보여준다",
                    "purpose": "hook",
                    "preferred_roles": ["hero", "best_feature", "lifestyle"],
                },
                {
                    "goal": "핵심 장점을 한눈에 이해시킨다",
                    "purpose": "benefit",
                    "preferred_roles": ["feature", "text", "comparison"],
                },
                {
                    "goal": "구조와 세부 기능을 설명한다",
                    "purpose": "feature",
                    "preferred_roles": ["detail", "feature", "size"],
                },
                {
                    "goal": "실제 사용 환경에서 장점을 보여준다",
                    "purpose": "usage",
                    "preferred_roles": ["usage", "lifestyle", "before_after"],
                },
                {
                    "goal": "리뷰나 구성 정보로 신뢰를 강화한다",
                    "purpose": "proof",
                    "preferred_roles": ["review", "package", "detail"],
                },
                {
                    "goal": "제품의 최종 가치를 정리한다",
                    "purpose": "cta",
                    "preferred_roles": ["hero", "best_feature", "lifestyle"],
                },
            ],
        },
    }

    PRODUCT_KEYWORDS: Dict[str, Sequence[str]] = {
        "laundry_storage": (
            "빨래바구니", "세탁바구니", "세탁물", "빨래", "세탁", "분리수거",
            "트롤리", "이동식", "3단", "다단", "바구니", "수납", "정리",
            "laundry basket", "laundry hamper", "hamper", "laundry cart",
        ),
        "storage": (
            "수납", "정리", "보관", "바구니", "트롤리", "선반", "옷장",
            "공간활용", "공간 활용", "틈새", "정리함", "수납함",
        ),
        "bathroom": (
            "욕실", "화장실", "샤워", "배수", "물빠짐", "슬리퍼", "칫솔",
            "비누", "세면대", "욕조",
        ),
        "travel": (
            "캐리어", "여행", "기내용", "수하물", "여행가방", "트렁크",
            "인치", "공항", "여행용", "바퀴",
        ),
        "kitchen": (
            "주방", "조리", "냄비", "프라이팬", "팬", "칼", "도마", "식기",
            "텀블러", "보온", "싱크대", "주방용",
        ),
        "cleaning": (
            "청소", "세척", "먼지", "걸레", "브러시", "세제", "오염",
            "닦기", "청소기",
        ),
        "beauty": (
            "뷰티", "화장", "피부", "헤어", "미용", "마사지", "메이크업",
        ),
        "fashion": (
            "의류", "옷", "신발", "가방", "패션", "착용", "코디",
        ),
        "electronics": (
            "충전", "배터리", "전자", "전기", "무선", "블루투스", "케이블", "led",
        ),
        "baby": (
            "아기", "유아", "육아", "기저귀", "어린이", "아이",
        ),
        "pet": (
            "강아지", "고양이", "반려", "펫", "배변", "사료",
        ),
    }

    PRODUCT_TYPE_PRIORITY = (
        "laundry_storage", "travel", "bathroom", "kitchen", "cleaning",
        "storage", "electronics", "baby", "pet", "beauty", "fashion",
    )

    PRODUCT_TYPE_LABELS = {
        "laundry_storage": "laundry_storage",
        "storage": "storage",
        "bathroom": "bathroom",
        "travel": "travel",
        "kitchen": "kitchen",
        "cleaning": "cleaning",
        "beauty": "beauty",
        "fashion": "fashion",
        "electronics": "electronics",
        "baby": "baby",
        "pet": "pet",
        "general": "general",
    }

    COMPARISON_KEYWORDS = (
        "비교",
        "차이",
        "vs",
        "대비",
        "어떤 걸",
        "어느 것",
        "크기",
        "사이즈",
        "인치",
        "옵션",
    )

    DEMONSTRATION_KEYWORDS = (
        "사용",
        "작동",
        "움직",
        "굴러",
        "세척",
        "조립",
        "설치",
        "접이",
        "회전",
        "테스트",
        "전후",
        "비포",
        "애프터",
    )

    def build(
        self,
        product_info: Any = None,
        review_insight: Any = None,
        vision_result: Any = None,
        image_tags: Any = None,
        ocr_result: Any = None,
        analysis_bundle: Any = None,
        scene_count: int = 6,
    ) -> Dict[str, Any]:
        normalized_scene_count = max(
            1,
            min(int(scene_count or self.SCENE_COUNT), 12),
        )

        product_data = self._to_dict(product_info)
        review_data = self._to_dict(review_insight)
        vision_items = self._to_list(vision_result)
        tag_items = self._to_list(image_tags)
        ocr_items = self._to_list(ocr_result)
        analysis_data = self._to_dict(analysis_bundle)

        corpus = self._build_corpus(
            product_data=product_data,
            review_data=review_data,
            vision_items=vision_items,
            tag_items=tag_items,
            ocr_items=ocr_items,
            analysis_data=analysis_data,
        )

        product_type, product_type_scores = self._infer_product_type(
            corpus=corpus,
            product_data=product_data,
            analysis_data=analysis_data,
        )
        product_subtype = self._infer_product_subtype(
            product_type=product_type,
            product_data=product_data,
            analysis_data=analysis_data,
            corpus=corpus,
        )
        review_signals = self._extract_review_signals(
            review_data=review_data,
            analysis_data=analysis_data,
            ocr_items=ocr_items,
        )
        auto_complement = self._build_auto_complement(
            product_type=product_type,
            product_subtype=product_subtype,
            review_signals=review_signals,
        )
        selling_points = self._extract_selling_points(
            review_data=review_data,
            analysis_data=analysis_data,
            corpus=corpus,
            product_type=product_type,
            product_subtype=product_subtype,
            review_signals=review_signals,
            auto_complement=auto_complement,
        )
        story_type, story_type_scores = self._select_story_type(
            corpus=corpus,
            review_data=review_data,
            analysis_data=analysis_data,
            vision_items=vision_items,
        )

        template_manager = StoryTemplateManager(
            base_templates=self.STORY_TEMPLATES,
        )
        template_result = template_manager.resolve(
            product_type=product_type,
            product_subtype=product_subtype,
            story_type=story_type,
        )
        template = template_result["template"]

        scene_goals = self._build_scene_goals(
            template=template,
            scene_count=normalized_scene_count,
            product_type=product_type,
            selling_points=selling_points,
        )

        image_role_plan = [
            {
                "scene_id": item["scene_id"],
                "purpose": item["purpose"],
                "preferred_roles": list(item["preferred_roles"]),
            }
            for item in scene_goals
        ]

        result = {
            "ok": True,
            "ready": True,
            "version": self.VERSION,
            "status": "planned",
            "story_type": story_type,
            "story_type_scores": story_type_scores,
            "story_template_version": template_result["version"],
            "story_template_category": template_result["category"],
            "story_template_key": template_result["template_key"],
            "story_template_source": template_result["source"],
            "story_template_fallback_used": template_result["fallback_used"],
            "story_template_profile": template_result["profile"],
            "product_type": product_type,
            "product_subtype": product_subtype,
            "product_type_scores": product_type_scores,
            "pain_points": auto_complement["pain_points"],
            "benefits": auto_complement["benefits"],
            "evidence": review_signals["evidence"],
            "selling_points": selling_points,
            "auto_complement": auto_complement,
            "emotion_curve": list(template["emotion_curve"]),
            "scene_count": len(scene_goals),
            "scene_goals": scene_goals,
            "image_role_plan": image_role_plan,
            "recommended_images": [],
            "source_counts": {
                "vision": len(vision_items),
                "image_tags": len(tag_items),
                "ocr": len(ocr_items),
                "review_insight": 1 if review_data else 0,
                "analysis_bundle": 1 if analysis_data else 0,
            },
            "quality": {
                "broken_text_filtered": True,
                "product_type_rule_version": "120-1",
                "story_template_manager_enabled": True,
                "story_template_manager_version": template_result["version"],
                "review_sentiment_guard_version": "120-2",
                "auto_complement_enabled": True,
                "review_broken_text_filtered": review_signals["broken_filtered_count"],
            },
            "warnings": [],
            "errors": [],
        }

        if not corpus.strip():
            result["warnings"].append(
                "분석 입력이 부족하여 기본 문제 해결형 스토리를 생성했습니다"
            )

        self._print_log(result)
        return result

    def _build_scene_goals(
        self,
        template: Mapping[str, Any],
        scene_count: int,
        product_type: str,
        selling_points: Sequence[str],
    ) -> List[Dict[str, Any]]:
        source_goals = list(template.get("scene_goals") or [])

        if not source_goals:
            source_goals = list(
                self.STORY_TEMPLATES["problem_solution"]["scene_goals"]
            )

        selected: List[Dict[str, Any]] = []

        if scene_count == len(source_goals):
            selected = [dict(item) for item in source_goals]
        elif scene_count < len(source_goals):
            indexes = self._spread_indexes(
                total=len(source_goals),
                count=scene_count,
            )
            selected = [
                dict(source_goals[index])
                for index in indexes
            ]
        else:
            selected = [dict(item) for item in source_goals]

            while len(selected) < scene_count:
                selected.insert(
                    max(1, len(selected) - 1),
                    {
                        "goal": "추가 기능이나 사용 장면을 보여준다",
                        "purpose": "feature",
                        "preferred_roles": [
                            "feature",
                            "usage",
                            "detail",
                        ],
                    },
                )

        primary_point = (
            selling_points[0]
            if selling_points
            else "핵심 장점"
        )

        scene_goals: List[Dict[str, Any]] = []

        for index, item in enumerate(selected, start=1):
            goal = str(item.get("goal") or "").strip()

            if index == 3 and primary_point:
                goal = f"{primary_point}을 중심으로 핵심 기능을 보여준다"

            scene_goals.append(
                {
                    "scene_id": f"scene_{index:02d}",
                    "order": index,
                    "goal": goal,
                    "purpose": str(
                        item.get("purpose") or "feature"
                    ),
                    "preferred_roles": list(
                        item.get("preferred_roles")
                        or ["feature", "detail", "hero"]
                    ),
                    "product_type": product_type,
                    "primary_selling_point": primary_point,
                }
            )

        return scene_goals

    def _select_story_type(
        self,
        corpus: str,
        review_data: Mapping[str, Any],
        analysis_data: Mapping[str, Any],
        vision_items: Sequence[Any],
    ) -> tuple[str, Dict[str, float]]:
        lowered = corpus.lower()

        scores = {
            "problem_solution": 2.0,
            "comparison": 0.0,
            "review_evidence": 0.0,
            "demonstration": 0.0,
            "benefit_first": 0.0,
        }

        for keyword in self.COMPARISON_KEYWORDS:
            if keyword.lower() in lowered:
                scores["comparison"] += 1.5

        for keyword in self.DEMONSTRATION_KEYWORDS:
            if keyword.lower() in lowered:
                scores["demonstration"] += 1.0

        review_count = self._first_number(
            review_data.get("review_count"),
            analysis_data.get("review_count"),
            analysis_data.get("raw_review_count"),
        )

        evidence = self._first_text(
            review_data.get("best_evidence"),
            review_data.get("evidence"),
            analysis_data.get("best_evidence"),
        )
        pain = self._first_text(
            review_data.get("best_pain"),
            review_data.get("best_pain_point"),
            analysis_data.get("best_pain"),
            analysis_data.get("best_pain_point"),
        )
        benefit = self._first_text(
            review_data.get("best_benefit"),
            analysis_data.get("best_benefit"),
        )

        if review_count >= 3:
            scores["review_evidence"] += 2.0

        if evidence:
            scores["review_evidence"] += 3.0

        if pain:
            scores["problem_solution"] += 2.5

        if benefit:
            scores["benefit_first"] += 1.5

        if len(vision_items) >= 4:
            scores["demonstration"] += 0.5
            scores["benefit_first"] += 0.5

        explicit_strategy = self._first_text(
            analysis_data.get("shorts_strategy"),
            analysis_data.get("story_type"),
            analysis_data.get("bridge_psychology"),
            review_data.get("story_type"),
        ).lower()

        if "comparison" in explicit_strategy or "비교" in explicit_strategy:
            scores["comparison"] += 5.0

        if "review" in explicit_strategy or "후기" in explicit_strategy:
            scores["review_evidence"] += 5.0

        if (
            "problem" in explicit_strategy
            or "solution" in explicit_strategy
            or "문제" in explicit_strategy
            or "해결" in explicit_strategy
        ):
            scores["problem_solution"] += 4.0

        priority = [
            "comparison",
            "review_evidence",
            "problem_solution",
            "demonstration",
            "benefit_first",
        ]

        story_type = max(
            priority,
            key=lambda name: (
                scores[name],
                -priority.index(name),
            ),
        )

        return story_type, {
            key: round(value, 2)
            for key, value in scores.items()
        }

    def _infer_product_type(
        self,
        corpus: str,
        product_data: Mapping[str, Any],
        analysis_data: Mapping[str, Any],
    ) -> tuple[str, Dict[str, float]]:
        # 제품명과 카테고리는 OCR/이미지 설명보다 신뢰도가 높으므로 별도 가중치를 줍니다.
        product_name = self._first_text(
            product_data.get("product_name"),
            product_data.get("name"),
            product_data.get("title"),
            analysis_data.get("product_name"),
        )
        category = self._first_text(
            product_data.get("category"),
            analysis_data.get("category"),
        )
        keyword = self._first_text(
            product_data.get("keyword"),
            analysis_data.get("keyword"),
        )

        weighted_sources = [
            (self._normalize_for_matching(product_name), 8.0),
            (self._normalize_for_matching(category), 5.0),
            (self._normalize_for_matching(keyword), 4.0),
            (self._normalize_for_matching(corpus), 1.0),
        ]
        scores: Dict[str, float] = {}

        for product_type, keywords in self.PRODUCT_KEYWORDS.items():
            score = 0.0
            for source_text, source_weight in weighted_sources:
                if not source_text or self._is_broken_text(source_text):
                    continue
                for keyword_item in keywords:
                    token = self._normalize_for_matching(keyword_item)
                    if not token:
                        continue
                    occurrences = source_text.count(token)
                    if occurrences:
                        token_weight = 2.0 if len(token) >= 4 else 1.0
                        score += min(24.0, occurrences * source_weight * token_weight)
            scores[product_type] = round(score, 2)

        trusted = " ".join(
            value for value in (
                self._normalize_for_matching(product_name),
                self._normalize_for_matching(category),
                self._normalize_for_matching(keyword),
            ) if value and not self._is_broken_text(value)
        )

        laundry_phrases = (
            "빨래바구니", "세탁바구니", "세탁물바구니",
            "laundry basket", "laundry hamper", "laundry cart",
        )
        if any(phrase in trusted for phrase in laundry_phrases):
            scores["laundry_storage"] = scores.get("laundry_storage", 0.0) + 100.0
        elif ("빨래" in trusted or "세탁" in trusted) and (
            "바구니" in trusted or "트롤리" in trusted or "수납" in trusted
        ):
            scores["laundry_storage"] = scores.get("laundry_storage", 0.0) + 70.0

        if "캐리어" in trusted and ("인치" in trusted or "여행" in trusted):
            scores["travel"] = scores.get("travel", 0.0) + 80.0
        if "욕실" in trusted and "슬리퍼" in trusted:
            scores["bathroom"] = scores.get("bathroom", 0.0) + 80.0

        # kitchen 같은 오분류는 신뢰 입력에 주방 단어가 있을 때만 강하게 인정합니다.
        if not any(word in trusted for word in ("주방", "싱크대", "조리", "kitchen")):
            scores["kitchen"] = min(scores.get("kitchen", 0.0), 12.0)

        priority = list(self.PRODUCT_TYPE_PRIORITY)
        best_type = max(
            scores,
            key=lambda name: (
                scores.get(name, 0.0),
                -priority.index(name) if name in priority else -999,
            ),
            default="general",
        )
        if scores.get(best_type, 0.0) <= 0:
            best_type = "general"

        return self.PRODUCT_TYPE_LABELS.get(best_type, best_type), {
            key: round(value, 2) for key, value in scores.items()
        }

    def _normalize_for_matching(self, value: Any) -> str:
        text = unicodedata.normalize("NFKC", str(value or "")).lower()
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _is_broken_text(self, value: Any) -> bool:
        text = str(value or "").strip()
        if not text:
            return True
        if "�" in text:
            return True
        if "?" in text and len(text) <= 30:
            return True
        suspicious = sum(text.count(ch) for ch in ("?", "㈃", "꾨", "곸", "놁", "λ"))
        korean = len(re.findall(r"[가-힣]", text))
        ascii_letters = len(re.findall(r"[A-Za-z]", text))
        meaningful = korean + ascii_letters + len(re.findall(r"[0-9]", text))
        if suspicious >= 2 and meaningful < max(3, len(text) // 3):
            return True
        if len(text) <= 8 and suspicious >= 1 and korean == 0:
            return True
        return False

    def _infer_product_subtype(
        self,
        product_type: str,
        product_data: Mapping[str, Any],
        analysis_data: Mapping[str, Any],
        corpus: str,
    ) -> str:
        trusted = " ".join(
            value for value in (
                self._first_text(
                    product_data.get("product_name"),
                    product_data.get("name"),
                    product_data.get("title"),
                    analysis_data.get("product_name"),
                ),
                self._first_text(product_data.get("category"), analysis_data.get("category")),
                corpus,
            ) if value
        ).lower()
        subtype_rules = {
            "cutting_board": ("도마", "cutting board", "tpu 도마", "실리콘 도마"),
            "cookware": ("냄비", "프라이팬", "팬", "웍"),
            "tumbler": ("텀블러", "보온병", "보냉병"),
            "laundry_basket": ("빨래바구니", "세탁바구니", "laundry basket"),
            "carrier": ("캐리어", "여행가방", "기내용"),
        }
        for subtype, keywords in subtype_rules.items():
            if any(keyword in trusted for keyword in keywords):
                return subtype
        return product_type

    def _extract_review_signals(
        self,
        review_data: Mapping[str, Any],
        analysis_data: Mapping[str, Any],
        ocr_items: Sequence[Any],
    ) -> Dict[str, Any]:
        raw_candidates: List[tuple[str, str]] = []
        field_groups = {
            "benefit": (
                review_data.get("best_benefit"), analysis_data.get("best_benefit"),
                analysis_data.get("primary_benefit"),
            ),
            "pain": (
                review_data.get("best_pain"), review_data.get("best_pain_point"),
                analysis_data.get("best_pain"), analysis_data.get("best_pain_point"),
            ),
            "evidence": (
                review_data.get("best_evidence"), review_data.get("evidence"),
                analysis_data.get("best_evidence"),
            ),
        }
        for kind, values in field_groups.items():
            for value in values:
                text = str(value or "").strip()
                if text:
                    raw_candidates.append((kind, text))

        for item in ocr_items:
            for text in self._flatten_text(item):
                raw_candidates.append(("ocr", text))

        benefits: List[str] = []
        pains: List[str] = []
        evidence: List[str] = []
        broken_filtered_count = 0

        # Sprint120-2 Review Sentiment Guard
        # "불편" 안의 "편"처럼 부정 문장이 긍정으로 오분류되는 문제를 막습니다.
        positive_tokens = (
            "좋다", "좋아요", "좋았", "편하다", "편해", "편리",
            "쉬워", "쉽다", "만족", "튼튼", "가볍", "유연",
            "안 미끄", "잘 된다", "잘돼", "깔끔", "추천",
            "도움", "효율", "간편", "수월",
        )
        negative_tokens = (
            "불편", "아쉽", "단점", "미끄럽", "미끄러",
            "무겁", "냄새", "자국", "오염", "작다", "작아서",
            "약하다", "약해", "어렵", "번거롭", "불안", "불량",
            "문제", "부족", "답답", "귀찮", "힘들",
        )

        def has_negative_signal(value: str) -> bool:
            return any(token in value for token in negative_tokens)

        def has_positive_signal(value: str) -> bool:
            return any(token in value for token in positive_tokens)

        for kind, raw in raw_candidates:
            text = self._clean_point(raw)
            if not text:
                broken_filtered_count += 1
                continue

            negative_signal = has_negative_signal(text)
            positive_signal = has_positive_signal(text)

            if kind == "pain" or negative_signal:
                target = pains
            elif kind == "benefit" or positive_signal:
                target = benefits
            else:
                target = evidence

            if text not in target:
                target.append(text)

        return {
            "benefits": benefits[:5],
            "pain_points": pains[:5],
            "evidence": evidence[:5],
            "broken_filtered_count": broken_filtered_count,
            "review_input_present": bool(raw_candidates),
        }

    def _build_auto_complement(
        self,
        product_type: str,
        product_subtype: str,
        review_signals: Mapping[str, Any],
    ) -> Dict[str, Any]:
        defaults = {
            "cutting_board": {
                "pain_points": ["일반 도마는 사용 중 밀리거나 재료를 옮기기 불편할 수 있다"],
                "benefits": ["유연하게 휘어 손질한 재료를 옮기기 편하다", "가볍고 세척과 보관이 편리하다"],
            },
            "laundry_basket": {
                "pain_points": ["세탁물을 나누고 옮기는 과정이 번거롭다"],
                "benefits": ["세탁물을 분리 수납하기 쉽다", "이동과 공간 활용이 편리하다"],
            },
            "carrier": {
                "pain_points": ["여행 기간에 맞는 크기와 수납력을 고르기 어렵다"],
                "benefits": ["짐을 체계적으로 수납하기 좋다", "이동이 편리하다"],
            },
            "kitchen": {
                "pain_points": ["조리 과정에서 반복되는 작은 불편이 있다"],
                "benefits": ["조리와 정리를 더 편리하게 돕는다"],
            },
            "general": {
                "pain_points": ["기존 사용 방식에 반복되는 불편이 있다"],
                "benefits": ["일상 사용의 편의성을 높인다"],
            },
        }
        base = defaults.get(product_subtype) or defaults.get(product_type) or defaults["general"]
        pains = list(review_signals.get("pain_points") or [])
        benefits = list(review_signals.get("benefits") or [])
        generated_pain = False
        generated_benefit = False
        if not pains:
            pains = list(base["pain_points"])
            generated_pain = True
        if not benefits:
            benefits = list(base["benefits"])
            generated_benefit = True
        return {
            "pain_points": pains[:5],
            "benefits": benefits[:5],
            "generated_pain": generated_pain,
            "generated_benefit": generated_benefit,
            "mode": (
                "review_only" if not generated_pain and not generated_benefit
                else "hybrid" if review_signals.get("review_input_present")
                else "product_fallback"
            ),
        }

    def _extract_selling_points(
        self,
        review_data: Mapping[str, Any],
        analysis_data: Mapping[str, Any],
        corpus: str,
        product_type: str,
        product_subtype: str,
        review_signals: Mapping[str, Any],
        auto_complement: Mapping[str, Any],
    ) -> List[str]:
        selling_points: List[str] = []
        for candidate in list(auto_complement.get("benefits") or []) + list(review_signals.get("evidence") or []):
            cleaned = self._clean_point(candidate)
            if cleaned and cleaned not in selling_points:
                selling_points.append(cleaned)

        if not selling_points:
            keyword_counts = Counter()
            for keywords in self.PRODUCT_KEYWORDS.values():
                for keyword in keywords:
                    count = corpus.lower().count(keyword.lower())
                    if count:
                        keyword_counts[keyword] += count
            selling_points.extend(keyword for keyword, _ in keyword_counts.most_common(3))

        if not selling_points:
            defaults = {
                "cutting_board": ["유연한 재료 이동", "세척 편의성", "간편한 보관"],
                "laundry_basket": ["빨래 분리 수납", "이동 편의성", "공간 활용"],
                "carrier": ["넉넉한 수납", "부드러운 이동", "여행 편의성"],
                "kitchen": ["조리 편의성", "세척 편의성", "간편한 보관"],
                "storage": ["수납력", "정리 편의성", "공간 활용"],
            }
            selling_points = defaults.get(product_subtype) or defaults.get(product_type) or ["제품의 핵심 편의성"]

        return selling_points[:5]

    def _build_corpus(
        self,
        product_data: Mapping[str, Any],
        review_data: Mapping[str, Any],
        vision_items: Sequence[Any],
        tag_items: Sequence[Any],
        ocr_items: Sequence[Any],
        analysis_data: Mapping[str, Any],
    ) -> str:
        parts: List[str] = []

        parts.extend(self._flatten_text(product_data))
        parts.extend(self._flatten_text(review_data))
        parts.extend(self._flatten_text(analysis_data))

        for item in vision_items:
            parts.extend(self._flatten_text(item))

        for item in tag_items:
            parts.extend(self._flatten_text(item))

        for item in ocr_items:
            parts.extend(self._flatten_text(item))

        return " ".join(
            part.strip()
            for part in parts
            if str(part).strip()
        )

    def _flatten_text(
        self,
        value: Any,
        depth: int = 0,
    ) -> List[str]:
        if depth > 4 or value is None:
            return []

        if isinstance(value, str):
            text = " ".join(value.split())
            return [] if self._is_broken_text(text) else [text]

        if isinstance(value, (int, float, bool)):
            text = str(value)
            return [] if self._is_broken_text(text) else [text]

        if isinstance(value, Mapping):
            texts: List[str] = []

            for key, item in value.items():
                if str(key).lower() in {
                    "path",
                    "url",
                    "sha256",
                    "manifest_path",
                    "output_dir",
                }:
                    continue

                texts.extend(
                    self._flatten_text(item, depth + 1)
                )

            return texts

        if isinstance(value, Iterable):
            texts = []

            for item in value:
                texts.extend(
                    self._flatten_text(item, depth + 1)
                )

            return texts

        return [str(value)]

    def _spread_indexes(
        self,
        total: int,
        count: int,
    ) -> List[int]:
        if count <= 1:
            return [0]

        if count >= total:
            return list(range(total))

        indexes = []

        for index in range(count):
            position = round(
                index * (total - 1) / (count - 1)
            )
            indexes.append(int(position))

        return sorted(set(indexes))

    def _to_dict(self, value: Any) -> Dict[str, Any]:
        if isinstance(value, Mapping):
            return dict(value)

        return {}

    def _to_list(self, value: Any) -> List[Any]:
        if value is None:
            return []

        if isinstance(value, Mapping):
            for key in (
                "images",
                "items",
                "results",
                "analyses",
                "tags",
                "reviews",
            ):
                candidate = value.get(key)

                if isinstance(candidate, Sequence) and not isinstance(
                    candidate,
                    (str, bytes, bytearray),
                ):
                    return list(candidate)

            return [dict(value)]

        if isinstance(value, Sequence) and not isinstance(
            value,
            (str, bytes, bytearray),
        ):
            return list(value)

        return [value]

    def _first_text(self, *values: Any) -> str:
        for value in values:
            text = str(value or "").strip()

            if text:
                return text

        return ""

    def _first_number(self, *values: Any) -> int:
        for value in values:
            try:
                return int(value)
            except (TypeError, ValueError):
                continue

        return 0

    def _clean_point(self, value: str) -> str:
        text = " ".join(str(value or "").split())

        if not text or self._is_broken_text(text):
            return ""

        return text[:120]

    def _print_log(self, result: Mapping[str, Any]) -> None:
        print(
            "[Sprint100-1 Story Intelligence] Version:",
            result.get("version", ""),
            flush=True,
        )
        print(
            "[Sprint100-1 Story Intelligence] Status:",
            result.get("status", ""),
            flush=True,
        )
        print(
            "[Sprint100-1 Story Intelligence] Product Type:",
            result.get("product_type", ""),
            flush=True,
        )
        print(
            "[Sprint100-1 Story Intelligence] Story Type:",
            result.get("story_type", ""),
            flush=True,
        )
        print(
            "[Sprint100-1 Story Intelligence] Selling Points:",
            result.get("selling_points", []),
            flush=True,
        )
        print(
            "[Sprint100-1 Story Intelligence] Scene Count:",
            result.get("scene_count", 0),
            flush=True,
        )
        print(
            "[Sprint120-1 Story Template] Version:",
            result.get("story_template_version", ""),
            flush=True,
        )
        print(
            "[Sprint120-1 Story Template] Category:",
            result.get("story_template_category", ""),
            flush=True,
        )
        print(
            "[Sprint120-1 Story Template] Key:",
            result.get("story_template_key", ""),
            flush=True,
        )
        print(
            "[Sprint120-1 Story Template] Source:",
            result.get("story_template_source", ""),
            flush=True,
        )
        print(
            "[Sprint120-2 Review Sentiment Guard] Version:",
            (result.get("quality") or {}).get("review_sentiment_guard_version", ""),
            flush=True,
        )
        print(
            "[Sprint120-2 Review Sentiment Guard] Pain Points:",
            result.get("pain_points", []),
            flush=True,
        )
        print(
            "[Sprint120-2 Review Sentiment Guard] Benefits:",
            result.get("benefits", []),
            flush=True,
        )
        print(
            "[Sprint100-1 Story Intelligence] Errors:",
            result.get("errors", []),
            flush=True,
        )