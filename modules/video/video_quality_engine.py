from pathlib import Path
import subprocess
import json


class VideoQualityEngine:
    def score(self, video_path):
        path = Path(video_path) if video_path else None

        if not path or not path.exists():
            return {
                "ok": False,
                "score": 0,
                "grade": "D",
                "recommendation": "분석 불가",
                "reason": "영상 파일을 찾을 수 없습니다.",
                "video_path": str(video_path or ""),
            }

        meta = self._probe(path)

        score = 10
        checks = ["영상 파일 존재"]

        width = meta.get("width", 0)
        height = meta.get("height", 0)
        duration = meta.get("duration", 0)
        fps = meta.get("fps", 0)

        if height > width:
            score += 20
            checks.append("세로 영상")

        if width >= 1080 and height >= 1920:
            score += 20
            checks.append("1080x1920 이상")

        if 5 <= duration <= 30:
            score += 20
            checks.append("쇼츠 적정 길이")

        if fps >= 24:
            score += 10
            checks.append("FPS 양호")

        if path.stat().st_size > 1_000_000:
            score += 10
            checks.append("파일 용량 정상")

        score = min(score, 100)
        grade = self._grade(score)
        recommendation = self._recommendation(score)

        return {
            "ok": True,
            "score": score,
            "grade": grade,
            "recommendation": recommendation,
            "reason": "기본 메타데이터 기반 품질 평가 완료",
            "checks": checks,
            "details": {
                "width": width,
                "height": height,
                "duration": duration,
                "fps": fps,
                "size_mb": round(path.stat().st_size / 1024 / 1024, 2),
            },
            "video_path": str(path),
        }

    def _probe(self, path):
        try:
            cmd = [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height,r_frame_rate,duration",
                "-of",
                "json",
                str(path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            stream = data.get("streams", [{}])[0]

            fps_text = stream.get("r_frame_rate", "0/1")
            fps = self._parse_fps(fps_text)

            return {
                "width": int(stream.get("width", 0) or 0),
                "height": int(stream.get("height", 0) or 0),
                "duration": float(stream.get("duration", 0) or 0),
                "fps": fps,
            }

        except Exception as exc:
            return {
                "width": 0,
                "height": 0,
                "duration": 0,
                "fps": 0,
                "error": str(exc),
            }

    def _parse_fps(self, value):
        try:
            if "/" in value:
                a, b = value.split("/")
                return round(float(a) / float(b), 2) if float(b) else 0
            return round(float(value), 2)
        except Exception:
            return 0

    def _grade(self, score):
        if score >= 90:
            return "S"
        if score >= 80:
            return "A"
        if score >= 60:
            return "B"
        if score >= 40:
            return "C"
        return "D"

    def _recommendation(self, score):
        if score >= 90:
            return "즉시 사용 추천"
        if score >= 80:
            return "사용 추천"
        if score >= 60:
            return "보완 후 사용"
        if score >= 40:
            return "검토 필요"
        return "재수집 권장"