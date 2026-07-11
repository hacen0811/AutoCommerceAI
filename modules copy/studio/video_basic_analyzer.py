from pathlib import Path


class VideoBasicAnalyzer:
    """Local video analyzer for Shorts Studio 3.7.

    Uses OpenCV when installed. It returns metadata plus simple scene signals
    such as brightness and motion candidates. Optional OCR/YOLO can be plugged in
    later without changing the UI.
    """

    def analyze(self, video_path='', sample_count=6):
        if not video_path:
            return {'ok': False, 'message': '원본 영상 없음', 'frames': [], 'summary': '영상이 업로드되지 않았습니다.'}
        path = Path(str(video_path))
        if not path.exists():
            return {'ok': False, 'message': '영상 파일을 찾을 수 없음', 'path': str(path), 'frames': [], 'summary': '영상 경로가 없습니다.'}
        try:
            import cv2  # type: ignore
            import numpy as np  # type: ignore
        except Exception:
            return {'ok': True, 'mode': 'fallback', 'path': str(path), 'frames': [], 'summary': 'OpenCV 미설치: 파일 경로만 확인했습니다.', 'file_size_mb': round(path.stat().st_size / 1024 / 1024, 2)}

        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            return {'ok': False, 'message': '영상을 열 수 없음', 'path': str(path), 'frames': [], 'summary': '영상 열기 실패'}
        fps = cap.get(cv2.CAP_PROP_FPS) or 0
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration = round(frame_count / fps, 2) if fps else 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        total = max(1, int(sample_count or 6))
        picks = []
        prev_gray = None
        if frame_count > 0:
            for idx in range(total):
                frame_no = int(frame_count * (idx + 1) / (total + 1))
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
                ok, frame = cap.read()
                row = {'frame': frame_no, 'time_sec': round(frame_no / fps, 2) if fps else 0}
                if ok and frame is not None:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    brightness = float(gray.mean())
                    contrast = float(gray.std())
                    row['brightness'] = round(brightness, 1)
                    row['contrast'] = round(contrast, 1)
                    row['brightness_label'] = '밝음' if brightness >= 150 else ('어두움' if brightness < 85 else '보통')
                    row['text_safe'] = self._caption_safe(width, height)
                    if prev_gray is not None:
                        small = cv2.resize(gray, (160, 90))
                        prev_small = cv2.resize(prev_gray, (160, 90))
                        motion = float(np.mean(cv2.absdiff(small, prev_small)))
                        row['motion_score'] = round(motion, 1)
                    else:
                        row['motion_score'] = 0
                    prev_gray = gray
                picks.append(row)
        cap.release()
        ratio = '9:16' if height > width else '16:9/가로'
        best_hook = max(picks, key=lambda x: (x.get('motion_score', 0), x.get('contrast', 0)), default={})
        safe = self._caption_safe(width, height)
        return {
            'ok': True,
            'mode': 'opencv-3.7',
            'path': str(path),
            'width': width,
            'height': height,
            'ratio': ratio,
            'fps': round(fps, 2) if fps else 0,
            'duration_sec': duration,
            'frames': picks,
            'best_hook_time_sec': best_hook.get('time_sec', 0),
            'caption_safe_area': safe,
            'recommended_edit': self._recommend_edit(ratio, duration, best_hook),
            'summary': f'{duration}초 / {width}x{height} / {ratio} / 추천 후킹 {best_hook.get("time_sec", 0)}초',
        }

    def _caption_safe(self, width, height):
        return {
            'position': '중앙 하단',
            'bottom_percent': 40,
            'max_lines': 2,
            'note': 'CapCut 자막은 하단 40% 위쪽, 2줄 이하 권장',
        }

    def _recommend_edit(self, ratio, duration, hook):
        tips = []
        if ratio == '16:9/가로':
            tips.append('9:16 캔버스에 중앙 크롭 + 배경 블러 적용')
        if duration and duration > 45:
            tips.append('35초 이하로 핵심 사용 장면만 컷 편집')
        tips.append(f"첫 화면은 {hook.get('time_sec', 0)}초 부근 움직임 큰 장면 추천")
        tips.append('후킹 자막은 0~2초 안에 크게 표시')
        return tips
