from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence


class ScenePlanner:
    """
    Sprint93-4 Scene Planner

    역할:
    - Sprint93-3 image_tags.json 또는 ImageTagger 결과를 입력받음
    - 이미지 태그 보유 현황을 기준으로 쇼츠 장면 구조를 자동 설계
    - 각 장면에 필요한 태그, 대체 태그, 목적, 길이, 전환 방식을 정의
    - Sprint93-5 Scene Image Selector가 사용할 scene_plan.json 생성

    기본 구조:
    Hook → Problem → Feature → Detail → Proof → CTA

    안전 원칙:
    - 실제 존재하는 이미지 태그를 우선 반영
    - 없는 태그를 필수 조건으로 강제하지 않음
    - 원본 이미지와 태그 파일은 수정하지 않음
    """

    VERSION = "scene-planner-93-4"

    DEFAULT_DURATION_SECONDS = 24.0
    MIN_SCENES = 5
    MAX_SCENES = 8

    SCENE_LIBRARY: Dict[str, Dict[str, Any]] = {
        "hook": {
            "title": "Hook",
            "purpose": "첫 1~2초 안에 제품과 핵심 관심 포인트를 보여준다",
            "required_tags": ["hero"],
            "fallback_tags": ["thumbnail", "product", "detail"],
            "scene_roles": ["opening", "hook"],
            "duration_weight": 0.10,
            "motion": "slow_push_in",
            "transition": "cut",
            "priority": 100,
        },
        "problem": {
            "title": "Problem",
            "purpose": "사용자가 겪는 불편이나 구매 전 고민을 보여준다",
            "required_tags": ["usage", "lifestyle"],
            "fallback_tags": ["comparison", "size", "detail", "product"],
            "scene_roles": ["problem", "demonstration"],
            "duration_weight": 0.17,
            "motion": "subtle_pan",
            "transition": "cut",
            "priority": 80,
        },
        "feature": {
            "title": "Feature",
            "purpose": "제품의 핵심 기능이나 장점을 보여준다",
            "required_tags": ["feature"],
            "fallback_tags": [
                "storage",
                "wheel",
                "handle",
                "material",
                "detail",
            ],
            "scene_roles": ["feature"],
            "duration_weight": 0.20,
            "motion": "focus_reveal",
            "transition": "match_cut",
            "priority": 95,
        },
        "detail": {
            "title": "Detail",
            "purpose": "제품의 구조, 소재, 부위 또는 마감 품질을 확대해 보여준다",
            "required_tags": ["detail"],
            "fallback_tags": [
                "wheel",
                "handle",
                "storage",
                "material",
                "components",
                "product",
            ],
            "scene_roles": ["feature", "proof"],
            "duration_weight": 0.18,
            "motion": "macro_zoom",
            "transition": "cut",
            "priority": 85,
        },
        "proof": {
            "title": "Proof",
            "purpose": "사용 장면, 비교, 크기 또는 구성으로 구매 근거를 보여준다",
            "required_tags": ["usage", "comparison"],
            "fallback_tags": [
                "before_after",
                "size",
                "components",
                "lifestyle",
                "feature",
                "detail",
            ],
            "scene_roles": ["proof", "comparison", "decision"],
            "duration_weight": 0.20,
            "motion": "demonstration_move",
            "transition": "match_cut",
            "priority": 90,
        },
        "cta": {
            "title": "CTA",
            "purpose": "제품을 다시 보여주며 영상의 결론과 구매 행동을 유도한다",
            "required_tags": ["cta"],
            "fallback_tags": ["hero", "thumbnail", "product", "feature"],
            "scene_roles": ["closing"],
            "duration_weight": 0.15,
            "motion": "slow_pull_out",
            "transition": "fade",
            "priority": 100,
        },
        "comparison": {
            "title": "Comparison",
            "purpose": "크기, 기능 또는 사용 전후 차이를 비교한다",
            "required_tags": ["comparison"],
            "fallback_tags": ["before_after", "size", "feature", "detail"],
            "scene_roles": ["comparison", "decision"],
            "duration_weight": 0.17,
            "motion": "split_reveal",
            "transition": "cut",
            "priority": 88,
        },
        "installation": {
            "title": "Installation",
            "purpose": "설치나 조립 과정이 간단하다는 점을 보여준다",
            "required_tags": ["installation"],
            "fallback_tags": ["components", "usage", "feature", "detail"],
            "scene_roles": ["demonstration", "proof"],
            "duration_weight": 0.17,
            "motion": "step_motion",
            "transition": "cut",
            "priority": 82,
        },
    }

    def plan(
        self,
        tag_result: Any = None,
        image_tags_path: Any = "",
        output_dir: Any = "",
        product_name: str = "",
        project_id: Any = "",
        target_duration_seconds: Any = DEFAULT_DURATION_SECONDS,
        target_scene_count: Any = 6,
        save_result: bool = True,
    ) -> Dict[str, Any]:
        started_at = time.time()

        result: Dict[str, Any] = {
            "ok": False,
            "ready": False,
            "version": self.VERSION,
            "status": "not_run",
            "project_id": str(project_id or ""),
            "product_name": str(product_name or "").strip(),
            "image_tags_path": str(image_tags_path or "").strip(),
            "output_dir": "",
            "scene_plan_path": "",
            "target_duration_seconds": 0.0,
            "target_scene_count": 0,
            "available_tags": [],
            "available_scene_roles": [],
            "scenes": [],
            "summary": {},
            "warnings": [],
            "errors": [],
            "elapsed_seconds": 0.0,
        }

        tag_data = self._resolve_tag_result(
            tag_result=tag_result,
            image_tags_path=image_tags_path,
        )

        images = (
            tag_data.get("images", [])
            if isinstance(tag_data, dict)
            else []
        )
        images = images if isinstance(images, list) else []

        resolved_output_dir = self._resolve_output_dir(
            output_dir=output_dir,
            image_tags_path=image_tags_path,
            tag_data=tag_data,
            project_id=project_id,
        )
        resolved_output_dir.mkdir(parents=True, exist_ok=True)
        result["output_dir"] = str(resolved_output_dir)

        duration = self._normalize_duration(target_duration_seconds)
        scene_count = self._normalize_scene_count(target_scene_count)

        result["target_duration_seconds"] = duration
        result["target_scene_count"] = scene_count

        if not images:
            result["status"] = "no_tagged_images"
            result["warnings"].append("Scene Planner에 사용할 태깅 이미지가 없습니다")
            result["elapsed_seconds"] = round(time.time() - started_at, 3)
            if save_result:
                self._save_result(result, resolved_output_dir)
            return result

        available_tags = self._collect_available_tags(images)
        available_roles = self._collect_available_roles(images)

        result["available_tags"] = available_tags
        result["available_scene_roles"] = available_roles

        scene_keys = self._choose_scene_structure(
            available_tags=available_tags,
            target_scene_count=scene_count,
        )

        scenes = self._build_scenes(
            scene_keys=scene_keys,
            available_tags=available_tags,
            available_roles=available_roles,
            total_duration=duration,
        )

        result["scenes"] = scenes
        result["summary"] = self._build_summary(
            scenes=scenes,
            images=images,
            available_tags=available_tags,
        )
        result["ok"] = bool(scenes)
        result["ready"] = bool(scenes)
        result["status"] = "planned" if scenes else "failed"
        result["elapsed_seconds"] = round(time.time() - started_at, 3)

        if save_result:
            self._save_result(result, resolved_output_dir)

        return result

    def _resolve_tag_result(
        self,
        tag_result: Any,
        image_tags_path: Any,
    ) -> Dict[str, Any]:
        if isinstance(tag_result, dict):
            return dict(tag_result)

        path_value = str(image_tags_path or "").strip()

        if not path_value and isinstance(tag_result, (str, Path)):
            path_value = str(tag_result)

        if not path_value:
            return {}

        path = Path(path_value).expanduser()

        if not path.is_file():
            return {}

        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            return loaded if isinstance(loaded, dict) else {}
        except Exception:
            return {}

    def _resolve_output_dir(
        self,
        output_dir: Any,
        image_tags_path: Any,
        tag_data: Dict[str, Any],
        project_id: Any,
    ) -> Path:
        if str(output_dir or "").strip():
            return Path(str(output_dir)).expanduser()

        data_output = str(tag_data.get("output_dir") or "").strip()
        if data_output:
            return Path(data_output).expanduser()

        tags_path = str(image_tags_path or "").strip()
        if tags_path:
            return Path(tags_path).expanduser().parent

        project_key = str(project_id or "unknown").strip() or "unknown"
        return Path("assets") / "product_images" / f"project_{project_key}"

    def _normalize_duration(self, value: Any) -> float:
        try:
            duration = float(value)
        except Exception:
            duration = self.DEFAULT_DURATION_SECONDS

        return round(min(60.0, max(12.0, duration)), 2)

    def _normalize_scene_count(self, value: Any) -> int:
        try:
            count = int(value)
        except Exception:
            count = 6

        return min(self.MAX_SCENES, max(self.MIN_SCENES, count))

    def _collect_available_tags(
        self,
        images: Sequence[Dict[str, Any]],
    ) -> List[str]:
        collected: List[str] = []

        for image in images:
            if not isinstance(image, dict) or not image.get("ok"):
                continue

            values = list(image.get("semantic_tags") or [])

            primary_tag = str(image.get("primary_tag") or "").strip()
            if primary_tag:
                values.insert(0, primary_tag)

            for value in values:
                tag = str(value or "").strip()
                if tag and tag not in collected:
                    collected.append(tag)

        return collected

    def _collect_available_roles(
        self,
        images: Sequence[Dict[str, Any]],
    ) -> List[str]:
        collected: List[str] = []

        for image in images:
            if not isinstance(image, dict) or not image.get("ok"):
                continue

            for value in image.get("scene_roles") or []:
                role = str(value or "").strip()
                if role and role not in collected:
                    collected.append(role)

        return collected

    def _choose_scene_structure(
        self,
        available_tags: Sequence[str],
        target_scene_count: int,
    ) -> List[str]:
        tag_set = set(available_tags)

        structure: List[str] = ["hook", "problem", "feature", "detail", "proof", "cta"]

        if "installation" in tag_set:
            structure.insert(3, "installation")

        if tag_set.intersection({"comparison", "before_after", "size"}):
            insert_at = max(3, len(structure) - 2)
            structure.insert(insert_at, "comparison")

        structure = self._dedupe_preserve_order(structure)

        if len(structure) > target_scene_count:
            protected = {"hook", "feature", "proof", "cta"}

            while len(structure) > target_scene_count:
                removable = [
                    key
                    for key in structure
                    if key not in protected
                ]

                if not removable:
                    structure = structure[:target_scene_count]
                    break

                remove_key = min(
                    removable,
                    key=lambda key: self.SCENE_LIBRARY[key]["priority"],
                )
                structure.remove(remove_key)

        if len(structure) < target_scene_count:
            expansion_order = [
                "detail",
                "feature",
                "comparison",
                "installation",
                "problem",
            ]

            for candidate in expansion_order:
                if len(structure) >= target_scene_count:
                    break

                if candidate in structure:
                    duplicate_key = f"{candidate}_extra"
                    structure.insert(-1, duplicate_key)
                else:
                    structure.insert(-1, candidate)

        return structure[:target_scene_count]

    def _build_scenes(
        self,
        scene_keys: Sequence[str],
        available_tags: Sequence[str],
        available_roles: Sequence[str],
        total_duration: float,
    ) -> List[Dict[str, Any]]:
        definitions: List[Dict[str, Any]] = []

        for index, raw_key in enumerate(scene_keys, start=1):
            library_key = raw_key.replace("_extra", "")
            base = dict(self.SCENE_LIBRARY[library_key])

            required_tags = self._filter_or_fallback_tags(
                preferred=base.get("required_tags", []),
                fallback=base.get("fallback_tags", []),
                available_tags=available_tags,
            )

            fallback_tags = [
                tag
                for tag in base.get("fallback_tags", [])
                if tag in available_tags and tag not in required_tags
            ]

            matching_roles = [
                role
                for role in base.get("scene_roles", [])
                if role in available_roles
            ]

            definitions.append(
                {
                    "scene_id": f"scene_{index:02d}",
                    "scene_index": index,
                    "scene_type": library_key,
                    "title": (
                        f"{base['title']} {index}"
                        if raw_key.endswith("_extra")
                        else base["title"]
                    ),
                    "purpose": base["purpose"],
                    "required_tags": required_tags,
                    "fallback_tags": fallback_tags,
                    "preferred_scene_roles": matching_roles,
                    "motion": base["motion"],
                    "transition": base["transition"],
                    "duration_weight": float(base["duration_weight"]),
                    "selection_status": "waiting_for_sprint93_5",
                    "selected_image_path": "",
                    "selected_image_index": None,
                }
            )

        durations = self._allocate_durations(
            weights=[
                float(scene.get("duration_weight") or 0.0)
                for scene in definitions
            ],
            total_duration=total_duration,
        )

        for scene, duration in zip(definitions, durations):
            scene["duration_seconds"] = duration
            scene.pop("duration_weight", None)

        return definitions

    def _filter_or_fallback_tags(
        self,
        preferred: Sequence[str],
        fallback: Sequence[str],
        available_tags: Sequence[str],
    ) -> List[str]:
        available = set(available_tags)

        selected = [
            tag
            for tag in preferred
            if tag in available
        ]

        if selected:
            return selected

        selected = [
            tag
            for tag in fallback
            if tag in available
        ]

        if selected:
            return selected[:3]

        if available_tags:
            return list(available_tags[:2])

        return ["product"]

    def _allocate_durations(
        self,
        weights: Sequence[float],
        total_duration: float,
    ) -> List[float]:
        if not weights:
            return []

        normalized_weights = [
            max(0.01, float(weight or 0.0))
            for weight in weights
        ]
        total_weight = sum(normalized_weights)

        raw = [
            max(1.5, total_duration * weight / total_weight)
            for weight in normalized_weights
        ]

        current_total = sum(raw)

        if current_total <= 0:
            even = total_duration / len(raw)
            raw = [even for _ in raw]
        else:
            scale = total_duration / current_total
            raw = [value * scale for value in raw]

        rounded = [round(value, 2) for value in raw]
        difference = round(total_duration - sum(rounded), 2)

        if rounded:
            rounded[-1] = round(max(1.5, rounded[-1] + difference), 2)

        return rounded

    def _build_summary(
        self,
        scenes: Sequence[Dict[str, Any]],
        images: Sequence[Dict[str, Any]],
        available_tags: Sequence[str],
    ) -> Dict[str, Any]:
        scene_types = [
            str(scene.get("scene_type") or "")
            for scene in scenes
        ]

        required_tag_counts: Dict[str, int] = {}

        for scene in scenes:
            for tag in scene.get("required_tags") or []:
                required_tag_counts[tag] = required_tag_counts.get(tag, 0) + 1

        valid_image_count = sum(
            1
            for image in images
            if isinstance(image, dict) and image.get("ok")
        )

        return {
            "scene_count": len(scenes),
            "scene_types": scene_types,
            "total_duration_seconds": round(
                sum(float(scene.get("duration_seconds") or 0.0) for scene in scenes),
                2,
            ),
            "valid_image_count": valid_image_count,
            "available_tag_count": len(available_tags),
            "required_tag_counts": required_tag_counts,
            "selection_ready": bool(scenes and valid_image_count),
            "next_step": "Sprint93-5 Scene Image Selector",
        }

    def _dedupe_preserve_order(
        self,
        values: Sequence[str],
    ) -> List[str]:
        result: List[str] = []

        for value in values:
            if value not in result:
                result.append(value)

        return result

    def _save_result(
        self,
        result: Dict[str, Any],
        output_dir: Path,
    ) -> None:
        path = output_dir / "scene_plan.json"
        result["scene_plan_path"] = str(path)

        path.write_text(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )