class VisionScoreEngine:
    """
    SmartCut 2.0 점수 계산 엔진.
    video_ai + YOLO + PaddleOCR/Vision 결과를 통합해
    후킹/썸네일/삭제/줌 후보 점수를 계산합니다.
    """

    def score_frames(self, video_ai=None, yolo=None, ocr=None):
        video_ai = video_ai or {}
        yolo = yolo or {}
        ocr = ocr or {}

        samples = video_ai.get("samples", []) or []
        yolo_dets = yolo.get("detections", []) or []
        ocr_dets = ocr.get("detections", []) or ocr.get("ocr_texts", []) or []

        scored = []
        for sample in samples:
            t = sample.get("time", 0)
            base = int(sample.get("score", 50) or 50)

            nearby_yolo = self._nearby(yolo_dets, t, window=1.2)
            nearby_ocr = self._nearby(ocr_dets, t, window=1.2)

            product_score = self._product_score(nearby_yolo)
            text_penalty = self._text_penalty(nearby_ocr)
            brightness_score = self._brightness_score(sample)
            change_score = min(15, int(float(sample.get("change", 0) or 0)))

            final = base + product_score + brightness_score + change_score - text_penalty
            final = max(0, min(100, int(final)))

            scored.append({
                "time": t,
                "frame": sample.get("frame", ""),
                "score": final,
                "base_score": base,
                "product_score": product_score,
                "brightness_score": brightness_score,
                "change_score": change_score,
                "text_penalty": text_penalty,
                "reason": self._reason(final, product_score, text_penalty, sample),
                "recommend": self._recommend(final, text_penalty),
            })

        scored = sorted(scored, key=lambda x: x["score"], reverse=True)
        return {
            "frames": scored,
            "hook_candidates": scored[:5],
            "thumbnail_candidates": scored[:5],
            "delete_candidates": [x for x in scored if x["score"] < 55][-5:],
            "zoom_candidates": [x for x in scored if x["product_score"] >= 15][:5],
        }

    def _nearby(self, items, t, window=1.0):
        out = []
        for item in items:
            try:
                if abs(float(item.get("time", 0)) - float(t)) <= window:
                    out.append(item)
            except Exception:
                continue
        return out

    def _product_score(self, detections):
        if not detections:
            return 0
        score = 0
        for d in detections:
            role = str(d.get("role", ""))
            label = str(d.get("label", "")).lower()
            conf = float(d.get("confidence", d.get("score", 0.5)) or 0.5)
            if "상품" in role or label in ["bottle", "cup", "cell phone", "laptop", "bowl", "chair"]:
                score += int(20 * conf)
            elif label == "person" or "사람" in role:
                score += int(8 * conf)
            else:
                score += int(5 * conf)
        return min(25, score)

    def _text_penalty(self, detections):
        if not detections:
            return 0
        penalty = 0
        for d in detections:
            region = str(d.get("region", ""))
            text = str(d.get("text", ""))
            if region == "bottom" or "bottom" in region:
                penalty += 12
            elif region == "top" or "top" in region:
                penalty += 6
            if len(text) >= 8:
                penalty += 5
        return min(25, penalty)

    def _brightness_score(self, sample):
        b = float(sample.get("brightness", 100) or 100)
        c = float(sample.get("contrast", 30) or 30)
        score = 0
        if 60 <= b <= 210:
            score += 8
        if c >= 35:
            score += 7
        return score

    def _reason(self, final, product_score, text_penalty, sample):
        reasons = []
        if product_score >= 15:
            reasons.append("상품/객체 후보가 뚜렷함")
        if text_penalty >= 12:
            reasons.append("자막/텍스트 위험 있음")
        if sample.get("change", 0) >= 15:
            reasons.append("장면 변화가 있어 후킹에 적합")
        if not reasons:
            reasons.append("기본 프레임 품질 기준")
        return " / ".join(reasons)

    def _recommend(self, final, text_penalty):
        if final >= 85 and text_penalty < 12:
            return "후킹/썸네일 강력 후보"
        if final >= 75:
            return "사용 후보"
        if final < 55:
            return "삭제 후보"
        return "검토 후보"
