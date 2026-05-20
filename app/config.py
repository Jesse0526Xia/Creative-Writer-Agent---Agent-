"""
Creative Writer Agent - 配置管理
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


# 项目根目录（必须在Settings类之前定义，供BaseSettings使用）
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """应用配置"""

    # LLM API配置
    doubao_api_key: Optional[str] = None
    doubao_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    doubao_model: str = "doubao-pro-32k"

    kimi_api_key: Optional[str] = None
    kimi_base_url: str = "https://api.moonshot.cn/v1"
    kimi_model: str = "moonshot-v1-8k"

    # 方案3: DeepSeek API
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # 选择使用的API
    active_llm: str = "doubao"  # "doubao", "kimi" 或 "deepseek"

    # Embedding配置
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_device: str = "cpu"
    embedding_dimension: int = 384

    # 数据库配置
    database_url: str = "sqlite:///data/db/writer.db"

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # RAG配置
    vector_store_path: str = "data/vectors"
    material_upload_path: str = "data/materials"
    max_material_size: int = 10 * 1024 * 1024  # 10MB

    # 写作配置
    default_iterations: int = 3
    max_iterations: int = 5
    context_window: int = 4096

    # CORS配置
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:8000,http://localhost:8000,http://127.0.0.1:3000"

    # HuggingFace 配置
    hf_endpoint: str = "https://huggingface.co"

    class Config:
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"


# 全局配置实例
settings = Settings()

# 项目目录（与上面保持一致，供其他模块使用）
DATA_DIR = BASE_DIR / "data"
VECTOR_DIR = DATA_DIR / "vectors"
MATERIAL_DIR = DATA_DIR / "materials"
DB_DIR = DATA_DIR / "db"

# 确保目录存在
for dir_path in [DATA_DIR, VECTOR_DIR, MATERIAL_DIR, DB_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# 调试日志：仅在debug模式下打印配置加载状态
if settings.debug:
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    # 根据active_llm判断当前提供商
    active_provider = settings.active_llm
    if active_provider == "deepseek":
        api_key_loaded = bool(settings.deepseek_api_key)
        logger.info(f"[Config Debug] 当前LLM提供商: DeepSeek, API Key已加载: {api_key_loaded}")
    elif active_provider == "doubao":
        api_key_loaded = bool(settings.doubao_api_key)
        logger.info(f"[Config Debug] 当前LLM提供商: Doubao, API Key已加载: {api_key_loaded}")
    elif active_provider == "kimi":
        api_key_loaded = bool(settings.kimi_api_key)
        logger.info(f"[Config Debug] 当前LLM提供商: Kimi, API Key已加载: {api_key_loaded}")
    else:
        logger.info(f"[Config Debug] 当前LLM提供商: {active_provider}")
