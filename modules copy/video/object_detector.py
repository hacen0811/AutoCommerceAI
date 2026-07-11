from pathlib import Path


class ObjectDetector:
    """
    Object Detection Starter.
    실제 YOLO 모델 전 단계입니다.
    OpenCV로 중앙 상품 후보 영역, 손/움직임 후보, 썸네일 후보를 계산합니다.
    """

    def detect(self, video_path, sample_count=10):
        path = Path(video_path or "")
        if not video_path or not path.exists():
            return self.empty("영상 파일이 없습니다.")

        try:
            import cv2
        except Exception:
            return self.empty("opencv-python이 설치되지 않았습니다.")

        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            return self.empty("영상을 열 수 없습니다.")

        fps = cap.get(cv2.CAP_PROP_FPS) or 0
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

        step = max(1, total // max(1, sample_count))
        export_dir = Path("exports/object_frames")
        export_dir.mkdir(parents=True, exist_ok=True)

        frames = []
        idx = 0
        sample_i = 0
        prev_gray = None

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if idx % step == 0:
                time_sec = round(idx / fps, 2) if fps else 0
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                blur = cv2.GaussianBlur(gray, (5, 5), 0)
                edges = cv2.Canny(blur, 60, 160)

                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                boxes = []
                frame_area = width * height if width and height else 1

                for c in contours:
                    x, y, w, h = cv2.boundingRect(c)
                    area = w * h
                    if area < frame_area * 0.01 or area > frame_area * 0.65:
                        continue
                    center_score = self._center_score(x, y, w, h, width, height)
                    boxes.append({
                        "box": [int(x), int(y), int(x+w), int(y+h)],
                        "area_ratio": round(area / frame_area, 4),
                        "center_score": center_score,
                    })

                boxes = sorted(boxes, key=lambda b: (b["center_score"], b["area_ratio"]), reverse=True)[:5]

                movement = 0
                if prev_gray is not None:
                    import numpy as np
                    movement = float(np.mean(cv2.absdiff(cv2.resize(prev_gray, (160, 90)), cv2.resize(gray, (160, 90)))))
                prev_gray = gray

                score = self._score(boxes, movement)

                frame_name = f"{path.stem}_object_{sample_i:02d}.jpg"
                frame_path = export_dir / frame_name
                overlay = frame.copy()
                for b in boxes[:3]:
                    x1, y1, x2, y2 = b["box"]
                    cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), 3)
                cv2.imwrite(str(frame_path), overlay)

                frames.append({
                    "time": time_sec,
                    "frame": str(frame_path),
                    "object_candidates": boxes,
                    "movement": round(movement, 2),
                    "score": score,
                    "recommend": self._recommend(score, movement, boxes),
                })

                sample_i += 1

            idx += 1

        cap.release()

        ranked = sorted(frames, key=lambda x: x["score"], reverse=True)

        return {
            "ok": True,
            "file": str(path),
            "width": width,
            "height": height,
            "fps": round(fps, 2) if fps else "",
            "frames": frames,
            "best_product_frames": ranked[:5],
            "best_motion_frames": sorted(frames, key=lambda x: x["movement"], reverse=True)[:5],
            "guide": self._guide(ranked[:5]),
            "notice": "현재는 YOLO 전 단계의 객체 후보 분석입니다. 실제 상품/손/얼굴 분류는 다음 단계에서 모델 연결이 필요합니다.",
        }

    def empty(self, msg):
        return {
            "ok": False,
            "error": msg,
            "frames": [],
            "best_product_frames": [],
            "best_motion_frames": [],
            "guide": self._guide([]),
        }

    def _center_score(self, x, y, w, h, fw, fh):
        if not fw or not fh:
            return 0
        cx = x + w / 2
        cy = y + h / 2
        dx = abs(cx - fw/2) / (fw/2)
        dy = abs(cy - fh/2) / (fh/2)
        return round(max(0, 1 - (dx + dy) / 2), 3)

    def _score(self, boxes, movement):
        score = 50
        if boxes:
            score += int(boxes[0]["center_score"] * 25)
            score += min(15, int(boxes[0]["area_ratio"] * 100))
        if movement >= 10:
            score += 10
        return min(100, score)

    def _recommend(self, score, movement, boxes):
        if score >= 85:
            return "상품/썸네일 후보"
        if movement >= 16:
            return "사용 장면/손동작 후보"
        if boxes:
            return "제품 장면 후보"
        return "사용 주의"

    def _guide(self, top):
        if not top:
            return {
                "hook": "기본 후킹 장면 사용",
                "thumbnail": "직접 선택 필요",
                "zoom": "중앙 상품 장면에서 105~115% 확대",
            }

        first = top[0]
        return {
            "hook": f"{first.get('time')}초 장면을 후킹 후보로 사용",
            "thumbnail": f"{first.get('time')}초 장면을 썸네일 후보로 사용",
            "zoom": "객체 박스가 중앙에 있는 장면은 105~115% 확대 추천",
            "capcut": "제품 후보 박스가 작으면 Zoom In, 손동작 후보는 Click 8 dB",
        }
