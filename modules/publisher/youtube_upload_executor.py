from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import mimetypes
import re
from typing import Any, Dict, List, Optional


class YouTubeUploadExecutor:
    """
    Sprint83-2 YouTube Upload Executor

    역할:
    - Sprint83-1 UploadDispatcher의 youtube_shorts dispatch job을 입력으로 받음
    - 영상 파일, 제목, 설명, 태그, 공개 상태, 예약 시간을 검증
    - 기본 dry_run=True로 실제 업로드 없이 실행 준비 상태만 확인
    - execute=True일 때만 YouTube Data API videos.insert 호출
    - OAuth 토큰 파일을 재사용하고 필요 시 사용자 승인 흐름 실행
    - 업로드 성공 시 video_id / watch_url / API 응답 반환
    - 원본 dispatch job과 queue 파일은 직접 변경하지 않음
    """

    VERSION = "youtube-upload-executor-83-2"
    SOURCE_VERSION = "upload-dispatcher-83-1"
    PLATFORM = "youtube_shorts"
    EXECUTOR_NAME = "YouTubeUploadExecutor"
    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

    def execute(
        self,
        dispatch_job: Any = None,
        *,
        dry_run: bool = True,
        credentials_file: Any = "",
        token_file: Any = "",
        authorize: bool = False,
        notify_subscribers: bool = False,
        chunk_size: int = 8 * 1024 * 1024,
    ) -> Dict[str, Any]:
        source = dispatch_job if isinstance(dispatch_job, dict) else {}
        validation = self._validate_dispatch_job(source)

        if not validation["valid"]:
            return self._result(
                ok=False,
                status="invalid_dispatch_job",
                dry_run=dry_run,
                upload_ready=False,
                source=source,
                errors=validation["errors"],
                warnings=validation["warnings"],
            )

        payload = source.get("payload")
        payload = payload if isinstance(payload, dict) else {}

        normalized = self._normalize_upload_payload(
            source=source,
            payload=payload,
        )
        checks = self._build_checks(normalized)
        errors = [key for key, passed in checks.items() if not passed]
        warnings = list(validation["warnings"])

        upload_ready = not errors
        if not upload_ready:
            return self._result(
                ok=False,
                status="incomplete",
                dry_run=dry_run,
                upload_ready=False,
                source=source,
                normalized=normalized,
                checks=checks,
                errors=errors,
                warnings=warnings,
            )

        if dry_run:
            result = self._result(
                ok=True,
                status="dry_run_ready",
                dry_run=True,
                upload_ready=True,
                source=source,
                normalized=normalized,
                checks=checks,
                errors=[],
                warnings=warnings,
            )
            self._print_result(result)
            return result

        resolved_credentials_file = self._clean_text(credentials_file)
        resolved_token_file = self._clean_text(token_file)

        if not resolved_credentials_file:
            errors.append("credentials_file이 없습니다")
        if not resolved_token_file:
            errors.append("token_file이 없습니다")

        if errors:
            result = self._result(
                ok=False,
                status="credentials_missing",
                dry_run=False,
                upload_ready=False,
                source=source,
                normalized=normalized,
                checks=checks,
                errors=errors,
                warnings=warnings,
            )
            self._print_result(result)
            return result

        try:
            youtube = self._build_youtube_service(
                credentials_file=resolved_credentials_file,
                token_file=resolved_token_file,
                authorize=authorize,
            )
            response = self._upload_video(
                youtube=youtube,
                normalized=normalized,
                notify_subscribers=notify_subscribers,
                chunk_size=chunk_size,
            )
        except ModuleNotFoundError as exc:
            result = self._result(
                ok=False,
                status="dependency_missing",
                dry_run=False,
                upload_ready=False,
                source=source,
                normalized=normalized,
                checks=checks,
                errors=[
                    "Google API 라이브러리가 설치되지 않았습니다",
                    str(exc),
                ],
                warnings=warnings,
            )
            self._print_result(result)
            return result
        except Exception as exc:
            result = self._result(
                ok=False,
                status="upload_failed",
                dry_run=False,
                upload_ready=False,
                source=source,
                normalized=normalized,
                checks=checks,
                errors=[str(exc)],
                warnings=warnings,
            )
            self._print_result(result)
            return result

        video_id = self._clean_text(response.get("id"))
        result = self._result(
            ok=bool(video_id),
            status="uploaded" if video_id else "upload_response_missing_id",
            dry_run=False,
            upload_ready=bool(video_id),
            source=source,
            normalized=normalized,
            checks=checks,
            errors=[] if video_id else ["YouTube 응답에 video id가 없습니다"],
            warnings=warnings,
            extra={
                "video_id": video_id,
                "watch_url": (
                    f"https://www.youtube.com/watch?v={video_id}"
                    if video_id
                    else ""
                ),
                "api_response": response,
                "uploaded_at": self._utc_now(),
                "actual_upload_performed": bool(video_id),
            },
        )
        self._print_result(result)
        return result

    def run(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Compatibility alias."""
        return self.execute(*args, **kwargs)

    def upload(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Compatibility alias."""
        kwargs["dry_run"] = False
        return self.execute(*args, **kwargs)

    def _validate_dispatch_job(self, source: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []

        if not source:
            return {
                "valid": False,
                "errors": ["dispatch job이 비어 있습니다"],
                "warnings": warnings,
            }

        platform = self._clean_text(source.get("platform"))
        if platform != self.PLATFORM:
            errors.append(
                f"플랫폼이 {self.PLATFORM}이 아닙니다: {platform or 'empty'}"
            )

        executor = self._clean_text(source.get("executor"))
        if executor and executor != self.EXECUTOR_NAME:
            warnings.append(
                f"executor 값이 다릅니다: {executor}"
            )

        dispatch_status = self._clean_text(source.get("dispatch_status"))
        if dispatch_status != "ready":
            errors.append("dispatch_status가 ready가 아닙니다")

        payload = source.get("payload")
        if not isinstance(payload, dict):
            errors.append("payload가 딕셔너리가 아닙니다")

        source_version = self._clean_text(source.get("dispatcher_version"))
        if source_version and source_version != self.SOURCE_VERSION:
            warnings.append(
                f"Dispatcher 버전이 다릅니다: {source_version}"
            )

        return {
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
        }

    def _normalize_upload_payload(
        self,
        *,
        source: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        snippet = payload.get("snippet")
        snippet = snippet if isinstance(snippet, dict) else {}

        status = payload.get("status")
        status = status if isinstance(status, dict) else {}

        video_path = (
            self._clean_text(payload.get("video_path"))
            or self._clean_text(source.get("video_path"))
        )

        tags = snippet.get("tags")
        tags = tags if isinstance(tags, list) else []
        normalized_tags = []
        for tag in tags:
            cleaned = self._clean_text(tag)
            if cleaned and cleaned not in normalized_tags:
                normalized_tags.append(cleaned)

        privacy_status = self._clean_text(
            status.get("privacy_status")
            or status.get("privacyStatus")
            or "private"
        ).lower()
        if privacy_status not in {"private", "unlisted", "public"}:
            privacy_status = "private"

        publish_at = self._clean_text(
            status.get("publish_at")
            or status.get("publishAt")
        )

        normalized_status = {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": bool(
                status.get("self_declared_made_for_kids")
                if "self_declared_made_for_kids" in status
                else status.get("selfDeclaredMadeForKids", False)
            ),
            "containsSyntheticMedia": bool(
                status.get("contains_synthetic_media")
                if "contains_synthetic_media" in status
                else status.get("containsSyntheticMedia", False)
            ),
        }
        if publish_at:
            normalized_status["publishAt"] = publish_at

        normalized_snippet = {
            "title": self._shorten(snippet.get("title"), 100),
            "description": self._shorten(
                snippet.get("description"),
                5000,
            ),
            "categoryId": self._clean_text(
                snippet.get("category_id")
                or snippet.get("categoryId")
                or "22"
            ),
            "defaultLanguage": self._clean_text(
                snippet.get("default_language")
                or snippet.get("defaultLanguage")
                or "ko"
            ),
        }
        if normalized_tags:
            normalized_snippet["tags"] = normalized_tags

        return {
            "platform": self.PLATFORM,
            "queue_id": self._clean_text(source.get("queue_id")),
            "job_id": self._clean_text(source.get("job_id")),
            "job_path": self._clean_text(source.get("job_path")),
            "video_path": video_path,
            "snippet": normalized_snippet,
            "status": normalized_status,
            "mime_type": self._guess_mime_type(video_path),
            "request_body": {
                "snippet": normalized_snippet,
                "status": normalized_status,
            },
        }

    def _build_checks(self, normalized: Dict[str, Any]) -> Dict[str, bool]:
        video_path = Path(normalized.get("video_path", ""))
        snippet = normalized.get("snippet", {})
        status = normalized.get("status", {})

        publish_at = self._clean_text(status.get("publishAt"))
        privacy_status = self._clean_text(status.get("privacyStatus"))

        return {
            "has_video_path": bool(normalized.get("video_path")),
            "video_exists": video_path.is_file(),
            "has_title": bool(self._clean_text(snippet.get("title"))),
            "has_description": bool(
                self._clean_text(snippet.get("description"))
            ),
            "title_within_limit": len(
                self._clean_text(snippet.get("title"))
            ) <= 100,
            "description_within_limit": len(
                self._clean_text(snippet.get("description"))
            ) <= 5000,
            "privacy_status_valid": privacy_status
            in {"private", "unlisted", "public"},
            "schedule_valid": (
                not publish_at
                or privacy_status == "private"
            ),
        }

    def _build_youtube_service(
        self,
        *,
        credentials_file: str,
        token_file: str,
        authorize: bool,
    ) -> Any:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        credentials_path = Path(credentials_file).expanduser()
        token_path = Path(token_file).expanduser()

        if not credentials_path.is_file():
            raise FileNotFoundError(
                f"OAuth credentials 파일이 없습니다: {credentials_path}"
            )

        creds: Optional[Any] = None
        if token_path.is_file():
            creds = Credentials.from_authorized_user_file(
                str(token_path),
                self.SCOPES,
            )

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        if not creds or not creds.valid:
            if not authorize:
                raise RuntimeError(
                    "유효한 OAuth 토큰이 없습니다. authorize=True로 승인 절차를 실행하세요"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path),
                self.SCOPES,
            )
            creds = flow.run_local_server(
                port=0,
                access_type="offline",
                prompt="consent",
            )

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(
            creds.to_json(),
            encoding="utf-8",
        )

        return build(
            "youtube",
            "v3",
            credentials=creds,
            cache_discovery=False,
        )

    def _upload_video(
        self,
        *,
        youtube: Any,
        normalized: Dict[str, Any],
        notify_subscribers: bool,
        chunk_size: int,
    ) -> Dict[str, Any]:
        from googleapiclient.http import MediaFileUpload

        video_path = normalized["video_path"]
        media = MediaFileUpload(
            video_path,
            mimetype=normalized["mime_type"],
            chunksize=max(256 * 1024, int(chunk_size)),
            resumable=True,
        )

        request = youtube.videos().insert(
            part="snippet,status",
            body=normalized["request_body"],
            media_body=media,
            notifySubscribers=bool(notify_subscribers),
        )

        response = None
        while response is None:
            _status, response = request.next_chunk()

        return response if isinstance(response, dict) else {}

    def _result(
        self,
        *,
        ok: bool,
        status: str,
        dry_run: bool,
        upload_ready: bool,
        source: Dict[str, Any],
        normalized: Optional[Dict[str, Any]] = None,
        checks: Optional[Dict[str, bool]] = None,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        result = {
            "ok": ok,
            "version": self.VERSION,
            "status": status,
            "platform": self.PLATFORM,
            "source_version": self._clean_text(
                source.get("dispatcher_version")
            ),
            "queue_id": self._clean_text(source.get("queue_id")),
            "job_id": self._clean_text(source.get("job_id")),
            "job_path": self._clean_text(source.get("job_path")),
            "dry_run": bool(dry_run),
            "upload_ready": bool(upload_ready),
            "normalized_payload": normalized or {},
            "checks": checks or {},
            "errors": errors or [],
            "warnings": warnings or [],
            "actual_upload_performed": False,
        }
        if extra:
            result.update(extra)
        return result

    def _print_result(self, result: Dict[str, Any]) -> None:
        print("[Sprint83-2 YouTube Upload] Version:", self.VERSION, flush=True)
        print(
            "[Sprint83-2 YouTube Upload] Status:",
            result.get("status"),
            flush=True,
        )
        print(
            "[Sprint83-2 YouTube Upload] Ready:",
            result.get("upload_ready"),
            flush=True,
        )
        print(
            "[Sprint83-2 YouTube Upload] Dry Run:",
            result.get("dry_run"),
            flush=True,
        )
        print(
            "[Sprint83-2 YouTube Upload] Video ID:",
            result.get("video_id", ""),
            flush=True,
        )

    def _guess_mime_type(self, video_path: str) -> str:
        guessed, _ = mimetypes.guess_type(video_path)
        if guessed and guessed.startswith("video/"):
            return guessed
        return "video/mp4"

    def _shorten(self, value: Any, max_length: int) -> str:
        cleaned = self._clean_text(value)
        if len(cleaned) <= max_length:
            return cleaned
        return cleaned[: max(1, max_length - 1)].rstrip() + "…"

    def _clean_text(self, value: Any) -> str:
        if value is None:
            return ""
        return re.sub(r"\s+", " ", str(value)).strip()

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()