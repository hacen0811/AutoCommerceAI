from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import re
from typing import Any, Dict, List, Tuple


class UploadDispatcher:
    """
    Sprint83-1 Upload Dispatcher

    역할:
    - Sprint82-9 UploadQueueEngine 결과 또는 queue.json을 입력으로 받음
    - queued 작업과 예약 시간이 도래한 scheduled 작업만 선별
    - blocked / uploading / uploaded / failed 작업은 자동 제외
    - 플랫폼별 실행기 호출 직전 dispatch payload를 생성
    - 실제 업로드나 외부 API 호출은 수행하지 않음
    - persist=True인 경우 작업 상태를 dispatch_ready로 안전하게 저장
    """

    VERSION = "upload-dispatcher-83-1"
    SOURCE_VERSION = "upload-queue-engine-82-9"
    SUPPORTED_PLATFORMS = (
        "youtube_shorts",
        "instagram_reels",
        "tiktok",
    )
    DISPATCHABLE_STATUSES = {"queued", "scheduled", "retry_wait"}
    TERMINAL_STATUSES = {"uploaded", "cancelled", "blocked"}

    def dispatch(
        self,
        queue_result: Any = None,
        queue_path: Any = "",
        now: Any = "",
        platforms: Any = None,
        max_jobs: Any = 0,
        persist: bool = False,
    ) -> Dict[str, Any]:
        source = queue_result if isinstance(queue_result, dict) else {}
        resolved_queue_path = self._clean_text(queue_path)
        if not resolved_queue_path:
            resolved_queue_path = self._clean_text(source.get("queue_path"))

        validation = self._validate_source(source, resolved_queue_path)
        if not validation["valid"]:
            return {
                "ok": False,
                "version": self.VERSION,
                "status": "invalid_queue_result",
                "dispatch_ready": False,
                "source_version": self._clean_text(source.get("version")),
                "queue_id": self._clean_text(source.get("queue_id")),
                "queue_path": resolved_queue_path,
                "dispatch_count": 0,
                "dispatch_jobs": {},
                "skipped_jobs": {},
                "errors": validation["errors"],
                "warnings": validation["warnings"],
                "validation": validation,
            }

        try:
            queue_record = self._read_json(Path(resolved_queue_path))
        except Exception as exc:
            return self._error_result(
                source=source,
                queue_path=resolved_queue_path,
                error=exc,
                validation=validation,
            )

        resolved_now = self._normalize_now(now)
        requested_platforms = self._normalize_platforms(platforms)
        resolved_max_jobs = self._normalize_max_jobs(max_jobs)
        queue_folder = Path(resolved_queue_path).parent
        job_paths = self._resolve_job_paths(source, queue_record, queue_folder)

        dispatch_jobs: Dict[str, Dict[str, Any]] = {}
        skipped_jobs: Dict[str, Dict[str, Any]] = {}
        warnings = list(validation["warnings"])
        errors: List[str] = []

        for platform in self.SUPPORTED_PLATFORMS:
            if requested_platforms and platform not in requested_platforms:
                skipped_jobs[platform] = {
                    "platform": platform,
                    "reason": "platform_not_requested",
                }
                continue

            job_path = self._clean_text(job_paths.get(platform))
            if not job_path:
                skipped_jobs[platform] = {
                    "platform": platform,
                    "reason": "job_path_missing",
                }
                continue

            try:
                job = self._read_json(Path(job_path))
            except Exception as exc:
                errors.append(f"{platform}: {exc}")
                skipped_jobs[platform] = {
                    "platform": platform,
                    "reason": "job_read_failed",
                    "error": str(exc),
                    "job_path": job_path,
                }
                continue

            eligibility = self._check_eligibility(job, resolved_now)
            if not eligibility["eligible"]:
                skipped_jobs[platform] = {
                    "platform": platform,
                    "reason": eligibility["reason"],
                    "status": self._clean_text(job.get("status")),
                    "scheduled_at": self._clean_text(job.get("scheduled_at")),
                    "job_path": job_path,
                }
                continue

            dispatch_payload = self._build_dispatch_payload(
                platform=platform,
                job=job,
                job_path=job_path,
                queue_record=queue_record,
                now=resolved_now,
            )
            dispatch_jobs[platform] = dispatch_payload

            if persist:
                try:
                    updated_job = dict(job)
                    updated_job["status"] = "dispatch_ready"
                    updated_job["dispatch_ready_at"] = resolved_now.isoformat()
                    updated_job["dispatcher_version"] = self.VERSION
                    self._write_json(Path(job_path), updated_job)
                except Exception as exc:
                    warnings.append(f"{platform} 상태 저장 실패: {exc}")

            if resolved_max_jobs and len(dispatch_jobs) >= resolved_max_jobs:
                break

        dispatch_count = len(dispatch_jobs)
        dispatch_ready = dispatch_count > 0 and not errors
        status = "ready" if dispatch_ready else "no_dispatchable_jobs"
        if errors and dispatch_count:
            status = "partial"
        elif errors and not dispatch_count:
            status = "dispatch_failed"

        result = {
            "ok": dispatch_ready,
            "version": self.VERSION,
            "status": status,
            "dispatch_ready": dispatch_ready,
            "source_version": self._clean_text(
                source.get("version") or queue_record.get("version")
            ),
            "queue_id": self._clean_text(
                source.get("queue_id") or queue_record.get("queue_id")
            ),
            "queue_path": resolved_queue_path,
            "evaluated_at": resolved_now.isoformat(),
            "dispatch_count": dispatch_count,
            "dispatch_platforms": list(dispatch_jobs.keys()),
            "dispatch_jobs": dispatch_jobs,
            "skipped_job_count": len(skipped_jobs),
            "skipped_jobs": skipped_jobs,
            "persisted": bool(persist),
            "actual_upload_performed": False,
            "errors": errors,
            "warnings": warnings,
            "validation": validation,
        }

        print("[Sprint83-1 Dispatcher] Version:", self.VERSION, flush=True)
        print(
            "[Sprint83-1 Dispatcher] Queue ID:",
            result["queue_id"],
            flush=True,
        )
        print(
            "[Sprint83-1 Dispatcher] Ready:",
            result["dispatch_ready"],
            flush=True,
        )
        print(
            "[Sprint83-1 Dispatcher] Jobs:",
            result["dispatch_platforms"],
            flush=True,
        )
        print(
            "[Sprint83-1 Dispatcher] Skipped:",
            list(result["skipped_jobs"].keys()),
            flush=True,
        )

        return result

    def build(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Compatibility alias for callers that use build()."""
        return self.dispatch(*args, **kwargs)

    def run(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Compatibility alias for callers that use run()."""
        return self.dispatch(*args, **kwargs)

    def _validate_source(
        self,
        source: Dict[str, Any],
        queue_path: str,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []

        if not source and not queue_path:
            errors.append("UploadQueueEngine 결과와 queue 경로가 없습니다")
            return {"valid": False, "errors": errors, "warnings": warnings}

        if source:
            source_version = self._clean_text(source.get("version"))
            if source_version and source_version != self.SOURCE_VERSION:
                warnings.append("Sprint82-9 UploadQueueEngine 버전이 아닙니다")
            if source.get("queue_ready") is False:
                warnings.append("Queue 결과가 전체 준비 상태가 아닙니다")

        if not queue_path:
            errors.append("queue.json 경로가 없습니다")
        else:
            path = Path(queue_path)
            if not path.exists() or not path.is_file():
                errors.append("queue.json 파일을 찾을 수 없습니다")

        return {
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
        }

    def _resolve_job_paths(
        self,
        source: Dict[str, Any],
        queue_record: Dict[str, Any],
        queue_folder: Path,
    ) -> Dict[str, str]:
        paths: Dict[str, str] = {}
        candidates = []
        for value in (source.get("job_paths"), queue_record.get("job_paths")):
            if isinstance(value, dict):
                candidates.append(value)

        for platform in self.SUPPORTED_PLATFORMS:
            for candidate in candidates:
                path = self._clean_text(candidate.get(platform))
                if path:
                    paths[platform] = path
                    break
            if platform not in paths:
                fallback = queue_folder / "jobs" / f"{platform}.json"
                if fallback.exists():
                    paths[platform] = str(fallback)
        return paths

    def _check_eligibility(
        self,
        job: Dict[str, Any],
        now: datetime,
    ) -> Dict[str, Any]:
        status = self._clean_text(job.get("status")).lower()

        if status in self.TERMINAL_STATUSES:
            return {"eligible": False, "reason": f"terminal_status:{status}"}
        if status in {"uploading", "dispatch_ready"}:
            return {"eligible": False, "reason": f"already_processing:{status}"}
        if status == "failed":
            attempt_count = self._to_int(job.get("attempt_count"), 0)
            max_retries = self._to_int(job.get("max_retries"), 0)
            if attempt_count >= max_retries:
                return {"eligible": False, "reason": "retry_limit_reached"}
            next_retry = self._parse_datetime(job.get("next_retry_at"))
            if next_retry and next_retry > now:
                return {"eligible": False, "reason": "retry_not_due"}
        elif status not in self.DISPATCHABLE_STATUSES:
            return {"eligible": False, "reason": f"status_not_dispatchable:{status}"}

        if not bool(job.get("queue_ready")):
            return {"eligible": False, "reason": "queue_not_ready"}
        if not bool(job.get("upload_ready")):
            return {"eligible": False, "reason": "upload_not_ready"}

        scheduled_at = self._parse_datetime(job.get("scheduled_at"))
        if scheduled_at and scheduled_at > now:
            return {"eligible": False, "reason": "schedule_not_due"}

        return {"eligible": True, "reason": "ready"}

    def _build_dispatch_payload(
        self,
        platform: str,
        job: Dict[str, Any],
        job_path: str,
        queue_record: Dict[str, Any],
        now: datetime,
    ) -> Dict[str, Any]:
        payload = job.get("payload") if isinstance(job.get("payload"), dict) else {}
        return {
            "dispatcher_version": self.VERSION,
            "platform": platform,
            "queue_id": self._clean_text(job.get("queue_id")),
            "job_id": self._clean_text(job.get("job_id")),
            "job_path": job_path,
            "dispatch_status": "ready",
            "dispatch_ready_at": now.isoformat(),
            "video_path": self._clean_text(job.get("video_path")),
            "payload": payload,
            "attempt_count": self._to_int(job.get("attempt_count"), 0),
            "max_retries": self._to_int(job.get("max_retries"), 0),
            "scheduled_at": self._clean_text(job.get("scheduled_at")),
            "executor": self._executor_name(platform),
            "metadata": {
                "queue_version": self._clean_text(queue_record.get("version")),
                "prepared_only": True,
                "actual_upload_performed": False,
            },
        }

    def _executor_name(self, platform: str) -> str:
        return {
            "youtube_shorts": "YouTubeUploadExecutor",
            "instagram_reels": "InstagramUploadExecutor",
            "tiktok": "TikTokUploadExecutor",
        }.get(platform, "UnknownUploadExecutor")

    def _normalize_platforms(self, value: Any) -> List[str]:
        if value is None or value == "":
            return []
        values = value if isinstance(value, (list, tuple, set)) else [value]
        result: List[str] = []
        for item in values:
            platform = self._clean_text(item).lower()
            if platform in self.SUPPORTED_PLATFORMS and platform not in result:
                result.append(platform)
        return result

    def _normalize_max_jobs(self, value: Any) -> int:
        number = self._to_int(value, 0)
        return max(0, min(number, len(self.SUPPORTED_PLATFORMS)))

    def _normalize_now(self, value: Any) -> datetime:
        parsed = self._parse_datetime(value)
        return parsed or datetime.now(timezone.utc)

    def _parse_datetime(self, value: Any) -> datetime | None:
        cleaned = self._clean_text(value)
        if not cleaned:
            return None
        try:
            parsed = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            return None

    def _read_json(self, path: Path) -> Dict[str, Any]:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(f"JSON 객체가 아닙니다: {path}")
        return value

    def _write_json(self, path: Path, value: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(value, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        temporary.replace(path)

    def _error_result(
        self,
        source: Dict[str, Any],
        queue_path: str,
        error: Exception,
        validation: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "ok": False,
            "version": self.VERSION,
            "status": "dispatch_failed",
            "dispatch_ready": False,
            "source_version": self._clean_text(source.get("version")),
            "queue_id": self._clean_text(source.get("queue_id")),
            "queue_path": queue_path,
            "dispatch_count": 0,
            "dispatch_jobs": {},
            "skipped_jobs": {},
            "errors": [str(error)],
            "warnings": validation["warnings"],
            "validation": validation,
        }

    def _to_int(self, value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _clean_text(self, value: Any) -> str:
        if value is None:
            return ""
        text = str(value)
        text = re.sub(r"\s+", " ", text)
        return text.strip()