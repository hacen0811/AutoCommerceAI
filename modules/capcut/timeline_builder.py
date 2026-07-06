from modules.capcut.track_builder import CapCutTrackBuilder


class CapCutTimelineBuilder:
    """
    Sprint 41

    Timeline Builder

    역할
    - TrackBuilder를 이용하여 Timeline 생성
    - Timeline 조회
    - Timeline 유효성 검사

    원칙
    - Timeline은 Track만 관리
    - Segment 생성은 SegmentBuilder
    - Track 생성은 TrackBuilder
    """

    def __init__(self):
        self.track_builder = CapCutTrackBuilder()

    def build(
        self,
        video_segments=None,
        text_segments=None,
    ):
        tracks = self.track_builder.build_tracks(
            video_segments=video_segments or [],
            text_segments=text_segments or [],
        )

        return self._timeline(tracks)

    def build_empty(self):
        return self._timeline([])

    def has_tracks(self, timeline):
        return bool(self.tracks(timeline))

    def tracks(self, timeline):
        if not isinstance(timeline, dict):
            return []

        tracks = timeline.get("tracks")

        if isinstance(tracks, list):
            return tracks

        return []

    def video_track(self, timeline):
        return self._find_track(
            timeline,
            "video",
        )

    def text_track(self, timeline):
        return self._find_track(
            timeline,
            "text",
        )

    def add_track(
        self,
        timeline,
        track,
    ):
        timeline = timeline or self.build_empty()

        if not isinstance(track, dict):
            return timeline

        timeline.setdefault("tracks", [])
        timeline["tracks"].append(track)

        return timeline

    def track_count(self, timeline):
        return len(self.tracks(timeline))

    def _timeline(self, tracks):
        return {
            "tracks": tracks,
        }

    def _find_track(
        self,
        timeline,
        track_type,
    ):
        for track in self.tracks(timeline):
            if track.get("type") == track_type:
                return track

        return None