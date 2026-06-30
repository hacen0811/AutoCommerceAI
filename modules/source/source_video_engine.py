import json
import shutil
from pathlib import Path
from urllib.parse import urlparse


class SourceVideoEngine:
    """
    Douyin/Taobao 원본 영상 관리 엔진.
    자동 다운로드는 각 서비스 약관/저작권 이슈가 있어 기본값은 '수동 확보 영상 관리'입니다.
    사용자가 직접 확보한 영상 파일을 프로젝트별 라이브러리에 저장하고, 분석 후보로 랭킹합니다.
    """

    SUPPORTED = {"douyin", "taobao", "1688", "local", "coupang"}

    def project_dir(self, project_name):
        safe = "".join(c for c in str(project_name or "project") if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        if not safe:
            safe = "project"
        path = Path("assets/source_videos") / safe
        path.mkdir(parents=True, exist_ok=True)
        return path

    def detect_platform(self, url):
        host = urlparse(url or "").netloc.lower()
        if "douyin" in host:
            return "douyin"
        if "taobao" in host or "tmall" in host:
            return "taobao"
        if "1688" in host:
            return "1688"
        if "coupang" in host:
            return "coupang"
        return "local"

    def make_search_plan(self, project, product_plan=None):
        product_name = getattr(project, "product_name", "") if project else ""
        keyword = getattr(project, "keyword", "정보") if project else "정보"

        keywords = {}
        if product_plan:
            keywords = product_plan.get("keywords", {}) or {}

        taobao_query = keywords.get("taobao_keyword") or product_name
        douyin_query = keywords.get("douyin_keyword") or f"{product_name} 使用 效果"
        korean_query = keywords.get("korean_search") or product_name

        return {
            "product_name": product_name,
            "keyword": keyword,
            "search_queries": {
                "taobao": taobao_query,
                "douyin": douyin_query,
                "korean": korean_query,
            },
            "taobao_top10": keywords.get("taobao_top10", []),
            "douyin_top10": keywords.get("douyin_top10", []),
            "collection_checklist": [
                "타오바오/도우인에서 직접 사용 가능한 원본 영상 후보 확보",
                "워터마크/중국어 자막이 적은 영상 우선",
                "상품 사용 장면이 5초 이상 선명한 영상 우선",
                "가로 영상보다 세로 영상 우선",
                "다운로드한 파일을 Source Video AI에 업로드",
            ],
            "legal_note": "영상은 저작권과 플랫폼 이용약관을 확인하고 사용 권한이 있는 파일만 등록하세요.",
        }

    def register_source_url(self, project, url, memo=""):
        platform = self.detect_platform(url)
        path = self.project_dir(getattr(project, "product_name", "project"))
        registry_path = path / "source_urls.json"

        if registry_path.exists():
            data = json.loads(registry_path.read_text(encoding="utf-8"))
        else:
            data = []

        item = {
            "platform": platform,
            "url": url,
            "memo": memo,
            "status": "registered",
        }
        data.append(item)
        registry_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return item

    def save_uploaded_video(self, project, uploaded_file, platform="local", memo=""):
        path = self.project_dir(getattr(project, "product_name", "project"))
        platform = platform if platform in self.SUPPORTED else "local"

        original_name = getattr(uploaded_file, "name", "source_video.mp4")
        target = path / f"{platform}_{len(list(path.glob(platform + '_*'))) + 1}_{original_name}"

        with open(target, "wb") as f:
            shutil.copyfileobj(uploaded_file, f)

        meta = self._load_meta(path)
        meta.append({
            "filename": target.name,
            "path": str(target),
            "platform": platform,
            "memo": memo,
            "status": "uploaded",
        })
        self._save_meta(path, meta)
        return str(target)

    def list_project_videos(self, project):
        path = self.project_dir(getattr(project, "product_name", "project"))
        meta = self._load_meta(path)
        existing = []
        for item in meta:
            if Path(item.get("path", "")).exists():
                existing.append(item)
        return existing

    def _load_meta(self, path):
        meta_path = path / "source_videos.json"
        if meta_path.exists():
            try:
                return json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def _save_meta(self, path, data):
        (path / "source_videos.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
