import json
from pathlib import Path

import streamlit as st

from ui.dashboard import render_dashboard
from ui.shorts_page import render_shorts_page
from ui.analysis_page import render_analysis_page


PRODUCT_DB = Path("data/products/products.json")


def load_json(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


st.set_page_config(
    page_title="AutoCommerceAI",
    page_icon="🚀",
    layout="wide",
)

st.title("🚀 오토커머스 AI")
st.caption("쿠팡 링크 + 상품명 → GPT 쇼핑쇼츠 생성")

menu = st.sidebar.radio(
    "메뉴",
    ["대시보드", "쇼츠 AI", "제품 DB", "분석"]
)

if menu == "대시보드":
    render_dashboard()

elif menu == "쇼츠 AI":
    render_shorts_page()

elif menu == "제품 DB":
    st.subheader("제품 DB")
    st.json(load_json(PRODUCT_DB, {}))

elif menu == "분석":
    render_analysis_page()