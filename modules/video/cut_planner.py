from typing import List, Dict, Any


class CutPlanner:
    """
    Sprint 31
    AI Cut Planner 3.0

    목표:
    - 기존 cut_plan UI와 호환 유지
    - confidence를 0~100 점수로 표시
    - CapCut Export에 바로 쓸 수 있는 편집 필드 추가
    - scene별 transition / speed / camera / subtitle_position / hook_level 추천
    """

    def build(self, content_pack: Dict[str, Any]) -> List[Dict[str, Any]]:
        edit = content_pack.get("edit_assistant", {})

        timeline = (
            edit.get("timeline")
            or edit.get("scene_plan")
            or []
        )
        candidates = content_pack.get("selected_sources", [])
        video_quality = content_pack.get("video_quality", {})

        suitability = video_quality.get("suitability_score", 70)

        plans = []

        for idx, item in enumerate(timeline, start=1):
            candidate = self._pick_candidate(candidates, idx)

            confidence = self._confidence(
                candidate=candidate,
                video_quality=video_quality,
                suitability=suitability,
            )

            start, end = self._recommend_time(
                confidence=confidence,
                scene=idx,
            )

            hook_level = self._hook_level(
                scene=idx,
                confidence=confidence,
            )

            plans.append(
                {
                    "planner_version": "sprint31-cutplanner-3.0",
                    "scene": idx,
                    "purpose": self._scene_purpose(idx),
                    "candidate": candidate.get("platform", "현재 연결 영상"),
                    "query": candidate.get("query", ""),
                    "url": candidate.get("url", ""),

                    "start": start,
                    "end": end,
                    "confidence": confidence,

                    # 기존 UI 호환 필드
                    "effect": item.get("sfx") or self._effect(idx, confidence),
                    "zoom": item.get("zoom") or self._zoom(idx, confidence),
                    "subtitle": item.get("subtitle_animation") or self._subtitle_animation(idx),

                    # Sprint 31 신규 필드
                    "reason": self._reason(
                        candidate=candidate,
                        confidence=confidence,
                        suitability=suitability,
                        scene=idx,
                    ),
                    "transition": self._transition(idx, confidence),
                    "speed": self._speed(idx, confidence),
                    "camera": self._camera(idx, confidence),
                    "subtitle_position": item.get("subtitle_position") or self._subtitle_position(idx),
                    "hook_level": hook_level,
                    "edit_note": self._edit_note(idx, hook_level),
                }
            )

        return plans

    def _pick_candidate(self, candidates, scene):
        if not candidates:
            return {}

        return candidates[(scene - 1) % len(candidates)]
    def _candidate_query(self, candidate):
        return (
            candidate.get("query")
            or candidate.get("keyword")
            or candidate.get("search_query")
            or candidate.get("title")
            or ""
        )
   
    def _confidence(self, candidate, video_quality, suitability):
        score = 55

        candidate_score = candidate.get("score")
        if isinstance(candidate_score, (int, float)):
            score += candidate_score * 0.25

        quality = video_quality.get("score")
        if isinstance(quality, (int, float)):
            score += quality * 0.15

        if isinstance(suitability, (int, float)):
            score += suitability * 0.10

        return int(min(max(score, 50), 99))

    def _recommend_time(self, confidence, scene):
        if scene == 1:
            return "00.0", "03.0"

        if confidence >= 90:
            return "00.5", "04.5"

        if confidence >= 80:
            return "01.0", "05.0"

        if confidence >= 70:
            return "01.5", "05.5"

        return "02.0", "06.0"

    def _scene_purpose(self, scene):
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

    def _hook_level(self, scene, confidence):
        if scene == 1 or confidence >= 90:
            return "High"

        if scene in [2, 3, 4] or confidence >= 80:
            return "Medium"

        return "Low"

    def _transition(self, scene, confidence):
        if scene == 1:
            return "Flash"

        if scene in [2, 3]:
            return "Cut"

        if scene == 5:
            return "Split / Before After"

        if confidence >= 90:
            return "Whip"

        return "None"

    def _speed(self, scene, confidence):
        if scene == 1:
            return "1.15x"

        if scene in [2, 3]:
            return "1.05x"

        if confidence >= 90:
            return "1.10x"

        return "1.0x"

    def _camera(self, scene, confidence):
        if scene == 1:
            return "Zoom In"

        if scene == 3:
            return "Product Close-up"

        if scene == 5:
            return "Side by Side"

        if confidence >= 90:
            return "Slow Zoom In"

        return "Static"

    def _subtitle_position(self, scene):
        if scene == 1:
            return "중앙"

        if scene == 5:
            return "상단"

        return "하단40%"

    def _subtitle_animation(self, scene):
        if scene == 1:
            return "Bounce"

        if scene in [2, 3]:
            return "Pop"

        return "Fade"

    def _effect(self, scene, confidence):
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

    def _zoom(self, scene, confidence):
        if scene == 1:
            return "110%"

        if scene == 3:
            return "105%"

        if confidence >= 90:
            return "108%"

        return "100%"

    def _reason(self, candidate, confidence, suitability, scene):
        reasons = []

        if scene == 1:
            reasons.append("초반 이탈 방지를 위한 후킹 컷")
        elif scene == 2:
            reasons.append("문제 상황 공감 컷")
        elif scene == 3:
            reasons.append("제품 등장 컷")
        elif scene == 5:
            reasons.append("Before / After 비교 컷")
        else:
            reasons.append("쇼츠 흐름 보강 컷")

        query = self._candidate_query(candidate)

        if query:
            reasons.append(f"검색어 '{query}' 기반 후보")

        if isinstance(suitability, (int, float)):
            reasons.append(f"쇼핑쇼츠 적합도 {suitability}점")

        if confidence >= 90:
            reasons.append("대표 컷으로 사용 추천")
        elif confidence >= 80:
            reasons.append("메인 흐름에 적합")
        else:
            reasons.append("보조 컷으로 사용 권장")

        return " / ".join(reasons)

    def _edit_note(self, scene, hook_level):
        if hook_level == "High":
            return "자막 크게, 컷 전환 빠르게, 첫 1초 시선 집중"

        if hook_level == "Medium":
            return "기능 설명이 잘 보이도록 안정적인 컷 유지"

        return "흐름 연결용으로 짧게 사용"