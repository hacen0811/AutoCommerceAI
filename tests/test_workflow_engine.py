from modules.workflow.workflow_engine import WorkflowEngine
from modules.workflow.job_queue import JobQueue
from modules.workflow.pipeline_state import PipelineState


class P:
    id = 1
    product_name = "문틈 방충망"
    keyword = "방충망"
    coupang_url = "https://www.coupang.com/vp/products/9067798449?vendorItemId=93562341136"
    partner_url = ""
    price = ""
    category = ""
    image_url = ""
    video_path = ""


def test_workflow_steps():
    steps = WorkflowEngine().steps()
    assert len(steps) == 7
    assert steps[0]["name"] == "product_plan"


def test_workflow_runs_with_no_video():
    result = WorkflowEngine().run_project(P(), sample_count=4)
    assert result["job_id"]
    assert result["state"]["progress"] >= 80
    assert "product_plan" in result["outputs"]


def test_job_queue_add(tmp_path):
    q = JobQueue(path=str(tmp_path / "jobs.json"))
    job = q.add(1, "테스트")
    assert job["status"] == "queued"
    assert len(q.load()) == 1


def test_pipeline_state(tmp_path):
    s = PipelineState(base_dir=str(tmp_path))
    s.create("abc", "테스트", [{"name": "a", "status": "pending"}])
    s.update_step("abc", "a", "done", {"ok": True})
    data = s.load("abc")
    assert data["progress"] == 100
