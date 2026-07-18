from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple


class SceneImageSelector:
    """
    Sprint98-1 Multi Reference Scene Image Selector

    역할:
    - Sprint93-4 scene_plan.json과 Sprint93-3 image_tags.json을 입력받음
    - 장면별 required_tags / fallback_tags / preferred_scene_roles를 기준으로
      가장 적합한 이미지를 최대 4장까지 자동 선택
    - 첫 번째 이미지는 primary reference로 유지
    - 기존 selected_image_path 키를 유지하여 하위 호환
    - selected_image_paths / reference_images를 추가하여 멀티 레퍼런스 지원
    - 동일 이미지 반복 사용을 줄이되 Hook/CTA는 대표이미지 재사용 허용
    - 결과를 scene_selection.json으로 저장
    """

    VERSION = "scene-image-selector-98-1"

    REUSE_ALLOWED_SCENES = {"hook", "cta"}
    MAX_CANDIDATES_PER_SCENE = 8
    MAX_REFERENCE_IMAGES_PER_SCENE = 4
    MIN_SECONDARY_MATCH_SCORE = 12.0

    def select(
        self,
        scene_plan: Any = None,
        scene_plan_path: Any = "",
        tag_result: Any = None,
        image_tags_path: Any = "",
        output_dir: Any = "",
        project_id: Any = "",
        product_name: str = "",
        save_result: bool = True,
        max_reference_images: int = 4,
    ) -> Dict[str, Any]:
        started_at = time.time()

        max_reference_images = max(
            1,
            min(
                int(max_reference_images or self.MAX_REFERENCE_IMAGES_PER_SCENE),
                self.MAX_REFERENCE_IMAGES_PER_SCENE,
            ),
        )

        result: Dict[str, Any] = {
            "ok": False,
            "ready": False,
            "version": self.VERSION,
            "status": "not_run",
            "project_id": str(project_id or ""),
            "product_name": str(product_name or "").strip(),
            "scene_plan_path": str(scene_plan_path or "").strip(),
            "image_tags_path": str(image_tags_path or "").strip(),
            "output_dir": "",
            "scene_selection_path": "",
            "scene_count": 0,
            "selected_count": 0,
            "unselected_count": 0,
            "max_reference_images": max_reference_images,
            "total_reference_image_count": 0,
            "scenes": [],
            "summary": {},
            "warnings": [],
            "errors": [],
            "elapsed_seconds": 0.0,
        }

        plan_data = self._resolve_json_source(
            value=scene_plan,
            path_value=scene_plan_path,
        )
        tag_data = self._resolve_json_source(
            value=tag_result,
            path_value=image_tags_path,
        )

        scenes = (
            plan_data.get("scenes", [])
            if isinstance(plan_data, dict)
            else []
        )
        images = (
            tag_data.get("images", [])
            if isinstance(tag_data, dict)
            else []
        )

        scenes = scenes if isinstance(scenes, list) else []
        images = images if isinstance(images, list) else []

        result["scene_count"] = len(scenes)

        resolved_output_dir = self._resolve_output_dir(
            output_dir=output_dir,
            scene_plan_path=scene_plan_path,
            image_tags_path=image_tags_path,
            plan_data=plan_data,
            tag_data=tag_data,
            project_id=project_id,
        )
        resolved_output_dir.mkdir(parents=True, exist_ok=True)
        result["output_dir"] = str(resolved_output_dir)

        if not scenes:
            result["status"] = "no_scenes"
            result["warnings"].append("선택할 Scene Plan이 없습니다")
            result["elapsed_seconds"] = round(time.time() - started_at, 3)
            if save_result:
                self._save_result(result, resolved_output_dir)
            return result

        valid_images = [
            image
            for image in images
            if isinstance(image, dict)
            and image.get("ok")
            and str(image.get("path") or "").strip()
            and Path(str(image.get("path") or "")).is_file()
        ]

        if not valid_images:
            result["status"] = "no_tagged_images"
            result["warnings"].append("선택 가능한 태깅 이미지가 없습니다")
            result["elapsed_seconds"] = round(time.time() - started_at, 3)
            if save_result:
                self._save_result(result, resolved_output_dir)
            return result

        globally_selected_paths: List[str] = []
        selected_scenes: List[Dict[str, Any]] = []

        for scene in scenes:
            if not isinstance(scene, dict):
                continue

            selected_scene = self._select_for_scene(
                scene=scene,
                images=valid_images,
                selected_paths=globally_selected_paths,
                max_reference_images=max_reference_images,
            )

            scene_type = str(
                selected_scene.get("scene_type") or ""
            ).strip()

            selected_paths = [
                str(path or "").strip()
                for path in selected_scene.get("selected_image_paths") or []
                if str(path or "").strip()
            ]

            for selected_path in selected_paths:
                if (
                    scene_type not in self.REUSE_ALLOWED_SCENES
                    and selected_path not in globally_selected_paths
                ):
                    globally_selected_paths.append(selected_path)

            selected_scenes.append(selected_scene)

        selected_count = sum(
            1
            for scene in selected_scenes
            if scene.get("selection_status") == "selected"
        )

        total_reference_image_count = sum(
            len(scene.get("selected_image_paths") or [])
            for scene in selected_scenes
        )

        result["scenes"] = selected_scenes
        result["selected_count"] = selected_count
        result["unselected_count"] = len(selected_scenes) - selected_count
        result["total_reference_image_count"] = total_reference_image_count
        result["summary"] = self._build_summary(
            scenes=selected_scenes,
            images=valid_images,
        )
        result["ok"] = selected_count > 0
        result["ready"] = selected_count == len(selected_scenes)
        result["status"] = (
            "selected"
            if result["ready"]
            else "partial"
            if selected_count > 0
            else "failed"
        )
        result["elapsed_seconds"] = round(time.time() - started_at, 3)

        if save_result:
            self._save_result(result, resolved_output_dir)

        return result

    def _resolve_json_source(
        self,
        value: Any,
        path_value: Any,
    ) -> Dict[str, Any]:
        if isinstance(value, dict):
            return dict(value)

        resolved_path = str(path_value or "").strip()

        if not resolved_path and isinstance(value, (str, Path)):
            resolved_path = str(value)

        if not resolved_path:
            return {}

        path = Path(resolved_path).expanduser()

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
        scene_plan_path: Any,
        image_tags_path: Any,
        plan_data: Dict[str, Any],
        tag_data: Dict[str, Any],
        project_id: Any,
    ) -> Path:
        if str(output_dir or "").strip():
            return Path(str(output_dir)).expanduser()

        for data in (plan_data, tag_data):
            data_output = str(data.get("output_dir") or "").strip()
            if data_output:
                return Path(data_output).expanduser()

        for raw_path in (scene_plan_path, image_tags_path):
            value = str(raw_path or "").strip()
            if value:
                return Path(value).expanduser().parent

        project_key = str(project_id or "unknown").strip() or "unknown"
        return Path("assets") / "product_images" / f"project_{project_key}"

    def _select_for_scene(
        self,
        scene: Dict[str, Any],
        images: Sequence[Dict[str, Any]],
        selected_paths: Sequence[str],
        max_reference_images: int,
    ) -> Dict[str, Any]:
        scene_copy = dict(scene)
        scored_candidates: List[Dict[str, Any]] = []

        for image in images:
            score, breakdown, matched_tags, matched_roles = self._score_candidate(
                scene=scene,
                image=image,
                selected_paths=selected_paths,
            )

            scored_candidates.append(
                {
                    "path": str(image.get("path") or ""),
                    "filename": str(image.get("filename") or ""),
                    "image_index": image.get("index"),
                    "primary_tag": str(image.get("primary_tag") or ""),
                    "semantic_tags": list(image.get("semantic_tags") or []),
                    "scene_roles": list(image.get("scene_roles") or []),
                    "quality_score": float(image.get("quality_score") or 0.0),
                    "tag_confidence": float(image.get("tag_confidence") or 0.0),
                    "match_score": round(score, 2),
                    "score_breakdown": breakdown,
                    "matched_tags": matched_tags,
                    "matched_roles": matched_roles,
                    "reused": str(image.get("path") or "") in selected_paths,
                }
            )

        scored_candidates.sort(
            key=lambda item: (
                -float(item.get("match_score") or 0.0),
                -float(item.get("quality_score") or 0.0),
                str(item.get("filename") or ""),
            )
        )

        top_candidates = scored_candidates[: self.MAX_CANDIDATES_PER_SCENE]
        selected_references = self._select_reference_set(
            candidates=top_candidates,
            max_reference_images=max_reference_images,
        )

        if not selected_references:
            scene_copy["selection_status"] = "not_selected"
            scene_copy["selected_image_path"] = ""
            scene_copy["selected_image_paths"] = []
            scene_copy["primary_reference_image"] = ""
            scene_copy["reference_images"] = []
            scene_copy["selected_image_index"] = None
            scene_copy["selected_image_filename"] = ""
            scene_copy["match_score"] = 0.0
            scene_copy["matched_tags"] = []
            scene_copy["matched_roles"] = []
            scene_copy["selection_reason"] = "적합한 이미지 후보가 없습니다"
            scene_copy["candidate_images"] = top_candidates
            scene_copy["reference_image_count"] = 0
            return scene_copy

        primary = selected_references[0]
        reference_paths = [
            str(item.get("path") or "")
            for item in selected_references
            if str(item.get("path") or "").strip()
        ]

        scene_copy["selection_status"] = "selected"

        # 하위 호환 키
        scene_copy["selected_image_path"] = primary["path"]
        scene_copy["selected_image_index"] = primary["image_index"]
        scene_copy["selected_image_filename"] = primary["filename"]

        # Sprint98 멀티 레퍼런스 키
        scene_copy["selected_image_paths"] = reference_paths
        scene_copy["primary_reference_image"] = primary["path"]
        scene_copy["reference_images"] = reference_paths
        scene_copy["reference_image_count"] = len(reference_paths)
        scene_copy["selected_reference_images"] = selected_references

        scene_copy["match_score"] = primary["match_score"]
        scene_copy["matched_tags"] = primary["matched_tags"]
        scene_copy["matched_roles"] = primary["matched_roles"]
        scene_copy["selection_reason"] = self._selection_reason(
            scene=scene,
            candidate=primary,
            reference_count=len(reference_paths),
        )
        scene_copy["candidate_images"] = top_candidates

        return scene_copy

    def _select_reference_set(
        self,
        candidates: Sequence[Dict[str, Any]],
        max_reference_images: int,
    ) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        primary = candidates[0]
        if float(primary.get("match_score") or 0.0) <= 0:
            return []

        selected = [dict(primary)]
        selected_paths = {str(primary.get("path") or "")}
        covered_tags = set(primary.get("matched_tags") or [])
        covered_roles = set(primary.get("matched_roles") or [])

        for candidate in candidates[1:]:
            if len(selected) >= max_reference_images:
                break

            path = str(candidate.get("path") or "").strip()
            score = float(candidate.get("match_score") or 0.0)

            if not path or path in selected_paths:
                continue
            if score < self.MIN_SECONDARY_MATCH_SCORE:
                continue

            candidate_tags = set(candidate.get("matched_tags") or [])
            candidate_roles = set(candidate.get("matched_roles") or [])

            adds_new_information = bool(
                candidate_tags - covered_tags
                or candidate_roles - covered_roles
            )

            strong_support = score >= max(
                self.MIN_SECONDARY_MATCH_SCORE,
                float(primary.get("match_score") or 0.0) * 0.45,
            )

            if not adds_new_information and not strong_support:
                continue

            selected.append(dict(candidate))
            selected_paths.add(path)
            covered_tags.update(candidate_tags)
            covered_roles.update(candidate_roles)

        return selected

    def _score_candidate(
        self,
        scene: Dict[str, Any],
        image: Dict[str, Any],
        selected_paths: Sequence[str],
    ) -> Tuple[float, Dict[str, float], List[str], List[str]]:
        required_tags = [
            str(tag)
            for tag in scene.get("required_tags") or []
        ]
        fallback_tags = [
            str(tag)
            for tag in scene.get("fallback_tags") or []
        ]
        preferred_roles = [
            str(role)
            for role in scene.get("preferred_scene_roles") or []
        ]

        semantic_tags = [
            str(tag)
            for tag in image.get("semantic_tags") or []
        ]
        scene_roles = [
            str(role)
            for role in image.get("scene_roles") or []
        ]

        semantic_set = set(semantic_tags)
        role_set = set(scene_roles)

        matched_required = [
            tag for tag in required_tags if tag in semantic_set
        ]
        matched_fallback = [
            tag for tag in fallback_tags if tag in semantic_set
        ]
        matched_roles = [
            role for role in preferred_roles if role in role_set
        ]

        primary_tag = str(image.get("primary_tag") or "")
        quality_score = float(image.get("quality_score") or 0.0)
        confidence = float(image.get("tag_confidence") or 0.0)
        scene_type = str(scene.get("scene_type") or "")

        required_score = min(55.0, len(matched_required) * 32.0)
        fallback_score = min(22.0, len(matched_fallback) * 10.0)
        role_score = min(18.0, len(matched_roles) * 9.0)
        primary_bonus = (
            12.0
            if primary_tag in matched_required
            else 6.0
            if primary_tag in matched_fallback
            else 0.0
        )
        quality_component = min(12.0, quality_score * 0.12)
        confidence_component = min(8.0, confidence * 0.08)

        path = str(image.get("path") or "")
        reuse_penalty = 0.0

        if path in selected_paths and scene_type not in self.REUSE_ALLOWED_SCENES:
            reuse_penalty = 26.0

        no_tag_penalty = 0.0
        if not matched_required and not matched_fallback:
            no_tag_penalty = 20.0

        score = (
            required_score
            + fallback_score
            + role_score
            + primary_bonus
            + quality_component
            + confidence_component
            - reuse_penalty
            - no_tag_penalty
        )

        breakdown = {
            "required_tag_score": round(required_score, 2),
            "fallback_tag_score": round(fallback_score, 2),
            "scene_role_score": round(role_score, 2),
            "primary_tag_bonus": round(primary_bonus, 2),
            "quality_score": round(quality_component, 2),
            "confidence_score": round(confidence_component, 2),
            "reuse_penalty": round(-reuse_penalty, 2),
            "no_tag_penalty": round(-no_tag_penalty, 2),
        }

        matched_tags = matched_required + [
            tag
            for tag in matched_fallback
            if tag not in matched_required
        ]

        return (
            max(0.0, score),
            breakdown,
            matched_tags,
            matched_roles,
        )

    def _selection_reason(
        self,
        scene: Dict[str, Any],
        candidate: Dict[str, Any],
        reference_count: int,
    ) -> str:
        reasons: List[str] = []

        matched_tags = candidate.get("matched_tags") or []
        matched_roles = candidate.get("matched_roles") or []

        if matched_tags:
            reasons.append(
                "장면 태그 일치: " + ", ".join(matched_tags)
            )

        if matched_roles:
            reasons.append(
                "장면 역할 일치: " + ", ".join(matched_roles)
            )

        quality = float(candidate.get("quality_score") or 0.0)
        if quality >= 70:
            reasons.append(f"이미지 품질 {quality:.1f}")

        if candidate.get("reused"):
            reasons.append("대표 이미지 재사용 허용 장면")

        reasons.append(f"멀티 레퍼런스 {reference_count}장")

        return " / ".join(reasons)

    def _build_summary(
        self,
        scenes: Sequence[Dict[str, Any]],
        images: Sequence[Dict[str, Any]],
    ) -> Dict[str, Any]:
        selected_scenes = [
            scene
            for scene in scenes
            if scene.get("selection_status") == "selected"
        ]

        all_selected_paths: List[str] = []
        scene_reference_counts: Dict[str, int] = {}

        for scene in selected_scenes:
            scene_id = str(scene.get("scene_id") or "")
            paths = [
                str(path or "").strip()
                for path in scene.get("selected_image_paths") or []
                if str(path or "").strip()
            ]
            all_selected_paths.extend(paths)
            scene_reference_counts[scene_id] = len(paths)

        unique_selected_paths = list(dict.fromkeys(all_selected_paths))
        reused_count = max(
            0,
            len(all_selected_paths) - len(unique_selected_paths),
        )

        scores = [
            float(scene.get("match_score") or 0.0)
            for scene in selected_scenes
        ]

        return {
            "scene_count": len(scenes),
            "selected_scene_count": len(selected_scenes),
            "available_image_count": len(images),
            "total_reference_image_count": len(all_selected_paths),
            "unique_selected_image_count": len(unique_selected_paths),
            "reused_image_count": reused_count,
            "average_references_per_scene": (
                round(len(all_selected_paths) / len(selected_scenes), 2)
                if selected_scenes
                else 0.0
            ),
            "scene_reference_counts": scene_reference_counts,
            "average_match_score": (
                round(sum(scores) / len(scores), 2)
                if scores
                else 0.0
            ),
            "minimum_match_score": (
                round(min(scores), 2)
                if scores
                else 0.0
            ),
            "maximum_match_score": (
                round(max(scores), 2)
                if scores
                else 0.0
            ),
            "selected_image_paths": unique_selected_paths,
            "multi_reference_ready": all(
                len(scene.get("selected_image_paths") or []) >= 1
                for scene in selected_scenes
            ),
            "director_ready": len(selected_scenes) == len(scenes),
            "next_step": "Sprint98-2 Gemini Director Multi Reference",
        }

    def _save_result(
        self,
        result: Dict[str, Any],
        output_dir: Path,
    ) -> None:
        path = output_dir / "scene_selection.json"
        result["scene_selection_path"] = str(path)

        path.write_text(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )