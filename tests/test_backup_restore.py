from modules.system.auto_migration import AutoMigration
from modules.system.project_backup import ProjectBackup


def test_auto_migration_empty(tmp_path):
    assert AutoMigration().find_candidates(base=tmp_path) == []


def test_project_backup_latest_empty(tmp_path):
    b = ProjectBackup(root=tmp_path)
    assert b.latest_backup() == ""
