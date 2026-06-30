import streamlit as st

from modules.system.ffmpeg_checker import FFmpegChecker


def show_system_check():
    st.title("🧰 시스템 체크")
    st.caption("FFmpeg/ffprobe, 영상 분석 환경을 확인합니다.")

    result = FFmpegChecker().check()

    c1, c2, c3 = st.columns(3)
    c1.metric("FFmpeg", "OK" if result.get("ffmpeg_ok") else "NO")
    c2.metric("ffprobe", "OK" if result.get("ffprobe_ok") else "NO")
    c3.metric("상태", "준비됨" if result.get("ready") else "설치 필요")

    st.write("ffmpeg:", result.get("ffmpeg_path") or "-")
    st.write("ffprobe:", result.get("ffprobe_path") or "-")

    if result.get("ffmpeg_version"):
        st.code(result.get("ffmpeg_version"))
    if result.get("ffprobe_version"):
        st.code(result.get("ffprobe_version"))

    if not result.get("ready"):
        st.warning("ffprobe가 없으면 OpenCV fallback으로 분석하지만, 일부 영상은 길이/해상도 분석이 제한될 수 있습니다.")
        st.subheader("Windows 빠른 설치")
        st.code(result.get("winget_command"), language="powershell")
        st.subheader("수동 설치")
        for item in result.get("install_guide", []):
            st.write("•", item)
