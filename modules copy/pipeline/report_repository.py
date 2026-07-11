import json
from datetime import datetime
from pathlib import Path


class PipelineReportRepository:
    def __init__(self):
        self.base = Path("exports/real_vision_reports")
        self.base.mkdir(parents=True, exist_ok=True)

    def save(self, project, report):
        safe_name = "".join(c for c in project.product_name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        if not safe_name:
            safe_name = f"project_{project.id}"

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = self.base / f"{safe_name}_{ts}.json"
        txt_path = self.base / f"{safe_name}_{ts}.txt"

        json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        lines = [
            f"# Real Vision Report - {project.product_name}",
            "",
            f"요약: {report.get('summary')}",
            "",
            "## 상태",
        ]
        for k, v in report.get("status", {}).items():
            lines.append(f"- {k}: {'OK' if v else 'NO'}")

        lines += ["", "## 다음 작업"]
        for item in report.get("next_actions", []):
            lines.append(f"- [ ] {item}")

        lines += ["", "## Auto Editor 타임라인"]
        for cut in report.get("auto_editor", {}).get("timeline", []):
            lines.append(f"- {cut.get('time')} / {cut.get('role') or cut.get('scene')}: {cut.get('caption')} / {cut.get('capcut')}")

        txt_path.write_text("\n".join(lines), encoding="utf-8")

        return {"json": str(json_path), "txt": str(txt_path)}
