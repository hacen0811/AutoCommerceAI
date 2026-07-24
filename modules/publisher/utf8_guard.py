from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Mapping, Tuple


class PublisherUTF8Guard:
    """
    Sprint128-3 Publisher UTF-8 Guard

    역할:
    - Sprint81-10 export_pack과 Sprint82 Publisher 결과의 텍스트를 변경하지 않고 검사
    - title/caption/description/script/hashtags 계열의 최초 깨짐 위치를 로그로 추적
    - 정상 한글을 임의 재인코딩하거나 자동 복구하지 않음
    - CP949/EUC-KR/UTF-8 혼선에서 발생하는 실제 mojibake 패턴을 탐지
    - 전체 원문 대신 경로, 판정 사유, 짧은 미리보기만 출력
    """

    VERSION = "publisher-utf8-guard-128-3"

    TEXT_KEYS = {
        "title",
        "caption",
        "description",
        "script",
        "body",
        "hashtags",
        "hashtag",
        "hook",
        "cta",
    }

    SUSPICIOUS_FRAGMENTS = (
        "???",
        "?쒖",
        "?섏",
        "?덉",
        "?꾨",
        "?먯",
        "?ㅼ",
        "?대",
        "?ъ",
        "?뺤",
        "?깅",
        "?쒗",
        "?쇳",
        "?ㅽ",
        "?뱁",
        "紐⑷",
        "誘몃땲",
        "臾댁꽑",
        "좏뭾",
        "湲곗",
        "媛??",
        "由щ럭",
        "遺꾩",
        "諛고",
        "援щℓ",
        "留곹",
        "蹂댁",
        "愿묎",
        "異붿",
        "瑗쇨",
        "鍮꾧",
        "洹몃",
        "媛숈",
        "梨낆",
        "몄썙",
        "곹솴",
        "⑸땲",
        "덈떎",
    )

    HANGUL_PATTERN = re.compile(r"[가-힣]")
    QUESTION_MARK_PATTERN = re.compile(r"\?")
    REPLACEMENT_PATTERN = re.compile(r"\ufffd")

    CJK_PATTERN = re.compile(
        r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]"
    )

    BOX_DRAWING_PATTERN = re.compile(
        r"[\u2500-\u257f\u2580-\u259f\u25a0-\u25ff]"
    )

    QUESTION_BOUNDARY_PATTERN = re.compile(
        r"(?:"
        r"[\?][가-힣\u3400-\u9fff\uf900-\ufaff\u2500-\u257f]"
        r"|"
        r"[가-힣\u3400-\u9fff\uf900-\ufaff\u2500-\u257f][\?]"
        r")"
    )

    MOJIBAKE_CLUSTER_PATTERN = re.compile(
        r"(?:"
        r"[?][^\s?]{1,4}[?]"
        r"|"
        r"[\u3400-\u9fff\uf900-\ufaff]{2,}"
        r"|"
        r"[\u2500-\u257f][^\s]{0,3}"
        r")"
    )

    @classmethod
    def inspect(cls, payload: Any, stage: str) -> Dict[str, Any]:
        findings: List[Dict[str, Any]] = []

        for path, value in cls._walk(payload):
            key = path.rsplit(".", 1)[-1].split("[", 1)[0].lower()
            if key not in cls.TEXT_KEYS:
                continue

            text = cls._to_text(value)
            if not text:
                continue

            findings.append(
                cls.inspect_text(
                    text=text,
                    path=path,
                    stage=stage,
                )
            )

        broken = [item for item in findings if item["broken"]]

        result = {
            "ok": not broken,
            "ready": True,
            "version": cls.VERSION,
            "stage": stage,
            "text_count": len(findings),
            "broken_count": len(broken),
            "findings": findings,
            "broken_paths": [item["path"] for item in broken],
        }

        cls.print_result(result)
        return result

    @classmethod
    def inspect_text(
        cls,
        text: str,
        path: str,
        stage: str,
    ) -> Dict[str, Any]:
        reasons: List[str] = []
        text_length = max(len(text), 1)

        replacement_count = len(cls.REPLACEMENT_PATTERN.findall(text))
        question_mark_count = len(cls.QUESTION_MARK_PATTERN.findall(text))
        question_boundary_count = len(
            cls.QUESTION_BOUNDARY_PATTERN.findall(text)
        )
        cjk_count = len(cls.CJK_PATTERN.findall(text))
        hangul_count = len(cls.HANGUL_PATTERN.findall(text))
        box_drawing_count = len(cls.BOX_DRAWING_PATTERN.findall(text))
        mojibake_cluster_count = len(
            cls.MOJIBAKE_CLUSTER_PATTERN.findall(text)
        )

        suspicious_fragments = [
            fragment
            for fragment in cls.SUSPICIOUS_FRAGMENTS
            if fragment in text
        ]

        question_ratio = question_mark_count / text_length
        cjk_ratio = cjk_count / text_length
        hangul_ratio = hangul_count / text_length

        if replacement_count > 0:
            reasons.append("unicode_replacement_character")

        if suspicious_fragments:
            reasons.append("known_mojibake_fragment")

        if box_drawing_count > 0:
            reasons.append("box_drawing_character")

        if (
            question_mark_count >= 3
            and question_ratio >= 0.03
            and question_boundary_count >= 2
        ):
            reasons.append("mojibake_question_mark_density")

        if (
            cjk_count >= 3
            and cjk_ratio >= 0.04
            and (
                hangul_count == 0
                or cjk_count >= hangul_count
                or hangul_ratio < 0.20
            )
        ):
            reasons.append("abnormal_cjk_hangul_mix")

        if mojibake_cluster_count >= 2 and (
            question_mark_count >= 2
            or cjk_count >= 3
            or box_drawing_count > 0
        ):
            reasons.append("mojibake_cluster_pattern")

        reasons = list(dict.fromkeys(reasons))

        return {
            "stage": stage,
            "path": path,
            "broken": bool(reasons),
            "reasons": reasons,
            "length": len(text),
            "preview": cls._preview(text),
            "metrics": {
                "replacement_count": replacement_count,
                "question_mark_count": question_mark_count,
                "question_boundary_count": question_boundary_count,
                "cjk_count": cjk_count,
                "hangul_count": hangul_count,
                "box_drawing_count": box_drawing_count,
                "mojibake_cluster_count": mojibake_cluster_count,
                "question_ratio": round(question_ratio, 4),
                "cjk_ratio": round(cjk_ratio, 4),
                "hangul_ratio": round(hangul_ratio, 4),
            },
        }

    @classmethod
    def print_result(cls, result: Mapping[str, Any]) -> None:
        stage = str(result.get("stage") or "unknown")

        print(
            f"[Sprint128-3 UTF8 Guard] Version: {cls.VERSION}",
            flush=True,
        )
        print(
            f"[Sprint128-3 UTF8 Guard] Stage: {stage}",
            flush=True,
        )
        print(
            f"[Sprint128-3 UTF8 Guard] Text Count: "
            f"{result.get('text_count', 0)}",
            flush=True,
        )
        print(
            f"[Sprint128-3 UTF8 Guard] Broken Count: "
            f"{result.get('broken_count', 0)}",
            flush=True,
        )

        for item in result.get("findings", []) or []:
            status = "BROKEN" if item.get("broken") else "OK"

            print(
                f"[Sprint128-3 UTF8 Guard] {stage} {status}: "
                f"path={item.get('path', '')} "
                f"reasons={item.get('reasons', [])} "
                f"metrics={item.get('metrics', {})} "
                f"preview={item.get('preview', '')!r}",
                flush=True,
            )

    @classmethod
    def compare(
        cls,
        before: Mapping[str, Any],
        after: Mapping[str, Any],
    ) -> Dict[str, Any]:
        before_broken = int(before.get("broken_count", 0) or 0)
        after_broken = int(after.get("broken_count", 0) or 0)

        if before_broken > 0:
            first_broken_stage = str(
                before.get("stage") or "export_pack"
            )
        elif after_broken > 0:
            first_broken_stage = str(
                after.get("stage") or "publisher_result"
            )
        else:
            first_broken_stage = "none"

        result = {
            "ok": first_broken_stage == "none",
            "version": cls.VERSION,
            "first_broken_stage": first_broken_stage,
            "export_pack_broken_count": before_broken,
            "publisher_result_broken_count": after_broken,
        }

        print(
            "[Sprint128-3 UTF8 Guard] First Broken Stage:",
            first_broken_stage,
            flush=True,
        )
        print(
            "[Sprint128-3 UTF8 Guard] Summary:",
            result,
            flush=True,
        )

        return result

    @classmethod
    def _walk(
        cls,
        value: Any,
        path: str = "root",
    ) -> Iterable[Tuple[str, Any]]:
        if isinstance(value, Mapping):
            for key, child in value.items():
                child_path = f"{path}.{key}"

                if isinstance(child, (Mapping, list, tuple)):
                    yield from cls._walk(child, child_path)
                else:
                    yield child_path, child

            return

        if isinstance(value, (list, tuple)):
            for index, child in enumerate(value):
                child_path = f"{path}[{index}]"

                if isinstance(child, (Mapping, list, tuple)):
                    yield from cls._walk(child, child_path)
                else:
                    yield child_path, child

    @staticmethod
    def _to_text(value: Any) -> str:
        if isinstance(value, str):
            return value.strip()

        if isinstance(value, (list, tuple)):
            return " ".join(
                str(item).strip()
                for item in value
                if str(item).strip()
            )

        return ""

    @staticmethod
    def _preview(text: str, limit: int = 140) -> str:
        compact = " ".join(text.split())

        if len(compact) <= limit:
            return compact

        return compact[: limit - 3] + "..."