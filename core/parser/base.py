"""
文档解析基类
"""
from abc import ABC, abstractmethod
from typing import Optional


class BaseParser(ABC):
    """文档解析器基类"""

    @property
    @abstractmethod
    def file_type(self) -> str:
        """支持的文件类型"""
        pass

    @abstractmethod
    def parse(self, file_path: str) -> str:
        """
        解析文件

        Args:
            file_path: 文件路径

        Returns:
            提取的文本内容
        """
        pass

    @abstractmethod
    def parse_content(self, content: bytes) -> str:
        """
        解析文件内容

        Args:
            content: 文件字节内容

        Returns:
            提取的文本内容
        """
        pass
