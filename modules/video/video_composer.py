from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


class VideoComposer:
    """
    Sprint 55
    AI Video Composer 2.0

    역할:
    - content_pack의 cut_plan을 읽음
    - selected_sources에서 실제 제품 영상만 선택
    - 테스트 영상과 자동 생성 영상을 완전히 제외
    - 장면별 영상 경로와 편집 정보를 정리
    - FFmpeg가 실행할 편집 작업 목록 생성

    제외 대상 예시:
    - default_final.mp4
    - default_merged.mp4
    - test_shorts.mp4
    - project_9_test_shorts.mp4
    - sample.mp4
    - demo.mp4
    """

    COMPOSER_VERSION = "sprint55-video-composer-2.0"

    BLOCKED_VIDEO_KEYWORDS = (
        "default_final",
        "default_merged",
        "test_shorts",
        "test_video",
        "test_final",
        "test_merged",
        "subtitle_test",
        "render_test",
        "sample",
        "demo",
        "example",
        "placeholder",
        "dummy",
    )

    VIDEO_EXTENSIONS = (
        ".mp4",
        ".mov",
        ".m4v",
        ".webm",
        ".avi",
        ".mkv",
    )

    def compose(
        self,
        content_pack: Dict[str, Any],
        project: Any = None,
    ) -> Dict[str, Any]:
        """
        content_pack을 기반으로 실제 제품 영상 편집 작업 계획을 생성합니다.
        """

        content_pack = content_pack or {}

        cut_plan = content_pack.get("cut_plan") or []
        selected_sources = (
            content_pack.get("selected_sources")
            or content_pack.get("sources")
            or []
        )

        project_video_paths = self._project_video_paths(
            project=project,
            content_pack=content_pack,
        )

        jobs = self.build_jobs(
            cut_plan=cut_plan,
            selected_sources=selected_sources,
            project_video_paths=project_video_paths,
        )

        valid_jobs = [
            job
            for job in jobs
            if (
                job.get("video_path")
                and job.get("video_exists")
                and not job.get("is_test_video")
            )
        ]

        invalid_jobs = [
            job
            for job in jobs
            if job not in valid_jobs
        ]

        project_id = self._project_id(project)

        used_video_paths = self._unique_paths(
            [
                job.get("video_path", "")
                for job in valid_jobs
            ]
        )

        return {
            "ok": bool(valid_jobs),
            "composer_version": self.COMPOSER_VERSION,
            "project_id": project_id,
            "format": {
                "width": 1080,
                "height": 1920,
                "aspect_ratio": "9:16",
                "fps": 30,
                "video_codec": "h264",
                "audio_codec": "aac",
            },
            "scene_count": len(jobs),
            "valid_scene_count": len(valid_jobs),
            "invalid_scene_count": len(invalid_jobs),
            "source_video_count": len(used_video_paths),
            "source_video_paths": used_video_paths,
            "jobs": jobs,
            "valid_jobs": valid_jobs,
            "invalid_jobs": invalid_jobs,
            "output_path": self._output_path(project_id),
            "render_status": (
                "ready"
                if valid_jobs
                else "missing_product_video"
            ),
            "message": self._result_message(
                jobs=jobs,
                valid_jobs=valid_jobs,
            ),
        }

    def build_jobs(
        self,
        cut_plan: List[Dict[str, Any]],
        selected_sources: List[Dict[str, Any]],
        project_video_paths: List[str] | None = None,
    ) -> List[Dict[str, Any]]:
        """
        CutPlanner 결과를 FFmpeg 작업 단위로 변환합니다.

        영상 선택 우선순위:
        1. cut_plan에 직접 연결된 실제 제품 영상
        2. selected_sources에 연결된 실제 제품 영상
        3. project.video_path 등 프로젝트에 연결된 실제 제품 영상

        테스트 영상은 모든 단계에서 제외합니다.
        """

        cut_plan = cut_plan or []
        selected_sources = selected_sources or []
        project_video_paths = project_video_paths or []

        valid_sources = self._valid_sources(selected_sources)
        valid_project_paths = self._valid_video_paths(
            project_video_paths
        )

        jobs: List[Dict[str, Any]] = []

        for index, cut in enumerate(cut_plan, start=1):
            cut = cut or {}

            source = self._pick_source(
                cut=cut,
                selected_sources=valid_sources,
                scene=index,
            )

            video_path = self._video_path(
                cut=cut,
                source=source,
            )

            video_origin = ""

            if video_path:
                video_origin = self._video_origin(
                    cut=cut,
                    source=source,
                    video_path=video_path,
                )

            if not video_path and valid_project_paths:
                video_path = valid_project_paths[
                    (index - 1) % len(valid_project_paths)
                ]
                video_origin = "project_video_path"

            video_exists = self._video_exists(video_path)
            is_test_video = self._is_test_video(video_path)

            start = self._time_value(
                cut.get("start"),
                default=0.0,
            )

            end = self._time_value(
                cut.get("end"),
                default=start + 3.0,
            )

            if end <= start:
                end = start + 3.0

            duration = max(end - start, 0.1)

            speed_value = self._speed_value(
                cut.get("speed_value")
                or cut.get("speed")
                or 1.0
            )

            bgm_volume_value = self._volume_value(
                cut.get("bgm_volume_value")
                or cut.get("bgm_volume")
                or 0.15
            )

            missing_reason = self._missing_reason(
                video_path=video_path,
                video_exists=video_exists,
                is_test_video=is_test_video,
            )

            job = {
                "scene": (
                    cut.get("scene")
                    or index
                ),
                "purpose": (
                    cut.get("purpose")
                    or f"Scene {index}"
                ),

                # 원본 영상
                "candidate": (
                    cut.get("candidate")
                    or source.get("platform")
                    or source.get("source")
                    or source.get("candidate")
                    or "현재 연결 영상"
                ),
                "candidate_rank": (
                    cut.get("candidate_rank")
                    or source.get("rank")
                    or source.get("candidate_rank")
                    or index
                ),
                "query": (
                    cut.get("query")
                    or source.get("query")
                    or source.get("keyword")
                    or source.get("search_query")
                    or ""
                ),
                "url": (
                    cut.get("url")
                    or source.get("url")
                    or source.get("video_url")
                    or source.get("play_url")
                    or source.get("search_url")
                    or ""
                ),
                "video_path": video_path,
                "video_origin": video_origin,
                "video_exists": video_exists,
                "is_test_video": is_test_video,

                # 컷 구간
                "start": start,
                "end": end,
                "duration": duration,

                # 편집 추천
                "transition": (
                    cut.get("transition")
                    or "Cut"
                ),
                "speed": (
                    cut.get("speed")
                    or f"{speed_value}x"
                ),
                "speed_value": speed_value,
                "camera": (
                    cut.get("camera")
                    or "Static"
                ),
                "zoom": (
                    cut.get("zoom")
                    or "100%"
                ),

                # 자막
                "subtitle": (
                    cut.get("subtitle")
                    or cut.get("caption")
                    or cut.get("text")
                    or ""
                ),
                "subtitle_position": (
                    cut.get("subtitle_position")
                    or "하단40%"
                ),
                "subtitle_animation": (
                    cut.get("subtitle_animation")
                    or "Fade"
                ),

                # 오디오
                "bgm": (
                    cut.get("bgm")
                    or ""
                ),
                "bgm_volume": (
                    cut.get("bgm_volume")
                    or "15%"
                ),
                "bgm_volume_value": bgm_volume_value,
                "sound_effect": (
                    cut.get("sound_effect")
                    or cut.get("sfx")
                    or cut.get("effect")
                    or ""
                ),

                # AI 정보
                "confidence": (
                    cut.get("confidence")
                    or 0
                ),
                "hook_level": (
                    cut.get("hook_level")
                    or "Low"
                ),
                "reason": (
                    cut.get("reason")
                    or ""
                ),
                "edit_note": (
                    cut.get("edit_note")
                    or ""
                ),

                # 실행 상태
                "status": (
                    "ready"
                    if (
                        video_path
                        and video_exists
                        and not is_test_video
                    )
                    else "missing_product_video"
                ),
                "missing_reason": missing_reason,
            }

            jobs.append(job)

        return jobs

    def _pick_source(
        self,
        cut: Dict[str, Any],
        selected_sources: List[Dict[str, Any]],
        scene: int,
    ) -> Dict[str, Any]:
        """
        cut_plan에 실제 영상이 없을 경우 selected_sources에서 보완합니다.
        """

        cut_video_path = self._first_path(
            cut.get("video_path"),
            cut.get("local_path"),
            cut.get("download_path"),
            cut.get("file_path"),
            cut.get("media_path"),
            cut.get("path"),
        )

        if self._is_valid_product_video(cut_video_path):
            return cut

        if not selected_sources:
            return {}

        candidate_rank = (
            cut.get("candidate_rank")
            or cut.get("rank")
        )

        if candidate_rank not in (None, ""):
            for source in selected_sources:
                source_rank = (
                    source.get("rank")
                    or source.get("candidate_rank")
                )

                if str(source_rank) == str(candidate_rank):
                    return source

        candidate_name = str(
            cut.get("candidate")
            or ""
        ).strip().lower()

        if candidate_name:
            for source in selected_sources:
                source_name = str(
                    source.get("platform")
                    or source.get("source")
                    or source.get("candidate")
                    or ""
                ).strip().lower()

                if source_name == candidate_name:
                    return source

        return selected_sources[
            (scene - 1) % len(selected_sources)
        ]

    def _video_path(
        self,
        cut: Dict[str, Any],
        source: Dict[str, Any],
    ) -> str:
        """
        장면에서 사용할 실제 로컬 제품 영상 경로를 찾습니다.

        존재하지 않는 경로와 테스트 영상은 빈 문자열로 반환합니다.
        """

        path_candidates = [
            cut.get("video_path"),
            cut.get("local_path"),
            cut.get("download_path"),
            cut.get("file_path"),
            cut.get("media_path"),
            cut.get("path"),
            source.get("video_path"),
            source.get("local_path"),
            source.get("download_path"),
            source.get("file_path"),
            source.get("media_path"),
            source.get("path"),
        ]

        for value in path_candidates:
            path = self._normalize_path(value)

            if self._is_valid_product_video(path):
                return path

        return ""

    def _valid_sources(
        self,
        selected_sources: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        실제 제품 영상 경로가 연결된 source만 반환합니다.
        """

        valid_sources: List[Dict[str, Any]] = []

        for source in selected_sources:
            if not isinstance(source, dict):
                continue

            path = self._first_path(
                source.get("video_path"),
                source.get("local_path"),
                source.get("download_path"),
                source.get("file_path"),
                source.get("media_path"),
                source.get("path"),
            )

            if self._is_valid_product_video(path):
                valid_sources.append(source)

        return valid_sources

    def _project_video_paths(
        self,
        project: Any,
        content_pack: Dict[str, Any],
    ) -> List[str]:
        """
        프로젝트 및 content_pack에서 실제 제품 영상 경로를 수집합니다.
        """

        candidates: List[Any] = []

        if project is not None:
            for attr_name in (
                "video_path",
                "source_video_path",
                "downloaded_video_path",
                "local_video_path",
                "media_path",
            ):
                candidates.append(
                    getattr(project, attr_name, None)
                )

            project_video_paths = getattr(
                project,
                "video_paths",
                None,
            )

            if isinstance(project_video_paths, (list, tuple)):
                candidates.extend(project_video_paths)

        for key in (
            "video_path",
            "source_video_path",
            "downloaded_video_path",
            "local_video_path",
            "media_path",
        ):
            candidates.append(content_pack.get(key))

        content_pack_video_paths = content_pack.get(
            "video_paths"
        )

        if isinstance(
            content_pack_video_paths,
            (list, tuple),
        ):
            candidates.extend(content_pack_video_paths)

        product = content_pack.get("product") or {}

        if isinstance(product, dict):
            for key in (
                "video_path",
                "source_video_path",
                "downloaded_video_path",
                "local_video_path",
                "media_path",
            ):
                candidates.append(product.get(key))

        project_data = content_pack.get("project") or {}

        if isinstance(project_data, dict):
            for key in (
                "video_path",
                "source_video_path",
                "downloaded_video_path",
                "local_video_path",
                "media_path",
            ):
                candidates.append(project_data.get(key))

        return self._valid_video_paths(candidates)

    def _valid_video_paths(
        self,
        values: List[Any],
    ) -> List[str]:
        paths: List[str] = []

        for value in values:
            if isinstance(value, (list, tuple)):
                nested_paths = self._valid_video_paths(
                    list(value)
                )

                for nested_path in nested_paths:
                    if nested_path not in paths:
                        paths.append(nested_path)

                continue

            path = self._normalize_path(value)

            if (
                self._is_valid_product_video(path)
                and path not in paths
            ):
                paths.append(path)

        return paths

    def _is_valid_product_video(
        self,
        video_path: Any,
    ) -> bool:
        path = self._normalize_path(video_path)

        if not path:
            return False

        if self._is_test_video(path):
            return False

        if not self._is_video_file(path):
            return False

        return self._video_exists(path)

    def _is_test_video(
        self,
        video_path: Any,
    ) -> bool:
        """
        자동 테스트 또는 샘플 영상인지 검사합니다.
        """

        path = self._normalize_path(video_path)

        if not path:
            return False

        path_text = path.lower().replace("\\", "/")
        filename = Path(path).name.lower()

        for keyword in self.BLOCKED_VIDEO_KEYWORDS:
            if (
                keyword in filename
                or f"/{keyword}/" in path_text
            ):
                return True

        return False

    def _is_video_file(
        self,
        video_path: Any,
    ) -> bool:
        path = self._normalize_path(video_path)

        if not path:
            return False

        return Path(path).suffix.lower() in self.VIDEO_EXTENSIONS

    def _video_exists(
        self,
        video_path: Any,
    ) -> bool:
        path = self._normalize_path(video_path)

        if not path:
            return False

        try:
            return Path(path).is_file()
        except (OSError, TypeError, ValueError):
            return False

    def _normalize_path(
        self,
        value: Any,
    ) -> str:
        if value in (None, ""):
            return ""

        try:
            text = str(value).strip().strip('"').strip("'")

            if not text:
                return ""

            return str(Path(text))
        except (OSError, TypeError, ValueError):
            return ""

    def _first_path(
        self,
        *values: Any,
    ) -> str:
        for value in values:
            path = self._normalize_path(value)

            if path:
                return path

        return ""

    def _video_origin(
        self,
        cut: Dict[str, Any],
        source: Dict[str, Any],
        video_path: str,
    ) -> str:
        cut_paths = self._valid_video_paths(
            [
                cut.get("video_path"),
                cut.get("local_path"),
                cut.get("download_path"),
                cut.get("file_path"),
                cut.get("media_path"),
                cut.get("path"),
            ]
        )

        if video_path in cut_paths:
            return "cut_plan"

        source_paths = self._valid_video_paths(
            [
                source.get("video_path"),
                source.get("local_path"),
                source.get("download_path"),
                source.get("file_path"),
                source.get("media_path"),
                source.get("path"),
            ]
        )

        if video_path in source_paths:
            return "selected_sources"

        return "unknown"

    def _missing_reason(
        self,
        video_path: str,
        video_exists: bool,
        is_test_video: bool,
    ) -> str:
        if not video_path:
            return "실제 제품 영상 경로가 연결되지 않았습니다."

        if is_test_video:
            return "자동 테스트 영상은 렌더링 대상에서 제외되었습니다."

        if not self._is_video_file(video_path):
            return "지원하지 않는 영상 파일 형식입니다."

        if not video_exists:
            return "연결된 영상 파일이 실제 경로에 존재하지 않습니다."

        return ""

    def _unique_paths(
        self,
        paths: List[str],
    ) -> List[str]:
        result: List[str] = []

        for path in paths:
            normalized = self._normalize_path(path)

            if normalized and normalized not in result:
                result.append(normalized)

        return result

    def _time_value(
        self,
        value: Any,
        default: float,
    ) -> float:
        """
        00.0, 01.5, 00:03.5 형식의 값을 초 단위로 변환합니다.
        """

        if isinstance(value, (int, float)):
            return max(float(value), 0.0)

        text = str(value or "").strip()

        if not text:
            return default

        try:
            if ":" not in text:
                return max(float(text), 0.0)

            parts = text.split(":")

            if len(parts) == 2:
                minutes = float(parts[0])
                seconds = float(parts[1])

                return max(
                    (minutes * 60) + seconds,
                    0.0,
                )

            if len(parts) == 3:
                hours = float(parts[0])
                minutes = float(parts[1])
                seconds = float(parts[2])

                return max(
                    (hours * 3600)
                    + (minutes * 60)
                    + seconds,
                    0.0,
                )

        except (TypeError, ValueError):
            return default

        return default

    def _speed_value(
        self,
        value: Any,
    ) -> float:
        if isinstance(value, (int, float)):
            return max(float(value), 0.1)

        text = (
            str(value or "1.0")
            .lower()
            .replace("x", "")
            .strip()
        )

        try:
            return max(float(text), 0.1)
        except (TypeError, ValueError):
            return 1.0

    def _volume_value(
        self,
        value: Any,
    ) -> float:
        if isinstance(value, (int, float)):
            number = float(value)

            if number > 1:
                return max(
                    min(number / 100.0, 1.0),
                    0.0,
                )

            return max(
                min(number, 1.0),
                0.0,
            )

        text = (
            str(value or "")
            .replace("%", "")
            .strip()
        )

        try:
            return max(
                min(float(text) / 100.0, 1.0),
                0.0,
            )
        except (TypeError, ValueError):
            return 0.15

    def _project_id(
        self,
        project: Any,
    ) -> str:
        if project is None:
            return "default"

        project_id = getattr(project, "id", None)

        if project_id in (None, ""):
            project_id = getattr(
                project,
                "name",
                "default",
            )

        return (
            str(project_id)
            .replace(" ", "_")
            .replace("/", "_")
            .replace("\\", "_")
        )

    def _output_path(
        self,
        project_id: str,
    ) -> str:
        output_dir = Path("exports") / "videos"
        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        return str(
            output_dir
            / f"{project_id}_shorts.mp4"
        )

    def _result_message(
        self,
        jobs: List[Dict[str, Any]],
        valid_jobs: List[Dict[str, Any]],
    ) -> str:
        if not jobs:
            return "편집할 장면이 없습니다."

        if not valid_jobs:
            return (
                "실제 제품 영상이 연결되지 않아 렌더링을 시작하지 않습니다. "
                "default_final, test_shorts 등의 자동 테스트 영상은 제외되었습니다."
            )

        if len(valid_jobs) < len(jobs):
            return (
                f"총 {len(jobs)}개 장면 중 "
                f"{len(valid_jobs)}개 장면에 실제 제품 영상이 연결되었습니다. "
                "영상이 없는 장면은 렌더링 대상에서 제외됩니다."
            )

        return (
            f"총 {len(jobs)}개 장면 모두 실제 제품 영상으로 "
            "편집 준비가 완료되었습니다."
        )