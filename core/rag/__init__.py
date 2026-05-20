"""RAG包初始化"""
# 使用懒加载避免在应用启动时导入重型依赖

def get_material_retriever():
    from core.rag.retriever import get_material_retriever as _get
    return _get()

def get_character_retriever():
    from core.rag.retriever import get_character_retriever as _get
    return _get()

def get_embedding_model():
    from core.rag.embeddings import get_embedding_model as _get
    return _get()

def get_vector_store():
    from core.rag.vector_store import get_vector_store as _get
    return _get()

__all__ = [
    "get_material_retriever", "get_character_retriever",
    "get_embedding_model", "get_vector_store",
]
