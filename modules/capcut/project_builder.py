import json
import shutil
import time
from pathlib import Path

from modules.capcut.uuid_helper import new_uuid


class CapCutProjectBuilder:
    """
    Sprint 45-1
    CapCut native draft project builder.

    핵심:
    - 템플릿 프로젝트 폴더를 AppData CapCut Drafts로 복사
    - Timelines/<timeline_uuid> 폴더명을 새 UUID로 변경
    - Timelines/project.json / project.json.bak 내부 timeline id 갱신
    - draft_content.json / draft_content.json.bak 갱신
    - CapCut 프로젝트 목록 DB 역할의 root_meta_info.json 등록/갱신
    """

    def __init__(self, template_dir=None, drafts_root=None, root_meta_path=None):
        self.template_dir = Path(template_dir) if template_dir else self._default_template_dir()
        self.drafts_root = Path(drafts_root) if drafts_root else self._default_drafts_root()
        self.root_meta_path = Path(root_meta_path) if root_meta_path else self._default_root_meta_path()

    def build(self, project_name, draft_content):
        native_dir = self._create_native_project_dir(project_name)

        self._copy_template(native_dir)
        self._refresh_timeline_project(native_dir)
        self._write_draft_content(native_dir, draft_content)
        self._register_root_meta(native_dir, project_name)

        return {
            "ok": True,
            "native_dir": str(native_dir),
            "project_name": project_name,
            "root_meta_path": str(self.root_meta_path),
        }

    def _default_template_dir(self):
        return Path("templates/capcut/native_template")

    def _default_drafts_root(self):
        return Path.home() / "AppData" / "Local" / "CapCut Drafts"

    def _default_root_meta_path(self):
        return (
            Path.home()
            / "AppData"
            / "Local"
            / "CapCut"
            / "User Data"
            / "Projects"
            / "com.lveditor.draft"
            / "root_meta_info.json"
        )

    def _create_native_project_dir(self, project_name):
        safe_name = self._safe_name(project_name)
        native_dir = self.drafts_root / safe_name

        if not native_dir.exists():
            return native_dir

        index = 2
        while True:
            candidate = self.drafts_root / f"{safe_name} ({index})"
            if not candidate.exists():
                return candidate
            index += 1

    def _copy_template(self, native_dir):
        if not self.template_dir.exists():
            raise FileNotFoundError(f"CapCut template directory not found: {self.template_dir}")

        native_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(self.template_dir, native_dir)

    def _write_draft_content(self, native_dir, draft_content):
        text = json.dumps(
            draft_content,
            ensure_ascii=False,
            indent=4,
        )

        targets = [
            native_dir / "draft_content.json",
            native_dir / "draft_content.json.bak",
        ]

        timelines_dir = native_dir / "Timelines"

        if timelines_dir.exists():
            for timeline in timelines_dir.iterdir():
                if not timeline.is_dir():
                    continue

                targets.extend([
                    timeline / "draft_content.json",
                    timeline / "draft_content.json.bak",
                ])

        for path in targets:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                text,
                encoding="utf-8",
            )

    def _refresh_timeline_project(self, native_dir):
        native_dir = Path(native_dir)

        timelines_dir = native_dir / "Timelines"
        project_json = timelines_dir / "project.json"
        project_bak = timelines_dir / "project.json.bak"

        if not timelines_dir.exists():
            return

        if not project_json.exists():
            return

        timeline_dirs = [
            path for path in timelines_dir.iterdir()
            if path.is_dir()
        ]

        if not timeline_dirs:
            return

        old_timeline_dir = timeline_dirs[0]
        new_timeline_id = new_uuid()
        new_timeline_dir = timelines_dir / new_timeline_id

        if old_timeline_dir.name != new_timeline_id:
            shutil.move(str(old_timeline_dir), str(new_timeline_dir))

        now = int(time.time())

        self._update_timeline_project_file(
            project_json,
            new_timeline_id=new_timeline_id,
            now=now,
        )

        self._update_timeline_project_file(
            project_bak,
            new_timeline_id=new_timeline_id,
            now=now,
        )

    def _update_timeline_project_file(self, path, new_timeline_id, now):
        path = Path(path)

        if not path.exists():
            return

        data = json.loads(path.read_text(encoding="utf-8"))

        data["id"] = new_uuid()
        data["main_timeline_id"] = new_timeline_id
        data["create_time"] = now
        data["update_time"] = now

        timelines = data.get("timelines", [])
        if timelines:
            timelines[0]["id"] = new_timeline_id

        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=4),
            encoding="utf-8",
        )

    def _register_root_meta(self, native_dir, project_name):
        native_dir = Path(native_dir)

        if not self.root_meta_path.exists():
            return

        root_meta = json.loads(self.root_meta_path.read_text(encoding="utf-8"))

        stores = root_meta.get("all_draft_store", [])
        if not isinstance(stores, list):
            stores = []

        now = self._capcut_timestamp()

        safe_project_name = self._safe_name(project_name)
        fold_path = self._capcut_path(native_dir)
        json_file = self._capcut_path(native_dir / "draft_content.json")
        cover_file = self._capcut_path(native_dir / "draft_cover.jpg")

        draft_item = self._build_root_meta_item(
            project_name=safe_project_name,
            fold_path=fold_path,
            json_file=json_file,
            cover_file=cover_file,
            now=now,
            native_dir=native_dir,
        )

        replaced = False
        for index, item in enumerate(stores):
            if item.get("draft_fold_path") == fold_path:
                stores[index] = draft_item
                replaced = True
                break

        if not replaced:
            stores.append(draft_item)

        root_meta["all_draft_store"] = stores
        root_meta["draft_ids"] = len(stores)
        root_meta.setdefault(
            "root_path",
            self._capcut_path(self.root_meta_path.parent),
        )

        self.root_meta_path.write_text(
            json.dumps(root_meta, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )

    def _build_root_meta_item(self, project_name, fold_path, json_file, cover_file, now, native_dir):
        return {
            "cloud_draft_cover": False,
            "cloud_draft_sync": False,
            "draft_cloud_last_action_download": False,
            "draft_cloud_purchase_info": "",
            "draft_cloud_template_id": "",
            "draft_cloud_tutorial_info": "",
            "draft_cloud_videocut_purchase_info": "",
            "draft_cover": cover_file,
            "draft_fold_path": fold_path,
            "draft_id": new_uuid(),
            "draft_is_ai_shorts": False,
            "draft_is_cloud_temp_draft": False,
            "draft_is_invisible": False,
            "draft_is_pippit_draft": False,
            "draft_is_web_article_video": False,
            "draft_json_file": json_file,
            "draft_name": project_name,
            "draft_new_version": "",
            "draft_root_path": self._capcut_path(self.drafts_root),
            "draft_timeline_materials_size": self._draft_timeline_materials_size(native_dir),
            "draft_type": "",
            "draft_web_article_video_enter_from": "",
            "pippit_avatar_url": "",
            "pippit_extra_info": "",
            "pippit_id": "",
            "pippit_user_name": "",
            "streaming_edit_draft_ready": True,
            "tm_draft_cloud_completed": "",
            "tm_draft_cloud_entry_id": -1,
            "tm_draft_cloud_modified": 0,
            "tm_draft_cloud_parent_entry_id": -1,
            "tm_draft_cloud_space_id": -1,
            "tm_draft_cloud_user_id": -1,
            "tm_draft_create": now,
            "tm_draft_modified": now,
            "tm_draft_removed": 0,
            "tm_duration": self._draft_duration(native_dir),
        }

    def _draft_timeline_materials_size(self, native_dir):
        native_dir = Path(native_dir)
        total = 0

        for name in [
            "draft_content.json",
            "draft_meta_info.json",
            "key_value.json",
            "timeline_layout.json",
        ]:
            path = native_dir / name
            if path.exists():
                total += path.stat().st_size

        timelines_dir = native_dir / "Timelines"
        if timelines_dir.exists():
            for path in timelines_dir.rglob("*"):
                if path.is_file():
                    total += path.stat().st_size

        return total

    def _draft_duration(self, native_dir):
        draft_content_path = Path(native_dir) / "draft_content.json"

        if not draft_content_path.exists():
            return 0

        try:
            data = json.loads(draft_content_path.read_text(encoding="utf-8"))
        except Exception:
            return 0

        duration = data.get("duration")
        if isinstance(duration, int):
            return duration

        max_end = 0
        tracks = data.get("tracks", [])
        for track in tracks:
            for segment in track.get("segments", []):
                target_timerange = segment.get("target_timerange", {})
                start = target_timerange.get("start", 0)
                seg_duration = target_timerange.get("duration", 0)

                if isinstance(start, int) and isinstance(seg_duration, int):
                    max_end = max(max_end, start + seg_duration)

        return max_end

    def _capcut_timestamp(self):
        return int(time.time() * 1000000)

    def _capcut_path(self, path):
        return str(Path(path)).replace("\\", "/")

    def _safe_name(self, name):
        value = str(name or "AutoCommerceAI Draft").strip()

        for char in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
            value = value.replace(char, "_")

        return value or "AutoCommerceAI Draft"