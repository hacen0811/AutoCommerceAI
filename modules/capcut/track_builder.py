from modules.capcut.uuid_helper import new_uuid


class CapCutTrackBuilder:
    """
    Sprint 39
    실제 CapCut draft_content.json 구조에 맞춘 Track Builder.

    역할:
    - video track 생성
    - text track 생성
    - segment 목록 연결
    """

    def build_video_track(self, segments):
        return self._build_track(
            track_type="video",
            segments=segments,
            render_index=0,
        )

    def build_text_track(self, segments):
        return self._build_track(
            track_type="text",
            segments=segments,
            render_index=1,
        )

    def build_tracks(self, video_segments=None, text_segments=None):
        tracks = []

        if video_segments:
            tracks.append(self.build_video_track(video_segments))

        if text_segments:
            tracks.append(self.build_text_track(text_segments))

        return tracks

    def _build_track(self, track_type, segments, render_index=0):
        clean_segments = []

        for segment in segments or []:
            if isinstance(segment, dict):
                segment["track_render_index"] = render_index
                clean_segments.append(segment)

        return {
            "id": new_uuid(),
            "type": track_type,
            "segments": clean_segments,
            "flag": 0,
            "attribute": 0,
            "name": "",
            "is_default_name": True,
        }