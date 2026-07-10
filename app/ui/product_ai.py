import json
from pathlib import Path

import streamlit as st

from modules.product.product_engine import ProductEngine
from modules.project.service import ProjectService
from modules.project.repository import ProjectRepository
from modules.video.service import VideoService
from app.ui.render import copybox


IMAGE_DIR = Path("assets/product_images")


def save_uploaded_image(uploaded_image, product_name="product"):
    if not uploaded_image:
        return ""

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    safe_name = "".join(
        c for c in (product_name or "product")
        if c.isalnum() or c in (" ", "_", "-")
    ).strip().replace(" ", "_")

    if not safe_name:
        safe_name = "product"

    suffix = Path(uploaded_image.name).suffix or ".jpg"
    path = IMAGE_DIR / f"{safe_name}{suffix}"

    path.write_bytes(uploaded_image.getbuffer())
    return str(path)


def build_payload(url, product_name, price, category, image_url, partner_url, uploaded_image):
    image_path = save_uploaded_image(uploaded_image, product_name=product_name)

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

    if image_path:
        payload["image_path"] = image_path
        built["image_path"] = image_path
        built["project_payload"]["image_path"] = image_path
        built["project_payload"].setdefault("data", {})
        built["project_payload"]["data"]["image_path"] = image_path

    return built, payload, image_path


def show_product_ai():
    st.title("🛒 Product AI 2.0")
    st.caption("쿠팡 링크 하나로 프로젝트 생성/수정/검색어 생성을 처리합니다.")
    st.info("쿠팡 자동 이미지 추출은 차단될 수 있어 대표 이미지 URL 또는 이미지 업로드를 지원합니다.")

    url = st.text_input("쿠팡 원본 링크", placeholder="https://www.coupang.com/vp/products/...")
    product_name = st.text_area("상품명 보완", placeholder="상품명을 붙여넣으면 검색어 품질이 올라갑니다.", height=90)
    partner_url = st.text_input("쿠팡파트너스 링크")
    image_url = st.text_input("대표 이미지 URL")
    uploaded_image = st.file_uploader("대표 이미지 파일 업로드", type=["jpg", "jpeg", "png", "webp"])
    price = st.text_input("가격")
    category = st.text_input("카테고리")
    uploaded_video = st.file_uploader("원본 영상 바로 업로드", type=["mp4", "mov", "webm"])

    if uploaded_image:
        st.image(uploaded_image, caption="업로드한 대표 이미지", use_container_width=True)

    built = None
    payload = None

    if url:
        built, payload, _ = build_payload(
            url, product_name, price, category, image_url, partner_url, None
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

        with st.expander("Product Engine JSON"):
            copybox("JSON", json.dumps(built, ensure_ascii=False, indent=2), 420)

    st.divider()
    st.subheader("프로젝트 작업")

    col1, col2 = st.columns(2)

    with col1:
        create_clicked = st.button("🆕 새 프로젝트 생성", use_container_width=True)

    with col2:
        update_clicked = st.button("📝 기존 프로젝트 업데이트", use_container_width=True)

    if create_clicked:
        if not url.strip():
            st.warning("쿠팡 링크를 입력하세요.")
            return

        built, payload, image_path = build_payload(
            url, product_name, price, category, image_url, partner_url, uploaded_image
        )

        existing = ProjectRepository().find_by_coupang_url(payload.get("coupang_url", ""))
        if existing:
            st.warning(f"이미 등록된 프로젝트입니다: {existing.product_name}")
            st.info("수정하려면 '기존 프로젝트 업데이트'를 눌러주세요.")
            return

        video_path = VideoService().save_uploaded_video(uploaded_video) if uploaded_video else ""
        payload["video_path"] = video_path

        project = ProjectService().create_project(payload)
        saved_path = ProductEngine().save_plan(built)

        st.success(f"프로젝트 생성 완료: {project.product_name}")
        st.write("Product Plan 저장:", saved_path)
        if image_path:
            st.write("대표 이미지 저장:", image_path)

    if update_clicked:
        if not url.strip():
            st.warning("쿠팡 링크를 입력하세요.")
            return

        built, payload, image_path = build_payload(
            url, product_name, price, category, image_url, partner_url, uploaded_image
        )

        existing = ProjectRepository().find_by_coupang_url(payload.get("coupang_url", ""))
        if not existing:
            st.warning("기존 프로젝트를 찾을 수 없습니다. 먼저 새 프로젝트를 생성하세요.")
            return

        video_path = VideoService().save_uploaded_video(uploaded_video) if uploaded_video else getattr(existing, "video_path", "")
        payload["video_path"] = video_path
        payload["title"] = payload.get("product_name", "")

        updated = ProjectRepository().update_project(existing.id, payload)
        saved_path = ProductEngine().save_plan(built)

        st.success(f"기존 프로젝트 업데이트 완료: {updated.product_name}")
        st.write("Product Plan 저장:", saved_path)
        if image_path:
            st.write("대표 이미지 저장:", image_path)