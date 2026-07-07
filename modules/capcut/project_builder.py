import importlib
import json
import shutil
from datetime import datetime
from pathlib import Path

from modules.capcut.uuid_helper import new_uuid

CAPCUT_PROJECT_DIR = Path("exports/capcut_projects")


class CapCutProjectBuilder:
    """
    Sprint 42-3
    CapCut 프로젝트 폴더 생성 오케스트레이터.

    역할:
    - draft_content.json 최상위 구조를 실제 CapCut 샘플에 가깝게 생성
    - Builder 호출만 담당
    - 기존 산출물 파일명과 반환 구조 유지
    - 순환 import 방지를 위해 동적 import 유지
    """

    def __init__(self):
        CAPCUT_PROJECT_DIR.mkdir(parents=True, exist_ok=True)

    def build(self, project, capcut_draft):
        if not isinstance(capcut_draft, dict) or not capcut_draft:
            return {}

        project_id = self._safe_project_id(project)
        timestamp = self._timestamp()

        folder_name = f"{project_id}_capcut_project_{timestamp}"
        project_dir = CAPCUT_PROJECT_DIR / folder_name
        project_dir.mkdir(parents=True, exist_ok=True)

        draft_content_path = project_dir / "draft_content.json"
        draft_meta_path = project_dir / "draft_meta_info.json"
        source_draft_path = project_dir / "source_draft.json"
        readme_path = project_dir / "README.txt"

        draft_content = self._build_draft_content(project, capcut_draft)
        draft_meta = self._build_draft_meta(project, capcut_draft)

        self._write_json(draft_content_path, draft_content)
        self._write_json(draft_meta_path, draft_meta)
        self._write_json(source_draft_path, capcut_draft)

        readme_path.write_text(
            self._build_readme(project, capcut_draft),
            encoding="utf-8",
        )

        zip_path = self._zip_project(project_dir)

        return {
            "project_dir": str(project_dir),
            "project_zip": str(zip_path),
            "draft_content": str(draft_content_path),
            "draft_meta": str(draft_meta_path),
            "source_draft": str(source_draft_path),
        }

    def _build_draft_content(self, project, capcut_draft):
        scenes = self._extract_scenes(capcut_draft)
        tracks = self._build_tracks(capcut_draft, scenes)
        materials = self._build_materials(scenes, tracks)
        duration = self._duration_from_tracks(tracks, scenes)

        return {
            "id": new_uuid(),
            "version": 360000,
            "new_version": "175.0.0",
            "name": self._project_name(project),
            "duration": duration,
            "create_time": 0,
            "update_time": 0,
            "fps": 30.0,
            "is_drop_frame_timecode": False,
            "color_space": 0,
            "config": self._build_config(),
            "canvas_config": self._build_canvas_config(),
            "tracks": tracks,
            "group_container": None,
            "materials": materials,

            "auto_commerce_metadata": {
                "source": "AutoCommerceAI",
                "draft_version": capcut_draft.get("version"),
                "builder": "CapCutProjectBuilder",
                "builder_role": "orchestrator",
                "sprint": "sprint42-3-top-level-structure",
                "created_at": self._now(),
                "project_name": self._project_name(project),
            },

            "canvas": {
                "ratio": "9:16",
                "width": 1080,
                "height": 1920,
            },
        }

    def _build_draft_meta(self, project, capcut_draft):
        scenes = self._extract_scenes(capcut_draft)
        tracks = self._build_tracks(capcut_draft, scenes)

        return {
            "draft_name": self._project_name(project),
            "created_at": self._now(),
            "updated_at": self._now(),
            "app": "AutoCommerceAI",
            "type": "capcut_project_mvp",
            "version": capcut_draft.get("version"),
            "track_count": len(tracks),
            "scene_count": len(scenes)
            or capcut_draft.get("meta", {}).get("scene_count", 0),
            "status": "generated",
        }

    def _build_config(self):
        return {
            "video_mute": False,
            "record_audio_last_index": 1,
            "extract_audio_last_index": 1,
            "original_sound_last_index": 1,
            "subtitle_recognition_id": "",
            "subtitle_taskinfo": [],
            "lyrics_recognition_id": "",
            "lyrics_taskinfo": [],
            "subtitle_sync": True,
            "lyrics_sync": True,
            "voice_change_sync": False,
            "sticker_max_index": 1,
            "adjust_max_index": 1,
            "material_save_mode": 0,
            "export_range": None,
            "maintrack_adsorb": True,
            "combination_max_index": 1,
            "attachment_info": [],
            "zoom_info_params": None,
            "system_font_list": [],
            "multi_language_mode": "none",
            "multi_language_main": "none",
            "multi_language_current": "none",
            "multi_language_list": [],
            "subtitle_keywords_config": None,
            "use_float_render": False,
        }

    def _build_canvas_config(self):
        return {
            "ratio": "original",
            "width": 1080,
            "height": 1920,
            "background": None,
        }

    def _extract_scenes(self, capcut_draft):
        scenes = capcut_draft.get("scenes")
        if isinstance(scenes, list):
            return scenes

        edit_plan = capcut_draft.get("edit_plan", {})
        scenes = edit_plan.get("scenes")
        if isinstance(scenes, list):
            return scenes

        cut_plan = capcut_draft.get("cut_plan")
        if isinstance(cut_plan, list):
            return cut_plan

        timeline = capcut_draft.get("timeline", {})
        tracks = timeline.get("tracks", [])
        if isinstance(tracks, list) and tracks:
            return tracks

        return []

    def _build_tracks(self, capcut_draft, scenes):
        builder = self._load_builder(
            module_name="modules.capcut.timeline_builder",
            class_name="CapCutTimelineBuilder",
        )

        if builder and hasattr(builder, "build_timeline"):
            try:
                built = builder.build_timeline(scenes)
                if isinstance(built, dict):
                    return built.get("tracks", [])
                if isinstance(built, list):
                    return built
            except Exception:
                pass

        timeline = capcut_draft.get("timeline", {})
        tracks = timeline.get("tracks", [])

        if isinstance(tracks, list):
            return tracks

        return []

    def _build_materials(self, scenes, tracks):
        builder = self._load_builder(
            module_name="modules.capcut.material_builder",
            class_name="CapCutMaterialBuilder",
        )

        if builder and hasattr(builder, "build_materials"):
            try:
                built = builder.build_materials(scenes)
                if isinstance(built, dict):
                    return built
            except Exception:
                pass

        return self._fallback_materials(tracks)

    def _load_builder(self, module_name, class_name):
        try:
            module = importlib.import_module(module_name)
            builder_class = getattr(module, class_name, None)
            if builder_class:
                return builder_class()
        except Exception:
            return None

        return None

    def _fallback_materials(self, tracks):
        materials = {
            "videos": [],
            "texts": [],
            "effects": [],
            "audios": [],
        }

        for track in tracks or []:
            track_type = track.get("type")
            clips = track.get("clips", [])

            if track_type == "video":
                materials["videos"].extend(clips)
            elif track_type == "text":
                materials["texts"].extend(clips)
            elif track_type == "effect":
                materials["effects"].extend(clips)
            elif track_type == "audio":
                materials["audios"].extend(clips)

        return materials

    def _duration_from_tracks(self, tracks, scenes):
        max_end = 0

        for track in tracks or []:
            for segment in track.get("segments", []) or []:
                timerange = segment.get("target_timerange", {}) or {}
                start = int(timerange.get("start", 0) or 0)
                duration = int(timerange.get("duration", 0) or 0)
                max_end = max(max_end, start + duration)

        if max_end > 0:
            return max_end

        total = 0
        for scene in scenes or []:
            total += self._scene_duration(scene)

        return total if total > 0 else 5_000_000

    def _scene_duration(self, scene):
        try:
            start = float(str(scene.get("start", "0")).replace("초", ""))
            end = float(str(scene.get("end", "3")).replace("초", ""))
            if end <= start:
                return 3_000_000
            return int((end - start) * 1_000_000)
        except Exception:
            return 3_000_000

    def _build_readme(self, project, capcut_draft):
        lines = []
        lines.append("AutoCommerceAI CapCut Project")
        lines.append("")
        lines.append(f"프로젝트명: {self._project_name(project)}")
        lines.append(f"생성일: {self._now()}")
        lines.append(f"Draft Version: {capcut_draft.get('version')}")
        lines.append("")
        lines.append("포함 파일:")
        lines.append("- draft_content.json")
        lines.append("- draft_meta_info.json")
        lines.append("- source_draft.json")
        lines.append("")
        lines.append("구조:")
        lines.append("- project_builder.py: 오케스트레이터")
        lines.append("- material_builder.py: materials 생성")
        lines.append("- timeline_builder.py: timeline/tracks 생성")
        lines.append("")
        lines.append("Sprint 42-3:")
        lines.append("- draft_content.json 최상위 구조를 실제 CapCut 샘플에 맞춰 보강")
        lines.append("- id / version / new_version / fps / duration / config / canvas_config 추가")
        lines.append("")
        lines.append("주의:")
        lines.append("- 기존 ZIP 산출물 구조를 유지합니다.")
        lines.append("- CapCut 내부 포맷 호환성은 다음 Sprint에서 계속 고도화합니다.")
        return "\n".join(lines)

    def _zip_project(self, project_dir):
        zip_path = shutil.make_archive(
            base_name=str(project_dir),
            format="zip",
            root_dir=project_dir,
        )
        return Path(zip_path)

    def _write_json(self, path, data):
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _timestamp(self):
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _now(self):
        return datetime.now().isoformat(timespec="seconds")

    def _safe_project_id(self, project):
        value = str(getattr(project, "id", "default"))
        return (
            value.replace(" ", "_")
            .replace("/", "_")
            .replace("\\", "_")
            .replace(":", "_")
        )

    def _project_name(self, project):
        return (
            getattr(project, "product_name", "")
            or getattr(project, "title", "")
            or getattr(project, "id", "")
            or "AutoCommerceAI Project"
        )