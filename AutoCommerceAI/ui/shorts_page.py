import json

import streamlit as st

from core.coupang_parser import analyze_coupang_url
from core.generator import generate_ai_shorts
from ui.capcut_tab import render_capcut_tab
from ui.hooks_tab import render_hooks_tab
from ui.inpock_tab import render_inpock_tab
from ui.product_tab import render_product_tab
from ui.scripts_tab import render_scripts_tab
from ui.social_tab import render_social_tab


def render_full_json_tab(result: dict):
    full = json.dumps(result, ensure_ascii=False, indent=2)

    st.subheader("전체 JSON")
    st.text_area("전체 JSON", full, height=500)

    st.download_button(
        "JSON 다운로드",
        data=full,
        file_name=f"{result['product']}_ai_shorts.json",
        mime="application/json",
    )


def render_ai_result(result: dict):
    ai = result["ai_result"]

    st.success("AI 쇼핑쇼츠 생성 완료")
    st.info(f"저장 위치: {result['save_path']}")

    tabs = st.tabs([
        "제품분석",
        "후킹",
        "대본",
        "자막",
        "촬영컷",
        "릴스/유튜브",
        "캡컷",
        "인포크",
        "전체 JSON",
    ])

    with tabs[0]:
        render_product_tab(ai)

    with tabs[1]:
        render_hooks_tab(ai)

    with tabs[2]:
        render_scripts_tab(ai)

    with tabs[3]:
        st.subheader("자막")
        st.text_area("전체 자막", ai.get("captions", ""), height=260)

    with tabs[4]:
        st.subheader("촬영컷")
        st.text_area("촬영 순서", ai.get("scenes", ""), height=280)

    with tabs[5]:
        render_social_tab(ai)

    with tabs[6]:
        render_capcut_tab(ai)

    with tabs[7]:
        render_inpock_tab(ai)

    with tabs[8]:
        render_full_json_tab(result)


def render_shorts_page():
    st.subheader("쇼츠 AI")

    coupang_url = st.text_input(
        "쿠팡 상품 링크",
        placeholder="https://www.coupang.com/vp/products/...",
    )

    if coupang_url:
        coupang_info = analyze_coupang_url(coupang_url)

        if coupang_info.get("is_valid"):
            st.success(coupang_info.get("message", "쿠팡 링크 확인 완료"))
            st.write(f"상품 ID: {coupang_info.get('product_id', '')}")

            if coupang_info.get("item_id"):
                st.write(f"Item ID: {coupang_info.get('item_id')}")

            if coupang_info.get("vendor_item_id"):
                st.write(f"Vendor Item ID: {coupang_info.get('vendor_item_id')}")
        else:
            st.warning(coupang_info.get("message", "쿠팡 링크를 확인할 수 없습니다."))

    product = st.text_input(
        "상품명",
        value="문틈 방충망",
        help="현재는 직접 입력합니다. 쿠팡 상품명 자동 추출은 추후 안정화합니다.",
    )

    if st.button("GPT 쇼핑쇼츠 생성하기", use_container_width=True):
        if not product.strip():
            st.error("상품명을 입력해주세요.")
            return

        with st.spinner("GPT가 쇼핑쇼츠 기획을 생성 중입니다..."):
            try:
                result = generate_ai_shorts(
                    product_name=product.strip(),
                    coupang_url=coupang_url.strip(),
                )
                render_ai_result(result)
            except Exception as e:
                st.error("AI 생성 중 오류가 발생했습니다.")
                st.exception(e)