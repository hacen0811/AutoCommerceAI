from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence


class GeminiDirector:
    """
    Sprint93-6A Gemini Director Core

    역할:
    - Sprint93-5 scene_selection.json을 입력받음
    - 선택된 제품 이미지와 장면 목적을 Gemini/Veo용 프롬프트로 변환
    - 첫 프레임 유지, 제품 재해석 금지, 카메라 연출, 전환, 연속성 규칙 생성
    - 장면별 prompt / negative_prompt / policy를 구성
    - Sprint93-6B 저장 단계에서 사용할 director_manifest 구조 반환

    이 단계는 API 호출을 수행하지 않는다.
    """

    VERSION = "gemini-director-93-6a"

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
        "Create a vertical 9:16 video. Keep the product sharp, realistic, stable, "
        "and commercially presentable. No subtitles, no captions, no graphic text, "
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

        for scene in scenes:
            if not isinstance(scene, dict):
                continue

            directed_scene = self._direct_scene(
                scene=scene,
                vision_index=vision_index,
                tag_index=tag_index,
                product_name=result["product_name"],
                style=result["style"],
                language=result["language"],
            )
            directed_scenes.append(directed_scene)

        ready_count = sum(
            1
            for scene in directed_scenes
            if scene.get("ready")
        )

        result["scenes"] = directed_scenes
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
        motion_key = str(scene.get("motion") or "static_hold").strip()
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
        goal = self.GOAL_LIBRARY.get(
            scene_type,
            str(scene.get("purpose") or "").strip()
            or self.GOAL_LIBRARY["feature"],
        )
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
            "title": str(scene.get("title") or "").strip(),
            "goal": goal,
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
            f"Scene goal: {goal}",
            f"Camera direction: {motion_instruction}",
            f"Ending direction: {transition_instruction}",
            f"Reference-image context: {visual_context}",
            "",
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

        return {
            "scene_count": len(scenes),
            "ready_scene_count": len(ready_scenes),
            "not_ready_scene_count": len(scenes) - len(ready_scenes),
            "total_duration_seconds": round(sum(durations), 2),
            "prompt_count": len(ready_scenes),
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