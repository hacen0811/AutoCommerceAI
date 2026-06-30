from modules.source.source_video_engine import SourceVideoEngine
from modules.source.video_ranker import SourceVideoRanker


class P:
    product_name = "문틈 방충망"
    keyword = "방충망"
    video_path = ""


def test_search_plan_contains_queries():
    plan = SourceVideoEngine().make_search_plan(P())
    assert "taobao" in plan["search_queries"]
    assert "douyin" in plan["search_queries"]


def test_platform_detection():
    e = SourceVideoEngine()
    assert e.detect_platform("https://www.douyin.com/video/123") == "douyin"
    assert e.detect_platform("https://item.taobao.com/item.htm?id=1") == "taobao"


def test_ranker_empty():
    ranked = SourceVideoRanker().rank([])
    assert ranked == []
