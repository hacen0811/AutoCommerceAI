import re


class SearchKeywordEngine:
    """
    Sprint 51
    SearchKeywordEngine 2.0

    목표:
    - 단어 1:1 번역 사전 의존 줄이기
    - 상품명 문맥으로 카테고리 먼저 판단
    - 타오바오 / 1688 / 도우인 검색어를 카테고리별로 안정 생성
    """

    STOPWORDS = {
        "무료배송", "로켓배송", "쿠팡", "정품", "국내배송", "해외배송",
        "특가", "세트", "개입", "개", "입", "팩",
        "1개", "2개", "3개", "4개", "5개", "10개",
        "화이트", "블랙", "그레이", "베이지", "투명",
        "M", "L", "XL", "S",
    }

    CATEGORY_RULES = [
        {
            "category": "insect",
            "match": ["초파리", "모기", "벌레", "날파리", "끈끈이", "방충", "트랩", "퇴치"],
            "base_cn": ["果蝇", "蚊虫", "粘虫板"],
            "ko_main": "벌레 퇴치 끈끈이 트랩",
            "angle": "여름 벌레 차단 / 생활 불편 해결형",
        },
        {
            "category": "drain",
            "match": ["배수구", "하수구", "냄새", "악취", "욕실", "싱크대", "트랩", "차단"],
            "base_cn": ["地漏", "防臭", "下水道"],
            "ko_main": "배수구 냄새 차단 트랩",
            "angle": "욕실·주방 냄새 해결형",
        },
        {
            "category": "kitchen_storage",
            "match": ["주방", "양념", "조미료", "수납", "정리", "선반", "정리대", "슬라이딩", "슬라이드"],
            "base_cn": ["厨房", "收纳", "调料架"],
            "ko_main": "주방 수납 정리대",
            "angle": "주방 정리 Before/After / 살림템 추천형",
        },
        {
            "category": "shoe",
            "match": ["신발", "운동화", "건조", "건조기", "냄새", "습기"],
            "base_cn": ["烘鞋器", "鞋子", "除臭"],
            "ko_main": "신발 건조기",
            "angle": "장마철 냄새/습기 해결형",
        },
        {
            "category": "ice",
            "match": ["얼음", "아이스", "트레이", "보틀", "물병", "텀블러"],
            "base_cn": ["冰格", "冰块", "水壶"],
            "ko_main": "얼음 트레이 보틀",
            "angle": "얼죽아 공감형 / 여름 홈카페",
        },
        {
            "category": "faucet",
            "match": ["수전", "연장", "수도", "세면대", "싱크대", "물튀김"],
            "base_cn": ["水龙头", "延伸器", "防溅"],
            "ko_main": "수전 연장탭",
            "angle": "물튀김 방지 / 생활 불편 해결형",
        },
        {
            "category": "glove",
            "match": ["장갑", "비닐장갑", "일회용", "홀더", "디스펜서"],
            "base_cn": ["一次性手套", "收纳盒", "挂架"],
            "ko_main": "비닐장갑 홀더",
            "angle": "주방 소모품 정리 / 편의성 강조형",
        },
        {
            "category": "travel_pouch",
            "match": ["세면백", "파우치", "여행", "화장품", "수납백"],
            "base_cn": ["洗漱包", "旅行", "收纳包"],
            "ko_main": "여행 세면 파우치",
            "angle": "여행 준비 / 수납 편의형",
        },
        {
            "category": "vegetable_spinner",
            "match": ["야채", "채소", "샐러드", "탈수기", "물기", "펌프식"],
            "base_cn": ["蔬菜脱水器", "沙拉", "按压式"],
            "ko_main": "야채 탈수기",
            "angle": "샐러드 준비 / 주방 시간 단축형",
        },
        {
            "category": "stone",
            "match": ["돌", "돌덩이", "자연석", "조경석", "자갈", "조약돌"],
            "base_cn": ["天然石", "景观石", "鹅卵石"],
            "ko_main": "조경 자연석",
            "angle": "인테리어·조경 소품형",
        },
    ]

    FALLBACK_CN = {
        "무타공": "免打孔",
        "수납형": "收纳",
        "수납": "收纳",
        "정리": "收纳",
        "선반": "置物架",
        "거치대": "支架",
        "걸이": "挂架",
        "홀더": "支架",
        "드라이기": "吹风机",
        "드라이어": "吹风机",
        "헤어드라이기": "吹风机",
        "욕실": "浴室",
        "화장실": "卫生间",
        "벽걸이": "壁挂",
        "부착식": "粘贴式",
        "접착식": "免打孔",
        "대용량": "大容量",
        "다용도": "多功能",
        "휴대용": "便携",
        "가정용": "家用",
        "생활": "家用",
    }

    def generate(self, product_name="", category="", memo=""):
        clean = self.clean(product_name)
        tokens = self.tokens(clean)

        detected = self.detect_category(clean, tokens, category)

        text = " ".join(tokens) + " " + clean

        if any(x in text for x in ["드라이기", "드라이어", "헤어드라이기", "헤어드라이어"]):
            detected = self.fallback_category(clean, tokens)

        cn_base = detected["base_cn"]
        cn_keyword = " ".join(cn_base)

        ko_keyword = self.main_korean_keyword(tokens, clean, detected)

        taobao_top10 = self.taobao_top10(detected, cn_keyword)
        source_1688_top10 = self.source_1688_top10(detected, cn_keyword)
        douyin_top10 = self.douyin_top10(detected, cn_keyword)

        return {
            "clean_name": clean,
            "tokens": tokens,
            "category": detected["category"],
            "category_score": detected["score"],
            "main_keyword": ko_keyword,
            "comment_keyword": self.comment_keyword(tokens, clean, detected),

            "taobao_keyword": taobao_top10[0]["query"] if taobao_top10 else cn_keyword,
            "source_1688_keyword": source_1688_top10[0]["query"] if source_1688_top10 else cn_keyword,
            "douyin_keyword": douyin_top10[0]["query"] if douyin_top10 else f"{cn_keyword} 使用",

            "taobao_top10": taobao_top10,
            "source_1688_top10": source_1688_top10,
            "douyin_top10": douyin_top10,

            "korean_search": ko_keyword,
            "content_angle": detected.get("angle") or self.content_angle(tokens, clean),
        }

    def clean(self, text):
        text = str(text or "")
        text = re.sub(r"\[[^\]]+\]|\([^\)]+\)", " ", text)
        text = re.sub(r"[^\w가-힣\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def tokens(self, clean):
        out = []

        for t in clean.split():
            if t in self.STOPWORDS:
                continue
            if re.match(r"^\d+$", t):
                continue
            if len(t) <= 1:
                continue
            out.append(t)

        return list(dict.fromkeys(out))

    def detect_category(self, clean, tokens, category=""):
        text = " ".join(tokens) + " " + clean + " " + str(category or "")
        scores = []

        for rule in self.CATEGORY_RULES:
            score = 0

            for word in rule["match"]:
                if word in text:
                    score += 1

            if score:
                scores.append((score, rule))

        if scores:
            scores.sort(key=lambda x: x[0], reverse=True)
            score, rule = scores[0]
            result = dict(rule)
            result["score"] = score
            return result

        fallback = self.fallback_category(clean, tokens)
        return fallback

    def fallback_category(self, clean, tokens):
        text = " ".join(tokens) + " " + clean
        cn_tokens = []

        phrase_rules = [
            (["무타공", "드라이기", "거치대"], ["免打孔", "吹风机", "置物架"]),
            (["드라이기", "거치대"], ["吹风机", "支架"]),
            (["욕실", "수납", "거치대"], ["浴室", "收纳", "置物架"]),
            (["무타공", "수납"], ["免打孔", "收纳", "置物架"]),
            (["벽걸이", "거치대"], ["壁挂", "支架"]),
        ]

        for required, cn_words in phrase_rules:
            if all(word in text for word in required):
                cn_tokens.extend(cn_words)

        for token in tokens:
            cn = self.FALLBACK_CN.get(token)
            if cn:
                cn_tokens.append(cn)

        cn_tokens = list(dict.fromkeys(cn_tokens))

        if not cn_tokens:
            cn_tokens = ["家用", "多功能"]

        return {
            "category": "general",
            "match": [],
            "base_cn": cn_tokens[:5],
            "ko_main": " ".join(tokens[:4]) if tokens else "생활용품 추천템",
            "angle": "생활 불편 해결형",
            "score": 0,
        }

    def main_korean_keyword(self, tokens, clean, detected):
        if detected.get("ko_main"):
            return detected["ko_main"]

        return " ".join(tokens[:4]) if tokens else clean or "생활용품"

    def taobao_top10(self, detected, cn_keyword):
        category = detected.get("category")

        if category == "insect":
            queries = [
                ("果蝇 粘虫板", "초파리 끈끈이 상품 정확도 우선", 99),
                ("蚊虫 粘虫板", "모기/날벌레 끈끈이 후보", 97),
                ("果蝇 诱捕器", "초파리 유인 트랩 후보", 95),
                ("家用 粘虫板", "가정용 끈끈이 후보", 93),
                ("厨房 果蝇 诱捕器", "주방 초파리 트랩 후보", 91),
                ("灭蚊 粘虫板", "모기 퇴치 끈끈이 후보", 89),
                ("小飞虫 粘虫板", "날파리 끈끈이 후보", 87),
                ("防虫 粘贴板", "방충 접착판 후보", 85),
                ("果蝇 捕虫器", "포충기형 후보", 83),
                ("家用 捕虫贴", "가정용 벌레 포획 스티커", 81),
            ]
            return self._pack(queries)

        if category == "drain":
            queries = [
                ("地漏 防臭芯", "배수구 냄새 차단 정확도 우선", 99),
                ("下水道 防臭 地漏", "하수구 악취 차단 후보", 97),
                ("厨房 水槽 防臭塞", "싱크대 냄새 차단 후보", 95),
                ("卫生间 地漏 防臭", "욕실 배수구 후보", 93),
                ("地漏 防虫 防臭", "벌레/악취 차단 후보", 91),
                ("下水道 防臭神器", "바이럴형 후보", 89),
                ("水槽 防臭 防虫", "싱크대 벌레 차단 후보", 87),
                ("地漏芯 防臭", "배수구 코어 후보", 85),
                ("地漏 硅胶 防臭", "실리콘 구조 후보", 83),
                ("排水口 防臭塞", "배수구 마개 후보", 81),
            ]
            return self._pack(queries)

        if category == "kitchen_storage":
            queries = [
                ("厨房 收纳 调料架", "주방 정리 정확도 우선", 99),
                ("厨房 抽拉式 调料收纳架", "슬라이딩 양념 정리대", 97),
                ("厨房 调味料置物架", "조미료 선반형 후보", 95),
                ("厨房 多层收纳架", "다층 정리대 후보", 93),
                ("厨房 台面收纳架", "상판 정리대 후보", 91),
                ("厨房 收纳神器", "바이럴형 후보", 89),
                ("厨房 置物架", "넓은 상품 후보", 87),
                ("调料盒 收纳架", "양념통 정리 후보", 85),
                ("厨房 抽屉式收纳", "서랍형 후보", 83),
                ("厨房 调料架 新款", "신상품 후보", 81),
            ]
            return self._pack(queries)

        return self.generic_top10(cn_keyword, platform="taobao")

    def source_1688_top10(self, detected, cn_keyword):
        category = detected.get("category")

        if category == "insect":
            queries = [
                ("果蝇 粘虫板 批发", "1688 초파리 끈끈이 도매", 99),
                ("蚊虫 粘虫板 厂家", "제조사 후보", 97),
                ("捕虫贴 源头工厂", "소스 공장 후보", 95),
                ("家用 粘虫板 批发", "가정용 도매 후보", 93),
                ("果蝇 诱捕器 厂家", "초파리 트랩 제조사", 91),
                ("灭蚊 粘虫板 批发", "모기 퇴치 도매", 89),
                ("小飞虫 粘虫板 厂家", "날파리 끈끈이 제조사", 87),
                ("防虫 粘贴板 批发", "방충 접착판 도매", 85),
                ("捕虫器 一件代发", "위탁/대행 후보", 83),
                ("粘虫板 跨境", "해외판매 후보", 81),
            ]
            return self._pack(queries)

        if category == "drain":
            queries = [
                ("地漏 防臭芯 批发", "1688 배수구 도매 정확도 우선", 99),
                ("下水道 防臭 地漏 厂家", "제조사 후보", 97),
                ("地漏芯 源头工厂", "소스 공장 후보", 95),
                ("水槽 防臭塞 批发", "싱크대 냄새 차단 도매", 93),
                ("卫生间 地漏 防臭 厂家", "욕실 배수구 제조사", 91),
                ("地漏 防虫 防臭 批发", "벌레/악취 차단 도매", 89),
                ("排水口 防臭塞 厂家", "배수구 마개 제조사", 87),
                ("地漏 硅胶 防臭 批发", "실리콘 구조 도매", 85),
                ("下水道 防臭神器 一件代发", "위탁/대행 후보", 83),
                ("地漏芯 跨境", "해외판매 후보", 81),
            ]
            return self._pack(queries)

        if category == "kitchen_storage":
            queries = [
                ("厨房 收纳 调料架 批发", "1688 주방정리 도매", 99),
                ("厨房 调料收纳架 厂家", "공장/제조사 후보", 97),
                ("抽拉式 调料架 批发", "슬라이딩 양념대 도매", 95),
                ("厨房 置物架 源头工厂", "소스 공장 후보", 93),
                ("厨房 多层收纳架 批发", "다층형 도매 후보", 91),
                ("厨房 收纳架 一件代发", "위탁/대행 가능 후보", 89),
                ("调料盒 收纳架 厂家", "양념통 정리 제조사", 87),
                ("厨房 收纳神器 批发", "바이럴 상품 도매", 85),
                ("厨房 台面收纳架 现货", "재고 보유 후보", 83),
                ("厨房 置物架 跨境", "해외판매 후보", 81),
            ]
            return self._pack(queries)

        return self.generic_top10(cn_keyword, platform="1688")

    def douyin_top10(self, detected, cn_keyword):
        category = detected.get("category")

        if category == "insect":
            queries = [
                ("果蝇 粘虫板", "초파리 끈끈이 사용 장면", 98),
                ("厨房 果蝇 诱捕器 使用", "주방 초파리 트랩 사용", 96),
                ("蚊虫 粘虫板 测评", "모기/벌레 끈끈이 리뷰", 94),
                ("小飞虫 粘虫板 推荐", "날파리 추천 영상", 92),
                ("夏天 防虫 好物", "여름 방충 쇼핑쇼츠", 90),
                ("灭蚊 粘虫板 效果", "효과 장면", 88),
                ("家用 捕虫贴 开箱", "언박싱", 86),
                ("果蝇 诱捕器 对比", "Before/After 비교", 84),
                ("厨房 小飞虫 解决", "문제 해결형 영상", 82),
                ("防虫神器", "후킹 강한 영상", 80),
            ]
            return self._pack(queries)

        if category == "drain":
            queries = [
                ("地漏 防臭 使用", "배수구 냄새 차단 사용 장면", 98),
                ("下水道 防臭 测评", "하수구 악취 리뷰", 96),
                ("卫生间 地漏 防臭 推荐", "욕실 추천형 영상", 94),
                ("厨房 水槽 防臭 效果", "싱크대 효과 장면", 92),
                ("地漏 防虫 防臭", "벌레/악취 차단 영상", 90),
                ("下水道 防臭神器", "후킹 강한 영상", 88),
                ("地漏芯 安装", "설치 장면", 86),
                ("排水口 防臭 对比", "Before/After 비교", 84),
                ("卫生间 除臭 好物", "쇼핑쇼츠 후보", 82),
                ("地漏 防臭 开箱", "언박싱", 80),
            ]
            return self._pack(queries)

        if category == "kitchen_storage":
            queries = [
                ("厨房 收纳 调料架", "주방정리 기본 영상", 98),
                ("厨房 抽拉式 调料收纳架 使用", "슬라이딩 사용 장면", 96),
                ("厨房 调料收纳架 测评", "리뷰/체험 영상", 94),
                ("厨房 收纳神器", "후킹 강한 영상", 92),
                ("厨房 收纳 改造", "Before/After", 90),
                ("厨房 调料架 推荐", "추천형 영상", 88),
                ("厨房 台面收纳 效果", "효과 장면", 86),
                ("厨房 置物架 开箱", "언박싱", 84),
                ("厨房 收纳技巧", "생활꿀팁형", 82),
                ("厨房 好物", "쇼핑쇼츠 후보", 80),
            ]
            return self._pack(queries)

        return self.generic_top10(cn_keyword, platform="douyin")

    def generic_top10(self, cn_keyword, platform="taobao"):
        if platform == "1688":
            suffixes = ["批发", "厂家", "源头工厂", "一件代发", "跨境", "现货", "新款", "家用", "多功能", "供应商"]
        elif platform == "douyin":
            suffixes = ["使用", "测评", "推荐", "好物", "神器", "对比", "安装", "开箱", "效果", "教程"]
        else:
            suffixes = ["", "家用", "多功能", "神器", "收纳", "安装", "新款", "同款"]

        return self._pack([
            (f"{cn_keyword} {s}".strip(), self._purpose(s), 96 - i * 3)
            for i, s in enumerate(suffixes)
            if cn_keyword
        ])

    def _pack(self, items):
        return [
            {
                "rank": i + 1,
                "query": q,
                "purpose": p,
                "score": s,
            }
            for i, (q, p, s) in enumerate(items)
        ]

    def _purpose(self, suffix):
        return {
            "": "기본 검색",
            "安装": "설치 장면",
            "使用": "사용 장면",
            "测评": "리뷰 영상",
            "推荐": "추천 영상",
            "好物": "쇼핑쇼츠 후보",
            "神器": "후킹 강한 영상",
            "收纳": "정리 장면",
            "家用": "생활 사용 장면",
            "多功能": "기능 설명",
            "开箱": "언박싱",
            "效果": "효과 장면",
            "对比": "Before/After",
            "新款": "신상품 후보",
            "批发": "도매 후보",
            "厂家": "제조사 후보",
            "源头工厂": "소스 공장 후보",
            "一件代发": "위탁/대행 후보",
            "跨境": "해외판매 후보",
            "现货": "재고 보유 후보",
            "供应商": "공급업체 후보",
            "同款": "동일/유사 상품",
        }.get(suffix, "검색 후보")

    def comment_keyword(self, tokens, clean, detected):
        category = detected.get("category")

        if category == "insect":
            return "벌레퇴치"
        if category == "drain":
            return "냄새차단"
        if category == "kitchen_storage":
            return "정리"
        if category == "shoe":
            return "신발"
        if category == "ice":
            return "얼음"
        if category == "vegetable_spinner":
            return "야채탈수기"

        return tokens[0] if tokens else "정보"

    def content_angle(self, tokens, clean):
        text = " ".join(tokens) + " " + clean

        if any(k in text for k in ["주방", "양념", "수납", "정리"]):
            return "주방 정리 Before/After / 살림템 추천형"
        if any(k in text for k in ["방충", "모기", "초파리", "벌레", "끈끈이"]):
            return "여름 벌레 차단 / 생활 불편 해결형"
        if any(k in text for k in ["신발", "건조"]):
            return "장마철 냄새/습기 해결형"
        if any(k in text for k in ["배수구", "하수구", "냄새"]):
            return "욕실·주방 냄새 해결형"
        if any(k in text for k in ["얼음", "아이스", "보틀"]):
            return "얼죽아 공감형 / 여름 홈카페"

        return "생활 불편 해결형"