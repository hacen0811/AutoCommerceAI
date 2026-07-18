from datetime import datetime
from pathlib import Path
import json

import pandas as pd
import streamlit as st


PERF_DB = Path("data/performance/performance.json")


def load_json(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def render_analysis_page():
    rows = load_json(PERF_DB, [])

    st.subheader("성과 학습")

    if rows:
        st.dataframe(pd.DataFrame(rows).sort_values("views", ascending=False))
    else:
        st.info("아직 저장된 성과 데이터가 없습니다.")

    product = st.text_input("제품명")
    hook = st.text_input("후킹")
    views = st.number_input("조회수", min_value=0, step=100)

    if st.button("성과 저장"):
        rows.append({
            "product": product,
            "hook": hook,
            "views": int(views),
            "created_at": datetime.now().isoformat(timespec="seconds"),
        })
        save_json(PERF_DB, rows)
        st.success("저장 완료")