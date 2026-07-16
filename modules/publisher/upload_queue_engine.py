from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import re
from typing import Any, Dict, List


class UploadQueueEngine:
    """
    Sprint82-9 Upload Queue Engine

    역할:
    - Sprint82-7 PublisherResultStore 저장 결과를 업로드 대기열로 등록
    - YouTube Shorts / Instagram Reels / TikTok 플랫폼별 작업 생성
    - 즉시 대기와 예약 대기를 구분
    - 재시도 횟수와 작업 상태 메타데이터 관리
    - 실제 업로드나 외부 API 호출은 수행하지 않음
    - 원본 저장 결과와 플랫폼 JSON을 변경하지 않음
    """

    VERSION = "upload-queue-engine-82-9"
    SOURCE_VERSION = "publisher-result-store-82-7"
    DEFAULT_QUEUE_DIR = "exports/upload_queue"
    SUPPORTED_PLATFORMS = (
        "youtube_shorts",
        "instagram_reels",
        "tiktok",
    )

    def enqueue(
        self,
        store_result: Any = None,
        manifest_path: Any = "",
        schedule_at: Any = "",
        platform_schedules: Any = None,
        max_retries: Any = 3,
        queue_dir: Any = "",
        queue_id: Any = "",
    ) -> Dict[str, Any]:
        source = store_result if isinstance(store_result, dict) else {}
        resolved_manifest_path = self._clean_text(manifest_path)

        if not resolved_manifest_path:
            resolved_manifest_path = self._clean_text(
                source.get("manifest_path")
            )

        validation = self._validate_source(
            source=source,
            manifest_path=resolved_manifest_path,
        )
        if not validation["valid"]:
            return {
                "ok": False,
                "version": self.VERSION,
                "status": "invalid_store_result",
                "queued": False,
                "source_version": self._clean_text(source.get("version")),
                "queue_id": "",
                "queue_path": "",
                "job_count": 0,
                "jobs": {},
                "errors": validation["errors"],
                "warnings": validation["warnings"],
                "validation": validation,
            }

        manifest = self._read_json(Path(resolved_manifest_path))
        resolved_queue_id = self._clean_text(queue_id) or self._make_queue_id()
        resolved_queue_dir = Path(
            self._clean_text(queue_dir) or self.DEFAULT_QUEUE_DIR
        )
        queue_folder = resolved_queue_dir / self._safe_name(resolved_queue_id)
        jobs_folder = queue_folder / "jobs"

        try:
            jobs_folder.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            resolved_queue_id = f"{resolved_queue_id}_{self._make_suffix()}"
            queue_folder = resolved_queue_dir / self._safe_name(resolved_queue_id)
            jobs_folder = queue_folder / "jobs"
            jobs_folder.mkdir(parents=True, exist_ok=False)
        except Exception as exc:
            return self._queue_error(
                source=source,
                queue_id=resolved_queue_id,
                error=exc,
                validation=validation,
            )

        resolved_max_retries = self._normalize_retry_count(max_retries)
        default_schedule = self._normalize_schedule(schedule_at)
        schedules = (
            platform_schedules
            if isinstance(platform_schedules, dict)
            else {}
        )
        created_at = datetime.now(timezone.utc).isoformat()
        jobs: Dict[str, Dict[str, Any]] = {}
        job_paths: Dict[str, str] = {}
        errors: List[str] = []

        try:
            platform_manifest = (
                manifest.get("platforms")
                if isinstance(manifest.get("platforms"), dict)
                else {}
            )

            for platform in self.SUPPORTED_PLATFORMS:
                platform_info = platform_manifest.get(platform)
                if not isinstance(platform_info, dict):
                    errors.append(f"manifest 플랫폼 정보가 없습니다: {platform}")
                    continue

                platform_path = self._clean_text(platform_info.get("path"))
                if not platform_path:
                    errors.append(f"플랫폼 JSON 경로가 없습니다: {platform}")
                    continue

                platform_payload = self._read_json(Path(platform_path))
                resolved_schedule = self._normalize_schedule(
                    schedules.get(platform)
                ) or default_schedule
                queue_status = "scheduled" if resolved_schedule else "queued"

                job = {
                    "version": self.VERSION,
                    "queue_id": resolved_queue_id,
                    "job_id": f"{resolved_queue_id}_{platform}",
                    "platform": platform,
                    "status": queue_status,
                    "created_at": created_at,
                    "scheduled_at": resolved_schedule,
                    "attempt_count": 0,
                    "max_retries": resolved_max_retries,
                    "next_retry_at": "",
                    "last_error": "",
                    "upload_ready": bool(platform_payload.get("upload_ready")),
                    "source_manifest_path": resolved_manifest_path,
                    "source_platform_path": platform_path,
                    "video_path": self._video_path(platform_payload),
                    "payload": platform_payload.get("payload", {}),
                    "metadata": {
                        "prepared_only": True,
                        "actual_upload_performed": False,
                        "source_store_version": self._clean_text(
                            source.get("version")
                        ),
                        "source_orchestrator_version": self._clean_text(
                            manifest.get("source_version")
                        ),
                    },
                }

                checks = {
                    "upload_ready": bool(job["upload_ready"]),
                    "has_video_path": bool(job["video_path"]),
                    "has_payload": isinstance(job["payload"], dict)
                    and bool(job["payload"]),
                }
                job["checks"] = checks
                job["queue_ready"] = all(checks.values())

                if not job["queue_ready"]:
                    job["status"] = "blocked"
                    job["last_error"] = ", ".join(
                        key for key, passed in checks.items() if not passed
                    )

                job_path = jobs_folder / f"{platform}.json"
                self._write_json(job_path, job)
                job["job_path"] = str(job_path)
                jobs[platform] = job
                job_paths[platform] = str(job_path)

            if errors:
                raise ValueError("; ".join(errors))

            ready_jobs = [
                platform
                for platform, job in jobs.items()
                if job.get("queue_ready")
            ]
            blocked_jobs = [
                platform
                for platform, job in jobs.items()
                if not job.get("queue_ready")
            ]
            queue_ready = len(ready_jobs) == len(self.SUPPORTED_PLATFORMS)

            queue_record = {
                "version": self.VERSION,
                "status": "ready" if queue_ready else "partial",
                "queued": queue_ready,
                "queue_ready": queue_ready,
                "queue_id": resolved_queue_id,
                "created_at": created_at,
                "source_store_version": self._clean_text(source.get("version")),
                "source_manifest_path": resolved_manifest_path,
                "project_id": self._clean_text(manifest.get("project_id")),
                "project_name": self._clean_text(manifest.get("project_name")),
                "run_id": self._clean_text(manifest.get("run_id")),
                "job_count": len(jobs),
                "ready_job_count": len(ready_jobs),
                "ready_jobs": ready_jobs,
                "blocked_jobs": blocked_jobs,
                "job_paths": job_paths,
                "max_retries": resolved_max_retries,
                "prepared_only": True,
                "actual_upload_performed": False,
            }
            queue_path = queue_folder / "queue.json"
            self._write_json(queue_path, queue_record)

            latest_path = resolved_queue_dir / "latest.json"
            self._write_json(
                latest_path,
                {
                    "version": self.VERSION,
                    "queue_id": resolved_queue_id,
                    "created_at": created_at,
                    "queue_path": str(queue_path),
                    "queue_folder": str(queue_folder),
                },
            )

        except Exception as exc:
            return {
                "ok": False,
                "version": self.VERSION,
                "status": "queue_failed",
                "queued": False,
                "source_version": self._clean_text(source.get("version")),
                "queue_id": resolved_queue_id,
                "queue_path": "",
                "queue_folder": str(queue_folder),
                "job_count": len(jobs),
                "jobs": jobs,
                "job_paths": job_paths,
                "errors": [str(exc)],
                "warnings": validation["warnings"],
                "validation": validation,
            }

        result = {
            "ok": queue_ready,
            "version": self.VERSION,
            "status": "ready" if queue_ready else "partial",
            "queued": queue_ready,
            "queue_ready": queue_ready,
            "source_version": self._clean_text(source.get("version")),
            "queue_id": resolved_queue_id,
            "queue_folder": str(queue_folder),
            "queue_path": str(queue_path),
            "latest_pointer_path": str(latest_path),
            "job_count": len(jobs),
            "ready_job_count": len(ready_jobs),
            "ready_jobs": ready_jobs,
            "blocked_jobs": blocked_jobs,
            "jobs": jobs,
            "job_paths": job_paths,
            "errors": [],
            "warnings": validation["warnings"],
            "validation": validation,
        }

        print("[Sprint82-9 Queue] Version:", self.VERSION, flush=True)
        print("[Sprint82-9 Queue] Ready:", result["queue_ready"], flush=True)
        print("[Sprint82-9 Queue] Queue ID:", result["queue_id"], flush=True)
        print("[Sprint82-9 Queue] Jobs:", result["ready_jobs"], flush=True)
        print("[Sprint82-9 Queue] Path:", result["queue_path"], flush=True)

        return result

    def build(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Compatibility alias for callers that use build()."""
        return self.enqueue(*args, **kwargs)

    def add(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Compatibility alias for callers that use add()."""
        return self.enqueue(*args, **kwargs)

    def _validate_source(
        self,
        source: Dict[str, Any],
        manifest_path: str,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []

        if not source and not manifest_path:
            errors.append("PublisherResultStore 결과와 manifest 경로가 없습니다")
            return {"valid": False, "errors": errors, "warnings": warnings}

        if source:
            source_version = self._clean_text(source.get("version"))
            if source_version != self.SOURCE_VERSION:
                warnings.append("Sprint82-7 PublisherResultStore 버전이 아닙니다")
            if not bool(source.get("stored")):
                errors.append("Publisher 결과가 저장 완료 상태가 아닙니다")

        if not manifest_path:
            errors.append("manifest 경로가 없습니다")
        else:
            path = Path(manifest_path)
            if not path.exists() or not path.is_file():
                errors.append("manifest 파일을 찾을 수 없습니다")

        return {
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
        }

    def _video_path(self, platform_payload: Dict[str, Any]) -> str:
        payload = (
            platform_payload.get("payload")
            if isinstance(platform_payload.get("payload"), dict)
            else {}
        )
        return self._clean_text(
            payload.get("video_path")
            or platform_payload.get("video_path")
        )

    def _normalize_retry_count(self, value: Any) -> int:
        try:
            number = int(value)
        except (TypeError, ValueError):
            number = 3
        return max(0, min(number, 10))

    def _normalize_schedule(self, value: Any) -> str:
        cleaned = self._clean_text(value)
        if not cleaned:
            return ""
        try:
            parsed = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc).isoformat()
        except ValueError:
            return ""

    def _read_json(self, path: Path) -> Dict[str, Any]:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(f"JSON 객체가 아닙니다: {path}")
        return value

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

    def _queue_error(
        self,
        source: Dict[str, Any],
        queue_id: str,
        error: Exception,
        validation: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "ok": False,
            "version": self.VERSION,
            "status": "queue_failed",
            "queued": False,
            "source_version": self._clean_text(source.get("version")),
            "queue_id": queue_id,
            "queue_path": "",
            "job_count": 0,
            "jobs": {},
            "errors": [str(error)],
            "warnings": validation["warnings"],
            "validation": validation,
        }

    def _make_queue_id(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")

    def _make_suffix(self) -> str:
        return datetime.now(timezone.utc).strftime("%f")

    def _safe_name(self, value: Any) -> str:
        cleaned = self._clean_text(value)
        cleaned = re.sub(r"[^0-9A-Za-z가-힣._-]+", "_", cleaned)
        cleaned = cleaned.strip("._-")
        return cleaned[:140] or "queue"

    def _clean_text(self, value: Any) -> str:
        if value is None:
            return ""
        text = str(value)
        text = re.sub(r"\s+", " ", text)
        return text.strip()