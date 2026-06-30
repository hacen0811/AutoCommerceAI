from modules.video.yolo_engine import YOLOEngine
from modules.video.paddle_ocr_engine import PaddleOCREngine


class AIConnectorStatus:
    def check_all(self):
        yolo = YOLOEngine().check()
        paddle = PaddleOCREngine().check()

        ready_count = sum([bool(yolo.get("ready")), bool(paddle.get("ready"))])

        return {
            "ready_count": ready_count,
            "total": 2,
            "yolo": yolo,
            "paddleocr": paddle,
            "next_steps": [
                "YOLO가 필요하면: python -m pip install ultralytics",
                "PaddleOCR가 필요하면: python -m pip install paddleocr paddlepaddle",
                "설치 후 프로그램을 재시작하세요.",
                "처음 실행 시 YOLO 모델 파일(yolov8n.pt)을 자동 다운로드할 수 있습니다.",
            ],
        }
