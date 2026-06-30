from io import BytesIO
from pathlib import Path

from modules.project.project_selector import ProjectSelector
from modules.video.service import VideoService


class FakeUpload(BytesIO):
    def __init__(self, name, data):
        super().__init__(data)
        self.name = name


def test_project_selector_labels_empty():
    labels = ProjectSelector().labels([])
    assert labels == {}


def test_video_service_saves_nonzero_file():
    upload = FakeUpload("test.mp4", b"abc123")
    path = VideoService().save_uploaded_video(upload)
    assert Path(path).exists()
    assert Path(path).stat().st_size == 6
