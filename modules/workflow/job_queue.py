import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4


class JobQueue:
    """
    여러 프로젝트를 순서대로 처리하기 위한 간단한 파일 기반 큐.
    """

    def __init__(self, path="exports/workflow_queue/jobs.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.path.exists():
            return []
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def save(self, jobs):
        self.path.write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8")
        return jobs

    def add(self, project_id, project_name):
        jobs = self.load()
        job = {
            "job_id": uuid4().hex[:12],
            "project_id": project_id,
            "project_name": project_name,
            "status": "queued",
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        jobs.append(job)
        self.save(jobs)
        return job

    def update(self, job_id, status):
        jobs = self.load()
        for job in jobs:
            if job.get("job_id") == job_id:
                job["status"] = status
                job["updated_at"] = datetime.now().isoformat(timespec="seconds")
                break
        self.save(jobs)
        return jobs

    def clear_done(self):
        jobs = [j for j in self.load() if j.get("status") not in ["done", "failed"]]
        return self.save(jobs)
