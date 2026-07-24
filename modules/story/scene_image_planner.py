from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

from .scene_director import SceneDirector
from .scene_beat_planner import SceneBeatPlanner


class SceneImagePlanner:
    """
    Sprint127-1 Scene Image Planner

    역할:
    - Story Intelligence와 Scene Planner 결과를 결합
    - 장면별 자막·목적·리뷰 근거에 맞는 이미지 제작 계획 생성
    - 실제 상품 이미지 재사용과 AI 보완 이미지 생성을 구분
    - 모델·의상·배경 톤을 고정하기 위한 연속성 프로필 생성
    - 외부 이미지 생성 API는 호출하지 않음
    """

    VERSION = "scene-image-planner-127-1"

    PURPOSE_PROFILES: Dict[str, Dict[str, Any]] = {
        "hook": {
            "visual_goal": "첫 2초 안에 제품과 핵심 변화를 동시에 보여준다",
            "scene_kind": "attention_product_usage",
            "camera": "medium_close_up",
            "composition": "제품을 전경에 크게 두고 사용 결과가 한눈에 보이는 세로 구도",
            "source_strategy": "mixed",
            "ai_priority": "high",
            "motion": "strong_push_in",
        },
        "pain": {
            "visual_goal": "기존 사용 방식의 불편을 실제 상황으로 보여준다",
            "scene_kind": "problem_context",
            "camera": "medium_shot",
            "composition": "불편한 행동과 표정이 보이되 제품 혼동이 없도록 단순한 배경 사용",
            "source_strategy": "ai_generated",
            "ai_priority": "high",
            "motion": "slow_pan",
        },
        "feature": {
            "visual_goal": "대사에서 말하는 핵심 기능을 제품 중심으로 명확히 보여준다",
            "scene_kind": "feature_demonstration",
            "camera": "close_up",
            "composition": "제품 형태와 기능 부위가 가려지지 않는 디테일 중심 구도",
            "source_strategy": "product_image",
            "ai_priority": "medium",
            "motion": "micro_zoom",
        },
        "solution": {
            "visual_goal": "제품을 사용해 문제가 해결되는 순간을 보여준다",
            "scene_kind": "solution_usage",
            "camera": "medium_close_up",
            "composition": "모델의 사용 동작과 제품이 동시에 선명하게 보이는 구도",
            "source_strategy": "mixed",
            "ai_priority": "high",
            "motion": "slow_zoom_in",
        },
        "benefit": {
            "visual_goal": "제품 사용 후 얻는 편리함과 결과를 보여준다",
            "scene_kind": "benefit_result",
            "camera": "medium_shot",
            "composition": "사용 환경과 제품 결과가 함께 보이는 생활형 광고 구도",
            "source_strategy": "mixed",
            "ai_priority": "medium",
            "motion": "slow_zoom_in",
        },
        "usage": {
            "visual_goal": "대사에 나온 실제 환경에서 올바른 사용 모습을 보여준다",
            "scene_kind": "lifestyle_usage",
            "camera": "medium_shot",
            "composition": "손과 제품의 사용 관계가 명확하고 제품이 가려지지 않는 구도",
            "source_strategy": "mixed",
            "ai_priority": "high",
            "motion": "pan_left_to_right",
        },
        "comparison": {
            "visual_goal": "두 방식 또는 전후 차이를 한눈에 비교하게 한다",
            "scene_kind": "comparison",
            "camera": "wide_medium",
            "composition": "좌우 또는 전후가 명확히 구분되는 단순한 비교 구도",
            "source_strategy": "product_image",
            "ai_priority": "low",
            "motion": "gentle_hold",
        },
        "proof": {
            "visual_goal": "리뷰 근거와 제품 세부 정보를 시각적으로 증명한다",
            "scene_kind": "detail_proof",
            "camera": "close_up",
            "composition": "제품 디테일과 근거가 되는 기능 부위를 확대하되 화면 내 문자는 생성하지 않음",
            "source_strategy": "product_image",
            "ai_priority": "low",
            "motion": "micro_zoom",
        },
        "cta": {
            "visual_goal": "제품의 최종 가치를 정리하고 깔끔하게 마무리한다",
            "scene_kind": "clean_product_close",
            "camera": "hero_shot",
            "composition": "제품 단독 또는 모델과 제품을 중심에 둔 깨끗한 광고 마감 구도",
            "source_strategy": "product_image",
            "ai_priority": "low",
            "motion": "slow_zoom_out",
        },
    }

    PRODUCT_ENVIRONMENTS: Dict[str, List[str]] = {
        "electronics": ["밝고 정돈된 한국 사무실", "책상과 노트북이 있는 실내", "일상적인 출퇴근 환경"],
        "laundry_storage": ["정돈된 한국 세탁실", "밝은 베란다", "생활감 있는 욕실 앞 공간"],
        "laundry_basket": ["정돈된 한국 세탁실", "밝은 베란다", "세탁기 옆 수납 공간"],
        "storage": ["정돈된 한국 가정집", "수납장 앞", "좁은 공간을 활용한 실내"],
        "cutting_board": ["밝고 깨끗한 한국 주방", "싱크대 옆 조리대", "자연광이 드는 주방"],
        "kitchen": ["밝고 깨끗한 한국 주방", "정돈된 조리대", "싱크대 주변"],
        "carrier": ["현대적인 공항 출국장", "깔끔한 호텔 객실", "여행 준비 중인 한국 가정집"],
        "travel": ["현대적인 공항", "깔끔한 호텔", "여행 준비 공간"],
        "bathroom": ["밝고 청결한 한국 욕실", "건식 세면대 주변", "정돈된 샤워 공간"],
        "cleaning": ["깔끔한 한국 가정집", "청소가 필요한 생활 공간", "정돈된 거실"],
        "beauty": ["밝은 화장대", "깔끔한 드레스룸", "자연광이 드는 실내"],
        "fashion": ["밝은 드레스룸", "심플한 실내", "일상적인 외출 공간"],
        "baby": ["안전하고 밝은 한국 가정집", "정돈된 육아 공간", "따뜻한 거실"],
        "pet": ["밝은 한국 가정집", "반려동물 생활 공간", "정돈된 거실"],
        "general": ["밝고 정돈된 한국 가정집", "제품 사용에 자연스러운 실내", "단순하고 깨끗한 배경"],
    }

    ROLE_TO_ASSET_TYPE = {
        "hero": "main_product",
        "usage": "usage_product",
        "lifestyle": "usage_product",
        "feature": "detail_product",
        "detail": "detail_product",
        "review": "review_evidence",
        "comparison": "comparison_product",
        "before_after": "comparison_product",
        "size": "detail_product",
        "package": "detail_product",
        "best_feature": "main_product",
        "problem": "context_reference",
        "text": "review_evidence",
    }

    def build(
        self,
        story_result: Any = None,
        scene_plan: Any = None,
        product_info: Any = None,
        image_role_result: Any = None,
        output_dir: Any = "",
        project_id: Any = "",
        save_result: bool = True,
    ) -> Dict[str, Any]:
        story = self._to_dict(story_result)
        plan = self._to_dict(scene_plan)
        product = self._to_dict(product_info)
        roles = self._to_dict(image_role_result)

        product_name = self._first_text(
            product.get("product_name"), product.get("name"), product.get("title"),
            story.get("product_name"), "선택 상품",
        )
        product_type = self._first_text(story.get("product_subtype"), story.get("product_type"), "general")
        scenes = [item for item in list(plan.get("scenes") or []) if isinstance(item, dict)]
        goals = [item for item in list(story.get("scene_goals") or []) if isinstance(item, dict)]
        image_inventory = self._build_image_inventory(roles)
        continuity = self._build_continuity_profile(product_name, product_type)
        scene_director = SceneDirector()
        scene_beat_planner = SceneBeatPlanner()

        planned: List[Dict[str, Any]] = []
        warnings: List[str] = []
        errors: List[str] = []

        count = max(len(scenes), len(goals))
        for index in range(count):
            scene = scenes[index] if index < len(scenes) else {}
            goal = goals[index] if index < len(goals) else {}
            planned.append(
                self._build_scene_item(
                    index=index,
                    scene=scene,
                    goal=goal,
                    story=story,
                    product_name=product_name,
                    product_type=product_type,
                    image_inventory=image_inventory,
                    continuity=continuity,
                    scene_director=scene_director,
                    scene_beat_planner=scene_beat_planner,
                )
            )

        if not planned:
            warnings.append("Scene Planner와 Story Intelligence에 장면이 없어 이미지 계획을 만들지 못했습니다")

        generated_count = sum(1 for item in planned if item.get("need_ai_image"))
        product_count = sum(1 for item in planned if item.get("use_product_image"))
        mixed_count = sum(1 for item in planned if item.get("visual_source") == "mixed")

        result: Dict[str, Any] = {
            "ok": bool(planned),
            "ready": bool(planned),
            "version": self.VERSION,
            "status": "planned" if planned else "empty",
            "project_id": str(project_id or ""),
            "product_name": product_name,
            "product_type": product_type,
            "story_type": str(story.get("story_type") or ""),
            "scene_count": len(planned),
            "generated_scene_count": generated_count,
            "product_image_scene_count": product_count,
            "mixed_scene_count": mixed_count,
            "beat_count": sum(int(item.get("beat_count") or 0) for item in planned),
            "multi_beat_scene_count": sum(1 for item in planned if int(item.get("beat_count") or 0) > 1),
            "continuity_profile": continuity,
            "image_inventory": image_inventory,
            "scenes": planned,
            "cost_policy": {
                "video_generation_enabled": False,
                "ai_image_generation_mode": "missing_scenes_only",
                "reuse_existing_product_images": True,
                "reuse_generated_images": True,
                "max_ai_image_scenes": generated_count,
            },
            "plan_path": "",
            "warnings": warnings,
            "errors": errors,
        }

        if save_result and output_dir:
            try:
                target_dir = Path(str(output_dir))
                target_dir.mkdir(parents=True, exist_ok=True)
                target_path = target_dir / "scene_image_plan_127_1.json"
                target_path.write_text(
                    json.dumps(result, ensure_ascii=False, indent=2, default=str),
                    encoding="utf-8",
                )
                result["plan_path"] = str(target_path)
            except Exception as exc:
                result["warnings"].append(f"계획 JSON 저장 실패: {type(exc).__name__}: {exc}")

        self._print_log(result)
        return result

    def _build_scene_item(
        self,
        index: int,
        scene: Mapping[str, Any],
        goal: Mapping[str, Any],
        story: Mapping[str, Any],
        product_name: str,
        product_type: str,
        image_inventory: Mapping[str, Any],
        continuity: Mapping[str, Any],
        scene_director: SceneDirector,
        scene_beat_planner: SceneBeatPlanner,
    ) -> Dict[str, Any]:
        scene_id = self._first_text(scene.get("scene_id"), goal.get("scene_id"), f"scene_{index + 1:02d}")
        purpose = self._normalize_purpose(
            self._first_text(scene.get("story_purpose"), goal.get("purpose"), scene.get("script_section_key"), "feature")
        )
        profile = dict(self.PURPOSE_PROFILES.get(purpose) or self.PURPOSE_PROFILES["feature"])
        subtitle = self._first_text(scene.get("dialogue"), scene.get("subtitle_text"), goal.get("subtitle"))
        story_goal = self._first_text(scene.get("story_goal"), goal.get("goal"), profile["visual_goal"])
        evidence = self._first_text(
            scene.get("review_evidence"), goal.get("review_evidence"), goal.get("evidence_text"),
        )
        selling_point = self._first_text(
            scene.get("primary_selling_point"), goal.get("primary_selling_point"),
            (story.get("selling_points") or [""])[0] if isinstance(story.get("selling_points"), Sequence) else "",
        )
        preferred_roles = self._unique_strings(
            scene.get("preferred_roles") or goal.get("preferred_roles") or []
        )
        preferred_asset_types = self._unique_strings(
            self.ROLE_TO_ASSET_TYPE.get(role, role) for role in preferred_roles
        )
        available_roles = set(image_inventory.get("available_roles") or [])
        existing_match = next((role for role in preferred_roles if role in available_roles), "")

        source_strategy = str(profile["source_strategy"])
        if purpose == "pain":
            visual_source = "ai_generated"
        elif existing_match and source_strategy == "product_image":
            visual_source = "product_image"
        elif existing_match and source_strategy == "mixed":
            visual_source = "mixed"
        elif source_strategy == "product_image":
            visual_source = "product_image"
        else:
            visual_source = "ai_generated"

        need_ai_image = visual_source in {"ai_generated", "mixed"}
        use_product_image = visual_source in {"product_image", "mixed"}
        environment = self._select_environment(product_type, purpose, subtitle)
        people = 0 if purpose in {"feature", "proof", "comparison", "cta"} else 1
        direction = scene_director.direct(
            scene_id=scene_id,
            purpose=purpose,
            subtitle=subtitle,
            story_goal=story_goal,
            product_name=product_name,
            product_type=product_type,
            environment=environment,
            continuity=continuity,
            people=people,
        )
        beat_plan = scene_beat_planner.plan(
            scene_id=scene_id,
            purpose=purpose,
            subtitle=subtitle,
            story_goal=story_goal,
            scene_direction=direction,
            product_name=product_name,
            product_type=product_type,
            environment=environment,
            people=people,
        )
        prompt = self._build_prompt(
            product_name=product_name,
            subtitle=subtitle,
            purpose=purpose,
            environment=environment,
            profile=profile,
            selling_point=selling_point,
            continuity=continuity,
            direction=direction,
            beat_plan=beat_plan,
        )

        return {
            "scene_id": scene_id,
            "order": index + 1,
            "purpose": purpose,
            "subtitle": subtitle,
            "story_goal": story_goal,
            "review_evidence": evidence,
            "primary_selling_point": selling_point,
            "visual_goal": profile["visual_goal"],
            "scene_kind": profile["scene_kind"],
            "visual_source": visual_source,
            "need_ai_image": need_ai_image,
            "use_product_image": use_product_image,
            "ai_priority": profile["ai_priority"],
            "preferred_roles": preferred_roles,
            "preferred_asset_types": preferred_asset_types,
            "matched_existing_role": existing_match,
            "environment": environment,
            "people": people,
            "model_usage": purpose in {"hook", "pain", "solution", "benefit", "usage"},
            "camera": profile["camera"],
            "composition": profile["composition"],
            "product_visibility": "제품 전체 형태와 핵심 기능 부위가 명확히 보여야 함",
            "continuity_profile_id": continuity.get("profile_id", ""),
            "motion": profile["motion"],
            "scene_direction": direction,
            "scene_beat_plan": beat_plan,
            "beat_count": beat_plan.get("beat_count", 0),
            "primary_beat_id": beat_plan.get("primary_beat_id", ""),
            "image_prompt": prompt,
            "negative_prompt": (
                "제품 형태 변경, 제품 색상 변경, 로고 변경, 다른 제품, 추가 제품, "
                "손가락 오류, 비현실적인 손, 화면 속 글자, 자막, 워터마크, 가격표, "
                "과도한 소품, 복잡한 배경, 제품 가림, 가로 이미지"
            ),
            "generation_rules": {
                "aspect_ratio": "9:16",
                "language_text_in_image": False,
                "preserve_product_identity": True,
                "reference_product_image_required": need_ai_image,
                "same_model_required": bool(continuity.get("use_same_model")),
                "cache_key": f"{product_type}:{scene_id}:{purpose}:{subtitle[:80]}",
            },
        }

    def _build_prompt(
        self,
        product_name: str,
        subtitle: str,
        purpose: str,
        environment: str,
        profile: Mapping[str, Any],
        selling_point: str,
        continuity: Mapping[str, Any],
        direction: Mapping[str, Any],
        beat_plan: Mapping[str, Any],
    ) -> str:
        model_text = ""
        if purpose in {"hook", "pain", "solution", "benefit", "usage"}:
            model_text = (
                f"{continuity.get('model_description', '')}, "
                f"{continuity.get('wardrobe', '')}, 같은 모델과 같은 의상 유지, "
            )
        return " ".join(
            part for part in [
                "세로 9:16 한국 쇼핑 쇼츠용 사실적인 광고 이미지.",
                f"제품: {product_name}.",
                f"장면 대사: {subtitle}." if subtitle else "",
                f"장면 목적: {profile.get('visual_goal', '')}.",
                f"핵심 장점: {selling_point}." if selling_point else "",
                f"환경: {environment}.",
                model_text,
                f"카메라: {profile.get('camera', '')}.",
                f"구도: {profile.get('composition', '')}.",
                f"감독 연출: {direction.get('directing_summary', '')}.",
                f"장면 비트: {beat_plan.get('beat_prompt_summary', '')}.",
                "제공된 상품 참고 이미지의 제품 형태, 색상, 크기 비율, 구조와 로고를 그대로 유지.",
                "제품이 화면에서 명확히 보이고 실제 사용법이 물리적으로 자연스러워야 함.",
                "이미지 안에 글자, 자막, 가격, 워터마크를 넣지 않음.",
                "자연스러운 한국 생활 공간, 과장되지 않은 광고 사진, 깨끗한 조명, 높은 제품 선명도.",
            ] if part
        )

    def _build_continuity_profile(self, product_name: str, product_type: str) -> Dict[str, Any]:
        return {
            "profile_id": f"continuity-{product_type}-127-1",
            "use_same_model": True,
            "model_description": "30대 한국인 여성 모델 1명, 자연스러운 얼굴, 현실적인 체형",
            "wardrobe": "무지 밝은 베이지 상의와 검정 하의",
            "product_identity": product_name,
            "background_tone": "밝고 깨끗한 생활형 광고 톤",
            "lighting": "부드러운 자연광과 중성적인 실내 조명",
            "camera_style": "현실적인 한국 쇼핑 광고 사진",
            "rules": [
                "사람이 등장하는 모든 장면은 동일 인물과 동일 의상 유지",
                "제품 형태·색상·비율·버튼·구조·로고 변경 금지",
                "장면마다 모델 또는 제품을 새롭게 재해석하지 않음",
                "이미지 안에 자막이나 설명 글자를 생성하지 않음",
            ],
        }

    def _build_image_inventory(self, role_result: Mapping[str, Any]) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        paths: Dict[str, List[str]] = {}
        for item in list(role_result.get("images") or []):
            if not isinstance(item, Mapping):
                continue
            role = self._first_text(item.get("image_type"), item.get("role"), "unknown").lower()
            path = self._first_text(item.get("output_path"), item.get("path"), item.get("source_path"))
            counts[role] = counts.get(role, 0) + 1
            if path:
                paths.setdefault(role, []).append(path)
        return {
            "available_roles": sorted(counts),
            "role_counts": counts,
            "paths_by_role": paths,
            "image_count": sum(counts.values()),
        }

    def _select_environment(self, product_type: str, purpose: str, subtitle: str) -> str:
        text = str(subtitle or "")
        keyword_environments = (
            (("책상", "사무실", "노트북", "업무"), "밝고 정돈된 한국 사무실 책상"),
            (("캠핑", "야외"), "깨끗하고 현실적인 캠핑 환경"),
            (("출퇴근", "지하철", "버스"), "한국의 현실적인 출퇴근 환경"),
            (("주방", "요리", "칼질", "세척"), "밝고 깨끗한 한국 주방 조리대"),
            (("세탁", "빨래", "세탁기"), "정돈된 한국 가정집 세탁실"),
            (("공항", "여행", "호텔"), "현대적이고 깔끔한 여행 환경"),
        )
        for keywords, environment in keyword_environments:
            if any(keyword in text for keyword in keywords):
                return environment
        environments = self.PRODUCT_ENVIRONMENTS.get(product_type) or self.PRODUCT_ENVIRONMENTS["general"]
        if purpose == "pain" and len(environments) > 1:
            return environments[1]
        return environments[0]

    def _normalize_purpose(self, value: str) -> str:
        lowered = str(value or "feature").strip().lower()
        aliases = {
            "intro": "hook", "opening": "hook", "empathy": "pain",
            "problem": "pain", "result": "benefit", "demonstration": "usage",
            "evidence": "proof", "close": "cta", "ending": "cta",
        }
        return aliases.get(lowered, lowered if lowered in self.PURPOSE_PROFILES else "feature")

    def _unique_strings(self, values: Any) -> List[str]:
        if isinstance(values, str):
            values = [values]
        output: List[str] = []
        for value in values or []:
            text = str(value or "").strip().lower()
            if text and text not in output:
                output.append(text)
        return output

    def _to_dict(self, value: Any) -> Dict[str, Any]:
        return dict(value) if isinstance(value, Mapping) else {}

    def _first_text(self, *values: Any) -> str:
        for value in values:
            text = str(value or "").strip()
            if text:
                return text
        return ""

    def _print_log(self, result: Mapping[str, Any]) -> None:
        print("[Sprint127-1 Scene Image Planner] Version:", result.get("version", ""), flush=True)
        print("[Sprint127-1 Scene Image Planner] Status:", result.get("status", ""), flush=True)
        print("[Sprint127-1 Scene Image Planner] Scene Count:", result.get("scene_count", 0), flush=True)
        print("[Sprint127-1 Scene Image Planner] AI Images:", result.get("generated_scene_count", 0), flush=True)
        print("[Sprint127-1 Scene Image Planner] Product Images:", result.get("product_image_scene_count", 0), flush=True)
        print("[Sprint127-1 Scene Image Planner] Plan Path:", result.get("plan_path", ""), flush=True)
        for item in list(result.get("scenes") or []):
            print(
                "[Sprint127-1 Scene Beat]",
                item.get("scene_id", ""),
                f"purpose={item.get('purpose', '')}",
                f"source={item.get('visual_source', '')}",
                "->",
                item.get("subtitle", ""),
                flush=True,
            )
        print("[Sprint127-1 Scene Image Planner] Errors:", result.get("errors", []), flush=True)