def analyze_product(product_name="", source_query=""):
    """
    Sprint 17-1
    상품명/검색어 기반 간단 상품 분석기.
    GPT 없이 규칙 기반으로 먼저 안정화.
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
        })

    elif any(k in text for k in ["수전", "세면대", "연장", "탭"]):
        profile.update({
            "category": "욕실/세면대",
            "usage_place": "욕실, 세면대",
            "keyword": "수전",
            "problem": "물줄기가 짧아서 손 씻기나 세면대 청소가 불편한 순간",
            "solution": "물줄기 방향을 편하게 바꿔주는 아이템",
            "benefit": "손 씻기와 세면대 청소가 훨씬 편해져요",
            "features": ["각도 조절", "물튀김 감소", "간편 설치"],
            "scene": "세면대 사용 전 / 물줄기 조절 / 청소 장면",
        })

    elif any(k in text for k in ["얼음", "트레이", "아이스", "보틀"]):
        profile.update({
            "category": "주방/홈카페",
            "usage_place": "주방, 냉동실",
            "keyword": "얼음",
            "problem": "얼음 얼리고 빼는 과정이 매번 귀찮은 순간",
            "solution": "얼음을 더 편하게 만들고 꺼낼 수 있는 아이템",
            "benefit": "홈카페 준비가 훨씬 간단해져요",
            "features": ["간편 분리", "공간 절약", "홈카페 활용"],
            "scene": "냉동실 / 얼음 분리 / 컵에 담는 장면",
        })

    return profile