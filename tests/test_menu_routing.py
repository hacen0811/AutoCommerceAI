from pathlib import Path


def test_main_menu_routes_are_distinct():
    main = Path("main.py").read_text(encoding="utf-8")
    assert '"🎞️ 쇼츠 스튜디오 3.0": show_shorts_studio' in main
    assert '"📦 데이터 가져오기": show_data_migration' in main
    assert '"💾 백업/복원": show_backup_restore' in main
    assert '"🧩 프로젝트 빠른 복구": show_project_recovery' in main


def test_no_bad_tuple_elif_left():
    main = Path("main.py").read_text(encoding="utf-8")
    assert 'elif menu ==' not in main
    assert 'ROUTES = {' in main


def test_no_known_missing_modules_imported():
    main = Path("main.py").read_text(encoding="utf-8")
    assert "real_vision_mvp" not in main
    assert "model_setup" not in main
    assert "shopping_shorts_ai" not in main
