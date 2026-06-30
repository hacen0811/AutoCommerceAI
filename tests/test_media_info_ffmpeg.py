from modules.system.ffmpeg_checker import FFmpegChecker
from modules.video.media_info import MediaInfo
from modules.video.analyzer import VideoAnalyzer


def test_ffmpeg_checker_shape():
    data = FFmpegChecker().check()
    assert "ffmpeg_ok" in data
    assert "ffprobe_ok" in data


def test_media_info_empty():
    data = MediaInfo().analyze("")
    assert data["ok"] is False


def test_video_analyzer_empty_has_safe_area():
    data = VideoAnalyzer().analyze("")
    assert "safe_area" in data
    assert "edit_risk" in data
