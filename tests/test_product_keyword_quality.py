from modules.product.product_title_engine import ProductTitleEngine
from modules.product.search_keyword_engine import SearchKeywordEngine
from modules.product.product_engine import ProductEngine


TITLE = "주방 정리대 양념통 정리대 코너 주방 슬라이딩 수납장 다층 선반 조리도구 걸이 냄비뚜껑 거치대"


def test_title_engine_short_title():
    data = ProductTitleEngine().improve("쿠팡상품", TITLE)
    assert "주방" in data["short_title"]
    assert data["is_placeholder"] is True


def test_keyword_engine_kitchen_top10():
    data = SearchKeywordEngine().generate(TITLE)
    assert len(data["taobao_top10"]) == 10
    assert len(data["douyin_top10"]) == 10
    assert data["comment_keyword"] == "정리"
    assert "厨房" in data["taobao_keyword"]


def test_product_engine_manual_title():
    url = "https://www.coupang.com/vp/products/9430023509?itemId=28036458604&vendorItemId=94993820562"
    built = ProductEngine().build_from_coupang(url, product_name="쿠팡상품", manual_product_name=TITLE)
    assert "주방" in built["project_payload"]["product_name"]
    assert built["project_payload"]["keyword"] == "정리"
    assert built["keywords"]["taobao_top10"][0]["query"] == "厨房 调料收纳架 抽拉式"
