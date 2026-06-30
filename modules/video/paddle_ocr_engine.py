from pathlib import Path


class PaddleOCREngine:
    """
    안정화된 PaddleOCR connector.
    - paddleocr 설치 시 실제 OCR
    - OCR 결과 정규화/중복 제거
    - 실패 시 앱 중단 없이 상세 메시지 반환
    """

    def check(self):
        result = {
            "installed": False,
            "ready": False,
            "message": "",
            "install_command": "python -m pip install paddleocr paddlepaddle",
        }
        try:
            import paddleocr  # noqa
            result["installed"] = True
            result["ready"] = True
            result["message"] = "PaddleOCR 사용 가능"
        except Exception as exc:
            result["message"] = f"PaddleOCR 미설치 또는 로딩 실패: {exc}"
        return result

    def analyze_video(self, video_path, sample_count=6, lang="ch"):
        path = Path(video_path or "")
        if not video_path or not path.exists():
            return self.empty("영상 파일이 없습니다.")

        status = self.check()
        if not status["ready"]:
            return self.empty(status["message"], status)

        try:
            import cv2
            from paddleocr import PaddleOCR
        except Exception as exc:
            return self.empty(f"OCR 실행 준비 실패: {exc}", status)

        try:
            ocr = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)
        except TypeError:
            try:
                ocr = PaddleOCR(use_angle_cls=True, lang=lang)
            except Exception as exc:
                return self.empty(f"PaddleOCR 초기화 실패: {exc}", status)
        except Exception as exc:
            return self.empty(f"PaddleOCR 초기화 실패: {exc}", status)

        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            return self.empty("영상을 열 수 없습니다.", status)

        fps = cap.get(cv2.CAP_PROP_FPS) or 0
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        step = max(1, total // max(1, int(sample_count or 1)))

        out_dir = Path("exports/paddle_ocr_frames")
        out_dir.mkdir(parents=True, exist_ok=True)

        detections = []
        sample_images = []
        seen = set()
        i = 0
        si = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if i % step == 0:
                t = round(i / fps, 2) if fps else 0
                frame_path = out_dir / f"{path.stem}_ocr_{si:02d}.jpg"
                cv2.imwrite(str(frame_path), frame)
                sample_images.append({"time": t, "frame": str(frame_path)})

                try:
                    res = ocr.ocr(str(frame_path), cls=True)
                    parsed = self._parse_ocr_result(res, t, width, height)
                    for row in parsed:
                        key = (row.get("region"), row.get("text"))
                        if key in seen:
                            continue
                        seen.add(key)
                        detections.append(row)
                except Exception as exc:
                    detections.append({
                        "time": t,
                        "text": "",
                        "error": str(exc),
                        "box": [],
                        "region": "error",
                        "score": 0,
                    })

                si += 1

            i += 1

        cap.release()
        guide = self._guide(detections, width, height)

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

    def _parse_ocr_result(self, res, time_sec, width, height):
        rows = []
        if not res:
            return rows

        items = res[0] if isinstance(res, list) and res else res
        if not items:
            return rows

        for item in items:
            try:
                box = item[0]
                text = self._clean_text(item[1][0])
                score = float(item[1][1])
                if not text:
                    continue
                xs = [p[0] for p in box]
                ys = [p[1] for p in box]
                x1, y1, x2, y2 = int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))
                rows.append({
                    "time": time_sec,
                    "text": text,
                    "score": round(score, 3),
                    "box": [x1, y1, x2, y2],
                    "region": self._region(y1, y2, height),
                    "length": len(text),
                })
            except Exception:
                continue
        return rows

    def _clean_text(self, text):
        return " ".join(str(text or "").replace("\n", " ").split()).strip()

    def _region(self, y1, y2, height):
        if not height:
            return "unknown"
        center_y = (y1 + y2) / 2
        ratio = center_y / height
        if ratio < 0.25:
            return "top"
        if ratio > 0.65:
            return "bottom"
        return "middle"

    def _guide(self, detections, width, height):
        valid = [d for d in detections if d.get("text")]
        bottom = [d for d in valid if d.get("region") == "bottom"]
        top = [d for d in valid if d.get("region") == "top"]

        if bottom:
            subtitle = "45~50% 높이로 올리기"
        elif top:
            subtitle = "중앙 하단 / 하단 40% 유지"
        else:
            subtitle = "중앙 하단 / 하단 40%"

        return {
            "subtitle_position": subtitle,
            "detected_text_count": len(valid),
            "detected_bottom_text_count": len(bottom),
            "detected_top_text_count": len(top),
            "crop": "9:16 유지, 텍스트가 가장자리면 105~115% 확대 검토",
            "blur": "상품을 가리지 않는 텍스트/워터마크만 블러",
            "summary": f"OCR 텍스트 {len(valid)}개 감지. 하단 {len(bottom)}개, 상단 {len(top)}개. 자막 위치는 {subtitle} 추천.",
            "voice_db": "20 dB",
            "bgm_db": "8 dB",
            "pop_db": "7 dB",
            "click_db": "8 dB",
            "whoosh_db": "6 dB",
        }

    def _default_guide(self):
        return {
            "subtitle_position": "중앙 하단 / 하단 40%",
            "detected_text_count": 0,
            "crop": "9:16 유지",
            "blur": "필요 시 수동 확인",
            "summary": "PaddleOCR 설치 후 실제 OCR 분석이 가능합니다.",
            "voice_db": "20 dB",
            "bgm_db": "8 dB",
            "pop_db": "7 dB",
            "click_db": "8 dB",
            "whoosh_db": "6 dB",
        }

    def _capcut_actions(self, guide):
        return [
            {"action": "자막 위치", "value": guide.get("subtitle_position"), "reason": "PaddleOCR 텍스트 위치 기반"},
            {"action": "크롭", "value": guide.get("crop"), "reason": "텍스트/워터마크 위치 기준"},
            {"action": "블러", "value": guide.get("blur"), "reason": "가려야 할 텍스트가 남는 경우"},
            {"action": "AI 음성", "value": guide.get("voice_db"), "reason": "CapCut 최대 기준"},
            {"action": "BGM", "value": guide.get("bgm_db"), "reason": "하센 기본 프리셋"},
        ]
