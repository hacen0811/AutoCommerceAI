import json
import shutil
from datetime import datetime
from pathlib import Path

from modules.capcut.uuid_helper import new_uuid

CAPCUT_PROJECT_DIR = Path("exports/capcut_projects")


class CapCutProjectBuilder:
    """
    Sprint 38 MVP
    AutoCommerceAI CapCut Draft JSON을 실제 프로젝트 폴더 형태로 저장한다.

    주의:
    - 아직 CapCut 내부 포맷 완전 호환 버전은 아님
    - draft_content.json / draft_meta_info.json / source_draft.json 생성
    - 다음 단계에서 실제 CapCut 샘플 프로젝트 구조와 맞춰 고도화
    """

    def __init__(self):
        CAPCUT_PROJECT_DIR.mkdir(parents=True, exist_ok=True)

    def build(self, project, capcut_draft):
        if not isinstance(capcut_draft, dict) or not capcut_draft:
            return {}

        project_id = self._safe_project_id(project)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

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
        timeline = capcut_draft.get("timeline", {})
        tracks = timeline.get("tracks", [])

        return {
            "version": "sprint38-capcut-project-mvp",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "project_name": self._project_name(project),
            "canvas": {
                "ratio": "9:16",
                "width": 1080,
                "height": 1920,
            },
            "tracks": tracks,
            "materials": self._build_materials(tracks),
            "metadata": {
                "source": "AutoCommerceAI",
                "draft_version": capcut_draft.get("version"),
            },
        }

    def _build_draft_meta(self, project, capcut_draft):
        tracks = capcut_draft.get("timeline", {}).get("tracks", [])

        return {
            "draft_name": self._project_name(project),
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "app": "AutoCommerceAI",
            "type": "capcut_project_mvp",
            "version": capcut_draft.get("version"),
            "track_count": len(tracks),
            "scene_count": capcut_draft.get("meta", {}).get("scene_count", 0),
            "status": "generated",
        }

    def _build_materials(self, tracks):
        materials = {
            "videos": [],
            "texts": [],
            "effects": [],
            "audios": [],
        }

        for track in tracks:
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

    def _build_readme(self, project, capcut_draft):
        lines = []
        lines.append("AutoCommerceAI CapCut Project MVP")
        lines.append("")
        lines.append(f"프로젝트명: {self._project_name(project)}")
        lines.append(f"생성일: {datetime.now().isoformat(timespec='seconds')}")
        lines.append(f"Draft Version: {capcut_draft.get('version')}")
        lines.append("")
        lines.append("포함 파일:")
        lines.append("- draft_content.json")
        lines.append("- draft_meta_info.json")
        lines.append("- source_draft.json")
        lines.append("")
        lines.append("주의:")
        lines.append("- 현재는 CapCut 내부 포맷 완전 호환 전 단계입니다.")
        lines.append("- 다음 Sprint에서 실제 CapCut 샘플 프로젝트 구조에 맞춰 고도화합니다.")
        return "\n".join(lines)

    def _zip_project(self, project_dir):
        zip_base = project_dir
        zip_path = shutil.make_archive(
            base_name=str(zip_base),
            format="zip",
            root_dir=project_dir,
        )
        return Path(zip_path)

    def _write_json(self, path, data):
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

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