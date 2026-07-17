from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Protocol, Sequence


class AIVideoProvider(Protocol):
    """AI 영상 공급자 공통 규격."""

    VERSION: str
    PROVIDER_NAME: str

    def generate(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        """정규화된 생성 요청을 받아 공급자별 결과를 반환한다."""


@dataclass(frozen=True)
class VideoScene:
    """AI 영상 한 장면의 생성 정보."""

    scene_id: str
    prompt: str
    duration_seconds: int = 6
    negative_prompt: str = ""
    reference_image_path: str = ""
    aspect_ratio: str = "9:16"
    seed: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "prompt": self.prompt,
            "duration_seconds": self.duration_seconds,
            "negative_prompt": self.negative_prompt,
            "reference_image_path": self.reference_image_path,
            "aspect_ratio": self.aspect_ratio,
            "seed": self.seed,
            "metadata": copy.deepcopy(self.metadata),
        }


class AIVideoEngine:
    """
    Sprint92-1 AI Video Engine

    역할:
    - Gemini Veo, Kling, Runway 등 공급자를 교체 가능한 구조로 관리
    - 상품·대본·장면 정보를 표준 생성 요청으로 정규화
    - 실제 공급자 연결 전에도 dry-run 생성 계획을 반환
    - 원본 입력을 변경하지 않고 독립적으로 동작
    """

    VERSION = "ai-video-engine-92-1"
    DEFAULT_PROVIDER = "gemini_veo"
    DEFAULT_ASPECT_RATIO = "9:16"
    DEFAULT_SCENE_DURATION = 6
    MIN_SCENE_DURATION = 3
    MAX_SCENE_DURATION = 8
    DEFAULT_OUTPUT_ROOT = Path("exports") / "ai_videos"
    DEFAULT_MULTI_SCENE_COUNT = 6
    MAX_MULTI_SCENE_COUNT = 6

    SCENE_BLUEPRINTS = (
        {
            "scene_type": "hero",
            "prompt": (
                "Begin from the supplied product image. Present the exact product as a premium "
                "hero shot. Use a slow, stable camera push-in and subtle natural product movement "
                "in a clean Korean home-shopping setting."
            ),
            "camera": "slow stable push-in",
            "lighting": "soft daylight",
        },
        {
            "scene_type": "interaction",
            "prompt": (
                "Begin from the supplied product image. A realistic person's hand gently touches, "
                "holds, opens, slides, or demonstrates the product according to its visible design. "
                "Keep the action small and physically plausible."
            ),
            "camera": "medium close product demonstration",
            "lighting": "bright natural indoor light",
        },
        {
            "scene_type": "benefit",
            "prompt": (
                "Begin from the supplied product image. Demonstrate the product's main practical "
                "benefit in a realistic everyday Korean home environment without changing the product."
            ),
            "camera": "stable three-quarter view",
            "lighting": "clean commercial daylight",
        },
        {
            "scene_type": "space_solution",
            "prompt": (
                "Begin from the supplied product image. Show the exact product being positioned or "
                "used neatly in an appropriate compact living space, emphasizing organization and convenience."
            ),
            "camera": "wide-to-medium continuous shot",
            "lighting": "soft interior daylight",
        },
        {
            "scene_type": "detail",
            "prompt": (
                "Begin from the supplied product image. Create a realistic close-up detail shot that "
                "highlights the visible material, texture, edges, joints, wheels, handle, zipper, surface, "
                "or other actual product details. Do not invent unseen features."
            ),
            "camera": "slow macro detail move",
            "lighting": "soft directional product light",
        },
        {
            "scene_type": "ending",
            "prompt": (
                "Begin from the supplied product image. Finish with the exact product neatly placed and "
                "fully visible in a satisfying premium closing shot. Use gentle camera movement and no text."
            ),
            "camera": "slow pull-back ending shot",
            "lighting": "warm clean commercial light",
        },
    )

    def __init__(
        self,
        providers: Optional[Mapping[str, AIVideoProvider]] = None,
        output_root: Any = None,
    ) -> None:
        self._providers: Dict[str, AIVideoProvider] = {}
        self.output_root = Path(output_root or self.DEFAULT_OUTPUT_ROOT)

        for name, provider in dict(providers or {}).items():
            self.register_provider(name, provider)

    def register_provider(self, name: str, provider: AIVideoProvider) -> None:
        provider_name = self._clean_text(name).lower()
        if not provider_name:
            raise ValueError("provider name is required")
        if provider is None or not callable(getattr(provider, "generate", None)):
            raise TypeError("provider must implement generate(request)")
        self._providers[provider_name] = provider

    def available_providers(self) -> List[str]:
        return sorted(self._providers.keys())

    def plan_multi_scenes(
        self,
        *,
        product_name: Any,
        reference_image_path: Any,
        scene_count: Any = DEFAULT_MULTI_SCENE_COUNT,
        duration_seconds: Any = DEFAULT_SCENE_DURATION,
        aspect_ratio: Any = DEFAULT_ASPECT_RATIO,
        product_context: Any = "",
    ) -> List[Dict[str, Any]]:
        """대표 이미지 한 장을 공통 기준으로 사용하는 6개 상품 장면을 계획합니다."""
        name = self._clean_text(product_name) or "선택 상품"
        reference = self._clean_text(reference_image_path)
        context = self._clean_text(product_context)
        try:
            count = int(scene_count)
        except (TypeError, ValueError):
            count = self.DEFAULT_MULTI_SCENE_COUNT
        count = max(1, min(self.MAX_MULTI_SCENE_COUNT, count))
        duration = self._normalize_duration(duration_seconds)
        ratio = self._clean_text(aspect_ratio) or self.DEFAULT_ASPECT_RATIO

        scenes: List[Dict[str, Any]] = []
        for index, blueprint in enumerate(self.SCENE_BLUEPRINTS[:count], start=1):
            prompt_parts = [
                f"Product name: {name}.",
                self._clean_text(blueprint.get("prompt")),
            ]
            if context:
                prompt_parts.append(
                    f"Use this product context only when visually plausible: {context}."
                )
            scenes.append(
                {
                    "scene_id": f"scene_{index:02d}",
                    "prompt": " ".join(part for part in prompt_parts if part),
                    "duration_seconds": duration,
                    "aspect_ratio": ratio,
                    "reference_image_path": reference,
                    "metadata": {
                        "scene_index": index,
                        "scene_type": self._clean_text(blueprint.get("scene_type")),
                        "camera": self._clean_text(blueprint.get("camera")),
                        "lighting": self._clean_text(blueprint.get("lighting")),
                        "style": "realistic Korean social-commerce product video",
                        "planner_version": self.VERSION,
                    },
                }
            )
        return scenes

    def build_request(
        self,
        *,
        project_id: Any,
        product_name: Any,
        scenes: Any = None,
        script: Any = "",
        provider: Any = DEFAULT_PROVIDER,
        aspect_ratio: Any = DEFAULT_ASPECT_RATIO,
        reference_images: Any = None,
        output_dir: Any = "",
        metadata: Any = None,
    ) -> Dict[str, Any]:
        normalized_project_id = self._clean_text(project_id)
        normalized_product_name = self._clean_text(product_name)
        normalized_provider = self._clean_text(provider).lower() or self.DEFAULT_PROVIDER
        normalized_aspect_ratio = self._clean_text(aspect_ratio) or self.DEFAULT_ASPECT_RATIO

        errors: List[str] = []
        if not normalized_project_id:
            errors.append("project_id is required")
        if not normalized_product_name:
            errors.append("product_name is required")
        if normalized_aspect_ratio not in {"9:16", "16:9", "1:1", "4:5"}:
            errors.append("unsupported aspect_ratio")

        normalized_scenes = self._normalize_scenes(
            scenes=scenes,
            script=script,
            aspect_ratio=normalized_aspect_ratio,
            reference_images=reference_images,
        )
        if not normalized_scenes:
            errors.append("at least one scene is required")

        run_id = self._make_run_id(
            project_id=normalized_project_id,
            product_name=normalized_product_name,
            scenes=normalized_scenes,
        )

        resolved_output_dir = Path(output_dir) if self._clean_text(output_dir) else (
            self.output_root / normalized_project_id / run_id
        )

        request = {
            "ok": not errors,
            "engine_version": self.VERSION,
            "provider": normalized_provider,
            "project_id": normalized_project_id,
            "product_name": normalized_product_name,
            "aspect_ratio": normalized_aspect_ratio,
            "scene_count": len(normalized_scenes),
            "scenes": [scene.to_dict() for scene in normalized_scenes],
            "reference_images": self._normalize_paths(reference_images),
            "output_dir": str(resolved_output_dir),
            "run_id": run_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": copy.deepcopy(metadata) if isinstance(metadata, Mapping) else {},
            "errors": errors,
        }
        return request

    def generate(
        self,
        request: Any,
        *,
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        normalized_request = copy.deepcopy(request) if isinstance(request, Mapping) else {}
        errors = list(normalized_request.get("errors") or [])

        if not normalized_request or not normalized_request.get("ok"):
            return self._result(
                request=normalized_request,
                status="invalid_request",
                ready=False,
                dry_run=dry_run,
                errors=errors or ["valid request is required"],
            )

        provider_name = self._clean_text(normalized_request.get("provider")).lower()

        if dry_run:
            output_dir = Path(self._clean_text(normalized_request.get("output_dir")))
            planned_outputs = [
                str(output_dir / f"{scene.get('scene_id', f'scene_{index:02d}')}.mp4")
                for index, scene in enumerate(normalized_request.get("scenes") or [], start=1)
            ]
            return self._result(
                request=normalized_request,
                status="planned",
                ready=True,
                dry_run=True,
                generated_files=[],
                planned_outputs=planned_outputs,
                provider=provider_name,
            )

        provider = self._providers.get(provider_name)
        if provider is None:
            return self._result(
                request=normalized_request,
                status="provider_not_registered",
                ready=False,
                dry_run=False,
                provider=provider_name,
                errors=[f"provider is not registered: {provider_name}"],
            )

        try:
            provider_result = dict(provider.generate(copy.deepcopy(normalized_request)) or {})
        except Exception as exc:  # 공급자 오류가 Workflow 전체를 깨지 않도록 결과화
            return self._result(
                request=normalized_request,
                status="provider_error",
                ready=False,
                dry_run=False,
                provider=provider_name,
                errors=[f"{type(exc).__name__}: {exc}"],
            )

        generated_files = self._normalize_paths(
            provider_result.get("generated_files")
            or provider_result.get("video_paths")
            or provider_result.get("output_files")
        )
        provider_ok = bool(provider_result.get("ok", generated_files))
        status = self._clean_text(provider_result.get("status")) or (
            "generated" if provider_ok else "generation_failed"
        )

        return self._result(
            request=normalized_request,
            status=status,
            ready=provider_ok,
            dry_run=False,
            generated_files=generated_files,
            provider=provider_name,
            provider_version=self._clean_text(getattr(provider, "VERSION", "")),
            provider_result=provider_result,
            errors=list(provider_result.get("errors") or []),
        )

    def save_request(self, request: Mapping[str, Any]) -> Dict[str, Any]:
        output_dir = Path(self._clean_text(request.get("output_dir")))
        if not output_dir:
            return {"saved": False, "path": "", "error": "output_dir is required"}

        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            path = output_dir / "request.json"
            path.write_text(
                json.dumps(dict(request), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return {"saved": True, "path": str(path), "error": ""}
        except Exception as exc:
            return {
                "saved": False,
                "path": "",
                "error": f"{type(exc).__name__}: {exc}",
            }

    def _normalize_scenes(
        self,
        *,
        scenes: Any,
        script: Any,
        aspect_ratio: str,
        reference_images: Any,
    ) -> List[VideoScene]:
        raw_scenes: List[Any]
        if isinstance(scenes, Sequence) and not isinstance(scenes, (str, bytes)):
            raw_scenes = list(scenes)
        elif isinstance(scenes, Mapping):
            raw_scenes = [scenes]
        else:
            raw_scenes = []

        if not raw_scenes:
            raw_scenes = self._scenes_from_script(script)

        normalized_references = self._normalize_paths(reference_images)
        result: List[VideoScene] = []

        for index, raw in enumerate(raw_scenes, start=1):
            if isinstance(raw, Mapping):
                prompt = self._clean_text(
                    raw.get("prompt")
                    or raw.get("description")
                    or raw.get("scene")
                    or raw.get("text")
                )
                duration = self._normalize_duration(raw.get("duration_seconds", raw.get("duration")))
                scene_id = self._clean_text(raw.get("scene_id")) or f"scene_{index:02d}"
                negative_prompt = self._clean_text(raw.get("negative_prompt"))
                reference_image = self._clean_text(raw.get("reference_image_path"))
                seed = raw.get("seed") if isinstance(raw.get("seed"), int) else None
                scene_metadata = copy.deepcopy(raw.get("metadata")) if isinstance(raw.get("metadata"), Mapping) else {}
            else:
                prompt = self._clean_text(raw)
                duration = self.DEFAULT_SCENE_DURATION
                scene_id = f"scene_{index:02d}"
                negative_prompt = ""
                reference_image = ""
                seed = None
                scene_metadata = {}

            if not prompt:
                continue
            if not reference_image and normalized_references:
                reference_image = (
                    normalized_references[index - 1]
                    if index <= len(normalized_references)
                    else normalized_references[0]
                )

            result.append(
                VideoScene(
                    scene_id=scene_id,
                    prompt=prompt,
                    duration_seconds=duration,
                    negative_prompt=negative_prompt,
                    reference_image_path=reference_image,
                    aspect_ratio=aspect_ratio,
                    seed=seed,
                    metadata=scene_metadata,
                )
            )

        return result

    def _scenes_from_script(self, script: Any) -> List[str]:
        text = self._clean_text(script)
        if not text:
            return []

        lines = [line.strip(" -\t") for line in text.splitlines() if line.strip(" -\t")]
        if len(lines) > 1:
            return lines[:10]

        sentences = [part.strip() for part in text.replace("!", ".").replace("?", ".").split(".")]
        return [sentence for sentence in sentences if sentence][:10]

    def _normalize_duration(self, value: Any) -> int:
        try:
            duration = int(float(value))
        except (TypeError, ValueError):
            duration = self.DEFAULT_SCENE_DURATION
        return max(self.MIN_SCENE_DURATION, min(self.MAX_SCENE_DURATION, duration))

    def _make_run_id(
        self,
        *,
        project_id: str,
        product_name: str,
        scenes: Iterable[VideoScene],
    ) -> str:
        payload = {
            "project_id": project_id,
            "product_name": product_name,
            "scenes": [scene.to_dict() for scene in scenes],
        }
        digest = hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        return digest[:12]

    def _result(
        self,
        *,
        request: Mapping[str, Any],
        status: str,
        ready: bool,
        dry_run: bool,
        provider: str = "",
        generated_files: Any = None,
        planned_outputs: Any = None,
        provider_version: str = "",
        provider_result: Any = None,
        errors: Any = None,
    ) -> Dict[str, Any]:
        return {
            "ok": bool(ready),
            "ready": bool(ready),
            "engine_version": self.VERSION,
            "provider": provider or self._clean_text(request.get("provider")),
            "provider_version": provider_version,
            "status": status,
            "dry_run": bool(dry_run),
            "project_id": self._clean_text(request.get("project_id")),
            "run_id": self._clean_text(request.get("run_id")),
            "scene_count": len(request.get("scenes") or []),
            "generated_files": self._normalize_paths(generated_files),
            "planned_outputs": self._normalize_paths(planned_outputs),
            "output_dir": self._clean_text(request.get("output_dir")),
            "provider_result": copy.deepcopy(provider_result) if isinstance(provider_result, Mapping) else {},
            "errors": list(errors or []),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _clean_text(value: Any) -> str:
        return str(value or "").strip()

    @classmethod
    def _normalize_paths(cls, values: Any) -> List[str]:
        if values is None:
            return []
        if isinstance(values, (str, Path)):
            values = [values]
        if not isinstance(values, Sequence):
            return []
        return [cls._clean_text(value) for value in values if cls._clean_text(value)]


if __name__ == "__main__":
    engine = AIVideoEngine()
    sample_request = engine.build_request(
        project_id=50,
        product_name="이동식 수납 바구니",
        scenes=engine.plan_multi_scenes(
            product_name="이동식 수납 바구니",
            reference_image_path="assets/products/project_50/main.png",
        ),
        provider="gemini_veo",
    )
    print(json.dumps(engine.generate(sample_request, dry_run=True), ensure_ascii=False, indent=2))