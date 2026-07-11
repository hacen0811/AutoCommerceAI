from modules.capcut.material_builder import CapCutMaterialBuilder
from modules.capcut.segment_builder import CapCutSegmentBuilder
from modules.capcut.track_builder import CapCutTrackBuilder


class CapCutTimelineBuilder:
    """
    Sprint 43-3

    Timeline Builder

    역할:
    - ProjectBuilder가 호출하는 build_timeline(scenes) 제공
    - MaterialBuilder가 만든 materials.videos[].id를 segment.material_id로 연결
    - SegmentBuilder로 video/text segment 생성
    - TrackBuilder로 tracks 조립
    """

    def __init__(self):
        self.material_builder = CapCutMaterialBuilder()
        self.segment_builder = CapCutSegmentBuilder()
        self.track_builder = CapCutTrackBuilder()

    def build_timeline(self, scenes, materials=None):
        scenes = [scene for scene in scenes or [] if isinstance(scene, dict)]

        if not isinstance(materials, dict):
            materials = self.material_builder.build_materials(scenes)
        videos = materials.get("videos", [])
        texts = materials.get("texts", [])

        video_segments = []
        text_segments = []

        for idx, scene in enumerate(scenes):
            video_material_id = self._material_id_at(videos, idx)
            text_material_id = self._material_id_at(texts, idx)

            if video_material_id:
                video_segments.append(
                    self.segment_builder.build_video_segment(
                        scene=scene,
                        material_id=video_material_id,
                    )
                )

            if text_material_id:
                text_segments.append(
                    self.segment_builder.build_text_segment(
                        scene=scene,
                        material_id=text_material_id,
                    )
                )

        tracks = self.track_builder.build_tracks(
            video_segments=video_segments,
            text_segments=text_segments,
        )

        return {
            "tracks": tracks,
        }

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

    def _material_id_at(self, materials, idx):
        try:
            material = materials[idx]
            if isinstance(material, dict):
                return material.get("id")
        except Exception:
            return None

        return None