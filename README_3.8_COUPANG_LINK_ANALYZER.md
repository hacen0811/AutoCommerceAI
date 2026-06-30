# AutoCommerceAI 3.8 Coupang Link Analyzer

## 추가 기능

- 쿠팡 링크 공개 메타데이터 자동 분석
  - productId / itemId / vendorItemId 추출
  - og:title / og:image / description 추출
  - JSON-LD Product 정보 추출 시도
  - 가격, 대표 이미지, 상품 특징 후보 자동 보강
- 쇼츠 스튜디오에 `쿠팡분석` 탭 추가
- 쿠팡이 차단해도 앱이 멈추지 않고 기존 입력값 기반으로 안전 실행

## 실행

```cmd
python -m streamlit run main.py
```

## 주의

쿠팡 페이지가 접근을 제한할 수 있습니다. 이 버전은 로그인, 우회, 차단 회피를 하지 않으며 공개 메타데이터만 읽습니다.
