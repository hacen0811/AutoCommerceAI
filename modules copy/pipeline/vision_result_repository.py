import json
from datetime import datetime
from pathlib import Path


class VisionResultRepository:
    def __init__(self):
        self.base = Path("exports/vision_results")
        self.base.mkdir(parents=True, exist_ok=True)

    def save(self, project, result):
        safe_name = "".join(c for c in project.product_name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        if not safe_name:
            safe_name = f"project_{project.id}"

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.base / f"{safe_name}_{ts}_vision.json"
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path)

    def latest_files(self, limit=20):
        files = sorted(self.base.glob("*_vision.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        return files[:limit]
