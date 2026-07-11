from pathlib import Path


class YOLOEngine:
    """
    안정화된 YOLO connector.
    - ultralytics 설치 시 실제 추론
    - CPU/GPU 자동 선택
    - 실패 시 앱 중단 없이 상세 메시지 반환
    """

    def check(self):
        result = {
            "installed": False,
            "ready": False,
            "device": "cpu",
            "message": "",
            "install_command": "python -m pip install ultralytics",
        }
        try:
            import torch
            result["device"] = "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            result["device"] = "cpu"

        try:
            import ultralytics  # noqa
            result["installed"] = True
            result["ready"] = True
            result["message"] = f"YOLO 사용 가능 / device={result['device']}"
        except Exception as exc:
            result["message"] = f"ultralytics 미설치 또는 로딩 실패: {exc}"
        return result

    def analyze_video(self, video_path, sample_count=6, model_name="yolov8n.pt", conf=0.25):
        path = Path(video_path or "")
        if not video_path or not path.exists():
            return self.empty("영상 파일이 없습니다.")

        status = self.check()
        if not status["ready"]:
            return self.empty(status["message"], status)

        try:
            import cv2
            from ultralytics import YOLO
        except Exception as exc:
            return self.empty(f"YOLO 실행 준비 실패: {exc}", status)

        try:
            model = YOLO(model_name)
        except Exception as exc:
            return self.empty(f"YOLO 모델 로딩 실패: {exc}", status)

        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            return self.empty("영상을 열 수 없습니다.", status)

        fps = cap.get(cv2.CAP_PROP_FPS) or 0
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        step = max(1, total // max(1, int(sample_count or 1)))

        out_dir = Path("exports/yolo_frames")
        out_dir.mkdir(parents=True, exist_ok=True)

        detections = []
        sample_images = []
        i = 0
        si = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if i % step == 0:
                time_sec = round(i / fps, 2) if fps else 0

                try:
                    result = model.predict(frame, verbose=False, conf=conf, device=status.get("device", "cpu"))[0]
                except TypeError:
                    result = model.predict(frame, verbose=False, conf=conf)[0]

                overlay = frame.copy()
                frame_dets = []
                names = getattr(result, "names", {}) or {}
                boxes = result.boxes

                if boxes is not None:
                    for b in boxes:
                        xyxy = b.xyxy[0].tolist()
                        cls_id = int(b.cls[0].item()) if b.cls is not None else -1
                        score = float(b.conf[0].item()) if b.conf is not None else 0
                        label = names.get(cls_id, str(cls_id))
                        x1, y1, x2, y2 = [int(v) for v in xyxy]

                        cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), 3)
                        cv2.putText(overlay, f"{label} {score:.2f}", (x1, max(25, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

                        frame_dets.append({
                            "time": time_sec,
                            "label": label,
                            "confidence": round(score, 3),
                            "box": [x1, y1, x2, y2],
                            "role": self._role(label),
                            "center_score": self._center_score([x1, y1, x2, y2], width, height),
                        })

                frame_path = out_dir / f"{path.stem}_yolo_{si:02d}.jpg"
                cv2.imwrite(str(frame_path), overlay)
                sample_images.append({"time": time_sec, "frame": str(frame_path), "detections": len(frame_dets)})
                detections.extend(frame_dets)
                si += 1

            i += 1

        cap.release()
        guide = self._guide(detections)

        return {
            "ok": True,
            "status": status,
            "file": str(path),
            "width": width,
            "height": height,
            "fps": round(fps, 2) if fps else "",
            "sampled_frames": si,
            "detections": detections,
            "sample_images": sample_images,
            "guide": guide,
            "capcut_actions": self._capcut_actions(guide),
        }

    def empty(self, message, status=None):
        return {
            "ok": False,
            "error": message,
            "status": status or self.check(),
            "detections": [],
            "sample_images": [],
            "guide": self._default_guide(),
            "capcut_actions": self._capcut_actions(self._default_guide()),
        }

    def _role(self, label):
        label = (label or "").lower()
        if label == "person":
            return "사람/손동작 후보"
        if label in ["cell phone", "bottle", "cup", "bowl", "chair", "tv", "laptop", "book", "backpack", "handbag"]:
            return "상품 후보"
        return "객체 후보"

    def _center_score(self, box, width, height):
        if not width or not height:
            return 0
        x1, y1, x2, y2 = box
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        dx = abs(cx - width / 2) / (width / 2)
        dy = abs(cy - height / 2) / (height / 2)
        return round(max(0, 1 - (dx + dy) / 2), 3)

    def _guide(self, detections):
        if not detections:
            return self._default_guide()

        ranked = sorted(detections, key=lambda x: (x.get("confidence", 0) + x.get("center_score", 0)), reverse=True)
        best = ranked[0]
        product = [d for d in detections if d.get("role") == "상품 후보"]
        person = [d for d in detections if d.get("label") == "person"]

        return {
            "hook_frame": f"{best.get('time')}초 / {best.get('label')}",
            "thumbnail_frame": f"{best.get('time')}초 / confidence {best.get('confidence')}",
            "person_count": len(person),
            "product_candidate_count": len(product),
            "summary": f"{best.get('time')}초 부근의 {best.get('label')} 객체를 후킹/썸네일 후보로 추천합니다.",
            "zoom": "객체 박스 중심으로 105~115% 확대 검토",
            "subtitle_position": "중앙 하단 / 하단 40%",
        }

    def _default_guide(self):
        return {
            "hook_frame": "기본 후킹 장면 사용",
            "thumbnail_frame": "Smart Cut 후보 사용",
            "summary": "YOLO 탐지 데이터가 없어 기존 Smart Cut 기준을 사용합니다.",
            "zoom": "중앙 상품 장면에서 105~115% 확대",
            "subtitle_position": "중앙 하단 / 하단 40%",
        }

    def _capcut_actions(self, guide):
        return [
            {"action": "후킹 컷", "value": guide.get("hook_frame"), "reason": "YOLO 객체 탐지 기반"},
            {"action": "썸네일 컷", "value": guide.get("thumbnail_frame"), "reason": "객체 confidence + 중앙성 기준"},
            {"action": "확대", "value": guide.get("zoom"), "reason": "객체 중심 강조"},
            {"action": "자막 위치", "value": guide.get("subtitle_position"), "reason": "기본 안전영역"},
            {"action": "AI 음성", "value": "20 dB", "reason": "CapCut 최대 기준"},
        ]
