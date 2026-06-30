from modules.pipeline.real_vision_runner import RealVisionRunner


class BatchAnalyzer:
    """
    소스 영상 후보를 프로젝트에 하나씩 연결해 Real Vision Runner로 분석합니다.
    기존 project.video_path를 임시 변경하는 방식이므로 저장소 DB를 직접 변경하지 않습니다.
    """

    def analyze(self, project, video_items, limit=5, sample_count=6):
        results = []
        original_video = getattr(project, "video_path", "")

        for item in (video_items or [])[:limit]:
            try:
                project.video_path = item.get("path", "")
                result = RealVisionRunner().run(project, sample_count=sample_count, use_yolo=True, use_paddle=True)
                results.append({
                    "source": item,
                    "summary": result.get("summary"),
                    "status": result.get("status", {}),
                    "smart_cut": result.get("smart_cut", {}),
                    "caption_safe": result.get("caption_safe", {}),
                    "ok": result.get("ok", False),
                })
            except Exception as exc:
                results.append({
                    "source": item,
                    "ok": False,
                    "error": str(exc),
                })

        project.video_path = original_video
        return results
