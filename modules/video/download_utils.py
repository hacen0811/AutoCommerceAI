import re
from pathlib import Path


def safe_file_name(text, fallback="video"):
    text = str(text or fallback).strip()
    text = re.sub(r"[^0-9A-Za-z가-힣._-]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text[:80] or fallback


def project_source_video_dir(project):
    project_id = str(getattr(project, "id", "") or "unknown_project")
    project_name = safe_file_name(
        getattr(project, "product_name", "") or getattr(project, "title", ""),
        "project",
    )

    folder = Path("assets") / "source_videos" / f"project_{project_id}_{project_name}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def download_folders():
    folders = []
    home_downloads = Path.home() / "Downloads"
    folders.append(home_downloads)

    for candidate in [
        Path(r"C:\Users\user\Downloads"),
        Path(r"C:\Users\user\다운로드"),
        Path.home() / "다운로드",
    ]:
        if candidate not in folders:
            folders.append(candidate)

    return [folder for folder in folders if folder.exists()]


def latest_downloaded_video(max_age_minutes=240):
    allowed = {".mp4", ".mov", ".webm"}
    candidates = []

    for folder in download_folders():
        try:
            for path in folder.iterdir():
                if not path.is_file():
                    continue
                if path.suffix.lower() not in allowed:
                    continue
                if path.name.lower().endswith(".crdownload") or path.name.lower().endswith(".part"):
                    continue
                candidates.append(path)
        except Exception:
            pass

    if not candidates:
        return None

    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]