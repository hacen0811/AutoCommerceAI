from pathlib import Path
import json

CONFIG_PATH = Path("config/local_settings.json")

DEFAULT_CONFIG = {
    "app_name": "AutoCommerceAI",
    "version": "1.1",
    "capcut": {
        "voice_db": "20 dB",
        "bgm_db": "8 dB",
        "pop_db": "7 dB",
        "click_db": "8 dB",
        "whoosh_db": "6 dB",
        "subtitle_position": "중앙 하단 / 하단 40%",
    },
    "ai_models": {
        "yolo_model": "yolov8n.pt",
        "paddleocr_lang": "ch",
    },
}


class AppConfig:
    def load(self):
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not CONFIG_PATH.exists():
            self.save(DEFAULT_CONFIG)
            return DEFAULT_CONFIG
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            return DEFAULT_CONFIG

    def save(self, data):
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return data
