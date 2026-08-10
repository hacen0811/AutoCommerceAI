from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional


class TypecastTTSGenerator:
    VERSION = "typecast-tts-generator-193-33"

    @classmethod
    def generate(
        cls,
        text: str,
        output_path,
        voice_id: str = "",
        voice_name: str = "지안",
        api_key: str = "",
        speech_speed: float = 1.0,
        volume_percent: int = 100,
        model: str = "ssfm-v30",
        language: str = "kor",
    ) -> Dict[str, Any]:
        text = str(text or "").strip()
        target = Path(output_path)

        if not text:
            return {"ok": False, "status": "text_missing", "output_path": ""}

        resolved_key = str(
            api_key or os.getenv("TYPECAST_API_KEY", "") or ""
        ).strip()
        if not resolved_key:
            return {
                "ok": False,
                "status": "api_key_missing",
                "output_path": "",
            }

        try:
            from typecast import Typecast
            from typecast.models import TTSRequest, Output

            client = Typecast(api_key=resolved_key)
            resolved_voice_id = str(voice_id or "").strip()
            resolved_voice_name = str(voice_name or "지안").strip() or "지안"

            if not resolved_voice_id:
                for item in list(client.voices_v2() or []):
                    if (
                        str(getattr(item, "voice_name", "") or "").strip()
                        == resolved_voice_name
                    ):
                        resolved_voice_id = str(
                            getattr(item, "voice_id", "") or ""
                        ).strip()
                        if resolved_voice_id:
                            break

            if not resolved_voice_id:
                return {
                    "ok": False,
                    "status": "voice_id_missing",
                    "voice_name": resolved_voice_name,
                    "output_path": "",
                }

            volume_pct = max(0, min(200, int(volume_percent or 100)))
            target_lufs = -32.0 + (volume_pct / 200.0) * 24.0
            tempo = max(0.5, min(2.0, float(speech_speed or 1.0)))

            response = client.text_to_speech(
                TTSRequest(
                    text=text,
                    model=str(model or "ssfm-v30"),
                    voice_id=resolved_voice_id,
                    language=str(language or "kor"),
                    output=Output(
                        target_lufs=float(target_lufs),
                        audio_tempo=float(tempo),
                        audio_format="mp3",
                    ),
                )
            )

            target.parent.mkdir(parents=True, exist_ok=True)

            audio_bytes = None
            for attr_name in ("audio_data", "audio", "content", "data"):
                candidate = getattr(response, attr_name, None)
                if isinstance(candidate, (bytes, bytearray)) and candidate:
                    audio_bytes = bytes(candidate)
                    break

            if audio_bytes is not None:
                target.write_bytes(audio_bytes)
            elif hasattr(response, "save") and callable(response.save):
                response.save(str(target))
            elif hasattr(response, "save_to_file") and callable(response.save_to_file):
                response.save_to_file(str(target))
            else:
                raise RuntimeError(
                    "Typecast 응답에서 오디오 데이터를 찾지 못했습니다. "
                    f"response_type={type(response).__name__}"
                )

            if not target.is_file() or target.stat().st_size <= 1024:
                raise RuntimeError(
                    f"Typecast 음성 파일 생성 실패: {target}"
                )

            result = {
                "ok": True,
                "status": "typecast_generated",
                "output_path": str(target),
                "voice_name": resolved_voice_name,
                "voice_id": resolved_voice_id,
                "bytes": int(target.stat().st_size),
                "target_lufs": float(target_lufs),
                "speech_speed": float(tempo),
            }
            print("[Sprint193-18 Typecast TTS] GENERATED", result, flush=True)
            return result

        except Exception as exc:
            result = {
                "ok": False,
                "status": "typecast_failed",
                "output_path": "",
                "voice_name": str(voice_name or "지안"),
                "error": f"{type(exc).__name__}: {exc}",
            }
            print("[Sprint193-18 Typecast TTS] ERROR", result, flush=True)
            return result


VERSION = TypecastTTSGenerator.VERSION
