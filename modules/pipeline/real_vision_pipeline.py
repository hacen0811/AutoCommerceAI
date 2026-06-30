from modules.video.yolo_engine import YOLOEngine
from modules.video.paddle_ocr_engine import PaddleOCREngine
from modules.video.vision_ai_engine import VisionAIEngine
from modules.video.ai_analyzer import VideoAIAnalyzer
from modules.video.smart_cut_engine import SmartCutEngine
from modules.editor.caption_safe_engine import CaptionSafeEngine
from modules.editor.auto_editor_engine import AutoEditorEngine
from modules.ai.shopping_shorts_engine import ShoppingShortsEngine


class RealVisionPipeline:
    def run(self, project, sample_count=6, run_yolo=True, run_paddle=True):
        product_name = getattr(project, "product_name", "추천상품")
        keyword = getattr(project, "keyword", "정보")
        video_path = getattr(project, "video_path", "")

        result = {
            "project": {
                "id": getattr(project, "id", 0),
                "product_name": product_name,
                "keyword": keyword,
                "video_path": video_path,
            },
            "status": {},
            "video_ai": {},
            "vision": {},
            "yolo": {},
            "paddleocr": {},
            "smart_cut": {},
            "caption_safe": {},
            "auto_editor": {},
            "shopping_shorts": {},
            "summary": "",
            "next_actions": [],
        }

        if not video_path:
            result["summary"] = "원본 영상이 없습니다. 먼저 영상관리에서 영상을 업로드하세요."
            result["next_actions"] = ["원본 영상 업로드", "다시 Real Vision 실행"]
            return result

        video_ai = VideoAIAnalyzer().analyze(video_path, sample_count=sample_count)
        vision = VisionAIEngine().analyze(video_path, sample_count=min(sample_count, 8), use_ocr=False)

        yolo = YOLOEngine().analyze_video(video_path, sample_count=min(sample_count, 6)) if run_yolo else YOLOEngine().empty("YOLO 실행 안 함")
        paddle = PaddleOCREngine().analyze_video(video_path, sample_count=min(sample_count, 4)) if run_paddle else PaddleOCREngine().empty("PaddleOCR 실행 안 함")

        smart = SmartCutEngine().build(video_ai, product_name, keyword)

        caption_source = paddle if paddle.get("ok") else vision
        caption_safe = CaptionSafeEngine().build(caption_source, caption_source)

        shorts = ShoppingShortsEngine().generate(
            product_name=product_name,
            keyword=keyword,
            video_intel=smart,
            ocr_result=caption_source,
        )

        auto_editor = AutoEditorEngine().create_plan(
            product_name=product_name,
            keyword=keyword,
            smart_cut=smart,
            vision=caption_source,
            shorts=shorts,
        )

        result.update({
            "status": {
                "video_ai": bool(video_ai.get("ok")),
                "vision": bool(vision.get("ok")),
                "yolo": bool(yolo.get("ok")),
                "paddleocr": bool(paddle.get("ok")),
            },
            "video_ai": video_ai,
            "vision": vision,
            "yolo": yolo,
            "paddleocr": paddle,
            "smart_cut": smart,
            "caption_safe": caption_safe,
            "auto_editor": auto_editor,
            "shopping_shorts": shorts,
            "summary": self._summary(video_ai, yolo, paddle, smart, caption_safe),
            "next_actions": self._next_actions(yolo, paddle, smart, caption_safe),
        })

        return result

    def _summary(self, video_ai, yolo, paddle, smart, caption_safe):
        hook = smart.get("hook_cut", {}).get("time", "-")
        subtitle = caption_safe.get("safe_subtitle_position", "중앙 하단 / 하단 40%")
        yolo_status = "YOLO 성공" if yolo.get("ok") else "YOLO 미사용/실패"
        ocr_status = "PaddleOCR 성공" if paddle.get("ok") else "PaddleOCR 미사용/실패"
        return f"추천 후킹 컷은 {hook}초 부근입니다. 자막 위치는 {subtitle}를 추천합니다. {yolo_status}, {ocr_status}."

    def _next_actions(self, yolo, paddle, smart, caption_safe):
        actions = [
            "추천 후킹 컷을 0~2초에 배치",
            "Smart Cut 타임라인대로 20초 쇼츠 구성",
            "CapCut에서 AI 음성 20 dB, BGM 8 dB 적용",
        ]
        if not yolo.get("ok"):
            actions.append("YOLO 정확도 향상을 위해 ultralytics 설치 또는 모델 확인")
        if not paddle.get("ok"):
            actions.append("중국어 자막 실제 인식을 위해 PaddleOCR 설치 확인")
        actions.append(f"자막 위치: {caption_safe.get('safe_subtitle_position', '중앙 하단 / 하단 40%')}")
        return actions
