"""
Embedding 向量化模块
"""
import os
from app.config import settings

# 使用配置文件中的 HF_ENDPOINT 设置 HuggingFace 镜像
os.environ["HF_ENDPOINT"] = settings.hf_endpoint
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

from typing import List, Optional
from sentence_transformers import SentenceTransformer
from app.config import settings
import numpy as np


class EmbeddingModel:
    """Embedding模型封装"""

    _instance: Optional["EmbeddingModel"] = None
    _model: Optional[SentenceTransformer] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def model(self) -> SentenceTransformer:
        """获取模型"""
        if self._model is None:
            self._model = SentenceTransformer(
                settings.embedding_model,
                device=settings.embedding_device
            )
        return self._model

    @property
    def dimension(self) -> int:
        """获取向量维度"""
        return settings.embedding_dimension

    def encode(self, texts: List[str], normalize: bool = True) -> np.ndarray:
        """
        将文本编码为向量

        Args:
            texts: 文本列表
            normalize: 是否归一化

        Returns:
            向量数组 (n, dimension)
        """
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=normalize,
            show_progress_bar=False
        )
        return embeddings

    def encode_single(self, text: str, normalize: bool = True) -> np.ndarray:
        """
        编码单个文本

        Args:
            text: 文本
            normalize: 是否归一化

        Returns:
            向量 (dimension,)
        """
        return self.encode([text], normalize=normalize)[0]

    def similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度分数
        """
        vec1 = self.encode_single(text1)
        vec2 = self.encode_single(text2)

        # 归一化后点积即为余弦相似度
        return float(np.dot(vec1, vec2))

    def batch_similarity(
        self,
        query: str,
        texts: List[str]
    ) -> List[float]:
        """
        批量计算相似度

        Args:
            query: 查询文本
            texts: 待比较文本列表

        Returns:
            相似度分数列表
        """
        query_vec = self.encode_single(query)
        text_vecs = self.encode(texts)

        similarities = np.dot(text_vecs, query_vec)
        return similarities.tolist()


# 全局实例
embedding_model = EmbeddingModel()


def get_embedding_model() -> EmbeddingModel:
    """获取Embedding模型"""
    return embedding_model
