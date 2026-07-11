from pathlib import Path


class OCRDetector:
    """
    OCR Engine Starter.
    실제 중국어 문자를 읽는 OCR 전 단계입니다.
    OpenCV로 텍스트가 있을 가능성이 높은 영역을 감지합니다.

    목적:
    - 하단 중국어 자막 위험
    - 상단 텍스트 위험
    - 좌우 워터마크/로고 위험
    - CapCut 자막 안전 위치 추천
    """

    def detect(self, video_path, sample_count=8):
        path = Path(video_path or "")
        if not video_path or not path.exists():
            return self.empty("영상 파일이 없습니다.")

        try:
            import cv2
            import numpy as np
        except Exception:
            return self.empty("opencv-python이 설치되지 않았습니다. python -m pip install -r requirements.txt 를 실행하세요.")

        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            return self.empty("영상을 열 수 없습니다.")

        fps = cap.get(cv2.CAP_PROP_FPS) or 0
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

        if total <= 0 or width <= 0 or height <= 0:
            cap.release()
            return self.empty("영상 정보를 읽을 수 없습니다.")

        positions = self._regions(width, height)
        hits = {key: [] for key in positions.keys()}

        step = max(1, total // max(1, sample_count))
        frame_i = 0
        sampled = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_i % step == 0:
                time_sec = round(frame_i / fps, 2) if fps else 0
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                edges = cv2.Canny(gray, 80, 180)

                for key, (x1, y1, x2, y2) in positions.items():
                    roi = edges[y1:y2, x1:x2]
                    density = float((roi > 0).mean()) if roi.size else 0

                    # 자막/로고는 일반 배경보다 edge density가 높게 나오는 경향
                    if density >= self._threshold(key):
                        hits[key].append({
                            "time": time_sec,
                            "density": round(density, 4),
                            "region": [x1, y1, x2, y2],
                        })

                sampled += 1

            frame_i += 1

        cap.release()

        risk = self._risk_summary(hits, sampled)
        recommendation = self._recommendation(risk)

        return {
            "ok": True,
            "file": str(path),
            "width": width,
            "height": height,
            "fps": round(fps, 2) if fps else "",
            "sampled_frames": sampled,
            "regions": positions,
            "hits": hits,
            "risk": risk,
            "recommendation": recommendation,
            "capcut_actions": self._capcut_actions(recommendation),
            "notice": "이 기능은 OCR 전 단계의 텍스트/워터마크 가능 영역 감지입니다. 실제 중국어 문자인지 판독하는 기능은 다음 단계에서 확장합니다.",
        }

    def empty(self, message):
        return {
            "ok": False,
            "error": message,
            "regions": {},
            "hits": {},
            "risk": {},
            "recommendation": {
                "subtitle_position": "중앙 하단 / 하단 40%",
                "crop": "9:16 유지",
                "blur": "필요 시 수동 확인",
            },
            "capcut_actions": [],
        }

    def _regions(self, w, h):
        return {
            "top_text": (int(w*0.05), int(h*0.02), int(w*0.95), int(h*0.18)),
            "bottom_caption": (int(w*0.05), int(h*0.70), int(w*0.95), int(h*0.92)),
            "left_logo": (0, int(h*0.08), int(w*0.22), int(h*0.45)),
            "right_logo": (int(w*0.78), int(h*0.08), w, int(h*0.45)),
            "bottom_left_mark": (0, int(h*0.78), int(w*0.30), h),
            "bottom_right_mark": (int(w*0.70), int(h*0.78), w, h),
        }

    def _threshold(self, key):
        if "caption" in key:
            return 0.045
        if "text" in key:
            return 0.04
        return 0.035

    def _risk_summary(self, hits, sampled):
        sampled = max(1, sampled)
        result = {}
        for key, arr in hits.items():
            ratio = len(arr) / sampled
            if ratio >= 0.45:
                level = "높음"
            elif ratio >= 0.2:
                level = "중간"
            elif ratio > 0:
                level = "낮음"
            else:
                level = "없음"
            result[key] = {
                "level": level,
                "hit_count": len(arr),
                "sampled_frames": sampled,
                "ratio": round(ratio, 2),
            }
        return result

    def _recommendation(self, risk):
        bottom = risk.get("bottom_caption", {}).get("level", "없음")
        top = risk.get("top_text", {}).get("level", "없음")
        right = risk.get("right_logo", {}).get("level", "없음")
        left = risk.get("left_logo", {}).get("level", "없음")
        br = risk.get("bottom_right_mark", {}).get("level", "없음")
        bl = risk.get("bottom_left_mark", {}).get("level", "없음")

        if bottom in ["높음", "중간"]:
            subtitle = "45~50% 높이로 올리기"
        elif top in ["높음", "중간"]:
            subtitle = "중앙 하단 / 하단 40% 유지"
        else:
            subtitle = "중앙 하단 / 하단 40%"

        crop = "9:16 유지"
        if right in ["높음", "중간"] or left in ["높음", "중간"] or br in ["높음", "중간"] or bl in ["높음", "중간"]:
            crop = "105~115% 확대 크롭 우선 검토"

        blur = "필요 없음"
        if right in ["높음", "중간"] or left in ["높음", "중간"] or br in ["높음", "중간"] or bl in ["높음", "중간"]:
            blur = "상품을 가리지 않는 로고/워터마크만 블러"

        return {
            "subtitle_position": subtitle,
            "crop": crop,
            "blur": blur,
            "caption_note": "하단 중국어 자막 위험이 있으면 하센 자막을 더 위로 올리세요.",
        }

    def _capcut_actions(self, rec):
        return [
            {"action": "자막 위치", "value": rec.get("subtitle_position"), "reason": rec.get("caption_note")},
            {"action": "크롭", "value": rec.get("crop"), "reason": "로고/워터마크 가능 영역 기준"},
            {"action": "블러", "value": rec.get("blur"), "reason": "워터마크가 남을 경우"},
            {"action": "AI 음성", "value": "20 dB", "reason": "CapCut 최대 볼륨 기준"},
            {"action": "BGM", "value": "8 dB", "reason": "정보형 기본값"},
        ]
