from modules.product.product_engine import ProductEngine
from modules.project.service import ProjectService
from modules.video.service import VideoService
from modules.project.repository import ProjectRepository


class ProjectRecovery:
    """
    예전 DB가 없어도 쿠팡 링크/상품명/영상으로 프로젝트를 빠르게 다시 만드는 복구 도구.
    """

    def rebuild(self, coupang_url, product_name, uploaded_video=None, price="", category="", image_url="", partner_url=""):
        if not coupang_url.strip():
            return {"ok": False, "message": "쿠팡 링크가 필요합니다."}
        if not product_name.strip():
            return {"ok": False, "message": "상품명을 입력해야 검색어 품질이 좋아집니다."}

        built = ProductEngine().build_from_coupang(
            coupang_url,
            product_name=product_name,
            manual_product_name=product_name,
            price=price,
            category=category,
            image_url=image_url,
            partner_url=partner_url,
        )

        payload = built["project_payload"]

        if uploaded_video:
            payload["video_path"] = VideoService().save_uploaded_video(uploaded_video)
        else:
            payload["video_path"] = ""

        existing = None
        try:
            existing = ProjectRepository().find_by_coupang_url(payload.get("coupang_url", ""))
        except Exception:
            existing = None

        if existing:
            return {
                "ok": True,
                "message": f"이미 같은 쿠팡 링크 프로젝트가 있습니다: {existing.product_name}",
                "project_id": existing.id,
                "project_name": existing.product_name,
                "built": built,
                "existing": True,
            }

        project = ProjectService().create_project(payload)
        return {
            "ok": True,
            "message": f"프로젝트 복구/생성 완료: {project.product_name}",
            "project_id": project.id,
            "project_name": project.product_name,
            "video_path": payload.get("video_path", ""),
            "built": built,
            "existing": False,
        }
