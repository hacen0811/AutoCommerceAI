import json
import os
from pathlib import Path
from typing import Any, Dict, List

from modules.content.prompts import PRODUCT_ANALYSIS_PROMPT, CONTENT_PACK_PROMPT


class ContentFactory:
    def status(self) -> Dict[str, Any]:
        openai_key = bool(os.getenv("OPENAI_API_KEY"))
        return {
            "openai_key": openai_key,
            "available": openai_key,
            "provider": "openai" if openai_key else "offline-template",
        }

    def _json_from_text(self, text: str) -> Dict[str, Any]:
        text = (text or "").strip()

        if text.startswith("```"):
            text = text.strip("`").strip()
            if text.lower().startswith("json"):
                text = text[4:].strip()

        start = text.find("{")
        end = text.rfind("}")

        if start >= 0 and end > start:
            text = text[start : end + 1]

        return json.loads(text)

    def _call_openai_json(self, prompt: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from openai import OpenAI  # type: ignore

            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            user_content = (
                prompt.strip()
                + "\n\n[입력 데이터]\n"
                + json.dumps(payload, ensure_ascii=False, indent=2)
            )
            
            print("\n========== CONTENT PACK PAYLOAD ==========")
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            print("=========================================\n")

            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {
                        "role": "user",
                        "content": user_content,
                    }
                ],
                temperature=0.7,
                response_format={"type": "json_object"},
            )

            return self._json_from_text(resp.choices[0].message.content or "{}")

        except Exception as e:
            return {
                "ok": False,
                "provider": "openai",
                "message": f"OpenAI 연결 실패: {e}",
            }

    def _source_payload(self, selected_sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        main = selected_sources[0] if selected_sources else {}

        return {
            "main": {
                "query": str(main.get("query", "선택 상품")).strip(),
                "platform": str(main.get("platform", "-")).strip(),
                "purpose": str(main.get("purpose", "-")).strip(),
                "score": str(main.get("score", "-")).strip(),
                "url": str(main.get("url", "")).strip(),
            },
            "selected_sources": selected_sources,
        }

    def _fallback_analysis(self, selected_sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        main = selected_sources[0] if selected_sources else {}

        query = str(main.get("query", "선택 상품")).strip()
        platform = str(main.get("platform", "-")).strip()
        purpose = str(main.get("purpose", "-")).strip()
        score = str(main.get("score", "-")).strip()
        url = str(main.get("url", "")).strip()

        return {
            "ok": False,
            "provider": "offline-template",
            "product_name": query,
            "platform": platform,
            "purpose": purpose,
            "score": score,
            "url": url,
            "summary": f"{query}는 쇼핑쇼츠에서 문제 해결형 콘텐츠로 풀기 좋은 상품입니다.",
            "usp": [
                "생활 속 불편함을 직관적으로 해결해주는 상품",
                "Before / After 구조로 보여주기 좋음",
                "짧은 영상에서 기능 전달이 쉬움",
            ],
            "target": [
                "생활용품과 살림템에 관심 있는 시청자",
                "실용적인 쇼핑 정보를 찾는 사용자",
                "시간과 불편함을 줄이고 싶은 사용자",
            ],
            "buying_points": [
                "사용 전후 차이가 명확함",
                "쇼츠에서 시각적으로 설명하기 좋음",
                "댓글 CTA와 연결하기 쉬움",
            ],
            "shorts_angles": [
                "공감형",
                "문제 해결형",
                "Before / After",
                "생활꿀팁형",
                "리뷰형",
            ],
            "hooks": [
                f"아직도 {query} 없이 불편하게 쓰세요?",
                "왜 이제 알았지 싶은 살림템입니다.",
                "이거 하나로 생활이 훨씬 편해집니다.",
                "써보기 전엔 몰랐던 차이입니다.",
                "살림 시간이 줄어드는 이유입니다.",
            ],
        }

    def analyze_product(self, selected_sources, project_name=""):
        selected_sources = selected_sources or []
        payload = self._source_payload(selected_sources)
        payload["project_name"] = project_name

        if self.status()["available"]:
            data = self._call_openai_json(PRODUCT_ANALYSIS_PROMPT, payload)

            if data.get("ok") is False:
                fallback = self._fallback_analysis(selected_sources)
                if project_name:
                    fallback["product_name"] = project_name
                return fallback

            main = payload["main"]
            data["ok"] = True
            data["provider"] = "openai"
            data["platform"] = main.get("platform", "-")
            data["purpose"] = main.get("purpose", "-")
            data["score"] = main.get("score", "-")
            data["url"] = main.get("url", "")

            if project_name:
                data["product_name"] = project_name
            elif not data.get("product_name"):
                data["product_name"] = main.get("query", "선택 상품")

            return data

        fallback = self._fallback_analysis(selected_sources)
        if project_name:
            fallback["product_name"] = project_name
        return fallback

    def _fallback_content_pack(self, project, selected_sources=None, analysis=None):
        selected_sources = selected_sources or []
        analysis = analysis or self.analyze_product(selected_sources)

        project_name = (
            getattr(project, "product_name", "")
            or getattr(project, "product_name", "")
            or getattr(project, "title", "")
            or "선택 상품"
        )

        return {
            "project_id": getattr(project, "id", ""),
            "project_name": project_name,
            "analysis": analysis,
            "shorts": {
                "titles": [
                    f"{project_name}, 왜 이제 알았지?",
                    f"생활이 편해지는 {project_name}",
                    f"아직도 불편하게 쓰고 계세요?",
                ],
                "hooks": analysis.get("hooks", []),
                "script": [
                    "아직도 이 불편함을 참고 계셨나요?",
                    f"오늘 소개할 제품은 {project_name}입니다.",
                    "사용 전에는 번거롭고 귀찮았던 부분이 있었는데요.",
                    "이 제품을 쓰면 훨씬 간단하게 해결할 수 있습니다.",
                    "작은 차이지만 매일 쓰면 체감이 큽니다.",
                    "제품 정보가 궁금하시면 댓글을 남겨주세요.",
                ],
                "cta": "댓글에 키워드를 남겨주세요 👇",
            },
            "capcut": {
                "timeline": [
                    {"time": "0-3초", "scene": "불편한 상황", "caption": "아직도 이렇게 쓰세요?"},
                    {"time": "3-8초", "scene": "제품 등장", "caption": "이거 하나면 편해집니다"},
                    {"time": "8-20초", "scene": "사용 장면", "caption": "사용 전후 차이"},
                    {"time": "20-35초", "scene": "장점 정리", "caption": "살림 시간이 줄어듭니다"},
                    {"time": "35-45초", "scene": "CTA", "caption": "댓글에 키워드 남겨주세요"},
                ],
                "bgm": "CapCut 밝고 경쾌한 생활템 BGM",
                "sfx": ["Pop", "Click", "Whoosh"],
            },
            "thumbnail": {
                "main_text": "왜 이제 알았지?",
                "sub_text": "생활이 편해지는 아이템",
                "image_prompt": f"9:16 쇼핑쇼츠 썸네일, {project_name}, 밝은 배경, 제품 강조, 한국어 큰 글씨 공간",
            },
            "inpock": {
                "size": "1000x1000",
                "title": project_name,
                "main_text": "생활이 편해지는 추천템",
                "image_prompt": f"1000x1000 인포크 링크 이미지, {project_name}, 깔끔한 쇼핑몰 스타일, 제품 중심",
            },
            "upload": {
                "youtube_title": f"{project_name} 추천템 #shorts",
                "youtube_desc": "🔗 제품 정보는 영상 아래 설명란 링크 또는 프로필 링크를 확인해주세요.",
                "instagram_body": "생활이 조금 편해지는 추천템입니다.\n\n제품 정보가 궁금하시면 댓글 남겨주세요 👇",
                "hashtags": [
                    "#쇼핑쇼츠",
                    "#생활용품추천",
                    "#살림템",
                    "#쿠팡추천",
                    "#shorts",
                ],
            },
        }

    def build_content_pack(self, project, selected_sources=None, analysis=None):
        selected_sources = selected_sources or []

        project_name_from_project = (
            getattr(project, "product_name", "")
            or getattr(project, "title", "")
            or "선택 상품"
        )

        analysis = analysis or self.analyze_product(
            selected_sources,
            project_name=project_name_from_project,
        )

        project_name = (
            project_name_from_project
            or analysis.get("product_name")
            or "선택 상품"
        )

        payload = {
            "project_id": getattr(project, "id", ""),
            "project_name": project_name,
            "analysis": analysis,
            "selected_sources": selected_sources,
        }

        if self.status()["available"]:
            data = self._call_openai_json(CONTENT_PACK_PROMPT, payload)

            if data.get("ok") is False:
                return self._fallback_content_pack(project, selected_sources, analysis)

            data["ok"] = True
            data["provider"] = "openai"
            data["project_id"] = getattr(project, "id", "")
            data["project_name"] = project_name
            data["analysis"] = analysis

            return data

        return self._fallback_content_pack(project, selected_sources, analysis)

    def save_content_pack(self, project, content_pack):
        out_dir = Path("exports/content_packs")
        out_dir.mkdir(parents=True, exist_ok=True)

        project_id = str(getattr(project, "id", "project")).replace(" ", "_")

        json_path = out_dir / f"{project_id}_content_pack.json"
        txt_path = out_dir / f"{project_id}_content_pack.txt"

        json_path.write_text(
            json.dumps(content_pack, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        txt_lines = self.to_text(content_pack)
        txt_path.write_text(txt_lines, encoding="utf-8")

        return {
            "json_path": str(json_path),
            "txt_path": str(txt_path),
            "data": content_pack,
        }

    def to_text(self, content_pack):
        lines = []

        lines.append("[AI 콘텐츠 팩]")
        lines.append("")
        lines.append(f"프로젝트: {content_pack.get('project_name', '')}")
        lines.append(f"생성방식: {content_pack.get('provider', 'offline-template')}")
        lines.append("")

        lines.append("[상품 분석]")
        analysis = content_pack.get("analysis", {})
        lines.append(analysis.get("summary", ""))

        lines.append("")
        lines.append("[쇼츠 제목]")
        for title in content_pack.get("shorts", {}).get("titles", []):
            lines.append(f"- {title}")

        lines.append("")
        lines.append("[후킹]")
        for hook in content_pack.get("shorts", {}).get("hooks", []):
            lines.append(f"- {hook}")

        lines.append("")
        lines.append("[대본]")
        for line in content_pack.get("shorts", {}).get("script", []):
            if isinstance(line, dict):
                lines.append(
                    f"- {line.get('time', '')} / {line.get('role', '')} / {line.get('line', '')}"
                )
            else:
                lines.append(f"- {line}")

        lines.append("")
        lines.append("[CapCut]")
        for item in content_pack.get("capcut", {}).get("timeline", []):
            if isinstance(item, dict):
                lines.append(
                    f"- {item.get('time')} / {item.get('scene')} / {item.get('caption')}"
                )
            else:
                lines.append(f"- {item}")

        lines.append("")
        lines.append("[썸네일]")
        lines.append(content_pack.get("thumbnail", {}).get("main_text", ""))

        lines.append("")
        lines.append("[인포크]")
        lines.append(content_pack.get("inpock", {}).get("main_text", ""))

        lines.append("")
        lines.append("[업로드]")
        upload = content_pack.get("upload", {})
        lines.append(upload.get("youtube_title", ""))
        lines.append(upload.get("youtube_desc", ""))
        lines.append(upload.get("instagram_body", ""))

        return "\n".join(lines)