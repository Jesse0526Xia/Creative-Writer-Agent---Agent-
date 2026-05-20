"""
PDF 文档解析
"""
from typing import Optional
import PyPDF2
from io import BytesIO
from core.parser.base import BaseParser


class PdfParser(BaseParser):
    """PDF 文件解析器"""

    @property
    def file_type(self) -> str:
        return ".pdf"

    def parse(self, file_path: str) -> str:
        """解析文件"""
        with open(file_path, "rb") as f:
            return self.parse_content(f.read())

    def parse_content(self, content: bytes) -> str:
        """解析文件内容"""
        try:
            pdf_file = BytesIO(content)
            reader = PyPDF2.PdfReader(pdf_file)

            paragraphs = []
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    # 清理文本
                    lines = text.split("\n")
                    for line in lines:
                        line = line.strip()
                        if line:
                            paragraphs.append(line)

            return "\n".join(paragraphs)
        except Exception as e:
            return f"[PDF解析失败: {str(e)}]"


# 全局实例
_pdf_parser: Optional[PdfParser] = None


def get_pdf_parser() -> PdfParser:
    """获取解析器"""
    global _pdf_parser
    if _pdf_parser is None:
        _pdf_parser = PdfParser()
    return _pdf_parser
