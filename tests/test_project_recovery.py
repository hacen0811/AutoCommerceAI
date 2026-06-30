from modules.system.project_recovery import ProjectRecovery


def test_project_recovery_requires_url():
    result = ProjectRecovery().rebuild("", "상품명")
    assert result["ok"] is False


def test_project_recovery_requires_name():
    result = ProjectRecovery().rebuild("https://www.coupang.com/vp/products/1", "")
    assert result["ok"] is False
