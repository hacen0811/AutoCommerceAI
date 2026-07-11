from typing import Any, Dict, List, Tuple


class CutPlanner:
    """
    Sprint 55
    AI Cut Planner 4.0 / Auto Edit Plan v1

    목표:
    - 기존 cut_plan UI와 완전 호환
    - 기존 CapCut Export 필드 유지
    - 후보 영상별 자동 컷 구간 추천
    - 렌더링 엔진이 바로 사용할 수 있는 숫자형 시간 제공
    - 자막, 화면 효과, 전환, 속도, 카메라, 오디오 편집 명령 생성
    - timeline이 없어도 기본 쇼핑쇼츠 장면 자동 생성
    """

    PLANNER_VERSION = "sprint55-cutplanner-4.0-auto-edit"

    def build(
        self,
        content_pack: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        content_pack = content_pack or {}

        edit = content_pack.get("edit_assistant") or {}

        timeline = (
            edit.get("timeline")
            or edit.get("scene_plan")
            or content_pack.get("timeline")
            or []
        )

        if not timeline:
            timeline = self._default_timeline()

        candidates = (
            content_pack.get("selected_sources")
            or content_pack.get("candidates")
            or []
        )

        video_quality = content_pack.get("video_quality") or {}
        suitability = self._number(
            video_quality.get("suitability_score"),
            default=70,
        )

        plans: List[Dict[str, Any]] = []

        for idx, raw_item in enumerate(timeline, start=1):
            item = raw_item if isinstance(raw_item, dict) else {}

            candidate = self._pick_candidate(
                candidates=candidates,
                scene=idx,
            )

            confidence = self._confidence(
                candidate=candidate,
                video_quality=video_quality,
                suitability=suitability,
            )

            start, end = self._recommend_time(
                confidence=confidence,
                scene=idx,
                item=item,
            )

            start_sec = self._time_to_seconds(start)
            end_sec = self._time_to_seconds(end)

            if end_sec <= start_sec:
                end_sec = start_sec + self._default_duration(idx)
                end = self._seconds_to_time(end_sec)

            duration_sec = round(end_sec - start_sec, 2)

            hook_level = self._hook_level(
                scene=idx,
                confidence=confidence,
            )

            query = self._candidate_query(candidate)
            subtitle_text = self._subtitle_text(
                item=item,
                scene=idx,
            )

            transition = (
                item.get("transition")
                or self._transition(idx, confidence)
            )

            speed = (
                item.get("speed")
                or self._speed(idx, confidence)
            )

            camera = (
                item.get("camera")
                or self._camera(idx, confidence)
            )

            effect = (
                item.get("sfx")
                or item.get("effect")
                or self._effect(idx, confidence)
            )

            zoom = (
                item.get("zoom")
                or self._zoom(idx, confidence)
            )

            subtitle_animation = (
                item.get("subtitle_animation")
                or item.get("subtitle_effect")
                or self._subtitle_animation(idx)
            )

            subtitle_position = (
                item.get("subtitle_position")
                or self._subtitle_position(idx)
            )

            bgm_volume = self._bgm_volume(idx, hook_level)
            source_volume = self._source_volume(idx)
            sfx_volume = self._sfx_volume(effect)

            plan = {
                "planner_version": self.PLANNER_VERSION,
                "scene": idx,
                "purpose": (
                    item.get("purpose")
                    or item.get("role")
                    or self._scene_purpose(idx)
                ),

                # 후보 영상 정보
                "candidate": (
                    candidate.get("platform")
                    or candidate.get("source")
                    or "현재 연결 영상"
                ),
                "candidate_rank": candidate.get("rank", idx),
                "query": query,
                "url": self._candidate_url(candidate),
                "video_path": (
                    candidate.get("video_path")
                    or candidate.get("local_path")
                    or candidate.get("path")
                    or ""
                ),

                # 기존 UI 호환 시간 필드
                "start": start,
                "end": end,

                # 자동 편집/렌더링용 숫자 필드
                "start_sec": start_sec,
                "end_sec": end_sec,
                "duration_sec": duration_sec,

                "confidence": confidence,

                # 기존 UI 호환 필드
                "effect": effect,
                "zoom": zoom,
                "subtitle": subtitle_animation,

                # 자막 편집 정보
                "subtitle_text": subtitle_text,
                "subtitle_position": subtitle_position,
                "subtitle_animation": subtitle_animation,
                "subtitle_emphasis": self._subtitle_emphasis(
                    scene=idx,
                    hook_level=hook_level,
                ),

                # 영상 편집 정보
                "transition": transition,
                "speed": speed,
                "speed_value": self._speed_value(speed),
                "camera": camera,
                "hook_level": hook_level,
                
                # 추가
                "bgm": self._bgm(idx),
                "bgm_volume": self._bgm_volume(idx),
                "sound_effect": self._sound_effect(idx),


                # 오디오 편집 정보
                "audio": {
                    "keep_source_audio": True,
                    "source_volume": source_volume,
                    "bgm_volume": bgm_volume,
                    "sfx": effect,
                    "sfx_volume": sfx_volume,
                    "ducking": self._audio_ducking(idx),
                },

                # 판단 근거
                "reason": self._reason(
                    candidate=candidate,
                    confidence=confidence,
                    suitability=suitability,
                    scene=idx,
                ),
                "edit_note": self._edit_note(
                    scene=idx,
                    hook_level=hook_level,
                ),

                # 향후 FFmpeg/MP4 Renderer가 그대로 읽을 편집 명령
                "edit_actions": {
                    "trim": {
                        "start_sec": start_sec,
                        "end_sec": end_sec,
                        "duration_sec": duration_sec,
                    },
                    "transform": {
                        "zoom": zoom,
                        "camera": camera,
                    },
                    "playback": {
                        "speed": speed,
                        "speed_value": self._speed_value(speed),
                    },
                    "transition": {
                        "type": transition,
                        "duration_sec": self._transition_duration(
                            transition
                        ),
                    },
                    "subtitle": {
                        "text": subtitle_text,
                        "position": subtitle_position,
                        "animation": subtitle_animation,
                        "emphasis": self._subtitle_emphasis(
                            scene=idx,
                            hook_level=hook_level,
                        ),
                    },
                    "audio": {
                        "keep_source_audio": True,
                        "source_volume": source_volume,
                        "bgm_volume": bgm_volume,
                        "sfx": effect,
                        "sfx_volume": sfx_volume,
                        "ducking": self._audio_ducking(idx),
                    },
                },
            }

            plans.append(plan)

        return plans

    def _default_timeline(self) -> List[Dict[str, Any]]:
        """
        AI 콘텐츠 팩에 timeline이 없을 경우에도
        쇼핑쇼츠 기본 7개 장면을 생성한다.
        """
        return [
            {
                "purpose": "후킹 / 첫 시선 집중",
                "subtitle": "잠깐, 이거 아직 모르셨어요?",
            },
            {
                "purpose": "문제 상황 공감",
                "subtitle": "이럴 때마다 정말 불편했죠.",
            },
            {
                "purpose": "제품 등장",
                "subtitle": "이 제품 하나면 해결됩니다.",
            },
            {
                "purpose": "핵심 기능 설명",
                "subtitle": "사용 방법도 정말 간단해요.",
            },
            {
                "purpose": "Before / After",
                "subtitle": "사용 전후 차이를 확인해 보세요.",
            },
            {
                "purpose": "실사용 장면",
                "subtitle": "일상에서 편하게 사용할 수 있어요.",
            },
            {
                "purpose": "CTA / 마무리",
                "subtitle": "제품 정보는 아래에서 확인해 주세요.",
            },
        ]

    def _pick_candidate(
        self,
        candidates: Any,
        scene: int,
    ) -> Dict[str, Any]:
        if not isinstance(candidates, list) or not candidates:
            return {}

        candidate = candidates[(scene - 1) % len(candidates)]

        if not isinstance(candidate, dict):
            return {}

        return candidate

    def _candidate_query(
        self,
        candidate: Dict[str, Any],
    ) -> str:
        return str(
            candidate.get("query")
            or candidate.get("keyword")
            or candidate.get("search_query")
            or candidate.get("title")
            or ""
        ).strip()

    def _candidate_url(
        self,
        candidate: Dict[str, Any],
    ) -> str:
        return str(
            candidate.get("url")
            or candidate.get("video_url")
            or candidate.get("play_url")
            or candidate.get("search_url")
            or ""
        ).strip()

    def _confidence(
        self,
        candidate: Dict[str, Any],
        video_quality: Dict[str, Any],
        suitability: float,
    ) -> int:
        score = 55.0

        candidate_score = self._optional_number(
            candidate.get("score")
        )
        if candidate_score is not None:
            score += candidate_score * 0.25

        quality = self._optional_number(
            video_quality.get("score")
        )
        if quality is not None:
            score += quality * 0.15

        if isinstance(suitability, (int, float)):
            score += suitability * 0.10

        if self._candidate_url(candidate):
            score += 2

        if candidate.get("video_path") or candidate.get("local_path"):
            score += 3

        return int(min(max(score, 50), 99))

    def _recommend_time(
        self,
        confidence: int,
        scene: int,
        item: Dict[str, Any],
    ) -> Tuple[str, str]:
        item_start = (
            item.get("start")
            or item.get("source_start")
            or item.get("start_time")
        )
        item_end = (
            item.get("end")
            or item.get("source_end")
            or item.get("end_time")
        )

        if item_start is not None and item_end is not None:
            return (
                self._normalize_time(item_start),
                self._normalize_time(item_end),
            )

        if scene == 1:
            return "00.0", "03.0"

        if confidence >= 90:
            return "00.5", "04.5"

        if confidence >= 80:
            return "01.0", "05.0"

        if confidence >= 70:
            return "01.5", "05.5"

        return "02.0", "06.0"

    def _scene_purpose(self, scene: int) -> str:
        purposes = {
            1: "후킹 / 첫 시선 집중",
            2: "문제 상황 공감",
            3: "제품 등장",
            4: "핵심 기능 설명",
            5: "Before / After",
            6: "실사용 장면",
            7: "CTA / 마무리",
        }

        return purposes.get(scene, f"Scene {scene}")

    def _subtitle_text(
        self,
        item: Dict[str, Any],
        scene: int,
    ) -> str:
        value = (
            item.get("subtitle_text")
            or item.get("caption")
            or item.get("text")
            or item.get("subtitle")
            or item.get("script")
        )

        if value:
            return str(value).strip()

        defaults = {
            1: "잠깐, 이거 아직 모르셨어요?",
            2: "이럴 때마다 정말 불편했죠.",
            3: "이 제품 하나면 해결됩니다.",
            4: "사용 방법도 정말 간단해요.",
            5: "사용 전후 차이를 확인해 보세요.",
            6: "일상에서 편하게 사용할 수 있어요.",
            7: "제품 정보는 아래에서 확인해 주세요.",
        }

        return defaults.get(scene, "")

    def _hook_level(
        self,
        scene: int,
        confidence: int,
    ) -> str:
        if scene == 1 or confidence >= 90:
            return "High"

        if scene in [2, 3, 4] or confidence >= 80:
            return "Medium"

        return "Low"

    def _transition(
        self,
        scene: int,
        confidence: int,
    ) -> str:
        if scene == 1:
            return "Flash"

        if scene in [2, 3]:
            return "Cut"

        if scene == 5:
            return "Split / Before After"

        if confidence >= 90:
            return "Whip"

        return "None"

    def _transition_duration(self, transition: str) -> float:
        transition_lower = str(transition).lower()

        if transition_lower in {"none", "cut", ""}:
            return 0.0

        if "flash" in transition_lower:
            return 0.15

        if "whip" in transition_lower:
            return 0.20

        if "split" in transition_lower:
            return 0.25

        return 0.20

    def _speed(
        self,
        scene: int,
        confidence: int,
    ) -> str:
        if scene == 1:
            return "1.15x"

        if scene in [2, 3]:
            return "1.05x"

        if confidence >= 90:
            return "1.10x"

        return "1.0x"

    def _speed_value(self, speed: Any) -> float:
        if isinstance(speed, (int, float)):
            return max(float(speed), 0.1)

        text = str(speed or "1.0").lower()
        text = text.replace("x", "").strip()

        try:
            return max(float(text), 0.1)
        except (TypeError, ValueError):
            return 1.0

    def _camera(
        self,
        scene: int,
        confidence: int,
    ) -> str:
        if scene == 1:
            return "Zoom In"

        if scene == 3:
            return "Product Close-up"

        if scene == 5:
            return "Side by Side"

        if confidence >= 90:
            return "Slow Zoom In"

        return "Static"

    def _subtitle_position(self, scene: int) -> str:
        if scene == 1:
            return "중앙"

        if scene == 5:
            return "상단"

        return "하단40%"

    def _subtitle_animation(self, scene: int) -> str:
        if scene == 1:
            return "Bounce"

        if scene in [2, 3]:
            return "Pop"

        return "Fade"

    def _subtitle_emphasis(
        self,
        scene: int,
        hook_level: str,
    ) -> Dict[str, Any]:
        if scene == 1:
            return {
                "enabled": True,
                "style": "keyword",
                "scale": 1.15,
                "max_words": 3,
            }

        if hook_level == "Medium":
            return {
                "enabled": True,
                "style": "keyword",
                "scale": 1.08,
                "max_words": 2,
            }

        return {
            "enabled": False,
            "style": "none",
            "scale": 1.0,
            "max_words": 0,
        }

    def _effect(
        self,
        scene: int,
        confidence: int,
    ) -> str:
        if scene == 1:
            return "Pop"

        if scene == 2:
            return "Click"

        if scene == 3:
            return "Whoosh"

        if scene == 5:
            return "Switch"

        if confidence >= 90:
            return "Impact"

        return "None"

    def _zoom(
        self,
        scene: int,
        confidence: int,
    ) -> str:
        if scene == 1:
            return "110%"

        if scene == 3:
            return "105%"

        if confidence >= 90:
            return "108%"

        return "100%"

    def _bgm_volume(
        self,
        scene: int,
        hook_level: str,
    ) -> int:
        if scene == 1:
            return 12

        if hook_level == "High":
            return 15

        if hook_level == "Medium":
            return 18

        return 20

    def _source_volume(self, scene: int) -> int:
        if scene == 1:
            return 100

        if scene == 7:
            return 70

        return 85

    def _sfx_volume(self, effect: str) -> int:
        if not effect or str(effect).lower() == "none":
            return 0

        if str(effect).lower() in {"impact", "pop"}:
            return 40

        return 35

    def _audio_ducking(self, scene: int) -> bool:
        return scene in [1, 3, 5, 7]

    def _reason(
        self,
        candidate: Dict[str, Any],
        confidence: int,
        suitability: float,
        scene: int,
    ) -> str:
        reasons = []

        if scene == 1:
            reasons.append("초반 이탈 방지를 위한 후킹 컷")
        elif scene == 2:
            reasons.append("문제 상황 공감 컷")
        elif scene == 3:
            reasons.append("제품 등장 컷")
        elif scene == 5:
            reasons.append("Before / After 비교 컷")
        elif scene == 7:
            reasons.append("CTA 마무리 컷")
        else:
            reasons.append("쇼츠 흐름 보강 컷")

        query = self._candidate_query(candidate)

        if query:
            reasons.append(f"검색어 '{query}' 기반 후보")

        if isinstance(suitability, (int, float)):
            reasons.append(
                f"쇼핑쇼츠 적합도 {int(suitability)}점"
            )

        if confidence >= 90:
            reasons.append("대표 컷으로 사용 추천")
        elif confidence >= 80:
            reasons.append("메인 흐름에 적합")
        else:
            reasons.append("보조 컷으로 사용 권장")

        return " / ".join(reasons)

    def _edit_note(
        self,
        scene: int,
        hook_level: str,
    ) -> str:
        if hook_level == "High":
            return (
                "자막 크게, 컷 전환 빠르게, "
                "첫 1초 시선 집중"
            )

        if hook_level == "Medium":
            return (
                "기능 설명이 잘 보이도록 "
                "안정적인 컷 유지"
            )

        if scene == 7:
            return (
                "CTA 문구를 충분히 읽을 수 있도록 "
                "마지막 장면 유지"
            )

        return "흐름 연결용으로 짧게 사용"

    def _default_duration(self, scene: int) -> float:
        if scene == 1:
            return 3.0

        if scene == 7:
            return 3.0

        return 4.0

    def _normalize_time(self, value: Any) -> str:
        seconds = self._time_to_seconds(value)
        return self._seconds_to_time(seconds)

    def _time_to_seconds(self, value: Any) -> float:
        if isinstance(value, (int, float)):
            return max(round(float(value), 2), 0.0)

        text = str(value or "0").strip()

        if not text:
            return 0.0

        if ":" in text:
            parts = text.split(":")

            try:
                if len(parts) == 2:
                    minutes = float(parts[0])
                    seconds = float(parts[1])
                    return max(
                        round(minutes * 60 + seconds, 2),
                        0.0,
                    )

                if len(parts) == 3:
                    hours = float(parts[0])
                    minutes = float(parts[1])
                    seconds = float(parts[2])

                    return max(
                        round(
                            hours * 3600
                            + minutes * 60
                            + seconds,
                            2,
                        ),
                        0.0,
                    )
            except (TypeError, ValueError):
                return 0.0

        try:
            return max(round(float(text), 2), 0.0)
        except (TypeError, ValueError):
            return 0.0

    def _seconds_to_time(self, seconds: float) -> str:
        seconds = max(float(seconds), 0.0)
        return f"{seconds:04.1f}"

    def _number(
        self,
        value: Any,
        default: float,
    ) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    def _optional_number(
        self,
        value: Any,
    ) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None