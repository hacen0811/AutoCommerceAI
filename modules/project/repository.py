import json
from sqlalchemy import select
from database.db import SessionLocal
from database.models import Project, Checklist
from modules.system.project_backup import ProjectBackup


class ProjectRepository:
    def create(self, payload):
        with SessionLocal() as db:
            item = Project(
                title=payload.get("title") or payload.get("product_name") or "새 프로젝트",
                product_name=payload.get("product_name", ""),
                status=payload.get("status", "기획"),
                coupang_url=payload.get("coupang_url", ""),
                partner_url=payload.get("partner_url", ""),
                taobao_url=payload.get("taobao_url", ""),
                douyin_url=payload.get("douyin_url", ""),
                video_path=payload.get("video_path", ""),
                image_url=payload.get("image_url", ""),
                price=payload.get("price", ""),
                category=payload.get("category", ""),
                keyword=payload.get("keyword", "정보"),
                score=payload.get("score", 0),
                data_json=json.dumps(payload.get("data", {}), ensure_ascii=False, indent=2),
            )
            db.add(item)
            db.commit()
            db.refresh(item)

            checklist = Checklist(project_id=item.id, source_video=bool(item.video_path))
            db.add(checklist)
            db.commit()
            ProjectBackup().auto_export_on_change()
            ProjectBackup().auto_export_on_change()
            return item


    def find_by_coupang_url(self, coupang_url):
        with SessionLocal() as db:
            return db.scalar(select(Project).where(Project.coupang_url == coupang_url))

    def all(self):
        with SessionLocal() as db:
            return list(db.scalars(select(Project).order_by(Project.id.desc())))

    def get(self, project_id):
        with SessionLocal() as db:
            return db.get(Project, project_id)

    def update_status(self, project_id, status):
        with SessionLocal() as db:
            item = db.get(Project, project_id)
            if not item:
                return None
            item.status = status
            db.commit()
            ProjectBackup().auto_export_on_change()
            return item

    def update_links_and_media(self, project_id, **kwargs):
        with SessionLocal() as db:
            item = db.get(Project, project_id)
            if not item:
                return None
            for key, value in kwargs.items():
                if hasattr(item, key):
                    setattr(item, key, value)
            db.commit()
            db.refresh(item)
            ProjectBackup().auto_export_on_change()
            return item

    def checklist(self, project_id):
        with SessionLocal() as db:
            item = db.scalar(select(Checklist).where(Checklist.project_id == project_id))
            if not item:
                item = Checklist(project_id=project_id)
                db.add(item)
                db.commit()
                db.refresh(item)
            return item

    def update_checklist(self, project_id, **kwargs):
        with SessionLocal() as db:
            item = db.scalar(select(Checklist).where(Checklist.project_id == project_id))
            if not item:
                item = Checklist(project_id=project_id)
                db.add(item)
            for key, value in kwargs.items():
                if hasattr(item, key):
                    setattr(item, key, bool(value))
            db.commit()
            db.refresh(item)
            return item
