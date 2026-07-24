from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence


class SceneBeatPlanner:
    """
    Sprint127-1 Scene Beat Planner

    역할:
    - Scene Director의 행동 순서와 전환 정보를 촬영 가능한 Beat 단위로 분해
    - 각 Beat에 목표·행동·환경·카메라·제품 상태·연속성 규칙 부여
    - 한 이미지에 여러 행동을 억지로 넣지 않도록 대표 Beat 지정
    - 외부 API 호출 없이 결정론적으로 동작
    """

    VERSION = "scene-beat-planner-127-1"

    PURPOSE_CAMERA: Dict[str, Sequence[str]] = {
        "hook": ("medium_close_up", "close_up", "hero_shot"),
        "pain": ("medium_shot", "close_up", "medium_close_up"),
        "feature": ("close_up", "detail_close_up", "medium_close_up"),
        "solution": ("medium_close_up", "medium_shot", "close_up"),
        "benefit": ("medium_shot", "medium_close_up", "hero_shot"),
        "usage": ("medium_shot", "close_up", "medium_close_up"),
        "comparison": ("wide_medium", "close_up", "wide_medium"),
        "proof": ("close_up", "detail_close_up", "hero_shot"),
        "cta": ("hero_shot", "close_up", "hero_shot"),
    }

    def plan(
        self,
        scene_id: str,
        purpose: str,
        subtitle: str,
        story_goal: str,
        scene_direction: Mapping[str, Any],
        product_name: str,
        product_type: str,
        environment: str,
        people: int,
    ) -> Dict[str, Any]:
        normalized_purpose = str(purpose or "feature").strip().lower()
        direction = dict(scene_direction or {})
        actions = self._unique_strings(direction.get("action_sequence") or [])
        transition = dict(direction.get("transition") or {})
        transition_beats = self._unique_strings(transition.get("beats") or [])

        raw_beats = self._derive_beats(
            purpose=normalized_purpose,
            subtitle=str(subtitle or ""),
            story_goal=str(story_goal or ""),
            actions=actions,
            transition_beats=transition_beats,
            product_type=str(product_type or "general"),
            product_name=str(product_name or ""),
        )

        camera_sequence = self.PURPOSE_CAMERA.get(
            normalized_purpose,
            self.PURPOSE_CAMERA["feature"],
        )
        product = dict(direction.get("product") or {})
        actor = dict(direction.get("actor") or {})
        continuity = dict(direction.get("continuity") or {})

        beats: List[Dict[str, Any]] = []
        for index, beat in enumerate(raw_beats):
            beat_environment = self._beat_environment(
                base_environment=environment,
                beat_text=beat["action"],
                index=index,
            )
            shot = camera_sequence[min(index, len(camera_sequence) - 1)]
            beats.append(
                {
                    "beat_id": f"{scene_id}_beat_{index + 1:02d}",
                    "order": index + 1,
                    "goal": beat["goal"],
                    "action": beat["action"],
                    "environment": beat_environment,
                    "people": max(0, int(people or 0)),
                    "actor_direction": self._actor_direction(actor, people),
                    "product_state": self._product_state(
                        beat_text=beat["action"],
                        product_name=product_name,
                        fallback=str(product.get("placement") or ""),
                    ),
                    "camera": {
                        "shot": shot,
                        "angle": self._camera_angle(index, normalized_purpose),
                        "focus": self._camera_focus(beat["goal"], normalized_purpose),
                        "orientation": "vertical_9_16",
                    },
                    "continuity": {
                        "profile_id": str(continuity.get("profile_id") or ""),
                        "same_model": bool(continuity.get("same_model")) if people else False,
                        "same_clothes": bool(continuity.get("same_clothes")) if people else False,
                        "same_product": True,
                        "same_lighting": True,
                        "same_background_tone": True,
                    },
                    "image_rule": "한 이미지에는 이 Beat의 핵심 행동 하나만 명확히 표현",
                }
            )

        primary_index = self._primary_beat_index(normalized_purpose, len(beats))
        for index, beat in enumerate(beats):
            beat["primary_image_beat"] = index == primary_index

        return {
            "ok": bool(beats),
            "ready": bool(beats),
            "version": self.VERSION,
            "scene_id": str(scene_id or ""),
            "purpose": normalized_purpose,
            "beat_count": len(beats),
            "primary_beat_id": beats[primary_index]["beat_id"] if beats else "",
            "multi_beat": len(beats) > 1,
            "beats": beats,
            "beat_prompt_summary": self._build_prompt_summary(beats),
            "rules": [
                "각 Beat는 하나의 명확한 행동만 포함",
                "여러 Beat가 있어도 동일 모델·동일 의상·동일 제품 유지",
                "제품 형태·색상·비율·구조·로고 변경 금지",
                "사람이 없는 Beat에는 모델 설명과 인체 동작을 넣지 않음",
                "이미지 안에 자막·가격·워터마크 생성 금지",
            ],
            "warnings": [],
            "errors": [],
        }

    def _derive_beats(
        self,
        purpose: str,
        subtitle: str,
        story_goal: str,
        actions: List[str],
        transition_beats: List[str],
        product_type: str,
        product_name: str,
    ) -> List[Dict[str, str]]:
        text = f"{product_name} {subtitle} {story_goal}".strip()

        if self._is_neck_fan(product_type, text):
            if purpose == "cta":
                return [
                    {"goal": "제품 전체와 구매 전 확인 요소를 정리", "action": "제품을 책상 위에 단독으로 세우고 전체 형태를 깨끗하게 보여준다"},
                    {"goal": "사용 환경 적합성 확인", "action": "무게·사용 시간·소음은 화면 글자 없이 제품 디테일과 차분한 사용 장면으로 암시한다"},
                ]
            if "이동" in text and any(word in text for word in ("책상", "탁상", "세워")):
                return [
                    {"goal": "이동 중 목걸이형 사용", "action": "같은 모델이 제품을 목에 걸고 양손을 자유롭게 둔 채 자연스럽게 이동한다"},
                    {"goal": "탁상형 전환", "action": "같은 모델이 제품을 목에서 벗겨 각도를 조절한다"},
                    {"goal": "책상 위 탁상형 사용", "action": "같은 제품을 책상 위에 안정적으로 세우고 노트북 작업을 이어간다"},
                ]
            if any(word in text for word in ("목에 걸", "목걸이")) and any(word in text for word in ("책상", "탁상", "세워")):
                return [
                    {"goal": "목걸이형 사용 결과", "action": "모델이 제품을 목에 걸고 양손이 자유로운 상태를 보여준다"},
                    {"goal": "탁상형 사용 결과", "action": "같은 제품을 책상 위에 세워 송풍구가 얼굴 방향을 향하게 한다"},
                ]
            if purpose == "pain":
                return [
                    {"goal": "손이 묶이는 불편 제시", "action": "한 손으로 기존 선풍기를 들고 다른 손으로 마우스를 사용하려 해 불편함을 보여준다"},
                    {"goal": "바람 방향 조절의 불편 제시", "action": "선풍기 방향을 반복해서 맞추며 답답한 표정을 보여준다"},
                ]
            if purpose in {"feature", "proof"}:
                return [
                    {"goal": "각도 조절 구조 확인", "action": "제품을 가까이 보여주고 손가락으로 각도 조절 부위를 움직인다"},
                    {"goal": "탁상형 안정성 확인", "action": "제품을 책상 위에 세워 흔들림 없이 유지되는 모습을 보여준다"},
                ]

        candidates = transition_beats if len(transition_beats) > 1 else actions
        if not candidates:
            candidates = [story_goal or subtitle or "제품의 핵심 사용 결과를 보여준다"]

        max_beats = 3 if purpose in {"hook", "usage", "solution", "benefit"} else 2
        results: List[Dict[str, str]] = []
        for action in candidates[:max_beats]:
            results.append({"goal": self._goal_from_action(action, purpose), "action": action})
        return results

    @staticmethod
    def _is_neck_fan(product_type: str, text: str) -> bool:
        return "electronics" in product_type and any(
            keyword in text for keyword in ("선풍기", "목에 걸", "탁상", "바람", "송풍")
        )

    @staticmethod
    def _goal_from_action(action: str, purpose: str) -> str:
        labels = {
            "hook": "핵심 결과를 즉시 제시",
            "pain": "불편 원인을 행동으로 제시",
            "feature": "핵심 기능 구조 확인",
            "solution": "문제가 해결되는 과정",
            "benefit": "사용 후 편리함 확인",
            "usage": "실제 사용법 시연",
            "comparison": "차이를 명확히 비교",
            "proof": "제품 근거와 디테일 확인",
            "cta": "제품 가치 정리",
        }
        return f"{labels.get(purpose, '핵심 행동 표현')}: {action[:45]}"

    @staticmethod
    def _beat_environment(base_environment: str, beat_text: str, index: int) -> str:
        if "이동" in beat_text or "걷" in beat_text:
            return "밝고 현실적인 한국 사무실 복도 또는 출퇴근 동선"
        if "책상" in beat_text or "노트북" in beat_text:
            return "밝고 정돈된 한국 사무실 책상"
        return str(base_environment or "밝고 정돈된 한국 생활 공간")

    @staticmethod
    def _actor_direction(actor: Mapping[str, Any], people: int) -> Dict[str, Any]:
        if max(0, int(people or 0)) == 0:
            return {
                "people": 0,
                "model_required": False,
                "expression": "",
                "body_pose": "",
                "hand_direction": "필요한 경우 제품 기능을 보여주는 손만 최소한으로 등장",
            }
        return {
            "people": max(0, int(people or 0)),
            "model_required": True,
            "expression": str(actor.get("expression") or "자연스러운 표정"),
            "body_pose": str(actor.get("body_pose") or "제품 사용법이 보이는 자세"),
            "hand_direction": str(actor.get("hand_direction") or "제품을 가리지 않는 손 위치"),
        }

    @staticmethod
    def _product_state(beat_text: str, product_name: str, fallback: str) -> str:
        if "목에" in beat_text:
            return f"{product_name}을 모델의 목 중앙에 자연스럽게 착용"
        if "책상" in beat_text or "세우" in beat_text:
            return f"{product_name}을 책상 위에 안정적으로 세우고 각도 조절 구조 노출"
        if "가까이" in beat_text or "디테일" in beat_text:
            return f"{product_name}의 핵심 기능 부위를 카메라 전경에 크게 배치"
        return fallback or f"{product_name} 전체 형태가 명확히 보이도록 배치"

    @staticmethod
    def _camera_angle(index: int, purpose: str) -> str:
        if purpose in {"feature", "proof"} and index > 0:
            return "slight_high_angle"
        return "eye_level"

    @staticmethod
    def _camera_focus(goal: str, purpose: str) -> str:
        if purpose in {"feature", "proof"}:
            return "제품 기능 부위와 실제 작동 상태"
        if purpose == "pain":
            return "불편한 행동과 표정"
        return goal

    @staticmethod
    def _primary_beat_index(purpose: str, beat_count: int) -> int:
        if beat_count <= 1:
            return 0
        if purpose in {"hook", "benefit", "cta"}:
            return beat_count - 1
        return 0

    @staticmethod
    def _build_prompt_summary(beats: List[Mapping[str, Any]]) -> str:
        parts: List[str] = []
        for beat in beats:
            parts.append(
                f"Beat {beat.get('order')}: {beat.get('goal')}; "
                f"행동은 {beat.get('action')}; 카메라는 {(beat.get('camera') or {}).get('shot', '')}"
            )
        return " | ".join(parts)

    @staticmethod
    def _unique_strings(values: Any) -> List[str]:
        if isinstance(values, str):
            values = [values]
        if not isinstance(values, Sequence):
            return []
        result: List[str] = []
        seen = set()
        for value in values:
            text = str(value or "").strip()
            if text and text not in seen:
                seen.add(text)
                result.append(text)
        return result