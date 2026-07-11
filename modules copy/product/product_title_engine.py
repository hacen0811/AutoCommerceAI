import re


class ProductTitleEngine:
    """
    쿠팡에서 상품명을 자동 수집하지 못했을 때도
    사용자가 입력한 긴 상품명을 쇼핑쇼츠용 핵심 상품명으로 정리합니다.
    """

    BAD_NAMES = {"", "쿠팡상품", "추천상품", "새 상품", "새 프로젝트"}

    def is_placeholder(self, name):
        return str(name or "").strip() in self.BAD_NAMES

    def clean_title(self, title):
        title = str(title or "").strip()
        title = re.sub(r"\[[^\]]+\]|\([^\)]+\)", " ", title)
        title = re.sub(r"\s+", " ", title)
        title = title.replace("무료배송", "").replace("로켓배송", "")
        return title.strip()

    def short_title(self, title):
        clean = self.clean_title(title)
        if not clean:
            return "생활용품 추천상품"

        priority = [
            "주방 슬라이딩 양념통 정리대",
            "주방 양념통 정리대",
            "주방 슬라이딩 수납장",
            "냄비뚜껑 거치대",
            "문틈 방충망",
            "신발건조기",
            "배수구 냄새 차단 트랩",
        ]
        for p in priority:
            if all(x in clean for x in p.split()[:2]):
                return p

        tokens = [t for t in clean.split() if len(t) > 1]
        return " ".join(tokens[:5]) if tokens else clean[:30]

    def core_terms(self, title):
        clean = self.clean_title(title)
        terms = []
        dictionary = [
            "주방", "정리대", "양념통", "코너", "슬라이딩", "수납장",
            "다층", "선반", "조리도구", "걸이", "냄비뚜껑", "거치대",
            "문틈", "방충망", "신발건조기", "배수구", "트랩", "수전",
            "얼음", "보틀", "장갑", "파우치",
        ]
        for term in dictionary:
            if term in clean:
                terms.append(term)
        return list(dict.fromkeys(terms))

    def improve(self, current_name="", manual_name=""):
        source = manual_name.strip() or current_name.strip()
        if self.is_placeholder(current_name) and manual_name.strip():
            source = manual_name.strip()
        clean = self.clean_title(source)
        short = self.short_title(clean)
        return {
            "source_title": source,
            "clean_title": clean,
            "short_title": short,
            "core_terms": self.core_terms(clean),
            "is_placeholder": self.is_placeholder(current_name),
        }
