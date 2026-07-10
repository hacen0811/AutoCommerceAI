import json
from pathlib import Path

import streamlit as st


EXPORT_DIR = Path("exports/source_candidates")


def latest_candidate_file(platform=None):
    if not EXPORT_DIR.exists():
        return None

    files = sorted(
        EXPORT_DIR.glob("*_latest_candidates.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if platform:
        for f in files:
            if platform.lower() in f.stem.lower():
                return f

    return files[0] if files else None


def load_candidates(platform=None):
    path = latest_candidate_file(platform)

    if not path:
        return []

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def show_source_candidates(platform=None):
    st.subheader("📦 실제 수집 후보")

    candidates = load_candidates(platform)

    if not candidates:
        st.info("아직 수집된 후보가 없습니다.")
        return

    st.caption(f"{len(candidates)}개의 후보를 찾았습니다.")

    for item in candidates:
        with st.container(border=True):

            c1, c2 = st.columns([1, 3])

            with c1:
                thumb = item.get("thumbnail", "")

                if thumb:
                    st.image(thumb, use_container_width=True)

            with c2:

                st.markdown(
                    f"### {item.get('rank', '-')}. {item.get('title', '-')}"
                )

                st.write(
                    f"플랫폼 : {item.get('platform','-')}"
                )

                st.write(
                    f"AI 점수 : {item.get('score',0)}"
                )

                url = item.get("url","")

                if url:
                    st.code(url)

                if st.button(
                    "채택",
                    key=f"candidate_{item.get('platform')}_{item.get('rank')}",
                    use_container_width=True,
                ):
                    st.success("다음 Sprint에서 채택 기능과 연결됩니다.")