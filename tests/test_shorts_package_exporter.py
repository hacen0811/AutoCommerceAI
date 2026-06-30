from pathlib import Path
from modules.studio.shorts_package_exporter import ShortsPackageExporter


def test_exporter_saves_files(tmp_path, monkeypatch):
    # Override exporter directory after construction
    pkg = {
        "project": {"name": "테스트"},
        "product": {"name": "주방 정리대", "keyword": "정리", "taobao_keyword": "厨房 收纳架", "douyin_keyword": "厨房 收纳架 使用", "taobao_top10": [], "douyin_top10": []},
        "scripts": {"15s": [], "25s": []},
        "capcut": {"timeline": []},
        "youtube": {},
        "instagram": {},
        "thumbnail": {},
    }
    exporter = ShortsPackageExporter()
    exporter.out_dir = tmp_path
    result = exporter.save(pkg)
    assert Path(result["json"]).exists()
    assert Path(result["txt"]).exists()
    assert Path(result["md"]).exists()
