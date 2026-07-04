def analyze_product(product_name="", source_query=""):
    """
    Sprint 17-2
    상품명/검색어 기반 상품 분석기.
    콘텐츠 생성에 바로 쓸 수 있는 hook/problem/benefit/scene 후보까지 반환.
    """
    name = str(product_name or "")
    query = str(source_query or "")
    text = f"{name} {query}".lower()

    profile = {
        "category": "생활용품",
        "usage_place": "생활 공간",
        "keyword": "제품",
        "problem": "매일 쓰는 물건인데 은근 불편함이 반복되는 순간",
        "solution": "생활 속 작은 불편을 줄여주는 아이템",
        "benefit": "반복되는 귀찮음이 줄어 생활이 조금 더 편해져요",
        "features": ["간편 사용", "정리 효과", "생활 편의"],
        "scene": "생활 공간 / 제품 사용 전후",
        "hook_candidates": [
            "아직도 이 불편함을 그냥 참고 계세요?",
            "매일 쓰는 물건인데 은근 불편하지 않으세요?",
            "이거 하나로 반복되는 귀찮음이 줄어듭니다.",
        ],
        "problem_candidates": [
            "쓸 때마다 불편한데 그냥 참고 쓰게 됩니다.",
            "작은 불편이 반복되면 은근 스트레스가 됩니다.",
        ],
        "benefit_candidates": [
            "생활 동선이 조금 더 편해집니다.",
            "반복되는 귀찮음이 줄어듭니다.",
        ],
        "scene_candidates": [
            "사용 전 불편한 장면",
            "제품 첫 등장",
            "사용 후 달라진 장면",
        ],
    }

    if any(k in text for k in ["정리", "수납", "슬라이딩", "서랍", "선반", "보관", "抽拉"]):
        profile.update({
            "category": "수납/정리",
            "usage_place": "싱크대 밑, 수납장, 화장대, 책상 아래",
            "keyword": "정리",
            "problem": "안쪽 물건 꺼내려고 앞에 있는 것까지 다 꺼내야 하는 순간",
            "solution": "슬라이딩 방식으로 안쪽 물건까지 쉽게 꺼낼 수 있는 정리 아이템",
            "benefit": "깊은 공간도 버리지 않고 깔끔하게 활용할 수 있어요",
            "features": ["슬라이딩 수납", "공간 활용", "정리 시간 단축"],
            "scene": "싱크대 밑 정리 전 / 슬라이딩으로 꺼내는 장면 / 정리 후",
            "hook_candidates": [
                "싱크대 밑, 아직도 다 꺼내고 찾으세요?",
                "안쪽 물건 꺼내려면 앞에 있는 것부터 치우시나요?",
                "정리했는데도 왜 금방 어질러질까요?",
                "깊은 수납장, 그냥 방치하고 계셨나요?",
                "꺼내기 힘든 안쪽 공간, 이제 이렇게 써보세요.",
            ],
            "problem_candidates": [
                "깊숙한 곳에 넣어둔 물건은 꺼내기가 너무 불편합니다.",
                "정리해도 안쪽 물건은 금방 잊혀지고 다시 어질러집니다.",
                "공간은 있는데 제대로 활용하지 못하는 경우가 많습니다.",
            ],
            "benefit_candidates": [
                "슬라이딩으로 안쪽 물건까지 한 번에 꺼낼 수 있습니다.",
                "버려지던 깊은 공간까지 깔끔하게 활용할 수 있습니다.",
                "찾는 시간과 정리 시간이 함께 줄어듭니다.",
            ],
            "scene_candidates": [
                "싱크대 밑 어지러운 수납장 보여주기",
                "앞 물건을 하나씩 꺼내는 불편한 장면",
                "슬라이딩 정리함을 앞으로 당기는 장면",
                "세제/양념/소품이 한눈에 보이는 장면",
                "정리 전후 Before / After 비교",
            ],
        })

    elif any(k in text for k in ["건조", "신발", "운동화", "제습"]):
        profile.update({
            "category": "신발 관리",
            "usage_place": "현관, 세탁실",
            "keyword": "신발",
            "problem": "젖은 신발이나 냄새나는 운동화 때문에 신경 쓰이는 순간",
            "solution": "신발 안쪽 습기와 냄새를 관리해주는 아이템",
            "benefit": "비 오는 날이나 운동 후에도 신발을 더 깔끔하게 관리할 수 있어요",
            "features": ["습기 관리", "냄새 관리", "간편 사용"],
            "scene": "젖은 신발 / 제품 사용 / 건조 후",
            "hook_candidates": [
                "비 온 날 젖은 신발, 그냥 말리고 계세요?",
                "운동화 냄새 때문에 신경 쓰인 적 있으시죠?",
                "신발 안쪽 습기, 생각보다 오래 남습니다.",
            ],
            "problem_candidates": [
                "젖은 신발은 잘 마르지 않고 냄새까지 남기 쉽습니다.",
                "운동 후 신발 안쪽 습기가 오래 남으면 찝찝합니다.",
            ],
            "benefit_candidates": [
                "신발 안쪽까지 더 깔끔하게 관리할 수 있습니다.",
                "비 오는 날에도 신발 관리가 훨씬 쉬워집니다.",
            ],
            "scene_candidates": [
                "젖은 운동화 클로즈업",
                "제품을 신발 안에 넣는 장면",
                "사용 후 신발을 다시 신는 장면",
            ],
        })

    return profile

def show_real_vision_runner():
    import streamlit as st

    st.subheader("YOLO 비전")
    st.info("Real Vision Runner 화면은 현재 준비 중입니다.")