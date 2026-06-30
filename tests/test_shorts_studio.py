from modules.studio.shorts_studio_engine import ShortsStudioEngine


def test_shorts_studio_missing_url():
    result = ShortsStudioEngine().build_package("", "상품명")
    assert result["ok"] is False


def test_shorts_studio_missing_name():
    result = ShortsStudioEngine().build_package("https://www.coupang.com/vp/products/1", "")
    assert result["ok"] is False
