import json
import streamlit as st


def copybox(title, value, height=110):
    st.markdown(f"### {title}")
    st.text_area(title, value=value or "", height=height, label_visibility="collapsed")


def render_project_detail(project, checklist):
    data = json.loads(project.data_json or "{}")
    ai = data.get("ai", {})
    capcut = data.get("capcut", {})
    video_analysis = data.get("video_analysis", {})
    inpock = data.get("inpock", {})

    tabs = st.tabs(["작업순서", "영상/CapCut", "AI 콘텐츠", "인포크", "성과", "원본"])

    with tabs[0]:
        c1, c2 = st.columns([1, 3])
        with c1:
            if project.image_url:
                st.image(project.image_url, width=220)
            else:
                st.info("대표 이미지 없음")
        with c2:
            st.subheader(project.product_name)
            st.write("가격:", project.price or "-")
            st.write("카테고리:", project.category or "-")
            st.write("쿠팡:", project.coupang_url or "-")
            st.write("쿠팡파트너스:", project.partner_url or "-")
            st.write("타오바오:", project.taobao_url or "-")
            st.write("도우인:", project.douyin_url or "-")
            st.write("원본 영상:", project.video_path or "미등록")
            st.metric("AI 점수", project.score)

        st.divider()
        st.subheader("업로드 체크리스트")
        st.write("□ 원본 영상 확보:", "완료" if checklist.source_video else "미완료")
        st.write("□ CapCut 편집:", "완료" if checklist.capcut_edit else "미완료")
        st.write("□ 인포크 등록:", "완료" if checklist.inpock else "미완료")
        st.write("□ 유튜브 업로드:", "완료" if checklist.youtube else "미완료")
        st.write("□ 인스타 업로드:", "완료" if checklist.instagram else "미완료")
        st.write("□ 성과 입력:", "완료" if checklist.performance else "미완료")

    with tabs[1]:
        st.subheader("영상 분석")
        if video_analysis:
            st.write("해상도:", f"{video_analysis.get('width', '-')} x {video_analysis.get('height', '-')}")
            st.write("방향:", video_analysis.get("orientation", "-"))
            st.write("길이:", video_analysis.get("duration", "-"))
            for item in video_analysis.get("edit_risk", []):
                st.write("⚠️", item)
        st.divider()
        st.subheader("CapCut 편집 지시서")
        for key, value in capcut.items():
            if isinstance(value, list):
                copybox(key, "\n".join(value), 160)
            else:
                st.write(f"**{key}**: {value}")

    with tabs[2]:
        for i, hook in enumerate(ai.get("hooks", []), 1):
            copybox(f"후킹 {i}", hook, 70)
        for name, lines in ai.get("scripts", {}).items():
            copybox(name, "\n".join(lines), 190)
        copybox("유튜브 제목", ai.get("youtube_title", ""), 70)
        copybox("유튜브 설명", ai.get("youtube_desc", ""), 120)
        copybox("인스타 본문", ai.get("instagram_body", ""), 150)
        copybox("썸네일", "\n".join(ai.get("thumbnails", [])), 120)

    with tabs[3]:
        for key, value in inpock.items():
            copybox(key, value, 90)

    with tabs[4]:
        st.info("성과 입력은 성과 메뉴에서 진행합니다.")

    with tabs[5]:
        copybox("프로젝트 JSON", json.dumps(data, ensure_ascii=False, indent=2), 420)
