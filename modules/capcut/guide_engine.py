from modules.capcut.preset_engine import CapCutPresetEngine


class CapCutGuideEngine:
    def generate(self, payload):
        preset_name = payload.get("preset_name", "하센 기본")
        preset = CapCutPresetEngine().get(preset_name)

        return {
            "preset_name": preset_name,
            "preset": preset,
            "ratio": preset["ratio"],
            "subtitle_position": preset["position"],
            "font": preset["font"],
            "font_size": preset["font_size"],
            "stroke": preset["stroke"],
            "shadow": preset["shadow"],
            "animation": preset["animation"],
            "voice_db": preset["voice_db"],
            "bgm_db": preset["bgm_db"],
            "sfx": {
                "Pop": preset["pop_db"],
                "Click": preset["click_db"],
                "Whoosh": preset["whoosh_db"],
                "Water": preset["water_db"],
                "Door": preset["door_db"],
            },
            "edit_checklist": [
                "원본 영상 확보",
                "중국어 자막 위치 확인",
                "워터마크 위치 확인",
                "필요 시 크롭 또는 블러",
                "하센 자막 중앙 하단 / 하단 40% 배치",
                f"BGM {preset['bgm_db']}",
                f"Pop {preset['pop_db']} / Click {preset['click_db']} / Whoosh {preset['whoosh_db']}",
                "최종 9:16 저장",
            ],
            "cut_guide": [
                "0~2초: 가장 강한 사용 장면 또는 불편함 장면",
                "2~6초: 문제 상황",
                "6~13초: 제품 사용 장면",
                "13~18초: Before / After",
                "18~20초: CTA",
            ],
        }
