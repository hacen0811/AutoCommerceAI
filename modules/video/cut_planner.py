from typing import Any, Dict, List


class CutPlanner:
    """
    Sprint 32
    AI Edit Director 4.0

    목표:
    - 기존 cut_plan UI 호환 유지
    - 장면 목적과 후킹 강도를 기반으로 편집값 추천
    - transition / speed / camera / subtitle_position 추천
    - BGM / BGM 볼륨 / 효과음 추천
    - CapCut Export에서 사용할 수 있는 수치 필드 제공
    """

    PLANNER_VERSION = "sprint32-ai-edit-director-4.0"

    def build(
        self,
        content_pack: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        edit = content_pack.get("edit_assistant") or {}

        timeline = (
            edit.get("timeline")
            or edit.get("scene_plan")
            or []
        )

        candidates = content_pack.get("selected_sources") or []
        video_quality = content_pack.get("video_quality") or {}

        suitability = video_quality.get("suitability_score", 70)

        plans: List[Dict[str, Any]] = []

        for idx, item in enumerate(timeline, start=1):
            candidate = self._pick_candidate(candidates, idx)

            confidence = self._confidence(
                candidate=candidate,
                video_quality=video_quality,
                suitability=suitability,
            )

            purpose = (
                item.get("purpose")
                or item.get("role")
                or self._scene_purpose(idx)
            )

            start, end = self._recommend_time(
                confidence=confidence,
                scene=idx,
            )

            hook_level = self._hook_level(
                scene=idx,
                confidence=confidence,
                purpose=purpose,
            )

            transition = (
                item.get("transition")
                or self._transition(
                    scene=idx,
                    confidence=confidence,
                    purpose=purpose,
                )
            )

            speed = (
                item.get("speed")
                or self._speed(
                    scene=idx,
                    confidence=confidence,
                    purpose=purpose,
                )
            )

            camera = (
                item.get("camera")
                or item.get("zoom")
                or self._camera(
                    scene=idx,
                    confidence=confidence,
                    purpose=purpose,
                )
            )

            subtitle_position = (
                item.get("subtitle_position")
                or self._subtitle_position(
                    scene=idx,
                    purpose=purpose,
                )
            )

            bgm = (
                item.get("bgm")
                or self._bgm(
                    scene=idx,
                    purpose=purpose,
                    hook_level=hook_level,
                )
            )

            bgm_volume = (
                item.get("bgm_volume")
                or self._bgm_volume(
                    scene=idx,
                    purpose=purpose,
                    hook_level=hook_level,
                )
            )

            sound_effect = (
                item.get("sound_effect")
                or item.get("sfx")
                or self._sound_effect(
                    scene=idx,
                    purpose=purpose,
                    hook_level=hook_level,
                )
            )

            plan = {
                "planner_version": self.PLANNER_VERSION,
                "scene": idx,
                "purpose": purpose,

                # 후보 영상 정보
                "candidate": (
                    candidate.get("platform")
                    or candidate.get("source")
                    or "현재 연결 영상"
                ),
                "candidate_rank": candidate.get("rank", idx),
                "query": self._candidate_query(candidate),
                "url": self._candidate_url(candidate),
                "video_path": (
                    candidate.get("video_path")
                    or candidate.get("local_path")
                    or candidate.get("path")
                    or ""
                ),

                # 추천 구간
                "start": start,
                "end": end,
                "confidence": confidence,

                # 기존 UI 호환 필드
                "effect": sound_effect,
                "zoom": camera,
                "subtitle": (
                    item.get("subtitle_animation")
                    or self._subtitle_animation(
                        scene=idx,
                        purpose=purpose,
                    )
                ),

                # AI 편집 추천 필드
                "reason": self._reason(
                    candidate=candidate,
                    confidence=confidence,
                    suitability=suitability,
                    scene=idx,
                    purpose=purpose,
                ),
                "transition": transition,
                "speed": speed,
                "speed_value": self._speed_value(speed),
                "camera": camera,
                "subtitle_position": subtitle_position,
                "hook_level": hook_level,

                # 오디오 추천 필드
                "bgm": bgm,
                "bgm_volume": bgm_volume,
                "bgm_volume_value": self._volume_value(bgm_volume),
                "sound_effect": sound_effect,
                "sfx": sound_effect,

                # 편집 안내
                "edit_note": self._edit_note(
                    scene=idx,
                    hook_level=hook_level,
                    purpose=purpose,
                ),
            }

            plans.append(plan)

        return plans

    def _pick_candidate(
        self,
        candidates: List[Dict[str, Any]],
        scene: int,
    ) -> Dict[str, Any]:
        if not candidates:
            return {}

        return candidates[(scene - 1) % len(candidates)]

    def _candidate_query(
        self,
        candidate: Dict[str, Any],
    ) -> str:
        return (
            candidate.get("query")
            or candidate.get("keyword")
            or candidate.get("search_query")
            or candidate.get("title")
            or ""
        )

    def _candidate_url(
        self,
        candidate: Dict[str, Any],
    ) -> str:
        return (
            candidate.get("url")
            or candidate.get("search_url")
            or candidate.get("video_url")
            or candidate.get("play_url")
            or ""
        )

    def _confidence(
        self,
        candidate: Dict[str, Any],
        video_quality: Dict[str, Any],
        suitability: Any,
    ) -> int:
        score = 55.0

        candidate_score = candidate.get("score")
        if isinstance(candidate_score, (int, float)):
            score += float(candidate_score) * 0.25

        quality = video_quality.get("score")
        if isinstance(quality, (int, float)):
            score += float(quality) * 0.15

        if isinstance(suitability, (int, float)):
            score += float(suitability) * 0.10

        if self._candidate_url(candidate):
            score += 3

        if (
            candidate.get("video_path")
            or candidate.get("local_path")
            or candidate.get("path")
        ):
            score += 5

        return int(min(max(score, 50), 99))

    def _recommend_time(
        self,
        confidence: int,
        scene: int,
    ) -> tuple[str, str]:
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

    def _hook_level(
        self,
        scene: int,
        confidence: int,
        purpose: str,
    ) -> str:
        purpose_text = str(purpose).lower()

        if (
            scene == 1
            or confidence >= 92
            or "후킹" in purpose_text
            or "첫 시선" in purpose_text
        ):
            return "High"

        if (
            confidence >= 80
            or any(
                keyword in purpose_text
                for keyword in [
                    "제품",
                    "기능",
                    "before",
                    "after",
                    "비교",
                ]
            )
        ):
            return "Medium"

        return "Low"

    def _transition(
        self,
        scene: int,
        confidence: int,
        purpose: str,
    ) -> str:
        purpose_text = str(purpose).lower()

        if scene == 1 or "후킹" in purpose_text:
            return "Flash"

        if "문제" in purpose_text or "공감" in purpose_text:
            return "Cut"

        if "제품 등장" in purpose_text:
            return "Zoom"

        if "기능" in purpose_text:
            return "Cut"

        if (
            "before" in purpose_text
            or "after" in purpose_text
            or "비교" in purpose_text
        ):
            return "Split / Before After"

        if "cta" in purpose_text or "마무리" in purpose_text:
            return "Fade"

        if confidence >= 90:
            return "Whip"

        return "Cut"

    def _speed(
        self,
        scene: int,
        confidence: int,
        purpose: str,
    ) -> str:
        purpose_text = str(purpose).lower()

        if scene == 1 or "후킹" in purpose_text:
            return "1.15x"

        if "문제" in purpose_text or "공감" in purpose_text:
            return "1.0x"

        if "제품 등장" in purpose_text:
            return "1.05x"

        if "기능" in purpose_text:
            return "1.0x"

        if (
            "before" in purpose_text
            or "after" in purpose_text
            or "비교" in purpose_text
        ):
            return "1.10x"

        if "cta" in purpose_text or "마무리" in purpose_text:
            return "1.0x"

        if confidence >= 90:
            return "1.10x"

        return "1.0x"

    def _speed_value(self, speed: Any) -> float:
        if isinstance(speed, (int, float)):
            return float(speed)

        text = str(speed).lower().replace("x", "").strip()

        try:
            return float(text)
        except (TypeError, ValueError):
            return 1.0

    def _camera(
        self,
        scene: int,
        confidence: int,
        purpose: str,
    ) -> str:
        purpose_text = str(purpose).lower()

        if scene == 1 or "후킹" in purpose_text:
            return "Zoom In"

        if "문제" in purpose_text or "공감" in purpose_text:
            return "Static"

        if "제품 등장" in purpose_text:
            return "Product Close-up"

        if "기능" in purpose_text:
            return "Detail Close-up"

        if (
            "before" in purpose_text
            or "after" in purpose_text
            or "비교" in purpose_text
        ):
            return "Side by Side"

        if "실사용" in purpose_text:
            return "Follow Shot"

        if "cta" in purpose_text or "마무리" in purpose_text:
            return "Slow Zoom Out"

        if confidence >= 90:
            return "Slow Zoom In"

        return "Static"

    def _subtitle_position(
        self,
        scene: int,
        purpose: str,
    ) -> str:
        purpose_text = str(purpose).lower()

        if scene == 1 or "후킹" in purpose_text:
            return "중앙"

        if (
            "before" in purpose_text
            or "after" in purpose_text
            or "비교" in purpose_text
        ):
            return "상단"

        return "하단40%"

    def _subtitle_animation(
        self,
        scene: int,
        purpose: str,
    ) -> str:
        purpose_text = str(purpose).lower()

        if scene == 1 or "후킹" in purpose_text:
            return "Bounce"

        if "제품" in purpose_text or "기능" in purpose_text:
            return "Pop"

        if "cta" in purpose_text or "마무리" in purpose_text:
            return "Fade"

        return "Fade"

    def _bgm(
        self,
        scene: int,
        purpose: str,
        hook_level: str,
    ) -> str:
        purpose_text = str(purpose).lower()

        if scene == 1 or hook_level == "High":
            return "서사적 도입부"

        if "문제" in purpose_text or "공감" in purpose_text:
            return "차분한 소프트 비트"

        if "제품 등장" in purpose_text:
            return "모던 팝"

        if "기능" in purpose_text:
            return "클린 테크 비트"

        if (
            "before" in purpose_text
            or "after" in purpose_text
            or "비교" in purpose_text
        ):
            return "경쾌한 업비트"

        if "실사용" in purpose_text:
            return "밝은 라이프스타일 팝"

        if "cta" in purpose_text or "마무리" in purpose_text:
            return "긍정적인 엔딩 테마"

        return "모던 팝"

    def _bgm_volume(
        self,
        scene: int,
        purpose: str,
        hook_level: str,
    ) -> str:
        purpose_text = str(purpose).lower()

        if scene == 1 or hook_level == "High":
            return "12%"

        if "문제" in purpose_text or "공감" in purpose_text:
            return "14%"

        if "제품 등장" in purpose_text:
            return "16%"

        if "기능" in purpose_text:
            return "15%"

        if (
            "before" in purpose_text
            or "after" in purpose_text
            or "비교" in purpose_text
        ):
            return "18%"

        if "실사용" in purpose_text:
            return "20%"

        if "cta" in purpose_text or "마무리" in purpose_text:
            return "22%"

        return "15%"

    def _volume_value(self, volume: Any) -> float:
        if isinstance(volume, (int, float)):
            value = float(volume)

            if value > 1:
                return value / 100

            return value

        text = str(volume).replace("%", "").strip()

        try:
            return float(text) / 100
        except (TypeError, ValueError):
            return 0.15

    def _sound_effect(
        self,
        scene: int,
        purpose: str,
        hook_level: str,
    ) -> str:
        purpose_text = str(purpose).lower()

        if scene == 1 or hook_level == "High":
            return "임팩트"

        if "문제" in purpose_text or "공감" in purpose_text:
            return "휙"

        if "제품 등장" in purpose_text:
            return "팝"

        if "기능" in purpose_text:
            return "클릭"

        if (
            "before" in purpose_text
            or "after" in purpose_text
            or "비교" in purpose_text
        ):
            return "스와이프"

        if "실사용" in purpose_text:
            return "반짝"

        if "cta" in purpose_text or "마무리" in purpose_text:
            return "성공 효과"

        return "클릭"

    def _reason(
        self,
        candidate: Dict[str, Any],
        confidence: int,
        suitability: Any,
        scene: int,
        purpose: str,
    ) -> str:
        reasons = [f"{purpose}에 적합한 편집 구성"]

        query = self._candidate_query(candidate)

        if query:
            reasons.append(f"검색어 '{query}' 기반 후보")

        if isinstance(suitability, (int, float)):
            reasons.append(f"쇼핑쇼츠 적합도 {int(suitability)}점")

        if confidence >= 90:
            reasons.append("대표 컷으로 사용 추천")
        elif confidence >= 80:
            reasons.append("메인 흐름에 적합")
        else:
            reasons.append("보조 컷으로 사용 권장")

        if scene == 1:
            reasons.append("첫 1초 이탈 방지")

        return " / ".join(reasons)

    def _edit_note(
        self,
        scene: int,
        hook_level: str,
        purpose: str,
    ) -> str:
        purpose_text = str(purpose).lower()

        if hook_level == "High":
            return "자막을 크게 표시하고 첫 1초 안에 빠르게 전환"

        if (
            "before" in purpose_text
            or "after" in purpose_text
            or "비교" in purpose_text
        ):
            return "변화 전후가 동시에 잘 보이도록 비교 화면 유지"

        if "기능" in purpose_text:
            return "제품의 핵심 기능이 가려지지 않도록 안정적인 컷 유지"

        if "cta" in purpose_text or "마무리" in purpose_text:
            return "CTA 자막을 충분히 읽을 수 있도록 마지막 컷 유지"

        return "장면 흐름을 방해하지 않도록 짧고 자연스럽게 연결"