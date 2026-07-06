import shutil
import subprocess
import sys
from pathlib import Path

from modules.project.repository import ProjectRepository
from modules.video.download_utils import latest_downloaded_video


def safe_file_name(value, default="file"):
    text = str(value or "").strip()

    if not text:
        text = default

    blocked = '<>:"/\\|?*'

    for ch in blocked:
        text = text.replace(ch, "_")

    return text[:80]


def project_source_video_dir(project):
    project_id = getattr(project, "id", "default")
    base_dir = Path("data") / "source_videos" / str(project_id)
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def open_with_login_browser(url):
    if not url:
        return False

    subprocess.Popen(
        [
            sys.executable,
            "tools/open_source_url.py",
            url,
        ]
    )
    return True


def connect_latest_download_to_project(project, item=None, index=0):
    latest = latest_downloaded_video()

    if not latest:
        return {
            "ok": False,
            "message": "Downloads 폴더에서 mp4/mov/webm 파일을 찾지 못했습니다.",
            "source_path": "",
            "video_path": "",
        }

    out_dir = project_source_video_dir(project)

    project_name = safe_file_name(
        getattr(project, "product_name", "") or getattr(project, "title", ""),
        "project",
    )

    query = safe_file_name(
        (item or {}).get("query", "candidate"),
        "candidate",
    )

    ext = latest.suffix.lower()
    target = out_dir / f"candidate_{index + 1:02d}_{project_name}_{query}{ext}"

    if target.exists():
        stem = target.stem
        n = 2

        while target.exists():
            target = out_dir / f"{stem}_{n}{ext}"
            n += 1

    try:
        shutil.copy2(str(latest), str(target))

        ProjectRepository().update_links_and_media(
            getattr(project, "id"),
            video_path=str(target),
        )

        return {
            "ok": True,
            "message": "다운로드된 최신 영상을 현재 프로젝트에 연결했습니다.",
            "source_path": str(latest),
            "video_path": str(target),
            "size_mb": round(target.stat().st_size / (1024 * 1024), 2),
        }

    except Exception as exc:
        return {
            "ok": False,
            "message": f"영상 연결 실패: {exc}",
            "source_path": str(latest),
            "video_path": "",
        }