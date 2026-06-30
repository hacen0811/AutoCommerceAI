class CapCutPresetEngine:
    def presets(self):
        return {
            "하센 기본": {
                "ratio": "9:16",
                "font": "Pretendard 또는 기본 고딕",
                "font_size": "46",
                "stroke": "6",
                "shadow": "60%",
                "position": "중앙 하단 / 하단 40%",
                "animation": "Bounce",
                "voice_db": "20 dB",
                "bgm_db": "8 dB",
                "pop_db": "7 dB",
                "click_db": "8 dB",
                "whoosh_db": "6 dB",
                "water_db": "10 dB",
                "door_db": "9 dB",
            },
            "공감형": {
                "ratio": "9:16",
                "font": "Pretendard 또는 기본 고딕",
                "font_size": "46",
                "stroke": "6",
                "shadow": "60%",
                "position": "중앙 하단 / 하단 40%",
                "animation": "Fade In / Bounce",
                "voice_db": "20 dB",
                "bgm_db": "7 dB",
                "pop_db": "6 dB",
                "click_db": "7 dB",
                "whoosh_db": "5 dB",
                "water_db": "8 dB",
                "door_db": "8 dB",
            },
            "정보형": {
                "ratio": "9:16",
                "font": "Pretendard 또는 기본 고딕",
                "font_size": "46",
                "stroke": "6",
                "shadow": "60%",
                "position": "중앙 하단 / 하단 40%",
                "animation": "Slide Up",
                "voice_db": "20 dB",
                "bgm_db": "8 dB",
                "pop_db": "7 dB",
                "click_db": "8 dB",
                "whoosh_db": "6 dB",
                "water_db": "10 dB",
                "door_db": "9 dB",
            },
            "충격형": {
                "ratio": "9:16",
                "font": "Pretendard 또는 기본 고딕",
                "font_size": "48",
                "stroke": "7",
                "shadow": "65%",
                "position": "중앙 하단 / 하단 40%",
                "animation": "Pop / Bounce",
                "voice_db": "20 dB",
                "bgm_db": "10 dB",
                "pop_db": "9 dB",
                "click_db": "8 dB",
                "whoosh_db": "8 dB",
                "water_db": "10 dB",
                "door_db": "10 dB",
            },
        }

    def get(self, name="하센 기본"):
        return self.presets().get(name) or self.presets()["하센 기본"]

    def guide_text(self, name="하센 기본"):
        preset = self.get(name)
        lines = [f"[{name} CapCut 프리셋]"]
        lines += [
            f"영상비율: {preset['ratio']}",
            f"자막 폰트: {preset['font']}",
            f"자막 크기: {preset['font_size']}",
            f"자막 획: {preset['stroke']}",
            f"그림자: {preset['shadow']}",
            f"자막 위치: {preset['position']}",
            f"자막 애니메이션: {preset['animation']}",
            f"AI 음성: {preset['voice_db']}",
            f"BGM: {preset['bgm_db']}",
            f"Pop: {preset['pop_db']}",
            f"Click: {preset['click_db']}",
            f"Whoosh: {preset['whoosh_db']}",
            f"Water: {preset['water_db']}",
            f"Door: {preset['door_db']}",
        ]
        return "\n".join(lines)
