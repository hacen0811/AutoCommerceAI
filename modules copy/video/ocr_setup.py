class OCRSetupChecker:
    def check(self):
        result = {
            "pytesseract": False,
            "tesseract_program": False,
            "version": "",
            "languages": [],
            "ready": False,
            "message": "",
            "install_guide": [
                "1. Windows용 Tesseract OCR 설치",
                "2. 설치 시 chi_sim, eng, kor 언어팩 포함",
                "3. 설치 후 CMD/PowerShell 재시작",
                "4. tesseract --version 실행 확인",
                "5. AutoCommerceAI 재실행",
            ],
        }

        try:
            import pytesseract
            result["pytesseract"] = True
            try:
                result["version"] = str(pytesseract.get_tesseract_version())
                result["tesseract_program"] = True
            except Exception as exc:
                result["message"] = f"Tesseract 프로그램을 찾지 못했습니다: {exc}"

            try:
                result["languages"] = list(pytesseract.get_languages(config=""))
            except Exception:
                result["languages"] = []

        except Exception as exc:
            result["message"] = f"pytesseract 패키지가 없습니다: {exc}"

        langs = set(result["languages"])
        has_needed = bool(langs.intersection({"chi_sim", "eng", "kor"}))
        result["ready"] = bool(result["pytesseract"] and result["tesseract_program"] and has_needed)

        if result["ready"]:
            result["message"] = "OCR 사용 가능 상태입니다."
        elif result["pytesseract"] and result["tesseract_program"]:
            result["message"] = "Tesseract는 설치되어 있지만 chi_sim/eng/kor 언어팩 확인이 필요합니다."

        return result
