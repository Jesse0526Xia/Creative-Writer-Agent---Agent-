"""
FAISS 向量存储
"""
import os
import json
import faiss
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from app.config import VECTOR_DIR, settings
from core.rag.embeddings import get_embedding_model


class VectorStore:
    """FAISS向量存储"""

    def __init__(self, dimension: int = None, index_name: str = "default"):
        """
        初始化向量存储

        Args:
            dimension: 向量维度，默认使用embedding维度
            index_name: 索引名称
        """
        self.dimension = dimension or settings.embedding_dimension
        self.index_name = index_name
        self.index_path = VECTOR_DIR / f"{index_name}.index"
        self.meta_path = VECTOR_DIR / f"{index_name}_meta.json"

        self.index: Optional[faiss.Index] = None
        self.metadata: List[Dict[str, Any]] = []
        self.embedding = get_embedding_model()

        self._load()

    def _load(self):
        """加载索引"""
        if self.index_path.exists():
            try:
                self.index = faiss.read_index(str(self.index_path))
            except Exception:
                self.index = None

        if self.meta_path.exists():
            try:
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
            except Exception:
                self.metadata = []

        if self.index is None:
            self._create_index()

    def _create_index(self):
        """创建新索引"""
        # 使用内积索引（归一化后等价于余弦相似度）
        self.index = faiss.IndexIDMap(
            faiss.IndexFlatIP(self.dimension)
        )
        self.metadata = []

    def _save(self):
        """保存索引"""
        if self.index is not None:
            faiss.write_index(self.index, str(self.index_path))

        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    def add_texts(
        self,
        texts: List[str],
        metadata: List[Dict[str, Any]] = None
    ) -> List[int]:
        """
        添加文本到向量库

        Args:
            texts: 文本列表
            metadata: 元数据列表

        Returns:
            添加的ID列表
        """
        if not texts:
            return []

        # 编码文本
        vectors = self.embedding.encode(texts)

        # 生成ID
        start_id = len(self.metadata)
        ids = list(range(start_id, start_id + len(texts)))

        # 添加到索引
        self.index.add_with_ids(vectors.astype(np.float32), np.array(ids))

        # 添加元数据
        if metadata:
            self.metadata.extend(metadata)
        else:
            self.metadata.extend([{"text": text} for text in texts])

        self._save()

        return ids

    def add_text(
        self,
        text: str,
        metadata: Dict[str, Any] = None
    ) -> int:
        """添加单个文本"""
        ids = self.add_texts([text], [metadata] if metadata else None)
        return ids[0] if ids else -1

    def search(
        self,
        query: str,
        k: int = 5,
        filter_metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索相似文本

        Args:
            query: 查询文本
            k: 返回数量
            filter_metadata: 元数据过滤条件

        Returns:
            搜索结果列表
        """
        # 编码查询
        query_vector = self.embedding.encode_single(query).reshape(1, -1).astype(np.float32)

        # 搜索
        scores, indices = self.index.search(query_vector, min(k * 2, self.index.ntotal))

        # 整理结果
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue

            meta = self.metadata[idx].copy()
            meta["score"] = float(score)
            meta["id"] = int(idx)

            # 过滤
            if filter_metadata:
                if not all(meta.get(k) == v for k, v in filter_metadata.items()):
                    continue

            results.append(meta)

            if len(results) >= k:
                break

        return results

    def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取"""
        if 0 <= id < len(self.metadata):
            meta = self.metadata[id].copy()
            meta["id"] = id
            return meta
        return None

    def delete_by_id(self, id: int):
        """删除指定ID（标记删除）"""
        if 0 <= id < len(self.metadata):
            self.metadata[id]["deleted"] = True
            self._save()

    def count(self) -> int:
        """获取总数"""
        return self.index.ntotal if self.index else 0

    def clear(self):
        """清空"""
        self._create_index()
        self._save()

    def rebuild(self):
        """重建索引"""
        # 获取未删除的
        valid_meta = [m for m in self.metadata if not m.get("deleted", False)]
        valid_texts = [m.get("text", "") for m in valid_meta]

        # 重建
        self._create_index()
        if valid_texts:
            self.add_texts(valid_texts, valid_meta)


# 简化的全局存储
_vector_store: Optional[VectorStore] = None


def get_vector_store(index_name: str = "default") -> VectorStore:
    """获取向量存储"""
    global _vector_store
    if _vector_store is None or _vector_store.index_name != index_name:
        _vector_store = VectorStore(index_name=index_name)
    return _vector_store
