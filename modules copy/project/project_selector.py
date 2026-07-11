from sqlalchemy import select

from database.db import SessionLocal
from database.models import Project
from modules.project.repository import ProjectRepository


class ProjectSelector:
    """
    UI 공통 프로젝트 선택 유틸.
    Repository 결과가 비어 보이는 경우에도 DB에서 직접 재조회합니다.
    """

    def all_projects(self):
        projects = ProjectRepository().all()
        if projects:
            return projects

        # fallback: direct DB query
        with SessionLocal() as db:
            return list(db.scalars(select(Project).order_by(Project.id.desc())))

    def labels(self, projects):
        return {
            f"{p.id} | {p.product_name or p.title or '이름 없음'} | {p.status}": p
            for p in projects
        }

    def get_latest(self):
        projects = self.all_projects()
        return projects[0] if projects else None
