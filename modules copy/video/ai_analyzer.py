from pathlib import Path

from modules.video.media_info import MediaInfo


class VideoAIAnalyzer:
    """
    OpenCV 기반 프레임 분석.
    ffprobe 없이도 OpenCV로 FPS/해상도/길이를 읽고 샘플 프레임을 저장합니다.
    """

    def analyze(self, video_path, sample_count=12):
        path = Path(video_path or "")
        if not video_path or not path.exists():
            return {"ok": False, "error": "영상 파일이 없습니다.", "samples": []}

        try:
            import cv2
        except Exception as exc:
            return {"ok": False, "error": f"opencv-python이 필요합니다: {exc}", "samples": []}

        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            return {"ok": False, "error": "영상을 열 수 없습니다.", "samples": []}

        media = MediaInfo().analyze(str(path))
        fps = float(media.get("fps") or cap.get(cv2.CAP_PROP_FPS) or 0)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(media.get("width") or cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(media.get("height") or cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        duration = float(media.get("duration") or (total / fps if fps else 0))

        out_dir = Path("exports/frames")
        out_dir.mkdir(parents=True, exist_ok=True)

        step = max(1, total // max(1, int(sample_count or 1)))
        samples = []
        scene_changes = []
        idx = 0
        si = 0
        prev_gray = None

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if idx % step == 0:
                t = round(idx / fps, 2) if fps else 0
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                brightness = float(gray.mean())
                contrast = float(gray.std())
                change = 0

                if prev_gray is not None:
                    small_prev = cv2.resize(prev_gray, (160, 90))
                    small_gray = cv2.resize(gray, (160, 90))
                    change = float(cv2.absdiff(small_prev, small_gray).mean())
                    if change >= 18:
                        scene_changes.append({"time": t, "change": round(change, 2)})
                prev_gray = gray

                score = self._score(brightness, contrast, change)
                frame_path = out_dir / f"{path.stem}_frame_{si:02d}.jpg"
                cv2.imwrite(str(frame_path), frame)

                samples.append({
                    "time": t,
                    "frame": str(frame_path),
                    "brightness": round(brightness, 2),
                    "contrast": round(contrast, 2),
                    "change": round(change, 2),
                    "score": score,
                    "recommend": self._recommend(score),
                })
                si += 1

            idx += 1

        cap.release()
        ranked = sorted(samples, key=lambda x: x.get("score", 0), reverse=True)

        return {
            "ok": True,
            "file": str(path),
            "filename": path.name,
            "size_mb": media.get("size_mb", 0),
            "width": width,
            "height": height,
            "fps": round(fps, 2) if fps else 0,
            "duration": round(duration, 2),
            "orientation": media.get("orientation", "-"),
            "metadata_method": media.get("method", ""),
            "samples": samples,
            "top_frames": ranked[:5],
            "scene_changes": scene_changes,
        }

    def _score(self, brightness, contrast, change):
        score = 50
        if 60 <= brightness <= 210:
            score += 15
        if contrast >= 35:
            score += 15
        if change >= 12:
            score += 10
        return min(100, int(score))

    def _recommend(self, score):
        if score >= 85:
            return "후킹/썸네일 후보"
        if score >= 70:
            return "사용 후보"
        if score < 55:
            return "삭제 후보"
        return "검토 후보"
