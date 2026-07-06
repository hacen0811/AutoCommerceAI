from modules.capcut.track_builder import CapCutTrackBuilder


class CapCutTimelineBuilder:
    """
    Sprint 39

    Timeline Builder

    역할
    - Video Track 생성
    - Text Track 생성
    - CapCut timeline(tracks) 조립
    """

    def __init__(self):
        self.track_builder = CapCutTrackBuilder()

    def build(
        self,
        video_segments=None,
        text_segments=None,
    ):
        video_segments = video_segments or []
        text_segments = text_segments or []

        tracks = self.track_builder.build_tracks(
            video_segments=video_segments,
            text_segments=text_segments,
        )

        return {
            "tracks": tracks
        }

    def build_empty(self):
        return {
            "tracks": []
        }

    def has_tracks(self, timeline):
        if not isinstance(timeline, dict):
            return False

        return bool(timeline.get("tracks"))

    def video_track(self, timeline):
        if not isinstance(timeline, dict):
            return None

        for track in timeline.get("tracks", []):
            if track.get("type") == "video":
                return track

        return None

    def text_track(self, timeline):
        if not isinstance(timeline, dict):
            return None

        for track in timeline.get("tracks", []):
            if track.get("type") == "text":
                return track

        return None