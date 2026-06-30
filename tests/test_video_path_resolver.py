from modules.video.video_path_resolver import VideoPathResolver


class P:
    id = None
    title = "테스트"
    product_name = ""
    video_path = ""


def test_video_path_resolver_empty():
    data = VideoPathResolver().debug(P())
    assert data["title"] == "테스트"
    assert data["exists"] is False
