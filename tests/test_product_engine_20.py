from modules.product.product_engine import ProductEngine
from modules.product.search_keyword_engine import SearchKeywordEngine


def test_product_engine_parse_and_keywords():
    url = "https://www.coupang.com/vp/products/9067798449?vendorItemId=93562341136&sourceType=HOME"
    built = ProductEngine().build_from_coupang(url, product_name="문틈 방충망")
    assert built["parsed"]["product_id"] == "9067798449"
    assert built["parsed"]["vendor_item_id"] == "93562341136"
    assert "防" in built["keywords"]["taobao_keyword"] or "纱窗" in built["keywords"]["taobao_keyword"]
    assert built["project_payload"]["keyword"] == "방충망"


def test_search_keyword_engine_shoe_dryer():
    data = SearchKeywordEngine().generate("장마철 신발건조기")
    assert data["comment_keyword"] in ["신발", "신발건조기"]
    assert data["taobao_keyword"]
    assert data["douyin_keyword"]
