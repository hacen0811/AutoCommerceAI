import json
import shutil
from datetime import datetime
from pathlib import Path

from database.db import SessionLocal
from database.models import Project, Checklist, Performance


class ProjectBackup:
    """
    DB가 사라져도 프로젝트를 복구할 수 있도록 JSON 백업/복원을 제공합니다.
    """

    def __init__(self, root=None):
        self.root = Path(root or Path.cwd()).resolve()
        self.backup_dir = self.root / "backups" / "project_backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def export_all(self, include_assets=True):
        data = {
            "version": "2.0",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "projects": [],
            "checklists": [],
            "performances": [],
            "assets": {"videos": [], "images": []},
        }

        with SessionLocal() as db:
            data["projects"] = [self._model_dict(p) for p in db.query(Project).all()]
            data["checklists"] = [self._model_dict(c) for c in db.query(Checklist).all()]
            data["performances"] = [self._model_dict(p) for p in db.query(Performance).all()]

        if include_assets:
            for folder, key in [("assets/videos", "videos"), ("assets/images", "images")]:
                src = self.root / folder
                if src.exists():
                    for f in src.iterdir():
                        if f.is_file():
                            data["assets"][key].append(str(f.relative_to(self.root)))

        out = self.backup_dir / f"autocommerce_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return str(out)

    def import_backup(self, backup_json, copy_assets_from=None, overwrite=False):
        path = Path(backup_json)
        if not path.exists():
            return {"ok": False, "message": "백업 JSON을 찾을 수 없습니다."}

        data = json.loads(path.read_text(encoding="utf-8"))
        imported = {"projects": 0, "checklists": 0, "performances": 0, "assets": 0}

        with SessionLocal() as db:
            for item in data.get("projects", []):
                existing = db.get(Project, item.get("id")) if item.get("id") else None
                if existing and not overwrite:
                    continue
                obj = existing or Project()
                self._apply(obj, item, Project)
                db.add(obj)
                imported["projects"] += 1

            for item in data.get("checklists", []):
                existing = db.get(Checklist, item.get("id")) if item.get("id") else None
                if existing and not overwrite:
                    continue
                obj = existing or Checklist()
                self._apply(obj, item, Checklist)
                db.add(obj)
                imported["checklists"] += 1

            for item in data.get("performances", []):
                existing = db.get(Performance, item.get("id")) if item.get("id") else None
                if existing and not overwrite:
                    continue
                obj = existing or Performance()
                self._apply(obj, item, Performance)
                db.add(obj)
                imported["performances"] += 1

            db.commit()

        if copy_assets_from:
            base = Path(copy_assets_from)
            for rel in (data.get("assets", {}).get("videos", []) + data.get("assets", {}).get("images", [])):
                src = base / rel
                dst = self.root / rel
                if src.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    if overwrite or not dst.exists():
                        shutil.copy2(src, dst)
                        imported["assets"] += 1

        return {"ok": True, "message": "백업 복원 완료", "imported": imported}

    def latest_backup(self):
        files = sorted(self.backup_dir.glob("autocommerce_backup_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        return str(files[0]) if files else ""

    def auto_export_on_change(self):
        try:
            return self.export_all(include_assets=True)
        except Exception:
            return ""

    def _model_dict(self, obj):
        out = {}
        for col in obj.__table__.columns:
            v = getattr(obj, col.name)
            out[col.name] = v.isoformat() if hasattr(v, "isoformat") else v
        return out

    def _apply(self, obj, data, model):
        cols = {c.name for c in model.__table__.columns}
        for k, v in data.items():
            if k in cols and k != "created_at":
                setattr(obj, k, v)
