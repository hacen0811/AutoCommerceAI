from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Mapping


class AIImageDirector:
    """
    Sprint131-1 AI Image + Motion Director

    역할:
    - SceneImagePlanner 결과를 기반으로 AI 이미지 생성이 필요한 장면만 선별
    - 실제 상품 이미지가 배정된 장면은 재사용 대상으로 보존
    - AI 이미지 생성용 prompt / negative_prompt를 내부 데이터로만 생성
    - 프롬프트 문자열이 Image Motion 또는 영상 렌더 입력으로 전달되지 않도록
      image_path와 prompt 데이터를 명확히 분리
    - 장면 목적, 이미지 역할, 구도 정보를 바탕으로 자연스러운 이미지 모션 추천
    - 기존 ImageMotionGenerator가 인식하는 모션 이름만 반환하여 하위 호환 유지

    기본 구조:
        SceneImagePlanner
            ↓
        AIImageDirector
            ├─ existing_product_image → 기존 이미지 재사용 + 모션 추천
            └─ ai_image_required      → 이미지 생성 프롬프트 + 모션 추천
    """

    VERSION = "ai-image-director-131-1"
    RESULT_FILENAME = "ai_image_director_131_1.json"

    HUMAN_POLICY = {
        "hook": {
            "allowed": False,
            "reason": "첫 화면은 제품 집중",
        },
        "pain": {
            "allowed": True,
            "reason": "불편 상황 전달",
        },
        "feature": {
            "allowed": True,
            "reason": "사용 상황 설명",
        },
        "solution": {
            "allowed": True,
            "reason": "제품을 통한 해결 상황 표현",
        },
        "usage": {
            "allowed": True,
            "reason": "실제 활용 표현",
        },
        "proof": {
            "allowed": False,
            "reason": "기능 증명 중심",
        },
        "cta": {
            "allowed": False,
            "reason": "구매 결정용 제품 중심",
        },
    }

    AI_SOURCE_MARKERS = {
        "ai",
        "ai_image",
        "generated",
        "generate",
        "missing_scene",
        "missing_scenes_only",
        "ai_required",
        "ai_image_required",
    }

    EXISTING_SOURCE_MARKERS = {
        "product_image",
        "existing_image",
        "existing_product_image",
        "reuse",
        "manual_image",
        "selected_image",
        "source_image",
    }

    MOTION_POLICY = {
        "hook": {
            "motion": "zoom_in",
            "speed": "slow",
            "camera_style": "commercial_focus",
            "reason": "첫 장면은 제품 정체성을 빠르게 인식시키는 중앙 확대가 적합",
        },
        "hero": {
            "motion": "zoom_in",
            "speed": "slow",
            "camera_style": "commercial_focus",
            "reason": "대표 상품 이미지는 제품 중심의 느린 확대가 가장 안정적",
        },
        "pain": {
            "motion": "pan_left",
            "speed": "medium",
            "camera_style": "context_reveal",
            "reason": "불편 상황은 주변 환경을 함께 보여주는 수평 이동이 적합",
        },
        "feature": {
            "motion": "dolly_in",
            "speed": "slow",
            "camera_style": "feature_emphasis",
            "reason": "핵심 기능은 제품 디테일로 접근하는 확대가 적합",
        },
        "solution": {
            "motion": "zoom_out",
            "speed": "slow",
            "camera_style": "solution_reveal",
            "reason": "해결 장면은 제품과 사용 환경을 함께 드러내는 완만한 축소가 적합",
        },
        "usage": {
            "motion": "pan_right",
            "speed": "medium",
            "camera_style": "usage_follow",
            "reason": "사용 장면은 시선 흐름을 따라가는 수평 이동이 자연스러움",
        },
        "detail": {
            "motion": "dolly_in",
            "speed": "slow",
            "camera_style": "detail_closeup",
            "reason": "상세 이미지는 작은 기능과 재질을 강조하는 접근 모션이 적합",
        },
        "comparison": {
            "motion": "ken_burns",
            "speed": "medium",
            "camera_style": "comparison_scan",
            "reason": "비교 이미지는 화면 전체를 훑는 복합 이동이 적합",
        },
        "review": {
            "motion": "tilt_up",
            "speed": "slow",
            "camera_style": "evidence_scan",
            "reason": "리뷰·근거 이미지는 위로 읽어가는 시선 흐름이 자연스러움",
        },
        "proof": {
            "motion": "tilt_down",
            "speed": "slow",
            "camera_style": "proof_inspection",
            "reason": "기능 증명 장면은 제품 구조를 차분하게 훑는 모션이 적합",
        },
        "cta": {
            "motion": "zoom_in",
            "speed": "slow",
            "camera_style": "purchase_focus",
            "reason": "마지막 장면은 제품을 다시 중앙에 집중시키는 확대가 적합",
        },
    }

    SUPPORTED_MOTIONS = {
        "zoom_in",
        "pan_left",
        "zoom_out",
        "pan_right",
        "tilt_up",
        "dolly_in",
        "tilt_down",
        "ken_burns",
    }

    def generate(
        self,
        product_name: str = "",
        scenes: List[Dict[str, Any]] | None = None,
        product_context: Dict[str, Any] | None = None,
        scene_image_plan: Dict[str, Any] | None = None,
        output_dir: str = "",
        project_id: Any = "",
        save_result: bool = False,
    ) -> Dict[str, Any]:
        product_context = product_context or {}
        scene_image_plan = scene_image_plan or {}

        resolved_scenes = self._resolve_scenes(
            scenes=scenes,
            scene_image_plan=scene_image_plan,
        )

        resolved_product_name = str(
            product_name
            or product_context.get("product_name")
            or scene_image_plan.get("product_name")
            or ""
        ).strip()

        result: Dict[str, Any] = {
            "ok": False,
            "ready": False,
            "version": self.VERSION,
            "status": "not_run",
            "project_id": str(project_id or scene_image_plan.get("project_id") or ""),
            "product_name": resolved_product_name,
            "scene_count": len(resolved_scenes),
            "ai_image_scene_count": 0,
            "existing_image_scene_count": 0,
            "skipped_scene_count": 0,
            "image_prompts": [],
            "motion_plan": [],
            "motion_scene_count": 0,
            "scenes": [],
            "result_path": "",
            "warnings": [],
            "errors": [],
        }

        if not resolved_scenes:
            result["status"] = "no_scenes"
            result["errors"].append("AI 이미지 방향을 설계할 장면이 없습니다")
            return self._save_if_requested(
                result=result,
                output_dir=output_dir,
                save_result=save_result,
            )

        for index, raw_scene in enumerate(resolved_scenes, start=1):
            if not isinstance(raw_scene, Mapping):
                result["skipped_scene_count"] += 1
                result["warnings"].append(
                    f"scene_{index:02d}: dict 형식이 아니어서 제외했습니다"
                )
                continue

            scene = dict(raw_scene)
            item = self._build_scene_direction(
                product_name=resolved_product_name,
                scene=scene,
                product_context=product_context,
                index=index,
            )
            result["scenes"].append(item)

            result["motion_plan"].append(
                {
                    "scene_id": item["scene_id"],
                    "scene_index": item["scene_index"],
                    "purpose": item["purpose"],
                    "recommended_motion": item["recommended_motion"],
                    "motion_speed": item["motion_speed"],
                    "motion_reason": item["motion_reason"],
                    "camera_style": item["camera_style"],
                    "motion_input_allowed": item["motion_input_allowed"],
                }
            )
            result["motion_scene_count"] += 1

            if item["generation_required"]:
                result["image_prompts"].append(
                    {
                        "scene_id": item["scene_id"],
                        "purpose": item["purpose"],
                        "image_prompt": item["image_prompt"],
                        "negative_prompt": item["negative_prompt"],
                        "reference_image_path": item["reference_image_path"],
                        "output_image_path": item["output_image_path"],
                        "prompt_internal_only": True,
                    }
                )
                result["ai_image_scene_count"] += 1
            elif item["resolved_image_path"]:
                result["existing_image_scene_count"] += 1
            else:
                result["skipped_scene_count"] += 1

        result["ok"] = bool(result["scenes"])
        result["ready"] = bool(result["image_prompts"])
        result["status"] = (
            "prompts_ready"
            if result["ready"]
            else "existing_images_only"
            if result["existing_image_scene_count"] > 0
            else "no_generation_targets"
        )

        return self._save_if_requested(
            result=result,
            output_dir=output_dir,
            save_result=save_result,
        )

    def build(
        self,
        scene_image_plan: Dict[str, Any] | None = None,
        product_name: str = "",
        product_context: Dict[str, Any] | None = None,
        output_dir: str = "",
        project_id: Any = "",
        save_result: bool = True,
    ) -> Dict[str, Any]:
        """WorkflowEngine 연결용 별칭."""
        return self.generate(
            product_name=product_name,
            product_context=product_context,
            scene_image_plan=scene_image_plan,
            output_dir=output_dir,
            project_id=project_id,
            save_result=save_result,
        )

    def _resolve_scenes(
        self,
        scenes: List[Dict[str, Any]] | None,
        scene_image_plan: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        if isinstance(scenes, list) and scenes:
            return [dict(item) for item in scenes if isinstance(item, Mapping)]

        for key in (
            "scenes",
            "scene_images",
            "image_scenes",
            "plans",
            "items",
        ):
            value = scene_image_plan.get(key)
            if isinstance(value, list):
                return [dict(item) for item in value if isinstance(item, Mapping)]

        return []

    def _build_scene_direction(
        self,
        product_name: str,
        scene: Dict[str, Any],
        product_context: Dict[str, Any],
        index: int,
    ) -> Dict[str, Any]:
        scene_id = str(
            scene.get("scene_id")
            or f"scene_{index:02d}"
        ).strip()

        purpose = self._first_text(
            scene.get("story_purpose"),
            scene.get("purpose"),
            scene.get("scene_type"),
            scene.get("role"),
            "feature",
        ).lower()

        must_show = self._first_text(
            scene.get("must_show"),
            scene.get("primary_selling_point"),
            scene.get("selling_point"),
            scene.get("scene_goal"),
            scene.get("visual_goal"),
        )

        existing_image_path = self._first_text(
            scene.get("resolved_image_path"),
            scene.get("selected_image_path"),
            scene.get("existing_image_path"),
            scene.get("product_image_path"),
            scene.get("source_image_path"),
            scene.get("image_path"),
            scene.get("reference_image_path"),
        )

        source_type = self._first_text(
            scene.get("source_type"),
            scene.get("image_source"),
            scene.get("source"),
            scene.get("generation_mode"),
            scene.get("image_mode"),
        ).lower()

        generation_required = self._requires_ai_image(
            scene=scene,
            source_type=source_type,
            existing_image_path=existing_image_path,
        )

        human_policy = self._resolve_human_policy(purpose)

        reference_image_path = self._first_text(
            scene.get("reference_image_path"),
            existing_image_path,
            product_context.get("main_image_path"),
            product_context.get("product_image_path"),
        )

        prompt = ""
        negative_prompt = ""
        output_image_path = ""

        if generation_required:
            prompt = self._create_prompt(
                product_name=product_name,
                purpose=purpose,
                must_show=must_show,
                human_policy=human_policy,
                scene=scene,
                product_context=product_context,
            )
            negative_prompt = self._create_negative_prompt(
                human_policy=human_policy,
            )
            output_image_path = self._first_text(
                scene.get("output_image_path"),
                scene.get("generated_image_path"),
                f"{scene_id}_ai.png",
            )

        motion_direction = self._resolve_motion_direction(
            purpose=purpose,
            scene=scene,
        )

        return {
            "scene_id": scene_id,
            "scene_index": int(scene.get("scene_index") or index),
            "purpose": purpose,
            "product_name": product_name,
            "must_show": must_show,
            "source_type": (
                "ai_image_required"
                if generation_required
                else "existing_product_image"
                if existing_image_path
                else "unresolved"
            ),
            "generation_required": generation_required,
            "resolved_image_path": (
                ""
                if generation_required
                else existing_image_path
            ),
            "reference_image_path": reference_image_path,
            "output_image_path": output_image_path,
            "image_prompt": prompt,
            "negative_prompt": negative_prompt,
            "prompt_internal_only": True,
            "motion_input_allowed": False if generation_required else bool(existing_image_path),
            "recommended_motion": motion_direction["motion"],
            "motion_speed": motion_direction["speed"],
            "motion_reason": motion_direction["reason"],
            "camera_style": motion_direction["camera_style"],
            "motion_source": motion_direction["source"],
            "human_allowed": human_policy["allowed"],
            "human_policy_reason": human_policy["reason"],
            "product_priority": True,
            "source_scene": scene,
        }

    def _requires_ai_image(
        self,
        scene: Dict[str, Any],
        source_type: str,
        existing_image_path: str,
    ) -> bool:
        explicit = scene.get("generation_required")
        if isinstance(explicit, bool):
            return explicit

        for key in (
            "ai_image_required",
            "needs_ai_image",
            "generate_image",
            "should_generate",
            "missing_scene",
        ):
            value = scene.get(key)
            if isinstance(value, bool):
                return value

        normalized_source = str(source_type or "").strip().lower()
        if any(marker in normalized_source for marker in self.AI_SOURCE_MARKERS):
            return True
        if any(marker in normalized_source for marker in self.EXISTING_SOURCE_MARKERS):
            return False

        return not bool(existing_image_path)

    def _resolve_human_policy(
        self,
        purpose: str,
    ) -> Dict[str, Any]:
        normalized = str(purpose or "").lower()
        for key, value in self.HUMAN_POLICY.items():
            if key in normalized:
                return dict(value)
        return dict(self.HUMAN_POLICY["feature"])

    def _resolve_motion_direction(
        self,
        purpose: str,
        scene: Dict[str, Any],
    ) -> Dict[str, str]:
        requested_motion = self._first_text(
            scene.get("recommended_motion"),
            scene.get("motion"),
            scene.get("camera_motion"),
            scene.get("motion_type"),
        ).lower()

        requested_speed = self._first_text(
            scene.get("motion_speed"),
            scene.get("speed"),
        ).lower()

        if requested_motion in self.SUPPORTED_MOTIONS:
            return {
                "motion": requested_motion,
                "speed": requested_speed or "slow",
                "reason": "상위 장면 계획에서 지정한 모션을 사용",
                "camera_style": self._first_text(
                    scene.get("camera_style"),
                    "planned",
                ),
                "source": "scene_override",
            }

        normalized_purpose = str(purpose or "").strip().lower()

        for key, policy in self.MOTION_POLICY.items():
            if key in normalized_purpose:
                return {
                    "motion": str(policy["motion"]),
                    "speed": requested_speed or str(policy["speed"]),
                    "reason": str(policy["reason"]),
                    "camera_style": str(policy["camera_style"]),
                    "source": f"purpose_policy:{key}",
                }

        image_role = self._first_text(
            scene.get("image_role"),
            scene.get("role"),
            scene.get("visual_role"),
            scene.get("scene_type"),
        ).lower()

        for key, policy in self.MOTION_POLICY.items():
            if key in image_role:
                return {
                    "motion": str(policy["motion"]),
                    "speed": requested_speed or str(policy["speed"]),
                    "reason": str(policy["reason"]),
                    "camera_style": str(policy["camera_style"]),
                    "source": f"role_policy:{key}",
                }

        return {
            "motion": "zoom_in",
            "speed": requested_speed or "slow",
            "reason": "장면 유형을 특정할 수 없어 가장 안전한 제품 중심 확대를 사용",
            "camera_style": "commercial_focus",
            "source": "default",
        }

    def _create_prompt(
        self,
        product_name: str,
        purpose: str,
        must_show: str,
        human_policy: Dict[str, Any],
        scene: Dict[str, Any],
        product_context: Dict[str, Any],
    ) -> str:
        human_text = (
            "A natural Korean adult may appear using the product, "
            "but the product must remain clearly visible and be the main subject."
            if human_policy["allowed"]
            else
            "No person, no face, no hands, no human model. Show the product only."
        )

        environment = self._first_text(
            scene.get("environment"),
            scene.get("location"),
            scene.get("setting"),
            product_context.get("environment"),
            "a realistic Korean daily-life environment",
        )

        composition = self._first_text(
            scene.get("composition"),
            scene.get("shot_type"),
            scene.get("camera"),
            "vertical commercial composition with clear product visibility",
        )

        return (
            "Create one realistic commercial product photograph for a vertical "
            "9:16 shopping short.\n\n"
            f"Product: {product_name or 'the provided product'}\n"
            f"Scene purpose: {purpose}\n"
            f"Required visual: {must_show or 'show the main product benefit clearly'}\n"
            f"Environment: {environment}\n"
            f"Composition: {composition}\n\n"
            "Product identity requirements:\n"
            "- Use the provided reference product as the exact identity source.\n"
            "- Preserve the exact shape, color, proportions, material, controls, "
            "attachments and visible details.\n"
            "- Do not redesign, replace, simplify or invent product parts.\n"
            "- Keep the product clearly visible and visually dominant.\n\n"
            "Human policy:\n"
            f"- {human_text}\n\n"
            "Image requirements:\n"
            "- Photorealistic Korean commercial photography.\n"
            "- Natural lighting and realistic shadows.\n"
            "- Clean premium shopping advertisement quality.\n"
            "- One coherent scene, not a collage.\n"
            "- No text, no captions, no subtitles, no letters, no numbers.\n"
            "- No logos, no price tags, no badges, no watermarks, no UI elements.\n"
            "- Do not render any part of this prompt inside the image."
        )

    def _create_negative_prompt(
        self,
        human_policy: Dict[str, Any],
    ) -> str:
        parts = [
            "text",
            "caption",
            "subtitle",
            "letters",
            "numbers",
            "logo",
            "watermark",
            "price tag",
            "badge",
            "poster",
            "infographic",
            "user interface",
            "screenshot",
            "collage",
            "split screen",
            "duplicate product",
            "wrong product",
            "altered product",
            "deformed product",
            "invented controls",
            "incorrect color",
            "blurry product",
            "cropped product",
        ]
        if not human_policy["allowed"]:
            parts.extend(
                [
                    "person",
                    "face",
                    "hands",
                    "human model",
                ]
            )
        return ", ".join(parts)

    def _save_if_requested(
        self,
        result: Dict[str, Any],
        output_dir: str,
        save_result: bool,
    ) -> Dict[str, Any]:
        if not save_result:
            return result

        directory = Path(str(output_dir or ".")).expanduser()
        path = directory / self.RESULT_FILENAME
        result["result_path"] = self.save_json(result, str(path))
        return result

    def _first_text(self, *values: Any) -> str:
        for value in values:
            text = str(value or "").strip()
            if text:
                return text
        return ""

    def save_json(
        self,
        result: Dict[str, Any],
        path: str,
    ) -> str:
        output = Path(path)
        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        output.write_text(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        return str(output)


if __name__ == "__main__":
    engine = AIImageDirector()

    sample = engine.generate(
        product_name="에어클립 휴대용 회전 초미니 선풍기",
        scene_image_plan={
            "project_id": "sample",
            "scenes": [
                {
                    "scene_id": "scene_01",
                    "purpose": "hook",
                    "must_show": "제품 첫인상",
                    "source_type": "existing_product_image",
                    "selected_image_path": "assets/sample/hero.png",
                },
                {
                    "scene_id": "scene_03",
                    "purpose": "usage",
                    "must_show": "사무실 책상에서 사용하는 장면",
                    "source_type": "ai_image_required",
                    "reference_image_path": "assets/sample/product.png",
                },
            ],
        },
        output_dir=".",
        save_result=False,
    )

    print(
        json.dumps(
            sample,
            ensure_ascii=False,
            indent=2,
        )
    )