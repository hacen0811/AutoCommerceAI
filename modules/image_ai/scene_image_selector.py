from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple


class SceneImageSelector:
    """
    Sprint110-1 Scene Purpose Image Selector

    역할:
    - Sprint93-4 scene_plan.json과 Sprint93-3 image_tags.json을 입력받음
    - 장면별 required_tags / fallback_tags / preferred_scene_roles를 기준으로
      가장 적합한 이미지를 자동 선택
    - 장면 목적(hook/problem/usage/benefit/detail/review/comparison/cta)에 맞는
      이미지 역할을 추가 가중치로 반영
    - 리뷰 장면에는 review 이미지를, 사용 장면에는 usage 이미지를,
      상세 장면에는 detail 이미지를 우선 선택
    - 동일 이미지 반복 사용을 줄이되 Hook/CTA는 대표이미지 재사용 허용
    - 선택 점수, 근거, 후보 목록을 저장
    - 결과를 scene_selection.json으로 저장
    """

    VERSION = "scene-image-selector-110-1"

    REUSE_ALLOWED_SCENES = {"hook", "cta"}
    MAX_CANDIDATES_PER_SCENE = 5

    PURPOSE_ROLE_MAP = {
        "hook": {"hero", "main", "product", "feature"},
        "problem": {"problem", "usage", "review", "comparison"},
        "pain": {"problem", "usage", "review", "comparison"},
        "usage": {"usage", "lifestyle", "demonstration", "feature"},
        "use": {"usage", "lifestyle", "demonstration", "feature"},
        "benefit": {"benefit", "feature", "usage", "detail"},
        "feature": {"feature", "detail", "benefit", "product"},
        "detail": {"detail", "feature", "closeup", "product"},
        "review": {"review", "testimonial", "evidence", "benefit"},
        "evidence": {"review", "testimonial", "evidence", "detail"},
        "comparison": {"comparison", "detail", "feature", "review"},
        "cta": {"cta", "hero", "main", "product"},
    }

    PURPOSE_TAG_MAP = {
        "hook": {"hero", "main", "product", "overview"},
        "problem": {"problem", "pain", "before", "issue"},
        "pain": {"problem", "pain", "before", "issue"},
        "usage": {"usage", "use", "lifestyle", "demonstration"},
        "use": {"usage", "use", "lifestyle", "demonstration"},
        "benefit": {"benefit", "feature", "advantage", "result"},
        "feature": {"feature", "detail", "function", "spec"},
        "detail": {"detail", "closeup", "texture", "structure"},
        "review": {"review", "testimonial", "evidence", "rating"},
        "evidence": {"review", "testimonial", "evidence", "rating"},
        "comparison": {"comparison", "compare", "versus", "difference"},
        "cta": {"cta", "hero", "main", "product"},
    }

    REVIEW_HINTS = {
        "review",
        "testimonial",
        "evidence",
        "rating",
        "customer",
        "feedback",
        "후기",
        "리뷰",
        "평점",
        "고객",
    }

    USAGE_HINTS = {
        "usage",
        "use",
        "lifestyle",
        "demonstration",
        "using",
        "사용",
        "활용",
        "연출",
    }

    DETAIL_HINTS = {
        "detail",
        "closeup",
        "feature",
        "texture",
        "structure",
        "디테일",
        "상세",
        "기능",
    }

    HERO_HINTS = {
        "hero",
        "main",
        "product",
        "overview",
        "대표",
        "메인",
        "상품",
    }

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
    ) -> Dict[str, Any]:
        started_at = time.time()

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

        scenes = plan_data.get("scenes", []) if isinstance(plan_data, dict) else []
        images = tag_data.get("images", []) if isinstance(tag_data, dict) else []

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
        ]

        if not valid_images:
            result["status"] = "no_tagged_images"
            result["warnings"].append("선택 가능한 태깅 이미지가 없습니다")
            result["elapsed_seconds"] = round(time.time() - started_at, 3)
            if save_result:
                self._save_result(result, resolved_output_dir)
            return result

        selected_paths: List[str] = []
        selected_scenes: List[Dict[str, Any]] = []

        for scene in scenes:
            if not isinstance(scene, dict):
                continue

            selected_scene = self._select_for_scene(
                scene=scene,
                images=valid_images,
                selected_paths=selected_paths,
            )

            selected_path = str(
                selected_scene.get("selected_image_path") or ""
            ).strip()
            scene_type = self._normalize_token(
                selected_scene.get("scene_type")
            )

            if (
                selected_path
                and (
                    scene_type not in self.REUSE_ALLOWED_SCENES
                    or selected_path not in selected_paths
                )
            ):
                selected_paths.append(selected_path)

            selected_scenes.append(selected_scene)

        selected_count = sum(
            1
            for scene in selected_scenes
            if scene.get("selection_status") == "selected"
        )

        result["scenes"] = selected_scenes
        result["selected_count"] = selected_count
        result["unselected_count"] = len(selected_scenes) - selected_count
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
    ) -> Dict[str, Any]:
        scene_copy = dict(scene)
        scene_purpose = self._resolve_scene_purpose(scene)
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
                    "image_role": str(
                        image.get("image_role")
                        or image.get("role")
                        or image.get("primary_role")
                        or ""
                    ),
                    "quality_score": float(image.get("quality_score") or 0.0),
                    "tag_confidence": float(image.get("tag_confidence") or 0.0),
                    "match_score": round(score, 2),
                    "score_breakdown": breakdown,
                    "matched_tags": matched_tags,
                    "matched_roles": matched_roles,
                    "scene_purpose": scene_purpose,
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
        best = top_candidates[0] if top_candidates else None

        if not best or float(best.get("match_score") or 0.0) <= 0:
            scene_copy["selection_status"] = "not_selected"
            scene_copy["selected_image_path"] = ""
            scene_copy["selected_image_index"] = None
            scene_copy["selected_image_filename"] = ""
            scene_copy["match_score"] = 0.0
            scene_copy["matched_tags"] = []
            scene_copy["matched_roles"] = []
            scene_copy["scene_purpose"] = scene_purpose
            scene_copy["selection_reason"] = "적합한 이미지 후보가 없습니다"
            scene_copy["candidate_images"] = top_candidates
            return scene_copy

        scene_copy["selection_status"] = "selected"
        scene_copy["selected_image_path"] = best["path"]
        scene_copy["selected_image_index"] = best["image_index"]
        scene_copy["selected_image_filename"] = best["filename"]
        scene_copy["selected_image_role"] = best["image_role"]
        scene_copy["match_score"] = best["match_score"]
        scene_copy["matched_tags"] = best["matched_tags"]
        scene_copy["matched_roles"] = best["matched_roles"]
        scene_copy["scene_purpose"] = scene_purpose
        scene_copy["selection_reason"] = self._selection_reason(
            scene=scene,
            candidate=best,
        )
        scene_copy["candidate_images"] = top_candidates

        return scene_copy

    def _score_candidate(
        self,
        scene: Dict[str, Any],
        image: Dict[str, Any],
        selected_paths: Sequence[str],
    ) -> Tuple[float, Dict[str, float], List[str], List[str]]:
        required_tags = self._normalize_list(scene.get("required_tags"))
        fallback_tags = self._normalize_list(scene.get("fallback_tags"))
        preferred_roles = self._normalize_list(
            scene.get("preferred_scene_roles")
        )

        semantic_tags = self._normalize_list(image.get("semantic_tags"))
        scene_roles = self._normalize_list(image.get("scene_roles"))

        image_role = self._normalize_token(
            image.get("image_role")
            or image.get("role")
            or image.get("primary_role")
        )
        if image_role:
            scene_roles = list(dict.fromkeys(scene_roles + [image_role]))

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

        primary_tag = self._normalize_token(image.get("primary_tag"))
        quality_score = float(image.get("quality_score") or 0.0)
        confidence = float(image.get("tag_confidence") or 0.0)
        scene_type = self._normalize_token(scene.get("scene_type"))
        scene_purpose = self._resolve_scene_purpose(scene)

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

        purpose_role_score, purpose_role_matches = self._purpose_role_score(
            scene_purpose=scene_purpose,
            image_roles=role_set,
        )
        purpose_tag_score, purpose_tag_matches = self._purpose_tag_score(
            scene_purpose=scene_purpose,
            image_tags=semantic_set | ({primary_tag} if primary_tag else set()),
        )
        source_hint_score = self._source_hint_score(
            scene_purpose=scene_purpose,
            image=image,
            semantic_tags=semantic_set,
            scene_roles=role_set,
        )

        path = str(image.get("path") or "")
        reuse_penalty = 0.0
        if path in selected_paths and scene_type not in self.REUSE_ALLOWED_SCENES:
            reuse_penalty = 38.0

        no_tag_penalty = 0.0
        if (
            not matched_required
            and not matched_fallback
            and not purpose_tag_matches
            and not purpose_role_matches
        ):
            no_tag_penalty = 20.0

        mismatch_penalty = self._purpose_mismatch_penalty(
            scene_purpose=scene_purpose,
            image_tags=semantic_set,
            image_roles=role_set,
            image=image,
        )

        score = (
            required_score
            + fallback_score
            + role_score
            + primary_bonus
            + quality_component
            + confidence_component
            + purpose_role_score
            + purpose_tag_score
            + source_hint_score
            - reuse_penalty
            - no_tag_penalty
            - mismatch_penalty
        )

        breakdown = {
            "required_tag_score": round(required_score, 2),
            "fallback_tag_score": round(fallback_score, 2),
            "scene_role_score": round(role_score, 2),
            "primary_tag_bonus": round(primary_bonus, 2),
            "quality_score": round(quality_component, 2),
            "confidence_score": round(confidence_component, 2),
            "purpose_role_score": round(purpose_role_score, 2),
            "purpose_tag_score": round(purpose_tag_score, 2),
            "source_hint_score": round(source_hint_score, 2),
            "reuse_penalty": round(-reuse_penalty, 2),
            "no_tag_penalty": round(-no_tag_penalty, 2),
            "purpose_mismatch_penalty": round(-mismatch_penalty, 2),
        }

        matched_tags = matched_required + [
            tag
            for tag in matched_fallback + purpose_tag_matches
            if tag not in matched_required
        ]
        matched_roles = matched_roles + [
            role
            for role in purpose_role_matches
            if role not in matched_roles
        ]

        return (
            max(0.0, score),
            breakdown,
            matched_tags,
            matched_roles,
        )

    def _resolve_scene_purpose(self, scene: Dict[str, Any]) -> str:
        candidates = [
            scene.get("scene_type"),
            scene.get("role"),
            scene.get("scene_role"),
            scene.get("purpose"),
            scene.get("name"),
            scene.get("title"),
        ]
        text = " ".join(
            self._normalize_token(value)
            for value in candidates
            if str(value or "").strip()
        )

        aliases = (
            ("review", ("review", "testimonial", "evidence", "후기", "리뷰", "평점")),
            ("comparison", ("comparison", "compare", "versus", "비교")),
            ("detail", ("detail", "closeup", "spec", "상세", "디테일")),
            ("usage", ("usage", "use", "lifestyle", "사용", "활용")),
            ("benefit", ("benefit", "advantage", "장점", "효과")),
            ("problem", ("problem", "pain", "before", "문제", "불편")),
            ("cta", ("cta", "call to action", "구매", "행동")),
            ("hook", ("hook", "intro", "opening", "후킹", "도입")),
            ("feature", ("feature", "function", "기능")),
        )

        for purpose, keywords in aliases:
            if any(keyword in text for keyword in keywords):
                return purpose

        scene_type = self._normalize_token(scene.get("scene_type"))
        return scene_type or "feature"

    def _purpose_role_score(
        self,
        *,
        scene_purpose: str,
        image_roles: set[str],
    ) -> Tuple[float, List[str]]:
        preferred = self.PURPOSE_ROLE_MAP.get(scene_purpose, set())
        matches = sorted(preferred & image_roles)
        return min(30.0, len(matches) * 15.0), matches

    def _purpose_tag_score(
        self,
        *,
        scene_purpose: str,
        image_tags: set[str],
    ) -> Tuple[float, List[str]]:
        preferred = self.PURPOSE_TAG_MAP.get(scene_purpose, set())
        matches = sorted(preferred & image_tags)
        return min(24.0, len(matches) * 12.0), matches

    def _source_hint_score(
        self,
        *,
        scene_purpose: str,
        image: Dict[str, Any],
        semantic_tags: set[str],
        scene_roles: set[str],
    ) -> float:
        haystack = " ".join(
            [
                self._normalize_token(image.get("path")),
                self._normalize_token(image.get("filename")),
                self._normalize_token(image.get("source")),
                self._normalize_token(image.get("source_type")),
                " ".join(sorted(semantic_tags)),
                " ".join(sorted(scene_roles)),
            ]
        )

        if scene_purpose == "review" and any(
            hint in haystack for hint in self.REVIEW_HINTS
        ):
            return 35.0
        if scene_purpose == "usage" and any(
            hint in haystack for hint in self.USAGE_HINTS
        ):
            return 24.0
        if scene_purpose in {"detail", "feature", "benefit"} and any(
            hint in haystack for hint in self.DETAIL_HINTS
        ):
            return 20.0
        if scene_purpose in {"hook", "cta"} and any(
            hint in haystack for hint in self.HERO_HINTS
        ):
            return 20.0
        return 0.0

    def _purpose_mismatch_penalty(
        self,
        *,
        scene_purpose: str,
        image_tags: set[str],
        image_roles: set[str],
        image: Dict[str, Any],
    ) -> float:
        combined = set(image_tags) | set(image_roles)
        source_text = " ".join(
            [
                self._normalize_token(image.get("path")),
                self._normalize_token(image.get("filename")),
                self._normalize_token(image.get("source")),
                self._normalize_token(image.get("source_type")),
            ]
        )

        is_review = bool(combined & self.REVIEW_HINTS) or any(
            hint in source_text for hint in self.REVIEW_HINTS
        )
        is_usage = bool(combined & self.USAGE_HINTS)
        is_hero = bool(combined & self.HERO_HINTS)

        if scene_purpose == "review" and not is_review:
            return 28.0
        if scene_purpose == "usage" and not is_usage:
            return 16.0
        if scene_purpose in {"hook", "cta"} and is_review and not is_hero:
            return 18.0
        if scene_purpose in {"detail", "feature"} and is_review:
            return 12.0
        return 0.0

    def _selection_reason(
        self,
        scene: Dict[str, Any],
        candidate: Dict[str, Any],
    ) -> str:
        reasons: List[str] = []
        scene_purpose = candidate.get("scene_purpose") or self._resolve_scene_purpose(scene)
        breakdown = candidate.get("score_breakdown") or {}

        reasons.append(f"장면 목적: {scene_purpose}")

        matched_tags = candidate.get("matched_tags") or []
        matched_roles = candidate.get("matched_roles") or []

        if matched_tags:
            reasons.append("장면 태그 일치: " + ", ".join(matched_tags))
        if matched_roles:
            reasons.append("장면 역할 일치: " + ", ".join(matched_roles))

        purpose_score = float(breakdown.get("purpose_role_score") or 0.0) + float(
            breakdown.get("purpose_tag_score") or 0.0
        )
        if purpose_score > 0:
            reasons.append(f"목적 적합도 +{purpose_score:.1f}")

        source_hint_score = float(breakdown.get("source_hint_score") or 0.0)
        if source_hint_score > 0:
            reasons.append(f"이미지 출처·역할 보강 +{source_hint_score:.1f}")

        quality = float(candidate.get("quality_score") or 0.0)
        if quality >= 70:
            reasons.append(f"이미지 품질 {quality:.1f}")

        if candidate.get("reused"):
            reasons.append("대표 이미지 재사용 허용 장면")

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

        selected_paths = [
            str(scene.get("selected_image_path") or "")
            for scene in selected_scenes
            if str(scene.get("selected_image_path") or "").strip()
        ]

        unique_selected_paths = list(dict.fromkeys(selected_paths))
        reused_count = max(0, len(selected_paths) - len(unique_selected_paths))

        scores = [
            float(scene.get("match_score") or 0.0)
            for scene in selected_scenes
        ]

        purpose_counts: Dict[str, int] = {}
        selected_role_counts: Dict[str, int] = {}

        for scene in selected_scenes:
            purpose = str(scene.get("scene_purpose") or "unknown")
            purpose_counts[purpose] = purpose_counts.get(purpose, 0) + 1

            role = str(scene.get("selected_image_role") or "unknown")
            selected_role_counts[role] = selected_role_counts.get(role, 0) + 1

        return {
            "scene_count": len(scenes),
            "selected_scene_count": len(selected_scenes),
            "available_image_count": len(images),
            "unique_selected_image_count": len(unique_selected_paths),
            "reused_image_count": reused_count,
            "average_match_score": (
                round(sum(scores) / len(scores), 2)
                if scores
                else 0.0
            ),
            "minimum_match_score": round(min(scores), 2) if scores else 0.0,
            "maximum_match_score": round(max(scores), 2) if scores else 0.0,
            "scene_purpose_counts": purpose_counts,
            "selected_image_role_counts": selected_role_counts,
            "selected_image_paths": unique_selected_paths,
            "purpose_aware_selection": True,
            "director_ready": len(selected_scenes) == len(scenes),
            "next_step": "Sprint93-6 Gemini Director",
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

    @staticmethod
    def _normalize_token(value: Any) -> str:
        return str(value or "").strip().lower()

    def _normalize_list(self, value: Any) -> List[str]:
        if not isinstance(value, (list, tuple, set)):
            return []
        return [
            token
            for token in (self._normalize_token(item) for item in value)
            if token
        ]