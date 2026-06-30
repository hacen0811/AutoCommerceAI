import json
import streamlit as st

from modules.system.project_backup import ProjectBackup
from app.ui.render import copybox


def show_backup_restore():
    st.title("💾 백업/복원")
    st.caption("프로젝트 DB와 영상 경로를 JSON으로 백업하고 복원합니다.")

    backup = ProjectBackup()

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("백업 만들기")
        include_assets = st.checkbox("영상/이미지 경로 포함", value=True)
        if st.button("현재 프로젝트 백업", use_container_width=True):
            path = backup.export_all(include_assets=include_assets)
            st.success(f"백업 완료: {path}")

        latest = backup.latest_backup()
        st.write("최근 백업:", latest or "-")

    with c2:
        st.subheader("백업 복원")
        backup_path = st.text_input("백업 JSON 경로")
        asset_base = st.text_input("영상/이미지 원본 폴더", placeholder=r"C:\Users\user\Downloads\AutoCommerceAI_1.7.1_RealVisionPathFix")
        overwrite = st.checkbox("기존 데이터 덮어쓰기", value=False)

        if st.button("백업 복원 실행", use_container_width=True):
            result = backup.import_backup(backup_path, copy_assets_from=asset_base or None, overwrite=overwrite)
            if result.get("ok"):
                st.success(result.get("message"))
                st.info("복원 후 새로고침 또는 재실행하세요.")
            else:
                st.error(result.get("message"))
            copybox("복원 결과", json.dumps(result, ensure_ascii=False, indent=2), 300)

    st.divider()
    st.subheader("백업 파일 위치")
    st.code(str(backup.backup_dir))
