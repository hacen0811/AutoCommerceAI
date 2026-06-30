import json
import streamlit as st

from modules.system.data_migration import DataMigration
from modules.system.auto_migration import AutoMigration
from app.ui.render import copybox


def show_data_migration():
    st.title("📦 데이터 가져오기")
    st.caption("이전 버전 폴더의 프로젝트 DB와 영상 파일을 새 버전으로 가져옵니다.")
    st.warning("새 버전 폴더로 실행하면 기본적으로 DB가 비어 있습니다. 이전 폴더 경로를 넣고 가져오기를 실행하세요.")

    st.subheader("자동 감지 후보")
    candidates = AutoMigration().find_candidates()[:8]
    candidate_labels = [f"{c.get('path')} / DB: {c.get('db_exists')} / 영상: {c.get('video_count')}" for c in candidates]
    selected_candidate = ""
    if candidate_labels:
        selected_label = st.radio("이전 폴더 후보 선택", ["직접 입력"] + candidate_labels)
        if selected_label != "직접 입력":
            idx = candidate_labels.index(selected_label)
            selected_candidate = candidates[idx].get("path", "")
    else:
        st.caption("자동 감지 후보가 없습니다.")

    previous = st.text_input(
        "이전 AutoCommerceAI 폴더 경로",
        placeholder=r"C:\Users\user\Downloads\AutoCommerceAI_1.7.1_RealVisionPathFix",
        value=selected_candidate,
    )
    copy_exports = st.checkbox("exports 결과물도 함께 가져오기", value=False)
    overwrite = st.checkbox("기존 파일 덮어쓰기", value=True)

    mig = DataMigration()

    if previous:
        info = mig.inspect_previous(previous)
        st.subheader("이전 폴더 확인")
        st.write("폴더:", info.get("previous_folder"))
        st.write("폴더 존재:", "✅" if info.get("exists") else "❌")
        st.write("DB 존재:", "✅" if info.get("database_exists") else "❌")
        st.write("영상 수:", info.get("videos_count"))
        st.write("이미지 수:", info.get("images_count"))

    if st.button("이전 데이터 가져오기", use_container_width=True):
        if not previous.strip():
            st.warning("이전 폴더 경로를 입력하세요.")
        else:
            result = mig.import_data(previous, copy_exports=copy_exports, overwrite=overwrite)
            if result.get("ok"):
                st.success(result.get("message"))
                st.info("가져오기 완료 후 프로그램을 새로고침하거나 재실행하면 프로젝트가 보입니다.")
            else:
                st.error(result.get("message"))
            copybox("가져오기 결과", json.dumps(result, ensure_ascii=False, indent=2), 420)
