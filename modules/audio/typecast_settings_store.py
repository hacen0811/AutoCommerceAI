from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class TypecastSettingsStore:
    VERSION = "typecast-settings-store-193-33"
    PATH = Path("secrets") / "typecast_settings.json"

    @classmethod
    def load(cls) -> Dict[str, Any]:
        result = {
            "api_key": "",
            "last_voice_name": "지안",
            "last_voice_id": "",
        }
        try:
            if cls.PATH.is_file():
                data = json.loads(cls.PATH.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    result["api_key"] = str(data.get("api_key") or "").strip()
                    result["last_voice_name"] = (
                        str(
                            data.get("last_voice_name")
                            or data.get("default_voice")
                            or "지안"
                        ).strip()
                        or "지안"
                    )
                    result["last_voice_id"] = str(
                        data.get("last_voice_id") or ""
                    ).strip()

                    # Older Sprint193-10 format compatibility.
                    voices = data.get("voices")
                    if (
                        not result["last_voice_id"]
                        and isinstance(voices, dict)
                    ):
                        result["last_voice_id"] = str(
                            voices.get(result["last_voice_name"]) or ""
                        ).strip()
        except Exception as exc:
            print(
                "[Sprint193-17 Typecast Settings] LOAD ERROR",
                type(exc).__name__,
                str(exc),
                flush=True,
            )
        return result

    @classmethod
    def save(
        cls,
        payload=None,
        api_key="",
        last_voice_name="지안",
        last_voice_id="",
        **kwargs,
    ) -> Dict[str, Any]:
        # Supports both:
        # save({"api_key": "...", ...})
        # save(api_key="...", last_voice_name="...", last_voice_id="...")
        if isinstance(payload, dict):
            data = dict(payload)
        else:
            data = {}
            if payload not in (None, ""):
                # Legacy first positional value interpreted as API key.
                data["api_key"] = payload

        if api_key:
            data["api_key"] = api_key
        if last_voice_name:
            data.setdefault("last_voice_name", last_voice_name)
        if last_voice_id:
            data["last_voice_id"] = last_voice_id
        data.update(kwargs)

        current = cls.load()
        clean = {
            "api_key": str(
                data.get("api_key", current.get("api_key", "")) or ""
            ).strip(),
            "last_voice_name": (
                str(
                    data.get(
                        "last_voice_name",
                        current.get("last_voice_name", "지안"),
                    )
                    or "지안"
                ).strip()
                or "지안"
            ),
            "last_voice_id": str(
                data.get(
                    "last_voice_id",
                    current.get("last_voice_id", ""),
                )
                or ""
            ).strip(),
        }

        cls.PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.PATH.write_text(
            json.dumps(clean, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        print(
            "[Sprint193-17 Typecast Settings] SAVED",
            {
                "api_key_present": bool(clean["api_key"]),
                "voice_name": clean["last_voice_name"],
                "voice_id_present": bool(clean["last_voice_id"]),
                "path": str(cls.PATH),
            },
            flush=True,
        )
        return clean
