from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import re
from typing import Any, Dict, List


class PublisherResultStore:
    """
    Sprint82-7 Publisher Result Store

    역할:
    - Sprint82-5 PublisherOrchestrator 결과를 JSON 파일로 저장
    - 통합 결과와 플랫폼별 결과를 분리 저장
    - 최신 결과 포인터와 저장 이력 메타데이터 생성
    - 실제 업로드나 외부 API 호출 없이 로컬 저장만 수행
    - 원본 Orchestrator 결과를 변경하지 않음
    """

    VERSION = "publisher-result-store-82-7"
    SOURCE_VERSION = "publisher-orchestrator-82-5"
    DEFAULT_BASE_DIR = "exports/publisher_results"
    SUPPORTED_PLATFORMS = (
        "youtube_shorts",
        "instagram_reels",
        "tiktok",
    )

    def save(
        self,
        orchestrator_result: Any = None,
        project_id: Any = "",
        project_name: Any = "",
        base_dir: Any = "",
        run_id: Any = "",
    ) -> Dict[str, Any]:
        source = orchestrator_result if isinstance(orchestrator_result, dict) else {}
        validation = self._validate_source(source)

        if not validation["valid"]:
            return {
                "ok": False,
                "version": self.VERSION,
                "status": "invalid_orchestrator_result",
                "stored": False,
                "source_version": self._clean_text(source.get("version")),
                "project_id": self._clean_text(project_id),
                "project_name": self._clean_text(project_name),
                "run_id": "",
                "output_dir": "",
                "manifest_path": "",
                "platform_paths": {},
                "latest_pointer_path": "",
                "errors": validation["errors"],
                "warnings": validation["warnings"],
                "validation": validation,
            }

        resolved_project_id = self._clean_text(project_id) or "unknown"
        resolved_project_name = self._clean_text(project_name) or "project"
        resolved_run_id = self._clean_text(run_id) or self._make_run_id()
        resolved_base_dir = Path(
            self._clean_text(base_dir) or self.DEFAULT_BASE_DIR
        )

        project_folder = self._safe_name(
            f"{resolved_project_id}_{resolved_project_name}"
        )
        output_dir = resolved_base_dir / project_folder / resolved_run_id
        platform_dir = output_dir / "platforms"

        try:
            platform_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            resolved_run_id = f"{resolved_run_id}_{self._make_suffix()}"
            output_dir = resolved_base_dir / project_folder / resolved_run_id
            platform_dir = output_dir / "platforms"
            platform_dir.mkdir(parents=True, exist_ok=False)
        except Exception as exc:
            return self._storage_error(
                source=source,
                project_id=resolved_project_id,
                project_name=resolved_project_name,
                run_id=resolved_run_id,
                error=exc,
                validation=validation,
            )

        saved_at = datetime.now(timezone.utc).isoformat()
        platform_paths: Dict[str, str] = {}
        platform_summaries: Dict[str, Dict[str, Any]] = {}
        errors: List[str] = []

        try:
            for platform in self.SUPPORTED_PLATFORMS:
                platform_result = self._platform_result(source, platform)
                platform_path = platform_dir / f"{platform}.json"
                self._write_json(platform_path, platform_result)
                platform_paths[platform] = str(platform_path)
                platform_summaries[platform] = {
                    "upload_ready": bool(platform_result.get("upload_ready")),
                    "status": self._clean_text(platform_result.get("status")),
                    "version": self._clean_text(platform_result.get("version")),
                    "path": str(platform_path),
                }

            result_path = output_dir / "orchestrator_result.json"
            self._write_json(result_path, source)

            manifest = {
                "version": self.VERSION,
                "source_version": self._clean_text(source.get("version")),
                "saved_at": saved_at,
                "project_id": resolved_project_id,
                "project_name": resolved_project_name,
                "run_id": resolved_run_id,
                "orchestrator_ready": bool(source.get("orchestrator_ready")),
                "status": self._clean_text(source.get("status")),
                "platform_count": int(source.get("platform_count") or 0),
                "ready_platform_count": int(
                    source.get("ready_platform_count") or 0
                ),
                "ready_platforms": list(source.get("ready_platforms") or []),
                "failed_platforms": list(source.get("failed_platforms") or []),
                "orchestrator_result_path": str(result_path),
                "platforms": platform_summaries,
                "prepared_only": True,
                "actual_upload_performed": False,
            }
            manifest_path = output_dir / "manifest.json"
            self._write_json(manifest_path, manifest)

            latest_pointer_path = resolved_base_dir / project_folder / "latest.json"
            latest_pointer = {
                "version": self.VERSION,
                "project_id": resolved_project_id,
                "project_name": resolved_project_name,
                "run_id": resolved_run_id,
                "saved_at": saved_at,
                "manifest_path": str(manifest_path),
                "output_dir": str(output_dir),
            }
            self._write_json(latest_pointer_path, latest_pointer)

        except Exception as exc:
            errors.append(str(exc))
            return {
                "ok": False,
                "version": self.VERSION,
                "status": "storage_failed",
                "stored": False,
                "source_version": self._clean_text(source.get("version")),
                "project_id": resolved_project_id,
                "project_name": resolved_project_name,
                "run_id": resolved_run_id,
                "output_dir": str(output_dir),
                "manifest_path": "",
                "platform_paths": platform_paths,
                "latest_pointer_path": "",
                "errors": errors,
                "warnings": validation["warnings"],
                "validation": validation,
            }

        result = {
            "ok": True,
            "version": self.VERSION,
            "status": "stored",
            "stored": True,
            "source_version": self._clean_text(source.get("version")),
            "project_id": resolved_project_id,
            "project_name": resolved_project_name,
            "run_id": resolved_run_id,
            "saved_at": saved_at,
            "output_dir": str(output_dir),
            "manifest_path": str(manifest_path),
            "orchestrator_result_path": str(result_path),
            "platform_paths": platform_paths,
            "latest_pointer_path": str(latest_pointer_path),
            "ready_platform_count": int(
                source.get("ready_platform_count") or 0
            ),
            "ready_platforms": list(source.get("ready_platforms") or []),
            "errors": [],
            "warnings": validation["warnings"],
            "validation": validation,
        }

        print("[Sprint82-7 Store] Version:", self.VERSION, flush=True)
        print("[Sprint82-7 Store] Stored:", result["stored"], flush=True)
        print("[Sprint82-7 Store] Run ID:", result["run_id"], flush=True)
        print("[Sprint82-7 Store] Output:", result["output_dir"], flush=True)
        print(
            "[Sprint82-7 Store] Platforms:",
            result["ready_platforms"],
            flush=True,
        )

        return result

    def build(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Compatibility alias for callers that use build()."""
        return self.save(*args, **kwargs)

    def store(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Compatibility alias for callers that use store()."""
        return self.save(*args, **kwargs)

    def _validate_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []

        if not source:
            errors.append("PublisherOrchestrator 결과가 비어 있습니다")
            return {"valid": False, "errors": errors, "warnings": warnings}

        source_version = self._clean_text(source.get("version"))
        if source_version != self.SOURCE_VERSION:
            warnings.append("Sprint82-5 PublisherOrchestrator 버전이 아닙니다")

        if not bool(source.get("orchestrator_ready")):
            errors.append("PublisherOrchestrator 결과가 준비 상태가 아닙니다")

        platforms = source.get("platforms")
        if not isinstance(platforms, dict):
            errors.append("platforms가 딕셔너리가 아닙니다")
        else:
            for platform in self.SUPPORTED_PLATFORMS:
                result = platforms.get(platform)
                if not isinstance(result, dict):
                    errors.append(f"플랫폼 결과가 없습니다: {platform}")
                    continue
                if not bool(result.get("upload_ready")):
                    errors.append(f"플랫폼 준비가 완료되지 않았습니다: {platform}")

        return {
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
        }

    def _platform_result(
        self,
        source: Dict[str, Any],
        platform: str,
    ) -> Dict[str, Any]:
        platforms = source.get("platforms")
        if isinstance(platforms, dict):
            nested = platforms.get(platform)
            if isinstance(nested, dict):
                return nested

        direct = source.get(platform)
        if isinstance(direct, dict):
            return direct

        return {}

    def _write_json(self, path: Path, value: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(
                value,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        temporary.replace(path)

    def _storage_error(
        self,
        source: Dict[str, Any],
        project_id: str,
        project_name: str,
        run_id: str,
        error: Exception,
        validation: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "ok": False,
            "version": self.VERSION,
            "status": "storage_failed",
            "stored": False,
            "source_version": self._clean_text(source.get("version")),
            "project_id": project_id,
            "project_name": project_name,
            "run_id": run_id,
            "output_dir": "",
            "manifest_path": "",
            "platform_paths": {},
            "latest_pointer_path": "",
            "errors": [str(error)],
            "warnings": validation["warnings"],
            "validation": validation,
        }

    def _make_run_id(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")

    def _make_suffix(self) -> str:
        return datetime.now(timezone.utc).strftime("%f")

    def _safe_name(self, value: Any) -> str:
        cleaned = self._clean_text(value)
        cleaned = re.sub(r"[^0-9A-Za-z가-힣._-]+", "_", cleaned)
        cleaned = cleaned.strip("._-")
        return cleaned[:120] or "project"

    def _clean_text(self, value: Any) -> str:
        if value is None:
            return ""
        text = str(value)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

