import json
from pathlib import Path
from datetime import datetime

from modules.video.cut_planner import CutPlanner
from modules.capcut.export_builder import CapCutExportBuilder

CONTENT_PACK_DIR = Path("exports/content_packs")


class ContentFactory:
    def __init__(self):
        CONTENT_PACK_DIR.mkdir(parents=True, exist_ok=True)

    def apply_edit_assistant(self, pack):
        """
        AI 콘텐츠 팩에 실제 편집용 보조 정보를 추가합니다.
        기존 pack 구조는 유지하고, 없는 값만 안전하게 보강합니다.
        """

        if not isinstance(pack, dict):
            pack = {}

        project_name = (
            pack.get("project_name")
            or pack.get("product_name")
            or "선택 상품"
        )

        shorts = pack.get("shorts") or {}
        thumbnail = pack.get("thumbnail") or {}
        inpock = pack.get("inpock") or {}

        main_hook = self._first_value(
            shorts.get("hooks"),
            thumbnail.get("main_text"),
            "왜 이제 알았지?"
        )

        cta_keyword = self._guess_cta_keyword(project_name)

        pack["edit_assistant"] = {
            "status": "ready",
            "version": "sprint_28",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "summary": f"{project_name} 쇼핑쇼츠 제작용 편집 가이드입니다.",
            "platforms": {
                "youtube_shorts": {
                    "title_style": "검색형 + 후킹형",
                    "description_guide": "제품 정보 안내 문구와 쿠팡파트너스 고지를 포함하세요.",
                    "recommended_length": "35~50초",
                    "cta": f"댓글에 '{cta_keyword}' 남겨주세요 👇",
                },
                "instagram_reels": {
                    "title_style": "공감형 + 짧은 후킹",
                    "caption_guide": "팔로우 유도와 댓글 키워드를 함께 넣으세요.",
                    "recommended_length": "20~40초",
                    "cta": f"팔로우 하시고, 댓글에 '{cta_keyword}' 남겨주세요 👇",
                },
            },
            "capcut": {
                "format": "9:16",
                "subtitle_position": "중앙 하단, 하단 40%",
                "subtitle_style": {
                    "font": "굵고 읽기 쉬운 고딕 계열",
                    "main_size": "38~46",
                    "highlight_size": "46~54",
                    "stroke": "35~55",
                    "shadow": "40~60%",
                    "highlight_color": "#FFD54F",
                },
                "bgm": {
                    "type": "밝은 생활 꿀팁 / 쇼핑 추천템 분위기",
                    "volume": "12~18%",
                },
                "sfx": [
                    {
                        "scene": "후킹 등장",
                        "effect": "Pop / Click",
                        "volume": "35~45%",
                    },
                    {
                        "scene": "불편함 강조",
                        "effect": "Whoosh / Error",
                        "volume": "25~35%",
                    },
                    {
                        "scene": "해결 장면",
                        "effect": "Ding / Sparkle",
                        "volume": "35~45%",
                    },
                ],
            },
            "scene_plan": self._build_scene_plan(project_name, main_hook),
            "thumbnail_guide": {
                "size": thumbnail.get("size", "9:16"),
                "main_text": thumbnail.get("main_text", main_hook),
                "sub_text": thumbnail.get("sub_text", project_name),
                "layout": thumbnail.get(
                    "layout",
                    "제품 크게 + 왼쪽 상단 후킹 문구 + 하단 짧은 설명"
                ),
            },
            "inpock_guide": {
                "size": inpock.get("size", "1000x1000"),
                "title": inpock.get("title", project_name),
                "main_text": inpock.get("main_text", "생활이 편해지는 추천템"),
                "sub_text": inpock.get("sub_text", "제품 정보는 링크에서 확인"),
            },
        }

        pack["final_package"] = {
            "status": "ready",
            "items": [
                "쇼츠 제목",
                "후킹 문구",
                "릴스/쇼츠 본문",
                "CTA",
                "썸네일 가이드",
                "인포크 이미지 가이드",
                "CapCut 편집 가이드",
                "AI 컷 추천",
            ],
        }
        
        pack["cut_plan"] = CutPlanner().build(pack)

        pack["capcut_export"] = (
            CapCutExportBuilder().build(pack)
        )

        return pack

    def save_content_pack(self, project, pack):
        """
        콘텐츠 팩을 JSON/TXT 파일로 저장합니다.
        기존 download_center와 호환되도록 json_path, txt_path를 반환합니다.
        """

        project_id = self._safe_project_id(project)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        json_path = CONTENT_PACK_DIR / f"{project_id}_content_pack_{timestamp}.json"
        txt_path = CONTENT_PACK_DIR / f"{project_id}_content_pack_{timestamp}.txt"

        capcut_export_path = (
            CONTENT_PACK_DIR
            / f"{project_id}_capcut_export_{timestamp}.json"
        )
        json_path.write_text(
            json.dumps(pack, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        txt_path.write_text(
            self._to_text(pack),
            encoding="utf-8",
        )

        capcut_export_path.write_text(
            json.dumps(
                pack.get("capcut_export", {}),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        
        return {
            "json_path": str(json_path),
            "txt_path": str(txt_path),
            "capcut_export_json_path": str(capcut_export_path),
        }

    def _build_scene_plan(self, project_name, main_hook):
        return [
            {
                "scene": 1,
                "role": "후킹",
                "duration": "0~3초",
                "text": main_hook,
                "edit": "큰 자막 + 빠른 줌인 + Pop 효과",
            },
            {
                "scene": 2,
                "role": "문제 공감",
                "duration": "3~10초",
                "text": f"{project_name} 없이 불편했던 상황을 보여주세요.",
                "edit": "불편한 장면 짧게 컷 분리",
            },
            {
                "scene": 3,
                "role": "제품 등장",
                "duration": "10~18초",
                "text": f"{project_name} 등장 장면",
                "edit": "제품 클로즈업 + 밝은 전환",
            },
            {
                "scene": 4,
                "role": "사용 장점",
                "duration": "18~35초",
                "text": "편해지는 포인트를 2~3개로 나눠 보여주세요.",
                "edit": "장점마다 짧은 자막 강조",
            },
            {
                "scene": 5,
                "role": "CTA",
                "duration": "마지막 3~5초",
                "text": "제품 정보는 링크에서 확인해주세요.",
                "edit": "댓글 키워드 + 링크 안내",
            },
        ]

    def _to_text(self, pack):
        project_name = pack.get("project_name", "선택 상품")
        shorts = pack.get("shorts", {})
        edit = pack.get("edit_assistant", {})

        lines = []
        lines.append(f"[AI 콘텐츠 팩] {project_name}")
        lines.append("")

        lines.append("■ 쇼츠 제목")
        for title in shorts.get("titles", []):
            lines.append(f"- {title}")
        lines.append("")

        lines.append("■ 후킹 문구")
        for hook in shorts.get("hooks", []):
            lines.append(f"- {hook}")
        lines.append("")

        lines.append("■ CapCut 편집 가이드")
        capcut = edit.get("capcut", {})
        lines.append(f"- 화면비율: {capcut.get('format', '9:16')}")
        lines.append(f"- 자막 위치: {capcut.get('subtitle_position', '')}")
        lines.append(f"- BGM: {capcut.get('bgm', {}).get('type', '')}")
        lines.append("")

        lines.append("■ 장면 구성")
        for scene in edit.get("scene_plan", []):
            lines.append(
                f"{scene.get('scene')}. {scene.get('role')} / "
                f"{scene.get('duration')} / {scene.get('text')}"
            )

        return "\n".join(lines)

    def _safe_project_id(self, project):
        raw = str(getattr(project, "id", "project"))
        return (
            raw.replace(" ", "_")
            .replace("/", "_")
            .replace("\\", "_")
            .replace(":", "_")
        )

    def _first_value(self, value, fallback=None, default=""):
        if isinstance(value, list) and value:
            return value[0]
        if isinstance(value, str) and value.strip():
            return value
        if isinstance(fallback, str) and fallback.strip():
            return fallback
        return default

    def _guess_cta_keyword(self, project_name):
        name = str(project_name).strip()

        keywords = [
            "수전", "얼음", "장갑", "건조기", "파우치",
            "트랩", "방충망", "거름망", "선풍기",
        ]

        for keyword in keywords:
            if keyword in name:
                return keyword

        if name:
            return name[:2]

        return "정보"