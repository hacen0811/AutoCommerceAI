from pathlib import Path
import shutil


class DataMigration:
    def __init__(self, current_root=None):
        self.current_root = Path(current_root or Path.cwd()).resolve()

    def inspect_previous(self, previous_folder):
        prev = Path(previous_folder or "").expanduser().resolve()
        db = prev / "database" / "autocommerce_x.db"
        videos = prev / "assets" / "videos"
        images = prev / "assets" / "images"
        exports = prev / "exports"

        return {
            "previous_folder": str(prev),
            "exists": prev.exists(),
            "database_exists": db.exists(),
            "database_path": str(db),
            "videos_exists": videos.exists(),
            "videos_count": len(list(videos.glob("*"))) if videos.exists() else 0,
            "images_exists": images.exists(),
            "images_count": len(list(images.glob("*"))) if images.exists() else 0,
            "exports_exists": exports.exists(),
        }

    def import_data(self, previous_folder, copy_exports=False, overwrite=True):
        info = self.inspect_previous(previous_folder)
        if not info["exists"]:
            return {"ok": False, "message": "이전 폴더를 찾을 수 없습니다.", "info": info}

        copied = []
        src_db = Path(info["database_path"])
        dst_db = self.current_root / "database" / "autocommerce_x.db"
        if src_db.exists():
            dst_db.parent.mkdir(parents=True, exist_ok=True)
            if overwrite or not dst_db.exists():
                shutil.copy2(src_db, dst_db)
                copied.append(str(dst_db))

        for folder in ["assets/videos", "assets/images"]:
            src = Path(previous_folder) / folder
            dst = self.current_root / folder
            if src.exists():
                dst.mkdir(parents=True, exist_ok=True)
                for item in src.iterdir():
                    if item.is_file():
                        target = dst / item.name
                        if overwrite or not target.exists():
                            shutil.copy2(item, target)
                            copied.append(str(target))

        if copy_exports:
            src = Path(previous_folder) / "exports"
            dst = self.current_root / "exports"
            if src.exists():
                for item in src.rglob("*"):
                    if item.is_file():
                        target = dst / item.relative_to(src)
                        target.parent.mkdir(parents=True, exist_ok=True)
                        if overwrite or not target.exists():
                            shutil.copy2(item, target)
                            copied.append(str(target))

        return {"ok": True, "message": f"{len(copied)}개 파일을 가져왔습니다.", "copied": copied[:100], "info": info}
