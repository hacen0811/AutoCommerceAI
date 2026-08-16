from __future__ import annotations

import json
import os
import random
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


class YouTubeUploadExecutor:
    """YouTube Data API v3 uploader used by the reservation worker.

    The reservation worker calls this class only when the queue item becomes due.
    Therefore privacy_status='public' publishes immediately at the reserved time.
    """

    VERSION = "youtube-upload-executor-194-77-4-metadata-schedule"
    SCOPES = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.force-ssl",
    ]

    TOKEN_CANDIDATES = (
        "config/youtube/token.json",
        "credentials/youtube_token.json",
        "data/youtube/token.json",
        "token.json",
    )
    CLIENT_SECRET_CANDIDATES = (
        "config/youtube/client_secret.json",
        "credentials/client_secret.json",
        "client_secret.json",
        "client_secrets.json",
    )

    def __init__(self, project_root: Optional[str] = None) -> None:
        self.project_root = Path(project_root or os.getcwd()).resolve()
        self.manifest_dir = self.project_root / "data" / "publisher" / "youtube_manifests"
        self.manifest_dir.mkdir(parents=True, exist_ok=True)

    def execute(
        self,
        video_path: str,
        title: str = "",
        description: str = "",
        privacy_status: str = "private",
        payload: Optional[Dict[str, Any]] = None,
        **_: Any,
    ) -> Dict[str, Any]:
        payload = dict(payload or {})
        path = Path(video_path).resolve()
        if not path.is_file() or path.stat().st_size < 1024:
            raise FileNotFoundError(f"YouTube 업로드 영상이 없습니다: {path}")

        resolved_title = self._clean_title(title or payload.get("title") or path.stem)
        resolved_description = str(description or payload.get("description") or "").strip()
        resolved_privacy = str(
            payload.get("youtube_privacy_status") or privacy_status or "private"
        ).lower().strip()
        if resolved_privacy not in {"private", "unlisted", "public"}:
            resolved_privacy = "private"

        youtube = self._build_service(payload=payload)
        publish_at = str(
            payload.get("youtube_publish_at")
            or payload.get("publish_at")
            or payload.get("publishAt")
            or ""
        ).strip()
        if publish_at:
            # YouTube scheduled publishing requires the video to be private until publishAt.
            resolved_privacy = "private"

        request_body = {
            "snippet": {
                "title": resolved_title,
                "description": resolved_description,
                "categoryId": str(payload.get("youtube_category_id") or "22"),
                "tags": self._normalize_tags(payload.get("tags") or payload.get("hashtags")),
                "defaultLanguage": str(payload.get("default_language") or "ko"),
                "defaultAudioLanguage": str(payload.get("default_audio_language") or "ko"),
            },
            "status": {
                "privacyStatus": resolved_privacy,
                "selfDeclaredMadeForKids": bool(payload.get("made_for_kids", False)),
                "embeddable": True,
                "publicStatsViewable": True,
            },
        }
        if publish_at:
            request_body["status"]["publishAt"] = publish_at

        from googleapiclient.http import MediaFileUpload

        media = MediaFileUpload(
            str(path),
            chunksize=8 * 1024 * 1024,
            resumable=True,
            mimetype="video/mp4",
        )
        request = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media,
            notifySubscribers=bool(payload.get("notify_subscribers", False)),
        )
        response = self._execute_resumable(request)
        video_id = str(response.get("id") or "").strip()
        if not video_id:
            raise RuntimeError(f"YouTube 응답에 video id가 없습니다: {response}")

        thumbnail_result: Dict[str, Any] = {"ok": False, "status": "not_requested"}
        thumbnail_path = str(payload.get("thumbnail_path") or "").strip()
        if thumbnail_path and Path(thumbnail_path).is_file():
            thumbnail_result = self._upload_thumbnail(youtube, video_id, thumbnail_path)

        comment_result: Dict[str, Any] = {"ok": False, "status": "not_requested"}
        comment_text = str(
            payload.get("pinned_comment")
            or payload.get("fixed_comment")
            or payload.get("comment")
            or ""
        ).strip()
        if comment_text:
            comment_result = self._insert_top_level_comment(youtube, video_id, comment_text)

        uploaded_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        result = {
            "ok": True,
            "version": self.VERSION,
            "status": "uploaded",
            "platform": "youtube",
            "actual_upload_performed": True,
            "video_id": video_id,
            "watch_url": f"https://www.youtube.com/watch?v={video_id}",
            "shorts_url": f"https://www.youtube.com/shorts/{video_id}",
            "privacy_status": resolved_privacy,
            "uploaded_at": uploaded_at,
            "thumbnail": thumbnail_result,
            "comment": comment_result,
            "comment_pin_status": "manual_required",
            "comment_pin_note": "YouTube Data API로 댓글 작성은 가능하지만 고정은 지원되지 않아 Studio에서 수동 고정해야 합니다.",
        }
        result["manifest_path"] = self._write_manifest(video_id, result, payload, path)
        print(
            f"[Sprint182-1 YouTube Reserved Upload] SUCCESS video_id={video_id} privacy={resolved_privacy}",
            flush=True,
        )
        return result

    upload = execute
    run = execute
    publish = execute

    @staticmethod
    def _safe_account_key(value: str) -> str:
        mapping = {
            "실물로그": "silmullog",
            "하센맘": "hasenmom",
            "역사쿠키": "history_cookie_ko",
            "History Cookie": "history_cookie_en",
        }
        raw = str(value or "").strip()
        return mapping.get(raw, re.sub(r"[^0-9A-Za-z_-]+", "_", raw).strip("_").lower())

    def _account_token_candidates(self, payload: Dict[str, Any]) -> tuple[str, ...]:
        account = str(payload.get("youtube_account") or payload.get("channel") or "실물로그").strip()
        key = self._safe_account_key(account)
        if account == "실물로그":
            return tuple(self.TOKEN_CANDIDATES)
        return (
            f"config/youtube/token_{key}.json",
            f"credentials/youtube_token_{key}.json",
            f"data/youtube/token_{key}.json",
        )

    def _build_service(self, payload: Optional[Dict[str, Any]] = None):
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise RuntimeError(
                "YouTube 업로드 패키지가 없습니다. 실행: "
                "pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"
            ) from exc

        payload = dict(payload or {})
        account = str(payload.get("youtube_account") or payload.get("channel") or "실물로그").strip()
        token_candidates = self._account_token_candidates(payload)
        token_path = self._first_existing(token_candidates)
        client_secret_path = self._first_existing(self.CLIENT_SECRET_CANDIDATES)
        credentials = None
        if token_path:
            try:
                credentials = Credentials.from_authorized_user_file(str(token_path), self.SCOPES)
            except Exception:
                credentials = None

        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            self._save_token(credentials, token_path or self._default_token_path())

        if not credentials or not credentials.valid:
            if not client_secret_path:
                raise FileNotFoundError(
                    "YouTube OAuth client secret이 없습니다. 다음 중 한 곳에 두세요: "
                    + ", ".join(self.CLIENT_SECRET_CANDIDATES)
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), self.SCOPES)
            credentials = flow.run_local_server(port=0, access_type="offline", prompt="consent")
            if token_path is None:
                token_path = (
                    self._default_token_path()
                    if account == "실물로그"
                    else self.project_root / token_candidates[0]
                )
            self._save_token(credentials, token_path)
            print(
                "[Sprint194-77 YouTube OAuth] AUTHORIZED",
                {"account": account, "token_path": str(token_path)},
                flush=True,
            )

        return build("youtube", "v3", credentials=credentials, cache_discovery=False)

    def _execute_resumable(self, request, max_retries: int = 8) -> Dict[str, Any]:
        response = None
        retry = 0
        while response is None:
            try:
                status, response = request.next_chunk()
                if status:
                    percent = int(status.progress() * 100)
                    print(f"[Sprint182-1 YouTube Upload] progress={percent}%", flush=True)
            except Exception as exc:
                retry += 1
                if retry > max_retries or not self._is_retryable(exc):
                    raise
                delay = min(64, (2 ** retry) + random.random())
                print(
                    f"[Sprint182-1 YouTube Upload] retry={retry} delay={delay:.1f}s error={type(exc).__name__}: {exc}",
                    flush=True,
                )
                time.sleep(delay)
        return dict(response or {})

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        status = getattr(getattr(exc, "resp", None), "status", None)
        return status in {500, 502, 503, 504} or isinstance(exc, (OSError, TimeoutError))

    def _upload_thumbnail(self, youtube, video_id: str, thumbnail_path: str) -> Dict[str, Any]:
        try:
            from googleapiclient.http import MediaFileUpload

            response = youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path, resumable=False),
            ).execute()
            return {"ok": True, "status": "uploaded", "response": response}
        except Exception as exc:
            return {"ok": False, "status": "failed", "error": f"{type(exc).__name__}: {exc}"}

    @staticmethod
    def _insert_top_level_comment(youtube, video_id: str, text: str) -> Dict[str, Any]:
        try:
            response = youtube.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "topLevelComment": {"snippet": {"textOriginal": text}},
                    }
                },
            ).execute()
            comment_id = (
                response.get("snippet", {})
                .get("topLevelComment", {})
                .get("id", "")
            )
            return {"ok": True, "status": "created", "comment_id": comment_id}
        except Exception as exc:
            return {"ok": False, "status": "failed", "error": f"{type(exc).__name__}: {exc}"}

    def _first_existing(self, candidates: Iterable[str]) -> Optional[Path]:
        for candidate in candidates:
            path = (self.project_root / candidate).resolve()
            if path.is_file():
                return path
        return None

    def _default_token_path(self) -> Path:
        path = self.project_root / "config" / "youtube" / "token.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _save_token(credentials, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(credentials.to_json(), encoding="utf-8")

    @staticmethod
    def _clean_title(value: str) -> str:
        cleaned = " ".join(str(value).replace("\x00", " ").split()).strip()
        return (cleaned or "쇼핑 쇼츠")[:100]

    @staticmethod
    def _normalize_tags(value: Any) -> list[str]:
        if isinstance(value, str):
            raw = value.replace("#", " ").replace(",", " ").split()
        elif isinstance(value, (list, tuple, set)):
            raw = list(value)
        else:
            raw = []
        result: list[str] = []
        for item in raw:
            tag = " ".join(str(item).split()).strip().lstrip("#")
            if tag and tag not in result:
                result.append(tag[:30])
        return result[:30]

    def _write_manifest(
        self,
        video_id: str,
        result: Dict[str, Any],
        payload: Dict[str, Any],
        source_path: Path,
    ) -> str:
        target = self.manifest_dir / f"{video_id}.json"
        document = {
            "version": self.VERSION,
            "source_video": str(source_path),
            "payload": payload,
            "result": result,
        }
        target.write_text(json.dumps(document, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return str(target)
