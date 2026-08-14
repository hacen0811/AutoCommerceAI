from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = ImageDraw = ImageFont = None

from modules.audio.bgm_manager import BGMManager
from modules.audio.sfx_manager import SFXManager

print("######## VIDEO_PIPELINE SPRINT194-58 HISTORY REGRESSION RESTORE LOADED ########", flush=True)


class VideoPipeline:
    PIPELINE_VERSION = "video-pipeline-194-58-history-regression-restore"

    def __init__(
        self,
        render_dir="exports/rendered_scenes",
        merged_dir="exports/videos",
        subtitle_dir="exports/subtitle_pipeline",
    ):
        self.render_dir = Path(render_dir)
        self.merged_dir = Path(merged_dir)
        self.subtitle_dir = Path(subtitle_dir)
        for path in (self.render_dir, self.merged_dir, self.subtitle_dir):
            path.mkdir(parents=True, exist_ok=True)
        self.bgm_manager = BGMManager()
        self.sfx_manager = SFXManager()

    def run(
        self,
        content_pack,
        project=None,
        clip_paths=None,
        render=True,
        apply_subtitles=True,
        apply_voice=True,
        apply_bgm=True,
        apply_effects=True,
        playback_speed=1.5,
    ):
        content_pack = dict(content_pack or {})
        channel_type = str(content_pack.get("channel_type") or "shopping").strip().lower()
        production_mode = str(content_pack.get("production_mode") or "").strip().lower()
        is_history_mode = channel_type == "history" or production_mode.startswith("history_")
        content_pack["_is_history_mode"] = bool(is_history_mode)
        project_id = self._project_id(project, content_pack)
        content_pack["_project_id"] = project_id
        project_payload = self._project_payload(project)

        clip_edit_sidecar = self._load_clip_edit_sidecar(project_id)
        sidecar_clip_subtitles = [
            str(item or "").strip()
            for item in list(clip_edit_sidecar.get("clip_subtitles") or [])
        ]
        sidecar_subtitle_style = dict(clip_edit_sidecar.get("subtitle_style") or {})
        sidecar_effects = [
            str(item or "기본").strip()
            for item in list(clip_edit_sidecar.get("clip_subtitle_effects") or [])
        ]
        sidecar_sfx = [
            str(item or "없음").strip()
            for item in list(clip_edit_sidecar.get("clip_sfx") or [])
        ]
        sidecar_narrations = [
            str(item or "").strip()
            for item in list(clip_edit_sidecar.get("clip_narrations") or [])
        ]
        sidecar_speeds = [
            max(0.5, min(2.0, float(item or 1.5)))
            for item in list(clip_edit_sidecar.get("clip_playback_speeds") or [])
        ]

        if sidecar_effects:
            content_pack["clip_subtitle_effects"] = sidecar_effects
        if sidecar_sfx:
            content_pack["clip_sfx"] = sidecar_sfx
        if sidecar_narrations:
            content_pack["clip_narrations"] = sidecar_narrations
        if sidecar_speeds:
            content_pack["clip_playback_speeds"] = sidecar_speeds

        if sidecar_subtitle_style:
            content_pack["subtitle_style"] = sidecar_subtitle_style
        elif not isinstance(content_pack.get("subtitle_style"), dict):
            content_pack["subtitle_style"] = {}

        recovered_clip_subtitles = self._deep_project_value(
            project_payload,
            ("clip_subtitles", "video_subtitles", "scene_subtitles"),
        )

        current_clip_subtitles = content_pack.get("clip_subtitles")
        if sidecar_clip_subtitles:
            content_pack["clip_subtitles"] = sidecar_clip_subtitles
        elif isinstance(current_clip_subtitles, list) and current_clip_subtitles:
            content_pack["clip_subtitles"] = [
                str(item or "").strip() for item in current_clip_subtitles
            ]
        elif isinstance(recovered_clip_subtitles, list):
            content_pack["clip_subtitles"] = [
                str(item or "").strip() for item in recovered_clip_subtitles
            ]
        else:
            content_pack["clip_subtitles"] = []

        def recover_project_value(*keys):
            return self._deep_project_value(project_payload, keys)

        if not str(content_pack.get("manual_subtitle_text") or "").strip():
            content_pack["manual_subtitle_text"] = str(
                recover_project_value("manual_subtitle_text", "shorts_subtitle_text", "subtitle_text") or ""
            ).strip()

        if "monthly_purchase_count" not in content_pack or content_pack.get("monthly_purchase_count") in (None, ""):
            content_pack["monthly_purchase_count"] = self._safe_int(
                recover_project_value("monthly_purchase_count", "monthly_purchases", "purchase_count")
            )
        if not int(float(content_pack.get("declared_review_count") or content_pack.get("review_count") or 0)):
            recovered_review = self._safe_int(
                recover_project_value("declared_review_count", "review_count", "reviews_count")
            )
            content_pack["declared_review_count"] = recovered_review
            content_pack["review_count"] = recovered_review
        if not float(content_pack.get("rating") or 0):
            content_pack["rating"] = self._safe_float(
                recover_project_value("rating", "star_rating", "review_rating")
            )

        print(
            "[Sprint191-20 Project Input Recovery]",
            {
                "manual_subtitle_chars": len(str(content_pack.get("manual_subtitle_text") or "").strip()),
                "monthly_purchase_count": content_pack.get("monthly_purchase_count"),
                "declared_review_count": content_pack.get("declared_review_count"),
                "rating": content_pack.get("rating"),
                "project_id": project_id,
            },
            flush=True,
        )

        clips = self._existing_files(clip_paths or content_pack.get("gemini_clip_paths") or [])
        merged = self.merged_dir / f"{project_id}_gemini_merged.mp4"
        final = self.merged_dir / f"{project_id}_final.mp4"
        result: Dict[str, Any] = {
            "ok": False,
            "pipeline_version": self.PIPELINE_VERSION,
            "status": "planned",
            "clip_count": len(clips),
            "clip_paths": clips,
            "merged_path": "",
            "output_path": "",
            "steps": {},
            "errors": [],
            "warnings": [],
        }
        if not clips:
            result.update(status="gemini_clips_missing")
            result["errors"].append("연결할 Gemini 영상 클립이 없습니다.")
            return result
        if not render:
            result.update(ok=True, status="plan_only", output_path=clips[0])
            return result

        # Sprint193-15: Trust intro must be long enough for its narration.
        intro_voice_path = str(content_pack.get("intro_voice_path") or "").strip()
        intro_voice_duration = (
            self._probe_duration(Path(intro_voice_path))
            if intro_voice_path and Path(intro_voice_path).is_file()
            else 0.0
        )
        configured_trust_duration = float(content_pack.get("trust_card_duration") or 3.4)
        if intro_voice_duration > 0:
            configured_trust_duration = max(
                configured_trust_duration,
                intro_voice_duration + 0.22,
            )
        # Keep the intro short, but never cut off the actual intro narration.
        content_pack["trust_card_duration"] = max(
            2.8,
            min(7.0, configured_trust_duration),
        )
        content_pack["_intro_voice_duration"] = float(intro_voice_duration)

        print(
            "[Sprint193-20 Auto Sync Intro]",
            {
                "intro_voice_duration": round(float(intro_voice_duration), 3),
                "trust_card_duration": round(float(content_pack["trust_card_duration"]), 3),
            },
            flush=True,
        )

        self._active_clip_voice_paths = list(content_pack.get("clip_voice_paths") or [])
        merge_result = self._merge_clips(
            clips,
            merged,
            playback_speed=playback_speed,
            clip_playback_speeds=content_pack.get("clip_playback_speeds"),
        )
        result["steps"]["merge"] = merge_result
        if not merge_result.get("ok"):
            result.update(status="merge_failed")
            result["errors"].extend(merge_result.get("errors") or [])
            return result
        current = Path(merge_result["output_path"])
        result["merged_path"] = str(current)
        content_pack["_normalized_clip_durations"] = list(
            merge_result.get("normalized_clip_durations") or []
        )
        content_pack["_applied_clip_speeds"] = list(
            merge_result.get("applied_clip_speeds") or []
        )

        resolved_hook, resolved_body = self._resolve_hook_and_body(content_pack)
        full_script = self._full_script(content_pack)
        content_pack["resolved_hook_text"] = resolved_hook
        content_pack["resolved_body_script"] = resolved_body
        content_pack["full_script"] = full_script
        content_pack["narration_text"] = full_script
        content_pack["script"] = full_script
        content_pack["short_script"] = full_script
        result["full_script_chars"] = len(full_script)
        result["hook_included"] = bool(resolved_hook)
        result["hook_source"] = (
            "explicit" if str(content_pack.get("hook_text") or content_pack.get("hook") or "").strip()
            else "locked_script_first_sentence" if resolved_hook
            else "missing"
        )
        result["resolved_hook_text"] = resolved_hook
        result["cta_included"] = False

        duration = self._probe_duration(current)
        if duration <= 0:
            result.update(status="duration_probe_failed")
            result["errors"].append("병합 영상 길이를 확인하지 못했습니다.")
            return result

        # Sprint194-53: 역사쿠키는 쇼핑용 Trust 카드 없이 Scene 1부터 즉시 시작합니다.
        if is_history_mode:
            content_pack["_effective_trust_duration"] = 0.0
            result["steps"]["trust_card"] = {
                "ok": True,
                "status": "history_trust_card_skipped",
                "output_path": str(current),
                "card_duration": 0.0,
            }
            print(
                "[Sprint194-53 History Timeline] TRUST SKIPPED",
                {"project_id": project_id, "clip_count": len(clips)},
                flush=True,
            )
        else:
            # 쇼핑 쇼츠는 기존 Trust 후킹 카드를 유지합니다.
            trust_output = self.merged_dir / f"{project_id}_trust_intro.mp4"
            trust_step = self._prepend_trust_card(current, trust_output, content_pack)
            result["steps"]["trust_card"] = trust_step
            if trust_step.get("ok"):
                current = Path(trust_step["output_path"])
                duration = self._probe_duration(current)
                content_pack["_effective_trust_duration"] = float(
                    trust_step.get("card_duration")
                    or content_pack.get("trust_card_duration")
                    or 0.0
                )
            else:
                content_pack["_effective_trust_duration"] = 0.0
                result["warnings"].append("Trust 후킹 생성 실패: 본문 타임라인을 0초부터 시작합니다.")

            print(
                "[Sprint193-20 Hook State]",
                {
                    "ok": bool(trust_step.get("ok")),
                    "effective_trust_duration": round(float(content_pack.get("_effective_trust_duration") or 0.0), 3),
                },
                flush=True,
            )

        # 1) 장면별 나레이션을 각 영상 시작점에 맞춰 삽입합니다.
        voice_audio = Path(str(content_pack.get("voice_audio_path") or ""))
        has_scene_voice = bool(
            str(content_pack.get("intro_voice_path") or "").strip()
            or [p for p in list(content_pack.get("clip_voice_paths") or []) if str(p or "").strip()]
        )
        if apply_voice and has_scene_voice:
            out = self.merged_dir / f"{project_id}_scene_voiced.mp4"
            step = self._apply_scene_voice(current, out, duration, content_pack)
            result["steps"]["voice"] = step
            if step.get("ok"):
                current = Path(step["output_path"])
            else:
                result["warnings"].append("장면별 나레이션 삽입에 실패했습니다.")
        elif apply_voice and voice_audio.is_file():
            out = self.merged_dir / f"{project_id}_voiced.mp4"
            step = self._apply_voice(current, voice_audio, out, duration)
            result["steps"]["voice"] = step
            if step.get("ok"):
                current = Path(step["output_path"])
            else:
                result["warnings"].append("나레이션 음성 삽입에 실패했습니다.")
        elif apply_voice:
            result["steps"]["voice"] = {
                "ok": False,
                "status": "voice_audio_missing",
                "output_path": "",
            }
            result["warnings"].append("나레이션 음성 파일이 없어 음성은 적용되지 않았습니다.")
        else:
            result["steps"]["voice"] = {"ok": True, "status": "disabled"}

        # 2) BGM은 라이브러리 파일을 우선 사용하고, 없으면 쇼핑용 합성 BGM을 생성합니다.
        bgm_selection = self.bgm_manager.select(
            channel_type=str(content_pack.get("channel_type") or "shopping"),
            explicit_path=str(content_pack.get("bgm_audio_path") or ""),
        )
        if apply_bgm:
            out = self.merged_dir / f"{project_id}_bgm.mp4"
            selected_path = str(bgm_selection.get("path") or "")
            if selected_path and Path(selected_path).is_file():
                step = self._apply_bgm(current, Path(selected_path), out, duration)
            else:
                step = self._apply_generated_bgm(current, out, duration, str(content_pack.get("channel_type") or "shopping"))
            step["selection"] = bgm_selection
            result["steps"]["bgm"] = step
            if step.get("ok"):
                current = Path(step["output_path"])
            else:
                result["warnings"].append("BGM 믹싱에 실패했습니다.")
        else:
            result["steps"]["bgm"] = {"ok": True, "status": "disabled"}

        # 3) 외부 효과음 파일 없이 FFmpeg 합성 효과음을 직접 생성·믹싱합니다.
        if apply_effects:
            print(
                "[Sprint193-13 SFX INPUT]",
                {
                    "clip_sfx": list(content_pack.get("clip_sfx") or []),
                    "clip_subtitle_effects": list(content_pack.get("clip_subtitle_effects") or []),
                },
                flush=True,
            )
            out = self.merged_dir / f"{project_id}_effects.mp4"
            cue_times = self._effect_cue_times(duration, len(clips), full_script, content_pack)
            step = self._apply_effects(current, out, duration, cue_times)
            result["steps"]["effects"] = step
            if step.get("ok"):
                current = Path(step["output_path"])
            else:
                result["warnings"].append("효과음 믹싱에 실패했습니다.")
        else:
            result["steps"]["effects"] = {"ok": True, "status": "disabled"}

        # 4) 후킹+수동 본문 자막(없으면 자동)+CTA를 안전영역에 적용합니다.
        if apply_subtitles and (full_script or list(content_pack.get("clip_subtitles") or [])):
            out = self.merged_dir / f"{project_id}_subtitled.mp4"
            step = self._apply_full_script_subtitles(current, out, content_pack, full_script, duration, len(clips))
            result["steps"]["subtitle"] = step
            if step.get("ok"):
                current = Path(step["output_path"])
            else:
                result["warnings"].append("쇼츠 자막 적용에 실패했습니다.")
        elif apply_subtitles:
            result["steps"]["subtitle"] = {"ok": False, "status": "full_script_missing"}
            result["warnings"].append("전체 대본이 없어 자막을 적용하지 못했습니다.")
        else:
            result["steps"]["subtitle"] = {"ok": True, "status": "disabled"}

        if current.resolve() != final.resolve():
            shutil.copy2(current, final)

        required_steps = (["merge", "effects", "subtitle"] if is_history_mode else ["merge", "trust_card", "effects", "subtitle"])
        required_ok = all(bool((result["steps"].get(name) or {}).get("ok")) for name in required_steps)
        if is_history_mode and apply_voice:
            required_ok = required_ok and bool((result["steps"].get("voice") or {}).get("ok"))
        print("[Sprint194-53 History Timeline] REQUIRED STEPS:", required_steps, "VOICE REQUIRED:", bool(is_history_mode and apply_voice), flush=True)
        result.update(
            ok=required_ok,
            status=("completed" if required_ok and not result["warnings"] else "completed_with_warnings" if required_ok else "required_step_failed"),
            output_path=str(final) if final.is_file() else "",
        )

        print("[Sprint179-1 Video Pipeline] CLIPS:", len(clips), flush=True)
        print("[Sprint179-1 Video Pipeline] PLAYBACK SPEED:", playback_speed, flush=True)
        print("[Sprint179-1 Video Pipeline] GEMINI AUDIO REMOVED: True", flush=True)
        print("[Sprint193-19 Video Pipeline] FULL FRAME: True / blur_background=False / subtitle_safe_zone_only=True", flush=True)
        print("[Sprint179-1 Video Pipeline] SUBTITLE SAFE ZONE: Default MarginV=560 / Hook MarginV=230 / right_margin=250", flush=True)
        print("[Sprint191-21 Video Pipeline] FULL SCRIPT CHARS:", len(full_script), flush=True)
        print("[Sprint193-10 Video Pipeline] CLIP SUBTITLE COUNT:", len(list(content_pack.get("clip_subtitles") or [])), flush=True)
        print("[Sprint179-1 Video Pipeline] HOOK INCLUDED:", result["hook_included"], flush=True)
        print("[Sprint179-1 Video Pipeline] HOOK SOURCE:", result.get("hook_source"), flush=True)
        print("[Sprint179-1 Video Pipeline] RESOLVED HOOK:", result.get("resolved_hook_text"), flush=True)
        print("[Sprint179-1 Video Pipeline] CTA INCLUDED:", result["cta_included"], flush=True)
        print("[Sprint179-1 Video Pipeline] VOICE STEP:", result["steps"].get("voice"), flush=True)
        print("[Sprint179-1 Video Pipeline] BGM STEP:", result["steps"].get("bgm"), flush=True)
        print("[Sprint179-1 Video Pipeline] EFFECTS STEP:", result["steps"].get("effects"), flush=True)
        print("[Sprint179-1 Video Pipeline] SUBTITLE STEP:", result["steps"].get("subtitle"), flush=True)
        print("[Sprint179-1 Video Pipeline] TRUST VALUES:", self._trust_values(content_pack), flush=True)
        print("[Sprint193-14 Video Pipeline] BLOCK ORDER: TRUST(NARRATION ONLY) -> BODY / CTA DISABLED", flush=True)
        print("[Sprint179-1 Video Pipeline] HOOK EFFECT: punch_pop_72_132_92_106_100", flush=True)
        print("[Sprint193-14 Video Pipeline] CTA DISABLED: True", flush=True)
        print("[Sprint179-1 Video Pipeline] BLANK TRUST INTRO BLOCKED: True", flush=True)
        print("[Sprint179-1 Video Pipeline] FINAL VIDEO:", final, flush=True)
        return result

    def plan(self, content_pack, project=None, clip_paths=None):
        return self.run(content_pack, project, clip_paths, False, False, False, False, False)

    def render(self, content_pack, project=None, clip_paths=None, apply_subtitles=True):
        return self.run(content_pack, project, clip_paths, True, apply_subtitles)

    def _merge_clips(self, clips: List[str], output_path: Path, playback_speed: float = 1.5, clip_playback_speeds=None) -> Dict[str, Any]:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        speed = max(0.5, min(3.0, float(playback_speed or 1.5)))
        if speed >= 1.95:
            speed = max(speed, 2.20)
        requested_speeds = [
            float(item if item is not None else 0.0)
            for item in list(clip_playback_speeds or [])
        ]
        scene_voice_paths = [
            str(item or "").strip()
            for item in list(getattr(self, "_active_clip_voice_paths", []) or [])
        ]
        normalized_dir = output_path.parent / f"{output_path.stem}_normalized"
        if normalized_dir.exists():
            shutil.rmtree(normalized_dir, ignore_errors=True)
        normalized_dir.mkdir(parents=True, exist_ok=True)
        normalized: List[Path] = []
        errors: List[str] = []
        durations: List[float] = []
        applied_speeds: List[float] = []
        applied_scene_pads: List[float] = []
        for index, value in enumerate(clips, start=1):
            source = Path(value)
            requested_scene_speed = (
                requested_speeds[index - 1]
                if index - 1 < len(requested_speeds)
                else speed
            )
            source_duration = self._probe_duration(source)
            voice_path = (
                scene_voice_paths[index - 1]
                if index - 1 < len(scene_voice_paths)
                else ""
            )
            voice_duration = (
                self._probe_duration(Path(voice_path))
                if voice_path and Path(voice_path).is_file()
                else 0.0
            )

            is_auto_speed = requested_scene_speed <= 0
            if is_auto_speed and source_duration > 0 and voice_duration > 0:
                # Target visual duration follows narration + a tiny breathing gap.
                target_duration = max(0.8, voice_duration + 0.18)
                raw_scene_speed = source_duration / target_duration
            else:
                raw_scene_speed = (
                    requested_scene_speed
                    if requested_scene_speed > 0
                    else speed
                )

            if source_duration > 0 and voice_duration > 0 and requested_scene_speed >= 1.95:
                narration_fit_speed = source_duration / max(0.8, voice_duration + 0.10)
                raw_scene_speed = max(float(raw_scene_speed or speed), narration_fit_speed)
            scene_speed = max(0.5, min(3.0, float(raw_scene_speed or speed)))
            sped_duration = (
                source_duration / scene_speed
                if source_duration > 0
                else 0.0
            )

            # If narration is still longer even at 0.5x (or with a manual speed),
            # freeze the final frame so the next narration cannot start early.
            required_scene_duration = (
                max(sped_duration, voice_duration + 0.18)
                if voice_duration > 0
                else sped_duration
            )
            pad_duration = max(0.0, required_scene_duration - sped_duration)

            target = normalized_dir / f"clip_{index:02d}.mp4"
            filter_tail = f"setpts=PTS/{scene_speed:.6f}"
            if pad_duration > 0.03:
                filter_tail += f",tpad=stop_mode=clone:stop_duration={pad_duration:.6f}"

            print(
                "[Sprint193-20 Shorts Tempo]",
                {
                    "scene": index,
                    "mode": "auto" if is_auto_speed else "manual",
                    "source_duration": round(float(source_duration), 3),
                    "voice_duration": round(float(voice_duration), 3),
                    "speed": round(float(scene_speed), 3),
                    "pad_duration": round(float(pad_duration), 3),
                    "target_duration": round(float(required_scene_duration), 3),
                },
                flush=True,
            )

            command = [
                "ffmpeg", "-y", "-i", str(source), "-an",
                "-vf",
                (
                    # Sprint193-19: 영상 전체 9:16 채우기. 블러 가이드 없음.
                    # 안전영역은 자막 좌표에만 적용합니다.
                    "scale=1080:1920:force_original_aspect_ratio=increase,"
                    "crop=1080:1920,setsar=1,fps=30,"
                    + filter_tail
                ),
                "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(target),
            ]
            completed = self._run(command)
            if completed.returncode != 0 or not self._valid_file(target):
                errors.append(f"clip_{index:02d}: {completed.stderr[-1800:]}")
                continue
            normalized.append(target)
            durations.append(self._probe_duration(target))
            applied_speeds.append(scene_speed)
            applied_scene_pads.append(float(pad_duration))
        if len(normalized) != len(clips):
            return {
                "ok": False,
                "status": "clip_normalize_failed",
                "output_path": "",
                "playback_speed": speed,
                "applied_clip_speeds": applied_speeds,
                "audio_removed": True,
                "errors": errors or ["일부 Gemini 클립 정규화에 실패했습니다."],
            }
        list_path = output_path.with_suffix(".concat.txt")
        list_path.write_text(
            "\n".join(f"file '{str(value.resolve()).replace(chr(39), chr(39)+chr(92)+chr(39)+chr(39))}'" for value in normalized) + "\n",
            encoding="utf-8",
        )
        completed = self._run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_path),
            "-an", "-c:v", "copy", "-movflags", "+faststart", str(output_path),
        ])
        ok = completed.returncode == 0 and self._valid_file(output_path)
        return {
            "ok": ok,
            "status": "manual_clips_fast_concat_completed" if ok else "concat_failed",
            "output_path": str(output_path) if ok else "",
            "playback_speed": speed,
            "applied_clip_speeds": applied_speeds,
            "applied_scene_pads": applied_scene_pads,
            "audio_removed": True,
            "reels_safe_frame": True,
            "foreground_scale": "760x1352",
            "safe_margins": {"top": 220, "bottom": 348, "left": 70, "right": 250},
            "normalized_clip_count": len(normalized),
            "normalized_clip_durations": durations,
            "errors": [] if ok else [completed.stderr[-3000:]],
        }

    @staticmethod
    def _project_payload(project: Any) -> Dict[str, Any]:
        """프로젝트 data_json에 저장된 원클릭 입력값을 복원합니다."""
        if project is None:
            return {}
        raw = getattr(project, "data_json", "")
        if isinstance(raw, dict):
            return dict(raw)
        try:
            import json
            loaded = json.loads(str(raw or "{}"))
            return loaded if isinstance(loaded, dict) else {}
        except Exception:
            return {}

    @classmethod
    def _deep_project_value(
        cls,
        data: Any,
        keys: Sequence[str],
    ) -> Any:
        wanted = {str(key).lower() for key in keys}
        queue = [data]
        while queue:
            current = queue.pop(0)
            if isinstance(current, dict):
                for key, value in current.items():
                    if str(key).lower() in wanted and value not in (None, "", [], {}):
                        return value
                    if isinstance(value, (dict, list, tuple)):
                        queue.append(value)
            elif isinstance(current, (list, tuple)):
                queue.extend(current)
        return None

    @staticmethod
    def _safe_int(value: Any) -> int:
        try:
            return max(0, int(float(str(value).replace(",", "").strip())))
        except Exception:
            return 0

    @staticmethod
    def _safe_float(value: Any) -> float:
        try:
            return max(0.0, float(str(value).replace(",", "").strip()))
        except Exception:
            return 0.0

    @classmethod
    def _load_clip_subtitle_sidecar(
        cls,
        project_id: str,
    ) -> List[str]:
        project_id = str(project_id or "").strip()
        if not project_id:
            return []

        path = (
            Path("assets/products")
            / f"project_{project_id}"
            / "clip_subtitles.json"
        )
        if not path.is_file():
            print(
                "[Sprint190-2 Clip Subtitle Sidecar] MISSING",
                str(path),
                flush=True,
            )
            return []

        try:
            import json
            payload = json.loads(path.read_text(encoding="utf-8"))
            values = payload.get("clip_subtitles") if isinstance(payload, dict) else []
            result = [
                str(item or "").strip()
                for item in list(values or [])
            ]
            print(
                "[Sprint190-2 Clip Subtitle Sidecar] LOADED",
                {
                    "path": str(path),
                    "count": len(result),
                    "nonempty": len([x for x in result if x]),
                },
                flush=True,
            )
            return result
        except Exception as exc:
            print(
                "[Sprint190-2 Clip Subtitle Sidecar] ERROR",
                type(exc).__name__,
                str(exc),
                flush=True,
            )
            return []

    @classmethod
    def _load_clip_edit_sidecar(cls, project_id: str) -> Dict[str, Any]:
        project_id = str(project_id or "").strip()
        if not project_id:
            return {}
        path = Path("assets/products") / f"project_{project_id}" / "clip_subtitles.json"
        if not path.is_file():
            return {}
        try:
            import json
            payload = json.loads(path.read_text(encoding="utf-8"))
            result = dict(payload or {}) if isinstance(payload, dict) else {}
            print(
                "[Sprint193-10 Clip Edit Sidecar] LOADED",
                {
                    "path": str(path),
                    "subtitle_count": len(list(result.get("clip_subtitles") or [])),
                    "narration_count": len(list(result.get("clip_narrations") or [])),
                    "effect_count": len(list(result.get("clip_subtitle_effects") or [])),
                    "sfx_count": len(list(result.get("clip_sfx") or [])),
                    "speed_count": len(list(result.get("clip_playback_speeds") or [])),
                },
                flush=True,
            )
            return result
        except Exception as exc:
            print(
                "[Sprint193-10 Clip Edit Sidecar] ERROR",
                type(exc).__name__,
                str(exc),
                flush=True,
            )
            return {}

    @classmethod
    def _load_subtitle_style_sidecar(
        cls,
        project_id: str,
    ) -> Dict[str, Any]:
        project_id = str(project_id or "").strip()
        if not project_id:
            return {}

        path = (
            Path("assets/products")
            / f"project_{project_id}"
            / "clip_subtitles.json"
        )
        if not path.is_file():
            return {}

        try:
            import json
            payload = json.loads(path.read_text(encoding="utf-8"))
            style = payload.get("subtitle_style") if isinstance(payload, dict) else {}
            result = dict(style or {}) if isinstance(style, dict) else {}
            print(
                "[Sprint191-21 Subtitle Style Sidecar] LOADED",
                result,
                flush=True,
            )
            return result
        except Exception as exc:
            print(
                "[Sprint191-21 Subtitle Style Sidecar] ERROR",
                type(exc).__name__,
                str(exc),
                flush=True,
            )
            return {}

    def _hook_product_image_path(
        self,
        content_pack: Dict[str, Any],
    ) -> str:
        """대표 이미지가 없으면 첫 Gemini 영상의 첫 프레임을 자동 배경으로 사용합니다."""
        explicit = str(content_pack.get("hook_product_image_path") or "").strip()
        if explicit and Path(explicit).is_file():
            print(
                "[Sprint191-21 Hook Product BG] SOURCE explicit",
                explicit,
                flush=True,
            )
            return explicit

        project_id = str(content_pack.get("_project_id") or "").strip()
        if project_id:
            folder = Path("assets/products") / f"project_{project_id}"
            if folder.exists():
                preferred = []
                for pattern in ("00_main.*", "main.*", "product.*"):
                    preferred.extend(sorted(folder.glob(pattern)))
                if not preferred:
                    preferred = sorted(
                        p for p in folder.iterdir()
                        if p.is_file()
                        and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
                    )
                if preferred:
                    resolved = str(preferred[0])
                    print(
                        "[Sprint191-21 Hook Product BG] SOURCE project_image",
                        resolved,
                        flush=True,
                    )
                    return resolved

        # 대표 제품 이미지가 없으면 첫 Gemini 클립의 첫 프레임을 자동 추출합니다.
        clip_paths = [
            str(value or "").strip()
            for value in list(content_pack.get("gemini_clip_paths") or [])
            if str(value or "").strip()
        ]
        first_clip = Path(clip_paths[0]) if clip_paths else None
        if first_clip is not None and first_clip.is_file():
            frame_path = self.subtitle_dir / (
                f"{project_id or 'default'}_hook_product_frame.jpg"
            )
            try:
                cmd = [
                    self.ffmpeg_bin,
                    "-y",
                    "-ss",
                    "0.15",
                    "-i",
                    str(first_clip),
                    "-frames:v",
                    "1",
                    "-q:v",
                    "2",
                    str(frame_path),
                ]
                completed = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                if completed.returncode == 0 and frame_path.is_file():
                    print(
                        "[Sprint191-21 Hook Product BG] SOURCE first_clip_frame",
                        str(frame_path),
                        flush=True,
                    )
                    return str(frame_path)
                print(
                    "[Sprint191-21 Hook Product BG] FRAME EXTRACT FAILED",
                    completed.stderr[-500:],
                    flush=True,
                )
            except Exception as exc:
                print(
                    "[Sprint191-21 Hook Product BG] FRAME EXTRACT ERROR",
                    type(exc).__name__,
                    str(exc),
                    flush=True,
                )

        print(
            "[Sprint191-21 Hook Product BG] SOURCE missing",
            flush=True,
        )
        return ""

    @staticmethod
    def _find_nested_value(data: Any, keys: Sequence[str]) -> Any:
        """UI/DB/콘텐츠팩 어디에 저장돼도 같은 입력값을 찾습니다."""
        wanted = {str(key).lower() for key in keys}
        queue: List[Any] = [data]
        while queue:
            current = queue.pop(0)
            if isinstance(current, dict):
                for key, value in current.items():
                    if str(key).lower() in wanted and value not in (None, ""):
                        return value
                    if isinstance(value, (dict, list, tuple)):
                        queue.append(value)
            elif isinstance(current, (list, tuple)):
                queue.extend(current)
        return None

    @classmethod
    def _trust_values(cls, content_pack: Dict[str, Any]) -> Tuple[int, int, float]:
        """UI에서 전달된 최상위 값을 절대 우선하며, 없는 값만 보조 데이터에서 복구합니다."""
        def as_int(value: Any) -> int:
            try:
                return max(0, int(float(str(value).replace(",", "").strip())))
            except Exception:
                return 0

        def as_float(value: Any) -> float:
            try:
                return max(0.0, float(str(value).replace(",", "").strip()))
            except Exception:
                return 0.0

        # 중요: 원클릭 UI가 전달한 최상위 값이 진실의 원천입니다.
        # 과거 프로젝트 데이터나 대본의 예시 숫자가 이를 덮어쓸 수 없습니다.
        monthly_explicit = (
            "monthly_purchase_count" in content_pack
            and content_pack.get("monthly_purchase_count") not in (None, "")
        )
        monthly = as_int(content_pack.get("monthly_purchase_count"))
        review = as_int(content_pack.get("declared_review_count") or content_pack.get("review_count"))
        rating = as_float(content_pack.get("rating"))

        if not monthly_explicit:
            monthly = as_int(cls._find_nested_value(content_pack.get("trust_inputs") or {}, (
                "monthly_purchase_count", "monthly_purchases", "purchase_count",
                "recent_purchase_count", "declared_monthly_purchase_count",
            )))
        if not review:
            review = as_int(cls._find_nested_value(content_pack.get("trust_inputs") or {}, (
                "declared_review_count", "review_count", "reviews_count", "total_review_count",
            )))
        if not rating:
            rating = as_float(cls._find_nested_value(content_pack.get("trust_inputs") or {}, (
                "rating", "star_rating", "review_rating", "declared_rating",
            )))

        # 명시 입력이 전혀 없을 때만 잠금 대본에서 복구합니다.
        source_text = " ".join(str(content_pack.get(key) or "") for key in (
            "locked_script", "narration_text", "script", "short_script", "hook_text", "hook"
        ))
        if not monthly_explicit and not monthly:
            match = re.search(r"(?:최근\s*한\s*달[^0-9]{0,20})?([0-9][0-9,]*)\s*명\s*(?:이상\s*)?(?:구매|구입)", source_text)
            if match:
                monthly = as_int(match.group(1))
        if not review:
            match = re.search(r"(?:리뷰|후기)\s*([0-9][0-9,]*)\s*개", source_text)
            if not match:
                match = re.search(r"([0-9][0-9,]*)\s*개의?\s*(?:리뷰|후기)", source_text)
            if match:
                review = as_int(match.group(1))
        if not rating:
            match = re.search(r"(?:평점|별점)\s*([0-9](?:\.[0-9])?)\s*점?", source_text)
            if match:
                rating = as_float(match.group(1))

        print(
            "[Sprint178-2 Trust Source Priority]",
            {
                "ui_monthly": content_pack.get("monthly_purchase_count"),
                "resolved_monthly": monthly,
                "ui_review": content_pack.get("declared_review_count"),
                "resolved_review": review,
                "ui_rating": content_pack.get("rating"),
                "resolved_rating": rating,
            },
            flush=True,
        )
        return monthly, review, rating

    def _prepend_trust_card(self, input_path: Path, output_path: Path, content_pack: Dict[str, Any]) -> Dict[str, Any]:
        """구매수·리뷰수·평점을 순차적으로 팅팅 등장시키는 Trust Intro를 앞에 붙입니다."""
        duration = max(2.8, min(7.0, float(content_pack.get("trust_card_duration") or 3.4)))
        card_video = self.subtitle_dir / f"{output_path.stem}_card.mp4"
        animation_result = self._build_trust_card_video(card_video, content_pack, duration)
        if not animation_result.get("ok"):
            print("[Sprint193-22 Hook Fallback] PRIMARY FAILED", animation_result, flush=True)
            animation_result = self._build_trust_card_fallback_video(
                card_video,
                content_pack,
                duration,
            )
        if not animation_result.get("ok"):
            return {
                "ok": False,
                "status": "trust_card_animation_and_fallback_failed",
                "output_path": "",
                "animation_result": animation_result,
            }

        normalized_main = self.subtitle_dir / f"{output_path.stem}_main.mp4"
        normalize_cmd = [
            "ffmpeg", "-y", "-i", str(input_path), "-an",
            "-vf", "scale=1080:1920,setsar=1,fps=30,format=yuv420p",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18", str(normalized_main),
        ]
        normalized_completed = self._run(normalize_cmd)
        if normalized_completed.returncode != 0 or not self._valid_file(normalized_main):
            return {
                "ok": False,
                "status": "trust_main_normalize_failed",
                "output_path": "",
                "errors": [normalized_completed.stderr[-2500:]],
            }

        concat_file = self.subtitle_dir / f"{output_path.stem}.concat.txt"
        concat_file.write_text(
            f"file '{str(card_video.resolve()).replace(chr(39), chr(39)+chr(92)+chr(39)+chr(39))}'\n"
            f"file '{str(normalized_main.resolve()).replace(chr(39), chr(39)+chr(92)+chr(39)+chr(39))}'\n",
            encoding="utf-8",
        )
        concat_cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-an", "-c:v", "copy", "-movflags", "+faststart", str(output_path),
        ]
        completed = self._run(concat_cmd)
        ok = completed.returncode == 0 and self._valid_file(output_path)
        return {
            "ok": ok,
            "status": "trust_bounce_intro_prepended" if ok else "trust_card_concat_failed",
            "output_path": str(output_path) if ok else "",
            "card_duration": duration,
            "animation": "purchase_review_rating_sequential_bounce",
            "animation_result": animation_result,
            "subtitle_separate": True,
            "errors": [] if ok else [completed.stderr[-3000:]],
        }

    def _build_trust_card_fallback_video(
        self,
        output_path: Path,
        content_pack: Dict[str, Any],
        duration: float,
    ) -> Dict[str, Any]:
        """Fallback hook card: never silently lose the review/rating intro."""
        if Image is None or ImageDraw is None or ImageFont is None:
            return {"ok": False, "status": "fallback_pillow_missing", "output_path": ""}

        try:
            width, height = 1080, 1920
            monthly, review, rating = self._trust_values(content_pack)
            if not any((monthly, review, rating)):
                return {
                    "ok": False,
                    "status": "fallback_trust_values_missing",
                    "output_path": "",
                }

            font_paths = [
                Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "malgunbd.ttf",
                Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "malgun.ttf",
                Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
                Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
            ]
            font_path = next((p for p in font_paths if p.is_file()), None)
            if font_path is None:
                return {"ok": False, "status": "fallback_font_missing", "output_path": ""}

            def f(size):
                return ImageFont.truetype(str(font_path), size=size)

            img = Image.new("RGB", (width, height), "#FFF8EE")
            draw = ImageDraw.Draw(img)
            dark = "#24150E"
            accent_hot = "#FFD400"
            review_hot = accent_hot
            rating_hot = accent_hot
            buzz_hot = "#FFFFFF"

            def centered_segments(y, segments, font_obj):
                widths = []
                for text_value, fill_value, stroke_width in segments:
                    bbox = draw.textbbox((0, 0), text_value, font=font_obj, stroke_width=stroke_width)
                    widths.append(bbox[2] - bbox[0])
                x = (width - sum(widths)) / 2
                for (text_value, fill_value, stroke_width), w in zip(segments, widths):
                    draw.text(
                        (x, y),
                        text_value,
                        font=font_obj,
                        fill=fill_value,
                        stroke_width=stroke_width,
                        stroke_fill=dark,
                    )
                    x += w

            y = 650
            if review:
                centered_segments(
                    y,
                    [("리뷰 ", dark, 0), (f"{review:,}", review_hot, 6), ("개!", dark, 0)],
                    f(94),
                )
                y += 190

            if rating:
                rating_text = f"{rating:.2f}"
                centered_segments(
                    y,
                    [("평점도 ", dark, 0), (rating_text, rating_hot, 6), ("점?", dark, 0)],
                    f(90),
                )
                y += 220

            buzz = "리뷰 미쳤!!!"
            buzz_font = f(76)
            bbox = draw.textbbox((0, 0), buzz, font=buzz_font, stroke_width=6)
            bx = (width - (bbox[2] - bbox[0])) / 2
            draw.text(
                (bx, y),
                buzz,
                font=buzz_font,
                fill=buzz_hot,
                stroke_width=6,
                stroke_fill=dark,
            )

            still_path = self.subtitle_dir / f"{output_path.stem}_fallback.jpg"
            img.save(still_path, quality=95)

            cmd = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", str(still_path),
                "-t", f"{float(duration):.3f}",
                "-vf", "scale=1080:1920,setsar=1,fps=30,format=yuv420p",
                "-an",
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "18",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                str(output_path),
            ]
            completed = self._run(cmd)
            ok = completed.returncode == 0 and self._valid_file(output_path)
            print(
                "[Sprint193-22 Hook Fallback]",
                {"ok": ok, "review": review, "rating": rating, "duration": duration},
                flush=True,
            )
            return {
                "ok": ok,
                "status": "trust_hook_fallback_created" if ok else "trust_hook_fallback_failed",
                "output_path": str(output_path) if ok else "",
                "duration": float(duration),
                "errors": [] if ok else [completed.stderr[-2500:]],
            }
        except Exception as exc:
            return {
                "ok": False,
                "status": "trust_hook_fallback_exception",
                "output_path": "",
                "error": f"{type(exc).__name__}: {exc}",
            }

    @staticmethod
    def _ease_out_back(progress: float) -> float:
        """0→1 진입 시 살짝 커졌다 제자리로 돌아오는 팅팅 곡선입니다."""
        p = max(0.0, min(1.0, float(progress)))
        c1 = 1.70158
        c3 = c1 + 1.0
        return 1.0 + c3 * ((p - 1.0) ** 3) + c1 * ((p - 1.0) ** 2)

    def _build_trust_card_video(
        self,
        output_path: Path,
        content_pack: Dict[str, Any],
        duration: float,
    ) -> Dict[str, Any]:
        """Pillow 프레임을 만들어 Trust 수치가 실제로 팅팅 등장하는 영상을 생성합니다."""
        if Image is None or ImageDraw is None or ImageFont is None:
            return {"ok": False, "status": "pillow_missing", "output_path": ""}

        frame_dir = self.subtitle_dir / f"{output_path.stem}_frames"
        try:
            if frame_dir.exists():
                shutil.rmtree(frame_dir, ignore_errors=True)
            frame_dir.mkdir(parents=True, exist_ok=True)

            width, height, fps = 1080, 1920, 30
            frame_count = max(1, int(round(duration * fps)))
            monthly, review, rating = self._trust_values(content_pack)
            if not any((monthly, review, rating)):
                return {
                    "ok": False,
                    "status": "trust_values_all_missing_skip_intro",
                    "output_path": "",
                    "monthly_purchase_count": monthly,
                    "review_count": review,
                    "rating": rating,
                    "error": "구매수·리뷰수·평점이 모두 없어 Trust Intro 생성을 건너뜁니다.",
                }

            print(
                "[Sprint189-2 Trust Card Values]",
                {
                    "monthly_purchase_count": monthly,
                    "review_count": review,
                    "rating": rating,
                },
                flush=True,
            )
            monthly_text = f"{monthly:,}명 이상 구매" if monthly else ""
            review_text = f"리뷰 {review:,}개!" if review else ""
            rating_number = f"{rating:.2f}".rstrip("0").rstrip(".") if rating else ""
            rating_text = (f"평점도 {rating_number}점?" if (rating and not monthly) else rating_number)

            font_paths = [
                Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "malgunbd.ttf",
                Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "malgun.ttf",
                Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
                Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
            ]
            font_path = next((path for path in font_paths if path.is_file()), None)
            if font_path is None:
                raise RuntimeError("사용 가능한 한글 폰트를 찾지 못했습니다.")

            def font(size: int):
                return ImageFont.truetype(str(font_path), size=size)

            dark = "#351F12"
            gold = "#B06D2A"
            star = "#F2AD13"
            pale = "#F1DFC4"
            accent_hot = "#FFD400"
            review_hot = accent_hot
            rating_hot = accent_hot
            buzz_hot = "#FFFFFF"

            # 배경은 한 번만 생성해 모든 프레임에서 복사합니다.
            background = Image.new("RGB", (width, height), "#FFF9EF")
            pixels = background.load()
            center_x, center_y = width / 2, height / 2
            max_r = math.hypot(center_x, center_y)
            for y in range(height):
                for x in range(width):
                    ratio = min(1.0, math.hypot(x-center_x, y-center_y) / max_r)
                    base = (255, 250, 241)
                    edge = (244, 231, 210)
                    pixels[x, y] = tuple(
                        int(base[i] * (1-ratio*0.38) + edge[i] * (ratio*0.38))
                        for i in range(3)
                    )
            # 제품 대표 이미지 또는 첫 Gemini 프레임을 Trust/후킹 장면에 약 32%로 희미하게 표시합니다.
            hook_product_path = self._hook_product_image_path(content_pack)
            if hook_product_path:
                try:
                    product_layer = Image.open(hook_product_path).convert("RGBA")
                    product_layer.thumbnail((900, 1280), Image.Resampling.LANCZOS)
                    alpha = product_layer.getchannel("A").point(lambda value: int(value * 0.46))
                    product_layer.putalpha(alpha)
                    base_rgba = background.convert("RGBA")
                    px = int((width - product_layer.width) / 2)
                    py = int((height - product_layer.height) / 2 + 80)
                    base_rgba.alpha_composite(product_layer, (px, py))
                    background = base_rgba.convert("RGB")
                    print(
                        "[Sprint191-21 Hook Product BG] APPLIED",
                        hook_product_path,
                        flush=True,
                    )
                except Exception as exc:
                    print(
                        "[Sprint191-21 Hook Product BG] ERROR",
                        type(exc).__name__,
                        str(exc),
                        flush=True,
                    )

            bg_draw = ImageDraw.Draw(background)
            bg_draw.line((150, 760, 930, 760), fill="#D7BC92", width=3)
            bg_draw.line((150, 1280, 930, 1280), fill="#D7BC92", width=3)

            def centered_text(layer, y, text, text_font, fill):
                draw = ImageDraw.Draw(layer)
                bbox = draw.textbbox((0, 0), text, font=text_font)
                x = (width - (bbox[2] - bbox[0])) / 2
                draw.text((x, y), text, font=text_font, fill=fill)

            def centered_segments(layer, y, segments, text_font):
                draw = ImageDraw.Draw(layer)
                widths = []
                for text_value, fill_value, stroke_width in segments:
                    bbox = draw.textbbox((0, 0), text_value, font=text_font, stroke_width=stroke_width)
                    widths.append(bbox[2] - bbox[0])
                x = (width - sum(widths)) / 2
                for (text_value, fill_value, stroke_width), seg_w in zip(segments, widths):
                    draw.text((x, y), text_value, font=text_font, fill=fill_value, stroke_width=stroke_width, stroke_fill=dark)
                    x += seg_w

            def rounded_label(layer, box, text, size):
                draw = ImageDraw.Draw(layer)
                draw.rounded_rectangle(box, radius=22, fill=pale)
                f = font(size)
                bbox = draw.textbbox((0, 0), text, font=f)
                x = (box[0] + box[2] - (bbox[2]-bbox[0])) / 2
                y = (box[1] + box[3] - (bbox[3]-bbox[1])) / 2 - 4
                draw.text((x, y), text, font=f, fill=dark)

            # 상단 라벨은 처음부터 고정하고, 실제 수치 3개만 순서대로 팝업합니다.
            # 기존처럼 라벨과 구매수를 한 레이어로 묶으면 "최근 한 달"만 먼저 보이는
            # 페이드처럼 느껴질 수 있어 완전히 분리합니다.
            header_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            if monthly_text:
                rounded_label(header_layer, (360, 300, 720, 390), "최근 한 달", 52)

            purchase_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            if monthly_text:
                # Sprint191-18: 구매 후킹만 92로 축소하고 숫자/수량 부분만 강조합니다.
                purchase_prefix = monthly_text
                purchase_suffix = ""
                if monthly_text.endswith(" 구매"):
                    purchase_prefix = monthly_text[:-3].rstrip()
                    purchase_suffix = "구매"

                purchase_draw = ImageDraw.Draw(purchase_layer)
                purchase_font = font(78)
                prefix_bbox = purchase_draw.textbbox((0, 0), purchase_prefix, font=purchase_font)
                suffix_bbox = (
                    purchase_draw.textbbox((0, 0), purchase_suffix, font=purchase_font)
                    if purchase_suffix else (0, 0, 0, 0)
                )
                gap = 18 if purchase_suffix else 0
                prefix_w = prefix_bbox[2] - prefix_bbox[0]
                suffix_w = suffix_bbox[2] - suffix_bbox[0]
                start_x = (width - (prefix_w + gap + suffix_w)) / 2

                purchase_draw.text(
                    (start_x, 535),
                    purchase_prefix,
                    font=purchase_font,
                    fill=gold,
                )
                if purchase_suffix:
                    purchase_draw.text(
                        (start_x + prefix_w + gap, 535),
                        purchase_suffix,
                        font=purchase_font,
                        fill=dark,
                    )

            rating_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            if rating_text:
                if monthly:
                    centered_segments(rating_layer, 835, [("평점 ", dark, 0), (rating_number, rating_hot, 5), ("점!", dark, 0)], font(90))
                else:
                    centered_segments(rating_layer, 1010, [("평점도 ", dark, 0), (rating_number, rating_hot, 5), ("점?", dark, 0)], font(90))

            review_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            if review_text:
                centered_segments(review_layer, 710 if not monthly else 1080, [("리뷰 ", dark, 0), (f"{review:,}", review_hot, 5), ("개!", dark, 0)], font(92))

            review_buzz_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            if review:
                buzz_draw = ImageDraw.Draw(review_buzz_layer)
                buzz_font = font(72)
                buzz_text = "리뷰 미쳤!!!"
                bbox = buzz_draw.textbbox((0, 0), buzz_text, font=buzz_font, stroke_width=5)
                x = (width - (bbox[2] - bbox[0])) / 2
                buzz_draw.text((x, 1245 if monthly else 1215), buzz_text, font=buzz_font, fill=buzz_hot, stroke_width=5, stroke_fill=dark)

            # 각 요소의 실제 내용 영역만 잘라서 해당 위치 중심에서 확대합니다.
            def crop_nonempty(layer):
                bbox = layer.getbbox()
                return layer.crop(bbox) if bbox else Image.new("RGBA", (1, 1), (0, 0, 0, 0))

            header_layer = crop_nonempty(header_layer)
            purchase_layer = crop_nonempty(purchase_layer)
            rating_layer = crop_nonempty(rating_layer)
            review_layer = crop_nonempty(review_layer)
            review_buzz_layer = crop_nonempty(review_buzz_layer)

            def true_bounce_scale(elapsed: float) -> float:
                """페이드 없이 0→125→88→108→100%로 튀는 명시적 키프레임입니다."""
                if elapsed < 0.0:
                    return 0.0
                keyframes = (
                    (0.000, 0.00),
                    (0.075, 1.25),
                    (0.155, 0.88),
                    (0.245, 1.08),
                    (0.360, 1.00),
                )
                if elapsed >= keyframes[-1][0]:
                    return 1.0
                for index in range(1, len(keyframes)):
                    left_t, left_s = keyframes[index - 1]
                    right_t, right_s = keyframes[index]
                    if elapsed <= right_t:
                        progress = (elapsed - left_t) / max(0.000001, right_t - left_t)
                        # 각 구간을 부드럽게 연결하되 투명도는 사용하지 않습니다.
                        smooth = progress * progress * (3.0 - 2.0 * progress)
                        return left_s + (right_s - left_s) * smooth
                return 1.0

            def paste_fixed(base_image, layer, center):
                cx, cy = center
                base_image.alpha_composite(
                    layer,
                    (int(cx - layer.width / 2), int(cy - layer.height / 2)),
                )

            def paste_true_bounce(base_image, layer, start_time, now, center):
                scale = true_bounce_scale(now - start_time)
                if scale <= 0.0:
                    return
                scaled = layer.resize(
                    (max(1, int(round(layer.width * scale))),
                     max(1, int(round(layer.height * scale)))),
                    Image.Resampling.LANCZOS,
                )
                cx, cy = center
                base_image.alpha_composite(
                    scaled,
                    (int(cx - scaled.width / 2), int(cy - scaled.height / 2)),
                )

            for frame_index in range(frame_count):
                now = frame_index / fps
                frame = background.convert("RGBA")
                # Sprint193-22: 리뷰 → 평점 → 리뷰 미쳤!!! 딱 세 번 팅팅팅.
                paste_true_bounce(frame, review_layer, 0.18, now, (width / 2, 770))
                paste_true_bounce(frame, rating_layer, 0.92, now, (width / 2, 1065))
                paste_true_bounce(frame, review_buzz_layer, 1.58, now, (width / 2, 1270))
                frame.convert("RGB").save(
                    frame_dir / f"frame_{frame_index:04d}.jpg",
                    quality=92,
                    optimize=False,
                )

            command = [
                "ffmpeg", "-y", "-framerate", str(fps),
                "-i", str(frame_dir / "frame_%04d.jpg"),
                "-t", f"{duration:.3f}", "-an",
                "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output_path),
            ]
            completed = self._run(command)
            ok = completed.returncode == 0 and self._valid_file(output_path)
            return {
                "ok": ok,
                "status": "trust_bounce_video_created" if ok else "trust_bounce_encode_failed",
                "output_path": str(output_path) if ok else "",
                "frame_count": frame_count,
                "fps": fps,
                "monthly_purchase_count": monthly,
                "review_count": review,
                "rating": rating,
                "entry_times": {"review": 0.18, "rating": 0.92, "review_buzz": 1.58},
                "animation": "true_scale_keyframes_0_125_88_108_100",
                "opacity_animation": False,
                "errors": [] if ok else [completed.stderr[-3000:]],
            }
        except Exception as exc:
            return {
                "ok": False,
                "status": "trust_bounce_build_failed",
                "output_path": "",
                "error": f"{type(exc).__name__}: {exc}",
            }
        finally:
            shutil.rmtree(frame_dir, ignore_errors=True)

    def _apply_scene_voice(
        self,
        input_path: Path,
        output_path: Path,
        duration: float,
        content_pack: Dict[str, Any],
    ) -> Dict[str, Any]:
        intro_path = str(content_pack.get("intro_voice_path") or "").strip()
        scene_paths = [str(item or "").strip() for item in list(content_pack.get("clip_voice_paths") or [])]
        scene_durations = [
            max(0.0, float(item or 0.0))
            for item in list(content_pack.get("_normalized_clip_durations") or [])
        ]
        trust_duration = max(0.0, float(content_pack.get("_effective_trust_duration") or 0.0))

        audio_inputs = []
        placements = []
        if intro_path and Path(intro_path).is_file():
            audio_inputs.append(intro_path)
            placements.append((len(audio_inputs), 0.0, "intro"))

        # Sprint193-20: exact final scene start timing.
        cursor = trust_duration
        for idx, scene_path in enumerate(scene_paths):
            scene_start = cursor
            if scene_path and Path(scene_path).is_file():
                audio_inputs.append(scene_path)
                placements.append((len(audio_inputs), scene_start, f"scene_{idx+1}"))
            if idx < len(scene_durations):
                cursor += scene_durations[idx]

        if not placements:
            return {"ok": False, "status": "scene_voice_missing", "output_path": ""}

        command = ["ffmpeg", "-y", "-i", str(input_path)]
        for audio_path in audio_inputs:
            command.extend(["-i", audio_path])

        filters = []
        labels = []
        for input_index, start_sec, label_name in placements:
            delay_ms = max(0, int(round(start_sec * 1000)))
            label = f"v{input_index}"
            filters.append(
                f"[{input_index}:a]aresample=48000,volume=1.0,"
                f"adelay={delay_ms}|{delay_ms}[{label}]"
            )
            labels.append(f"[{label}]")

        filters.append(
            "".join(labels)
            + f"amix=inputs={len(labels)}:duration=longest:normalize=0,"
              f"apad,atrim=0:{duration:.6f},alimiter=limit=0.95[a]"
        )

        command.extend([
            "-filter_complex", ";".join(filters),
            "-map", "0:v:0", "-map", "[a]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-t", f"{duration:.6f}", "-movflags", "+faststart",
            str(output_path),
        ])
        completed = self._run(command)
        ok = completed.returncode == 0 and self._valid_file(output_path)
        return {
            "ok": ok,
            "status": "per_scene_voice_applied" if ok else "per_scene_voice_failed",
            "output_path": str(output_path) if ok else "",
            "placements": [
                {"start": start, "label": label}
                for _, start, label in placements
            ],
            "overlap_guard": True,
            "errors": [] if ok else [completed.stderr[-3000:]],
        }

    def _apply_voice(self, input_path: Path, audio_path: Path, output_path: Path, duration: float) -> Dict[str, Any]:
        command = [
            "ffmpeg", "-y", "-i", str(input_path), "-i", str(audio_path),
            "-filter_complex", f"[1:a]aresample=48000,apad,atrim=0:{duration:.6f},volume=1.0[a]",
            "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-t", f"{duration:.6f}", "-movflags", "+faststart", str(output_path),
        ]
        completed = self._run(command)
        ok = completed.returncode == 0 and self._valid_file(output_path)
        return {"ok": ok, "status": "manual_jian_voice_applied" if ok else "manual_voice_failed", "output_path": str(output_path) if ok else "", "audio_path": str(audio_path), "errors": [] if ok else [completed.stderr[-2500:]]}

    def _apply_bgm(self, input_path: Path, audio_path: Path, output_path: Path, duration: float) -> Dict[str, Any]:
        """외부 BGM을 더 또렷하게 넣고, 내레이션 구간에서는 자동 Ducking 합니다."""
        has_audio = self._has_audio(input_path)
        bgm_volume = 0.20
        if has_audio:
            filter_complex = (
                f"[0:a]aresample=48000,volume=1.0,asplit=2[voice][side];"
                f"[1:a]aresample=48000,volume={bgm_volume:.2f},atrim=0:{duration:.6f},"
                f"afade=t=in:st=0:d=0.45,afade=t=out:st={max(0.0, duration-0.8):.6f}:d=0.8[bgm];"
                f"[bgm][side]sidechaincompress=threshold=0.025:ratio=8:attack=18:release=260:makeup=1[ducked];"
                f"[voice][ducked]amix=inputs=2:duration=first:dropout_transition=2:normalize=0,"
                f"alimiter=limit=0.95[a]"
            )
        else:
            filter_complex = (
                f"[1:a]aresample=48000,volume={bgm_volume:.2f},atrim=0:{duration:.6f},"
                f"afade=t=in:st=0:d=0.45,afade=t=out:st={max(0.0, duration-0.8):.6f}:d=0.8,"
                f"alimiter=limit=0.95[a]"
            )
        command = [
            "ffmpeg", "-y", "-i", str(input_path), "-stream_loop", "-1", "-i", str(audio_path),
            "-filter_complex", filter_complex, "-map", "0:v:0", "-map", "[a]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{duration:.6f}",
            "-movflags", "+faststart", str(output_path),
        ]
        completed = self._run(command)
        ok = completed.returncode == 0 and self._valid_file(output_path)
        return {
            "ok": ok,
            "status": "bgm_ducking_mixed" if ok else "bgm_ducking_failed",
            "output_path": str(output_path) if ok else "",
            "audio_path": str(audio_path),
            "bgm_volume": bgm_volume,
            "voice_ducking": bool(has_audio),
            "ducking_ratio": 8 if has_audio else 0,
            "errors": [] if ok else [completed.stderr[-3000:]],
        }

    def _apply_generated_bgm(self, input_path: Path, output_path: Path, duration: float, channel_type: str) -> Dict[str, Any]:
        """BGM 파일이 없을 때도 들리는 합성 루프를 만들고 음성 기준 Ducking을 적용합니다."""
        has_audio = self._has_audio(input_path)
        channel = str(channel_type or "shopping").lower()
        if channel == "emotional":
            tones = "sine=frequency=220:sample_rate=48000:duration={d},volume=0.075[a1];sine=frequency=329.63:sample_rate=48000:duration={d},volume=0.052[a2]"
        elif channel == "history":
            tones = "sine=frequency=146.83:sample_rate=48000:duration={d},volume=0.070[a1];sine=frequency=220:sample_rate=48000:duration={d},volume=0.045[a2]"
        else:
            tones = "sine=frequency=261.63:sample_rate=48000:duration={d},volume=0.095[a1];sine=frequency=392:sample_rate=48000:duration={d},volume=0.065[a2]"
        tones = tones.format(d=f"{duration:.6f}")
        filters = [
            tones,
            f"[a1][a2]amix=inputs=2:normalize=0,highpass=f=100,lowpass=f=5000,"
            f"afade=t=in:st=0:d=0.35,afade=t=out:st={max(0.0,duration-0.7):.6f}:d=0.7[bgm]",
        ]
        if has_audio:
            filters.append("[0:a]aresample=48000,volume=1.0,asplit=2[voice][side]")
            filters.append("[bgm][side]sidechaincompress=threshold=0.025:ratio=8:attack=18:release=260:makeup=1[ducked]")
            filters.append("[voice][ducked]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]")
        else:
            filters.append("[bgm]alimiter=limit=0.95[a]")
        command = [
            "ffmpeg", "-y", "-i", str(input_path), "-filter_complex", ";".join(filters),
            "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-t", f"{duration:.6f}", "-movflags", "+faststart", str(output_path),
        ]
        completed = self._run(command)
        ok = completed.returncode == 0 and self._valid_file(output_path) and self._has_audio(output_path)
        return {
            "ok": ok,
            "status": "generated_bgm_ducking_mixed" if ok else "generated_bgm_failed",
            "output_path": str(output_path) if ok else "",
            "channel_type": channel,
            "audible_volume": 0.16,
            "voice_ducking": bool(has_audio),
            "ducking_ratio": 8 if has_audio else 0,
            "errors": [] if ok else [completed.stderr[-3000:]],
        }

    def _apply_effects(self, input_path: Path, output_path: Path, duration: float, cue_times: Sequence[Tuple[str, float]]) -> Dict[str, Any]:
        """Sprint193-23: SFX 순간에 원음 ducking + 선명한 합성 pop을 전면 배치합니다."""
        has_audio = self._has_audio(input_path)
        command = ["ffmpeg", "-y", "-i", str(input_path)]
        filters: List[str] = []
        labels: List[str] = []

        cue_list = [(str(kind or "").strip().lower(), float(time_sec or 0.0)) for kind, time_sec in list(cue_times or [])]

        # SFX가 울리는 짧은 순간에는 나레이션/BGM을 32%까지 낮춰 효과음이 묻히지 않게 합니다.
        duck_windows = []
        for kind, time_sec in cue_list:
            if kind == "pop":
                duck_windows.append((max(0.0, time_sec - 0.04), min(duration, time_sec + 0.28)))
            elif kind in {"click", "mouse_click"}:
                duck_windows.append((max(0.0, time_sec - 0.03), min(duration, time_sec + 0.16)))
            elif kind == "whoosh":
                duck_windows.append((max(0.0, time_sec - 0.03), min(duration, time_sec + 0.36)))
            else:
                duck_windows.append((max(0.0, time_sec - 0.03), min(duration, time_sec + 0.24)))

        if has_audio:
            if duck_windows:
                expr = "+".join(
                    f"between(t\\,{start:.3f}\\,{end:.3f})"
                    for start, end in duck_windows
                )
                filters.append(
                    f"[0:a]aresample=48000,"
                    f"volume='if(gt({expr}\\,0)\\,0.32\\,1.0)':eval=frame[base]"
                )
            else:
                filters.append("[0:a]aresample=48000,volume=1.0[base]")
        else:
            filters.append(f"anullsrc=r=48000:cl=mono,atrim=0:{duration:.6f}[base]")
        labels.append("[base]")

        selected = []
        input_index = 1

        for idx, (kind, time_sec) in enumerate(cue_list, start=1):
            resolved = self.sfx_manager.resolve(kind)
            delay_ms = max(0, int(round(time_sec * 1000)))
            label = f"sfx{idx}"
            path = str(resolved.get("path") or "")

            # Hook POP은 asset 음량 편차를 없애기 위해 항상 합성음으로 만듭니다.
            # 860Hz + 1320Hz의 짧은 이중 톤 + 아주 짧은 저역 임팩트.
            if kind == "pop":
                tone1 = f"{label}a"
                tone2 = f"{label}b"
                tone3 = f"{label}c"
                filters.append(
                    f"sine=frequency=860:sample_rate=48000:duration=0.16,"
                    f"volume=1.55,afade=t=out:st=0.035:d=0.125,"
                    f"adelay={delay_ms}|{delay_ms}[{tone1}]"
                )
                filters.append(
                    f"sine=frequency=1320:sample_rate=48000:duration=0.11,"
                    f"volume=1.20,afade=t=out:st=0.02:d=0.09,"
                    f"adelay={delay_ms}|{delay_ms}[{tone2}]"
                )
                filters.append(
                    f"sine=frequency=150:sample_rate=48000:duration=0.13,"
                    f"volume=0.90,afade=t=out:st=0.02:d=0.11,"
                    f"adelay={delay_ms}|{delay_ms}[{tone3}]"
                )
                filters.append(
                    f"[{tone1}][{tone2}][{tone3}]"
                    f"amix=inputs=3:normalize=0,"
                    f"highpass=f=90,alimiter=limit=0.96[{label}]"
                )
            elif path and Path(path).is_file():
                command.extend(["-i", path])
                trim_end = 1.35 if kind == "keyboard_typing" else 0.55
                filters.append(
                    f"[{input_index}:a]aresample=48000,volume=1.65,"
                    f"atrim=0:{trim_end:.2f},adelay={delay_ms}|{delay_ms},"
                    f"alimiter=limit=0.96[{label}]"
                )
                input_index += 1
            elif kind == "whoosh":
                filters.append(
                    f"anoisesrc=color=pink:amplitude=0.95:d=0.36:r=48000,"
                    f"highpass=f=350,lowpass=f=6500,"
                    f"volume=1.45,"
                    f"afade=t=in:st=0:d=0.02,afade=t=out:st=0.11:d=0.20,"
                    f"adelay={delay_ms}|{delay_ms}[{label}]"
                )
            elif kind in {"click", "mouse_click"}:
                frequency = 2400 if kind == "mouse_click" else 1900
                filters.append(
                    f"sine=frequency={frequency}:sample_rate=48000:duration=0.12,"
                    f"volume=2.00,afade=t=out:st=0.02:d=0.10,"
                    f"adelay={delay_ms}|{delay_ms}[{label}]"
                )
            elif kind == "keyboard_typing":
                filters.append(
                    f"anoisesrc=color=white:amplitude=0.34:d=1.20:r=48000,"
                    f"highpass=f=1400,lowpass=f=7200,"
                    f"tremolo=f=8.5:d=0.92,volume=1.20,"
                    f"afade=t=in:st=0:d=0.03,afade=t=out:st=0.95:d=0.22,"
                    f"adelay={delay_ms}|{delay_ms}[{label}]"
                )
            else:
                filters.append(
                    f"sine=frequency=260:sample_rate=48000:duration=0.20,"
                    f"volume=1.75,afade=t=out:st=0.03:d=0.17,"
                    f"adelay={delay_ms}|{delay_ms}[{label}]"
                )

            labels.append(f"[{label}]")
            selected.append({
                "kind": kind,
                "time": time_sec,
                "source": "generated_pop_v23" if kind == "pop" else resolved.get("source"),
                "path": "" if kind == "pop" else path,
            })

        filters.append(
            "".join(labels)
            + f"amix=inputs={len(labels)}:duration=first:normalize=0,"
              f"alimiter=limit=0.96[a]"
        )

        command.extend([
            "-filter_complex", ";".join(filters),
            "-map", "0:v:0", "-map", "[a]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "256k",
            "-t", f"{duration:.6f}",
            "-movflags", "+faststart",
            str(output_path),
        ])
        completed = self._run(command)
        ok = (
            completed.returncode == 0
            and self._valid_file(output_path)
            and self._has_audio(output_path)
        )
        print(
            "[Sprint193-33 SFX MIX]",
            {
                "ok": ok,
                "cue_times": list(cue_times),
                "duck_windows": duck_windows,
                "selected": selected,
            },
            flush=True,
        )
        return {
            "ok": ok,
            "status": "audible_sfx_ducked_mix" if ok else "sfx_failed",
            "output_path": str(output_path) if ok else "",
            "cue_times": list(cue_times),
            "duck_windows": duck_windows,
            "selected": selected,
            "errors": [] if ok else [completed.stderr[-3000:]],
        }


    def _apply_generated_effects_legacy(self, input_path: Path, output_path: Path, duration: float, cue_times: Sequence[Tuple[str, float]]) -> Dict[str, Any]:
        has_audio = self._has_audio(input_path)
        inputs = ["-i", str(input_path)]
        filters: List[str] = []
        mix_labels: List[str] = []
        if has_audio:
            filters.append("[0:a]aresample=48000,volume=1.0[base]")
        else:
            filters.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{duration:.6f}[base]")
        mix_labels.append("[base]")

        for idx, (kind, time_sec) in enumerate(cue_times, start=1):
            delay_ms = max(0, int(round(time_sec * 1000)))
            label = f"sfx{idx}"
            if kind == "whoosh":
                # 짧은 노이즈 스윕
                filters.append(
                    f"anoisesrc=color=white:amplitude=0.16:d=0.22:r=48000,"
                    f"highpass=f=500,lowpass=f=5000,afade=t=in:st=0:d=0.03,afade=t=out:st=0.10:d=0.12,"
                    f"adelay={delay_ms}|{delay_ms}[{label}]"
                )
            elif kind == "click":
                filters.append(
                    f"sine=frequency=1500:sample_rate=48000:duration=0.08,volume=0.20,"
                    f"afade=t=out:st=0.02:d=0.06,adelay={delay_ms}|{delay_ms}[{label}]"
                )
            else:  # pop / impact
                filters.append(
                    f"sine=frequency=220:sample_rate=48000:duration=0.16,volume=0.24,"
                    f"afade=t=out:st=0.03:d=0.13,adelay={delay_ms}|{delay_ms}[{label}]"
                )
            mix_labels.append(f"[{label}]")
        filters.append("".join(mix_labels) + f"amix=inputs={len(mix_labels)}:duration=first:normalize=0[a]")
        command = ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{duration:.6f}", "-movflags", "+faststart", str(output_path)]
        completed = self._run(command)
        ok = completed.returncode == 0 and self._valid_file(output_path)
        return {"ok": ok, "status": "generated_sfx_mixed" if ok else "generated_sfx_failed", "output_path": str(output_path) if ok else "", "cue_times": list(cue_times), "errors": [] if ok else [completed.stderr[-3000:]]}

    def _apply_full_script_subtitles(self, input_path: Path, output_path: Path, content_pack: Dict[str, Any], full_script: str, duration: float, clip_count: int) -> Dict[str, Any]:
        cues = self._subtitle_cues(content_pack, full_script, duration, clip_count)
        if not cues:
            return {"ok": False, "status": "subtitle_cues_missing", "output_path": ""}
        ass_path = self.subtitle_dir / f"{output_path.stem}.ass"
        ass_path.parent.mkdir(parents=True, exist_ok=True)
        ass_path.write_text(self._build_ass(cues, content_pack), encoding="utf-8-sig")
        ass_filter = self._ffmpeg_filter_path(ass_path)
        command = [
            "ffmpeg", "-y", "-i", str(input_path), "-vf", f"ass='{ass_filter}'",
            "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
            "-c:a", "copy", "-movflags", "+faststart", str(output_path),
        ]
        completed = self._run(command)
        ok = completed.returncode == 0 and self._valid_file(output_path)
        return {
            "ok": ok,
            "status": "hook_cta_premium_subtitles_applied" if ok else "subtitle_burn_failed",
            "output_path": str(output_path) if ok else "",
            "ass_path": str(ass_path),
            "subtitle_count": len(cues),
            "trust_intro_subtitle_suppressed": True,
            "full_cta_restored": False,
            "first_cue_is_separate_hook": bool(cues and cues[0][3] == "HookPremium"),
            "hook_text": cues[0][2] if cues and cues[0][3] == "HookPremium" else "",
            "visible_backslash_removed": True,
            "sentence_based": True,
            "per_clip_subtitles_used": bool(list(content_pack.get("clip_subtitles") or [])),
            "clip_subtitle_count": len(list(content_pack.get("clip_subtitles") or [])),
            "subtitle_style": dict(content_pack.get("subtitle_style") or {}),
            "errors": [] if ok else [completed.stderr[-3000:]],
        }

    @classmethod
    def _cta_text(cls, content_pack: Dict[str, Any]) -> str:
        # Sprint193-14: 영상 CTA 완전 비활성화.
        return ""

    @classmethod
    def _platform_cta_text(cls, content_pack: Dict[str, Any]) -> str:
        return ""

    @classmethod
    def _full_script(cls, content_pack: Dict[str, Any]) -> str:
        hook, body = cls._resolve_hook_and_body(content_pack)
        return "\n\n".join(part for part in (hook, body) if part)

    @classmethod
    def _clean_trust_and_cta_text(cls, value: Any) -> str:
        """수치가 포함된 Trust 문장과 중복 CTA만 제거하고 일반 리뷰 문장은 보존합니다."""
        text = cls._sanitize_subtitle_text(value)
        if not text:
            return ""
        trust_pattern = re.compile(
            r"(?:최근\s*한\s*달|구매|평점|리뷰)[^.!?。！？\n]*"
            r"(?:\d[\d,]*\s*(?:명|개)|\d+(?:\.\d+)?\s*점)",
            re.IGNORECASE,
        )
        cta_pattern = re.compile(
            r"(?:궁금하시면\s*클릭|구매\s*링크|설명란|고정\s*댓글|링크는)", re.IGNORECASE
        )
        kept: List[str] = []
        for sentence in cls._sentences(text):
            clean = re.sub(r"\s+", " ", sentence).strip()
            if not clean or trust_pattern.search(clean) or cta_pattern.search(clean):
                continue
            kept.append(clean)
        return "\n".join(kept).strip()

    @classmethod
    def _resolve_hook_and_body(cls, content_pack: Dict[str, Any]) -> Tuple[str, str]:
        """명시 후킹이 없으면 잠금 대본의 첫 유효 문장을 후킹으로 자동 복구합니다."""
        explicit_hook = cls._clean_trust_and_cta_text(
            content_pack.get("hook_text") or content_pack.get("hook") or ""
        )
        raw_body = (
            content_pack.get("locked_script")
            or content_pack.get("body_script")
            or content_pack.get("narration_text")
            or content_pack.get("script")
            or content_pack.get("short_script")
            or ""
        )
        cleaned_body = cls._clean_trust_and_cta_text(raw_body)
        body_sentences = cls._sentences(cleaned_body)

        hook = explicit_hook.strip()
        if not hook and body_sentences:
            hook = body_sentences.pop(0).strip()
        if not hook:
            hook = "실제 후기를 살펴보면"
        elif hook and body_sentences:
            normalized_hook = re.sub(r"\W+", "", hook).lower()
            normalized_first = re.sub(r"\W+", "", body_sentences[0]).lower()
            if normalized_hook and (
                normalized_first == normalized_hook
                or normalized_first.startswith(normalized_hook)
                or normalized_hook.startswith(normalized_first)
            ):
                body_sentences.pop(0)

        body = "\n".join(body_sentences).strip()
        return hook, body

    @staticmethod
    def _trust_line(content_pack: Dict[str, Any]) -> str:
        monthly, review, rating = VideoPipeline._trust_values(content_pack)
        parts = []
        if monthly > 0:
            parts.append(f"최근 한 달 {monthly:,}명 이상이 구매!")
        if rating > 0:
            parts.append(f"평점 {rating:.1f}점!")
        if review > 0:
            parts.append(f"리뷰 {review:,}개!")
        return " ".join(parts)

    @staticmethod
    def _sentences(text: str) -> List[str]:
        text = str(text or "").replace("\r", "\n")
        paragraphs = [re.sub(r"\s+", " ", p).strip() for p in text.split("\n") if re.sub(r"\s+", " ", p).strip()]
        sentences: List[str] = []
        for paragraph in paragraphs:
            parts = re.split(r"(?<=[.!?。！？])\s+", paragraph)
            for part in parts:
                clean = part.strip()
                if clean:
                    sentences.append(clean)
        return sentences

    @staticmethod
    def _sanitize_subtitle_text(text: str) -> str:
        """화면에 노출되는 역슬래시와 잘못 이스케이프된 줄바꿈을 정리합니다."""
        value = str(text or "").replace("\r", "")
        value = value.replace("\\\\N", "\n")
        value = value.replace("\\N", "\n")
        value = value.replace("\\n", "\n")
        value = value.replace("\\", "")
        value = re.sub(r"[ \t]+", " ", value)
        value = re.sub(r" *\n *", "\n", value)
        return value.strip()

    @classmethod
    def _manual_two_line_subtitle(cls, text: str) -> str:
        clean = cls._sanitize_subtitle_text(text)
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in clean.split("\n")]
        lines = [line for line in lines if line]
        if not lines:
            return ""
        if len(lines) == 1:
            return lines[0]
        # 사용자가 엔터로 나눈 문장을 그대로 1줄/2줄로 게시합니다.
        # 3줄 이상 입력되어도 화면에는 앞의 2줄만 사용합니다.
        return "\n".join(lines[:2])

    @classmethod
    def _wrap_sentence(cls, text: str, max_chars: int = 18) -> str:
        clean = cls._sanitize_subtitle_text(text)
        source_lines = [line.strip() for line in clean.split("\n") if line.strip()] or [clean]
        output: List[str] = []
        for source in source_lines:
            words = source.split()
            if not words:
                continue
            current = ""
            for word in words:
                candidate = word if not current else current + " " + word
                if len(candidate) <= max_chars:
                    current = candidate
                else:
                    if current:
                        output.append(current)
                    current = word
            if current:
                output.append(current)
        return "\n".join(output)

    def _subtitle_cues(self, content_pack: Dict[str, Any], full_script: str, duration: float, clip_count: int) -> List[Tuple[float, float, str, str]]:
        suppress_separate_hook = bool(content_pack.get("suppress_separate_hook"))
        if suppress_separate_hook:
            hook = ""
            raw_body = (
                content_pack.get("locked_script")
                or content_pack.get("body_script")
                or content_pack.get("narration_text")
                or content_pack.get("script")
                or content_pack.get("short_script")
                or ""
            )
            body = self._clean_trust_and_cta_text(raw_body)
        else:
            hook, body = self._resolve_hook_and_body(content_pack)
        cues: List[Tuple[float, float, str, str]] = []

        trust_duration = max(0.0, float(content_pack.get("_effective_trust_duration") or 0.0))
        first_scene_end = min(duration, trust_duration)

        # Sprint193-9: Trust Intro 뒤에 사용자가 입력한 후킹멘트를 별도 표시합니다.
        hook = self._sanitize_subtitle_text(hook).strip()

        clip_subtitles = [
            self._sanitize_subtitle_text(item).strip()
            for item in list(content_pack.get("clip_subtitles") or [])
        ]
        if clip_subtitles:
            body_sentences = []
            subtitle_source = "per_clip_manual"
        else:
            body_sentences = self._sentences(body) if body else []
            subtitle_source = "auto_locked_script"

        print(
            "[Sprint193-20 Subtitle Source]",
            {
                "source": subtitle_source,
                "clip_subtitle_count": len(clip_subtitles),
                "nonempty_clip_subtitle_count": len(
                    [item for item in clip_subtitles if item]
                ),
                "body_cues": len(body_sentences),
                "suppress_separate_hook": suppress_separate_hook,
            },
            flush=True,
        )

        # Sprint193-14: CTA 없음.
        # 리뷰/평점 신뢰 후킹과 후킹멘트는 나레이션 전용이며 자막을 만들지 않습니다.
        body_start = first_scene_end
        body_end = duration

        if clip_subtitles and body_end > body_start + 0.2:
            effective_clip_count = max(
                1,
                int(clip_count or len(clip_subtitles) or 1),
            )
            raw_durations = [
                max(0.05, float(item or 0.0))
                for item in list(content_pack.get("_normalized_clip_durations") or [])
            ]
            if len(raw_durations) < effective_clip_count:
                raw_durations = []
            available_body_duration = max(0.1, body_end - body_start)
            cursor_time = body_start

            for idx in range(effective_clip_count):
                subtitle = (
                    clip_subtitles[idx]
                    if idx < len(clip_subtitles)
                    else ""
                )

                if raw_durations:
                    scene_len = raw_durations[idx]
                else:
                    scene_len = available_body_duration / effective_clip_count

                start_time = cursor_time
                end_time = (
                    body_end
                    if idx == effective_clip_count - 1
                    else min(body_end, cursor_time + scene_len)
                )
                cursor_time = end_time

                if not subtitle:
                    continue
                if end_time > start_time + 0.12:
                    effects = [
                        str(item or "기본").strip()
                        for item in list(content_pack.get("clip_subtitle_effects") or [])
                    ]
                    effect_name = effects[idx] if idx < len(effects) else "기본"
                    effect_key = str(effect_name or "기본").strip().lower()
                    effect_style = {
                        "팝": "SubPop", "pop": "SubPop",
                        "페이드": "SubFade", "fade": "SubFade",
                        "바운스": "SubBounce", "bounce": "SubBounce",
                        "강조": "SubBounce", "highlight": "SubBounce",
                    }.get(effect_key, "Default")
                    print("[Sprint193-20 Subtitle Effect]", {"scene": idx + 1, "selected": effect_name, "ass_style": effect_style}, flush=True)
                    print(
                        "[Sprint193-20 Subtitle Timeline]",
                        {"scene": idx + 1, "start": round(start_time, 3), "end": round(end_time, 3)},
                        flush=True,
                    )
                    cues.append(
                        (
                            start_time,
                            end_time,
                            self._manual_two_line_subtitle(subtitle),
                            effect_style,
                        )
                    )

        # Sprint193-24: 마지막 수동 CTA 장면에만 상품명 로고 자막.
        if clip_subtitles:
            last_text = str(clip_subtitles[-1] or "").strip()
            cta_tokens = ("프로필", "링크", "만나보세요", "확인하세요", "구매")
            if any(token in last_text for token in cta_tokens):
                product_logo_text = str(
                    content_pack.get("cta_product_logo_text")
                    or ""
                ).strip()

                # Sprint193-32: 미소랩 워터탭은 2줄 로고형으로 표시.
                # 1줄: 미소랩 / 2줄: 스윙글 워터탭
                if product_logo_text == "미소랩 스윙글 워터탭":
                    product_logo_text = "미소랩\\N스윙글 워터탭"

                if product_logo_text:
                    effective_clip_count = max(1, int(clip_count or len(clip_subtitles) or 1))
                    raw_durations = [
                        max(0.0, float(item or 0.0))
                        for item in list(content_pack.get("_normalized_clip_durations") or [])
                    ]
                    if raw_durations:
                        logo_start = body_start + sum(raw_durations[:max(0, effective_clip_count - 1)])
                        last_idx = min(effective_clip_count - 1, len(raw_durations) - 1)
                        logo_end = min(duration, logo_start + raw_durations[last_idx])
                    else:
                        logo_start = body_start
                        logo_end = body_end

                    if logo_end > logo_start + 0.05:
                        # Sprint193-30:
                        # 자막 cue에는 순수 텍스트만 넣습니다.
                        # ASS 팅팅팅/색상 태그는 최종 렌더 단계에서만 붙입니다.
                        cues.append((logo_start, logo_end, product_logo_text, "CTALogo"))
                        print(
                            "[Sprint193-33 CTA Product Logo]",
                            {
                                "text": product_logo_text,
                                "start": round(float(logo_start), 3),
                                "end": round(float(logo_end), 3),
                            },
                            flush=True,
                        )

        elif body_sentences and body_end > body_start + 0.2:
            available = body_end - body_start
            weights = [max(6, len(re.sub(r"\s+", "", t))) for t in body_sentences]
            total = sum(weights) or 1
            cursor = body_start
            for idx, (sentence, weight) in enumerate(zip(body_sentences, weights)):
                segment = available * weight / total
                end_time = body_end if idx == len(body_sentences) - 1 else min(body_end, cursor + max(0.8, segment))
                if end_time > cursor + 0.12:
                    cues.append((cursor, end_time, self._wrap_sentence(sentence, 18), "Default"))
                cursor = end_time

        return cues

    @staticmethod
    def _ass_time(seconds: float) -> str:
        seconds = max(0.0, float(seconds))
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h}:{m:02d}:{s:05.2f}"

    @staticmethod
    def _hex_to_ass_colour(value: Any, alpha: int = 0) -> str:
        text = str(value or "").strip().lstrip("#")
        if not re.fullmatch(r"[0-9A-Fa-f]{6}", text):
            text = "FFFFFF"
        r = text[0:2]
        g = text[2:4]
        b = text[4:6]
        alpha = max(0, min(255, int(alpha)))
        return f"&H{alpha:02X}{b.upper()}{g.upper()}{r.upper()}"

    @classmethod
    def _subtitle_style_values(cls, content_pack: Dict[str, Any]) -> Dict[str, Any]:
        raw = dict(content_pack.get("subtitle_style") or {})
        try:
            font_size = max(32, min(140, int(raw.get("font_size", 76))))
        except Exception:
            font_size = 76
        try:
            outline = max(0, min(30, int(raw.get("outline", 6))))
        except Exception:
            outline = 6
        try:
            opacity = max(0, min(100, int(raw.get("background_opacity", 10))))
        except Exception:
            opacity = 10

        # UI의 '배경 진하기'는 0=투명, 100=불투명.
        ass_alpha = round(255 * (1.0 - opacity / 100.0))
        return {
            "font": str(raw.get("font") or "Gmarket Sans Bold").strip(),
            "font_size": font_size,
            "outline": outline,
            "text_color": cls._hex_to_ass_colour(raw.get("text_color") or "#FFFFFF", 0),
            "background_color": cls._hex_to_ass_colour(
                raw.get("background_color") or "#000000",
                ass_alpha,
            ),
            "highlight_color": cls._hex_to_ass_colour(
                raw.get("highlight_color") or "#FFD700",
                0,
            ),
            "background_opacity": opacity,
        }

    @classmethod
    def _apply_highlight_markup(cls, text: str, highlight_ass: str) -> str:
        """[[문구]] 부분만 강조색으로 렌더링하고 괄호는 화면에서 제거합니다."""
        clean = str(text or "")
        pattern = re.compile(r"\[\[(.+?)\]\]")
        return pattern.sub(
            lambda match: (
                r"{\c" + highlight_ass + "}"
                + match.group(1)
                + r"{\c}"
            ),
            clean,
        )

    def _build_ass(self, cues: Sequence[Tuple[float, float, str, str]], content_pack: Dict[str, Any] = None) -> str:
        style_values = self._subtitle_style_values(dict(content_pack or {}))
        print(
            "[Sprint191-21 Subtitle Render Style]",
            style_values,
            flush=True,
        )
        default_style = (
            "Style: Default,"
            f"{style_values['font']},"
            f"{style_values['font_size']},"
            f"{style_values['text_color']},"
            "&H000000FF,"
            "&H00000000,"
            "&HFF000000,"
            "-1,0,0,0,100,100,0,0,1,"
            f"{style_values['outline']},"
            "0,2,120,250,560,1"
        )
        body_bg_style = (
            "Style: BodyBG,"
            f"{style_values['font']},"
            f"{style_values['font_size']},"
            "&HFFFFFFFF,"
            "&HFFFFFFFF,"
            f"{style_values['background_color']},"
            f"{style_values['background_color']},"
            "-1,0,0,0,100,100,0,0,3,"
            "10,0,2,120,250,560,1"
        )

        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
{default_style}
{body_bg_style}
Style: SubPop,{style_values['font']},{style_values['font_size']},{style_values['text_color']},&H000000FF,&H00000000,&HFF000000,-1,0,0,0,100,100,0,0,1,{style_values['outline']},0,2,120,250,560,1
Style: SubFade,{style_values['font']},{style_values['font_size']},{style_values['text_color']},&H000000FF,&H00000000,&HFF000000,-1,0,0,0,100,100,0,0,1,{style_values['outline']},0,2,120,250,560,1
Style: SubBounce,{style_values['font']},{style_values['font_size']},{style_values['text_color']},&H000000FF,&H00000000,&HFF000000,-1,0,0,0,100,100,0,0,1,{style_values['outline']},0,2,120,250,560,1
Style: HookPremium,Noto Sans CJK KR,62,&H00FFFFFF,&H000000FF,&H0020160D,&H9A2A1608,-1,0,0,0,100,100,0,0,3,3,1,2,130,250,245,1
Style: CTALink,{style_values['font']},50,{style_values['text_color']},&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,6,0,2,150,270,340,1
Style: CTALogo,{style_values['font']},104,{style_values['highlight_color']},&H000000FF,&H001A1A1A,&H30000000,-1,0,0,0,100,100,1,0,1,7,1,8,85,85,230,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
        events: List[str] = []
        for start, end, text, style in cues:
            if style in {"Default", "SubPop", "SubFade", "SubBounce"}:
                # Sprint190-8: [[강조문구]] 마커가 sanitize 단계에서 제거되기 전에
                # 토큰으로 보존한 뒤 ASS 강조색 태그로 복원합니다.
                raw_text = str(text or "")
                highlight_tokens = []
                def _hold_highlight(match):
                    token = f"HLTOKEN{len(highlight_tokens)}END"
                    highlighted_text = match.group(1) if match.group(1) is not None else match.group(2)
                    highlight_tokens.append((token, highlighted_text))
                    return token
                held_text = re.sub(r"\[\[([^\[\]]+?)\]\]|\[([^\[\]]+?)\]", _hold_highlight, raw_text)
                clean = self._sanitize_subtitle_text(held_text)
                escaped = clean.replace("{", r"\{").replace("}", r"\}").replace("\n", r"\N")
                safe_text = escaped
                for token, highlighted in highlight_tokens:
                    highlighted_clean = self._sanitize_subtitle_text(highlighted)
                    highlighted_safe = highlighted_clean.replace("{", r"\{").replace("}", r"\}").replace("\n", r"\N")
                    safe_text = safe_text.replace(
                        token,
                        r"{\c" + style_values["highlight_color"] + "}"
                        + highlighted_safe
                        + r"{\c" + style_values["text_color"] + "}",
                    )
            elif style == "CTALink":
                raw_text = str(text or "")
                highlight_tokens = []
                def _hold_cta_highlight(match):
                    token = f"CTATOKEN{len(highlight_tokens)}END"
                    highlight_tokens.append((token, match.group(1)))
                    return token
                held_text = re.sub(r"\[\[([^\[\]]+?)\]\]", _hold_cta_highlight, raw_text)
                clean = self._sanitize_subtitle_text(held_text)
                safe_text = clean.replace("{", r"\{").replace("}", r"\}").replace("\n", r"\N")
                for token, highlighted in highlight_tokens:
                    highlighted_clean = self._sanitize_subtitle_text(highlighted)
                    highlighted_safe = highlighted_clean.replace("{", r"\{").replace("}", r"\}").replace("\n", r"\N")
                    safe_text = safe_text.replace(
                        token,
                        r"{\fs68\c" + style_values["highlight_color"] + "}"
                        + highlighted_safe
                        + r"{\fs50\c" + style_values["text_color"] + "}",
                    )
            else:
                clean = self._sanitize_subtitle_text(text)
                safe_text = clean.replace("{", r"\{").replace("}", r"\}").replace("\n", r"\N")
            layer = 0
            if style == "SubPop":
                safe_text = (
                    r"{\an2\fscx42\fscy42"
                    r"\t(0,90,\fscx165\fscy165)"
                    r"\t(100,210,\fscx96\fscy96)"
                    r"\t(210,320,\fscx100\fscy100)}" + safe_text
                )
                layer = 2
            elif style == "SubFade":
                safe_text = r"{\alpha&HFF&\t(0,260,\alpha&H00&)\fad(260,160)}" + safe_text
                layer = 2
            elif style == "SubBounce":
                safe_text = (
                    r"{\an2\fscx50\fscy50"
                    r"\t(0,100,\fscx155\fscy155)"
                    r"\t(110,220,\fscx96\fscy96)"
                    r"\t(220,340,\fscx104\fscy104)"
                    r"\t(340,430,\fscx100\fscy100)}" + safe_text
                )
                layer = 2
            elif style == "HookPremium":
                # CapCut식 Punch Pop: 72% -> 132% -> 92% -> 106% -> 100%
                safe_text = (
                    r"{\an2\pos(455,430)\fscx72\fscy72"
                    r"\t(0,95,\fscx132\fscy132)"
                    r"\t(95,185,\fscx92\fscy92)"
                    r"\t(185,270,\fscx106\fscy106)"
                    r"\t(270,350,\fscx100\fscy100)"
                    r"\bord6\shad2}" + safe_text
                )
                layer = 2
            elif style == "CTAButton":
                safe_text = safe_text.replace(
                    "클릭!",
                    r"{\c" + style_values["highlight_color"] + "}클릭!"
                    + r"{\c" + style_values["text_color"] + "}",
                )
                safe_text = (
                    r"{\an2\pos(455,1395)\fscx65\fscy65"
                    r"\t(0,105,\fscx136\fscy136)"
                    r"\t(105,205,\fscx90\fscy90)"
                    r"\t(205,300,\fscx108\fscy108)"
                    r"\t(300,390,\fscx100\fscy100)"
                    r"\bord5\shad1}" + safe_text
                )
                layer = 3
            elif style == "CTALink":
                # Sprint191-13: 본문과 동일한 Gmarket Sans Bold.
                # 제품정보는/에서/확인하세요! = 54, 핵심 링크 문구 = 76 + 강조색.
                safe_text = (
                    r"{\an2\pos(455,1120)\fs50"
                    r"\t(0,180,\fscx104\fscy104)"
                    r"\t(180,280,\fscx100\fscy100)}" + safe_text
                )
                layer = 2
            elif style == "CTALogo":
                # Sprint193-32:
                # 두 줄 로고형 CTA.
                # 한글 텍스트는 그대로 두고, ASS 제어 태그는 sanitize 이후에만 붙입니다.
                # \N이 포함된 경우:
                # 1줄 '미소랩'은 조금 작게, 2줄 '스윙글 워터탭'은 더 크게.
                if r"\N" in safe_text:
                    first_line, second_line = safe_text.split(r"\N", 1)
                    rendered_logo = (
                        r"{\an8\pos(540,405)"
                        r"\c" + style_values["highlight_color"]
                        + r"\bord7\shad1"
                        r"\fscx45\fscy45"
                        r"\t(0,90,\fscx145\fscy145)"
                        r"\t(90,180,\fscx96\fscy96)"
                        r"\t(180,270,\fscx132\fscy132)"
                        r"\t(270,360,\fscx98\fscy98)"
                        r"\t(360,450,\fscx118\fscy118)"
                        r"\t(450,540,\fscx100\fscy100)"
                        r"\fs78}"
                        + first_line
                        + r"\N"
                        + r"{\fs108}"
                        + second_line
                    )
                else:
                    rendered_logo = (
                        r"{\an8\pos(540,410)"
                        r"\c" + style_values["highlight_color"]
                        + r"\bord7\shad1"
                        r"\fscx45\fscy45"
                        r"\t(0,90,\fscx145\fscy145)"
                        r"\t(90,180,\fscx96\fscy96)"
                        r"\t(180,270,\fscx132\fscy132)"
                        r"\t(270,360,\fscx98\fscy98)"
                        r"\t(360,450,\fscx118\fscy118)"
                        r"\t(450,540,\fscx100\fscy100)}"
                        + safe_text
                    )

                safe_text = rendered_logo
                layer = 4
                print(
                    "[Sprint193-33 CTA Logo Render]",
                    {
                        "text": clean,
                        "color": style_values["highlight_color"],
                        "line1_font_size": 78 if r"\N" in clean else 104,
                        "line2_font_size": 108 if r"\N" in clean else 104,
                        "position": {"x": 540, "y": 405 if r"\N" in clean else 410},
                        "effect": "ting3_scale_group",
                    },
                    flush=True,
                )

            if style == "CTALink":
                # Sprint191-15: CTA 배경은 글자 모양을 따라가는 박스가 아니라
                # CTA 3줄 전체를 감싸는 하나의 고정 크기 카드입니다.
                card = (
                    r"{\an7\pos(0,0)\p1\bord0\shad0"
                    r"\1c&H000000&\1a&HAA&}"
                    r"m 145 930 l 935 930 l 935 1295 l 145 1295"
                )
                events.append(
                    f"Dialogue: 0,{self._ass_time(start)},{self._ass_time(end)},Default,,0,0,0,,{card}"
                )
                layer = max(layer, 2)
            if style in {"Default", "SubPop", "SubFade", "SubBounce"} and style_values["background_opacity"] > 0:
                bg_text = self._sanitize_subtitle_text(text)
                bg_text = re.sub(
                    r"\[\[([^\[\]]+?)\]\]|\[([^\[\]]+?)\]",
                    lambda m: m.group(1) or m.group(2),
                    bg_text,
                )
                bg_text = bg_text.replace("{", r"\{").replace("}", r"\}").replace("\n", r"\N")
                events.append(
                    f"Dialogue: 0,{self._ass_time(start)},{self._ass_time(end)},BodyBG,,0,0,0,,{bg_text}"
                )
                layer = max(layer, 1)
            resolved_layer = max(layer, 4) if style == "CTALogo" else (max(layer, 3) if style == "CTALink" else layer)
            events.append(f"Dialogue: {resolved_layer},{self._ass_time(start)},{self._ass_time(end)},{style},,0,0,0,,{safe_text}")
        return header + "\n".join(events) + "\n"

    @staticmethod
    def _effect_cue_times(duration: float, clip_count: int, full_script: str, content_pack: Dict[str, Any] = None) -> List[Tuple[str, float]]:
        pack = content_pack or {}
        trust_duration = max(
            0.0,
            float(
                pack.get("_effective_trust_duration")
                if pack.get("_effective_trust_duration") is not None
                else pack.get("trust_card_duration")
                or 0.0
            ),
        )
        selected = [
            str(item or "없음").strip().lower()
            for item in list(pack.get("clip_sfx") or [])
        ]
        clip_count = max(1, int(clip_count or len(selected) or 1))
        scene_durations = [
            max(0.05, float(item or 0.0))
            for item in list(pack.get("_normalized_clip_durations") or [])
        ]

        # Sprint193-22: 후킹 Pop/Scale과 같은 시점에 pop 효과음 3번.
        cues: List[Tuple[str, float]] = []
        hook_pop_times = (0.18, 0.92, 1.58)
        if trust_duration > 0.0:
            for hook_time in hook_pop_times:
                if hook_time < min(duration, trust_duration):
                    cues.append(("pop", hook_time))
        print(
            "[Sprint193-33 Hook Ting3 SFX]",
            {"trust_duration": trust_duration, "pop_times": [t for k, t in cues if k == "pop"]},
            flush=True,
        )

        # Sprint193-26: 마지막 CTA 상단 상품명도 팅팅팅 + pop 3회.
        cta_logo_text = str(pack.get("cta_product_logo_text") or "").strip()
        clip_subtitles = [
            str(item or "").strip()
            for item in list(pack.get("clip_subtitles") or [])
        ]
        if cta_logo_text and clip_subtitles and scene_durations:
            last_text = clip_subtitles[-1]
            if any(token in last_text for token in ("프로필", "링크", "만나보세요", "확인하세요", "구매")):
                cta_start = trust_duration + sum(scene_durations[:-1])
                cta_pop_times = []
                for offset in (0.00, 0.18, 0.36):
                    t = cta_start + offset
                    if 0.0 <= t < duration - 0.05:
                        cues.append(("pop", t))
                        cta_pop_times.append(round(float(t), 3))
                print(
                    "[Sprint193-33 CTA Logo Ting3 SFX]",
                    {
                        "text": cta_logo_text,
                        "cta_start": round(float(cta_start), 3),
                        "pop_times": cta_pop_times,
                    },
                    flush=True,
                )

        cursor = trust_duration
        for idx in range(clip_count):
            kind = selected[idx] if idx < len(selected) else "없음"
            if kind in {"pop", "whoosh", "click", "마우스 클릭", "키보드 타이핑"}:
                internal_kind = {
                    "마우스 클릭": "mouse_click",
                    "키보드 타이핑": "keyboard_typing",
                }.get(kind, kind)
                time_sec = min(duration - 0.15, cursor + 0.06)
                if 0.1 < time_sec < duration - 0.1:
                    cues.append((internal_kind, time_sec))
            if idx < len(scene_durations):
                cursor += scene_durations[idx]
            else:
                remaining = max(0.2, duration - trust_duration)
                cursor += remaining / clip_count

        return cues

    def _resolve_bgm(self, content_pack: Dict[str, Any]) -> str:
        explicit = Path(str(content_pack.get("bgm_audio_path") or ""))
        if explicit.is_file():
            return str(explicit)
        for folder in self._bgm_search_paths(content_pack):
            path = Path(folder)
            if not path.exists():
                continue
            candidates = sorted(
                p for p in path.rglob("*")
                if p.is_file() and p.suffix.lower() in {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
            )
            if candidates:
                return str(candidates[0])
        return ""

    @staticmethod
    def _bgm_search_paths(content_pack: Dict[str, Any]) -> List[str]:
        channel = str(content_pack.get("channel_type") or "shopping").strip().lower()
        aliases = {
            "shopping": ["shopping", "shop", "upbeat"],
            "emotional": ["emotional", "healing", "rise"],
            "history": ["history", "documentary"],
        }
        folders = [Path("assets/bgm") / name for name in aliases.get(channel, [channel])]
        folders.append(Path("assets/bgm"))
        return [str(path) for path in folders]

    @staticmethod
    def _ffmpeg_filter_path(path: Path) -> str:
        value = str(path.resolve()).replace("\\", "/")
        if re.match(r"^[A-Za-z]:", value):
            value = value[0] + r"\:" + value[2:]
        return value.replace("'", r"\'")

    @staticmethod
    def _probe_duration(path: Path) -> float:
        try:
            completed = subprocess.run([
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", str(path),
            ], capture_output=True, text=True, encoding="utf-8", errors="replace")
            return max(0.0, float((completed.stdout or "0").strip() or 0))
        except Exception:
            return 0.0

    @staticmethod
    def _has_audio(path: Path) -> bool:
        completed = subprocess.run([
            "ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=index",
            "-of", "csv=p=0", str(path),
        ], capture_output=True, text=True, encoding="utf-8", errors="replace")
        return bool((completed.stdout or "").strip())

    @staticmethod
    def _run(command: Sequence[str]) -> subprocess.CompletedProcess:
        return subprocess.run(list(command), capture_output=True, text=True, encoding="utf-8", errors="replace")

    @staticmethod
    def _valid_file(path: Path) -> bool:
        return path.is_file() and path.stat().st_size > 1024

    @staticmethod
    def _existing_files(values) -> List[str]:
        seen = set()
        files = []
        for value in list(values or []):
            path = Path(str(value)).expanduser()
            if not path.is_file():
                continue
            key = str(path.resolve()).lower()
            if key in seen:
                continue
            seen.add(key)
            files.append(str(path))
        return files

    @staticmethod
    def _project_id(project, content_pack):
        candidates = []
        if isinstance(project, dict):
            candidates += [project.get("id"), project.get("project_id")]
        elif project is not None:
            candidates += [getattr(project, "id", None), getattr(project, "project_id", None)]
        candidates += [content_pack.get("project_id"), content_pack.get("id")]
        value = next((str(v).strip() for v in candidates if v not in (None, "")), "default")
        return value.replace(" ", "_").replace("/", "_").replace("\\", "_")
