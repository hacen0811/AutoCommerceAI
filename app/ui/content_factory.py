import json
import streamlit as st

from modules.project.repository import ProjectRepository
from modules.project.project_selector import ProjectSelector
from modules.ai.content_factory import ContentFactory
from app.ui.render import copybox


def show_content_factory():
    st.title("🏭 Content Factory")
    st.caption("쇼츠/릴스/인포크/블로그/업로드 문구를 한 번에 생성합니다.")

    projects = ProjectSelector().all_projects()
    if not projects:
        st.info("프로젝트가 없습니다.")
        return

    labels = ProjectSelector().labels(projects)
    project = labels[st.selectbox("프로젝트", list(labels.keys()))]

    if st.button("콘텐츠 패키지 생성", use_container_width=True):
        bundle = ContentFactory().build(project)

        st.success("콘텐츠 패키지 생성 완료")

        tab1, tab2, tab3, tab4 = st.tabs(["쇼츠/릴스", "인포크", "블로그", "업로드"])

        with tab1:
            shorts = bundle.get("shorts", {})
            for group, hooks in shorts.get("hooks", {}).items():
                st.subheader(group)
                for i, hook in enumerate(hooks, 1):
                    copybox(f"{group} {i}", hook, 70)

            for name, lines in shorts.get("scripts", {}).items():
                copybox(name, "\n".join(lines), 190)

            copybox("썸네일", "\n".join(shorts.get("thumbnail", [])), 120)

        with tab2:
            for k, v in bundle.get("inpock", {}).items():
                copybox(k, v, 90)

        with tab3:
            blog = bundle.get("blog", {})
            copybox("블로그 제목", blog.get("title"), 80)
            copybox("블로그 본문", blog.get("body"), 300)

        with tab4:
            for k, v in bundle.get("upload_bundle", {}).items():
                copybox(k, v, 120)
            copybox("전체 JSON", json.dumps(bundle, ensure_ascii=False, indent=2), 420)
