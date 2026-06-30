import json
from datetime import datetime
from pathlib import Path
import re
from urllib.parse import quote_plus

from modules.studio.shorts_studio_engine import ShortsStudioEngine
from modules.studio.coupang_metadata_extractor import CoupangMetadataExtractor
from modules.studio.video_basic_analyzer import VideoBasicAnalyzer
from modules.studio.llm_content_generator import LLMContentGenerator
from modules.studio.video_sourcing_engine import VideoSourcingEngine
from modules.workflow.workflow_engine import WorkflowEngine
from modules.project.repository import ProjectRepository
from config.settings import EXPORTS_DIR


class StudioPipelineEngine:
    """Shorts Studio full pipeline.

    v3.9 adds a video source finder for Taobao/1688/Douyin candidates.
    It creates ranked video-source candidates and a manifest folder so the Shorts Studio can move toward
    Coupang link -> source video -> shopping shorts automation.
    """

    def __init__(self):
        self.out_dir = EXPORTS_DIR / "studio_pipeline"
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def run(self, coupang_url, product_name, uploaded_video=None, price="", category="", image_url="", partner_url="", run_one_click=True, sample_count=6):
        package = ShortsStudioEngine().build_package(
            coupang_url=coupang_url,
            product_name=product_name,
            uploaded_video=uploaded_video,
            price=price,
            category=category,
            image_url=image_url,
            partner_url=partner_url,
            sample_count=sample_count,
        )
        if not package.get("ok"):
            return package

        package = self.enrich_package(package, coupang_url, product_name, price, category, image_url, partner_url, sample_count)

        project_id = package.get("project", {}).get("id")
        pipeline = None
        if run_one_click and project_id:
            project = ProjectRepository().get(project_id)
            if project:
                try:
                    pipeline = WorkflowEngine().run_project(project, sample_count=sample_count)
                except Exception as e:
                    pipeline = {"ok": False, "error": str(e), "message": "원클릭 파이프라인 실행 중 오류가 발생했습니다. 쇼츠 패키지는 정상 생성되었습니다."}

        final = {
            "ok": True,
            "version": "3.9 Video Source Finder",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "package": package,
            "pipeline": pipeline,
            "next_actions": [
                "영상후보 탭에서 TOP 후보 URL 확인",
                "도우인/타오바오/1688 후보 영상 저장",
                "CapCut 편집안과 자막 복사",
                "유튜브 쇼츠 제목/설명 복사",
                "인스타 릴스 본문 복사",
                "성과 등록 후 AI 학습",
            ],
        }
        final["exports"] = self.save(final)
        return final

    def enrich_package(self, package, coupang_url, product_name, price, category, image_url, partner_url, sample_count):
        product = package.setdefault("product", {})
        project = package.setdefault("project", {})
        pname = product.get("name") or product_name or "쿠팡 추천상품"
        keyword = product.get("keyword") or self.comment_keyword(pname)
        product["keyword"] = keyword

        coupang = CoupangMetadataExtractor().extract(coupang_url, pname, price, category, image_url, partner_url, fetch=True)
        product["coupang"] = coupang
        if coupang.get("product_name") and (not product.get("name") or product.get("name") == product_name):
            product["name"] = coupang.get("product_name")
            pname = product["name"]
        if coupang.get("price"):
            product["price"] = coupang.get("price")
        if coupang.get("image_url"):
            product["image_url"] = coupang.get("image_url")
        if coupang.get("features"):
            product["features"] = coupang.get("features")

        video_path = project.get("video_path") or ""
        vision = VideoBasicAnalyzer().analyze(video_path, sample_count=sample_count)
        package["vision"] = vision

        product["search_urls"] = self.search_urls(product)
        product["taobao_top10"] = self.expand_top10(product.get("taobao_top10"), product.get("taobao_keyword") or pname, "taobao")
        product["douyin_top10"] = self.expand_top10(product.get("douyin_top10"), product.get("douyin_keyword") or pname, "douyin")

        package["video_sources"] = VideoSourcingEngine().collect(product)

        package["scripts"] = self.build_scripts(pname, keyword, product, vision)
        package["capcut"] = self.build_capcut_plan(pname, keyword, vision)
        package["thumbnail"] = self.build_thumbnail(pname, keyword, product)
        package["youtube"] = self.build_youtube(pname, keyword)
        package["instagram"] = self.build_instagram(pname, keyword)

        llm = LLMContentGenerator()
        ai_generated = llm.generate(product, vision, keyword)
        package["ai_generated"] = ai_generated
        package["ai_status"] = {
            "mode": ai_generated.get("provider", "offline-template"),
            "ready_for_api": True,
            "available": llm.status().get("available"),
            "message": ai_generated.get("message", ""),
            "note": "OPENAI_API_KEY 또는 GEMINI_API_KEY가 있으면 실제 AI 문구를 적용합니다. 없으면 기본 템플릿으로 안전하게 생성합니다.",
        }
        if ai_generated.get("ok"):
            self.apply_ai_generated(package, ai_generated, pname, keyword)
        return package


    def apply_ai_generated(self, package, ai, pname, keyword):
        """Merge real AI output into the normal package shape without breaking UI."""
        if isinstance(ai.get("scripts"), dict):
            package["scripts"] = ai["scripts"]
        if isinstance(ai.get("youtube"), dict):
            yt = package.setdefault("youtube", {})
            yt.update({k: v for k, v in ai["youtube"].items() if v})
            yt.setdefault("comment_cta", f"댓글에 '{keyword}' 남겨주세요 👇")
            if "쿠팡 파트너스" not in yt.get("description", ""):
                yt["description"] = (yt.get("description", "") + "\n\n🔗 제품 정보는 영상 아래 설명란 링크 또는 프로필 링크를 확인해주세요.\n이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.").strip()
        if isinstance(ai.get("instagram"), dict):
            ig = package.setdefault("instagram", {})
            ig.update({k: v for k, v in ai["instagram"].items() if v})
            if "쿠팡 파트너스" not in ig.get("caption", ""):
                ig["caption"] = (ig.get("caption", "") + "\n\n이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.").strip()
        if isinstance(ai.get("thumbnail"), dict):
            package.setdefault("thumbnail", {}).update({k: v for k, v in ai["thumbnail"].items() if v})
        if isinstance(ai.get("capcut_tips"), list):
            capcut = package.setdefault("capcut", {})
            timeline = capcut.setdefault("timeline", [])
            for idx, tip in enumerate(ai.get("capcut_tips", [])[:5], 1):
                timeline.append({"time": f"AI팁 {idx}", "edit": str(tip)})
        package["ai_applied"] = True

    def comment_keyword(self, name):
        words = re.findall(r"[가-힣A-Za-z0-9]+", name or "")
        stop = {"쿠팡", "추천", "상품", "세트", "개", "입", "무료배송"}
        for w in words:
            if len(w) >= 2 and w not in stop:
                return w[:8]
        return "정보"

    def expand_top10(self, current, base, kind):
        if current and len(current) >= 5:
            return current
        suffixes = ["사용법", "후기", "추천", "실사용", "비교", "꿀템", "정리", "살림템", "리뷰", "언박싱"]
        if kind == "taobao":
            suffixes = ["同款", "收纳", "家用", "神器", "厨房", "旅行", "便携", "批发", "实拍", "爆款"]
        rows = []
        for i, suf in enumerate(suffixes, 1):
            q = f"{base} {suf}".strip()
            rows.append({"rank": i, "query": q, "purpose": "원본/후킹 영상 후보 검색", "score": max(60, 96 - i * 3)})
        return rows

    def search_urls(self, product):
        taobao = product.get("taobao_keyword") or product.get("name") or ""
        douyin = product.get("douyin_keyword") or product.get("name") or ""
        coupang = product.get("coupang", {})
        return {
            "taobao_web": f"https://s.taobao.com/search?q={quote_plus(taobao)}" if taobao else "",
            "1688_web": f"https://s.1688.com/selloffer/offer_search.htm?keywords={quote_plus(taobao)}" if taobao else "",
            "douyin_web": f"https://www.douyin.com/search/{quote_plus(douyin)}" if douyin else "",
            "coupang_clean": coupang.get("clean_url", ""),
            "partner_url": coupang.get("partner_url", ""),
        }

    def build_scripts(self, pname, keyword, product, vision):
        hook = self.hook(pname)
        problem = self.problem_line(pname)
        use = self.use_line(pname)
        proof = "직접 쓰는 장면 위주로 보여주면 광고 느낌이 덜합니다."
        if vision.get("ok") and vision.get("duration_sec"):
            proof = f"원본 영상은 약 {vision.get('duration_sec')}초라 후킹컷을 앞쪽에 짧게 배치하세요."
        return {
            "15s": [
                {"time": "0~2초", "role": "후킹", "line": hook},
                {"time": "2~5초", "role": "공감", "line": problem},
                {"time": "5~10초", "role": "사용", "line": use},
                {"time": "10~13초", "role": "효과", "line": "작은 차이인데 생활이 훨씬 편해집니다."},
                {"time": "13~15초", "role": "CTA", "line": f"궁금하시면 댓글에 '{keyword}' 남겨주세요."},
            ],
            "25s": [
                {"time": "0~3초", "role": "후킹", "line": hook},
                {"time": "3~7초", "role": "문제", "line": problem},
                {"time": "7~14초", "role": "해결", "line": use},
                {"time": "14~20초", "role": "증거", "line": proof},
                {"time": "20~25초", "role": "CTA", "line": f"제품 정보는 댓글 '{keyword}' 확인해주세요."},
            ],
            "35s": [
                {"time": "0~3초", "role": "후킹", "line": hook},
                {"time": "3~8초", "role": "공감", "line": problem},
                {"time": "8~16초", "role": "사용 전", "line": "이전에는 꺼내고 정리하는 시간이 은근히 길었습니다."},
                {"time": "16~26초", "role": "사용 후", "line": use},
                {"time": "26~31초", "role": "정리", "line": "자주 쓰는 공간일수록 이런 작은 변화가 크게 느껴집니다."},
                {"time": "31~35초", "role": "CTA", "line": f"필요하시면 댓글에 '{keyword}' 남겨주세요."},
            ],
        }

    def hook(self, name):
        if "얼음" in name:
            return "얼죽아인데 얼음 빼는 게 귀찮다면 이거 보세요."
        if "신발" in name:
            return "장마철 신발 냄새, 그냥 두면 더 심해집니다."
        if "방충" in name or "모기" in name:
            return "문틈으로 벌레 들어온다면 여기부터 막아야 합니다."
        if "수전" in name or "세면" in name:
            return "세면대 쓸 때마다 불편했다면 이거 진짜 편합니다."
        return f"{name}, 왜 이제 알았지?"

    def problem_line(self, name):
        if "얼음" in name:
            return "얼음 얼리고, 빼고, 다시 채우는 게 매번 귀찮았어요."
        if "신발" in name:
            return "비 오고 나면 신발 속 습기와 냄새가 쉽게 안 빠집니다."
        if "방충" in name or "모기" in name:
            return "문을 닫아도 작은 틈으로 벌레가 들어올 때가 있습니다."
        return "저도 이거 때문에 매번 불편했어요."

    def use_line(self, name):
        if "얼음" in name:
            return "필요할 때 바로 꺼내 쓰기 쉬워서 홈카페가 편해집니다."
        if "신발" in name:
            return "안쪽까지 말려주면 다음 날 신기 훨씬 부담이 줄어듭니다."
        if "방충" in name or "모기" in name:
            return "틈에 맞춰 붙이면 벌레 들어오는 길을 줄일 수 있습니다."
        return f"{name}, 자주 쓰는 공간에 두면 훨씬 편합니다."

    def build_capcut_plan(self, pname, keyword, vision):

        timeline = [
            {"time": "0~2초", "edit": "가장 강한 사용 장면으로 시작 / Zoom In 105~115% / Pop 35%"},
            {"time": "2~5초", "edit": "불편한 Before 장면 / 자막 2줄 이하 / BGM 10~12%"},
            {"time": "5~10초", "edit": "제품 사용 과정 3컷 분할 / Click 40% / 손동작 강조"},
            {"time": "10~15초", "edit": "After 결과 컷 / Whoosh 30% / 밝기 살짝 보정"},
            {"time": "15~20초", "edit": f"CTA 고정 자막: 댓글에 '{keyword}' 남겨주세요 👇 / Bounce"},
        ]

        if vision.get("ratio") == "16:9/가로":
            timeline.insert(0, {"time": "편집 전", "edit": "가로 영상은 9:16 캔버스에 맞추고 중앙 크롭/배경 블러 적용"})

        return {
            "voice": "Typecast 지안 또는 일반 여성 내레이션 / 음성 18~20dB",
            "bgm": "CapCut 검색: 밝은 브이로그, fresh, daily / 볼륨 8~12%",
            "sfx": {"pop": "35%", "click": "40%", "whoosh": "30%"},
            "subtitle": {"position": "중앙 하단 / 하단 40%", "font": "기본 고딕 Bold", "stroke": "65", "shadow": "60%", "highlight": "#FFD54F", "max_lines": "2줄 이하"},
            "timeline": timeline,
            "draft_json": self.capcut_draft_json(pname, keyword, timeline),
        }

    def capcut_draft_json(self, pname, keyword, timeline):
        return {
            "project_name": f"{pname}_shopping_shorts",
            "canvas": "9:16",
            "fps": 30,
            "subtitle_safe_area": "bottom_40_percent",
            "cta": f"댓글에 '{keyword}' 남겨주세요 👇",
            "timeline": timeline,
        }

    def build_thumbnail(self, pname, keyword, product):
        return {
            "size": "9:16 영상용 / 인포크링크 1000x1000 별도 제작",
            "main_text": "왜 이제 알았지?" if len(pname) > 8 else f"{pname} 추천",
            "sub_text": "생활이 조금 쉬워지는 살림템",
            "composition": "제품 사용 장면 크게 + Before/After 작은 비교 + 노란 강조 자막",
            "copy_options": ["왜 이제 알았지?", "이거 하나로 편해짐", "아직도 불편하게 쓰세요?"],
        }

    def build_youtube(self, pname, keyword):
        return {
            "title": f"{pname} 써보면 왜 추천하는지 알게 됩니다 #shorts",
            "description": f"{pname} 사용 장면을 쇼츠로 정리했습니다.\n\n🔗 제품 정보는 영상 아래 설명란 링크 또는 프로필 링크를 확인해주세요.\n이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.",
            "hashtags": "#HA_CEN #하센 #쇼핑쇼츠 #생활용품추천 #살림템 #쿠팡추천 #쿠팡파트너스 #shorts",
            "comment_cta": f"댓글에 '{keyword}' 남겨주세요 👇",
        }

    def build_instagram(self, pname, keyword):
        return {
            "caption": f"{pname}\n\n작은 차이인데 생활이 조금 편해지는 아이템이에요.\n저장해두고 필요할 때 확인해보세요.\n\n팔로우 하시고, 댓글에 '{keyword}' 남겨주세요 👇\n제품 정보는 프로필 링크에서 확인해주세요.\n\n이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.",
            "hashtags": "#HA_CEN #하센맘 #쇼핑릴스 #생활용품추천 #주방용품추천 #살림템 #쿠팡파트너스",
        }

    def save(self, final):
        product_name = final.get("package", {}).get("product", {}).get("name", "studio_pipeline")
        safe = self.safe_name(product_name)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = self.out_dir / f"{safe}_{stamp}"
        json_path = base.with_suffix(".json")
        txt_path = base.with_suffix(".txt")
        md_path = base.with_suffix(".md")
        capcut_path = base.with_name(base.name + "_capcut_draft.json")
        json_path.write_text(json.dumps(final, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        txt_path.write_text(self.to_text(final), encoding="utf-8")
        md_path.write_text(self.to_markdown(final), encoding="utf-8")
        capcut_path.write_text(json.dumps(final.get("package", {}).get("capcut", {}).get("draft_json", {}), ensure_ascii=False, indent=2), encoding="utf-8")
        return {"folder": str(self.out_dir), "json": str(json_path), "txt": str(txt_path), "md": str(md_path), "capcut_draft": str(capcut_path)}

    def safe_name(self, text):
        text = re.sub(r"[^\w가-힣\s-]", "", str(text))
        text = re.sub(r"\s+", "_", text).strip("_")
        return text[:48] or "studio_pipeline"

    def to_text(self, final):
        package = final.get("package", {})
        product = package.get("product", {})
        lines = ["[Studio Pipeline 결과]", f"상품명: {product.get('name')}", f"댓글 키워드: {product.get('keyword')}", f"타오바오: {product.get('taobao_keyword')}", f"도우인: {product.get('douyin_keyword')}", "", "[검색 URL]"]
        for k, v in product.get("search_urls", {}).items():
            lines.append(f"{k}: {v}")
        lines += ["", "[영상 후보 TOP5]"]
        for item in package.get("video_sources", {}).get("best_candidates", []):
            lines.append(f"{item.get('rank')}. {item.get('platform')} / {item.get('title')} / {item.get('score')} / {item.get('search_url')}")
        lines += ["", "[Vision]", json.dumps(package.get("vision", {}), ensure_ascii=False, indent=2, default=str), "", "[15초 대본]"]
        for item in package.get("scripts", {}).get("15s", []):
            lines.append(f"{item.get('time')} / {item.get('role')} : {item.get('line')}")
        lines += ["", "[35초 대본]"]
        for item in package.get("scripts", {}).get("35s", []):
            lines.append(f"{item.get('time')} / {item.get('role')} : {item.get('line')}")
        lines += ["", "[CapCut]"]
        for item in package.get("capcut", {}).get("timeline", []):
            lines.append(f"{item.get('time')} : {item.get('edit')}")
        lines += ["", "[원클릭 파이프라인]", json.dumps(final.get("pipeline"), ensure_ascii=False, indent=2, default=str) if final.get("pipeline") else "실행 안 함"]
        return "\n".join(lines)

    def to_markdown(self, final):
        package = final.get("package", {})
        product = package.get("product", {})
        lines = ["# Studio Pipeline 결과", "", "## 상품", f"- 상품명: {product.get('name')}", f"- 댓글 키워드: {product.get('keyword')}", f"- 타오바오: `{product.get('taobao_keyword')}`", f"- 도우인: `{product.get('douyin_keyword')}`", "", "## 검색 URL"]
        for k, v in product.get("search_urls", {}).items():
            lines.append(f"- {k}: {v}")
        lines += ["", "## 영상 후보 TOP5"]
        for item in package.get("video_sources", {}).get("best_candidates", []):
            lines.append(f"- **{item.get('rank')}. {item.get('platform')}** {item.get('title')} / {item.get('score')}점: {item.get('search_url')}")
        lines += ["", "## Vision", f"- {package.get('vision', {}).get('summary', '')}", "", "## 15초 대본"]
        for item in package.get("scripts", {}).get("15s", []):
            lines.append(f"- **{item.get('time')} / {item.get('role')}**: {item.get('line')}")
        lines += ["", "## 35초 대본"]
        for item in package.get("scripts", {}).get("35s", []):
            lines.append(f"- **{item.get('time')} / {item.get('role')}**: {item.get('line')}")
        lines += ["", "## CapCut 편집안"]
        for item in package.get("capcut", {}).get("timeline", []):
            lines.append(f"- **{item.get('time')}**: {item.get('edit')}")
        yt = package.get("youtube", {})
        ig = package.get("instagram", {})
        lines += ["", "## 유튜브 쇼츠", f"- 제목: {yt.get('title')}", f"- 설명:\n\n{yt.get('description')}", "", "## 인스타 릴스", f"- 본문:\n\n{ig.get('caption')}", "", "## 원클릭 파이프라인", "```json", json.dumps(final.get("pipeline"), ensure_ascii=False, indent=2, default=str) if final.get("pipeline") else "실행 안 함", "```"]
        return "\n".join(lines)
