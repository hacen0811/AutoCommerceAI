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
                # 테스트 환경 또는 DB 미초기화 상태에서는 전달받은 객체를 그대로 사용
                return project
        return project

    def resolve_path(self, project):
        fresh = self.resolve_project(project)
        video_path = getattr(fresh, "video_path", "") or getattr(project, "video_path", "") or ""
        return str(video_path).strip().strip('"').strip("'")

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
