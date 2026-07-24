from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping


class SceneDirector:
    """
    Sprint126-1 Scene Director

    역할:
    - 장면 대사와 목적을 실제 촬영 가능한 연출 지시로 변환
    - 모델의 표정·자세·손동작·제품 사용 방식·소품·카메라를 구조화
    - 동일 모델·동일 의상·동일 제품 연속성 규칙을 장면마다 유지
    - 외부 API 호출 없이 결정론적으로 동작
    """

    VERSION = "scene-director-126-1"

    PURPOSE_DEFAULTS: Dict[str, Dict[str, Any]] = {
        "hook": {
            "emotion": "놀람과 호기심",
            "expression": "제품의 의외의 활용을 발견한 자연스러운 놀란 표정",
            "body_pose": "상체를 제품 쪽으로 살짝 기울이고 제품을 확인하는 자세",
            "camera_shot": "medium_close_up",
            "camera_angle": "eye_level",
            "focus": "제품과 사용 결과",
            "action_sequence": ["제품의 핵심 사용 결과를 먼저 보여준다", "모델이 결과를 확인한다"],
        },
        "pain": {
            "emotion": "답답함과 불편함",
            "expression": "과장되지 않은 답답한 표정과 살짝 찌푸린 눈썹",
            "body_pose": "한 손이 제품 사용에 묶여 다른 작업을 하기 어려운 자세",
            "camera_shot": "medium_shot",
            "camera_angle": "eye_level",
            "focus": "불편한 행동과 원인",
            "action_sequence": ["기존 방식으로 제품을 사용한다", "동시에 다른 작업을 시도하며 불편함을 드러낸다"],
        },
        "feature": {
            "emotion": "이해와 관심",
            "expression": "사람이 등장하지 않거나 차분한 설명 표정",
            "body_pose": "제품 기능 부위를 가리지 않는 안정적인 손 위치",
            "camera_shot": "close_up",
            "camera_angle": "slight_high_angle",
            "focus": "핵심 기능 부위와 작동 구조",
            "action_sequence": ["제품의 핵심 기능 부위를 선명하게 보여준다", "기능이 작동하는 상태를 보여준다"],
        },
        "solution": {
            "emotion": "안도와 만족",
            "expression": "불편이 해결된 편안한 표정",
            "body_pose": "양손이 자유롭고 자연스럽게 제품을 사용하는 자세",
            "camera_shot": "medium_close_up",
            "camera_angle": "eye_level",
            "focus": "문제가 해결되는 순간",
            "action_sequence": ["제품을 올바르게 배치한다", "불편 없이 다른 행동을 이어간다"],
        },
        "benefit": {
            "emotion": "편안함과 만족",
            "expression": "사용 결과에 만족하는 자연스러운 표정",
            "body_pose": "제품을 사용하면서 일상 행동을 편하게 이어가는 자세",
            "camera_shot": "medium_shot",
            "camera_angle": "eye_level",
            "focus": "제품 사용 후 달라진 생활 장면",
            "action_sequence": ["제품을 실제 환경에서 사용한다", "편리해진 결과를 행동으로 보여준다"],
        },
        "usage": {
            "emotion": "집중과 편안함",
            "expression": "제품 사용에 집중한 자연스러운 표정",
            "body_pose": "제품 사용법이 명확히 보이고 제품이 가려지지 않는 자세",
            "camera_shot": "medium_shot",
            "camera_angle": "eye_level",
            "focus": "손·몸·제품의 실제 사용 관계",
            "action_sequence": ["첫 사용 방식으로 제품을 사용한다", "다른 환경 또는 방식으로 전환한다"],
        },
        "comparison": {
            "emotion": "명확함",
            "expression": "사람이 등장하지 않거나 중립적인 표정",
            "body_pose": "좌우 비교 요소가 가려지지 않는 자세",
            "camera_shot": "wide_medium",
            "camera_angle": "eye_level",
            "focus": "두 방식의 차이",
            "action_sequence": ["기존 방식을 한쪽에 보여준다", "개선된 방식을 반대쪽에 보여준다"],
        },
        "proof": {
            "emotion": "신뢰와 확신",
            "expression": "사람이 등장하지 않거나 차분한 확인 표정",
            "body_pose": "근거가 되는 기능 부위를 가리지 않는 자세",
            "camera_shot": "close_up",
            "camera_angle": "slight_high_angle",
            "focus": "리뷰에서 반복된 기능과 제품 디테일",
            "action_sequence": ["근거가 되는 기능 부위를 확대한다", "실사용 상태를 함께 보여준다"],
        },
        "cta": {
            "emotion": "차분한 만족",
            "expression": "사람이 등장하면 편안한 미소",
            "body_pose": "제품이 중심에 오도록 단정한 마무리 자세",
            "camera_shot": "hero_shot",
            "camera_angle": "eye_level",
            "focus": "제품 전체와 최종 가치",
            "action_sequence": ["제품 전체를 깨끗하게 보여준다", "사용 환경과 함께 안정적으로 마무리한다"],
        },
    }

    def direct(
        self,
        scene_id: str,
        purpose: str,
        subtitle: str,
        story_goal: str,
        product_name: str,
        product_type: str,
        environment: str,
        continuity: Mapping[str, Any],
        people: int,
    ) -> Dict[str, Any]:
        normalized_purpose = purpose if purpose in self.PURPOSE_DEFAULTS else "feature"
        base = dict(self.PURPOSE_DEFAULTS[normalized_purpose])
        text = " ".join(str(value or "") for value in (subtitle, story_goal)).strip()

        actions = self._extract_actions(text, normalized_purpose)
        props = self._extract_props(text, product_type)
        hand_direction = self._build_hand_direction(text, normalized_purpose)
        product_direction = self._build_product_direction(text, normalized_purpose)
        transition = self._build_transition(text, normalized_purpose)

        action_sequence = self._unique(actions or list(base["action_sequence"]))
        return {
            "ok": True,
            "version": self.VERSION,
            "scene_id": str(scene_id or ""),
            "purpose": normalized_purpose,
            "environment": environment,
            "actor": {
                "people": max(0, int(people or 0)),
                "same_model": bool(continuity.get("use_same_model")),
                "model_description": str(continuity.get("model_description") or ""),
                "wardrobe": str(continuity.get("wardrobe") or ""),
                "emotion": base["emotion"],
                "expression": base["expression"],
                "body_pose": base["body_pose"],
                "hand_direction": hand_direction,
            },
            "product": {
                "name": product_name,
                "identity_rule": "참고 상품 이미지와 동일한 형태·색상·비율·버튼·구조·로고 유지",
                "placement": product_direction,
                "visibility": "제품 전체 또는 핵심 기능 부위가 손과 소품에 가려지지 않아야 함",
                "physical_rule": "실제 제품 구조로 가능한 사용법만 연출",
            },
            "camera": {
                "shot": base["camera_shot"],
                "angle": base["camera_angle"],
                "focus": base["focus"],
                "orientation": "vertical_9_16",
            },
            "action_sequence": action_sequence,
            "props": props,
            "transition": transition,
            "continuity": {
                "profile_id": str(continuity.get("profile_id") or ""),
                "same_model": bool(continuity.get("use_same_model")),
                "same_clothes": True,
                "same_product": True,
                "same_lighting": True,
                "same_background_tone": True,
            },
            "directing_summary": self._build_summary(
                environment=environment,
                expression=base["expression"],
                body_pose=base["body_pose"],
                hand_direction=hand_direction,
                product_direction=product_direction,
                actions=action_sequence,
                props=props,
                camera_shot=base["camera_shot"],
                camera_angle=base["camera_angle"],
            ),
            "warnings": [],
            "errors": [],
        }

    def _extract_actions(self, text: str, purpose: str) -> List[str]:
        rules = [
            (("목에 걸", "목에만", "목걸이"), "제품을 목에 자연스럽게 걸어 양손이 자유로운 상태를 보여준다"),
            (("책상", "탁상", "세워"), "제품의 각도를 조절해 책상 위에 안정적으로 세운다"),
            (("각도", "방향"), "바람이 얼굴 또는 필요한 방향을 향하도록 각도를 조절한다"),
            (("노트북", "업무", "마우스"), "양손으로 노트북과 마우스를 자연스럽게 사용한다"),
            (("이동", "출퇴근", "걸어"), "제품을 착용한 채 자연스럽게 이동한다"),
            (("세척", "씻"), "제품을 실제 세척 가능한 방식으로 씻는다"),
            (("접", "보관"), "제품을 접거나 정리해 보관한다"),
            (("수납", "정리"), "물건을 제품에 나누어 담고 정리한다"),
            (("굴러", "바퀴"), "제품을 바닥에서 부드럽게 이동시킨다"),
            (("비교", "전후"), "기존 방식과 제품 사용 방식을 한 화면에서 비교한다"),
        ]
        actions: List[str] = []
        for keywords, action in rules:
            if any(keyword in text for keyword in keywords):
                actions.append(action)
        if purpose == "pain" and not actions:
            actions.extend([
                "한 손으로 기존 방식의 제품을 들고 사용한다",
                "다른 손으로 일상 작업을 시도하며 손이 부족한 상황을 보여준다",
            ])
        return self._unique(actions)

    def _extract_props(self, text: str, product_type: str) -> List[str]:
        prop_rules = [
            (("책상", "노트북", "업무"), ["노트북", "마우스", "서류 한두 장"]),
            (("캠핑", "야외"), ["캠핑 의자", "작은 테이블"]),
            (("세탁", "빨래"), ["세탁기", "접힌 수건"]),
            (("주방", "요리", "도마"), ["조리대", "채소", "주방칼"]),
            (("공항", "여행", "캐리어"), ["여행 가방", "여권 지갑"]),
        ]
        props: List[str] = []
        for keywords, candidates in prop_rules:
            if any(keyword in text for keyword in keywords):
                props.extend(candidates)
        if not props and product_type == "electronics":
            props = ["단순한 책상", "노트북"]
        return self._unique(props)[:4]

    def _build_hand_direction(self, text: str, purpose: str) -> str:
        if purpose == "pain":
            return "한 손은 제품을 들거나 방향을 맞추는 데 사용하고, 다른 손은 마우스 또는 작업 도구를 잡으려 해 불편함이 보이게 한다"
        if "목에 걸" in text or "목에만" in text or "목걸이" in text:
            return "양손은 제품을 잡지 않고 자연스럽게 자유로운 상태로 유지한다"
        if "각도" in text or "세워" in text or "탁상" in text:
            return "한 손의 손가락으로 제품 각도를 조절하되 버튼과 송풍구를 가리지 않는다"
        if purpose in {"feature", "proof"}:
            return "손이 등장하면 손가락으로 핵심 기능 부위만 가리키고 제품을 가리지 않는다"
        return "손은 제품의 실제 사용법을 명확히 보여주되 제품 형태를 가리지 않는다"

    def _build_product_direction(self, text: str, purpose: str) -> str:
        if "목에 걸" in text or "목에만" in text or "목걸이" in text:
            return "제품을 모델의 목 중앙에 자연스럽게 착용하고 송풍구 방향이 얼굴 쪽을 향하게 배치"
        if "책상" in text or "탁상" in text or "세워" in text:
            return "제품을 책상 전경에 안정적으로 세우고 각도 조절 구조가 보이게 배치"
        if purpose in {"feature", "proof"}:
            return "제품을 화면 중앙 전경에 크게 배치하고 핵심 기능 부위를 카메라 쪽으로 향하게 배치"
        if purpose == "cta":
            return "제품 전체가 한눈에 보이도록 중앙에 단독 배치"
        return "제품이 모델의 몸이나 소품에 가려지지 않도록 전경 또는 중앙에 배치"

    def _build_transition(self, text: str, purpose: str) -> Dict[str, Any]:
        dual = bool(re.search(r"(이동|목에 걸).*(책상|탁상|세워)|(책상|탁상).*(목에 걸|이동)", text))
        if dual:
            return {
                "multi_beat": True,
                "beat_count": 2,
                "beats": [
                    "같은 모델이 이동 중 제품을 착용한 장면",
                    "같은 모델이 같은 제품을 책상 위 탁상형으로 사용하는 장면",
                ],
                "rule": "두 비트 모두 동일 모델·동일 의상·동일 제품을 유지",
            }
        return {
            "multi_beat": False,
            "beat_count": 1,
            "beats": ["한 장면 안에서 핵심 행동을 명확히 보여준다"],
            "rule": "장면 안에서 제품 형태와 사용 방향을 일관되게 유지",
        }

    def _build_summary(
        self,
        environment: str,
        expression: str,
        body_pose: str,
        hand_direction: str,
        product_direction: str,
        actions: List[str],
        props: List[str],
        camera_shot: str,
        camera_angle: str,
    ) -> str:
        action_text = " → ".join(actions)
        prop_text = ", ".join(props) if props else "최소한의 생활 소품"
        return (
            f"환경은 {environment}. 모델 표정은 {expression}. 자세는 {body_pose}. "
            f"손 연출은 {hand_direction}. 제품 배치는 {product_direction}. "
            f"행동 순서는 {action_text}. 소품은 {prop_text}. "
            f"카메라는 {camera_shot}, {camera_angle}."
        )

    def _unique(self, values: List[str]) -> List[str]:
        output: List[str] = []
        for value in values:
            text = str(value or "").strip()
            if text and text not in output:
                output.append(text)
        return output