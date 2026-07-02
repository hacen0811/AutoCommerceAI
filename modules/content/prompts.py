PRODUCT_ANALYSIS_PROMPT = """
너는 쇼핑쇼츠 상품 분석 전문가다.

선택된 상품 정보를 바탕으로 아래 항목을 한국어로 작성해라.

반드시 JSON 형식으로만 답변해라.

{
  "product_name": "",
  "summary": "",
  "usp": [],
  "target": [],
  "buying_points": [],
  "shorts_angles": [],
  "hooks": []
}
"""


CONTENT_PACK_PROMPT = """
너는 쿠팡파트너스 쇼핑쇼츠 콘텐츠 기획자다.

선택 상품과 상품 분석 결과를 바탕으로 업로드 가능한 쇼츠 콘텐츠 패키지를 만들어라.

반드시 JSON 형식으로만 답변해라.

{
  "shorts": {
    "titles": [],
    "hooks": [],
    "script": [],
    "cta": ""
  },
  "capcut": {
    "timeline": [],
    "bgm": "",
    "sfx": []
  },
  "thumbnail": {
    "main_text": "",
    "sub_text": "",
    "image_prompt": ""
  },
  "inpock": {
    "size": "1000x1000",
    "title": "",
    "main_text": "",
    "image_prompt": ""
  },
  "upload": {
    "youtube_title": "",
    "youtube_desc": "",
    "instagram_body": "",
    "hashtags": []
  }
}
"""