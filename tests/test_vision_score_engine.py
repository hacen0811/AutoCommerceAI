from modules.video.vision_score_engine import VisionScoreEngine
from modules.video.smart_cut_engine import SmartCutEngine


def test_vision_score_prefers_product_frame():
    video_ai = {
        "samples": [
            {"time": 1.0, "score": 60, "brightness": 100, "contrast": 40, "change": 10, "frame": "a.jpg"},
            {"time": 2.0, "score": 55, "brightness": 100, "contrast": 40, "change": 10, "frame": "b.jpg"},
        ]
    }
    yolo = {"detections": [{"time": 1.0, "label": "bottle", "confidence": 0.9, "role": "상품 후보"}]}
    result = VisionScoreEngine().score_frames(video_ai, yolo, {})
    assert result["frames"][0]["time"] == 1.0


def test_smart_cut_v2_build():
    video_ai = {
        "ok": True,
        "samples": [
            {"time": 1.0, "score": 80, "brightness": 120, "contrast": 40, "change": 15, "frame": "a.jpg"},
        ],
        "scene_changes": [],
    }
    result = SmartCutEngine().build(video_ai, "문틈 방충망", "방충망")
    assert result["version"] == "2.0"
    assert result["hook_cut"]["time"] == 1.0
