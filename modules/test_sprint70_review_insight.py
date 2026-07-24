import json

from modules.content.review_insight_engine import ReviewInsightEngine


comments = [
    {"text": "그냥 사지말라 해서 안삼", "comment_id": "1"},
    {"text": "자동", "comment_id": "2"},
    {"text": "구매방법", "comment_id": "3"},
    {"text": "프로필 들어오셔서 링크 눌러주세요!", "comment_id": "4"},
    {"text": "쓰는 사람입니다. 만족스럽게 쓰고 있어요. 쿠팡에서 검색하세요", "comment_id": "5"},
]

result = ReviewInsightEngine().analyze(
    reviews=[],
    social_comments=comments,
    product_name="전동 손톱깎이",
)

print(json.dumps(result, ensure_ascii=False, indent=2))
