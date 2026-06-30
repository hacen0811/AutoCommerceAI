from pathlib import Path
import shutil


class AutoMigration:
    """
    Downloads 폴더 주변의 AutoCommerceAI 이전 버전을 찾아 DB/영상이 있는 폴더를 제안합니다.
    """

    def find_candidates(self, base=None):
        base = Path(base or Path.home() / "Downloads")
        if not base.exists():
            return []
        candidates = []
        for p in base.glob("AutoCommerceAI*"):
            if not p.is_dir():
                continue
            db = p / "database" / "autocommerce_x.db"
            videos = p / "assets" / "videos"
            score = 0
            if db.exists():
                score += 100
            if videos.exists():
                score += len(list(videos.glob("*")))
            candidates.append({
                "path": str(p),
                "db_exists": db.exists(),
                "video_count": len(list(videos.glob("*"))) if videos.exists() else 0,
                "score": score,
            })
        return sorted(candidates, key=lambda x: x["score"], reverse=True)
