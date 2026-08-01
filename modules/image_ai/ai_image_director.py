from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping


class AIImageDirector:
    """
    Sprint141-6 Workflow Closed Loop Image Generation Controller

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

    VERSION = "ai-image-director-157-cost-guard-resume"
    RESULT_FILENAME = "ai_image_director_157.json"

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


    FIDELITY_THRESHOLD = 90.0
    MAX_GENERATION_ATTEMPTS = 2

    FIDELITY_WEIGHTS = {
        "shape_match": 24.0,
        "color_match": 14.0,
        "proportion_match": 14.0,
        "controls_match": 14.0,
        "attachment_match": 14.0,
        "material_match": 8.0,
        "scale_match": 6.0,
        "scene_match": 6.0,
    }

    FIDELITY_ALIASES = {
        "shape_match": (
            "shape_match",
            "shape",
            "silhouette_match",
            "structure_match",
            "form_match",
        ),
        "color_match": (
            "color_match",
            "colour_match",
            "color",
            "colour",
        ),
        "proportion_match": (
            "proportion_match",
            "proportions_match",
            "ratio_match",
            "dimension_match",
        ),
        "controls_match": (
            "controls_match",
            "button_match",
            "buttons_match",
            "display_match",
            "detail_match",
        ),
        "attachment_match": (
            "attachment_match",
            "attachments_match",
            "hinge_match",
            "clip_match",
            "mount_match",
        ),
        "material_match": (
            "material_match",
            "surface_match",
            "texture_match",
            "finish_match",
        ),
        "scale_match": (
            "scale_match",
            "size_match",
            "realistic_scale",
        ),
        "scene_match": (
            "scene_match",
            "scene_goal_match",
            "usage_match",
            "composition_match",
        ),
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
        product_context = dict(product_context or {})
        scene_image_plan = dict(scene_image_plan or {})

        # Sprint150-4: output_dir를 product_context와 별개로 직접 보존합니다.
        # 기존 호출부가 product_context에 프로젝트 경로를 넣지 않아도
        # 프로젝트 폴더의 00_main 이미지를 참조 이미지로 찾을 수 있어야 합니다.
        resolved_output_dir = str(
            output_dir
            or product_context.get("output_dir")
            or product_context.get("project_dir")
            or product_context.get("product_dir")
            or scene_image_plan.get("output_dir")
            or scene_image_plan.get("project_dir")
            or scene_image_plan.get("product_dir")
            or ""
        ).strip()
        if resolved_output_dir:
            product_context.setdefault("output_dir", resolved_output_dir)
            product_context.setdefault("project_dir", resolved_output_dir)
            product_context.setdefault("product_dir", resolved_output_dir)

        identity_bundle = self._load_product_identity_bundle(
            output_dir=output_dir,
            product_context=product_context,
            scene_image_plan=scene_image_plan,
        )
        product_context = self._merge_identity_bundle_into_context(
            product_context=product_context,
            identity_bundle=identity_bundle,
        )

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
            "product_identity_loaded": bool(identity_bundle.get("loaded")),
            "product_identity_status": str(identity_bundle.get("status") or "not_found"),
            "product_identity_dna_path": str(identity_bundle.get("dna_path") or ""),
            "product_identity_structure_board_path": str(
                identity_bundle.get("structure_board_path") or ""
            ),
            "product_identity_source_dir": str(identity_bundle.get("source_dir") or ""),
            "product_identity_warnings": list(identity_bundle.get("warnings") or []),
            "fidelity_threshold": self.FIDELITY_THRESHOLD,
            "fidelity_checked_scene_count": 0,
            "fidelity_passed_scene_count": 0,
            "fidelity_failed_scene_count": 0,
            "fidelity_retry_scene_count": 0,
            "fidelity_results": [],
            "closed_loop_supported": True,
            "closed_loop_executed": False,
            "max_generation_attempts": self.MAX_GENERATION_ATTEMPTS,
            "generation_runs": [],
            "warnings": list(identity_bundle.get("warnings") or []),
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
                output_dir=resolved_output_dir,
                index=index,
            )
            fidelity_result = self._evaluate_scene_fidelity(
                scene=scene,
                direction=item,
            )
            item["fidelity_validation"] = fidelity_result
            result["scenes"].append(item)

            if fidelity_result["checked"]:
                result["fidelity_results"].append(fidelity_result)
                result["fidelity_checked_scene_count"] += 1
                if fidelity_result["passed"]:
                    result["fidelity_passed_scene_count"] += 1
                else:
                    result["fidelity_failed_scene_count"] += 1
                if fidelity_result["retry_required"]:
                    result["fidelity_retry_scene_count"] += 1

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
                        "reference_image_paths": item["reference_image_paths"],
                        "require_reference_image": True,
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

    def _load_product_identity_bundle(
        self,
        output_dir: str,
        product_context: Dict[str, Any],
        scene_image_plan: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        프로젝트 폴더에서 Product DNA와 Structure Board를 자동 탐색합니다.

        명시적으로 전달된 경로를 우선하며, 없을 때 output_dir 및 인접 폴더를
        검색합니다. JSON은 실제로 읽어서 product_context에 합칠 수 있는
        dict 데이터로 반환합니다.
        """
        bundle: Dict[str, Any] = {
            "loaded": False,
            "status": "not_found",
            "source_dir": "",
            "dna_path": "",
            "structure_board_path": "",
            "dna": {},
            "warnings": [],
        }

        explicit_dna_path = self._first_text(
            product_context.get("product_identity_dna_path"),
            product_context.get("product_dna_path"),
            product_context.get("dna_path"),
            scene_image_plan.get("product_identity_dna_path"),
            scene_image_plan.get("product_dna_path"),
            scene_image_plan.get("dna_path"),
        )
        explicit_board_path = self._first_text(
            product_context.get("product_identity_structure_board_path"),
            product_context.get("product_identity_board_path"),
            product_context.get("structure_board_path"),
            product_context.get("identity_board_path"),
            scene_image_plan.get("product_identity_structure_board_path"),
            scene_image_plan.get("product_identity_board_path"),
            scene_image_plan.get("structure_board_path"),
            scene_image_plan.get("identity_board_path"),
        )

        candidate_dirs = self._identity_candidate_directories(
            output_dir=output_dir,
            product_context=product_context,
            scene_image_plan=scene_image_plan,
        )

        dna_path = self._resolve_identity_file(
            explicit_path=explicit_dna_path,
            candidate_dirs=candidate_dirs,
            filename_patterns=(
                "product_identity_dna.json",
                "product_identity_dna_*.json",
                "product_dna.json",
                "product_dna_*.json",
                "*identity*dna*.json",
            ),
        )
        board_path = self._resolve_identity_file(
            explicit_path=explicit_board_path,
            candidate_dirs=candidate_dirs,
            filename_patterns=(
                "product_identity_structure_board.png",
                "product_identity_structure_board_*.png",
                "product_identity_board.png",
                "product_identity_board_*.png",
                "*structure*board*.png",
                "*identity*board*.png",
            ),
        )

        dna_data: Dict[str, Any] = {}
        if dna_path:
            try:
                loaded = json.loads(Path(dna_path).read_text(encoding="utf-8"))
                if isinstance(loaded, Mapping):
                    dna_data = dict(loaded)
                else:
                    bundle["warnings"].append(
                        f"Product DNA JSON이 dict 형식이 아닙니다: {dna_path}"
                    )
            except Exception as exc:
                bundle["warnings"].append(
                    f"Product DNA JSON 읽기 실패: {dna_path} ({type(exc).__name__}: {exc})"
                )

        bundle["dna_path"] = dna_path
        bundle["structure_board_path"] = board_path
        bundle["dna"] = dna_data

        resolved_paths = [path for path in (dna_path, board_path) if path]
        if resolved_paths:
            bundle["loaded"] = bool(dna_data or board_path)
            bundle["status"] = (
                "dna_and_structure_board_loaded"
                if dna_data and board_path
                else "dna_loaded"
                if dna_data
                else "structure_board_loaded"
            )
            bundle["source_dir"] = str(Path(resolved_paths[0]).parent)
        else:
            bundle["warnings"].append(
                "Product DNA 및 Structure Board를 자동 탐색하지 못했습니다"
            )

        return bundle

    def _merge_identity_bundle_into_context(
        self,
        product_context: Dict[str, Any],
        identity_bundle: Dict[str, Any],
    ) -> Dict[str, Any]:
        merged = dict(product_context or {})
        dna = identity_bundle.get("dna")

        if isinstance(dna, Mapping) and dna:
            existing_dna = self._first_mapping(
                merged.get("product_identity_dna"),
                merged.get("product_dna"),
                merged.get("identity_dna"),
                merged.get("dna"),
            )
            combined_dna = dict(dna)
            combined_dna.update(existing_dna)
            merged["product_identity_dna"] = combined_dna
            merged.setdefault("product_dna", combined_dna)

            identity_payload = self._first_mapping(
                combined_dna.get("product_identity"),
                combined_dna.get("identity"),
                combined_dna.get("product_dna"),
                combined_dna,
            )
            if identity_payload:
                merged.setdefault("product_identity", identity_payload)

        dna_path = self._first_text(identity_bundle.get("dna_path"))
        if dna_path:
            merged.setdefault("product_identity_dna_path", dna_path)
            merged.setdefault("product_dna_path", dna_path)

        board_path = self._first_text(identity_bundle.get("structure_board_path"))
        if board_path:
            merged.setdefault("product_identity_structure_board_path", board_path)
            merged.setdefault("product_identity_board_path", board_path)
            merged.setdefault("structure_board_path", board_path)

        return merged

    def _identity_candidate_directories(
        self,
        output_dir: str,
        product_context: Dict[str, Any],
        scene_image_plan: Dict[str, Any],
    ) -> List[Path]:
        raw_paths = [
            output_dir,
            product_context.get("output_dir"),
            product_context.get("project_dir"),
            product_context.get("product_dir"),
            product_context.get("asset_dir"),
            scene_image_plan.get("output_dir"),
            scene_image_plan.get("project_dir"),
            scene_image_plan.get("product_dir"),
        ]

        directories: List[Path] = []
        for raw_path in raw_paths:
            text = str(raw_path or "").strip()
            if not text:
                continue

            path = Path(text).expanduser()
            directory = path if path.suffix == "" else path.parent

            for candidate in (
                directory,
                directory / "product_identity",
                directory / "viral_pipeline_137_1",
                directory.parent,
                directory.parent / "product_identity",
            ):
                if candidate not in directories:
                    directories.append(candidate)

        return directories

    def _resolve_identity_file(
        self,
        explicit_path: str,
        candidate_dirs: List[Path],
        filename_patterns: tuple[str, ...],
    ) -> str:
        explicit = str(explicit_path or "").strip()
        if explicit:
            path = Path(explicit).expanduser()
            if path.is_file():
                return str(path)

        matches: List[Path] = []
        for directory in candidate_dirs:
            if not directory.exists() or not directory.is_dir():
                continue
            for pattern in filename_patterns:
                try:
                    matches.extend(
                        path
                        for path in directory.glob(pattern)
                        if path.is_file()
                    )
                except OSError:
                    continue

        if not matches:
            return ""

        unique_matches = list(dict.fromkeys(matches))
        unique_matches.sort(
            key=lambda path: (
                path.stat().st_mtime if path.exists() else 0.0,
                path.name,
            ),
            reverse=True,
        )
        return str(unique_matches[0])

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
        output_dir: str,
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

        reference_image_paths = self._resolve_reference_image_paths(
            scene=scene,
            existing_image_path=existing_image_path,
            product_context=product_context,
            output_dir=output_dir,
        )
        reference_image_path = reference_image_paths[0] if reference_image_paths else ""
        print(
            "[Sprint150-4 Director Reference]",
            {
                "scene_id": scene_id,
                "output_dir": str(output_dir or ""),
                "reference_image_path": reference_image_path,
                "reference_image_count": len(reference_image_paths),
            },
            flush=True,
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
            output_image_path = self._resolve_output_image_path(
                scene=scene,
                scene_id=scene_id,
                product_context=product_context,
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
            "reference_image_paths": reference_image_paths,
            "reference_image_count": len(reference_image_paths),
            "require_reference_image": bool(generation_required),
            "output_image_path": output_image_path,
            "generated_image_path": self._first_text(
                scene.get("generated_image_path"),
                scene.get("final_generated_image_path"),
                scene.get("ai_generated_image_path"),
            ),
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

    def _resolve_reference_image_paths(
        self,
        scene: Dict[str, Any],
        existing_image_path: str,
        product_context: Dict[str, Any],
        output_dir: str = "",
    ) -> List[str]:
        """Sprint150-4: 대표 상품 이미지 1장을 프로젝트 폴더까지 직접 탐색합니다."""
        candidates: List[str] = []

        def add(value: Any) -> None:
            if isinstance(value, Mapping):
                value = self._first_text(
                    value.get("path"),
                    value.get("image_path"),
                    value.get("selected_image_path"),
                    value.get("reference_image_path"),
                )
            text = str(value or "").strip()
            if not text:
                return
            path = Path(text).expanduser()
            if path.is_file():
                normalized = str(path)
                if normalized not in candidates:
                    candidates.append(normalized)

        # 장면에서 명시한 참조를 최우선으로 사용합니다.
        raw_scene_refs = scene.get("reference_image_paths")
        if isinstance(raw_scene_refs, (list, tuple, set)):
            for value in raw_scene_refs:
                add(value)
        add(scene.get("reference_image_path"))
        add(existing_image_path)

        # 대표 이미지와 상품 이미지 전체를 함께 사용합니다.
        add(product_context.get("main_image_path"))
        add(product_context.get("product_image_path"))
        add(product_context.get("reference_image_path"))

        ranked: List[Dict[str, Any]] = []
        for key in ("product_images", "images", "reference_images", "source_images"):
            group = product_context.get(key)
            if not isinstance(group, list):
                continue
            for index, item in enumerate(group):
                if isinstance(item, Mapping):
                    entry = dict(item)
                elif str(item or "").strip():
                    entry = {"path": str(item).strip()}
                else:
                    continue
                entry["_index"] = index
                ranked.append(entry)

        def rank(item: Dict[str, Any]) -> tuple[int, int, int]:
            image_type = self._first_text(
                item.get("type"), item.get("original_type"), item.get("role")
            ).lower()
            try:
                priority = int(item.get("priority") or 0)
            except Exception:
                priority = 0
            type_score = 4 if image_type in {"main", "hero"} else 3 if image_type == "detail" else 2
            return (type_score, priority, -int(item.get("_index") or 0))

        for item in sorted(ranked, key=rank, reverse=True):
            add(item)

        # Sprint150-4: product_context에 경로가 없어도 generate()의 output_dir를 직접 사용합니다.
        directory_values = [
            output_dir,
            product_context.get("output_dir"),
            product_context.get("project_dir"),
            product_context.get("product_dir"),
            product_context.get("asset_dir"),
        ]
        checked_directories: List[Path] = []
        for raw_directory in directory_values:
            directory_text = str(raw_directory or "").strip()
            if not directory_text:
                continue
            directory = Path(directory_text).expanduser()
            if directory.is_file():
                directory = directory.parent
            if directory in checked_directories or not directory.is_dir():
                continue
            checked_directories.append(directory)

            preferred_names = (
                "00_main.png", "00_main.jpg", "00_main.jpeg", "00_main.webp",
                "01_detail.png", "01_detail.jpg", "01_detail.jpeg", "01_detail.webp",
            )
            for name in preferred_names:
                add(directory / name)

            for pattern in ("*_main.*", "*_detail.*"):
                for path in sorted(directory.glob(pattern)):
                    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                        add(path)

            # 이름 규칙이 다른 업로드 파일도 마지막 안전망으로 탐색합니다.
            if not candidates:
                for path in sorted(directory.iterdir()):
                    if (
                        path.is_file()
                        and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
                        and "scene_" not in path.name.lower()
                        and "structure_board" not in path.name.lower()
                    ):
                        add(path)

        return candidates[:1]

    def _resolve_reference_image_path(
        self,
        scene: Dict[str, Any],
        existing_image_path: str,
        product_context: Dict[str, Any],
        output_dir: str = "",
    ) -> str:
        """하위 호환용: 첫 번째 참조 이미지 경로를 반환합니다."""
        paths = self._resolve_reference_image_paths(
            scene=scene,
            existing_image_path=existing_image_path,
            product_context=product_context,
            output_dir=output_dir,
        )
        return paths[0] if paths else ""

    def _resolve_output_image_path(
        self,
        scene: Dict[str, Any],
        scene_id: str,
        product_context: Dict[str, Any],
    ) -> str:
        """Sprint144-1: 생성 이미지를 프로젝트 폴더 안에 저장합니다."""
        requested = self._first_text(
            scene.get("output_image_path"),
            scene.get("generated_image_path"),
            f"{scene_id}_ai.png",
        )
        path = Path(requested).expanduser()
        if path.is_absolute():
            return str(path)

        output_dir = self._first_text(
            product_context.get("output_dir"),
            product_context.get("project_dir"),
            product_context.get("product_dir"),
        )
        if output_dir:
            return str(Path(output_dir).expanduser() / path.name)
        return str(path)

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
        """
        Gemini 이미지 생성용 최종 감독 프롬프트를 조립합니다.

        외부 파이프라인 구조는 변경하지 않고 Image Director 내부에서만
        Product DNA, Structure Board, 장면 연출, 인물, 카메라, 조명,
        바이럴 시각 규칙을 결합합니다.
        """
        sections = [
            self._build_system_prompt(),
            self._build_product_identity_section(
                product_name=product_name,
                scene=scene,
                product_context=product_context,
            ),
            self._build_scene_section(
                purpose=purpose,
                must_show=must_show,
                scene=scene,
                product_context=product_context,
            ),
            self._build_human_section(
                human_policy=human_policy,
                scene=scene,
            ),
            self._build_environment_section(
                scene=scene,
                product_context=product_context,
            ),
            self._build_camera_section(scene=scene),
            self._build_lighting_section(
                scene=scene,
                product_context=product_context,
            ),
            self._build_composition_section(scene=scene),
            self._build_viral_section(
                purpose=purpose,
                scene=scene,
                product_context=product_context,
            ),
            self._build_output_rules_section(),
        ]
        return "\n\n".join(
            section.strip()
            for section in sections
            if str(section or "").strip()
        )

    def _build_system_prompt(self) -> str:
        return (
            "[SYSTEM ROLE]\n"
            "You are the product photography director for a vertical shopping short.\n"
            "Create exactly one photorealistic commercial scene from the supplied "
            "reference product.\n"
            "The reference product is immutable. Direct the scene around the product; "
            "never redesign the product to fit the scene."
        )

    def _build_product_identity_section(
        self,
        product_name: str,
        scene: Dict[str, Any],
        product_context: Dict[str, Any],
    ) -> str:
        identity = self._resolve_product_identity(
            product_name=product_name,
            scene=scene,
            product_context=product_context,
        )

        lines = [
            "[PRODUCT IDENTITY LOCK]",
            f"Product name: {identity['product_name']}",
            f"Primary reference image: {identity['reference_image_path'] or 'use the supplied reference image'}",
            f"Product DNA source: {identity['dna_path'] or 'embedded product context'}",
            f"Structure Board source: {identity['structure_board_path'] or 'use all supplied product reference views'}",
        ]

        if identity["identity_summary"]:
            lines.append(f"Verified identity summary: {identity['identity_summary']}")
        if identity["shape"]:
            lines.append(f"Exact shape and silhouette: {identity['shape']}")
        if identity["color"]:
            lines.append(f"Exact color and finish: {identity['color']}")
        if identity["material"]:
            lines.append(f"Exact material and surface: {identity['material']}")
        if identity["controls"]:
            lines.append(f"Exact controls and visible details: {identity['controls']}")
        if identity["attachments"]:
            lines.append(f"Exact attachments, hinge, mount or clip: {identity['attachments']}")
        if identity["proportions"]:
            lines.append(f"Exact proportions and scale: {identity['proportions']}")

        lines.extend(
            [
                "Mandatory original-product compositing rules (highest priority):",
                "- Do not render the product, a similar product, slippers, shoes or a substitute object in the AI background plate.",
                "- Leave one clean and unobstructed central-lower placement zone for the untouched original product photograph.",
                "- Do not place feet, hands, water splashes, props, furniture, shadows or reflections across the reserved product zone.",
                "- Match the reserved zone to realistic product scale, floor contact and camera perspective.",
                "- Product identity will be preserved by compositing original pixels; never attempt to redraw it.",
                "- When the requested scene requires contact or deformation, simplify it to a non-contact display scene.",
            ]
        )
        return "\n".join(lines)

    def _build_scene_section(
        self,
        purpose: str,
        must_show: str,
        scene: Dict[str, Any],
        product_context: Dict[str, Any],
    ) -> str:
        goal = self._first_text(
            scene.get("scene_goal"),
            scene.get("visual_goal"),
            scene.get("goal"),
            must_show,
            "show the main product benefit clearly",
        )
        action = self._first_text(
            scene.get("action"),
            scene.get("human_action"),
            scene.get("product_action"),
            scene.get("usage_action"),
            product_context.get("action"),
        )
        emotion = self._first_text(
            scene.get("emotion"),
            scene.get("emotional_tone"),
            scene.get("mood"),
            product_context.get("emotion"),
        )
        story_context = self._first_text(
            scene.get("story_context"),
            scene.get("narrative"),
            scene.get("subtitle"),
            scene.get("script"),
        )

        lines = [
            "[SCENE DIRECTION]",
            f"Story purpose: {purpose or 'feature'}",
            f"Scene goal: {goal}",
        ]
        if action:
            lines.append(f"Primary action: {action}")
        if emotion:
            lines.append(f"Emotional tone: {emotion}")
        if story_context:
            lines.append(f"Story context: {story_context}")
        lines.extend(
            [
                "- Show one clear moment, not multiple time steps.",
                "- Make the action immediately understandable without text.",
                "- The product must remain the visual cause of the scene's result.",
            ]
        )
        return "\n".join(lines)

    def _build_human_section(
        self,
        human_policy: Dict[str, Any],
        scene: Dict[str, Any],
    ) -> str:
        if not human_policy.get("allowed"):
            return (
                "[HUMAN DIRECTION]\n"
                "No person, no face, no hands and no human model.\n"
                "Show the product alone or naturally installed in the environment.\n"
                f"Reason: {human_policy.get('reason', 'product-focused scene')}"
            )

        subject = self._first_text(
            scene.get("human"),
            scene.get("person"),
            scene.get("model"),
            scene.get("subject"),
            "a natural Korean adult",
        )
        pose = self._first_text(
            scene.get("pose"),
            scene.get("human_pose"),
            scene.get("body_pose"),
            "a relaxed and believable everyday posture",
        )
        expression = self._first_text(
            scene.get("expression"),
            scene.get("facial_expression"),
            "a subtle natural expression appropriate for the scene",
        )
        interaction = self._first_text(
            scene.get("interaction"),
            scene.get("human_action"),
            scene.get("action"),
            "use the product naturally according to its real function",
        )

        return (
            "[HUMAN DIRECTION]\n"
            f"Subject: {subject}\n"
            f"Pose: {pose}\n"
            f"Expression: {expression}\n"
            f"Interaction: {interaction}\n"
            "- Use natural anatomy and realistic hand contact.\n"
            "- Do not let hands, clothing or hair hide the product's defining structure.\n"
            "- The person supports the product story but does not become the main subject."
        )

    def _build_environment_section(
        self,
        scene: Dict[str, Any],
        product_context: Dict[str, Any],
    ) -> str:
        environment = self._first_text(
            scene.get("environment"),
            scene.get("location"),
            scene.get("setting"),
            product_context.get("environment"),
            "a realistic Korean daily-life environment",
        )
        props = self._first_text(
            scene.get("props"),
            scene.get("background_objects"),
            scene.get("supporting_objects"),
        )
        time_of_day = self._first_text(
            scene.get("time_of_day"),
            scene.get("daypart"),
        )

        lines = [
            "[ENVIRONMENT DIRECTION]",
            f"Location: {environment}",
        ]
        if props:
            lines.append(f"Supporting objects: {props}")
        if time_of_day:
            lines.append(f"Time of day: {time_of_day}")
        lines.extend(
            [
                "- Keep the background realistic, uncluttered and subordinate to the product.",
                "- Use only props that clarify product use or scale.",
                "- Do not place unrelated products that compete for attention.",
            ]
        )
        return "\n".join(lines)

    def _build_camera_section(
        self,
        scene: Dict[str, Any],
    ) -> str:
        shot = self._first_text(
            scene.get("shot_type"),
            scene.get("shot"),
            "medium product-focused commercial shot",
        )
        angle = self._first_text(
            scene.get("camera_angle"),
            scene.get("angle"),
            "natural eye-level or slight three-quarter angle",
        )
        lens = self._first_text(
            scene.get("lens"),
            scene.get("focal_length"),
            "35mm to 50mm natural perspective",
        )
        focus = self._first_text(
            scene.get("focus"),
            scene.get("focus_target"),
            "sharp focus on the complete product",
        )

        return (
            "[CAMERA DIRECTION]\n"
            f"Shot: {shot}\n"
            f"Angle: {angle}\n"
            f"Lens: {lens}\n"
            f"Focus: {focus}\n"
            "- Avoid extreme wide-angle distortion.\n"
            "- Avoid macro framing that removes essential product structure.\n"
            "- Keep important controls, hinge, clip, mount and attachments readable when relevant."
        )

    def _build_lighting_section(
        self,
        scene: Dict[str, Any],
        product_context: Dict[str, Any],
    ) -> str:
        lighting = self._first_text(
            scene.get("lighting"),
            scene.get("light"),
            product_context.get("lighting"),
            "soft natural commercial lighting",
        )
        mood = self._first_text(
            scene.get("lighting_mood"),
            scene.get("mood"),
            "clean, bright and trustworthy",
        )

        return (
            "[LIGHTING DIRECTION]\n"
            f"Lighting: {lighting}\n"
            f"Lighting mood: {mood}\n"
            "- Use realistic shadows and contact shadows.\n"
            "- Preserve the product's true color and surface finish.\n"
            "- Avoid colored lighting that changes product identity.\n"
            "- Keep dark product details separated from the background."
        )

    def _build_composition_section(
        self,
        scene: Dict[str, Any],
    ) -> str:
        composition = self._first_text(
            scene.get("composition"),
            scene.get("framing"),
            scene.get("camera"),
            "vertical 9:16 commercial composition with clear product visibility",
        )
        placement = self._first_text(
            scene.get("product_placement"),
            scene.get("placement"),
            "place the product near the visual center with comfortable negative space",
        )

        return (
            "[COMPOSITION DIRECTION]\n"
            f"Composition: {composition}\n"
            f"Product placement: {placement}\n"
            "- Produce one coherent single-frame photograph, never a collage or split screen.\n"
            "- Keep the complete product visible unless the scene explicitly requires a verified detail close-up.\n"
            "- The product should occupy a believable size in the frame, not appear oversized.\n"
            "- Leave safe space for later subtitles without drawing text in the image."
        )

    def _build_viral_section(
        self,
        purpose: str,
        scene: Dict[str, Any],
        product_context: Dict[str, Any],
    ) -> str:
        hook = self._first_text(
            scene.get("viral_hook"),
            scene.get("hook"),
            product_context.get("viral_hook"),
            product_context.get("best_hook"),
        )
        visual_trigger = self._first_text(
            scene.get("visual_trigger"),
            scene.get("attention_point"),
            scene.get("surprise_point"),
        )
        proof = self._first_text(
            scene.get("proof"),
            scene.get("evidence"),
            scene.get("proof_point"),
            product_context.get("best_evidence"),
        )

        lines = [
            "[VIRAL VISUAL DIRECTION]",
            f"Purpose priority: {purpose or 'feature'}",
        ]
        if hook:
            lines.append(f"Hook to visualize without text: {hook}")
        if visual_trigger:
            lines.append(f"Immediate visual trigger: {visual_trigger}")
        if proof:
            lines.append(f"Visible proof: {proof}")

        lines.extend(
            [
                "- Make the main idea understandable within the first glance.",
                "- Prefer one strong visual contrast or one clear use result.",
                "- Do not exaggerate performance beyond the supplied scene and product evidence.",
                "- Avoid sensational props that weaken product credibility.",
            ]
        )
        return "\n".join(lines)

    def _build_output_rules_section(self) -> str:
        return (
            "[OUTPUT RULES]\n"
            "- Photorealistic Korean commercial product photography.\n"
            "- Premium but believable shopping-short quality.\n"
            "- Vertical 9:16 composition.\n"
            "- One image and one coherent scene only.\n"
            "- No text, captions, subtitles, letters, numbers, logos, badges, price tags, watermarks or UI.\n"
            "- Do not render prompt instructions inside the image.\n"
            "- Do not produce an infographic, poster, diagram, collage or comparison grid."
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
            "comparison grid",
            "duplicate product",
            "multiple products",
            "wrong product",
            "generic replacement product",
            "altered product",
            "redesigned product",
            "deformed product",
            "invented parts",
            "missing parts",
            "extra buttons",
            "invented controls",
            "moved controls",
            "incorrect display",
            "incorrect hinge",
            "incorrect clip",
            "incorrect mount",
            "incorrect attachment",
            "incorrect color",
            "incorrect material",
            "mirrored asymmetric product",
            "stretched product",
            "oversized product",
            "miniature product",
            "unrealistic scale",
            "blurry product",
            "cropped product",
            "hidden product",
            "extreme wide angle",
            "fisheye distortion",
            "floating product",
            "impossible grip",
            "bad anatomy",
            "extra fingers",
            "merged fingers",
            "plastic skin",
            "overprocessed image",
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

    def _resolve_product_identity(
        self,
        product_name: str,
        scene: Dict[str, Any],
        product_context: Dict[str, Any],
    ) -> Dict[str, str]:
        dna = self._first_mapping(
            scene.get("product_identity_dna"),
            scene.get("product_dna"),
            product_context.get("product_identity_dna"),
            product_context.get("product_dna"),
            product_context.get("identity_dna"),
            product_context.get("dna"),
        )
        identity = self._first_mapping(
            scene.get("product_identity"),
            product_context.get("product_identity"),
            product_context.get("identity"),
            dna,
        )

        reference_image_path = self._first_text(
            scene.get("reference_image_path"),
            scene.get("product_reference_image_path"),
            product_context.get("reference_image_path"),
            product_context.get("main_image_path"),
            product_context.get("product_image_path"),
            identity.get("reference_image_path"),
            dna.get("reference_image_path"),
        )
        dna_path = self._first_text(
            scene.get("product_identity_dna_path"),
            scene.get("product_dna_path"),
            product_context.get("product_identity_dna_path"),
            product_context.get("product_dna_path"),
            product_context.get("dna_path"),
        )
        structure_board_path = self._first_text(
            scene.get("product_identity_structure_board_path"),
            scene.get("structure_board_path"),
            scene.get("identity_board_path"),
            product_context.get("product_identity_structure_board_path"),
            product_context.get("structure_board_path"),
            product_context.get("identity_board_path"),
            product_context.get("product_identity_board_path"),
        )

        return {
            "product_name": self._first_text(
                product_name,
                identity.get("product_name"),
                dna.get("product_name"),
                "the provided product",
            ),
            "reference_image_path": reference_image_path,
            "dna_path": dna_path,
            "structure_board_path": structure_board_path,
            "identity_summary": self._first_text(
                identity.get("identity_summary"),
                identity.get("summary"),
                dna.get("identity_summary"),
                dna.get("summary"),
                product_context.get("product_identity_summary"),
            ),
            "shape": self._collect_identity_text(
                identity,
                dna,
                keys=("shape", "silhouette", "form", "body_shape", "structural_shape"),
            ),
            "color": self._collect_identity_text(
                identity,
                dna,
                keys=("color", "colors", "primary_color", "color_finish", "finish"),
            ),
            "material": self._collect_identity_text(
                identity,
                dna,
                keys=("material", "materials", "surface", "surface_finish", "texture"),
            ),
            "controls": self._collect_identity_text(
                identity,
                dna,
                keys=("controls", "buttons", "display", "visible_details", "key_details", "front_details"),
            ),
            "attachments": self._collect_identity_text(
                identity,
                dna,
                keys=("attachments", "attachment", "hinge", "clip", "mount", "connector", "structural_parts"),
            ),
            "proportions": self._collect_identity_text(
                identity,
                dna,
                keys=("proportions", "dimensions", "size", "scale", "aspect_ratio"),
            ),
        }

    def _collect_identity_text(
        self,
        *mappings: Mapping[str, Any],
        keys: tuple[str, ...],
    ) -> str:
        values: List[str] = []
        for mapping in mappings:
            if not isinstance(mapping, Mapping):
                continue
            for key in keys:
                text = self._compact_value(mapping.get(key))
                if text and text not in values:
                    values.append(text)
        return "; ".join(values[:8])

    def _compact_value(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, Mapping):
            parts: List[str] = []
            for key, item in value.items():
                item_text = self._compact_value(item)
                if item_text:
                    parts.append(f"{key}: {item_text}")
            return ", ".join(parts[:8])
        if isinstance(value, (list, tuple, set)):
            parts = [self._compact_value(item) for item in value]
            return ", ".join(part for part in parts if part)
        return str(value).strip()

    def _first_mapping(self, *values: Any) -> Dict[str, Any]:
        for value in values:
            if isinstance(value, Mapping) and value:
                return dict(value)
        return {}

    def evaluate_generated_image(
        self,
        scene_id: str = "",
        generated_image_path: str = "",
        vision_result: Dict[str, Any] | None = None,
        threshold: float | None = None,
    ) -> Dict[str, Any]:
        """
        외부 Vision 분석 결과를 제품 일치도 점수로 변환합니다.

        이 메서드는 Vision API를 직접 호출하지 않습니다. Gemini/Vision 호출부가
        반환한 dict를 받아 표준 Fidelity 결과로 정규화하므로 기존 공급자 구조와
        독립적으로 연결할 수 있습니다.
        """
        direction = {
            "scene_id": str(scene_id or "").strip(),
            "generated_image_path": str(generated_image_path or "").strip(),
        }
        scene = {
            "scene_id": str(scene_id or "").strip(),
            "generated_image_path": str(generated_image_path or "").strip(),
            "fidelity_threshold": (
                float(threshold)
                if threshold is not None
                else self.FIDELITY_THRESHOLD
            ),
            "vision_result": dict(vision_result or {}),
        }
        return self._evaluate_scene_fidelity(
            scene=scene,
            direction=direction,
        )

    def _evaluate_scene_fidelity(
        self,
        scene: Dict[str, Any],
        direction: Dict[str, Any],
    ) -> Dict[str, Any]:
        vision_result = self._first_mapping(
            scene.get("fidelity_validation"),
            scene.get("product_fidelity"),
            scene.get("image_validation"),
            scene.get("vision_validation"),
            scene.get("vision_result"),
            scene.get("generated_image_analysis"),
        )

        generated_image_path = self._first_text(
            direction.get("generated_image_path"),
            scene.get("generated_image_path"),
            scene.get("final_generated_image_path"),
            scene.get("ai_generated_image_path"),
        )

        threshold = self._to_float(
            scene.get("fidelity_threshold"),
            default=self.FIDELITY_THRESHOLD,
        )

        base: Dict[str, Any] = {
            "scene_id": self._first_text(
                direction.get("scene_id"),
                scene.get("scene_id"),
            ),
            "generated_image_path": generated_image_path,
            "checked": False,
            "passed": False,
            "retry_required": False,
            "product_fidelity_score": 0.0,
            "threshold": threshold,
            "checks": {},
            "issues": [],
            "retry_prompt": "",
            "source": "not_checked",
        }

        if not vision_result:
            return base

        normalized_checks: Dict[str, Any] = {}
        total_weight = 0.0
        earned_weight = 0.0

        explicit_score = self._to_optional_float(
            vision_result.get("product_fidelity_score")
        )
        if explicit_score is None:
            explicit_score = self._to_optional_float(
                vision_result.get("fidelity_score")
            )
        if explicit_score is None:
            explicit_score = self._to_optional_float(
                vision_result.get("score")
            )

        for canonical_key, weight in self.FIDELITY_WEIGHTS.items():
            raw_value = self._first_present_value(
                vision_result,
                self.FIDELITY_ALIASES.get(canonical_key, (canonical_key,)),
            )
            normalized = self._normalize_fidelity_value(raw_value)
            normalized_checks[canonical_key] = normalized

            if normalized["available"]:
                total_weight += weight
                earned_weight += weight * normalized["ratio"]

        calculated_score = (
            (earned_weight / total_weight) * 100.0
            if total_weight > 0
            else None
        )
        score = (
            explicit_score
            if explicit_score is not None
            else calculated_score
            if calculated_score is not None
            else 0.0
        )
        score = max(0.0, min(100.0, float(score)))

        issues = self._extract_fidelity_issues(
            vision_result=vision_result,
            checks=normalized_checks,
        )
        passed = score >= threshold and not self._has_critical_identity_failure(
            normalized_checks
        )

        base.update(
            {
                "checked": True,
                "passed": passed,
                "retry_required": not passed,
                "product_fidelity_score": round(score, 2),
                "checks": normalized_checks,
                "issues": issues,
                "retry_prompt": (
                    ""
                    if passed
                    else self._build_fidelity_retry_prompt(
                        issues=issues,
                        checks=normalized_checks,
                    )
                ),
                "source": (
                    "explicit_score"
                    if explicit_score is not None
                    else "weighted_checks"
                ),
            }
        )
        return base

    def _normalize_fidelity_value(self, value: Any) -> Dict[str, Any]:
        if value is None:
            return {
                "available": False,
                "passed": False,
                "ratio": 0.0,
                "raw": None,
            }

        if isinstance(value, bool):
            return {
                "available": True,
                "passed": value,
                "ratio": 1.0 if value else 0.0,
                "raw": value,
            }

        numeric = self._to_optional_float(value)
        if numeric is not None:
            ratio = numeric / 100.0 if numeric > 1.0 else numeric
            ratio = max(0.0, min(1.0, ratio))
            return {
                "available": True,
                "passed": ratio >= 0.9,
                "ratio": ratio,
                "raw": value,
            }

        text = str(value or "").strip().lower()
        positive = {
            "true",
            "yes",
            "pass",
            "passed",
            "match",
            "matched",
            "same",
            "correct",
            "ok",
            "good",
        }
        negative = {
            "false",
            "no",
            "fail",
            "failed",
            "mismatch",
            "different",
            "wrong",
            "incorrect",
            "missing",
        }

        if text in positive:
            return {
                "available": True,
                "passed": True,
                "ratio": 1.0,
                "raw": value,
            }
        if text in negative:
            return {
                "available": True,
                "passed": False,
                "ratio": 0.0,
                "raw": value,
            }

        return {
            "available": False,
            "passed": False,
            "ratio": 0.0,
            "raw": value,
        }

    def _extract_fidelity_issues(
        self,
        vision_result: Dict[str, Any],
        checks: Dict[str, Any],
    ) -> List[str]:
        issues: List[str] = []

        for key in (
            "issues",
            "problems",
            "mismatches",
            "errors",
            "warnings",
        ):
            value = vision_result.get(key)
            if isinstance(value, str) and value.strip():
                issues.append(value.strip())
            elif isinstance(value, (list, tuple, set)):
                for item in value:
                    text = str(item or "").strip()
                    if text and text not in issues:
                        issues.append(text)

        labels = {
            "shape_match": "제품 형태 또는 실루엣 불일치",
            "color_match": "제품 색상 또는 마감 불일치",
            "proportion_match": "제품 비율 또는 크기 불일치",
            "controls_match": "버튼·디스플레이·세부 구조 불일치",
            "attachment_match": "힌지·클립·마운트·부착 구조 불일치",
            "material_match": "재질 또는 표면 질감 불일치",
            "scale_match": "사람·가구 대비 제품 크기 불일치",
            "scene_match": "장면 목표 또는 사용 방식 불일치",
        }

        for key, result in checks.items():
            if result.get("available") and not result.get("passed"):
                label = labels.get(key, key)
                if label not in issues:
                    issues.append(label)

        return issues

    def _has_critical_identity_failure(
        self,
        checks: Dict[str, Any],
    ) -> bool:
        for key in (
            "shape_match",
            "color_match",
            "proportion_match",
            "controls_match",
            "attachment_match",
        ):
            result = checks.get(key) or {}
            if result.get("available") and not result.get("passed"):
                return True
        return False

    def _build_fidelity_retry_prompt(
        self,
        issues: List[str],
        checks: Dict[str, Any],
    ) -> str:
        issue_text = "; ".join(issues) if issues else "product identity mismatch"
        failed_keys = [
            key
            for key, result in checks.items()
            if result.get("available") and not result.get("passed")
        ]
        failed_text = ", ".join(failed_keys) if failed_keys else "identity details"

        return (
            "Regenerate the same scene using the original reference product. "
            f"Correct these problems: {issue_text}. "
            f"Pay special attention to: {failed_text}. "
            "Preserve the exact product shape, color, proportions, controls, display, "
            "hinge, clip, mount, material and realistic scale. "
            "Do not redesign or substitute the product. Keep the scene simpler if needed."
        )

    def _first_present_value(
        self,
        mapping: Mapping[str, Any],
        keys: tuple[str, ...],
    ) -> Any:
        for key in keys:
            if key in mapping:
                return mapping.get(key)
        return None

    def _to_optional_float(self, value: Any) -> float | None:
        if value is None or isinstance(value, bool):
            return None
        try:
            text = str(value).strip().replace("%", "")
            if not text:
                return None
            return float(text)
        except (TypeError, ValueError):
            return None

    def _to_float(
        self,
        value: Any,
        default: float,
    ) -> float:
        resolved = self._to_optional_float(value)
        return float(default if resolved is None else resolved)

    def execute_closed_loop(
        self,
        product_name: str = "",
        scenes: List[Dict[str, Any]] | None = None,
        product_context: Dict[str, Any] | None = None,
        scene_image_plan: Dict[str, Any] | None = None,
        output_dir: str = "",
        project_id: Any = "",
        image_generator: Callable[[Dict[str, Any]], Any] | None = None,
        image_validator: Callable[[Dict[str, Any]], Any] | None = None,
        max_attempts: int | None = None,
        threshold: float | None = None,
        save_result: bool = True,
    ) -> Dict[str, Any]:
        """
        장면 방향 설계와 생성·검증 폐쇄루프를 한 번에 실행합니다.

        WorkflowEngine은 이 메서드 하나만 호출하면 되며, 실제 공급자 호출은
        image_generator와 image_validator 콜백으로 주입합니다. 생성 대상이 없는
        경우에는 기존 상품 이미지 장면을 그대로 반환합니다.
        """
        director_result = self.generate(
            product_name=product_name,
            scenes=scenes,
            product_context=product_context,
            scene_image_plan=scene_image_plan,
            output_dir=output_dir,
            project_id=project_id,
            save_result=False,
        )

        director_result["workflow_connection_version"] = "workflow-ai-image-closed-loop-141-6"

        if not director_result.get("ready"):
            return self._save_if_requested(
                result=director_result,
                output_dir=output_dir,
                save_result=save_result,
            )

        if not callable(image_generator) or not callable(image_validator):
            director_result["ok"] = False
            director_result["status"] = "closed_loop_provider_missing"
            director_result["closed_loop_executed"] = False
            director_result["errors"] = list(director_result.get("errors") or [])
            if not callable(image_generator):
                director_result["errors"].append("이미지 생성기 콜백이 연결되지 않았습니다")
            if not callable(image_validator):
                director_result["errors"].append("이미지 검증기 콜백이 연결되지 않았습니다")
            return self._save_if_requested(
                result=director_result,
                output_dir=output_dir,
                save_result=save_result,
            )

        return self.run_closed_loop(
            director_result=director_result,
            image_generator=image_generator,
            image_validator=image_validator,
            max_attempts=max_attempts,
            threshold=threshold,
            save_result=save_result,
            output_dir=output_dir,
        )

    def run_closed_loop(
        self,
        director_result: Dict[str, Any],
        image_generator: Callable[[Dict[str, Any]], Any],
        image_validator: Callable[[Dict[str, Any]], Any],
        max_attempts: int | None = None,
        threshold: float | None = None,
        save_result: bool = False,
        output_dir: str = "",
    ) -> Dict[str, Any]:
        """
        이미지 생성 → Vision 검증 → 재생성 → 최고 점수 선택을 실행합니다.

        image_generator 계약:
            입력 dict:
                scene_id, attempt, prompt, negative_prompt,
                reference_image_path, output_image_path
            반환:
                문자열 이미지 경로 또는
                {"ok": bool, "image_path": str, ...}

        image_validator 계약:
            입력 dict:
                scene_id, attempt, generated_image_path,
                reference_image_path, prompt, negative_prompt
            반환:
                evaluate_generated_image()가 해석할 수 있는 Vision dict

        실제 Gemini SDK 호출은 공급자 모듈의 책임으로 유지합니다.
        따라서 이 메서드는 특정 SDK나 API 버전에 종속되지 않습니다.
        """
        if not isinstance(director_result, Mapping):
            return {
                "ok": False,
                "ready": False,
                "version": self.VERSION,
                "status": "invalid_director_result",
                "errors": ["director_result가 dict 형식이 아닙니다"],
            }

        result = dict(director_result)
        result["version"] = self.VERSION
        result["closed_loop_supported"] = True
        result["closed_loop_executed"] = True
        result["generation_runs"] = []
        result["cost_guard"] = {
            "enabled": True,
            "max_attempts_per_scene": 2,
            "api_calls": 0,
            "reused_scenes": 0,
            "generated_scenes": 0,
            "skipped_scenes": 0,
            "fatal_stop": False,
            "fatal_error_code": "",
            "fatal_scene_id": "",
        }
        result["errors"] = list(result.get("errors") or [])
        result["warnings"] = list(result.get("warnings") or [])

        resolved_attempts = min(2, max(1, int(max_attempts if max_attempts is not None else self.MAX_GENERATION_ATTEMPTS)))
        resolved_threshold = float(
            threshold
            if threshold is not None
            else result.get("fidelity_threshold")
            or self.FIDELITY_THRESHOLD
        )

        prompts = result.get("image_prompts")
        if not isinstance(prompts, list) or not prompts:
            result["status"] = "no_generation_targets"
            result["ready"] = False
            result["closed_loop_scene_count"] = 0
            result["closed_loop_passed_scene_count"] = 0
            result["closed_loop_failed_scene_count"] = 0
            return self._save_if_requested(
                result=result,
                output_dir=output_dir,
                save_result=save_result,
            )

        scene_run_map: Dict[str, Dict[str, Any]] = {}
        passed_count = 0
        failed_count = 0

        for prompt_item in prompts:
            if not isinstance(prompt_item, Mapping):
                continue

            scene_id = self._first_text(
                prompt_item.get("scene_id"),
                "unknown_scene",
            )
            base_prompt = self._first_text(prompt_item.get("image_prompt"))
            negative_prompt = self._first_text(
                prompt_item.get("negative_prompt")
            )
            reference_image_paths = [
                str(path).strip()
                for path in (prompt_item.get("reference_image_paths") or [])
                if str(path or "").strip()
            ]
            reference_image_path = self._first_text(
                prompt_item.get("reference_image_path"),
                reference_image_paths[0] if reference_image_paths else "",
            )
            if reference_image_path and reference_image_path not in reference_image_paths:
                reference_image_paths.insert(0, reference_image_path)
            requested_output_path = self._first_text(
                prompt_item.get("output_image_path"),
                f"{scene_id}_ai.png",
            )
            requested_path_obj = Path(requested_output_path).expanduser()
            if not requested_path_obj.is_absolute():
                requested_output_path = str(
                    Path(str(output_dir or ".")).expanduser()
                    / requested_path_obj.name
                )

            scene_run: Dict[str, Any] = {
                "scene_id": scene_id,
                "threshold": resolved_threshold,
                "max_attempts": resolved_attempts,
                "attempts": [],
                "selected_attempt": 0,
                "selected_image_path": "",
                "review_image_path": "",
                "best_failed_image_path": "",
                "best_passed_image_path": "",
                "attempt_paths": [],
                "best_score": 0.0,
                "passed": False,
                "status": "not_started",
                "errors": [],
            }

            current_prompt = base_prompt
            best_attempt: Dict[str, Any] | None = None

            cached_path, cached_state = self._find_cached_scene_image(
                output_dir=output_dir,
                scene_id=scene_id,
            )
            if cached_path:
                scene_run["selected_attempt"] = 0
                scene_run["selected_image_path"] = cached_path
                scene_run["review_image_path"] = cached_path
                scene_run["passed"] = cached_state == "best_passed"
                scene_run["manual_approval_required"] = not scene_run["passed"]
                scene_run["status"] = "reused_cached_scene"
                scene_run["best_score"] = 100.0 if scene_run["passed"] else 0.0
                if scene_run["passed"]:
                    scene_run["best_passed_image_path"] = cached_path
                    passed_count += 1
                else:
                    scene_run["best_failed_image_path"] = cached_path
                    failed_count += 1
                result["cost_guard"]["reused_scenes"] += 1
                scene_run_map[scene_id] = scene_run
                result["generation_runs"].append(scene_run)
                print(
                    "[Sprint157 Resume] Reused:",
                    scene_id,
                    cached_state,
                    cached_path,
                    flush=True,
                )
                continue

            for attempt in range(1, resolved_attempts + 1):
                attempt_output_path = self._build_attempt_output_path(
                    requested_output_path=requested_output_path,
                    scene_id=scene_id,
                    attempt=attempt,
                )
                generation_payload = {
                    "scene_id": scene_id,
                    "attempt": attempt,
                    "prompt": current_prompt,
                    "negative_prompt": negative_prompt,
                    "reference_image_path": reference_image_path,
                    "reference_image_paths": reference_image_paths,
                    "require_reference_image": True,
                    "output_image_path": attempt_output_path,
                    "fidelity_threshold": resolved_threshold,
                }

                attempt_result: Dict[str, Any] = {
                    "attempt": attempt,
                    "prompt": current_prompt,
                    "negative_prompt": negative_prompt,
                    "requested_output_image_path": attempt_output_path,
                    "generated_image_path": "",
                    "generation_ok": False,
                    "validation_ok": False,
                    "fidelity": {},
                    "score": 0.0,
                    "passed": False,
                    "error": "",
                }

                try:
                    result["cost_guard"]["api_calls"] += 1
                    print(
                        "[Sprint157 Cost] API Call:",
                        result["cost_guard"]["api_calls"],
                        "Scene:",
                        scene_id,
                        "Attempt:",
                        attempt,
                        flush=True,
                    )
                    raw_generation = image_generator(generation_payload)
                    generation = self._normalize_generation_result(
                        raw_generation=raw_generation,
                        fallback_output_path=attempt_output_path,
                    )
                    attempt_result["generation_result"] = generation
                    attempt_result["generation_ok"] = bool(generation["ok"])
                    attempt_result["original_generated_image_path"] = generation["image_path"]
                    attempt_result["preserved_review_image_path"] = self._first_text(
                        generation.get("preserved_review_image_path")
                    )
                    attempt_result["generated_image_path"] = self._first_text(
                        generation.get("preserved_review_image_path"),
                        generation["image_path"],
                    )

                    if attempt_result["generated_image_path"]:
                        scene_run["attempt_paths"].append(
                            attempt_result["generated_image_path"]
                        )

                    if not generation["ok"] or not attempt_result["generated_image_path"]:
                        attempt_result["error"] = self._first_text(
                            generation.get("error"),
                            "이미지 생성 결과 경로가 없습니다",
                        )
                        attempt_result["fatal_error"] = bool(
                            generation.get("fatal_error")
                        )
                        attempt_result["fatal_error_code"] = self._first_text(
                            generation.get("fatal_error_code")
                        )
                        scene_run["attempts"].append(attempt_result)

                        if attempt_result["fatal_error"]:
                            result["cost_guard"]["fatal_stop"] = True
                            result["cost_guard"]["fatal_error_code"] = (
                                attempt_result["fatal_error_code"]
                            )
                            result["cost_guard"]["fatal_scene_id"] = scene_id
                            scene_run["status"] = "fatal_provider_error"
                            scene_run["errors"].append(attempt_result["error"])
                            print(
                                "[Sprint157 Cost Guard] STOP ALL SCENES:",
                                attempt_result["fatal_error_code"],
                                "Scene:",
                                scene_id,
                                flush=True,
                            )
                            break
                        continue

                    validation_payload = {
                        "scene_id": scene_id,
                        "attempt": attempt,
                        "generated_image_path": attempt_result["generated_image_path"],
                        "reference_image_path": reference_image_path,
                        "reference_image_paths": reference_image_paths,
                        "prompt": current_prompt,
                        "negative_prompt": negative_prompt,
                        "fidelity_threshold": resolved_threshold,
                    }
                    raw_validation = image_validator(validation_payload)
                    vision_result = (
                        dict(raw_validation)
                        if isinstance(raw_validation, Mapping)
                        else {}
                    )
                    fidelity = self.evaluate_generated_image(
                        scene_id=scene_id,
                        generated_image_path=attempt_result["generated_image_path"],
                        vision_result=vision_result,
                        threshold=resolved_threshold,
                    )

                    attempt_result["validation_result"] = vision_result
                    attempt_result["validation_ok"] = bool(
                        fidelity.get("checked")
                    )
                    attempt_result["fidelity"] = fidelity
                    attempt_result["score"] = float(
                        fidelity.get("product_fidelity_score") or 0.0
                    )
                    attempt_result["passed"] = bool(fidelity.get("passed"))

                    if (
                        best_attempt is None
                        or attempt_result["score"] > best_attempt["score"]
                    ):
                        best_attempt = dict(attempt_result)

                    scene_run["attempts"].append(attempt_result)

                    if attempt_result["passed"]:
                        break

                    retry_prompt = self._first_text(
                        fidelity.get("retry_prompt")
                    )
                    if retry_prompt:
                        current_prompt = self._merge_retry_prompt(
                            base_prompt=base_prompt,
                            retry_prompt=retry_prompt,
                            attempt=attempt + 1,
                        )

                except Exception as exc:
                    attempt_result["error"] = (
                        f"{type(exc).__name__}: {exc}"
                    )
                    scene_run["attempts"].append(attempt_result)
                    scene_run["errors"].append(attempt_result["error"])

            if best_attempt:
                scene_run["selected_attempt"] = int(
                    best_attempt.get("attempt") or 0
                )
                scene_run["best_score"] = float(
                    best_attempt.get("score") or 0.0
                )
                scene_run["passed"] = bool(best_attempt.get("passed"))

                best_source_path = self._first_text(
                    best_attempt.get("generated_image_path"),
                    best_attempt.get("preserved_review_image_path"),
                    best_attempt.get("original_generated_image_path"),
                )
                best_review_path = self._preserve_best_review_image(
                    source_path=best_source_path,
                    output_dir=output_dir,
                    scene_id=scene_id,
                    passed=scene_run["passed"],
                )

                scene_run["selected_image_path"] = self._first_text(
                    best_review_path,
                    best_source_path,
                )
                scene_run["review_image_path"] = scene_run["selected_image_path"]
                scene_run["manual_approval_required"] = not scene_run["passed"]

                if scene_run["passed"]:
                    scene_run["best_passed_image_path"] = (
                        scene_run["selected_image_path"]
                    )
                    scene_run["status"] = "passed"
                else:
                    scene_run["best_failed_image_path"] = (
                        scene_run["selected_image_path"]
                    )
                    scene_run["status"] = (
                        "best_attempt_preserved_for_manual_review"
                    )
            else:
                scene_run["status"] = "generation_failed"

            if scene_run["passed"]:
                passed_count += 1
            else:
                failed_count += 1

            scene_run_map[scene_id] = scene_run
            result["generation_runs"].append(scene_run)

            if result["cost_guard"]["fatal_stop"]:
                remaining = max(
                    0,
                    len(prompts) - len(result["generation_runs"]),
                )
                result["cost_guard"]["skipped_scenes"] += remaining
                result["warnings"].append(
                    "치명적 공급자 오류로 남은 장면 생성을 즉시 중단했습니다."
                )
                break

        self._apply_closed_loop_selection(
            result=result,
            scene_run_map=scene_run_map,
        )

        result["closed_loop_scene_count"] = len(scene_run_map)
        result["closed_loop_passed_scene_count"] = passed_count
        result["closed_loop_failed_scene_count"] = failed_count
        result["closed_loop_all_passed"] = (
            bool(scene_run_map) and failed_count == 0
        )
        result["ok"] = bool(scene_run_map)
        result["ready"] = bool(scene_run_map)
        result["status"] = (
            "closed_loop_completed"
            if result["closed_loop_all_passed"]
            else "closed_loop_partial"
            if passed_count > 0
            else "closed_loop_failed"
        )

        return self._save_if_requested(
            result=result,
            output_dir=output_dir,
            save_result=save_result,
        )

    def _find_cached_scene_image(
        self,
        output_dir: str,
        scene_id: str,
    ) -> tuple[str, str]:
        review_dir = Path(str(output_dir or ".")) / "generated_review"
        if not review_dir.is_dir():
            return "", ""

        safe_scene_id = "".join(
            char if char.isalnum() or char in {"_", "-"} else "_"
            for char in str(scene_id or "scene")
        )
        for state in ("best_passed", "best_failed"):
            for suffix in (".png", ".jpg", ".jpeg", ".webp"):
                candidate = review_dir / f"{safe_scene_id}_{state}{suffix}"
                if candidate.is_file() and candidate.stat().st_size > 0:
                    return str(candidate), state
        return "", ""

    def _preserve_best_review_image(
        self,
        source_path: str,
        output_dir: str,
        scene_id: str,
        passed: bool,
    ) -> str:
        """
        장면별 최고 이미지를 best_passed 또는 best_failed 이름으로 보존합니다.
        """
        source = Path(str(source_path or "")).expanduser()
        if not source.is_file():
            return ""

        try:
            project_dir = Path(str(output_dir or source.parent)).expanduser()
            review_dir = project_dir / "generated_review"
            review_dir.mkdir(parents=True, exist_ok=True)

            suffix = source.suffix.lower() or ".png"
            safe_scene_id = "".join(
                char if char.isalnum() or char in {"_", "-"} else "_"
                for char in str(scene_id or "scene")
            )
            state = "best_passed" if passed else "best_failed"
            destination = review_dir / f"{safe_scene_id}_{state}{suffix}"

            shutil.copy2(source, destination)
            if destination.is_file() and destination.stat().st_size > 0:
                print(
                    "[Sprint156 Preserve Best] Scene:",
                    scene_id,
                    "Passed:",
                    passed,
                    "Path:",
                    destination,
                    flush=True,
                )
                return str(destination)
        except Exception as exc:
            print(
                "[Sprint156 Preserve Best] ERROR:",
                scene_id,
                f"{type(exc).__name__}: {exc}",
                flush=True,
            )
        return ""

    def _normalize_generation_result(
        self,
        raw_generation: Any,
        fallback_output_path: str,
    ) -> Dict[str, Any]:
        if isinstance(raw_generation, (str, Path)):
            image_path = str(raw_generation).strip()
            return {
                "ok": bool(image_path),
                "image_path": image_path,
                "error": "",
                "raw": image_path,
            }

        if isinstance(raw_generation, Mapping):
            raw = dict(raw_generation)
            image_path = self._first_text(
                raw.get("image_path"),
                raw.get("generated_image_path"),
                raw.get("output_image_path"),
                raw.get("path"),
                fallback_output_path
                if raw.get("ok") is True
                else "",
            )
            ok = bool(
                raw.get("ok")
                if "ok" in raw
                else raw.get("success")
                if "success" in raw
                else image_path
            )
            return {
                "ok": ok and bool(image_path),
                "image_path": image_path,
                "error": self._first_text(
                    raw.get("error"),
                    raw.get("message") if not ok else "",
                ),
                "fatal_error": bool(raw.get("fatal_error")),
                "fatal_error_code": self._first_text(
                    raw.get("fatal_error_code")
                ),
                "cost_guard_triggered": bool(
                    raw.get("cost_guard_triggered")
                ),
                "preserved_review_image_path": self._first_text(
                    raw.get("preserved_review_image_path")
                ),
                "raw": raw,
            }

        return {
            "ok": False,
            "image_path": "",
            "error": "지원하지 않는 이미지 생성 반환 형식입니다",
            "raw": raw_generation,
        }

    def _build_attempt_output_path(
        self,
        requested_output_path: str,
        scene_id: str,
        attempt: int,
    ) -> str:
        path = Path(
            requested_output_path
            or f"{scene_id}_ai.png"
        )
        suffix = path.suffix or ".png"
        stem = path.stem or f"{scene_id}_ai"
        return str(path.with_name(f"{stem}_attempt_{attempt}{suffix}"))

    def _merge_retry_prompt(
        self,
        base_prompt: str,
        retry_prompt: str,
        attempt: int,
    ) -> str:
        return (
            f"{base_prompt}\n\n"
            f"[FIDELITY RETRY {attempt}]\n"
            f"{retry_prompt}\n"
            "Keep every valid part of the previous scene direction unchanged."
        )

    def _apply_closed_loop_selection(
        self,
        result: Dict[str, Any],
        scene_run_map: Dict[str, Dict[str, Any]],
    ) -> None:
        scenes = result.get("scenes")
        if isinstance(scenes, list):
            for scene in scenes:
                if not isinstance(scene, dict):
                    continue
                scene_id = self._first_text(scene.get("scene_id"))
                run = scene_run_map.get(scene_id)
                if not run:
                    continue
                scene["closed_loop_generation"] = run
                scene["generated_image_path"] = self._first_text(
                    run.get("selected_image_path")
                )
                scene["resolved_image_path"] = self._first_text(
                    run.get("selected_image_path"),
                    scene.get("resolved_image_path"),
                )
                scene["generation_required"] = not bool(
                    run.get("selected_image_path")
                )
                scene["fidelity_validation"] = self._first_mapping(
                    next(
                        (
                            attempt.get("fidelity")
                            for attempt in run.get("attempts", [])
                            if int(attempt.get("attempt") or 0)
                            == int(run.get("selected_attempt") or 0)
                        ),
                        {},
                    )
                )
                scene["motion_input_allowed"] = bool(
                    run.get("selected_image_path")
                )

        prompts = result.get("image_prompts")
        if isinstance(prompts, list):
            for prompt_item in prompts:
                if not isinstance(prompt_item, dict):
                    continue
                scene_id = self._first_text(prompt_item.get("scene_id"))
                run = scene_run_map.get(scene_id)
                if not run:
                    continue
                prompt_item["selected_image_path"] = self._first_text(
                    run.get("selected_image_path")
                )
                prompt_item["selected_attempt"] = int(
                    run.get("selected_attempt") or 0
                )
                prompt_item["best_fidelity_score"] = float(
                    run.get("best_score") or 0.0
                )
                prompt_item["fidelity_passed"] = bool(run.get("passed"))

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