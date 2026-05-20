"""
文档解析器 - 统一入口（懒加载版本）
"""
from typing import Optional
from pathlib import Path
from core.parser.base import BaseParser


class DocumentParser:
    """统一文档解析器"""

    def __init__(self):
        self._parsers = {}
        self._parser_classes = {
            ".docx": ("core.parser.docx_parser", "get_docx_parser"),
            ".pdf": ("core.parser.pdf_parser", "get_pdf_parser"),
        }

    def _get_parser(self, ext: str):
        """懒加载解析器"""
        if ext not in self._parsers:
            if ext in self._parser_classes:
                module_name, func_name = self._parser_classes[ext]
                module = __import__(module_name, fromlist=[func_name])
                self._parsers[ext] = getattr(module, func_name)()
            else:
                return None
        return self._parsers.get(ext)

    def parse_file(self, file_path: str) -> str:
        path = Path(file_path)
        ext = path.suffix.lower()
        parser = self._get_parser(ext)
        if parser:
            return parser.parse(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {ext}")

    def parse_bytes(self, content: bytes, file_name: Optional[str] = None) -> str:
        if file_name:
            ext = Path(file_name).suffix.lower()
            parser = self._get_parser(ext)
            if parser:
                try:
                    return parser.parse_content(content)
                except Exception:
                    pass
            try:
                return content.decode("utf-8")
            except:
                return "[无法解析文件格式]"

        for ext in self._parser_classes:
            parser = self._get_parser(ext)
            if parser:
                try:
                    text = parser.parse_content(content)
                    if text and not text.startswith("["):
                        return text
                except:
                    continue

        try:
            return content.decode("utf-8")
        except:
            return "[无法解析文件内容]"

    def supported_types(self) -> list:
        return list(self._parser_classes.keys())


_document_parser: Optional[DocumentParser] = None


def get_document_parser() -> DocumentParser:
    """获取解析器"""
    global _document_parser
    if _document_parser is None:
        _document_parser = DocumentParser()
    return _document_parser
