from __future__ import annotations

import copy
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from modules.video.gemini_veo_provider import GeminiVeoProvider


class SceneVideoGenerator:
    """Sprint96-1 Director Manifest -> Gemini Veo scene MP4 generator."""

    VERSION = "scene-video-generator-96-1"
    REPORT_FILENAME = "scene_video_generation_report.json"

    def __init__(self, provider: Optional[GeminiVeoProvider] = None) -> None:
        self.provider = provider or GeminiVeoProvider()

    def generate(
        self,
        director_manifest: Any = None,
        director_manifest_path: Any = "",
        output_dir: Any = "",
        project_id: Any = "",
        product_name: Any = "",
        aspect_ratio: str = "9:16",
        update_manifest: bool = True,
    ) -> Dict[str, Any]:
        started_at = time.time()
        result: Dict[str, Any] = {
            "ok": False,
            "ready": False,
            "version": self.VERSION,
            "status": "not_run",
            "project_id": str(project_id or ""),
            "director_manifest_path": str(director_manifest_path or "").strip(),
            "output_dir": "",
            "report_path": "",
            "scene_count": 0,
            "generated_scene_count": 0,
            "failed_scene_count": 0,
            "generated_files": [],
            "scene_results": [],
            "updated_manifest": {},
            "updated_manifest_path": "",
            "provider": {},
            "warnings": [],
            "errors": [],
            "elapsed_seconds": 0.0,
        }

        manifest, manifest_path = self._resolve_manifest(
            director_manifest, director_manifest_path
        )
        if manifest_path:
            result["director_manifest_path"] = str(manifest_path)
        if not manifest:
            result["status"] = "manifest_not_found"
            result["errors"].append("director_manifest를 읽을 수 없습니다")
            result["elapsed_seconds"] = round(time.time() - started_at, 3)
            return result

        scenes = manifest.get("scenes") or []
        scenes = scenes if isinstance(scenes, list) else []
        result["scene_count"] = len(scenes)
        if not scenes:
            result["status"] = "no_scenes"
            result["errors"].append("영상으로 생성할 Director 장면이 없습니다")
            result["elapsed_seconds"] = round(time.time() - started_at, 3)
            return result

        resolved_output_dir = self._resolve_output_dir(
            output_dir, manifest, manifest_path, project_id
        )
        resolved_output_dir.mkdir(parents=True, exist_ok=True)
        result["output_dir"] = str(resolved_output_dir)
        report_path = resolved_output_dir / self.REPORT_FILENAME
        result["report_path"] = str(report_path)

        readiness = self.provider.readiness()
        result["provider"] = dict(readiness)
        if not readiness.get("ready"):
            result["status"] = "provider_not_ready"
            result["errors"].extend(list(readiness.get("errors") or []))
            result["elapsed_seconds"] = round(time.time() - started_at, 3)
            self._save_json(report_path, result)
            return result

        normalized_scenes: List[Dict[str, Any]] = []
        for index, raw_scene in enumerate(scenes, start=1):
            if not isinstance(raw_scene, Mapping):
                result["warnings"].append(
                    f"scene_{index:02d}: dict 형식이 아니어서 제외했습니다"
                )
                continue
            scene = dict(raw_scene)
            scene_id = str(scene.get("scene_id") or f"scene_{index:02d}").strip()
            normalized = self._normalize_scene(
                scene, scene_id, index, manifest, aspect_ratio
            )
            if not normalized.get("prompt"):
                result["warnings"].append(
                    f"{scene_id}: prompt가 비어 있어 제외했습니다"
                )
                continue
            normalized_scenes.append(normalized)

        if not normalized_scenes:
            result["status"] = "no_valid_scenes"
            result["errors"].append("유효한 영상 생성 장면이 없습니다")
            result["elapsed_seconds"] = round(time.time() - started_at, 3)
            self._save_json(report_path, result)
            return result

        request = {
            "project_id": str(project_id or manifest.get("project_id") or ""),
            "product_name": str(product_name or manifest.get("product_name") or ""),
            "aspect_ratio": str(aspect_ratio or "9:16"),
            "output_dir": str(resolved_output_dir),
            "scenes": normalized_scenes,
        }
        provider_result = self.provider.generate(request)
        provider_scene_results = (
            provider_result.get("scene_results") or []
            if isinstance(provider_result, dict)
            else []
        )
        generated_files = (
            list(provider_result.get("generated_files") or [])
            if isinstance(provider_result, dict)
            else []
        )

        result_by_scene_id = {
            str(item.get("scene_id") or "").strip(): item
            for item in provider_scene_results
            if isinstance(item, dict) and str(item.get("scene_id") or "").strip()
        }
        updated_manifest = copy.deepcopy(manifest)
        updated_scenes: List[Dict[str, Any]] = []
        generated_count = 0
        failed_count = 0

        for index, raw_scene in enumerate(scenes, start=1):
            if not isinstance(raw_scene, dict):
                continue
            scene_copy = dict(raw_scene)
            scene_id = str(scene_copy.get("scene_id") or f"scene_{index:02d}").strip()
            scene_result = result_by_scene_id.get(scene_id, {})
            generated_path = str(scene_result.get("output_path") or "").strip()
            if generated_path and Path(generated_path).is_file():
                scene_copy["generated_video_path"] = generated_path
                scene_copy["video_generation_status"] = "generated"
                generated_count += 1
            else:
                scene_copy["generated_video_path"] = str(
                    scene_copy.get("generated_video_path") or ""
                )
                scene_copy["video_generation_status"] = str(
                    scene_result.get("status") or "generation_failed"
                )
                failed_count += 1
            scene_copy["video_generator_version"] = self.VERSION
            scene_copy["video_generation_result"] = scene_result
            updated_scenes.append(scene_copy)

        updated_manifest["scenes"] = updated_scenes
        updated_manifest["scene_video_generator_version"] = self.VERSION
        updated_manifest["scenes_dir"] = str(resolved_output_dir)
        updated_manifest["generated_files"] = generated_files
        updated_manifest["generated_scene_count"] = generated_count
        updated_manifest["failed_scene_count"] = failed_count
        updated_manifest_path = manifest_path or (
            resolved_output_dir / "director_manifest.json"
        )
        updated_manifest["manifest_path"] = str(updated_manifest_path)
        if update_manifest:
            self._save_json(updated_manifest_path, updated_manifest)

        result["generated_scene_count"] = generated_count
        result["failed_scene_count"] = failed_count
        result["generated_files"] = generated_files
        result["scene_results"] = provider_scene_results
        result["updated_manifest"] = updated_manifest
        result["updated_manifest_path"] = str(updated_manifest_path)
        result["ok"] = generated_count == len(normalized_scenes) and generated_count > 0
        result["ready"] = result["ok"]
        if result["ok"]:
            result["status"] = "generated"
        elif generated_count > 0:
            result["status"] = "partially_generated"
        else:
            result["status"] = str(
                provider_result.get("status")
                if isinstance(provider_result, dict)
                else "generation_failed"
            )
        if isinstance(provider_result, dict):
            result["errors"].extend(list(provider_result.get("errors") or []))
        result["elapsed_seconds"] = round(time.time() - started_at, 3)
        self._save_json(report_path, result)
        return result

    def _resolve_manifest(self, value: Any, path_value: Any):
        if isinstance(value, dict):
            path_text = str(path_value or value.get("manifest_path") or "").strip()
            return copy.deepcopy(value), Path(path_text).expanduser() if path_text else None
        candidate = str(path_value or "").strip()
        if not candidate and isinstance(value, (str, Path)):
            candidate = str(value)
        if not candidate:
            return {}, None
        path = Path(candidate).expanduser()
        if not path.is_file():
            return {}, path
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}, path
        return payload if isinstance(payload, dict) else {}, path

    def _resolve_output_dir(self, output_dir: Any, manifest: Dict[str, Any], manifest_path, project_id: Any) -> Path:
        if str(output_dir or "").strip():
            return Path(str(output_dir)).expanduser()
        manifest_output = str(manifest.get("output_dir") or "").strip()
        if manifest_output:
            return Path(manifest_output).expanduser()
        if manifest_path:
            return manifest_path.parent
        project_key = str(project_id or manifest.get("project_id") or "unknown").strip() or "unknown"
        return Path("assets") / "products" / f"project_{project_key}"

    def _normalize_scene(self, scene: Dict[str, Any], scene_id: str, index: int, manifest: Dict[str, Any], default_aspect_ratio: str) -> Dict[str, Any]:
        reference_image_path = self._first_text(
            scene.get("reference_image_path"),
            scene.get("selected_image_path"),
            scene.get("image_path"),
            scene.get("source_image_path"),
            scene.get("product_image_path"),
            manifest.get("reference_image_path"),
            manifest.get("main_image_path"),
            manifest.get("product_image_path"),
        )
        return {
            "scene_id": scene_id,
            "scene_index": int(scene.get("scene_index") or index),
            "scene_type": str(scene.get("scene_type") or ""),
            "prompt": str(scene.get("prompt") or "").strip(),
            "negative_prompt": str(scene.get("negative_prompt") or "").strip(),
            "reference_image_path": reference_image_path,
            "duration_seconds": self._normalize_duration(
                scene.get("duration_seconds") or scene.get("duration") or 6
            ),
            "aspect_ratio": str(scene.get("aspect_ratio") or default_aspect_ratio or "9:16"),
            "seed": scene.get("seed"),
        }

    def _normalize_duration(self, value: Any) -> int:
        try:
            duration = int(round(float(value)))
        except Exception:
            duration = 6
        supported = (4, 6, 8)
        return min(supported, key=lambda item: abs(item - duration))

    def _first_text(self, *values: Any) -> str:
        for value in values:
            text = str(value or "").strip()
            if text:
                return text
        return ""

    def _save_json(self, path: Path, payload: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )