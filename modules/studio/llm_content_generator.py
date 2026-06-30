import json
import os
from typing import Any, Dict


class LLMContentGenerator:
    """Optional real AI connector for Shorts Studio.

    - Uses OpenAI when OPENAI_API_KEY is set and openai package is installed.
    - Uses Gemini when GEMINI_API_KEY or GOOGLE_API_KEY is set.
    - Returns a safe fallback when no key is configured, so the app never stops.
    """

    def status(self) -> Dict[str, Any]:
        openai_key = bool(os.getenv("OPENAI_API_KEY"))
        gemini_key = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
        return {
            "openai_key": openai_key,
            "gemini_key": gemini_key,
            "available": openai_key or gemini_key,
            "provider": "openai" if openai_key else ("gemini" if gemini_key else "offline-template"),
        }

    def generate(self, product: Dict[str, Any], vision: Dict[str, Any], keyword: str, durations=(15, 25, 35)) -> Dict[str, Any]:
        st = self.status()
        if st["provider"] == "openai":
            return self._generate_openai(product, vision, keyword, durations)
        if st["provider"] == "gemini":
            return self._generate_gemini(product, vision, keyword, durations)
        return {"ok": False, "provider": "offline-template", "message": "API 키 없음: 기본 템플릿으로 생성합니다."}

    def _prompt(self, product: Dict[str, Any], vision: Dict[str, Any], keyword: str, durations) -> str:
        pname = product.get("name") or product.get("coupang", {}).get("product_name") or "쿠팡 추천상품"
        return f"""
너는 한국 쇼핑쇼츠/인스타 릴스 기획자다. CapCut 편집 기준으로 작성한다.
상품명: {pname}
가격: {product.get('coupang', {}).get('price') or product.get('price') or ''}
카테고리: {product.get('coupang', {}).get('category') or product.get('category') or ''}
댓글 키워드: {keyword}
영상 분석: {json.dumps(vision, ensure_ascii=False)[:2500]}

아래 JSON만 반환해라. 설명 금지.
{{
  "hooks": ["후킹1", "후킹2", "후킹3"],
  "scripts": {{
    "15s": [{{"time":"0~2초","role":"후킹","line":"..."}}],
    "25s": [{{"time":"0~3초","role":"후킹","line":"..."}}],
    "35s": [{{"time":"0~3초","role":"후킹","line":"..."}}]
  }},
  "youtube": {{"title":"... #shorts", "description":"...", "hashtags":"..."}},
  "instagram": {{"caption":"...", "hashtags":"..."}},
  "capcut_tips": ["편집 팁1", "편집 팁2", "편집 팁3"],
  "thumbnail": {{"main_text":"...", "sub_text":"...", "copy_options":["...","...","..."]}}
}}
규칙: 과장 광고, 의학적 효능, 확정적 효과 표현 금지. 자연스러운 생활 공감형. CTA는 댓글에 '{keyword}' 남겨주세요.
""".strip()

    def _json_from_text(self, text: str) -> Dict[str, Any]:
        text = (text or "").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start:end+1]
        return json.loads(text)

    def _generate_openai(self, product, vision, keyword, durations):
        try:
            from openai import OpenAI  # type: ignore
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": self._prompt(product, vision, keyword, durations)}],
                temperature=0.7,
                response_format={"type": "json_object"},
            )
            data = self._json_from_text(resp.choices[0].message.content or "{}")
            data["ok"] = True
            data["provider"] = "openai"
            return data
        except Exception as e:
            return {"ok": False, "provider": "openai", "message": f"OpenAI 연결 실패: {e}"}

    def _generate_gemini(self, product, vision, keyword, durations):
        try:
            import urllib.request
            key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            payload = {"contents": [{"parts": [{"text": self._prompt(product, vision, keyword, durations)}]}]}
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = json.loads(r.read().decode("utf-8"))
            text = raw.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "{}")
            data = self._json_from_text(text)
            data["ok"] = True
            data["provider"] = "gemini"
            return data
        except Exception as e:
            return {"ok": False, "provider": "gemini", "message": f"Gemini 연결 실패: {e}"}
