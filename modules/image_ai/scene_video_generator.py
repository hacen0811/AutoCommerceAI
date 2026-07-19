from __future__ import annotations

import copy
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from modules.video.gemini_veo_provider import GeminiVeoProvider


class SceneVideoGenerator:
    """
    Sprint109-1 Veo Smart Cache

    핵심:
    - 동일한 장면 지문(prompt/reference/duration/aspect/seed)이면 기존 MP4 재사용
    - 변경된 장면과 실패한 장면만 Gemini/Veo 호출
    - 결제/크레딧/할당량 오류는 즉시 중단하여 불필요한 재시도 방지
    - 캐시 manifest를 별도 저장
    - 기존 generate() 인자와 반환 키 유지
    """

    VERSION = "scene-video-generator-109-2"
    REPORT_FILENAME = "scene_video_generation_report.json"
    CACHE_FILENAME = "scene_video_cache.json"

    TERMINAL_ERROR_MARKERS = (
        "resource_exhausted",
        "prepayment credits are depleted",
        "credits are depleted",
        "billing",
        "insufficient",
        "quota exceeded",
        "quota_exceeded",
        "daily quota",
        "rate limit",
        "rate_limit",
        "429",
    )

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
        max_attempts: int = 2,
        retry_delay_seconds: float = 2.0,
        reuse_existing: bool = True,
        force_regenerate: bool = False,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        started_at = time.time()
        max_attempts = max(1, int(max_attempts or 1))
        retry_delay_seconds = max(0.0, float(retry_delay_seconds or 0.0))

        result: Dict[str, Any] = {
            "ok": False,
            "ready": False,
            "version": self.VERSION,
            "status": "not_run",
            "project_id": str(project_id or ""),
            "director_manifest_path": str(director_manifest_path or "").strip(),
            "output_dir": "",
            "report_path": "",
            "cache_path": "",
            "scene_count": 0,
            "valid_scene_count": 0,
            "generated_scene_count": 0,
            "newly_generated_scene_count": 0,
            "reused_scene_count": 0,
            "cache_hit_count": 0,
            "cache_miss_count": 0,
            "failed_scene_count": 0,
            "skipped_scene_count": 0,
            "attempt_count": 0,
            "max_attempts": max_attempts,
            "force_regenerate": bool(force_regenerate),
            "dry_run": bool(dry_run),
            "terminal_error": False,
            "terminal_error_type": "",
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
            director_manifest,
            director_manifest_path,
        )
        if manifest_path:
            result["director_manifest_path"] = str(manifest_path)

        if not manifest:
            result["status"] = "manifest_not_found"
            result["errors"].append("director_manifest를 읽을 수 없습니다")
            return self._finish(result, started_at)

        scenes = manifest.get("scenes") or []
        scenes = scenes if isinstance(scenes, list) else []
        result["scene_count"] = len(scenes)

        if not scenes:
            result["status"] = "no_scenes"
            result["errors"].append("영상으로 생성할 Director 장면이 없습니다")
            return self._finish(result, started_at)

        resolved_output_dir = self._resolve_output_dir(
            output_dir,
            manifest,
            manifest_path,
            project_id,
        )
        resolved_output_dir.mkdir(parents=True, exist_ok=True)
        result["output_dir"] = str(resolved_output_dir)

        report_path = resolved_output_dir / self.REPORT_FILENAME
        cache_path = resolved_output_dir / self.CACHE_FILENAME
        result["report_path"] = str(report_path)
        result["cache_path"] = str(cache_path)

        cache = self._load_cache(cache_path)
        cache_scenes = cache.get("scenes")
        if not isinstance(cache_scenes, dict):
            cache_scenes = {}

        normalized_scenes: List[Dict[str, Any]] = []

        for index, raw_scene in enumerate(scenes, start=1):
            if not isinstance(raw_scene, Mapping):
                result["warnings"].append(
                    f"scene_{index:02d}: dict 형식이 아니어서 제외했습니다"
                )
                continue

            scene = dict(raw_scene)
            scene_id = str(
                scene.get("scene_id") or f"scene_{index:02d}"
            ).strip()
            normalized = self._normalize_scene(
                scene,
                scene_id,
                index,
                manifest,
                aspect_ratio,
            )

            if not normalized.get("prompt"):
                result["warnings"].append(
                    f"{scene_id}: prompt가 비어 있어 제외했습니다"
                )
                continue

            reference_path = str(
                normalized.get("reference_image_path") or ""
            ).strip()
            if reference_path and not Path(reference_path).is_file():
                result["warnings"].append(
                    f"{scene_id}: 참조 이미지 파일이 없습니다 - {reference_path}"
                )
                normalized["reference_image_path"] = ""

            normalized["scene_fingerprint"] = self._scene_fingerprint(normalized)
            normalized_scenes.append(normalized)

        result["valid_scene_count"] = len(normalized_scenes)

        if not normalized_scenes:
            result["status"] = "no_valid_scenes"
            result["errors"].append("유효한 영상 생성 장면이 없습니다")
            self._save_json(report_path, result)
            return self._finish(result, started_at)

        scene_results_by_id: Dict[str, Dict[str, Any]] = {}
        generated_files: List[str] = []
        pending_scenes: List[Dict[str, Any]] = []

        for scene in normalized_scenes:
            scene_id = str(scene["scene_id"])
            fingerprint = str(scene["scene_fingerprint"])
            cached_entry = cache_scenes.get(scene_id)
            cached_entry = cached_entry if isinstance(cached_entry, dict) else {}

            existing_path = self._existing_scene_path(
                scene_id=scene_id,
                scene=scene,
                manifest=manifest,
                output_dir=resolved_output_dir,
            )

            cached_path = self._valid_output_path(
                cached_entry.get("output_path")
            )
            cached_fingerprint = str(
                cached_entry.get("scene_fingerprint") or ""
            ).strip()

            reuse_path = ""
            reuse_reason = ""

            if reuse_existing and not force_regenerate:
                if cached_path and cached_fingerprint == fingerprint:
                    reuse_path = cached_path
                    reuse_reason = "fingerprint_cache_hit"
                elif existing_path and not cached_fingerprint:
                    # 구버전에서 만든 파일은 최초 1회 호환 재사용 후 현재 지문으로 등록
                    reuse_path = existing_path
                    reuse_reason = "legacy_existing_file"

            if reuse_path:
                scene_result = {
                    "ok": True,
                    "ready": True,
                    "scene_id": scene_id,
                    "status": "reused_existing",
                    "cache_status": "hit",
                    "reuse_reason": reuse_reason,
                    "scene_fingerprint": fingerprint,
                    "output_path": reuse_path,
                    "attempt": 0,
                    "errors": [],
                    "warnings": [],
                }
                scene_results_by_id[scene_id] = scene_result
                self._append_unique(generated_files, reuse_path)
                result["reused_scene_count"] += 1
                result["cache_hit_count"] += 1
                cache_scenes[scene_id] = self._cache_entry(
                    scene=scene,
                    output_path=reuse_path,
                    status="reused_existing",
                )
            else:
                result["cache_miss_count"] += 1
                pending_scenes.append(scene)

        if dry_run:
            for scene in pending_scenes:
                scene_id = str(scene["scene_id"])
                scene_results_by_id[scene_id] = {
                    "ok": False,
                    "ready": False,
                    "scene_id": scene_id,
                    "status": "skipped_dry_run",
                    "cache_status": "miss",
                    "scene_fingerprint": scene["scene_fingerprint"],
                    "output_path": "",
                    "attempt": 0,
                    "errors": [],
                    "warnings": [],
                }
                result["skipped_scene_count"] += 1
        elif pending_scenes:
            readiness = self.provider.readiness()
            result["provider"] = dict(readiness)

            if not readiness.get("ready"):
                result["status"] = "provider_not_ready"
                errors = list(readiness.get("errors") or [])
                result["errors"].extend(errors)
                for scene in pending_scenes:
                    scene_id = str(scene["scene_id"])
                    scene_results_by_id[scene_id] = {
                        "ok": False,
                        "ready": False,
                        "scene_id": scene_id,
                        "status": "provider_not_ready",
                        "cache_status": "miss",
                        "scene_fingerprint": scene["scene_fingerprint"],
                        "output_path": "",
                        "attempt": 0,
                        "errors": errors,
                        "warnings": [],
                    }
            else:
                remaining = list(pending_scenes)

                for attempt in range(1, max_attempts + 1):
                    if not remaining or result["terminal_error"]:
                        break

                    result["attempt_count"] = attempt
                    next_remaining: List[Dict[str, Any]] = []

                    # Sprint109-2:
                    # Provider에 여러 장면을 한꺼번에 넘기지 않는다.
                    # 장면을 1개씩 호출하고 첫 429/결제/할당량 오류에서 즉시 중단한다.
                    for scene_position, scene in enumerate(remaining):
                        if result["terminal_error"]:
                            next_remaining.extend(remaining[scene_position:])
                            break

                        scene_id = str(scene["scene_id"])
                        request = {
                            "project_id": str(
                                project_id or manifest.get("project_id") or ""
                            ),
                            "product_name": str(
                                product_name or manifest.get("product_name") or ""
                            ),
                            "aspect_ratio": str(aspect_ratio or "9:16"),
                            "output_dir": str(resolved_output_dir),
                            "scenes": [scene],
                        }

                        provider_result = self._safe_provider_generate(request)
                        terminal_type = self._terminal_error_type(provider_result)

                        provider_scene_results = (
                            provider_result.get("scene_results") or []
                        )
                        provider_generated_files = list(
                            provider_result.get("generated_files") or []
                        )

                        for path_text in provider_generated_files:
                            path_text = str(path_text or "").strip()
                            if path_text and Path(path_text).is_file():
                                self._append_unique(generated_files, path_text)

                        returned_by_id = {
                            str(item.get("scene_id") or "").strip(): dict(item)
                            for item in provider_scene_results
                            if isinstance(item, dict)
                            and str(item.get("scene_id") or "").strip()
                        }

                        scene_result = dict(returned_by_id.get(scene_id, {}))
                        scene_result.setdefault("scene_id", scene_id)
                        scene_result["attempt"] = attempt
                        scene_result["cache_status"] = "miss"
                        scene_result["scene_fingerprint"] = scene[
                            "scene_fingerprint"
                        ]

                        output_path = self._valid_output_path(
                            scene_result.get("output_path")
                        )
                        if not output_path:
                            output_path = self._find_generated_scene_file(
                                resolved_output_dir,
                                scene_id,
                            )

                        if output_path:
                            scene_result.update(
                                {
                                    "ok": True,
                                    "ready": True,
                                    "status": "generated",
                                    "output_path": output_path,
                                }
                            )
                            self._append_unique(generated_files, output_path)
                            cache_scenes[scene_id] = self._cache_entry(
                                scene=scene,
                                output_path=output_path,
                                status="generated",
                            )
                        else:
                            errors = list(
                                scene_result.get("errors")
                                or provider_result.get("errors")
                                or []
                            )
                            scene_result.update(
                                {
                                    "ok": False,
                                    "ready": False,
                                    "status": str(
                                        scene_result.get("status")
                                        or provider_result.get("status")
                                        or "generation_failed"
                                    ),
                                    "output_path": "",
                                    "errors": errors,
                                }
                            )
                            next_remaining.append(scene)

                        scene_results_by_id[scene_id] = scene_result

                        if terminal_type:
                            result["terminal_error"] = True
                            result["terminal_error_type"] = terminal_type

                            # 아직 호출하지 않은 장면은 API 요청 없이 중단 처리
                            for skipped_scene in remaining[scene_position + 1:]:
                                skipped_id = str(skipped_scene["scene_id"])
                                skipped_result = {
                                    "ok": False,
                                    "ready": False,
                                    "scene_id": skipped_id,
                                    "status": "skipped_after_terminal_error",
                                    "cache_status": "miss",
                                    "scene_fingerprint": skipped_scene[
                                        "scene_fingerprint"
                                    ],
                                    "output_path": "",
                                    "attempt": attempt,
                                    "errors": [],
                                    "warnings": [
                                        f"{scene_id}에서 {terminal_type} 발생 후 API 호출 생략"
                                    ],
                                }
                                scene_results_by_id[skipped_id] = skipped_result
                                next_remaining.append(skipped_scene)
                                result["skipped_scene_count"] += 1
                            break

                    if result["terminal_error"]:
                        break

                    if next_remaining and attempt < max_attempts:
                        time.sleep(retry_delay_seconds)

                    remaining = next_remaining

                for scene in remaining:
                    scene_id = str(scene["scene_id"])
                    previous = dict(scene_results_by_id.get(scene_id, {}))
                    previous.update(
                        {
                            "ok": False,
                            "ready": False,
                            "scene_id": scene_id,
                            "status": (
                                "terminal_error_no_retry"
                                if result["terminal_error"]
                                else str(
                                    previous.get("status")
                                    or "generation_failed"
                                )
                            ),
                            "cache_status": "miss",
                            "scene_fingerprint": scene["scene_fingerprint"],
                            "output_path": "",
                            "attempt": result["attempt_count"],
                        }
                    )
                    scene_results_by_id[scene_id] = previous

        updated_manifest = copy.deepcopy(manifest)
        updated_scenes: List[Dict[str, Any]] = []
        generated_count = 0
        newly_generated_count = 0
        failed_count = 0

        for index, raw_scene in enumerate(scenes, start=1):
            if not isinstance(raw_scene, dict):
                continue

            scene_copy = dict(raw_scene)
            scene_id = str(
                scene_copy.get("scene_id") or f"scene_{index:02d}"
            ).strip()
            scene_result = dict(scene_results_by_id.get(scene_id, {}))
            generated_path = self._valid_output_path(
                scene_result.get("output_path")
            )

            if generated_path:
                scene_copy["generated_video_path"] = generated_path
                scene_copy["video_generation_status"] = str(
                    scene_result.get("status") or "generated"
                )
                generated_count += 1
                if scene_result.get("status") == "generated":
                    newly_generated_count += 1
            else:
                scene_copy["generated_video_path"] = ""
                scene_copy["video_generation_status"] = str(
                    scene_result.get("status") or "generation_failed"
                )
                failed_count += 1

            scene_copy["scene_fingerprint"] = str(
                scene_result.get("scene_fingerprint") or ""
            )
            scene_copy["video_generator_version"] = self.VERSION
            scene_copy["video_generation_result"] = scene_result
            updated_scenes.append(scene_copy)

        ordered_scene_results = [
            dict(scene_results_by_id.get(str(scene["scene_id"]), {}))
            for scene in normalized_scenes
        ]

        updated_manifest["scenes"] = updated_scenes
        updated_manifest["scene_video_generator_version"] = self.VERSION
        updated_manifest["scenes_dir"] = str(resolved_output_dir)
        updated_manifest["generated_files"] = generated_files
        updated_manifest["generated_scene_count"] = generated_count
        updated_manifest["newly_generated_scene_count"] = newly_generated_count
        updated_manifest["reused_scene_count"] = result["reused_scene_count"]
        updated_manifest["failed_scene_count"] = failed_count
        updated_manifest["scene_video_cache_path"] = str(cache_path)

        updated_manifest_path = manifest_path or (
            resolved_output_dir / "director_manifest.json"
        )
        updated_manifest["manifest_path"] = str(updated_manifest_path)

        cache_payload = {
            "version": self.VERSION,
            "project_id": str(
                project_id or manifest.get("project_id") or ""
            ),
            "updated_at": time.strftime(
                "%Y-%m-%dT%H:%M:%S",
                time.localtime(),
            ),
            "scenes": cache_scenes,
        }
        self._save_json(cache_path, cache_payload)

        if update_manifest:
            self._save_json(updated_manifest_path, updated_manifest)

        result["generated_scene_count"] = generated_count
        result["newly_generated_scene_count"] = newly_generated_count
        result["failed_scene_count"] = failed_count
        result["generated_files"] = generated_files
        result["scene_results"] = ordered_scene_results
        result["updated_manifest"] = updated_manifest
        result["updated_manifest_path"] = str(updated_manifest_path)
        result["ok"] = (
            generated_count == len(normalized_scenes)
            and generated_count > 0
        )
        result["ready"] = result["ok"]

        if dry_run:
            result["status"] = (
                "dry_run_cache_only"
                if generated_count > 0
                else "dry_run_no_generation"
            )
        elif result["terminal_error"]:
            result["status"] = (
                "partially_generated_terminal_error"
                if generated_count > 0
                else "terminal_error_no_retry"
            )
        elif result["ok"]:
            if result["reused_scene_count"] == generated_count:
                result["status"] = "reused_existing"
            elif result["reused_scene_count"] > 0:
                result["status"] = "generated_with_cache"
            else:
                result["status"] = "generated"
        elif generated_count > 0:
            result["status"] = "partially_generated"
        elif result["status"] == "not_run":
            result["status"] = "generation_failed"

        for scene_result in ordered_scene_results:
            for error in list(scene_result.get("errors") or []):
                error_text = str(error)
                if error_text and error_text not in result["errors"]:
                    result["errors"].append(error_text)

        result = self._finish(result, started_at)
        self._save_json(report_path, result)
        return result

    def _safe_provider_generate(self, request: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = self.provider.generate(request)
            if isinstance(response, dict):
                return response
            return {
                "ok": False,
                "ready": False,
                "status": "invalid_provider_result",
                "scene_results": [],
                "generated_files": [],
                "errors": ["GeminiVeoProvider 결과가 dict 형식이 아닙니다"],
            }
        except Exception as exc:
            return {
                "ok": False,
                "ready": False,
                "status": "provider_exception",
                "scene_results": [],
                "generated_files": [],
                "errors": [f"{type(exc).__name__}: {exc}"],
            }

    def _terminal_error_type(self, payload: Any) -> str:
        try:
            text = json.dumps(
                payload,
                ensure_ascii=False,
                default=str,
            ).lower()
        except Exception:
            text = str(payload or "").lower()

        if not any(marker in text for marker in self.TERMINAL_ERROR_MARKERS):
            return ""

        if (
            "prepayment credits are depleted" in text
            or "credits are depleted" in text
            or "billing" in text
            or "insufficient" in text
        ):
            return "billing_or_credit_exhausted"
        if "rate limit" in text or "rate_limit" in text:
            return "rate_limit"
        if "daily quota" in text:
            return "daily_quota_exhausted"
        return "quota_or_resource_exhausted"

    def _scene_fingerprint(self, scene: Dict[str, Any]) -> str:
        reference_path = str(
            scene.get("reference_image_path") or ""
        ).strip()
        reference_signature = self._file_signature(reference_path)

        payload = {
            "scene_id": str(scene.get("scene_id") or ""),
            "prompt": str(scene.get("prompt") or "").strip(),
            "negative_prompt": str(
                scene.get("negative_prompt") or ""
            ).strip(),
            "reference_image_path": reference_path,
            "reference_signature": reference_signature,
            "duration_seconds": int(scene.get("duration_seconds") or 6),
            "aspect_ratio": str(scene.get("aspect_ratio") or "9:16"),
            "seed": scene.get("seed"),
        }
        raw = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def _file_signature(self, value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        path = Path(text).expanduser()
        if not path.is_file():
            return ""
        stat = path.stat()
        return f"{stat.st_size}:{stat.st_mtime_ns}"

    def _cache_entry(
        self,
        scene: Dict[str, Any],
        output_path: str,
        status: str,
    ) -> Dict[str, Any]:
        return {
            "scene_id": str(scene.get("scene_id") or ""),
            "scene_fingerprint": str(
                scene.get("scene_fingerprint") or ""
            ),
            "output_path": str(output_path or ""),
            "status": str(status or ""),
            "updated_at": time.strftime(
                "%Y-%m-%dT%H:%M:%S",
                time.localtime(),
            ),
            "generator_version": self.VERSION,
        }

    def _load_cache(self, path: Path) -> Dict[str, Any]:
        if not path.is_file():
            return {"scenes": {}}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {"scenes": {}}
        return payload if isinstance(payload, dict) else {"scenes": {}}

    def _resolve_manifest(self, value: Any, path_value: Any):
        if isinstance(value, dict):
            path_text = str(
                path_value or value.get("manifest_path") or ""
            ).strip()
            return (
                copy.deepcopy(value),
                Path(path_text).expanduser() if path_text else None,
            )

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

    def _resolve_output_dir(
        self,
        output_dir: Any,
        manifest: Dict[str, Any],
        manifest_path: Optional[Path],
        project_id: Any,
    ) -> Path:
        if str(output_dir or "").strip():
            return Path(str(output_dir)).expanduser()

        manifest_output = str(manifest.get("output_dir") or "").strip()
        if manifest_output:
            return Path(manifest_output).expanduser()

        if manifest_path:
            return manifest_path.parent

        project_key = str(
            project_id or manifest.get("project_id") or "unknown"
        ).strip() or "unknown"
        return Path("assets") / "products" / f"project_{project_key}"

    def _normalize_scene(
        self,
        scene: Dict[str, Any],
        scene_id: str,
        index: int,
        manifest: Dict[str, Any],
        default_aspect_ratio: str,
    ) -> Dict[str, Any]:
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
            "negative_prompt": str(
                scene.get("negative_prompt") or ""
            ).strip(),
            "reference_image_path": reference_image_path,
            "duration_seconds": self._normalize_duration(
                scene.get("duration_seconds")
                or scene.get("duration")
                or 6
            ),
            "aspect_ratio": str(
                scene.get("aspect_ratio")
                or default_aspect_ratio
                or "9:16"
            ),
            "seed": scene.get("seed"),
        }

    def _existing_scene_path(
        self,
        scene_id: str,
        scene: Dict[str, Any],
        manifest: Dict[str, Any],
        output_dir: Path,
    ) -> str:
        candidates = [
            scene.get("generated_video_path"),
            scene.get("output_path"),
        ]

        for raw_scene in manifest.get("scenes") or []:
            if not isinstance(raw_scene, dict):
                continue
            raw_scene_id = str(raw_scene.get("scene_id") or "").strip()
            if raw_scene_id == scene_id:
                candidates.extend(
                    [
                        raw_scene.get("generated_video_path"),
                        raw_scene.get("output_path"),
                    ]
                )

        candidates.extend(
            [
                output_dir / f"{scene_id}.mp4",
                output_dir / f"{scene_id}_generated.mp4",
            ]
        )

        for value in candidates:
            valid_path = self._valid_output_path(value)
            if valid_path:
                return valid_path
        return ""

    def _find_generated_scene_file(
        self,
        output_dir: Path,
        scene_id: str,
    ) -> str:
        exact = output_dir / f"{scene_id}.mp4"
        if exact.is_file() and exact.stat().st_size > 0:
            return str(exact)

        matches = sorted(
            output_dir.glob(f"{scene_id}*.mp4"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        for path in matches:
            if path.is_file() and path.stat().st_size > 0:
                return str(path)
        return ""

    def _valid_output_path(self, value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            return ""

        path = Path(text).expanduser()
        if path.is_file() and path.stat().st_size > 0:
            return str(path)
        return ""

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

    def _append_unique(self, values: List[str], value: str) -> None:
        normalized = str(value or "").strip()
        if normalized and normalized not in values:
            values.append(normalized)

    def _finish(
        self,
        result: Dict[str, Any],
        started_at: float,
    ) -> Dict[str, Any]:
        result["elapsed_seconds"] = round(time.time() - started_at, 3)
        return result

    def _save_json(
        self,
        path: Path,
        payload: Dict[str, Any],
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )