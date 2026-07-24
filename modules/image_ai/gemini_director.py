from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence


class GeminiDirector:
    """
    Sprint129-1 Gemini Director Core

    역할:
    - Sprint93-5 scene_selection.json을 입력받음
    - 선택된 제품 이미지와 장면 목적을 Gemini/Veo용 프롬프트로 변환
    - 첫 프레임 유지, 제품 재해석 금지, 카메라 연출, 전환, 연속성 규칙 생성
    - 장면별 prompt / negative_prompt / policy를 구성
    - Sprint93-6B 저장 단계에서 사용할 director_manifest 구조 반환

    이 단계는 API 호출을 수행하지 않는다.
    """

    VERSION = "gemini-director-129-1"

    ASPECT_RATIO = "9:16"
    DEFAULT_FPS = 30
    DEFAULT_STYLE = "photorealistic commercial product video"

    FIRST_FRAME_POLICY = (
        "Use the selected reference image exactly as the first frame. "
        "Start directly from the supplied image without recreating, redrawing, "
        "reframing, restaging, or reinterpreting it."
    )

    PRODUCT_IDENTITY_POLICY = (
        "Preserve the exact product identity throughout the shot. "
        "Keep the same product shape, dimensions, color, material, texture, "
        "logos, printed details, components, orientation, and visible defects. "
        "Do not add, remove, replace, duplicate, deform, or redesign any part."
    )

    COMPOSITION_POLICY = (
        "Preserve the original room, background, surface, lighting direction, "
        "camera position, perspective, framing, and object placement from the "
        "reference image. Only introduce the requested camera motion and minimal "
        "natural environmental movement."
    )

    CONTINUITY_POLICY = (
        "Maintain temporal and visual continuity from the first frame to the last. "
        "Avoid sudden changes in product position, scale, lighting, background, "
        "camera axis, or scene geometry."
    )

    OUTPUT_POLICY = (
        "Create a vertical 9:16 shopping-short video. Keep the product visible within "
        "the central safe area, sharp, realistic, stable, and commercially presentable. "
        "The product must remain the primary visual subject, not the model or background. "
        "No subtitles, no captions, no graphic text, "
        "no UI overlays, no watermark, and no generated brand marks."
    )

    NEGATIVE_BASE = [
        "product redesign",
        "changed product color",
        "changed product shape",
        "changed proportions",
        "changed material",
        "missing parts",
        "extra parts",
        "duplicated product",
        "warped geometry",
        "melting object",
        "floating object",
        "incorrect logo",
        "new text",
        "subtitles",
        "captions",
        "watermark",
        "UI overlay",
        "camera jump",
        "scene cut inside the shot",
        "background replacement",
        "lighting flicker",
        "focus pumping",
        "motion blur on product",
        "low resolution",
        "cartoon style",
        "illustration",
        "unrealistic physics",
        "human hands unless already visible",
        "new people",
    ]

    MOTION_LIBRARY: Dict[str, str] = {
        "slow_push_in": (
            "Apply a very slow, stable push-in toward the product. "
            "Keep the optical center and product proportions unchanged."
        ),
        "slow_pull_out": (
            "Apply a very slow, stable pull-out that reveals slightly more of "
            "the existing scene without changing the composition."
        ),
        "subtle_pan": (
            "Apply a subtle horizontal pan across the existing composition. "
            "Do not reveal newly invented areas outside the reference frame."
        ),
        "focus_reveal": (
            "Keep the camera nearly static while gradually shifting visual emphasis "
            "toward the key product feature using gentle focus and micro movement."
        ),
        "macro_zoom": (
            "Apply a restrained macro-style zoom toward the selected product detail. "
            "Do not invent texture or structure that is not visible."
        ),
        "demonstration_move": (
            "Use a controlled demonstration-style camera move that follows only "
            "the visible product feature. Do not animate unsupported product actions."
        ),
        "split_reveal": (
            "Use a restrained comparison reveal within the existing composition. "
            "Do not generate a literal split screen unless one already exists."
        ),
        "step_motion": (
            "Use a gentle step-by-step visual emphasis on visible installation or "
            "component details. Do not generate hands or tools unless present."
        ),
        "static_hold": (
            "Keep the camera locked with only minimal natural parallax and breathing motion."
        ),
    }

    TRANSITION_LIBRARY: Dict[str, str] = {
        "cut": "End on a stable frame suitable for a clean straight cut.",
        "match_cut": (
            "End with stable framing and product placement suitable for a visual match cut."
        ),
        "fade": "End on a stable composition suitable for a short fade-out.",
        "crossfade": "End with low motion suitable for a soft crossfade.",
        "none": "Do not create an internal transition inside this shot.",
    }

    GOAL_LIBRARY: Dict[str, str] = {
        "hook": (
            "Immediately establish the product as the visual focus and create curiosity "
            "within the first second."
        ),
        "problem": (
            "Emphasize the user problem, inconvenience, limitation, or purchase concern "
            "suggested by the selected image without inventing new events."
        ),
        "feature": (
            "Direct attention to the product's main visible feature and make its benefit "
            "easy to understand visually."
        ),
        "detail": (
            "Show the visible construction, material, finish, component, or mechanism "
            "with credible commercial detail."
        ),
        "proof": (
            "Present the visible usage evidence, capacity, size, comparison, or practical "
            "benefit as trustworthy purchase support."
        ),
        "comparison": (
            "Clarify a visible difference in size, function, configuration, or use case "
            "without generating unsupported comparison objects."
        ),
        "installation": (
            "Clarify the visible installation or assembly concept without inventing "
            "hands, tools, parts, or steps."
        ),
        "cta": (
            "Finish with a clean, confident hero presentation of the exact product."
        ),
    }


    ROLE_DIRECTION_LIBRARY: Dict[str, Dict[str, Any]] = {
        "hero": {
            "motions": ["slow_push_in", "slow_pull_out", "subtle_pan"],
            "action": "Keep the product still and premium while subtle natural light or background parallax creates immediate visual interest.",
            "shot": "Use a clean hero composition with the product as the unmistakable focal point from the first second.",
        },
        "usage": {
            "motions": ["demonstration_move", "subtle_pan", "slow_pull_out"],
            "action": "Show only a natural, physically credible use cue already supported by the reference image. Prefer environmental movement over invented hands or mechanisms.",
            "shot": "Frame the product in practical context so viewers can understand how it fits into everyday use.",
        },
        "detail": {
            "motions": ["macro_zoom", "focus_reveal", "static_hold"],
            "action": "Reveal visible material, texture, finish, seam, control, edge, or component detail without inventing hidden construction.",
            "shot": "Use restrained close-up emphasis and keep the exact visible geometry sharply readable.",
        },
        "feature": {
            "motions": ["focus_reveal", "demonstration_move", "slow_push_in"],
            "action": "Guide attention toward one visible feature and communicate its benefit through composition, focus, and camera movement rather than added graphics.",
            "shot": "Build one clear visual idea around the selected feature and avoid competing movements.",
        },
        "comparison": {
            "motions": ["split_reveal", "subtle_pan", "static_hold"],
            "action": "Clarify only differences already visible in the reference composition. Do not create a new comparison item or fake before-and-after state.",
            "shot": "Use measured side-to-side visual emphasis that supports a trustworthy comparison.",
        },
        "proof": {
            "motions": ["slow_pull_out", "focus_reveal", "subtle_pan"],
            "action": "Emphasize visible evidence such as capacity, scale, placement, stability, or practical fit without unsupported performance claims.",
            "shot": "Present the evidence calmly and credibly like commercial B-roll rather than a dramatic effect shot.",
        },
        "installation": {
            "motions": ["step_motion", "focus_reveal", "static_hold"],
            "action": "Visually guide the viewer through only the installation state already visible. Do not generate missing tools, hands, parts, or steps.",
            "shot": "Use orderly step emphasis with stable framing and clear component visibility.",
        },
        "cta": {
            "motions": ["slow_push_in", "static_hold", "slow_pull_out"],
            "action": "Finish with a confident, polished product hold. Keep motion minimal and end on a clean frame suitable for editing.",
            "shot": "Return to a premium hero presentation and make the final product silhouette easy to recognize.",
        },
        "problem": {
            "motions": ["subtle_pan", "slow_push_in", "static_hold"],
            "action": "Use the existing environment and composition to suggest the inconvenience or concern without inventing a new accident, mess, person, or failure.",
            "shot": "Create mild tension through framing and emphasis while preserving realism.",
        },
    }

    EMOTION_DIRECTION_LIBRARY: Dict[str, str] = {
        "curiosity": (
            "Create immediate visual curiosity with a clear focal reveal, but do not hide, "
            "distort, or replace the product."
        ),
        "empathy": (
            "Use restrained pacing and practical context so the viewer recognizes the real-life "
            "inconvenience without exaggerated acting or invented events."
        ),
        "tension": (
            "Build mild purchase tension through tighter emphasis and deliberate pacing while "
            "keeping the product and environment stable and realistic."
        ),
        "solution": (
            "Shift the visual rhythm toward clarity and relief by making the visible benefit easy "
            "to understand in one continuous action."
        ),
        "relief": (
            "Use smoother, calmer motion and more open visual breathing room to communicate that "
            "the practical problem has been reduced."
        ),
        "satisfaction": (
            "Finish with confident, polished product presentation and a stable final composition "
            "that feels complete rather than overly dramatic."
        ),
    }

    SCENE_ROLE_MAP: Dict[str, str] = {
        "hook": "hero",
        "problem": "problem",
        "feature": "feature",
        "detail": "detail",
        "proof": "proof",
        "comparison": "comparison",
        "installation": "installation",
        "cta": "cta",
        "usage": "usage",
        "hero": "hero",
    }

    def build(
        self,
        scene_selection: Any = None,
        scene_selection_path: Any = "",
        vision_analysis: Any = None,
        vision_analysis_path: Any = "",
        image_tags: Any = None,
        image_tags_path: Any = "",
        product_name: str = "",
        project_id: Any = "",
        model_name: str = "veo",
        style: str = DEFAULT_STYLE,
        language: str = "en",
    ) -> Dict[str, Any]:
        started_at = time.time()

        result: Dict[str, Any] = {
            "ok": False,
            "ready": False,
            "version": self.VERSION,
            "status": "not_run",
            "project_id": str(project_id or ""),
            "product_name": str(product_name or "").strip(),
            "model_name": str(model_name or "veo").strip(),
            "language": str(language or "en").strip().lower(),
            "aspect_ratio": self.ASPECT_RATIO,
            "fps": self.DEFAULT_FPS,
            "style": str(style or self.DEFAULT_STYLE).strip(),
            "scene_selection_path": str(scene_selection_path or "").strip(),
            "vision_analysis_path": str(vision_analysis_path or "").strip(),
            "image_tags_path": str(image_tags_path or "").strip(),
            "story_aware": True,
            "story_context_count": 0,
            "scenes": [],
            "summary": {},
            "warnings": [],
            "errors": [],
            "elapsed_seconds": 0.0,
        }

        selection_data = self._resolve_json_source(
            value=scene_selection,
            path_value=scene_selection_path,
        )
        vision_data = self._resolve_json_source(
            value=vision_analysis,
            path_value=vision_analysis_path,
        )
        tag_data = self._resolve_json_source(
            value=image_tags,
            path_value=image_tags_path,
        )

        scenes = (
            selection_data.get("scenes", [])
            if isinstance(selection_data, dict)
            else []
        )
        scenes = scenes if isinstance(scenes, list) else []

        if not result["product_name"]:
            result["product_name"] = self._first_non_empty(
                selection_data.get("product_name"),
                vision_data.get("product_name"),
                tag_data.get("product_name"),
            )

        if not result["project_id"]:
            result["project_id"] = self._first_non_empty(
                selection_data.get("project_id"),
                vision_data.get("project_id"),
                tag_data.get("project_id"),
            )

        if not scenes:
            result["status"] = "no_selected_scenes"
            result["warnings"].append("Gemini Director가 처리할 선택 장면이 없습니다")
            result["elapsed_seconds"] = round(time.time() - started_at, 3)
            return result

        vision_index = self._build_image_index(
            vision_data.get("images", [])
            if isinstance(vision_data, dict)
            else []
        )
        tag_index = self._build_image_index(
            tag_data.get("images", [])
            if isinstance(tag_data, dict)
            else []
        )

        directed_scenes: List[Dict[str, Any]] = []
        previous_motion = ""

        for scene_order, scene in enumerate(scenes, start=1):
            if not isinstance(scene, dict):
                continue

            directed_scene = self._direct_scene(
                scene=scene,
                vision_index=vision_index,
                tag_index=tag_index,
                product_name=result["product_name"],
                style=result["style"],
                language=result["language"],
                previous_motion=previous_motion,
                scene_order=scene_order,
            )
            directed_scenes.append(directed_scene)
            if directed_scene.get("ready"):
                previous_motion = str(directed_scene.get("camera_motion") or "")

        ready_count = sum(
            1
            for scene in directed_scenes
            if scene.get("ready")
        )

        result["scenes"] = directed_scenes
        result["story_context_count"] = sum(
            1 for item in directed_scenes if item.get("story_context_used")
        )
        result["summary"] = self._build_summary(directed_scenes)
        result["ok"] = ready_count > 0
        result["ready"] = ready_count == len(directed_scenes)
        result["status"] = (
            "directed"
            if result["ready"]
            else "partial"
            if ready_count > 0
            else "failed"
        )
        result["elapsed_seconds"] = round(time.time() - started_at, 3)

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

    def _build_image_index(
        self,
        images: Any,
    ) -> Dict[str, Dict[str, Any]]:
        index: Dict[str, Dict[str, Any]] = {}

        if not isinstance(images, list):
            return index

        for image in images:
            if not isinstance(image, dict):
                continue

            path = self._normalize_path(image.get("path"))
            filename = str(image.get("filename") or "").strip()

            if path:
                index[path] = image

            if filename:
                index[filename.lower()] = image

        return index

    def _direct_scene(
        self,
        scene: Dict[str, Any],
        vision_index: Dict[str, Dict[str, Any]],
        tag_index: Dict[str, Dict[str, Any]],
        product_name: str,
        style: str,
        language: str,
        previous_motion: str = "",
        scene_order: int = 1,
    ) -> Dict[str, Any]:
        scene_id = str(scene.get("scene_id") or "").strip()
        scene_type = str(scene.get("scene_type") or "feature").strip().lower()
        image_path = str(scene.get("selected_image_path") or "").strip()
        image_filename = str(
            scene.get("selected_image_filename")
            or Path(image_path).name
            or ""
        ).strip()

        duration = self._normalize_duration(
            scene.get("duration_seconds")
        )
        requested_motion = str(scene.get("motion") or "").strip()
        transition_key = str(scene.get("transition") or "cut").strip()

        vision = self._lookup_image(
            image_path=image_path,
            filename=image_filename,
            index=vision_index,
        )
        tags = self._lookup_image(
            image_path=image_path,
            filename=image_filename,
            index=tag_index,
        )

        visual_context = self._build_visual_context(
            vision=vision,
            tags=tags,
            scene=scene,
        )
        story_context = self._build_story_context(scene)
        goal = self.GOAL_LIBRARY.get(
            scene_type,
            str(scene.get("purpose") or "").strip()
            or self.GOAL_LIBRARY["feature"],
        )
        director_role = self._resolve_director_role(scene, scene_type)
        direction_plan = self._select_direction_plan(
            director_role=director_role,
            requested_motion=requested_motion,
            previous_motion=previous_motion,
            scene_order=scene_order,
        )
        motion_key = direction_plan["motion"]
        motion_instruction = self.MOTION_LIBRARY.get(
            motion_key,
            self.MOTION_LIBRARY["static_hold"],
        )
        transition_instruction = self.TRANSITION_LIBRARY.get(
            transition_key,
            self.TRANSITION_LIBRARY["cut"],
        )

        prompt = self._compose_prompt(
            scene_id=scene_id,
            scene_type=scene_type,
            product_name=product_name,
            duration=duration,
            style=style,
            goal=goal,
            motion_instruction=motion_instruction,
            transition_instruction=transition_instruction,
            visual_context=visual_context,
            director_role=director_role,
            action_instruction=direction_plan["action"],
            shot_instruction=direction_plan["shot"],
            diversity_instruction=direction_plan["diversity"],
            story_context=story_context,
        )

        negative_prompt = self._compose_negative_prompt(
            scene_type=scene_type,
            scene=scene,
        )

        ready = bool(
            scene_id
            and image_path
            and scene.get("selection_status") == "selected"
        )

        warnings: List[str] = []

        if not image_path:
            warnings.append("선택 이미지 경로 없음")

        if scene.get("selection_status") != "selected":
            warnings.append("Sprint93-5 이미지 선택 미완료")

        return {
            "scene_id": scene_id,
            "scene_index": scene.get("scene_index"),
            "scene_type": scene_type,
            "director_role": director_role,
            "title": str(scene.get("title") or "").strip(),
            "goal": goal,
            "story_goal": story_context.get("story_goal", ""),
            "story_purpose": story_context.get("story_purpose", ""),
            "emotion_stage": story_context.get("emotion_stage", ""),
            "emotion_instruction": story_context.get("emotion_instruction", ""),
            "primary_selling_point": story_context.get("primary_selling_point", ""),
            "review_evidence": story_context.get("review_evidence", ""),
            "must_show": story_context.get("must_show", ""),
            "story_context_used": bool(story_context.get("used")),
            "action_instruction": direction_plan["action"],
            "shot_instruction": direction_plan["shot"],
            "diversity_instruction": direction_plan["diversity"],
            "motion_reused_prevented": bool(direction_plan["reused_prevented"]),
            "selected_image_path": image_path,
            "selected_image_filename": image_filename,
            "duration_seconds": duration,
            "camera_motion": motion_key,
            "camera_instruction": motion_instruction,
            "transition": transition_key,
            "transition_instruction": transition_instruction,
            "aspect_ratio": self.ASPECT_RATIO,
            "fps": self.DEFAULT_FPS,
            "style": style,
            "visual_context": visual_context,
            "matched_tags": list(scene.get("matched_tags") or []),
            "matched_roles": list(scene.get("matched_roles") or []),
            "match_score": float(scene.get("match_score") or 0.0),
            "first_frame_policy": self.FIRST_FRAME_POLICY,
            "product_identity_policy": self.PRODUCT_IDENTITY_POLICY,
            "composition_policy": self.COMPOSITION_POLICY,
            "continuity_policy": self.CONTINUITY_POLICY,
            "output_policy": self.OUTPUT_POLICY,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "prompt_filename": self._prompt_filename(scene_id),
            "ready": ready,
            "status": "ready" if ready else "not_ready",
            "warnings": warnings,
        }

    def _build_story_context(self, scene: Dict[str, Any]) -> Dict[str, Any]:
        raw_context = scene.get("director_context")
        raw_context = raw_context if isinstance(raw_context, dict) else {}

        story_goal = self._first_non_empty(
            scene.get("story_goal"),
            raw_context.get("scene_goal"),
            raw_context.get("story_goal"),
        )
        story_purpose = self._first_non_empty(
            scene.get("story_purpose"),
            raw_context.get("scene_purpose"),
            raw_context.get("story_purpose"),
        )
        emotion_stage = self._first_non_empty(
            scene.get("emotion_stage"),
            raw_context.get("emotion_stage"),
        )
        primary_selling_point = self._first_non_empty(
            scene.get("primary_selling_point"),
            raw_context.get("primary_selling_point"),
        )
        review_evidence = self._first_non_empty(
            scene.get("review_evidence"),
            raw_context.get("review_evidence"),
            raw_context.get("evidence_text"),
        )
        must_show = self._first_non_empty(
            scene.get("must_show"),
            raw_context.get("must_show"),
            primary_selling_point,
            story_goal,
        )

        normalized_emotion = self._normalize_emotion_stage(emotion_stage)
        emotion_instruction = self.EMOTION_DIRECTION_LIBRARY.get(
            normalized_emotion,
            "Keep the emotional tone natural, credible, and visually restrained.",
        )

        return {
            "story_goal": story_goal,
            "story_purpose": story_purpose,
            "emotion_stage": emotion_stage,
            "normalized_emotion": normalized_emotion,
            "emotion_instruction": emotion_instruction,
            "primary_selling_point": primary_selling_point,
            "review_evidence": review_evidence,
            "must_show": must_show,
            "used": any(
                (story_goal, story_purpose, emotion_stage, primary_selling_point,
                 review_evidence, must_show)
            ),
        }

    def _normalize_emotion_stage(self, value: Any) -> str:
        text = str(value or "").strip().lower()
        mappings = (
            (("curiosity", "hook", "궁금", "호기심"), "curiosity"),
            (("empathy", "공감"), "empathy"),
            (("tension", "긴장", "불안", "문제"), "tension"),
            (("solution", "decision", "해결", "전환"), "solution"),
            (("relief", "안도", "편안"), "relief"),
            (("satisfaction", "만족", "cta", "완료"), "satisfaction"),
        )
        for tokens, normalized in mappings:
            if any(token in text for token in tokens):
                return normalized
        return ""

    def _resolve_director_role(
        self,
        scene: Dict[str, Any],
        scene_type: str,
    ) -> str:
        matched_roles = [
            str(role).strip().lower()
            for role in scene.get("matched_roles") or []
            if str(role).strip()
        ]
        for role in matched_roles:
            if role in self.ROLE_DIRECTION_LIBRARY:
                return role

        return self.SCENE_ROLE_MAP.get(scene_type, "feature")

    def _select_direction_plan(
        self,
        director_role: str,
        requested_motion: str,
        previous_motion: str,
        scene_order: int,
    ) -> Dict[str, Any]:
        role_plan = self.ROLE_DIRECTION_LIBRARY.get(
            director_role,
            self.ROLE_DIRECTION_LIBRARY["feature"],
        )
        candidates = list(role_plan.get("motions") or ["static_hold"])

        if requested_motion in self.MOTION_LIBRARY:
            candidates.insert(0, requested_motion)

        unique_candidates: List[str] = []
        for candidate in candidates:
            if candidate in self.MOTION_LIBRARY and candidate not in unique_candidates:
                unique_candidates.append(candidate)

        if not unique_candidates:
            unique_candidates = ["static_hold"]

        selected_motion = unique_candidates[0]
        reused_prevented = False
        if previous_motion and selected_motion == previous_motion:
            alternative = next(
                (item for item in unique_candidates if item != previous_motion),
                "",
            )
            if alternative:
                selected_motion = alternative
                reused_prevented = True

        diversity_instruction = (
            f"This is scene {max(1, int(scene_order))}. "
            "Do not repeat the immediately previous shot's camera rhythm, framing emphasis, "
            "or visual beat. Alternate between hero, context, detail, and usage emphasis when "
            "the reference images support it. Keep this scene distinct while preserving continuity."
        )

        return {
            "motion": selected_motion,
            "action": str(role_plan.get("action") or "").strip(),
            "shot": str(role_plan.get("shot") or "").strip(),
            "diversity": diversity_instruction,
            "reused_prevented": reused_prevented,
        }

    def _lookup_image(
        self,
        image_path: str,
        filename: str,
        index: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        normalized = self._normalize_path(image_path)

        if normalized and normalized in index:
            return dict(index[normalized])

        if filename and filename.lower() in index:
            return dict(index[filename.lower()])

        return {}

    def _build_visual_context(
        self,
        vision: Dict[str, Any],
        tags: Dict[str, Any],
        scene: Dict[str, Any],
    ) -> str:
        fragments: List[str] = []

        for key in (
            "description",
            "visual_summary",
            "scene_description",
            "product_description",
        ):
            value = str(vision.get(key) or "").strip()
            if value:
                fragments.append(value)
                break

        primary_tag = str(tags.get("primary_tag") or "").strip()
        if primary_tag:
            fragments.append(f"Primary visual tag: {primary_tag}.")

        semantic_tags = [
            str(tag).strip()
            for tag in tags.get("semantic_tags") or []
            if str(tag).strip()
        ]
        if semantic_tags:
            fragments.append(
                "Visible semantic tags: "
                + ", ".join(semantic_tags[:8])
                + "."
            )

        matched_tags = [
            str(tag).strip()
            for tag in scene.get("matched_tags") or []
            if str(tag).strip()
        ]
        if matched_tags:
            fragments.append(
                "Scene emphasis tags: "
                + ", ".join(matched_tags[:5])
                + "."
            )

        if not fragments:
            fragments.append(
                "Use only the visible product, objects, background, lighting, "
                "and composition in the selected reference image."
            )

        return " ".join(fragments)

    def _compose_prompt(
        self,
        scene_id: str,
        scene_type: str,
        product_name: str,
        duration: float,
        style: str,
        goal: str,
        motion_instruction: str,
        transition_instruction: str,
        visual_context: str,
        director_role: str,
        action_instruction: str,
        shot_instruction: str,
        diversity_instruction: str,
        story_context: Dict[str, Any],
    ) -> str:
        product_line = (
            f"Product: {product_name}."
            if product_name
            else "Product: preserve the exact referenced product."
        )

        sections = [
            f"Scene: {scene_id or scene_type}.",
            product_line,
            f"Duration: approximately {duration:.2f} seconds.",
            f"Visual style: {style}.",
            "",
            self.FIRST_FRAME_POLICY,
            self.PRODUCT_IDENTITY_POLICY,
            self.COMPOSITION_POLICY,
            self.CONTINUITY_POLICY,
            "",
            f"Story goal: {story_context.get('story_goal') or goal}",
            f"Story purpose: {story_context.get('story_purpose') or scene_type}.",
            f"Emotion stage: {story_context.get('emotion_stage') or 'natural commercial clarity'}.",
            f"Emotion direction: {story_context.get('emotion_instruction')}",
            f"Must show: {story_context.get('must_show') or 'the visible product benefit supported by the reference image'}.",
            f"Primary selling point: {story_context.get('primary_selling_point') or 'use only visible, supportable product value'}.",
            f"Review evidence context: {story_context.get('review_evidence') or 'No unsupported review claim; show only visible evidence'}.",
            "Do not render these story notes as text. Express them only through camera rhythm, emphasis, and visible action.",
            "",
            f"Director role: {director_role}.",
            f"Scene goal: {goal}",
            f"Shot design: {shot_instruction}",
            f"Natural action direction: {action_instruction}",
            f"Camera direction: {motion_instruction}",
            f"Sequence diversity: {diversity_instruction}",
            f"Ending direction: {transition_instruction}",
            f"Reference-image context: {visual_context}",
            "",
            "Shopping conversion direction: make the product understandable within the first second of this shot.",
            "Keep the product unobstructed and large enough for mobile viewing. Avoid decorative camera movement that hides the feature.",
            "Use only claims and actions supported by the reference image and story context.",
            self.OUTPUT_POLICY,
        ]

        return "\n".join(sections).strip()

    def _compose_negative_prompt(
        self,
        scene_type: str,
        scene: Dict[str, Any],
    ) -> str:
        negatives = list(self.NEGATIVE_BASE)

        if scene_type in {"detail", "feature"}:
            negatives.extend(
                [
                    "invented mechanism",
                    "invented internal structure",
                    "fake texture detail",
                ]
            )

        if scene_type in {"comparison", "proof"}:
            negatives.extend(
                [
                    "invented comparison product",
                    "fake before and after",
                    "unsupported performance claim",
                ]
            )

        if scene_type == "installation":
            negatives.extend(
                [
                    "invented installation step",
                    "invented tool",
                    "invented component",
                ]
            )

        unique: List[str] = []
        for item in negatives:
            normalized = str(item).strip()
            if normalized and normalized not in unique:
                unique.append(normalized)

        return ", ".join(unique)

    def _normalize_duration(self, value: Any) -> float:
        try:
            duration = float(value)
        except Exception:
            duration = 3.0

        return round(min(8.0, max(1.5, duration)), 2)

    def _normalize_path(self, value: Any) -> str:
        raw = str(value or "").strip()
        if not raw:
            return ""

        return raw.replace("\\", "/").lower()

    def _prompt_filename(self, scene_id: str) -> str:
        safe = re.sub(r"[^a-zA-Z0-9_-]+", "_", scene_id or "scene")
        return f"{safe}_prompt.txt"

    def _build_summary(
        self,
        scenes: Sequence[Dict[str, Any]],
    ) -> Dict[str, Any]:
        ready_scenes = [
            scene
            for scene in scenes
            if scene.get("ready")
        ]

        durations = [
            float(scene.get("duration_seconds") or 0.0)
            for scene in ready_scenes
        ]

        motion_counts: Dict[str, int] = {}
        role_counts: Dict[str, int] = {}
        prevented_count = 0
        story_context_count = 0
        emotion_counts: Dict[str, int] = {}
        for scene in ready_scenes:
            motion = str(scene.get("camera_motion") or "unknown")
            role = str(scene.get("director_role") or "unknown")
            motion_counts[motion] = motion_counts.get(motion, 0) + 1
            role_counts[role] = role_counts.get(role, 0) + 1
            if scene.get("motion_reused_prevented"):
                prevented_count += 1
            if scene.get("story_context_used"):
                story_context_count += 1
            emotion = str(scene.get("emotion_stage") or "").strip()
            if emotion:
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        return {
            "scene_count": len(scenes),
            "ready_scene_count": len(ready_scenes),
            "not_ready_scene_count": len(scenes) - len(ready_scenes),
            "total_duration_seconds": round(sum(durations), 2),
            "prompt_count": len(ready_scenes),
            "director_version": self.VERSION,
            "motion_counts": motion_counts,
            "role_counts": role_counts,
            "unique_motion_count": len(motion_counts),
            "consecutive_motion_prevented_count": prevented_count,
            "story_aware": True,
            "story_context_count": story_context_count,
            "emotion_counts": emotion_counts,
            "all_first_frame_locked": all(
                bool(scene.get("first_frame_policy"))
                for scene in ready_scenes
            ),
            "all_product_identity_locked": all(
                bool(scene.get("product_identity_policy"))
                for scene in ready_scenes
            ),
            "manifest_ready": len(ready_scenes) == len(scenes),
            "next_step": "Sprint93-6B Director Manifest Writer",
        }

    def _first_non_empty(self, *values: Any) -> str:
        for value in values:
            text = str(value or "").strip()
            if text:
                return text
        return ""