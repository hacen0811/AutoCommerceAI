from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATABASE_PATH = BASE_DIR / "database" / "autocommerce_x.db"
ASSETS_DIR = BASE_DIR / "assets"
VIDEO_DIR = ASSETS_DIR / "videos"
IMAGE_DIR = ASSETS_DIR / "images"
EXPORTS_DIR = BASE_DIR / "exports"

for path in [DATABASE_PATH.parent, VIDEO_DIR, IMAGE_DIR, EXPORTS_DIR, BASE_DIR / "backups"]:
    path.mkdir(parents=True, exist_ok=True)
