import json
from pathlib import Path

from modules.capcut.uuid_helper import new_uuid


class CapCutMaterialBuilder:
    """
    Sprint 42-2
    CapCut Material Builder.

    역할:
    - video material 생성
    - text material 생성
    - 실제 CapCut 샘플 기반 material registry 구조 보강
    - 기존 build_materials(scenes) 인터페이스 유지
    """

    def build_video_material(self, scene):
        source = scene.get("candidate") or scene.get("url") or ""
        path = Path(source)

        return {
            "id": new_uuid(),
            "unique_id": "",
            "type": "video",
            "duration": self._duration(scene),
            "path": str(path),
            "media_path": "",
            "local_id": "",
            "has_audio": False,
            "reverse_path": "",
            "intensifies_path": "",
            "reverse_intensifies_path": "",
            "intensifies_audio_path": "",
            "cartoon_path": "",
            "width": 1080,
            "height": 1920,
            "category_id": "",
            "category_name": "",
            "material_id": "",
            "material_name": path.name if path.name else "",
            "material_url": "",
            "crop": {
                "upper_left_x": 0.0,
                "upper_left_y": 0.0,
                "upper_right_x": 1.0,
                "upper_right_y": 0.0,
                "lower_left_x": 0.0,
                "lower_left_y": 1.0,
                "lower_right_x": 1.0,
                "lower_right_y": 1.0,
            },
            "crop_ratio": "free",
            "audio_fade": None,
            "crop_scale": 1.0,
            "extra_type_option": 0,
            "stable": {
                "stable_level": 0,
                "matrix_path": "",
                "time_range": {
                    "start": 0,
                    "duration": 0,
                },
            },
            "matting": {
                "flag": 0,
                "path": "",
                "interactiveTime": [],
                "has_use_quick_brush": False,
                "strokes": [],
                "has_use_quick_eraser": False,
                "expansion": 0,
                "feather": 0,
                "reverse": False,
                "custom_matting_id": "",
                "enable_matting_stroke": False,
                "is_clould": False,
                "mask_video_path": "",
                "cloud_product_fps": 0.0,
            },
            "source": 0,
            "source_platform": 0,
            "formula_id": "",
            "check_flag": 0,
            "video_algorithm": {
                "algorithms": [],
                "time_range": None,
                "path": "",
                "gameplay_configs": [],
                "ai_in_painting_config": [],
                "complement_frame_config": None,
                "motion_blur_config": None,
                "deflicker": None,
                "noise_reduction": None,
                "quality_enhance": None,
                "super_resolution": None,
                "ai_background_configs": [],
                "smart_complement_frame": None,
                "aigc_generate": None,
                "aigc_generate_list": [],
                "mouth_shape_driver": None,
                "ai_expression_driven": None,
                "ai_motion_driven": None,
                "image_interpretation": None,
                "story_video_modify_video_config": {
                    "task_id": "",
                    "is_overwrite_last_video": False,
                    "tracker_task_id": "",
                    "generate_id": "",
                    "generate_card_id": "",
                },
                "skip_algorithm_index": [],
            },
            "is_unified_beauty_mode": False,
            "is_set_beauty_mode": False,
            "object_locked": None,
            "smart_motion": None,
            "multi_camera_info": None,
            "freeze": None,
            "picture_from": "none",
            "picture_set_category_id": "",
            "picture_set_category_name": "",
            "team_id": "",
            "local_material_id": "",
            "origin_material_id": "",
            "request_id": "",
            "has_sound_separated": False,
            "is_text_edit_overdub": False,
            "is_ai_generate_content": False,
            "aigc_type": "none",
            "is_copyright": False,
            "aigc_history_id": "",
            "aigc_item_id": "",
            "local_material_from": "",
            "smart_match_info": None,
            "beauty_face_preset_infos": [],
            "beauty_body_preset_id": "",
            "beauty_face_auto_preset": {
                "preset_id": "",
                "name": "",
                "rate_map": "",
                "scene": "",
            },
            "beauty_face_auto_preset_infos": [],
            "beauty_body_auto_preset": None,
            "live_photo_timestamp": -1,
            "live_photo_cover_path": "",
            "content_feature_info": None,
            "corner_pin": None,
            "surface_trackings": [],
            "video_mask_stroke": {
                "resource_id": "",
                "path": "",
                "type": "",
                "color": "",
                "size": 0.0,
                "alpha": 0.0,
                "distance": 0.0,
                "texture": 0.0,
                "horizontal_shift": 0.0,
                "vertical_shift": 0.0,
            },
            "video_mask_shadow": {
                "resource_id": "",
                "path": "",
                "color": "",
                "alpha": 0.0,
                "blur": 0.0,
                "distance": 0.0,
                "angle": 0.0,
            },
        }

    def build_text_material(self, scene):
        text = (
            scene.get("caption")
            or scene.get("text")
            or scene.get("purpose")
            or ""
        )

        return {
            "recognize_task_id": "",
            "id": new_uuid(),
            "name": "",
            "recognize_text": "",
            "recognize_model": "",
            "punc_model": "",
            "type": "text",
            "content": self._rich_text_content(text),
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
            "font_size": 30.0,
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
            "font_source_platform": 0,
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

    def build_materials(self, scenes):
        videos = []
        texts = []

        for scene in scenes or []:
            videos.append(self.build_video_material(scene))
            texts.append(self.build_text_material(scene))

        return self.build_registry(
            videos=videos,
            texts=texts,
        )

    def build_registry(self, videos=None, texts=None):
        return {
            "flowers": [],
            "videos": videos or [],
            "tail_leaders": [],
            "audios": [],
            "images": [],
            "texts": texts or [],
            "effects": [],
            "stickers": [],
            "canvases": [self._canvas_material()],
            "transitions": [],
            "audio_effects": [],
            "audio_fades": [],
            "beats": [],
            "material_animations": [self._material_animation()],
            "animations": [],
            "placeholders": [],
            "placeholder_infos": [self._placeholder_info()],
            "speeds": [self._speed_material()],
            "common_mask": [],
            "chromas": [],
            "text_templates": [],
            "realtime_denoises": [],
            "audio_pannings": [],
            "audio_pitch_shifts": [],
            "video_trackings": [],
            "hsl": [],
            "drafts": [],
            "color_curves": [],
            "hsl_curves": [],
            "primary_color_wheels": [],
            "log_color_wheels": [],
            "video_effects": [],
            "ai_text_effects": [],
            "audio_balances": [],
            "handwrites": [],
            "manual_deformations": [],
            "manual_beautys": [],
            "plugin_effects": [],
            "sound_channel_mappings": [self._sound_channel_mapping()],
            "green_screens": [],
            "shapes": [],
            "material_colors": [self._material_color()],
            "digital_humans": [],
            "digital_human_model_dressing": [],
            "smart_crops": [],
            "ai_translates": [],
            "audio_track_indexes": [],
            "loudnesses": [self._loudness()],
            "vocal_beautifys": [],
            "vocal_separations": [self._vocal_separation()],
            "smart_relights": [],
            "time_marks": [],
            "multi_language_refs": [],
            "video_shadows": [],
            "video_strokes": [],
            "video_radius": [],
        }

    def _rich_text_content(self, text):
        content = {
            "text": text,
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
                        },
                    ],
                    "size": 30,
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
                        },
                    ],
                    "range": [0, len(text)],
                },
            ],
        }

        return json.dumps(content, ensure_ascii=False)

    def _canvas_material(self):
        return {
            "id": new_uuid(),
            "type": "canvas_color",
            "color": "",
            "blur": 0.0,
            "image": "",
            "album_image": "",
            "image_id": "",
            "image_name": "",
            "source_platform": 0,
            "team_id": "",
        }

    def _material_animation(self):
        return {
            "id": new_uuid(),
            "type": "sticker_animation",
            "animations": [],
            "multi_language_current": "none",
        }

    def _placeholder_info(self):
        return {
            "id": new_uuid(),
            "type": "placeholder_info",
            "meta_type": "none",
            "res_path": "",
            "res_text": "",
            "error_path": "",
            "error_text": "",
        }

    def _speed_material(self):
        return {
            "id": new_uuid(),
            "type": "speed",
            "mode": 0,
            "speed": 1.0,
            "curve_speed": None,
        }

    def _sound_channel_mapping(self):
        return {
            "id": new_uuid(),
            "type": "none",
            "audio_channel_mapping": 0,
            "is_config_open": False,
        }

    def _material_color(self):
        return {
            "id": new_uuid(),
            "is_color_clip": False,
            "is_gradient": False,
            "solid_color": "",
            "gradient_colors": [],
            "gradient_percents": [],
            "gradient_angle": 90.0,
            "width": 0.0,
            "height": 0.0,
        }

    def _loudness(self):
        return {
            "id": new_uuid(),
            "enable": False,
            "time_range": None,
            "file_id": "",
            "target_loudness": 0.0,
            "loudness_param": None,
        }

    def _vocal_separation(self):
        return {
            "id": new_uuid(),
            "type": "vocal_separation",
            "choice": 0,
            "removed_sounds": [],
            "time_range": None,
            "production_path": "",
            "final_algorithm": "",
            "enter_from": "",
        }

    def _duration(self, scene):
        try:
            start = float(str(scene.get("start", "0")).replace("초", ""))
            end = float(str(scene.get("end", "3")).replace("초", ""))

            if end <= start:
                return 3_000_000

            return int((end - start) * 1_000_000)
        except Exception:
            return 3_000_000