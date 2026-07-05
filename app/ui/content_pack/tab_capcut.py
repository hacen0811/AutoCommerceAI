import streamlit as st


def show_capcut_tab(pack):
    edit = pack.get("edit_assistant", {})
    capcut = edit.get("capcut", {})
    scene_plan = edit.get("scene_plan", [])

    st.markdown("### CapCut 기본 설정")

    st.write(f"**화면비율:** {capcut.get('format', '9:16')}")
    st.write(f"**자막 위치:** {capcut.get('subtitle_position', '중앙 하단')}")

    subtitle = capcut.get("subtitle_style", {})

    if subtitle:
        st.markdown("### 자막 스타일")
        st.write(f"- 폰트: {subtitle.get('font', '')}")
        st.write(f"- 본문 크기: {subtitle.get('main_size', '')}")
        st.write(f"- 강조 크기: {subtitle.get('highlight_size', '')}")
        st.write(f"- 자막 획: {subtitle.get('stroke', '')}")
        st.write(f"- 그림자: {subtitle.get('shadow', '')}")
        st.write(f"- 강조 색상: {subtitle.get('highlight_color', '')}")

    bgm = capcut.get("bgm", {})

    if bgm:
        st.markdown("### BGM")
        st.write(f"- 분위기: {bgm.get('type', '')}")
        st.write(f"- 볼륨: {bgm.get('volume', '')}")

    sfx = capcut.get("sfx", [])

    if sfx:
        st.markdown("### 효과음")
        for item in sfx:
            st.write(
                f"- {item.get('scene', '')}: "
                f"{item.get('effect', '')} / "
                f"{item.get('volume', '')}"
            )

    if scene_plan:
        st.markdown("### 장면별 편집 계획")
        for scene in scene_plan:
            st.markdown(f"**{scene.get('scene')}. {scene.get('role')}**")
            st.write(f"- 시간: {scene.get('duration', '')}")
            st.write(f"- 문구: {scene.get('text', '')}")
            st.write(f"- 편집: {scene.get('edit', '')}")