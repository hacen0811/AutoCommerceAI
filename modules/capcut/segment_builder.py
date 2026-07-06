from modules.capcut.uuid_helper import new_uuid


class CapCutSegmentBuilder:
    """
    Sprint 41
    CapCut Segment Builder.

    역할:
    - video segment 생성
    - text segment 생성
    - material_id 연결
    - target/source timerange 구성
    - TrackBuilder가 사용할 segment 단위 결과만 생성
    """

    def build_video_segment(self, scene, material_id):
        start_us, duration_us = self._timerange(scene)

        return self._base_segment(
            segment_type="video",
            material_id=material_id,
            start_us=start_us,
            duration_us=duration_us,
            render_index=0,
            track_render_index=0,
            extra_material_refs=[],
        )

    def build_text_segment(self, scene, material_id, animation_id=None):
        start_us, duration_us = self._timerange(scene)

        extra_refs = []
        if animation_id:
            extra_refs.append(animation_id)

        segment = self._base_segment(
            segment_type="text",
            material_id=material_id,
            start_us=start_us,
            duration_us=duration_us,
            render_index=14000,
            track_render_index=1,
            extra_material_refs=extra_refs,
        )

        segment["source_timerange"] = None
        segment["clip"]["transform"]["y"] = -0.11527377521613837

        return segment

    def _base_segment(
        self,
        segment_type,
        material_id,
        start_us,
        duration_us,
        render_index,
        track_render_index,
        extra_material_refs=None,
    ):
        is_video = segment_type == "video"

        return {
            "id": new_uuid(),
            "source_timerange": {
                "start": 0,
                "duration": duration_us,
            },
            "target_timerange": {
                "start": start_us,
                "duration": duration_us,
            },
            "render_timerange": {
                "start": 0,
                "duration": 0,
            },
            "desc": "",
            "state": 0,
            "speed": 1.0,
            "is_loop": False,
            "is_tone_modify": False,
            "reverse": False,
            "intensifies_audio": False,
            "cartoon": False,
            "volume": 1.0,
            "last_nonzero_volume": 1.0,
            "clip": {
                "scale": {
                    "x": 1.0,
                    "y": 1.0,
                },
                "rotation": 0.0,
                "transform": {
                    "x": 0.0,
                    "y": 0.0,
                },
                "flip": {
                    "vertical": False,
                    "horizontal": False,
                },
                "alpha": 1.0,
            },
            "uniform_scale": {
                "on": True,
                "value": 1.0,
            },
            "material_id": material_id,
            "extra_material_refs": extra_material_refs or [],
            "render_index": render_index,
            "keyframe_refs": [],
            "enable_lut": is_video,
            "enable_adjust": is_video,
            "enable_hsl": False,
            "visible": True,
            "group_id": "",
            "enable_color_curves": True,
            "enable_hsl_curves": True,
            "track_render_index": track_render_index,
            "hdr_settings": self._hdr_settings() if is_video else None,
            "enable_color_wheels": True,
            "track_attribute": 0,
            "is_placeholder": False,
            "template_id": "",
            "enable_smart_color_adjust": False,
            "template_scene": "default",
            "common_keyframes": [],
            "caption_info": None,
            "responsive_layout": {
                "enable": False,
                "target_follow": "",
                "size_layout": 0,
                "horizontal_pos_layout": 0,
                "vertical_pos_layout": 0,
            },
            "enable_color_match_adjust": False,
            "enable_color_correct_adjust": False,
            "enable_adjust_mask": False,
            "raw_segment_id": "",
            "lyric_keyframes": None,
            "enable_video_mask": True,
            "digital_human_template_group_id": "",
            "color_correct_alg_result": "",
            "source": "segmentsourcenormal",
            "enable_mask_stroke": False,
            "enable_mask_shadow": False,
            "enable_color_adjust_pro": False,
        }

    def _timerange(self, scene):
        start_us = self._to_microseconds(scene.get("start", "00.0"))
        end_us = self._to_microseconds(scene.get("end", "03.0"))

        if end_us <= start_us:
            end_us = start_us + 3_000_000

        return start_us, end_us - start_us

    def _hdr_settings(self):
        return {
            "mode": 1,
            "intensity": 1.0,
            "nits": 1000,
        }

    def _to_microseconds(self, value):
        try:
            text = str(value).replace("초", "").replace("s", "").strip()
            return int(float(text) * 1_000_000)
        except Exception:
            return 0