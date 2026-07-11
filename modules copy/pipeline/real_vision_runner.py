from modules.video.ai_analyzer import VideoAIAnalyzer
from modules.video.vision_ai_engine import VisionAIEngine
from modules.video.yolo_engine import YOLOEngine
from modules.video.paddle_ocr_engine import PaddleOCREngine
from modules.video.smart_cut_engine import SmartCutEngine
from modules.video.object_detector import ObjectDetector
from modules.editor.caption_safe_engine import CaptionSafeEngine
from modules.editor.auto_editor_engine import AutoEditorEngine
from modules.ai.shopping_shorts_engine import ShoppingShortsEngine
from modules.video.video_path_resolver import VideoPathResolver


class RealVisionRunner:
    """
    실제 실행용 Vision Runner.
    - 설치된 모델은 실제 실행
    - 미설치 모델은 자동으로 Starter 분석으로 대체
    - 결과를 하나의 표준 JSON으로 반환
    """

    def run(self, project, sample_count=8, use_yolo=True, use_paddle=True):
        resolver = VideoPathResolver()
        project = resolver.resolve_project(project)

        product_name = getattr(project, "product_name", "") or getattr(project, "title", "") or "추천상품"
        keyword = getattr(project, "keyword", "정보") or "정보"
        video_path = resolver.resolve_path(project)

        if not video_path or not resolver.exists(video_path):
            debug = resolver.debug(project)
            return {
                "ok": False,
                "summary": f"원본 영상 경로를 찾을 수 없습니다. 현재 경로: {debug.get('video_path') or '-'}",
                "fallback_used": [],
                "path_debug": debug,
                "next_actions": ["영상관리에서 영상 저장 다시 실행", "영상 경로가 실제 파일인지 확인", "Real Vision Runner 다시 실행"],
            }

        video_ai = VideoAIAnalyzer().analyze(video_path, sample_count=sample_count)
        vision = VisionAIEngine().analyze(video_path, sample_count=min(sample_count, 8), use_ocr=False)

        yolo = YOLOEngine().analyze_video(video_path, sample_count=min(sample_count, 6)) if use_yolo else YOLOEngine().empty("YOLO 사용 안 함")
        paddle = PaddleOCREngine().analyze_video(video_path, sample_count=min(sample_count, 4)) if use_paddle else PaddleOCREngine().empty("PaddleOCR 사용 안 함")

        fallback_used = []

        if not yolo.get("ok"):
            object_result = ObjectDetector().detect(video_path, sample_count=min(sample_count, 8))
            fallback_used.append("YOLO 미사용 → Object AI Starter 대체")
        else:
            object_result = {
                "ok": True,
                "guide": yolo.get("guide", {}),
                "best_product_frames": yolo.get("sample_images", []),
                "detections": yolo.get("detections", []),
            }

        caption_source = paddle if paddle.get("ok") else vision
        if not paddle.get("ok"):
            fallback_used.append("PaddleOCR 미사용 → Vision AI 자막 위험 분석 대체")

        smart = SmartCutEngine().build(video_ai, product_name, keyword, yolo=yolo, ocr=caption_source)
        caption_safe = CaptionSafeEngine().build(caption_source, caption_source)
        shorts = ShoppingShortsEngine().generate(product_name, keyword, smart, caption_source)
        editor = AutoEditorEngine().create_plan(product_name, keyword, smart, caption_source, shorts)

        summary = self._summary(smart, caption_safe, yolo, paddle, fallback_used)

        return {
            "ok": True,
            "project": {
                "id": getattr(project, "id", 0),
                "product_name": product_name,
                "keyword": keyword,
                "video_path": video_path,
            },
            "summary": summary,
            "fallback_used": fallback_used,
            "status": {
                "video_ai": bool(video_ai.get("ok")),
                "vision_ai": bool(vision.get("ok")),
                "yolo": bool(yolo.get("ok")),
                "paddleocr": bool(paddle.get("ok")),
                "object_fallback": bool(object_result.get("ok")),
            },
            "video_ai": video_ai,
            "vision_ai": vision,
            "yolo": yolo,
            "paddleocr": paddle,
            "object_ai": object_result,
            "smart_cut": smart,
            "caption_safe": caption_safe,
            "auto_editor": editor,
            "shopping_shorts": shorts,
            "next_actions": self._next_actions(caption_safe, fallback_used),
        }

    def _summary(self, smart, caption_safe, yolo, paddle, fallback_used):
        hook_time = smart.get("hook_cut", {}).get("time", "-")
        subtitle = caption_safe.get("safe_subtitle_position", "중앙 하단 / 하단 40%")
        yolo_text = "YOLO 실제 실행" if yolo.get("ok") else "YOLO 대체 분석"
        paddle_text = "PaddleOCR 실제 실행" if paddle.get("ok") else "PaddleOCR 대체 분석"
        fallback = f" 대체 사용: {', '.join(fallback_used)}." if fallback_used else ""
        return f"후킹 컷은 {hook_time}초 부근, 자막 위치는 {subtitle} 추천입니다. {yolo_text}, {paddle_text}.{fallback}"

    def _next_actions(self, caption_safe, fallback_used):
        actions = [
            f"CapCut 자막 위치: {caption_safe.get('safe_subtitle_position', '중앙 하단 / 하단 40%')}",
            "AI 음성 20 dB",
            "BGM 8 dB",
            "Pop 7 dB / Click 8 dB / Whoosh 6 dB",
            "Smart Cut 타임라인 기준으로 20초 영상 편집",
        ]
        if fallback_used:
            actions.append("정확도 향상을 위해 AI 모델 연결 메뉴에서 YOLO/PaddleOCR 설치 상태 확인")
        return actions
