from pathlib import Path


class VisionOverlayExporter:
    def export(self, video_path, regions, output_name="vision_regions.jpg"):
        path = Path(video_path or "")
        if not video_path or not path.exists():
            return ""

        try:
            import cv2
        except Exception:
            return ""

        cap = cv2.VideoCapture(str(path))
        ret, frame = cap.read()
        cap.release()

        if not ret:
            return ""

        colors = {
            "top_text": (255, 200, 0),
            "bottom_caption": (0, 0, 255),
            "center_product": (0, 255, 0),
            "left_logo": (255, 0, 255),
            "right_logo": (255, 0, 255),
            "bottom_left_mark": (0, 165, 255),
            "bottom_right_mark": (0, 165, 255),
        }

        for key, box in regions.items():
            x1, y1, x2, y2 = box
            color = colors.get(key, (255, 255, 255))
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
            cv2.putText(frame, key, (x1 + 8, max(25, y1 + 28)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        out_dir = Path("exports/vision_overlay")
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / output_name
        cv2.imwrite(str(out), frame)
        return str(out)
