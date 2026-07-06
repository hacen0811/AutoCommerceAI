from pathlib import Path

from modules.capcut.uuid_helper import new_uuid


class CapCutMaterialBuilder:
    """
    Sprint 39
    실제 CapCut draft_content.json 구조를 기반으로
    Video/Text Material 생성.
    """

    def build_video_material(self, scene):
        source = scene.get("candidate") or scene.get("url") or ""

        path = Path(source)

        return {
            "id": new_uuid(),
            "unique_id": "",
            "type": "video",
            "duration": self._duration(scene),
            "path": str(path),
            "media_path": "",
            "local_id": "",
            "material_name": path.name if path.name else "",
            "width": 1080,
            "height": 1920,
            "has_audio": False,
            "crop_ratio": "free",
            "source": 0,
            "source_platform": 0,
            "check_flag": 0,
        }

    def build_text_material(self, scene):
        text = (
            scene.get("caption")
            or scene.get("text")
            or scene.get("purpose")
            or ""
        )

        return {
            "id": new_uuid(),
            "type": "text",
            "content": text,
            "font_size": 30,
            "text_color": "#FFFFFF",
            "border_color": "#000000",
            "border_width": 0.08,
            "shadow_alpha": 0.35,
            "line_max_width": 0.82,
            "alignment": 1,
            "font_title": "none",
        }

    def build_materials(self, scenes):
        videos = []
        texts = []

        for scene in scenes or []:
            video = self.build_video_material(scene)
            text = self.build_text_material(scene)

            videos.append(video)
            texts.append(text)

        return {
            "videos": videos,
            "texts": texts,
        }

    def _duration(self, scene):
        try:
            start = float(str(scene.get("start", "0")).replace("초", ""))
            end = float(str(scene.get("end", "3")).replace("초", ""))
            return int((end - start) * 1_000_000)
        except Exception:
            return 3_000_000