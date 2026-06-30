import json
import os
import streamlit as st

from modules.studio.studio_pipeline_engine import StudioPipelineEngine
from app.ui.render import copybox


def show_shorts_studio():
    st.title("🎞️ 쇼츠 스튜디오 3.0")
    st.caption("쿠팡 링크 + 상품명 + 원본 영상으로 쇼핑쇼츠 제작 패키지를 생성합니다.")
    st.info("DB가 없어도 여기서 새 프로젝트를 만들고, 검색어/대본/CapCut/업로드 문구까지 한 번에 생성할 수 있습니다.")
    st.caption("4.0: Playwright 준비 시 도우인/타오바오/1688 실제 검색 후보 수집을 시도합니다.")

    coupang_url = st.text_area("쿠팡 링크", height=80, placeholder="https://www.coupang.com/vp/products/...")
    product_name = st.text_area("상품명", height=110, placeholder="쿠팡 상품명 전체를 붙여넣어 주세요.")
    uploaded_video = st.file_uploader("원본 영상", type=["mp4", "mov", "webm"])
    c1, c2 = st.columns(2)
    price = c1.text_input("가격")
    category = c2.text_input("카테고리")
    image_url = st.text_input("대표 이미지 URL")
    partner_url = st.text_input("쿠팡파트너스 링크")

    st.subheader("실행 옵션")
    run_one_click = st.checkbox("쇼핑쇼츠 패키지 생성 후 원클릭 파이프라인까지 실행", value=True)
    sample_count = st.slider("Vision 분석 프레임 수", min_value=3, max_value=12, value=6)
    live_collect = st.checkbox("실제 웹 수집 시도(도우인/타오바오/1688)", value=False)
    if live_collect:
        st.warning("실제 웹 수집은 사이트 로그인/차단 상태에 따라 결과가 비어 있을 수 있습니다. 처음에는 브라우저가 열릴 수 있습니다.")

    if st.button("쇼핑쇼츠 패키지 생성", use_container_width=True):
        os.environ["AUTO_SOURCE_LIVE"] = "1" if live_collect else "0"
        with st.spinner("쇼핑쇼츠 패키지와 원클릭 결과를 생성 중입니다..."):
            result = StudioPipelineEngine().run(coupang_url, product_name, uploaded_video, price, category, image_url, partner_url, run_one_click, sample_count)

        if not result.get("ok"):
            st.error(result.get("message", "생성 실패"))
            copybox("오류 JSON", json.dumps(result, ensure_ascii=False, indent=2, default=str), 300)
            return

        package = result.get("package", {})
        product = package.get("product", {})
        st.success("쇼핑쇼츠 패키지 생성 완료")
        st.write("프로젝트:", package.get("project", {}).get("name"))
        ai_status = package.get("ai_status", {})
        if package.get("ai_applied"):
            st.success(f"실제 AI 적용됨: {ai_status.get('mode')}")
        else:
            st.warning(f"AI API 미연결 또는 실패: {ai_status.get('message') or ai_status.get('mode')}")
        if result.get("exports"):
            st.info("최종 결과가 exports/studio_pipeline 폴더에 저장되었습니다.")
            st.write(result.get("exports"))

        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs(["검색어", "영상후보", "대본", "CapCut", "썸네일", "업로드 문구", "원클릭 결과", "Vision", "AI상태", "쿠팡분석", "전체 JSON"])
        with tab1:
            copybox("타오바오", product.get("taobao_keyword", ""), 80)
            copybox("도우인", product.get("douyin_keyword", ""), 80)
            st.subheader("타오바오 TOP10")
            for item in product.get("taobao_top10", []):
                st.write(f"{item.get('rank')}. {item.get('query')} — {item.get('purpose')} / {item.get('score')}")
            st.subheader("도우인 TOP10")
            for item in product.get("douyin_top10", []):
                st.write(f"{item.get('rank')}. {item.get('query')} — {item.get('purpose')} / {item.get('score')}")
            st.subheader("검색 URL")
            for k, v in product.get("search_urls", {}).items():
                if v:
                    st.write(f"{k}: {v}")
        with tab2:
            sources = package.get("video_sources", {})
            st.subheader("영상 후보 TOP5")
            st.write("상태:", sources.get("summary", ""))
            st.write("저장 폴더:", sources.get("save_folder", ""))
            auto = sources.get("automation_status", {})
            st.info(auto.get("message", ""))
            if auto.get("install_command"):
                copybox("Playwright 설치 명령어", auto.get("install_command"), 80)
            if auto.get("enable_command"):
                copybox("실제 수집 켜기 명령어", auto.get("enable_command"), 80)
            live = sources.get("live_collection", {})
            st.subheader("실제 웹 수집 결과")
            st.write(live.get("message", "실제 수집 미실행"))
            if live.get("save_path"):
                st.write("저장 파일:", live.get("save_path"))
            for item in live.get("results", [])[:10]:
                st.markdown(f"**[{item.get('platform')}] {item.get('score')}점**")
                st.write(item.get("title"))
                st.write(item.get("url"))
            if live.get("errors"):
                with st.expander("수집 오류/차단 기록"):
                    st.json(live.get("errors"))
            st.divider()
            for item in sources.get("best_candidates", []):
                st.markdown(f"### {item.get('rank')}. {item.get('platform')} / {item.get('score')}점")
                st.write(item.get("title"))
                st.write("목적:", item.get("purpose"))
                st.write("검색어:", item.get("keyword"))
                st.write(item.get("search_url"))
                st.caption(item.get("note", ""))
            st.subheader("전체 후보")
            for item in sources.get("candidates", []):
                st.write(f"{item.get('rank')}. [{item.get('platform')}] {item.get('title')} — {item.get('purpose')} / {item.get('score')}")
            copybox("영상 후보 JSON", json.dumps(sources, ensure_ascii=False, indent=2, default=str), 420)
        with tab3:
            scripts = package.get("scripts", {})
            st.subheader("15초 대본")
            for item in scripts.get("15s", []):
                st.write(f"**{item.get('time')} / {item.get('role')}**")
                st.write(item.get("line"))
            st.subheader("25초 대본")
            for item in scripts.get("25s", []):
                st.write(f"**{item.get('time')} / {item.get('role')}**")
                st.write(item.get("line"))
            st.subheader("35초 대본")
            for item in scripts.get("35s", []):
                st.write(f"**{item.get('time')} / {item.get('role')}**")
                st.write(item.get("line"))
        with tab4:
            capcut = package.get("capcut", {})
            st.write("음성:", capcut.get("voice"))
            st.write("BGM:", capcut.get("bgm"))
            st.write("자막:", capcut.get("subtitle"))
            for item in capcut.get("timeline", []):
                st.write(f"**{item.get('time')}** {item.get('edit')}")
            copybox("CapCut Draft JSON", json.dumps(capcut.get("draft_json", {}), ensure_ascii=False, indent=2, default=str), 260)
        with tab5:
            thumb = package.get("thumbnail", {})
            st.write("메인 문구:", thumb.get("main_text"))
            st.write("보조 문구:", thumb.get("sub_text"))
            st.write("구성:", thumb.get("composition"))
            st.write("크기:", thumb.get("size"))
        with tab6:
            yt = package.get("youtube", {})
            copybox("유튜브 제목", yt.get("title", ""), 80)
            copybox("유튜브 설명", yt.get("description", ""), 220)
            copybox("유튜브 해시태그", yt.get("hashtags", ""), 100)
            ig = package.get("instagram", {})
            copybox("인스타 본문", ig.get("caption", ""), 220)
            copybox("인스타 해시태그", ig.get("hashtags", ""), 100)
        with tab7:
            pipeline = result.get("pipeline")
            if pipeline:
                copybox("원클릭 파이프라인 결과", json.dumps(pipeline, ensure_ascii=False, indent=2, default=str), 520)
            else:
                st.info("원클릭 파이프라인은 실행하지 않았습니다.")
        with tab8:
            vision = package.get("vision", {})
            st.write("요약:", vision.get("summary"))
            copybox("Vision JSON", json.dumps(vision, ensure_ascii=False, indent=2, default=str), 420)
        with tab9:
            copybox("AI 상태", json.dumps(package.get("ai_status", {}), ensure_ascii=False, indent=2, default=str), 200)
            copybox("AI 원본 결과", json.dumps(package.get("ai_generated", {}), ensure_ascii=False, indent=2, default=str), 420)
        with tab10:
            coupang = product.get("coupang", {})
            st.write("자동 분석:", "성공" if coupang.get("auto_fetched") else "입력값/URL 기반")
            st.write("상태:", coupang.get("fetch_status"))
            st.write("상품명:", coupang.get("product_name"))
            st.write("가격:", coupang.get("price"))
            st.write("대표 이미지:", coupang.get("image_url"))
            st.write("상품 ID:", coupang.get("product_id"))
            st.write("itemId:", coupang.get("item_id"))
            st.write("vendorItemId:", coupang.get("vendor_item_id"))
            if coupang.get("features"):
                st.subheader("특징 후보")
                for row in coupang.get("features", []):
                    st.write("-", row)
            copybox("쿠팡 분석 JSON", json.dumps(coupang, ensure_ascii=False, indent=2, default=str), 420)
        with tab11:
            copybox("전체 결과 JSON", json.dumps(result, ensure_ascii=False, indent=2, default=str), 520)
