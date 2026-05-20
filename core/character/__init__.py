"""Character包初始化"""
# 使用懒加载避免在应用启动时导入重型依赖

def get_character_manager():
    from core.character.manager import get_character_manager as _get
    return _get()

def get_character_analyzer():
    from core.character.style_analyzer import get_character_analyzer as _get
    return _get()

__all__ = ["get_character_manager", "get_character_analyzer"]
