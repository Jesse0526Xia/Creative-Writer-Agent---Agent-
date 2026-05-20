"""
RAG 检索器
"""
from typing import List, Dict, Any, Optional
from core.rag.vector_store import get_vector_store


class MaterialRetriever:
    """素材检索器"""

    def __init__(self, index_name: str = "materials"):
        self.vector_store = get_vector_store(index_name)

    def add_material(
        self,
        content: str,
        file_name: Optional[str] = None,
        file_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        project_id: Optional[str] = None
    ) -> int:
        """
        添加素材

        Args:
            content: 内容
            file_name: 文件名
            file_type: 文件类型
            metadata: 其他元数据
            project_id: 所属项目ID

        Returns:
            素材ID
        """
        meta = {
            "text": content,
            "content": content[:500],  # 保留前500字
            "file_name": file_name,
            "file_type": file_type,
            "project_id": project_id
        }
        if metadata:
            meta.update(metadata)

        return self.vector_store.add_text(content, meta)

    def search(
        self,
        query: str,
        k: int = 5,
        file_type: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        检索素材

        Args:
            query: 查询文本
            k: 返回数量
            file_type: 文件类型过滤
            project_id: 项目ID过滤

        Returns:
            素材列表
        """
        filter_meta = {"file_type": file_type}
        if project_id:
            # project_id 为 None 表示全局素材
            filter_meta["project_id"] = project_id
        return self.vector_store.search(query, k=k, filter_metadata=filter_meta)

    def get_material(self, id: int) -> Optional[Dict[str, Any]]:
        """获取素材"""
        return self.vector_store.get_by_id(id)

    def delete_material(self, id: int):
        """删除素材"""
        self.vector_store.delete_by_id(id)


class CharacterRetriever:
    """角色检索器"""

    def __init__(self, index_name: str = "characters"):
        self.vector_store = get_vector_store(index_name)

    def add_character(
        self,
        character_data: Dict[str, Any]
    ) -> int:
        """
        添加角色

        Args:
            character_data: 角色数据

        Returns:
            角色ID
        """
        # 构建角色文本描述
        lines = []

        basic = character_data.get("basic", {})
        lines.append(f"姓名: {basic.get('name', '')}")

        personality = character_data.get("personality", {})
        if personality.get("traits"):
            lines.append(f"性格: {', '.join(personality['traits'])}")
        if personality.get("mbti"):
            lines.append(f"MBTI: {personality['mbti']}")

        speaking = character_data.get("speaking", {})
        if speaking.get("catchphrases"):
            lines.append(f"口头禅: {', '.join(speaking['catchphrases'])}")

        background = character_data.get("background", {})
        if background.get("origin"):
            lines.append(f"背景: {background['origin']}")

        text = "\n".join(lines)

        metadata = {
            "character_id": character_data.get("id"),
            "name": basic.get("name"),
            "data": character_data
        }

        return self.vector_store.add_text(text, metadata)

    def search_similar(
        self,
        query: str,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """搜索相似角色"""
        return self.vector_store.search(query, k=k)

    def get_character(self, id: int) -> Optional[Dict[str, Any]]:
        """获取角色"""
        return self.vector_store.get_by_id(id)


# 全局检索器
_material_retriever: Optional[MaterialRetriever] = None
_character_retriever: Optional[CharacterRetriever] = None


def get_material_retriever() -> MaterialRetriever:
    """获取素材检索器"""
    global _material_retriever
    if _material_retriever is None:
        _material_retriever = MaterialRetriever()
    return _material_retriever


def get_character_retriever() -> CharacterRetriever:
    """获取角色检索器"""
    global _character_retriever
    if _character_retriever is None:
        _character_retriever = CharacterRetriever()
    return _character_retriever
