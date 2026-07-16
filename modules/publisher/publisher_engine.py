from __future__ import annotations

import re
from typing import Any, Dict, List


class PublisherEngine:
    """
    Sprint82-1 Publisher Engine

    역할:
    - Sprint81-10 Export Pack을 입력으로 받음
    - TikTok / Instagram Reels / YouTube Shorts 게시용 데이터를 생성
    - 실제 업로드나 외부 API 호출 없이 게시 준비 데이터만 구성
    - 입력 Export Pack을 변경하지 않고 독립적으로 동작
    """

    VERSION = "publisher-engine-82-1"
    SUPPORTED_PLATFORMS = (
        "tiktok",
        "instagram_reels",
        "youtube_shorts",
    )

    def build(self, export_pack: Any = None) -> Dict[str, Any]:
        pack = export_pack if isinstance(export_pack, dict) else {}

        validation = self._validate_export_pack(pack)
        if not validation["valid"]:
            return {
                "ok": False,
                "version": self.VERSION,
                "status": "invalid_export_pack",
                "publisher_ready": False,
                "source_export_version": self._clean_text(pack.get("version")),
                "platform_count": 0,
                "platforms": {},
                "validation": validation,
                "errors": validation["errors"],
                "warnings": validation["warnings"],
            }

        product_name = self._clean_text(pack.get("product_name"))
        title = self._clean_text(pack.get("title"))
        description = self._clean_text(pack.get("description"))
        hashtags = self._normalize_hashtags(pack.get("hashtags"))
        hashtag_text = self._clean_text(pack.get("hashtag_text"))
        if not hashtag_text:
            hashtag_text = " ".join(f"#{tag}" for tag in hashtags)

        platform_scripts = (
            pack.get("platform_scripts")
            if isinstance(pack.get("platform_scripts"), dict)
            else {}
        )
        platform_cta = (
            pack.get("platform_cta")
            if isinstance(pack.get("platform_cta"), dict)
            else {}
        )

        platforms = {
            platform: self._build_platform_payload(
                platform=platform,
                product_name=product_name,
                base_title=title,
                base_description=description,
                script=self._clean_text(platform_scripts.get(platform)),
                cta=self._clean_text(platform_cta.get(platform)),
                hashtags=hashtags,
                hashtag_text=hashtag_text,
                export_pack=pack,
            )
            for platform in self.SUPPORTED_PLATFORMS
        }

        ready_platforms = [
            platform
            for platform, payload in platforms.items()
            if payload.get("ready")
        ]
        publisher_ready = len(ready_platforms) == len(self.SUPPORTED_PLATFORMS)

        result = {
            "ok": publisher_ready,
            "version": self.VERSION,
            "status": "ready" if publisher_ready else "partial",
            "publisher_ready": publisher_ready,
            "source_export_version": self._clean_text(pack.get("version")),
            "product_name": product_name,
            "platform_count": len(platforms),
            "ready_platform_count": len(ready_platforms),
            "ready_platforms": ready_platforms,
            "platforms": platforms,
            "youtube_shorts": platforms["youtube_shorts"],
            "instagram_reels": platforms["instagram_reels"],
            "tiktok": platforms["tiktok"],
            "validation": validation,
            "errors": [],
            "warnings": validation["warnings"],
            "metadata": {
                "engine_version": self.VERSION,
                "source_generator_version": self._clean_text(
                    self._dict_value(pack, "metadata", "generator_version")
                ),
                "source_export_ready": bool(pack.get("ready")),
                "source_validation_passed": bool(pack.get("validation_passed")),
                "supported_platforms": list(self.SUPPORTED_PLATFORMS),
            },
        }

        print("[Sprint82-1 Publisher] Version:", self.VERSION, flush=True)
        print(
            "[Sprint82-1 Publisher] Source Export:",
            result["source_export_version"],
            flush=True,
        )
        print(
            "[Sprint82-1 Publisher] Ready:",
            result["publisher_ready"],
            flush=True,
        )
        print(
            "[Sprint82-1 Publisher] Platforms:",
            result["ready_platforms"],
            flush=True,
        )
        for platform, payload in platforms.items():
            print(
                f"[Sprint82-1 Publisher] {platform}:",
                {
                    "ready": payload.get("ready", False),
                    "title": payload.get("title", ""),
                    "script_length": len(payload.get("script", "")),
                },
                flush=True,
            )

        return result

    def generate(self, export_pack: Any = None) -> Dict[str, Any]:
        """Compatibility alias for callers that use generate()."""
        return self.build(export_pack=export_pack)

    def _build_platform_payload(
        self,
        platform: str,
        product_name: str,
        base_title: str,
        base_description: str,
        script: str,
        cta: str,
        hashtags: List[str],
        hashtag_text: str,
        export_pack: Dict[str, Any],
    ) -> Dict[str, Any]:
        title = self._platform_title(platform, base_title, product_name)
        description = self._platform_description(
            platform=platform,
            base_description=base_description,
            cta=cta,
            hashtag_text=hashtag_text,
        )
        limits = self._platform_limits(platform)
        checks = {
            "has_script": bool(script),
            "has_title": bool(title),
            "has_description": bool(description),
            "has_cta": bool(cta),
            "title_within_limit": len(title) <= limits["title_max"],
            "description_within_limit": len(description) <= limits["description_max"],
        }
        ready = all(checks.values())

        return {
            "platform": platform,
            "ready": ready,
            "title": title,
            "description": description,
            "script": script,
            "cta": cta,
            "hashtags": list(hashtags),
            "hashtag_text": hashtag_text,
            "thumbnail_prompt": self._clean_text(export_pack.get("thumbnail_prompt")),
            "checks": checks,
            "limits": limits,
            "upload_metadata": {
                "visibility": "private",
                "schedule_at": "",
                "affiliate_link": "",
                "disclosure_text": "",
                "upload_status": "prepared",
            },
        }

    def _validate_export_pack(self, pack: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        warnings: List[str] = []

        if not pack:
            errors.append("Export Pack이 비어 있습니다")
            return {"valid": False, "errors": errors, "warnings": warnings}

        if self._clean_text(pack.get("version")) != "script-export-pack-81-10":
            warnings.append("Sprint81-10 Export Pack 버전이 아닙니다")

        if not bool(pack.get("ready")):
            errors.append("Export Pack ready 값이 True가 아닙니다")

        if not bool(pack.get("validation_passed")):
            errors.append("최종 대본 검증을 통과하지 못했습니다")

        required_text = {
            "product_name": pack.get("product_name"),
            "title": pack.get("title"),
            "description": pack.get("description"),
            "best_hook": pack.get("best_hook"),
        }
        for key, value in required_text.items():
            if not self._clean_text(value):
                errors.append(f"필수 값이 없습니다: {key}")

        platform_scripts = pack.get("platform_scripts")
        if not isinstance(platform_scripts, dict):
            errors.append("platform_scripts가 딕셔너리가 아닙니다")
        else:
            for platform in self.SUPPORTED_PLATFORMS:
                if not self._clean_text(platform_scripts.get(platform)):
                    errors.append(f"플랫폼 대본이 없습니다: {platform}")

        platform_cta = pack.get("platform_cta")
        if not isinstance(platform_cta, dict):
            errors.append("platform_cta가 딕셔너리가 아닙니다")
        else:
            for platform in self.SUPPORTED_PLATFORMS:
                if not self._clean_text(platform_cta.get(platform)):
                    errors.append(f"플랫폼 CTA가 없습니다: {platform}")

        if not self._normalize_hashtags(pack.get("hashtags")):
            warnings.append("해시태그가 비어 있습니다")

        return {
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
        }

    def _platform_title(
        self,
        platform: str,
        base_title: str,
        product_name: str,
    ) -> str:
        title = self._clean_text(base_title)
        if not title:
            title = product_name

        max_length = self._platform_limits(platform)["title_max"]
        return self._shorten(title, max_length)

    def _platform_description(
        self,
        platform: str,
        base_description: str,
        cta: str,
        hashtag_text: str,
    ) -> str:
        parts = [self._clean_text(base_description)]
        if cta:
            parts.append(self._sentence(cta))
        if hashtag_text:
            parts.append(hashtag_text)

        description = "\n\n".join(part for part in parts if part)
        return self._shorten(
            description,
            self._platform_limits(platform)["description_max"],
        )

    def _platform_limits(self, platform: str) -> Dict[str, int]:
        # Sprint82-1 internal preparation limits. External API constraints are
        # intentionally not enforced until each platform publisher is added.
        limits = {
            "tiktok": {"title_max": 100, "description_max": 2200},
            "instagram_reels": {"title_max": 100, "description_max": 2200},
            "youtube_shorts": {"title_max": 100, "description_max": 5000},
        }
        return dict(limits.get(platform, {"title_max": 100, "description_max": 2200}))

    def _normalize_hashtags(self, value: Any) -> List[str]:
        values = value if isinstance(value, list) else []
        result: List[str] = []
        for item in values:
            cleaned = re.sub(r"[^0-9A-Za-z가-힣_]", "", self._clean_text(item).lstrip("#"))
            if cleaned and cleaned not in result:
                result.append(cleaned)
        return result

    def _dict_value(self, source: Dict[str, Any], key: str, nested_key: str) -> Any:
        nested = source.get(key)
        if not isinstance(nested, dict):
            return ""
        return nested.get(nested_key, "")

    def _sentence(self, text: Any) -> str:
        cleaned = self._clean_text(text)
        if not cleaned:
            return ""
        if cleaned[-1] in ".!?":
            return cleaned
        return f"{cleaned}."

    def _shorten(self, text: Any, max_length: int) -> str:
        cleaned = self._clean_text(text)
        if len(cleaned) <= max_length:
            return cleaned
        return cleaned[: max(1, max_length - 1)].rstrip() + "…"

    def _clean_text(self, value: Any) -> str:
        if value is None:
            return ""
        text = str(value)
        text = re.sub(r"\s+", " ", text)
        return text.strip()