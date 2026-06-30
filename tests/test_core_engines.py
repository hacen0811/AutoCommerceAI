from modules.product.coupang_product_engine import CoupangProductEngine
from modules.editor.auto_editor_engine import AutoEditorEngine
from modules.pipeline.real_vision_pipeline import RealVisionPipeline


def test_coupang_parse():
    url = "https://www.coupang.com/vp/products/9067798449?vendorItemId=93562341136&x=1"
    parsed = CoupangProductEngine().parse(url)
    assert parsed["product_id"] == "9067798449"
    assert parsed["vendor_item_id"] == "93562341136"


def test_capcut_voice_db():
    plan = AutoEditorEngine().create_plan("문틈 방충망", "방충망")
    assert plan["capcut_preset"]["voice"] == "20 dB"


def test_real_vision_no_video():
    class P:
        id = 1
        product_name = "문틈 방충망"
        keyword = "방충망"
        video_path = ""

    result = RealVisionPipeline().run(P())
    assert "원본 영상" in result["summary"]
