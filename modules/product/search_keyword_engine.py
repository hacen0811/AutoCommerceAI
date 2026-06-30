import re


class SearchKeywordEngine:
    KO_TO_CN = {
        "주방": "厨房",
        "정리대": "收纳架",
        "양념통": "调料",
        "양념": "调料",
        "조미료": "调味料",
        "코너": "角落",
        "슬라이딩": "抽拉式",
        "수납장": "收纳柜",
        "다층": "多层",
        "선반": "置物架",
        "조리도구": "厨具",
        "걸이": "挂钩",
        "냄비뚜껑": "锅盖",
        "거치대": "架",
        "문틈": "门缝",
        "방충망": "防蚊纱窗",
        "모기장": "蚊帐",
        "신발": "鞋",
        "건조기": "烘干器",
        "신발건조기": "烘鞋器",
        "배수구": "地漏",
        "냄새": "防臭",
        "차단": "防臭",
        "트랩": "地漏防臭芯",
        "얼음": "冰块",
        "트레이": "冰格",
        "보틀": "水壶",
        "수전": "水龙头",
        "연장": "延伸器",
        "비닐장갑": "一次性手套",
        "장갑": "手套",
        "홀더": "收纳架",
        "세면백": "洗漱包",
        "파우치": "收纳包",
        "여행": "旅行",
        "욕실": "浴室",
        "싱크대": "水槽",
        "거름망": "过滤网",
    }

    STOPWORDS = {
        "무료배송", "로켓배송", "쿠팡", "정품", "국내배송", "해외배송",
        "대용량", "특가", "세트", "개입", "개", "입", "팩", "1개", "2개",
        "화이트", "블랙", "M", "L", "XL",
    }

    def generate(self, product_name="", category="", memo=""):
        clean = self.clean(product_name)
        tokens = self.tokens(clean)
        ko_keyword = self.main_korean_keyword(tokens, clean)
        cn_keyword = self.main_chinese_keyword(tokens, clean)

        taobao_top10 = self.taobao_top10(tokens, clean, cn_keyword)
        douyin_top10 = self.douyin_top10(tokens, clean, cn_keyword)

        return {
            "clean_name": clean,
            "tokens": tokens,
            "main_keyword": ko_keyword,
            "comment_keyword": self.comment_keyword(tokens, clean),
            "taobao_keyword": taobao_top10[0]["query"] if taobao_top10 else cn_keyword,
            "douyin_keyword": douyin_top10[0]["query"] if douyin_top10 else f"{cn_keyword} 使用",
            "taobao_top10": taobao_top10,
            "douyin_top10": douyin_top10,
            "korean_search": ko_keyword,
            "content_angle": self.content_angle(tokens, clean),
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

        joined = "".join(out)
        if "주방" in joined and "양념" in joined and "정리" in joined:
            out.insert(0, "주방")
            out.insert(1, "양념통")
            out.insert(2, "정리대")
        if "슬라이딩" in joined or "슬라이드" in joined:
            out.insert(0, "슬라이딩")
        if "냄비" in joined and "뚜껑" in joined:
            out.insert(0, "냄비뚜껑")
        if "신발" in joined and "건조" in joined:
            out.insert(0, "신발건조기")
        if "방충" in joined:
            out.insert(0, "방충망")
        return list(dict.fromkeys(out))

    def main_korean_keyword(self, tokens, clean):
        if all(k in clean for k in ["주방", "양념"]):
            return "주방 양념통 정리대"
        if "슬라이딩" in tokens and "수납장" in tokens:
            return "주방 슬라이딩 수납장"
        return " ".join(tokens[:4]) if tokens else clean or "생활용품"

    def main_chinese_keyword(self, tokens, clean):
        if all(k in clean for k in ["주방", "양념"]):
            if "슬라이딩" in tokens or "슬라이딩" in clean:
                return "厨房 调料收纳架 抽拉式"
            return "厨房 调料收纳架"
        cn_tokens = [self.KO_TO_CN.get(t, "") for t in tokens]
        cn_tokens = [t for t in cn_tokens if t]
        return " ".join(cn_tokens[:4]) if cn_tokens else self.fallback_cn(clean)

    def taobao_top10(self, tokens, clean, cn_keyword):
        if all(k in clean for k in ["주방", "양념"]):
            queries = [
                ("厨房 调料收纳架 抽拉式", "슬라이딩 사용 장면 찾기", 98),
                ("厨房 调味料收纳架", "양념통 정리대 기본 검색", 95),
                ("厨房 滑轨收纳架", "레일/슬라이딩 구조 영상", 92),
                ("厨房 收纳柜 抽拉", "수납장형 상품 후보", 90),
                ("厨房 多层置物架", "다층 선반 구조", 86),
                ("厨房 调料架", "넓은 후보 검색", 84),
                ("厨房 收纳架 带挂钩", "조리도구 걸이 장면", 82),
                ("锅盖收纳架 厨房", "냄비뚜껑 거치 장면", 80),
                ("厨房 台面收纳架", "주방 상판 정리 장면", 78),
                ("厨房 调料置物架", "양념 선반 후보", 76),
            ]
            return self._pack(queries)
        base = cn_keyword or self.main_chinese_keyword(tokens, clean)
        suffixes = ["", "安装", "使用", "推荐", "测评", "神器", "收纳", "家用", "多功能", "开箱"]
        return self._pack([(f"{base} {s}".strip(), self._purpose(s), 95 - i*3) for i, s in enumerate(suffixes)])

    def douyin_top10(self, tokens, clean, cn_keyword):
        if all(k in clean for k in ["주방", "양념"]):
            queries = [
                ("厨房 调料收纳架", "기본 바이럴 영상", 98),
                ("厨房 调料收纳架 使用", "사용 장면", 96),
                ("厨房 调料收纳架 测评", "리뷰/체험 영상", 94),
                ("厨房 调料收纳架 推荐", "추천형 영상", 92),
                ("厨房 调料收纳架 好物", "쇼핑쇼츠용 好物 영상", 90),
                ("厨房 收纳神器", "주방 정리 후킹 영상", 88),
                ("厨房 收纳 改造", "Before/After", 86),
                ("厨房 收纳 对比", "비교 영상", 84),
                ("厨房 调料架 开箱", "언박싱", 80),
                ("厨房 收纳技巧", "생활꿀팁형", 78),
            ]
            return self._pack(queries)
        base = cn_keyword or self.main_chinese_keyword(tokens, clean)
        suffixes = ["", "使用", "测评", "推荐", "好物", "神器", "对比", "安装", "开箱", "效果"]
        return self._pack([(f"{base} {s}".strip(), self._purpose(s), 95 - i*3) for i, s in enumerate(suffixes)])

    def _pack(self, items):
        return [{"rank": i + 1, "query": q, "purpose": p, "score": s} for i, (q, p, s) in enumerate(items)]

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
        }.get(suffix, "검색 후보")

    def fallback_cn(self, clean):
        for ko, cn in self.KO_TO_CN.items():
            if ko in clean:
                return cn
        return ""

    def comment_keyword(self, tokens, clean):
        if all(k in clean for k in ["주방", "양념"]):
            return "정리"
        for preferred in ["방충망", "신발건조기", "배수구", "얼음", "수전", "장갑", "파우치"]:
            if preferred in tokens or preferred in clean:
                return preferred.replace("신발건조기", "신발")
        return tokens[0] if tokens else "정보"

    def content_angle(self, tokens, clean):
        text = " ".join(tokens) + " " + clean
        if any(k in text for k in ["주방", "양념", "수납", "정리"]):
            return "주방 정리 Before/After / 살림템 추천형"
        if any(k in text for k in ["방충", "모기", "문틈"]):
            return "여름 벌레 차단 / 생활 불편 해결형"
        if any(k in text for k in ["신발", "건조"]):
            return "장마철 냄새/습기 해결형"
        if any(k in text for k in ["배수구", "냄새", "트랩"]):
            return "욕실·주방 냄새 해결형"
        if any(k in text for k in ["얼음", "아이스"]):
            return "얼죽아 공감형 / 여름 홈카페"
        return "생활 불편 해결형"
