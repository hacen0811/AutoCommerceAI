import json
import streamlit as st

from modules.product.product_engine import ProductEngine
from modules.project.service import ProjectService
from modules.project.repository import ProjectRepository
from modules.video.service import VideoService
from app.ui.render import copybox


def show_product_ai():
    st.title("🛒 Product AI 2.0")
    st.caption("쿠팡 링크 하나로 프로젝트, 검색어, 작업 큐를 준비합니다.")
    st.info("쿠팡이 상품명을 막으면 상품명 보완 칸에 상품명을 붙여넣어 주세요. 그러면 타오바오/도우인 TOP10 검색어가 정확해집니다.")

    url = st.text_input("쿠팡 원본 링크", placeholder="https://www.coupang.com/vp/products/...")
    product_name = st.text_area("상품명 보완", placeholder="쿠팡 상품명을 붙여넣으면 검색어 품질이 올라갑니다.", height=90)
    partner_url = st.text_input("쿠팡파트너스 링크")
    image_url = st.text_input("대표 이미지 URL")
    price = st.text_input("가격")
    category = st.text_input("카테고리")
    uploaded_video = st.file_uploader("원본 영상 바로 업로드", type=["mp4", "mov", "webm"])

    if url:
        built = ProductEngine().build_from_coupang(
            url,
            product_name=product_name,
            manual_product_name=product_name,
            price=price,
            category=category,
            image_url=image_url,
            partner_url=partner_url,
        )

        parsed = built.get("parsed", {})
        keywords = built.get("keywords", {})

        st.subheader("쿠팡 URL 분석")
        c1, c2, c3 = st.columns(3)
        c1.metric("Product ID", parsed.get("product_id") or "-")
        c2.metric("VendorItem ID", parsed.get("vendor_item_id") or "-")
        c3.metric("댓글 키워드", keywords.get("comment_keyword") or "-")

        copybox("정리된 쿠팡 링크", parsed.get("clean_url", ""), 80)

        st.subheader("검색어 자동 생성")
        k1, k2 = st.columns(2)
        with k1:
            copybox("타오바오 검색어", keywords.get("taobao_keyword", ""), 80)
            copybox("한국어 검색어", keywords.get("korean_search", ""), 80)
        with k2:
            copybox("도우인 검색어", keywords.get("douyin_keyword", ""), 80)
            copybox("콘텐츠 각도", keywords.get("content_angle", ""), 80)

        st.subheader("타오바오 TOP10")
        for item in keywords.get("taobao_top10", []):
            with st.container(border=True):
                st.write(f"**{item.get('rank')}. {item.get('query')}**")
                st.caption(f"{item.get('purpose')} / 추천도 {item.get('score')}")

        st.subheader("도우인 TOP10")
        for item in keywords.get("douyin_top10", []):
            with st.container(border=True):
                st.write(f"**{item.get('rank')}. {item.get('query')}**")
                st.caption(f"{item.get('purpose')} / 추천도 {item.get('score')}")

        st.subheader("작업 큐")
        for task in built.get("task_queue", []):
            with st.container(border=True):
                st.write(f"**{task.get('step')}. {task.get('title')}**")
                if task.get("query"):
                    st.code(task.get("query"))
                if task.get("memo"):
                    st.caption(task.get("memo"))

        with st.expander("Product Engine JSON"):
            copybox("JSON", json.dumps(built, ensure_ascii=False, indent=2), 420)

    if st.button("Product AI 프로젝트 생성", use_container_width=True):
        if not url.strip():
            st.warning("쿠팡 링크를 입력하세요.")
            return

        built = ProductEngine().build_from_coupang(
            url,
            product_name=product_name,
            manual_product_name=product_name,
            price=price,
            category=category,
            image_url=image_url,
            partner_url=partner_url,
        )
        payload = built["project_payload"]

        existing = ProjectRepository().find_by_coupang_url(payload.get("coupang_url", ""))
        if existing:
            st.warning(f"이미 등록된 프로젝트입니다: {existing.product_name}")
            return

        video_path = VideoService().save_uploaded_video(uploaded_video) if uploaded_video else ""
        payload["video_path"] = video_path

        project = ProjectService().create_project(payload)
        saved_path = ProductEngine().save_plan(built)

        st.success(f"프로젝트 생성 완료: {project.product_name}")
        st.write("Product Plan 저장:", saved_path)
        st.info("다음 단계: 영상관리 → Real Vision Runner → Content Factory")
