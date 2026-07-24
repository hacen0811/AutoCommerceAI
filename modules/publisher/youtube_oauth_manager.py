from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import os
import re
from typing import Any, Dict, List, Optional


class YouTubeOAuthManager:
    """
    Sprint83-4 YouTube OAuth Manager

    역할:
    - YouTube Data API OAuth 클라이언트 비밀 파일과 사용자 토큰 관리
    - 토큰 존재/유효/만료 상태 검사
    - refresh_token이 있으면 만료된 access token 자동 갱신
    - 최초 승인 시 InstalledAppFlow.run_local_server() 실행
    - token.json을 UTF-8로 안전하게 저장
    - 인증 정보의 실제 secret/token 값은 반환하거나 로그에 출력하지 않음
    """

    VERSION = "youtube-oauth-manager-83-4"
    DEFAULT_SCOPES = (
        "https://www.googleapis.com/auth/youtube.upload",
    )

    def inspect(
        self,
        *,
        credentials_file: Any = "",
        token_file: Any = "",
        scopes: Any = None,
    ) -> Dict[str, Any]:
        resolved_scopes = self._normalize_scopes(scopes)
        credentials_path = self._resolve_path(credentials_file)
        token_path = self._resolve_path(token_file)

        dependency = self._dependency_status()
        credentials_check = self._inspect_credentials_file(credentials_path)
        token_check = self._inspect_token_file(
            token_path=token_path,
            scopes=resolved_scopes,
            dependency=dependency,
        )

        ready = (
            dependency["available"]
            and credentials_check["valid"]
            and token_check["valid"]
        )

        result = {
            "ok": ready,
            "version": self.VERSION,
            "status": "ready" if ready else "not_ready",
            "oauth_ready": ready,
            "credentials_file": str(credentials_path) if credentials_path else "",
            "token_file": str(token_path) if token_path else "",
            "scopes": list(resolved_scopes),
            "dependency": dependency,
            "credentials": credentials_check,
            "token": token_check,
            "errors": (
                dependency["errors"]
                + credentials_check["errors"]
                + token_check["errors"]
            ),
            "warnings": (
                dependency["warnings"]
                + credentials_check["warnings"]
                + token_check["warnings"]
            ),
        }

        self._print_status(result)
        return result

    def authorize(
        self,
        *,
        credentials_file: Any,
        token_file: Any,
        scopes: Any = None,
        force_reauthorize: bool = False,
        open_browser: bool = True,
        port: int = 0,
    ) -> Dict[str, Any]:
        resolved_scopes = self._normalize_scopes(scopes)
        credentials_path = self._resolve_path(credentials_file)
        token_path = self._resolve_path(token_file)

        dependency = self._dependency_status()
        if not dependency["available"]:
            return self._failure(
                status="dependency_missing",
                credentials_path=credentials_path,
                token_path=token_path,
                scopes=resolved_scopes,
                errors=dependency["errors"],
                warnings=dependency["warnings"],
            )

        credentials_check = self._inspect_credentials_file(credentials_path)
        if not credentials_check["valid"]:
            return self._failure(
                status="invalid_credentials_file",
                credentials_path=credentials_path,
                token_path=token_path,
                scopes=resolved_scopes,
                errors=credentials_check["errors"],
                warnings=credentials_check["warnings"],
            )

        try:
            creds, source = self._load_or_authorize(
                credentials_path=credentials_path,
                token_path=token_path,
                scopes=resolved_scopes,
                force_reauthorize=force_reauthorize,
                open_browser=open_browser,
                port=port,
            )
        except Exception as exc:
            result = self._failure(
                status="authorization_failed",
                credentials_path=credentials_path,
                token_path=token_path,
                scopes=resolved_scopes,
                errors=[str(exc)],
                warnings=[],
            )
            self._print_status(result)
            return result

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(
            creds.to_json(),
            encoding="utf-8",
        )

        result = {
            "ok": bool(creds and creds.valid),
            "version": self.VERSION,
            "status": "authorized" if creds and creds.valid else "invalid_token",
            "oauth_ready": bool(creds and creds.valid),
            "credentials_file": str(credentials_path),
            "token_file": str(token_path),
            "scopes": list(resolved_scopes),
            "credential_source": source,
            "token": self._credential_summary(creds),
            "saved": token_path.is_file(),
            "authorized_at": self._utc_now(),
            "errors": [],
            "warnings": [],
        }
        self._print_status(result)
        return result

    def refresh(
        self,
        *,
        token_file: Any,
        scopes: Any = None,
    ) -> Dict[str, Any]:
        resolved_scopes = self._normalize_scopes(scopes)
        token_path = self._resolve_path(token_file)
        dependency = self._dependency_status()

        if not dependency["available"]:
            return self._failure(
                status="dependency_missing",
                credentials_path=None,
                token_path=token_path,
                scopes=resolved_scopes,
                errors=dependency["errors"],
                warnings=dependency["warnings"],
            )

        if not token_path or not token_path.is_file():
            return self._failure(
                status="token_missing",
                credentials_path=None,
                token_path=token_path,
                scopes=resolved_scopes,
                errors=["token 파일이 없습니다"],
                warnings=[],
            )

        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials

            creds = Credentials.from_authorized_user_file(
                str(token_path),
                list(resolved_scopes),
            )

            if creds.valid:
                result = {
                    "ok": True,
                    "version": self.VERSION,
                    "status": "already_valid",
                    "oauth_ready": True,
                    "token_file": str(token_path),
                    "scopes": list(resolved_scopes),
                    "token": self._credential_summary(creds),
                    "saved": True,
                    "errors": [],
                    "warnings": [],
                }
                self._print_status(result)
                return result

            if not creds.expired:
                raise RuntimeError("토큰이 유효하지 않지만 만료 상태도 아닙니다")

            if not creds.refresh_token:
                raise RuntimeError("refresh_token이 없어 자동 갱신할 수 없습니다")

            creds.refresh(Request())
            token_path.write_text(
                creds.to_json(),
                encoding="utf-8",
            )
        except Exception as exc:
            result = self._failure(
                status="refresh_failed",
                credentials_path=None,
                token_path=token_path,
                scopes=resolved_scopes,
                errors=[str(exc)],
                warnings=[],
            )
            self._print_status(result)
            return result

        result = {
            "ok": bool(creds.valid),
            "version": self.VERSION,
            "status": "refreshed" if creds.valid else "refresh_invalid",
            "oauth_ready": bool(creds.valid),
            "token_file": str(token_path),
            "scopes": list(resolved_scopes),
            "token": self._credential_summary(creds),
            "saved": token_path.is_file(),
            "refreshed_at": self._utc_now(),
            "errors": [],
            "warnings": [],
        }
        self._print_status(result)
        return result

    def revoke_local_token(
        self,
        *,
        token_file: Any,
    ) -> Dict[str, Any]:
        token_path = self._resolve_path(token_file)
        if not token_path or not token_path.exists():
            return {
                "ok": True,
                "version": self.VERSION,
                "status": "token_already_absent",
                "token_file": str(token_path) if token_path else "",
                "deleted": False,
                "errors": [],
                "warnings": [],
            }

        try:
            token_path.unlink()
        except Exception as exc:
            return {
                "ok": False,
                "version": self.VERSION,
                "status": "token_delete_failed",
                "token_file": str(token_path),
                "deleted": False,
                "errors": [str(exc)],
                "warnings": [],
            }

        return {
            "ok": True,
            "version": self.VERSION,
            "status": "token_deleted",
            "token_file": str(token_path),
            "deleted": True,
            "errors": [],
            "warnings": [
                "로컬 token 파일만 삭제했습니다. Google 계정 권한 철회는 별도로 필요합니다"
            ],
        }

    def get_credentials(
        self,
        *,
        credentials_file: Any,
        token_file: Any,
        scopes: Any = None,
        authorize_if_needed: bool = False,
        open_browser: bool = True,
        port: int = 0,
    ) -> Any:
        """
        YouTubeUploadExecutor 등 내부 호출자가 사용할 Credentials 객체 반환.
        외부 사용자 응답에는 토큰 문자열을 노출하지 않습니다.
        """
        resolved_scopes = self._normalize_scopes(scopes)
        credentials_path = self._resolve_path(credentials_file)
        token_path = self._resolve_path(token_file)

        creds, _source = self._load_or_authorize(
            credentials_path=credentials_path,
            token_path=token_path,
            scopes=resolved_scopes,
            force_reauthorize=False,
            open_browser=open_browser,
            port=port,
            authorize_if_needed=authorize_if_needed,
        )

        if not creds or not creds.valid:
            raise RuntimeError("유효한 YouTube OAuth credentials를 만들지 못했습니다")

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(
            creds.to_json(),
            encoding="utf-8",
        )
        return creds

    def _load_or_authorize(
        self,
        *,
        credentials_path: Path,
        token_path: Path,
        scopes: tuple[str, ...],
        force_reauthorize: bool,
        open_browser: bool,
        port: int,
        authorize_if_needed: bool = True,
    ) -> tuple[Any, str]:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow

        creds: Optional[Any] = None
        source = "none"

        if token_path.is_file() and not force_reauthorize:
            creds = Credentials.from_authorized_user_file(
                str(token_path),
                list(scopes),
            )
            source = "token_file"

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            source = "refreshed_token"

        if creds and creds.valid:
            return creds, source

        if not authorize_if_needed:
            raise RuntimeError(
                "유효한 token이 없습니다. authorize_if_needed=True가 필요합니다"
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(credentials_path),
            scopes=list(scopes),
        )
        creds = flow.run_local_server(
            host="localhost",
            port=max(0, int(port)),
            open_browser=bool(open_browser),
            access_type="offline",
            prompt="consent",
            success_message=(
                "YouTube 인증이 완료되었습니다. 이 창을 닫아도 됩니다."
            ),
        )
        return creds, "browser_authorization"

    def _dependency_status(self) -> Dict[str, Any]:
        missing: List[str] = []

        for module_name, package_name in (
            ("google.auth", "google-auth"),
            ("google_auth_oauthlib", "google-auth-oauthlib"),
            ("googleapiclient", "google-api-python-client"),
        ):
            try:
                __import__(module_name)
            except Exception:
                missing.append(package_name)

        return {
            "available": not missing,
            "missing_packages": missing,
            "errors": (
                []
                if not missing
                else [
                    "Google OAuth 의존성이 설치되지 않았습니다: "
                    + ", ".join(missing)
                ]
            ),
            "warnings": [],
        }

    def _inspect_credentials_file(
        self,
        path: Optional[Path],
    ) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []
        client_type = ""

        if not path:
            errors.append("credentials_file 경로가 없습니다")
            return {
                "exists": False,
                "valid": False,
                "client_type": client_type,
                "errors": errors,
                "warnings": warnings,
            }

        if not path.is_file():
            errors.append(f"credentials 파일이 없습니다: {path}")
            return {
                "exists": False,
                "valid": False,
                "client_type": client_type,
                "errors": errors,
                "warnings": warnings,
            }

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"credentials JSON 읽기 실패: {exc}")
            return {
                "exists": True,
                "valid": False,
                "client_type": client_type,
                "errors": errors,
                "warnings": warnings,
            }

        if isinstance(data.get("installed"), dict):
            client_type = "installed"
            client_data = data["installed"]
        elif isinstance(data.get("web"), dict):
            client_type = "web"
            client_data = data["web"]
            warnings.append(
                "데스크톱 앱에서는 installed 유형 OAuth 클라이언트를 권장합니다"
            )
        else:
            client_data = {}
            errors.append("credentials JSON에 installed 또는 web 구성이 없습니다")

        for key in ("client_id", "client_secret", "auth_uri", "token_uri"):
            if not self._clean_text(client_data.get(key)):
                errors.append(f"credentials 필수 값이 없습니다: {key}")

        return {
            "exists": True,
            "valid": not errors,
            "client_type": client_type,
            "file_size": path.stat().st_size,
            "errors": errors,
            "warnings": warnings,
        }

    def _inspect_token_file(
        self,
        *,
        token_path: Optional[Path],
        scopes: tuple[str, ...],
        dependency: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not token_path:
            return {
                "exists": False,
                "valid": False,
                "expired": False,
                "refreshable": False,
                "errors": ["token_file 경로가 없습니다"],
                "warnings": [],
            }

        if not token_path.is_file():
            return {
                "exists": False,
                "valid": False,
                "expired": False,
                "refreshable": False,
                "errors": ["token 파일이 아직 없습니다"],
                "warnings": [],
            }

        if not dependency["available"]:
            return {
                "exists": True,
                "valid": False,
                "expired": False,
                "refreshable": False,
                "errors": [],
                "warnings": [
                    "의존성이 없어 token 유효성을 검사하지 못했습니다"
                ],
            }

        try:
            from google.oauth2.credentials import Credentials

            creds = Credentials.from_authorized_user_file(
                str(token_path),
                list(scopes),
            )
        except Exception as exc:
            return {
                "exists": True,
                "valid": False,
                "expired": False,
                "refreshable": False,
                "errors": [f"token 읽기 실패: {exc}"],
                "warnings": [],
            }

        summary = self._credential_summary(creds)
        summary.update(
            {
                "exists": True,
                "errors": [],
                "warnings": (
                    []
                    if creds.valid
                    else ["token이 유효하지 않습니다"]
                ),
            }
        )
        return summary

    def _credential_summary(self, creds: Any) -> Dict[str, Any]:
        expiry = getattr(creds, "expiry", None)
        granted_scopes = list(getattr(creds, "scopes", None) or [])

        return {
            "valid": bool(getattr(creds, "valid", False)),
            "expired": bool(getattr(creds, "expired", False)),
            "refreshable": bool(getattr(creds, "refresh_token", None)),
            "expiry": expiry.isoformat() if expiry else "",
            "granted_scopes": granted_scopes,
            "has_access_token": bool(getattr(creds, "token", None)),
            "has_refresh_token": bool(
                getattr(creds, "refresh_token", None)
            ),
        }

    def _failure(
        self,
        *,
        status: str,
        credentials_path: Optional[Path],
        token_path: Optional[Path],
        scopes: tuple[str, ...],
        errors: List[str],
        warnings: List[str],
    ) -> Dict[str, Any]:
        result = {
            "ok": False,
            "version": self.VERSION,
            "status": status,
            "oauth_ready": False,
            "credentials_file": (
                str(credentials_path) if credentials_path else ""
            ),
            "token_file": str(token_path) if token_path else "",
            "scopes": list(scopes),
            "errors": errors,
            "warnings": warnings,
        }
        self._print_status(result)
        return result

    def _normalize_scopes(self, scopes: Any) -> tuple[str, ...]:
        values = (
            list(scopes)
            if isinstance(scopes, (list, tuple, set))
            else list(self.DEFAULT_SCOPES)
        )
        result: List[str] = []
        for value in values:
            cleaned = self._clean_text(value)
            if cleaned and cleaned not in result:
                result.append(cleaned)
        return tuple(result or self.DEFAULT_SCOPES)

    def _resolve_path(self, value: Any) -> Optional[Path]:
        cleaned = self._clean_text(value)
        if not cleaned:
            return None
        return Path(os.path.expandvars(cleaned)).expanduser()

    def _print_status(self, result: Dict[str, Any]) -> None:
        print("[Sprint83-4 YouTube OAuth] Version:", self.VERSION, flush=True)
        print(
            "[Sprint83-4 YouTube OAuth] Status:",
            result.get("status", ""),
            flush=True,
        )
        print(
            "[Sprint83-4 YouTube OAuth] Ready:",
            bool(result.get("oauth_ready")),
            flush=True,
        )
        print(
            "[Sprint83-4 YouTube OAuth] Token:",
            result.get("token_file", ""),
            flush=True,
        )

    def _clean_text(self, value: Any) -> str:
        if value is None:
            return ""
        return re.sub(r"\s+", " ", str(value)).strip()

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()