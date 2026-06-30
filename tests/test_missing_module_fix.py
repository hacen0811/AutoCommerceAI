from pathlib import Path


def test_missing_real_vision_mvp_removed():
    main = Path("main.py").read_text(encoding="utf-8")
    assert "real_vision_mvp" not in main
    assert "show_real_vision_mvp" not in main


def test_shorts_studio_route_exists():
    main = Path("main.py").read_text(encoding="utf-8")
    assert '"🎞️ 쇼츠 스튜디오 3.0": show_shorts_studio' in main
