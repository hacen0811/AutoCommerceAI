from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List


class GeneratedImageVisionValidator:
    VERSION = "generated-image-vision-validator-154-product-human-duplicate"
    DEFAULT_MODEL = "gemini-3.5-flash"
    IDENTITY_THRESHOLD = 95.0
    CRITICAL_THRESHOLD = 92.0

    def __init__(self, api_key: Any = "", model: Any = "") -> None:
        self.api_key = str(
            api_key
            or os.getenv("GEMINI_API_KEY", "")
            or os.getenv("GOOGLE_API_KEY", "")
        ).strip()
        self.model = str(
            model
            or os.getenv("GEMINI_VISION_MODEL", "")
            or self.DEFAULT_MODEL
        ).strip()

    def validate(
        self,
        scene_id: Any = "",
        attempt: Any = 1,
        generated_image_path: Any = "",
        image_path: Any = "",
        reference_image_path: Any = "",
        prompt: Any = "",
        negative_prompt: Any = "",
        fidelity_threshold: Any = 95.0,
        **_: Any,
    ) -> Dict[str, Any]:
        scene_id_text = str(scene_id or "").strip() or "scene_unknown"
        generated_path = Path(str(generated_image_path or image_path or "")).expanduser()
        reference_path = Path(str(reference_image_path or "")).expanduser()
        threshold = max(self.IDENTITY_THRESHOLD, self._safe_float(fidelity_threshold, 95.0))

        score_keys = [
            "shape_score",
            "hole_count_score",
            "hole_position_score",
            "hole_size_score",
            "hole_spacing_score",
            "sole_outline_score",
            "sole_thickness_score",
            "material_score",
            "color_score",
            "physics_score",
            "scene_match_score",
            "artifact_score",
            "product_count_score",
            "product_scale_score",
            "human_anatomy_score",
            "human_contact_score",
            "duplicate_risk_score",
            "location_variety_score",
        ]
        result: Dict[str, Any] = {
            "ok": False,
            "ready": False,
            "version": self.VERSION,
            "status": "not_run",
            "provider": "google_genai",
            "model": self.model,
            "scene_id": scene_id_text,
            "attempt": self._safe_int(attempt, 1),
            "generated_image_path": str(generated_path),
            "reference_image_path": str(reference_path) if str(reference_image_path or "").strip() else "",
            "threshold": threshold,
            "fidelity_score": 0.0,
            "product_identity_score": 0.0,
            "score": 0.0,
            "passed": False,
            "critical_failures": [],
            "issues": [],
            "retry_prompt": "",
            "analysis": "",
            "raw_response": "",
            "errors": [],
            "warnings": [],
        }
        for key in score_keys:
            result[key] = 0.0

        if not self.api_key:
            result["status"] = "api_key_missing"
            result["errors"].append("GEMINI_API_KEY 또는 GOOGLE_API_KEY가 설정되지 않았습니다.")
            return result
        if not generated_path.is_file():
            result["status"] = "generated_image_missing"
            result["errors"].append(f"생성 이미지 파일이 없습니다: {generated_path}")
            return result
        if not reference_path.is_file():
            result["status"] = "reference_image_missing"
            result["errors"].append(f"Sprint152-1 기준 상품 이미지가 없습니다: {reference_path}")
            return result

        try:
            from google import genai
            from google.genai import types
            from PIL import Image
        except Exception as exc:
            result["status"] = "dependency_import_failed"
            result["errors"].append(
                f"{type(exc).__name__}: {exc}. pip install -U google-genai pillow 를 실행하세요."
            )
            return result

        try:
            with Image.open(reference_path) as image:
                reference_image = image.convert("RGB").copy()
            with Image.open(generated_path) as image:
                generated_image = image.convert("RGB").copy()
        except Exception as exc:
            result["status"] = "image_read_failed"
            result["errors"].append(f"{type(exc).__name__}: {exc}")
            return result

        schema = {
            "type": "OBJECT",
            "properties": {
                "shape_score": {"type": "NUMBER"},
                "hole_count_score": {"type": "NUMBER"},
                "hole_position_score": {"type": "NUMBER"},
                "hole_size_score": {"type": "NUMBER"},
                "hole_spacing_score": {"type": "NUMBER"},
                "sole_outline_score": {"type": "NUMBER"},
                "sole_thickness_score": {"type": "NUMBER"},
                "material_score": {"type": "NUMBER"},
                "color_score": {"type": "NUMBER"},
                "physics_score": {"type": "NUMBER"},
                "scene_match_score": {"type": "NUMBER"},
                "artifact_score": {"type": "NUMBER"},
                "product_count_score": {"type": "NUMBER"},
                "product_scale_score": {"type": "NUMBER"},
                "human_anatomy_score": {"type": "NUMBER"},
                "human_contact_score": {"type": "NUMBER"},
                "duplicate_risk_score": {"type": "NUMBER"},
                "location_variety_score": {"type": "NUMBER"},
                "issues": {"type": "ARRAY", "items": {"type": "STRING"}},
                "retry_prompt": {"type": "STRING"},
                "analysis": {"type": "STRING"},
            },
            "required": score_keys + ["issues", "retry_prompt", "analysis"],
        }

        try:
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model=self.model,
                contents=[
                    reference_image,
                    generated_image,
                    self._build_validation_prompt(
                        scene_id_text,
                        str(prompt or "").strip(),
                        str(negative_prompt or "").strip(),
                        threshold,
                    ),
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.0,
                ),
            )
            result["raw_response"] = str(getattr(response, "text", "") or "").strip()
        except Exception as exc:
            result["status"] = "provider_error"
            result["errors"].append(f"{type(exc).__name__}: {exc}")
            print("[Sprint152-1 Identity Vision] Provider Error:", scene_id_text, repr(exc), flush=True)
            return result

        payload = self._parse_json(result["raw_response"])
        if not isinstance(payload, dict):
            result["status"] = "invalid_json_response"
            result["errors"].append("Gemini Vision 응답을 JSON으로 해석하지 못했습니다.")
            return result

        scores = {key: self._clamp_score(payload.get(key, 0)) for key in score_keys}
        identity_weights = {
            "shape_score": 0.18,
            "hole_count_score": 0.12,
            "hole_position_score": 0.16,
            "hole_size_score": 0.08,
            "hole_spacing_score": 0.08,
            "sole_outline_score": 0.14,
            "sole_thickness_score": 0.08,
            "material_score": 0.08,
            "color_score": 0.08,
        }
        product_identity_score = sum(scores[key] * weight for key, weight in identity_weights.items())
        fidelity_score = (
            product_identity_score * 0.60
            + scores["physics_score"] * 0.08
            + scores["scene_match_score"] * 0.05
            + scores["artifact_score"] * 0.05
            + scores["product_count_score"] * 0.07
            + scores["product_scale_score"] * 0.05
            + scores["human_anatomy_score"] * 0.04
            + scores["human_contact_score"] * 0.04
            + scores["duplicate_risk_score"] * 0.01
            + scores["location_variety_score"] * 0.01
        )

        critical_keys = [
            "shape_score",
            "hole_count_score",
            "hole_position_score",
            "sole_outline_score",
            "product_count_score",
            "product_scale_score",
            "human_anatomy_score",
            "human_contact_score",
        ]
        critical_failures = [
            key for key in critical_keys
            if scores[key] < self.CRITICAL_THRESHOLD
        ]
        passed = bool(
            product_identity_score >= threshold
            and fidelity_score >= threshold
            and not critical_failures
            and scores["physics_score"] >= 90.0
            and scores["artifact_score"] >= 92.0
            and scores["product_count_score"] >= 98.0
            and scores["product_scale_score"] >= 94.0
            and scores["human_anatomy_score"] >= 94.0
            and scores["human_contact_score"] >= 94.0
            and scores["duplicate_risk_score"] >= 85.0
        )

        issues = [
            str(item).strip()
            for item in list(payload.get("issues") or [])
            if str(item).strip()
        ]
        retry_prompt = str(payload.get("retry_prompt") or "").strip()
        if not passed:
            retry_prompt = self._build_retry_prompt(scores, issues, retry_prompt)

        result.update(
            ok=True,
            ready=True,
            status="passed" if passed else "retry_required",
            fidelity_score=round(fidelity_score, 2),
            product_identity_score=round(product_identity_score, 2),
            score=round(fidelity_score, 2),
            passed=passed,
            critical_failures=critical_failures,
            issues=issues,
            retry_prompt=retry_prompt,
            analysis=str(payload.get("analysis") or "").strip(),
            **scores,
        )

        print(
            "[Sprint152-1 Identity Vision] Scene:", scene_id_text,
            "Attempt:", result["attempt"],
            "Identity:", result["product_identity_score"],
            "Fidelity:", result["fidelity_score"],
            "Critical:", critical_failures,
            "Passed:", passed,
            flush=True,
        )
        return result

    def analyze(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        return self.validate(*args, **kwargs)

    def evaluate(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        return self.validate(*args, **kwargs)

    def inspect(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        return self.validate(*args, **kwargs)

    def run(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        return self.validate(*args, **kwargs)

    def _build_validation_prompt(self, scene_id: str, scene_prompt: str, negative_prompt: str, threshold: float) -> str:
        return (
            "You are a forensic product identity inspector. "
            "Image 1 is the exact real product reference and is the source of truth. "
            "Image 2 is the AI-generated scene. Do not reward beauty or advertising quality. "
            f"Scene ID: {scene_id}\nRequested scene: {scene_prompt}\n"
            f"Negative constraints: {negative_prompt}\nPassing threshold: {threshold:.1f}/100.\n\n"
            "Score conservatively: exact shape, visible hole count, hole positions, hole sizes, "
            "hole spacing, sole outline, sole thickness, material, color, gravity-correct water flow, "
            "drainage, hand/foot contact, scene match, duplicate products, realistic product scale, "
            "exactly one pair or one item as requested, coherent hands/feet/legs, natural anatomy, "
            "no body fusion or penetration, no repeated composition/background, text overlays and artifacts. "
            "Changed hole layout or sole outline must fail even when the image is attractive. "
            "Return JSON only. retry_prompt must give concrete corrections for the next single-image attempt."
        )

    def _build_retry_prompt(self, scores: Dict[str, float], issues: List[str], supplied: str) -> str:
        checks = [
            ("shape_score", 95, "Match the exact reference silhouette and proportions"),
            ("hole_count_score", 95, "Use the exact same visible hole count as the reference"),
            ("hole_position_score", 95, "Copy every hole position relative to the product edges exactly"),
            ("hole_size_score", 94, "Copy each corresponding hole size exactly"),
            ("hole_spacing_score", 94, "Preserve the exact spacing and pattern between holes"),
            ("sole_outline_score", 95, "Copy the exact sole perimeter, toe curve and heel outline"),
            ("sole_thickness_score", 94, "Preserve the exact sole thickness and edge profile"),
            ("material_score", 93, "Match the exact material texture and surface finish"),
            ("color_score", 93, "Match the exact product color"),
            ("physics_score", 90, "Correct gravity, drainage and all hand/foot contact physics"),
            ("artifact_score", 92, "Remove text overlays, malformed objects and visual artifacts"),
            ("product_count_score", 98, "Show exactly the requested number of products; never add a second pair"),
            ("product_scale_score", 94, "Keep the product at realistic human-scale proportions"),
            ("human_anatomy_score", 94, "Use anatomically coherent hands, feet, legs and body proportions"),
            ("human_contact_score", 94, "Make all hand/foot contact physically natural with no penetration"),
            ("duplicate_risk_score", 85, "Use a clearly different composition and background from prior scenes"),
            ("location_variety_score", 85, "Use the assigned location and avoid repeating bathroom-only scenes"),
        ]
        corrections = [message for key, minimum, message in checks if scores.get(key, 0) < minimum]
        corrections.extend(issues[:4])
        if supplied:
            corrections.append(supplied)
        unique = []
        seen = set()
        for item in corrections:
            text = str(item).strip().rstrip(".")
            if text and text.lower() not in seen:
                seen.add(text.lower())
                unique.append(text)
        return (
            "Regenerate exactly one image only. Use the attached reference as immutable product geometry. "
            + ". ".join(unique[:10])
            + ". Do not redesign any part of the product."
        )

    @staticmethod
    def _parse_json(value: Any) -> Any:
        text = str(value or "").strip()
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        try:
            return json.loads(text)
        except Exception:
            match = re.search(r"\{.*\}", text, flags=re.DOTALL)
            if not match:
                return None
            try:
                return json.loads(match.group(0))
            except Exception:
                return None

    @staticmethod
    def _safe_float(value: Any, default: float) -> float:
        try:
            return float(value)
        except Exception:
            return float(default)

    @staticmethod
    def _safe_int(value: Any, default: int) -> int:
        try:
            return int(value)
        except Exception:
            return int(default)

    @staticmethod
    def _clamp_score(value: Any) -> float:
        try:
            return round(max(0.0, min(100.0, float(value))), 2)
        except Exception:
            return 0.0
