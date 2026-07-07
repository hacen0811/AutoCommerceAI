from pathlib import Path

from modules.capcut.uuid_helper import new_uuid


class CapCutMaterialBuilder:
    """
    Sprint 42-1
    CapCut Material Builder.

    역할:
    - video material 생성
    - text material 생성
    - 기본 material registry 구조 생성
    - 기존 build_materials(scenes) 인터페이스 유지
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
            videos.append(self.build_video_material(scene))
            texts.append(self.build_text_material(scene))

        return self.build_registry(
            videos=videos,
            texts=texts,
        )

    def build_registry(
        self,
        videos=None,
        texts=None,
        audios=None,
        effects=None,
        animations=None,
        canvases=None,
        speeds=None,
        transitions=None,
    ):
        return {
            "videos": videos or [],
            "texts": texts or [],
            "audios": audios or [],
            "effects": effects or [],
            "animations": animations or [],
            "canvases": canvases or [],
            "speeds": speeds or [],
            "transitions": transitions or [],
        }

    def _duration(self, scene):
        try:
            start = float(str(scene.get("start", "0")).replace("초", ""))
            end = float(str(scene.get("end", "3")).replace("초", ""))

            if end <= start:
                return 3_000_000

            return int((end - start) * 1_000_000)
        except Exception:
            return 3_000_000