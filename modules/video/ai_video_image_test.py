from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from modules.video.ai_video_engine import AIVideoEngine
from modules.video.gemini_veo_provider import GeminiVeoProvider


class AIVideoImageTest:
    """
    Sprint91-4 Gemini Veo 상품 이미지→영상 실제 생성 테스트

    실행 우선순위:
    1) 명령행 첫 번째 인자
    2) PRODUCT_REFERENCE_IMAGE 환경 변수
    3) assets/products/48/main.jpg
    """

    VERSION = "ai-video-image-test-91-4"
    PROJECT_ID = "48"
    PRODUCT_NAME = "24인치 기내용 캐리어"
    DEFAULT_REFERENCE_IMAGE = Path("assets") / "products" / PROJECT_ID / "main.jpg"

    def __init__(self, reference_image_path: Optional[str] = None) -> None:
        self.reference_image_path = self._resolve_reference_image(reference_image_path)
        self.provider = GeminiVeoProvider()
        self.engine = AIVideoEngine(
            providers={GeminiVeoProvider.PROVIDER_NAME: self.provider}
        )

    def run(self) -> Dict[str, Any]:
        print("[Sprint91-4 Image Video] Test Version:", self.VERSION, flush=True)
        print("[Sprint91-4 Image Video] Engine Version:", AIVideoEngine.VERSION, flush=True)
        print("[Sprint91-4 Image Video] Provider Version:", GeminiVeoProvider.VERSION, flush=True)
        print("[Sprint91-4 Image Video] Reference Image:", self.reference_image_path, flush=True)

        image_path = Path(self.reference_image_path)
        if not image_path.is_file():
            result = {
                "ok": False,
                "ready": False,
                "status": "reference_image_not_found",
                "test_version": self.VERSION,
                "reference_image_path": self.reference_image_path,
                "errors": [f"상품 대표 이미지를 찾을 수 없습니다: {image_path}"],
            }
            print("[Sprint91-4 Image Video] Reference Ready: False", flush=True)
            print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
            return result

        readiness = self.provider.readiness()
        print("[Sprint91-4 Image Video] Provider Ready:", readiness.get("ready"), flush=True)
        if not readiness.get("ready"):
            result = {
                "ok": False,
                "ready": False,
                "status": "provider_not_ready",
                "test_version": self.VERSION,
                "provider_readiness": readiness,
                "errors": list(readiness.get("errors") or []),
            }
            print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
            return result

        request = self.engine.build_request(
            project_id=self.PROJECT_ID,
            product_name=self.PRODUCT_NAME,
            provider=GeminiVeoProvider.PROVIDER_NAME,
            aspect_ratio="9:16",
            reference_images=[self.reference_image_path],
            scenes=[
                {
                    "scene_id": "scene_01",
                    "duration_seconds": 6,
                    "reference_image_path": self.reference_image_path,
                    "prompt": (
                        "Begin exactly from the supplied product photograph. The identical "
                        "suitcase remains upright. A natural human hand enters slowly, raises "
                        "only the telescopic handle, and gently rolls the same suitcase forward "
                        "a short distance. Keep the product centered and fully visible. Use very "
                        "small, physically realistic motion so product identity remains stable."
                    ),
                    "negative_prompt": (
                        "opening the suitcase, changing the background abruptly, replacing the "
                        "suitcase, changing product design, dramatic camera movement"
                    ),
                    "metadata": {
                        "camera": "stable vertical 9:16 product shot, subtle slow push-in",
                        "lighting": "preserve the source image lighting and natural shadows",
                        "style": "photorealistic Korean social-commerce product footage",
                    },
                }
            ],
            metadata={
                "sprint": "91-4",
                "purpose": "single_scene_image_to_video_product_identity_test",
            },
        )

        saved_request = self.engine.save_request(request)
        print("[Sprint91-4 Image Video] Reference Ready: True", flush=True)
        print("[Sprint91-4 Image Video] Request Saved:", saved_request.get("saved"), flush=True)
        print("[Sprint91-4 Image Video] Output Dir:", request.get("output_dir"), flush=True)
        print("[Sprint91-4 Image Video] Input Mode: image_to_video", flush=True)
        print("[Sprint91-4 Image Video] Real Generation Start: True", flush=True)
        print("[Sprint91-4 Image Video] This can take several minutes.", flush=True)

        result = self.engine.generate(request, dry_run=False)
        result["test_version"] = self.VERSION
        result["reference_image_path"] = self.reference_image_path
        result["request_saved"] = saved_request

        result_path = Path(str(request.get("output_dir") or "")) / "result.json"
        try:
            result_path.parent.mkdir(parents=True, exist_ok=True)
            result_path.write_text(
                json.dumps(result, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            result["result_saved"] = True
            result["result_path"] = str(result_path)
        except Exception as exc:
            result["result_saved"] = False
            result["result_path"] = ""
            result.setdefault("errors", []).append(
                f"result save failed: {type(exc).__name__}: {exc}"
            )

        print("[Sprint91-4 Image Video] Status:", result.get("status"), flush=True)
        print("[Sprint91-4 Image Video] Ready:", result.get("ready"), flush=True)
        print("[Sprint91-4 Image Video] Generated Files:", result.get("generated_files"), flush=True)
        print("[Sprint91-4 Image Video] Errors:", result.get("errors"), flush=True)
        print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
        return result

    @classmethod
    def _resolve_reference_image(cls, supplied: Optional[str]) -> str:
        return str(
            supplied
            or os.getenv("PRODUCT_REFERENCE_IMAGE")
            or cls.DEFAULT_REFERENCE_IMAGE
        ).strip()


def main() -> int:
    supplied_path = sys.argv[1] if len(sys.argv) > 1 else None
    result = AIVideoImageTest(supplied_path).run()
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())