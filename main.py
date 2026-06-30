import streamlit as st

from database.init_db import init_db

from app.ui.dashboard import show_dashboard
from app.ui.one_click_pipeline import show_one_click_pipeline
from app.ui.real_vision_runner import show_real_vision_runner
from app.ui.product_ai import show_product_ai
from app.ui.video import show_video
from app.ui.source_video_ai import show_source_video_ai
from app.ui.auto_editor import show_auto_editor
from app.ui.content_factory import show_content_factory
from app.ui.capcut_export import show_capcut_export
from app.ui.yolo_ai import show_yolo_ai
from app.ui.object_ai import show_object_ai
from app.ui.caption_safe import show_caption_safe
from app.ui.vision_ai import show_vision_ai
from app.ui.paddle_ocr import show_paddle_ocr
from app.ui.ocr_setup import show_ocr_setup
from app.ui.intelligence import show_intelligence
from app.ui.ocr import show_ocr
from app.ui.smart_cut import show_smart_cut
from app.ui.video_library import show_video_library
from app.ui.capcut import show_capcut
from app.ui.performance import show_performance
from app.ui.learning import show_learning
from app.ui.shorts_studio import show_shorts_studio
from app.ui.project_recovery import show_project_recovery
from app.ui.data_migration import show_data_migration
from app.ui.backup_restore import show_backup_restore
from app.ui.system_check import show_system_check
from app.ui.settings import show_settings


init_db()

st.set_page_config(
    page_title="AutoCommerceAI",
    page_icon="🏠",
    layout="wide",
)

MENU_ITEMS = [
    "🏠 대시보드",
    "⚡ 원클릭 파이프라인",
    "🚀 리얼 비전 러너",
    "🛒 제품 AI",
    "🎬 영상관리",
    "🎥 소스 비디오 AI",
    "🎬 자동 편집기",
    "🏭 콘텐츠 팩토리",
    "📤 CapCut 내보내기",
    "🧠 YOLO 비전",
    "🧲 객체 AI",
    "🛡️ 캡션 안전",
    "👁️ 비전 AI",
    "🧠 패들OCR",
    "🧩 OCR 설치 확인",
    "🧠 비디오 인텔리전스",
    "🔍 OCR/자막 감지",
    "🎯 스마트 컷",
    "📂 영상 라이브러리",
    "✂️ CapCut 편집",
    "📈 성과",
    "📊 AI 학습",
    "🎞️ 쇼츠 스튜디오 3.0",
    "🧩 프로젝트 빠른 복구",
    "📦 데이터 가져오기",
    "💾 백업/복원",
    "🧰 시스템 체크",
    "⚙️ 설정",
]

ROUTES = {
    "🏠 대시보드": show_dashboard,
    "⚡ 원클릭 파이프라인": show_one_click_pipeline,
    "🚀 리얼 비전 러너": show_real_vision_runner,
    "🛒 제품 AI": show_product_ai,
    "🎬 영상관리": show_video,
    "🎥 소스 비디오 AI": show_source_video_ai,
    "🎬 자동 편집기": show_auto_editor,
    "🏭 콘텐츠 팩토리": show_content_factory,
    "📤 CapCut 내보내기": show_capcut_export,
    "🧠 YOLO 비전": show_yolo_ai,
    "🧲 객체 AI": show_object_ai,
    "🛡️ 캡션 안전": show_caption_safe,
    "👁️ 비전 AI": show_vision_ai,
    "🧠 패들OCR": show_paddle_ocr,
    "🧩 OCR 설치 확인": show_ocr_setup,
    "🧠 비디오 인텔리전스": show_intelligence,
    "🔍 OCR/자막 감지": show_ocr,
    "🎯 스마트 컷": show_smart_cut,
    "📂 영상 라이브러리": show_video_library,
    "✂️ CapCut 편집": show_capcut,
    "📈 성과": show_performance,
    "📊 AI 학습": show_learning,
    "🎞️ 쇼츠 스튜디오 3.0": show_shorts_studio,
    "🧩 프로젝트 빠른 복구": show_project_recovery,
    "📦 데이터 가져오기": show_data_migration,
    "💾 백업/복원": show_backup_restore,
    "🧰 시스템 체크": show_system_check,
    "⚙️ 설정": show_settings,
}

menu = st.sidebar.radio("메뉴", MENU_ITEMS)
st.sidebar.write("현재 선택:", menu)

handler = ROUTES.get(menu)
if handler:
    handler()
else:
    st.error(f"메뉴 라우팅을 찾을 수 없습니다: {menu}")