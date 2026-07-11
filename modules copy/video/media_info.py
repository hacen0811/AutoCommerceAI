import json
import subprocess
from pathlib import Path

from modules.system.ffmpeg_checker import FFmpegChecker


class MediaInfo:
    """
    영상 메타데이터 분석.
    1순위: ffprobe
    2순위: OpenCV fallback
    """

    def analyze(self, video_path):
        path = Path(video_path or "")
        if not video_path or not path.exists():
            return self.empty("영상 파일이 없습니다.")

        base = {
            "ok": True,
            "file": str(path),
            "filename": path.name,
            "size_mb": round(path.stat().st_size / (1024 * 1024), 2),
            "width": 0,
            "height": 0,
            "fps": 0,
            "duration": 0,
            "orientation": "-",
            "method": "",
            "warning": "",
        }

        ff = FFmpegChecker().check()
        if ff.get("ffprobe_ok"):
            result = self._ffprobe(path, base)
            if result.get("width") and result.get("height"):
                return result

        result = self._opencv(path, base)
        if result.get("width") and result.get("height"):
            if not ff.get("ffprobe_ok"):
                result["warning"] = "ffprobe 미설치: OpenCV fallback으로 분석했습니다."
            return result

        base["warning"] = "ffprobe/OpenCV 모두 영상 메타데이터를 읽지 못했습니다."
        return base

    def empty(self, msg):
        return {
            "ok": False,
            "error": msg,
            "file": "",
            "filename": "",
            "size_mb": 0,
            "width": 0,
            "height": 0,
            "fps": 0,
            "duration": 0,
            "orientation": "-",
            "method": "",
            "warning": msg,
        }

    def _ffprobe(self, path, base):
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height,r_frame_rate,duration",
                "-of", "json",
                str(path),
            ]
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            data = json.loads(out.stdout or "{}")
            stream = (data.get("streams") or [{}])[0]
            width = int(stream.get("width") or 0)
            height = int(stream.get("height") or 0)
            fps = self._fps(stream.get("r_frame_rate", "0/1"))
            duration = float(stream.get("duration") or 0)

            base.update({
                "width": width,
                "height": height,
                "fps": round(fps, 2),
                "duration": round(duration, 2),
                "orientation": self._orientation(width, height),
                "method": "ffprobe",
            })
            return base
        except Exception as exc:
            base["warning"] = f"ffprobe 분석 실패: {exc}"
            return base

    def _opencv(self, path, base):
        try:
            import cv2
            cap = cv2.VideoCapture(str(path))
            if not cap.isOpened():
                base["warning"] = "OpenCV가 영상을 열 수 없습니다."
                return base

            fps = cap.get(cv2.CAP_PROP_FPS) or 0
            total = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
            cap.release()

            duration = float(total / fps) if fps else 0
            base.update({
                "width": width,
                "height": height,
                "fps": round(float(fps), 2) if fps else 0,
                "duration": round(duration, 2),
                "orientation": self._orientation(width, height),
                "method": "opencv",
            })
            return base
        except Exception as exc:
            base["warning"] = f"OpenCV 분석 실패: {exc}"
            return base

    def _fps(self, value):
        try:
            if "/" in value:
                a, b = value.split("/", 1)
                return float(a) / float(b or 1)
            return float(value)
        except Exception:
            return 0

    def _orientation(self, width, height):
        if not width or not height:
            return "-"
        if height > width:
            return "세로 9:16 후보"
        if width > height:
            return "가로 영상 / 9:16 크롭 필요"
        return "정사각형"
