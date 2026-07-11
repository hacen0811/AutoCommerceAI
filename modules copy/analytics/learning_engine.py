class LearningEngine:
    def evaluate(self, rows):
        rows = rows or []
        if not rows:
            return {
                "status": "데이터 부족",
                "summary": "성과 데이터가 아직 없습니다.",
                "recommendation": [
                    "조회수, 좋아요, 댓글, 저장 데이터를 최소 3개 이상 입력하세요.",
                    "초기에는 공감형 후킹과 정보형 구성을 함께 테스트하세요.",
                ],
            }

        total_views = sum(int(getattr(r, "views", 0) or 0) for r in rows)
        total_likes = sum(int(getattr(r, "likes", 0) or 0) for r in rows)
        total_comments = sum(int(getattr(r, "comments", 0) or 0) for r in rows)
        total_saves = sum(int(getattr(r, "saves", 0) or 0) for r in rows)

        save_rate = round((total_saves / total_views * 100), 2) if total_views else 0
        comment_rate = round((total_comments / total_views * 100), 2) if total_views else 0
        like_rate = round((total_likes / total_views * 100), 2) if total_views else 0

        rec = []
        if save_rate >= 3:
            rec.append("저장률이 좋습니다. 정보형/꿀팁형 구성을 더 늘려도 좋습니다.")
        else:
            rec.append("저장률이 낮습니다. Before/After와 사용법 설명을 더 명확히 넣으세요.")

        if comment_rate >= 1:
            rec.append("댓글 반응이 있습니다. 댓글 키워드 CTA를 유지하세요.")
        else:
            rec.append("댓글률이 낮습니다. '댓글에 키워드 남겨주세요'를 마지막 3초에 더 크게 노출하세요.")

        if like_rate >= 5:
            rec.append("좋아요 반응이 좋습니다. 현재 후킹 톤을 유지하세요.")
        else:
            rec.append("좋아요 반응이 약합니다. 첫 2초 후킹을 더 강하게 바꾸세요.")

        best = sorted(rows, key=lambda r: int(getattr(r, "views", 0) or 0), reverse=True)[0]

        return {
            "status": "분석 완료",
            "summary": f"총 조회수 {total_views:,}, 저장률 {save_rate}%, 댓글률 {comment_rate}%, 좋아요율 {like_rate}%입니다.",
            "metrics": {
                "views": total_views,
                "likes": total_likes,
                "comments": total_comments,
                "saves": total_saves,
                "save_rate": save_rate,
                "comment_rate": comment_rate,
                "like_rate": like_rate,
            },
            "best_project_id": getattr(best, "project_id", 0),
            "recommendation": rec,
            "next_strategy": [
                "후킹: 왜 이제 알았지? / 저도 이거 때문에 스트레스였어요 계열 우선 테스트",
                "편집: 첫 2초에 제품 사용 장면 또는 불편 장면 배치",
                "자막: 중앙 하단 40%, 중국어 자막 있으면 45~50%",
                "오디오: AI 음성 20 dB, BGM 8 dB, Pop 7 dB 유지",
            ],
        }
