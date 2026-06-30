from pathlib import Path
import shutil
from uuid import uuid4
from config.settings import VIDEO_DIR


class VideoService:
    def save_uploaded_video(self, uploaded_file):
        if not uploaded_file:
            return ""

        original = Path(getattr(uploaded_file, "name", "source_video.mp4")).name
        suffix = Path(original).suffix or ".mp4"
        stem = Path(original).stem or "source_video"
        safe_stem = "".join(c for c in stem if c.isalnum() or c in ("_", "-", " ")).strip().replace(" ", "_") or "source_video"
        target = VIDEO_DIR / f"{safe_stem}_{uuid4().hex[:8]}{suffix}"

        VIDEO_DIR.mkdir(parents=True, exist_ok=True)

        with open(target, "wb") as f:
            # Streamlit UploadedFile supports file-like copy.
            try:
                uploaded_file.seek(0)
            except Exception:
                pass
            shutil.copyfileobj(uploaded_file, f)

        if not target.exists() or target.stat().st_size == 0:
            raise RuntimeError("영상 저장 실패: 저장된 파일 크기가 0입니다.")

        return str(target)
