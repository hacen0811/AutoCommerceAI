import json
from datetime import datetime
from pathlib import Path


class PipelineState:
    """
    One Click Pipeline 실행 상태 저장소.
    실패해도 JSON 상태 파일을 보고 어디서 멈췄는지 확인할 수 있습니다.
    """

    def __init__(self, base_dir="exports/workflow_states"):
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)

    def state_path(self, job_id):
        return self.base / f"{job_id}.json"

    def create(self, job_id, project_name="", steps=None):
        data = {
            "job_id": job_id,
            "project_name": project_name,
            "status": "created",
            "current_step": "",
            "progress": 0,
            "steps": steps or [],
            "results": {},
            "errors": [],
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        return self.save(job_id, data)

    def load(self, job_id):
        path = self.state_path(job_id)
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, job_id, data):
        data["updated_at"] = datetime.now().isoformat(timespec="seconds")
        self.state_path(job_id).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return data

    def update_step(self, job_id, step_name, status, result=None, error=None):
        data = self.load(job_id)
        if not data:
            data = self.create(job_id)

        data["current_step"] = step_name
        if error:
            data.setdefault("errors", []).append({"step": step_name, "error": str(error)})
        if result is not None:
            data.setdefault("results", {})[step_name] = result

        steps = data.get("steps", [])
        for s in steps:
            if s.get("name") == step_name:
                s["status"] = status
                break

        done = len([s for s in steps if s.get("status") in ["done", "skipped"]])
        data["progress"] = int(done / len(steps) * 100) if steps else 0
        data["status"] = "failed" if error else ("done" if data["progress"] >= 100 else "running")
        return self.save(job_id, data)

    def list_recent(self, limit=20):
        files = sorted(self.base.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        return files[:limit]
