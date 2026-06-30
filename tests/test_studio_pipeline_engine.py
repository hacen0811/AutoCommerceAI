from modules.studio.studio_pipeline_engine import StudioPipelineEngine


def test_studio_pipeline_missing_url():
    result = StudioPipelineEngine().run("", "상품명", run_one_click=False)
    assert result["ok"] is False


def test_studio_pipeline_missing_name():
    result = StudioPipelineEngine().run("https://www.coupang.com/vp/products/1", "", run_one_click=False)
    assert result["ok"] is False
