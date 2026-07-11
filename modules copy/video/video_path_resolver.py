from pathlib import Path
from modules.project.repository import ProjectRepository


class VideoPathResolver:
    def resolve_project(self, project):
        project_id = getattr(project, "id", None)
        if project_id:
            try:
                fresh = ProjectRepository().get(project_id)
                if fresh:
                    return fresh
            except Exception:
                return project
        return project

    def _safe_name(self, name):
        return (
            str(name or "project")
            .replace(" ", "_")
            .replace("/", "_")
            .replace("\\", "_")
            .replace(":", "_")
        )

    def _candidate_dirs(self, project):
        project_id = getattr(project, "id", None)
        product_name = getattr(project, "product_name", "") or getattr(project, "title", "")

        names = []

        if project_id and product_name:
            names.append(f"project_{project_id}_{self._safe_name(product_name)}")

        if product_name:
            names.append(self._safe_name(product_name))

        if project_id:
            names.append(f"project_{project_id}")

        return [Path("assets/source_videos") / name for name in names]

    def _find_latest_video(self, project):
        candidates = []

        for folder in self._candidate_dirs(project):
            if folder.exists():
                candidates.extend(folder.glob("*.mp4"))

        if not candidates:
            return ""

        latest = max(candidates, key=lambda p: p.stat().st_mtime)
        return str(latest)

    def resolve_path(self, project):
        fresh = self.resolve_project(project)

        video_path = (
            getattr(fresh, "video_path", "")
            or getattr(project, "video_path", "")
            or ""
        )

        video_path = str(video_path).strip().strip('"').strip("'")

        if video_path and Path(video_path).exists():
            return video_path

        fallback = self._find_latest_video(fresh)

        if fallback:
            try:
                ProjectRepository().update_links_and_media(
                    getattr(fresh, "id", None),
                    video_path=fallback,
                )
            except Exception:
                pass

            return fallback

        return video_path

    def exists(self, video_path):
        return bool(video_path) and Path(video_path).exists()

    def debug(self, project):
        fresh = self.resolve_project(project)
        video_path = self.resolve_path(fresh)
        p = Path(video_path) if video_path else None

        return {
            "project_id": getattr(fresh, "id", None),
            "title": getattr(fresh, "title", ""),
            "product_name": getattr(fresh, "product_name", ""),
            "video_path": video_path,
            "exists": bool(p and p.exists()),
            "size_mb": round(p.stat().st_size / (1024 * 1024), 2) if p and p.exists() else 0,
        }
