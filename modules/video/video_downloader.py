from pathlib import Path
import shutil
from datetime import datetime


class VideoDownloader:
    def __init__(self, base_dir="assets/source_videos"):
        self.base_dir = Path(base_dir)

    def safe_name(self, name):
        return (
            str(name or "project")
            .replace(" ", "_")
            .replace("/", "_")
            .replace("\\", "_")
            .replace(":", "_")
        )

    def save_video(self, project_name, downloaded_file):
        downloaded_file = Path(downloaded_file)

        if not downloaded_file.exists():
            raise FileNotFoundError(f"다운로드 영상 파일을 찾을 수 없습니다: {downloaded_file}")

        project_dir = self.base_dir / self.safe_name(project_name)
        project_dir.mkdir(parents=True, exist_ok=True)

        ext = downloaded_file.suffix or ".mp4"
        filename = f"source_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"

        target_path = project_dir / filename
        shutil.copy2(downloaded_file, target_path)

        return str(target_path)