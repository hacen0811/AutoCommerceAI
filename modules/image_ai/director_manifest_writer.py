from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List


class DirectorManifestWriter:
    """
    Sprint93-6B Director Manifest Writer

    역할:
    - Sprint93-6A GeminiDirector 결과를 입력받음
    - director_manifest.json 저장
    - 장면별 scene_XX_prompt.txt 저장
    - 장면별 scene_XX_negative_prompt.txt 저장
    - 저장 성공 여부와 파일 목록 반환
    """

    VERSION = "director-manifest-writer-93-6b"

    MANIFEST_FILENAME = "director_manifest.json"

    def write(
        self,
        director_result: Any = None,
        output_dir: Any = "",
        project_id: Any = "",
        save_negative_prompts: bool = True,
    ) -> Dict[str, Any]:
        started_at = time.time()

        result: Dict[str, Any] = {
            "ok": False,
            "ready": False,
            "version": self.VERSION,
            "status": "not_run",
            "project_id": str(project_id or ""),
            "output_dir": "",
            "manifest_path": "",
            "prompt_files": [],
            "negative_prompt_files": [],
            "scene_count": 0,
            "written_scene_count": 0,
            "warnings": [],
            "errors": [],
            "elapsed_seconds": 0.0,
        }

        if not isinstance(director_result, dict):
            result["status"] = "invalid_director_result"
            result["errors"].append("director_result가 dict 형식이 아닙니다")
            result["elapsed_seconds"] = round(time.time() - started_at, 3)
            return result

        scenes = director_result.get("scenes") or []
        scenes = scenes if isinstance(scenes, list) else []
        result["scene_count"] = len(scenes)

        resolved_output_dir = self._resolve_output_dir(
            output_dir=output_dir,
            director_result=director_result,
            project_id=project_id,
        )
        resolved_output_dir.mkdir(parents=True, exist_ok=True)
        result["output_dir"] = str(resolved_output_dir)

        if not scenes:
            result["status"] = "no_director_scenes"
            result["warnings"].append("저장할 Director 장면이 없습니다")
            result["elapsed_seconds"] = round(time.time() - started_at, 3)
            self._write_manifest(
                director_result=director_result,
                output_dir=resolved_output_dir,
                writer_result=result,
            )
            return result

        prompt_files: List[str] = []
        negative_prompt_files: List[str] = []
        written_scene_count = 0
        manifest_scenes: List[Dict[str, Any]] = []

        for index, scene in enumerate(scenes, start=1):
            if not isinstance(scene, dict):
                continue

            scene_copy = dict(scene)
            scene_id = str(scene.get("scene_id") or f"scene_{index:02d}").strip()
            prompt = str(scene.get("prompt") or "").strip()
            negative_prompt = str(scene.get("negative_prompt") or "").strip()

            prompt_filename = str(
                scene.get("prompt_filename") or f"{scene_id}_prompt.txt"
            ).strip()
            prompt_path = resolved_output_dir / prompt_filename

            scene_copy["prompt_path"] = ""
            scene_copy["negative_prompt_path"] = ""

            if prompt:
                prompt_path.write_text(prompt, encoding="utf-8")
                scene_copy["prompt_path"] = str(prompt_path)
                prompt_files.append(str(prompt_path))
                written_scene_count += 1
            else:
                result["warnings"].append(
                    f"{scene_id}: prompt가 비어 있어 저장하지 않았습니다"
                )

            if save_negative_prompts and negative_prompt:
                negative_filename = f"{scene_id}_negative_prompt.txt"
                negative_path = resolved_output_dir / negative_filename
                negative_path.write_text(
                    negative_prompt,
                    encoding="utf-8",
                )
                scene_copy["negative_prompt_path"] = str(negative_path)
                negative_prompt_files.append(str(negative_path))

            manifest_scenes.append(scene_copy)

        manifest_data = dict(director_result)
        manifest_data["writer_version"] = self.VERSION
        manifest_data["output_dir"] = str(resolved_output_dir)
        manifest_data["scenes"] = manifest_scenes
        manifest_data["prompt_files"] = prompt_files
        manifest_data["negative_prompt_files"] = negative_prompt_files
        manifest_data["written_scene_count"] = written_scene_count

        manifest_path = resolved_output_dir / self.MANIFEST_FILENAME
        manifest_data["manifest_path"] = str(manifest_path)

        manifest_path.write_text(
            json.dumps(
                manifest_data,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        result["manifest_path"] = str(manifest_path)
        result["prompt_files"] = prompt_files
        result["negative_prompt_files"] = negative_prompt_files
        result["written_scene_count"] = written_scene_count
        result["ok"] = bool(manifest_path.is_file())
        result["ready"] = (
            written_scene_count == len(scenes)
            and bool(scenes)
            and manifest_path.is_file()
        )
        result["status"] = (
            "written"
            if result["ready"]
            else "partial"
            if written_scene_count > 0
            else "failed"
        )
        result["elapsed_seconds"] = round(time.time() - started_at, 3)

        return result

    def _resolve_output_dir(
        self,
        output_dir: Any,
        director_result: Dict[str, Any],
        project_id: Any,
    ) -> Path:
        if str(output_dir or "").strip():
            return Path(str(output_dir)).expanduser()

        existing_output = str(
            director_result.get("output_dir") or ""
        ).strip()
        if existing_output:
            return Path(existing_output).expanduser()

        selection_path = str(
            director_result.get("scene_selection_path") or ""
        ).strip()
        if selection_path:
            return Path(selection_path).expanduser().parent

        project_key = (
            str(
                project_id
                or director_result.get("project_id")
                or "unknown"
            ).strip()
            or "unknown"
        )

        return (
            Path("assets")
            / "product_images"
            / f"project_{project_key}"
            / "director"
        )

    def _write_manifest(
        self,
        director_result: Dict[str, Any],
        output_dir: Path,
        writer_result: Dict[str, Any],
    ) -> None:
        manifest_path = output_dir / self.MANIFEST_FILENAME

        manifest_data = dict(director_result)
        manifest_data["writer_version"] = self.VERSION
        manifest_data["output_dir"] = str(output_dir)
        manifest_data["manifest_path"] = str(manifest_path)
        manifest_data["writer_result"] = writer_result

        manifest_path.write_text(
            json.dumps(
                manifest_data,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        writer_result["manifest_path"] = str(manifest_path)