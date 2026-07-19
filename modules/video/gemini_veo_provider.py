from __future__ import annotations

import copy
import hashlib
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional


class GeminiVeoProvider:
    """
    Sprint92-1 Gemini Veo Multi-Scene Image-to-Video Provider

    역할:
    - AIVideoEngine 표준 요청을 Gemini Veo API 요청으로 변환
    - 텍스트→영상과 상품 대표 이미지→영상 모두 지원
    - reference_image_path가 있으면 첫 프레임 이미지로 사용
    - 상품 외형 보존 지시를 프롬프트에 자동 보강
    - 장면별 4/6/8초 영상을 생성하고 로컬 MP4로 저장
    - 공급자 오류를 장면별 결과로 반환하여 Workflow 전체 중단 방지

    환경 변수:
    - GEMINI_API_KEY: 필수
    - GEMINI_VEO_MODEL: 선택, 기본 veo-3.1-fast-generate-preview
    - GEMINI_VEO_RESOLUTION: 선택, 기본 720p
    - GEMINI_VEO_POLL_SECONDS: 선택, 기본 10
    - GEMINI_VEO_TIMEOUT_SECONDS: 선택, 기본 420
    """

    VERSION = "gemini-veo-provider-109-3"
    PROVIDER_NAME = "gemini_veo"
    DEFAULT_MODEL = "veo-3.1-fast-generate-preview"
    DEFAULT_RESOLUTION = "720p"
    DEFAULT_POLL_SECONDS = 10
    DEFAULT_TIMEOUT_SECONDS = 420
    SUPPORTED_DURATIONS = (4, 6, 8)
    SUPPORTED_ASPECT_RATIOS = {"9:16", "16:9"}
    SUPPORTED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
    MAX_SCENES_PER_REQUEST = 6

    PRODUCT_LOCK_PROMPT = (
        "Use the supplied product image as the exact first frame and primary visual "
        "reference. Preserve the exact same product identity throughout the entire shot: "
        "same color, shell pattern, proportions, corners, handle, zipper, wheels, seams, "
        "surface texture, accessories, and visible design details. Animate only the requested "
        "movement. Do not redesign, replace, restyle, simplify, embellish, or morph the product. "
        "Do not introduce a different model or a similar-looking substitute."
    )

    DEFAULT_NEGATIVE_PROMPT = (
        "different product, redesigned product, changed color, changed shell pattern, changed "
        "handle, changed wheels, extra wheels, missing wheels, extra handles, duplicate product, "
        "warped geometry, morphing, deformed hands, subtitles, captions, text, watermark, logo "
        "distortion, scene cuts, camera shake"
    )

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        resolution: Optional[str] = None,
        poll_seconds: Optional[int] = None,
        timeout_seconds: Optional[int] = None,
    ) -> None:
        self.api_key = self._clean_text(api_key or os.getenv("GEMINI_API_KEY"))
        self.model = self._clean_text(
            model or os.getenv("GEMINI_VEO_MODEL") or self.DEFAULT_MODEL
        )
        self.resolution = self._clean_text(
            resolution or os.getenv("GEMINI_VEO_RESOLUTION") or self.DEFAULT_RESOLUTION
        )
        self.poll_seconds = self._positive_int(
            poll_seconds or os.getenv("GEMINI_VEO_POLL_SECONDS"),
            self.DEFAULT_POLL_SECONDS,
        )
        self.timeout_seconds = self._positive_int(
            timeout_seconds or os.getenv("GEMINI_VEO_TIMEOUT_SECONDS"),
            self.DEFAULT_TIMEOUT_SECONDS,
        )
        self.disabled = self._truthy(os.getenv("GEMINI_VEO_DISABLED"))

    def readiness(self) -> Dict[str, Any]:
        errors: List[str] = []
        if self.disabled:
            return {
                "ok": False,
                "ready": False,
                "provider": self.PROVIDER_NAME,
                "provider_version": self.VERSION,
                "model": self.model,
                "resolution": self.resolution,
                "api_key_configured": bool(self.api_key),
                "supports_text_to_video": True,
                "supports_image_to_video": True,
                "disabled": True,
                "status": "disabled",
                "errors": ["Gemini Veo disabled by GEMINI_VEO_DISABLED"],
            }
        if not self.api_key:
            errors.append("GEMINI_API_KEY is not configured")
        try:
            import google.genai  # type: ignore  # noqa: F401
        except Exception:
            errors.append("google-genai package is not installed")

        return {
            "ok": not errors,
            "ready": not errors,
            "provider": self.PROVIDER_NAME,
            "provider_version": self.VERSION,
            "model": self.model,
            "resolution": self.resolution,
            "api_key_configured": bool(self.api_key),
            "supports_text_to_video": True,
            "supports_image_to_video": True,
            "disabled": False,
            "status": "ready" if not errors else "not_ready",
            "errors": errors,
        }

    def generate(self, request: Mapping[str, Any]) -> Dict[str, Any]:
        normalized_request = copy.deepcopy(dict(request or {}))
        request_disabled = self._request_disables_veo(normalized_request)
        if self.disabled or request_disabled:
            disabled_by = (
                "GEMINI_VEO_DISABLED"
                if self.disabled
                else "request.veo_enabled=false"
            )
            print(
                f"[Sprint109-3 Veo Guard] Status: disabled ({disabled_by})",
                flush=True,
            )
            return self._result(
                request=normalized_request,
                ok=False,
                status="disabled",
                errors=[f"Gemini Veo disabled by {disabled_by}"],
            )

        readiness = self.readiness()
        if not readiness["ready"]:
            return self._result(
                request=normalized_request,
                ok=False,
                status="not_ready",
                errors=list(readiness["errors"]),
            )

        scenes = normalized_request.get("scenes") or []
        if not isinstance(scenes, list) or not scenes:
            return self._result(
                request=normalized_request,
                ok=False,
                status="invalid_request",
                errors=["at least one scene is required"],
            )

        if len(scenes) > self.MAX_SCENES_PER_REQUEST:
            return self._result(
                request=normalized_request,
                ok=False,
                status="too_many_scenes",
                errors=[
                    f"scene count {len(scenes)} exceeds maximum "
                    f"{self.MAX_SCENES_PER_REQUEST}"
                ],
            )

        output_dir = Path(
            self._clean_text(normalized_request.get("output_dir"))
            or (Path("exports") / "ai_videos" / "unknown")
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            from google import genai
        except Exception as exc:
            return self._result(
                request=normalized_request,
                ok=False,
                status="sdk_import_error",
                errors=[f"{type(exc).__name__}: {exc}"],
            )

        client = genai.Client(api_key=self.api_key)
        generated_files: List[str] = []
        scene_results: List[Dict[str, Any]] = []
        errors: List[str] = []

        for index, scene in enumerate(scenes, start=1):
            scene_id = self._clean_text(
                scene.get("scene_id") if isinstance(scene, Mapping) else ""
            ) or f"scene_{index:02d}"
            print(
                f"[Sprint92-1 Veo] Scene {index}/{len(scenes)} Start: {scene_id}",
                flush=True,
            )
            scene_result = self._generate_scene(
                client=client,
                request=normalized_request,
                scene=scene if isinstance(scene, Mapping) else {},
                index=index,
                output_dir=output_dir,
            )
            scene_results.append(scene_result)
            print(
                f"[Sprint92-1 Veo] Scene {index}/{len(scenes)} Status: "
                f"{scene_result.get('status')}",
                flush=True,
            )
            if scene_result.get("ok") and scene_result.get("output_path"):
                generated_files.append(str(scene_result["output_path"]))
            else:
                errors.extend(scene_result.get("errors") or [])

        all_generated = bool(scene_results) and len(generated_files) == len(scene_results)
        partial_generated = bool(generated_files) and not all_generated
        status = (
            "generated"
            if all_generated
            else "partially_generated"
            if partial_generated
            else "generation_failed"
        )

        return self._result(
            request=normalized_request,
            ok=all_generated,
            status=status,
            generated_files=generated_files,
            scene_results=scene_results,
            errors=errors,
        )

    def _generate_scene(
        self,
        *,
        client: Any,
        request: Mapping[str, Any],
        scene: Mapping[str, Any],
        index: int,
        output_dir: Path,
    ) -> Dict[str, Any]:
        scene_id = self._clean_text(scene.get("scene_id")) or f"scene_{index:02d}"
        duration_seconds = self._normalize_duration(scene.get("duration_seconds"))
        aspect_ratio = self._normalize_aspect_ratio(
            scene.get("aspect_ratio") or request.get("aspect_ratio")
        )
        reference_image_path = self._clean_text(scene.get("reference_image_path"))
        image_info = self._validate_reference_image(reference_image_path)
        input_mode = "image_to_video" if reference_image_path else "text_to_video"
        prompt = self._build_prompt(
            request=request,
            scene=scene,
            image_to_video=bool(reference_image_path),
        )
        output_path = output_dir / f"{scene_id}.mp4"

        if not prompt:
            return self._scene_result(
                scene_id=scene_id,
                ok=False,
                status="invalid_prompt",
                input_mode=input_mode,
                errors=[f"{scene_id}: prompt is required"],
            )
        if reference_image_path and not image_info["ok"]:
            return self._scene_result(
                scene_id=scene_id,
                ok=False,
                status=image_info["status"],
                input_mode=input_mode,
                reference_image_path=reference_image_path,
                errors=[f"{scene_id}: {image_info['error']}"],
            )

        try:
            from google.genai import types

            config_kwargs: Dict[str, Any] = {
                "aspect_ratio": aspect_ratio,
                "resolution": self.resolution,
                "duration_seconds": duration_seconds,
                "number_of_videos": 1,
            }
            negative_prompt = self._build_negative_prompt(scene)
            if negative_prompt:
                config_kwargs["negative_prompt"] = negative_prompt
            seed = scene.get("seed")
            if isinstance(seed, int):
                config_kwargs["seed"] = seed

            image = None
            if reference_image_path:
                image = types.Image.from_file(location=reference_image_path)

            operation = client.models.generate_videos(
                model=self.model,
                prompt=prompt,
                image=image,
                config=types.GenerateVideosConfig(**config_kwargs),
            )

            started_at = time.monotonic()
            while not operation.done:
                if time.monotonic() - started_at >= self.timeout_seconds:
                    return self._scene_result(
                        scene_id=scene_id,
                        ok=False,
                        status="timeout",
                        input_mode=input_mode,
                        operation_name=self._clean_text(getattr(operation, "name", "")),
                        reference_image_path=reference_image_path,
                        reference_image_sha256=image_info.get("sha256", ""),
                        errors=[
                            f"{scene_id}: generation timed out after "
                            f"{self.timeout_seconds} seconds"
                        ],
                    )
                time.sleep(self.poll_seconds)
                operation = client.operations.get(operation)

            response = getattr(operation, "response", None)
            generated_videos = getattr(response, "generated_videos", None) or []
            if not generated_videos:
                return self._scene_result(
                    scene_id=scene_id,
                    ok=False,
                    status="empty_response",
                    input_mode=input_mode,
                    operation_name=self._clean_text(getattr(operation, "name", "")),
                    reference_image_path=reference_image_path,
                    reference_image_sha256=image_info.get("sha256", ""),
                    errors=[f"{scene_id}: Veo returned no generated video"],
                )

            video_file = getattr(generated_videos[0], "video", None)
            if video_file is None:
                return self._scene_result(
                    scene_id=scene_id,
                    ok=False,
                    status="missing_video_file",
                    input_mode=input_mode,
                    operation_name=self._clean_text(getattr(operation, "name", "")),
                    reference_image_path=reference_image_path,
                    reference_image_sha256=image_info.get("sha256", ""),
                    errors=[f"{scene_id}: generated video file is missing"],
                )

            client.files.download(file=video_file)
            video_file.save(str(output_path))
            if not output_path.is_file() or output_path.stat().st_size <= 0:
                return self._scene_result(
                    scene_id=scene_id,
                    ok=False,
                    status="save_failed",
                    input_mode=input_mode,
                    operation_name=self._clean_text(getattr(operation, "name", "")),
                    reference_image_path=reference_image_path,
                    reference_image_sha256=image_info.get("sha256", ""),
                    errors=[f"{scene_id}: generated file was not saved"],
                )

            return self._scene_result(
                scene_id=scene_id,
                ok=True,
                status="generated",
                input_mode=input_mode,
                output_path=str(output_path),
                operation_name=self._clean_text(getattr(operation, "name", "")),
                duration_seconds=duration_seconds,
                aspect_ratio=aspect_ratio,
                prompt=prompt,
                reference_image_path=reference_image_path,
                reference_image_sha256=image_info.get("sha256", ""),
            )
        except Exception as exc:
            return self._scene_result(
                scene_id=scene_id,
                ok=False,
                status="provider_error",
                input_mode=input_mode,
                reference_image_path=reference_image_path,
                reference_image_sha256=image_info.get("sha256", ""),
                errors=[f"{scene_id}: {type(exc).__name__}: {exc}"],
            )

    def _build_prompt(
        self,
        *,
        request: Mapping[str, Any],
        scene: Mapping[str, Any],
        image_to_video: bool,
    ) -> str:
        parts: List[str] = []
        product_name = self._clean_text(request.get("product_name"))
        prompt = self._clean_text(scene.get("prompt"))
        if product_name:
            parts.append(f"Product: {product_name}.")
        if image_to_video:
            parts.append(self.PRODUCT_LOCK_PROMPT)
        if prompt:
            parts.append(prompt)

        metadata = scene.get("metadata")
        if isinstance(metadata, Mapping):
            for label, key in (("Camera", "camera"), ("Lighting", "lighting"), ("Style", "style")):
                value = self._clean_text(metadata.get(key))
                if value:
                    parts.append(f"{label}: {value}.")

        parts.append(
            "One continuous realistic product shot with clean composition. No subtitles, "
            "no captions, no text overlays, no watermark, and no logo distortion."
        )
        return " ".join(part.strip() for part in parts if part.strip())

    def _build_negative_prompt(self, scene: Mapping[str, Any]) -> str:
        custom = self._clean_text(scene.get("negative_prompt"))
        if not custom:
            return self.DEFAULT_NEGATIVE_PROMPT
        return f"{self.DEFAULT_NEGATIVE_PROMPT}, {custom}"

    def _validate_reference_image(self, raw_path: str) -> Dict[str, Any]:
        if not raw_path:
            return {"ok": True, "status": "not_used", "error": "", "sha256": ""}
        path = Path(raw_path)
        if not path.is_file():
            return {
                "ok": False,
                "status": "reference_image_not_found",
                "error": f"reference image not found: {path}",
                "sha256": "",
            }
        if path.suffix.lower() not in self.SUPPORTED_IMAGE_SUFFIXES:
            return {
                "ok": False,
                "status": "unsupported_reference_image",
                "error": f"unsupported reference image type: {path.suffix}",
                "sha256": "",
            }
        if path.stat().st_size <= 0:
            return {
                "ok": False,
                "status": "empty_reference_image",
                "error": f"reference image is empty: {path}",
                "sha256": "",
            }
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return {"ok": True, "status": "valid", "error": "", "sha256": digest}

    def _result(
        self,
        *,
        request: Mapping[str, Any],
        ok: bool,
        status: str,
        generated_files: Optional[List[str]] = None,
        scene_results: Optional[List[Dict[str, Any]]] = None,
        errors: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        return {
            "ok": bool(ok),
            "ready": bool(ok),
            "provider": self.PROVIDER_NAME,
            "provider_version": self.VERSION,
            "model": self.model,
            "resolution": self.resolution,
            "status": status,
            "project_id": self._clean_text(request.get("project_id")),
            "run_id": self._clean_text(request.get("run_id")),
            "scene_count": len(request.get("scenes") or []),
            "generated_files": list(generated_files or []),
            "scene_results": list(scene_results or []),
            "output_dir": self._clean_text(request.get("output_dir")),
            "errors": list(errors or []),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

    def _scene_result(self, *, scene_id: str, ok: bool, status: str, **kwargs: Any) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "scene_id": scene_id,
            "ok": bool(ok),
            "status": status,
            "input_mode": self._clean_text(kwargs.pop("input_mode", "text_to_video")),
            "output_path": self._clean_text(kwargs.pop("output_path", "")),
            "operation_name": self._clean_text(kwargs.pop("operation_name", "")),
            "duration_seconds": int(kwargs.pop("duration_seconds", 0) or 0),
            "aspect_ratio": self._clean_text(kwargs.pop("aspect_ratio", "")),
            "prompt": self._clean_text(kwargs.pop("prompt", "")),
            "reference_image_path": self._clean_text(kwargs.pop("reference_image_path", "")),
            "reference_image_sha256": self._clean_text(kwargs.pop("reference_image_sha256", "")),
            "errors": list(kwargs.pop("errors", []) or []),
        }
        result.update(kwargs)
        return result

    def _normalize_duration(self, value: Any) -> int:
        try:
            duration = int(value)
        except (TypeError, ValueError):
            duration = 6
        return min(self.SUPPORTED_DURATIONS, key=lambda item: abs(item - duration))

    def _normalize_aspect_ratio(self, value: Any) -> str:
        ratio = self._clean_text(value) or "9:16"
        return ratio if ratio in self.SUPPORTED_ASPECT_RATIOS else "9:16"

    @classmethod
    def _request_disables_veo(cls, request: Mapping[str, Any]) -> bool:
        if "veo_enabled" not in request:
            return False
        value = request.get("veo_enabled")
        if isinstance(value, bool):
            return not value
        text = cls._clean_text(value).lower()
        return text in {"0", "false", "no", "off", "disabled"}

    @staticmethod
    def _truthy(value: Any) -> bool:
        return str(value or "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
            "enabled",
        }

    @staticmethod
    def _positive_int(value: Any, default: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return default
        return parsed if parsed > 0 else default

    @staticmethod
    def _clean_text(value: Any) -> str:
        return str(value or "").strip()


if __name__ == "__main__":
    import json

    print(json.dumps(GeminiVeoProvider().readiness(), ensure_ascii=False, indent=2))