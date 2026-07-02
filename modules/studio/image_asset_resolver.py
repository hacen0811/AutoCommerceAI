from __future__ import annotations

import re
import shutil
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict

try:
    from config.settings import EXPORTS_DIR
except Exception:
    EXPORTS_DIR = Path("exports")


class ImageAssetResolver:
    """Resolve a product image URL/path into a local file for Playwright upload."""

    def __init__(self):
        self.out_dir = EXPORTS_DIR / "studio_image_search_assets"
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def resolve(self, image_url: str = "", image_path: str = "", name: str = "product") -> Dict:
        image_url = (image_url or "").strip()
        image_path = (image_path or "").strip()

        if image_path:
            src = Path(image_path)
            if src.exists() and src.is_file():
                local = self.out_dir / self._filename(name, src.suffix or ".jpg")
                shutil.copy2(src, local)
                return {
                    "ok": True,
                    "source": "local_path",
                    "image_url": image_url,
                    "image_path": str(local),
                    "message": "로컬 제품 이미지를 검색용 파일로 준비했습니다.",
                }

        if image_url:
            suffix = self._suffix_from_url(image_url)
            local = self.out_dir / self._filename(name, suffix)
            try:
                req = urllib.request.Request(
                    image_url,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
                        )
                    },
                )
                with urllib.request.urlopen(req, timeout=20) as r:
                    data = r.read()
                if data:
                    local.write_bytes(data)
                    return {
                        "ok": True,
                        "source": "image_url",
                        "image_url": image_url,
                        "image_path": str(local),
                        "message": "제품 이미지를 다운로드해 검색용 파일로 준비했습니다.",
                    }
            except Exception as exc:
                return {
                    "ok": False,
                    "source": "image_url",
                    "image_url": image_url,
                    "image_path": "",
                    "message": f"제품 이미지 다운로드 실패: {exc}",
                }

        return {
            "ok": False,
            "source": "none",
            "image_url": image_url,
            "image_path": "",
            "message": "제품 이미지가 없어 이미지 검색을 건너뜁니다.",
        }

    def _filename(self, name: str, suffix: str) -> str:
        safe = re.sub(r"[^\w가-힣\s-]", "", str(name or "product"))
        safe = re.sub(r"\s+", "_", safe).strip("_")[:40] or "product"
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not suffix.startswith("."):
            suffix = "." + suffix
        return f"{safe}_{ts}{suffix}"

    def _suffix_from_url(self, url: str) -> str:
        m = re.search(r"\.(jpg|jpeg|png|webp)(?:\?|$)", url, re.I)
        if m:
            return "." + m.group(1).lower().replace("jpeg", "jpg")
        return ".jpg"
