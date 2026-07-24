from sqlalchemy import select

from database.db import SessionLocal
from database.models import Project
from modules.project.repository import ProjectRepository


VERSION = "project-selector-130-4-utf8-display-trace"

print(
    "######## PROJECT_SELECTOR SPRINT130-4 UTF8 DISPLAY TRACE LOADED ########",
    flush=True,
)


class ProjectSelector:
    """
    UI 공통 프로젝트 선택 유틸.
    Repository 결과가 비어 보이는 경우에도 DB에서 직접 재조회합니다.
    """

    def all_projects(self):
        projects = ProjectRepository().all()

        if projects:
            print(
                "[UTF8 SELECTOR SOURCE] repository",
                "count=",
                len(projects),
                flush=True,
            )
            return projects

        # fallback: direct DB query
        with SessionLocal() as db:
            projects = list(
                db.scalars(
                    select(Project).order_by(Project.id.desc())
                )
            )

        print(
            "[UTF8 SELECTOR SOURCE] direct_db",
            "count=",
            len(projects),
            flush=True,
        )

        return projects

    def labels(self, projects):
        labels = {}

        for project in projects:
            project_id = getattr(project, "id", None)
            product_name = getattr(project, "product_name", "")
            title = getattr(project, "title", "")
            status = getattr(project, "status", "")
            display_name = product_name or title or "이름 없음"
            label = f"{project_id} | {display_name} | {status}"

            print(
                "[UTF8 SELECTOR LABEL]",
                {
                    "id": project_id,
                    "product_name_raw": product_name,
                    "product_name_repr": repr(product_name),
                    "title_raw": title,
                    "title_repr": repr(title),
                    "status_raw": status,
                    "status_repr": repr(status),
                    "label_raw": label,
                    "label_repr": repr(label),
                },
                flush=True,
            )

            labels[label] = project

        return labels

    def get_latest(self):
        projects = self.all_projects()
        return projects[0] if projects else None