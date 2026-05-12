import fitz


class PDFLoader:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    def load_text(self) -> str:
        """
        PDF 파일에서 전체 텍스트를 추출합니다.

        Returns:
            str: 추출된 전체 텍스트
        """

        text = ""

        try:
            doc = fitz.open(self.pdf_path)

            for page in doc:
                page_text = page.get_text()

                if page_text:
                    text += page_text + "\n"

            doc.close()

            return text.strip()

        except Exception as e:
            raise Exception(f"PDF 텍스트 추출 중 오류 발생: {e}")
        

