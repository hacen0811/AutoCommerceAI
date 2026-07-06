import json

from modules.capcut.uuid_helper import new_uuid


class CapCutTextBuilder:
    """
    Sprint 39
    실제 CapCut text material 구조에 맞춘 Text Builder.

    역할:
    - 텍스트 material 생성
    - CapCut content JSON 문자열 생성
    - 자막 스타일 기본값 적용
    """

    def build_text_material(self, scene):
        text = (
            scene.get("caption")
            or scene.get("text")
            or scene.get("purpose")
            or ""
        )

        material_id = new_uuid()

        return {
            "recognize_task_id": "",
            "id": material_id,
            "name": "",
            "recognize_text": "",
            "recognize_model": "",
            "punc_model": "",
            "type": "text",
            "content": self._build_content(text),
            "base_content": "",
            "words": {
                "start_time": [],
                "end_time": [],
                "text": [],
            },
            "current_words": {
                "start_time": [],
                "end_time": [],
                "text": [],
            },
            "global_alpha": 1.0,
            "combo_info": {
                "text_templates": [],
            },
            "caption_template_info": {
                "resource_id": "",
                "third_resource_id": "",
                "resource_name": "",
                "category_id": "",
                "category_name": "",
                "effect_id": "",
                "request_id": "",
                "path": "",
                "is_new": False,
                "source_platform": 0,
            },
            "layer_weight": 1,
            "letter_spacing": 0.0,
            "text_curve": None,
            "text_loop_on_path": False,
            "offset_on_path": 0.0,
            "enable_path_typesetting": False,
            "text_exceeds_path_process_type": 0,
            "text_typesetting_paths": None,
            "text_typesetting_paths_file": "",
            "text_typesetting_path_index": 0,
            "line_spacing": 0.02,
            "has_shadow": True,
            "shadow_color": "#000000",
            "shadow_alpha": 0.35,
            "shadow_smoothing": 0.45,
            "shadow_distance": 5.0,
            "shadow_point": {
                "x": 0.6363961030678928,
                "y": -0.6363961030678928,
            },
            "shadow_angle": -45.0,
            "shadow_thickness_projection_enable": False,
            "shadow_thickness_projection_angle": 0.0,
            "shadow_thickness_projection_distance": 0.0,
            "border_alpha": 1.0,
            "border_color": "#000000",
            "border_width": 0.08,
            "border_mode": 0,
            "style_name": "",
            "text_color": "#FFFFFF",
            "text_alpha": 1.0,
            "font_name": "",
            "font_title": "none",
            "font_size": 17.0,
            "font_path": "",
            "font_id": "",
            "font_resource_id": "",
            "initial_scale": 1.0,
            "font_url": "",
            "typesetting": 0,
            "alignment": 1,
            "line_feed": 1,
            "use_effect_default_color": True,
            "is_rich_text": False,
            "shape_clip_x": False,
            "shape_clip_y": False,
            "ktv_color": "",
            "text_to_audio_ids": [],
            "bold_width": 0.0,
            "italic_degree": 0,
            "underline": False,
            "underline_width": 0.05,
            "underline_offset": 0.22,
            "sub_type": 0,
            "check_flag": 47,
            "text_size": 30,
            "font_category_name": "",
            "font_source_platform": 1,
            "font_third_resource_id": "",
            "font_category_id": "",
            "add_type": 0,
            "operation_type": 0,
            "recognize_type": 0,
            "fonts": [],
            "background_color": "",
            "background_alpha": 1.0,
            "background_style": 0,
            "background_round_radius": 0.0,
            "background_width": 0.14,
            "background_height": 0.14,
            "background_vertical_offset": 0.0,
            "background_horizontal_offset": 0.0,
            "background_fill": "",
            "single_char_bg_enable": False,
            "single_char_bg_color": "",
            "single_char_bg_alpha": 1.0,
            "single_char_bg_round_radius": 0.3,
            "single_char_bg_width": 0.0,
            "single_char_bg_height": 0.0,
            "single_char_bg_vertical_offset": 0.0,
            "single_char_bg_horizontal_offset": 0.0,
            "font_team_id": "",
            "tts_auto_update": False,
            "text_preset_resource_id": "",
            "group_id": "",
            "preset_id": "",
            "preset_name": "",
            "preset_category": "",
            "preset_category_id": "",
            "preset_index": 0,
            "preset_has_set_alignment": False,
            "force_apply_line_max_width": False,
            "language": "",
            "relevance_segment": [],
            "original_size": [],
            "fixed_width": -1.0,
            "fixed_height": -1.0,
            "line_max_width": 0.82,
            "oneline_cutoff": False,
            "cutoff_postfix": "",
            "subtitle_template_original_fontsize": 0.0,
            "subtitle_keywords": None,
            "inner_padding": -1.0,
            "multi_language_current": "none",
            "source_from": "",
            "is_lyric_effect": False,
            "lyric_group_id": "",
            "lyrics_template": {
                "resource_id": "",
                "resource_name": "",
                "panel": "",
                "effect_id": "",
                "path": "",
                "category_id": "",
                "category_name": "",
                "request_id": "",
            },
            "is_batch_replace": False,
            "is_words_linear": False,
            "ssml_content": "",
            "subtitle_keywords_config": None,
            "sub_template_id": -1,
            "translate_original_text": "",
        }

    def build_text_materials(self, scenes):
        materials = []

        for scene in scenes or []:
            if not isinstance(scene, dict):
                continue

            text = (
                scene.get("caption")
                or scene.get("text")
                or scene.get("purpose")
                or ""
            )

            if text:
                materials.append(self.build_text_material(scene))

        return materials

    def _build_content(self, text):
        content = {
            "text": str(text or ""),
            "styles": [
                {
                    "fill": {
                        "content": {
                            "render_type": "solid",
                            "solid": {
                                "color": [1, 1, 1],
                            },
                        },
                    },
                    "strokes": [
                        {
                            "content": {
                                "render_type": "solid",
                                "solid": {
                                    "color": [0, 0, 0],
                                },
                            },
                            "width": 0.08,
                            "mode": 0,
                        }
                    ],
                    "size": 17,
                    "shadows": [
                        {
                            "thickness_projection_angle": -45,
                            "thickness_projection_enable": False,
                            "diffuse": 0.025,
                            "alpha": 0.35,
                            "distance": 5.0,
                            "content": {
                                "render_type": "solid",
                                "solid": {
                                    "color": [0, 0, 0],
                                },
                            },
                            "angle": -45,
                            "thickness_projection_distance": 0,
                        }
                    ],
                    "range": [0, len(str(text or ""))],
                }
            ],
        }

        return json.dumps(content, ensure_ascii=False)