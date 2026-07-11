import shutil
import subprocess


class FFmpegChecker:
    """
    FFmpeg/ffprobe 설치 상태 확인.
    자동 설치는 Windows 환경별 권한 문제가 있어 안내 중심으로 구현합니다.
    """

    def check(self):
        ffmpeg = shutil.which("ffmpeg")
        ffprobe = shutil.which("ffprobe")

        result = {
            "ffmpeg_path": ffmpeg or "",
            "ffprobe_path": ffprobe or "",
            "ffmpeg_ok": bool(ffmpeg),
            "ffprobe_ok": bool(ffprobe),
            "ready": bool(ffmpeg and ffprobe),
            "ffmpeg_version": "",
            "ffprobe_version": "",
            "install_guide": [
                "1. https://www.gyan.dev/ffmpeg/builds/ 에서 ffmpeg-release-essentials.zip 다운로드",
                "2. 압축 해제 후 bin 폴더 경로 확인",
                "3. Windows 환경 변수 Path에 bin 폴더 추가",
                "4. PowerShell/CMD를 새로 열고 ffmpeg -version, ffprobe -version 확인",
                "5. AutoCommerceAI 재실행",
            ],
            "winget_command": "winget install Gyan.FFmpeg",
        }

        if ffmpeg:
            result["ffmpeg_version"] = self._version("ffmpeg")
        if ffprobe:
            result["ffprobe_version"] = self._version("ffprobe")

        return result

    def _version(self, cmd):
        try:
            out = subprocess.run([cmd, "-version"], capture_output=True, text=True, timeout=5)
            return (out.stdout or out.stderr).splitlines()[0]
        except Exception as exc:
            return str(exc)
