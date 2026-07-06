from modules.capcut.uuid_helper import new_uuid


class CapCutTrackBuilder:
    """
    Sprint 41

    역할
    - Video Track 생성
    - Text Track 생성
    - Segment를 Track으로 조립
    - Track 관련 메타데이터 관리

    원칙
    - Segment 생성은 SegmentBuilder 담당
    - TrackBuilder는 Segment를 묶기만 한다.
    """

    VIDEO_RENDER_INDEX = 0
    TEXT_RENDER_INDEX = 1

    def build_video_track(self, segments):
        return self._build_track(
            track_type="video",
            segments=segments,
            render_index=self.VIDEO_RENDER_INDEX,
        )

    def build_text_track(self, segments):
        return self._build_track(
            track_type="text",
            segments=segments,
            render_index=self.TEXT_RENDER_INDEX,
        )

    def build_tracks(
        self,
        video_segments=None,
        text_segments=None,
    ):
        tracks = []

        video_track = self._optional_track(
            self.build_video_track,
            video_segments,
        )

        if video_track:
            tracks.append(video_track)

        text_track = self._optional_track(
            self.build_text_track,
            text_segments,
        )

        if text_track:
            tracks.append(text_track)

        return tracks

    def _optional_track(self, builder, segments):
        if not segments:
            return None
        return builder(segments)

    def _build_track(
        self,
        track_type,
        segments,
        render_index,
    ):
        clean_segments = self._normalize_segments(
            segments,
            render_index,
        )

        return {
            "id": new_uuid(),
            "type": track_type,
            "segments": clean_segments,
            "flag": 0,
            "attribute": 0,
            "name": "",
            "is_default_name": True,
            "render_index": render_index,
            "visible": True,
            "locked": False,
        }

    def _normalize_segments(
        self,
        segments,
        render_index,
    ):
        normalized = []

        for segment in segments or []:
            if not isinstance(segment, dict):
                continue

            item = dict(segment)
            item["track_render_index"] = render_index

            normalized.append(item)

        return normalized