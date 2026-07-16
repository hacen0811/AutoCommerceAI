from __future__ import annotations

import re
from typing import Any, Dict, List


class TikTokPublisher:
    """
    Sprint82-4 TikTok Publisher

    역할:
    - Sprint82-1 PublisherEngine의 tiktok 게시 준비 데이터를 입력으로 받음
    - 실제 TikTok API 호출 없이 업로드 직전 페이로드를 생성
    - 캡션, 해시태그, CTA, 공개 상태, 예약 시간, 제휴 고지 문구를 검증
    - 원본 입력을 변경하지 않고 독립적으로 동작
    """

    VERSION = "tiktok-publisher-82-4"
    SOURCE_VERSION = "publisher-engine-82-1"
    PLATFORM = "tiktok"

    def build(
        self,
        publisher_result: Any = None,
        video_path: Any = "",
        visibility: str = "private",
        schedule_at: Any = "",
        affiliate_link: Any = "",
        disclosure_text: Any = "",
        allow_comments: bool = True,
        allow_duet: bool = True,
        allow_stitch: bool = True,
    ) -> Dict[str, Any]:
        source = publisher_result if isinstance(publisher_result, dict) else {}
        platform_payload = self._extract_platform_payload(source)

        validation = self._validate_source(source, platform_payload)
        if not validation["valid"]:
            return {
                "ok": False,
                "version": self.VERSION,
                "status": "invalid_publisher_payload",
                "upload_ready": False,
                "platform": self.PLATFORM,
                "source_version": self._clean_text(source.get("version")),
                "payload": {},
                "checks": {},
                "errors": validation["errors"],
                "warnings": validation["warnings"],
                "validation": validation,
            }

        title = self._shorten(platform_payload.get("title"), 100)
        script = self._clean_text(platform_payload.get("script"))
        cta = self._clean_text(platform_payload.get("cta"))
        hashtags = self._normalize_hashtags(platform_payload.get("hashtags"))
        hashtag_text = self._build_hashtag_text(hashtags)

        resolved_disclosure = self._clean_text(disclosure_text)
        if not resolved_disclosure and self._clean_text(affiliate_link):
            resolved_disclosure = (
                "이 게시물은 쿠팡 파트너스 활동의 일환으로, "
                "이에 따른 일정액의 수수료를 제공받습니다."
            )

        caption = self._build_caption(
            base_description=platform_payload.get("description"),
            cta=cta,
            affiliate_link=affiliate_link,
            disclosure_text=resolved_disclosure,
            hashtag_text=hashtag_text,
        )

        resolved_visibility = self._normalize_visibility(visibility)
        resolved_schedule = self._clean_text(schedule_at)
        resolved_video_path = self._clean_text(video_path)

        checks = {
            "source_ready": bool(platform_payload.get("ready")),
            "has_title": bool(title),
            "has_caption": bool(caption),
            "has_script": bool(script),
            "has_video_path": bool(resolved_video_path),
            "title_within_limit": len(title) <= 100,
            "caption_within_limit": len(caption) <= 2200,
            "visibility_valid": resolved_visibility in {
                "private",
                "public",
                "friends",
            },
            "schedule_valid": not resolved_schedule
            or resolved_visibility == "private",
        }

        upload_ready = all(checks.values())
        errors = [key for key, passed in checks.items() if not passed]

        payload = {
            "platform": self.PLATFORM,
            "video_path": resolved_video_path,
            "title": title,
            "caption": caption,
            "hashtags": hashtags,
            "publish_settings": {
                "visibility": resolved_visibility,
                "schedule_at": resolved_schedule,
                "allow_comments": bool(allow_comments),
                "allow_duet": bool(allow_duet),
                "allow_stitch": bool(allow_stitch),
            },
            "content": {
                "script": script,
                "cta": cta,
                "affiliate_link": self._clean_text(affiliate_link),
                "disclosure_text": resolved_disclosure,
                "thumbnail_prompt": self._clean_text(
                    platform_payload.get("thumbnail_prompt")
                ),
            },
            "metadata": {
                "publisher_version": self.VERSION,
                "source_engine_version": self._clean_text(source.get("version")),
                "source_export_version": self._clean_text(
                    source.get("source_export_version")
                ),
                "prepared_only": True,
                "actual_upload_performed": False,
            },
        }

        result = {
            "ok": upload_ready,
            "version": self.VERSION,
            "status": "ready" if upload_ready else "incomplete",
            "upload_ready": upload_ready,
            "platform": self.PLATFORM,
            "source_version": self._clean_text(source.get("version")),
            "payload": payload,
            "checks": checks,
            "errors": errors,
            "warnings": validation["warnings"],
            "validation": validation,
        }

        print("[Sprint82-4 TikTok] Version:", self.VERSION, flush=True)
        print(
            "[Sprint82-4 TikTok] Source:",
            result["source_version"],
            flush=True,
        )
        print(
            "[Sprint82-4 TikTok] Ready:",
            result["upload_ready"],
            flush=True,
        )
        print(
            "[Sprint82-4 TikTok] Title:",
            payload["title"],
            flush=True,
        )
        print(
            "[Sprint82-4 TikTok] Video:",
            payload["video_path"],
            flush=True,
        )

        return result

    def generate(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Compatibility alias for callers that use generate()."""
        return self.build(*args, **kwargs)

    def _extract_platform_payload(self, source: Dict[str, Any]) -> Dict[str, Any]:
        direct = source.get(self.PLATFORM)
        if isinstance(direct, dict):
            return direct

        platforms = source.get("platforms")
        if isinstance(platforms, dict):
            nested = platforms.get(self.PLATFORM)
            if isinstance(nested, dict):
                return nested

        return {}

    def _validate_source(
        self,
        source: Dict[str, Any],
        platform_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []

        if not source:
            errors.append("Publisher 결과가 비어 있습니다")
            return {"valid": False, "errors": errors, "warnings": warnings}

        source_version = self._clean_text(source.get("version"))
        if source_version != self.SOURCE_VERSION:
            warnings.append("Sprint82-1 PublisherEngine 버전이 아닙니다")

        if not bool(source.get("publisher_ready")):
            errors.append("Publisher 결과가 준비 상태가 아닙니다")

        if not platform_payload:
            errors.append("tiktok 게시 데이터가 없습니다")
            return {"valid": False, "errors": errors, "warnings": warnings}

        if not bool(platform_payload.get("ready")):
            errors.append("tiktok 게시 데이터가 준비 상태가 아닙니다")

        required = {
            "title": platform_payload.get("title"),
            "description": platform_payload.get("description"),
            "script": platform_payload.get("script"),
            "cta": platform_payload.get("cta"),
        }
        for key, value in required.items():
            if not self._clean_text(value):
                errors.append(f"필수 값이 없습니다: {key}")

        if not self._normalize_hashtags(platform_payload.get("hashtags")):
            warnings.append("TikTok 해시태그가 비어 있습니다")

        return {
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
        }

    def _build_caption(
        self,
        base_description: Any,
        cta: Any,
        affiliate_link: Any,
        disclosure_text: Any,
        hashtag_text: Any,
    ) -> str:
        parts: List[str] = []

        for value in (
            base_description,
            cta,
            affiliate_link,
            disclosure_text,
            hashtag_text,
        ):
            cleaned = self._clean_text(value)
            if cleaned and cleaned not in parts:
                parts.append(cleaned)

        return self._shorten("\n\n".join(parts), 2200)

    def _normalize_visibility(self, value: Any) -> str:
        cleaned = self._clean_text(value).lower()
        if cleaned in {"private", "public", "friends"}:
            return cleaned
        return "private"

    def _normalize_hashtags(self, value: Any) -> List[str]:
        values = value if isinstance(value, list) else []
        result: List[str] = []
        for item in values:
            cleaned = re.sub(
                r"[^0-9A-Za-z가-힣_]",
                "",
                self._clean_text(item).lstrip("#"),
            )
            if cleaned and cleaned not in result:
                result.append(cleaned)
        return result

    def _build_hashtag_text(self, hashtags: List[str]) -> str:
        return " ".join(f"#{tag}" for tag in hashtags)

    def _shorten(self, value: Any, max_length: int) -> str:
        cleaned = self._clean_text(value)
        if len(cleaned) <= max_length:
            return cleaned
        return cleaned[: max(1, max_length - 1)].rstrip() + "…"

    def _clean_text(self, value: Any) -> str:
        if value is None:
            return ""
        text = str(value)
        text = re.sub(r"\s+", " ", text)
        return text.strip()