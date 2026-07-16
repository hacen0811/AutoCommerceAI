from __future__ import annotations

from typing import Any, Dict, List

from .instagram_publisher import InstagramPublisher
from .tiktok_publisher import TikTokPublisher
from .youtube_publisher import YouTubePublisher


class PublisherOrchestrator:
    """
    Sprint82-5 Publisher Orchestrator

    역할:
    - Sprint82-1 PublisherEngine 결과를 입력으로 받음
    - YouTube Shorts / Instagram Reels / TikTok Publisher를 한 번에 실행
    - 플랫폼별 업로드 직전 페이로드와 준비 상태를 하나의 결과로 통합
    - 실제 외부 API 업로드는 수행하지 않음
    - 원본 PublisherEngine 결과와 입력 설정을 변경하지 않음
    """

    VERSION = "publisher-orchestrator-82-5"
    SOURCE_VERSION = "publisher-engine-82-1"
    SUPPORTED_PLATFORMS = (
        "youtube_shorts",
        "instagram_reels",
        "tiktok",
    )

    def __init__(self) -> None:
        self.youtube_publisher = YouTubePublisher()
        self.instagram_publisher = InstagramPublisher()
        self.tiktok_publisher = TikTokPublisher()

    def build(
        self,
        publisher_result: Any = None,
        video_path: Any = "",
        platform_video_paths: Any = None,
        affiliate_link: Any = "",
        disclosure_text: Any = "",
        platform_settings: Any = None,
    ) -> Dict[str, Any]:
        source = publisher_result if isinstance(publisher_result, dict) else {}
        video_paths = (
            platform_video_paths
            if isinstance(platform_video_paths, dict)
            else {}
        )
        settings = (
            platform_settings
            if isinstance(platform_settings, dict)
            else {}
        )

        validation = self._validate_source(source)
        if not validation["valid"]:
            return {
                "ok": False,
                "version": self.VERSION,
                "status": "invalid_publisher_result",
                "orchestrator_ready": False,
                "source_version": self._clean_text(source.get("version")),
                "platform_count": 0,
                "ready_platform_count": 0,
                "ready_platforms": [],
                "failed_platforms": list(self.SUPPORTED_PLATFORMS),
                "platforms": {},
                "youtube_shorts": {},
                "instagram_reels": {},
                "tiktok": {},
                "errors": validation["errors"],
                "warnings": validation["warnings"],
                "validation": validation,
            }

        common_video_path = self._clean_text(video_path)
        resolved_affiliate_link = self._clean_text(affiliate_link)
        resolved_disclosure = self._clean_text(disclosure_text)

        youtube_result = self.youtube_publisher.build(
            publisher_result=source,
            video_path=self._platform_video_path(
                "youtube_shorts",
                video_paths,
                common_video_path,
            ),
            visibility=self._setting(
                settings,
                "youtube_shorts",
                "visibility",
                "private",
            ),
            schedule_at=self._setting(
                settings,
                "youtube_shorts",
                "schedule_at",
                "",
            ),
            affiliate_link=self._setting(
                settings,
                "youtube_shorts",
                "affiliate_link",
                resolved_affiliate_link,
            ),
            disclosure_text=self._setting(
                settings,
                "youtube_shorts",
                "disclosure_text",
                resolved_disclosure,
            ),
        )

        instagram_result = self.instagram_publisher.build(
            publisher_result=source,
            video_path=self._platform_video_path(
                "instagram_reels",
                video_paths,
                common_video_path,
            ),
            visibility=self._setting(
                settings,
                "instagram_reels",
                "visibility",
                "private",
            ),
            schedule_at=self._setting(
                settings,
                "instagram_reels",
                "schedule_at",
                "",
            ),
            affiliate_link=self._setting(
                settings,
                "instagram_reels",
                "affiliate_link",
                resolved_affiliate_link,
            ),
            disclosure_text=self._setting(
                settings,
                "instagram_reels",
                "disclosure_text",
                resolved_disclosure,
            ),
            cover_image_path=self._setting(
                settings,
                "instagram_reels",
                "cover_image_path",
                "",
            ),
            share_to_feed=self._bool_setting(
                settings,
                "instagram_reels",
                "share_to_feed",
                True,
            ),
        )

        tiktok_result = self.tiktok_publisher.build(
            publisher_result=source,
            video_path=self._platform_video_path(
                "tiktok",
                video_paths,
                common_video_path,
            ),
            visibility=self._setting(
                settings,
                "tiktok",
                "visibility",
                "private",
            ),
            schedule_at=self._setting(
                settings,
                "tiktok",
                "schedule_at",
                "",
            ),
            affiliate_link=self._setting(
                settings,
                "tiktok",
                "affiliate_link",
                resolved_affiliate_link,
            ),
            disclosure_text=self._setting(
                settings,
                "tiktok",
                "disclosure_text",
                resolved_disclosure,
            ),
            allow_comments=self._bool_setting(
                settings,
                "tiktok",
                "allow_comments",
                True,
            ),
            allow_duet=self._bool_setting(
                settings,
                "tiktok",
                "allow_duet",
                True,
            ),
            allow_stitch=self._bool_setting(
                settings,
                "tiktok",
                "allow_stitch",
                True,
            ),
        )

        platforms = {
            "youtube_shorts": youtube_result,
            "instagram_reels": instagram_result,
            "tiktok": tiktok_result,
        }
        ready_platforms = [
            platform
            for platform, result in platforms.items()
            if bool(result.get("upload_ready"))
        ]
        failed_platforms = [
            platform
            for platform in self.SUPPORTED_PLATFORMS
            if platform not in ready_platforms
        ]
        orchestrator_ready = len(ready_platforms) == len(
            self.SUPPORTED_PLATFORMS
        )

        errors = self._collect_messages(platforms, "errors")
        warnings = validation["warnings"] + self._collect_messages(
            platforms,
            "warnings",
        )

        result = {
            "ok": orchestrator_ready,
            "version": self.VERSION,
            "status": "ready" if orchestrator_ready else "partial",
            "orchestrator_ready": orchestrator_ready,
            "source_version": self._clean_text(source.get("version")),
            "platform_count": len(platforms),
            "ready_platform_count": len(ready_platforms),
            "ready_platforms": ready_platforms,
            "failed_platforms": failed_platforms,
            "platforms": platforms,
            "youtube_shorts": youtube_result,
            "instagram_reels": instagram_result,
            "tiktok": tiktok_result,
            "errors": errors,
            "warnings": self._unique(warnings),
            "validation": validation,
            "metadata": {
                "orchestrator_version": self.VERSION,
                "source_engine_version": self._clean_text(
                    source.get("version")
                ),
                "youtube_publisher_version": YouTubePublisher.VERSION,
                "instagram_publisher_version": InstagramPublisher.VERSION,
                "tiktok_publisher_version": TikTokPublisher.VERSION,
                "prepared_only": True,
                "actual_upload_performed": False,
            },
        }

        print("[Sprint82-5 Orchestrator] Version:", self.VERSION, flush=True)
        print(
            "[Sprint82-5 Orchestrator] Source:",
            result["source_version"],
            flush=True,
        )
        print(
            "[Sprint82-5 Orchestrator] Ready:",
            result["orchestrator_ready"],
            flush=True,
        )
        print(
            "[Sprint82-5 Orchestrator] Ready Platforms:",
            result["ready_platforms"],
            flush=True,
        )
        print(
            "[Sprint82-5 Orchestrator] Failed Platforms:",
            result["failed_platforms"],
            flush=True,
        )

        return result

    def generate(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Compatibility alias for callers that use generate()."""
        return self.build(*args, **kwargs)

    def _validate_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []

        if not source:
            errors.append("PublisherEngine 결과가 비어 있습니다")
            return {
                "valid": False,
                "errors": errors,
                "warnings": warnings,
            }

        source_version = self._clean_text(source.get("version"))
        if source_version != self.SOURCE_VERSION:
            warnings.append("Sprint82-1 PublisherEngine 버전이 아닙니다")

        if not bool(source.get("publisher_ready")):
            errors.append("PublisherEngine 결과가 준비 상태가 아닙니다")

        platforms = source.get("platforms")
        if not isinstance(platforms, dict):
            errors.append("PublisherEngine platforms 값이 딕셔너리가 아닙니다")
            return {
                "valid": False,
                "errors": errors,
                "warnings": warnings,
            }

        for platform in self.SUPPORTED_PLATFORMS:
            payload = platforms.get(platform)
            if not isinstance(payload, dict):
                errors.append(f"플랫폼 게시 데이터가 없습니다: {platform}")
                continue
            if not bool(payload.get("ready")):
                errors.append(
                    f"플랫폼 게시 데이터가 준비 상태가 아닙니다: {platform}"
                )

        return {
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
        }

    def _platform_video_path(
        self,
        platform: str,
        platform_video_paths: Dict[str, Any],
        common_video_path: str,
    ) -> str:
        platform_path = self._clean_text(
            platform_video_paths.get(platform)
        )
        return platform_path or common_video_path

    def _setting(
        self,
        settings: Dict[str, Any],
        platform: str,
        key: str,
        default: Any,
    ) -> Any:
        platform_settings = settings.get(platform)
        if not isinstance(platform_settings, dict):
            return default
        value = platform_settings.get(key, default)
        return default if value is None else value

    def _bool_setting(
        self,
        settings: Dict[str, Any],
        platform: str,
        key: str,
        default: bool,
    ) -> bool:
        value = self._setting(settings, platform, key, default)
        return value if isinstance(value, bool) else default

    def _collect_messages(
        self,
        platforms: Dict[str, Dict[str, Any]],
        key: str,
    ) -> List[str]:
        messages: List[str] = []
        for platform, result in platforms.items():
            values = result.get(key)
            if not isinstance(values, list):
                continue
            for value in values:
                cleaned = self._clean_text(value)
                if cleaned:
                    messages.append(f"{platform}: {cleaned}")
        return messages

    def _unique(self, values: List[Any]) -> List[str]:
        result: List[str] = []
        for value in values:
            cleaned = self._clean_text(value)
            if cleaned and cleaned not in result:
                result.append(cleaned)
        return result

    def _clean_text(self, value: Any) -> str:
        if value is None:
            return ""
        return " ".join(str(value).split()).strip()