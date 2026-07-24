from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Mapping


class StoryTemplateManager:
    """
    Sprint120-1 상품군별 Story Template Manager.

    기존 Story Type 판정은 유지하면서 상품군별 감정곡선과
    6장면 목적을 적용합니다. 상품군 템플릿이 없으면 기존
    공통 Story Template으로 안전하게 복귀합니다.
    """

    VERSION = "story-template-manager-120-1"

    CATEGORY_ALIASES = {
        "laundry_storage": "storage",
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

    PROFILES: Dict[str, Dict[str, Any]] = {
        "storage": {
            "label": "수납·정리",
            "opening_focus": "정리 전의 혼잡함과 공간 낭비",
            "proof_focus": "수납량·동선·공간 변화",
            "cta_style": "정리가 필요한 공간과 사용자를 구체적으로 제안",
            "emotion_curve": ["discomfort", "empathy", "possibility", "organization", "relief", "satisfaction"],
            "scene_goals": [
                {"goal": "정리되지 않은 공간의 불편을 한눈에 보여준다", "purpose": "hook", "preferred_roles": ["problem", "before_after", "lifestyle"]},
                {"goal": "쌓이고 섞이는 물건 때문에 생기는 불편을 공감시킨다", "purpose": "pain", "preferred_roles": ["problem", "lifestyle", "detail"]},
                {"goal": "분리 수납 구조와 공간 활용 기능을 보여준다", "purpose": "feature", "preferred_roles": ["feature", "detail", "size"]},
                {"goal": "물건을 나누어 넣고 꺼내는 실제 동선을 보여준다", "purpose": "usage", "preferred_roles": ["usage", "lifestyle", "feature"]},
                {"goal": "정리 전후와 실제 수납량으로 변화를 증명한다", "purpose": "proof", "preferred_roles": ["before_after", "comparison", "review"]},
                {"goal": "정돈된 공간의 결과와 추천 대상을 연결한다", "purpose": "cta", "preferred_roles": ["hero", "lifestyle", "best_feature"]},
            ],
        },
        "kitchen": {
            "label": "주방용품",
            "opening_focus": "조리 중 반복되는 불편 또는 결과",
            "proof_focus": "사용 과정·세척·재료 변화",
            "cta_style": "조리 습관과 사용 빈도에 맞춰 추천",
            "emotion_curve": ["friction", "empathy", "interest", "ease", "proof", "satisfaction"],
            "scene_goals": [
                {"goal": "조리 중 반복되는 불편이나 결과를 즉시 보여준다", "purpose": "hook", "preferred_roles": ["problem", "usage", "hero"]},
                {"goal": "손질·조리·세척 과정의 번거로움을 공감시킨다", "purpose": "pain", "preferred_roles": ["problem", "lifestyle", "detail"]},
                {"goal": "재질과 구조가 만드는 핵심 편의 기능을 보여준다", "purpose": "feature", "preferred_roles": ["feature", "detail", "comparison"]},
                {"goal": "재료 손질이나 조리 과정에서 직접 사용하는 모습을 보여준다", "purpose": "usage", "preferred_roles": ["usage", "lifestyle", "feature"]},
                {"goal": "완성 결과와 세척·보관 편의성으로 효용을 증명한다", "purpose": "proof", "preferred_roles": ["before_after", "detail", "review"]},
                {"goal": "주방에서 달라지는 사용 경험과 추천 대상을 정리한다", "purpose": "cta", "preferred_roles": ["hero", "lifestyle", "best_feature"]},
            ],
        },
        "cleaning": {
            "label": "청소용품",
            "opening_focus": "오염과 청소 전후 차이",
            "proof_focus": "제거력·도달 범위·작업 시간",
            "cta_style": "청소가 어려운 장소를 기준으로 추천",
            "emotion_curve": ["disgust", "tension", "hope", "action", "relief", "satisfaction"],
            "scene_goals": [
                {"goal": "눈에 띄는 오염이나 청소 사각지대를 먼저 보여준다", "purpose": "hook", "preferred_roles": ["problem", "before_after", "detail"]},
                {"goal": "기존 방법으로 잘 닦이지 않는 불편을 공감시킨다", "purpose": "pain", "preferred_roles": ["problem", "lifestyle", "usage"]},
                {"goal": "브러시·흡입·세척 구조 등 핵심 원리를 보여준다", "purpose": "feature", "preferred_roles": ["feature", "detail", "usage"]},
                {"goal": "오염 부위에 직접 사용하는 과정을 보여준다", "purpose": "usage", "preferred_roles": ["usage", "lifestyle", "feature"]},
                {"goal": "청소 전후 차이와 남은 오염 상태를 확인한다", "purpose": "proof", "preferred_roles": ["before_after", "comparison", "detail"]},
                {"goal": "깨끗해진 결과와 적합한 청소 장소를 정리한다", "purpose": "cta", "preferred_roles": ["hero", "before_after", "best_feature"]},
            ],
        },
        "travel": {
            "label": "여행용품",
            "opening_focus": "여행 준비와 이동 중 선택 고민",
            "proof_focus": "수납량·크기·이동 편의성",
            "cta_style": "여행 기간과 이동 방식에 맞춰 추천",
            "emotion_curve": ["curiosity", "confusion", "comparison", "clarity", "confidence", "decision"],
            "scene_goals": [
                {"goal": "여행 기간에 맞는 크기 선택 고민을 질문으로 제시한다", "purpose": "hook", "preferred_roles": ["comparison", "hero", "size"]},
                {"goal": "크기와 수납량 차이를 직관적으로 보여준다", "purpose": "comparison", "preferred_roles": ["comparison", "size", "option"]},
                {"goal": "바퀴·손잡이·내부 구성 등 이동 기능을 보여준다", "purpose": "feature", "preferred_roles": ["feature", "detail", "comparison"]},
                {"goal": "여행 기간과 짐의 양에 맞는 사용 기준을 보여준다", "purpose": "usage", "preferred_roles": ["usage", "lifestyle", "size"]},
                {"goal": "실제 후기와 수납 장면으로 선택 근거를 강화한다", "purpose": "proof", "preferred_roles": ["review", "usage", "detail"]},
                {"goal": "여행 유형별 추천 크기를 정리해 결정을 돕는다", "purpose": "cta", "preferred_roles": ["hero", "comparison", "best_feature"]},
            ],
        },
        "bathroom": {
            "label": "욕실용품",
            "opening_focus": "물기·위생·좁은 공간의 불편",
            "proof_focus": "배수·건조·설치 후 변화",
            "cta_style": "욕실 환경과 설치 조건에 맞춰 추천",
            "emotion_curve": ["discomfort", "empathy", "interest", "cleanliness", "relief", "satisfaction"],
            "scene_goals": [
                {"goal": "물기나 어수선한 욕실 상태를 먼저 보여준다", "purpose": "hook", "preferred_roles": ["problem", "before_after", "lifestyle"]},
                {"goal": "젖음·미끄러짐·위생 관리의 불편을 공감시킨다", "purpose": "pain", "preferred_roles": ["problem", "detail", "lifestyle"]},
                {"goal": "배수·건조·부착 구조 등 핵심 기능을 보여준다", "purpose": "feature", "preferred_roles": ["feature", "detail", "usage"]},
                {"goal": "욕실에 설치하거나 사용하는 과정을 보여준다", "purpose": "usage", "preferred_roles": ["usage", "lifestyle", "feature"]},
                {"goal": "사용 전후의 물기와 정돈 상태를 비교한다", "purpose": "proof", "preferred_roles": ["before_after", "comparison", "review"]},
                {"goal": "깔끔해진 욕실 결과와 추천 환경을 정리한다", "purpose": "cta", "preferred_roles": ["hero", "lifestyle", "best_feature"]},
            ],
        },
        "beauty": {
            "label": "뷰티",
            "opening_focus": "외관 고민과 기대하는 변화",
            "proof_focus": "사용 과정·표현·마무리 변화",
            "cta_style": "피부·헤어 고민과 사용 루틴에 맞춰 추천",
            "emotion_curve": ["desire", "curiosity", "understanding", "trust", "confidence", "satisfaction"],
            "scene_goals": [
                {"goal": "가장 매력적인 완성 결과를 먼저 보여준다", "purpose": "hook", "preferred_roles": ["before_after", "hero", "lifestyle"]},
                {"goal": "어떤 고민을 위한 제품인지 명확히 보여준다", "purpose": "benefit", "preferred_roles": ["problem", "text", "lifestyle"]},
                {"goal": "제형·도구·작동 방식의 핵심 특징을 보여준다", "purpose": "feature", "preferred_roles": ["detail", "feature", "usage"]},
                {"goal": "실제 루틴에서 사용하는 과정을 보여준다", "purpose": "usage", "preferred_roles": ["usage", "lifestyle", "detail"]},
                {"goal": "사용 전후와 후기 근거로 변화를 확인한다", "purpose": "proof", "preferred_roles": ["before_after", "review", "detail"]},
                {"goal": "적합한 고민과 사용 루틴을 정리한다", "purpose": "cta", "preferred_roles": ["hero", "best_feature", "lifestyle"]},
            ],
        },
        "fashion": {
            "label": "패션",
            "opening_focus": "착용 결과와 스타일 변화",
            "proof_focus": "핏·소재·코디 활용",
            "cta_style": "체형·상황·코디 목적에 맞춰 추천",
            "emotion_curve": ["desire", "curiosity", "imagination", "confidence", "trust", "decision"],
            "scene_goals": [
                {"goal": "가장 돋보이는 착용 결과를 먼저 보여준다", "purpose": "hook", "preferred_roles": ["lifestyle", "hero", "best_feature"]},
                {"goal": "핏과 스타일의 핵심 장점을 보여준다", "purpose": "benefit", "preferred_roles": ["lifestyle", "feature", "comparison"]},
                {"goal": "소재·마감·수납 등 세부 특징을 보여준다", "purpose": "feature", "preferred_roles": ["detail", "feature", "size"]},
                {"goal": "다른 상황과 코디에서 활용하는 모습을 보여준다", "purpose": "usage", "preferred_roles": ["usage", "lifestyle", "comparison"]},
                {"goal": "착용 후기와 디테일로 선택 근거를 강화한다", "purpose": "proof", "preferred_roles": ["review", "detail", "lifestyle"]},
                {"goal": "어떤 체형과 스타일에 맞는지 정리한다", "purpose": "cta", "preferred_roles": ["hero", "lifestyle", "best_feature"]},
            ],
        },
        "electronics": {
            "label": "전자기기",
            "opening_focus": "기능 결과와 기존 방식의 비효율",
            "proof_focus": "속도·연결·배터리·작동 안정성",
            "cta_style": "사용 환경과 필요한 기능을 기준으로 추천",
            "emotion_curve": ["surprise", "curiosity", "focus", "demonstration", "trust", "confidence"],
            "scene_goals": [
                {"goal": "핵심 기능이 작동하는 결과를 먼저 보여준다", "purpose": "hook", "preferred_roles": ["usage", "hero", "before_after"]},
                {"goal": "기존 연결이나 사용 방식의 불편을 보여준다", "purpose": "pain", "preferred_roles": ["problem", "usage", "lifestyle"]},
                {"goal": "연결 방식과 주요 사양을 직관적으로 보여준다", "purpose": "feature", "preferred_roles": ["feature", "detail", "text"]},
                {"goal": "실제 환경에서 기능을 작동시키는 과정을 보여준다", "purpose": "usage", "preferred_roles": ["usage", "lifestyle", "feature"]},
                {"goal": "속도·안정성·배터리 결과로 성능을 확인한다", "purpose": "proof", "preferred_roles": ["comparison", "detail", "review"]},
                {"goal": "필요한 사용자와 사용 환경을 정리한다", "purpose": "cta", "preferred_roles": ["hero", "best_feature", "lifestyle"]},
            ],
        },
        "baby": {
            "label": "유아용품",
            "opening_focus": "보호자의 반복되는 돌봄 불편",
            "proof_focus": "안전·세척·사용 편의성",
            "cta_style": "아이의 연령과 보호자의 사용 상황에 맞춰 추천",
            "emotion_curve": ["concern", "empathy", "hope", "care", "relief", "confidence"],
            "scene_goals": [
                {"goal": "돌봄 중 반복되는 불편을 조심스럽게 보여준다", "purpose": "hook", "preferred_roles": ["problem", "lifestyle", "usage"]},
                {"goal": "보호자가 겪는 시간과 위생 부담을 공감시킨다", "purpose": "pain", "preferred_roles": ["problem", "lifestyle", "detail"]},
                {"goal": "안전·세척·사용 편의 구조를 보여준다", "purpose": "feature", "preferred_roles": ["feature", "detail", "usage"]},
                {"goal": "보호자가 실제로 사용하는 과정을 보여준다", "purpose": "usage", "preferred_roles": ["usage", "lifestyle", "feature"]},
                {"goal": "안전 요소와 실제 후기로 신뢰를 강화한다", "purpose": "proof", "preferred_roles": ["detail", "review", "package"]},
                {"goal": "아이 연령과 사용 상황에 맞는 추천을 정리한다", "purpose": "cta", "preferred_roles": ["hero", "lifestyle", "best_feature"]},
            ],
        },
        "pet": {
            "label": "반려동물용품",
            "opening_focus": "반려생활의 반복되는 불편",
            "proof_focus": "반응·위생·관리 편의성",
            "cta_style": "반려동물의 크기와 생활 습관에 맞춰 추천",
            "emotion_curve": ["concern", "empathy", "interest", "interaction", "relief", "satisfaction"],
            "scene_goals": [
                {"goal": "반려생활에서 반복되는 불편을 먼저 보여준다", "purpose": "hook", "preferred_roles": ["problem", "lifestyle", "usage"]},
                {"goal": "위생·급여·놀이 관리의 어려움을 공감시킨다", "purpose": "pain", "preferred_roles": ["problem", "lifestyle", "detail"]},
                {"goal": "제품 구조와 안전한 사용 방식을 보여준다", "purpose": "feature", "preferred_roles": ["feature", "detail", "usage"]},
                {"goal": "반려동물이 실제로 사용하는 장면을 보여준다", "purpose": "usage", "preferred_roles": ["usage", "lifestyle", "feature"]},
                {"goal": "반응과 관리 편의성을 후기나 전후 장면으로 증명한다", "purpose": "proof", "preferred_roles": ["review", "before_after", "detail"]},
                {"goal": "적합한 반려동물과 생활 환경을 정리한다", "purpose": "cta", "preferred_roles": ["hero", "lifestyle", "best_feature"]},
            ],
        },
        "general": {
            "label": "일반 상품",
            "opening_focus": "가장 강한 불편 또는 결과",
            "proof_focus": "핵심 기능·사용 장면·리뷰",
            "cta_style": "사용 상황과 추천 대상을 구체적으로 정리",
        },
    }

    def __init__(self, base_templates: Mapping[str, Mapping[str, Any]]) -> None:
        self.base_templates = {
            str(key): deepcopy(dict(value))
            for key, value in dict(base_templates or {}).items()
        }

    def resolve(
        self,
        product_type: str,
        story_type: str,
        product_subtype: str = "",
    ) -> Dict[str, Any]:
        requested_type = str(product_type or "general").strip().lower()
        requested_story = str(story_type or "problem_solution").strip().lower()
        category = self.CATEGORY_ALIASES.get(requested_type, "general")
        profile = deepcopy(self.PROFILES.get(category, self.PROFILES["general"]))

        base_template = deepcopy(
            self.base_templates.get(requested_story)
            or self.base_templates.get("problem_solution")
            or {}
        )

        category_template = {}
        if profile.get("emotion_curve") and profile.get("scene_goals"):
            category_template = {
                "emotion_curve": profile["emotion_curve"],
                "scene_goals": profile["scene_goals"],
            }

        template = deepcopy(base_template)
        template.update(deepcopy(category_template))

        fallback_used = not bool(category_template)
        source = "category_override" if category_template else "base_story_template"

        if not self._is_valid(template):
            template = deepcopy(self.base_templates.get("problem_solution") or {})
            fallback_used = True
            source = "emergency_problem_solution_fallback"

        return {
            "version": self.VERSION,
            "category": category,
            "template_key": f"{category}.{requested_story}",
            "source": source,
            "fallback_used": fallback_used,
            "profile": {
                "label": profile.get("label", ""),
                "opening_focus": profile.get("opening_focus", ""),
                "proof_focus": profile.get("proof_focus", ""),
                "cta_style": profile.get("cta_style", ""),
            },
            "template": template,
        }

    def _is_valid(self, template: Mapping[str, Any]) -> bool:
        curve = list(template.get("emotion_curve") or [])
        goals = list(template.get("scene_goals") or [])
        return bool(curve and goals) and all(
            isinstance(item, Mapping)
            and str(item.get("goal") or "").strip()
            and str(item.get("purpose") or "").strip()
            and bool(item.get("preferred_roles"))
            for item in goals
        )