from datetime import datetime


class CapCutDraftBuilder:
    """
    Sprint 37
    CapCut Export JSON을 기반으로 편집 지시가 포함된 Draft JSON을 생성한다.
    실제 CapCut 내부 포맷 완전 호환 전 단계의 AutoCommerceAI Draft 포맷.
    """

    def build(self, capcut_export):
        if not isinstance(capcut_export, dict) or not capcut_export:
            return {}

        scenes = capcut_export.get("scenes", []) or capcut_export.get("clips", [])
        scenes = [scene for scene in scenes if isinstance(scene, dict)]

        return {
            "version": "sprint37-capcut-draft-2.0",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "draft_type": "autocommerceai_capcut_draft",
            "meta": {
                "source_version": capcut_export.get("version"),
                "scene_count": len(scenes),
                "aspect_ratio": capcut_export.get("aspect_ratio", "9:16"),
                "duration_target": capcut_export.get("duration_target", "50s"),
            },
            "timeline": {
                "tracks": [
                    {
                        "type": "video",
                        "clips": self._build_video_clips(scenes),
                    },
                    {
                        "type": "text",
                        "clips": self._build_text_clips(scenes),
                    },
                    {
                        "type": "effect",
                        "clips": self._build_effect_clips(scenes),
                    },
                    {
                        "type": "audio",
                        "clips": self._build_audio_clips(scenes),
                    },
                ]
            },
            "edit_guide": self._build_edit_guide(scenes),
        }

    def _build_video_clips(self, scenes):
        clips = []

        for idx, scene in enumerate(scenes, start=1):
            start = scene.get("start", "00.0")
            end = scene.get("end", "03.0")

            clips.append(
                {
                    "id": f"video_clip_{idx}",
                    "scene": scene.get("scene") or idx,
                    "source": scene.get("candidate") or scene.get("url") or "",
                    "query": scene.get("query", ""),
                    "start": start,
                    "end": end,
                    "duration": self._duration(start, end),
                    "purpose": scene.get("purpose", ""),
                    "edit": {
                        "scale": scene.get("scale", "105%"),
                        "speed": scene.get("speed", "1.0x"),
                        "transition_in": scene.get("transition_in", self._default_transition(idx)),
                        "transition_out": scene.get("transition_out", "cut"),
                    },
                }
            )

        return clips

    def _build_text_clips(self, scenes):
        clips = []

        for idx, scene in enumerate(scenes, start=1):
            text = (
                scene.get("caption")
                or scene.get("text")
                or scene.get("purpose")
                or ""
            )

            if not text:
                continue

            clips.append(
                {
                    "id": f"text_clip_{idx}",
                    "scene": scene.get("scene") or idx,
                    "text": text,
                    "start": scene.get("start", "00.0"),
                    "end": scene.get("end", "03.0"),
                    "style": {
                        "position": "bottom_center",
                        "safe_area": True,
                        "font_size": 42,
                        "stroke": 70,
                        "shadow": 60,
                        "highlight_color": "#FFD54F",
                        "animation_in": "bounce",
                        "animation_out": "fade",
                    },
                }
            )

        return clips

    def _build_effect_clips(self, scenes):
        clips = []

        for idx, scene in enumerate(scenes, start=1):
            purpose = str(scene.get("purpose", "")).lower()

            effect = "zoom_in"
            if "후킹" in purpose or "hook" in purpose:
                effect = "quick_zoom"
            elif "비교" in purpose or "before" in purpose or "after" in purpose:
                effect = "split_compare"
            elif "cta" in purpose or "댓글" in purpose:
                effect = "cta_pop"

            clips.append(
                {
                    "id": f"effect_clip_{idx}",
                    "scene": scene.get("scene") or idx,
                    "start": scene.get("start", "00.0"),
                    "end": scene.get("end", "03.0"),
                    "effect": effect,
                    "intensity": scene.get("effect_intensity", "medium"),
                }
            )

        return clips

    def _build_audio_clips(self, scenes):
        clips = []

        for idx, scene in enumerate(scenes, start=1):
            purpose = str(scene.get("purpose", "")).lower()

            sfx = "pop"
            volume = "35%"

            if "후킹" in purpose or "hook" in purpose:
                sfx = "pop"
                volume = "40%"
            elif "비교" in purpose or "before" in purpose or "after" in purpose:
                sfx = "whoosh"
                volume = "35%"
            elif "cta" in purpose or "댓글" in purpose:
                sfx = "click"
                volume = "40%"

            clips.append(
                {
                    "id": f"audio_clip_{idx}",
                    "scene": scene.get("scene") or idx,
                    "start": scene.get("start", "00.0"),
                    "end": scene.get("end", "03.0"),
                    "sfx": sfx,
                    "volume": volume,
                    "bgm_volume": self._bgm_volume(idx, len(scenes)),
                }
            )

        return clips

    def _build_edit_guide(self, scenes):
        guide = []

        for idx, scene in enumerate(scenes, start=1):
            guide.append(
                {
                    "scene": scene.get("scene") or idx,
                    "purpose": scene.get("purpose", ""),
                    "instruction": self._instruction_for_scene(idx, scene),
                }
            )

        return guide

    def _instruction_for_scene(self, idx, scene):
        purpose = str(scene.get("purpose", ""))

        if idx == 1 or "후킹" in purpose:
            return "첫 장면은 빠른 줌인과 큰 자막으로 시선을 잡습니다."

        if "비교" in purpose or "Before" in purpose or "After" in purpose:
            return "사용 전후 차이가 보이도록 좌우 비교 또는 빠른 컷 전환을 사용합니다."

        if "CTA" in purpose or "댓글" in purpose:
            return "댓글 유도 문구를 하단 중앙에 고정하고 클릭 효과음을 넣습니다."

        return "장면 목적에 맞춰 제품 사용 장면을 짧고 명확하게 보여줍니다."

    def _default_transition(self, idx):
        if idx == 1:
            return "none"
        return "cut"

    def _bgm_volume(self, idx, total):
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
            return round(float(str(end).replace("초", "")) - float(str(start).replace("초", "")), 1)
        except Exception:
            return None