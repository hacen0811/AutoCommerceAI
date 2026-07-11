from pathlib import Path
import subprocess
import json


class VideoQualityEngine:
    def score(self, video_path, real_vision=None):
        path = Path(video_path) if video_path else None

        if not path or not path.exists():
            return {
                "ok": False,
                "score": 0,
                "grade": "D",
                "recommendation": "분석 불가",
                "reason": "영상 파일을 찾을 수 없습니다.",
                "checks": [],
                "suitability_score": 0,
                "suitability_checks": [],
                "video_path": str(video_path or ""),
            }

        meta = self._probe(path)
        real_vision = real_vision or {}

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

        suitability_score, suitability_checks = self._score_suitability(real_vision)

        final_score = min(score + suitability_score, 100)
        grade = self._grade(final_score)
        recommendation = self._recommendation(final_score)

        return {
            "ok": True,
            "score": final_score,
            "base_score": score,
            "grade": grade,
            "recommendation": recommendation,
            "reason": "메타데이터 + 쇼핑쇼츠 적합도 평가 완료",
            "checks": checks,
            "suitability_score": suitability_score,
            "suitability_checks": suitability_checks,
            "details": {
                "width": width,
                "height": height,
                "duration": duration,
                "fps": fps,
                "size_mb": round(path.stat().st_size / 1024 / 1024, 2),
            },
            "video_path": str(path),
        }

    def _score_suitability(self, real_vision):
        suitability_score = 0
        suitability_checks = []

        summary = real_vision.get("summary", "")

        if summary:
            suitability_score += 10
            suitability_checks.append("Real Vision 분석 결과 있음")

        if "후킹" in summary:
            suitability_score += 10
            suitability_checks.append("후킹 컷 후보 있음")

        if "중앙 하단" in summary:
            suitability_score += 10
            suitability_checks.append("자막 안전 위치 추천 있음")

        status = real_vision.get("status", {})

        if status.get("object_fallback") or status.get("video_ai"):
            suitability_score += 10
            suitability_checks.append("상품/장면 분석 사용 가능")

        return suitability_score, suitability_checks

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