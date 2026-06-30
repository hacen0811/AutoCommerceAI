from modules.ai.shopping_shorts_engine import ShoppingShortsEngine


class ContentFactory:
    def build(self, project, smart=None, vision=None):
        product_name = getattr(project, "product_name", "추천상품")
        keyword = getattr(project, "keyword", "정보")

        package = ShoppingShortsEngine().generate(
            product_name=product_name,
            keyword=keyword,
            video_intel=smart or {},
            ocr_result=vision or {},
        )

        return {
            "shorts": package,
            "blog": self.blog(product_name, keyword),
            "inpock": self.inpock(product_name, keyword, getattr(project, "partner_url", "")),
            "upload_bundle": self.upload_bundle(product_name, keyword, package),
        }

    def blog(self, product_name, keyword):
        return {
            "title": f"{product_name} 사용 전후 차이, 왜 많이 찾을까요?",
            "body": "\n".join([
                f"{product_name}은 생활 속 불편함을 줄여주는 제품입니다.",
                "",
                "이런 분께 추천합니다.",
                "- 매번 같은 불편함을 겪는 분",
                "- 간단한 생활용품으로 시간을 줄이고 싶은 분",
                "- 쇼핑 전 핵심 포인트를 빠르게 확인하고 싶은 분",
                "",
                f"자세한 제품 정보는 링크를 확인해주세요. 댓글에 '{keyword}' 남겨주시면 관련 정보를 정리해드릴게요.",
            ]),
        }

    def inpock(self, product_name, keyword, partner_url):
        return {
            "title": product_name,
            "description": f"생활이 조금 쉬워지는 {product_name}\n댓글에 '{keyword}' 남겨주세요 👇",
            "button": "제품 보러가기",
            "link": partner_url or "쿠팡파트너스 링크를 입력하세요.",
        }

    def upload_bundle(self, product_name, keyword, package):
        copy = package.get("platform_copy", {})
        return {
            "youtube_title": copy.get("유튜브 제목", f"{product_name}, 왜 이제 알았을까요?"),
            "youtube_desc": copy.get("유튜브 설명", ""),
            "instagram_body": copy.get("인스타 본문", ""),
            "fixed_comment": f"댓글에 '{keyword}' 남겨주세요 👇",
            "partner_notice": "※ 쿠팡파트너스 활동의 일환으로 일정액의 수수료를 받을 수 있습니다.",
        }
