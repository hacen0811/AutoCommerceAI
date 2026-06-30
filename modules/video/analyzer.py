from modules.video.media_info import MediaInfo


class VideoAnalyzer:
    def analyze(self, video_path):
        info = MediaInfo().analyze(video_path)

        safe_area = {
            "default_subtitle_position": "중앙 하단 / 하단 40%",
            "when_bottom_caption_exists": "자막을 45~50% 높이로 올리기",
            "when_top_caption_exists": "자막을 중앙 하단 40% 유지",
            "when_side_logo_exists": "로고 반대편으로 상품/텍스트 배치",
            "crop": "9:16 유지, 워터마크가 가장자리면 105~115% 확대 크롭",
        }

        edit_risk = []
        if info.get("warning"):
            edit_risk.append(info["warning"])
        if info.get("orientation") and "가로" in info.get("orientation"):
            edit_risk.append("가로 영상입니다. 9:16 크롭이 필요할 수 있습니다.")
        edit_risk += [
            "타오바오/도우인 원본 영상은 중국어 자막 또는 워터마크가 있을 수 있음",
            "하단 자막이 있으면 하센 자막은 중앙 하단보다 약간 위로 조정 권장",
            "우측/좌측 로고가 있으면 크롭 또는 블러 확인 필요",
        ]

        timeline = [
            {"time": "0~2초", "use": "후킹", "guide": "가장 강한 장면 또는 문제 상황", "capcut": "Zoom In / Pop 7 dB"},
            {"time": "2~5초", "use": "공감", "guide": "사용 전 불편함", "capcut": "BGM 8 dB"},
            {"time": "5~10초", "use": "사용", "guide": "제품 설치/사용 장면", "capcut": "Click 8 dB"},
            {"time": "10~15초", "use": "효과", "guide": "Before/After", "capcut": "Whoosh 6 dB"},
            {"time": "15~20초", "use": "CTA", "guide": "댓글 키워드 안내", "capcut": "Pop 7 dB"},
        ]

        return {
            **info,
            "safe_area": safe_area,
            "edit_risk": edit_risk,
            "timeline": timeline,
        }
