from typing import Dict, Any, List


class CapCutExportBuilder:
    """
    Sprint 38
    CapCut Export 2.0

    목적:
    - content_pack의 cut_plan을 CapCut Draft Builder가 쓰기 좋은 표준 JSON으로 변환
    - clips / subtitles / effects / audio / scenes를 모두 포함
    - 실제 CapCut 프로젝트 생성 전 단계의 안정적인 중간 포맷
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
        if not isinstance(cut_plan, list):
            cut_plan = []

        scenes = self._build_scenes(cut_plan)

        return {
            "version": "sprint38-capcut-export-2.0",
            "project_name": project_name,
            "format": "9:16",
            "aspect_ratio": "9:16",
            "duration_target": "50s",
            "source": "AutoCommerceAI",
            "scenes": scenes,
            "clips": self._build_clips(scenes),
            "subtitles": self._build_subtitles(scenes),
            "effects": self._build_effects(scenes),
            "audio": self._build_audio(scenes),
            "meta": {
                "scene_count": len(scenes),
                "clip_count": len(scenes),
                "status": "ready" if scenes else "empty",
            },
        }

    def _build_scenes(self, cut_plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        scenes = []

        for idx, item in enumerate(cut_plan, start=1):
            if not isinstance(item, dict):
                continue

            start = item.get("start", "00.0")
            end = item.get("end", "03.0")

            scenes.append(
                {
                    "scene": item.get("scene") or idx,
                    "candidate": item.get("candidate", ""),
                    "query": item.get("query", ""),
                    "url": item.get("url", ""),
                    "start": start,
                    "end": end,
                    "duration": self._duration(start, end),
                    "purpose": item.get("purpose", ""),
                    "caption": item.get("caption") or item.get("purpose", ""),
                    "confidence": item.get("confidence", 0),
                    "hook_level": item.get("hook_level", "Low"),
                    "reason": item.get("reason", ""),
                    "speed": item.get("speed", "1.0x"),
                    "camera": item.get("camera", "Static"),
                    "zoom": item.get("zoom", "105%"),
                    "transition": item.get("transition", self._default_transition(idx)),
                    "effect": item.get("effect", self._default_effect(idx, item)),
                    "subtitle": item.get("subtitle", self._default_subtitle_animation(idx)),
                    "subtitle_position": item.get("subtitle_position", "하단40%"),
                    "sfx": item.get("sfx", self._default_sfx(idx, item)),
                    "bgm_volume": item.get("bgm_volume", self._default_bgm_volume(idx, len(cut_plan))),
                    "edit_note": item.get("edit_note", ""),
                }
            )

        return scenes

    def _build_clips(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        clips = []

        for item in scenes:
            clips.append(
                {
                    "scene": item.get("scene"),
                    "candidate": item.get("candidate", ""),
                    "query": item.get("query", ""),
                    "url": item.get("url", ""),
                    "start": item.get("start", "00.0"),
                    "end": item.get("end", "03.0"),
                    "duration": item.get("duration"),
                    "speed": item.get("speed", "1.0x"),
                    "camera": item.get("camera", "Static"),
                    "zoom": item.get("zoom", "105%"),
                    "transition": item.get("transition", "cut"),
                    "confidence": item.get("confidence", 0),
                    "hook_level": item.get("hook_level", "Low"),
                    "reason": item.get("reason", ""),
                }
            )

        return clips

    def _build_subtitles(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        subtitles = []

        for item in scenes:
            subtitles.append(
                {
                    "scene": item.get("scene"),
                    "text": item.get("caption") or item.get("purpose", ""),
                    "start": item.get("start", "00.0"),
                    "end": item.get("end", "03.0"),
                    "animation": item.get("subtitle", "Bounce"),
                    "position": item.get("subtitle_position", "하단40%"),
                    "style": {
                        "font": "bold gothic",
                        "main_size": 44,
                        "stroke": 70,
                        "shadow": 60,
                        "highlight_color": "#FFD54F",
                    },
                }
            )

        return subtitles

    def _build_effects(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        effects = []

        for item in scenes:
            effects.append(
                {
                    "scene": item.get("scene"),
                    "start": item.get("start", "00.0"),
                    "end": item.get("end", "03.0"),
                    "effect": item.get("effect", "zoom_in"),
                    "transition": item.get("transition", "cut"),
                    "zoom": item.get("zoom", "105%"),
                    "speed": item.get("speed", "1.0x"),
                    "edit_note": item.get("edit_note", ""),
                }
            )

        return effects

    def _build_audio(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        audio = []

        for item in scenes:
            audio.append(
                {
                    "scene": item.get("scene"),
                    "start": item.get("start", "00.0"),
                    "end": item.get("end", "03.0"),
                    "sfx": item.get("sfx", "pop"),
                    "sfx_volume": item.get("sfx_volume", "35%"),
                    "bgm_volume": item.get("bgm_volume", "18%"),
                }
            )

        return audio

    def _default_transition(self, idx: int) -> str:
        if idx == 1:
            return "none"
        return "cut"

    def _default_effect(self, idx: int, item: Dict[str, Any]) -> str:
        purpose = str(item.get("purpose", "")).lower()

        if idx == 1 or "후킹" in purpose or "hook" in purpose:
            return "quick_zoom"

        if "비교" in purpose or "before" in purpose or "after" in purpose:
            return "split_compare"

        if "cta" in purpose or "댓글" in purpose:
            return "cta_pop"

        return "zoom_in"

    def _default_subtitle_animation(self, idx: int) -> str:
        if idx == 1:
            return "Bounce"
        return "Pop"

    def _default_sfx(self, idx: int, item: Dict[str, Any]) -> str:
        purpose = str(item.get("purpose", "")).lower()

        if idx == 1 or "후킹" in purpose or "hook" in purpose:
            return "Pop"

        if "비교" in purpose or "before" in purpose or "after" in purpose:
            return "Whoosh"

        if "cta" in purpose or "댓글" in purpose:
            return "Click"

        return "Pop"

    def _default_bgm_volume(self, idx: int, total: int) -> str:
        if total <= 1:
            return "15%"

        ratio = idx / total

        if ratio < 0.3:
            return "12%"
        if ratio < 0.7:
            return "18%"
        return "22%"

    def _duration(self, start, end):
        try:
            return round(
                float(str(end).replace("초", "")) -
                float(str(start).replace("초", "")),
                1,
            )
        except Exception:
            return None