import streamlit as st
from pathlib import Path
from config.settings import VIDEO_DIR


def show_video_library():
    st.title("📂 영상 라이브러리")
    st.caption("업로드된 원본 영상을 한 곳에서 확인합니다.")

    videos = []
    for ext in ["*.mp4", "*.mov", "*.webm"]:
        videos.extend(Path(VIDEO_DIR).glob(ext))

    if not videos:
        st.info("아직 저장된 영상이 없습니다.")
        return

    for video in sorted(videos, key=lambda x: x.stat().st_mtime, reverse=True):
        with st.container(border=True):
            st.write(f"**{video.name}**")
            st.caption(str(video))
            st.write(f"크기: {round(video.stat().st_size / 1024 / 1024, 2)} MB")
