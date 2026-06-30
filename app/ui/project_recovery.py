import json
import streamlit as st

from modules.system.project_recovery import ProjectRecovery
from app.ui.render import copybox


def show_project_recovery():
    st.title("🧩 프로젝트 빠른 복구")
    st.caption("예전 DB를 못 찾았을 때 쿠팡 링크 + 상품명 + 원본 영상으로 프로젝트를 빠르게 다시 만듭니다.")

    st.info("이전 DB가 없어도 괜찮습니다. 쿠팡 링크와 상품명을 넣으면 타오바오/도우인 TOP10 검색어까지 다시 생성합니다.")

    coupang_url = st.text_area("쿠팡 링크", height=80, placeholder="https://www.coupang.com/vp/products/...")
    product_name = st.text_area(
        "상품명",
        height=110,
        placeholder="예: 주방 정리대 양념통 정리대 코너 주방 슬라이딩 수납장 다층 선반 조리도구 걸이 냄비뚜껑 거치대",
    )

    uploaded_video = st.file_uploader("원본 영상 선택", type=["mp4", "mov", "webm"])
    price = st.text_input("가격")
    category = st.text_input("카테고리")
    image_url = st.text_input("대표 이미지 URL")
    partner_url = st.text_input("쿠팡파트너스 링크")

    if st.button("프로젝트 복구/생성", use_container_width=True):
        result = ProjectRecovery().rebuild(
            coupang_url=coupang_url,
            product_name=product_name,
            uploaded_video=uploaded_video,
            price=price,
            category=category,
            image_url=image_url,
            partner_url=partner_url,
        )

        if result.get("ok"):
            st.success(result.get("message"))
            built = result.get("built", {})
            keywords = built.get("keywords", {})

            st.subheader("생성된 검색어")
            st.write("타오바오:", keywords.get("taobao_keyword"))
            st.write("도우인:", keywords.get("douyin_keyword"))
            st.write("댓글 키워드:", built.get("project_payload", {}).get("keyword"))

            st.subheader("타오바오 TOP10")
            for item in keywords.get("taobao_top10", []):
                st.write(f"{item.get('rank')}. {item.get('query')} — {item.get('purpose')}")

            st.subheader("도우인 TOP10")
            for item in keywords.get("douyin_top10", []):
                st.write(f"{item.get('rank')}. {item.get('query')} — {item.get('purpose')}")

            st.info("다음 단계: ⚡ 원클릭 파이프라인에서 방금 만든 프로젝트를 선택해 실행하세요.")
        else:
            st.error(result.get("message"))

        copybox("복구 결과 JSON", json.dumps(result, ensure_ascii=False, indent=2, default=str), 420)
