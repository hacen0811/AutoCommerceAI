from modules.system.project_recovery import ProjectRecovery
from modules.studio.shorts_package_exporter import ShortsPackageExporter


class ShortsStudioEngine:
    def build_package(self, coupang_url, product_name, uploaded_video=None, price="", category="", image_url="", partner_url="", platform="both"):
        recovered = ProjectRecovery().rebuild(
            coupang_url=coupang_url,
            product_name=product_name,
            uploaded_video=uploaded_video,
            price=price,
            category=category,
            image_url=image_url,
            partner_url=partner_url,
        )
        if not recovered.get("ok"):
            return recovered

        built = recovered.get("built", {})
        payload = built.get("project_payload", {})
        keywords = built.get("keywords", {})
        pname = payload.get("product_name", product_name)
        keyword = payload.get("keyword", "정보")

        package = {
            "ok": True,
            "project": {
                "id": recovered.get("project_id"),
                "name": recovered.get("project_name"),
                "video_path": recovered.get("video_path", ""),
                "existing": recovered.get("existing", False),
            },
            "product": {
                "name": pname,
                "keyword": keyword,
                "content_angle": keywords.get("content_angle", ""),
                "taobao_keyword": keywords.get("taobao_keyword", ""),
                "douyin_keyword": keywords.get("douyin_keyword", ""),
                "taobao_top10": keywords.get("taobao_top10", []),
                "douyin_top10": keywords.get("douyin_top10", []),
            },
            "scripts": self.scripts(pname, keyword, keywords),
            "capcut": self.capcut_plan(pname, keyword),
            "thumbnail": self.thumbnail(pname),
            "youtube": self.youtube(pname, keyword),
            "instagram": self.instagram(pname, keyword),
            "inpock": self.inpock(pname),
            "workflow_checklist": self.workflow_checklist(),
            "next_step": "⚡ 원클릭 파이프라인에서 생성된 프로젝트를 선택해 실행하세요.",
        }
        package["exports"] = ShortsPackageExporter().save(package)
        return package

    def workflow_checklist(self):
        return [
            "타오바오/도우인 TOP10 중 1~3번 검색어로 원본 영상 찾기",
            "원본 영상을 영상관리 또는 쇼츠 스튜디오에서 업로드",
            "원클릭 파이프라인 실행",
            "CapCut 편집안 확인",
            "유튜브 쇼츠/인스타 릴스 문구 복사",
        ]

    def scripts(self, product_name, keyword, keywords):
        angle = keywords.get("content_angle") or "생활 불편 해결형"
        return {
            "15s": [
                {"time": "0~2초", "role": "후킹", "line": self.hook(product_name, angle)},
                {"time": "2~5초", "role": "공감", "line": "저도 이거 때문에 매번 불편했어요."},
                {"time": "5~10초", "role": "사용", "line": f"{product_name}, 이렇게 쓰면 훨씬 편합니다."},
                {"time": "10~13초", "role": "효과", "line": "작지만 정리되는 느낌이 확 달라져요."},
                {"time": "13~15초", "role": "CTA", "line": f"궁금하시면 댓글에 '{keyword}' 남겨주세요."},
            ],
            "25s": [
                {"time": "0~3초", "role": "후킹", "line": self.hook(product_name, angle)},
                {"time": "3~7초", "role": "문제", "line": "쓰기 전에는 자꾸 찾고, 꺼내고, 다시 정리해야 했습니다."},
                {"time": "7~14초", "role": "해결", "line": f"{product_name}은 자주 쓰는 물건을 한곳에 모아줍니다."},
                {"time": "14~20초", "role": "사용감", "line": "설치도 복잡하지 않고, 자주 쓰는 공간이 깔끔해집니다."},
                {"time": "20~25초", "role": "CTA", "line": f"제품 정보는 댓글 '{keyword}' 확인해주세요."},
            ],
        }

    def hook(self, product_name, angle):
        if "주방" in product_name or "정리" in product_name:
            return "주방이 좁다면 이거 하나로 정리가 쉬워집니다."
        if "방충" in product_name:
            return "문틈으로 들어오는 벌레, 이렇게 막아보세요."
        if "신발" in product_name:
            return "장마철 신발 냄새, 그냥 두지 마세요."
        return f"{product_name}, 왜 이제 알았을까요?"

    def capcut_plan(self, product_name, keyword):
        return {
            "voice": "AI 음성 20 dB",
            "bgm": "BGM 8 dB",
            "sfx": {"pop": "7 dB", "click": "8 dB", "whoosh": "6 dB"},
            "subtitle": {"position": "중앙 하단 / 하단 40%", "stroke": "65", "shadow": "60%", "max_lines": "2줄 이하"},
            "timeline": [
                {"time": "0~2초", "edit": "Zoom In 105~115% / Pop 7 dB / 후킹 자막"},
                {"time": "2~5초", "edit": "문제 장면 짧게 컷 / BGM 8 dB"},
                {"time": "5~10초", "edit": "사용 장면 / Click 8 dB / 손동작 강조"},
                {"time": "10~15초", "edit": "Before After / Whoosh 6 dB"},
                {"time": "15~20초", "edit": f"CTA / 댓글 '{keyword}' / Bounce"},
            ],
        }

    def thumbnail(self, product_name):
        return {
            "size": "9:16 영상용 / 인포크 1000x1000 별도",
            "main_text": "주방 정리, 이거 하나면 끝" if "주방" in product_name or "정리" in product_name else "왜 이제 알았지?",
            "sub_text": "생활이 조금 쉬워지는 살림템",
            "composition": "제품 사용 장면 + Before/After 느낌 + 큰 글씨 6~10자",
        }

    def youtube(self, product_name, keyword):
        return {
            "title": f"{product_name} 써보면 왜 추천하는지 알게 됩니다 #shorts",
            "description": f"{product_name} 사용 장면을 쇼츠로 정리했습니다.\n\n🔗 제품 정보는 영상 아래 설명란 링크 또는 프로필 링크를 확인해주세요.\n이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.",
            "hashtags": "#쇼핑쇼츠 #살림템 #생활용품추천 #쿠팡추천 #shorts",
            "comment_cta": f"댓글에 '{keyword}' 남겨주세요 👇",
        }

    def instagram(self, product_name, keyword):
        return {
            "caption": f"{product_name}\n작은 차이인데 생활이 조금 편해지는 아이템이에요.\n\n팔로우 하시고, 댓글에 '{keyword}' 남겨주세요 👇\n제품 정보는 프로필 링크에서 확인해주세요.",
            "hashtags": "#살림템 #생활용품추천 #주방용품추천 #쇼핑릴스 #쿠팡파트너스",
        }

    def inpock(self, product_name):
        return {"title": product_name[:28], "description": f"생활이 조금 쉬워지는 {product_name}", "button": "제품 보러가기", "image_size": "1000x1000"}
