from modules.system.data_migration import DataMigration


def test_data_migration_inspect_missing(tmp_path):
    result = DataMigration(current_root=tmp_path).inspect_previous(tmp_path / "missing")
    assert result["exists"] is False


def test_data_migration_import_db_and_video(tmp_path):
    prev = tmp_path / "prev"
    cur = tmp_path / "cur"
    (prev / "database").mkdir(parents=True)
    (prev / "assets" / "videos").mkdir(parents=True)
    (prev / "database" / "autocommerce_x.db").write_bytes(b"db")
    (prev / "assets" / "videos" / "a.mp4").write_bytes(b"video")
    result = DataMigration(current_root=cur).import_data(prev)
    assert result["ok"] is True
    assert (cur / "database" / "autocommerce_x.db").exists()
    assert (cur / "assets" / "videos" / "a.mp4").exists()
