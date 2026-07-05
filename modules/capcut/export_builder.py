from typing import Dict, Any, List


class CapCutExportBuilder:
    """
    Sprint 32
    CapCut Export MVP

    목적:
    - content_pack의 cut_plan을 CapCut 편집용 표준 JSON으로 변환
    - 실제 CapCut draft 생성 전 단계의 중간 포맷
    """

    def build(self, content_pack: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(content_pack, dict):
            content_pack = {}

        project_name = (
            content_pack.get("project_name")
            or content_pack.get("product_name")
            or "선택 상품"
        )

        cut_plan = content_pack.get("cut_plan", [])

        return {
            "version": "sprint32-capcut-export-mvp",
            "project_name": project_name,
            "format": "9:16",
            "source": "AutoCommerceAI",
            "clips": self._build_clips(cut_plan),
            "subtitles": self._build_subtitles(cut_plan),
            "effects": self._build_effects(cut_plan),
            "meta": {
                "clip_count": len(cut_plan),
                "status": "ready" if cut_plan else "empty",
            },
        }

    def _build_clips(self, cut_plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        clips = []

        for item in cut_plan:
            clips.append(
                {
                    "scene": item.get("scene"),
                    "candidate": item.get("candidate", ""),
                    "query": item.get("query", ""),
                    "url": item.get("url", ""),
                    "start": item.get("start", "00.0"),
                    "end": item.get("end", "03.0"),
                    "speed": item.get("speed", "1.0x"),
                    "camera": item.get("camera", "Static"),
                    "zoom": item.get("zoom", "100%"),
                    "transition": item.get("transition", "None"),
                    "confidence": item.get("confidence", 0),
                    "hook_level": item.get("hook_level", "Low"),
                    "reason": item.get("reason", ""),
                }
            )

        return clips

    def _build_subtitles(self, cut_plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        subtitles = []

        for item in cut_plan:
            subtitles.append(
                {
                    "scene": item.get("scene"),
                    "text": item.get("purpose", ""),
                    "animation": item.get("subtitle", "Fade"),
                    "position": item.get("subtitle_position", "하단40%"),
                    "style": {
                        "font": "bold gothic",
                        "main_size": 44,
                        "stroke": 45,
                        "highlight_color": "#FFD54F",
                    },
                }
            )

        return subtitles

    def _build_effects(self, cut_plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        effects = []

        for item in cut_plan:
            effects.append(
                {
                    "scene": item.get("scene"),
                    "effect": item.get("effect", "None"),
                    "transition": item.get("transition", "None"),
                    "zoom": item.get("zoom", "100%"),
                    "speed": item.get("speed", "1.0x"),
                    "edit_note": item.get("edit_note", ""),
                }
            )

        return effects