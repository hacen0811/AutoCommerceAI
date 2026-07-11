
하센님, 현재 실제 파일에 먼저 고쳐야 할 오류가 보입니다.

class ContentFactory:
        CONTENT_PACK_DIR.mkdir(parents=True, exist_ok=True)
여기에는 __init__() 함수가 빠져 있습니다. 이 상태면 실행 시 오류가 납니다.

아래처럼 수정해 주세요.

class ContentFactory:
    def __init__(self):
        CONTENT_PACK_DIR.mkdir(parents=True, exist_ok=True)
그리고 VideoComposer 연결 방식은 반환 구조를 먼저 확인해야 안전합니다. 아래 명령을 실행해 주세요.

Get-Content .\modules\video\video_composer.py
결과를 붙여 주시면 다음 단계에서:

from modules.video.video_composer import VideoComposer
와 pack["cut_plan"] 아래의 정확한 연결 코드를 현재 구조에 맞춰 넣겠습니다.


class ContentFactory:
    def __init__(self):
        CONTENT_PACK_DIR.mkdir(parents=True, exist_ok=True):
    """
    Sprint 51 ContentFactory

하센님, 마지막 줄 끝의 :가 하나 더 들어갔습니다. 아래처럼 바꿔주세요.

class ContentFactory:
    def __init__(self):
        CONTENT_PACK_DIR.mkdir(parents=True, exist_ok=True)

    """
    Sprint 51 ContentFactory
다만 클래스 설명 문자열은 __init__()보다 위에 두는 게 맞습니다. 가장 안전한 형태는 아래입니다.

class ContentFactory:
    """
    Sprint 51 ContentFactory
    """

    def __init__(self):
        CONTENT_PACK_DIR.mkdir(parents=True, exist_ok=True)
이 형태로 수정한 뒤 저장해 주세요.



Pasted code(64).py
Python
전체해줘

하센님, content_factory.py 전체 교체본입니다.
중복된 __init__, 잘못 열린 설명문, VideoComposer, CapCutProjectBuilder 연결까지 정리했습니다. 기존 파일에는 클래스 내부 설명문이 코드로 들어가 문법 오류가 발생하는 구조였습니다. 


content_factory.py

기존 파일을 아래 경로에서 통째로 교체해 주세요.

modules\content\content_factory.py
교체 후 문법 검사를 실행합니다.

python -m py_compile .\modules\content\content_factory.py
오류가 없으면 앱을 실행해 주세요.

python -m streamlit run main.py
이번 전체본에는 다음 흐름이 들어 있습니다.

AI 콘텐츠 팩
→ Edit Assistant
→ CutPlanner
→ VideoComposer
→ CapCut Export
→ CapCut Draft
→ CapCut Project 저장
VideoComposer 결과는 아래 키로 저장됩니다.

pack["video_composer"]
그리고 별도 JSON 파일도 생성됩니다.

exports\content_packs\프로젝트ID_video_composer_날짜시간.json



라이브러리
/
content_factory.py


import json
from pathlib import Path
from datetime import datetime

from modules.ai.shopping_shorts_engine import ShoppingShortsEngine
from modules.video.cut_planner import CutPlanner
from modules.video.video_composer import VideoComposer
from modules.capcut.export_builder import CapCutExportBuilder
from modules.video.capcut_draft_builder import CapCutDraftBuilder
from modules.capcut.project_builder import CapCutProjectBuilder


CONTENT_PACK_DIR = Path("exports/content_packs")


class ContentFactory:
    """
    Sprint 51 ContentFactory

    흐름:
    후보 채택
      -> AI 콘텐츠 팩 생성
      -> Edit Assistant
      -> CutPlanner
      -> VideoComposer
      -> CapCut Export
      -> CapCut Draft
      -> CapCut Project
      -> 저장
    """

    def __init__(self):
        CONTENT_PACK_DIR.mkdir(parents=True, exist_ok=True)

    def build(self, project, selected_candidates=None, smart=None, vision=None):
        selected_candidates = selected_candidates or []

        product_name = self._get_project_value(
            project,
            ["product_name", "title", "name"],
            "추천상품",
        )

        keyword = self._get_project_value(
            project,
            ["keyword", "main_keyword", "search_keyword"],
            product_name,
        )

        partner_url = self._get_project_value(
            project,
            ["partner_url", "coupang_partner_url"],
            "",
        )

        package = ShoppingShortsEngine().generate(
            product_name=product_name,
            keyword=keyword,
            video_intel=smart or {},
            ocr_result=vision or {},
        )

        pack = {
            "version": "sprint51-content-pack-1.0",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "summary": self.summary(
                project,
                product_name,
                keyword,
                selected_candidates,
            ),
            "selected_sources": selected_candidates,
            "shorts": package,
            "scripts": self.scripts(product_name, keyword, package),
            "captions": self.captions(product_name, keyword, package),
            "thumbnail": self.thumbnail(product_name, keyword, package),
            "blog": self.blog(product_name, keyword),
            "inpock": self.inpock(product_name, keyword, partner_url),
            "upload_bundle": self.upload_bundle(
                product_name,
                keyword,
                package,
            ),
        }

        pack = self.apply_edit_assistant(pack)

        pack["cut_plan"] = CutPlanner().build(pack)

        composer_result = VideoComposer().compose(pack)
        pack["video_composer"] = (
            composer_result
            if isinstance(composer_result, dict)
            else {
                "status": "completed",
                "result": composer_result,
            }
        )

        pack["capcut_export"] = CapCutExportBuilder().build(pack)

        pack["capcut_draft"] = CapCutDraftBuilder().build(
            pack.get("capcut_export", {})
        )

        return pack

    def summary(self, project, product_name, keyword, selected_candidates):
        return {
            "product_name": product_name,
            "keyword": keyword,
            "candidate_count": len(selected_candidates),
            "project_id": self._get_project_value(
                project,
                ["id", "project_id"],
                "",
            ),
            "project_name": self._get_project_value(
                project,
                ["project_name", "name", "title"],
                product_name,
            ),
        }

    def scripts(self, product_name, keyword, package):
        scripts = (
            package.get("scripts")
            or package.get("shorts_scripts")
            or {}
        )

        return {
            "main": scripts.get("main") or package.get("script") or "",
            "hook": (
                scripts.get("hook")
                or package.get("hook")
                or f"{product_name}, 왜 이제 알았을까요?"
            ),
            "cta": (
                scripts.get("cta")
                or f"댓글에 '{keyword}' 남겨주세요 👇"
            ),
            "raw": scripts,
        }

    def captions(self, product_name, keyword, package):
        captions = (
            package.get("captions")
            or package.get("subtitle")
            or []
        )

        if isinstance(captions, str):
            captions = [captions]

        if not captions:
            captions = [
                f"{product_name}, 왜 이제 알았을까요?",
                "생활 속 불편함을 줄여주는 추천템입니다.",
                f"댓글에 '{keyword}' 남겨주세요 👇",
            ]

        return {
            "items": captions,
            "safe_area": "하단 40~50%",
            "font": "Noto Serif KR Bold",
            "max_lines": 2,
        }

    def thumbnail(self, product_name, keyword, package):
        return {
            "size": "9:16",
            "main_text": package.get("hook") or "왜 이제 알았지?",
            "sub_text": product_name,
            "layout": (
                "제품 크게 + 왼쪽 상단 후킹 문구 "
                "+ 하단 짧은 설명"
            ),
            "image_prompt": (
                "9:16 vertical shopping shorts thumbnail, "
                "clean Korean ecommerce style, "
                f"product concept: {product_name}, "
                f"keyword: {keyword}, "
                "bright home background, "
                "large bold Korean text area, "
                "realistic product-focused composition"
            ),
        }

    def blog(self, product_name, keyword):
        return {
            "title": (
                f"{product_name} 사용 전후 차이, "
                "왜 많이 찾을까요?"
            ),
            "body": "\n".join(
                [
                    (
                        f"{product_name}은 생활 속 불편함을 "
                        "줄여주는 제품입니다."
                    ),
                    "",
                    "이런 분께 추천합니다.",
                    "- 매번 같은 불편함을 겪는 분",
                    "- 간단한 생활용품으로 시간을 줄이고 싶은 분",
                    "- 쇼핑 전 핵심 포인트를 빠르게 확인하고 싶은 분",
                    "",
                    (
                        "자세한 제품 정보는 링크를 확인해주세요. "
                        f"댓글에 '{keyword}' 남겨주시면 "
                        "관련 정보를 정리해드릴게요."
                    ),
                ]
            ),
        }

    def inpock(self, product_name, keyword, partner_url):
        return {
            "size": "1000x1000",
            "title": product_name,
            "description": (
                f"생활이 조금 쉬워지는 {product_name}\n"
                f"댓글에 '{keyword}' 남겨주세요 👇"
            ),
            "button": "제품 보러가기",
            "link": (
                partner_url
                or "쿠팡파트너스 링크를 입력하세요."
            ),
            "image_prompt": (
                "1000x1000 square product promo image "
                "for Inpock link page, "
                "clean Korean shopping design, "
                f"product concept: {product_name}, "
                "white background, neat layout, "
                "space for Korean title text"
            ),
        }

    def upload_bundle(self, product_name, keyword, package):
        copy = package.get("platform_copy", {})

        return {
            "youtube_title": copy.get(
                "유튜브 제목",
                f"{product_name}, 왜 이제 알았을까요?",
            ),
            "youtube_desc": copy.get("유튜브 설명", ""),
            "instagram_body": copy.get("인스타 본문", ""),
            "fixed_comment": (
                f"댓글에 '{keyword}' 남겨주세요 👇"
            ),
            "partner_notice": (
                "※ 쿠팡파트너스 활동의 일환으로 "
                "일정액의 수수료를 받을 수 있습니다."
            ),
        }

    def apply_edit_assistant(self, pack):
        selected_sources = pack.get("selected_sources", [])
        captions = pack.get("captions", {}).get("items", [])

        pack["edit_assistant"] = {
            "version": "sprint51-edit-assistant-1.0",
            "goal": (
                "채택된 후보 영상을 기반으로 "
                "쇼핑쇼츠 편집 방향을 제안합니다."
            ),
            "source_count": len(selected_sources),
            "recommended_flow": [
                "0~3초: 후킹 컷",
                "3~8초: 문제 상황",
                "8~15초: 제품 사용 장면",
                "15~22초: 장점 강조",
                "22초 이후: CTA",
            ],
            "caption_guide": {
                "font": "Noto Serif KR Bold",
                "position": "하단 40~50%",
                "max_lines": 2,
                "highlight_color": "#FFD54F",
            },
            "sound_guide": {
                "bgm": "밝고 가벼운 쇼핑/생활템 분위기",
                "sfx": ["Pop", "Click", "Whoosh"],
                "volume": {
                    "bgm": "12~18%",
                    "sfx": "25~40%",
                },
            },
            "caption_preview": captions[:5],
        }

        return pack

    def save_content_pack(self, project, pack):
        project_id = self._get_project_value(
            project,
            ["id", "project_id"],
            "project",
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        json_path = (
            CONTENT_PACK_DIR
            / f"{project_id}_content_pack_{timestamp}.json"
        )
        txt_path = (
            CONTENT_PACK_DIR
            / f"{project_id}_content_pack_{timestamp}.txt"
        )
        capcut_path = (
            CONTENT_PACK_DIR
            / f"{project_id}_capcut_export_{timestamp}.json"
        )
        draft_path = (
            CONTENT_PACK_DIR
            / f"{project_id}_capcut_draft_{timestamp}.json"
        )
        edit_guide_path = (
            CONTENT_PACK_DIR
            / f"{project_id}_edit_guide_{timestamp}.txt"
        )
        video_composer_path = (
            CONTENT_PACK_DIR
            / f"{project_id}_video_composer_{timestamp}.json"
        )

        self._write_json(json_path, pack)
        self._write_text(txt_path, self._pack_to_text(pack))
        self._write_json(
            capcut_path,
            pack.get("capcut_export", {}),
        )
        self._write_json(
            draft_path,
            pack.get("capcut_draft", {}),
        )
        self._write_json(
            video_composer_path,
            pack.get("video_composer", {}),
        )
        self._write_text(
            edit_guide_path,
            self._edit_guide_to_text(pack),
        )

        project_paths = {}

        if pack.get("capcut_draft"):
            project_paths = CapCutProjectBuilder().build(
                project,
                pack["capcut_draft"],
            )

        return {
            "json_path": str(json_path),
            "txt_path": str(txt_path),
            "capcut_path": str(capcut_path),
            "capcut_export_path": str(capcut_path),
            "draft_path": str(draft_path),
            "capcut_draft_path": str(draft_path),
            "edit_guide_path": str(edit_guide_path),
            "video_composer_path": str(video_composer_path),
            **project_paths,
        }

    def _pack_to_text(self, pack):
        lines = []

        summary = pack.get("summary", {})
        upload = pack.get("upload_bundle", {})
        scripts = pack.get("scripts", {})
        captions = pack.get("captions", {})

        lines.append("[AI 콘텐츠 팩]")
        lines.append(
            f"상품명: {summary.get('product_name', '')}"
        )
        lines.append(
            f"키워드: {summary.get('keyword', '')}"
        )
        lines.append("")

        lines.append("[후킹]")
        lines.append(str(scripts.get("hook", "")))
        lines.append("")

        lines.append("[대본]")
        lines.append(str(scripts.get("main", "")))
        lines.append("")

        lines.append("[자막]")
        for item in captions.get("items", []):
            lines.append(f"- {item}")
        lines.append("")

        lines.append("[업로드]")
        lines.append(
            f"유튜브 제목: {upload.get('youtube_title', '')}"
        )
        lines.append(
            f"유튜브 설명: {upload.get('youtube_desc', '')}"
        )
        lines.append(
            f"인스타 본문: {upload.get('instagram_body', '')}"
        )
        lines.append(
            f"고정 댓글: {upload.get('fixed_comment', '')}"
        )
        lines.append(upload.get("partner_notice", ""))

        return "\n".join(lines)

    def _edit_guide_to_text(self, pack):
        edit = pack.get("edit_assistant", {})
        lines = []

        lines.append("[Edit Assistant]")
        lines.append(edit.get("goal", ""))
        lines.append("")

        lines.append("[추천 흐름]")
        for item in edit.get("recommended_flow", []):
            lines.append(f"- {item}")
        lines.append("")

        lines.append("[자막 가이드]")
        for key, value in edit.get("caption_guide", {}).items():
            lines.append(f"- {key}: {value}")
        lines.append("")

        lines.append("[사운드 가이드]")
        for key, value in edit.get("sound_guide", {}).items():
            lines.append(f"- {key}: {value}")

        return "\n".join(lines)

    def _write_json(self, path, data):
        path.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

    def _write_text(self, path, text):
        path.write_text(
            text or "",
            encoding="utf-8",
        )

    def _get_project_value(self, project, names, default=""):
        for name in names:
            if isinstance(project, dict):
                value = project.get(name)
            else:
                value = getattr(project, name, None)

            if value:
                return value

        return default
라이브러리
/
content_factory.py


import json
from pathlib import Path
from datetime import datetime

from modules.ai.shopping_shorts_engine import ShoppingShortsEngine
from modules.video.cut_planner import CutPlanner
from modules.video.video_composer import VideoComposer
from modules.capcut.export_builder import CapCutExportBuilder
from modules.video.capcut_draft_builder import CapCutDraftBuilder
from modules.capcut.project_builder import CapCutProjectBuilder


CONTENT_PACK_DIR = Path("exports/content_packs")


class ContentFactory:
    """
    Sprint 51 ContentFactory

    흐름:
    후보 채택
      -> AI 콘텐츠 팩 생성
      -> Edit Assistant
      -> CutPlanner
      -> VideoComposer
      -> CapCut Export
      -> CapCut Draft
      -> CapCut Project
      -> 저장
    """

    def __init__(self):
        CONTENT_PACK_DIR.mkdir(parents=True, exist_ok=True)

    def build(self, project, selected_candidates=None, smart=None, vision=None):
        selected_candidates = selected_candidates or []

        product_name = self._get_project_value(
            project,
            ["product_name", "title", "name"],
            "추천상품",
        )

        keyword = self._get_project_value(
            project,
            ["keyword", "main_keyword", "search_keyword"],
            product_name,
        )

        partner_url = self._get_project_value(
            project,
            ["partner_url", "coupang_partner_url"],
            "",
        )

        package = ShoppingShortsEngine().generate(
            product_name=product_name,
            keyword=keyword,
            video_intel=smart or {},
            ocr_result=vision or {},
        )

        pack = {
            "version": "sprint51-content-pack-1.0",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "summary": self.summary(
                project,
                product_name,
                keyword,
                selected_candidates,
            ),
            "selected_sources": selected_candidates,
            "shorts": package,
            "scripts": self.scripts(product_name, keyword, package),
            "captions": self.captions(product_name, keyword, package),
            "thumbnail": self.thumbnail(product_name, keyword, package),
            "blog": self.blog(product_name, keyword),
            "inpock": self.inpock(product_name, keyword, partner_url),
            "upload_bundle": self.upload_bundle(
                product_name,
                keyword,
                package,
            ),
        }

        pack = self.apply_edit_assistant(pack)

        pack["cut_plan"] = CutPlanner().build(pack)

        composer_result = VideoComposer().compose(pack)
        pack["video_composer"] = (
            composer_result
            if isinstance(composer_result, dict)
            else {
                "status": "completed",
                "result": composer_result,
            }
        )

        pack["capcut_export"] = CapCutExportBuilder().build(pack)

        pack["capcut_draft"] = CapCutDraftBuilder().build(
            pack.get("capcut_export", {})
        )

        return pack

    def summary(self, project, product_name, keyword, selected_candidates):
        return {
            "product_name": product_name,
            "keyword": keyword,
            "candidate_count": len(selected_candidates),
            "project_id": self._get_project_value(
                project,
                ["id", "project_id"],
                "",
            ),
            "project_name": self._get_project_value(
                project,
                ["project_name", "name", "title"],
                product_name,
            ),
        }

    def scripts(self, product_name, keyword, package):
        scripts = (
            package.get("scripts")
            or package.get("shorts_scripts")
            or {}
        )

        return {
            "main": scripts.get("main") or package.get("script") or "",
            "hook": (
                scripts.get("hook")
                or package.get("hook")
                or f"{product_name}, 왜 이제 알았을까요?"
            ),
            "cta": (
                scripts.get("cta")
                or f"댓글에 '{keyword}' 남겨주세요 👇"
            ),
            "raw": scripts,
        }

    def captions(self, product_name, keyword, package):
        captions = (
            package.get("captions")
            or package.get("subtitle")
            or []
        )

        if isinstance(captions, str):
            captions = [captions]

        if not captions:
            captions = [
                f"{product_name}, 왜 이제 알았을까요?",
                "생활 속 불편함을 줄여주는 추천템입니다.",
                f"댓글에 '{keyword}' 남겨주세요 👇",
            ]

        return {
            "items": captions,
            "safe_area": "하단 40~50%",
            "font": "Noto Serif KR Bold",
            "max_lines": 2,
        }

    def thumbnail(self, product_name, keyword, package):
        return {
            "size": "9:16",
            "main_text": package.get("hook") or "왜 이제 알았지?",
            "sub_text": product_name,
            "layout": (
                "제품 크게 + 왼쪽 상단 후킹 문구 "
                "+ 하단 짧은 설명"
            ),
            "image_prompt": (
                "9:16 vertical shopping shorts thumbnail, "
                "clean Korean ecommerce style, "
                f"product concept: {product_name}, "
                f"keyword: {keyword}, "
                "bright home background, "
                "large bold Korean text area, "
                "realistic product-focused composition"
            ),
        }

    def blog(self, product_name, keyword):
        return {
            "title": (
                f"{product_name} 사용 전후 차이, "
                "왜 많이 찾을까요?"
            ),
            "body": "\n".join(
                [
                    (
                        f"{product_name}은 생활 속 불편함을 "
                        "줄여주는 제품입니다."
                    ),
                    "",
                    "이런 분께 추천합니다.",
                    "- 매번 같은 불편함을 겪는 분",
                    "- 간단한 생활용품으로 시간을 줄이고 싶은 분",
                    "- 쇼핑 전 핵심 포인트를 빠르게 확인하고 싶은 분",
                    "",
                    (
                        "자세한 제품 정보는 링크를 확인해주세요. "
                        f"댓글에 '{keyword}' 남겨주시면 "
                        "관련 정보를 정리해드릴게요."
                    ),
                ]
            ),
        }

    def inpock(self, product_name, keyword, partner_url):
        return {
            "size": "1000x1000",
            "title": product_name,
            "description": (
                f"생활이 조금 쉬워지는 {product_name}\n"
                f"댓글에 '{keyword}' 남겨주세요 👇"
            ),
            "button": "제품 보러가기",
            "link": (
                partner_url
                or "쿠팡파트너스 링크를 입력하세요."
            ),
            "image_prompt": (
                "1000x1000 square product promo image "
                "for Inpock link page, "
                "clean Korean shopping design, "
                f"product concept: {product_name}, "
                "white background, neat layout, "
                "space for Korean title text"
            ),
        }

    def upload_bundle(self, product_name, keyword, package):
        copy = package.get("platform_copy", {})

        return {
            "youtube_title": copy.get(
                "유튜브 제목",
                f"{product_name}, 왜 이제 알았을까요?",
            ),
            "youtube_desc": copy.get("유튜브 설명", ""),
            "instagram_body": copy.get("인스타 본문", ""),
            "fixed_comment": (
                f"댓글에 '{keyword}' 남겨주세요 👇"
            ),
            "partner_notice": (
                "※ 쿠팡파트너스 활동의 일환으로 "
                "일정액의 수수료를 받을 수 있습니다."
            ),
        }

    def apply_edit_assistant(self, pack):
        selected_sources = pack.get("selected_sources", [])
        captions = pack.get("captions", {}).get("items", [])

        pack["edit_assistant"] = {
            "version": "sprint51-edit-assistant-1.0",
            "goal": (
                "채택된 후보 영상을 기반으로 "
                "쇼핑쇼츠 편집 방향을 제안합니다."
            ),
            "source_count": len(selected_sources),
            "recommended_flow": [
                "0~3초: 후킹 컷",
                "3~8초: 문제 상황",
                "8~15초: 제품 사용 장면",
                "15~22초: 장점 강조",
                "22초 이후: CTA",
            ],
            "caption_guide": {
                "font": "Noto Serif KR Bold",
                "position": "하단 40~50%",
                "max_lines": 2,
                "highlight_color": "#FFD54F",
            },
            "sound_guide": {
                "bgm": "밝고 가벼운 쇼핑/생활템 분위기",
                "sfx": ["Pop", "Click", "Whoosh"],
                "volume": {
                    "bgm": "12~18%",
                    "sfx": "25~40%",
                },
            },
            "caption_preview": captions[:5],
        }

        return pack

    def save_content_pack(self, project, pack):
        project_id = self._get_project_value(
            project,
            ["id", "project_id"],
            "project",
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        json_path = (
            CONTENT_PACK_DIR
            / f"{project_id}_content_pack_{timestamp}.json"
        )
        txt_path = (
            CONTENT_PACK_DIR
            / f"{project_id}_content_pack_{timestamp}.txt"
        )
        capcut_path = (
            CONTENT_PACK_DIR
            / f"{project_id}_capcut_export_{timestamp}.json"
        )
        draft_path = (
            CONTENT_PACK_DIR
            / f"{project_id}_capcut_draft_{timestamp}.json"
        )
        edit_guide_path = (
            CONTENT_PACK_DIR
            / f"{project_id}_edit_guide_{timestamp}.txt"
        )
        video_composer_path = (
            CONTENT_PACK_DIR
            / f"{project_id}_video_composer_{timestamp}.json"
        )

        self._write_json(json_path, pack)
        self._write_text(txt_path, self._pack_to_text(pack))
        self._write_json(
            capcut_path,
            pack.get("capcut_export", {}),
        )
        self._write_json(
            draft_path,
            pack.get("capcut_draft", {}),
        )
        self._write_json(
            video_composer_path,
            pack.get("video_composer", {}),
        )
        self._write_text(
            edit_guide_path,
            self._edit_guide_to_text(pack),
        )

        project_paths = {}

        if pack.get("capcut_draft"):
            project_paths = CapCutProjectBuilder().build(
                project,
                pack["capcut_draft"],
            )

        return {
            "json_path": str(json_path),
            "txt_path": str(txt_path),
            "capcut_path": str(capcut_path),
            "capcut_export_path": str(capcut_path),
            "draft_path": str(draft_path),
            "capcut_draft_path": str(draft_path),
            "edit_guide_path": str(edit_guide_path),
            "video_composer_path": str(video_composer_path),
            **project_paths,
        }

    def _pack_to_text(self, pack):
        lines = []

        summary = pack.get("summary", {})
        upload = pack.get("upload_bundle", {})
        scripts = pack.get("scripts", {})
        captions = pack.get("captions", {})

        lines.append("[AI 콘텐츠 팩]")
        lines.append(
            f"상품명: {summary.get('product_name', '')}"
        )
        lines.append(
            f"키워드: {summary.get('keyword', '')}"
        )
        lines.append("")

        lines.append("[후킹]")
        lines.append(str(scripts.get("hook", "")))
        lines.append("")

        lines.append("[대본]")
        lines.append(str(scripts.get("main", "")))
        lines.append("")

        lines.append("[자막]")
        for item in captions.get("items", []):
            lines.append(f"- {item}")
        lines.append("")

        lines.append("[업로드]")
        lines.append(
            f"유튜브 제목: {upload.get('youtube_title', '')}"
        )
        lines.append(
            f"유튜브 설명: {upload.get('youtube_desc', '')}"
        )
        lines.append(
            f"인스타 본문: {upload.get('instagram_body', '')}"
        )
        lines.append(
            f"고정 댓글: {upload.get('fixed_comment', '')}"
        )
        lines.append(upload.get("partner_notice", ""))

        return "\n".join(lines)

    def _edit_guide_to_text(self, pack):
        edit = pack.get("edit_assistant", {})
        lines = []

        lines.append("[Edit Assistant]")
        lines.append(edit.get("goal", ""))
        lines.append("")

        lines.append("[추천 흐름]")
        for item in edit.get("recommended_flow", []):
            lines.append(f"- {item}")
        lines.append("")

        lines.append("[자막 가이드]")
        for key, value in edit.get("caption_guide", {}).items():
            lines.append(f"- {key}: {value}")
        lines.append("")

        lines.append("[사운드 가이드]")
        for key, value in edit.get("sound_guide", {}).items():
            lines.append(f"- {key}: {value}")

        return "\n".join(lines)

    def _write_json(self, path, data):
        path.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

    def _write_text(self, path, text):
        path.write_text(
            text or "",
            encoding="utf-8",
        )

    def _get_project_value(self, project, names, default=""):
        for name in names:
            if isinstance(project, dict):
                value = project.get(name)
            else:
                value = getattr(project, name, None)

            if value:
                return value

        return default