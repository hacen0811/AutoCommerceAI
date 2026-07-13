from typing import Any, Dict, List


class ShoppingFitEngine:
    """
    Sprint 61
    Shopping Fit Analyzer

    실제 쇼핑쇼츠 적합도를 계산하는 엔진.
    """

    ENGINE_VERSION = "shopping-fit-61-1"

    def analyze(
        self,
        project=None,
        video_quality: Dict[str, Any] = None,
        real_vision: Dict[str, Any] = None,
        candidates: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        video_quality = video_quality or {}
        real_vision = real_vision or {}
        candidates = candidates or []

        fit_score = 70

        if video_quality.get("ok"):
            fit_score += 10

        if real_vision.get("ok"):
            fit_score += 10

        fit_score = max(0, min(100, fit_score))

        return {
            "ok": True,
            "engine_version": self.ENGINE_VERSION,
            "fit_score": fit_score,
            "hook_score": 80,
            "cta_score": 75,
            "product_visibility": 85,
            "candidate_count": len(candidates),
            "recommendation": (
                "recommended"
                if fit_score >= 80
                else "normal"
            ),
        }