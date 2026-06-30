from modules.project.repository import ProjectRepository
from modules.ai.content_engine import AIContentEngine
from modules.capcut.guide_engine import CapCutGuideEngine
from modules.video.analyzer import VideoAnalyzer


class ProjectService:
    def create_project(self, payload):
        product_name = payload.get("product_name", "새 상품")
        keyword = payload.get("keyword", "정보")
        ai_data = AIContentEngine().generate(product_name, keyword)
        capcut = CapCutGuideEngine().generate(payload)

        payload["title"] = product_name
        payload["score"] = ai_data.get("score", 80)
        payload["data"] = {
            "ai": ai_data,
            "capcut": capcut,
            "video_analysis": VideoAnalyzer().analyze(payload.get("video_path", "")),
            "inpock": {
                "title": product_name,
                "description": f"생활이 조금 쉬워지는 {product_name}\n댓글에 '{keyword}' 남겨주세요 👇",
                "button": "제품 보러가기",
                "link": payload.get("partner_url", ""),
            },
        }
        return ProjectRepository().create(payload)
