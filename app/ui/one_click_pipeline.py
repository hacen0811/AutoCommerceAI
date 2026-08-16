import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import traceback
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from urllib.parse import quote_plus


def _configure_utf8_runtime():
    """Windows CP949 환경에서 파이프라인 로그와 자식 프로세스를 UTF-8로 고정합니다."""
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if not callable(reconfigure):
            continue
        try:
            reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:
            pass


_configure_utf8_runtime()

import streamlit as st

from app.utils.project_keys import safe_project_id
from app.utils.selected_sources import init_selected_sources

from modules.project.project_selector import ProjectSelector
from modules.project.repository import ProjectRepository
from modules.project.service import ProjectService
from modules.workflow.workflow_engine import WorkflowEngine
from modules.audio.typecast_settings_store import TypecastSettingsStore
from modules.workflow.job_queue import JobQueue
from modules.workflow.pipeline_state import PipelineState

from app.ui.pipeline_result import show_pipeline_result
from app.ui.selected_sources_view import show_selected_sources
from app.ui.content_pack.content_pack_view import (
    show_content_pack_view as show_content_pack_view_new,
)
from app.ui.download_connect import open_with_login_browser

from modules.video.video_path_resolver import VideoPathResolver
from modules.publisher.reservation_queue import ReservationQueue
from modules.publisher.scheduled_metadata_builder import ScheduledMetadataBuilder
from modules.publisher.existing_project_loader import ExistingProjectLoader
from modules.publisher.content_library import ContentLibrary
from modules.publisher.youtube_upload_executor import YouTubeUploadExecutor
from modules.publisher.instagram_upload_executor import InstagramUploadExecutor
from modules.publisher.meta_business_suite_scheduler import MetaBusinessSuiteScheduler
from modules.publisher.tiktok_upload_executor import TikTokUploadExecutor
from modules.publisher.threads_upload_executor import ThreadsUploadExecutor
from modules.publisher.naver_clip_upload_executor import NaverClipUploadExecutor
from modules.utils.product_output_naming import create_product_named_video_copy

try:
    from modules.product.product_engine import ProductEngine
except Exception:
    ProductEngine = None

try:
    from modules.search.search_keyword_engine import SearchKeywordEngine
except Exception:
    SearchKeywordEngine = None


UI_VERSION = "sprint194-77-4-history-youtube-metadata-schedule"
RESULT_DIR = Path("exports/one_click_results")
OPENAI_LOCALIZATION_KEY_PATH = Path("secrets/openai_localization_api_key.txt")


def _sprint194_28_load_openai_localization_key():
    env_key = str(os.getenv("OPENAI_API_KEY", "") or "").strip()
    if env_key:
        return env_key
    try:
        if OPENAI_LOCALIZATION_KEY_PATH.is_file():
            return OPENAI_LOCALIZATION_KEY_PATH.read_text(encoding="utf-8").strip()
    except Exception:
        pass
    return ""


def _sprint194_28_save_openai_localization_key(value):
    key = str(value or "").strip()
    OPENAI_LOCALIZATION_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if key:
        OPENAI_LOCALIZATION_KEY_PATH.write_text(key, encoding="utf-8")
        os.environ["OPENAI_API_KEY"] = key
    elif OPENAI_LOCALIZATION_KEY_PATH.exists():
        OPENAI_LOCALIZATION_KEY_PATH.unlink()
        os.environ.pop("OPENAI_API_KEY", None)
    return bool(key)


def _sprint194_28_extract_openai_text(data):
    """Extract output_text from a raw Responses API JSON payload without SDK dependency."""
    if not isinstance(data, dict):
        return ""
    direct = data.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    chunks = []
    for item in list(data.get("output") or []):
        if not isinstance(item, dict):
            continue
        for part in list(item.get("content") or []):
            if not isinstance(part, dict):
                continue
            text = part.get("text")
            if isinstance(text, str) and text.strip():
                chunks.append(text)
    return "\n".join(chunks).strip()



def _sprint194_32_has_hangul(text):
    return bool(re.search(r"[가-힣]", str(text or "")))


def _sprint194_32_source_hash(payload_items, *, narration_only=False):
    canonical = []
    for idx, row in enumerate(list(payload_items or []), start=1):
        row = row if isinstance(row, dict) else {}
        item = {
            "scene": idx,
            "narration_ko": re.sub(r"\s+", " ", str(row.get("narration_ko") or "").strip()),
        }
        if not narration_only:
            item["subtitle_ko"] = re.sub(r"\s+", " ", str(row.get("subtitle_ko") or "").strip())
        canonical.append(item)
    return hashlib.sha256(json.dumps(canonical, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:24]


def _sprint194_32_project_snapshot_path(project_id):
    pid = str(project_id or "").strip()
    if not pid:
        return None
    return Path("assets/products") / f"project_{pid}" / "history_en_localization.json"


def _sprint194_32_save_project_localization(project_id, payload_items, scenes, provider="reused", model=""):
    path = _sprint194_32_project_snapshot_path(project_id)
    if path is None:
        return ""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": "history-en-localization-194-32",
        "project_id": str(project_id or ""),
        "source_hash": _sprint194_32_source_hash(payload_items),
        "source_narration_hash": _sprint194_32_source_hash(payload_items, narration_only=True),
        "provider": str(provider or ""),
        "model": str(model or ""),
        "scenes": list(scenes or []),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[Sprint194-32 Localization Snapshot] SAVED", {"path": str(path), "scenes": len(list(scenes or [])), "provider": provider}, flush=True)
    return str(path)


def _sprint194_32_validate_reusable_scenes(scenes, expected_count):
    rows = list(scenes or [])
    if len(rows) != int(expected_count or 0):
        return []
    out = []
    for idx, row in enumerate(rows, start=1):
        row = row if isinstance(row, dict) else {}
        narration = str(row.get("narration") or row.get("narration_en") or "").strip()
        subtitle = str(row.get("subtitle") or row.get("subtitle_en") or narration).strip()
        if not narration or _sprint194_32_has_hangul(narration) or _sprint194_32_has_hangul(subtitle):
            return []
        out.append({"scene": idx, "narration": narration, "subtitle": subtitle or narration})
    return out


def _sprint194_32_try_project_reuse(project_id, payload_items):
    expected = len(list(payload_items or []))
    path = _sprint194_32_project_snapshot_path(project_id)
    if path is not None and path.is_file():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            exact = str(payload.get("source_hash") or "") == _sprint194_32_source_hash(payload_items)
            narration_match = str(payload.get("source_narration_hash") or "") == _sprint194_32_source_hash(payload_items, narration_only=True)
            scenes = _sprint194_32_validate_reusable_scenes(payload.get("scenes"), expected)
            if scenes and (exact or narration_match):
                print("[Sprint194-32 Localization Cache] PROJECT_HIT", {"path": str(path), "scenes": len(scenes), "exact": exact, "narration_match": narration_match}, flush=True)
                return scenes
        except Exception as exc:
            print("[Sprint194-32 Localization Cache] PROJECT_INVALID", repr(exc), flush=True)

    # Recovery path for a previously rendered English project (e.g. successful 470 output)
    # that predates the dedicated 194-32 snapshot file.
    pid = str(project_id or "").strip()
    if pid:
        preset_path = Path("assets/products") / f"project_{pid}" / "edit_preset.json"
        if preset_path.is_file():
            try:
                preset = json.loads(preset_path.read_text(encoding="utf-8"))
                if str(preset.get("production_mode") or "") == "history_en":
                    subs = list(preset.get("clip_subtitles") or [])
                    nars = list(preset.get("clip_narrations") or [])
                    rows = [
                        {"scene": i + 1, "subtitle": subs[i] if i < len(subs) else "", "narration": nars[i] if i < len(nars) else ""}
                        for i in range(max(len(subs), len(nars)))
                    ]
                    scenes = _sprint194_32_validate_reusable_scenes(rows, expected)
                    if scenes:
                        _sprint194_32_save_project_localization(pid, payload_items, scenes, provider="english_edit_preset")
                        print("[Sprint194-32 Localization Cache] ENGLISH_PRESET_HIT", {"path": str(preset_path), "scenes": len(scenes)}, flush=True)
                        return scenes
            except Exception as exc:
                print("[Sprint194-32 Localization Cache] ENGLISH_PRESET_INVALID", repr(exc), flush=True)
    return []


def _sprint194_32_normalize_openai_payload(parsed):
    """Sprint194-40: recover scene rows from common and nested OpenAI JSON shapes."""
    def _looks_like_scene(row):
        if not isinstance(row, dict):
            return False
        keys = {str(k).lower() for k in row.keys()}
        return bool(keys & {"narration_en", "subtitle_en", "narration", "subtitle", "english_narration", "english_subtitle"})

    def _scene_order(row, fallback):
        if isinstance(row, dict):
            raw = row.get("scene") or row.get("scene_id") or row.get("index") or row.get("order")
            m = re.search(r"\d+", str(raw or ""))
            if m:
                return int(m.group(0))
        return fallback

    def _walk(value, depth=0):
        if depth > 8:
            return []
        if isinstance(value, str):
            text = value.strip()
            if text[:1] in {"{", "["}:
                try:
                    return _walk(json.loads(text), depth + 1)
                except Exception:
                    return []
            return []
        if isinstance(value, list):
            direct = [x for x in value if _looks_like_scene(x)]
            if direct:
                return direct
            for item in value:
                found = _walk(item, depth + 1)
                if found:
                    return found
            return []
        if not isinstance(value, dict):
            return []

        for key in ("scenes", "items", "translations", "results", "data", "localized_scenes", "output", "response"):
            if key in value:
                found = _walk(value.get(key), depth + 1)
                if found:
                    return found

        keyed = []
        for key, item in value.items():
            if isinstance(item, dict) and _looks_like_scene(item):
                m = re.search(r"\d+", str(key))
                keyed.append((int(m.group(0)) if m else len(keyed) + 1, item))
        if keyed:
            keyed.sort(key=lambda x: x[0])
            return [item for _, item in keyed]

        for item in value.values():
            found = _walk(item, depth + 1)
            if found:
                return found
        return []

    rows = _walk(parsed)
    normalized = []
    for idx, row in enumerate(rows, start=1):
        row = dict(row) if isinstance(row, dict) else {}
        narration = str(row.get("narration_en") or row.get("narration") or row.get("english_narration") or "").strip()
        subtitle = str(row.get("subtitle_en") or row.get("subtitle") or row.get("english_subtitle") or narration).strip()
        normalized.append({"scene": _scene_order(row, idx), "narration_en": narration, "subtitle_en": subtitle})
    normalized.sort(key=lambda x: int(x.get("scene") or 999999))
    return {"scenes": normalized}

def _sprint194_28_localization_prompt(payload_items):
    return (
        "You are localizing a Korean history YouTube Short for a US audience. "
        "Return ONLY valid JSON with key scenes, an array in exactly the same order and count. "
        "Each item must have scene, narration_en, subtitle_en. "
        "Preserve historical facts, names, dates, causal meaning, humor and emotional tone. "
        "Do not add facts. Do not merge or split scenes. Rewrite rather than literally translate: use natural, conversational American English for a fast, friendly history YouTube Short. "
        "This is a 17-scene vertical Short targeting about 50-55 seconds total with Oliver TTS at 1.3x. "
        "Keep narration aggressively concise: normally 5-7 spoken words per scene, usually one short sentence, and aim for about 108-116 English narration words TOTAL across all scenes. "
        "Never expand a Korean sentence into extra explanation. Remove repetition, filler, setup phrases, and documentary/formal translationese while preserving the essential fact and causal meaning of each scene. "
        "Use natural, idiomatic American English suitable for spoken YouTube Shorts. Avoid compressed headline-like phrases that sound unnatural when spoken. "
        "Prefer clear subject-verb sentences over noun stacks or literal Korean-to-English phrasing. For example, prefer 'He loved meat, but still followed the mourning rules.' over unnatural constructions such as 'Meat love met ritual duty.' "
        "For the final scene, keep the CTA very short. "
        "Keep subtitle especially short and punchy: ideally 3-7 words and normally no more than 36 characters total, while preserving the scene meaning. "
        "Do not address the viewer unless the Korean source does. Narration must sound natural for TTS. No markdown.\nINPUT:\n"
        + json.dumps(payload_items, ensure_ascii=False)
    )


def _sprint194_28_validate_localized(parsed, expected_count):
    scenes = list((parsed or {}).get("scenes") or []) if isinstance(parsed, dict) else []
    if len(scenes) != int(expected_count):
        raise RuntimeError(f"영어 현지화 장면 수 불일치: source={expected_count} localized={len(scenes)}")
    out = []
    for idx, row in enumerate(scenes, start=1):
        row = row if isinstance(row, dict) else {}
        narration = str(row.get("narration_en") or "").strip()
        subtitle = str(row.get("subtitle_en") or "").strip()
        if not narration:
            raise RuntimeError(f"영어 현지화 나레이션 누락: scene={idx}")
        if not subtitle:
            subtitle = narration
        out.append({"scene": idx, "narration": narration, "subtitle": subtitle})
    _total_words_194_75h = sum(
        len(re.findall(r"[A-Za-z0-9']+", str(x.get("narration") or "")))
        for x in out
    )
    print("[Sprint194-75H English Short Localization] VALIDATED", {
        "scenes": len(out),
        "narration_words": _total_words_194_75h,
        "target_words": "108-116",
        "target_seconds": "53-55",
        "english_style": "natural-spoken-american-shorts",
    }, flush=True)
    return out


def _sprint194_28_localize_with_openai(payload_items, api_key):
    """OpenAI Responses API primary localizer. One request for all scenes."""
    import urllib.request
    import urllib.error
    key = str(api_key or "").strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY_MISSING")
    prompt = _sprint194_28_localization_prompt(payload_items)
    model = str(os.getenv("OPENAI_LOCALIZATION_MODEL", "gpt-5.6-luna") or "gpt-5.6-luna").strip()
    body = json.dumps({
        "model": model,
        "input": prompt,
        "reasoning": {"effort": "low"},
    }, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        status = int(getattr(exc, "code", 0) or 0)
        try:
            body_text = exc.read().decode("utf-8", errors="replace")[:1600]
        except Exception:
            body_text = ""
        print("[Sprint194-28 OpenAI Localization] HTTP_ERROR", {"status": status, "model": model, "body": body_text}, flush=True)
        raise RuntimeError(f"OpenAI 영어 현지화 실패 HTTP {status}") from exc
    text = _sprint194_28_extract_openai_text(data)
    if not text:
        raise RuntimeError("OpenAI 영어 현지화 응답 텍스트가 비어 있습니다.")
    try:
        parsed = json.loads(text)
    except Exception:
        # Strip markdown fences first, then recover the outermost JSON object/array if prose leaked in.
        cleaned = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", text, flags=re.I | re.S).strip()
        try:
            parsed = json.loads(cleaned)
        except Exception:
            starts = [pos for pos in (cleaned.find("{"), cleaned.find("[")) if pos >= 0]
            if not starts:
                raise
            start = min(starts)
            end_obj = cleaned.rfind("}")
            end_arr = cleaned.rfind("]")
            end = max(end_obj, end_arr)
            if end < start:
                raise
            parsed = json.loads(cleaned[start:end + 1])
    _raw_parsed_type_194_40 = type(parsed).__name__
    _raw_keys_194_40 = list(parsed.keys())[:20] if isinstance(parsed, dict) else []
    parsed = _sprint194_32_normalize_openai_payload(parsed)
    print("[Sprint194-40 OpenAI Localization Recovery]", {
        "raw_type": _raw_parsed_type_194_40,
        "raw_keys": _raw_keys_194_40,
        "source_scenes": len(payload_items),
        "recovered_scenes": len(list(parsed.get("scenes") or [])),
    }, flush=True)
    out = _sprint194_28_validate_localized(parsed, len(payload_items))
    print("[Sprint194-28 OpenAI Localization] READY", {"model": model, "scenes": len(out)}, flush=True)
    return out, model


def _sprint194_28_localize_with_gemini(payload_items):
    """Gemini fallback. Kept as secondary provider only."""
    import urllib.request
    import urllib.error
    import time
    api_key = str(os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")).strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY_MISSING")
    prompt = _sprint194_28_localization_prompt(payload_items)
    body = json.dumps({"contents":[{"parts":[{"text":prompt}]}], "generationConfig":{"temperature":0.25,"responseMimeType":"application/json"}}).encode("utf-8")
    model = str(os.getenv("GEMINI_TEXT_MODEL", "gemini-2.0-flash")).strip() or "gemini-2.0-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    data = None
    max_attempts = 3
    fallback_waits = (5, 15)
    for attempt in range(1, max_attempts + 1):
        req = urllib.request.Request(url, data=body, headers={"Content-Type":"application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            print("[Sprint194-28 Gemini Fallback] READY", {"attempt": attempt, "model": model, "scenes": len(payload_items)}, flush=True)
            break
        except urllib.error.HTTPError as exc:
            status = int(getattr(exc, "code", 0) or 0)
            if status != 429 or attempt >= max_attempts:
                print("[Sprint194-28 Gemini Fallback] HTTP_ERROR", {"status": status, "attempt": attempt, "model": model}, flush=True)
                raise RuntimeError(f"Gemini fallback 실패 HTTP {status}") from exc
            retry_after = 0.0
            try:
                retry_after = float((exc.headers or {}).get("Retry-After") or 0)
            except Exception:
                retry_after = 0.0
            wait_seconds = max(retry_after, float(fallback_waits[attempt - 1]))
            print("[Sprint194-28 Gemini Fallback] RATE_LIMIT", {"attempt": attempt, "wait_seconds": wait_seconds}, flush=True)
            time.sleep(wait_seconds)
    if data is None:
        raise RuntimeError("Gemini fallback 응답을 받지 못했습니다.")
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    parsed = json.loads(text)
    out = _sprint194_28_validate_localized(parsed, len(payload_items))
    return out, model


def _sprint194_21_auto_localize_history_to_english(items, openai_api_key="", project_id=""):
    """Sprint194-32: project-persistent reuse first, then OpenAI -> Gemini only for a genuinely new localization."""
    payload_items = []
    for i, item in enumerate(list(items or []), start=1):
        payload_items.append({
            "scene": i,
            "narration_ko": str((item or {}).get("narration") or "").strip(),
            "subtitle_ko": str((item or {}).get("subtitle") or "").strip(),
        })
    if not payload_items:
        raise RuntimeError("영어 현지화할 장면이 없습니다.")

    # 194-32 priority 1: never call a translation API again when this project already
    # has a valid 1:1 English localization from a previous successful render.
    # Sprint194-75H: do not reuse pre-75H project localization because it may
    # contain the old long-form English narration. The new versioned hash cache below
    # is safe to reuse after the first successful 75H localization.
    reused = None
    print("[Sprint194-75H English Short Localization] PROJECT_OLD_REUSE_SKIPPED", {
        "project_id": str(project_id or ""),
        "profile": "history-en-short-53-55s-v3",
    }, flush=True)

    cache_dir = RESULT_DIR / "history_localization_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    # Sprint194-75H: version the localization cache. Older cached English text
    # was valid linguistically but too verbose for a ~50-55s Short, so do not reuse it.
    _localization_profile_194_75h = "history-en-short-53-55s-v3"
    cache_key = hashlib.sha256(
        json.dumps(
            {"profile": _localization_profile_194_75h, "items": payload_items},
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()[:24]
    cache_path = cache_dir / f"{cache_key}_en.json"
    if cache_path.is_file():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            scenes = list(cached.get("scenes") or [])
            if len(scenes) == len(payload_items):
                print("[Sprint194-32 Localization Cache] HASH_HIT", {"path": str(cache_path), "scenes": len(scenes), "provider": cached.get("provider")}, flush=True)
                _sprint194_32_save_project_localization(project_id, payload_items, scenes, provider=str(cached.get("provider") or "hash_cache"), model=str(cached.get("model") or ""))
                return scenes
        except Exception as exc:
            print("[Sprint194-28 Localization Cache] INVALID", repr(exc), flush=True)

    provider_errors = []
    key = str(openai_api_key or os.getenv("OPENAI_API_KEY", "") or "").strip()
    if key:
        try:
            scenes, model = _sprint194_28_localize_with_openai(payload_items, key)
            cache_path.write_text(json.dumps({"provider":"openai", "model":model, "scenes":scenes}, ensure_ascii=False, indent=2), encoding="utf-8")
            _sprint194_32_save_project_localization(project_id, payload_items, scenes, provider="openai", model=model)
            print("[Sprint194-32 History Auto Localization] READY", {"provider":"openai", "model":model, "scenes":len(scenes), "cached":True}, flush=True)
            return scenes
        except Exception as exc:
            provider_errors.append(f"OpenAI: {exc}")
            print("[Sprint194-28 Localization Fallback] OPENAI_FAILED", repr(exc), flush=True)
    else:
        provider_errors.append("OpenAI: API key missing")
        print("[Sprint194-28 Localization Fallback] OPENAI_SKIPPED", {"reason":"api_key_missing"}, flush=True)

    try:
        scenes, model = _sprint194_28_localize_with_gemini(payload_items)
        cache_path.write_text(json.dumps({"provider":"gemini", "model":model, "scenes":scenes}, ensure_ascii=False, indent=2), encoding="utf-8")
        _sprint194_32_save_project_localization(project_id, payload_items, scenes, provider="gemini", model=model)
        print("[Sprint194-32 History Auto Localization] READY", {"provider":"gemini", "model":model, "scenes":len(scenes), "cached":True}, flush=True)
        return scenes
    except Exception as exc:
        provider_errors.append(f"Gemini: {exc}")
        print("[Sprint194-28 Localization Fallback] GEMINI_FAILED", repr(exc), flush=True)

    raise RuntimeError("영어 자동 현지화 제공자 모두 실패: " + " | ".join(provider_errors))

# Sprint192-1: TikTok / Naver Clip 계정별 Playwright 프로필 분리.
# 기존 실물로그 프로필 경로는 그대로 유지하여 현재 로그인 세션을 보존합니다.
PUBLISH_ACCOUNT_PROFILES = {
    "실물로그": {
        "tiktok": "secrets/tiktok_playwright_profile",
        "threads": "secrets/threads_playwright_profile",
        "naver_clip": "secrets/naver_clip_playwright_profile",
    },
    "하센맘": {
        "tiktok": "secrets/tiktok_playwright_profile_hasenmom",
        "threads": "secrets/threads_playwright_profile_hasenmom",
        "naver_clip": "secrets/naver_clip_playwright_profile_hasenmom",
    },
}

# Sprint194-77: YouTube 채널별 OAuth token 분리.
YOUTUBE_UPLOAD_ACCOUNTS = ["실물로그", "하센맘", "역사쿠키", "History Cookie"]

def _sprint194_77_default_youtube_account(production_mode):
    mode = str(production_mode or "").strip()
    if mode == "history_en":
        return "History Cookie"
    if mode == "history_ko":
        return "역사쿠키"
    return "실물로그"



def _publisher_profile(account_name, platform):
    account = str(account_name or "실물로그").strip()
    platform_key = str(platform or "").strip().lower()
    profiles = PUBLISH_ACCOUNT_PROFILES.get(
        account,
        PUBLISH_ACCOUNT_PROFILES["실물로그"],
    )
    return str(
        profiles.get(platform_key)
        or PUBLISH_ACCOUNT_PROFILES["실물로그"].get(platform_key, "")
    )




def _save_clip_subtitle_sidecar(project, clip_subtitles, subtitle_style=None, clip_narrations=None, clip_subtitle_effects=None, clip_sfx=None, clip_playback_speeds=None):
    """프로젝트별 영상 자막을 별도 JSON으로 저장합니다."""
    project_id = str(safe_project_id(project))
    folder = Path("assets/products") / f"project_{project_id}"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "clip_subtitles.json"
    payload = {
        "version": "clip-subtitles-190-2",
        "project_id": project_id,
        "clip_subtitles": [
            str(item or "").strip() for item in list(clip_subtitles or [])
        ],
        "clip_narrations": [
            str(item or "").strip() for item in list(clip_narrations or [])
        ],
        "clip_subtitle_effects": [
            str(item or "기본").strip() for item in list(clip_subtitle_effects or [])
        ],
        "clip_sfx": [
            str(item or "없음").strip() for item in list(clip_sfx or [])
        ],
        "clip_playback_speeds": [
            float(item if item is not None else 0.0) for item in list(clip_playback_speeds or [])
        ],
        "subtitle_style": dict(subtitle_style or {}),
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        "[Sprint190-2 Clip Subtitle Sidecar] SAVED",
        {
            "path": str(path),
            "count": len(payload["clip_subtitles"]),
            "nonempty": len([x for x in payload["clip_subtitles"] if x]),
            "subtitle_style": payload.get("subtitle_style", {}),
        },
        flush=True,
    )
    return str(path)
REVIEW_IMAGE_ROOT = Path("assets/review_images")
PRODUCT_IMAGE_ROOT = Path("assets/products")
VIRAL_UPLOAD_ROOT = Path("assets/viral_uploads")
SUPPORTED_VIRAL_VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}
SUPPORTED_PRODUCT_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
SUPPORTED_REVIEW_IMAGE_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
}


print("######## ONE_CLICK_PIPELINE SPRINT194-2 HISTORY IMAGE VIDEO LOADED ########", __file__, flush=True)

# Sprint102-3: 한 Streamlit 프로세스에서 동일 프로젝트 중복 실행을 차단합니다.
_PIPELINE_RUN_GUARD = threading.RLock()
_ACTIVE_PIPELINE_PROJECTS = set()


def read_json(path, default=None):
    try:
        p = Path(path)
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )


def _sprint193_29_project_name(project_id):
    try:
        repo = ProjectRepository()
        project = repo.get(project_id)
        if project is None:
            try:
                project = repo.get(int(project_id))
            except Exception:
                project = None
        if project is not None:
            return str(
                getattr(project, "product_name", "")
                or getattr(project, "title", "")
                or ""
            ).strip()
    except Exception:
        pass
    return ""


def _sprint193_29_legacy_payload(project_id, sidecar_path, clip_paths):
    """193-28 이전 프로젝트를 기존 sidecar + Gemini 클립 + DB에서 복구합니다."""
    sidecar = read_json(sidecar_path, {})
    if not isinstance(sidecar, dict):
        sidecar = {}

    product_name = _sprint193_29_project_name(project_id) or f"프로젝트 {project_id}"
    project_folder = Path("assets/products") / f"project_{project_id}"

    # 가능한 기존 메타데이터에서 평점/리뷰/후킹/CTA도 보강합니다.
    meta_candidates = [
        project_folder / "publisher_metadata.json",
        project_folder / "content_pack.json",
        Path("exports/one_click_results") / f"{project_id}_latest_result.json",
    ]
    merged_meta = {}
    for meta_path in meta_candidates:
        data = read_json(meta_path, {})
        if isinstance(data, dict):
            merged_meta.update(data)

    return {
        "version": "edit-preset-193-29-recovered",
        "project_id": str(project_id),
        "product_name": product_name,
        "rating": float(
            merged_meta.get("rating")
            or ((merged_meta.get("trust_inputs") or {}).get("rating") if isinstance(merged_meta.get("trust_inputs"), dict) else 0)
            or 4.8
        ),
        "declared_review_count": int(
            merged_meta.get("declared_review_count")
            or merged_meta.get("review_count")
            or ((merged_meta.get("trust_inputs") or {}).get("declared_review_count") if isinstance(merged_meta.get("trust_inputs"), dict) else 0)
            or 0
        ),
        "monthly_purchase_count": 0,
        "hook_text": str(
            merged_meta.get("hook_text")
            or merged_meta.get("best_hook")
            or ""
        ).strip(),
        "clip_subtitles": list(sidecar.get("clip_subtitles") or []),
        "clip_narrations": list(sidecar.get("clip_narrations") or []),
        "clip_subtitle_effects": list(sidecar.get("clip_subtitle_effects") or []),
        "clip_sfx": list(sidecar.get("clip_sfx") or []),
        "clip_playback_speeds": list(sidecar.get("clip_playback_speeds") or []),
        "gemini_clip_paths": list(clip_paths or []),
        "subtitle_style": dict(sidecar.get("subtitle_style") or {}),
        "cta_product_logo_text": str(
            merged_meta.get("cta_product_logo_text")
            or product_name
            or ""
        ).strip(),
        "playback_speed": float(merged_meta.get("playback_speed") or 1.5),
        "channel_type": str(merged_meta.get("channel_type") or "shopping"),
        "youtube_privacy_status": str(merged_meta.get("youtube_privacy_status") or "unlisted"),
        "voice_name": str(merged_meta.get("voice_name") or "지안"),
        "voice_id": str(merged_meta.get("voice_id") or ""),
        "tts_volume_percent": int(merged_meta.get("tts_volume_percent") or 100),
        "tts_speech_speed": float(merged_meta.get("tts_speech_speed") or 1.0),
        "bgm_volume_percent": int(merged_meta.get("bgm_volume_percent") or 10),
        "voice_audio_path": str(merged_meta.get("voice_audio_path") or ""),
        "bgm_audio_path": str(merged_meta.get("bgm_audio_path") or ""),
        "saved_at": "",
        "recovered_from_legacy": True,
    }


def _sprint193_29_recent_edit_presets(limit=50):
    """신규 프리셋 + 193-28 이전 프로젝트를 모두 최근 작업 목록에 표시합니다."""
    items_by_project = {}
    product_root = Path("assets/products")
    clip_root = Path("assets/gemini_clips")

    # 1) 정상 edit_preset.json 우선
    if product_root.exists():
        for path in product_root.glob("project_*/edit_preset.json"):
            try:
                payload = read_json(path, {})
                if not isinstance(payload, dict) or not payload:
                    continue
                project_id = str(payload.get("project_id") or path.parent.name.replace("project_", ""))
                clip_paths = [
                    str(item or "").strip()
                    for item in list(payload.get("gemini_clip_paths") or [])
                    if str(item or "").strip() and Path(str(item)).is_file()
                ]
                if not clip_paths:
                    clip_folder = clip_root / f"project_{project_id}"
                    if clip_folder.exists():
                        clip_paths = [
                            str(p) for p in sorted(clip_folder.iterdir())
                            if p.is_file() and p.suffix.lower() in SUPPORTED_VIRAL_VIDEO_SUFFIXES
                        ]
                if not clip_paths:
                    continue
                items_by_project[project_id] = {
                    "path": str(path),
                    "project_id": project_id,
                    "product_name": str(payload.get("product_name") or _sprint193_29_project_name(project_id) or "이전 작업").strip(),
                    "saved_at": str(payload.get("saved_at") or ""),
                    "mtime": path.stat().st_mtime,
                    "clip_count": len(clip_paths),
                    "recovered": False,
                }
            except Exception as exc:
                print("[Sprint193-29 Existing Preset Scan] ERROR", str(path), repr(exc), flush=True)

    # 2) edit_preset이 없는 기존 프로젝트 복구
    candidate_ids = set()
    if product_root.exists():
        for folder in product_root.glob("project_*"):
            if folder.is_dir():
                candidate_ids.add(folder.name.replace("project_", ""))
    if clip_root.exists():
        for folder in clip_root.glob("project_*"):
            if folder.is_dir():
                candidate_ids.add(folder.name.replace("project_", ""))

    for project_id in candidate_ids:
        if project_id in items_by_project:
            continue
        try:
            sidecar_path = product_root / f"project_{project_id}" / "clip_subtitles.json"
            clip_folder = clip_root / f"project_{project_id}"
            clip_paths = []
            if clip_folder.exists():
                clip_paths = [
                    str(p) for p in sorted(clip_folder.iterdir())
                    if p.is_file() and p.suffix.lower() in SUPPORTED_VIRAL_VIDEO_SUFFIXES
                ]
            if not clip_paths:
                continue

            # 자막 sidecar가 없더라도 영상 자체는 목록에 살립니다.
            recovered_payload = _sprint193_29_legacy_payload(
                project_id,
                sidecar_path,
                clip_paths,
            )
            product_name = str(recovered_payload.get("product_name") or f"프로젝트 {project_id}")
            mtime_candidates = [p.stat().st_mtime for p in [sidecar_path, clip_folder] if p.exists()]
            mtime = max(mtime_candidates) if mtime_candidates else 0.0
            items_by_project[project_id] = {
                "path": str(sidecar_path),
                "project_id": str(project_id),
                "product_name": product_name,
                "saved_at": "",
                "mtime": mtime,
                "clip_count": len(clip_paths),
                "recovered": True,
                "legacy_payload": recovered_payload,
            }
        except Exception as exc:
            print("[Sprint193-29 Legacy Scan] ERROR", project_id, repr(exc), flush=True)

    items = list(items_by_project.values())
    items.sort(key=lambda item: float(item.get("mtime") or 0.0), reverse=True)
    print(
        "[Sprint193-29 Previous Work Scan]",
        {
            "total": len(items),
            "recovered": len([x for x in items if x.get("recovered")]),
            "preset": len([x for x in items if not x.get("recovered")]),
        },
        flush=True,
    )
    return items[:max(1, int(limit or 50))]



def _sprint193_29_save_edit_preset(project, payload):
    project_id = str(safe_project_id(project))
    target = Path("assets/products") / f"project_{project_id}" / "edit_preset.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    write_json(target, dict(payload or {}))
    print(
        "[Sprint193-29 Edit Preset] SAVED",
        {"path": str(target), "project_id": project_id},
        flush=True,
    )
    return str(target)


def _sprint193_29_apply_preset_to_session(preset):
    """Streamlit 위젯 생성 전에 이전 편집값을 session_state에 복원합니다."""
    preset = dict(preset or {})
    mapping = {
        "sprint172_product_name": preset.get("product_name", ""),
        "sprint178_rating": float(preset.get("rating") or 4.8),
        "sprint178_declared_review_count": int(preset.get("declared_review_count") or 0),
        "sprint193_9_hook_phrase": preset.get("hook_text", ""),
        "sprint193_25_cta_product_logo_text": preset.get("cta_product_logo_text", ""),
        "sprint176_playback_speed": float(preset.get("playback_speed") or 1.5),
        "sprint172_channel_type": preset.get("channel_type", "shopping"),
        "sprint172_privacy": preset.get("youtube_privacy_status", "unlisted"),
        "sprint193_1_tts_volume": int(preset.get("tts_volume_percent") or 100),
        "sprint193_1_tts_speed": float(preset.get("tts_speech_speed") or 1.0),
        "sprint193_1_bgm_volume": int(preset.get("bgm_volume_percent") or 10),
        # Sprint194-25: top-level mode widget is now only shopping/history.
        # Preserve old history_ko/history_en presets by splitting mode and language state.
        "sprint194_25_content_mode": (
            "history" if str(preset.get("production_mode") or preset.get("channel_type") or "").startswith("history_") else "shopping"
        ),
        "sprint194_25_history_language": (
            "en" if str(preset.get("production_mode") or preset.get("channel_type") or "") == "history_en" else "ko"
        ),
    }

    subtitle_style = dict(preset.get("subtitle_style") or {})
    mapping.update({
        "sprint190_9_subtitle_font": subtitle_style.get("font", "Gmarket Sans Bold"),
        "sprint190_9_subtitle_font_size": int(subtitle_style.get("font_size") or 76),
        "sprint190_9_subtitle_outline": int(subtitle_style.get("outline") or 6),
        "sprint190_9_subtitle_text_color": subtitle_style.get("text_color", "#FFFFFF"),
        "sprint190_9_subtitle_background_color": subtitle_style.get("background_color", "#000000"),
        "sprint190_9_subtitle_highlight_color": subtitle_style.get("highlight_color", "#FFD700"),
        "sprint190_9_subtitle_background_opacity": int(subtitle_style.get("background_opacity") if subtitle_style.get("background_opacity") is not None else 10),
    })

    for key, value in mapping.items():
        st.session_state[key] = value

    subtitles = list(preset.get("clip_subtitles") or [])
    narrations = list(preset.get("clip_narrations") or [])
    effects = list(preset.get("clip_subtitle_effects") or [])
    sfx = list(preset.get("clip_sfx") or [])
    speeds = list(preset.get("clip_playback_speeds") or [])

    count = max(
        len(subtitles), len(narrations), len(effects), len(sfx), len(speeds),
        len(list(preset.get("gemini_clip_paths") or [])),
    )
    speed_options = ["자동", 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]
    for idx in range(count):
        n = idx + 1
        st.session_state[f"sprint193_9_clip_subtitle_{n}"] = str(subtitles[idx] if idx < len(subtitles) else "")
        st.session_state[f"sprint193_9_clip_narration_{n}"] = str(narrations[idx] if idx < len(narrations) else "")
        st.session_state[f"sprint193_9_clip_subtitle_effect_{n}"] = str(effects[idx] if idx < len(effects) else "기본")
        st.session_state[f"sprint193_9_clip_sfx_{n}"] = str(sfx[idx] if idx < len(sfx) else "없음")
        raw_speed = float(speeds[idx] or 0.0) if idx < len(speeds) else 0.0
        selected_speed = "자동" if raw_speed <= 0 else min(
            speed_options[1:],
            key=lambda value: abs(float(value) - raw_speed),
        )
        st.session_state[f"sprint193_14_clip_speed_{n}"] = selected_speed

    st.session_state["sprint193_29_loaded_clip_paths"] = [
        str(item or "").strip()
        for item in list(preset.get("gemini_clip_paths") or [])
        if str(item or "").strip() and Path(str(item)).is_file()
    ]
    st.session_state["sprint193_29_loaded_preset_path"] = str(preset.get("_preset_path") or "")
    st.session_state["sprint193_29_loaded_project_id"] = str(preset.get("project_id") or "")


def normalize_text(value, fallback=""):
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def make_search_url(platform, query):
    encoded = quote_plus(query or "")

    if platform == "taobao":
        return f"https://s.taobao.com/search?q={encoded}"

    if platform == "douyin":
        return f"https://www.douyin.com/search/{encoded}"

    if platform == "1688":
        return f"https://s.1688.com/selloffer/offer_search.htm?keywords={encoded}"

    return ""


def safe_file_name(text, fallback="video"):
    text = str(text or fallback).strip()
    text = re.sub(r"[^0-9A-Za-z가-힣._-]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text[:80] or fallback


def _sprint194_4_estimate_scene_seconds(narration, tts_speed=1.2):
    """역사 장면 길이 안전 추정치. 실제 VideoPipeline의 TTS 자동맞춤이 최종 보정합니다."""
    text = re.sub(r"\s+", "", str(narration or ""))
    if not text:
        return 3.0
    speed = max(0.7, float(tts_speed or 1.2))
    # 한국어/영어 혼합 쇼츠 기준 보수적 추정 + 장면 전환 여유 0.35초
    seconds = (len(text) / (4.2 * speed)) + 0.35
    return max(2.2, min(7.0, seconds))


def _sprint194_4_render_history_image_clip(image_path, output_path, seconds=5.0, fps=30, motion_index=1):
    """Sprint194-8: 역사 이미지 임시 클립. zoompan을 쓰지 않아 미세 떨림을 제거합니다.

    최종 장면 길이는 Workflow에서 실제 TTS 길이를 측정한 뒤 다시 렌더링합니다.
    """
    image = Path(str(image_path))
    output = Path(str(output_path))
    output.parent.mkdir(parents=True, exist_ok=True)
    duration = max(2.5, float(seconds or 5.0))
    fps = int(fps or 30)
    mode = (int(motion_index or 1) - 1) % 5
    d = max(duration, 0.001)
    # 고정 확대 후 crop 좌표만 한 방향으로 이동: 왕복/zoompan 없음.
    motions = [
        f"crop=1080:1920:x='(iw-1080)*t/{d:.6f}':y='(ih-1920)/2'",
        f"crop=1080:1920:x='(iw-1080)*(1-t/{d:.6f})':y='(ih-1920)/2'",
        f"crop=1080:1920:x='(iw-1080)/2':y='(ih-1920)*t/{d:.6f}'",
        f"crop=1080:1920:x='(iw-1080)/2':y='(ih-1920)*(1-t/{d:.6f})'",
        "crop=1080:1920:x='(iw-1080)/2':y='(ih-1920)/2'",
    ]
    vf = (
        "scale=1188:2112:force_original_aspect_ratio=increase,"
        + motions[mode]
        + ",fps=30,format=yuv420p"
    )
    command = [
        "ffmpeg", "-y", "-loop", "1", "-i", str(image),
        "-vf", vf, "-t", f"{duration:.3f}",
        "-an", "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    ok = completed.returncode == 0 and output.is_file() and output.stat().st_size > 1024
    print("[Sprint194-8 History Placeholder Motion]", {"ok": ok, "scene": motion_index, "seconds": round(duration, 3), "motion": mode + 1}, flush=True)
    if not ok:
        raise RuntimeError("history_image_clip_failed: " + str((completed.stderr or completed.stdout or "")[-1200:]))
    return str(output)


def _sprint194_5_scene_sort_key(item):
    name = str(getattr(item, "name", item) or "")
    parts = re.split(r"(\d+)", Path(name).stem.lower())
    return [int(part) if part.isdigit() else part for part in parts]


def _sprint194_5_merge_history_uploads(primary, extra=None):
    """기본/추가 업로드를 파일명 기준으로 합치고 1,2,...10 순으로 정렬합니다."""
    merged = {}
    for item in list(primary or []) + list(extra or []):
        name = str(getattr(item, "name", "") or "").strip()
        if not name:
            continue
        merged[name.lower()] = item
    return sorted(merged.values(), key=_sprint194_5_scene_sort_key)[:25]


def _sprint194_4_save_history_scene_images(project, uploaded_images, clip_narrations=None, tts_speed=1.2, first_scene_video=None):
    """History scenes: scene 1 may be supplied by video while images start at 2.png."""
    project_id = str(safe_project_id(project))
    image_folder = Path("assets/history_scene_images") / f"project_{project_id}"
    clip_folder = Path("assets/gemini_clips") / f"project_{project_id}"
    image_folder.mkdir(parents=True, exist_ok=True)
    clip_folder.mkdir(parents=True, exist_ok=True)
    images = sorted(list(uploaded_images or []), key=_sprint194_5_scene_sort_key)[:25]
    narrations = list(clip_narrations or [])

    def _scene_no(item, fallback):
        name = str(getattr(item, "name", "") or "")
        match = re.search(r"(\d+)", Path(name).stem)
        return int(match.group(1)) if match else int(fallback)

    image_scene_numbers = [_scene_no(item, i) for i, item in enumerate(images, start=1)]
    scene1_missing_from_images = 1 not in set(image_scene_numbers)
    clip_map = {}

    def _render_scene1_video():
        video_name = str(getattr(first_scene_video, "name", "scene_01.mp4") or "scene_01.mp4")
        video_suffix = Path(video_name).suffix.lower()
        if video_suffix not in SUPPORTED_VIRAL_VIDEO_SUFFIXES:
            video_suffix = ".mp4"
        original_video = clip_folder / f"history_01_source{video_suffix}"
        first_scene_video.seek(0)
        original_video.write_bytes(first_scene_video.getbuffer())
        clip_target = clip_folder / "history_01.mp4"
        command = [
            "ffmpeg", "-y", "-i", str(original_video), "-map", "0:v:0", "-an",
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,fps=30,format=yuv420p",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(clip_target),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
        ok = completed.returncode == 0 and clip_target.is_file() and clip_target.stat().st_size > 1024
        print("[Sprint194-47A History Scene1 Video]", {"ok": ok, "source": str(original_video), "output": str(clip_target)}, flush=True)
        if not ok:
            raise RuntimeError("history_scene1_video_failed: " + str((completed.stderr or completed.stdout or "")[-1200:]))
        return str(clip_target)

    if first_scene_video is not None and scene1_missing_from_images:
        clip_map[1] = _render_scene1_video()

    for fallback_index, uploaded in enumerate(images, start=1):
        scene_no = _scene_no(uploaded, fallback_index + (1 if scene1_missing_from_images and first_scene_video is not None else 0))
        original_name = str(getattr(uploaded, "name", f"scene_{scene_no:02d}.png") or "")
        suffix = Path(original_name).suffix.lower()
        if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
            suffix = ".png"
        image_target = image_folder / f"scene_{scene_no:02d}{suffix}"
        uploaded.seek(0)
        image_target.write_bytes(uploaded.getbuffer())
        clip_target = clip_folder / f"history_{scene_no:02d}.mp4"
        narration = narrations[scene_no - 1] if scene_no - 1 < len(narrations) else ""
        seconds = _sprint194_4_estimate_scene_seconds(narration, tts_speed)
        if scene_no == 1 and first_scene_video is not None:
            clip_map[1] = _render_scene1_video()
        else:
            clip_map[scene_no] = _sprint194_4_render_history_image_clip(image_target, clip_target, seconds, 30, scene_no)

    clip_paths = [clip_map[key] for key in sorted(clip_map)]
    expected_count = len(images) + (1 if first_scene_video is not None and scene1_missing_from_images else 0)
    if len(clip_paths) != expected_count:
        raise RuntimeError(f"history_scene_count_mismatch: expected={expected_count} clips={len(clip_paths)}")
    print("[Sprint194-47A History Scene Images] READY", {"images": len(images), "scene1_video": bool(first_scene_video is not None), "clips": len(clip_paths), "narrations": len(narrations)}, flush=True)
    return clip_paths


def pipeline_result_path(project):
    return RESULT_DIR / f"{safe_project_id(project)}_latest_result.json"


def save_pipeline_result(project, result):
    if isinstance(result, dict) and result:
        write_json(pipeline_result_path(project), result)


def load_pipeline_result(project):
    data = read_json(pipeline_result_path(project), {})
    return data if isinstance(data, dict) else {}


def review_image_dir(project):
    return REVIEW_IMAGE_ROOT / f"project_{safe_project_id(project)}"


def list_saved_review_images(project):
    folder = review_image_dir(project)

    if not folder.exists():
        return []

    return [
        str(path)
        for path in sorted(folder.iterdir())
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_REVIEW_IMAGE_SUFFIXES
    ]


def save_uploaded_review_images(project, uploaded_files):
    """
    업로드된 리뷰 이미지를 프로젝트별 폴더에 저장합니다.

    같은 프로젝트에서 새 이미지를 업로드하면 기존 review_* 이미지들은
    제거한 뒤 이번 업로드 파일로 교체합니다.
    """
    files = list(uploaded_files or [])

    if not files:
        return list_saved_review_images(project)

    folder = review_image_dir(project)
    folder.mkdir(parents=True, exist_ok=True)

    for old_path in folder.iterdir():
        if (
            old_path.is_file()
            and old_path.suffix.lower() in SUPPORTED_REVIEW_IMAGE_SUFFIXES
        ):
            old_path.unlink()

    saved_paths = []

    for index, uploaded_file in enumerate(files, start=1):
        original_name = getattr(uploaded_file, "name", "") or ""
        suffix = Path(original_name).suffix.lower()

        if suffix not in SUPPORTED_REVIEW_IMAGE_SUFFIXES:
            suffix = ".png"

        destination = folder / f"review_{index:02d}{suffix}"
        destination.write_bytes(uploaded_file.getbuffer())
        saved_paths.append(str(destination))

    return saved_paths


def product_image_dir(project):
    return PRODUCT_IMAGE_ROOT / f"project_{safe_project_id(project)}"


def list_saved_product_images(project):
    """프로젝트별로 저장된 상품/상세 이미지를 순서대로 반환합니다."""
    folder = product_image_dir(project)
    if not folder.exists():
        return []

    return [
        str(path)
        for path in sorted(folder.iterdir())
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_PRODUCT_IMAGE_SUFFIXES
    ]


def find_saved_product_image(project):
    """기존 1장 호출부 호환용 대표 이미지 경로를 반환합니다."""
    paths = list_saved_product_images(project)
    return paths[0] if paths else ""


def save_uploaded_product_images(project, uploaded_files):
    """
    상품 대표 이미지와 상세페이지 캡처를 프로젝트 폴더에 저장합니다.

    새 파일이 선택되면 기존 상품 이미지들을 모두 교체합니다.
    첫 번째 이미지는 00_main, 나머지는 detail 이미지로 저장합니다.
    """
    files = list(uploaded_files or [])

    if not files:
        return list_saved_product_images(project)

    folder = product_image_dir(project)
    folder.mkdir(parents=True, exist_ok=True)

    for old_path in folder.iterdir():
        if (
            old_path.is_file()
            and old_path.suffix.lower() in SUPPORTED_PRODUCT_IMAGE_SUFFIXES
        ):
            old_path.unlink()

    saved_paths = []

    for index, uploaded_file in enumerate(files):
        original_name = getattr(uploaded_file, "name", "") or ""
        suffix = Path(original_name).suffix.lower()
        if suffix not in SUPPORTED_PRODUCT_IMAGE_SUFFIXES:
            suffix = ".jpg"

        filename = (
            f"00_main{suffix}"
            if index == 0
            else f"{index:02d}_detail{suffix}"
        )
        destination = folder / filename
        destination.write_bytes(uploaded_file.getbuffer())
        saved_paths.append(str(destination))

    return saved_paths


def save_uploaded_product_image(project, uploaded_file):
    """기존 1장 호출부 호환용 저장 함수입니다."""
    files = [] if uploaded_file is None else [uploaded_file]
    paths = save_uploaded_product_images(project, files)
    return paths[0] if paths else ""


def show_product_image_upload_area(project, key_prefix):
    project_safe_id = safe_project_id(project)
    saved_paths = list_saved_product_images(project)

    st.subheader("상품 이미지 · 상세페이지 캡처")
    st.caption(
        "상품 대표 이미지와 상세페이지 캡처를 여러 장 선택하세요. "
        "첫 번째 이미지는 대표 이미지, 나머지는 상세 이미지로 사용합니다."
    )

    uploaded_files = st.file_uploader(
        "상품 이미지 여러 장 선택",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key=f"{key_prefix}_product_images_{project_safe_id}",
    )

    if uploaded_files:
        st.success(
            f"새 상품 이미지 {len(uploaded_files)}장이 선택되었습니다."
        )
        preview_columns = st.columns(min(4, len(uploaded_files)))
        for index, uploaded_file in enumerate(uploaded_files[:4]):
            with preview_columns[index % len(preview_columns)]:
                st.image(
                    uploaded_file,
                    caption=("대표" if index == 0 else f"상세 {index}"),
                    width=180,
                )
    elif saved_paths:
        st.info(
            f"저장된 상품 이미지 {len(saved_paths)}장을 다시 사용합니다."
        )
        st.caption(str(product_image_dir(project)))
    else:
        st.warning(
            "상품 이미지가 없습니다. Vision·Image Tagger·Scene Planner를 건너뜁니다."
        )

    return uploaded_files


def viral_upload_dir(project):
    return VIRAL_UPLOAD_ROOT / f"project_{safe_project_id(project)}"


def list_saved_viral_videos(project):
    folder = viral_upload_dir(project)
    if not folder.exists():
        return []
    return [
        str(path)
        for path in sorted(folder.iterdir())
        if path.is_file() and path.suffix.lower() in SUPPORTED_VIRAL_VIDEO_SUFFIXES
    ]


def save_uploaded_viral_videos(project, uploaded_files):
    files = list(uploaded_files or [])[:10]
    if not files:
        return list_saved_viral_videos(project)

    folder = viral_upload_dir(project)
    folder.mkdir(parents=True, exist_ok=True)
    for old_path in folder.iterdir():
        if old_path.is_file() and old_path.suffix.lower() in SUPPORTED_VIRAL_VIDEO_SUFFIXES:
            old_path.unlink()

    saved_paths = []
    for index, uploaded_file in enumerate(files, start=1):
        original_name = getattr(uploaded_file, "name", "") or ""
        suffix = Path(original_name).suffix.lower()
        if suffix not in SUPPORTED_VIRAL_VIDEO_SUFFIXES:
            suffix = ".mp4"
        destination = folder / f"viral_{index:02d}{suffix}"
        destination.write_bytes(uploaded_file.getbuffer())
        saved_paths.append(str(destination))
    return saved_paths


def parse_viral_urls(value):
    urls = []
    for line in str(value or "").splitlines():
        clean = line.strip()
        if clean and clean.startswith(("http://", "https://")) and clean not in urls:
            urls.append(clean)
    return urls[:10]


def show_viral_input_area(project, key_prefix):
    project_safe_id = safe_project_id(project)
    saved_paths = list_saved_viral_videos(project)

    st.subheader("바이럴 쇼츠 참고 영상")
    st.caption(
        "직접 고른 바이럴 쇼츠 URL 또는 영상 파일을 최대 10개 입력하세요. "
        "영상 자체를 복제하지 않고 장면 길이·컷 속도·모션·자막 위치 패턴만 분석합니다."
    )
    viral_urls_text = st.text_area(
        "바이럴 쇼츠 URL (한 줄에 하나)",
        height=130,
        placeholder="https://www.youtube.com/shorts/...",
        key=f"{key_prefix}_viral_urls_{project_safe_id}",
    )
    uploaded_files = st.file_uploader(
        "바이럴 쇼츠 영상 파일",
        type=["mp4", "mov", "mkv", "webm", "m4v"],
        accept_multiple_files=True,
        key=f"{key_prefix}_viral_videos_{project_safe_id}",
    )
    url_count = len(parse_viral_urls(viral_urls_text))
    upload_count = len(uploaded_files or [])
    if url_count + upload_count > 10:
        st.warning("URL과 파일을 합쳐 앞의 10개만 분석합니다.")
    elif url_count or upload_count:
        st.success(f"바이럴 참고 영상 {url_count + upload_count}개가 준비됐습니다.")
    elif saved_paths:
        st.info(f"저장된 바이럴 영상 {len(saved_paths)}개를 다시 사용합니다.")
    else:
        st.caption("입력하지 않으면 바이럴 편집 분석 단계만 건너뜁니다.")
    return viral_urls_text, uploaded_files


def extract_product_payload(built, coupang_url, product_name):
    if not isinstance(built, dict):
        return {
            "coupang_url": coupang_url,
            "product_name": product_name,
            "title": product_name,
        }

    for key in ["payload", "product", "project", "data", "result"]:
        value = built.get(key)
        if isinstance(value, dict):
            payload = dict(value)
            payload.setdefault("coupang_url", coupang_url)
            payload.setdefault("product_name", product_name)
            payload.setdefault("title", product_name)
            return payload

    payload = dict(built)
    payload.setdefault("coupang_url", coupang_url)
    payload.setdefault("product_name", product_name)
    payload.setdefault("title", product_name)
    return payload


def build_keywords(product_payload, product_name):
    fallback = {
        "main_keyword": product_name,
        "taobao_keyword": product_name,
        "keyword": product_name,
        "keywords": [product_name],
    }

    if SearchKeywordEngine is None:
        return fallback

    engine = SearchKeywordEngine()

    for method_name in ["build", "generate", "run", "create", "extract"]:
        method = getattr(engine, method_name, None)
        if not callable(method):
            continue

        try:
            result = method(product_payload)
        except TypeError:
            try:
                result = method(product_name)
            except Exception:
                continue
        except Exception:
            continue

        if isinstance(result, dict):
            result.setdefault("main_keyword", product_name)
            result.setdefault(
                "taobao_keyword",
                result.get("main_keyword", product_name),
            )
            return result

    return fallback


def create_project_from_payload(product_payload, keywords):
    payload = dict(product_payload)
    payload["keywords"] = keywords

    service = ProjectService()

    for method_name in [
        "create_project",
        "create",
        "save_project",
        "create_from_product",
        "build_project",
    ]:
        method = getattr(service, method_name, None)
        if not callable(method):
            continue

        try:
            project = method(payload)
            if project:
                return project
        except TypeError:
            try:
                project = method(
                    product_name=(
                        payload.get("product_name")
                        or payload.get("title")
                    ),
                    coupang_url=payload.get("coupang_url"),
                    keywords=keywords,
                    payload=payload,
                )
                if project:
                    return project
            except Exception:
                continue
        except Exception:
            continue

    raise RuntimeError(
        "ProjectService에서 사용 가능한 프로젝트 생성 메서드를 찾지 못했습니다."
    )


def rebuild_project_from_coupang(
    coupang_url,
    product_name,
):
    if ProductEngine is None:
        raise RuntimeError(
            "ProductEngine import 실패: "
            "modules.product.product_engine 확인 필요"
        )

    print(
        "[PROJECT CREATE] 1. ProductEngine START",
        flush=True,
    )

    try:
        built = ProductEngine().build_from_coupang(
            coupang_url,
            product_name=product_name,
            manual_product_name=product_name,
        )
    except Exception as exc:
        raise RuntimeError(
            "ProductEngine 단계 실패: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    print(
        "[PROJECT CREATE] 1. ProductEngine DONE",
        flush=True,
    )

    print(
        "[PROJECT CREATE] 2. Product Payload START",
        flush=True,
    )

    try:
        product_payload = extract_product_payload(
            built,
            coupang_url,
            product_name,
        )
    except Exception as exc:
        raise RuntimeError(
            "Product Payload 단계 실패: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    print(
        "[PROJECT CREATE] 2. Product Payload DONE",
        flush=True,
    )

    print(
        "[PROJECT CREATE] 3. Keyword Build START",
        flush=True,
    )

    try:
        keywords = build_keywords(
            product_payload,
            product_name,
        )
    except Exception as exc:
        raise RuntimeError(
            "Keyword Build 단계 실패: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    print(
        "[PROJECT CREATE] 3. Keyword Build DONE",
        flush=True,
    )

    print(
        "[PROJECT CREATE] 4. Project Save START",
        flush=True,
    )

    try:
        print(
            "[UTF8 PAYLOAD BEFORE SAVE]",
            json.dumps(
                {
                    "product_payload": product_payload,
                    "keywords": keywords,
                },
                ensure_ascii=False,
                default=str,
            ),
            flush=True,
        )
        project = create_project_from_payload(
            product_payload,
            keywords,
        )
    except Exception as exc:
        raise RuntimeError(
            "Project Save 단계 실패: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    print(
        "[PROJECT CREATE] 4. Project Save DONE",
        flush=True,
    )

    project_id = getattr(
        project,
        "id",
        None,
    )

    if project_id:
        project = (
            ProjectRepository().get(project_id)
            or project
        )

    return project, product_payload, keywords

def show_search_links(keywords, key_prefix="main"):
    if not keywords:
        return

    main_keyword = (
        keywords.get("main_keyword")
        or keywords.get("keyword")
        or ""
    )

    taobao_keyword = (
        keywords.get("taobao_keyword")
        or main_keyword
    )

    source_1688_keyword = (
        keywords.get("source_1688_keyword")
        or keywords.get("1688_keyword")
        or taobao_keyword
    )

    douyin_keyword = (
        keywords.get("douyin_keyword")
        or main_keyword
        or taobao_keyword
    )

    st.subheader("자동 검색 키워드")
    st.write("타오바오:", taobao_keyword)
    st.write("1688:", source_1688_keyword)
    st.write("도우인:", douyin_keyword)

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button(
            "타오바오 열기",
            key=f"{key_prefix}_search_taobao",
            use_container_width=True,
        ):
            open_with_login_browser(
                make_search_url("taobao", taobao_keyword)
            )
            st.success("타오바오 검색을 열었습니다.")

    with c2:
        if st.button(
            "1688 열기",
            key=f"{key_prefix}_search_1688",
            use_container_width=True,
        ):
            open_with_login_browser(
                make_search_url("1688", source_1688_keyword)
            )
            st.success("1688 검색을 열었습니다.")

    with c3:
        if st.button(
            "도우인 열기",
            key=f"{key_prefix}_search_douyin",
            use_container_width=True,
        ):
            open_with_login_browser(
                make_search_url("douyin", douyin_keyword)
            )
            st.success("도우인 검색을 열었습니다.")


def run_project_pipeline(
    project,
    sample_count,
    review_image_paths=None,
    review_text="",
    locked_script="",
    product_image_paths=None,
    product_image_path="",
    youtube_privacy_status="private",
    viral_video_sources=None,
    declared_review_count=0,
    review_checked_at="",
    monthly_purchase_count=0,
    rating=0.0,
    input_product_name="",
    stop_after_image_generation=False,
    gemini_video_mode=False,
    hook_text="",
    cta_text="",
    cta_product_logo_text="",
    voice_audio_path="",
    bgm_audio_path="",
    bgm_volume_percent=10,
    voice_name="지안",
    voice_id="",
    typecast_api_key="",
    tts_volume_percent=100,
    tts_speech_speed=1.0,
    clip_subtitles=None,
    clip_subtitle_effects=None,
    clip_sfx=None,
    clip_playback_speeds=None,
    clip_narrations=None,
    gemini_clip_count=4,
    upload_enabled=False,
    playback_speed=1.5,
    channel_type="shopping",
    reservation_payload=None,
    force_run_id="",
):
    """Sprint193-27: 동일 입력도 영상만 제작 버튼을 누를 때마다 새로 실행합니다."""
    base_project_key = str(safe_project_id(project))
    resolved_force_run_id = str(force_run_id or "").strip()
    project_key = (
        f"{base_project_key}:direct:{resolved_force_run_id}"
        if resolved_force_run_id
        else base_project_key
    )

    with _PIPELINE_RUN_GUARD:
        if project_key in _ACTIVE_PIPELINE_PROJECTS:
            print(
                "[Sprint102-3 One Click Guard] SKIPPED:",
                project_key,
                flush=True,
            )
            cached = st.session_state.get(
                f"one_click_result_{base_project_key}",
                {},
            )
            if isinstance(cached, dict) and cached:
                return cached
            return {
                "job_id": "",
                "state": {},
                "outputs": {
                    "duplicate_execution_skipped": True,
                    "project_key": project_key,
                },
                "summary": "동일 프로젝트가 이미 실행 중이어서 중복 실행을 건너뛰었습니다.",
                "duplicate_execution_skipped": True,
            }

        _ACTIVE_PIPELINE_PROJECTS.add(project_key)

    print(
        "[Sprint193-29 One Click Guard] ACQUIRED:",
        {
            "project_key": project_key,
            "base_project_key": base_project_key,
            "force_run_id": resolved_force_run_id,
        },
        flush=True,
    )

    try:
        print(
            "[Sprint147-5 UI ROUTE]",
            {
                "project_key": project_key,
                "stop_after_image_generation": bool(stop_after_image_generation),
                "locked_script_chars": len(str(locked_script or "").strip()),
            },
            flush=True,
        )
        return _run_project_pipeline_impl(
            project=project,
            sample_count=sample_count,
            review_image_paths=review_image_paths,
            review_text=review_text,
            locked_script=locked_script,
            product_image_paths=product_image_paths,
            product_image_path=product_image_path,
            youtube_privacy_status=youtube_privacy_status,
            viral_video_sources=viral_video_sources,
            declared_review_count=declared_review_count,
            review_checked_at=review_checked_at,
            monthly_purchase_count=monthly_purchase_count,
            rating=rating,
            input_product_name=input_product_name,
            stop_after_image_generation=stop_after_image_generation,
            gemini_video_mode=gemini_video_mode,
            hook_text=hook_text,
            cta_text=cta_text,
            cta_product_logo_text=cta_product_logo_text,
            voice_audio_path=voice_audio_path,
            bgm_audio_path=bgm_audio_path,
            bgm_volume_percent=bgm_volume_percent,
            voice_name=voice_name,
            voice_id=voice_id,
            typecast_api_key=typecast_api_key,
            tts_volume_percent=tts_volume_percent,
            tts_speech_speed=tts_speech_speed,
            clip_subtitles=clip_subtitles,
            clip_subtitle_effects=clip_subtitle_effects,
            clip_sfx=clip_sfx,
            clip_playback_speeds=clip_playback_speeds,
            clip_narrations=clip_narrations,
            gemini_clip_count=gemini_clip_count,
            upload_enabled=upload_enabled,
            playback_speed=playback_speed,
            channel_type=channel_type,
            reservation_payload=reservation_payload,
        )
    finally:
        with _PIPELINE_RUN_GUARD:
            _ACTIVE_PIPELINE_PROJECTS.discard(project_key)
        print(
            "[Sprint193-29 One Click Guard] RELEASED:",
            project_key,
            flush=True,
        )


def _run_project_pipeline_impl(
    project,
    sample_count,
    review_image_paths=None,
    review_text="",
    locked_script="",
    product_image_paths=None,
    product_image_path="",
    youtube_privacy_status="private",
    viral_video_sources=None,
    declared_review_count=0,
    review_checked_at="",
    monthly_purchase_count=0,
    rating=0.0,
    input_product_name="",
    stop_after_image_generation=False,
    gemini_video_mode=False,
    hook_text="",
    cta_text="",
    cta_product_logo_text="",
    voice_audio_path="",
    bgm_audio_path="",
    bgm_volume_percent=10,
    voice_name="지안",
    voice_id="",
    typecast_api_key="",
    tts_volume_percent=100,
    tts_speech_speed=1.0,
    clip_subtitles=None,
    clip_subtitle_effects=None,
    clip_sfx=None,
    clip_playback_speeds=None,
    clip_narrations=None,
    gemini_clip_count=4,
    upload_enabled=False,
    playback_speed=1.5,
    channel_type="shopping",
    reservation_payload=None,
):
    print(
        "[Sprint172-1] run_project_pipeline entered",
        flush=True,
    )

    review_image_paths = list(review_image_paths or [])
    review_text = str(review_text or "").strip()
    locked_script = str(locked_script or "").strip()
    product_image_paths = list(product_image_paths or [])
    if product_image_path and product_image_path not in product_image_paths:
        product_image_paths.insert(0, product_image_path)
    product_image_path = product_image_paths[0] if product_image_paths else ""
    # Sprint194-12: 쇼핑 모드는 기존 최대 10개 소스 제한을 유지하지만,
    # 역사쿠키는 장면 이미지/MP4가 최대 25장까지 필요하므로 10개로 자르지 않습니다.
    _raw_viral_video_sources_194_12 = [
        str(item).strip()
        for item in list(viral_video_sources or [])
        if str(item).strip()
    ]
    _history_mode_194_12_ui = str(channel_type or "").strip().lower() in {
        "history", "history_ko", "history_en"
    }
    viral_video_sources = (
        _raw_viral_video_sources_194_12[:25]
        if _history_mode_194_12_ui
        else _raw_viral_video_sources_194_12[:10]
    )
    print(
        "[Sprint194-12 History Scene Pass Through]",
        {
            "history_mode": _history_mode_194_12_ui,
            "input_count": len(_raw_viral_video_sources_194_12),
            "passed_count": len(viral_video_sources),
            "cap": 25 if _history_mode_194_12_ui else 10,
        },
        flush=True,
    )

    print(
        "[Sprint72-1] Review Images:",
        len(review_image_paths),
        review_image_paths,
        flush=True,
    )

    print(
        "[Sprint115-1 Evidence Input] Manual Review Text:",
        bool(review_text),
        "chars=",
        len(review_text),
        flush=True,
    )

    print(
        "[Sprint134-1 Viral Input] Sources:",
        len(viral_video_sources),
        viral_video_sources,
        flush=True,
    )

    print(
        "[Sprint94-1 Manual Images] Product Images:",
        len(product_image_paths),
        product_image_paths,
        flush=True,
    )

    print(
        "[Sprint146-9 UI -> WORKFLOW]",
        {
            "locked_script_chars": len(locked_script),
            "monthly_purchase_count": int(monthly_purchase_count or 0),
            "review_count": int(declared_review_count or 0),
            "rating": float(rating or 0),
            "review_checked_at": str(review_checked_at or ""),
            "image_count": len(product_image_paths),
        },
        flush=True,
    )

    print(
        "[Sprint147-5 UI -> WORKFLOW CALL]",
        {
            "stop_after_image_generation": bool(stop_after_image_generation),
            "locked_script_chars": len(locked_script),
            "image_count": len(product_image_paths),
        },
        flush=True,
    )

    result = WorkflowEngine().run_project(
        project,
        sample_count=sample_count,
        review_image_paths=review_image_paths,
        review_text=review_text,
        locked_script=locked_script,
        product_image_paths=product_image_paths,
        product_image_path=product_image_path,
        youtube_privacy_status=youtube_privacy_status,
        viral_video_sources=viral_video_sources,
        declared_review_count=declared_review_count,
        review_checked_at=review_checked_at,
        monthly_purchase_count=monthly_purchase_count,
        rating=rating,
        input_product_name=input_product_name,
        stop_after_image_generation=stop_after_image_generation,
        gemini_video_mode=gemini_video_mode,
        hook_text=hook_text,
        cta_text=cta_text,
        cta_product_logo_text=cta_product_logo_text,
        voice_audio_path=voice_audio_path,
        bgm_audio_path=bgm_audio_path,
        bgm_volume_percent=bgm_volume_percent,
        voice_name=voice_name,
        voice_id=voice_id,
        typecast_api_key=typecast_api_key,
        tts_volume_percent=tts_volume_percent,
        tts_speech_speed=tts_speech_speed,
        clip_subtitles=list(clip_subtitles or []),
        clip_subtitle_effects=list(clip_subtitle_effects or []),
        clip_sfx=list(clip_sfx or []),
        clip_playback_speeds=list(clip_playback_speeds or []),
        clip_narrations=list(clip_narrations or []),
        gemini_clip_count=gemini_clip_count,
        upload_enabled=upload_enabled,
        playback_speed=playback_speed,
        channel_type=channel_type,
        reservation_payload=reservation_payload,
    )

    try:
        product_named = create_product_named_video_copy(
            result=result,
            product_name=(
                str(input_product_name or "").strip()
                or str(getattr(project, "product_name", "") or "").strip()
                or str(getattr(project, "title", "") or "").strip()
            ),
            project_id=str(safe_project_id(project)),
        )
        if product_named:
            outputs = result.setdefault("outputs", {})
            outputs["product_named_final_video_path"] = product_named
            outputs["human_readable_final_video_path"] = product_named
            result["product_named_final_video_path"] = product_named
            print(
                "[Sprint181-3 Product Name Output] SAVED:",
                product_named,
                flush=True,
            )
    except Exception as exc:
        print(
            "[Sprint181-3 Product Name Output] ERROR:",
            type(exc).__name__,
            str(exc),
            flush=True,
        )

    try:
        _save_project_publisher_metadata(
            project=project,
            result=result,
            product_name=input_product_name,
            hook_text=hook_text,
            locked_script=locked_script,
            cta_text=cta_text,
            reservation_payload=reservation_payload,
        )
    except Exception as exc:
        print(
            "[Sprint183-2 Publisher Metadata] ERROR:",
            type(exc).__name__,
            str(exc),
            flush=True,
        )

    save_pipeline_result(project, result)

    st.session_state[
        f"one_click_result_{safe_project_id(project)}"
    ] = result

    return result


def show_review_upload_area(project, key_prefix):
    project_safe_id = safe_project_id(project)
    saved_paths = list_saved_review_images(project)

    st.subheader("리뷰 이미지 OCR")
    st.caption(
        "쿠팡 리뷰 캡처 이미지를 여러 장 선택하면 "
        "프로젝트별 폴더에 저장한 뒤 OCR과 리뷰 분석에 사용합니다."
    )

    uploaded_files = st.file_uploader(
        "리뷰 이미지 선택",
        type=["png", "jpg", "jpeg", "webp", "bmp"],
        accept_multiple_files=True,
        key=f"{key_prefix}_review_images_{project_safe_id}",
    )

    if uploaded_files:
        st.success(
            f"새 리뷰 이미지 {len(uploaded_files)}장이 선택되었습니다."
        )
    elif saved_paths:
        st.info(
            f"이 프로젝트에 저장된 리뷰 이미지 {len(saved_paths)}장을 "
            "다시 사용합니다."
        )
        st.caption(str(review_image_dir(project)))
    else:
        st.caption("선택되거나 저장된 리뷰 이미지가 없습니다.")

    return uploaded_files


def show_review_text_input_area(project, key_prefix):
    """Sprint115-3: 리뷰 입력값을 text_area 반환값으로 직접 전달합니다."""
    project_safe_id = safe_project_id(project)
    state_key = f"{key_prefix}_review_text_{project_safe_id}"

    st.subheader("리뷰 · 댓글 직접 입력")
    st.caption(
        "한글 리뷰나 댓글을 그대로 붙여넣으세요. "
        "내용이 있으면 리뷰 이미지 OCR보다 직접 입력값을 우선 사용합니다."
    )

    review_text = st.text_area(
        "리뷰 또는 댓글 붙여넣기",
        height=220,
        placeholder=(
            "바퀴가 부드럽게 잘 굴러가요.\n\n"
            "3박 4일 여행에 크기가 잘 맞았습니다."
        ),
        key=state_key,
    )

    review_text = str(review_text or "")

    st.caption(f"현재 입력 글자 수: {len(review_text.strip())}")

    if review_text.strip():
        st.success(
            f"직접 입력 리뷰가 준비됐습니다. "
            f"({len(review_text.strip())}자)"
        )

    return review_text


def render_project_pipeline(
    project,
    sample_count,
    review_text="",
    youtube_privacy_status="private",
):
    init_selected_sources(project)

    project_safe_id = safe_project_id(project)
    result_key = f"one_click_result_{project_safe_id}"

    path_debug = VideoPathResolver().debug(project)
    project_name = (
        getattr(project, "product_name", "")
        or getattr(project, "title", "")
    )

    print(
        "[UTF8 UI PROJECT DISPLAY]",
        {
            "product_name_raw": getattr(project, "product_name", ""),
            "product_name_repr": repr(getattr(project, "product_name", "")),
            "title_raw": getattr(project, "title", ""),
            "title_repr": repr(getattr(project, "title", "")),
            "project_name_raw": project_name,
            "project_name_repr": repr(project_name),
        },
        flush=True,
    )

    st.success(f"선택된 프로젝트: {project_name}")

    if not path_debug.get("exists"):
        st.warning("이 프로젝트에는 아직 원본 영상이 없습니다.")
    else:
        st.caption(
            f"영상: {path_debug.get('video_path')} / "
            f"{path_debug.get('size_mb')}MB"
        )

    uploaded_product_images = show_product_image_upload_area(
        project,
        key_prefix="existing",
    )

    uploaded_review_images = show_review_upload_area(
        project,
        key_prefix="existing",
    )

    viral_urls_text, uploaded_viral_videos = show_viral_input_area(
        project,
        key_prefix="existing",
    )

    manual_review_text = str(review_text or "")

    c1, c2 = st.columns(2)

    if c1.button(
        "현재 프로젝트 원클릭 실행",
        use_container_width=True,
        key=f"existing_one_click_{project_safe_id}",
    ):
        manual_review_text = str(manual_review_text or "")
        print(
            "[Sprint115-4 Unified Review Value] chars=",
            len(manual_review_text.strip()),
            flush=True,
        )
        print(
            "[Sprint72-1] One Click button pressed",
            flush=True,
        )

        try:
            product_image_paths = save_uploaded_product_images(
                project,
                uploaded_product_images,
            )
            product_image_path = (
                product_image_paths[0] if product_image_paths else ""
            )
        except Exception as exc:
            st.error(f"상품 대표 이미지 저장 실패: {exc}")
            return

        try:
            review_paths = save_uploaded_review_images(
                project,
                uploaded_review_images,
            )
        except Exception as exc:
            st.error(f"리뷰 이미지 저장 실패: {exc}")
            return

        try:
            viral_file_paths = save_uploaded_viral_videos(project, uploaded_viral_videos)
            viral_sources = (parse_viral_urls(viral_urls_text) + viral_file_paths)[:10]
        except Exception as exc:
            st.error(f"바이럴 영상 저장 실패: {exc}")
            return

        if product_image_paths:
            st.info(
                f"상품 이미지 {len(product_image_paths)}장을 AI Director에 전달합니다."
            )

        if manual_review_text.strip():
            st.info("직접 입력한 한글 리뷰를 우선 사용합니다. 리뷰 이미지 OCR은 건너뜁니다.")
        elif review_paths:
            st.info(
                f"리뷰 이미지 {len(review_paths)}장을 OCR에 전달합니다."
            )

        with st.spinner("One Click Pipeline 실행 중입니다..."):
            try:
                result = run_project_pipeline(
                    project,
                    sample_count,
                    review_image_paths=review_paths,
                    review_text=manual_review_text,
                    product_image_paths=product_image_paths,
                    product_image_path=product_image_path,
                    youtube_privacy_status=youtube_privacy_status,
                    viral_video_sources=viral_sources,
                    input_product_name=project_name,
                )
            except Exception as exc:
                st.error(f"원클릭 실행 실패: {exc}")
                return

        st.success("원클릭 실행 결과를 저장했습니다.")

        outputs = (
            result.get("outputs", {})
            if isinstance(result, dict)
            else {}
        )

        review_ocr = outputs.get("review_ocr", {})
        review_insight = outputs.get("review_insight", {})
        product_plan = outputs.get("product_plan", {})

        st.write(
            "OCR 이미지 수:",
            review_ocr.get("image_count", len(review_paths)),
        )
        st.write(
            "OCR 리뷰 수:",
            review_ocr.get("review_count", 0),
        )
        st.write(
            "최종 병합 리뷰 수:",
            product_plan.get(
                "review_count",
                review_insight.get("review_count", 0),
            ),
        )
        st.write(
            "리뷰 분석 성공:",
            bool(review_insight.get("ok")),
        )

        project_latest = ProjectRepository().get(getattr(project, "id", "")) or project
        try:
            data = json.loads(getattr(project_latest, "data_json", "") or "{}")
        except Exception:
            data = {}

        youtube = data.get("youtube", {})
        youtube_history = data.get("youtube_history", [])

        if youtube.get("watch_url"):
            st.divider()
            st.subheader("📺 YouTube 업로드")
            st.success("YouTube 업로드 완료")
            st.write("Video ID:", youtube.get("video_id", ""))
            st.write("Watch URL:", youtube.get("watch_url", ""))
            st.link_button(
                "브라우저에서 열기",
                youtube.get("watch_url"),
                use_container_width=True,
            )

        if isinstance(youtube_history, list) and youtube_history:
            st.divider()
            st.subheader("📚 YouTube 업로드 이력")
            st.caption(
                f"총 {len(youtube_history)}개의 업로드 이력이 있습니다."
            )

            for index, item in enumerate(
                youtube_history,
                start=1,
            ):
                if not isinstance(item, dict):
                    continue

                video_id = item.get("video_id", "")
                watch_url = item.get("watch_url", "")
                uploaded_at = item.get("uploaded_at", "")
                status = item.get("status", "")
                manifest_path = item.get("manifest_path", "")

                with st.expander(
                    f"{index}. {video_id or 'Video ID 없음'}",
                    expanded=index == 1,
                ):
                    st.write("상태:", status)
                    st.write("업로드 시간:", uploaded_at)
                    st.write("Video ID:", video_id)
                    st.write("Watch URL:", watch_url)

                    if manifest_path:
                        st.caption(
                            f"Manifest: {manifest_path}"
                        )

                    if watch_url:
                        st.link_button(
                            "영상 열기",
                            watch_url,
                            use_container_width=True,
                            key=(
                                f"youtube_history_link_"
                                f"{project_safe_id}_{index}"
                            ),
                        )

    if c2.button("큐에 추가", use_container_width=True):
        job = JobQueue().add(
            getattr(project, "id", ""),
            project_name,
        )
        st.success(f"큐 추가 완료: {job.get('job_id')}")

    result = st.session_state.get(result_key)

    if not result:
        result = load_pipeline_result(project)
        if result:
            st.session_state[result_key] = result
            st.caption(
                "최근 원클릭 결과를 복원했습니다: "
                f"{pipeline_result_path(project)}"
            )

    if result:
        st.success("최근 원클릭 실행 결과가 있습니다.")

        show_result_detail = st.checkbox(
            "최근 실행 결과 상세 화면 열기",
            value=False,
            key=f"show_result_detail_{project_safe_id}",
        )

        if show_result_detail:
            show_pipeline_result(
                project,
                result,
                path_debug,
            )

            show_selected_sources(project)

            show_content_pack_view_new(
                project=project,
                result=result,
                content_pack=st.session_state.get(
                    f"content_pack_{project_safe_id}",
                    {},
                ),
                paths=st.session_state.get(
                    f"ai_content_pack_export_"
                    f"{getattr(project, 'id', '')}",
                    {},
                ),
            )

    else:
        st.info(
            "원클릭 결과가 아직 없습니다. "
            "먼저 원클릭 실행을 완료해 주세요."
        )


def _resolve_final_video_path(result):
    """Sprint146-5: Workflow 결과 구조가 달라도 실제 최종 MP4를 찾습니다."""
    outputs = result.get("outputs", {}) if isinstance(result, dict) else {}
    candidates = [
        outputs.get("product_named_final_video_path"),
        outputs.get("human_readable_final_video_path"),
        result.get("product_named_final_video_path") if isinstance(result, dict) else None,
    ]

    final_video = outputs.get("final_video")
    if isinstance(final_video, dict):
        candidates.extend(
            [
                final_video.get("output_path"),
                final_video.get("video_path"),
                final_video.get("path"),
            ]
        )
    else:
        candidates.append(final_video)

    for key in (
        "final_video_path",
        "produced_final_path",
        "active_video_path",
        "ai_video_path",
        "image_motion_video_path",
        "merged_video_path",
    ):
        candidates.append(outputs.get(key))

    content_factory = outputs.get("content_factory")
    if isinstance(content_factory, dict):
        for key in (
            "final_video_path",
            "video_path",
            "active_video_path",
            "output_path",
        ):
            candidates.append(content_factory.get(key))

    for raw_path in candidates:
        path_text = str(raw_path or "").strip()
        if not path_text:
            continue
        path = Path(path_text)
        if path.is_file() and path.suffix.lower() == ".mp4":
            return str(path)

    return ""


def _extract_image_review_scenes(result):
    outputs = result.get("outputs", {}) if isinstance(result, dict) else {}
    review = outputs.get("image_review", {})
    if not isinstance(review, dict):
        return []
    return [dict(item) for item in list(review.get("scenes") or []) if isinstance(item, dict)]



def _first_existing_image_path(*values):
    for value in values:
        path_text = str(value or "").strip()
        if path_text and Path(path_text).is_file():
            return path_text
    return ""


def _find_first_value(data, keys):
    """중첩 dict/list에서 지정 키의 첫 유효 값을 찾습니다."""
    if isinstance(data, dict):
        for key in keys:
            value = data.get(key)
            if value not in (None, "", [], {}):
                return value
        for value in data.values():
            found = _find_first_value(value, keys)
            if found not in (None, "", [], {}):
                return found
    elif isinstance(data, list):
        for item in data:
            found = _find_first_value(item, keys)
            if found not in (None, "", [], {}):
                return found
    return None



def _collect_project_metadata_sources(project_id, selected_metadata=None):
    """기존 프로젝트에 저장된 게시용 메타데이터 JSON을 최신순으로 수집합니다."""
    sources = []
    if isinstance(selected_metadata, dict) and selected_metadata:
        sources.append(("content_library", selected_metadata))

    clean_id = str(project_id or "").strip()
    candidate_paths = []
    if clean_id:
        product_folder = PRODUCT_IMAGE_ROOT / f"project_{clean_id}"
        publisher_metadata_path = product_folder / "publisher_metadata.json"
        candidate_paths.extend([
            publisher_metadata_path,
            RESULT_DIR / f"{clean_id}_latest_result.json",
            Path("exports/one_click_results") / f"project_{clean_id}_latest_result.json",
        ])
        if product_folder.exists():
            candidate_paths.extend(
                path for path in product_folder.rglob("*.json")
                if path != publisher_metadata_path
            )

    unique = []
    seen = set()
    for path in candidate_paths:
        try:
            resolved = str(Path(path).resolve())
        except Exception:
            resolved = str(path)
        if resolved in seen or not Path(path).is_file():
            continue
        seen.add(resolved)
        unique.append(Path(path))

    # publisher_metadata.json은 영상 제작 시 확정한 게시 데이터이므로 항상 최우선입니다.
    unique.sort(
        key=lambda path: (
            0 if path.name == "publisher_metadata.json" else 1,
            -path.stat().st_mtime,
        )
    )
    for path in unique:
        loaded = read_json(path, {})
        if isinstance(loaded, dict) and loaded:
            sources.append((str(path), loaded))
    return sources


def _deep_find_first(data, keys):
    """키 우선순위대로 중첩 JSON 전체에서 첫 유효 값을 찾습니다."""
    for key in keys:
        value = _find_first_value(data, (key,))
        if value not in (None, "", [], {}):
            return value
    return None


def _normalize_hashtag_value(value):
    if isinstance(value, str):
        parts = [item for item in re.split(r"[\s,]+", value) if item.strip()]
    elif isinstance(value, (list, tuple, set)):
        parts = list(value)
    else:
        parts = []
    output = []
    for raw in parts:
        clean = re.sub(r"[^0-9A-Za-z가-힣_]", "", str(raw).lstrip("#").strip())
        if clean and clean not in output:
            output.append(clean)
    return output


def _save_project_publisher_metadata(
    *,
    project,
    result,
    product_name="",
    hook_text="",
    locked_script="",
    cta_text="",
    reservation_payload=None,
):
    """영상 제작 완료 시 예약 게시용 메타데이터를 프로젝트 폴더에 확정 저장합니다."""
    project_id = str(safe_project_id(project))
    final_video_path = _resolve_final_video_path(result)
    if not final_video_path or not Path(final_video_path).is_file():
        return ""

    payload = dict(reservation_payload or {})
    resolved_product_name = str(
        product_name
        or getattr(project, "product_name", "")
        or getattr(project, "title", "")
        or ""
    ).strip()
    resolved_hook = str(hook_text or "").strip()
    resolved_script = str(locked_script or "").strip()
    resolved_cta = str(cta_text or "").strip()
    infock_url = str(payload.get("infock_url") or "").strip()

    outputs = result.get("outputs", {}) if isinstance(result, dict) else {}
    video_pipeline = outputs.get("video_pipeline", {}) if isinstance(outputs, dict) else {}
    if not resolved_hook and isinstance(video_pipeline, dict):
        resolved_hook = str(
            video_pipeline.get("resolved_hook_text")
            or ((video_pipeline.get("steps") or {}).get("subtitle") or {}).get("hook_text")
            or ""
        ).strip()

    title_override = resolved_hook.splitlines()[0].strip() if resolved_hook else ""
    built = ScheduledMetadataBuilder.build(
        product_name=resolved_product_name or title_override or Path(final_video_path).stem,
        hook_text=resolved_hook,
        locked_script=resolved_script,
        cta_text=resolved_cta,
        infock_url=infock_url,
        hashtags=[],
        title_override=title_override,
    )

    metadata = {
        "version": "publisher-metadata-183-2",
        "project_id": project_id,
        "product_name": resolved_product_name,
        "display_name": resolved_product_name,
        "title": str(built.get("title") or "").strip(),
        "youtube_title": str(built.get("title") or "").strip(),
        "description": str(built.get("description") or "").strip(),
        "youtube_description": str(built.get("description") or "").strip(),
        "pinned_comment": str(built.get("pinned_comment") or "").strip(),
        "hashtags": list(built.get("hashtags") or []),
        "hashtag_text": " ".join(
            f"#{str(tag).lstrip('#')}" for tag in list(built.get("hashtags") or [])
        ),
        "infock_url": infock_url,
        "hook_text": resolved_hook,
        "locked_script": resolved_script,
        "cta_text": resolved_cta,
        "video_path": final_video_path,
        "final_video_path": final_video_path,
        "youtube_privacy_status": str(outputs.get("youtube_privacy_status") or "private"),
        "created_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
        "source": "video_completion",
    }
    target = PRODUCT_IMAGE_ROOT / f"project_{project_id}" / "publisher_metadata.json"
    write_json(target, metadata)

    if isinstance(result, dict):
        result_outputs = result.setdefault("outputs", {})
        result_outputs["publisher_metadata_path"] = str(target)
        result_outputs["publisher_metadata"] = metadata
        result["publisher_metadata_path"] = str(target)

    print(
        "[Sprint183-2 Publisher Metadata] SAVED:",
        str(target),
        "Title:",
        metadata["title"],
        flush=True,
    )
    return str(target)


def _restore_project_publisher_metadata(project_id, selected_metadata=None):
    """Publisher Pack/원클릭 결과에서 실제 제목·본문·댓글·해시태그를 복원합니다."""
    restored = {
        "product_name": "",
        "title": "",
        "description": "",
        "pinned_comment": "",
        "hashtags": [],
        "locked_script": "",
        "hook_text": "",
        "cta_text": "",
        "infock_url": "",
        "source_paths": [],
    }
    sources = _collect_project_metadata_sources(project_id, selected_metadata)
    restored["source_paths"] = [name for name, _ in sources]

    field_keys = {
        "product_name": ("product_name", "display_name", "product_title"),
        "title": ("youtube_title", "video_title", "shorts_title", "title"),
        "description": ("youtube_description", "description", "body", "caption", "reels_caption"),
        "pinned_comment": ("pinned_comment", "fixed_comment", "first_comment", "comment_text"),
        "locked_script": ("locked_script", "approved_script_text", "best_script", "original_best_script"),
        "hook_text": ("best_hook", "hook_text", "hook"),
        "cta_text": ("cta_text", "cta", "youtube_cta"),
        "infock_url": ("infock_url", "inpock_url", "affiliate_link", "partner_url"),
    }
    for field, keys in field_keys.items():
        for _, source in sources:
            value = _deep_find_first(source, keys)
            if value not in (None, "", [], {}):
                restored[field] = str(value).strip()
                break

    for _, source in sources:
        tags = _deep_find_first(source, ("hashtag_text", "hashtags", "tags"))
        normalized = _normalize_hashtag_value(tags)
        if normalized:
            restored["hashtags"] = normalized
            break

    # title이 단순 상품명+쇼츠인 낡은 pack이면 후킹을 우선합니다.
    if restored["title"].endswith(" 쇼츠") and restored["hook_text"]:
        restored["title"] = restored["hook_text"].splitlines()[0].strip()
    return restored


def _director_json_candidates(project_id):
    folder = PRODUCT_IMAGE_ROOT / f"project_{project_id}"
    preferred = [
        folder / "ai_image_director_154_2.json",
        folder / "ai_image_director_154.json",
        folder / "ai_image_director_150_4.json",
        folder / "ai_image_manifest.json",
        folder / "manifest.json",
    ]
    existing = [path for path in preferred if path.is_file()]

    extras = sorted(
        folder.glob("ai_image_director*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for path in extras:
        if path not in existing:
            existing.append(path)
    return existing


def _recover_review_scenes_from_project(project_id):
    """
    기존 Director JSON과 생성 시도 PNG에서 검토용 장면을 복원합니다.
    새 Gemini 생성이나 Vision 호출은 하지 않습니다.
    """
    project_id = str(project_id).strip()
    folder = PRODUCT_IMAGE_ROOT / f"project_{project_id}"
    source_path = None
    director_data = {}

    for candidate in _director_json_candidates(project_id):
        loaded = read_json(candidate, {})
        if isinstance(loaded, dict) and loaded:
            director_data = loaded
            source_path = candidate
            if isinstance(loaded.get("generation_runs"), list):
                break

    generation_runs = (
        director_data.get("generation_runs")
        if isinstance(director_data.get("generation_runs"), list)
        else []
    )

    if not generation_runs:
        nested = _find_first_value(director_data, ("generation_runs",))
        if isinstance(nested, list):
            generation_runs = nested

    scenes = []
    for index, raw_run in enumerate(generation_runs, start=1):
        if not isinstance(raw_run, dict):
            continue

        scene_id = str(
            raw_run.get("scene_id")
            or f"scene_{index:02d}"
        ).strip()
        attempts = [
            dict(item)
            for item in list(raw_run.get("attempts") or [])
            if isinstance(item, dict)
        ]

        best_attempt = None
        for item in attempts:
            candidate_path = _first_existing_image_path(
                item.get("generated_image_path"),
                item.get("image_path"),
                item.get("output_image_path"),
                item.get("output_path"),
            )
            if not candidate_path:
                continue
            candidate = dict(item)
            candidate["_existing_path"] = candidate_path
            score = float(
                candidate.get("score")
                or candidate.get("fidelity_score")
                or candidate.get("product_identity_score")
                or 0
            )
            candidate["_score"] = score
            if best_attempt is None or score > best_attempt["_score"]:
                best_attempt = candidate

        selected_path = _first_existing_image_path(
            raw_run.get("selected_image_path"),
            raw_run.get("review_image_path"),
            raw_run.get("generated_image_path"),
            raw_run.get("resolved_image_path"),
        )
        if not selected_path and best_attempt:
            selected_path = best_attempt["_existing_path"]

        # JSON에 시도가 없더라도 프로젝트 폴더의 장면 PNG를 복원합니다.
        if not selected_path:
            scene_files = sorted(
                folder.glob(f"{scene_id}_ai_attempt_*.png"),
                key=lambda path: path.stat().st_mtime,
            )
            if scene_files:
                selected_path = str(scene_files[-1])

        source_scene = (
            raw_run.get("source_scene")
            if isinstance(raw_run.get("source_scene"), dict)
            else {}
        )
        fidelity = (
            best_attempt.get("fidelity")
            if best_attempt and isinstance(best_attempt.get("fidelity"), dict)
            else {}
        )
        issues = list(
            raw_run.get("issues")
            or fidelity.get("issues")
            or (
                best_attempt.get("issues")
                if best_attempt else []
            )
            or []
        )
        score = float(
            raw_run.get("best_score")
            or fidelity.get("fidelity_score")
            or (
                best_attempt.get("_score")
                if best_attempt else 0
            )
            or 0
        )
        passed = bool(
            raw_run.get("passed")
            or fidelity.get("passed")
            or (
                best_attempt.get("passed")
                if best_attempt else False
            )
        )

        scenes.append(
            {
                "scene_id": scene_id,
                "scene_index": int(
                    raw_run.get("scene_index")
                    or source_scene.get("scene_index")
                    or index
                ),
                "image_path": selected_path,
                "selected_image_path": selected_path,
                "review_image_path": selected_path,
                "generated_image_path": selected_path,
                "passed": passed,
                "fidelity_passed": passed,
                "best_score": score,
                "fidelity_score": score,
                "issues": issues,
                "attempts": attempts,
                "attempt_count": len(attempts),
                "subtitle_text": str(
                    raw_run.get("subtitle_text")
                    or source_scene.get("subtitle_text")
                    or source_scene.get("subtitle")
                    or source_scene.get("dialogue")
                    or ""
                ).strip(),
                "prompt": str(
                    raw_run.get("prompt")
                    or raw_run.get("image_prompt")
                    or source_scene.get("image_prompt")
                    or source_scene.get("prompt")
                    or ""
                ),
                "negative_prompt": str(
                    raw_run.get("negative_prompt")
                    or source_scene.get("negative_prompt")
                    or ""
                ),
                "reference_image_path": str(
                    raw_run.get("reference_image_path")
                    or source_scene.get("reference_image_path")
                    or folder / "00_main.png"
                ),
                "recovered_from_project": True,
            }
        )

    # generation_runs 구조를 못 찾으면 파일명으로 장면을 복원합니다.
    if not scenes:
        grouped = {}
        for path in sorted(folder.glob("scene_*_ai_attempt_*.png")):
            match = re.match(r"(scene_\d+)_ai_attempt_(\d+)\.png$", path.name)
            if not match:
                continue
            grouped.setdefault(match.group(1), []).append(path)

        for index, (scene_id, paths) in enumerate(sorted(grouped.items()), start=1):
            selected_path = str(paths[-1])
            scenes.append(
                {
                    "scene_id": scene_id,
                    "scene_index": index,
                    "image_path": selected_path,
                    "selected_image_path": selected_path,
                    "review_image_path": selected_path,
                    "generated_image_path": selected_path,
                    "passed": False,
                    "fidelity_passed": False,
                    "best_score": 0.0,
                    "issues": ["기존 생성 이미지를 파일에서 복원했습니다."],
                    "attempts": [
                        {
                            "attempt": attempt_index,
                            "generated_image_path": str(path),
                            "passed": False,
                        }
                        for attempt_index, path in enumerate(paths, start=1)
                    ],
                    "attempt_count": len(paths),
                    "subtitle_text": "",
                    "prompt": "",
                    "negative_prompt": "",
                    "reference_image_path": str(folder / "00_main.png"),
                    "recovered_from_project": True,
                }
            )

    return {
        "ok": bool(scenes),
        "project_id": project_id,
        "source_path": str(source_path or ""),
        "scenes": scenes,
        "scene_count": len(scenes),
    }


def _recover_project_input_payload(project, project_id):
    """최종 영상 제작에 필요한 기존 Locked Script와 신뢰 입력값을 복원합니다."""
    latest_result = read_json(
        RESULT_DIR / f"{project_id}_latest_result.json",
        {},
    )
    try:
        project_data = json.loads(getattr(project, "data_json", "") or "{}")
    except Exception:
        project_data = {}

    sources = [latest_result, project_data]
    locked_script = ""
    for source in sources:
        value = _find_first_value(
            source,
            (
                "locked_script",
                "approved_script_text",
                "original_best_script",
                "best_script",
            ),
        )
        if value:
            locked_script = str(value).strip()
            break

    def recover_number(keys, default):
        for source in sources:
            value = _find_first_value(source, keys)
            if value not in (None, ""):
                try:
                    return type(default)(value)
                except Exception:
                    continue
        return default

    return {
        "product_name": str(
            getattr(project, "product_name", "")
            or getattr(project, "title", "")
            or ""
        ),
        "locked_script": locked_script,
        "monthly_purchase_count": recover_number(
            ("monthly_purchase_count",),
            1,
        ),
        "declared_review_count": recover_number(
            ("declared_review_count", "review_count"),
            1,
        ),
        "rating": recover_number(("rating",), 0.0),
        "review_checked_at": str(
            _find_first_value(
                latest_result,
                ("review_checked_at",),
            )
            or _find_first_value(
                project_data,
                ("review_checked_at",),
            )
            or ""
        ),
    }


def _open_existing_project_review(project_id):
    project_id = str(project_id or "").strip()
    if not project_id:
        return {"ok": False, "message": "프로젝트 ID를 입력해 주세요."}

    project = ProjectRepository().get(project_id)
    if project is None:
        try:
            project = ProjectRepository().get(int(project_id))
        except Exception:
            project = None
    if project is None:
        return {
            "ok": False,
            "message": f"프로젝트 {project_id}를 DB에서 찾지 못했습니다.",
        }

    recovery = _recover_review_scenes_from_project(project_id)
    if not recovery.get("ok"):
        return {
            "ok": False,
            "message": (
                f"project_{project_id}에서 생성 이미지를 복원하지 못했습니다."
            ),
        }

    safe_id = str(safe_project_id(project))
    result = {
        "ok": True,
        "status": "recovered_project_review",
        "outputs": {
            "image_review": {
                "ok": True,
                "status": "recovered",
                "scenes": recovery["scenes"],
                "source_path": recovery["source_path"],
            }
        },
    }
    st.session_state["sprint147_active_project_id"] = getattr(
        project,
        "id",
        project_id,
    )
    st.session_state[f"one_click_result_{safe_id}"] = result
    st.session_state[f"sprint147_review_scenes_{safe_id}"] = recovery["scenes"]
    st.session_state[f"sprint147_approved_{safe_id}"] = {}
    st.session_state[f"sprint147_input_{safe_id}"] = (
        _recover_project_input_payload(project, safe_id)
    )
    st.session_state[f"sprint147_stage_{safe_id}"] = "review"

    print(
        "[Sprint155 Project Review] Opened:",
        safe_id,
        "Scenes:",
        recovery["scene_count"],
        "Source:",
        recovery["source_path"],
        flush=True,
    )
    return {
        "ok": True,
        "project": project,
        "project_id": safe_id,
        "scene_count": recovery["scene_count"],
        "source_path": recovery["source_path"],
    }


def _generate_single_scene_image(scene, output_path):
    """Sprint147-1: 선택한 장면 한 장만 Gemini 이미지 API로 다시 생성합니다."""
    generator_class = None
    import_errors = []
    for module_name, class_name in (
        ("modules.image_ai.gemini_image_generator", "GeminiImageGenerator"),
        ("modules.image_ai.ai_image_generator", "AIImageGenerator"),
    ):
        try:
            module = __import__(module_name, fromlist=[class_name])
            generator_class = getattr(module, class_name, None)
            if generator_class is not None:
                break
        except Exception as exc:
            import_errors.append(f"{module_name}: {type(exc).__name__}: {exc}")
    if generator_class is None:
        raise RuntimeError("이미지 생성기 import 실패: " + " | ".join(import_errors))

    engine = generator_class()
    payload = {
        "scene_id": str(scene.get("scene_id") or "scene"),
        "attempt": int(scene.get("attempt_count") or 1) + 1,
        "prompt": str(scene.get("prompt") or ""),
        "image_prompt": str(scene.get("prompt") or ""),
        "negative_prompt": str(scene.get("negative_prompt") or ""),
        "reference_image_path": str(scene.get("reference_image_path") or ""),
        "output_image_path": str(output_path),
        "output_path": str(output_path),
        "overwrite": True,
    }
    last_type_error = None
    for method_name in ("generate_image", "generate", "run", "create"):
        method = getattr(engine, method_name, None)
        if not callable(method):
            continue
        for call in (lambda: method(**payload), lambda: method(payload)):
            try:
                raw = call()
                candidate = ""
                if isinstance(raw, dict):
                    candidate = str(
                        raw.get("output_image_path")
                        or raw.get("output_path")
                        or raw.get("image_path")
                        or raw.get("path")
                        or ""
                    )
                elif isinstance(raw, (str, Path)):
                    candidate = str(raw)
                if candidate and Path(candidate).is_file():
                    return candidate
                if Path(output_path).is_file():
                    return str(output_path)
            except TypeError as exc:
                last_type_error = exc
                continue
    if last_type_error:
        raise last_type_error
    raise RuntimeError("이미지 생성 결과 파일을 확인하지 못했습니다.")


def _save_review_uploaded_image(project_id, scene_id, uploaded_file):
    suffix = Path(getattr(uploaded_file, "name", "") or "").suffix.lower()
    if suffix not in SUPPORTED_PRODUCT_IMAGE_SUFFIXES:
        suffix = ".png"
    folder = PRODUCT_IMAGE_ROOT / f"project_{project_id}" / "approved_images"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{safe_file_name(scene_id, 'scene')}_user{suffix}"
    path.write_bytes(uploaded_file.getbuffer())
    return str(path)


def _render_ai_image_review(project, result):
    project_id = str(safe_project_id(project))
    scenes_key = f"sprint147_review_scenes_{project_id}"
    approved_key = f"sprint147_approved_{project_id}"
    result_key = f"one_click_result_{project_id}"

    if scenes_key not in st.session_state:
        st.session_state[scenes_key] = _extract_image_review_scenes(result)
    if approved_key not in st.session_state:
        st.session_state[approved_key] = {}

    scenes = list(st.session_state.get(scenes_key) or [])
    approved = dict(st.session_state.get(approved_key) or {})
    if not scenes:
        outputs = result.get("outputs", {}) if isinstance(result, dict) else {}
        review = outputs.get("image_review", {}) if isinstance(outputs, dict) else {}
        st.error("생성된 장면 이미지가 없습니다.")
        if isinstance(review, dict):
            st.write("이미지 생성 상태:", review.get("status", ""))
            st.write("Director 상태:", review.get("director_status", ""))
            st.write("Closed Loop 상태:", review.get("closed_loop_status", ""))
            errors = list(review.get("generation_errors") or [])
            if errors:
                st.error(" / ".join(str(item) for item in errors))
        return

    st.divider()
    st.header("장면별 AI 이미지 확인")
    st.caption("마음에 드는 이미지는 승인하고, 마음에 들지 않는 장면만 다시 생성하세요.")

    for index, scene in enumerate(scenes):
        scene_id = str(scene.get("scene_id") or f"scene_{index + 1:02d}")
        image_path = str(
            scene.get("image_path")
            or scene.get("selected_image_path")
            or scene.get("approved_image_path")
            or scene.get("generated_image_path")
            or scene.get("final_image_path")
            or scene.get("resolved_image_path")
            or scene.get("output_image_path")
            or scene.get("review_image_path")
            or (
                (scene.get("attempts") or [{}])[-1].get("generated_image_path")
                if isinstance(scene.get("attempts"), list) and scene.get("attempts")
                else ""
            )
            or ""
        ).strip()
        with st.container(border=True):
            st.subheader(f"장면 {index + 1}")
            subtitle = str(scene.get("subtitle_text") or "").strip()
            if subtitle:
                st.write(f"자막: {subtitle}")

            passed = bool(
                scene.get("passed")
                or scene.get("fidelity_passed")
            )
            score = (
                scene.get("best_score")
                or scene.get("fidelity_score")
                or scene.get("score")
                or 0
            )
            issues = list(
                scene.get("issues")
                or scene.get("validation_issues")
                or []
            )

            if passed:
                st.success(f"자동 검수 통과 · 점수 {float(score or 0):.1f}")
            else:
                st.warning(
                    f"자동 검수 미통과 · 최고 점수 {float(score or 0):.1f} · "
                    "이미지를 확인한 뒤 직접 승인하거나 다시 생성하세요."
                )
                if issues:
                    st.caption(
                        "검수 사유: "
                        + " / ".join(str(item) for item in issues[:5])
                    )
            if image_path and Path(image_path).is_file():
                print(
                    "[Sprint154-1 Image Path Fallback] Scene:",
                    scene_id,
                    "Path:",
                    image_path,
                    flush=True,
                )
                st.image(image_path, use_container_width=True)
                st.caption(image_path)
            else:
                st.error("이미지 파일을 찾지 못했습니다.")

            c1, c2 = st.columns(2)
            if c1.button(
                "승인 완료" if approved.get(scene_id) else "이 이미지 승인",
                key=f"approve_{project_id}_{scene_id}",
                use_container_width=True,
                disabled=bool(approved.get(scene_id)) or not (image_path and Path(image_path).is_file()),
            ):
                approved[scene_id] = image_path
                st.session_state[approved_key] = approved
                st.rerun()

            if c2.button(
                "다시 생성",
                key=f"regen_{project_id}_{scene_id}",
                use_container_width=True,
            ):
                output_dir = PRODUCT_IMAGE_ROOT / f"project_{project_id}" / "generated_regenerated"
                output_dir.mkdir(parents=True, exist_ok=True)
                attempt = int(scene.get("attempt_count") or 1) + 1
                output_path = output_dir / f"{scene_id}_attempt_{attempt:02d}.png"
                with st.spinner(f"장면 {index + 1} 이미지를 다시 생성 중입니다..."):
                    try:
                        new_path = _generate_single_scene_image(scene, output_path)
                    except Exception as exc:
                        st.error(f"재생성 실패: {type(exc).__name__}: {exc}")
                    else:
                        scene["image_path"] = new_path
                        scene["selected_image_path"] = new_path
                        scene["approved_image_path"] = new_path
                        scene["generated_image_path"] = new_path
                        scene["final_image_path"] = new_path
                        scene["resolved_image_path"] = new_path
                        scene["output_image_path"] = new_path
                        scene["attempt_count"] = attempt
                        scenes[index] = scene
                        approved.pop(scene_id, None)
                        st.session_state[scenes_key] = scenes
                        st.session_state[approved_key] = approved
                        print(
                            "[Sprint147-3 Image Review] Regenerated:",
                            scene_id,
                            new_path,
                            flush=True,
                        )
                        st.rerun()

            replacement = st.file_uploader(
                "내 이미지로 교체",
                type=["png", "jpg", "jpeg", "webp"],
                key=f"replace_{project_id}_{scene_id}",
            )
            if replacement is not None:
                replacement_flag = f"replace_saved_{project_id}_{scene_id}_{replacement.name}_{replacement.size}"
                if not st.session_state.get(replacement_flag):
                    new_path = _save_review_uploaded_image(project_id, scene_id, replacement)
                    scene["image_path"] = new_path
                    scene["selected_image_path"] = new_path
                    scene["approved_image_path"] = new_path
                    scene["generated_image_path"] = new_path
                    scene["final_image_path"] = new_path
                    scene["resolved_image_path"] = new_path
                    scene["output_image_path"] = new_path
                    scenes[index] = scene
                    approved.pop(scene_id, None)
                    st.session_state[scenes_key] = scenes
                    st.session_state[approved_key] = approved
                    st.session_state[replacement_flag] = True
                    st.rerun()

    approved_count = sum(1 for scene in scenes if approved.get(str(scene.get("scene_id") or "")))
    st.progress(approved_count / max(1, len(scenes)))
    st.write(f"승인 완료: {approved_count} / {len(scenes)}")

    minimum_approved = min(8, len(scenes))
    if approved_count < minimum_approved:
        st.info(
            f"최소 {minimum_approved}장 이상 승인하면 최종 영상 제작 버튼이 활성화됩니다. "
            "승인하지 않은 장면은 최종 영상에서 제외됩니다."
        )
        return
    st.success(f"{approved_count}장 승인 완료. 승인된 장면만 사용합니다.")

    if st.button(
        "승인 이미지로 최종 영상 제작",
        type="primary",
        use_container_width=True,
        key=f"finalize_{project_id}",
    ):
        selected_paths = [
            approved[str(scene.get("scene_id") or "")]
            for scene in scenes
            if str(scene.get("scene_id") or "") in approved
        ]
        payload = st.session_state.get(f"sprint147_input_{project_id}", {})
        with st.spinner("승인된 이미지로 모션·자막·최종 영상을 제작 중입니다..."):
            final_result = run_project_pipeline(
                project=project,
                sample_count=6,
                review_text="",
                locked_script=str(payload.get("locked_script") or ""),
                review_image_paths=[],
                product_image_paths=selected_paths,
                product_image_path=selected_paths[0],
                youtube_privacy_status="private",
                viral_video_sources=[],
                declared_review_count=int(payload.get("declared_review_count") or 1),
                review_checked_at=str(payload.get("review_checked_at") or ""),
                monthly_purchase_count=int(payload.get("monthly_purchase_count") or 1),
                rating=float(payload.get("rating") or 0),
                input_product_name=str(payload.get("product_name") or ""),
                stop_after_image_generation=False,
            )
        st.session_state[result_key] = final_result
        st.session_state[f"sprint147_stage_{project_id}"] = "completed"
        st.rerun()


def show_one_click_pipeline():
    # Sprint194-6: 이전 작업 불러오기는 위젯 생성 뒤 session_state를 수정하면
    # StreamlitAPIException이 발생합니다. 클릭 시 preset을 pending으로 저장하고
    # rerun한 다음, 이 지점(어떤 위젯도 생성되기 전)에서 안전하게 복원합니다.
    pending_preset = st.session_state.pop("sprint194_6_pending_preset", None)
    _restore_intent_194_45 = st.session_state.pop("sprint194_45_restore_intent", None)
    if isinstance(pending_preset, dict) and pending_preset:
        _sprint193_29_apply_preset_to_session(pending_preset)
        # Sprint194-45: loading a Korean source project must not overwrite the user's
        # current History Cookie language choice. If English was selected before Load,
        # keep English selected after the rerun so Oliver/localized render stay active.
        if isinstance(_restore_intent_194_45, dict):
            _intent_content_194_45 = str(_restore_intent_194_45.get("content_mode") or "").strip()
            _intent_lang_194_45 = str(_restore_intent_194_45.get("history_language") or "").strip()
            if _intent_content_194_45 in {"shopping", "history"}:
                st.session_state["sprint194_25_content_mode"] = _intent_content_194_45
            if _intent_lang_194_45 in {"ko", "en"}:
                st.session_state["sprint194_25_history_language"] = _intent_lang_194_45
            print("[Sprint194-45 Previous Work Restore Intent] PRESERVED", {
                "content_mode": st.session_state.get("sprint194_25_content_mode"),
                "history_language": st.session_state.get("sprint194_25_history_language"),
                "source_preset_mode": str(pending_preset.get("production_mode") or pending_preset.get("channel_type") or "shopping"),
            }, flush=True)
        print(
            "[Sprint194-6 Previous Work Restore] APPLIED BEFORE WIDGETS",
            {
                "project_id": str(pending_preset.get("project_id") or ""),
                "production_mode": str(pending_preset.get("production_mode") or pending_preset.get("channel_type") or "shopping"),
                "clip_count": len(list(pending_preset.get("gemini_clip_paths") or [])),
                "subtitle_count": len(list(pending_preset.get("clip_subtitles") or [])),
                "narration_count": len(list(pending_preset.get("clip_narrations") or [])),
            },
            flush=True,
        )

    # Sprint194-26: English auto-localization is an explicit user intent.
    # Apply a one-shot language switch BEFORE widgets are created so a rerun cannot
    # fall back to the Korean preset value after the localization button is clicked.
    _pending_history_language = st.session_state.pop("sprint194_26_pending_history_language", "")
    if _pending_history_language in {"ko", "en"}:
        st.session_state["sprint194_25_history_language"] = _pending_history_language
        print("[Sprint194-26 History Language Intent] APPLIED", {
            "language": _pending_history_language,
            "before_widgets": True,
        }, flush=True)

    st.title("⚡ 쇼츠 원클릭")
    st.caption("쇼핑 쇼츠는 Gemini 영상을, 역사 쇼츠는 장면 이미지를 사용해 TTS·자막·BGM·효과음을 적용합니다.")
    st.caption(f"UI 버전: {UI_VERSION}")

    st.markdown("### 🎯 제작 모드")
    # Sprint194-25: keep a permanently stable widget tree.
    # The old single radio had three values (shopping/history_ko/history_en).
    # Chrome/Streamlit repeatedly hit React removeChild while swapping Korean/English.
    # Separate content type and language into two widgets that are ALWAYS rendered.
    _content_mode = st.radio(
        "쇼츠 종류",
        options=["shopping", "history"],
        format_func=lambda value: {"shopping": "🛍️ 쇼핑 쇼츠", "history": "🍪 역사쿠키"}[value],
        horizontal=True,
        key="sprint194_25_content_mode",
    )
    _history_language = st.radio(
        "역사쿠키 언어",
        options=["ko", "en"],
        format_func=lambda value: {"ko": "🇰🇷 한국어", "en": "🇺🇸 English"}[value],
        horizontal=True,
        key="sprint194_25_history_language",
    )
    is_history_mode = _content_mode == "history"
    production_mode = (f"history_{_history_language}" if is_history_mode else "shopping")
    _history_mode_info = (
        "🌍 History Cookie English: 한국어 장면을 불러온 뒤 영어 자동 현지화로 영어 자막·나레이션을 생성하고 별도 MP4를 제작합니다."
        if production_mode == "history_en"
        else (
            "🍪 역사 쇼츠 모드: 장면 이미지 1~25장 + 장면별 나레이션/자막/SFX를 넣어 최종 9:16 MP4를 제작합니다."
            if is_history_mode
            else "🛍️ 쇼핑 쇼츠 모드: 기존 쇼핑 원클릭 흐름을 그대로 사용합니다."
        )
    )
    _history_mode_caption = (
        "영어는 미국 Shorts용으로 자연스럽게 현지화하며 장면 수·순서·이미지·모션·SFX·BGM은 그대로 유지합니다."
        if production_mode == "history_en"
        else (
            "쇼핑용 리뷰·평점·상품 CTA는 사용하지 않습니다. 한국어 기본 성우는 기존 설정을 유지합니다."
            if is_history_mode
            else "역사쿠키 언어 선택은 쇼핑 모드에서는 무시됩니다."
        )
    )
    # Always render both slots so language changes update text only.
    st.info(_history_mode_info)
    st.caption(_history_mode_caption)
    print("[Sprint194-25 Stable Language State]", {
        "content_mode": _content_mode,
        "history_language": _history_language,
        "production_mode": production_mode,
        "stable_dom": True,
    }, flush=True)

    st.markdown("### 📂 이전 작업 불러오기")

    # Sprint194-75G: restore the History Cookie "latest final per video/topic" list.
    # A regression had fallen back to the generic most-recent-30 list, which could hide
    # older topics such as Sejong behind many rerenders of Taejong/elephant.
    if is_history_mode:
        _history_target_mode_194_75g = production_mode
        _history_candidates_194_75g = []

        _history_product_root_194_75g = Path("assets/products")
        if _history_product_root_194_75g.exists():
            for _preset_path_194_75g in _history_product_root_194_75g.glob("project_*/edit_preset.json"):
                try:
                    _payload_194_75g = read_json(_preset_path_194_75g, {})
                    if not isinstance(_payload_194_75g, dict) or not _payload_194_75g:
                        continue

                    _mode_194_75g = str(
                        _payload_194_75g.get("production_mode")
                        or _payload_194_75g.get("channel_type")
                        or ""
                    ).strip().lower()
                    if _mode_194_75g not in {"history_ko", "history_en"}:
                        continue

                    # Sprint194-75GC source-list policy:
                    # - Korean production: show Korean latest finals only.
                    # - English production: show BOTH English latest finals and
                    #   Korean latest finals, because a Korean final is a valid
                    #   source project for creating/localizing the English version.
                    if _history_target_mode_194_75g == "history_ko":
                        if _mode_194_75g != "history_ko":
                            continue
                    elif _history_target_mode_194_75g == "history_en":
                        if _mode_194_75g not in {"history_en", "history_ko"}:
                            continue
                    else:
                        continue

                    _pid_194_75g = str(
                        _payload_194_75g.get("project_id")
                        or _preset_path_194_75g.parent.name.replace("project_", "")
                    ).strip()
                    _name_194_75g = str(
                        _payload_194_75g.get("product_name")
                        or _payload_194_75g.get("title")
                        or f"프로젝트 {_pid_194_75g}"
                    ).strip()

                    _clips_194_75g = [
                        str(x or "").strip()
                        for x in list(_payload_194_75g.get("gemini_clip_paths") or [])
                        if str(x or "").strip()
                    ]
                    if not _clips_194_75g:
                        _clip_dir_194_75g = Path("assets/gemini_clips") / f"project_{_pid_194_75g}"
                        if _clip_dir_194_75g.exists():
                            _clips_194_75g = [
                                str(p) for p in _clip_dir_194_75g.iterdir()
                                if p.is_file() and p.suffix.lower() in SUPPORTED_VIRAL_VIDEO_SUFFIXES
                            ]
                    if not _clips_194_75g:
                        continue

                    _history_candidates_194_75g.append({
                        "path": str(_preset_path_194_75g),
                        "project_id": _pid_194_75g,
                        "product_name": _name_194_75g,
                        "saved_at": str(_payload_194_75g.get("saved_at") or ""),
                        "mtime": float(_preset_path_194_75g.stat().st_mtime),
                        "clip_count": len(_clips_194_75g),
                        "recovered": False,
                        "history_language": "en" if _mode_194_75g == "history_en" else "ko",
                    })
                except Exception as _history_index_exc_194_75g:
                    print("[Sprint194-75G History Latest Index] SKIP", {
                        "path": str(_preset_path_194_75g),
                        "error": f"{type(_history_index_exc_194_75g).__name__}: {_history_index_exc_194_75g}",
                    }, flush=True)

        # One row per video/topic: normalize only UI/version prefixes and whitespace;
        # the newest project for the same title wins.
        def _history_topic_key_194_75g(_name):
            _key = str(_name or "").strip().casefold()
            _key = re.sub(r"^\[(?:역사쿠키|history\s*cookie)\s*/\s*(?:한글|한국어|영어|ko|en)\]\s*", "", _key)
            _key = re.sub(r"^\[(?:한글|한국어|영어|ko|en)\]\s*", "", _key)
            _key = re.sub(r"\s+", " ", _key).strip()
            return _key

        _history_candidates_194_75g.sort(
            key=lambda x: (float(x.get("mtime") or 0.0), int(str(x.get("project_id") or "0")) if str(x.get("project_id") or "").isdigit() else 0),
            reverse=True,
        )
        _latest_by_topic_194_75g = {}
        for _item_194_75g in _history_candidates_194_75g:
            _topic_key_194_75g = _history_topic_key_194_75g(_item_194_75g.get("product_name"))
            # Sprint194-75GC: in English mode, preserve one latest KO row and
            # one latest EN row independently for the same topic.
            _language_key_194_75gc = str(_item_194_75g.get("history_language") or "").lower()
            _dedup_key_194_75gc = (
                f"{_language_key_194_75gc}::{_topic_key_194_75g}"
                if _history_target_mode_194_75g == "history_en"
                else _topic_key_194_75g
            )
            if _topic_key_194_75g and _dedup_key_194_75gc not in _latest_by_topic_194_75g:
                _latest_by_topic_194_75g[_dedup_key_194_75gc] = _item_194_75g

        recent_presets = list(_latest_by_topic_194_75g.values())
        print("[Sprint194-75G History Previous Work Latest Final] READY", {
            "production_mode": production_mode,
            "source_language_policy": "ko-only" if production_mode == "history_ko" else "en+ko",
            "candidate_count": len(_history_candidates_194_75g),
            "visible_count": len(recent_presets),
            "visible": [
                {
                    "project_id": str(x.get("project_id") or ""),
                    "product_name": str(x.get("product_name") or ""),
                }
                for x in recent_presets
            ],
        }, flush=True)
    else:
        recent_presets = _sprint193_29_recent_edit_presets(limit=30)

    if recent_presets:
        preset_options = ["선택 안 함"] + [
            (
                (
                    ("[영어] " if str(item.get("history_language") or "").lower() == "en" else "[한글] ")
                    if is_history_mode else ""
                )
                + f"{item['product_name']} · 프로젝트 {item['project_id']} · 영상 {item['clip_count']}개"
                + (" · 기존작업 복구" if item.get("recovered") else "")
            )
            for item in recent_presets
        ]
        preset_choice = st.selectbox(
            "최근 작업",
            options=preset_options,
            key="sprint193_29_preset_choice",
        )
        load_col, clear_col = st.columns([1, 1])
        with load_col:
            load_preset_clicked = st.button(
                "📥 설정 불러오기",
                use_container_width=True,
                key="sprint193_29_load_preset",
            )
        with clear_col:
            clear_preset_clicked = st.button(
                "새 작업으로 초기화",
                use_container_width=True,
                key="sprint193_29_clear_preset",
            )

        if load_preset_clicked:
            if preset_choice == "선택 안 함":
                st.warning("불러올 이전 작업을 선택해 주세요.")
            else:
                selected_index = preset_options.index(preset_choice) - 1
                selected_meta = recent_presets[selected_index]
                if selected_meta.get("recovered"):
                    preset = dict(selected_meta.get("legacy_payload") or {})
                    if preset:
                        target = (
                            Path("assets/products")
                            / f"project_{selected_meta['project_id']}"
                            / "edit_preset.json"
                        )
                        target.parent.mkdir(parents=True, exist_ok=True)
                        preset["version"] = "edit-preset-193-29-recovered"
                        preset["saved_at"] = datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
                        write_json(target, preset)
                        preset["_preset_path"] = str(target)
                        selected_meta["path"] = str(target)
                        print(
                            "[Sprint193-29 Legacy Preset] CONVERTED",
                            {
                                "project_id": selected_meta["project_id"],
                                "path": str(target),
                                "clip_count": len(list(preset.get("gemini_clip_paths") or [])),
                            },
                            flush=True,
                        )
                else:
                    preset = read_json(selected_meta["path"], {})

                if isinstance(preset, dict) and preset:
                    preset["_preset_path"] = str(selected_meta.get("path") or "")
                    # Sprint194-6: 현재 run에서 제작 모드 위젯이 이미 만들어졌으므로
                    # 여기서 직접 session_state를 수정하지 않습니다. 다음 rerun 시작 전에 적용합니다.
                    st.session_state["sprint194_6_pending_preset"] = dict(preset)
                    # Sprint194-45: remember what the user selected BEFORE loading.
                    # The source preset can be Korean while the requested output is English.
                    st.session_state["sprint194_45_restore_intent"] = {
                        "content_mode": str(_content_mode or ""),
                        "history_language": str(_history_language or ""),
                    }
                    st.session_state["sprint193_29_preset_loaded_notice"] = (
                        f"{selected_meta['product_name']} 설정을 불러왔습니다."
                    )
                    print(
                        "[Sprint194-6 Previous Work Restore] QUEUED",
                        {
                            "path": selected_meta.get("path"),
                            "project_id": selected_meta["project_id"],
                            "clip_count": selected_meta["clip_count"],
                            "production_mode": str(preset.get("production_mode") or preset.get("channel_type") or "shopping"),
                            "legacy_recovered": bool(selected_meta.get("recovered")),
                        },
                        flush=True,
                    )
                    st.rerun()
                else:
                    st.error("이전 작업 설정 파일을 읽지 못했습니다.")

        if clear_preset_clicked:
            keys_to_clear = [
                key for key in list(st.session_state.keys())
                if key.startswith("sprint193_9_clip_")
                or key.startswith("sprint193_14_clip_speed_")
                or key in {
                    "sprint193_29_loaded_clip_paths",
                    "sprint193_29_loaded_preset_path",
                    "sprint193_29_loaded_project_id",
                    "sprint194_6_pending_preset",
                }
            ]
            for key in keys_to_clear:
                st.session_state.pop(key, None)
            st.session_state["sprint193_29_preset_loaded_notice"] = ""
            st.rerun()
    else:
        st.caption("아직 저장된 이전 원클릭 작업이 없습니다.")

    loaded_notice = str(st.session_state.pop("sprint193_29_preset_loaded_notice", "") or "")
    if loaded_notice:
        st.success(loaded_notice)
    st.markdown("""<style>.block-container{max-width:1500px;padding-top:1rem}.exact-title{text-align:center;font-size:20px;font-weight:800;border:1px solid #222;padding:7px}.mini-grid{border:1px solid #222;padding:6px;text-align:center;font-size:12px;background:#fafafa}</style>""",unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="exact-title">영상만 제작</div>', unsafe_allow_html=True)
    top_create_slot = st.empty()

    st.markdown(
        ("""<div class="mini-grid">역사 주제 │ 캐릭터 기준이미지 │ 장면이미지 │ 오디오 │ BGM │ 자막 │ 나레이션 │ 자막효과 │ 사운드효과 │ 장면속도</div><div class="mini-grid">역사 장면 이미지 최대 25장 · 이미지 → 9:16 영상 자동 변환 · 장면별 자막/나레이션/SFX/속도 편집</div>"""
         if is_history_mode else
         """<div class="mini-grid">상품명 │ 평점 │ 리뷰수 │ 대표이미지 │ 오디오 │ BGM │ 자막 │ 나레이션 │ 자막효과 │ 사운드효과 │ 장면속도</div><div class="mini-grid">Gemini 영상 수동 업로드 1~10 · 영상별 자막 / 나레이션 / 자막효과 / 사운드효과 한 줄 편집</div>"""),
        unsafe_allow_html=True,
    )

    product_name = st.text_input(
        "역사 주제" if is_history_mode else "상품명",
        placeholder=("예: 조선 코끼리 유배 사건" if is_history_mode else "예: 미끄럼 방지 EVA 욕실화"),
        key="sprint172_product_name",
    )
    # Sprint191-4: 별도 후킹 입력란 제거.
    # 첫 장면 후킹은 아래 신뢰 정보(구매수/평점/리뷰수)로 고정합니다.
    # Sprint193-7: 별도 확정 대본 입력란은 제거합니다.
    # 영상별 나레이션을 순서대로 합쳐 내부 locked_script로 사용합니다.
    hook_text = ""
    locked_script = ""

    # Sprint190-6: 영상 제작 버튼이 플랫폼별 입력 UI보다 먼저 실행돼도
    # platform_metadata 참조 오류가 발생하지 않도록 선초기화합니다.
    platform_metadata = {
        "youtube": {"title": "", "description": ""},
        "instagram": {"title": "", "description": ""},
        "tiktok": {"title": "", "description": ""},
        "naver_clip": {"title": "", "description": ""},
        "threads": {"title": "", "description": ""},
    }
    # Sprint193-14: 영상 CTA 완전 제거.
    cta_keyword = ""
    video_cta_platform = "none"
    cta_text = ""

    st.markdown("#### 기준 이미지 (선택)" if is_history_mode else "#### 제품 대표이미지")
    hook_product_image = st.file_uploader(
        "역사 캐릭터/대표 이미지 (선택)" if is_history_mode else "제품 대표 이미지 (선택)",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=False,
        key="sprint189_hook_product_image",
        help="첫 신뢰 후킹 장면의 제품 배경으로 사용합니다. 후킹 배경의 실제 표시 강도는 영상 파이프라인에서 적용됩니다.",
    )
    st.caption("이 이미지는 캐릭터 일관성 기준용입니다. 실제 영상 장면은 아래 역사 장면 이미지에서 선택합니다." if is_history_mode else "대표 이미지를 올리지 않으면 첫 Gemini 영상 프레임을 자동으로 사용합니다.")

    # Sprint193-8: 최근 한 달 구매수 입력은 제거합니다.
    # 현재 쇼핑 후킹은 리뷰수 + 평점 기준으로 고정합니다.
    monthly_purchase_count = 0
    if is_history_mode:
        declared_review_count = 0
        rating = 0.0
        st.caption("역사 모드에서는 쇼핑용 평점·리뷰 신뢰 후킹을 사용하지 않습니다.")
    else:
        st.markdown("#### 평점 · 리뷰수")
        trust_c1, trust_c2 = st.columns(2)
        with trust_c1:
            rating = st.number_input(
                "평점", min_value=0.0, max_value=5.0, value=4.8, step=0.1,
                format="%.1f", key="sprint178_rating",
            )
        with trust_c2:
            declared_review_count = st.number_input(
                "리뷰 수", min_value=0, value=0, step=1,
                key="sprint178_declared_review_count",
            )

    # Sprint193-4: 구매수 유무에 따라 신뢰 후킹 문구를 자동 분기합니다.
    # 구매수가 없으면 리뷰 수를 첫 줄에 배치하고, 평점은 질문형으로 연결합니다.
    if int(monthly_purchase_count or 0) > 0:
        hook_lines = [f"최근 한 달 {int(monthly_purchase_count):,}명 이상 구매!"]
        if float(rating or 0) > 0:
            hook_lines.append(f"평점 {float(rating):.2f}점!")
        if int(declared_review_count or 0) > 0:
            hook_lines.append(f"리뷰 {int(declared_review_count):,}개!")
    else:
        hook_lines = []
        if int(declared_review_count or 0) > 0:
            hook_lines.append(f"리뷰 {int(declared_review_count):,}개!")
        if float(rating or 0) > 0:
            hook_lines.append(f"평점도 {float(rating):.2f}점?")

    auto_hook_text = "\n".join(hook_lines).strip()
    if auto_hook_text:
        st.markdown("**신뢰 후킹 미리보기**")
        st.info(auto_hook_text)

    hook_text = st.text_area(
        "역사 후킹멘트" if is_history_mode else "후킹멘트",
        height=78,
        placeholder=(
            "예: 조선시대에 코끼리가 유배를 갔다?!"
            if is_history_mode
            else "예: 양치할 때 아직도 손으로 물 받아 쓰세요?"
        ),
        key="sprint193_9_hook_phrase",
        help=(
            "구독 요청이 아니라, 사건에서 가장 궁금한 사실을 첫 문장으로 넣습니다."
            if is_history_mode
            else "신뢰 후킹 다음, 첫 Gemini 영상 시작 시 표시·나레이션될 후킹 문장입니다."
        ),
    )

    st.markdown("#### 성우 · 오디오 · BGM")
    st.caption("Typecast API 키가 있으면 선택한 성우로 자동 나레이션을 생성합니다. 직접 만든 음성 파일을 올리면 업로드 파일을 우선 사용합니다.")

    @st.cache_data(ttl=3600, show_spinner=False)
    def _typecast_voice_choices(api_key=""):
        resolved_key = str(api_key or "").strip()
        if not resolved_key:
            return []
        try:
            from typecast import Typecast
            client = Typecast(api_key=resolved_key)
            raw_voices = list(client.voices_v2() or [])
            parsed, seen = [], set()
            for voice in raw_voices:
                if isinstance(voice, dict):
                    name = str(voice.get("voice_name") or voice.get("name") or voice.get("display_name") or "").strip()
                    vid = str(voice.get("voice_id") or voice.get("id") or "").strip()
                else:
                    name = str(getattr(voice, "voice_name", "") or getattr(voice, "name", "") or getattr(voice, "display_name", "") or "").strip()
                    vid = str(getattr(voice, "voice_id", "") or getattr(voice, "id", "") or "").strip()
                if name and vid and (name, vid) not in seen:
                    seen.add((name, vid))
                    parsed.append((name, vid))
            parsed.sort(key=lambda item: (0 if item[0] == "지안" else 1 if item[0] == "서연" else 2, item[0]))
            print("[Sprint193-19 Typecast Voices]", {"raw": len(raw_voices), "parsed": len(parsed)}, flush=True)
            return parsed
        except Exception as exc:
            print("[Sprint193-19 Typecast Voices] ERROR", type(exc).__name__, str(exc), flush=True)
            return []

    _saved_typecast = TypecastSettingsStore.load()
    _saved_typecast_key = str(_saved_typecast.get("api_key") or "").strip()

    with st.expander("⚙ Typecast API 설정", expanded=not bool(_saved_typecast_key)):
        _typecast_key_input = st.text_input(
            "Typecast API Key",
            value=_saved_typecast_key,
            type="password",
            key="sprint193_16_typecast_api_key_saved",
            help="한 번 저장하면 다음 실행부터 자동으로 사용합니다.",
        )
        if st.button("Typecast API Key 저장", key="sprint193_16_save_typecast_key"):
            TypecastSettingsStore.save({
                "api_key": str(_typecast_key_input or "").strip(),
                "last_voice_name": str(_saved_typecast.get("last_voice_name") or "지안"),
                "last_voice_id": str(_saved_typecast.get("last_voice_id") or ""),
            })
            st.cache_data.clear()
            st.success("Typecast API Key 저장 완료")
            st.rerun()

    typecast_api_key = _saved_typecast_key
    if typecast_api_key:
        os.environ["TYPECAST_API_KEY"] = typecast_api_key
        st.caption("Typecast API Key 저장됨 · 자동 사용")

    _voice_choices = _typecast_voice_choices(typecast_api_key)
    _voice_labels = [name for name, _ in _voice_choices]

    # Sprint194-22: History Cookie English uses Oliver as the channel voice.
    # Typecast may expose the display name as Aaron / 에런 / 애런, so resolve by name
    # from the already-authenticated voices_v2() list and keep the actual voice_id.
    def _sprint194_41_find_oliver_voice(choices):
        aliases = ("oliver", "올리버")
        normalized = []
        for _name, _vid in list(choices or []):
            _label = str(_name or "").strip()
            _low = _label.casefold()
            _rank = None
            if _low in aliases:
                _rank = 0
            elif any(_alias in _low for _alias in aliases):
                _rank = 1
            if _rank is not None and str(_vid or "").strip():
                normalized.append((_rank, _label, str(_vid).strip()))
        normalized.sort(key=lambda row: (row[0], len(row[1]), row[1]))
        return (normalized[0][1], normalized[0][2]) if normalized else ("", "")

    _oliver_voice_name, _oliver_voice_id = _sprint194_41_find_oliver_voice(_voice_choices)
    # Sprint194-23: never mutate the selectbox's saved/default value merely because the
    # language radio changed.  Oliver is applied only to the internal English TTS values
    # after the stable voice widget has been rendered.
    _saved_voice_name = str(_saved_typecast.get("last_voice_name") or "지안")

    # Sprint194-75D: when a Korean History project was restored, its project voice
    # must win over the global Typecast last_voice (which may still be Oliver from
    # the immediately preceding English project).
    _restored_ko_voice_name_194_75d = ""
    if production_mode == "history_ko":
        for _voice_state_key_194_75d in (
            "sprint194_71_restored_voice_name",
            "sprint194_6_restored_voice_name",
            "sprint193_19_voice_select",
        ):
            _candidate_194_75d = str(st.session_state.get(_voice_state_key_194_75d) or "").strip()
            if _candidate_194_75d and _candidate_194_75d.casefold() not in {"oliver", "올리버"}:
                _restored_ko_voice_name_194_75d = _candidate_194_75d
                break
        # The lightweight restore already places the project voice into the stable
        # widget/session path. Prefer that value when it is present in Typecast.
        if _restored_ko_voice_name_194_75d in _voice_labels:
            _saved_voice_name = _restored_ko_voice_name_194_75d
        elif "Junho" in _voice_labels and str(st.session_state.get("sprint193_19_voice_select") or "").strip() == "Junho":
            _saved_voice_name = "Junho"
            _restored_ko_voice_name_194_75d = "Junho"
    if production_mode == "history_en" and _oliver_voice_name and _oliver_voice_id:
        print("[Sprint194-23 English Stable Voice] FOUND", {
            "voice_name": _oliver_voice_name,
            "voice_id_present": True,
            "voice_count": len(_voice_choices),
            "widget_value_preserved": True,
        }, flush=True)
    elif production_mode == "history_en":
        print("[Sprint194-23 English Stable Voice] NOT_FOUND", {
            "aliases": ["Oliver", "올리버"],
            "voice_count": len(_voice_choices),
            "widget_value_preserved": True,
        }, flush=True)
    # Sprint194-75E: seed the stable voice widget BEFORE it is instantiated.
    # This is the safe Streamlit pattern and avoids StreamlitAPIException.
    if (
        production_mode == "history_ko"
        and _restored_ko_voice_name_194_75d
        and _restored_ko_voice_name_194_75d in _voice_labels
    ):
        _current_widget_seed_194_75e = str(
            st.session_state.get("sprint193_19_voice_select") or ""
        ).strip()
        if _current_widget_seed_194_75e != _restored_ko_voice_name_194_75d:
            st.session_state["sprint193_19_voice_select"] = _restored_ko_voice_name_194_75d
        _saved_voice_name = _restored_ko_voice_name_194_75d
        print("[Sprint194-75E History KO Voice PreWidget Lock] READY", {
            "production_mode": production_mode,
            "voice_name": _restored_ko_voice_name_194_75d,
            "widget_seeded_before_creation": True,
        }, flush=True)

    _default_voice_index = (
        _voice_labels.index(_saved_voice_name)
        if _saved_voice_name in _voice_labels
        else next((i for i, name in enumerate(_voice_labels) if name == "지안"), 0)
    )

    if _voice_labels:
        voice_search_text = st.text_input(
            "🔎 Typecast 성우 검색",
            value="",
            placeholder="예: 지안, 서연",
            key="sprint193_19_voice_search_text",
        )
        _needle = str(voice_search_text or "").strip().lower()
        _filtered_voice_labels = [name for name in _voice_labels if _needle in name.lower()] if _needle else list(_voice_labels)
        if not _filtered_voice_labels:
            st.warning("검색 결과가 없습니다.")
            _filtered_voice_labels = list(_voice_labels)
        _filtered_default_index = _filtered_voice_labels.index(_saved_voice_name) if _saved_voice_name in _filtered_voice_labels else 0
        selected_voice_name = st.selectbox(
            "Typecast 성우 선택",
            options=_filtered_voice_labels,
            index=_filtered_default_index,
            key="sprint193_19_voice_select",
        )
        _widget_voice_name = selected_voice_name
        _widget_voice_id = dict(_voice_choices).get(_widget_voice_name, "")
        selected_voice_id = _widget_voice_id
        _auto_voice_message = "현재 선택 성우를 사용합니다."
        if production_mode == "history_en" and _oliver_voice_name and _oliver_voice_id:
            selected_voice_name = _oliver_voice_name
            selected_voice_id = _oliver_voice_id
            _auto_voice_message = f"🌍 English 자동 성우: {selected_voice_name} · Typecast voice_id 자동 적용"
        elif production_mode == "history_en" and typecast_api_key:
            _auto_voice_message = "🌍 올리버 자동 검색 실패 · 현재 선택 성우를 영어 TTS에 사용합니다."
        elif production_mode == "history_ko":
            # Sprint194-75D: never allow stale English Oliver to become the Korean
            # render voice after a Korean project restore.
            _ko_effective_name_194_75d = str(
                _restored_ko_voice_name_194_75d or _widget_voice_name or _saved_voice_name
            ).strip()
            if _ko_effective_name_194_75d.casefold() in {"oliver", "올리버"}:
                if "Junho" in _voice_labels:
                    _ko_effective_name_194_75d = "Junho"
                else:
                    _ko_effective_name_194_75d = next(
                        (n for n in _voice_labels if str(n).casefold() not in {"oliver", "올리버"}),
                        _widget_voice_name,
                    )
            selected_voice_name = _ko_effective_name_194_75d
            selected_voice_id = dict(_voice_choices).get(selected_voice_name, _widget_voice_id)
            _widget_voice_name = selected_voice_name
            _widget_voice_id = selected_voice_id
            _auto_voice_message = f"🍪 한국어 성우: {selected_voice_name}"
            print("[Sprint194-75E History KO Voice Lock] READY", {
                "production_mode": production_mode,
                "restored_voice": _restored_ko_voice_name_194_75d,
                "effective_voice": selected_voice_name,
                "oliver_blocked": str(selected_voice_name or "").casefold() not in {"oliver", "올리버"},
                "voice_id_present": bool(selected_voice_id),
            }, flush=True)
        st.caption(_auto_voice_message)

        # Persist only what the user chose in the stable widget.  Do not overwrite the
        # Korean saved voice with Oliver just because English mode was viewed.
        if _widget_voice_name != _saved_voice_name or _widget_voice_id != str(_saved_typecast.get("last_voice_id") or ""):
            TypecastSettingsStore.save({
                "api_key": typecast_api_key,
                "last_voice_name": _widget_voice_name,
                "last_voice_id": _widget_voice_id,
            })
    else:
        selected_voice_name = _saved_voice_name
        selected_voice_id = str(_saved_typecast.get("last_voice_id") or "")
        if typecast_api_key:
            st.warning("Typecast 보이스 목록을 불러오지 못했습니다.")

    if production_mode == "history_ko" and str(selected_voice_name or "").strip().casefold() in {"oliver", "올리버"}:
        raise RuntimeError("history_ko_voice_guard_blocked_oliver")
    if production_mode == "history_ko":
        print("[Sprint194-75E History KO Render Voice Guard] READY", {
            "voice_name": selected_voice_name,
            "voice_id_present": bool(selected_voice_id),
            "guard": "oliver-forbidden-in-history-ko",
        }, flush=True)

    print("[Sprint193-19 Typecast]", {
        "api_key_present": bool(typecast_api_key),
        "voice_name": selected_voice_name,
        "voice_id_present": bool(selected_voice_id),
        "voice_count": len(_voice_choices),
    }, flush=True)
    if production_mode == "history_en":
        print("[Sprint194-45 English Voice Lock]", {
            "production_mode": production_mode,
            "voice_name": selected_voice_name,
            "is_oliver": str(selected_voice_name or "").strip().casefold() in {"oliver", "올리버"},
            "voice_id_present": bool(selected_voice_id),
        }, flush=True)

    uploaded_voice_audio = st.file_uploader(
        "TTS 음성 파일 직접 업로드 (선택)",
        type=["mp3", "wav", "m4a", "aac"],
        accept_multiple_files=False,
        key="sprint173_voice_audio",
    )
    uploaded_bgm_audio = st.file_uploader(
        "BGM 파일 (선택)",
        type=["mp3", "wav", "m4a", "aac"],
        accept_multiple_files=False,
        key="sprint173_bgm_audio",
    )

    audio_c1, audio_c2, audio_c3 = st.columns(3)
    with audio_c1:
        tts_volume_percent = st.slider(
            "TTS 볼륨",
            min_value=0,
            max_value=200,
            value=100,
            step=5,
            format="%d%%",
            key="sprint193_1_tts_volume",
            help="기본값 100%. 현재 영상 제작 파이프라인의 기본 음량을 유지하면서 운영값을 저장합니다.",
        )
    with audio_c2:
        tts_speech_speed = st.slider(
            "TTS 말하기 속도",
            min_value=0.5,
            max_value=2.0,
            value=1.0,
            step=0.1,
            format="%.1f배",
            key="sprint193_1_tts_speed",
        )
    # Sprint194-41: English History Cookie uses a slightly brisker Oliver delivery.
    # The visible/saved slider and Korean voice speed remain untouched.
    _effective_tts_speech_speed_194_41 = (
        max(1.1, float(tts_speech_speed or 1.0)) if production_mode == "history_en"
        else float(tts_speech_speed or 1.0)
    )
    if production_mode == "history_en":
        print("[Sprint194-41 English Oliver Voice] READY", {
            "voice_name": selected_voice_name,
            "speed": _effective_tts_speech_speed_194_41,
            "korean_setting_untouched": True,
        }, flush=True)

    with audio_c3:
        bgm_volume_percent = st.slider(
            "BGM 볼륨",
            min_value=0,
            max_value=100,
            value=10,
            step=5,
            format="%d%%",
            key="sprint193_1_bgm_volume",
        )

    uploaded_history_scene_images = []
    uploaded_history_scene1_video = None
    uploaded_gemini_clips = []
    history_expected_scene_count = 0
    if is_history_mode:
        st.info("🎨 역사쿠키 스타일 고정: 귀엽고 친근한 2D 웹툰·카툰 캐릭터 / 동글동글한 형태 / 풍부한 표정 / 실사풍 3D 제외")
        st.markdown("#### 역사 장면 이미지 업로드 · 최대 25장")
        uploaded_history_scene1_video = st.file_uploader(
            "1번 장면 영상 (선택 · MP4/MOV)",
            type=["mp4", "mov", "mkv", "webm", "m4v"],
            accept_multiple_files=False,
            key="sprint194_47_history_scene1_video",
            help="선택하면 1번 장면 이미지는 기준/편집용으로 유지하고, 최종 영상의 1번 장면만 이 영상으로 교체합니다. 영상 자체의 오디오는 제거됩니다.",
        )
        if uploaded_history_scene1_video is not None:
            st.success(f"1번 장면 영상 적용: {uploaded_history_scene1_video.name} · 원본 프레임 유지, 오디오 제거")
        history_expected_scene_count = st.number_input(
            "이번 영상의 장면 수", min_value=1, max_value=25, value=17, step=1,
            key="sprint194_5_expected_history_scene_count",
            help="17컷 영상이면 17로 두세요. 업로드 감지 수와 다르면 제작 전에 누락 파일을 알려드립니다.",
        )
        primary_history_images = st.file_uploader(
            "편집 순서대로 장면 이미지 선택",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
            key="sprint194_2_history_scene_images",
            help="1.png~17.png처럼 번호를 붙이면 자동으로 숫자 순서로 정렬합니다.",
        )
        extra_history_images = st.file_uploader(
            "누락 이미지 추가 (선택)",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
            key="sprint194_5_history_scene_images_extra",
            help="선택했는데 감지되지 않은 이미지가 있을 때 해당 파일만 추가하세요. 같은 파일명은 최신 선택으로 교체합니다.",
        )
        uploaded_history_scene_images = _sprint194_5_merge_history_uploads(
            primary_history_images, extra_history_images
        )
        history_scene_count = len(uploaded_history_scene_images)
        if history_scene_count:
            detected_names = [str(getattr(item, "name", "") or "") for item in uploaded_history_scene_images]
            st.write(f"**업로드 감지: {history_scene_count}장 / 목표: {int(history_expected_scene_count)}장**")
            st.caption("감지 파일: " + ", ".join(detected_names))
            numeric_ids = []
            for name in detected_names:
                match = re.search(r"(\d+)", Path(name).stem)
                if match:
                    numeric_ids.append(int(match.group(1)))
            expected_ids = set(range(1, int(history_expected_scene_count) + 1))
            detected_id_set = set(numeric_ids)
            scene1_video_replaces_missing_image = bool(uploaded_history_scene1_video is not None and 1 not in detected_id_set)
            effective_scene_count = history_scene_count + (1 if scene1_video_replaces_missing_image else 0)
            covered_ids = detected_id_set | ({1} if scene1_video_replaces_missing_image else set())
            missing_ids = sorted(expected_ids - covered_ids) if numeric_ids else []
            if effective_scene_count == int(history_expected_scene_count) and not missing_ids:
                if scene1_video_replaces_missing_image:
                    st.success(f"1번 영상 + 역사 장면 이미지 {history_scene_count}장 감지 → 총 {effective_scene_count}장면 정상입니다.")
                else:
                    st.success(f"역사 장면 이미지 {history_scene_count}장 감지 → 편집창 {history_scene_count}개를 1:1로 생성합니다.")
            else:
                missing_text = f" 누락 번호: {', '.join(map(str, missing_ids))}" if missing_ids else ""
                st.error(
                    f"선택한 장면 수와 감지 수가 다릅니다. 목표 {int(history_expected_scene_count)}장 / 유효 장면 {effective_scene_count}장 (이미지 {history_scene_count}장).{missing_text}"
                )
            print(
                "[Sprint194-5 History Upload Count]",
                {"expected": int(history_expected_scene_count), "detected": history_scene_count, "files": detected_names, "missing": missing_ids},
                flush=True,
            )
    else:
        st.markdown("#### Gemini 영상수동업로드 · 1~10")
        uploaded_gemini_clips = st.file_uploader(
            "편집 순서대로 영상 선택",
            type=["mp4", "mov", "mkv", "webm", "m4v"],
            accept_multiple_files=True,
            key="sprint172_gemini_clips",
        )

    loaded_gemini_clip_paths = [
        str(item or "").strip()
        for item in list(st.session_state.get("sprint193_29_loaded_clip_paths") or [])
        if str(item or "").strip() and Path(str(item)).is_file()
    ]
    if is_history_mode:
        _history_editor_images = list(uploaded_history_scene_images or [])
        _history_image_ids = []
        for _item in _history_editor_images:
            _name = str(getattr(_item, "name", "") or "")
            _match = re.search(r"(\d+)", Path(_name).stem)
            if _match:
                _history_image_ids.append(int(_match.group(1)))
        _scene1_video_is_source = bool(uploaded_history_scene1_video is not None)

        # Sprint194-47C: Scene 1 video must replace only Scene 1, never collapse
        # an already-loaded 17-scene project down to one row.
        # Priority:
        #   A) newly uploaded 2..N images -> [scene1 video] + those images
        #   B) no new images but previous project clips exist -> replace loaded scene 1 only
        #   C) no scene1 video -> normal image/upload/loaded behavior
        if _scene1_video_is_source and _history_editor_images:
            _images_without_scene1_194_47c = []
            for _img in _history_editor_images:
                _nm = str(getattr(_img, "name", "") or "")
                _m = re.search(r"(\d+)", Path(_nm).stem)
                if _m and int(_m.group(1)) == 1:
                    continue
                _images_without_scene1_194_47c.append(_img)
            newly_uploaded_sources = [uploaded_history_scene1_video] + _images_without_scene1_194_47c
        elif _scene1_video_is_source and loaded_gemini_clip_paths:
            editor_clip_sources = [uploaded_history_scene1_video] + list(loaded_gemini_clip_paths[1:])
            newly_uploaded_sources = []
            st.caption(
                f"1번 영상만 교체하고 이전 작업의 2~{len(editor_clip_sources)}번 장면을 그대로 유지합니다."
            )
            print("[Sprint194-47C History Scene1 Merge] LOADED_ROWS_PRESERVED", {
                "scene1_video": True,
                "loaded_before": len(loaded_gemini_clip_paths),
                "editor_after": len(editor_clip_sources),
            }, flush=True)
        else:
            newly_uploaded_sources = list(_history_editor_images)
    else:
        newly_uploaded_sources = list(uploaded_gemini_clips or [])

    if newly_uploaded_sources:
        editor_clip_sources = list(newly_uploaded_sources)
        loaded_gemini_clip_paths = []
        st.session_state["sprint193_29_loaded_clip_paths"] = []
        st.caption(
            "새로 업로드한 장면 소스 순서대로 연결합니다. 1번 영상은 Scene 1만 교체하고 나머지 장면은 그대로 유지합니다."
            if is_history_mode
            else "새로 업로드한 영상 목록의 순서대로 연결합니다. 기존 불러온 영상 대신 새 영상을 사용합니다."
        )
    elif not (is_history_mode and _scene1_video_is_source and loaded_gemini_clip_paths):
        editor_clip_sources = list(loaded_gemini_clip_paths)
        if loaded_gemini_clip_paths:
            st.success(
                f"이전 작업의 역사 장면 영상 {len(loaded_gemini_clip_paths)}개를 다시 사용합니다."
                if is_history_mode
                else f"이전 작업의 Gemini 영상 {len(loaded_gemini_clip_paths)}개를 다시 사용합니다. 영상 재업로드가 필요 없습니다."
            )
        else:
            st.caption(
                "장면 이미지를 1장 이상 선택하세요. 이미지 자체에는 자막을 넣지 않고 원클릭에서 자막을 합성합니다."
                if is_history_mode
                else "업로드 목록의 순서대로 연결합니다. Gemini 영상의 기존 BGM과 음향은 자동 제거됩니다."
            )

    clip_subtitles = []
    clip_narrations = []
    clip_subtitle_effects = []
    clip_sfx = []
    clip_playback_speeds = []
    subtitle_style = {
        "font": "Gmarket Sans Bold",
        "font_size": 76,
        "outline": 6,
        "text_color": "#FFFFFF",
        "background_color": "#000000",
        "background_opacity": 10,
        "highlight_color": "#FFD700",
    }
    if editor_clip_sources:
        st.markdown("#### 장면별 편집" if is_history_mode else "#### 영상별 편집")
        st.caption(
            ("장면마다 한 줄에서 자막 · 나레이션 · 자막효과 · 사운드효과를 바로 입력합니다. "
             "입력한 나레이션을 장면 순서대로 합쳐 확정 대본으로 사용합니다.")
            if is_history_mode else
            ("영상마다 한 줄에서 자막 · 나레이션 · 자막효과 · 사운드효과를 바로 입력합니다. "
             "확정 대본이 비어 있으면 입력한 나레이션을 영상 순서대로 합쳐 사용합니다.")
        )

        # Sprint194-23: render the same localization controls in both history languages.
        # Korean mode keeps the button disabled; switching to English changes props/text
        # only, not the surrounding DOM tree.
        if is_history_mode:
            st.markdown("#### 🌍 영어 자동 현지화")
            _localize_enabled = production_mode == "history_en"
            st.caption(
                "한국어판을 불러온 상태에서 누르면 같은 장면 수로 영어 Shorts 자막·나레이션을 자동 생성합니다."
                if _localize_enabled
                else "영어 모드로 전환하면 현재 한국어 장면을 자동 현지화할 수 있습니다."
            )
            _saved_openai_localization_key = _sprint194_28_load_openai_localization_key()
            _openai_localization_key = st.text_input(
                "OpenAI API Key · 영어 현지화 1순위",
                value=_saved_openai_localization_key,
                type="password",
                key="sprint194_28_openai_localization_key",
                help="한 번 저장하면 영어 역사쿠키 자동 현지화에 재사용합니다. 키가 없으면 Gemini fallback을 사용합니다.",
            )
            _key_c1, _key_c2 = st.columns([1, 2])
            with _key_c1:
                if st.button("OpenAI Key 저장", key="sprint194_28_save_openai_localization_key", use_container_width=True):
                    _present = _sprint194_28_save_openai_localization_key(_openai_localization_key)
                    st.success("OpenAI API Key 저장 완료" if _present else "OpenAI API Key 삭제 완료")
            with _key_c2:
                st.caption(
                    "OpenAI → Gemini 순서로 자동 현지화 · 성공 결과는 캐시되어 다시 API를 호출하지 않습니다."
                )

            _localize_clicked = st.button(
                "✨ 영어 버전 자동 생성",
                use_container_width=True,
                key="sprint194_24_auto_localize_en",
                disabled=False,
            )
            print("[Sprint194-26 English Auto Localize Button]", {
                "production_mode": production_mode,
                "enabled": True,
                "scene_count": len(editor_clip_sources),
            }, flush=True)
            if _localize_clicked:
                # Sprint194-26: clicking this button itself means "make English".
                # Do not trust production_mode here because a loaded Korean preset can
                # momentarily restore the radio state during the button rerun.
                _requested_language = "en"
                print("[Sprint194-26 English Auto Localize Intent] CLICKED", {
                    "ui_production_mode": production_mode,
                    "requested_language": _requested_language,
                    "scene_count": len(editor_clip_sources),
                }, flush=True)
                _src=[]
                for _i in range(1, len(editor_clip_sources)+1):
                    _src.append({
                        "subtitle": st.session_state.get(f"sprint193_9_clip_subtitle_{_i}", ""),
                        "narration": st.session_state.get(f"sprint193_9_clip_narration_{_i}", ""),
                    })
                if not any(x.get("narration") for x in _src):
                    st.error("한국어 나레이션이 없습니다. 먼저 한국어 이전 작업을 불러와 주세요.")
                else:
                    try:
                        _localized=_sprint194_21_auto_localize_history_to_english(_src, openai_api_key=_openai_localization_key, project_id=str(st.session_state.get("sprint193_29_loaded_project_id") or ""))
                        _localized_subtitles_194_30 = []
                        _localized_narrations_194_30 = []
                        for _row in _localized:
                            _i=int(_row["scene"])
                            _sub_194_30 = str(_row.get("subtitle") or "").strip()
                            _nar_194_30 = str(_row.get("narration") or "").strip()
                            st.session_state[f"sprint193_9_clip_subtitle_{_i}"]=_sub_194_30
                            st.session_state[f"sprint193_9_clip_narration_{_i}"]=_nar_194_30
                            _localized_subtitles_194_30.append(_sub_194_30)
                            _localized_narrations_194_30.append(_nar_194_30)
                        # Sprint194-30: keep a dedicated English render snapshot.
                        # Widget/preset reruns may restore Korean edit fields; final English render
                        # must use the localization result, not whatever preset happens to be visible later.
                        st.session_state["sprint194_30_english_subtitles"] = list(_localized_subtitles_194_30)
                        st.session_state["sprint194_30_english_narrations"] = list(_localized_narrations_194_30)
                        # Sprint194-75J: bind the in-session English snapshot to the
                        # current short-localization profile. Old 75H/75I snapshots
                        # must not silently drive a new render.
                        st.session_state["sprint194_75j_english_profile"] = "history-en-short-53-55s-v3"
                        st.session_state["sprint194_21_localized_ready"]=True
                        st.session_state["sprint194_26_pending_history_language"] = "en"
                        st.session_state["sprint194_23_localized_notice"] = f"영어 {len(_localized)}개 장면 자동 현지화 완료"
                        print("[Sprint194-26 English Auto Localize Intent] COMPLETED", {
                            "localized_count": len(_localized),
                            "next_language": "en",
                        }, flush=True)
                        st.rerun()
                    except Exception as _exc:
                        print("[Sprint194-21 History Auto Localization] ERROR", repr(_exc), flush=True)
                        st.error(f"영어 자동 현지화 실패: {_exc}")
            _localized_notice = str(st.session_state.pop("sprint194_23_localized_notice", "") or "")
            st.caption(
                ("✅ " + _localized_notice)
                if _localized_notice
                else ("English localization READY" if st.session_state.get("sprint194_21_localized_ready") else "Localization standby")
            )

        st.markdown("#### 자막 스타일")
        if is_history_mode:
            st.caption("역사쿠키 자동 연출: 본문은 읽기 쉬운 고딕, 후킹·강조는 굵은 폰트, 핵심 단어는 겨자/금색으로 자동 강조합니다. 장면 의미에 따라 Pop/Fade/Impact와 SFX가 자동 적용됩니다.")
        style_c1, style_c2, style_c3 = st.columns(3)
        with style_c1:
            subtitle_font = st.selectbox(
                "자막 글씨체",
                options=["Gmarket Sans Bold", "Noto Sans CJK KR", "Malgun Gothic", "Segoe UI", "Arial"],
                index=0,
                key="sprint190_9_subtitle_font",
            )
        with style_c2:
            subtitle_font_size = st.number_input(
                "자막 크기",
                min_value=32,
                max_value=140,
                value=76,
                step=2,
                key="sprint190_9_subtitle_font_size",
            )
        with style_c3:
            subtitle_outline = st.number_input(
                "외곽선 두께",
                min_value=0,
                max_value=30,
                value=6,
                step=1,
                key="sprint190_9_subtitle_outline",
            )

        style_c4, style_c5, style_c6 = st.columns(3)
        with style_c4:
            subtitle_text_color = st.color_picker(
                "자막 글자색",
                value="#FFFFFF",
                key="sprint190_9_subtitle_text_color",
            )
        with style_c5:
            subtitle_background_color = st.color_picker(
                "자막 배경색",
                value="#000000",
                key="sprint190_9_subtitle_background_color",
            )
        with style_c6:
            subtitle_highlight_color = st.color_picker(
                "강조 문구 글자색",
                value="#FFD700",
                key="sprint190_9_subtitle_highlight_color",
            )

        subtitle_background_opacity = st.slider(
            "자막 배경 진하기",
            min_value=0,
            max_value=100,
            value=10,
            step=5,
            format="%d%%",
            key="sprint190_9_subtitle_background_opacity",
            help="0%는 배경 없음, 100%는 완전 불투명입니다. 기본값은 10%입니다.",
        )
        st.caption(
            "강조할 문구는 [이렇게] 입력하세요. "
            "영상에서는 대괄호가 사라지고 해당 문구만 선택한 강조색으로 표시됩니다."
        )

        subtitle_style = {
            "font": str(subtitle_font or "Gmarket Sans Bold"),
            "font_size": int(subtitle_font_size or 76),
            "outline": int(subtitle_outline or 15),
            "text_color": str(subtitle_text_color or "#FFFFFF"),
            "background_color": str(subtitle_background_color or "#000000"),
            "background_opacity": int(subtitle_background_opacity if subtitle_background_opacity is not None else 10),
            "highlight_color": str(subtitle_highlight_color or "#FFD700"),
        }

        # Sprint193-6: 영상 1개당 한 줄 편집
        # [영상] [자막] [나레이션] [자막효과] [사운드효과]
        header_cols = st.columns([0.7, 2.8, 2.8, 1.15, 1.25, 1.0])
        for col, label in zip(
            header_cols,
            ["장면" if is_history_mode else "영상", "자막", "나레이션", "자막효과", "사운드효과", "속도"],
        ):
            with col:
                st.markdown(f"**{label}**")

        for index, uploaded_clip in enumerate(editor_clip_sources, start=1):
            if isinstance(uploaded_clip, (str, Path)):
                clip_name = Path(str(uploaded_clip)).name
            else:
                clip_name = str(
                    getattr(uploaded_clip, "name", f"장면 {index}" if is_history_mode else f"영상 {index}")
                    or (f"장면 {index}" if is_history_mode else f"영상 {index}")
                )
            row_c0, row_c1, row_c2, row_c3, row_c4, row_c5 = st.columns(
                [0.7, 2.8, 2.8, 1.15, 1.25, 1.0],
                vertical_alignment="center",
            )
            with row_c0:
                # Sprint194-47B: Scene 1 video replaces only the visual source.
                # Subtitle/narration/effects/SFX/speed remain Scene 1 inputs exactly as before.
                _scene_source_label_194_47b = (
                    "영상" if is_history_mode and index == 1 and _scene1_video_is_source else "이미지"
                )
                st.markdown(f"**{index}**")
                if is_history_mode:
                    st.caption(f"{clip_name} · {_scene_source_label_194_47b}")
                else:
                    st.caption(clip_name)
            with row_c1:
                subtitle_value = st.text_area(
                    f"영상 {index} 자막",
                    height=72,
                    placeholder="첫 번째 문장\n두 번째 문장",
                    key=f"sprint193_9_clip_subtitle_{index}",
                    label_visibility="collapsed",
                )
            with row_c2:
                narration_value = st.text_area(
                    f"영상 {index} 나레이션",
                    height=72,
                    placeholder="이 영상에서 읽을 나레이션 대사",
                    key=f"sprint193_9_clip_narration_{index}",
                    label_visibility="collapsed",
                )
            with row_c3:
                subtitle_effect_value = st.selectbox(
                    f"영상 {index} 자막효과",
                    options=["기본", "팝", "페이드", "바운스", "강조"],
                    key=f"sprint193_9_clip_subtitle_effect_{index}",
                    label_visibility="collapsed",
                )
            with row_c4:
                sfx_value = st.selectbox(
                    f"영상 {index} 사운드효과",
                    options=["없음", "pop", "whoosh", "click", "마우스 클릭", "키보드 타이핑"],
                    key=f"sprint193_9_clip_sfx_{index}",
                    label_visibility="collapsed",
                )
            with row_c5:
                scene_speed_value = st.selectbox(
                    f"영상 {index} 속도",
                    options=["자동", 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0],
                    index=0,
                    format_func=lambda value: (
                        "자동맞춤" if value == "자동" else f"{float(value):g}배"
                    ),
                    key=f"sprint193_14_clip_speed_{index}",
                    label_visibility="collapsed",
                    help="자동맞춤은 장면별 나레이션 실제 길이에 맞춰 영상 속도를 계산하고, 음성이 더 길면 마지막 프레임을 자동 연장해 다음 장면과 겹치지 않게 합니다.",
                )
            clip_subtitles.append(str(subtitle_value or "").strip())
            clip_narrations.append(str(narration_value or "").strip())
            clip_subtitle_effects.append(str(subtitle_effect_value or "기본").strip())
            clip_sfx.append(str(sfx_value or "없음").strip())
            clip_playback_speeds.append(0.0 if scene_speed_value == "자동" else float(scene_speed_value or 1.5))

        # Sprint194-47B: a Scene 1 MP4 is visual-source replacement only.
        # Keep all 1..N editing arrays aligned so Scene 1 still receives subtitle/TTS/effects.
        if is_history_mode:
            _edit_count_194_47b = len(editor_clip_sources)
            _edit_arrays_194_47b = {
                "subtitles": len(clip_subtitles),
                "narrations": len(clip_narrations),
                "subtitle_effects": len(clip_subtitle_effects),
                "sfx": len(clip_sfx),
                "speeds": len(clip_playback_speeds),
            }
            if any(v != _edit_count_194_47b for v in _edit_arrays_194_47b.values()):
                raise RuntimeError(
                    f"history_scene_edit_count_mismatch: scenes={_edit_count_194_47b} arrays={_edit_arrays_194_47b}"
                )
            print(
                "[Sprint194-47B History Scene Edit Preserve]",
                {
                    "scene1_video": bool(_scene1_video_is_source),
                    "scene_count": _edit_count_194_47b,
                    "scene1_subtitle_present": bool(clip_subtitles[0]) if clip_subtitles else False,
                    "scene1_narration_present": bool(clip_narrations[0]) if clip_narrations else False,
                    "arrays": _edit_arrays_194_47b,
                },
                flush=True,
            )

        # Sprint194-30: English Render Input Lock.
        # Never let the final History Cookie English renderer fall back to the Korean preset arrays.
        if production_mode == "history_en":
            _en_subs_194_30 = [str(x or "").strip() for x in list(st.session_state.get("sprint194_30_english_subtitles") or [])]
            _en_nars_194_30 = [str(x or "").strip() for x in list(st.session_state.get("sprint194_30_english_narrations") or [])]
            _scene_count_194_30 = len(editor_clip_sources)
            _profile_194_75j = str(st.session_state.get("sprint194_75j_english_profile") or "")
            _snapshot_ready_194_30 = (
                _profile_194_75j == "history-en-short-53-55s-v3"
                and len(_en_subs_194_30) == _scene_count_194_30
                and len(_en_nars_194_30) == _scene_count_194_30
                and all(_en_nars_194_30)
            )
            if _snapshot_ready_194_30:
                clip_subtitles = list(_en_subs_194_30)
                clip_narrations = list(_en_nars_194_30)
            else:
                # If the app was restarted after localization, the visible English widget values
                # are allowed as a recovery source, but Korean leakage is blocked below.
                _en_subs_194_30 = list(clip_subtitles or [])
                _en_nars_194_30 = list(clip_narrations or [])

            import re as _re_194_30
            _hangul_194_30 = _re_194_30.compile(r"[가-힣]")
            _ko_sub_count_194_30 = sum(bool(_hangul_194_30.search(str(x or ""))) for x in list(clip_subtitles or []))
            _ko_nar_count_194_30 = sum(bool(_hangul_194_30.search(str(x or ""))) for x in list(clip_narrations or []))
            print("[Sprint194-30 English Render Input Lock]", {
                "scene_count": _scene_count_194_30,
                "snapshot_ready": bool(_snapshot_ready_194_30),
                "localization_profile": _profile_194_75j,
                "profile_required": "history-en-short-53-55s-v3",
                "subtitle_count": len(list(clip_subtitles or [])),
                "narration_count": len(list(clip_narrations or [])),
                "hangul_subtitles": _ko_sub_count_194_30,
                "hangul_narrations": _ko_nar_count_194_30,
                "first_subtitle": str((list(clip_subtitles or [""])+[""])[0])[:90],
                "first_narration": str((list(clip_narrations or [""])+[""])[0])[:90],
            }, flush=True)
            if _ko_sub_count_194_30 or _ko_nar_count_194_30:
                st.error("영어 영상 렌더 입력에 한국어가 남아 있습니다. '영어 버전 자동 생성'을 한 번 눌러 영어 17개 장면을 만든 뒤 다시 제작해 주세요.")
                return

        narration_script = " ".join(
            item for item in clip_narrations if str(item or "").strip()
        ).strip()
        locked_script = narration_script
        if narration_script:
            st.caption("영상별 나레이션을 순서대로 합쳐 내부 확정 대본으로 사용합니다.")

    if is_history_mode:
        # Sprint194-3: 역사 모드에는 쇼핑 CTA 상품명 입력을 노출하지 않습니다.
        cta_product_logo_text = ""
        channel_type = production_mode
        st.markdown("#### 채널")
        st.success(
            "🍪 역사쿠키 (한국어)"
            if production_mode == "history_ko"
            else "🌍 History Cookie (English)"
        )
        _youtube_default_account_194_77_1 = _sprint194_77_default_youtube_account(
            production_mode
        )
        youtube_upload_account = st.selectbox(
            "YouTube 업로드 채널",
            options=list(YOUTUBE_UPLOAD_ACCOUNTS),
            index=(
                list(YOUTUBE_UPLOAD_ACCOUNTS).index(_youtube_default_account_194_77_1)
                if _youtube_default_account_194_77_1 in list(YOUTUBE_UPLOAD_ACCOUNTS)
                else 0
            ),
            key="sprint194_77_1_youtube_upload_account",
            help="한국어 역사쿠키는 '역사쿠키', 영어 버전은 'History Cookie' 채널을 선택합니다.",
        )
        st.caption(
            "현재 YouTube 업로드 대상: "
            + str(youtube_upload_account or _youtube_default_account_194_77_1)
        )
    else:
        st.markdown("#### CTA 상단 상품명")
        cta_product_logo_text = st.text_input(
            "CTA 상단 로고 자막",
            value="",
            placeholder="예: 미소랩 스윙글 워터탭",
            key="sprint193_25_cta_product_logo_text",
            help="마지막 수동 CTA 장면 상단에 로고형 상품명 자막으로 표시합니다. 비워두면 표시하지 않습니다.",
        )
        st.caption("마지막 CTA 장면에만 표시됩니다. 자동 CTA 문구를 생성하지는 않습니다.")
        youtube_upload_account = "실물로그"
        channel_type = st.selectbox(
            "채널",
            options=["shopping", "standing"],
            format_func=lambda value: {
                "shopping": "쇼핑 쇼츠",
                "standing": "일어서기",
            }.get(value, value),
            index=0,
            key="sprint172_channel_type",
        )

    c2, c3 = st.columns(2)
    with c2:
        playback_speed = st.slider(
            "영상 속도",
            min_value=0.5,
            max_value=2.0,
            value=1.5,
            step=0.1,
            format="%.1f배",
            key="sprint176_playback_speed",
            help=("역사 장면의 기본 재생 속도입니다. 장면별 자동맞춤을 선택하면 나레이션 길이에 맞춰 개별 조절됩니다." if is_history_mode else "Gemini 원본 영상 속도를 0.5배부터 2.0배까지 직접 조절합니다."),
        )
    with c3:
        youtube_privacy_status = st.selectbox(
            "YouTube 공개 설정",
            options=["unlisted", "private", "public"],
            index=0,
            format_func=lambda value: {"unlisted": "비등록", "private": "비공개", "public": "공개"}[value],
            key="sprint172_privacy",
        )

    history_youtube_schedule_enabled = False
    history_youtube_schedule_date = None
    history_youtube_schedule_time = None
    history_youtube_title = ""
    history_youtube_description = ""
    history_youtube_hashtags_text = ""
    if is_history_mode:
        st.markdown("##### YouTube 업로드 정보")
        history_youtube_title = st.text_input(
            "YouTube 제목",
            value=str(product_name or "").strip(),
            key="sprint194_77_4_history_youtube_title",
            placeholder="예: 왕이 신하에게 욕설 편지를 보냈다?! 정조의 비밀 어찰",
        )
        history_youtube_description = st.text_area(
            "YouTube 설명",
            value="",
            height=130,
            key="sprint194_77_4_history_youtube_description",
            placeholder="영상 설명을 입력하세요.",
        )
        history_youtube_hashtags_text = st.text_input(
            "YouTube 해시태그",
            value="#역사쿠키 #조선역사 #Shorts",
            key="sprint194_77_4_history_youtube_hashtags",
            placeholder="#역사쿠키 #조선역사 #Shorts",
        )

        st.markdown("##### YouTube 예약 게시")
        history_youtube_schedule_enabled = st.checkbox(
            "예약 게시 사용",
            value=False,
            key="sprint194_77_3_history_youtube_schedule_enabled",
            help="선택하면 완성 MP4를 비공개로 업로드한 뒤 지정한 한국 시간에 자동 공개합니다.",
        )
        if history_youtube_schedule_enabled:
            schedule_col1, schedule_col2 = st.columns(2)
            with schedule_col1:
                history_youtube_schedule_date = st.date_input(
                    "예약 날짜",
                    key="sprint194_77_3_history_youtube_schedule_date",
                )
            with schedule_col2:
                history_youtube_schedule_time = st.time_input(
                    "예약 시간",
                    key="sprint194_77_3_history_youtube_schedule_time",
                    step=300,
                )
            st.caption("예약 시간 기준: 한국시간(KST)")

    st.markdown("---")
    st.subheader("🎬 쇼츠 제작")
    st.caption(
        "업로드하지 않고 최종 MP4만 먼저 만들 수 있습니다. "
        "자막·신뢰 후킹·제품 배경을 확인할 때는 '영상만 제작'을 누르세요."
    )

    create_col, upload_col = st.columns(2)
    with create_col:
        create_only_clicked = st.button(
            "🎬 영상만 제작",
            type="primary",
            use_container_width=True,
            key="sprint189_3_create_only",
        )
    with upload_col:
        create_upload_clicked = st.button(
            "🚀 제작 + YouTube 업로드",
            use_container_width=True,
            key="sprint189_3_create_and_upload",
        )

    # Sprint189-6: 영상만 제작은 업로드/예약 UI를 전혀 거치지 않고 여기서 즉시 실행합니다.
    if create_only_clicked:
        direct_run_counter_key = "sprint193_27_direct_run_counter"
        direct_run_counter = int(st.session_state.get(direct_run_counter_key, 0) or 0) + 1
        st.session_state[direct_run_counter_key] = direct_run_counter
        direct_force_run_id = f"{direct_run_counter:06d}"

        print(
            "[Sprint193-29 DIRECT CREATE] CLICKED",
            {
                "run_counter": direct_run_counter,
                "force_run_id": direct_force_run_id,
                "bgm_volume_percent": int(bgm_volume_percent if bgm_volume_percent is not None else 10),
            },
            flush=True,
        )
        print("[Sprint194-39 UI BGM Volume] PASS", {
            "ui_percent": int(bgm_volume_percent if bgm_volume_percent is not None else 10),
            "history_mode": bool(is_history_mode),
        }, flush=True)
        if not str(locked_script or "").strip():
            st.error("영상별 나레이션을 한 줄 이상 입력해 주세요.")
            return
        if (
            locked_script
            and uploaded_voice_audio is None
            and not str(typecast_api_key or os.getenv("TYPECAST_API_KEY", "") or "").strip()
        ):
            st.error("나레이션 자동 생성을 위해 Typecast API Key를 입력해 주세요.")
            return

        direct_errors = []
        if not str(product_name or "").strip():
            direct_errors.append("역사 주제를 입력해 주세요." if is_history_mode else "상품명을 입력해 주세요.")
        if not str(locked_script or "").strip():
            direct_errors.append("확정 대본을 입력해 주세요.")
        if not editor_clip_sources:
            direct_errors.append("역사 장면 이미지를 한 장 이상 업로드하거나 이전 작업을 불러와 주세요." if is_history_mode else "Gemini 영상 파일을 업로드하거나 이전 작업을 불러와 주세요.")
        if is_history_mode and uploaded_history_scene_images:
            _ids = []
            for _item in uploaded_history_scene_images:
                _m = re.search(r"(\d+)", Path(str(getattr(_item, "name", "") or "")).stem)
                if _m:
                    _ids.append(int(_m.group(1)))
            _effective_count = len(uploaded_history_scene_images) + (1 if uploaded_history_scene1_video is not None and 1 not in set(_ids) else 0)
            if _effective_count != int(history_expected_scene_count or 0):
                direct_errors.append(
                    f"역사 장면 수를 확인해 주세요. 목표 {int(history_expected_scene_count)}장 / 유효 장면 {_effective_count}장"
                )

        if direct_errors:
            for error in direct_errors:
                st.error(error)
            return

        direct_payload = {
            "coupang_url": "",
            "product_name": product_name.strip(),
            "title": product_name.strip(),
            "source": ("manual_history_image_edit_194_4" if is_history_mode else "manual_gemini_video_edit_193_27_repeat"),
            "direct_run_id": direct_force_run_id,
            "hook_text": hook_text.strip(),
            "suppress_separate_hook": False,
            "locked_script": locked_script.strip(),
            "clip_subtitles": list(clip_subtitles or []),
            "clip_narrations": list(clip_narrations or []),
            "clip_subtitle_effects": list(clip_subtitle_effects or []),
            "clip_sfx": list(clip_sfx or []),
            "clip_playback_speeds": list(clip_playback_speeds or []),
            "subtitle_style": dict(subtitle_style or {}),
            "cta_text": cta_text.strip(),
            "cta_platform": str(video_cta_platform),
            "cta_keyword": str(cta_keyword or "").strip(),
            "gemini_clip_count": len(editor_clip_sources),
            "youtube_privacy_status": youtube_privacy_status,
            "upload_enabled": False,
            "channel_type": channel_type,
            "playback_speed": float(playback_speed),
            "voice_name": str(selected_voice_name or "지안"),
            "voice_id": str(selected_voice_id or ""),
            "monthly_purchase_count": int(monthly_purchase_count or 0),
            "declared_review_count": int(declared_review_count or 0),
            "rating": float(rating or 0.0),
            "reservation_enabled": False,
            "reservation_platforms": [],
            "infock_url": "",
            "platform_metadata": dict(platform_metadata or {}),
        }

        try:
            direct_project = create_project_from_payload(
                direct_payload,
                [product_name.strip()],
            )
            direct_project_id = getattr(direct_project, "id", None)
            if direct_project_id:
                direct_project = (
                    ProjectRepository().get(direct_project_id)
                    or direct_project
                )
        except Exception as exc:
            st.error(f"프로젝트 생성 실패: {exc}")
            return

        _save_clip_subtitle_sidecar(
            direct_project,
            clip_subtitles,
            subtitle_style,
            clip_narrations,
            clip_subtitle_effects,
            clip_sfx,
            clip_playback_speeds,
        )

        # 후킹 배경 제품 이미지 저장
        direct_hook_product_image_path = ""
        if hook_product_image is not None:
            product_folder = (
                Path("assets/products")
                / f"project_{safe_project_id(direct_project)}"
            )
            product_folder.mkdir(parents=True, exist_ok=True)
            suffix = Path(
                getattr(hook_product_image, "name", "product.jpg")
            ).suffix.lower()
            if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
                suffix = ".jpg"
            product_target = product_folder / f"00_main{suffix}"
            product_target.write_bytes(hook_product_image.getbuffer())
            direct_hook_product_image_path = str(product_target)

        # 역사 이미지는 9:16 MP4 장면으로 변환하고, 쇼핑 모드는 기존 Gemini 클립을 저장합니다.
        direct_folder = (
            Path("assets/gemini_clips")
            / f"project_{safe_project_id(direct_project)}"
        )
        direct_folder.mkdir(parents=True, exist_ok=True)
        direct_clip_paths = []
        if is_history_mode and uploaded_history_scene_images:
            try:
                direct_clip_paths = _sprint194_4_save_history_scene_images(
                    direct_project, uploaded_history_scene_images, clip_narrations, _effective_tts_speech_speed_194_41, uploaded_history_scene1_video
                )
            except Exception as exc:
                st.error(f"역사 장면 이미지 영상 변환 실패: {type(exc).__name__}: {exc}")
                return
        elif uploaded_gemini_clips:
            for index, uploaded in enumerate(uploaded_gemini_clips, start=1):
                suffix = Path(
                    getattr(uploaded, "name", "clip.mp4")
                ).suffix.lower() or ".mp4"
                destination = direct_folder / f"gemini_{index:02d}{suffix}"
                destination.write_bytes(uploaded.getbuffer())
                direct_clip_paths.append(str(destination))
        else:
            direct_clip_paths = [
                str(path)
                for path in loaded_gemini_clip_paths
                if Path(str(path)).is_file()
            ]
            print(
                "[Sprint194-2 Edit Preset] REUSE CLIPS",
                {"count": len(direct_clip_paths), "paths": direct_clip_paths},
                flush=True,
            )

        # 수동 오디오 저장
        direct_audio_folder = (
            Path("assets/manual_audio")
            / f"project_{safe_project_id(direct_project)}"
        )
        direct_audio_folder.mkdir(parents=True, exist_ok=True)
        direct_voice_audio_path = ""
        direct_bgm_audio_path = ""

        if uploaded_voice_audio is not None:
            suffix = Path(
                getattr(uploaded_voice_audio, "name", "voice.mp3")
            ).suffix.lower() or ".mp3"
            voice_target = direct_audio_folder / f"jian_voice{suffix}"
            voice_target.write_bytes(uploaded_voice_audio.getbuffer())
            direct_voice_audio_path = str(voice_target)

        if uploaded_bgm_audio is not None:
            suffix = Path(
                getattr(uploaded_bgm_audio, "name", "bgm.mp3")
            ).suffix.lower() or ".mp3"
            bgm_target = direct_audio_folder / f"shopping_bgm{suffix}"
            bgm_target.write_bytes(uploaded_bgm_audio.getbuffer())
            direct_bgm_audio_path = str(bgm_target)

        edit_preset_payload = {
            "version": "edit-preset-193-29",
            "project_id": str(safe_project_id(direct_project)),
            "product_name": str(product_name or "").strip(),
            "rating": float(rating or 0.0),
            "declared_review_count": int(declared_review_count or 0),
            "monthly_purchase_count": int(monthly_purchase_count or 0),
            "hook_text": str(hook_text or "").strip(),
            "clip_subtitles": list(clip_subtitles or []),
            "clip_narrations": list(clip_narrations or []),
            "clip_subtitle_effects": list(clip_subtitle_effects or []),
            "clip_sfx": list(clip_sfx or []),
            "clip_playback_speeds": list(clip_playback_speeds or []),
            "gemini_clip_paths": list(direct_clip_paths or []),
            "subtitle_style": dict(subtitle_style or {}),
            "cta_product_logo_text": str(cta_product_logo_text or "").strip(),
            "playback_speed": float(playback_speed or 1.5),
            "channel_type": str(channel_type or "shopping"),
            "youtube_privacy_status": str(youtube_privacy_status or "unlisted"),
            "voice_name": str(selected_voice_name or "지안"),
            "voice_id": str(selected_voice_id or ""),
            "tts_volume_percent": int(tts_volume_percent or 100),
            "tts_speech_speed": float(tts_speech_speed or 1.0),
            "bgm_volume_percent": int(bgm_volume_percent if bgm_volume_percent is not None else 10),
            "voice_audio_path": str(direct_voice_audio_path or ""),
            "bgm_audio_path": str(direct_bgm_audio_path or ""),
            "production_mode": str(production_mode or "shopping"),
            "history_expected_scene_count": int(history_expected_scene_count or 0),
            "saved_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
        }
        edit_preset_path = _sprint193_29_save_edit_preset(
            direct_project,
            edit_preset_payload,
        )
        st.session_state["sprint193_29_loaded_preset_path"] = edit_preset_path

        print(
            "[Sprint193-10 CLIP EDIT INPUT]",
            {
                "clip_subtitles": list(clip_subtitles or []),
                "clip_narrations": list(clip_narrations or []),
                "clip_subtitle_effects": list(clip_subtitle_effects or []),
                "clip_sfx": list(clip_sfx or []),
                "clip_playback_speeds": list(clip_playback_speeds or []),
                "voice_name": str(selected_voice_name or "지안"),
                "voice_id_present": bool(str(selected_voice_id or "").strip()),
                "cta_product_logo_text": str(cta_product_logo_text or "").strip(),
            },
            flush=True,
        )

        print(
            "[Sprint189-6 DIRECT CREATE] INPUT",
            {
                "project_id": safe_project_id(direct_project),
                "clip_subtitle_count": len([x for x in list(clip_subtitles or []) if str(x).strip()]),
                "monthly_purchase_count": int(monthly_purchase_count or 0),
                "declared_review_count": int(declared_review_count or 0),
                "rating": float(rating or 0.0),
                "hook_product_image_path": direct_hook_product_image_path,
                "clip_count": len(direct_clip_paths),
                "force_run_id": direct_force_run_id,
            },
            flush=True,
        )

        with st.spinner(
            "영상만 제작 중입니다... 자막·신뢰 후킹·BGM·효과음을 적용하고 있습니다."
        ):
            try:
                direct_result = run_project_pipeline(
                    project=direct_project,
                    sample_count=len(direct_clip_paths),
                    review_text=hook_text.strip(),
                    locked_script=locked_script.strip(),
                    review_image_paths=[],
                    product_image_paths=[],
                    product_image_path="",
                    youtube_privacy_status=youtube_privacy_status,
                    viral_video_sources=direct_clip_paths,
                    input_product_name=product_name.strip(),
                    stop_after_image_generation=False,
                    gemini_video_mode=True,
                    hook_text=hook_text.strip(),
                    cta_text=cta_text.strip(),
                    cta_product_logo_text=str(cta_product_logo_text or "").strip(),
                    voice_audio_path=direct_voice_audio_path,
                    bgm_audio_path=direct_bgm_audio_path,
                    bgm_volume_percent=int(bgm_volume_percent if bgm_volume_percent is not None else 10),
                    voice_name=str(selected_voice_name or "지안"),
                    voice_id=str(selected_voice_id or ""),
                    typecast_api_key=str(typecast_api_key or ""),
                    tts_volume_percent=int(tts_volume_percent or 100),
                    tts_speech_speed=float(_effective_tts_speech_speed_194_41),
                    clip_subtitles=list(clip_subtitles or []),
                    clip_subtitle_effects=list(clip_subtitle_effects or []),
                    clip_sfx=list(clip_sfx or []),
                    clip_playback_speeds=list(clip_playback_speeds or []),
                    clip_narrations=list(clip_narrations or []),
                    gemini_clip_count=len(direct_clip_paths),
                    upload_enabled=False,
                    playback_speed=float(playback_speed),
                    channel_type=channel_type,
                    monthly_purchase_count=int(monthly_purchase_count or 0),
                    declared_review_count=int(declared_review_count or 0),
                    rating=float(rating or 0.0),
                    reservation_payload=None,
                    force_run_id=direct_force_run_id,
                )
            except Exception as exc:
                Path("full_error.log").write_text(
                    traceback.format_exc(),
                    encoding="utf-8",
                )
                st.error(
                    f"영상 제작 실패: {type(exc).__name__}: {exc}"
                )
                return

        direct_final_path = _resolve_final_video_path(direct_result)
        if direct_final_path and Path(direct_final_path).is_file():
            st.success("🎬 영상 제작이 완료됐습니다. 업로드는 실행하지 않았습니다.")
            st.video(direct_final_path)
            st.caption(f"최종 영상: {direct_final_path}")
            print(
                "[Sprint193-29 DIRECT CREATE] FINAL VIDEO:",
                direct_final_path,
                flush=True,
            )
        else:
            st.error(
                str(
                    direct_result.get("summary")
                    or "최종 MP4가 생성되지 않았습니다."
                )
            )
            st.json(direct_result)
        return

    # 제작 버튼을 누르기 전에는 아래 테스트/예약 UI를 계속 보여주되,
    # 실제 제작 실행부까지 내려갈 수 있도록 세션에 클릭 상태를 저장합니다.
    st.subheader("YouTube 비공개 업로드 테스트")
    if is_history_mode:
        st.info(
            "역사쿠키는 Gemini 장면 테스트 대신 완성된 MP4를 직접 선택해 "
            "현재 선택한 YouTube 채널로 비공개 업로드합니다."
        )
        history_youtube_test_video = st.file_uploader(
            "역사쿠키 테스트용 완성 MP4",
            type=["mp4"],
            accept_multiple_files=False,
            key="sprint194_77_2_history_youtube_test_video",
        )
        st.caption(
            "업로드 시 위 제목·설명·해시태그가 그대로 YouTube에 적용됩니다."
        )
        if st.button(
            "역사쿠키 완성 MP4 → YouTube 비공개 테스트 업로드",
            width="stretch",
            key="sprint194_77_2_history_youtube_test_upload",
        ):
            if history_youtube_test_video is None:
                st.error("테스트할 완성 MP4를 선택해 주세요.")
            else:
                try:
                    test_root = Path("assets/youtube_test_uploads")
                    test_root.mkdir(parents=True, exist_ok=True)
                    original_name = str(
                        getattr(history_youtube_test_video, "name", "history_test.mp4")
                        or "history_test.mp4"
                    )
                    test_path = test_root / (
                        f"history_{safe_file_name(Path(original_name).stem)}_"
                        f"{datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y%m%d_%H%M%S')}.mp4"
                    )
                    test_path.write_bytes(history_youtube_test_video.getbuffer())

                    test_title = (
                        str(history_youtube_title or "").strip()
                        or str(product_name or "역사쿠키").strip()
                    )[:100]
                    _hashtags_194_77_4 = [
                        token.lstrip("#")
                        for token in re.split(
                            r"[\s,]+",
                            str(history_youtube_hashtags_text or ""),
                        )
                        if token.strip().lstrip("#")
                    ]
                    _hashtags_text_194_77_4 = " ".join(
                        f"#{tag}" for tag in _hashtags_194_77_4
                    )
                    _description_base_194_77_4 = str(
                        history_youtube_description or ""
                    ).strip()
                    test_description = "\n\n".join(
                        value
                        for value in (
                            _description_base_194_77_4,
                            _hashtags_text_194_77_4,
                        )
                        if value
                    )
                    test_payload = {
                        "youtube_privacy_status": "private",
                        "youtube_account": str(
                            youtube_upload_account
                            or _sprint194_77_default_youtube_account(production_mode)
                        ).strip(),
                        "channel": str(
                            youtube_upload_account
                            or _sprint194_77_default_youtube_account(production_mode)
                        ).strip(),
                        "tags": _hashtags_194_77_4,
                        "notify_subscribers": False,
                        "made_for_kids": False,
                        "default_language": "en" if production_mode == "history_en" else "ko",
                        "default_audio_language": "en" if production_mode == "history_en" else "ko",
                    }
                    if history_youtube_schedule_enabled:
                        if history_youtube_schedule_date is None or history_youtube_schedule_time is None:
                            raise RuntimeError("YouTube 예약 날짜와 시간을 선택해 주세요.")
                        scheduled_kst = datetime.combine(
                            history_youtube_schedule_date,
                            history_youtube_schedule_time,
                            tzinfo=ZoneInfo("Asia/Seoul"),
                        )
                        now_kst = datetime.now(ZoneInfo("Asia/Seoul"))
                        if scheduled_kst <= now_kst:
                            raise RuntimeError("YouTube 예약 시간은 현재보다 이후여야 합니다.")
                        scheduled_utc = scheduled_kst.astimezone(ZoneInfo("UTC"))
                        test_payload["youtube_publish_at"] = (
                            scheduled_utc.isoformat(timespec="seconds").replace("+00:00", "Z")
                        )
                        test_payload["youtube_privacy_status"] = "private"
                    print(
                        "[Sprint194-77-2 History YouTube Direct Test] START",
                        {
                            "account": test_payload["youtube_account"],
                            "video_path": str(test_path),
                            "production_mode": production_mode,
                        },
                        flush=True,
                    )
                    with st.spinner(
                        f"{test_payload['youtube_account']} 채널로 비공개 테스트 업로드 중입니다..."
                    ):
                        test_result = YouTubeUploadExecutor().execute(
                            video_path=str(test_path),
                            title=test_title,
                            description=test_description,
                            privacy_status="private",
                            payload=test_payload,
                        )
                    st.session_state["sprint194_77_2_history_youtube_test_result"] = test_result
                    st.success("역사쿠키 YouTube 비공개 테스트 업로드가 완료됐습니다.")
                    st.write("채널:", test_payload["youtube_account"])
                    st.write("Video ID:", test_result.get("video_id", ""))
                    st.write("공개 상태:", test_result.get("privacy_status", "private"))
                    if history_youtube_schedule_enabled:
                        st.write(
                            "예약 게시:",
                            scheduled_kst.strftime("%Y-%m-%d %H:%M KST"),
                        )
                    shorts_url = str(
                        test_result.get("shorts_url")
                        or test_result.get("watch_url")
                        or ""
                    )
                    if shorts_url:
                        st.link_button(
                            "YouTube에서 확인",
                            shorts_url,
                            use_container_width=True,
                        )
                    print(
                        "[Sprint194-77-2 History YouTube Direct Test] SUCCESS",
                        {
                            "account": test_payload["youtube_account"],
                            "video_id": test_result.get("video_id", ""),
                            "privacy": test_result.get("privacy_status", ""),
                        },
                        flush=True,
                    )
                except Exception as exc:
                    Path("full_error.log").write_text(
                        traceback.format_exc(),
                        encoding="utf-8",
                    )
                    st.error(
                        "역사쿠키 YouTube 비공개 테스트 업로드 실패: "
                        f"{type(exc).__name__}: {exc}"
                    )
                    print(
                        "[Sprint194-77-2 History YouTube Direct Test] ERROR",
                        type(exc).__name__,
                        str(exc),
                        flush=True,
                    )
    else:
        st.caption(
            "쇼핑 쇼츠는 기존 첫 장면 Gemini MP4 비공개 테스트를 그대로 사용합니다."
        )
        if st.button(
            "첫 장면 YouTube 비공개 테스트 업로드",
            width="stretch",
            key="sprint183_single_scene_upload",
        ):
            if not first_clip:
                st.error("Gemini 영상 파일을 한 개 이상 선택해 주세요.")
            else:
                test_root = Path("assets/youtube_test_uploads")
                test_root.mkdir(parents=True, exist_ok=True)
                test_path = test_root / f"single_scene_{safe_file_name(product_name)}.mp4"
                try:
                    test_path.write_bytes(first_clip.getbuffer())
                    test_title = normalize_text(product_name, "쇼핑 쇼츠")
                    test_title = f"[업로드 테스트] {test_title}"[:100]
                    test_description = (
                        "YouTube Shorts 자동업로드 연결 확인을 위한 비공개 테스트 영상입니다.\n"
                        "첫 번째 Gemini 장면만 업로드했습니다.\n\n"
                        "#쇼츠 #업로드테스트"
                    )
                    with st.spinner("첫 장면을 YouTube 비공개 영상으로 업로드 중입니다..."):
                        test_result = YouTubeUploadExecutor().execute(
                            video_path=str(test_path),
                            title=test_title,
                            description=test_description,
                            privacy_status="private",
                            payload={
                                "youtube_privacy_status": "private",
                                "tags": ["쇼츠", "업로드테스트"],
                                "notify_subscribers": False,
                                "made_for_kids": False,
                            },
                        )
                    st.session_state["sprint183_single_scene_upload_result"] = test_result
                    st.success("첫 장면 YouTube 비공개 업로드가 완료됐습니다.")
                    st.write("Video ID:", test_result.get("video_id", ""))
                    st.write("공개 상태:", test_result.get("privacy_status", "private"))
                    shorts_url = str(
                        test_result.get("shorts_url")
                        or test_result.get("watch_url")
                        or ""
                    )
                    if shorts_url:
                        st.link_button(
                            "YouTube에서 확인",
                            shorts_url,
                            use_container_width=True,
                        )
                    print(
                        "[Sprint183-1 Single Scene Upload] SUCCESS",
                        test_result.get("video_id", ""),
                        test_result.get("privacy_status", ""),
                        flush=True,
                    )
                except Exception as exc:
                    Path("full_error.log").write_text(
                        traceback.format_exc(),
                        encoding="utf-8",
                    )
                    st.error(
                        f"첫 장면 YouTube 업로드 실패: {type(exc).__name__}: {exc}"
                    )
                    print(
                        "[Sprint183-1 Single Scene Upload] ERROR",
                        type(exc).__name__,
                        str(exc),
                        flush=True,
                    )

    st.subheader("Meta Business Suite 릴스 예약 테스트")
    st.info(
        "Meta 로그인 저장과 릴스 예약을 분리했습니다. 최초 1회 로그인 저장을 완료한 뒤 예약 테스트를 실행하세요. "
        "즉시 게시 버튼은 누르지 않고 예약 버튼만 실행합니다."
    )

    if st.button(
        "① Meta 로그인 저장",
        width="stretch",
        key="sprint184_1_meta_login_save",
    ):
        try:
            with st.spinner("Facebook 로그인 브라우저를 여는 중입니다. 로그인 후 Business Suite 화면이 열릴 때까지 기다려 주세요..."):
                login_result = MetaBusinessSuiteScheduler().save_login_session(
                    user_data_dir="secrets/meta_business_suite_profile",
                    headless=False,
                    login_timeout_seconds=600,
                    action_timeout_seconds=60,
                    slow_mo=120,
                )
            st.session_state["sprint184_1_meta_login_result"] = login_result
            if login_result.get("ok"):
                st.success("Meta 로그인 세션이 저장됐습니다. 이제 아래 예약 테스트를 실행하세요.")
                print(
                    "[Sprint184-1 Meta Login UI] SUCCESS",
                    login_result.get("final_url", ""),
                    flush=True,
                )
            else:
                st.error(
                    "Meta 로그인 저장에 실패했습니다: "
                    f"{login_result.get('status')} / {login_result.get('errors')}"
                )
                failure_screenshot = str(login_result.get("failure_screenshot") or "")
                if failure_screenshot:
                    st.caption(f"실패 화면: {failure_screenshot}")
                print(
                    "[Sprint184-1 Meta Login UI] ERROR",
                    login_result.get("status"),
                    login_result.get("errors"),
                    flush=True,
                )
        except Exception as exc:
            Path("full_error.log").write_text(traceback.format_exc(), encoding="utf-8")
            st.error(f"Meta 로그인 저장 실패: {type(exc).__name__}: {exc}")

    meta_c1, meta_c2 = st.columns(2)
    default_meta_date = (datetime.now(ZoneInfo("Asia/Seoul")) + timedelta(days=1)).date()
    with meta_c1:
        meta_schedule_date = st.date_input(
            "Instagram 테스트 예약 날짜",
            value=default_meta_date,
            key="sprint183_4_meta_schedule_date",
        )
    with meta_c2:
        meta_schedule_time = st.time_input(
            "Instagram 테스트 예약 시간",
            value=datetime.strptime("10:00", "%H:%M").time(),
            key="sprint183_4_meta_schedule_time",
        )

    if st.button(
        "② 첫 장면 Meta Business Suite 릴스 예약 테스트",
        width="stretch",
        key="sprint183_4_meta_single_scene_schedule_test",
    ):
        if not uploaded_gemini_clips:
            st.error("Gemini 영상 파일을 한 개 이상 선택해 주세요.")
        else:
            first_clip = uploaded_gemini_clips[0]
            test_root = Path("assets/meta_business_suite_test_uploads")
            test_root.mkdir(parents=True, exist_ok=True)
            original_name = str(getattr(first_clip, "name", "scene_01.mp4") or "scene_01.mp4")
            suffix = Path(original_name).suffix.lower()
            if suffix not in SUPPORTED_VIRAL_VIDEO_SUFFIXES:
                suffix = ".mp4"
            timestamp = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d_%H%M%S")
            test_path = test_root / f"single_scene_{timestamp}{suffix}"
            try:
                test_path.write_bytes(first_clip.getbuffer())
                scheduled_at = datetime.combine(meta_schedule_date, meta_schedule_time)
                test_caption = (
                    f"[예약 테스트] {normalize_text(product_name, '쇼핑 쇼츠')}\n\n"
                    "첫 번째 장면 Meta Business Suite 릴스 예약 연결 테스트입니다.\n\n"
                    "#릴스 #쇼핑쇼츠 #예약테스트"
                )[:2200]
                with st.spinner("Meta Business Suite를 열고 첫 장면 릴스를 예약 중입니다..."):
                    test_result = MetaBusinessSuiteScheduler().schedule_reel(
                        video_path=str(test_path),
                        caption=test_caption,
                        scheduled_at=scheduled_at,
                        user_data_dir="secrets/meta_business_suite_profile",
                        headless=False,
                        allow_manual_login=False,
                        login_timeout_seconds=30,
                        action_timeout_seconds=60,
                        slow_mo=150,
                        keep_browser_open=False,
                    )
                st.session_state["sprint183_4_meta_schedule_result"] = test_result
                if test_result.get("ok"):
                    st.success(
                        "Meta Business Suite 릴스 예약이 완료됐습니다: "
                        f"{test_result.get('scheduled_at', '')}"
                    )
                    print(
                        "[Sprint184-1 Meta Single Scene Schedule] SUCCESS",
                        test_result.get("scheduled_at", ""),
                        flush=True,
                    )
                else:
                    st.error(
                        "Meta Business Suite 예약에 실패했습니다: "
                        f"{test_result.get('status')} / {test_result.get('errors')}"
                    )
                    failure_screenshot = str(test_result.get("failure_screenshot") or "")
                    if failure_screenshot:
                        st.caption(f"실패 화면: {failure_screenshot}")
                    print(
                        "[Sprint184-1 Meta Single Scene Schedule] ERROR",
                        test_result.get("status"),
                        test_result.get("errors"),
                        flush=True,
                    )
            except Exception as exc:
                Path("full_error.log").write_text(traceback.format_exc(), encoding="utf-8")
                st.error(f"Meta Business Suite 예약 실패: {type(exc).__name__}: {exc}")
                print(
                    "[Sprint184-1 Meta Single Scene Schedule] ERROR",
                    type(exc).__name__,
                    str(exc),
                    flush=True,
                )


    st.subheader("TikTok 첫 장면 업로드 테스트")
    st.info(
        "최초 1회 TikTok 로그인을 저장한 뒤 첫 장면 업로드 테스트를 실행하세요. "
        "영상과 캡션을 입력한 뒤 실제 게시 버튼까지 자동으로 누릅니다."
    )

    tiktok_upload_account = st.selectbox(
        "TikTok 업로드 계정",
        options=["실물로그", "하센맘"],
        index=0,
        key="sprint192_1_tiktok_upload_account",
        help="계정별 로그인 세션을 서로 다른 브라우저 프로필에 저장합니다.",
    )
    tiktok_profile_dir = _publisher_profile(
        tiktok_upload_account,
        "tiktok",
    )
    st.caption(f"TikTok 로그인 프로필: {tiktok_upload_account}")

    if st.button(
        "① TikTok 로그인 저장",
        width="stretch",
        key="sprint185_1_tiktok_login_save",
    ):
        try:
            with st.spinner(
                "TikTok 로그인 브라우저를 여는 중입니다. "
                f"{tiktok_upload_account} 계정으로 로그인한 뒤 TikTok 홈 또는 Studio 화면이 열릴 때까지 기다려 주세요..."
            ):
                login_result = TikTokUploadExecutor().save_login_session(
                    user_data_dir=tiktok_profile_dir,
                    headless=False,
                    login_timeout_seconds=600,
                    action_timeout_seconds=60,
                    slow_mo=120,
                )
            st.session_state["sprint185_1_tiktok_login_result"] = login_result
            if login_result.get("ok"):
                st.success("TikTok 로그인 세션이 저장됐습니다.")
                print(
                    "[Sprint185-1 TikTok Login UI] SUCCESS",
                    login_result.get("final_url", ""),
                    flush=True,
                )
            else:
                st.error(
                    "TikTok 로그인 저장에 실패했습니다: "
                    f"{login_result.get('status')} / {login_result.get('errors')}"
                )
                failure_screenshot = str(
                    login_result.get("failure_screenshot") or ""
                )
                if failure_screenshot:
                    st.caption(f"실패 화면: {failure_screenshot}")
                print(
                    "[Sprint185-1 TikTok Login UI] ERROR",
                    login_result.get("status"),
                    login_result.get("errors"),
                    flush=True,
                )
        except Exception as exc:
            Path("full_error.log").write_text(
                traceback.format_exc(),
                encoding="utf-8",
            )
            st.error(
                f"TikTok 로그인 저장 실패: {type(exc).__name__}: {exc}"
            )

    if st.button(
        "② 첫 장면 TikTok 실제 게시 테스트",
        width="stretch",
        key="sprint185_1_tiktok_single_scene_preview",
    ):
        if not uploaded_gemini_clips:
            st.error("Gemini 영상 파일을 한 개 이상 선택해 주세요.")
        else:
            first_clip = uploaded_gemini_clips[0]
            test_root = Path("assets/tiktok_test_uploads")
            test_root.mkdir(parents=True, exist_ok=True)
            original_name = str(
                getattr(first_clip, "name", "scene_01.mp4")
                or "scene_01.mp4"
            )
            suffix = Path(original_name).suffix.lower()
            if suffix not in SUPPORTED_VIRAL_VIDEO_SUFFIXES:
                suffix = ".mp4"
            timestamp = datetime.now(
                ZoneInfo("Asia/Seoul")
            ).strftime("%Y%m%d_%H%M%S")
            test_path = (
                test_root / f"single_scene_{timestamp}{suffix}"
            )
            try:
                test_path.write_bytes(first_clip.getbuffer())
                tiktok_test_hashtags = (
                    "#하센맘 #업로드테스트"
                    if tiktok_upload_account == "하센맘"
                    else "#실물로그 #쇼핑쇼츠 #제품소개 #업로드테스트"
                )
                test_caption = (
                    f"[업로드 테스트] "
                    f"{normalize_text(product_name, '쇼핑 쇼츠')}\n\n"
                    "첫 번째 장면 TikTok 자동업로드 연결 테스트입니다.\n\n"
                    f"{tiktok_test_hashtags}"
                )[:2200]

                with st.spinner(
                    "TikTok에 영상과 캡션을 입력하고 실제 게시까지 진행 중입니다..."
                ):
                    test_result = TikTokUploadExecutor().prepare_upload(
                        video_path=str(test_path),
                        caption=test_caption,
                        user_data_dir=tiktok_profile_dir,
                        headless=False,
                        allow_manual_login=False,
                        login_timeout_seconds=30,
                        action_timeout_seconds=60,
                        slow_mo=150,
                        keep_browser_open=False,
                        publish=True,
                    )

                st.session_state[
                    "sprint185_1_tiktok_preview_result"
                ] = test_result

                if test_result.get("ok"):
                    st.success(
                        "TikTok 게시 직전 준비가 완료됐습니다. "
                        "열린 브라우저에서 영상·캡션을 확인하세요. "
                        "게시 버튼은 자동으로 누르지 않았습니다."
                    )
                    st.write(
                        "상태:",
                        test_result.get("status", ""),
                    )
                    st.write(
                        "최종 화면:",
                        test_result.get("final_url", ""),
                    )
                    print(
                        "[Sprint186-1 TikTok Publish UI] SUCCESS",
                        test_result.get("status", ""),
                        flush=True,
                    )
                else:
                    st.error(
                        "TikTok 게시 직전 테스트에 실패했습니다: "
                        f"{test_result.get('status')} / "
                        f"{test_result.get('errors')}"
                    )
                    failure_screenshot = str(
                        test_result.get("failure_screenshot") or ""
                    )
                    if failure_screenshot:
                        st.caption(f"실패 화면: {failure_screenshot}")
                    print(
                        "[Sprint186-1 TikTok Publish UI] ERROR",
                        test_result.get("status"),
                        test_result.get("errors"),
                        flush=True,
                    )
            except Exception as exc:
                Path("full_error.log").write_text(
                    traceback.format_exc(),
                    encoding="utf-8",
                )
                st.error(
                    "TikTok 게시 직전 테스트 실패: "
                    f"{type(exc).__name__}: {exc}"
                )
                print(
                    "[Sprint186-1 TikTok Publish UI] ERROR",
                    type(exc).__name__,
                    str(exc),
                    flush=True,
                )



    st.subheader("스레드 예약 업로드 테스트")
    st.info("실제 게시 성공 확인 완료. 이제 원클릭의 게시 날짜/시간을 Threads 자체 예약 게시에 적용합니다.")

    threads_upload_account = st.selectbox(
        "스레드 계정",
        options=["실물로그", "하센맘"],
        index=1,
        key="threads_sprint1_account",
    )
    threads_profile_dir = _publisher_profile(threads_upload_account, "threads")
    st.caption(f"스레드 로그인 프로필: {threads_profile_dir}")

    if st.button("① 스레드 로그인 저장", width="stretch", key="threads_sprint1_login_save"):
        with st.spinner("스레드 로그인 브라우저를 여는 중입니다. 브라우저에서 로그인을 완료해 주세요."):
            threads_login_result = ThreadsUploadExecutor().save_login_session(
                user_data_dir=threads_profile_dir,
                headless=False,
                login_timeout_seconds=600,
                action_timeout_seconds=60,
                slow_mo=120,
            )
        if threads_login_result.get("ok"):
            st.success("스레드 로그인 세션이 저장됐습니다.")
        else:
            st.error(
                "스레드 로그인 저장 실패: "
                f"{threads_login_result.get('status')} / {threads_login_result.get('errors')}"
            )

    threads_test_video = st.file_uploader(
        "스레드 테스트용 MP4",
        type=["mp4", "mov", "m4v", "webm"],
        key="threads_sprint1_test_video",
    )
    threads_test_text = st.text_area(
        "스레드 본문",
        value="",
        height=120,
        key="threads_sprint1_text",
        placeholder="테스트 게시물 본문을 입력하세요.",
    )

    threads_now = datetime.now(ZoneInfo("Asia/Seoul"))
    threads_default_schedule = threads_now + timedelta(hours=1)
    threads_schedule_col1, threads_schedule_col2 = st.columns(2)
    with threads_schedule_col1:
        threads_schedule_date = st.date_input(
            "스레드 예약 날짜",
            value=threads_default_schedule.date(),
            min_value=threads_now.date(),
            key="threads_sprint2_schedule_date",
        )
    with threads_schedule_col2:
        threads_schedule_time = st.time_input(
            "스레드 예약 시간",
            value=threads_default_schedule.time().replace(second=0, microsecond=0),
            step=300,
            key="threads_sprint2_schedule_time",
        )

    threads_schedule_at_preview = datetime.combine(
        threads_schedule_date,
        threads_schedule_time,
        tzinfo=ZoneInfo("Asia/Seoul"),
    )
    st.caption(
        "Threads 예약시간: "
        f"{threads_schedule_at_preview.strftime('%Y-%m-%d %H:%M')}"
    )

    if st.button(
        "② 스레드 예약 게시 테스트",
        type="primary",
        width="stretch",
        key="threads_sprint1_publish",
    ):
        if threads_test_video is None:
            st.error("스레드 테스트용 MP4를 선택해 주세요.")
        else:
            try:
                test_root = Path("assets/threads_test_uploads")
                test_root.mkdir(parents=True, exist_ok=True)
                original_name = str(getattr(threads_test_video, "name", "threads_test.mp4") or "threads_test.mp4")
                suffix = Path(original_name).suffix.lower()
                if suffix not in {".mp4", ".mov", ".m4v", ".webm"}:
                    suffix = ".mp4"
                timestamp = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d_%H%M%S")
                threads_test_path = test_root / f"threads_test_{timestamp}{suffix}"
                threads_test_path.write_bytes(threads_test_video.getbuffer())

                test_text = str(threads_test_text or "").strip()
                if not test_text:
                    test_text = f"{normalize_text(product_name, '쇼핑 쇼츠')}\n\n#실물로그 #제품리뷰 #업로드테스트"

                print(
                    "[Threads Sprint1 UI] PUBLISH START",
                    {
                        "account": threads_upload_account,
                        "profile_dir": threads_profile_dir,
                        "video_path": str(threads_test_path),
                    },
                    flush=True,
                )

                threads_schedule_at = datetime.combine(
                    threads_schedule_date,
                    threads_schedule_time,
                    tzinfo=ZoneInfo("Asia/Seoul"),
                )
                if threads_schedule_at <= datetime.now(
                    ZoneInfo("Asia/Seoul")
                ):
                    st.error(
                        "스레드 예약 날짜/시간은 현재 시각보다 이후로 지정해 주세요."
                    )
                    return

                threads_schedule_iso = threads_schedule_at.isoformat(
                    timespec="minutes"
                )

                print(
                    "[Threads Sprint2 UI] SCHEDULE",
                    {
                        "scheduled_publish_at": threads_schedule_iso,
                    },
                    flush=True,
                )

                with st.spinner(
                    "스레드에 본문·영상을 입력하고 예약 날짜/시간을 설정하는 중입니다..."
                ):
                    threads_result = ThreadsUploadExecutor().prepare_upload(
                        video_path=str(threads_test_path),
                        text=test_text,
                        user_data_dir=threads_profile_dir,
                        headless=False,
                        allow_manual_login=True,
                        login_timeout_seconds=600,
                        action_timeout_seconds=60,
                        slow_mo=150,
                        keep_browser_open=True,
                        publish=True,
                        scheduled_publish_at=threads_schedule_iso,
                    )

                if threads_result.get("ok"):
                    st.success("스레드 예약 게시 설정이 완료됐습니다.")
                    st.write("상태:", threads_result.get("status", ""))
                else:
                    st.error(
                        "스레드 실제 게시 테스트 실패: "
                        f"{threads_result.get('status')} / {threads_result.get('errors')}"
                    )
                    screenshot = str(threads_result.get("failure_screenshot") or "")
                    if screenshot:
                        st.caption(f"실패 화면: {screenshot}")

                print(
                    "[Threads Sprint1 UI] PUBLISH COMPLETE",
                    {
                        "ok": threads_result.get("ok"),
                        "status": threads_result.get("status"),
                        "final_url": threads_result.get("final_url"),
                    },
                    flush=True,
                )
            except Exception as exc:
                Path("full_error.log").write_text(traceback.format_exc(), encoding="utf-8")
                st.error(f"스레드 실제 게시 테스트 실패: {type(exc).__name__}: {exc}")

    st.markdown("---")

    st.subheader("네이버 클립 첫 장면 업로드 테스트")
    st.info(
        "최초 1회 네이버 로그인을 저장한 뒤 첫 장면 업로드 테스트를 실행하세요. "
        "게시 직전 테스트와 실제 게시 테스트를 분리해서 실행합니다."
    )

    naver_clip_upload_account = st.selectbox(
        "네이버 클립 업로드 계정",
        options=["실물로그", "하센맘"],
        index=0,
        key="sprint192_1_naver_clip_upload_account",
        help="계정별 네이버 로그인 세션을 서로 다른 브라우저 프로필에 저장합니다.",
    )
    naver_clip_profile_dir = _publisher_profile(
        naver_clip_upload_account,
        "naver_clip",
    )
    st.caption(f"네이버 클립 로그인 프로필: {naver_clip_upload_account}")

    if st.button(
        "① 네이버 클립 로그인 저장",
        width="stretch",
        key="sprint187_1_naver_clip_login_save",
    ):
        try:
            with st.spinner(
                "네이버 Creator Studio 로그인 브라우저를 여는 중입니다. "
                "로그인 후 Creator Studio 화면이 열릴 때까지 기다려 주세요..."
            ):
                login_result = NaverClipUploadExecutor().save_login_session(
                    user_data_dir=naver_clip_profile_dir,
                    headless=False,
                    login_timeout_seconds=600,
                    action_timeout_seconds=60,
                    slow_mo=120,
                    target_channel_name=(
                        "하센맘"
                        if naver_clip_upload_account == "하센맘"
                        else ""
                    ),
                )
            st.session_state["sprint187_1_naver_clip_login_result"] = login_result
            if login_result.get("ok"):
                st.success("네이버 클립 로그인 세션이 저장됐습니다.")
                print(
                    "[Sprint187-10 Naver Clip Login UI] SUCCESS",
                    login_result.get("final_url", ""),
                    flush=True,
                )
            else:
                st.error(
                    "네이버 클립 로그인 저장에 실패했습니다: "
                    f"{login_result.get('status')} / {login_result.get('errors')}"
                )
                failure_screenshot = str(login_result.get("failure_screenshot") or "")
                if failure_screenshot:
                    st.caption(f"실패 화면: {failure_screenshot}")
        except Exception as exc:
            Path("full_error.log").write_text(
                traceback.format_exc(),
                encoding="utf-8",
            )
            st.error(
                f"네이버 클립 로그인 저장 실패: {type(exc).__name__}: {exc}"
            )

    if st.button(
        "② 첫 장면 네이버 클립 게시 직전 테스트",
        width="stretch",
        key="sprint187_1_naver_clip_preview",
    ):
        if not uploaded_gemini_clips:
            st.error("Gemini 영상 파일을 한 개 이상 선택해 주세요.")
        else:
            first_clip = uploaded_gemini_clips[0]
            test_root = Path("assets/naver_clip_test_uploads")
            test_root.mkdir(parents=True, exist_ok=True)
            original_name = str(
                getattr(first_clip, "name", "scene_01.mp4")
                or "scene_01.mp4"
            )
            suffix = Path(original_name).suffix.lower()
            if suffix not in SUPPORTED_VIRAL_VIDEO_SUFFIXES:
                suffix = ".mp4"
            timestamp = datetime.now(
                ZoneInfo("Asia/Seoul")
            ).strftime("%Y%m%d_%H%M%S")
            test_path = test_root / f"single_scene_{timestamp}{suffix}"

            try:
                test_path.write_bytes(first_clip.getbuffer())
                test_title = (
                    f"[업로드 테스트] "
                    f"{normalize_text(product_name, '쇼핑 쇼츠')}"
                )[:100]
                naver_test_hashtags = (
                    "#하센맘 #업로드테스트"
                    if naver_clip_upload_account == "하센맘"
                    else "#실물로그 #쇼핑쇼츠 #제품소개 #업로드테스트"
                )
                test_description = (
                    "첫 번째 장면 네이버 클립 자동업로드 연결 테스트입니다.\n\n"
                    f"{naver_test_hashtags}"
                )[:1000]

                with st.spinner(
                    "네이버 로그인부터 영상·제목·설명 입력까지 같은 브라우저에서 진행 중입니다..."
                ):
                    print(
                        "[Sprint192-9 Naver Clip Publish Profile]",
                        {
                            "account": naver_clip_upload_account,
                            "profile_dir": naver_clip_profile_dir,
                        },
                        flush=True,
                    )
                    test_result = NaverClipUploadExecutor().prepare_upload(
                        video_path=str(test_path),
                        title=test_title,
                        description=test_description,
                        user_data_dir=naver_clip_profile_dir,
                        headless=False,
                        allow_manual_login=True,
                        login_timeout_seconds=600,
                        action_timeout_seconds=60,
                        slow_mo=150,
                        keep_browser_open=True,
                    )

                st.session_state[
                    "sprint187_1_naver_clip_preview_result"
                ] = test_result

                if test_result.get("ok"):
                    st.success(
                        "네이버 클립 게시 직전 준비가 완료됐습니다. "
                        "열린 브라우저에서 영상·설명·카테고리를 확인하세요. "
                        "게시 버튼은 자동으로 누르지 않았습니다."
                    )
                    st.write("상태:", test_result.get("status", ""))
                    st.write("최종 화면:", test_result.get("final_url", ""))
                    print(
                        "[Sprint187-10 Naver Clip Preview UI] SUCCESS",
                        test_result.get("status", ""),
                        flush=True,
                    )
                else:
                    st.error(
                        "네이버 클립 게시 직전 테스트에 실패했습니다: "
                        f"{test_result.get('status')} / {test_result.get('errors')}"
                    )
                    failure_screenshot = str(test_result.get("failure_screenshot") or "")
                    if failure_screenshot:
                        st.caption(f"실패 화면: {failure_screenshot}")
                    print(
                        "[Sprint187-10 Naver Clip Preview UI] ERROR",
                        test_result.get("status"),
                        test_result.get("errors"),
                        flush=True,
                    )
            except Exception as exc:
                Path("full_error.log").write_text(
                    traceback.format_exc(),
                    encoding="utf-8",
                )
                st.error(
                    "네이버 클립 게시 직전 테스트 실패: "
                    f"{type(exc).__name__}: {exc}"
                )



    # Sprint192-22:
    # ③ 실제 게시 영역을 st.fragment로 분리합니다.
    # 이 버튼을 누르면 원클릭 전체 페이지가 아니라 이 fragment만 다시 실행되므로,
    # 상단 Content Scan을 다시 거치지 않고 곧바로 네이버 실제 게시 코드에 진입합니다.
    @st.fragment
    def _sprint192_22_naver_publish_fragment() -> None:
        st.warning(
            "③ 실제 게시 버튼은 네이버 클립에 실제로 등록합니다. "
            "테스트 영상/설명/카테고리를 확인한 뒤 실행하세요."
        )

        print(
            "[Sprint192-22 Naver Clip Publish Fragment] RENDER",
            flush=True,
        )

        if st.button(
            "③ 첫 장면 네이버 클립 즉시 게시 테스트",
            width="stretch",
            key="sprint192_22_naver_clip_actual_publish",
            type="primary",
        ):
            print(
                "[Sprint192-22 Naver Clip Publish Fragment] BUTTON CLICKED",
                flush=True,
            )

            if not uploaded_gemini_clips:
                st.error("Gemini 영상 파일을 한 개 이상 선택해 주세요.")
                print(
                    "[Sprint192-22 Naver Clip Publish Fragment] VIDEO MISSING",
                    flush=True,
                )
                return

            first_clip = uploaded_gemini_clips[0]
            test_root = Path("assets/naver_clip_test_uploads")
            test_root.mkdir(parents=True, exist_ok=True)

            original_name = str(
                getattr(first_clip, "name", "scene_01.mp4")
                or "scene_01.mp4"
            )
            suffix = Path(original_name).suffix.lower()
            if suffix not in SUPPORTED_VIRAL_VIDEO_SUFFIXES:
                suffix = ".mp4"

            timestamp = datetime.now(
                ZoneInfo("Asia/Seoul")
            ).strftime("%Y%m%d_%H%M%S")
            publish_path = (
                test_root
                / f"single_scene_publish_{timestamp}{suffix}"
            )

            try:
                print(
                    "[Sprint192-22 Naver Clip Publish Fragment] FILE PREPARE",
                    str(publish_path),
                    flush=True,
                )
                publish_path.write_bytes(first_clip.getbuffer())

                publish_title = (
                    f"[업로드 테스트] "
                    f"{normalize_text(product_name, '쇼핑 쇼츠')}"
                )[:100]

                naver_publish_hashtags = (
                    "#하센맘 #업로드테스트"
                    if naver_clip_upload_account == "하센맘"
                    else "#실물로그 #쇼핑쇼츠 #제품소개 #업로드테스트"
                )
                publish_description = (
                    "첫 번째 장면 네이버 클립 즉시 게시 테스트 테스트입니다.\n\n"
                    f"{naver_publish_hashtags}"
                )[:1000]

                print(
                    "[Sprint192-22 Naver Clip Actual Publish Profile]",
                    {
                        "account": naver_clip_upload_account,
                        "profile_dir": naver_clip_profile_dir,
                    },
                    flush=True,
                )

                with st.spinner(
                    "네이버 클립에 영상·설명·카테고리를 입력하고 실제 게시 중입니다..."
                ):
                    publish_result = NaverClipUploadExecutor().prepare_upload(
                        video_path=str(publish_path),
                        title=publish_title,
                        description=publish_description,
                        user_data_dir=naver_clip_profile_dir,
                        headless=False,
                        allow_manual_login=True,
                        login_timeout_seconds=600,
                        action_timeout_seconds=60,
                        slow_mo=150,
                        keep_browser_open=True,
                        category_primary="쇼핑",
                        category_secondary="상품리뷰",
                        perform_publish=True,
                    )

                st.session_state[
                    "sprint192_22_naver_clip_actual_publish_result"
                ] = publish_result

                print(
                    "[Sprint192-22 Naver Clip Publish Fragment] COMPLETE",
                    {
                        "ok": publish_result.get("ok"),
                        "status": publish_result.get("status"),
                    },
                    flush=True,
                )

                if publish_result.get("ok"):
                    st.success("네이버 클립 실제 게시가 완료됐습니다.")
                    st.write(
                        "상태:",
                        publish_result.get("status", ""),
                    )
                    st.write(
                        "최종 화면:",
                        publish_result.get("final_url", ""),
                    )
                else:
                    st.error(
                        "네이버 클립 실제 게시에 실패했습니다: "
                        f"{publish_result.get('status')} / "
                        f"{publish_result.get('errors')}"
                    )

            except Exception as exc:
                Path("full_error.log").write_text(
                    traceback.format_exc(),
                    encoding="utf-8",
                )
                print(
                    "[Sprint192-22 Naver Clip Publish Fragment] ERROR",
                    type(exc).__name__,
                    str(exc),
                    flush=True,
                )
                st.error(
                    "네이버 클립 실제 게시 실패: "
                    f"{type(exc).__name__}: {exc}"
                )

    _sprint192_22_naver_publish_fragment()

    st.markdown("---")
    st.markdown('<div class="exact-title">업로드 예약</div>', unsafe_allow_html=True)
    st.caption(
        "완성 영상 1개를 공통으로 선택한 뒤 YouTube · META(릴스) · TikTok · "
        "네이버 클립 · Threads의 제목/본문/예약시간을 한 화면에서 설정합니다."
    )

    reservation_enabled = st.checkbox(
        "선택 플랫폼 전체 예약 업로드 사용",
        value=True,
        key="sprint180_reservation_enabled",
    )

    # 공통 최종 영상: 아래 기존 프로젝트 영역에서도 같은 업로드 값을 그대로 사용합니다.
    common_video_c1, common_video_c2 = st.columns([2, 1])
    with common_video_c1:
        common_upload_video = st.file_uploader(
            "업로드할 최종 동영상 · 전체 플랫폼 공통",
            type=["mp4"],
            accept_multiple_files=False,
            key="sprint182_2_uploaded_final_video",
            help="대부분 동일 영상을 5개 플랫폼에 사용합니다. 아래 기존 프로젝트 선택으로도 대체할 수 있습니다.",
        )
    with common_video_c2:
        st.info("플랫폼별 다른 영상이 필요한 경우 기존 프로젝트/완성영상 영역에서 변경할 수 있습니다.")

    platform_order = ["youtube", "instagram", "tiktok", "naver_clip", "threads"]
    platform_labels = {
        "youtube": "YouTube Shorts",
        "instagram": "META (릴스)",
        "tiktok": "TikTok",
        "naver_clip": "네이버 클립",
        "threads": "Threads",
    }

    selected_platforms = st.multiselect(
        "업로드 플랫폼 ON/OFF",
        options=platform_order,
        default=platform_order,
        format_func=lambda value: platform_labels.get(value, value),
        key="sprint180_platforms",
    )

    link_c1, link_c2 = st.columns([2, 1])
    with link_c1:
        infock_url = st.text_input(
            "인포크링크 상품 URL",
            placeholder="https://link.inpock.co.kr/...",
            key="sprint180_infock_url",
            help="본문과 고정댓글에 자동 삽입됩니다.",
        )
    with link_c2:
        infock_image = st.file_uploader(
            "인포크링크 이미지 (선택)",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=False,
            key="sprint193_1_infock_image",
        )

    schedule_c1, schedule_c2, schedule_c3 = st.columns(3)
    tomorrow = datetime.now(ZoneInfo("Asia/Seoul")) + timedelta(days=1)
    with schedule_c1:
        reservation_date = st.date_input(
            "첫 게시 날짜",
            value=tomorrow.date(),
            key="sprint180_date",
        )
    with schedule_c2:
        reservation_time = st.time_input(
            "첫 게시 시간",
            value=tomorrow.replace(hour=9, minute=0, second=0).time(),
            key="sprint180_time",
        )
    with schedule_c3:
        platform_interval_minutes = st.number_input(
            "플랫폼 자동 간격(분)",
            min_value=0,
            max_value=1440,
            value=60,
            step=10,
            key="sprint180_interval",
        )

    preview_start = datetime.combine(
        reservation_date,
        reservation_time,
        tzinfo=ZoneInfo("Asia/Seoul"),
    )

    st.markdown("#### 플랫폼별 업로드 정보")
    st.caption(
        "각 플랫폼 행에서 채널·동영상·예약시간은 선택하고, 제목·설명·본문은 직접 입력합니다."
    )

    # 원클릭/기존 완성 영상 후보를 이 위치에서 먼저 준비합니다.
    inline_video_candidates = []
    inline_video_root = Path("exports/videos")
    if inline_video_root.exists():
        for pattern in ("*_final.mp4", "*_subtitled.mp4", "*.mp4"):
            for candidate in inline_video_root.glob(pattern):
                if candidate.is_file() and candidate.stat().st_size >= 1024:
                    value = str(candidate)
                    if value not in inline_video_candidates:
                        inline_video_candidates.append(value)
        inline_video_candidates.sort(
            key=lambda value: Path(value).stat().st_mtime,
            reverse=True,
        )

    platform_metadata = dict(platform_metadata or {})
    platform_schedule_times = {}
    platform_video_choices = {}

    header_cols = st.columns([0.85, 1.0, 1.55, 1.25, 1.25, 2.0, 1.1, 1.15, 0.8, 0.9])
    for _col, _label in zip(
        header_cols,
        ["구분", "채널명", "동영상", "제목", "설명", "본문(해시태그포함)", "고정댓글", "예약시간", "상태", "결과"],
    ):
        with _col:
            st.markdown(f"**{_label}**")

    for platform_index, platform_key in enumerate(platform_order):
        if platform_key not in list(selected_platforms or []):
            continue

        platform_label = platform_labels[platform_key]
        default_dt = preview_start + timedelta(
            minutes=int(platform_interval_minutes or 0) * platform_index
        )
        status_key = f"sprint193_1_upload_status_{platform_key}"
        result_key = f"sprint193_1_upload_result_{platform_key}"

        row = st.columns([0.85, 1.0, 1.55, 1.25, 1.25, 2.0, 1.1, 1.15, 0.8, 0.9])

        with row[0]:
            st.markdown(f"**{platform_label}**")

        with row[1]:
            if platform_key == "youtube":
                platform_channel = str(
                    youtube_upload_account
                    or _sprint194_77_default_youtube_account(production_mode)
                ).strip()
                st.write(f"📺 {platform_channel}")
            else:
                platform_channel = st.selectbox(
                    "채널명",
                    options=list(PUBLISH_ACCOUNT_PROFILES.keys()),
                    key=f"sprint193_3_{platform_key}_channel",
                    label_visibility="collapsed",
                )

        with row[2]:
            video_options = ["공통 영상"] + inline_video_candidates + ["PC 직접 선택"]
            platform_video_choice = st.selectbox(
                "동영상",
                options=video_options,
                format_func=lambda value: (
                    value if value in {"공통 영상", "PC 직접 선택"} else Path(value).name
                ),
                key=f"sprint193_3_{platform_key}_video_choice",
                label_visibility="collapsed",
            )
            if platform_video_choice == "PC 직접 선택":
                platform_video_upload = st.file_uploader(
                    f"{platform_label} MP4",
                    type=["mp4"],
                    accept_multiple_files=False,
                    key=f"sprint193_3_{platform_key}_video_upload",
                    label_visibility="collapsed",
                )
            else:
                platform_video_upload = None
            platform_video_choices[platform_key] = {
                "choice": platform_video_choice,
                "upload": platform_video_upload,
            }

        with row[3]:
            platform_title = st.text_input(
                "제목",
                key=f"sprint190_5_{platform_key}_title",
                placeholder="제목 입력",
                label_visibility="collapsed",
            )

        with row[4]:
            platform_summary = st.text_input(
                "설명",
                key=f"sprint193_3_{platform_key}_summary",
                placeholder="설명 입력",
                label_visibility="collapsed",
            )

        with row[5]:
            platform_body = st.text_area(
                "본문",
                height=78,
                key=f"sprint190_5_{platform_key}_description",
                placeholder="본문 / 해시태그 입력",
                label_visibility="collapsed",
            )

        with row[6]:
            platform_pinned_comment = st.text_area(
                "고정댓글",
                height=78,
                key=f"sprint193_1_{platform_key}_pinned_comment",
                placeholder="고정댓글",
                label_visibility="collapsed",
            )

        with row[7]:
            platform_schedule_time = st.time_input(
                "예약시간",
                value=default_dt.time().replace(second=0, microsecond=0),
                key=f"sprint193_1_{platform_key}_schedule_time",
                label_visibility="collapsed",
            )

        with row[8]:
            st.write(str(st.session_state.get(status_key) or "대기"))

        with row[9]:
            _result = str(st.session_state.get(result_key) or "")
            st.write(_result if _result else "-")

        platform_metadata[platform_key] = {
            "title": str(platform_title or "").strip(),
            "summary": str(platform_summary or "").strip(),
            "description": str(platform_body or "").strip(),
            "body": str(platform_body or "").strip(),
            "pinned_comment": str(platform_pinned_comment or "").strip(),
            "channel": str(platform_channel or "").strip(),
        }
        platform_schedule_times[platform_key] = datetime.combine(
            reservation_date,
            platform_schedule_time,
            tzinfo=ZoneInfo("Asia/Seoul"),
        )

        st.markdown("---")

    print(
        "[Sprint193-3 Platform Metadata UI]",
        {
            key: {
                "title_chars": len(str(value.get("title") or "")),
                "description_chars": len(str(value.get("description") or "")),
            }
            for key, value in dict(platform_metadata or {}).items()
        },
        flush=True,
    )

    preview_rows = []
    for platform_key in list(selected_platforms or []):
        scheduled_dt = platform_schedule_times.get(
            platform_key,
            preview_start,
        )
        status_key = f"sprint193_1_upload_status_{platform_key}"
        result_key = f"sprint193_1_upload_result_{platform_key}"
        preview_rows.append(
            {
                "구분": platform_labels.get(platform_key, platform_key),
                "예약시간": scheduled_dt.strftime("%Y-%m-%d %H:%M"),
                "상태": str(st.session_state.get(status_key) or "대기"),
                "결과": str(st.session_state.get(result_key) or ""),
            }
        )

    st.markdown("#### 예약 현황")
    if preview_rows:
        st.dataframe(
            preview_rows,
            width="stretch",
            hide_index=True,
        )
    else:
        st.warning("업로드할 플랫폼을 선택해 주세요.")

    if "naver_clip" in list(selected_platforms or []):
        naver_preview_time = platform_schedule_times.get(
            "naver_clip",
            preview_start,
        )
        st.info(
            "네이버 클립 게시 방식: 등록예약 고정 · "
            f"{naver_preview_time.strftime('%Y-%m-%d %H:%M')}"
        )

    st.markdown("---")
    st.subheader("네이버 클립 등록예약 테스트")
    st.caption(
        "테스트용 MP4를 직접 넣어 네이버 자체 등록예약만 실행합니다. "
        "기존 프로젝트 불러오기는 사용하지 않습니다."
    )

    naver_manual_test_video = st.file_uploader(
        "네이버 테스트용 MP4",
        type=["mp4", "mov", "m4v", "webm"],
        key="sprint192_32_naver_manual_test_video",
    )

    if st.button(
        "네이버 클립 등록예약 테스트 실행",
        type="primary",
        width="stretch",
        key="sprint192_32_naver_manual_schedule_run",
    ):
        if naver_manual_test_video is None:
            st.error("테스트할 MP4를 직접 선택해 주세요.")
        elif "naver_clip" not in list(selected_platforms or []):
            st.error("예약 플랫폼에서 네이버 클립을 선택해 주세요.")
        else:
            try:
                test_root = Path("assets/naver_clip_test_uploads")
                test_root.mkdir(parents=True, exist_ok=True)

                original_name = str(
                    getattr(naver_manual_test_video, "name", "naver_test.mp4")
                    or "naver_test.mp4"
                )
                suffix = Path(original_name).suffix.lower()
                if suffix not in {".mp4", ".mov", ".m4v", ".webm"}:
                    suffix = ".mp4"

                timestamp = datetime.now(
                    ZoneInfo("Asia/Seoul")
                ).strftime("%Y%m%d_%H%M%S")
                manual_video_path = (
                    test_root / f"oneclick_manual_schedule_{timestamp}{suffix}"
                )
                manual_video_path.write_bytes(
                    naver_manual_test_video.getbuffer()
                )

                selected_platform_list = list(selected_platforms or [])
                naver_index = selected_platform_list.index("naver_clip")
                manual_schedule_at = platform_schedule_times.get(
                    "naver_clip",
                    datetime.combine(
                        reservation_date,
                        reservation_time,
                        tzinfo=ZoneInfo("Asia/Seoul"),
                    ) + timedelta(
                        minutes=int(platform_interval_minutes or 0) * naver_index
                    ),
                )
                scheduled_iso = manual_schedule_at.isoformat(timespec="minutes")

                naver_override = dict(
                    (platform_metadata or {}).get("naver_clip") or {}
                )
                manual_title = (
                    str(naver_override.get("title") or "").strip()
                    or str(product_name or "").strip()
                    or Path(original_name).stem
                )
                manual_description = str(
                    naver_override.get("description") or ""
                ).strip()

                print(
                    "[Sprint192-32 Naver Manual Schedule] START",
                    {
                        "account": naver_clip_upload_account,
                        "profile_dir": naver_clip_profile_dir,
                        "video_path": str(manual_video_path),
                        "scheduled_publish_at": scheduled_iso,
                    },
                    flush=True,
                )

                with st.spinner(
                    "네이버 클립 영상 업로드 → 쇼핑/상품리뷰 → 등록예약 → 날짜/시간 → 등록 중입니다..."
                ):
                    manual_result = NaverClipUploadExecutor().prepare_upload(
                        video_path=str(manual_video_path),
                        title=manual_title,
                        description=manual_description,
                        user_data_dir=naver_clip_profile_dir,
                        headless=False,
                        allow_manual_login=True,
                        login_timeout_seconds=600,
                        action_timeout_seconds=60,
                        slow_mo=150,
                        keep_browser_open=True,
                        category_primary="쇼핑",
                        category_secondary="상품리뷰",
                        perform_publish=True,
                        scheduled_publish_at=scheduled_iso,
                    )

                st.session_state[
                    "sprint192_32_naver_manual_schedule_result"
                ] = manual_result

                print(
                    "[Sprint192-32 Naver Manual Schedule] COMPLETE",
                    {
                        "ok": manual_result.get("ok"),
                        "status": manual_result.get("status"),
                        "scheduled_publish_at": manual_result.get(
                            "scheduled_publish_at"
                        ),
                        "final_url": manual_result.get("final_url"),
                    },
                    flush=True,
                )

                if manual_result.get("ok"):
                    st.success(
                        "네이버 클립 등록예약 테스트가 완료됐습니다."
                    )
                    st.write(
                        "예약시간:",
                        manual_result.get(
                            "scheduled_publish_at",
                            scheduled_iso,
                        ),
                    )
                    st.write("상태:", manual_result.get("status", ""))
                else:
                    st.error(
                        "네이버 클립 등록예약 테스트 실패: "
                        f"{manual_result.get('status')} / "
                        f"{manual_result.get('errors')}"
                    )
                    screenshot = str(
                        manual_result.get("failure_screenshot") or ""
                    )
                    if screenshot:
                        st.caption(f"실패 화면: {screenshot}")

            except Exception as exc:
                Path("full_error.log").write_text(
                    traceback.format_exc(),
                    encoding="utf-8",
                )
                print(
                    "[Sprint192-32 Naver Manual Schedule] ERROR",
                    type(exc).__name__,
                    str(exc),
                    flush=True,
                )
                st.error(
                    "네이버 클립 등록예약 테스트 실행 실패: "
                    f"{type(exc).__name__}: {exc}"
                )

    st.markdown("---")
    st.subheader("기존 프로젝트 또는 완성 영상 불러오기")
    st.caption(
        "프로젝트를 선택하면 영상·제목·본문·고정댓글·해시태그를 함께 복원합니다. "
        "완성 MP4만 선택하거나 PC에서 직접 업로드할 수도 있습니다."
    )

    content_library = ContentLibrary()
    library_c1, library_c2 = st.columns([2, 1])
    with library_c1:
        library_query = st.text_input(
            "콘텐츠 검색",
            placeholder="상품명, 프로젝트 번호, 제목 검색",
            key="sprint180_4_library_query",
        )
    with library_c2:
        library_status = st.selectbox(
            "상태 필터",
            options=["all", "unscheduled", "scheduled", "published", "failed"],
            format_func=lambda value: {
                "all": "전체",
                "unscheduled": "예약 안 함",
                "scheduled": "예약 완료",
                "published": "게시 완료",
                "failed": "실패/재시도",
            }[value],
            key="sprint180_4_library_status",
        )

    all_project_candidates = content_library.list(
        query=library_query,
        status=library_status,
        limit=5000,
    )

    status_labels = {
        "unscheduled": "⚪ 예약 안 함",
        "scheduled": "🟡 예약 완료",
        "published": "🟢 게시 완료",
        "failed": "🔴 실패/재시도",
    }

    page_size = 30
    total_count = len(all_project_candidates)
    total_pages = max(1, (total_count + page_size - 1) // page_size)
    page_key = "sprint180_6_library_page"
    current_page = int(st.session_state.get(page_key, 1) or 1)
    current_page = max(1, min(current_page, total_pages))
    st.session_state[page_key] = current_page

    st.caption(f"검색 결과: {total_count}개 · 한 페이지에 {page_size}개 표시")
    nav_c1, nav_c2, nav_c3 = st.columns([1, 2, 1])
    with nav_c1:
        if st.button("◀ 이전", disabled=current_page <= 1, key="sprint180_6_prev"):
            st.session_state[page_key] = current_page - 1
            st.rerun()
    with nav_c2:
        requested_page = st.number_input(
            "페이지",
            min_value=1,
            max_value=total_pages,
            value=current_page,
            step=1,
            key="sprint180_6_page_input",
        )
        if int(requested_page) != current_page:
            st.session_state[page_key] = int(requested_page)
            st.rerun()
        st.caption(f"{current_page} / {total_pages}")
    with nav_c3:
        if st.button("다음 ▶", disabled=current_page >= total_pages, key="sprint180_6_next"):
            st.session_state[page_key] = current_page + 1
            st.rerun()

    page_start = (current_page - 1) * page_size
    project_candidates = all_project_candidates[page_start:page_start + page_size]
    project_by_key = {item["key"]: item for item in project_candidates}

    if project_candidates:
        for item in project_candidates:
            metadata = dict(item.get("metadata") or {})
            project_label = f"project_{item.get('project_id')}"
            product_label = metadata.get("product_name") or "상품명 없음"
            video_name = Path(str(item.get("video_path") or "")).name or "영상 없음"
            status_label = status_labels.get(item.get("library_status"), str(item.get("library_status") or ""))
            with st.container(border=True):
                row_c1, row_c2, row_c3 = st.columns([3, 2, 1])
                with row_c1:
                    st.markdown(f"**{project_label} · {product_label}**")
                    st.caption(video_name)
                with row_c2:
                    st.write(status_label)
                    st.caption(
                        f"예약 {int(item.get('reservation_count') or 0)} · "
                        f"게시 {int(item.get('published_count') or 0)}"
                    )
                with row_c3:
                    if st.button("불러오기", key=f"sprint180_6_load_{item['key']}"):
                        st.session_state["sprint180_6_selected_project_key"] = item["key"]
                        st.rerun()
    else:
        st.warning("검색된 프로젝트가 없습니다. exports/videos와 assets/products 경로를 확인해 주세요.")
        st.caption(f"검색 기준 루트: {content_library.loader.project_root}")

    selected_default = str(st.session_state.get("sprint180_6_selected_project_key") or "")
    selected_options = [""] + list(project_by_key.keys())
    selected_index = selected_options.index(selected_default) if selected_default in selected_options else 0
    selected_project_key = st.selectbox(
        "기존 프로젝트 불러오기",
        options=selected_options,
        index=selected_index,
        format_func=lambda value: "선택 안 함" if not value else (
            f"{status_labels.get(project_by_key[value].get('library_status'), '')} · "
            f"{project_by_key[value].get('label', value)}"
        ),
        key="sprint180_4_existing_project",
        help="콘텐츠 라이브러리에서 프로젝트와 게시 상태를 함께 검색합니다.",
    )
    selected_project = project_by_key.get(selected_project_key) or {}
    restored = dict(selected_project.get("metadata") or {})
    if selected_project:
        info_c1, info_c2, info_c3 = st.columns(3)
        info_c1.metric("프로젝트", str(selected_project.get("project_id") or "-"))
        info_c2.metric("영상", Path(str(selected_project.get("video_path") or "")).name or "-")
        info_c3.metric("상태", status_labels.get(selected_project.get("library_status"), "영상 없음"))
        published_urls = list(selected_project.get("published_urls") or [])
        if published_urls:
            st.caption("게시 URL")
            for published_url in published_urls:
                st.code(published_url, language=None)
        if selected_project.get("last_error"):
            st.error(f"최근 게시 오류: {selected_project.get('last_error')}")
        if selected_project.get("thumbnail_path") and Path(str(selected_project["thumbnail_path"])).is_file():
            st.image(str(selected_project["thumbnail_path"]), width=180)

    # Sprint182-6: 메타데이터 생성 버튼을 입력 위젯보다 먼저 실행합니다.
    # Streamlit은 이미 생성된 위젯의 session_state 값을 같은 실행에서 바꾸지 못하므로,
    # 영상 선택 → 생성 버튼 → session_state 저장 → 입력 위젯 렌더 순서를 고정합니다.
    restored_product_key = f"sprint180_4_restored_product_{selected_project_key}"
    restored_title_key = f"sprint180_4_restored_title_{selected_project_key}"
    restored_description_key = f"sprint180_4_restored_description_{selected_project_key}"
    restored_comment_key = f"sprint180_4_restored_comment_{selected_project_key}"
    restored_hashtags_key = f"sprint180_4_restored_hashtags_{selected_project_key}"

    # 프로젝트가 바뀌었을 때만 저장된 메타데이터를 초기값으로 복원합니다.
    metadata_context_key = "sprint182_6_metadata_context"
    metadata_context = str(selected_project_key or "pc_upload")
    if st.session_state.get(metadata_context_key) != metadata_context:
        st.session_state[metadata_context_key] = metadata_context
        st.session_state[restored_product_key] = str(
            restored.get("product_name") or product_name or ""
        )
        st.session_state[restored_title_key] = str(restored.get("title") or "")
        st.session_state[restored_description_key] = str(
            restored.get("description") or restored.get("body") or ""
        )
        st.session_state[restored_comment_key] = str(
            restored.get("pinned_comment") or restored.get("comment") or ""
        )
        restored_tags = restored.get("hashtags") or restored.get("tags") or []
        if isinstance(restored_tags, str):
            restored_tags = [
                value.lstrip("#")
                for value in re.split(r"[\s,]+", restored_tags)
                if value.strip().lstrip("#")
            ]
        st.session_state[restored_hashtags_key] = " ".join(
            value if str(value).startswith("#") else f"#{value}"
            for value in list(restored_tags or [])
            if str(value).strip()
        )

    existing_video_candidates = []
    existing_video_root = Path("exports/videos")
    if existing_video_root.exists():
        for pattern in ("*_final.mp4", "*_subtitled.mp4", "*.mp4"):
            for candidate in existing_video_root.glob(pattern):
                if candidate.is_file() and candidate.stat().st_size >= 1024:
                    value = str(candidate)
                    if value not in existing_video_candidates:
                        existing_video_candidates.append(value)
        existing_video_candidates.sort(
            key=lambda value: Path(value).stat().st_mtime,
            reverse=True,
        )

    load_c1, load_c2 = st.columns(2)
    with load_c1:
        selected_existing_video = st.selectbox(
            "기존 완성 영상 선택",
            options=[""] + existing_video_candidates,
            format_func=lambda value: "선택 안 함" if not value else Path(value).name,
            key="sprint180_2_existing_final_video",
            help="exports/videos 폴더에 저장된 최신 MP4가 위쪽에 표시됩니다.",
        )
    with load_c2:
        uploaded_completed_video = common_upload_video
        if uploaded_completed_video is not None:
            st.success(
                "상단 '업로드할 최종 동영상'을 공통 영상으로 사용합니다: "
                f"{getattr(uploaded_completed_video, 'name', 'completed.mp4')}"
            )
        else:
            st.caption("상단 업로드 예약 영역에서 공통 MP4를 선택할 수 있습니다.")

    uploaded_session_path = str(
        st.session_state.get("sprint182_2_uploaded_video_path") or ""
    ).strip()
    uploaded_session_name = str(
        st.session_state.get("sprint182_2_uploaded_video_name") or ""
    ).strip()

    if uploaded_completed_video is not None:
        upload_bytes = uploaded_completed_video.getvalue()
        upload_signature = hashlib.sha256(upload_bytes).hexdigest()
        previous_signature = str(
            st.session_state.get("sprint182_2_uploaded_video_signature") or ""
        )
        if upload_signature != previous_signature or not Path(uploaded_session_path).is_file():
            upload_root = Path("exports/scheduled_upload_inputs")
            upload_root.mkdir(parents=True, exist_ok=True)
            original_name = getattr(
                uploaded_completed_video, "name", "completed.mp4"
            ) or "completed.mp4"
            stem = safe_file_name(Path(original_name).stem, fallback="completed")
            timestamp = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d_%H%M%S")
            upload_target = upload_root / f"{timestamp}_{stem}.mp4"
            upload_target.write_bytes(upload_bytes)
            uploaded_session_path = str(upload_target)
            uploaded_session_name = original_name
            st.session_state["sprint182_2_uploaded_video_path"] = uploaded_session_path
            st.session_state["sprint182_2_uploaded_video_name"] = uploaded_session_name
            st.session_state["sprint182_2_uploaded_video_signature"] = upload_signature

    if uploaded_session_path and Path(uploaded_session_path).is_file():
        selected_info_c1, selected_info_c2 = st.columns([5, 1])
        with selected_info_c1:
            st.success(
                f"선택 영상 유지 중: {uploaded_session_name or Path(uploaded_session_path).name}"
            )
            st.caption(uploaded_session_path)
        with selected_info_c2:
            if st.button(
                "선택 해제",
                key="sprint182_2_clear_uploaded_video",
                use_container_width=True,
            ):
                st.session_state.pop("sprint182_2_uploaded_video_path", None)
                st.session_state.pop("sprint182_2_uploaded_video_name", None)
                st.session_state.pop("sprint182_2_uploaded_video_signature", None)
                st.session_state.pop("sprint182_2_uploaded_final_video", None)
                st.rerun()

    selected_video_for_metadata = str(
        uploaded_session_path
        or selected_existing_video
        or selected_project.get("video_path")
        or ""
    ).strip()

    if st.button(
        "📦 저장된 게시 메타데이터 불러오기",
        use_container_width=True,
        key="sprint183_2_restore_metadata",
        help="저장된 프로젝트 게시 메타데이터를 우선 복원하고, 없는 항목만 대본과 영상 정보로 보완합니다.",
    ):
        selected_project_id = str(selected_project.get("project_id") or "").strip()
        project_metadata = _restore_project_publisher_metadata(
            selected_project_id,
            selected_metadata=restored,
        )

        current_product_name = str(
            project_metadata.get("product_name")
            or st.session_state.get(restored_product_key)
            or restored.get("product_name")
            or product_name
            or ""
        ).strip()

        filename_stem = safe_file_name(
            Path(selected_video_for_metadata).stem if selected_video_for_metadata else "",
            fallback="",
        )
        filename_stem = re.sub(
            r"(?:_final|_subtitled|_merged|_image_motion|_shorts)+$",
            "",
            filename_stem,
            flags=re.IGNORECASE,
        ).strip("_")
        if filename_stem.isdigit() or re.fullmatch(
            r"(?:project_)?\d+", filename_stem, re.IGNORECASE
        ):
            filename_stem = ""

        product_basis = current_product_name or filename_stem
        script_basis = str(
            project_metadata.get("locked_script")
            or restored.get("locked_script")
            or restored.get("best_script")
            or locked_script
            or ""
        ).strip()
        hook_basis = str(
            project_metadata.get("hook_text")
            or restored.get("hook_text")
            or restored.get("best_hook")
            or hook_text
            or ""
        ).strip()
        cta_basis = str(
            project_metadata.get("cta_text")
            or restored.get("cta_text")
            or cta_text
            or ""
        ).strip()
        link_basis = str(
            infock_url
            or project_metadata.get("infock_url")
            or restored.get("infock_url")
            or ""
        ).strip()

        stored_title = str(project_metadata.get("title") or "").strip()
        if stored_title:
            auto_title = stored_title
        elif hook_basis:
            auto_title = next(
                (line.strip() for line in hook_basis.splitlines() if line.strip()),
                "",
            )
        elif product_basis and int(monthly_purchase_count or 0) > 0:
            auto_title = (
                f"{product_basis}, 최근 한 달 {int(monthly_purchase_count):,}명 이상 구매한 이유"
            )
        elif product_basis:
            auto_title = f"{product_basis}, 왜 이렇게 인기일까요?"
        elif script_basis:
            auto_title = next(
                (line.strip() for line in script_basis.splitlines() if line.strip()),
                "이 제품이 인기 있는 이유",
            )
        else:
            auto_title = "써보면 이유를 알게 되는 생활 꿀템"
        auto_title = re.sub(r"\s+", " ", auto_title).strip()[:95]

        stored_description = str(project_metadata.get("description") or "").strip()
        stored_comment = str(project_metadata.get("pinned_comment") or "").strip()
        stored_tags = list(project_metadata.get("hashtags") or [])

        built = ScheduledMetadataBuilder.build(
            product_name=product_basis or auto_title,
            hook_text=hook_basis or auto_title,
            locked_script=script_basis,
            cta_text=cta_basis,
            infock_url=link_basis,
            hashtags=stored_tags,
            title_override=auto_title,
            description_override=stored_description,
            pinned_comment_override=stored_comment,
        )

        generated_title = str(built.get("title") or auto_title).strip()
        generated_description = str(
            built.get("description")
            or built.get("body")
            or built.get("caption")
            or stored_description
            or ""
        ).strip()
        generated_comment = str(
            built.get("pinned_comment")
            or built.get("comment")
            or built.get("first_comment")
            or stored_comment
            or ""
        ).strip()
        generated_tags = built.get("hashtags") or built.get("tags") or stored_tags
        if isinstance(generated_tags, str):
            generated_tags = [
                value.lstrip("#")
                for value in re.split(r"[\s,]+", generated_tags)
                if value.strip().lstrip("#")
            ]
        generated_hashtag_text = " ".join(
            value if str(value).startswith("#") else f"#{value}"
            for value in list(generated_tags or [])
            if str(value).strip()
        )

        if not generated_description:
            description_lines = [generated_title]
            if script_basis:
                script_lines = [
                    line.strip()
                    for line in script_basis.splitlines()
                    if line.strip()
                ]
                description_lines.extend(script_lines[:6])
            description_lines.append("실제 후기를 바탕으로 제작한 영상입니다.")
            if link_basis:
                description_lines.extend(["", "👇 구매 링크", link_basis])
            generated_description = "\n".join(description_lines)

        if not generated_comment:
            generated_comment = "궁금하신 제품 정보는 아래 링크에서 확인해 주세요."
            if link_basis:
                generated_comment += f"\n\n👇 구매 링크\n{link_basis}"

        if not generated_hashtag_text:
            raw_words = re.findall(
                r"[0-9A-Za-z가-힣]+", product_basis or generated_title
            )
            stop_words = {
                "최근", "한", "달", "이상", "구매한", "이유",
                "왜", "이렇게", "인기일까요",
            }
            tags = []
            for word in raw_words:
                if len(word) < 2 or word in stop_words or word in tags:
                    continue
                tags.append(word)
                if len(tags) >= 4:
                    break
            for fallback_tag in ("살림템", "생활꿀템", "쇼핑쇼츠"):
                if fallback_tag not in tags:
                    tags.append(fallback_tag)
            generated_hashtag_text = " ".join(
                f"#{tag}" for tag in tags[:7]
            )

        if product_basis:
            st.session_state[restored_product_key] = product_basis
        st.session_state[restored_title_key] = generated_title
        st.session_state[restored_description_key] = generated_description
        st.session_state[restored_comment_key] = generated_comment
        st.session_state[restored_hashtags_key] = generated_hashtag_text
        st.session_state["sprint183_2_metadata_loaded"] = True

        print(
            "[Sprint183-2 Publisher Metadata Restore] LOADED:",
            {
                "title": generated_title,
                "description_chars": len(generated_description),
                "comment_chars": len(generated_comment),
                "hashtags": generated_hashtag_text,
                "video": selected_video_for_metadata,
            },
            flush=True,
        )

    if st.session_state.get("sprint183_2_metadata_loaded"):
        st.success("영상 제목·본문·고정댓글·해시태그를 자동으로 채웠습니다.")

    # 생성 버튼 이후에 위젯을 만들기 때문에 같은 실행에서 채운 값이 즉시 표시됩니다.
    restored_product_name = st.text_input(
        "불러온 상품명",
        key=restored_product_key,
    )
    restored_title = st.text_input(
        "영상 제목",
        key=restored_title_key,
    )
    meta_c1, meta_c2 = st.columns(2)
    with meta_c1:
        restored_description = st.text_area(
            "본문",
            height=150,
            key=restored_description_key,
        )
    with meta_c2:
        restored_pinned_comment = st.text_area(
            "고정 댓글",
            height=150,
            key=restored_comment_key,
        )
    restored_hashtags = st.text_input(
        "해시태그",
        key=restored_hashtags_key,
    )

    existing_schedule_clicked = st.button(
        "선택 플랫폼 전체 예약 업로드",
        use_container_width=True,
        key="sprint182_2_schedule_existing_video",
    )

    if existing_schedule_clicked:
        existing_errors = []
        if not reservation_enabled:
            existing_errors.append("예약 업로드를 켜주세요.")
        if not selected_platforms:
            existing_errors.append("예약할 플랫폼을 한 개 이상 선택해 주세요.")

        selected_video_path = str(
            uploaded_session_path
            or selected_existing_video
            or selected_project.get("video_path")
            or ""
        ).strip()

        if not selected_video_path or not Path(selected_video_path).is_file():
            existing_errors.append("예약할 완성 MP4를 선택하거나 업로드해 주세요.")

        if existing_errors:
            for error in existing_errors:
                st.error(error)
        else:
            try:
                parsed_hashtags = [
                    value.lstrip("#")
                    for value in re.split(r"[\s,]+", str(restored_hashtags or ""))
                    if value.strip().lstrip("#")
                ]
                metadata = ScheduledMetadataBuilder.build(
                    product_name=str(restored_product_name or product_name or restored_title or Path(selected_video_path).stem).strip(),
                    hook_text=str(restored.get("hook_text") or hook_text or "").strip(),
                    locked_script=str(restored.get("locked_script") or locked_script or "").strip(),
                    cta_text=str(restored.get("cta_text") or cta_text or "").strip(),
                    infock_url=str(infock_url or restored.get("infock_url") or "").strip(),
                    hashtags=parsed_hashtags,
                    title_override=str(restored_title or "").strip(),
                    description_override=str(restored_description or "").strip(),
                    pinned_comment_override=str(restored_pinned_comment or "").strip(),
                )
                metadata["youtube_privacy_status"] = youtube_privacy_status
                metadata["source"] = "existing_completed_video"
                metadata["source_video_path"] = selected_video_path

                local_start = datetime.combine(
                    reservation_date,
                    reservation_time,
                    tzinfo=ZoneInfo("Asia/Seoul"),
                )
                queue = ReservationQueue()
                created_items = []
                naver_native_result = None
                project_key = str(
                    selected_project.get("project_id")
                    or f"existing_{safe_file_name(Path(selected_video_path).stem)}"
                )

                for platform_index, platform in enumerate(list(selected_platforms or [])):
                    scheduled_at = platform_schedule_times.get(
                        str(platform),
                        local_start + timedelta(
                            minutes=int(platform_interval_minutes or 0) * platform_index
                        ),
                    )
                    platform_key = str(platform)
                    platform_payload = dict(metadata)
                    platform_override = dict(
                        (platform_metadata or {}).get(platform_key) or {}
                    )
                    platform_title = str(
                        platform_override.get("title") or ""
                    ).strip()
                    platform_description = str(
                        platform_override.get("description") or ""
                    ).strip()

                    if platform_title:
                        platform_payload["title"] = platform_title
                        platform_payload[f"{platform_key}_title"] = platform_title
                    if platform_description:
                        platform_payload["description"] = platform_description
                        platform_payload["caption"] = platform_description
                        platform_payload[f"{platform_key}_description"] = platform_description

                    platform_payload["platform"] = platform_key
                    if platform_key == "youtube":
                        platform_payload["youtube_account"] = str(
                            platform_override.get("channel")
                            or youtube_upload_account
                            or _sprint194_77_default_youtube_account(production_mode)
                        ).strip()
                        print(
                            "[Sprint194-77-1 YouTube Channel Route]",
                            {
                                "account": platform_payload["youtube_account"],
                                "production_mode": production_mode,
                                "video_path": selected_video_path,
                            },
                            flush=True,
                        )

                    # Sprint192-31:
                    # 네이버 클립은 ReservationQueue에 넣지 않고 지금 바로
                    # 네이버 자체 '등록예약'으로 저장합니다.
                    if platform_key == "naver_clip":
                        naver_title = (
                            platform_title
                            or str(platform_payload.get("title") or "").strip()
                            or str(restored_product_name or product_name or "").strip()
                            or Path(selected_video_path).stem
                        )
                        naver_description = (
                            platform_description
                            or str(platform_payload.get("description") or "").strip()
                            or str(restored_description or "").strip()
                        )
                        scheduled_iso = scheduled_at.isoformat(timespec="minutes")

                        print(
                            "[Sprint192-31 Naver Native Schedule] START",
                            {
                                "account": naver_clip_upload_account,
                                "profile_dir": naver_clip_profile_dir,
                                "video_path": selected_video_path,
                                "scheduled_publish_at": scheduled_iso,
                            },
                            flush=True,
                        )

                        with st.spinner(
                            "네이버 클립 → 쇼핑/상품리뷰 → 등록예약 → 날짜/시간 → 등록 중입니다..."
                        ):
                            naver_native_result = NaverClipUploadExecutor().prepare_upload(
                                video_path=selected_video_path,
                                title=naver_title,
                                description=naver_description,
                                user_data_dir=naver_clip_profile_dir,
                                headless=False,
                                allow_manual_login=True,
                                login_timeout_seconds=600,
                                action_timeout_seconds=60,
                                slow_mo=150,
                                keep_browser_open=True,
                                category_primary="쇼핑",
                                category_secondary="상품리뷰",
                                perform_publish=True,
                                scheduled_publish_at=scheduled_iso,
                            )

                        print(
                            "[Sprint192-31 Naver Native Schedule] COMPLETE",
                            {
                                "ok": naver_native_result.get("ok"),
                                "status": naver_native_result.get("status"),
                                "scheduled_publish_at": naver_native_result.get(
                                    "scheduled_publish_at"
                                ),
                                "final_url": naver_native_result.get("final_url"),
                            },
                            flush=True,
                        )
                        continue

                    created_items.append(
                        queue.enqueue(
                            project_id=project_key,
                            platform=platform_key,
                            scheduled_at=scheduled_at,
                            video_path=selected_video_path,
                            payload=platform_payload,
                        )
                    )

                if created_items:
                    st.success(
                        f"YouTube/Instagram/TikTok/Threads 예약 큐 등록 완료: {len(created_items)}건"
                    )
                    for _platform in list(selected_platforms or []):
                        if _platform != "naver_clip":
                            st.session_state[
                                f"sprint193_1_upload_status_{_platform}"
                            ] = "예약완료"
                if "naver_clip" in list(selected_platforms or []):
                    if naver_native_result and naver_native_result.get("ok"):
                        st.session_state[
                            "sprint193_1_upload_status_naver_clip"
                        ] = "예약완료"
                        st.success(
                            "네이버 클립 자체 등록예약 완료: "
                            f"{naver_native_result.get('scheduled_publish_at', '')}"
                        )
                    else:
                        st.error(
                            "네이버 클립 자체 등록예약 실패: "
                            f"{(naver_native_result or {}).get('status')} / "
                            f"{(naver_native_result or {}).get('errors')}"
                        )
                st.video(selected_video_path)
                reservation_rows = []
                platform_names = {
                    "youtube": "YouTube Shorts",
                    "instagram": "Instagram Reels",
                    "tiktok": "TikTok",
                    "naver_clip": "네이버 클립",
                }
                for item in created_items:
                    utc_value = datetime.fromisoformat(str(item.get("scheduled_at_utc") or ""))
                    local_value = utc_value.astimezone(ZoneInfo("Asia/Seoul"))
                    reservation_rows.append({
                        "플랫폼": platform_names.get(item.get("platform"), item.get("platform")),
                        "예약시간": local_value.strftime("%Y-%m-%d %H:%M"),
                        "상태": item.get("status"),
                        "영상": Path(str(item.get("video_path") or "")).name,
                    })
                if naver_native_result:
                    naver_scheduled = str(
                        naver_native_result.get("scheduled_publish_at") or ""
                    )
                    try:
                        naver_local = datetime.fromisoformat(naver_scheduled)
                        naver_time_text = naver_local.astimezone(
                            ZoneInfo("Asia/Seoul")
                        ).strftime("%Y-%m-%d %H:%M")
                    except Exception:
                        naver_time_text = naver_scheduled
                    reservation_rows.append({
                        "플랫폼": "네이버 클립",
                        "예약시간": naver_time_text,
                        "상태": (
                            "네이버 등록예약 완료"
                            if naver_native_result.get("ok")
                            else str(naver_native_result.get("status") or "실패")
                        ),
                        "영상": Path(selected_video_path).name,
                    })
                st.dataframe(reservation_rows, use_container_width=True, hide_index=True)
                print(
                    "[Sprint180-4 Project Reservation] SCHEDULED:",
                    len(created_items),
                    selected_video_path,
                    flush=True,
                )
            except Exception as exc:
                st.error(f"기존 영상 예약 등록 실패: {type(exc).__name__}: {exc}")

    with st.expander("현재 예약 목록", expanded=True):
        try:
            queue_items = ReservationQueue().list(limit=100)
            if not queue_items:
                st.caption("등록된 예약이 없습니다.")
            else:
                platform_names = {
                    "youtube": "YouTube Shorts",
                    "instagram": "Instagram Reels",
                    "tiktok": "TikTok",
                    "naver_clip": "네이버 클립",
                }
                queue_rows = []
                for item in queue_items:
                    utc_value = datetime.fromisoformat(str(item.get("scheduled_at_utc") or ""))
                    local_value = utc_value.astimezone(ZoneInfo("Asia/Seoul"))
                    queue_rows.append({
                        "ID": str(item.get("id") or "")[:8],
                        "플랫폼": platform_names.get(item.get("platform"), item.get("platform")),
                        "예약시간": local_value.strftime("%Y-%m-%d %H:%M"),
                        "상태": item.get("status"),
                        "영상": Path(str(item.get("video_path") or "")).name,
                        "오류": str(item.get("last_error") or "")[:120],
                    })
                st.dataframe(queue_rows, use_container_width=True, hide_index=True)
        except Exception as exc:
            st.warning(f"예약 목록을 불러오지 못했습니다: {exc}")


    # 버튼 호출은 여기서 하지만 top_create_slot에 렌더링되므로 화면 맨 위에 표시됩니다.
    top_create_clicked = top_create_slot.button(
        "🎬 영상만 제작",
        type="primary",
        use_container_width=True,
        key="sprint189_5_create_only_top",
    )

    run_requested = bool(
        top_create_clicked or create_only_clicked or create_upload_clicked
    )
    if not run_requested:
        return

    upload_enabled = bool(create_upload_clicked)

    print(
        "[Sprint189-5 Run Mode]",
        {
            "top_create_clicked": bool(top_create_clicked),
            "lower_create_clicked": bool(create_only_clicked),
            "create_and_upload": bool(create_upload_clicked),
            "upload_enabled": bool(upload_enabled),
        },
        flush=True,
    )

    errors = []
    if not str(product_name or "").strip():
        errors.append("역사 주제를 입력해 주세요." if is_history_mode else "상품명을 입력해 주세요.")
    if not str(locked_script or "").strip():
        errors.append("확정 대본을 입력해 주세요.")
    if not editor_clip_sources:
        errors.append("역사 장면 이미지를 한 장 이상 업로드하거나 이전 작업을 불러와 주세요." if is_history_mode else "Gemini 영상 파일을 한 개 이상 업로드해 주세요.")
    if is_history_mode and uploaded_history_scene_images:
        _ids = []
        for _item in uploaded_history_scene_images:
            _m = re.search(r"(\d+)", Path(str(getattr(_item, "name", "") or "")).stem)
            if _m:
                _ids.append(int(_m.group(1)))
        _effective_count = len(uploaded_history_scene_images) + (1 if uploaded_history_scene1_video is not None and 1 not in set(_ids) else 0)
        if _effective_count != int(history_expected_scene_count or 0):
            errors.append(
                f"역사 장면 수를 확인해 주세요. 목표 {int(history_expected_scene_count)}장 / 유효 장면 {_effective_count}장"
            )
    if errors:
        for error in errors:
            st.error(error)
        return

    payload = {
        "coupang_url": "",
        "product_name": product_name.strip(),
        "title": product_name.strip(),
        "source": ("manual_history_image_edit_194_4" if is_history_mode else "manual_gemini_video_edit_189_2"),
        "hook_text": hook_text.strip(),
        "suppress_separate_hook": False,
        "locked_script": locked_script.strip(),
        "clip_subtitles": list(clip_subtitles or []),
        "clip_narrations": list(clip_narrations or []),
        "clip_subtitle_effects": list(clip_subtitle_effects or []),
        "clip_sfx": list(clip_sfx or []),
        "clip_playback_speeds": list(clip_playback_speeds or []),
        "subtitle_style": dict(subtitle_style or {}),
        "cta_text": cta_text.strip(),
        "cta_platform": str(video_cta_platform),
        "cta_keyword": str(cta_keyword or "").strip(),
        "gemini_clip_count": len(editor_clip_sources),
        "youtube_privacy_status": youtube_privacy_status,
        "upload_enabled": bool(upload_enabled),
        "channel_type": channel_type,
        "playback_speed": float(playback_speed),
        "voice_name": str(selected_voice_name or "지안"),
        "voice_id": str(selected_voice_id or ""),
        "monthly_purchase_count": int(monthly_purchase_count or 0),
        "declared_review_count": int(declared_review_count or 0),
        "rating": float(rating or 0.0),
        "reservation_enabled": bool(reservation_enabled),
        "reservation_platforms": list(selected_platforms or []),
        "infock_url": str(infock_url or "").strip(),
        "platform_metadata": dict(platform_metadata or {}),
        "youtube_account": str(
            youtube_upload_account
            or _sprint194_77_default_youtube_account(production_mode)
        ).strip(),
    }
    try:
        project = create_project_from_payload(payload, [product_name.strip()])
        project_id = getattr(project, "id", None)
        if project_id:
            project = ProjectRepository().get(project_id) or project
    except Exception as exc:
        st.error(f"프로젝트 생성 실패: {exc}")
        return

    _save_clip_subtitle_sidecar(
        project,
        clip_subtitles,
        subtitle_style,
        clip_narrations,
        clip_subtitle_effects,
        clip_sfx,
        clip_playback_speeds,
    )

    hook_product_image_path = ""
    if hook_product_image is not None:
        product_folder = Path("assets/products") / f"project_{safe_project_id(project)}"
        product_folder.mkdir(parents=True, exist_ok=True)
        suffix = Path(getattr(hook_product_image, "name", "product.jpg")).suffix.lower()
        if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
            suffix = ".jpg"
        product_target = product_folder / f"00_main{suffix}"
        product_target.write_bytes(hook_product_image.getbuffer())
        hook_product_image_path = str(product_target)
        print(
            "[Sprint189-1 Hook Product BG] SAVED:",
            hook_product_image_path,
            flush=True,
        )

    folder = Path("assets/gemini_clips") / f"project_{safe_project_id(project)}"
    folder.mkdir(parents=True, exist_ok=True)
    clip_paths = []
    if is_history_mode and uploaded_history_scene_images:
        try:
            clip_paths = _sprint194_4_save_history_scene_images(
                project, uploaded_history_scene_images, clip_narrations, _effective_tts_speech_speed_194_41, uploaded_history_scene1_video
            )
        except Exception as exc:
            st.error(f"역사 장면 이미지 영상 변환 실패: {type(exc).__name__}: {exc}")
            return
    elif uploaded_gemini_clips:
        for index, uploaded in enumerate(uploaded_gemini_clips, start=1):
            suffix = Path(getattr(uploaded, "name", "clip.mp4")).suffix.lower() or ".mp4"
            destination = folder / f"gemini_{index:02d}{suffix}"
            destination.write_bytes(uploaded.getbuffer())
            clip_paths.append(str(destination))
    else:
        clip_paths = [str(path) for path in loaded_gemini_clip_paths if Path(str(path)).is_file()]

    audio_folder = Path("assets/manual_audio") / f"project_{safe_project_id(project)}"
    audio_folder.mkdir(parents=True, exist_ok=True)
    voice_audio_path = ""
    bgm_audio_path = ""
    if uploaded_voice_audio is not None:
        suffix = Path(getattr(uploaded_voice_audio, "name", "voice.mp3")).suffix.lower() or ".mp3"
        voice_target = audio_folder / f"jian_voice{suffix}"
        voice_target.write_bytes(uploaded_voice_audio.getbuffer())
        voice_audio_path = str(voice_target)
    if uploaded_bgm_audio is not None:
        suffix = Path(getattr(uploaded_bgm_audio, "name", "bgm.mp3")).suffix.lower() or ".mp3"
        bgm_target = audio_folder / f"shopping_bgm{suffix}"
        bgm_target.write_bytes(uploaded_bgm_audio.getbuffer())
        bgm_audio_path = str(bgm_target)


    reservation_payload = None
    naver_native_generated_schedule = None
    if reservation_enabled:
        local_start = datetime.combine(
            reservation_date,
            reservation_time,
            tzinfo=ZoneInfo("Asia/Seoul"),
        )
        selected_platform_list = list(selected_platforms or [])
        queue_platforms = [
            platform for platform in selected_platform_list
            if platform != "naver_clip"
        ]

        if "naver_clip" in selected_platform_list:
            naver_index = selected_platform_list.index("naver_clip")
            naver_native_generated_schedule = local_start + timedelta(
                minutes=int(platform_interval_minutes or 0) * naver_index
            )

        _reservation_platform_metadata_194_77_1 = dict(platform_metadata or {})
        if "youtube" in list(queue_platforms or []):
            _youtube_meta_194_77_1 = dict(
                _reservation_platform_metadata_194_77_1.get("youtube") or {}
            )
            _youtube_meta_194_77_1["channel"] = str(
                youtube_upload_account
                or _sprint194_77_default_youtube_account(production_mode)
            ).strip()
            _youtube_meta_194_77_1["youtube_account"] = str(
                youtube_upload_account
                or _sprint194_77_default_youtube_account(production_mode)
            ).strip()
            _reservation_platform_metadata_194_77_1["youtube"] = _youtube_meta_194_77_1

        reservation_payload = {
            "enabled": bool(queue_platforms),
            "platforms": queue_platforms,
            "scheduled_at_local": local_start.isoformat(),
            "interval_minutes": int(platform_interval_minutes or 0),
            "infock_url": str(infock_url or "").strip(),
            "platform_metadata": _reservation_platform_metadata_194_77_1,
        }

    print(
        "[Sprint189-1 Manual Subtitle UI]",
        {
            "clip_subtitle_count": len([x for x in list(clip_subtitles or []) if str(x).strip()]),
            "hook_product_image_path": hook_product_image_path,
        },
        flush=True,
    )

    with st.spinner("기존 음향 제거 → 속도 조절 → 영상 연결 → 지안 TTS → 자막 → BGM → 효과음 → 최종 MP4 제작 중입니다..."):
        try:
            result = run_project_pipeline(
                project=project,
                sample_count=len(clip_paths),
                review_text=hook_text.strip(),
                locked_script=locked_script.strip(),
                review_image_paths=[],
                product_image_paths=[],
                product_image_path="",
                youtube_privacy_status=youtube_privacy_status,
                viral_video_sources=clip_paths,
                input_product_name=product_name.strip(),
                stop_after_image_generation=False,
                gemini_video_mode=True,
                hook_text=hook_text.strip(),
                cta_text=cta_text.strip(),
                voice_audio_path=voice_audio_path,
                bgm_audio_path=bgm_audio_path,
                voice_name=str(selected_voice_name or "지안"),
                voice_id=str(selected_voice_id or ""),
                typecast_api_key=str(typecast_api_key or ""),
                tts_volume_percent=int(tts_volume_percent or 100),
                tts_speech_speed=float(_effective_tts_speech_speed_194_41),
                clip_subtitles=list(clip_subtitles or []),
                clip_subtitle_effects=list(clip_subtitle_effects or []),
                clip_sfx=list(clip_sfx or []),
                clip_playback_speeds=list(clip_playback_speeds or []),
                clip_narrations=list(clip_narrations or []),
                gemini_clip_count=len(clip_paths),
                upload_enabled=bool(upload_enabled),
                playback_speed=float(playback_speed),
                channel_type=channel_type,
                monthly_purchase_count=int(monthly_purchase_count or 0),
                declared_review_count=int(declared_review_count or 0),
                rating=float(rating or 0.0),
                reservation_payload=reservation_payload,
            )
        except Exception as exc:
            Path("full_error.log").write_text(traceback.format_exc(), encoding="utf-8")
            st.error(f"쇼츠 자동 편집 실패: {type(exc).__name__}: {exc}")
            return

    final_path = _resolve_final_video_path(result)
    if final_path and Path(final_path).is_file():
        st.success("역사쿠키 쇼츠 제작이 완료됐습니다." if is_history_mode else "Gemini 쇼츠 자동 편집이 완료됐습니다.")
        st.video(final_path)
        st.caption(f"최종 영상: {final_path}")
        st.caption(f"적용 속도: {float(playback_speed):.2f}배 / 음성 파일: {'적용' if voice_audio_path else '자동 모듈 탐색'} / 공개 설정: {youtube_privacy_status}")

        # Sprint192-31: 새로 완성된 영상도 네이버는 큐가 아니라
        # 네이버 자체 등록예약으로 즉시 저장합니다.
        if (
            reservation_enabled
            and naver_native_generated_schedule is not None
            and "naver_clip" in list(selected_platforms or [])
        ):
            naver_override = dict(
                (platform_metadata or {}).get("naver_clip") or {}
            )
            naver_title = (
                str(naver_override.get("title") or "").strip()
                or str(product_name or "").strip()
                or Path(final_path).stem
            )
            naver_description = str(
                naver_override.get("description") or ""
            ).strip()
            naver_scheduled_iso = naver_native_generated_schedule.isoformat(
                timespec="minutes"
            )

            print(
                "[Sprint192-31 Naver Native Generated] START",
                {
                    "video_path": final_path,
                    "scheduled_publish_at": naver_scheduled_iso,
                    "account": naver_clip_upload_account,
                },
                flush=True,
            )

            with st.spinner(
                "완성 영상을 네이버 클립 자체 등록예약으로 저장 중입니다..."
            ):
                naver_generated_result = NaverClipUploadExecutor().prepare_upload(
                    video_path=str(final_path),
                    title=naver_title,
                    description=naver_description,
                    user_data_dir=naver_clip_profile_dir,
                    headless=False,
                    allow_manual_login=True,
                    login_timeout_seconds=600,
                    action_timeout_seconds=60,
                    slow_mo=150,
                    keep_browser_open=True,
                    category_primary="쇼핑",
                    category_secondary="상품리뷰",
                    perform_publish=True,
                    scheduled_publish_at=naver_scheduled_iso,
                )

            if naver_generated_result.get("ok"):
                st.success(
                    "네이버 클립 자체 등록예약 완료: "
                    f"{naver_generated_result.get('scheduled_publish_at', '')}"
                )
            else:
                st.error(
                    "네이버 클립 자체 등록예약 실패: "
                    f"{naver_generated_result.get('status')} / "
                    f"{naver_generated_result.get('errors')}"
                )

            print(
                "[Sprint192-31 Naver Native Generated] COMPLETE",
                {
                    "ok": naver_generated_result.get("ok"),
                    "status": naver_generated_result.get("status"),
                },
                flush=True,
            )

        reservation_result = ((result.get("outputs") or {}).get("reservations") or {})
        if reservation_result.get("ok"):
            st.success(f"예약 큐 등록 완료: {reservation_result.get('count', 0)}건")
            st.json(reservation_result.get("items") or [])
        elif reservation_enabled:
            st.warning(str(reservation_result.get("error") or "예약 큐에 등록되지 않았습니다."))
    else:
        st.error(str(result.get("summary") or "최종 MP4가 생성되지 않았습니다."))
        st.json(result)


render = show_one_click_pipeline
