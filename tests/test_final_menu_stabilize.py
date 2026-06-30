from pathlib import Path
import re

from modules.system.menu_route_checker import MenuRouteChecker


def test_menu_routes_complete():
    result = MenuRouteChecker(root=Path.cwd()).check()
    assert result["ok"] is True, result


def test_project_recovery_route_exists():
    main = Path("main.py").read_text(encoding="utf-8")
    assert '"🧩 프로젝트 빠른 복구"' in main
    assert '"🧩 프로젝트 빠른 복구": show_project_recovery' in main
    assert "from app.ui.project_recovery import show_project_recovery" in main


def test_critical_routes_exist():
    main = Path("main.py").read_text(encoding="utf-8")
    for route in [
        '"🎞️ 쇼츠 스튜디오 3.0": show_shorts_studio',
        '"📦 데이터 가져오기": show_data_migration',
        '"💾 백업/복원": show_backup_restore',
        '"🧰 시스템 체크": show_system_check',
    ]:
        assert route in main
