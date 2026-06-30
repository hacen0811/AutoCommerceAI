import json
import streamlit as st

from modules.project.repository import ProjectRepository
from modules.video.vision_ai_engine import VisionAIEngine
from modules.video.ocr_detector import OCRDetector
from modules.editor.caption_safe_engine import CaptionSafeEngine
from app.ui.render import copybox


def show_caption_safe():
    st.title("🛡️ Auto Caption Safe")
    st.caption("중국어 자막/워터마크 위험을 반영해 하센 자막 안전 위치를 추천합니다.")

    projects = ProjectRepository().all()
    if not projects:
        st.info("프로젝트가 없습니다.")
        return

    labels = {f"{p.id} | {p.product_name}": p for p in projects}
    project = labels[st.selectbox("프로젝트", list(labels.keys()))]

    if not project.video_path:
        st.warning("원본 영상이 없습니다. 영상관리에서 먼저 영상을 업로드하세요.")
        return

    if st.button("자막 안전영역 계산", use_container_width=True):
        with st.spinner("자막/워터마크 위험을 계산 중입니다..."):
            vision = VisionAIEngine().analyze(project.video_path, sample_count=8, use_ocr=False)
            ocr = OCRDetector().detect(project.video_path, sample_count=8)
            safe = CaptionSafeEngine().build(vision, ocr)

        st.success(f"추천 자막 위치: {safe.get('safe_subtitle_position')}")

        st.subheader("CapCut 적용 규칙")
        for item in safe.get("capcut_rule", []):
            st.write("✅", item)

        st.subheader("위험 구역")
        if not safe.get("danger_zones"):
            st.write("중간 이상 위험 구역이 뚜렷하지 않습니다.")
        for zone in safe.get("danger_zones", []):
            st.write(f"• {zone.get('zone')} / {zone.get('level')}")

        st.subheader("오디오 dB")
        for k, v in safe.get("audio_rule", {}).items():
            st.write(f"**{k}**: {v}")

        copybox("Caption Safe JSON", json.dumps(safe, ensure_ascii=False, indent=2), 420)
