from datetime import datetime


class CapCutDraftBuilder:
    """
    Sprint 34 MVP
    CapCut Export JSON을 기반으로 CapCut Draft 형태의 JSON을 생성한다.
    실제 CapCut 내부 포맷 완전 호환 전 단계.
    """

    def build(self, capcut_export):
        if not capcut_export:
            return {}

        scenes = capcut_export.get("scenes", []) or capcut_export.get("clips", [])

        draft = {
            "version": "sprint34-capcut-draft-mvp-1.0",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "draft_type": "capcut_json_mvp",
            "meta": {
                "source_version": capcut_export.get("version"),
                "scene_count": len(scenes),
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
                ]
            },
        }

        return draft

    def _build_video_clips(self, scenes):
        clips = []

        for idx, scene in enumerate(scenes, start=1):
            clips.append(
                {
                    "id": f"video_clip_{idx}",
                    "scene": scene.get("scene") or idx,
                    "source": scene.get("candidate") or scene.get("url") or "",
                    "query": scene.get("query", ""),
                    "start": scene.get("start", "00.0"),
                    "end": scene.get("end", "03.0"),
                    "purpose": scene.get("purpose", ""),
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
                    },
                }
            )

        return clips