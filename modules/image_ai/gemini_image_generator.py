from __future__ import annotations

import base64
import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List


class GeminiImageGenerator:
    """
    Sprint152-2 Single Reference Scene Generation with network retry.

    대표 상품사진 1장과 장면 프롬프트를 Gemini에 전달합니다.
    WinError 10054 및 일시적인 네트워크/서버 오류는 자동 재시도합니다.
    """

    VERSION = "gemini-image-generator-157-cost-guard"
    DEFAULT_MODEL = "gemini-3.1-flash-image-preview"
    SUPPORTED_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}

    # 최초 호출 + 최대 3회 재시도
    MAX_PROVIDER_ATTEMPTS = 4
    RETRY_DELAYS_SECONDS = (2, 5, 10)

    TRANSIENT_ERROR_TOKENS = (
        "connectionreseterror",
        "winerror 10054",
        "connection reset",
        "connection aborted",
        "connection closed",
        "remotedisconnected",
        "readtimeout",
        "connecttimeout",
        "timed out",
        "timeout",
        "temporarily unavailable",
        "service unavailable",
        "internal server error",
        "bad gateway",
        "gateway timeout",
        "429",
        "500",
        "502",
        "503",
        "504",
        "resource exhausted",
    )

    def __init__(self, api_key: Any = "", model: Any = "") -> None:
        self.api_key = str(
            api_key
            or os.getenv("GEMINI_API_KEY", "")
            or os.getenv("GOOGLE_API_KEY", "")
        ).strip()
        self.model = str(
            model
            or os.getenv("GEMINI_IMAGE_MODEL", "")
            or self.DEFAULT_MODEL
        ).strip()

    def generate_image(
        self,
        scene_id: Any = "",
        attempt: Any = 1,
        prompt: Any = "",
        image_prompt: Any = "",
        negative_prompt: Any = "",
        reference_image_path: Any = "",
        reference_image_paths: Any = None,
        require_reference_image: bool = False,
        output_image_path: Any = "",
        output_path: Any = "",
        overwrite: bool = True,
        **_: Any,
    ) -> Dict[str, Any]:
        scene_id_text = str(scene_id or "").strip() or "scene_unknown"
        prompt_text = str(image_prompt or prompt or "").strip()
        negative_text = str(negative_prompt or "").strip()
        references = self._resolve_reference_paths(
            reference_image_path,
            reference_image_paths,
        )[:1]
        target = Path(
            str(output_image_path or output_path or "")
        ).expanduser()

        result: Dict[str, Any] = {
            "ok": False,
            "ready": False,
            "version": self.VERSION,
            "status": "not_run",
            "provider": "google_genai",
            "model": self.model,
            "scene_id": scene_id_text,
            "attempt": self._safe_int(attempt, 1),
            "prompt": prompt_text,
            "negative_prompt": negative_text,
            "reference_image_path": str(references[0]) if references else "",
            "reference_image_paths": [str(path) for path in references],
            "reference_image_count": len(references),
            "require_reference_image": True,
            "generation_mode": "single_reference_scene_generation",
            "output_image_path": str(target),
            "output_path": str(target),
            "mime_type": "",
            "image_bytes": 0,
            "text_response": "",
            "provider_attempts": 0,
            "network_retry_count": 0,
            "retry_delays_seconds": [],
            "provider_errors": [],
            "errors": [],
            "warnings": [],
            "preserved_review_image_path": "",
            "preservation_status": "not_run",
            "fatal_error": False,
            "fatal_error_code": "",
            "cost_guard_triggered": False,
        }

        if not self.api_key:
            result["status"] = "api_key_missing"
            result["errors"].append(
                "GEMINI_API_KEY 또는 GOOGLE_API_KEY가 설정되지 않았습니다."
            )
            return result
        if not prompt_text:
            result["status"] = "prompt_missing"
            result["errors"].append("이미지 생성 프롬프트가 없습니다.")
            return result
        if not str(target).strip() or str(target) == ".":
            result["status"] = "output_path_missing"
            result["errors"].append("출력 이미지 경로가 없습니다.")
            return result
        if not references:
            result["status"] = "reference_image_missing"
            result["errors"].append(
                "대표 상품 참조 이미지 1장이 필요합니다."
            )
            return result

        if target.suffix.lower() not in self.SUPPORTED_SUFFIXES:
            target = target.with_suffix(".png")
        result["output_image_path"] = str(target)
        result["output_path"] = str(target)

        if target.exists() and not overwrite:
            result.update(
                ok=True,
                ready=True,
                status="reused_existing",
                image_bytes=target.stat().st_size,
            )
            return result

        try:
            from google import genai
            from google.genai import types
            from PIL import Image
        except Exception as exc:
            result["status"] = "dependency_import_failed"
            result["errors"].append(
                f"{type(exc).__name__}: {exc}. "
                "pip install -U google-genai pillow 를 실행하세요."
            )
            return result

        try:
            with Image.open(references[0]) as image:
                reference_image = image.convert("RGB").copy()
        except Exception as exc:
            result["status"] = "reference_image_load_failed"
            result["errors"].append(f"{type(exc).__name__}: {exc}")
            return result

        final_prompt = self._build_final_prompt(
            prompt_text,
            negative_text,
        )

        response = None
        for provider_attempt in range(1, self.MAX_PROVIDER_ATTEMPTS + 1):
            result["provider_attempts"] = provider_attempt
            print(
                f"[Sprint152-2 Retry] Scene {scene_id_text} "
                f"Provider Attempt {provider_attempt}/{self.MAX_PROVIDER_ATTEMPTS}",
                flush=True,
            )
            try:
                client = genai.Client(api_key=self.api_key)
                response = client.models.generate_content(
                    model=self.model,
                    contents=[reference_image, final_prompt],
                    config=types.GenerateContentConfig(
                        response_modalities=["TEXT", "IMAGE"]
                    ),
                )
                print(
                    f"[Sprint152-2 Retry] Scene {scene_id_text} "
                    f"Provider Success {provider_attempt}/{self.MAX_PROVIDER_ATTEMPTS}",
                    flush=True,
                )
                break
            except Exception as exc:
                error_text = f"{type(exc).__name__}: {exc}"
                transient = self._is_transient_error(exc)
                result["provider_errors"].append(
                    {
                        "provider_attempt": provider_attempt,
                        "error": error_text,
                        "transient": transient,
                    }
                )
                print(
                    f"[Sprint152-2 Retry] Scene {scene_id_text} "
                    f"Provider Error {provider_attempt}/{self.MAX_PROVIDER_ATTEMPTS}: "
                    f"{error_text}",
                    flush=True,
                )

                fatal_code = self._fatal_provider_error_code(error_text)
                if fatal_code:
                    result["status"] = "fatal_provider_error"
                    result["fatal_error"] = True
                    result["fatal_error_code"] = fatal_code
                    result["cost_guard_triggered"] = True
                    result["errors"].append(error_text)
                    print(
                        "[Sprint157 Cost Guard] FATAL:",
                        fatal_code,
                        "Scene:",
                        scene_id_text,
                        flush=True,
                    )
                    return result

                has_next = provider_attempt < self.MAX_PROVIDER_ATTEMPTS
                if not transient or not has_next:
                    result["status"] = (
                        "provider_error_after_retries"
                        if transient
                        else "provider_error"
                    )
                    result["errors"].append(error_text)
                    print(
                        f"[Sprint152-2 Retry] Scene {scene_id_text} "
                        f"Failed after {provider_attempt} provider attempts",
                        flush=True,
                    )
                    return result

                delay = self.RETRY_DELAYS_SECONDS[
                    min(
                        provider_attempt - 1,
                        len(self.RETRY_DELAYS_SECONDS) - 1,
                    )
                ]
                result["network_retry_count"] += 1
                result["retry_delays_seconds"].append(delay)
                print(
                    f"[Sprint152-2 Retry] Scene {scene_id_text} "
                    f"Waiting {delay} sec",
                    flush=True,
                )
                time.sleep(delay)

        if response is None:
            result["status"] = "provider_error_after_retries"
            result["errors"].append(
                "Gemini 응답이 생성되지 않았습니다."
            )
            return result

        image_data, mime_type, text_response = self._extract_response(
            response
        )
        result["text_response"] = text_response
        if not image_data:
            result["status"] = "image_not_returned"
            result["errors"].append(
                "Gemini 응답에서 생성 이미지 데이터를 찾지 못했습니다."
            )
            return result

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(image_data)
            if not target.is_file() or target.stat().st_size <= 0:
                raise RuntimeError("저장된 이미지 파일이 비어 있습니다.")
        except Exception as exc:
            result["status"] = "image_save_failed"
            result["errors"].append(f"{type(exc).__name__}: {exc}")
            return result

        preserved_path = self._preserve_generated_attempt(
            source_path=target,
            scene_id=scene_id_text,
            attempt=result["attempt"],
        )

        result.update(
            ok=True,
            ready=True,
            status="generated_single_reference_scene",
            mime_type=mime_type or "image/png",
            image_bytes=target.stat().st_size,
            output_image_path=str(target),
            output_path=str(target),
            preserved_review_image_path=preserved_path,
            preservation_status=(
                "preserved"
                if preserved_path
                else "preservation_failed"
            ),
        )
        print(
            "[Sprint152-2 Single Reference] Scene:",
            scene_id_text,
            "Closed Loop Attempt:",
            result["attempt"],
            "Provider Attempts:",
            result["provider_attempts"],
            "Network Retries:",
            result["network_retry_count"],
            "Status:",
            result["status"],
            "Reference:",
            result["reference_image_path"],
            "Output:",
            result["output_image_path"],
            "Bytes:",
            result["image_bytes"],
            flush=True,
        )
        return result

    def _preserve_generated_attempt(
        self,
        source_path: Path,
        scene_id: str,
        attempt: int,
    ) -> str:
        """
        생성 직후 검수 결과와 관계없이 별도 폴더에 복사합니다.
        이후 원본 시도 파일이 정리돼도 검토용 이미지는 남습니다.
        """
        try:
            review_dir = source_path.parent / "generated_review"
            review_dir.mkdir(parents=True, exist_ok=True)
            suffix = source_path.suffix.lower()
            if suffix not in self.SUPPORTED_SUFFIXES:
                suffix = ".png"
            safe_scene_id = "".join(
                char if char.isalnum() or char in {"_", "-"} else "_"
                for char in str(scene_id or "scene")
            )
            destination = (
                review_dir
                / f"{safe_scene_id}_attempt_{int(attempt):02d}{suffix}"
            )
            shutil.copy2(source_path, destination)
            if destination.is_file() and destination.stat().st_size > 0:
                print(
                    "[Sprint156 Preserve Attempt] Scene:",
                    scene_id,
                    "Attempt:",
                    attempt,
                    "Path:",
                    destination,
                    flush=True,
                )
                return str(destination)
        except Exception as exc:
            print(
                "[Sprint156 Preserve Attempt] ERROR:",
                scene_id,
                attempt,
                f"{type(exc).__name__}: {exc}",
                flush=True,
            )
        return ""

    def generate(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        return self.generate_image(*args, **kwargs)

    def run(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        return self.generate_image(*args, **kwargs)

    def create(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        return self.generate_image(*args, **kwargs)

    def _resolve_reference_paths(
        self,
        reference_image_path: Any,
        reference_image_paths: Any,
    ) -> List[Path]:
        raw: List[Any] = []
        if str(reference_image_path or "").strip():
            raw.append(reference_image_path)
        if isinstance(reference_image_paths, (list, tuple, set)):
            raw.extend(reference_image_paths)
        elif str(reference_image_paths or "").strip():
            raw.append(reference_image_paths)

        resolved: List[Path] = []
        for item in raw:
            path = Path(str(item or "")).expanduser()
            if path.is_file() and path not in resolved:
                resolved.append(path)
        return resolved

    @staticmethod
    def _build_final_prompt(
        prompt: str,
        negative_prompt: str,
    ) -> str:
        avoid = f"\nAvoid: {negative_prompt}" if negative_prompt else ""
        return (
            f"{prompt}{avoid}\n"
            "Use the attached image as the immutable exact product reference. "
            "Output one image only."
        )

    def _extract_response(
        self,
        response: Any,
    ) -> tuple[bytes, str, str]:
        image_data = b""
        mime_type = ""
        texts: List[str] = []

        try:
            for candidate in list(
                getattr(response, "candidates", None) or []
            ):
                content = getattr(candidate, "content", None)
                for part in list(
                    getattr(content, "parts", None) or []
                ):
                    text = getattr(part, "text", None)
                    if text:
                        texts.append(str(text))
                    inline = getattr(part, "inline_data", None)
                    raw = (
                        getattr(inline, "data", None)
                        if inline is not None
                        else None
                    )
                    if raw and not image_data:
                        image_data = self._normalize_bytes(raw)
                        mime_type = str(
                            getattr(inline, "mime_type", "")
                            or "image/png"
                        )
        except Exception:
            pass

        if not image_data:
            try:
                for generated in list(
                    getattr(response, "generated_images", None) or []
                ):
                    image_obj = (
                        getattr(generated, "image", None)
                        or generated
                    )
                    raw = (
                        getattr(image_obj, "image_bytes", None)
                        or getattr(image_obj, "data", None)
                    )
                    if raw:
                        image_data = self._normalize_bytes(raw)
                        mime_type = str(
                            getattr(image_obj, "mime_type", "")
                            or "image/png"
                        )
                        break
            except Exception:
                pass

        return (
            image_data,
            mime_type,
            "\n".join(texts).strip(),
        )

    @staticmethod
    def _fatal_provider_error_code(error_text: str) -> str:
        text = str(error_text or "").lower()
        if (
            "prepayment credits are depleted" in text
            or "resource_exhausted" in text
        ):
            return "billing_credits_depleted"
        if "api key not valid" in text or "invalid api key" in text:
            return "invalid_api_key"
        if "permission_denied" in text or "permission denied" in text:
            return "permission_denied"
        return ""

    @classmethod
    def _is_transient_error(cls, exc: Exception) -> bool:
        error_text = (
            f"{type(exc).__name__}: {exc}"
        ).lower()
        return any(
            token in error_text
            for token in cls.TRANSIENT_ERROR_TOKENS
        )

    @staticmethod
    def _normalize_bytes(value: Any) -> bytes:
        if isinstance(value, bytes):
            return value
        if isinstance(value, bytearray):
            return bytes(value)
        if isinstance(value, memoryview):
            return value.tobytes()
        if isinstance(value, str):
            try:
                return base64.b64decode(value)
            except Exception:
                return value.encode("utf-8")
        try:
            return bytes(value)
        except Exception:
            return b""

    @staticmethod
    def _safe_int(value: Any, default: int) -> int:
        try:
            return max(1, int(value))
        except Exception:
            return default
