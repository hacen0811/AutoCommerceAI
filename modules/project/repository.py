import json
from sqlalchemy import select

from database.db import SessionLocal
from database.models import Project, Checklist
from modules.system.project_backup import ProjectBackup


print(
    "######## PROJECT_REPOSITORY SPRINT130-3 UTF8 TRACE LOADED ########",
    flush=True,
)


class ProjectRepository:
    VERSION = "project-repository-130-3-utf8-trace"

    @staticmethod
    def _print_utf8_project_trace(stage, item, project_id=None):
        """
        Sprint130-3:
        SQLAlchemy가 반환한 Project 객체의 문자열을
        RAW, REPR, UNICODE ESCAPE 형태로 각각 출력합니다.

        실제 문자열은 변경하거나 재인코딩하지 않습니다.
        UNICODE ESCAPE 출력은 콘솔 인코딩과 무관하게
        Python 내부 유니코드 상태를 확인하기 위한 진단용입니다.
        """
        print(
            f"[Sprint130-3 Repository UTF8] Stage: {stage}",
            flush=True,
        )
        print(
            f"[Sprint130-3 Repository UTF8] Project ID: "
            f"{project_id if project_id is not None else getattr(item, 'id', None)}",
            flush=True,
        )

        if item is None:
            print(
                "[Sprint130-3 Repository UTF8] Project: None",
                flush=True,
            )
            return

        fields = {
            "title": str(getattr(item, "title", "") or ""),
            "product_name": str(
                getattr(item, "product_name", "") or ""
            ),
            "category": str(
                getattr(item, "category", "") or ""
            ),
            "keyword": str(
                getattr(item, "keyword", "") or ""
            ),
            "data_json_preview": str(
                getattr(item, "data_json", "") or ""
            )[:300],
        }

        for key, value in fields.items():
            print(
                f"[Sprint130-3 Repository UTF8] {key} RAW:",
                value,
                flush=True,
            )
            print(
                f"[Sprint130-3 Repository UTF8] {key} REPR:",
                repr(value),
                flush=True,
            )
            print(
                f"[Sprint130-3 Repository UTF8] {key} UNICODE:",
                value.encode("unicode_escape").decode("ascii"),
                flush=True,
            )

    def create(self, payload):
        with SessionLocal() as db:
            item = Project(
                title=payload.get("title")
                or payload.get("product_name")
                or "새 프로젝트",
                product_name=payload.get("product_name", ""),
                status=payload.get("status", "기획"),
                coupang_url=payload.get("coupang_url", ""),
                partner_url=payload.get("partner_url", ""),
                taobao_url=payload.get("taobao_url", ""),
                douyin_url=payload.get("douyin_url", ""),
                video_path=payload.get("video_path", ""),
                image_url=payload.get("image_url", ""),
                price=payload.get("price", ""),
                category=payload.get("category", ""),
                keyword=payload.get("keyword", "정보"),
                score=payload.get("score", 0),
                data_json=json.dumps(
                    payload.get("data", {}),
                    ensure_ascii=False,
                    indent=2,
                ),
            )

            print(
                "[Sprint130-3 Repository UTF8] CREATE INPUT",
                flush=True,
            )
            for key in ("title", "product_name"):
                value = str(getattr(item, key, "") or "")
                print(
                    f"[Sprint130-3 Repository UTF8] CREATE {key} RAW:",
                    value,
                    flush=True,
                )
                print(
                    f"[Sprint130-3 Repository UTF8] CREATE {key} REPR:",
                    repr(value),
                    flush=True,
                )
                print(
                    f"[Sprint130-3 Repository UTF8] CREATE {key} UNICODE:",
                    value.encode("unicode_escape").decode("ascii"),
                    flush=True,
                )

            db.add(item)
            db.commit()
            db.refresh(item)

            self._print_utf8_project_trace(
                stage="create_after_refresh",
                item=item,
            )

            checklist = Checklist(
                project_id=item.id,
                source_video=bool(item.video_path),
            )
            db.add(checklist)
            db.commit()

            ProjectBackup().auto_export_on_change()
            return item

    def find_by_coupang_url(self, coupang_url):
        with SessionLocal() as db:
            item = db.scalar(
                select(Project).where(
                    Project.coupang_url == coupang_url
                )
            )

            self._print_utf8_project_trace(
                stage="find_by_coupang_url",
                item=item,
            )
            return item

    def all(self):
        with SessionLocal() as db:
            items = list(
                db.scalars(
                    select(Project).order_by(Project.id.desc())
                )
            )

            print(
                "[Sprint130-3 Repository UTF8] ALL COUNT:",
                len(items),
                flush=True,
            )

            for item in items[:5]:
                self._print_utf8_project_trace(
                    stage="all",
                    item=item,
                )

            return items

    def get(self, project_id):
        with SessionLocal() as db:
            item = db.get(Project, project_id)

            self._print_utf8_project_trace(
                stage="get",
                item=item,
                project_id=project_id,
            )

            return item

    def update_project(self, project_id, payload):
        with SessionLocal() as db:
            item = db.get(Project, project_id)
            if not item:
                return None

            self._print_utf8_project_trace(
                stage="update_project_before",
                item=item,
                project_id=project_id,
            )

            fields = [
                "title",
                "product_name",
                "status",
                "coupang_url",
                "partner_url",
                "taobao_url",
                "douyin_url",
                "video_path",
                "image_url",
                "price",
                "category",
                "keyword",
                "score",
            ]

            for field in fields:
                if field in payload:
                    setattr(
                        item,
                        field,
                        payload.get(field) or "",
                    )

            if "data" in payload:
                item.data_json = json.dumps(
                    payload.get("data", {}),
                    ensure_ascii=False,
                    indent=2,
                )
            elif "data_json" in payload:
                item.data_json = (
                    payload.get("data_json") or "{}"
                )

            print(
                "[Sprint130-3 Repository UTF8] UPDATE PAYLOAD",
                flush=True,
            )
            for key in ("title", "product_name"):
                value = str(payload.get(key, "") or "")
                print(
                    f"[Sprint130-3 Repository UTF8] UPDATE {key} RAW:",
                    value,
                    flush=True,
                )
                print(
                    f"[Sprint130-3 Repository UTF8] UPDATE {key} REPR:",
                    repr(value),
                    flush=True,
                )
                print(
                    f"[Sprint130-3 Repository UTF8] UPDATE {key} UNICODE:",
                    value.encode("unicode_escape").decode("ascii"),
                    flush=True,
                )

            checklist = db.scalar(
                select(Checklist).where(
                    Checklist.project_id == project_id
                )
            )
            if not checklist:
                checklist = Checklist(project_id=project_id)
                db.add(checklist)

            checklist.source_video = bool(item.video_path)

            db.commit()
            db.refresh(item)

            self._print_utf8_project_trace(
                stage="update_project_after_refresh",
                item=item,
                project_id=project_id,
            )

            ProjectBackup().auto_export_on_change()
            return item

    def update_status(self, project_id, status):
        with SessionLocal() as db:
            item = db.get(Project, project_id)
            if not item:
                return None

            item.status = status
            db.commit()
            db.refresh(item)
            ProjectBackup().auto_export_on_change()
            return item

    def update_links_and_media(self, project_id, **kwargs):
        with SessionLocal() as db:
            item = db.get(Project, project_id)
            if not item:
                return None

            for key, value in kwargs.items():
                if hasattr(item, key):
                    setattr(item, key, value)

            db.commit()
            db.refresh(item)
            ProjectBackup().auto_export_on_change()
            return item

    def update_youtube_upload(
        self,
        project_id,
        upload_result,
        manifest_result=None,
    ):
        """
        Sprint86-1:
        YouTube 업로드 결과를 Project.data_json에 안전하게 저장합니다.
        기존 프로젝트 데이터는 그대로 보존합니다.
        """
        with SessionLocal() as db:
            item = db.get(Project, project_id)
            if not item:
                return {
                    "ok": False,
                    "version": self.VERSION,
                    "status": "project_not_found",
                    "project_id": project_id,
                }

            try:
                project_data = json.loads(
                    item.data_json or "{}"
                )
            except Exception:
                project_data = {}

            if not isinstance(project_data, dict):
                project_data = {}

            source = (
                upload_result
                if isinstance(upload_result, dict)
                else {}
            )
            manifest = (
                manifest_result
                if isinstance(manifest_result, dict)
                else {}
            )

            youtube_data = {
                "ok": bool(source.get("ok")),
                "status": str(
                    source.get("status") or "unknown"
                ),
                "platform": str(
                    source.get("platform")
                    or "youtube_shorts"
                ),
                "video_id": str(
                    source.get("video_id") or ""
                ),
                "watch_url": str(
                    source.get("watch_url") or ""
                ),
                "uploaded_at": str(
                    source.get("uploaded_at") or ""
                ),
                "actual_upload_performed": bool(
                    source.get(
                        "actual_upload_performed"
                    )
                ),
                "upload_ready": bool(
                    source.get("upload_ready")
                ),
                "dry_run": bool(source.get("dry_run")),
                "manifest_path": str(
                    manifest.get("manifest_path") or ""
                ),
                "manifest_saved": bool(
                    manifest.get("ok")
                ),
            }

            history = project_data.get(
                "youtube_history",
                [],
            )
            if not isinstance(history, list):
                history = []

            history_item = {
                "video_id": youtube_data["video_id"],
                "watch_url": youtube_data["watch_url"],
                "uploaded_at": youtube_data["uploaded_at"],
                "status": youtube_data["status"],
                "platform": youtube_data["platform"],
                "actual_upload_performed": youtube_data[
                    "actual_upload_performed"
                ],
                "manifest_path": youtube_data[
                    "manifest_path"
                ],
                "history_count": len(history),
            }

            is_duplicate = any(
                isinstance(entry, dict)
                and entry.get("video_id")
                == history_item["video_id"]
                and history_item["video_id"]
                for entry in history
            )

            history_item["history_added"] = bool(
                history_item["video_id"]
                and not is_duplicate
            )

            if history_item["history_added"]:
                history.insert(0, history_item)

            project_data["youtube"] = youtube_data
            project_data["youtube_upload"] = dict(source)
            project_data["youtube_manifest"] = dict(
                manifest
            )
            project_data["youtube_history"] = history

            item.data_json = json.dumps(
                project_data,
                ensure_ascii=False,
                indent=2,
                default=str,
            )

            db.commit()
            db.refresh(item)
            ProjectBackup().auto_export_on_change()

            return {
                "ok": True,
                "version": self.VERSION,
                "status": "saved",
                "project_id": project_id,
                "video_id": youtube_data["video_id"],
                "watch_url": youtube_data["watch_url"],
                "uploaded_at": youtube_data["uploaded_at"],
                "manifest_path": youtube_data[
                    "manifest_path"
                ],
            }

    def checklist(self, project_id):
        with SessionLocal() as db:
            item = db.scalar(
                select(Checklist).where(
                    Checklist.project_id == project_id
                )
            )
            if not item:
                item = Checklist(project_id=project_id)
                db.add(item)
                db.commit()
                db.refresh(item)
            return item

    def update_checklist(self, project_id, **kwargs):
        with SessionLocal() as db:
            item = db.scalar(
                select(Checklist).where(
                    Checklist.project_id == project_id
                )
            )
            if not item:
                item = Checklist(project_id=project_id)
                db.add(item)

            for key, value in kwargs.items():
                if hasattr(item, key):
                    setattr(item, key, bool(value))

            db.commit()
            db.refresh(item)
            return item

    def clear_video_path(self, project_id):
        with SessionLocal() as db:
            item = db.get(Project, project_id)
            if not item:
                return None

            item.video_path = ""

            checklist = db.scalar(
                select(Checklist).where(
                    Checklist.project_id == project_id
                )
            )
            if checklist:
                checklist.source_video = False

            db.commit()
            db.refresh(item)
            ProjectBackup().auto_export_on_change()
            return item