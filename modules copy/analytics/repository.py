from sqlalchemy import select
from database.db import SessionLocal
from database.models import Performance


class PerformanceRepository:
    def create(self, project_id, views=0, likes=0, comments=0, saves=0, note=""):
        with SessionLocal() as db:
            item = Performance(
                project_id=project_id,
                views=int(views),
                likes=int(likes),
                comments=int(comments),
                saves=int(saves),
                note=note,
            )
            db.add(item)
            db.commit()
            return item

    def all(self):
        with SessionLocal() as db:
            return list(db.scalars(select(Performance).order_by(Performance.views.desc())))
