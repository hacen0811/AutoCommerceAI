from pathlib import Path
from modules.video.vision_overlay import VisionOverlayExporter


class VisionAIEngine:
    """
    Vision AI Starter.
    - OpenCV 기반 영역 분석
    - OCR 도구가 PC에 설치되어 있으면 pytesseract로 텍스트 시도
    - 설치되어 있지 않아도 자막/워터마크 위험 분석은 계속 동작
    """

    def analyze(self, video_path, sample_count=6, use_ocr=False):
        path = Path(video_path or "")
        if not video_path or not path.exists():
            return self.empty("영상 파일이 없습니다.")

        try:
            import cv2
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

        regions = self._regions(width, height)
        region_stats = {k: [] for k in regions}
        ocr_texts = []
        sample_images = []

        export_dir = Path("exports/vision_frames")
        export_dir.mkdir(parents=True, exist_ok=True)

        step = max(1, total // max(1, sample_count))
        frame_i = 0
        sample_i = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_i % step == 0:
                time_sec = round(frame_i / fps, 2) if fps else 0
                frame_file = export_dir / f"{path.stem}_vision_{sample_i:02d}.jpg"
                cv2.imwrite(str(frame_file), frame)
                sample_images.append({"time": time_sec, "frame": str(frame_file)})

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                for key, (x1, y1, x2, y2) in regions.items():
                    roi = gray[y1:y2, x1:x2]
                    stats = self._roi_stats(roi)
                    stats.update({"time": time_sec, "region": [x1, y1, x2, y2]})
                    region_stats[key].append(stats)

                    if use_ocr and key in ["top_text", "bottom_caption"]:
                        text = self._try_ocr(roi)
                        if text:
                            ocr_texts.append({"time": time_sec, "region": key, "text": text})

                sample_i += 1

            frame_i += 1

        cap.release()

        risk = self._risk(region_stats)
        guide = self._guide(risk, ocr_texts)

        return {
            "ok": True,
            "file": str(path),
            "filename": path.name,
            "width": width,
            "height": height,
            "fps": round(fps, 2) if fps else "",
            "sampled_frames": sample_i,
            "regions": regions,
            "risk": risk,
            "ocr_texts": ocr_texts,
            "ocr_status": self._ocr_status(use_ocr),
            "sample_images": sample_images,
            "guide": guide,
            "capcut_actions": self._capcut_actions(guide),
            "overlay_image": VisionOverlayExporter().export(str(path), regions, f"{path.stem}_regions.jpg"),
            "notice": "OCR은 PC에 Tesseract OCR 프로그램이 설치되어 있을 때만 실제 문자 인식이 됩니다. 미설치 시에도 화면 영역 위험 분석은 동작합니다.",
        }

    def empty(self, message):
        return {
            "ok": False,
            "error": message,
            "risk": {},
            "ocr_texts": [],
            "ocr_status": "미실행",
            "sample_images": [],
            "guide": self._default_guide(),
            "capcut_actions": self._capcut_actions(self._default_guide()),
        }

    def _regions(self, w, h):
        return {
            "top_text": (int(w*0.05), int(h*0.02), int(w*0.95), int(h*0.18)),
            "bottom_caption": (int(w*0.05), int(h*0.68), int(w*0.95), int(h*0.93)),
            "center_product": (int(w*0.20), int(h*0.22), int(w*0.80), int(h*0.70)),
            "left_logo": (0, int(h*0.06), int(w*0.25), int(h*0.45)),
            "right_logo": (int(w*0.75), int(h*0.06), w, int(h*0.45)),
            "bottom_left_mark": (0, int(h*0.78), int(w*0.32), h),
            "bottom_right_mark": (int(w*0.68), int(h*0.78), w, h),
        }

    def _roi_stats(self, roi):
        try:
            import cv2
            if roi is None or roi.size == 0:
                return {"edge_density": 0, "brightness": 0, "contrast": 0}
            edges = cv2.Canny(roi, 80, 180)
            return {
                "edge_density": round(float((edges > 0).mean()), 4),
                "brightness": round(float(roi.mean()), 2),
                "contrast": round(float(roi.std()), 2),
            }
        except Exception:
            return {"edge_density": 0, "brightness": 0, "contrast": 0}

    def _try_ocr(self, roi):
        try:
            import pytesseract
            from PIL import Image
            import cv2
            img = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            pil = Image.fromarray(img)
            text = pytesseract.image_to_string(pil, lang="chi_sim+eng+kor")
            return " ".join(text.split()).strip()
        except Exception:
            return ""

    def _ocr_status(self, use_ocr):
        if not use_ocr:
            return "사용 안 함"
        try:
            import pytesseract
            _ = pytesseract.get_tesseract_version()
            return "사용 가능"
        except Exception:
            return "pytesseract 또는 Tesseract OCR 프로그램 미설치"

    def _risk(self, region_stats):
        result = {}
        for region, rows in region_stats.items():
            if not rows:
                result[region] = {"level": "없음", "avg_edge": 0, "hit_ratio": 0}
                continue

            if region == "center_product":
                # center_product is usefulness score, not danger
                avg_contrast = sum(r["contrast"] for r in rows) / len(rows)
                avg_brightness = sum(r["brightness"] for r in rows) / len(rows)
                level = "좋음" if avg_contrast >= 35 and 60 <= avg_brightness <= 210 else "보통"
                result[region] = {
                    "level": level,
                    "avg_contrast": round(avg_contrast, 2),
                    "avg_brightness": round(avg_brightness, 2),
                    "meaning": "상품/중앙 장면 선명도 후보",
                }
                continue

            avg_edge = sum(r["edge_density"] for r in rows) / len(rows)
            hit_ratio = sum(1 for r in rows if r["edge_density"] >= self._threshold(region)) / len(rows)

            if hit_ratio >= 0.5:
                level = "높음"
            elif hit_ratio >= 0.25:
                level = "중간"
            elif hit_ratio > 0:
                level = "낮음"
            else:
                level = "없음"

            result[region] = {
                "level": level,
                "avg_edge": round(avg_edge, 4),
                "hit_ratio": round(hit_ratio, 2),
            }
        return result

    def _threshold(self, region):
        if region == "bottom_caption":
            return 0.043
        if region == "top_text":
            return 0.04
        return 0.034

    def _guide(self, risk, ocr_texts):
        bottom = risk.get("bottom_caption", {}).get("level", "없음")
        top = risk.get("top_text", {}).get("level", "없음")
        logo_levels = [
            risk.get("left_logo", {}).get("level", "없음"),
            risk.get("right_logo", {}).get("level", "없음"),
            risk.get("bottom_left_mark", {}).get("level", "없음"),
            risk.get("bottom_right_mark", {}).get("level", "없음"),
        ]

        if bottom in ["높음", "중간"] or ocr_texts:
            subtitle = "45~50% 높이로 올리기"
        elif top in ["높음", "중간"]:
            subtitle = "중앙 하단 / 하단 40% 유지"
        else:
            subtitle = "중앙 하단 / 하단 40%"

        crop = "9:16 유지"
        blur = "필요 시 수동 확인"
        if any(x in ["높음", "중간"] for x in logo_levels):
            crop = "105~115% 확대 크롭 우선"
            blur = "상품을 가리지 않는 로고/워터마크만 블러"

        return {
            "subtitle_position": subtitle,
            "crop": crop,
            "blur": blur,
            "voice_db": "20 dB",
            "bgm_db": "8 dB",
            "pop_db": "7 dB",
            "click_db": "8 dB",
            "whoosh_db": "6 dB",
            "summary": f"자막 위치는 {subtitle}, 크롭은 {crop}, 블러는 {blur}를 추천합니다.",
        }

    def _default_guide(self):
        return {
            "subtitle_position": "중앙 하단 / 하단 40%",
            "crop": "9:16 유지",
            "blur": "필요 시 수동 확인",
            "voice_db": "20 dB",
            "bgm_db": "8 dB",
            "pop_db": "7 dB",
            "click_db": "8 dB",
            "whoosh_db": "6 dB",
            "summary": "기본 CapCut 프리셋을 사용하세요.",
        }

    def _capcut_actions(self, guide):
        return [
            {"action": "자막 위치", "value": guide.get("subtitle_position"), "reason": "텍스트/자막 위험 영역 분석 결과"},
            {"action": "크롭", "value": guide.get("crop"), "reason": "로고/워터마크 위험 영역 분석 결과"},
            {"action": "블러", "value": guide.get("blur"), "reason": "로고/워터마크가 남는 경우"},
            {"action": "AI 음성", "value": guide.get("voice_db"), "reason": "CapCut 최대 볼륨 기준"},
            {"action": "BGM", "value": guide.get("bgm_db"), "reason": "쇼핑쇼츠 정보형 기본값"},
            {"action": "효과음", "value": f"Pop {guide.get('pop_db')} / Click {guide.get('click_db')} / Whoosh {guide.get('whoosh_db')}", "reason": "하센 프리셋"},
        ]
