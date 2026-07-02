import json
from pathlib import Path

import streamlit as st

from modules.content.content_factory import ContentFactory

ANALYSIS_DIR = Path("exports/product_analysis")


def safe_text(value, default=""):
    if value is None:
        return default
    return str(value).strip()


def build_basic_product_analysis(selected_sources):
    main = selected_sources[0] if selected_sources else {}

    query = safe_text(main.get("query"), "선택 상품")
    platform = safe_text(main.get("platform"), "-")
    purpose = safe_text(main.get("purpose"), "-")
    score = safe_text(main.get("score"), "-")
    url = safe_text(main.get("url"), "")

    return {
        "product_name": query,
        "platform": platform,
        "purpose": purpose,
        "score": score,
        "url": url,
        "usp": [
            f"{query} 관련 문제를 빠르게 해결해주는 상품",
            "쇼츠에서 Before / After 구조로 보여주기 좋음",
            "생활 불편함을 공감형으로 풀기 좋음",
        ],
        "target": [
            "살림템에 관심 있는 20~40대",
            "생활 불편을 줄이고 싶은 사용자",
            "쇼핑쇼츠에서 실용템을 찾는 시청자",
        ],
        "buying_points": [
            "사용 전후 차이를 보여주기 쉬움",
            "짧은 영상에서 기능을 직관적으로 설명 가능",
            "댓글 CTA로 연결하기 좋음",
        ],
        "shorts_angles": [
            "공감형 쇼츠",
            "Before / After 쇼츠",
            "생활꿀팁형 쇼츠",
            "문제 해결형 쇼츠",
            "리뷰형 쇼츠",
        ],
        "hooks": [
            f"아직도 {query} 없이 불편하게 쓰세요?",
            "이거 하나로 생활이 훨씬 편해집니다",
            "왜 이제 알았지 싶은 살림템",
            "써보기 전엔 몰랐던 차이",
            "살림 시간이 줄어드는 이유",
        ],
    }


def save_product_analysis(project, analysis):
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    project_id = str(getattr(project, "id", "project")).replace(" ", "_")
    path = ANALYSIS_DIR / f"{project_id}_analysis.json"
    path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def show_ai_product_analysis(project, selected_sources):
    st.divider()
    st.subheader("🧠 AI 상품 분석")

    if not selected_sources:
        st.info("먼저 후보 상품을 선택해주세요.")
        return None

    if st.button("🧠 AI 상품 분석 생성", key=f"ai_product_analysis_{project.id}", use_container_width=True):
        analysis = build_basic_product_analysis(selected_sources)
        path = save_product_analysis(project, analysis)

        st.session_state[f"ai_product_analysis_result_{project.id}"] = analysis
        st.success(f"AI 상품 분석을 저장했습니다: {path}")

    analysis = st.session_state.get(f"ai_product_analysis_result_{project.id}")

    if not analysis:
        return None

    st.markdown("### 상품 요약")
    st.write(f"상품명/검색어: {analysis.get('product_name')}")
    st.write(f"플랫폼: {analysis.get('platform')}")
    st.write(f"목적: {analysis.get('purpose')}")
    st.write(f"점수: {analysis.get('score')}")

    if analysis.get("url"):
        st.link_button("상품/검색 링크 열기", analysis.get("url"), use_container_width=True)

    st.markdown("### USP")
    for item in analysis.get("usp", []):
        st.write(f"- {item}")

    st.markdown("### 타겟")
    for item in analysis.get("target", []):
        st.write(f"- {item}")

    st.markdown("### 구매 포인트")
    for item in analysis.get("buying_points", []):
        st.write(f"- {item}")

    st.markdown("### 추천 쇼츠 방향")
    for item in analysis.get("shorts_angles", []):
        st.write(f"- {item}")

    st.markdown("### 후킹 문구")
    for item in analysis.get("hooks", []):
        st.write(f"- {item}")

    return analysis