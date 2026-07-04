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
                messages=[{"role": "user", "content": user_content}],
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
                    "아직도 불편하게 쓰고 계세요?",
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
                "sub_text": project_name,
                "image_prompt": f"9:16 쇼핑쇼츠 썸네일, {project_name}, 밝은 배경, 제품 강조, 한국어 큰 글씨 공간",
            },
            "inpock": {
                "size": "1000x1000",
                "title": project_name,
                "main_text": "생활이 편해지는 추천템",
                "sub_text": "제품 정보는 링크에서 확인",
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

        clean_analysis = self._clean_content_analysis(analysis, project_name)

        payload = {
            "project_id": getattr(project, "id", ""),
            "project_name": project_name,
            "analysis": clean_analysis,
        }

        if self.status()["available"]:
            data = self._call_openai_json(CONTENT_PACK_PROMPT, payload)

            if data.get("ok") is False:
                data = self._fallback_content_pack(
                    project,
                    selected_sources,
                    clean_analysis,
                )
            else:
                data["ok"] = True
                data["provider"] = "openai"
                data["project_id"] = getattr(project, "id", "")
                data["project_name"] = project_name
                data["analysis"] = clean_analysis

            data = self._normalize_content_pack_product_name(
                data,
                project_name,
                selected_sources,
            )

            data = self.apply_selected_variant(data)
            return data

        data = self._fallback_content_pack(
            project,
            selected_sources,
            clean_analysis,
        )

        data = self._normalize_content_pack_product_name(
            data,
            project_name,
            selected_sources,
        )

        data = self.apply_selected_variant(data)
        return data

    def apply_selected_variant(self, content_pack):
        shorts = content_pack.get("shorts", {})
        titles = shorts.get("titles", [])
        hooks = shorts.get("hooks", [])
        script = shorts.get("script", [])

        selected_variant = content_pack.get("selected_variant") or {}

        if not selected_variant:
            selected_variant = {
                "title": titles[0] if titles else "",
                "hook": hooks[0] if hooks else "",
                "script": script,
                "cta": shorts.get("cta", ""),
            }

        content_pack["selected_variant"] = selected_variant

        title = selected_variant.get("title", "")
        hook = selected_variant.get("hook", "")
        cta = selected_variant.get("cta", "")

        if title:
            content_pack.setdefault("upload", {})
            content_pack["upload"]["youtube_title"] = title

        if hook:
            content_pack.setdefault("thumbnail", {})
            content_pack["thumbnail"]["main_text"] = hook

            content_pack.setdefault("inpock", {})
            content_pack["inpock"]["main_text"] = hook

        if cta:
            content_pack.setdefault("upload", {})
            instagram_body = content_pack["upload"].get("instagram_body", "")
            if cta not in instagram_body:
                content_pack["upload"]["instagram_body"] = (
                    instagram_body.rstrip() + "\n\n" + cta
                )

        return content_pack

    def _clean_content_analysis(self, analysis, project_name):
        if not isinstance(analysis, dict):
            return {"product_name": project_name}

        cleaned = dict(analysis)
        cleaned["product_name"] = project_name

        for key in ["query", "source_query", "search_query"]:
            cleaned.pop(key, None)

        return cleaned

    def _normalize_content_pack_product_name(
        self,
        data,
        project_name,
        selected_sources=None,
    ):
        if not isinstance(data, dict) or not project_name:
            return data

        selected_sources = selected_sources or []
        bad_words = []

        for source in selected_sources:
            if not isinstance(source, dict):
                continue

            query = str(source.get("query", "")).strip()
            if query and query != project_name:
                bad_words.append(query)

        bad_words = sorted(set(bad_words), key=len, reverse=True)

        def replace_text(value):
            if isinstance(value, str):
                for word in bad_words:
                    value = value.replace(word, project_name)
                return value

            if isinstance(value, list):
                return [replace_text(item) for item in value]

            if isinstance(value, dict):
                return {key: replace_text(item) for key, item in value.items()}

            return value

        return replace_text(data)

    def save_content_pack(self, project, content_pack):
        out_dir = Path("exports/content_packs")
        out_dir.mkdir(parents=True, exist_ok=True)

        project_id = str(getattr(project, "id", "project")).replace(" ", "_")

        json_path = out_dir / f"{project_id}_content_pack.json"
        txt_path = out_dir / f"{project_id}_content_pack.txt"

        capcut_edit_txt_path = out_dir / f"{project_id}_capcut_edit.txt"
        thumbnail_prompt_txt_path = out_dir / f"{project_id}_thumbnail_prompt.txt"
        inpock_prompt_txt_path = out_dir / f"{project_id}_inpock_prompt.txt"
        upload_txt_path = out_dir / f"{project_id}_upload_text.txt"

        json_path.write_text(
            json.dumps(content_pack, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        txt_lines = self.to_text(content_pack)
        txt_path.write_text(txt_lines, encoding="utf-8")

        selected_variant = content_pack.get("selected_variant") or {}
        capcut = content_pack.get("capcut") or {}
        thumbnail = content_pack.get("thumbnail") or {}
        inpock = content_pack.get("inpock") or {}
        upload_bundle = content_pack.get("upload_bundle") or {}

        capcut_edit_txt_path.write_text(
            self.to_capcut_edit_text(content_pack, selected_variant, capcut),
            encoding="utf-8",
        )

        thumbnail_prompt_txt_path.write_text(
            self.to_thumbnail_prompt_text(content_pack, selected_variant, thumbnail),
            encoding="utf-8",
        )

        inpock_prompt_txt_path.write_text(
            self.to_inpock_prompt_text(content_pack, selected_variant, inpock),
            encoding="utf-8",
        )

        upload_txt_path.write_text(
            self.to_upload_text(content_pack, selected_variant, upload_bundle),
            encoding="utf-8",
        )

        return {
            "json_path": str(json_path),
            "txt_path": str(txt_path),
            "capcut_edit_txt_path": str(capcut_edit_txt_path),
            "thumbnail_prompt_txt_path": str(thumbnail_prompt_txt_path),
            "inpock_prompt_txt_path": str(inpock_prompt_txt_path),
            "upload_txt_path": str(upload_txt_path),
            "data": content_pack,
        }
    
    


    def to_text(self, content_pack):
        lines = []

        variants = content_pack.get("shorts_variants", [])

        selected = next(
            (v for v in variants if v.get("recommended")),
            variants[0] if variants else {},
        )

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
        if selected.get("title"):
            lines.append(f"- {selected.get('title')}")
        else:
            for title in content_pack.get("shorts", {}).get("titles", []):
                lines.append(f"- {title}")

        lines.append("")
        lines.append("[후킹]")
        if selected.get("hook"):
            lines.append(f"- {selected.get('hook')}")
        else:
            for hook in content_pack.get("shorts", {}).get("hooks", []):
                lines.append(f"- {hook}")

        lines.append("")
        lines.append("[대본]")
        script = selected.get("script") or content_pack.get("shorts", {}).get("script", [])
        self._append_script_lines(lines, script)

        lines.append("")
        lines.append("[CapCut]")
        for item in content_pack.get("capcut", {}).get("timeline", []):
            if isinstance(item, dict):
                lines.append(
                    f"- {item.get('time', '')} / {item.get('scene', '')} / {item.get('caption', '')}"
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

    def to_capcut_edit_text(self, content_pack, selected_variant, capcut):
        lines = ["[CapCut 편집 TXT]", ""]

        timeline = capcut.get("timeline", [])
        if timeline:
            lines.append("[타임라인]")
            for item in timeline:
                if isinstance(item, dict):
                    lines.append(
                        f"- {item.get('time', '')} / {item.get('scene', '')} / {item.get('caption', '')}"
                    )
                else:
                    lines.append(f"- {item}")

        lines.append("")
        lines.append("[BGM]")
        lines.append(str(capcut.get("bgm", "")))

        lines.append("")
        lines.append("[SFX]")
        for item in capcut.get("sfx", []):
            lines.append(f"- {item}")

        lines.append("")
        lines.append("[대표 대본]")
        script = selected_variant.get("script") or content_pack.get("shorts", {}).get("script", [])
        self._append_script_lines(lines, script)

        return "\n".join(lines)

    def to_thumbnail_prompt_text(self, content_pack, selected_variant, thumbnail):
        lines = [
            "[썸네일 Prompt TXT]",
            "",
            "[메인 문구]",
            thumbnail.get("main_text", ""),
            "",
            "[서브 문구]",
            thumbnail.get("sub_text", ""),
            "",
            "[이미지 프롬프트]",
            thumbnail.get("image_prompt") or thumbnail.get("prompt") or "",
        ]

        return "\n".join(lines)

    def to_inpock_prompt_text(self, content_pack, selected_variant, inpock):
        lines = [
            "[인포크 Prompt TXT]",
            "",
            "[사이즈]",
            inpock.get("size", "1000x1000"),
            "",
            "[타이틀]",
            inpock.get("title", ""),
            "",
            "[메인 문구]",
            inpock.get("main_text", ""),
            "",
            "[서브 문구]",
            inpock.get("sub_text", ""),
            "",
            "[이미지 프롬프트]",
            inpock.get("image_prompt") or inpock.get("prompt") or "",
        ]

        return "\n".join(lines)

    def to_upload_text(self, content_pack, selected_variant, upload_bundle):
        upload = content_pack.get("upload", {})

        lines = [
            "[업로드 문구 TXT]",
            "",
            "[YouTube 제목]",
            upload.get("youtube_title", ""),
            "",
            "[YouTube 설명]",
            upload.get("youtube_desc", ""),
            "",
            "[Instagram 본문]",
            upload.get("instagram_body", ""),
            "",
            "[해시태그]",
        ]

        for tag in upload.get("hashtags", []):
            lines.append(tag)

        return "\n".join(lines)


    def _append_script_lines(self, lines, script):
        if isinstance(script, list):
            for line in script:
                if isinstance(line, dict):
                    lines.append(
                        f"- {line.get('time', '')} / {line.get('role', '')} / {line.get('line', '')}"
                    )
                else:
                    lines.append(f"- {line}")
        elif script:
            lines.append(str(script))
