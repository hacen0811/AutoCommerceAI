# -*- coding: utf-8 -*-

"""
NAVER BRAND CONNECT ONE CLICK V5.10

V5.10
- 역사쿠키 / 기존 쇼핑쇼츠 수정 없음
- 제품 이미지/영상
- 네이버 가격/쿠폰 캡처
- Tesseract 자동 경로 탐색
- 한국어 OCR(kor) 자동 확인
- OCR 다중 전처리
- OCR 실패 원인 화면 표시
- OCR 실패 시 수동 보정 가능
- 정상가 / 기본할인가 / 최대혜택가 / 할인율 / D-day / 쿠폰 분석
- 가격 분석 결과 즉시 표시
- 최대혜택가 + D-day CTA 최우선
- 리뷰 캡처 첫 3초 자동 삽입
- 가격 캡처 CTA 직전 자동 삽입
- Pretendard SemiBold 일반 자막
- Gmarket Sans Bold 강조 자막
- 한 장면 최대 2줄
- [강조] 수동 강조
- Typecast
- BGM 기본 20%
"""

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import hashlib
import tempfile

import streamlit as st


# =========================================================
# ROOT
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


APP_VERSION = "naver-brand-v5.20"

ROOT_DIR = PROJECT_ROOT / "assets" / "naver_brand"
UPLOAD_DIR = ROOT_DIR / "uploads"
PROJECT_DIR = ROOT_DIR / "projects"
WORK_DIR = ROOT_DIR / "work"
OCR_DIR = ROOT_DIR / "ocr_preview"

EXPORT_DIR = PROJECT_ROOT / "exports" / "naver_brand"

TYPECAST_CONFIG = ROOT_DIR / "typecast_config.json"
OPENAI_CONFIG = ROOT_DIR / "openai_config.json"
AI_NARRATION_HISTORY = ROOT_DIR / "ai_narration_history.json"


IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".m4v",
    ".webm",
    ".mkv",
}

AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
    ".ogg",
    ".flac",
}


for folder in (
    ROOT_DIR,
    UPLOAD_DIR,
    PROJECT_DIR,
    WORK_DIR,
    OCR_DIR,
    EXPORT_DIR,
):
    folder.mkdir(
        parents=True,
        exist_ok=True,
    )


# =========================================================
# FONT
# =========================================================

WINDOWS_FONT_DIR = Path(
    "C:/Windows/Fonts"
)

USER_FONT_DIR = (
    Path(
        os.environ.get(
            "LOCALAPPDATA",
            "",
        )
    )
    / "Microsoft"
    / "Windows"
    / "Fonts"
)

FONT_DIRS = [
    WINDOWS_FONT_DIR,
    USER_FONT_DIR,
]



# =========================================================
# GLOBAL CTA TIMING
# =========================================================
CTA_RESERVED_SECONDS = 3.0

# =========================================================
# SHOPPING SHORTS GLOBAL VISUAL SETTINGS
#
# 모든 상품 / 모든 새 영상에 공통 적용
# =========================================================

# 자막 배경
SUBTITLE_BOX_X = 145
SUBTITLE_BOX_WIDTH = 790

SUBTITLE_BOX_1LINE_Y = 1320
SUBTITLE_BOX_1LINE_HEIGHT = 132

SUBTITLE_BOX_2LINE_Y = 1267
SUBTITLE_BOX_2LINE_HEIGHT = 238

# 본문 컬러 이모지
BODY_EMOJI_SIZE = 108
BODY_EMOJI_X = 205
BODY_EMOJI_Y = 1330

# CTA
CTA_ADVANCE_SECONDS = 0.8


def normalize_font_name(text):
    return (
        str(text or "")
        .lower()
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
    )


def find_font_file(keywords):

    keywords = [
        normalize_font_name(x)
        for x in keywords
    ]

    for folder in FONT_DIRS:

        if not folder.is_dir():
            continue

        try:

            for path in folder.iterdir():

                if path.suffix.lower() not in {
                    ".ttf",
                    ".otf",
                    ".ttc",
                }:
                    continue

                name = normalize_font_name(
                    path.name
                )

                if all(
                    keyword in name
                    for keyword in keywords
                ):
                    return str(path)

        except Exception:
            pass

    return ""


def detect_fonts():

    pretendard = (
        find_font_file(
            ["pretendard", "semibold"]
        )
        or find_font_file(
            ["pretendard", "bold"]
        )
        or find_font_file(
            ["pretendard"]
        )
    )

    gmarket = (
        find_font_file(
            ["gmarket", "bold"]
        )
        or find_font_file(
            ["gmarketsans", "bold"]
        )
        or find_font_file(
            ["gmarket"]
        )
    )

    malgun_bold = (
        WINDOWS_FONT_DIR
        / "malgunbd.ttf"
    )

    malgun = (
        WINDOWS_FONT_DIR
        / "malgun.ttf"
    )

    fallback = ""

    if malgun_bold.is_file():
        fallback = str(malgun_bold)

    elif malgun.is_file():
        fallback = str(malgun)

    if not pretendard:
        pretendard = fallback

    if not gmarket:
        gmarket = fallback

    return {
        "normal_file":
            pretendard,

        "highlight_file":
            gmarket,

        "normal_name": (
            "Pretendard SemiBold"
            if "pretendard"
            in Path(pretendard).name.lower()
            else "Malgun Gothic"
        ),

        "highlight_name": (
            "Gmarket Sans Bold"
            if "gmarket"
            in Path(gmarket).name.lower()
            else "Malgun Gothic"
        ),
    }


# =========================================================
# COMMON
# =========================================================

def safe_name(text, fallback="product"):

    text = str(
        text or ""
    ).strip()

    if not text:
        text = fallback

    text = re.sub(
        r"[^0-9A-Za-z가-힣._-]+",
        "_",
        text,
    )

    text = re.sub(
        r"_+",
        "_",
        text,
    ).strip("_")

    return text[:70] or fallback


def compact_product_name(text):

    text = str(
        text or ""
    ).strip()

    for word in [
        "브랜드 스토어",
        "브랜드스토어",
        "공식스토어",
        "공식 스토어",
        "공식몰",
        "공식",
        "정품",
        "무료배송",
    ]:
        text = text.replace(
            word,
            " ",
        )

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    return text or "product"


def now_id():
    return datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )


def save_json(path, data):

    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def load_json(path, default=None):

    try:

        path = Path(path)

        if path.is_file():

            return json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )

    except Exception:
        pass

    return (
        default
        if default is not None
        else {}
    )


def run_command(command):

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if completed.returncode != 0:

        raise RuntimeError(
            (
                completed.stderr
                or completed.stdout
                or "command failed"
            )[-6000:]
        )

    return completed


def ffmpeg_available():
    return shutil.which(
        "ffmpeg"
    ) is not None


def ffprobe_available():
    return shutil.which(
        "ffprobe"
    ) is not None



def media_has_meaningful_audio(
    path,
    silence_db=-45.0,
):
    """
    ??? ??? ?? ?? ?? ???? ??? ?? ??.
    """

    path = Path(path)

    if (
        not path.is_file()
        or not ffprobe_available()
        or not ffmpeg_available()
    ):
        return False

    try:
        probe = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=index",
                "-of",
                "csv=p=0",
                str(path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )

        if not (probe.stdout or "").strip():
            return False

    except Exception:
        return False

    try:
        check = subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-nostats",
                "-i",
                str(path),
                "-map",
                "0:a:0",
                "-af",
                "volumedetect",
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )

        report = (
            (check.stderr or "")
            + "\n"
            + (check.stdout or "")
        )

        match = re.search(
            r"mean_volume:\s*(-?[\d.]+)\s*dB",
            report,
            re.I,
        )

        if not match:
            return False

        return float(match.group(1)) > float(silence_db)

    except Exception:
        return False


def build_source_audio_plan(
    sources,
    content_duration,
    scene_plan=None,
):
    """
    V5.20 SOURCE AUDIO PLAN

    화면 렌더링과 동일한 scene_plan을 사용한다.

    - 이미지: 원본음 없음
    - 영상: 실제 오디오가 있는 경우만 사용
    - 화면 scene start/end와 원본음 start/end 일치
    - 예전 duration / source count 균등배분 사용 안 함
    """

    sources = list(
        sources or []
    )

    if not sources:
        return []

    if scene_plan is None:

        scene_plan = (
            build_scene_plan(
                sources,
                content_duration,
            )
        )

    if not scene_plan:
        return []

    result = []

    for scene in scene_plan:

        if (
            str(
                scene.get(
                    "type",
                    "",
                )
            ).lower()
            != "video"
        ):
            continue

        source_path = str(
            scene.get(
                "path",
                "",
            )
            or ""
        )

        if not source_path:
            continue

        if not media_has_meaningful_audio(
            source_path
        ):
            continue

        start = max(
            0.0,
            float(
                scene.get(
                    "start",
                    0.0,
                )
            ),
        )

        end = max(
            start,
            float(
                scene.get(
                    "end",
                    start,
                )
            ),
        )

        source_duration = max(
            0.0,
            end - start,
        )

        if source_duration <= 0.01:
            continue

        result.append(
            {
                "path":
                    source_path,

                "start":
                    start,

                "end":
                    end,

                "duration":
                    source_duration,

                "scene_index":
                    scene.get(
                        "index",
                        -1,
                    ),
            }
        )

    return result



def media_duration(path):

    if not ffprobe_available():
        return 0.0

    result = run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
    )

    try:
        return float(
            result.stdout.strip()
        )

    except Exception:
        return 0.0


# =========================================================
# TESSERACT AUTO DETECT V5.10
# =========================================================

def setup_tesseract():

    try:
        import pytesseract

    except Exception as exc:

        return {
            "ok": False,
            "path": "",
            "version": "",
            "languages": [],
            "kor": False,
            "error": (
                "pytesseract를 불러오지 못했습니다: "
                + str(exc)
            ),
        }

    candidates = []

    path_from_env = shutil.which(
        "tesseract"
    )

    if path_from_env:
        candidates.append(
            path_from_env
        )

    candidates.extend(
        [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]
    )

    checked = set()

    for candidate in candidates:

        if not candidate:
            continue

        normalized = str(
            Path(candidate)
        )

        if normalized in checked:
            continue

        checked.add(
            normalized
        )

        if not Path(
            candidate
        ).is_file():
            continue

        try:

            pytesseract.pytesseract.tesseract_cmd = (
                candidate
            )

            version = str(
                pytesseract.get_tesseract_version()
            )

            languages = (
                pytesseract.get_languages(
                    config=""
                )
            )

            return {
                "ok": True,
                "path": candidate,
                "version": version,
                "languages": languages,
                "kor": (
                    "kor"
                    in languages
                ),
                "error": "",
            }

        except Exception as exc:

            return {
                "ok": False,
                "path": candidate,
                "version": "",
                "languages": [],
                "kor": False,
                "error": str(exc),
            }

    return {
        "ok": False,
        "path": "",
        "version": "",
        "languages": [],
        "kor": False,
        "error": (
            "Tesseract 실행파일을 찾지 못했습니다. "
            r"C:\Program Files\Tesseract-OCR\tesseract.exe "
            "설치 여부를 확인해주세요."
        ),
    }


# =========================================================
# OCR V5.10
# =========================================================

def normalize_ocr_text(text):

    text = str(
        text or ""
    )

    text = text.replace(
        "，",
        ",",
    )

    text = text.replace(
        "％",
        "%",
    )

    text = text.replace(
        "₩",
        "",
    )

    text = text.replace(
        "O원",
        "0원",
    )

    text = re.sub(
        r"(\d)\s*,\s*(\d)",
        r"\1,\2",
        text,
    )

    text = re.sub(
        r"(\d)\s*%\s*(\d)",
        r"\1% \2",
        text,
    )

    text = re.sub(
        r"D\s*[—–_]\s*(\d+)",
        r"D-\1",
        text,
        flags=re.I,
    )

    text = re.sub(
        r"D\s*-\s*(\d+)",
        r"D-\1",
        text,
        flags=re.I,
    )

    return text.strip()


def ocr_price_capture(image_path):

    """
    V5.10
    - Tesseract 실행파일 자동 탐색
    - kor 존재 확인
    - 여러 이미지 전처리
    - 여러 PSM 시도
    - kor+eng 우선
    - 실패 원인 반환
    """

    tesseract_status = (
        setup_tesseract()
    )

    if not tesseract_status[
        "ok"
    ]:

        return {
            "ok": False,
            "text": "",
            "error": (
                tesseract_status[
                    "error"
                ]
            ),
        }

    try:

        import pytesseract

        from PIL import (
            Image,
            ImageEnhance,
            ImageFilter,
            ImageOps,
        )

    except Exception as exc:

        return {
            "ok": False,
            "text": "",
            "error": (
                "OCR Python 모듈 오류: "
                + str(exc)
            ),
        }

    try:

        image = Image.open(
            image_path
        ).convert("RGB")

    except Exception as exc:

        return {
            "ok": False,
            "text": "",
            "error": (
                "가격 캡처 이미지를 열지 못했습니다: "
                + str(exc)
            ),
        }

    variants = []

    # -----------------------------------------------------
    # 1. 원본 확대
    # -----------------------------------------------------

    large = image.resize(
        (
            image.width * 2,
            image.height * 2,
        )
    )

    variants.append(
        large
    )

    # -----------------------------------------------------
    # 2. 흑백 + 대비
    # -----------------------------------------------------

    gray = ImageOps.grayscale(
        large
    )

    gray = (
        ImageEnhance.Contrast(
            gray
        )
        .enhance(
            2.2
        )
    )

    variants.append(
        gray
    )

    # -----------------------------------------------------
    # 3. 샤픈
    # -----------------------------------------------------

    sharp = gray.filter(
        ImageFilter.SHARPEN
    )

    sharp = sharp.filter(
        ImageFilter.SHARPEN
    )

    variants.append(
        sharp
    )

    # -----------------------------------------------------
    # 4. threshold
    # -----------------------------------------------------

    threshold_165 = gray.point(
        lambda p:
            255
            if p > 165
            else 0
    )

    variants.append(
        threshold_165
    )

    threshold_185 = gray.point(
        lambda p:
            255
            if p > 185
            else 0
    )

    variants.append(
        threshold_185
    )

    # -----------------------------------------------------
    # OCR
    # -----------------------------------------------------

    candidates = []

    configs = [
        "--psm 6",
        "--psm 11",
        "--psm 12",
    ]

    if tesseract_status[
        "kor"
    ]:

        languages = [
            "kor+eng",
            "kor",
            "eng",
        ]

    else:

        languages = [
            "eng",
        ]

    last_error = ""

    for variant in variants:

        for config in configs:

            for lang in languages:

                try:

                    text = (
                        pytesseract
                        .image_to_string(
                            variant,
                            lang=lang,
                            config=config,
                        )
                    )

                    text = (
                        normalize_ocr_text(
                            text
                        )
                    )

                    if text:

                        candidates.append(
                            {
                                "text":
                                    text,

                                "lang":
                                    lang,

                                "config":
                                    config,
                            }
                        )

                except Exception as exc:

                    last_error = str(
                        exc
                    )

    if not candidates:

        error_message = (
            "OCR 결과가 없습니다."
        )

        if last_error:

            error_message += (
                " 마지막 오류: "
                + last_error
            )

        return {
            "ok": False,
            "text": "",
            "error": error_message,
        }

    # -----------------------------------------------------
    # 가장 좋은 OCR 결과 선정
    # -----------------------------------------------------

    def score(row):

        text = row[
            "text"
        ]

        value = 0

        # 가격
        value += (
            len(
                re.findall(
                    r"\d[\d,]{2,}\s*원",
                    text,
                )
            )
            * 12
        )

        # % 할인율
        value += (
            len(
                re.findall(
                    r"\d{1,3}\s*%",
                    text,
                )
            )
            * 8
        )

        # D-day
        if re.search(
            r"D\s*-\s*\d+",
            text,
            re.I,
        ):
            value += 10

        # 한글 키워드
        if "쿠폰" in text:
            value += 7

        if "할인" in text:
            value += 5

        if "최대" in text:
            value += 5

        if "혜택" in text:
            value += 4

        # 한국어 OCR 결과 우선
        if row[
            "lang"
        ] == "kor+eng":
            value += 4

        elif row[
            "lang"
        ] == "kor":
            value += 2

        return value

    candidates.sort(
        key=score,
        reverse=True,
    )

    best = candidates[
        0
    ]

    return {
        "ok": True,
        "text": best[
            "text"
        ],
        "error": "",
        "lang": best[
            "lang"
        ],
        "config": best[
            "config"
        ],
    }


# =========================================================
# PROMOTION PARSER
# =========================================================

def format_price(value):

    if value is None:
        return "-"

    return (
        f"{int(value):,}원"
    )


def parse_promotion_info(text):

    raw = normalize_ocr_text(
        text
    )

    result = {
        "normal_price":
            None,

        "sale_price":
            None,

        "max_price":
            None,

        "discount_percent":
            None,

        "days_left":
            None,

        "coupon_present":
            False,
    }

    if not raw:
        return result

    # -----------------------------------------------------
    # 할인율
    # -----------------------------------------------------

    match = re.search(
        r"(\d{1,3})\s*%",
        raw,
    )

    if match:

        percent = int(
            match.group(
                1
            )
        )

        if (
            0
            < percent
            <= 100
        ):

            result[
                "discount_percent"
            ] = percent

    # -----------------------------------------------------
    # D-day
    # -----------------------------------------------------

    match = re.search(
        r"D\s*[-–—]?\s*(\d+)",
        raw,
        re.I,
    )

    if match:

        result[
            "days_left"
        ] = int(
            match.group(
                1
            )
        )

    else:

        match = re.search(
            r"(\d+)\s*일\s*(?:남음|한정|동안)",
            raw,
        )

        if match:

            result[
                "days_left"
            ] = int(
                match.group(
                    1
                )
            )

    # -----------------------------------------------------
    # 쿠폰
    # -----------------------------------------------------

    result[
        "coupon_present"
    ] = bool(
        re.search(
            r"쿠폰",
            raw,
            re.I,
        )
    )

    # -----------------------------------------------------
    # 가격 추출
    # -----------------------------------------------------

    price_matches = list(
        re.finditer(
            r"(\d[\d,]{2,})\s*원",
            raw,
        )
    )

    prices = []

    for match in price_matches:

        try:

            value = int(
                match.group(
                    1
                )
                .replace(
                    ",",
                    "",
                )
            )

        except Exception:

            continue

        if value <= 0:
            continue

        start = max(
            0,
            match.start()
            - 30,
        )

        end = min(
            len(raw),
            match.end()
            + 30,
        )

        prices.append(
            {
                "value":
                    value,

                "context":
                    raw[
                        start:end
                    ],
            }
        )

    unique_prices = []

    for item in prices:

        if (
            item[
                "value"
            ]
            not in unique_prices
        ):

            unique_prices.append(
                item[
                    "value"
                ]
            )

    # -----------------------------------------------------
    # 최대혜택가 명시
    # -----------------------------------------------------

    for item in prices:

        if re.search(
            (
                r"최대\s*할인가"
                r"|"
                r"최대\s*혜택가"
                r"|"
                r"최대\s*혜택"
                r"|"
                r"최종\s*할인가"
                r"|"
                r"최종\s*혜택가"
                r"|"
                r"쿠폰\s*적용"
            ),
            item[
                "context"
            ],
        ):

            result[
                "max_price"
            ] = item[
                "value"
            ]

    # -----------------------------------------------------
    # 정상가
    # -----------------------------------------------------

    if unique_prices:

        result[
            "normal_price"
        ] = max(
            unique_prices
        )

    # -----------------------------------------------------
    # 가격 3개 이상이면 최저가를 최대혜택가로 보조 추론
    # -----------------------------------------------------

    if (
        result[
            "max_price"
        ] is None
        and len(
            unique_prices
        ) >= 3
    ):

        result[
            "max_price"
        ] = min(
            unique_prices
        )

    # -----------------------------------------------------
    # 기본 할인가
    # -----------------------------------------------------

    if len(
        unique_prices
    ) >= 2:

        middle = [
            price
            for price
            in sorted(
                unique_prices,
                reverse=True,
            )
            if price
            != result[
                "normal_price"
            ]
            and price
            != result[
                "max_price"
            ]
        ]

        if middle:

            result[
                "sale_price"
            ] = middle[
                0
            ]

        elif (
            result[
                "max_price"
            ] is None
        ):

            result[
                "sale_price"
            ] = sorted(
                unique_prices,
                reverse=True,
            )[1]

    return result


def build_cta_text(text):

    promo = parse_promotion_info(text)

    days_left = promo.get("days_left")
    max_price = promo.get("max_price")
    sale_price = promo.get("sale_price")
    discount_percent = promo.get("discount_percent")

    # -----------------------------------------------------
    # V5.19 CTA
    # 가격 → 긴급성 → 행동
    # -----------------------------------------------------

    if days_left is not None and max_price:

        return {
            "price":
                f"D-{days_left} · 최대 {format_price(max_price)}",

            "urgency":
                "특가 종료 임박",

            "action":
                "하단 상품 태그 클릭",
        }

    if max_price:

        return {
            "price":
                f"최대 {format_price(max_price)}",

            "urgency":
                "특가 혜택 진행 중",

            "action":
                "하단 상품 태그 클릭",
        }

    if discount_percent and sale_price:

        return {
            "price":
                f"{discount_percent}% · {format_price(sale_price)}",

            "urgency":
                "할인 혜택 확인",

            "action":
                "하단 상품 태그 클릭",
        }

    if sale_price:

        return {
            "price":
                format_price(sale_price),

            "urgency":
                "현재 혜택 확인",

            "action":
                "하단 상품 태그 클릭",
        }

    return {
        "price":
            "지금 혜택 확인",

        "urgency":
            "특가 혜택 확인",

        "action":
            "하단 상품 태그 클릭",
    }

# =========================================================
# TYPECAST
# =========================================================

def load_typecast_settings():

    local = load_json(
        TYPECAST_CONFIG,
        {},
    )

    api_key = str(
        local.get(
            "api_key"
        )
        or os.getenv(
            "TYPECAST_API_KEY",
            "",
        )
        or ""
    ).strip()

    voice_name = str(
        local.get(
            "voice_name"
        )
        or "지안"
    ).strip()

    voice_id = str(
        local.get(
            "voice_id"
        )
        or ""
    ).strip()

    try:

        from modules.audio.typecast_settings_store import (
            TypecastSettingsStore,
        )

        original = (
            TypecastSettingsStore.load()
            or {}
        )

        if not api_key:

            api_key = str(
                original.get(
                    "api_key"
                )
                or ""
            ).strip()

        if not voice_id:

            voice_id = str(
                original.get(
                    "last_voice_id"
                )
                or ""
            ).strip()

        if not voice_name:

            voice_name = str(
                original.get(
                    "last_voice_name"
                )
                or "지안"
            ).strip()

    except Exception:
        pass

    return {
        "api_key":
            api_key,

        "voice_name":
            voice_name,

        "voice_id":
            voice_id,
    }


@st.cache_data(
    ttl=3600,
    show_spinner=False,
)
def typecast_voice_choices(api_key):

    if not api_key:
        return []

    try:

        from typecast import Typecast

        client = Typecast(
            api_key=api_key
        )

        result = []

        for voice in (
            client.voices_v2()
            or []
        ):

            if isinstance(
                voice,
                dict,
            ):

                name = str(
                    voice.get(
                        "voice_name"
                    )
                    or voice.get(
                        "name"
                    )
                    or ""
                ).strip()

                voice_id = str(
                    voice.get(
                        "voice_id"
                    )
                    or voice.get(
                        "id"
                    )
                    or ""
                ).strip()

            else:

                name = str(
                    getattr(
                        voice,
                        "voice_name",
                        "",
                    )
                    or getattr(
                        voice,
                        "name",
                        "",
                    )
                    or ""
                ).strip()

                voice_id = str(
                    getattr(
                        voice,
                        "voice_id",
                        "",
                    )
                    or getattr(
                        voice,
                        "id",
                        "",
                    )
                    or ""
                ).strip()

            if (
                name
                and voice_id
            ):

                result.append(
                    (
                        name,
                        voice_id,
                    )
                )

        return result

    except Exception:
        return []



def load_openai_settings():

    default = {
        "api_key": "",
        "model": "gpt-5-mini",
    }

    if not OPENAI_CONFIG.is_file():
        return default

    try:

        data = json.loads(
            OPENAI_CONFIG.read_text(
                encoding="utf-8"
            )
        )

        default.update(
            {
                "api_key":
                    str(
                        data.get(
                            "api_key",
                            "",
                        )
                    ),

                "model":
                    str(
                        data.get(
                            "model",
                            "gpt-5-mini",
                        )
                    ),
            }
        )

    except Exception:
        pass

    return default




def save_naver_brand_project_state(
    folder,
    project_id,
    sources,
    scene_inputs,
    narration="",
    subtitle="",
    promotion_text="",
    product_name="",
    bgm_volume=20,
    typecast=None,
    final_video="",
):
    """
    제작 후 다시 수정할 수 있도록
    프로젝트 편집 상태를 JSON으로 저장한다.

    API Key는 저장하지 않는다.
    """

    folder = Path(
        folder
    )

    folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    clean_sources = []

    for item in sources or []:

        item = item or {}

        clean_sources.append(
            {
                "path":
                    str(
                        item.get(
                            "path",
                            "",
                        )
                        or ""
                    ),

                "type":
                    str(
                        item.get(
                            "type",
                            "",
                        )
                        or ""
                    ),

                "original_name":
                    str(
                        item.get(
                            "original_name",
                            "",
                        )
                        or ""
                    ),
            }
        )

    clean_scenes = []

    for item in scene_inputs or []:

        item = item or {}

        clean_scenes.append(
            {
                "source_index":
                    item.get(
                        "source_index"
                    ),

                "source_type":
                    str(
                        item.get(
                            "source_type",
                            "",
                        )
                        or ""
                    ),

                "filename":
                    str(
                        item.get(
                            "filename",
                            "",
                        )
                        or ""
                    ),

                "narration":
                    str(
                        item.get(
                            "narration",
                            "",
                        )
                        or ""
                    ),

                "subtitle":
                    str(
                        item.get(
                            "subtitle",
                            "",
                        )
                        or ""
                    ),

                "emoji_left":
                    str(
                        item.get(
                            "emoji_left",
                            "",
                        )
                        or ""
                    ),

                "emoji_right":
                    str(
                        item.get(
                            "emoji_right",
                            "",
                        )
                        or ""
                    ),
            }
        )

    typecast = (
        typecast
        or {}
    )

    state = {
        "version":
            "nb-editable-project-v1",

        "project_id":
            str(
                project_id
                or ""
            ),

        "product_name":
            str(
                product_name
                or ""
            ),

        "sources":
            clean_sources,

        "scene_inputs":
            clean_scenes,

        "narration":
            str(
                narration
                or ""
            ),

        "subtitle":
            str(
                subtitle
                or ""
            ),

        "promotion_text":
            str(
                promotion_text
                or ""
            ),

        "bgm_volume":
            int(
                bgm_volume
                or 0
            ),

        "typecast": {
            "voice_id":
                str(
                    typecast.get(
                        "voice_id",
                        "",
                    )
                    or ""
                ),

            "speed":
                float(
                    typecast.get(
                        "speed",
                        1.1,
                    )
                    or 1.1
                ),
        },

        "final_video":
            str(
                final_video
                or ""
            ),

        "saved_at":
            datetime.now().isoformat(
                timespec="seconds"
            ),
    }

    state_path = (
        folder
        / "project_state.json"
    )

    state_path.write_text(
        json.dumps(
            state,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return str(
        state_path
    )



def recover_legacy_naver_brand_project_state(
    folder,
):
    """
    project_state.json이 없는 예전 프로젝트를
    가능한 범위에서 편집 가능한 상태로 복구한다.

    주의:
    예전 나레이션 원문이 별도 저장되지 않았다면
    WAV만으로 원문을 완벽하게 복원할 수는 없다.
    """

    folder = Path(
        folder
    )

    if not folder.is_dir():
        return {}

    video_exts = {
        ".mp4",
        ".mov",
        ".m4v",
        ".webm",
        ".mkv",
    }

    image_exts = {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
    }

    # 생성 결과물은 원본 소스로 다시 잡지 않는다.
    excluded_names = {
        "review.mp4",
        "subtitle.mp4",
        "body_icons.mp4",
        "price.mp4",
        "cta.mp4",
        "ad_badge.mp4",
        "content.mp4",
        "content_extended.mp4",
    }

    excluded_tokens = (
        "scene_narration",
        "ai_video_frames",
        "body_icons",
        "sfx",
        "subtitles",
        "review_capture",
        "price_capture",
        "cta_",
        "ad_badge",
        "content_extended",
        "content.mp4",
        "review.mp4",
        "subtitle.mp4",
        "price.mp4",
        "cta.mp4",
        "final",
        "output",
        "export",
    )

    candidates = []

    for item in folder.rglob("*"):

        if not item.is_file():
            continue

        suffix = item.suffix.lower()

        if (
            suffix not in video_exts
            and suffix not in image_exts
        ):
            continue

        name_lower = item.name.lower()

        if name_lower in excluded_names:
            continue

        path_lower = str(
            item
        ).lower()

        if any(
            token in path_lower
            for token in excluded_tokens
        ):
            continue

        candidates.append(
            item
        )

    def _natural_key(
        value,
    ):

        text = str(
            value
        ).lower()

        return [
            int(part)
            if part.isdigit()
            else part
            for part in re.split(
                r"(\d+)",
                text,
            )
        ]

    candidates = sorted(
        candidates,
        key=lambda p:
            _natural_key(
                p.name
            ),
    )

    sources = []

    for item in candidates:

        suffix = item.suffix.lower()

        source_type = (
            "video"
            if suffix in video_exts
            else "image"
        )

        sources.append(
            {
                "path":
                    str(
                        item
                    ),

                "type":
                    source_type,

                "original_name":
                    item.name,
            }
        )

    # --------------------------------------------------------
    # 장면 수 추정
    # --------------------------------------------------------

    scene_audio_dir = (
        folder
        / "scene_narration"
    )

    scene_audio_files = []

    if scene_audio_dir.is_dir():

        scene_audio_files = sorted(
            [
                p
                for p
                in scene_audio_dir.glob(
                    "scene_*.wav"
                )
                if (
                    "_raw" not in p.stem
                    and "_slot" not in p.stem
                )
            ],
            key=lambda p:
                _natural_key(
                    p.name
                ),
        )

    scene_count = max(
        len(
            sources
        ),
        len(
            scene_audio_files
        ),
    )

    # --------------------------------------------------------
    # 레거시 subtitles.ass에서 장면별 텍스트 복구
    # --------------------------------------------------------

    recovered_ass_texts = []

    ass_path = (
        folder
        / "subtitles.ass"
    )

    if ass_path.is_file():

        try:

            ass_text = ass_path.read_text(
                encoding="utf-8-sig",
                errors="replace",
            )

            for line in ass_text.splitlines():

                line = str(
                    line
                ).strip()

                if not line.startswith(
                    "Dialogue:"
                ):
                    continue

                # ASS Dialogue는 앞쪽 9개 콤마 뒤가 실제 텍스트
                parts = line.split(
                    ",",
                    9,
                )

                if len(parts) < 10:
                    continue

                text_value = str(
                    parts[9]
                )

                # ASS 스타일 태그 제거
                text_value = re.sub(
                    r"\{[^}]*\}",
                    "",
                    text_value,
                )

                text_value = (
                    text_value
                    .replace(
                        r"\N",
                        "\n",
                    )
                    .replace(
                        r"\n",
                        "\n",
                    )
                    .strip()
                )

                if text_value:

                    recovered_ass_texts.append(
                        text_value
                    )

        except Exception:

            recovered_ass_texts = []

    # --------------------------------------------------------
    # 레거시 장면별 WAV에서 나레이션 원문 복구
    # --------------------------------------------------------

    recovered_narrations = []

    if scene_audio_files:

        try:

            import os
            from openai import OpenAI

            saved_openai = (
                load_openai_settings()
            )

            transcription_api_key = str(
                saved_openai.get(
                    "api_key",
                    "",
                )
                or os.getenv(
                    "OPENAI_API_KEY",
                    "",
                )
                or ""
            ).strip()

            if transcription_api_key:

                transcription_client = (
                    OpenAI(
                        api_key=transcription_api_key
                    )
                )

                for wav_path in scene_audio_files:

                    try:

                        with Path(
                            wav_path
                        ).open(
                            "rb"
                        ) as audio_file:

                            response = (
                                transcription_client
                                .audio
                                .transcriptions
                                .create(
                                    model=(
                                        "gpt-4o-mini-transcribe"
                                    ),
                                    file=audio_file,
                                    language="ko",
                                )
                            )

                        narration_text = str(
                            getattr(
                                response,
                                "text",
                                "",
                            )
                            or ""
                        ).strip()

                    except Exception as scene_exc:

                        print(
                            "[LEGACY NARRATION TRANSCRIBE ERROR]",
                            Path(
                                wav_path
                            ).name,
                            type(
                                scene_exc
                            ).__name__,
                            str(
                                scene_exc
                            ),
                            flush=True,
                        )

                        narration_text = ""

                    recovered_narrations.append(
                        narration_text
                    )

            else:

                print(
                    "[LEGACY NARRATION RESTORE] "
                    "OPENAI API KEY MISSING",
                    flush=True,
                )

        except Exception as transcribe_exc:

            print(
                "[LEGACY NARRATION RESTORE ERROR]",
                type(
                    transcribe_exc
                ).__name__,
                str(
                    transcribe_exc
                ),
                flush=True,
            )

            recovered_narrations = []

    scene_inputs = []

    for index in range(
        scene_count
    ):

        source = (
            sources[index]
            if index < len(
                sources
            )
            else {}
        )

        scene_inputs.append(
            {
                "source_index":
                    index,

                "source_type":
                    str(
                        source.get(
                            "type",
                            "",
                        )
                        or ""
                    ),

                "filename":
                    str(
                        source.get(
                            "original_name",
                            "",
                        )
                        or ""
                    ),

                # 나레이션은 scene_XX.wav 음성인식 결과 사용
                "narration":
                    (
                        recovered_narrations[index]
                        if index < len(
                            recovered_narrations
                        )
                        else ""
                    ),

                "subtitle":
                    (
                        recovered_ass_texts[index]
                        if index < len(
                            recovered_ass_texts
                        )
                        else ""
                    ),
            }
        )

    state = {
        "version":
            "nb-legacy-recovered-v1",

        "project_id":
            folder.name,

        "product_name":
            "",

        "sources":
            sources,

        "scene_inputs":
            scene_inputs,

        "narration":
            "",

        "subtitle":
            "",

        "promotion_text":
            "",

        "bgm_volume":
            20,

        "typecast":
            {},

        "final_video":
            "",

        "legacy_recovered":
            True,

        "legacy_ass_text_count":
            len(
                recovered_ass_texts
            ),

        "legacy_narration_text_count":
            len(
                [
                    x
                    for x in recovered_narrations
                    if str(
                        x
                    ).strip()
                ]
            ),
    }

    return state


def load_naver_brand_project_state(
    folder,
):

    state_path = (
        Path(
            folder
        )
        / "project_state.json"
    )

    if not state_path.is_file():
        return {}

    try:

        data = json.loads(
            state_path.read_text(
                encoding="utf-8"
            )
        )

        return (
            data
            if isinstance(
                data,
                dict,
            )
            else {}
        )

    except Exception:

        return {}


def apply_naver_brand_project_state(
    state,
):
    """
    Streamlit 위젯이 생성되기 전에 호출해야 한다.
    """

    if not isinstance(
        state,
        dict,
    ):
        return

    scene_inputs = list(
        state.get(
            "scene_inputs",
            [],
        )
        or []
    )

    st.session_state[
        "nb510_scene_inputs"
    ] = scene_inputs

    for index, item in enumerate(
        scene_inputs
    ):

        item = item or {}

        st.session_state[
            f"nb510_scene_narration_{index}"
        ] = str(
            item.get(
                "narration",
                "",
            )
            or ""
        )

        st.session_state[
            f"nb510_scene_subtitle_{index}"
        ] = str(
            item.get(
                "subtitle",
                "",
            )
            or ""
        )

        st.session_state[
            f"scene_emoji_left_{index}"
        ] = str(
            item.get(
                "emoji_left",
                "",
            )
            or ""
        )

        st.session_state[
            f"scene_emoji_right_{index}"
        ] = str(
            item.get(
                "emoji_right",
                "",
            )
            or ""
        )

    if "narration" in state:

        st.session_state[
            "nb510_script"
        ] = str(
            state.get(
                "narration",
                "",
            )
            or ""
        )

    if "subtitle" in state:

        st.session_state[
            "nb510_subtitle"
        ] = str(
            state.get(
                "subtitle",
                "",
            )
            or ""
        )

    if "promotion_text" in state:

        st.session_state[
            "nb510_promotion"
        ] = str(
            state.get(
                "promotion_text",
                "",
            )
            or ""
        )

    if "bgm_volume" in state:

        st.session_state[
            "nb510_bgm_volume"
        ] = int(
            state.get(
                "bgm_volume",
                20,
            )
            or 20
        )

    st.session_state[
        "nb510_loaded_saved_sources"
    ] = list(
        state.get(
            "sources",
            [],
        )
        or []
    )

    st.session_state[
        "nb510_loaded_project_id"
    ] = str(
        state.get(
            "project_id",
            "",
        )
        or ""
    )


def list_saved_naver_brand_projects():
    """
    assets/naver_brand/work 아래의 기존 제작 프로젝트를 찾아
    최신 순으로 반환한다.
    """

    root = Path(
        "assets/naver_brand/work"
    )

    if not root.is_dir():
        return []

    projects = []

    for folder in root.iterdir():

        if not folder.is_dir():
            continue

        mp4_files = sorted(
            folder.glob(
                "*.mp4"
            ),
            key=lambda p:
                p.stat().st_mtime,
            reverse=True,
        )

        if not mp4_files:
            continue

        # 최종본으로 보이는 파일을 우선 선택
        final_candidates = [
            p
            for p in mp4_files
            if any(
                token in p.stem.lower()
                for token in (
                    "final",
                    "output",
                    "export",
                    "complete",
                    "result",
                )
            )
        ]

        if final_candidates:

            final_video = (
                final_candidates[0]
            )

        else:

            final_video = (
                mp4_files[0]
            )

        projects.append(
            {
                "project_id":
                    folder.name,

                "folder":
                    str(
                        folder
                    ),

                "video":
                    str(
                        final_video
                    ),

                "mtime":
                    float(
                        final_video
                        .stat()
                        .st_mtime
                    ),
            }
        )

    projects.sort(
        key=lambda item:
            item[
                "mtime"
            ],
        reverse=True,
    )

    return projects


def save_openai_settings(
    api_key,
    model,
):

    data = {
        "api_key":
            str(
                api_key or ""
            ).strip(),

        "model":
            str(
                model or "gpt-5-mini"
            ).strip(),
    }

    OPENAI_CONFIG.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )



def build_scene_narration_master(
    scene_plan,
    scene_inputs,
    folder,
    total_duration,
    typecast,
):
    """
    HISTORY COOKIE STYLE SHOPPING SHORTS TIMELINE

    핵심:
    1. 장면별 TTS를 각각 생성한다.
    2. 각 TTS의 앞뒤 무음을 제거한다.
    3. 실제 TTS 길이를 해당 장면 길이로 사용한다.
    4. start/end를 처음부터 다시 누적한다.
    5. 장면별 오디오 슬롯을 순서대로 concat한다.

    기존 adelay/amix 방식은 사용하지 않는다.
    """

    folder = Path(
        folder
    )

    scene_audio_folder = (
        folder
        / "scene_narration"
    )

    scene_audio_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    scene_inputs = list(
        scene_inputs or []
    )

    original_plan = [
        dict(item or {})
        for item in list(
            scene_plan or []
        )
    ]

    if not original_plan:
        raise RuntimeError(
            "장면 타임라인이 없습니다."
        )

    if not scene_inputs:
        raise RuntimeError(
            "장면별 나레이션 입력값이 없습니다."
        )

    def _probe_duration(
        audio_path,
    ):

        try:

            return max(
                0.0,
                float(
                    media_duration(
                        audio_path
                    )
                ),
            )

        except Exception:

            return 0.0

    def _trim_scene_audio(
        source,
        target,
    ):

        source = Path(
            source
        )

        target = Path(
            target
        )

        try:

            run_command(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(
                        source
                    ),
                    "-af",
                    (
                        "silenceremove="
                        "start_periods=1:"
                        "start_duration=0.02:"
                        "start_threshold=-52dB"
                    ),
                    "-ar",
                    "44100",
                    "-ac",
                    "2",
                    "-c:a",
                    "pcm_s16le",
                    str(
                        target
                    ),
                ]
            )

        except Exception:

            if target.exists():

                try:
                    target.unlink()
                except Exception:
                    pass

        # 무음 제거 결과가 이상하면
        # 원본을 표준 WAV로 다시 변환한다.
        if (
            not target.is_file()
            or target.stat().st_size <= 1024
            or _probe_duration(
                target
            ) < 0.15
        ):

            run_command(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(
                        source
                    ),
                    "-ar",
                    "44100",
                    "-ac",
                    "2",
                    "-c:a",
                    "pcm_s16le",
                    str(
                        target
                    ),
                ]
            )

        return str(
            target
        )

    # --------------------------------------------------------
    # 장면별 TTS 생성 + 실제 길이 확보
    # --------------------------------------------------------

    timeline_rows = []

    for index, scene in enumerate(
        original_plan
    ):

        # -------------------------------------------------
        # scene plan의 위치(index)가 아니라
        # 원본 source_index 기준으로 장면 입력을 찾는다.
        #
        # 중간 source가 빠져도
        # 영상 / 나레이션 / 자막 매핑이 밀리지 않는다.
        # -------------------------------------------------

        source_index = int(
            scene.get(
                "index",
                index,
            )
            or 0
        )

        scene_input = {}

        for candidate in scene_inputs:

            candidate = (
                candidate
                or {}
            )

            try:
                candidate_index = int(
                    candidate.get(
                        "source_index",
                        -1,
                    )
                )
            except Exception:
                candidate_index = -1

            if candidate_index == source_index:

                scene_input = candidate
                break

        # 구형 프로젝트 호환:
        # source_index가 없는 경우에만 위치 기반 fallback
        if (
            not scene_input
            and index < len(
                scene_inputs
            )
        ):

            scene_input = (
                scene_inputs[index]
                or {}
            )

        narration = str(
            scene_input.get(
                "narration",
                "",
            )
            or ""
        ).strip()

        old_duration = max(
            0.5,
            float(
                scene.get(
                    "duration",
                    1.0,
                )
                or 1.0
            ),
        )

        raw_path = (
            scene_audio_folder
            / f"scene_{index + 1:02d}_raw.wav"
        )

        trim_path = (
            scene_audio_folder
            / f"scene_{index + 1:02d}.wav"
        )

        if narration:

            generate_typecast_tts(
                narration,
                typecast[
                    "api_key"
                ],
                typecast[
                    "voice_id"
                ],
                raw_path,
                typecast[
                    "speed"
                ],
            )

            _trim_scene_audio(
                raw_path,
                trim_path,
            )

            # ------------------------------------------------
            # 장면별 나레이션 볼륨 정규화
            # 각 Typecast 생성물의 체감 음량 차이를 줄인다.
            # ------------------------------------------------

            normalized_path = (
                scene_audio_folder
                / f"scene_{index + 1:02d}_normalized.wav"
            )

            run_command(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(
                        trim_path
                    ),
                    "-af",
                    (
                        "loudnorm="
                        "I=-16:"
                        "TP=-1.5:"
                        "LRA=7"
                    ),
                    "-ar",
                    "44100",
                    "-ac",
                    "2",
                    "-c:a",
                    "pcm_s16le",
                    str(
                        normalized_path
                    ),
                ]
            )

            voice_duration = (
                _probe_duration(
                    normalized_path
                )
            )

            if voice_duration <= 0:

                raise RuntimeError(
                    f"장면 {index + 1} "
                    "TTS 길이를 확인하지 못했습니다."
                )

            trim_path = (
                normalized_path
            )

            # 역사쿠키처럼 TTS 실제 길이를 기준으로 한다.
            # 너무 짧은 장면은 최소 1초 확보.
            # 쇼핑쇼츠 장면은 너무 빨리 넘어가지 않도록
            # 최소 3초를 확보한다.
            #
            # 나레이션이 3초보다 길면
            # 실제 음성 길이 + 0.15초 여유를 사용한다.
            # 나레이션은 절대 자르지 않는다.
            # 최소 장면 길이는 3초,
            # 긴 나레이션은 실제 음성 길이 + 0.15초 사용.
            # 장면 길이를 실제 나레이션 길이에 맞춘다.
            # 음성이 끝난 뒤 약간의 여유만 확보한다.
            scene_duration = max(
                0.8,
                voice_duration + 0.06,
            )

            voice_path = str(
                trim_path
            )

        else:

            # 빈 나레이션 장면은 기존 화면 길이를 유지하고
            # 해당 슬롯에 무음을 넣는다.
            voice_duration = 0.0
            # 나레이션이 없는 장면은 기존 길이를 유지하되
            # 너무 짧은 장면만 최소 0.8초 확보.
            scene_duration = max(
                0.8,
                old_duration,
            )

            voice_path = ""

        timeline_rows.append(
            {
                "scene":
                    dict(
                        scene
                    ),

                "narration":
                    narration,

                "voice_path":
                    voice_path,

                "voice_duration":
                    voice_duration,

                "scene_duration":
                    scene_duration,
            }
        )

    # --------------------------------------------------------
    # TTS 실제 길이로 scene_plan 재작성
    # --------------------------------------------------------

    cursor = 0.0
    new_scene_plan = []

    for row in timeline_rows:

        scene = dict(
            row[
                "scene"
            ]
        )

        scene_duration = max(
            0.5,
            float(
                row[
                    "scene_duration"
                ]
            ),
        )

        start = cursor
        end = (
            start
            + scene_duration
        )

        scene[
            "start"
        ] = start

        scene[
            "end"
        ] = end

        scene[
            "duration"
        ] = scene_duration

        scene[
            "narration_duration"
        ] = float(
            row[
                "voice_duration"
            ]
        )

        new_scene_plan.append(
            scene
        )

        row[
            "start"
        ] = start

        row[
            "end"
        ] = end

        cursor = end

    content_duration = (
        cursor
    )

    # --------------------------------------------------------
    # 각 장면을 정확한 길이의 WAV 슬롯으로 만든다.
    #
    # 음성이 1.3초 / 장면이 1.3초면 그대로.
    # 음성이 0.8초 / 최소 장면 1초면 뒤에 0.2초 무음.
    # 빈 나레이션이면 해당 장면 전체가 무음.
    # --------------------------------------------------------

    slot_paths = []

    for index, row in enumerate(
        timeline_rows,
        start=1,
    ):

        scene_duration = float(
            row[
                "scene_duration"
            ]
        )

        slot_path = (
            scene_audio_folder
            / f"scene_{index:02d}_slot.wav"
        )

        voice_path = str(
            row.get(
                "voice_path",
                "",
            )
            or ""
        ).strip()

        if (
            voice_path
            and Path(
                voice_path
            ).is_file()
        ):

            run_command(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    voice_path,
                    "-af",
                    (
                        "apad,"
                        f"atrim=duration={scene_duration:.3f},"
                        "afade=t=out:st="
                        f"{max(0.0, scene_duration - 0.035):.3f}:"
                        "d=0.035"
                    ),
                    "-ar",
                    "44100",
                    "-ac",
                    "2",
                    "-c:a",
                    "pcm_s16le",
                    str(
                        slot_path
                    ),
                ]
            )

        else:

            run_command(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "anullsrc=r=44100:cl=stereo",
                    "-t",
                    f"{scene_duration:.3f}",
                    "-c:a",
                    "pcm_s16le",
                    str(
                        slot_path
                    ),
                ]
            )

        slot_paths.append(
            str(
                slot_path.resolve()
            )
        )

    if not slot_paths:

        raise RuntimeError(
            "장면 음성 슬롯을 만들지 못했습니다."
        )

    # --------------------------------------------------------
    # adelay + amix가 아니라
    # 역사쿠키처럼 장면 순서대로 concat
    # --------------------------------------------------------

    concat_list = (
        scene_audio_folder
        / "scene_audio.concat.txt"
    )

    concat_list.write_text(
        "\n".join(
            "file '"
            + path.replace(
                "'",
                "'\\''",
            )
            + "'"
            for path in slot_paths
        )
        + "\n",
        encoding="utf-8",
    )

    content_master = (
        folder
        / "scene_narration_content.wav"
    )

    run_command(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(
                concat_list
            ),
            "-c:a",
            "pcm_s16le",
            str(
                content_master
            ),
        ]
    )

    if (
        not content_master.is_file()
        or content_master.stat().st_size
        <= 1024
    ):

        raise RuntimeError(
            "장면 나레이션 concat에 실패했습니다."
        )

    return {
        "narration_path":
            str(
                content_master
            ),

        "scene_plan":
            new_scene_plan,

        "content_duration":
            content_duration,

        "scene_count":
            len(
                new_scene_plan
            ),
    }




def generate_typecast_tts(
    text,
    api_key,
    voice_id,
    output_path,
    tempo=1.2,
):

    from typecast import Typecast
    from typecast.models import TTSRequest

    client = Typecast(
        api_key=api_key
    )

    request = TTSRequest(
        text=text,
        model="ssfm-v30",
        voice_id=voice_id,
    )

    response = (
        client.text_to_speech(
            request
        )
    )

    audio_data = getattr(
        response,
        "audio_data",
        None,
    )

    if not audio_data:

        raise RuntimeError(
            "Typecast 음성 생성 실패"
        )

    output_path = Path(
        output_path
    )

    output_path.write_bytes(
        audio_data
    )

    tempo = max(
        0.8,
        min(
            1.5,
            float(
                tempo
            ),
        ),
    )

    if abs(
        tempo
        - 1
    ) > 0.01:

        temp = (
            output_path.parent
            / "narration_speed.wav"
        )

        run_command(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(
                    output_path
                ),
                "-filter:a",
                f"atempo={tempo:.3f}",
                str(
                    temp
                ),
            ]
        )

        shutil.move(
            str(
                temp
            ),
            str(
                output_path
            ),
        )


# =========================================================
# SAVE UPLOAD
# =========================================================

def save_uploaded(
    uploaded,
    folder,
    prefix,
):

    if uploaded is None:
        return ""

    suffix = Path(
        uploaded.name
    ).suffix.lower()

    folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = (
        folder
        / f"{prefix}{suffix}"
    )

    uploaded.seek(
        0
    )

    path.write_bytes(
        uploaded.getbuffer()
    )

    return str(
        path
    )


def save_sources(
    uploaded_files,
    folder,
):

    result = []

    for index, uploaded in enumerate(
        uploaded_files or [],
        start=1,
    ):

        suffix = Path(
            uploaded.name
        ).suffix.lower()

        if (
            suffix
            not in IMAGE_EXTENSIONS
            and suffix
            not in VIDEO_EXTENSIONS
        ):
            continue

        target = (
            folder
            / (
                f"source_"
                f"{index:02d}"
                f"{suffix}"
            )
        )

        uploaded.seek(
            0
        )

        target.write_bytes(
            uploaded.getbuffer()
        )

        result.append(
            {
                "path":
                    str(
                        target
                    ),

                "type": (
                    "video"
                    if suffix
                    in VIDEO_EXTENSIONS
                    else "image"
                ),

                # V5.30
                # 의미 기반 장면-자막 매칭용 원본 파일명
                "original_name":
                    str(
                        uploaded.name
                    ),
            }
        )

    return result


# =========================================================
# VIDEO
# =========================================================

def render_image_clip(
    image_path,
    output_path,
    duration,
    index,
):

    fps = 30

    frames = max(
        1,
        int(
            duration
            * fps
        ),
    )

    if index % 2:

        motion = (
            f"zoompan="
            f"z='min(zoom+0.0060,1.28)':"
            f"x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':"
            f"d={frames}:"
            f"s=1080x1920:"
            f"fps=30"
        )

    else:

        motion = (
            f"zoompan="
            f"z='1.20':"
            f"x='(iw-iw/zoom)*on/{frames}':"
            f"y='ih/2-(ih/zoom/2)':"
            f"d={frames}:"
            f"s=1080x1920:"
            f"fps=30"
        )

    vf = (
        "scale=1300:2200:"
        "force_original_aspect_ratio=increase,"
        "crop=1300:2200,"
        + motion
        + ",format=yuv420p"
    )

    run_command(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(
                image_path
            ),
            "-vf",
            vf,
            "-t",
            f"{duration:.3f}",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            str(
                output_path
            ),
        ]
    )


def render_video_clip(
    path,
    output,
    duration,
):

    run_command(
        [
            "ffmpeg",
            "-y",
            "-stream_loop",
            "-1",
            "-i",
            str(
                path
            ),
            "-t",
            f"{duration:.3f}",
            "-vf",
            (
                "scale=1080:1920:"
                "force_original_aspect_ratio=increase,"
                "crop=1080:1920,"
                "fps=30,"
                "format=yuv420p"
            ),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            str(
                output
            ),
        ]
    )


def concat_clips(
    clips,
    output,
    folder,
):

    txt = (
        folder
        / "concat.txt"
    )

    rows = []

    for clip in clips:

        path = (
            Path(
                clip
            )
            .resolve()
            .as_posix()
        )

        rows.append(
            f"file '{path}'"
        )

    txt.write_text(
        "\n".join(
            rows
        ),
        encoding="utf-8",
    )

    run_command(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(
                txt
            ),
            "-c",
            "copy",
            str(
                output
            ),
        ]
    )





def extract_video_analysis_frames(
    video_path,
    output_folder,
    frame_count=3,
):
    """
    V5.50 VIDEO ANALYSIS FRAME EXTRACTOR

    영상 자체는 수정하지 않고
    AI 분석용 대표 프레임만 추출한다.

    기본 3장:
    - 20%
    - 50%
    - 80%
    """

    video_path = Path(
        video_path
    )

    output_folder = Path(
        output_folder
    )

    output_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    if (
        not video_path.is_file()
    ):
        return []

    try:

        duration = float(
            media_duration(
                video_path
            )
        )

    except Exception:

        duration = 0.0

    if duration <= 0.05:
        return []

    if int(frame_count) <= 1:

        ratios = [
            0.50
        ]

    elif int(frame_count) == 2:

        ratios = [
            0.30,
            0.70,
        ]

    else:

        ratios = [
            0.20,
            0.50,
            0.80,
        ]

    result = []

    for frame_no, ratio in enumerate(
        ratios,
        start=1,
    ):

        timestamp = max(
            0.05,
            min(
                duration - 0.05,
                duration
                * float(ratio),
            ),
        )

        output_path = (
            output_folder
            / (
                f"frame_"
                f"{frame_no:02d}.jpg"
            )
        )

        try:

            run_command(
                [
                    "ffmpeg",
                    "-y",
                    "-ss",
                    f"{timestamp:.3f}",
                    "-i",
                    str(
                        video_path
                    ),
                    "-frames:v",
                    "1",
                    "-vf",
                    (
                        "scale=720:-2:"
                        "force_original_aspect_ratio=decrease"
                    ),
                    "-q:v",
                    "2",
                    str(
                        output_path
                    ),
                ]
            )

        except Exception:

            continue

        if output_path.is_file():

            result.append(
                {
                    "path":
                        str(
                            output_path
                        ),

                    "timestamp":
                        timestamp,

                    "ratio":
                        float(
                            ratio
                        ),
                }
            )

    return result


def build_video_analysis_manifest(
    sources,
    folder,
):
    """
    V5.60 AI SOURCE ANALYSIS MANIFEST

    영상 + 이미지 전체를 업로드 순서 그대로 분석 대상으로 만든다.

    영상:
    - 실제 길이 사용
    - 20% / 50% / 80% 대표 프레임 3장

    이미지:
    - 원본 이미지 자체를 분석
    - AI 나레이션용 예상 노출시간 1.55초

    원본 영상/이미지는 수정하지 않는다.
    """

    folder = Path(
        folder
    )

    analysis_root = (
        folder
        / "ai_video_frames"
    )

    analysis_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    IMAGE_AI_DURATION = 1.55

    result = []

    for source_index, source in enumerate(
        sources or [],
        start=1,
    ):

        source_type = str(
            source.get(
                "type",
                "",
            )
        ).lower()

        if source_type not in (
            "video",
            "image",
        ):
            continue

        source_path = str(
            source.get(
                "path",
                "",
            )
            or ""
        )

        if not source_path:
            continue

        original_name = str(
            source.get(
                "original_name",
                "",
            )
        )

        # -------------------------------------------------
        # VIDEO
        # -------------------------------------------------

        if source_type == "video":

            try:

                duration = float(
                    media_duration(
                        source_path
                    )
                )

            except Exception:

                duration = 0.0

            scene_folder = (
                analysis_root
                / f"video_{source_index:02d}"
            )

            frames = (
                extract_video_analysis_frames(
                    source_path,
                    scene_folder,
                    frame_count=3,
                )
            )

            result.append(
                {
                    "source_index":
                        source_index - 1,

                    "source_type":
                        "video",

                    "path":
                        source_path,

                    "original_name":
                        original_name,

                    "duration":
                        duration,

                    "frames":
                        frames,
                }
            )

        # -------------------------------------------------
        # IMAGE
        # -------------------------------------------------

        else:

            image_path = Path(
                source_path
            )

            if not image_path.is_file():
                continue

            result.append(
                {
                    "source_index":
                        source_index - 1,

                    "source_type":
                        "image",

                    "path":
                        source_path,

                    "original_name":
                        original_name,

                    "duration":
                        IMAGE_AI_DURATION,

                    "frames":
                        [
                            {
                                "path":
                                    source_path,

                                "timestamp":
                                    0.0,

                                "ratio":
                                    1.0,
                            }
                        ],
                }
            )

    return result


def build_ai_narration_cache_key(
    sources,
    product_name,
    review_summary,
    model,
):
    """
    동일한 제품/영상/리뷰요약/모델이면
    같은 캐시 키를 만든다.

    영상 파일은 내용 자체를 SHA256으로 확인한다.
    """

    hasher = hashlib.sha256()

    hasher.update(
        str(
            product_name or ""
        ).strip().encode(
            "utf-8"
        )
    )

    hasher.update(
        b"\n---review---\n"
    )

    hasher.update(
        str(
            review_summary or ""
        ).strip().encode(
            "utf-8"
        )
    )

    hasher.update(
        b"\n---model---\n"
    )

    hasher.update(
        str(
            model or ""
        ).strip().encode(
            "utf-8"
        )
    )

    for source in sources or []:

        source_type = str(
            source.get(
                "type",
                "",
            )
        ).lower()

        if source_type not in (
            "video",
            "image",
        ):
            continue

        source_path = Path(
            str(
                source.get(
                    "path",
                    "",
                )
            )
        )

        original_name = str(
            source.get(
                "original_name",
                "",
            )
        )

        hasher.update(
            original_name.encode(
                "utf-8"
            )
        )

        if not source_path.is_file():
            continue

        if source_type == "video":

            try:

                duration = float(
                    media_duration(
                        source_path
                    )
                )

            except Exception:

                duration = 0.0

            hasher.update(
                f"{duration:.3f}".encode(
                    "utf-8"
                )
            )

        else:

            hasher.update(
                b"IMAGE"
            )

        # 파일 내용까지 확인
        with source_path.open(
            "rb"
        ) as file_obj:

            while True:

                chunk = file_obj.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                hasher.update(
                    chunk
                )

    return hasher.hexdigest()


def find_ai_narration_cache(
    cache_key,
):
    """
    기존 AI 나레이션 히스토리에서
    동일 캐시 키를 찾는다.
    """

    if not cache_key:
        return None

    history = (
        load_ai_narration_history()
    )

    for item in history:

        if (
            str(
                item.get(
                    "cache_key",
                    "",
                )
            )
            == str(
                cache_key
            )
        ):

            return item

    return None


def load_ai_narration_history():
    """
    이전에 생성한 AI 나레이션 기록을 불러온다.
    최신 기록이 먼저 나오도록 반환.
    """

    if not AI_NARRATION_HISTORY.is_file():
        return []

    try:

        data = json.loads(
            AI_NARRATION_HISTORY.read_text(
                encoding="utf-8"
            )
        )

        if not isinstance(
            data,
            list,
        ):
            return []

        return list(
            reversed(
                data
            )
        )

    except Exception:

        return []


def save_ai_narration_history(
    product_name,
    script,
    results,
    review_summary="",
    cache_key="",
):
    """
    AI 나레이션 생성 성공 시 기록을 누적 저장한다.
    기존 기록은 덮어쓰지 않는다.
    """

    from datetime import datetime

    try:

        if AI_NARRATION_HISTORY.is_file():

            history = json.loads(
                AI_NARRATION_HISTORY.read_text(
                    encoding="utf-8"
                )
            )

            if not isinstance(
                history,
                list,
            ):
                history = []

        else:

            history = []

    except Exception:

        history = []

    now = datetime.now()

    clean_results = []

    for item in results or []:

        clean_results.append(
            {
                "video_no":
                    item.get(
                        "video_no"
                    ),

                "source_index":
                    item.get(
                        "source_index"
                    ),

                "duration":
                    float(
                        item.get(
                            "duration",
                            0.0,
                        )
                    ),

                "narration":
                    str(
                        item.get(
                            "narration",
                            "",
                        )
                    ),
            }
        )

    entry = {
        "id":
            now.strftime(
                "%Y%m%d_%H%M%S_%f"
            ),

        "created_at":
            now.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

        "product_name":
            str(
                product_name or ""
            ).strip(),

        "review_summary":
            str(
                review_summary or ""
            ).strip(),

        "script":
            str(
                script or ""
            ).strip(),

        "results":
            clean_results,

        "cache_key":
            str(
                cache_key or ""
            ),
    }

    history.append(
        entry
    )

    # 너무 오래 쌓이지 않게 최근 100개 보관
    history = history[
        -100:
    ]

    AI_NARRATION_HISTORY.write_text(
        json.dumps(
            history,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return entry


def generate_video_narration_with_openai(
    sources,
    folder,
    product_name,
    review_summary,
    api_key,
    model,
):
    """
    업로드된 '영상'을 실제 프레임으로 분석해서
    각 영상 길이에 맞는 짧은 광고 나레이션을 생성한다.

    중요:
    - 원본 영상 수정 안 함
    - 영상 속도 수정 안 함
    - 영상 길이 수정 안 함
    - 업로드 순서 수정 안 함
    """

    import base64
    import mimetypes

    from openai import OpenAI

    api_key = str(
        api_key or ""
    ).strip()

    if not api_key:
        raise RuntimeError(
            "OpenAI API Key가 없습니다."
        )

    model = str(
        model or "gpt-5-mini"
    ).strip()

    client = OpenAI(
        api_key=api_key
    )

    manifest = (
        build_video_analysis_manifest(
            sources,
            folder,
        )
    )

    if not manifest:
        raise RuntimeError(
            "분석할 영상이 없습니다."
        )

    review_summary = str(
        review_summary or ""
    ).strip()

    product_name = str(
        product_name or ""
    ).strip()

    results = []

    for video_no, item in enumerate(
        manifest,
        start=1,
    ):

        source_type = str(
            item.get(
                "source_type",
                "video",
            )
            or "video"
        ).lower()

        duration = max(
            0.1,
            float(
                item.get(
                    "duration",
                    0.0,
                )
            ),
        )

        frames = (
            item.get(
                "frames",
                []
            )
            or []
        )

        if not frames:
            continue

        # --------------------------------------------------
        # 영상 초수에 따른 대략적인 한국어 발화량
        #
        # Typecast 속도 차이가 있으므로
        # 꽉 채우지 않고 여유 있게 생성한다.
        # --------------------------------------------------

        target_chars = max(
            8,
            int(
                duration * 4.2
            ),
        )

        target_chars = min(
            target_chars,
            55,
        )

        scene_label = (
            "영상"
            if source_type == "video"
            else "이미지"
        )

        prompt = f"""
당신은 한국 쇼핑 숏폼 광고의 나레이션 작가입니다.

제품명:
{product_name or "제품명 미입력"}

현재 분석 장면:
{scene_label}

이 장면의 나레이션 가능 시간:
{duration:.2f}초

구매자 AI 리뷰요약:
{review_summary or "리뷰요약 없음"}

제공된 실제 장면을 확인한 뒤
그 장면에서 눈으로 확인되는 내용과 정확히 맞는
한국어 쇼핑 숏폼 광고 나레이션 한 문장만 작성하세요.

매우 중요한 규칙:

1. 이미지에서 확인되지 않는 동작을 지어내지 마세요.
2. 리뷰요약은 화면과 내용이 일치할 때만 활용하세요.
3. 제품명만 보고 기능을 추측하지 마세요.
4. 이 장면에서 사용할 수 있는 시간은 {duration:.2f}초입니다.
5. 약 {target_chars}자 안팎의 짧은 문장으로 작성하세요.
6. 장면이 끝나기 전에 읽을 수 있도록 짧게 작성하세요.
7. 자연스럽고 빠른 숏폼 광고 말투를 사용하세요.
8. 가격이나 할인 정보가 제공되지 않았다면 만들지 마세요.
9. 설명, 번호, 따옴표 없이 실제 읽을 나레이션만 출력하세요.
10. '영상에서', '화면에서', '이미지에서' 같은 표현은 사용하지 마세요.

예시 형식:
얼음도 빠르게 갈려서 시원한 음료를 간편하게 만들 수 있어요.
""".strip()

        content = [
            {
                "type": "input_text",
                "text": prompt,
            }
        ]

        for frame in frames:

            frame_path = Path(
                frame["path"]
            )

            if not frame_path.is_file():
                continue

            mime = (
                mimetypes.guess_type(
                    str(
                        frame_path
                    )
                )[0]
                or "image/jpeg"
            )

            encoded = (
                base64.b64encode(
                    frame_path.read_bytes()
                )
                .decode(
                    "ascii"
                )
            )

            content.append(
                {
                    "type": "input_image",
                    "image_url":
                        f"data:{mime};base64,{encoded}",
                }
            )

        response = (
            client.responses.create(
                model=model,
                input=[
                    {
                        "role": "user",
                        "content": content,
                    }
                ],
            )
        )

        narration = str(
            response.output_text
            or ""
        ).strip()

        if not narration:
            continue

        results.append(
            {
                "video_no":
                    video_no,

                "source_index":
                    item.get(
                        "source_index"
                    ),

                "source_type":
                    source_type,

                "duration":
                    duration,

                "narration":
                    narration,
            }
        )

    if not results:
        raise RuntimeError(
            "AI가 나레이션을 생성하지 못했습니다."
        )

    return results


def combine_ai_video_narrations(
    results,
):
    """
    영상별 AI 나레이션을
    Typecast 입력용 하나의 대본으로 합친다.
    """

    lines = []

    for item in results or []:

        text = str(
            item.get(
                "narration",
                "",
            )
        ).strip()

        if text:
            lines.append(
                text
            )

    return "\n\n".join(
        lines
    )


def classify_source_scene(source):
    """
    V5.30 SOURCE SCENE SEMANTIC CLASSIFIER

    원본 파일명에서 확실하게 판단 가능한 의미만 분류한다.

    중요:
    - 파일명을 근거 없이 추측하지 않는다.
    - 판단 불가능하면 generic.
    - scene 순서는 변경하지 않는다.
    """

    source = source or {}

    name = str(
        source.get(
            "original_name",
            "",
        )
        or Path(
            str(
                source.get(
                    "path",
                    "",
                )
            )
        ).name
    )

    compact = re.sub(
        r"[\s_\-\(\)\[\]]+",
        "",
        name,
    ).lower()

    # -----------------------------------------------
    # DISHWASHER
    # -----------------------------------------------

    if re.search(
        r"식기세척|식세기|dishwasher",
        compact,
        re.I,
    ):
        return "dishwasher"

    # -----------------------------------------------
    # CLEANING / WASH
    # -----------------------------------------------

    if re.search(
        r"세척|물세척|씻|청소|wash|clean",
        compact,
        re.I,
    ):
        return "cleaning"

    # -----------------------------------------------
    # COLOR / DESIGN
    # -----------------------------------------------

    if re.search(
        r"컬러|색상|색깔|color|colour",
        compact,
        re.I,
    ):
        return "color"

    # -----------------------------------------------
    # FOOD / DRINK / RESULT
    # -----------------------------------------------

    if re.search(
        (
            r"음식|요리|완성|빙수|주스|쥬스|"
            r"수프|스프|소스|스무디|음료|"
            r"레시피|food|juice|soup|sauce|"
            r"smoothie|recipe"
        ),
        compact,
        re.I,
    ):
        return "cooking"

    # -----------------------------------------------
    # INTERACTION / PRODUCT USE
    # -----------------------------------------------

    if re.search(
        (
            r"사용|작동|버튼|터치|분리|장착|"
            r"뚜껑|컵|열기|닫기|"
            r"use|button|lid|open|close"
        ),
        compact,
        re.I,
    ):
        return "interaction"

    # -----------------------------------------------
    # REVIEW
    # -----------------------------------------------

    if re.search(
        r"리뷰|후기|평점|별점|review",
        compact,
        re.I,
    ):
        return "review"

    # -----------------------------------------------
    # PRICE / PROMOTION
    # -----------------------------------------------

    if re.search(
        r"가격|할인|특가|쿠폰|price|sale",
        compact,
        re.I,
    ):
        return "promotion"

    return "generic"


def build_scene_plan(
    sources,
    duration,
):
    """
    V5.21 AUTO SCENE PLAN

    핵심 규칙
    - 업로드 순서 유지
    - 영상은 편집된 실제 길이 그대로 사용
    - 영상 속도/길이 자동 조정 금지
    - 이미지만 남은 시간에 맞춰 자동 배분
    - 모든 후속 기능은 동일 scene_plan 사용
    """

    sources = list(
        sources or []
    )

    if not sources:
        return []

    target_duration = max(
        1.0,
        float(
            duration
        ),
    )

    # -----------------------------------------------------
    # IMAGE RULE
    # -----------------------------------------------------

    IMAGE_BASE_DURATION = 1.55
    IMAGE_MIN_DURATION = 1.40
    IMAGE_MAX_DURATION = 1.90

    prepared = []

    video_total = 0.0
    image_count = 0

    # -----------------------------------------------------
    # 1. SOURCE ANALYSIS
    # -----------------------------------------------------

    for index, source in enumerate(
        sources
    ):

        source_type = str(
            source.get(
                "type",
                "image",
            )
        ).lower()

        source_path = str(
            source.get(
                "path",
                "",
            )
            or ""
        )

        if source_type == "video":

            try:

                real_duration = float(
                    media_duration(
                        source_path
                    )
                )

            except Exception:

                real_duration = 0.0

            # ffprobe 실패 시에만 최소 안전값
            if real_duration <= 0:

                real_duration = 1.0

            # 중요:
            # 영상은 원본 편집 길이를 그대로 사용
            scene_duration = real_duration

            video_total += (
                scene_duration
            )

        else:

            real_duration = 0.0
            scene_duration = None

            image_count += 1

        prepared.append(
            {
                "index": index,
                "type": source_type,
                "path": source_path,
                "real_duration":
                    real_duration,
                "duration":
                    scene_duration,
            }
        )

    # -----------------------------------------------------
    # 2. IMAGE DURATION
    #
    # 영상 시간은 고정.
    # 남는 시간만 이미지끼리 배분.
    # -----------------------------------------------------

    if image_count > 0:

        remaining = max(
            0.0,
            target_duration
            - video_total,
        )

        image_duration = (
            remaining
            / image_count
            if remaining > 0
            else IMAGE_MIN_DURATION
        )

        # 일반적인 경우 읽을 수 있는 범위 유지
        if remaining >= (
            IMAGE_MIN_DURATION
            * image_count
        ):

            image_duration = max(
                IMAGE_MIN_DURATION,
                min(
                    IMAGE_MAX_DURATION,
                    image_duration,
                ),
            )

        else:

            # 영상 길이는 절대 줄이지 않는다.
            #
            # 나레이션 기준 시간이 부족하더라도
            # 이미지 역시 읽을 수 있는 최소 시간을 보장한다.
            #
            # 따라서 필요한 경우 전체 scene timeline이
            # target_duration보다 길어지는 것을 허용한다.
            image_duration = (
                IMAGE_MIN_DURATION
            )

        for item in prepared:

            if item[
                "type"
            ] != "video":

                item[
                    "duration"
                ] = image_duration

    # -----------------------------------------------------
    # 3. EXACT TIMELINE
    # -----------------------------------------------------

    cursor = 0.0
    scene_plan = []

    for item in prepared:

        scene_duration = max(
            0.01,
            float(
                item[
                    "duration"
                ]
            ),
        )

        start = cursor
        end = (
            start
            + scene_duration
        )

        scene_plan.append(
            {
                "index":
                    item[
                        "index"
                    ],

                "type":
                    item[
                        "type"
                    ],

                "path":
                    item[
                        "path"
                    ],

                "semantic":
                    classify_source_scene(
                        sources[
                            item[
                                "index"
                            ]
                        ]
                    ),

                "original_name":
                    str(
                        sources[
                            item[
                                "index"
                            ]
                        ].get(
                            "original_name",
                            "",
                        )
                    ),

                "real_duration":
                    item[
                        "real_duration"
                    ],

                "start":
                    start,

                "end":
                    end,

                "duration":
                    scene_duration,
            }
        )

        cursor = end

    return scene_plan




def extend_video_to_duration(
    video,
    output,
    target_duration,
):
    """
    원본 장면의 속도/길이는 건드리지 않고
    필요한 경우 마지막 프레임만 유지해서
    최종 영상 길이를 확보한다.
    """

    current = float(
        media_duration(
            video
        )
    )

    target = max(
        current,
        float(
            target_duration
        ),
    )

    pad = max(
        0.0,
        target - current,
    )

    if pad <= 0.01:

        shutil.copy2(
            video,
            output,
        )

        return

    run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video),
            "-vf",
            (
                "tpad="
                "stop_mode=clone:"
                f"stop_duration={pad:.3f},"
                "format=yuv420p"
            ),
            "-an",
            "-t",
            f"{target:.3f}",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            str(output),
        ]
    )


def make_content_video(
    sources,
    duration,
    folder,
    scene_plan=None,
):

    if not sources:

        raise RuntimeError(
            "제품 이미지/영상이 없습니다."
        )

    if scene_plan is None:

        scene_plan = (
            build_scene_plan(
                sources,
                duration,
            )
        )

    if not scene_plan:

        raise RuntimeError(
            "장면 타임라인을 만들지 못했습니다."
        )

    clips = []

    for scene_no, scene in enumerate(
        scene_plan,
        start=1,
    ):

        output = (
            folder
            / f"clip_{scene_no:02d}.mp4"
        )

        source_path = (
            scene["path"]
        )

        scene_duration = max(
            0.35,
            float(
                scene["duration"]
            ),
        )

        if (
            scene["type"]
            == "video"
        ):

            render_video_clip(
                source_path,
                output,
                scene_duration,
            )

        else:

            render_image_clip(
                source_path,
                output,
                scene_duration,
                scene_no,
            )

        clips.append(
            str(
                output
            )
        )

    final = (
        folder
        / "content.mp4"
    )

    concat_clips(
        clips,
        final,
        folder,
    )

    return str(
        final
    )



# =========================================================
# IMAGE PROOF CARD
# =========================================================

def add_card(
    source_video,
    image_path,
    output_video,
    start,
    duration,
    width,
    y,
    x=None,
):

    if (
        not image_path
        or not Path(
            image_path
        ).is_file()
    ):

        shutil.copy2(
            source_video,
            output_video,
        )

        return

    end = (
        start
        + duration
    )

    overlay_x = (
        "(W-w)/2"
        if x is None
        else str(int(x))
    )

    fc = (
        "[1:v]"
        f"scale={width}:-1:"
        "force_original_aspect_ratio=decrease,"
        "format=rgba,"
        "pad=iw+30:ih+30:15:15:"
        "color=white@0.97,"
        f"setpts=PTS-STARTPTS+{start}/TB"
        "[card];"

        "[0:v][card]"
        "overlay="
        f"x={overlay_x}:"
        f"y={y}:"
        f"enable='between(t,{start},{end})'"
        "[v]"
    )

    run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(
                source_video
            ),
            "-loop",
            "1",
            "-t",
            str(
                duration
            ),
            "-i",
            str(
                image_path
            ),
            "-filter_complex",
            fc,
            "-map",
            "[v]",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            str(
                output_video
            ),
        ]
    )



def add_ad_badge(
    source_video,
    output_video,
):
    """
    전체 영상 왼쪽 상단에 [광고] 고정 표시.
    플랫폼 안전영역 안쪽에 배치.
    """

    fonts = detect_fonts()

    font_path = (
        fonts.get("highlight_file")
        or fonts.get("normal_file")
    )

    if not font_path:

        shutil.copy2(
            source_video,
            output_video,
        )
        return

    font_ffmpeg = (
        Path(font_path)
        .resolve()
        .as_posix()
        .replace(
            ":",
            r"\:",
        )
    )

    text = escape_drawtext(
        "[광고]"
    )

    vf = (
        "drawtext="
        f"fontfile='{font_ffmpeg}':"
        f"text='{text}':"
        "fontcolor=#FFE600:"
        "fontsize=42:"
        "x=62:"
        "y=72:"
        "box=1:"
        "boxcolor=black@0.72:"
        "boxborderw=14"
    )

    run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source_video),
            "-vf",
            vf,
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            str(output_video),
        ]
    )


# =========================================================
# SUBTITLE
# =========================================================

AUTO_HIGHLIGHT = re.compile(
    r"("
    r"\d{1,3}\s*%"
    r"|"
    r"\d{1,3}(?:,\d{3})+\s*원"
    r"|"
    r"\d+(?:\.\d+)?\s*L"
    r"|"
    r"리뷰\s*[\d,]+\s*개?"
    r"|"
    r"[\d,]+\s*개"
    r"|"
    r"후기\s*[\d,]+\s*개?"
    r"|"
    r"[\d,]+\s*개"
    r"|"
    r"★\s*\d+(?:\.\d+)?"
    r"|"
    r"D\s*-\s*\d+"
    r"|"
    r"\d+\s*일\s*한정"
    r"|"
    r"최대\s*혜택가"
    r"|"
    r"최대\s*할인가"
    r"|"
    r"올스테인리스"
    r"|"
    r"올스텐"
    r"|"
    r"대용량"
    r"|"
    r"할인"
    r"|"
    r"특가"
    r"|"
    r"종료\s*임박"
    r")",
    re.I,
)


PRICE_HIGHLIGHT = re.compile(
    r"("
    r"\d{1,3}(?:,\d{3})+\s*원"
    r"|"
    r"D\s*-\s*\d+"
    r"|"
    r"\d{1,3}\s*%"
    r"|"
    r"특가"
    r"|"
    r"종료\s*임박"
    r")",
    re.I,
)


STEEL_HIGHLIGHT = re.compile(
    r"("
    r"올스테인리스"
    r"|"
    r"올스텐"
    r")",
    re.I,
)


NUMBER_HIGHLIGHT = re.compile(
    r"("
    r"\d+(?:\.\d+)?\s*L"
    r"|"
    r"리뷰\s*[\d,]+\s*개?"
    r"|"
    r"[\d,]+\s*개"
    r"|"
    r"후기\s*[\d,]+\s*개?"
    r"|"
    r"[\d,]+\s*개"
    r"|"
    r"★\s*\d+(?:\.\d+)?"
    r")",
    re.I,
)


def ass_time(seconds):

    hour = int(seconds // 3600)

    seconds -= hour * 3600

    minute = int(seconds // 60)

    seconds -= minute * 60

    return (
        f"{hour}:"
        f"{minute:02d}:"
        f"{seconds:05.2f}"
    )


def escape_ass(text):

    return (
        str(text)
        .replace("{", "(")
        .replace("}", ")")
    )


def subtitle_highlight_tag(text):

    # 가격 / 긴급성 = 빨강·주황
    if PRICE_HIGHLIGHT.search(text):
        return (
            r"{\fnGmarket Sans Bold"
            r"\fs92"
            r"\c&H0038A8FF&"
            r"\bord6"
            r"\shad0}"
        )

    # 올스텐 = 민트
    if STEEL_HIGHLIGHT.search(text):
        return (
            r"{\fnGmarket Sans Bold"
            r"\fs88"
            r"\c&H00E6FF65&"
            r"\bord6"
            r"\shad0}"
        )

    # 리뷰 / 숫자 / 용량 = 노랑
    if NUMBER_HIGHLIGHT.search(text):
        return (
            r"{\fnGmarket Sans Bold"
            r"\fs90"
            r"\c&H0000EFFF&"
            r"\bord6"
            r"\shad0}"
        )

    return (
        r"{\fnGmarket Sans Bold"
        r"\fs86"
        r"\c&H0000EFFF&"
        r"\bord6"
        r"\shad0}"
    )


def style_subtitle_line(line):
    """
    V5.22 BRACKET HIGHLIGHT

    [무선] -> 무선만 강조
    얼음도 [강력하게 분쇄] -> 괄호 안만 강조
    [강조]문장 -> 기존 전체 강조 유지

    [] 문자는 최종 자막에 표시하지 않는다.
    """

    line = str(
        line or ""
    ).strip()

    # -----------------------------------------------------
    # 기존 [강조] 전체 문장
    # -----------------------------------------------------

    if line.startswith(
        "[강조]"
    ):

        line = line[
            len("[강조]"):
        ].strip()

        return (
            subtitle_highlight_tag(
                line
            )
            + escape_ass(
                line
            )
            + r"{\rDefault}"
        )

    # -----------------------------------------------------
    # 사용자가 직접 지정한 [단어] 부분 강조
    # -----------------------------------------------------

    bracket_pattern = re.compile(
        r"\[([^\[\]\r\n]+)\]"
    )

    matches = list(
        bracket_pattern.finditer(
            line
        )
    )

    if matches:

        result = []
        cursor = 0

        for match in matches:

            if match.start() > cursor:

                before = line[
                    cursor:
                    match.start()
                ]

                result.append(
                    escape_ass(
                        before
                    )
                )

            word = str(
                match.group(1)
                or ""
            ).strip()

            if word:

                result.append(
                    subtitle_highlight_tag(
                        word
                    )
                    + escape_ass(
                        word
                    )
                    + r"{\rDefault}"
                )

            cursor = match.end()

        if cursor < len(line):

            result.append(
                escape_ass(
                    line[cursor:]
                )
            )

        return "".join(
            result
        )

    # -----------------------------------------------------
    # 기존 자동 강조
    # -----------------------------------------------------

    result = []
    cursor = 0

    for match in AUTO_HIGHLIGHT.finditer(
        line
    ):

        if match.start() > cursor:

            result.append(
                escape_ass(
                    line[
                        cursor:
                        match.start()
                    ]
                )
            )

        matched = match.group(0)

        result.append(
            subtitle_highlight_tag(
                matched
            )
            + escape_ass(
                matched
            )
            + r"{\rDefault}"
        )

        cursor = match.end()

    result.append(
        escape_ass(
            line[cursor:]
        )
    )

    return "".join(
        result
    )

def clean_body_subtitle_line(text):
    """
    BODY SUBTITLE CLEAN V5.23

    - [단어] 강조 표시는 유지
    - CTA 문구는 본문에서 제외
    - 컬러 이모지는 ASS 자막에서 제거
    - 외부 CTA_LINE_PATTERN / BODY_EMOJI_PATTERN 의존성 없음
    """

    text = str(
        text or ""
    ).strip()

    # 기존 전체 강조 표기만 제거
    text = text.replace(
        "[강조]",
        ""
    ).strip()

    # -----------------------------------------------------
    # CTA 문구는 add_cta()가 전담
    # -----------------------------------------------------

    compact = re.sub(
        r"\s+",
        "",
        text,
    )

    if (
        "특가종료임박" in compact
        or "특가혜택확인" in compact
        or "지금혜택확인" in compact
        or "현재혜택확인" in compact
        or "하단상품태그" in compact
        or "상품태그클릭" in compact
    ):
        return ""

    # -----------------------------------------------------
    # 컬러 이모지는 PNG 레이어에서 따로 처리
    # ASS 자막에서는 제거
    # -----------------------------------------------------

    text = re.sub(
        (
            r"[\u2600-\u27BF]"
            r"|[\U0001F300-\U0001FAFF]"
        ),
        "",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    return text


def classify_shortform_line(text):
    """
    특정 상품명에 의존하지 않고
    자막 의미를 기준으로 장면 역할을 판별.
    """

    raw = str(
        text or ""
    )

    compact = re.sub(
        r"\s+",
        "",
        raw,
    )

    result = {
        "kind": "feature",
        "emoji": "✨",
        "sfx": "ting",
    }

    # -----------------------------------------------------
    # REVIEW / TRUST
    # -----------------------------------------------------

    if re.search(
        r"리뷰|후기|평점|구매자|만족도|별점",
        raw,
        re.I,
    ):

        result.update(
            {
                "kind": "review",
                "emoji": "⭐",
                "sfx": "pop",
            }
        )

        return result

    # -----------------------------------------------------
    # DISCOUNT / PROMOTION
    # -----------------------------------------------------

    if re.search(
        (
            r"할인|특가|쿠폰|혜택|"
            r"\d{1,3}\s*%|"
            r"\d{1,3}(?:,\d{3})+\s*원|"
            r"D\s*-\s*\d+"
        ),
        raw,
        re.I,
    ):

        result.update(
            {
                "kind": "promotion",
                "emoji": "🔥",
                "sfx": "ding",
            }
        )

        return result

    # -----------------------------------------------------
    # SIZE / CAPACITY / NUMBER
    # -----------------------------------------------------

    if re.search(
        (
            r"대용량|용량|사이즈|크기|"
            r"\d+(?:\.\d+)?\s*(?:L|ml|mL|kg|g|cm|인치)"
        ),
        raw,
        re.I,
    ):

        result.update(
            {
                "kind": "capacity",
                "emoji": "💥",
                "sfx": "pop",
            }
        )

        return result

    # -----------------------------------------------------
    # MATERIAL / QUALITY / FEATURE
    # -----------------------------------------------------

    if re.search(
        (
            r"스텐|스테인리스|소재|재질|"
            r"프리미엄|내구성|기능|성능|"
            r"흡입력|배터리|보습|성분|"
            r"방수|저소음|고속|강력"
        ),
        raw,
        re.I,
    ):

        result.update(
            {
                "kind": "feature",
                "emoji": "✨",
                "sfx": "ting",
            }
        )

        return result

    # -----------------------------------------------------
    # FOOD / COOKING
    # 지글거림은 실제 요리 관련일 때만 사용
    # -----------------------------------------------------

    if re.search(
        (
            r"요리|조리|굽|튀김|에어프라이|"
            r"오븐|치킨|고기|스테이크|"
            r"바삭|음식|레시피"
        ),
        raw,
        re.I,
    ):

        result.update(
            {
                "kind": "cooking",
                "emoji": "🔥",
                "sfx": "sizzle",
            }
        )

        return result

    # -----------------------------------------------------
    # ACTION / USE
    # 제품 사용 동작 전반
    # -----------------------------------------------------

    if re.search(
        (
            r"열면|닫으면|누르면|돌리면|"
            r"사용|장착|분리|세척|꺼내|"
            r"버튼|터치|클릭"
        ),
        raw,
        re.I,
    ):

        result.update(
            {
                "kind": "interaction",
                "emoji": "✅",
                "sfx": "click",
            }
        )

        return result

    return result



def subtitle_reading_weight(text):
    """
    실제 TTS 타임스탬프가 없을 때
    문장별 예상 발화량을 계산한다.

    짧은 문장은 짧게,
    긴 문장은 더 오래 표시한다.
    """

    raw = str(
        text or ""
    ).strip()

    if not raw:
        return 1.0

    # 강조 태그 제거
    clean = re.sub(
        r"\[[^\]]+\]",
        "",
        raw,
    )

    hangul = len(
        re.findall(
            r"[가-힣]",
            clean,
        )
    )

    digits = len(
        re.findall(
            r"[0-9]",
            clean,
        )
    )

    latin = len(
        re.findall(
            r"[A-Za-z]",
            clean,
        )
    )

    # 말할 때 자연스럽게 생기는 쉼
    comma_pause = len(
        re.findall(
            r"[,，·]",
            clean,
        )
    )

    sentence_pause = len(
        re.findall(
            r"[.!?。！？]",
            clean,
        )
    )

    weight = (
        hangul * 1.0
        + digits * 0.85
        + latin * 0.55
        + comma_pause * 1.2
        + sentence_pause * 1.8
    )

    return max(
        4.0,
        float(weight),
    )


def build_shortform_plan(
    subtitle_text,
    duration,
):

    raw_blocks = re.split(
        r"\n\s*\n",
        str(
            subtitle_text or ""
        ).strip(),
    )

    clean_blocks = []

    for raw in raw_blocks:

        lines = []

        for line in raw.splitlines():

            clean = (
                clean_body_subtitle_line(
                    line
                )
            )

            if clean:
                lines.append(
                    clean
                )

        if lines:

            clean_blocks.append(
                lines[:2]
            )

    duration = float(
        duration
    )

    # CTA 시작 전 본문을 완전히 종료
    body_end = max(
        1.0,
        duration
        - CTA_RESERVED_SECONDS
        - 0.0,
    )

    if not clean_blocks:

        return {
            "blocks": [],
            "events": [],
            "body_end": body_end,
            "cta_start": min(
                duration,
                body_end
                + 0.0,
            ),
        }

    combined_blocks = [
        " ".join(
            block
        )
        for block in clean_blocks
    ]

    weights = [
        subtitle_reading_weight(
            combined
        )
        for combined in combined_blocks
    ]

    total_weight = max(
        1.0,
        sum(
            weights
        ),
    )

    events = []

    cursor = 0.0

    for index, block in enumerate(
        clean_blocks
    ):

        combined = (
            combined_blocks[
                index
            ]
        )

        start = cursor

        if index == len(
            clean_blocks
        ) - 1:

            end = body_end

        else:

            share = (
                weights[
                    index
                ]
                / total_weight
            )

            end = min(
                body_end,
                start
                + body_end
                * share,
            )

        cursor = end

        semantic = (
            classify_shortform_line(
                combined
            )
        )

        events.append(
            {
                "index": index,
                "start": start,
                "end": end,
                "text": combined,
                "kind": semantic[
                    "kind"
                ],
                "emoji": semantic[
                    "emoji"
                ],
                "sfx": semantic[
                    "sfx"
                ],
            }
        )

    return {
        "blocks":
            clean_blocks,

        "events":
            events,

        "body_end":
            body_end,

        "cta_start":
            min(
                duration,
                body_end
                + 0.0,
            ),
    }

def build_subtitle_blocks(text):

    raw_blocks = re.split(
        r"\n\s*\n",
        str(
            text or ""
        ).strip(),
    )

    blocks = []

    for raw in raw_blocks:

        lines = []

        for line in raw.splitlines():

            clean = (
                clean_body_subtitle_line(
                    line
                )
            )

            if clean:
                lines.append(
                    clean
                )

        if lines:

            blocks.append(
                lines[:2]
            )

    return blocks



def align_subtitle_events_to_scenes(
    events,
    scene_plan,
    body_end,
):
    """
    기존 자막의 콘텐츠 가중치 타이밍은 최대한 유지하면서
    자막 전환 시점을 실제 장면 경계에 맞춘다.

    - scene 수와 subtitle 수가 달라도 자동 처리
    - 자막 전환이 장면 중간에 걸리는 현상 감소
    - 마지막 본문은 body_end 전에 종료
    """

    if (
        not events
        or not scene_plan
    ):
        return events

    body_end = max(
        0.1,
        float(body_end),
    )

    # body_end 안에 존재하는 실제 장면 경계만 사용
    boundaries = [0.0]

    for scene in scene_plan:

        end = min(
            body_end,
            float(
                scene.get(
                    "end",
                    0.0,
                )
            ),
        )

        if (
            end > boundaries[-1] + 0.01
            and end < body_end - 0.01
        ):
            boundaries.append(
                end
            )

    boundaries.append(
        body_end
    )

    # 자막이 하나뿐이면 전체 본문 구간 사용
    if len(events) == 1:

        result = [
            dict(
                events[0]
            )
        ]

        result[0]["start"] = 0.0
        result[0]["end"] = body_end

        return result

    result = []

    previous_boundary = 0.0

    for index, event in enumerate(
        events
    ):

        item = dict(
            event
        )

        if index == 0:

            start = 0.0

        else:

            start = previous_boundary

        if index == len(events) - 1:

            end = body_end

        else:

            # 기존 weighted timing에서 원하는 종료 지점
            target = float(
                event.get(
                    "end",
                    0.0,
                )
            )

            # 사용 가능한 장면 경계 중 가장 가까운 것 선택
            candidates = [
                value
                for value in boundaries
                if (
                    value > start + 0.05
                    and value < body_end - 0.05
                )
            ]

            if candidates:

                end = min(
                    candidates,
                    key=lambda value:
                        abs(
                            value - target
                        ),
                )

            else:

                end = min(
                    body_end,
                    target,
                )

            # 이전 자막보다 뒤로 가지 않도록 보호
            end = max(
                start + 0.10,
                end,
            )

            end = min(
                body_end,
                end,
            )

        item["start"] = start
        item["end"] = end

        result.append(
            item
        )

        previous_boundary = end

    return result


def write_ass(
    text,
    duration,
    path,
    scene_plan=None,
):

    fonts = (
        detect_fonts()
    )

    normal = fonts[
        "normal_name"
    ]

    highlight = fonts[
        "highlight_name"
    ]

    # -----------------------------------------------------
    # SHOPPING SHORTS SCENE SUBTITLE DIRECT MAP
    #
    # 장면별 모드에서는 전체 자막을 다시 분할하지 않는다.
    # 빈 줄 1개(문단 구분) = 다음 장면.
    #
    # scene 1 subtitle -> scene_plan[0]
    # scene 2 subtitle -> scene_plan[1]
    # ...
    # -----------------------------------------------------

    if scene_plan:

        scene_plan = list(
            scene_plan
            or []
        )

        # 장면별 UI에서 "\n\n"으로 합친 값을
        # 다시 정확히 장면 단위로 분리
        # 장면 슬롯을 절대 압축하지 않는다.
        #
        # 예:
        # scene1 = "A"
        # scene2 = ""
        # scene3 = "C"
        #
        # 반드시 ["A", "", "C"] 상태를 유지해야 한다.
        raw_scene_text = str(
            text
            or ""
        )

        scene_blocks = [
            str(block or "").strip()
            for block in re.split(
                r"\n\s*\n",
                raw_scene_text,
            )
        ]

        # 빈 전체 텍스트 보호
        if (
            len(scene_blocks) == 1
            and not scene_blocks[0]
        ):
            scene_blocks = []

        # 장면 수만큼 슬롯 보정
        if len(scene_blocks) < len(scene_plan):

            scene_blocks.extend(
                [""]
                * (
                    len(scene_plan)
                    - len(scene_blocks)
                )
            )

        elif len(scene_blocks) > len(scene_plan):

            # 초과 블록은 마지막 장면에 합쳐서
            # 자막 유실 방지
            extra = scene_blocks[
                len(scene_plan) - 1:
            ]

            scene_blocks = (
                scene_blocks[
                    :len(scene_plan) - 1
                ]
                + [
                    "\n".join(
                        extra
                    )
                ]
            )

        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,{normal},70,&H00FFFFFF,&H000000FF,&H00111111,&HFF000000,-1,0,0,0,100,100,0,0,1,4,0,2,60,60,430,1
Style: Highlight,{highlight},84,&H0000EFFF,&H000000FF,&H00111111,&HFF000000,-1,0,0,0,100,100,0,0,1,4,0,2,50,50,430,1
Style: Background,{normal},70,&H00FFFFFF,&H000000FF,&H00111111,&HFF000000,-1,0,0,0,100,100,0,0,1,4,0,2,40,40,430,1
Style: HighlightBackground,{highlight},82,&H0000EFFF,&H000000FF,&H00111111,&HFF000000,-1,0,0,0,100,100,0,0,1,4,0,2,40,40,430,1
Style: SubtitleBox,Arial,20,&HFFFFFFFF,&H000000FF,&HFF000000,&HFF000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""

        rows = []

        for index, scene in enumerate(
            scene_plan
        ):

            if index >= len(
                scene_blocks
            ):
                break

            block_text = str(
                scene_blocks[index]
                or ""
            ).strip()

            # -------------------------------------------------
            # CTA는 add_cta() 전용 레이어에서만 출력
            # 본문 ASS에 중복 출력하지 않는다.
            # -------------------------------------------------

            filtered_lines = []

            for _line in block_text.splitlines():

                _compact = re.sub(
                    r"\s+",
                    "",
                    str(
                        _line
                        or ""
                    ),
                )

                if (
                    "특가종료임박" in _compact
                    or "특가혜택확인" in _compact
                    or "지금혜택확인" in _compact
                    or "현재혜택확인" in _compact
                    or "하단상품태그" in _compact
                    or "상품태그클릭" in _compact
                ):
                    continue

                filtered_lines.append(
                    str(
                        _line
                        or ""
                    )
                )

            block_text = "\n".join(
                filtered_lines
            ).strip()

            # -------------------------------------------------
            # 자막 스타일 태그
            #
            # [강조]
            # [배경]
            # [강조][배경]
            # -------------------------------------------------

            dialogue_style = "Default"

            if (
                "[강조]" in block_text
                and "[배경]" in block_text
            ):

                dialogue_style = (
                    "HighlightBackground"
                )

            elif "[배경]" in block_text:

                dialogue_style = "Background"

            elif "[강조]" in block_text:

                dialogue_style = "Highlight"

            block_text = (
                block_text
                .replace(
                    "[배경]",
                    "",
                )
                .strip()
            )

            # 이 장면 자막이 비어 있으면
            # 이 장면에는 자막을 만들지 않는다.
            if not block_text:
                continue

            start = max(
                0.0,
                float(
                    scene.get(
                        "start",
                        0.0,
                    )
                    or 0.0
                ),
            )

            end = max(
                start + 0.05,
                float(
                    scene.get(
                        "end",
                        start + 0.05,
                    )
                    or (
                        start + 0.05
                    )
                ),
            )

            styled_lines = []

            for raw_line in block_text.splitlines():

                # -----------------------------------------
                # 컬러 이모지는 add_body_color_icons() 전담.
                # ASS 자막에 남아 있는 이모지를 제거해서
                # 아이콘이 2개 나오는 현상을 방지한다.
                # -----------------------------------------

                raw_line = re.sub(
                    (
                        r"[\u2600-\u27BF]"
                        r"|[\U0001F300-\U0001FAFF]"
                        r"|[\uFE0E\uFE0F]"
                        r"|\u200D"
                    ),
                    "",
                    str(
                        raw_line
                        or ""
                    ),
                )

                raw_line = re.sub(
                    r"\s+",
                    " ",
                    raw_line,
                ).strip()

                raw_line = str(
                    raw_line
                    or ""
                ).strip()

                if not raw_line:
                    continue

                cleaned = re.sub(
                    (
                        r"^[\s"
                        r"\u2605"
                        r"\u2606"
                        r"\u2B50"
                        r"\u2728"
                        r"\U0001F525"
                        r"\U0001F4A5"
                        r"\u2705"
                        r"\U0001F447"
                        r"\U0001F449"
                        r"\uFE0F"
                        r"]+"
                    ),
                    "",
                    raw_line,
                ).strip()

                if cleaned:

                    styled_lines.append(
                        style_subtitle_line(
                            cleaned
                        )
                    )

            if not styled_lines:
                continue

            line = r"\N".join(
                styled_lines
            )

            # -------------------------------------------------
            # FIXED SUBTITLE BACKGROUND
            #
            # 모든 장면에서 동일한 크기의 반투명 박스.
            # 자막 이벤트 시간 동안에만 표시된다.
            #
            # 1080 x 1920
            # x = 145
            # y = 1295
            # width = 790
            # height = 215
            # -------------------------------------------------

            line_count = max(
                1,
                len(styled_lines),
            )

            BOX_X = SUBTITLE_BOX_X
            BOX_W = SUBTITLE_BOX_WIDTH

            if line_count == 1:
                BOX_Y = SUBTITLE_BOX_1LINE_Y
                BOX_H = SUBTITLE_BOX_1LINE_HEIGHT
            else:
                BOX_Y = SUBTITLE_BOX_2LINE_Y
                BOX_H = SUBTITLE_BOX_2LINE_HEIGHT

            box_text = (
                r"{\an7"
                f"\\pos({BOX_X},{BOX_Y})"
                r"\p1"
                r"\1c&H000000&"
                r"\1a&H95&}"
                r"m 0 0 "
                f"l {BOX_W} 0 "
                f"l {BOX_W} {BOX_H} "
                f"l 0 {BOX_H}"
                r"{\p0}"
            )

            rows.append(
                "Dialogue: 0,"
                f"{ass_time(start)},"
                f"{ass_time(end)},"
                "SubtitleBox,,0,0,0,,"
                f"{box_text}"
            )

            # 실제 자막도 박스와 동일한 중심 좌표 사용
            subtitle_center_y = (
                BOX_Y
                + (
                    BOX_H
                    / 2
                )
            )

            positioned_line = (
                r"{\an5"
                f"\\pos(540,{subtitle_center_y:.0f})"
                r"}"
                + line
            )

            rows.append(
                "Dialogue: 1,"
                f"{ass_time(start)},"
                f"{ass_time(end)},"
                f"{dialogue_style},,0,0,0,,"
                f"{positioned_line}"
            )

        Path(
            path
        ).write_text(
            header
            + "\n".join(
                rows
            ),
            encoding="utf-8-sig",
        )

        return

    # -----------------------------------------------------
    # 기존 전체 자막 모드
    # -----------------------------------------------------

    plan = (
        build_shortform_plan(
            text,
            duration,
        )
    )

    blocks = plan[
        "blocks"
    ]

    body_end = plan[
        "body_end"
    ]

    if not blocks:
        return

    subtitle_events = (
        align_subtitle_events_to_scenes(
            plan["events"],
            scene_plan or [],
            body_end,
        )
    )

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,{normal},70,&H00FFFFFF,&H000000FF,&H00111111,&HFF000000,-1,0,0,0,100,100,0,0,1,4,0,2,60,60,430,1
Style: Highlight,{highlight},84,&H0000EFFF,&H000000FF,&H00111111,&HFF000000,-1,0,0,0,100,100,0,0,1,4,0,2,50,50,430,1
Style: Background,{normal},70,&H00FFFFFF,&H000000FF,&H00111111,&HFF000000,-1,0,0,0,100,100,0,0,1,4,0,2,40,40,430,1
Style: HighlightBackground,{highlight},82,&H0000EFFF,&H000000FF,&H00111111,&HFF000000,-1,0,0,0,100,100,0,0,1,4,0,2,40,40,430,1
Style: SubtitleBox,Arial,20,&HFFFFFFFF,&H000000FF,&HFF000000,&HFF000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""


    rows = []

    for index, block in enumerate(
        blocks
    ):

        event = subtitle_events[index]

        start = float(
            event["start"]
        )

        end = float(
            event["end"]
        )

        line = r"\N".join(
            style_subtitle_line(
                re.sub(
                    (
                        r"^[\s"
                        r"\u2605"
                        r"\u2606"
                        r"\u2B50"
                        r"\u2728"
                        r"\U0001F525"
                        r"\U0001F4A5"
                        r"\u2705"
                        r"\U0001F447"
                        r"\U0001F449"
                        r"\uFE0F"
                        r"]+"
                    ),
                    "",
                    x,
                ).strip()
            )
            for x
            in block
        )

        line_count = max(
            1,
            str(line).count(r"\N") + 1,
        )

        BOX_X = SUBTITLE_BOX_X
        BOX_W = SUBTITLE_BOX_WIDTH

        if line_count == 1:
            BOX_Y = SUBTITLE_BOX_1LINE_Y
            BOX_H = SUBTITLE_BOX_1LINE_HEIGHT
        else:
            BOX_Y = SUBTITLE_BOX_2LINE_Y
            BOX_H = SUBTITLE_BOX_2LINE_HEIGHT

        box_text = (
            r"{\an7"
            f"\\pos({BOX_X},{BOX_Y})"
            r"\p1"
            r"\1c&H000000&"
            r"\1a&H95&}"
            r"m 0 0 "
            f"l {BOX_W} 0 "
            f"l {BOX_W} {BOX_H} "
            f"l 0 {BOX_H}"
            r"{\p0}"
        )

        rows.append(
            "Dialogue: 0,"
            f"{ass_time(start)},"
            f"{ass_time(end)},"
            "SubtitleBox,,0,0,0,,"
            f"{box_text}"
        )

        subtitle_center_y = (
            BOX_Y
            + (
                BOX_H
                / 2
            )
        )

        positioned_line = (
            r"{\an5"
            f"\\pos(540,{subtitle_center_y:.0f})"
            r"}"
            + line
        )

        rows.append(
            "Dialogue: 1,"
            f"{ass_time(start)},"
            f"{ass_time(end)},"
            "Default,,0,0,0,,"
            f"{positioned_line}"
        )

    Path(
        path
    ).write_text(
        header
        + "\n".join(
            rows
        ),
        encoding="utf-8-sig",
    )
def burn_subtitles(
    video,
    ass_path,
    output,
):
    """
    Windows libass가 한글/특수문자 경로에서
    ASS 파일을 열지 못하는 문제를 피하기 위해
    ASCII 임시경로로 복사 후 자막을 렌더링한다.
    """

    source_ass = Path(
        ass_path
    )

    if not source_ass.is_file():

        raise RuntimeError(
            "ASS 자막 파일을 찾지 못했습니다: "
            + str(source_ass)
        )

    temp_root = (
        Path(
            tempfile.gettempdir()
        )
        / "naver_brand_ass"
    )

    temp_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_ass = (
        temp_root
        / (
            "subtitles_"
            + datetime.now().strftime(
                "%Y%m%d_%H%M%S_%f"
            )
            + ".ass"
        )
    )

    shutil.copy2(
        source_ass,
        temp_ass,
    )

    try:

        ass_filter = (
            temp_ass
            .resolve()
            .as_posix()
            .replace(
                ":",
                r"\:",
            )
        )

        run_command(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(
                    video
                ),
                "-vf",
                f"subtitles='{ass_filter}'",
                "-an",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "20",
                str(
                    output
                ),
            ]
        )

    finally:

        try:

            temp_ass.unlink(
                missing_ok=True
            )

        except Exception:

            pass


# =========================================================
# CTA
# =========================================================

def ffmpeg_font():

    fonts = (
        detect_fonts()
    )

    path = (
        fonts[
            "highlight_file"
        ]
        or fonts[
            "normal_file"
        ]
    )

    return (
        Path(
            path
        )
        .as_posix()
        .replace(
            ":",
            "\\:",
        )
    )


def escape_drawtext(text):

    return (
        str(
            text
        )
        .replace(
            "\\",
            "\\\\",
        )
        .replace(
            "'",
            "\\'",
        )
        .replace(
            ":",
            "\\:",
        )
        .replace(
            "%",
            "\\%",
        )
    )



def create_color_emoji_png(
    emoji_text,
    output_path,
    size=150,
):
    """
    Windows Segoe UI Emoji를 Pillow embedded_color로 렌더링.
    FFmpeg drawtext 대신 투명 PNG 오버레이에 사용.
    """

    from PIL import (
        Image,
        ImageDraw,
        ImageFont,
    )

    output_path = Path(
        output_path
    )

    emoji_font = Path(
        r"C:\Windows\Fonts\seguiemj.ttf"
    )

    if not emoji_font.is_file():
        raise RuntimeError(
            "Segoe UI Emoji 폰트를 찾지 못했습니다."
        )

    canvas = Image.new(
        "RGBA",
        (
            size * 2,
            size * 2,
        ),
        (
            0,
            0,
            0,
            0,
        ),
    )

    draw = ImageDraw.Draw(
        canvas
    )

    font = ImageFont.truetype(
        str(
            emoji_font
        ),
        size,
    )

    bbox = draw.textbbox(
        (
            0,
            0,
        ),
        emoji_text,
        font=font,
        embedded_color=True,
    )

    w = max(
        1,
        bbox[2] - bbox[0],
    )

    h = max(
        1,
        bbox[3] - bbox[1],
    )

    x = (
        canvas.width - w
    ) // 2 - bbox[0]

    y = (
        canvas.height - h
    ) // 2 - bbox[1]

    draw.text(
        (
            x,
            y,
        ),
        emoji_text,
        font=font,
        embedded_color=True,
    )

    # -----------------------------------------------------
    # EMOJI VISUAL BOUNDS CROP
    #
    # 중요:
    # size*2 투명 캔버스를 그대로 저장하면
    # FFmpeg에서 92x92로 축소할 때 실제 이모지는
    # 절반 정도 크기로 보이게 된다.
    #
    # 실제 알파 영역만 crop한 뒤 저장한다.
    # 최종 위치/크기는 add_body_color_icons()의
    # BODY_EMOJI_SIZE에서 통일한다.
    # -----------------------------------------------------

    alpha = canvas.getchannel(
        "A"
    )

    crop_box = alpha.getbbox()

    if crop_box:

        left, top, right, bottom = (
            crop_box
        )

        # 실제 그림이 가장자리에 너무 붙지 않도록
        # 약간의 투명 여백만 남긴다.
        visual_w = max(
            1,
            right - left,
        )

        visual_h = max(
            1,
            bottom - top,
        )

        margin = max(
            2,
            int(
                max(
                    visual_w,
                    visual_h,
                )
                * 0.04
            ),
        )

        left = max(
            0,
            left - margin,
        )

        top = max(
            0,
            top - margin,
        )

        right = min(
            canvas.width,
            right + margin,
        )

        bottom = min(
            canvas.height,
            bottom + margin,
        )

        canvas = canvas.crop(
            (
                left,
                top,
                right,
                bottom,
            )
        )

    canvas.save(
        output_path,
        "PNG",
    )

    return str(
        output_path
    )


def add_body_color_icons(
    video,
    subtitle_text,
    duration,
    output,
    scene_plan=None,
):
    """
    BODY COLOR ICON V5.24

    - 컬러 PNG 이모지 사용
    - 사용자가 직접 넣은 이모지 우선
    - 없으면 의미 기반 자동 이모지
    - [단어] 괄호는 위치 계산에서 제외
    - 자막 바로 왼쪽에 배치
    - 마지막 CTA 3초에는 본문 이모지 제거
    """

    from PIL import ImageFont

    scene_plan = list(
        scene_plan
        or []
    )

    if not scene_plan:

        shutil.copy2(
            video,
            output,
        )
        return

    raw_scene_text = str(
        subtitle_text
        or ""
    )

    scene_blocks = [
        str(block or "").strip()
        for block in re.split(
            r"\n\s*\n",
            raw_scene_text,
        )
    ]

    if len(scene_blocks) < len(scene_plan):

        scene_blocks.extend(
            [""]
            * (
                len(scene_plan)
                - len(scene_blocks)
            )
        )

    elif len(scene_blocks) > len(scene_plan):

        scene_blocks = scene_blocks[
            :len(scene_plan)
        ]

    fonts = detect_fonts()

    measure_font_path = (
        fonts.get("normal_file")
        or fonts.get("highlight_file")
    )

    try:

        measure_font = ImageFont.truetype(
            str(measure_font_path),
            70,
        )

    except Exception:

        measure_font = None

    work = (
        Path(output).parent
        / "body_icons"
    )

    work.mkdir(
        parents=True,
        exist_ok=True,
    )

    icon_paths = {}
    active_events = []

    # 외부 상수에 의존하지 않음
    cta_reserved = 3.0

    cta_cutoff = max(
        0.0,
        float(duration)
        - cta_reserved,
    )

    emoji_pattern = re.compile(
        (
            r"[\u2600-\u27BF]"
            r"|[\U0001F300-\U0001FAFF]"
        )
    )

    for index, scene in enumerate(
        scene_plan
    ):

        if index >= len(
            scene_blocks
        ):
            break

        raw_text = str(
            scene_blocks[index]
            or ""
        ).strip()

        if not raw_text:
            continue

        compact = re.sub(
            r"\s+",
            "",
            raw_text,
        )

        # CTA는 본문 아이콘에서 제외
        if (
            "특가종료임박" in compact
            or "특가혜택확인" in compact
            or "지금혜택확인" in compact
            or "현재혜택확인" in compact
            or "하단상품태그" in compact
            or "상품태그클릭" in compact
        ):
            continue

        start_time = max(
            0.0,
            float(
                scene.get(
                    "start",
                    0.0,
                )
                or 0.0
            ),
        )

        end_time = max(
            start_time + 0.05,
            float(
                scene.get(
                    "end",
                    start_time + 0.05,
                )
                or (
                    start_time + 0.05
                )
            ),
        )

        # 마지막 CTA 구간에는 본문 아이콘 금지
        if start_time >= cta_cutoff:
            continue

        end_time = min(
            end_time,
            cta_cutoff,
        )

        if end_time <= start_time:
            continue

        # -------------------------------------------------
        # 장면별 이모지 슬롯 우선
        #
        # 1순위: scene["emoji_left"]
        # 2순위: scene["emoji_right"]
        # 3순위: 자막 문자열 안의 직접 입력 이모지
        # 4순위: 의미 기반 자동 이모지
        # -------------------------------------------------

        scene_emoji_left = str(
            scene.get(
                "emoji_left",
                "",
            )
            or ""
        ).strip()

        scene_emoji_right = str(
            scene.get(
                "emoji_right",
                "",
            )
            or ""
        ).strip()

        explicit_emoji = ""

        emoji_match = emoji_pattern.search(
            raw_text
        )

        if emoji_match:

            explicit_emoji = str(
                emoji_match.group(0)
                or ""
            ).strip()

        clean_lines = []

        for raw_line in raw_text.splitlines():

            line = str(
                raw_line
                or ""
            )

            # 컬러 이모지는 ASS 글자 폭에서 제외
            line = emoji_pattern.sub(
                "",
                line,
            )

            # [무선] -> 무선
            line = re.sub(
                r"\[([^\[\]\r\n]+)\]",
                r"\1",
                line,
            )

            line = line.replace(
                "[강조]",
                "",
            )

            line = re.sub(
                r"\s+",
                " ",
                line,
            ).strip()

            if line:

                clean_lines.append(
                    line
                )

        if not clean_lines:
            continue

        clean_text = "\n".join(
            clean_lines
        )

        semantic = classify_shortform_line(
            clean_text
        )

        # -------------------------------------------------
        # DUAL EMOJI SLOT RENDER
        #
        # 역사쿠키 방식
        #
        # 왼쪽 입력값:
        #   첫 번째 자막 줄 왼쪽에 배치
        #
        # 오른쪽 입력값:
        #   마지막 자막 줄 오른쪽에 배치
        #
        # 두 칸 모두 입력:
        #   이모지 2개 동시 표시
        #
        # 두 칸 모두 비움:
        #   자막 직접 이모지 또는 자동 추천 이모지 1개를
        #   왼쪽에 표시
        # -------------------------------------------------

        auto_emoji = str(
            semantic.get(
                "emoji",
                "✨",
            )
            or "✨"
        ).strip()

        emoji_specs = []

        if scene_emoji_left:

            emoji_specs.append(
                {
                    "emoji":
                        scene_emoji_left,
                    "side":
                        "left",
                }
            )

        if scene_emoji_right:

            emoji_specs.append(
                {
                    "emoji":
                        scene_emoji_right,
                    "side":
                        "right",
                }
            )

        # 좌/우 전용칸을 모두 비운 경우만
        # FINAL: 사용자가 입력한 좌/우 이모지만 사용
        # 자동 semantic / explicit emoji fallback 금지
        if not emoji_specs:
            continue

        def _measure_body_line_width(
            target_line,
        ):

            target_line = str(
                target_line
                or ""
            ).strip()

            if measure_font:

                try:

                    bbox = measure_font.getbbox(
                        target_line
                    )

                    measured = max(
                        1,
                        bbox[2]
                        - bbox[0],
                    )

                except Exception:

                    measured = (
                        len(target_line)
                        * 36
                    )

            else:

                measured = (
                    len(target_line)
                    * 36
                )

            # 역사쿠키 Sprint196-23
            # ASS 외곽선 / 강조 안전 여백
            return int(
                min(
                    760,
                    max(
                        100,
                        (
                            measured
                            * 1.02
                        )
                        + 12,
                    ),
                )
            )

        # FINAL BODY EMOJI RENDER SIZE
        # FFmpeg scale / 위치 계산 모두 동일한 크기를 사용한다.
        # =================================================
        # FINAL BODY EMOJI LAYOUT SETUP
        #
        # 이 값들은 모든 emoji_spec 렌더 전에
        # 반드시 한 번 정의되어야 한다.
        # =================================================

        icon_size = BODY_EMOJI_SIZE

        line_count = max(
            1,
            min(
                2,
                len(clean_lines),
            ),
        )

        if line_count == 1:

            subtitle_box_y = (
                SUBTITLE_BOX_1LINE_Y
            )

            subtitle_box_h = (
                SUBTITLE_BOX_1LINE_HEIGHT
            )

        else:

            subtitle_box_y = (
                SUBTITLE_BOX_2LINE_Y
            )

            subtitle_box_h = (
                SUBTITLE_BOX_2LINE_HEIGHT
            )

        subtitle_center_y = (
            subtitle_box_y
            + (
                subtitle_box_h
                / 2
            )
        )

        # 자막 박스 좌우 내부 이모지 슬롯 여백
        EMOJI_SLOT_MARGIN = 8

        for emoji_spec in emoji_specs:

            emoji = str(
                emoji_spec.get(
                    "emoji",
                    "",
                )
                or ""
            ).strip()

            side = str(
                emoji_spec.get(
                    "side",
                    "left",
                )
                or "left"
            ).strip().lower()

            if not emoji:
                continue

            # ---------------------------------------------
            # 컬러 PNG 생성 / 캐시
            # ---------------------------------------------

            if emoji not in icon_paths:

                icon_target = (
                    work
                    / (
                        "icon_"
                        + str(
                            len(icon_paths)
                        )
                        + ".png"
                    )
                )

                try:

                    create_color_emoji_png(
                        emoji,
                        icon_target,
                        128,
                    )

                    icon_paths[
                        emoji
                    ] = str(
                        icon_target
                    )

                except Exception as emoji_exc:

                    print(
                        "[BODY EMOJI PNG ERROR]",
                        repr(emoji),
                        type(emoji_exc).__name__,
                        str(emoji_exc),
                        flush=True,
                    )

                    icon_paths[
                        emoji
                    ] = ""

            icon_path = icon_paths.get(
                emoji,
                "",
            )

            if not icon_path:
                continue

            # ---------------------------------------------
            # LEFT = 첫 번째 자막 줄
            # RIGHT = 마지막 자막 줄
            # ---------------------------------------------

            if side == "right":

                line_index = (
                    line_count
                    - 1
                )

                target_line = str(
                    clean_lines[
                        min(
                            len(clean_lines) - 1,
                            line_index,
                        )
                    ]
                    or ""
                ).strip()

            else:

                side = "left"

                line_index = 0

                target_line = str(
                    clean_lines[0]
                    or ""
                ).strip()

            line_width = (
                _measure_body_line_width(
                    target_line
                )
            )

# -------------------------------------------------
            # BODY EMOJI FIXED SIDE SLOTS
            #
            # Pillow 글자폭과 ASS 실제 렌더 폭의 차이 때문에
            # 문장마다 이모지가 좌우로 흔들리는 문제를 제거한다.
            #
            # 왼쪽  : 자막 박스 왼쪽 내부 슬롯
            # 오른쪽: 자막 박스 오른쪽 내부 슬롯
            #
            # 세로 위치는 기존처럼
            # 왼쪽=첫 줄 / 오른쪽=마지막 줄 중앙을 사용한다.
            # -------------------------------------------------

            EMOJI_SLOT_MARGIN = 8

            if side == "right":

                icon_x = int(
                    SUBTITLE_BOX_X
                    + SUBTITLE_BOX_WIDTH
                    - icon_size
                    - EMOJI_SLOT_MARGIN
                )

            else:

                icon_x = int(
                    SUBTITLE_BOX_X
                    + EMOJI_SLOT_MARGIN
                )

            # 화면 안전영역
            icon_x = max(
                24,
                min(
                    1080
                    - icon_size
                    - 24,
                    icon_x,
                ),
            )

            # ---------------------------------------------
            # 해당 자막 줄의 정확한 세로 중앙
            # ---------------------------------------------

            # FINAL BODY EMOJI Y ALIGNMENT
            if line_count == 1:
                line_center_y = subtitle_center_y
            else:
                BODY_TWO_LINE_OFFSET_Y = 44
            
                if side == "right":
                    line_center_y = (
                        subtitle_center_y
                        + BODY_TWO_LINE_OFFSET_Y
                    )
                else:
                    line_center_y = (
                        subtitle_center_y
                        - BODY_TWO_LINE_OFFSET_Y
                    )

            icon_y = int(
                line_center_y
                - (
                    icon_size
                    / 2
                )
            )

            icon_y = max(
                0,
                min(
                    1920
                    - icon_size,
                    icon_y,
                ),
            )

            active_events.append(
                {
                    "icon_path":
                        icon_path,

                    "icon_x":
                        icon_x,

                    "icon_y":
                        icon_y,

                    "side":
                        side,

                    "emoji":
                        emoji,

                    "start":
                        start_time,

                    "end":
                        end_time,
                }
            )

    if not active_events:

        shutil.copy2(
            video,
            output,
        )
        return

    print(
        "[BODY EMOJI EVENTS]",
        [
            {
                "emoji": event.get("emoji"),
                "side": event.get("side"),
                "icon_path": event.get("icon_path"),
                "icon_exists": Path(
                    str(event.get("icon_path") or "")
                ).is_file(),
                "x": event.get("icon_x"),
                "y": event.get("icon_y"),
                "start": round(float(event.get("start", 0)), 3),
                "end": round(float(event.get("end", 0)), 3),
            }
            for event in active_events
        ],
        flush=True,
    )

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video),
    ]

    for event in active_events:

        command += [
            "-loop",
            "1",
            "-i",
            event["icon_path"],
        ]

    filters = []
    current = "[0:v]"

    for input_index, event in enumerate(
        active_events,
        start=1,
    ):

        icon_label = (
            f"bodyicon{input_index}"
        )

        output_label = (
            f"bodyout{input_index}"
        )

        filters.append(
            (
                f"[{input_index}:v]"
                f"scale={BODY_EMOJI_SIZE}:{BODY_EMOJI_SIZE}:"
                "force_original_aspect_ratio=decrease,"
                f"pad={BODY_EMOJI_SIZE}:{BODY_EMOJI_SIZE}:"
                "(ow-iw)/2:(oh-ih)/2:"
                "color=0x00000000,"
                "format=rgba"
                f"[{icon_label}]"
            )
        )

        filters.append(
            (
                f"{current}"
                f"[{icon_label}]"
                "overlay="
                f"x={event['icon_x']}:"
                f"y={event['icon_y']}:"
                f"enable='between(t,"
                f"{event['start']:.3f},"
                f"{event['end']:.3f})'"
                f"[{output_label}]"
            )
        )

        current = (
            f"[{output_label}]"
        )

    filters.append(
        f"{current}null[v]"
    )

    command += [
        "-filter_complex",
        ";".join(filters),
        "-map",
        "[v]",
        "-an",
        "-t",
        f"{float(duration):.3f}",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        str(output),
    ]

    run_command(
        command
    )


def add_cta(
    video,
    output,
    promotion_text,
    duration,
):
    """
    CTA SINGLE COMPOSITE V5.26

    마지막 3초:
    🔥 특가 종료 임박!
    👇 하단 상품 태그 클릭

    두 줄 전체를 하나의 투명 PNG로 만든 뒤
    영상에 단 한 번 overlay한다.
    """

    from PIL import (
        Image,
        ImageDraw,
        ImageFont,
    )

    fonts = detect_fonts()

    font_original = (
        fonts.get("highlight_file")
        or fonts.get("normal_file")
        or ffmpeg_font()
    )

    urgency_text = (
        "특가 종료 임박!"
    )

    action_text = (
        "하단 상품 태그 클릭"
    )

    # -----------------------------------------------------
    # WORK
    # -----------------------------------------------------

    work = (
        Path(output).parent
        / "cta_icons"
    )

    work.mkdir(
        parents=True,
        exist_ok=True,
    )

    flame_png = (
        work
        / "flame.png"
    )

    finger_png = (
        work
        / "finger.png"
    )

    create_color_emoji_png(
        "🔥",
        flame_png,
        160,
    )

    create_color_emoji_png(
        "👇",
        finger_png,
        160,
    )

    # -----------------------------------------------------
    # FONT
    # -----------------------------------------------------

    try:

        font1 = ImageFont.truetype(
            str(font_original),
            88,
        )

    except Exception:

        font1 = ImageFont.load_default()

    try:

        font2 = ImageFont.truetype(
            str(font_original),
            74,
        )

    except Exception:

        font2 = ImageFont.load_default()

    # -----------------------------------------------------
    # COLOR EMOJI
    # -----------------------------------------------------

    flame = Image.open(
        flame_png
    ).convert(
        "RGBA"
    )

    finger = Image.open(
        finger_png
    ).convert(
        "RGBA"
    )

    try:

        resample = (
            Image.Resampling.LANCZOS
        )

    except AttributeError:

        resample = (
            Image.LANCZOS
        )

    flame.thumbnail(
        (128, 128),
        resample,
    )

    finger.thumbnail(
        (124, 124),
        resample,
    )

    # -----------------------------------------------------
    # CTA COMPOSITE
    #
    # 검정 배경 박스 없음.
    # 컬러 글자 + 검정 외곽선.
    # -----------------------------------------------------

    canvas_w = 1000
    canvas_h = 285

    canvas = Image.new(
        "RGBA",
        (
            canvas_w,
            canvas_h,
        ),
        (
            0,
            0,
            0,
            0,
        ),
    )

    draw = ImageDraw.Draw(
        canvas
    )

    box1 = draw.textbbox(
        (0, 0),
        urgency_text,
        font=font1,
        stroke_width=8,
    )

    width1 = max(
        1,
        box1[2] - box1[0],
    )

    box2 = draw.textbbox(
        (0, 0),
        action_text,
        font=font2,
        stroke_width=8,
    )

    width2 = max(
        1,
        box2[2] - box2[0],
    )

    gap = 18

    row1_width = (
        flame.width
        + gap
        + width1
    )

    row2_width = (
        finger.width
        + gap
        + width2
    )

    row1_x = max(
        10,
        int(
            (
                canvas_w
                - row1_width
            )
            / 2
        ),
    )

    row2_x = max(
        10,
        int(
            (
                canvas_w
                - row2_width
            )
            / 2
        ),
    )

    row1_y = 12
    row2_y = 142

    # -----------------------------------------------------
    # CTA ROW VERTICAL CENTER ALIGN
    #
    # 이모지를 고정 +16 / +2로 두지 않고
    # 실제 글자 높이 기준으로 각 줄 중앙에 맞춘다.
    # -----------------------------------------------------

    height1 = max(
        1,
        box1[3] - box1[1],
    )

    height2 = max(
        1,
        box2[3] - box2[1],
    )

    row1_visual_h = max(
        flame.height,
        height1,
    )

    row2_visual_h = max(
        finger.height,
        height2,
    )

    flame_y = int(
        row1_y
        + (
            row1_visual_h
            - flame.height
        )
        / 2
    )

    finger_y = int(
        row2_y
        + (
            row2_visual_h
            - finger.height
        )
        / 2
    )

    text1_y = int(
        row1_y
        + (
            row1_visual_h
            - height1
        )
        / 2
        - box1[1]
    )

    text2_y = int(
        row2_y
        + (
            row2_visual_h
            - height2
        )
        / 2
        - box2[1]
    )

    # -----------------------------------------------------
    # FIRST LINE
    # 🔥 특가 종료 임박!
    # -----------------------------------------------------

    canvas.alpha_composite(
        flame,
        (
            row1_x,
            flame_y,
        ),
    )

    draw.text(
        (
            row1_x
            + flame.width
            + gap,
            text1_y,
        ),
        urgency_text,
        font=font1,
        fill=(
            255,
            106,
            0,
            255,
        ),
        stroke_width=8,
        stroke_fill=(
            0,
            0,
            0,
            255,
        ),
    )

    # -----------------------------------------------------
    # SECOND LINE
    # 👇 하단 상품 태그 클릭
    # -----------------------------------------------------

    canvas.alpha_composite(
        finger,
        (
            row2_x,
            finger_y,
        ),
    )

    draw.text(
        (
            row2_x
            + finger.width
            + gap,
            text2_y,
        ),
        action_text,
        font=font2,
        fill=(
            245,
            255,
            0,
            255,
        ),
        stroke_width=8,
        stroke_fill=(
            0,
            0,
            0,
            255,
        ),
    )

    cta_png = (
        work
        / "cta_full.png"
    )

    canvas.save(
        cta_png
    )

    # -----------------------------------------------------
    # TIMING
    # -----------------------------------------------------

    reserved = 3.0

    # -----------------------------------------------------
    # 실제 BODY 영상 길이
    # -----------------------------------------------------

    try:

        actual_duration = float(
            media_duration(
                video
            )
        )

    except Exception:

        actual_duration = 0.0

    if actual_duration <= 0:

        actual_duration = max(
            0.1,
            float(duration)
            - reserved,
        )

    # -----------------------------------------------------
    # CTA는 BODY가 끝난 뒤 시작
    # -----------------------------------------------------

    # -----------------------------------------------------
    # CTA ADVANCE
    #
    # BODY가 완전히 끝난 뒤 CTA를 띄우지 않고
    # 마지막 BODY 장면과 0.8초 겹치게 시작한다.
    # -----------------------------------------------------


    cta_start = max(
        0.0,
        actual_duration
        - CTA_ADVANCE_SECONDS,
    )

    # CTA는 시작 후 reserved(3초) 동안 유지.
    final_duration = max(
        float(duration),
        cta_start
        + reserved,
    )

    extension_duration = max(
        0.0,
        final_duration
        - actual_duration,
    )

    # -----------------------------------------------------
    # FFMPEG
    #
    # CTA 두 줄을 하나의 PNG 입력으로만 사용.
    # -----------------------------------------------------

    filter_complex = (
        "[1:v]"
        "format=rgba,"
        "setpts=PTS-STARTPTS"
        "[cta];"

        "[0:v]"
        "setpts=PTS-STARTPTS,"
        f"tpad=stop_mode=clone:stop_duration={extension_duration:.3f}"
        "[base];"

        "[base][cta]"
        "overlay="
        "x=(W-w)/2:"
        "y=1215:"
        "eof_action=repeat:"
        "shortest=0:"
        f"enable='between(t,{cta_start:.3f},{final_duration:.3f})'"
        "[v]"
    )

    run_command(
        [
            "ffmpeg",
            "-y",

            "-i",
            str(video),

            "-loop",
            "1",
            "-framerate",
            "30",
            "-i",
            str(cta_png),

            "-filter_complex",
            filter_complex,

            "-map",
            "[v]",

            "-an",

            "-t",
            f"{final_duration:.3f}",

            "-c:v",
            "libx264",

            "-preset",
            "veryfast",

            "-crf",
            "20",

            "-pix_fmt",
            "yuv420p",

            str(output),
        ]
    )



# =========================================================
# AUDIO
# =========================================================


# =========================================================
# AUTO SHOPPING SFX V5.19
# =========================================================

def generate_shopping_sfx(folder):

    folder = Path(folder)

    sfx_dir = folder / "sfx"

    sfx_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    paths = {
        "review": sfx_dir / "review_pop.wav",
        "door": sfx_dir / "door_click.wav",
        "steel": sfx_dir / "steel_ting.wav",
        "sizzle": sfx_dir / "cook_sizzle.wav",
        "price": sfx_dir / "price_ding.wav",
        "cta1": sfx_dir / "cta_ting_1.wav",
        "cta2": sfx_dir / "cta_ting_2.wav",
    }

    # 리뷰 POP
    run_command(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=920:duration=0.10:sample_rate=44100",
            "-af",
            "volume=0.35,afade=t=out:st=0.03:d=0.07",
            str(paths["review"]),
        ]
    )

    # 오븐 문 찰칵
    run_command(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=2300:duration=0.055:sample_rate=44100",
            "-af",
            "volume=0.32,highpass=f=900,afade=t=out:st=0.018:d=0.037",
            str(paths["door"]),
        ]
    )

    # 올스테인리스 TING
    run_command(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=1800:duration=0.16:sample_rate=44100",
            "-af",
            "volume=0.24,afade=t=out:st=0.04:d=0.12",
            str(paths["steel"]),
        ]
    )

    # 조리 지글거림
    run_command(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anoisesrc=color=pink:duration=3.0:amplitude=0.09:sample_rate=44100",
            "-af",
            (
                "highpass=f=1400,"
                "lowpass=f=7500,"
                "tremolo=f=8:d=0.65,"
                "volume=0.18,"
                "afade=t=in:st=0:d=0.25,"
                "afade=t=out:st=2.45:d=0.55"
            ),
            str(paths["sizzle"]),
        ]
    )

    # 가격 DING
    run_command(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=1250:duration=0.20:sample_rate=44100",
            "-af",
            "volume=0.38,afade=t=out:st=0.05:d=0.15",
            str(paths["price"]),
        ]
    )

    # CTA 첫 번째 TING
    run_command(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=1450:duration=0.18:sample_rate=44100",
            "-af",
            "volume=0.32,afade=t=out:st=0.04:d=0.14",
            str(paths["cta1"]),
        ]
    )

    # CTA 두 번째 TING - 조금 높은 음
    run_command(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=1780:duration=0.20:sample_rate=44100",
            "-af",
            "volume=0.36,afade=t=out:st=0.05:d=0.15",
            str(paths["cta2"]),
        ]
    )

    return {
        key: str(value)
        for key, value
        in paths.items()
    }

def mix_audio(
    video,
    narration,
    output,
    duration,
    bgm="",
    bgm_volume=20,
    sfx_paths=None,
    review_time=0.8,
    door_time=3.2,
    steel_time=6.2,
    cook_time=9.0,
    price_time=0.0,
    cta_time=0.0,
    source_audio_plan=None,
    source_audio_volume=0.28,
):
    """
    V5.12

    narration = 100%
    BGM       = UI 설정값
    SFX       = 자동 타이밍

    후킹       0초
    리뷰       review_time
    가격       price_time
    CTA        cta_time
    """

    sfx_paths = (
        sfx_paths
        or {}
    )

    source_audio_plan = (
        source_audio_plan
        or []
    )

    # -----------------------------------------------------
    # FINAL AUDIO SAFE DURATION
    #
    # 최종 영상 길이가 나레이션보다 짧아
    # 마지막 음성이 잘리는 것을 방지한다.
    # -----------------------------------------------------

    try:

        narration_duration = float(
            media_duration(
                narration
            )
        )

    except Exception:

        narration_duration = 0.0

    safe_duration = max(
        float(
            duration
        ),
        narration_duration + 0.15,
    )

    inputs = [
        "-i",
        str(
            video
        ),
        "-i",
        str(
            narration
        ),
    ]

    filters = [
        "[1:a]volume=1.0[narr]"
    ]

    labels = [
        "[narr]"
    ]

    input_index = 2

    # -----------------------------------------------------
    # BGM
    # -----------------------------------------------------

    if (
        bgm
        and Path(
            bgm
        ).is_file()
    ):

        inputs += [
            "-stream_loop",
            "-1",
            "-i",
            str(
                bgm
            ),
        ]

        volume = (
            float(
                bgm_volume
            )
            / 100.0
        )

        filters.append(
            (
                f"[{input_index}:a]"
                f"volume={volume:.3f},"
                f"atrim=duration={safe_duration:.3f},"
                "asetpts=PTS-STARTPTS"
                "[bgm]"
            )
        )

        labels.append(
            "[bgm]"
        )

        input_index += 1

    # -----------------------------------------------------
    # ORIGINAL SOURCE AUDIO
    # -----------------------------------------------------

    for source_no, source_audio in enumerate(
        source_audio_plan,
        start=1,
    ):

        source_path = str(
            source_audio.get(
                "path",
                "",
            )
            or ""
        )

        if (
            not source_path
            or not Path(
                source_path
            ).is_file()
        ):
            continue

        source_start = max(
            0.0,
            float(
                source_audio.get(
                    "start",
                    0.0,
                )
                or 0.0
            ),
        )

        source_duration = max(
            0.0,
            float(
                source_audio.get(
                    "duration",
                    0.0,
                )
                or 0.0
            ),
        )

        source_duration = min(
            source_duration,
            max(
                0.0,
                float(safe_duration)
                - source_start,
            ),
        )

        if source_duration <= 0:
            continue

        inputs += [
            "-stream_loop",
            "-1",
            "-i",
            source_path,
        ]

        delay = max(
            0,
            int(
                source_start
                * 1000
            ),
        )

        label = (
            f"source_audio_{source_no}"
        )

        filters.append(
            (
                f"[{input_index}:a]"
                "aresample=44100,"
                f"atrim=duration={source_duration:.3f},"
                "asetpts=PTS-STARTPTS,"
                f"volume={float(source_audio_volume):.3f},"
                f"adelay={delay}|{delay}"
                f"[{label}]"
            )
        )

        labels.append(
            f"[{label}]"
        )

        input_index += 1


    def source_audio_active_at(
        start_seconds,
    ):

        if start_seconds is None:
            return False

        try:
            t = float(
                start_seconds
            )
        except Exception:
            return False

        for item in source_audio_plan:

            try:
                start = float(
                    item.get(
                        "start",
                        -1.0,
                    )
                )

                end = float(
                    item.get(
                        "end",
                        -1.0,
                    )
                )

            except Exception:
                continue

            if start <= t < end:
                return True

        return False


    # -----------------------------------------------------
    # SFX helper
    # -----------------------------------------------------

    def add_sfx(
        key,
        label,
        start_seconds,
        volume,
        skip_when_source_audio=False,
    ):
        nonlocal input_index

        # 해당 의미의 장면이 없는 제품이면 SFX 사용 안 함
        if (
            start_seconds is None
            or float(
                start_seconds
            ) < 0
        ):
            return

        if (
            skip_when_source_audio
            and source_audio_active_at(
                start_seconds
            )
        ):
            return

        path = (
            sfx_paths.get(
                key,
                ""
            )
        )

        if (
            not path
            or not Path(
                path
            ).is_file()
        ):
            return

        inputs.extend(
            [
                "-i",
                str(
                    path
                ),
            ]
        )

        delay = max(
            0,
            int(
                float(
                    start_seconds
                )
                * 1000
            ),
        )

        filters.append(
            (
                f"[{input_index}:a]"
                f"volume={volume:.3f},"
                f"adelay={delay}|{delay}"
                f"[{label}]"
            )
        )

        labels.append(
            f"[{label}]"
        )

        input_index += 1

    # 첫 후킹
    add_sfx(
        "hook",
        "hook_sfx",
        0.05,
        0.70,
    )

    # 리뷰 등장
    add_sfx(
        "review",
        "review_sfx",
        review_time,
        0.70,
    )

    # 가격 캡처
    # PRODUCT ACTION SFX
    add_sfx(
        "door",
        "interaction_sfx",
        door_time,
        0.55,
        skip_when_source_audio=True,
    )

    # PRODUCT FEATURE SFX
    add_sfx(
        "steel",
        "feature_sfx",
        steel_time,
        0.50,
        skip_when_source_audio=True,
    )

    # COOKING / OPERATION SFX
    add_sfx(
        "sizzle",
        "cooking_sfx",
        cook_time,
        0.25,
        skip_when_source_audio=True,
    )

    add_sfx(
        "price",
        "price_sfx",
        price_time,
        0.72,
    )

    # CTA
    add_sfx(
        "cta",
        "cta_sfx",
        cta_time,
        0.75,
    )

    # -----------------------------------------------------
    # FINAL MIX
    # -----------------------------------------------------

    if len(
        labels
    ) == 1:

        filters.append(
            "[narr]anull[mixed]"
        )

    else:

        filters.append(
            "".join(
                labels
            )
            + (
                f"amix="
                f"inputs={len(labels)}:"
                f"duration=longest:"
                f"dropout_transition=0,"
                f"alimiter=limit=0.95,"
                f"atrim=duration={safe_duration:.3f}"
                "[mixed]"
            )
        )

    run_command(
        [
            "ffmpeg",
            "-y",
            *inputs,
            "-filter_complex",
            ";".join(
                filters
            ),
            "-map",
            "0:v:0",
            "-map",
            "[mixed]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-t",
            f"{safe_duration:.3f}",
            str(
                output
            ),
        ]
    )


# =========================================================
# RENDER PROJECT
# =========================================================


def infer_semantic_sfx_times(
    subtitle_text,
    duration,
    scene_plan=None,
):

    plan = (
        build_shortform_plan(
            subtitle_text,
            duration,
        )
    )

    result = {
        "review": -1.0,
        "interaction": -1.0,
        "feature": -1.0,
        "cooking": -1.0,
        "promotion": -1.0,
    }

    events = (
        align_subtitle_events_to_scenes(
            plan["events"],
            scene_plan or [],
            plan["body_end"],
        )
    )

    for event in events:

        kind = event[
            "kind"
        ]

        if (
            kind in result
            and result[
                kind
            ] < 0
        ):

            result[
                kind
            ] = event[
                "start"
            ] + 0.08

    return result

def render_project(
    project_id,
    sources,
    narration_text,
    subtitle_text,
    promotion_text,
    review_path,
    price_path,
    bgm_path,
    bgm_volume,
    typecast,
    scene_inputs=None,
):

    folder = (
        WORK_DIR
        / project_id
    )

    folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    progress = (
        st.progress(
            0
        )
    )

    status = (
        st.empty()
    )

    # -----------------------------------------------------
    # TTS / SCENE MODE PREP
    # -----------------------------------------------------

    status.write(
        "🎙️ 음성 타임라인 준비 중..."
    )

    scene_inputs = list(
        scene_inputs or []
    )

    use_scene_tts = any(
        str(
            item.get(
                "narration",
                "",
            )
            or ""
        ).strip()
        for item in scene_inputs
    )

    # 장면별 모드에서는 전체 나레이션 길이로
    # scene_plan을 만들지 않는다.
    #
    # 영상 실제 길이 + 이미지 기본시간을 기준으로
    # 장면 타임라인을 먼저 만든다.
    if use_scene_tts:

        video_total_for_plan = 0.0
        image_count_for_plan = 0

        for source in sources or []:

            if (
                str(
                    source.get(
                        "type",
                        "",
                    )
                ).lower()
                == "video"
            ):

                try:

                    video_total_for_plan += max(
                        0.0,
                        float(
                            media_duration(
                                source.get(
                                    "path",
                                    "",
                                )
                            )
                        ),
                    )

                except Exception:

                    pass

            else:

                image_count_for_plan += 1

        duration = max(
            1.0,
            video_total_for_plan
            + (
                image_count_for_plan
                * 1.55
            ),
        )

        narration_path = ""

    else:

        narration_path = (
            folder
            / "narration.wav"
        )

        generate_typecast_tts(
            narration_text,
            typecast[
                "api_key"
            ],
            typecast[
                "voice_id"
            ],
            narration_path,
            typecast[
                "speed"
            ],
        )

        duration = (
            media_duration(
                narration_path
            )
        )

        if duration <= 0:

            raise RuntimeError(
                "음성 길이를 확인하지 못했습니다."
            )

    progress.progress(
        15
    )

    # -----------------------------------------------------
    # 제품 영상
    # -----------------------------------------------------

    status.write(
        "🎬 제품 영상 제작 중..."
    )

    scene_plan = (
        build_scene_plan(
            sources,
            duration
            + 0.3,
        )
    )

    # -----------------------------------------------------
    # SCENE INPUT -> SCENE PLAN MERGE
    #
    # UI에서 입력한 장면별 자막/이모지를
    # 실제 렌더 타임라인에 같은 인덱스로 연결한다.
    # -----------------------------------------------------

    for scene_index, scene in enumerate(
        scene_plan
    ):

        if scene_index >= len(
            scene_inputs
        ):
            break

        source_input = (
            scene_inputs[
                scene_index
            ]
            or {}
        )

        scene["subtitle"] = str(
            source_input.get(
                "subtitle",
                "",
            )
            or ""
        ).strip()

        scene["narration"] = str(
            source_input.get(
                "narration",
                "",
            )
            or ""
        ).strip()

        scene["emoji_left"] = str(
            source_input.get(
                "emoji_left",
                "",
            )
            or ""
        ).strip()

        scene["emoji_right"] = str(
            source_input.get(
                "emoji_right",
                "",
            )
            or ""
        ).strip()

    # -----------------------------------------------------
    # 실제 장면 길이를 기준으로 최종 영상 길이 자동 결정
    #
    # 모든 제품 장면을 먼저 보여준 뒤
    # CTA 전용 시간을 별도로 확보한다.
    # -----------------------------------------------------

    # -----------------------------------------------------
    # HISTORY COOKIE STYLE SCENE TIMELINE
    # -----------------------------------------------------

    if use_scene_tts:

        scene_timeline = (
            build_scene_narration_master(
                scene_plan,
                scene_inputs,
                folder,
                0.0,
                typecast,
            )
        )

        scene_plan = list(
            scene_timeline.get(
                "scene_plan",
                [],
            )
            or []
        )

        narration_path = str(
            scene_timeline.get(
                "narration_path",
                "",
            )
            or ""
        )

        duration = float(
            scene_timeline.get(
                "content_duration",
                0.0,
            )
            or 0.0
        )

        if (
            not narration_path
            or not Path(
                narration_path
            ).is_file()
        ):

            raise RuntimeError(
                "장면별 최종 나레이션 트랙이 없습니다."
            )

    scene_content_end = (
        float(
            scene_plan[-1]["end"]
        )
        if scene_plan
        else float(duration)
    )

    render_duration = max(
        float(duration),
        scene_content_end
        + 0.0
        + CTA_RESERVED_SECONDS,
    )

    # 장면별 나레이션은 제품 장면까지만 존재하므로
    # CTA 구간만큼 뒤에 무음을 추가한다.
    if use_scene_tts:

        narration_full_path = (
            folder
            / "scene_narration_master.wav"
        )

        run_command(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(
                    narration_path
                ),
                "-af",
                (
                    "apad,"
                    f"atrim=duration={render_duration:.3f}"
                ),
                "-ar",
                "44100",
                "-ac",
                "2",
                "-c:a",
                "pcm_s16le",
                str(
                    narration_full_path
                ),
            ]
        )

        narration_path = str(
            narration_full_path
        )


    content = (
        make_content_video(
            sources,
            duration
            + 0.3,
            folder,
            scene_plan=scene_plan,
        )
    )

    extended_content = (
        folder
        / "content_extended.mp4"
    )

    extend_video_to_duration(
        content,
        extended_content,
        render_duration,
    )

    content = str(
        extended_content
    )

    progress.progress(
        40
    )

    # -----------------------------------------------------
    # 리뷰 증거컷
    # -----------------------------------------------------

    status.write(
        "⭐ 리뷰 증거컷 넣는 중..."
    )

    review_video = (
        folder
        / "review.mp4"
    )

    add_card(
        content,
        review_path,
        review_video,
        1.05,
        0.95,
        320,
        700,
        x=65,
    )

    progress.progress(
        55
    )

    # -----------------------------------------------------
    # 자막
    # -----------------------------------------------------

    # -----------------------------------------------------
    # 장면별 쇼핑쇼츠 모드 자막 준비
    # -----------------------------------------------------

    if use_scene_tts:

        scene_subtitle_blocks = []

        # scene_plan 순서대로 subtitle slot을 만든다.
        # 각 scene의 원본 source_index를 기준으로
        # 해당 scene_input을 찾아서 1:1 연결한다.

        for plan_index, scene in enumerate(
            scene_plan
        ):

            source_index = int(
                scene.get(
                    "index",
                    plan_index,
                )
                or 0
            )

            item = {}

            for candidate in scene_inputs:

                candidate = (
                    candidate
                    or {}
                )

                try:
                    candidate_index = int(
                        candidate.get(
                            "source_index",
                            -1,
                        )
                    )
                except Exception:
                    candidate_index = -1

                if candidate_index == source_index:

                    item = candidate
                    break

            # 구형 프로젝트 호환 fallback
            if (
                not item
                and plan_index < len(
                    scene_inputs
                )
            ):

                item = (
                    scene_inputs[
                        plan_index
                    ]
                    or {}
                )

            scene_subtitle = str(
                item.get(
                    "subtitle",
                    "",
                )
                or ""
            ).strip()

            # 자막이 비어 있으면
            # 동일 source_index의 나레이션을 사용
            if not scene_subtitle:

                scene_subtitle = str(
                    item.get(
                        "narration",
                        "",
                    )
                    or ""
                ).strip()

            # 빈 슬롯도 반드시 유지
            scene_subtitle_blocks.append(
                scene_subtitle
            )

        # 장면별 TTS 모드에서는 기존 subtitle_text보다
        # scene_inputs의 장면별 자막을 무조건 우선한다.
        subtitle_text = "\n\n".join(
            scene_subtitle_blocks
        )

    elif not subtitle_text.strip():

        subtitle_text = (
            narration_text
            .replace(
                ". ",
                ".\n\n",
            )
        )

    ass = (
        folder
        / "subtitles.ass"
    )

    subtitle_video = (
        folder
        / "subtitle.mp4"
    )

    status.write(
        "💬 강조자막 넣는 중..."
    )

    if subtitle_text.strip():

        write_ass(
            subtitle_text,
            duration,
            ass,
            scene_plan=(
                scene_plan
                if use_scene_tts
                else None
            ),
        )

        if ass.is_file():

            burn_subtitles(
                review_video,
                ass,
                subtitle_video,
            )

        else:

            shutil.copy2(
                review_video,
                subtitle_video,
            )

    else:

        # 자막이 하나도 없으면
        # 자막 단계 자체를 건너뛴다.
        shutil.copy2(
            review_video,
            subtitle_video,
        )

    # -----------------------------------------------------
    # 본문 컬러 아이콘 렌더
    # -----------------------------------------------------

    body_icon_video = (
        folder
        / "body_icons.mp4"
    )

    status.write(
        "🎨 본문 컬러 아이콘 넣는 중..."
    )

    add_body_color_icons(
        subtitle_video,
        subtitle_text,
        duration,
        body_icon_video,
        scene_plan=(
            scene_plan
            if use_scene_tts
            else None
        ),
    )


    progress.progress(
        70
    )

    # -----------------------------------------------------
    # 가격 증거컷
    # -----------------------------------------------------

    price_video = (
        folder
        / "price.mp4"
    )

    # 가격 증거컷은 CTA 시작 전에 종료
    cta_visual_start = max(
        0.0,
        render_duration
        - CTA_RESERVED_SECONDS,
    )

    price_start = max(
        1.8,
        cta_visual_start
        - 1.6,
    )

    status.write(
        "💰 가격·쿠폰 증거컷 넣는 중..."
    )

    add_card(
        body_icon_video,
        price_path,
        price_video,
        price_start,
        1.5,
        620,
        420,
    )

    progress.progress(
        82
    )

    # -----------------------------------------------------
    # CTA
    # -----------------------------------------------------

    cta_video = (
        folder
        / "cta.mp4"
    )

    status.write(
        "🔥 최대혜택가 CTA 넣는 중..."
    )

    add_cta(
        price_video,
        cta_video,
        promotion_text,
        render_duration,
    )

    progress.progress(
        90
    )

    # -----------------------------------------------------
    # 전체 영상 [광고] 고정 표시
    # -----------------------------------------------------

    ad_video = (
        folder
        / "ad_badge.mp4"
    )

    add_ad_badge(
        cta_video,
        ad_video,
    )

    # -----------------------------------------------------
    # AUDIO
    # -----------------------------------------------------

    output = (
        EXPORT_DIR
        / (
            safe_name(
                project_id
            )
            + ".mp4"
        )
    )

    status.write(
        "🎵 BGM 믹싱 중..."
    )

    # -----------------------------------------------------
    # V5.19 자동 효과음 생성
    # -----------------------------------------------------

    sfx_paths = (
        generate_shopping_sfx(
            folder
        )
    )

    # 현재 15~17초 쇼핑숏폼 기준 자동 타이밍
    # 영상 길이가 달라져도 비율로 보정
    semantic_times = (
        infer_semantic_sfx_times(
            subtitle_text,
            duration,
            scene_plan=None,
        )
    )

    # 더 이상 특정 제품의
    # door / steel / cook 초를 고정하지 않음.
    door_time = semantic_times[
        "interaction"
    ]

    steel_time = semantic_times[
        "feature"
    ]

    cook_time = semantic_times[
        "cooking"
    ]

    plan = (
        build_shortform_plan(
            subtitle_text,
            render_duration,
        )
    )

    cta_start = plan[
        "cta_start"
    ]

    # ?? ??? ?? ??? ?? ????
    # ? ??? ??? ?? ??? ???.
    source_audio_plan = (
        build_source_audio_plan(
            sources,
            duration + 0.3,
            scene_plan=scene_plan,
        )
    )

    mix_audio(
        ad_video,
        narration_path,
        output,
        render_duration,
        bgm_path,
        bgm_volume,
        sfx_paths=sfx_paths,
        review_time=0.8,
        door_time=door_time,
        steel_time=steel_time,
        cook_time=cook_time,
        price_time=price_start,
        cta_time=cta_start,
        source_audio_plan=source_audio_plan,
    )

    progress.progress(
        100
    )

    status.write(
        "✅ 영상 제작 완료"
    )

    return str(
        output
    )


# =========================================================
# UI
# =========================================================

def main():


    # -----------------------------------------------------
    # SAVED PROJECT RESTORE
    #
    # 반드시 어떤 Streamlit 위젯보다 먼저 실행해야 한다.
    # -----------------------------------------------------

    pending_saved_project = (
        st.session_state.pop(
            "nb510_pending_saved_project_state",
            None,
        )
    )

    if (
        isinstance(
            pending_saved_project,
            dict,
        )
        and pending_saved_project
    ):

        apply_naver_brand_project_state(
            pending_saved_project
        )

        print(
            "[NAVER SAVED PROJECT RESTORE] "
            "APPLIED BEFORE WIDGETS",
            {
                "project_id":
                    str(
                        pending_saved_project.get(
                            "project_id",
                            "",
                        )
                        or ""
                    ),

                "scene_count":
                    len(
                        list(
                            pending_saved_project.get(
                                "scene_inputs",
                                [],
                            )
                            or []
                        )
                    ),
            },
            flush=True,
        )


    st.set_page_config(
        page_title=(
            "네이버 브랜드커넥트 원클릭"
        ),
        page_icon="🔥",
        layout="wide",
    )

    st.title(
        "🔥 네이버 브랜드커넥트 원클릭"
    )

    st.success(
        "V5.19 · 강조자막 + 생활 SFX + BGM Ducking + 2단 CTA"
    )

    st.caption(
        "역사쿠키 / 기존 쇼핑쇼츠는 수정하지 않습니다."
    )

    # -----------------------------------------------------
    # OCR STATUS
    # -----------------------------------------------------

    tesseract_status = (
        setup_tesseract()
    )

    if tesseract_status[
        "ok"
    ]:

        if tesseract_status[
            "kor"
        ]:

            st.success(
                "🔎 OCR 준비 완료 · Tesseract + 한국어(kor)"
            )

        else:

            st.warning(
                "⚠️ Tesseract는 연결됐지만 한국어(kor) 데이터가 없습니다."
            )

        with st.expander(
            "🔎 OCR 엔진 정보",
            expanded=False,
        ):

            st.write(
                "Tesseract 경로:",
                tesseract_status[
                    "path"
                ],
            )

            st.write(
                "설치 언어:",
                ", ".join(
                    tesseract_status[
                        "languages"
                    ]
                ),
            )

    else:

        st.error(
            "❌ OCR 엔진 연결 실패"
        )

        st.caption(
            tesseract_status[
                "error"
            ]
        )

    # -----------------------------------------------------
    # FONT
    # -----------------------------------------------------

    fonts = (
        detect_fonts()
    )

    with st.expander(
        "🔤 자막 글씨체",
        expanded=False,
    ):

        st.write(
            "일반 자막:",
            fonts[
                "normal_name"
            ],
        )

        st.write(
            "강조 자막:",
            fonts[
                "highlight_name"
            ],
        )

    # -----------------------------------------------------
    # PRODUCT
    # -----------------------------------------------------

    st.markdown(
        "### 🛍️ 제품"
    )

    product_name = (
        st.text_input(
            "제품명",
            placeholder=(
                "올스텐 오븐에어프라이어 대용량 22L 스텐"
            ),
            key="nb510_product",
        )
    )

    # -----------------------------------------------------
    # PRICE CAPTURE
    # -----------------------------------------------------

    st.markdown(
        "### 💰 네이버 가격 · 쿠폰 캡처"
    )

    price_capture = (
        st.file_uploader(
            "정상가 / 할인율 / 최대혜택가 / D-day가 보이는 캡처",
            type=[
                "png",
                "jpg",
                "jpeg",
                "webp",
            ],
            key="nb510_price",
        )
    )

    st.caption(
        "예: 398,000원 / 25% 298,000원 / "
        "268,000원 최대할인가 / D-4 쿠폰 받기"
    )

    ocr_text = ""

    if price_capture:

        suffix = (
            Path(
                price_capture.name
            )
            .suffix
            .lower()
        )

        preview = (
            OCR_DIR
            / (
                "price_preview"
                + suffix
            )
        )

        price_capture.seek(
            0
        )

        preview.write_bytes(
            price_capture.getbuffer()
        )

        if not tesseract_status[
            "ok"
        ]:

            st.error(
                "가격 캡처는 업로드됐지만 OCR 엔진이 연결되지 않았습니다."
            )

        else:

            with st.spinner(
                "🔎 가격 캡처 분석 중..."
            ):

                ocr_result = (
                    ocr_price_capture(
                        preview
                    )
                )

            if ocr_result[
                "ok"
            ]:

                ocr_text = (
                    ocr_result[
                        "text"
                    ]
                )

                st.success(
                    "✅ 가격 캡처 OCR 자동 인식 완료"
                )

                if (
                    ocr_result.get(
                        "lang"
                    )
                ):

                    st.caption(
                        "OCR 모드: "
                        f"{ocr_result.get('lang')} "
                        f"{ocr_result.get('config', '')}"
                    )

            else:

                st.warning(
                    "⚠️ OCR 자동 인식이 되지 않았습니다."
                )

                st.error(
                    "원인: "
                    + str(
                        ocr_result.get(
                            "error",
                            "알 수 없는 OCR 오류",
                        )
                    )
                )

                st.caption(
                    "영상 제작은 중단되지 않습니다. "
                    "아래 가격 정보 보정칸에 직접 입력할 수 있습니다."
                )

    # -----------------------------------------------------
    # OCR / MANUAL CORRECTION
    # -----------------------------------------------------

    promotion_text = (
        st.text_area(
            "OCR 결과 / 가격 정보 보정",
            value=(
                ocr_text
            ),
            placeholder=(
                "398,000원\n"
                "25% 298,000원\n"
                "268,000원 최대할인가\n"
                "D-4 쿠폰 받기"
            ),
            height=180,
            key="nb510_promotion",
        )
    )

    # -----------------------------------------------------
    # PROMOTION ANALYSIS
    # -----------------------------------------------------

    if promotion_text.strip():

        promo = (
            parse_promotion_info(
                promotion_text
            )
        )

        st.markdown(
            "#### 🔎 자동 분석 결과"
        )

        col1, col2 = (
            st.columns(
                2
            )
        )

        with col1:

            st.metric(
                "정상가",
                format_price(
                    promo[
                        "normal_price"
                    ]
                ),
            )

            st.metric(
                "기본 할인가",
                format_price(
                    promo[
                        "sale_price"
                    ]
                ),
            )

            st.metric(
                "할인율",
                (
                    f"{promo['discount_percent']}%"
                    if promo[
                        "discount_percent"
                    ]
                    is not None
                    else "-"
                ),
            )

        with col2:

            st.metric(
                "최대 혜택가",
                format_price(
                    promo[
                        "max_price"
                    ]
                ),
            )

            st.metric(
                "남은 기간",
                (
                    f"D-{promo['days_left']}"
                    if promo[
                        "days_left"
                    ]
                    is not None
                    else "-"
                ),
            )

            st.metric(
                "쿠폰",
                (
                    "있음"
                    if promo[
                        "coupon_present"
                    ]
                    else "-"
                ),
            )

        cta = (
            build_cta_text(
                promotion_text
            )
        )

        st.markdown(
            "#### 🔥 마지막 CTA 미리보기"
        )

        st.success(
            f"{cta['main']}\n\n"
            f"{cta['sub']}"
        )

    # -----------------------------------------------------
    # PENDING SAVED PROJECT RESTORE
    # -----------------------------------------------------

    pending_saved_project = (
        st.session_state.pop(
            "nb510_pending_saved_project_state",
            None,
        )
    )

    if (
        isinstance(
            pending_saved_project,
            dict,
        )
        and pending_saved_project
    ):

        apply_naver_brand_project_state(
            pending_saved_project
        )


    # -----------------------------------------------------
    # SAVED PROJECT LOADER
    # -----------------------------------------------------

    st.markdown(
        "### 📂 제작한 영상 불러오기"
    )

    saved_projects = (
        list_saved_naver_brand_projects()
    )

    if saved_projects:

        saved_project_labels = [
            item[
                "project_id"
            ]
            for item in saved_projects
        ]

        selected_saved_project_id = (
            st.selectbox(
                "기존 제작 프로젝트 선택",
                saved_project_labels,
                key=(
                    "nb510_saved_project_select"
                ),
            )
        )

        selected_saved_project = next(
            (
                item
                for item
                in saved_projects
                if item[
                    "project_id"
                ]
                == selected_saved_project_id
            ),
            None,
        )

        if selected_saved_project:

            st.video(
                selected_saved_project[
                    "video"
                ]
            )

            st.caption(
                selected_saved_project[
                    "video"
                ]
            )

            if st.button(
                "✏️ 이 프로젝트 불러와서 수정",
                key=(
                    "nb510_load_saved_project"
                ),
            ):

                loaded_state = (
                    load_naver_brand_project_state(
                        selected_saved_project[
                            "folder"
                        ]
                    )
                )

                if not loaded_state:

                    loaded_state = (
                        recover_legacy_naver_brand_project_state(
                            selected_saved_project[
                                "folder"
                            ]
                        )
                    )

                if loaded_state:

                    st.session_state[
                        "nb510_pending_saved_project_state"
                    ] = loaded_state

                    st.session_state[
                        "nb510_loaded_project_folder"
                    ] = (
                        selected_saved_project[
                            "folder"
                        ]
                    )

                    st.session_state[
                        "nb510_loaded_project_video"
                    ] = (
                        selected_saved_project[
                            "video"
                        ]
                    )

                    st.session_state[
                        "nb510_using_saved_sources"
                    ] = bool(
                        loaded_state.get(
                            "sources"
                        )
                    )

                    st.rerun()

                else:

                    st.warning(
                        "이 프로젝트에서 복구 가능한 원본 영상·이미지를 찾지 못했습니다."
                    )

    else:

        st.info(
            "아직 저장된 제작 영상이 없습니다."
        )


    # -----------------------------------------------------
    # MEDIA
    # -----------------------------------------------------

    st.markdown(
        "### 🎬 제품 영상 · 이미지"
    )

    media_files = (
        st.file_uploader(
            "제품 소스",
            type=[
                "png",
                "jpg",
                "jpeg",
                "webp",
                "mp4",
                "mov",
                "m4v",
                "webm",
                "mkv",
            ],
            accept_multiple_files=True,
            key="nb510_media",
        )
    )


    # -----------------------------------------------------
    # SHOPPING SHORTS SCENE EDITOR
    # -----------------------------------------------------

    scene_inputs = []

    loaded_saved_sources = list(
        st.session_state.get(
            "nb510_loaded_saved_sources",
            [],
        )
        or []
    )

    active_media_files = (
        list(media_files or [])
        or loaded_saved_sources
    )

    if active_media_files:

        st.markdown(
            "### 🎞️ 쇼핑쇼츠 장면별 설정"
        )

        st.caption(
            "각 영상·이미지마다 나레이션과 자막을 "
            "따로 입력할 수 있습니다."
        )

        ai_scene_results = (
            st.session_state.get(
                "nb510_ai_narration_results",
                [],
            )
            or []
        )

        ai_by_source = {}

        for ai_item in ai_scene_results:

            try:
                ai_source_index = int(
                    ai_item.get(
                        "source_index",
                        -1,
                    )
                )
            except Exception:
                ai_source_index = -1

            if ai_source_index >= 0:
                ai_by_source[
                    ai_source_index
                ] = ai_item

        for scene_index, uploaded in enumerate(
            active_media_files
        ):

            if isinstance(
                uploaded,
                dict,
            ):

                saved_path = str(
                    uploaded.get(
                        "path",
                        "",
                    )
                    or ""
                )

                filename = str(
                    uploaded.get(
                        "original_name",
                        "",
                    )
                    or Path(
                        saved_path
                    ).name
                    or ""
                )

                saved_type = str(
                    uploaded.get(
                        "type",
                        "",
                    )
                    or ""
                ).lower()

            else:

                saved_path = ""

                filename = str(
                    getattr(
                        uploaded,
                        "name",
                        "",
                    )
                    or ""
                )

                saved_type = ""

            suffix = (
                Path(filename)
                .suffix
                .lower()
            )

            if saved_type in {
                "video",
                "image",
            }:

                source_type = saved_type
                source_label = (
                    "영상"
                    if source_type == "video"
                    else "이미지"
                )

            elif suffix in {
                ".mp4",
                ".mov",
                ".m4v",
                ".webm",
                ".mkv",
            }:

                source_type = "video"
                source_label = "영상"

            else:

                source_type = "image"
                source_label = "이미지"

            ai_item = (
                ai_by_source.get(
                    scene_index,
                    {}
                )
                or {}
            )

            ai_narration = str(
                ai_item.get(
                    "narration",
                    "",
                )
                or ""
            ).strip()

            narration_key = (
                "nb510_scene_narration_"
                f"{scene_index}"
            )

            subtitle_key = (
                "nb510_scene_subtitle_"
                f"{scene_index}"
            )

            # AI 결과가 있고 아직 사용자가
            # 장면 대본을 직접 수정하지 않았다면
            # 초기값으로만 가져온다.
            if (
                narration_key
                not in st.session_state
                and ai_narration
            ):
                st.session_state[
                    narration_key
                ] = ai_narration

            with st.expander(
                f"장면 {scene_index + 1} · "
                f"{source_label} · {filename}",
                expanded=True,
            ):

                scene_narration = (
                    st.text_area(
                        "🎙️ 이 장면 나레이션",
                        key=narration_key,
                        height=80,
                        placeholder=(
                            "이 장면에서 읽을 "
                            "나레이션을 입력하세요."
                        ),
                    )
                )

                scene_subtitle = (
                    st.text_area(
                        "💬 이 장면 자막",
                        key=subtitle_key,
                        height=70,
                        placeholder=(
                            "이 장면에 표시할 "
                            "짧은 자막을 입력하세요."
                        ),
                    )
                )

                # ---------------------------------------------
                # 장면별 이모지 전용 입력칸
                # 자막 문자열과 이모지를 분리해서 관리
                # ---------------------------------------------

                emoji_left_key = (
                    f"scene_emoji_left_{scene_index}"
                )

                emoji_right_key = (
                    f"scene_emoji_right_{scene_index}"
                )

                emoji_col_left, emoji_col_right = (
                    st.columns(2)
                )

                with emoji_col_left:

                    scene_emoji_left = st.text_input(
                        "왼쪽 이모지",
                        key=emoji_left_key,
                        placeholder="예: 🔥",
                    )

                with emoji_col_right:

                    scene_emoji_right = st.text_input(
                        "오른쪽 이모지",
                        key=emoji_right_key,
                        placeholder="예: 👇",
                    )

            scene_inputs.append(
                {
                    "source_index":
                        scene_index,

                    "source_type":
                        source_type,

                    "filename":
                        filename,

                    "narration":
                        str(
                            scene_narration
                            or ""
                        ).strip(),

                    "subtitle":
                        str(
                            scene_subtitle
                            or ""
                        ).strip(),

                    "emoji_left":
                        str(
                            scene_emoji_left
                            or ""
                        ).strip(),

                    "emoji_right":
                        str(
                            scene_emoji_right
                            or ""
                        ).strip(),
                }
            )

        st.session_state[
            "nb510_scene_inputs"
        ] = scene_inputs

    loaded_source_preview = list(
        st.session_state.get(
            "nb510_loaded_saved_sources",
            [],
        )
        or []
    )

    if loaded_source_preview:

        st.info(
            f"📂 기존 프로젝트 소스 {len(loaded_source_preview)}개를 불러왔습니다. "
            "새 파일을 업로드하지 않으면 이 소스로 다시 제작합니다."
        )

    st.caption(
        "영상 길이·속도·업로드 순서는 변경하지 않고, "
        "영상 프레임을 분석해 나레이션 초안만 만듭니다."
    )

    # -----------------------------------------------------
    # AI 버튼용 OpenAI 설정 선로딩
    #
    # 아래쪽 설정 UI가 아직 실행되기 전이므로
    # 저장된 설정 + session_state를 먼저 사용한다.
    # -----------------------------------------------------

    _saved_openai_settings = (
        load_openai_settings()
    )

    active_openai_api_key = str(
        st.session_state.get(
            "nb510_openai_key",
            "",
        )
        or _saved_openai_settings.get(
            "api_key",
            "",
        )
        or ""
    ).strip()

    active_openai_model = str(
        st.session_state.get(
            "nb510_openai_model",
            "",
        )
        or _saved_openai_settings.get(
            "model",
            "gpt-5-mini",
        )
        or "gpt-5-mini"
    ).strip()

    active_review_summary = str(
        st.session_state.get(
            "nb510_review_summary",
            "",
        )
        or ""
    ).strip()

    if st.button(
        "🎬 영상 보고 나레이션 자동 생성",
        key="nb510_ai_narration_generate",
        type="primary",
    ):

        if not media_files:

            st.error(
                "먼저 제품 영상을 업로드해주세요."
            )

        elif not active_openai_api_key:

            st.error(
                "OpenAI API Key를 입력해주세요."
            )

        else:

            ai_folder = (
                WORK_DIR
                / "_ai_narration_preview"
            )

            if ai_folder.exists():

                shutil.rmtree(
                    ai_folder,
                    ignore_errors=True,
                )

            ai_folder.mkdir(
                parents=True,
                exist_ok=True,
            )

            try:

                with st.spinner(
                    "🎬 영상 장면을 분석하고 나레이션을 만드는 중..."
                ):

                    # 버튼을 누를 때 현재 OpenAI 설정도 자동 저장
                    save_openai_settings(
                        active_openai_api_key,
                        active_openai_model,
                    )

                    ai_sources = (
                        save_sources(
                            media_files,
                            ai_folder,
                        )
                    )

                    analysis_sources = [
                        source
                        for source in ai_sources
                        if (
                            str(
                                source.get(
                                    "type",
                                    "",
                                )
                            ).lower()
                            in (
                                "video",
                                "image",
                            )
                        )
                    ]

                    if not analysis_sources:

                        raise RuntimeError(
                            "분석할 영상/이미지 파일이 없습니다."
                        )

                    cache_key = (
                        build_ai_narration_cache_key(
                            analysis_sources,
                            product_name,
                            active_review_summary,
                            active_openai_model,
                        )
                    )

                    cached = (
                        find_ai_narration_cache(
                            cache_key
                        )
                    )

                    if cached:

                        ai_results = (
                            cached.get(
                                "results",
                                []
                            )
                            or []
                        )

                        ai_script = str(
                            cached.get(
                                "script",
                                "",
                            )
                            or ""
                        ).strip()

                        st.session_state[
                            "nb510_ai_cache_hit"
                        ] = True

                    else:

                        ai_results = (
                            generate_video_narration_with_openai(
                                analysis_sources,
                                ai_folder,
                                product_name,
                                active_review_summary,
                                active_openai_api_key,
                                active_openai_model,
                            )
                        )

                        ai_script = (
                            combine_ai_video_narrations(
                                ai_results
                            )
                        )

                        st.session_state[
                            "nb510_ai_cache_hit"
                        ] = False

                    if not ai_script.strip():

                        raise RuntimeError(
                            "생성된 나레이션이 비어 있습니다."
                        )

                    st.session_state[
                        "nb510_ai_narration_results"
                    ] = ai_results

                    st.session_state[
                        "nb510_ai_narration_pending"
                    ] = ai_script

                    if not cached:

                        saved_entry = (
                            save_ai_narration_history(
                                product_name,
                                ai_script,
                                ai_results,
                                active_review_summary,
                                cache_key=cache_key,
                            )
                        )

                        st.session_state[
                            "nb510_last_ai_narration_id"
                        ] = saved_entry[
                            "id"
                        ]

                st.rerun()

            except Exception as exc:

                st.error(
                    "AI 나레이션 생성 실패: "
                    + str(exc)
                )



    # -----------------------------------------------------
    # SAVED AI NARRATION HISTORY
    # -----------------------------------------------------

    narration_history = (
        load_ai_narration_history()
    )

    if narration_history:

        st.markdown(
            "#### 💾 저장된 AI 나레이션"
        )

        history_labels = []

        for item in narration_history:

            product_label = str(
                item.get(
                    "product_name",
                    "",
                )
            ).strip()

            if not product_label:
                product_label = "제품명 없음"

            created_label = str(
                item.get(
                    "created_at",
                    "",
                )
            )

            history_labels.append(
                (
                    f"{product_label}"
                    f" · {created_label}"
                )
            )

        selected_history_index = (
            st.selectbox(
                "저장된 대본 선택",
                options=list(
                    range(
                        len(
                            narration_history
                        )
                    )
                ),
                format_func=lambda index:
                    history_labels[
                        index
                    ],
                key="nb510_ai_history_select",
            )
        )

        selected_history = (
            narration_history[
                int(
                    selected_history_index
                )
            ]
        )

        col_load, col_preview = (
            st.columns(
                [1, 2]
            )
        )

        with col_load:

            if st.button(
                "📥 이 대본 불러오기",
                key="nb510_ai_history_load",
            ):

                loaded_script = str(
                    selected_history.get(
                        "script",
                        "",
                    )
                    or ""
                ).strip()

                if loaded_script:

                    st.session_state[
                        "nb510_ai_narration_pending"
                    ] = loaded_script

                    st.session_state[
                        "nb510_ai_narration_results"
                    ] = (
                        selected_history.get(
                            "results",
                            []
                        )
                        or []
                    )

                    st.rerun()

                else:

                    st.error(
                        "저장된 대본이 비어 있습니다."
                    )

        with col_preview:

            with st.expander(
                "선택한 대본 미리보기"
            ):

                st.write(
                    str(
                        selected_history.get(
                            "script",
                            "",
                        )
                    )
                )


    if st.session_state.get(
        "nb510_ai_cache_hit",
        False,
    ):

        st.success(
            "♻️ 동일한 영상과 리뷰요약의 기존 AI 나레이션을 "
            "찾아서 API를 다시 호출하지 않았습니다."
        )

    ai_preview = (
        st.session_state.get(
            "nb510_ai_narration_results",
            []
        )
        or []
    )

    if ai_preview:

        with st.expander(
            "🎙️ 장면별 AI 나레이션 결과 · 직접 수정 가능",
            expanded=True,
        ):

            edited_results = []

            video_display_no = 0
            image_display_no = 0

            for result_index, item in enumerate(
                ai_preview
            ):

                source_type = str(
                    item.get(
                        "source_type",
                        "video",
                    )
                    or "video"
                ).lower()

                if source_type == "image":

                    image_display_no += 1

                    scene_label = (
                        f"이미지 {image_display_no}"
                    )

                else:

                    video_display_no += 1

                    scene_label = (
                        f"영상 {video_display_no}"
                    )

                duration_value = float(
                    item.get(
                        "duration",
                        0.0,
                    )
                )

                narration_value = str(
                    item.get(
                        "narration",
                        "",
                    )
                    or ""
                )

                st.markdown(
                    f"**{scene_label} · "
                    f"{duration_value:.2f}초**"
                )

                edited_text = st.text_area(
                    f"{scene_label} 나레이션",
                    value=narration_value,
                    height=80,
                    key=(
                        "nb510_ai_scene_edit_"
                        f"{result_index}"
                    ),
                    label_visibility="collapsed",
                )

                edited_item = dict(
                    item
                )

                edited_item[
                    "narration"
                ] = str(
                    edited_text or ""
                ).strip()

                edited_results.append(
                    edited_item
                )

            st.caption(
                "문구 수정은 OpenAI를 다시 호출하지 않습니다."
            )

            if st.button(
                "✅ 수정한 나레이션 적용",
                key="nb510_ai_narration_apply_edits",
                type="primary",
            ):

                st.session_state[
                    "nb510_ai_narration_results"
                ] = edited_results

                edited_script = (
                    combine_ai_video_narrations(
                        edited_results
                    )
                )

                st.session_state[
                    "nb510_ai_narration_pending"
                ] = edited_script

                st.session_state[
                    "nb510_script"
                ] = edited_script

                st.success(
                    "수정한 나레이션을 최종 대본에 적용했습니다."
                )

                st.rerun()

    # -----------------------------------------------------
    # REVIEW
    # -----------------------------------------------------

    st.markdown(
        "### ⭐ 네이버 리뷰 증거컷"
    )

    review_capture = (
        st.file_uploader(
            "리뷰 수 + 평점 캡처",
            type=[
                "png",
                "jpg",
                "jpeg",
                "webp",
            ],
            key="nb510_review",
        )
    )

    st.caption(
        "예: 리뷰 5,972 / ★4.82"
    )

    # -----------------------------------------------------
    # AI REVIEW SUMMARY
    # -----------------------------------------------------

    st.markdown(
        "### 💡 AI 리뷰요약"
    )

    review_summary = (
        st.text_area(
            "구매자들이 많이 언급한 장점을 입력해주세요.",
            height=130,
            placeholder=(
                "휴대하기 편해요\n"
                "사용이 편해요\n"
                "무선이에요\n"
                "세척이 편리해요\n"
                "잘 갈려요\n"
                "관리가 편해요"
            ),
            key="nb510_review_summary",
        )
    )

    st.caption(
        "영상에 실제로 보이는 장면과 일치하는 리뷰 장점을 "
        "자동 나레이션 생성에 활용합니다."
    )

    # -----------------------------------------------------
    # OPENAI VISION / NARRATION
    # -----------------------------------------------------

    st.markdown(
        "### 🤖 AI 영상 분석 설정"
    )

    openai_defaults = (
        load_openai_settings()
    )

    openai_api_key = (
        st.text_input(
            "OpenAI API Key",
            value=(
                openai_defaults[
                    "api_key"
                ]
            ),
            type="password",
            key="nb510_openai_key",
        )
    )

    openai_model = (
        st.selectbox(
            "영상 분석 모델",
            options=[
                "gpt-5-mini",
                "gpt-5",
            ],
            index=(
                0
                if openai_defaults.get(
                    "model"
                )
                != "gpt-5"
                else 1
            ),
            key="nb510_openai_model",
        )
    )

    if st.button(
        "💾 AI 설정 저장",
        key="nb510_openai_save",
    ):

        save_openai_settings(
            openai_api_key,
            openai_model,
        )

        st.success(
            "OpenAI 설정을 저장했습니다."
        )

    st.caption(
        "다음 단계에서 업로드 영상의 대표 프레임을 분석해 "
        "장면별 나레이션을 자동 생성합니다."
    )

    # -----------------------------------------------------
    # SCRIPT
    # -----------------------------------------------------

    # -----------------------------------------------------
    # AI GENERATED NARRATION PENDING APPLY
    # -----------------------------------------------------

    if (
        "nb510_ai_narration_pending"
        in st.session_state
    ):

        pending_text = str(
            st.session_state.pop(
                "nb510_ai_narration_pending"
            )
            or ""
        ).strip()

        if pending_text:

            st.session_state[
                "nb510_script"
            ] = pending_text

    st.markdown(
        "### 🎙️ 나레이션 대본"
    )

    narration = (
        st.text_area(
            "Typecast가 읽을 대본",
            height=220,
            key="nb510_script",
        )
    )

    # -----------------------------------------------------
    # SUBTITLE
    # -----------------------------------------------------

    st.markdown(
        "### 💬 영상 자막"
    )

    subtitle = (
        st.text_area(
            "한 장면 최대 2줄 · 빈 줄 = 다음 장면",
            placeholder=(
                "후기 5,972개\n"
                "평점 ★4.82\n\n"

                "[강조] 4일 한정\n"
                "최대 혜택가 268,000원\n\n"

                "22L 대용량\n"
                "올스텐 구성"
            ),
            height=260,
            key="nb510_subtitle",
        )
    )

    st.caption(
        "[강조]를 붙이면 해당 줄 전체가 "
        "Gmarket Sans Bold 강조 스타일로 표시됩니다."
    )

    # -----------------------------------------------------
    # BGM
    # -----------------------------------------------------

    st.markdown(
        "### 🎵 BGM"
    )

    bgm = (
        st.file_uploader(
            "BGM",
            type=[
                "mp3",
                "wav",
                "m4a",
                "aac",
                "ogg",
                "flac",
            ],
            key="nb510_bgm",
        )
    )

    bgm_volume = (
        st.slider(
            "BGM 볼륨",
            0,
            50,
            20,
            5,
            key="nb510_bgm_volume",
        )
    )

    # -----------------------------------------------------
    # TYPECAST
    # -----------------------------------------------------

    st.markdown(
        "### 🎙️ Typecast"
    )

    defaults = (
        load_typecast_settings()
    )

    api_key = (
        st.text_input(
            "Typecast API Key",
            value=(
                defaults[
                    "api_key"
                ]
            ),
            type="password",
            key="nb510_typecast_key",
        )
    )

    choices = (
        typecast_voice_choices(
            api_key
        )
        if api_key
        else []
    )

    voice_id = (
        defaults[
            "voice_id"
        ]
    )

    voice_name = (
        defaults[
            "voice_name"
        ]
    )

    if choices:

        names = [
            item[0]
            for item
            in choices
        ]

        # -------------------------------------------------
        # 저장된 이름 + ID가 모두 같은 항목 우선
        # -------------------------------------------------

        exact_matches = [
            i
            for i, item
            in enumerate(
                choices
            )
            if (
                item[0] == voice_name
                and item[1] == voice_id
            )
        ]

        name_matches = [
            i
            for i, item
            in enumerate(
                choices
            )
            if item[0] == voice_name
        ]

        if exact_matches:

            default_index = (
                exact_matches[0]
            )

        elif name_matches:

            default_index = (
                name_matches[0]
            )

        elif "서연" in names:

            default_index = (
                names.index(
                    "서연"
                )
            )

        elif "지안" in names:

            default_index = (
                names.index(
                    "지안"
                )
            )

        else:

            default_index = 0

        # -------------------------------------------------
        # 이름이 같은 성우가 있을 수 있으므로
        # Voice ID 일부를 화면에 함께 표시
        # -------------------------------------------------

        labels = []

        for name, this_voice_id in choices:

            duplicate_count = (
                names.count(
                    name
                )
            )

            if duplicate_count > 1:

                short_id = (
                    this_voice_id[-8:]
                    if len(
                        this_voice_id
                    ) > 8
                    else this_voice_id
                )

                labels.append(
                    f"{name} · ID {short_id}"
                )

            else:

                labels.append(
                    name
                )

        selected_index = (
            st.selectbox(
                "성우",
                options=list(
                    range(
                        len(
                            choices
                        )
                    )
                ),
                index=default_index,
                format_func=lambda i: labels[i],
                key="nb510_voice_exact",
            )
        )

        voice_name = (
            choices[
                selected_index
            ][0]
        )

        voice_id = (
            choices[
                selected_index
            ][1]
        )

        st.caption(
            f"실제 Typecast 전달 성우: "
            f"{voice_name} · "
            f"Voice ID: {voice_id}"
        )

        if (
            names.count(
                voice_name
            )
            > 1
        ):

            st.warning(
                "같은 이름의 Typecast 성우가 여러 명 있습니다. "
                "Voice ID가 다른 항목을 직접 선택할 수 있습니다."
            )

    speed = (
        st.slider(
            "말하기 속도",
            0.8,
            1.5,
            1.25,
            0.1,
            key="nb512_speed",
        )
    )

    # -----------------------------------------------------
    # CREATE
    # -----------------------------------------------------

    st.markdown(
        "---"
    )

    if st.button(
        "🔥 네이버 클립 원클릭 제작",
        type="primary",
        use_container_width=True,
        key="nb510_create",
    ):

        if not product_name.strip():

            st.error(
                "제품명을 입력해주세요."
            )

            return

        loaded_saved_sources = list(
            st.session_state.get(
                "nb510_loaded_saved_sources",
                [],
            )
            or []
        )

        if (
            not media_files
            and not loaded_saved_sources
        ):

            st.error(
                "제품 영상/이미지를 넣어주세요."
            )

            return

        # AI 자동 생성 대본이 session_state에 들어온 경우도
        # 제작용 narration에 확실하게 반영
        scene_inputs_for_render = (
            st.session_state.get(
                "nb510_scene_inputs",
                [],
            )
            or []
        )

        has_scene_narration = any(
            str(
                item.get(
                    "narration",
                    "",
                )
                or ""
            ).strip()
            for item in scene_inputs_for_render
        )

        narration = str(
            narration
            or st.session_state.get(
                "nb510_script",
                "",
            )
            or ""
        ).strip()

        if (
            not narration
            and not has_scene_narration
        ):

            st.error(
                "장면별 나레이션 또는 전체 나레이션 대본을 입력해주세요."
            )

            return

        if not api_key:

            st.error(
                "Typecast API 키가 없습니다."
            )

            return

        if not voice_id:

            st.error(
                "Typecast 성우를 선택해주세요."
            )

            return

        project_id = (
            f"{now_id()}_"
            f"{safe_name(compact_product_name(product_name))}"
        )

        upload_folder = (
            UPLOAD_DIR
            / project_id
        )

        upload_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        work_folder = (
            WORK_DIR
            / project_id
        )

        work_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        loaded_saved_sources = list(
            st.session_state.get(
                "nb510_loaded_saved_sources",
                [],
            )
            or []
        )

        if media_files:

            sources = (
                save_sources(
                    media_files,
                    upload_folder,
                )
            )

        elif loaded_saved_sources:

            sources = []

            generated_source_tokens = (
                "scene_narration",
                "ai_video_frames",
                "body_icons",
                "\\sfx\\",
                "/sfx/",
                "review_capture",
                "price_capture",
                "ad_badge",
                "content_extended",
            )

            for saved_source in loaded_saved_sources:

                saved_source = (
                    saved_source
                    or {}
                )

                saved_path = str(
                    saved_source.get(
                        "path",
                        "",
                    )
                    or ""
                ).strip()

                saved_path_lower = (
                    saved_path
                    .replace("\\", "/")
                    .lower()
                )

                if any(
                    token
                    .replace("\\", "/")
                    .lower()
                    in saved_path_lower
                    for token
                    in generated_source_tokens
                ):
                    continue

                if (
                    not saved_path
                    or not Path(
                        saved_path
                    ).is_file()
                ):
                    continue

                sources.append(
                    {
                        "path":
                            saved_path,

                        "type":
                            str(
                                saved_source.get(
                                    "type",
                                    "",
                                )
                                or ""
                            ),

                        "original_name":
                            str(
                                saved_source.get(
                                    "original_name",
                                    Path(
                                        saved_path
                                    ).name,
                                )
                                or Path(
                                    saved_path
                                ).name
                            ),
                    }
                )

        else:

            sources = []

        if not sources:

            raise RuntimeError(
                "제품 영상·이미지가 없습니다. "
                "새 파일을 업로드하거나 기존 프로젝트를 불러와주세요."
            )

        price_path = (
            save_uploaded(
                price_capture,
                upload_folder,
                "price_capture",
            )
            if price_capture
            else ""
        )

        review_path = (
            save_uploaded(
                review_capture,
                upload_folder,
                "review_capture",
            )
            if review_capture
            else ""
        )

        bgm_path = (
            save_uploaded(
                bgm,
                upload_folder,
                "bgm",
            )
            if bgm
            else ""
        )

        typecast = {
            "api_key":
                api_key,

            "voice_id":
                voice_id,

            "speed":
                speed,
        }

        try:

            final_path = (
                render_project(
                    project_id,
                    sources,
                    narration.strip(),
                    subtitle.strip(),
                    promotion_text.strip(),
                    review_path,
                    price_path,
                    bgm_path,
                    bgm_volume,
                    typecast,
                    scene_inputs=scene_inputs_for_render,
                )
            )

            try:

                save_naver_brand_project_state(
                    folder=(
                        WORK_DIR
                        / project_id
                    ),
                    project_id=project_id,
                    sources=sources,
                    scene_inputs=(
                        scene_inputs_for_render
                    ),
                    narration=(
                        narration.strip()
                    ),
                    subtitle=(
                        subtitle.strip()
                    ),
                    promotion_text=(
                        promotion_text.strip()
                    ),
                    product_name=(
                        product_name
                    ),
                    bgm_volume=(
                        bgm_volume
                    ),
                    typecast=(
                        typecast
                    ),
                    final_video=(
                        final_path
                    ),
                )

            except Exception as state_exc:

                print(
                    "[PROJECT STATE SAVE ERROR]",
                    type(state_exc).__name__,
                    str(state_exc),
                    flush=True,
                )

            st.success(
                "🎉 완성되었습니다."
            )

            st.video(
                final_path
            )

            st.caption(
                final_path
            )

        except Exception as exc:

            st.error(
                "영상 제작 중 오류가 발생했습니다."
            )

            st.code(
                str(
                    exc
                )
            )


if __name__ == "__main__":
    main()






























