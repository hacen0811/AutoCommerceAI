from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

from modules.video.ai_video_engine import AIVideoEngine
from modules.video.gemini_veo_provider import GeminiVeoProvider


class AIVideoSingleTest:
    """
    Sprint91-3 Gemini Veo 단일 장면 실제 생성 테스트

    역할:
    - Sprint91-1 AIVideoEngine에 Sprint91-2 GeminiVeoProvider 등록
    - 프로젝트 48 캐리어용 9:16, 6초 영상 한 장면만 실제 생성
    - 생성 요청과 결과 JSON 저장
    - Workflow 연결 전에 API, 모델, 파일 저장을 단독 검증
    """

    VERSION = "ai-video-single-test-91-3"
    PROJECT_ID = "48"
    PRODUCT_NAME = "24인치 기내용 캐리어"

    def __init__(self) -> None:
        self.provider = GeminiVeoProvider()
        self.engine = AIVideoEngine(
            providers={GeminiVeoProvider.PROVIDER_NAME: self.provider}
        )

    def run(self) -> Dict[str, Any]:
        readiness = self.provider.readiness()
        print("[Sprint91-3 AI Video] Test Version:", self.VERSION, flush=True)
        print(
            "[Sprint91-3 AI Video] Engine Version:",
            AIVideoEngine.VERSION,
            flush=True,
        )
        print(
            "[Sprint91-3 AI Video] Provider Version:",
            GeminiVeoProvider.VERSION,
            flush=True,
        )
        print(
            "[Sprint91-3 AI Video] Provider Ready:",
            readiness.get("ready"),
            flush=True,
        )

        if not readiness.get("ready"):
            result = {
                "ok": False,
                "ready": False,
                "version": self.VERSION,
                "status": "provider_not_ready",
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
            scenes=[
                {
                    "scene_id": "scene_01",
                    "duration_seconds": 6,
                    "prompt": (
                        "A realistic 24-inch hard-shell carry-on suitcase stands "
                        "upright in a bright modern Korean apartment entryway. "
                        "A person's hand smoothly extends the telescopic handle, "
                        "then gently rolls the suitcase forward to demonstrate "
                        "stable wheels and practical travel size. Keep the suitcase "
                        "shape, color, handle, wheels, and proportions consistent "
                        "throughout the shot. One continuous shot, natural movement."
                    ),
                    "negative_prompt": (
                        "subtitles, captions, text, watermark, brand logo, distorted "
                        "suitcase, duplicated wheels, extra handles, deformed hands, "
                        "changing product color, scene cuts, camera shake"
                    ),
                    "metadata": {
                        "camera": (
                            "vertical 9:16 medium full shot, stable camera, "
                            "slow subtle push-in"
                        ),
                        "lighting": "soft natural daylight, clean commercial lighting",
                        "style": (
                            "photorealistic Korean social-commerce product video, "
                            "premium but natural"
                        ),
                    },
                }
            ],
            metadata={
                "sprint": "91-3",
                "purpose": "single_scene_real_generation_test",
            },
        )

        saved_request = self.engine.save_request(request)
        print(
            "[Sprint91-3 AI Video] Request Saved:",
            saved_request.get("saved"),
            flush=True,
        )
        print(
            "[Sprint91-3 AI Video] Output Dir:",
            request.get("output_dir"),
            flush=True,
        )
        print(
            "[Sprint91-3 AI Video] Real Generation Start: True",
            flush=True,
        )
        print(
            "[Sprint91-3 AI Video] This can take several minutes.",
            flush=True,
        )

        result = self.engine.generate(request, dry_run=False)
        result["test_version"] = self.VERSION
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

        print(
            "[Sprint91-3 AI Video] Status:",
            result.get("status"),
            flush=True,
        )
        print(
            "[Sprint91-3 AI Video] Ready:",
            result.get("ready"),
            flush=True,
        )
        print(
            "[Sprint91-3 AI Video] Generated Files:",
            result.get("generated_files"),
            flush=True,
        )
        print(
            "[Sprint91-3 AI Video] Errors:",
            result.get("errors"),
            flush=True,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
        return result


def main() -> int:
    result = AIVideoSingleTest().run()
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())