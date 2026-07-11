import json
from pathlib import Path


class CapCutProjectExporter:
    """
    CapCut 자동 프로젝트 생성 준비 단계.
    실제 CapCut 내부 프로젝트 포맷은 환경마다 다를 수 있으므로
    우선 편집 지시서를 JSON/TXT로 내보냅니다.
    """

    def export_plan(self, project, plan):
        out_dir = Path("exports/capcut_plans")
        out_dir.mkdir(parents=True, exist_ok=True)

        safe_name = "".join(c for c in project.product_name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        if not safe_name:
            safe_name = f"project_{project.id}"

        json_path = out_dir / f"{safe_name}_capcut_plan.json"
        txt_path = out_dir / f"{safe_name}_capcut_plan.txt"

        json_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

        lines = [
            f"# {project.product_name} CapCut 편집 지시서",
            "",
            "## 기본 설정",
        ]

        for k, v in plan.get("capcut_preset", {}).items():
            lines.append(f"- {k}: {v}")

        lines += ["", "## 타임라인"]
        for cut in plan.get("timeline", []):
            lines.append(f"- {cut.get('time')} / {cut.get('role') or cut.get('scene')}: {cut.get('caption')} / {cut.get('capcut')}")

        lines += ["", "## 체크리스트"]
        for item in plan.get("export_checklist", []):
            lines.append(f"- [ ] {item}")

        txt_path.write_text("\n".join(lines), encoding="utf-8")

        return {"json": str(json_path), "txt": str(txt_path)}
