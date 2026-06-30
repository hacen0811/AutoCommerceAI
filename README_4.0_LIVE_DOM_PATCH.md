# AutoCommerceAI 4.0 Live DOM Patch

이번 패치는 `modules/studio/playwright_video_collector.py`를 실제 검색 결과 링크 중심으로 수정합니다.

## 개선 내용
- 도우인: `/video/`, `/note/`, `/user/` 후보만 수집
- 타오바오: `item.taobao.com/item.htm`, `detail.tmall.com/item.htm` 후보만 수집
- 1688: `detail.1688.com/offer/` 후보만 수집
- 구매내역/판매내역/추천 메인/피드백/로그인 링크 제외
- 검색 페이지 스크린샷 저장
- 로그인/캡차/차단 진단 메시지 저장

## 실행
1. `INSTALL_PLAYWRIGHT.bat`
2. `RUN_LIVE_SOURCE.bat`
3. 쇼츠 스튜디오에서 쿠팡 링크/상품명 입력 후 생성
4. `영상후보` 탭에서 `실제 웹 수집 결과` 확인

로그인이 필요하면 `LOGIN_SOURCE_BROWSER.bat` 실행 후 열린 브라우저에서 로그인하세요.
