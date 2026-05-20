"""
角色档案管理
"""
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from models.schemas import CharacterProfile, CharacterBasic, CharacterPersonality
from models.schemas import CharacterSpeaking, CharacterBackground, RelationshipEntry


class CharacterManager:
    """角色管理器"""

    def __init__(self):
        self._retriever = None
        self._characters: Dict[str, Dict[str, Any]] = {}
        self._load_characters()

    @property
    def retriever(self):
        """懒加载 retriever，避免启动时触发 embedding 模型下载"""
        if self._retriever is None:
            from core.rag.retriever import get_character_retriever
            self._retriever = get_character_retriever()
        return self._retriever

    def _load_characters(self):
        """加载角色数据"""
        storage_path = Path("data/characters.json")
        if storage_path.exists():
            try:
                with open(storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._characters = data.get("characters", {})
            except Exception:
                self._characters = {}

    def _save_characters(self):
        """保存角色数据"""
        storage_path = Path("data/characters.json")
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(storage_path, "w", encoding="utf-8") as f:
            json.dump({
                "characters": self._characters,
                "updated_at": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)

    def create_character(
        self,
        name: str,
        gender: Optional[str] = None,
        age: Optional[int] = None,
        occupation: Optional[str] = None,
        personality_traits: List[str] = None,
        mbti: Optional[str] = None,
        speaking_style: Optional[str] = None,
        catchphrases: List[str] = None,
        background: Optional[str] = None,
        relationships: List[Dict[str, Any]] = None,
        custom_fields: Dict[str, Any] = None,
        project_id: Optional[str] = None
    ) -> CharacterProfile:
        """
        创建角色

        Args:
            name: 名称
            gender: 性别
            age: 年龄
            occupation: 职业
            personality_traits: 性格特点
            mbti: MBTI
            speaking_style: 说话风格描述
            catchphrases: 口头禅
            background: 背景
            relationships: 人物关系列表 [{"related_id": "...", "type": "...", "description": "...", "story": "..."}]
            custom_fields: 自定义字段
            project_id: 所属项目ID，None表示全局角色

        Returns:
            角色档案
        """
        char_id = str(uuid.uuid4())

        # 处理关系数据
        relationships_dict = {}
        if relationships:
            for rel in relationships:
                related_name = rel.get("related_name", "")
                if related_name:
                    relationships_dict[related_name] = {
                        "type": rel.get("type", "friend"),
                        "description": rel.get("description", ""),
                        "story": rel.get("story", ""),
                        "related_id": rel.get("related_id", "")
                    }

        profile = {
            "id": char_id,
            "project_id": project_id,
            "basic": {
                "name": name,
                "gender": gender,
                "age": age,
                "occupation": occupation
            },
            "personality": {
                "traits": personality_traits or [],
                "mbti": mbti
            },
            "appearance": {
                "style": "",
                "distinctive_features": []
            },
            "speaking": {
                "vocabulary": [],
                "sentence_patterns": [],
                "catchphrases": catchphrases or [],
                "style_description": speaking_style
            },
            "background": {
                "origin": background or "",
                "key_events": [],
                "current_situation": ""
            },
            "relationships": relationships_dict,
            "custom_fields": custom_fields or {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        self._characters[char_id] = profile
        self._save_characters()

        # 尝试添加到向量索引，失败不阻塞角色创建
        try:
            self.retriever.add_character(profile)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"角色向量索引失败（不影响创建）: {e}")

        return self._to_profile(profile)

    def get_character(self, char_id: str) -> Optional[CharacterProfile]:
        """获取角色"""
        profile = self._characters.get(char_id)
        if profile:
            return self._to_profile(profile)
        return None

    def update_character(
        self,
        char_id: str,
        **kwargs
    ) -> Optional[CharacterProfile]:
        """更新角色"""
        if char_id not in self._characters:
            return None

        profile = self._characters[char_id]

        # 更新各部分
        if "name" in kwargs:
            profile["basic"]["name"] = kwargs["name"]
        if "age" in kwargs:
            profile["basic"]["age"] = kwargs["age"]
        if "occupation" in kwargs:
            profile["basic"]["occupation"] = kwargs["occupation"]
        if "personality_traits" in kwargs:
            profile["personality"]["traits"] = kwargs["personality_traits"]
        if "mbti" in kwargs:
            profile["personality"]["mbti"] = kwargs["mbti"]
        if "speaking_style" in kwargs:
            profile["speaking"]["style_description"] = kwargs["speaking_style"]
        if "catchphrases" in kwargs:
            profile["speaking"]["catchphrases"] = kwargs["catchphrases"]
        if "background" in kwargs:
            profile["background"]["origin"] = kwargs["background"]

        profile["updated_at"] = datetime.now().isoformat()

        self._save_characters()
        return self._to_profile(profile)

    def delete_character(self, char_id: str) -> bool:
        """删除角色"""
        if char_id in self._characters:
            del self._characters[char_id]
            self._save_characters()
            return True
        return False

    def list_characters(self, project_id: Optional[str] = None) -> List[CharacterProfile]:
        """
        列出角色

        Args:
            project_id: 按项目ID筛选，None表示返回所有角色
                       None返回全局+所有项目的角色
                       具体ID返回该项目角色+全局角色
                       "__global__"只返回全局角色
        """
        if project_id is None:
            # 返回所有角色
            return [self._to_profile(p) for p in self._characters.values()]
        elif project_id == "__global__":
            # 只返回全局角色
            return [self._to_profile(p) for p in self._characters.values()
                    if p.get("project_id") is None]
        else:
            # 返回指定项目角色 + 全局角色
            return [self._to_profile(p) for p in self._characters.values()
                    if p.get("project_id") is None or p.get("project_id") == project_id]

    def add_relationship(
        self,
        char_id: str,
        related_name: str,
        relation_type: str,
        description: str
    ) -> bool:
        """添加人物关系"""
        if char_id not in self._characters:
            return False

        self._characters[char_id]["relationships"][related_name] = {
            "type": relation_type,
            "description": description
        }
        self._save_characters()
        return True

    def search_similar(self, query: str, k: int = 3) -> List[CharacterProfile]:
        """搜索相似角色"""
        results = self.retriever.search_similar(query, k=k)
        profiles = []
        for r in results:
            char_data = r.get("data", {})
            if char_data:
                profiles.append(self._to_profile(char_data))
        return profiles

    def _to_profile(self, data: Dict[str, Any]) -> CharacterProfile:
        """转换为CharacterProfile模型"""
        return CharacterProfile(
            id=data.get("id"),
            basic=CharacterBasic(**data.get("basic", {})),
            personality=CharacterPersonality(**data.get("personality", {})),
            appearance=data.get("appearance", {}),
            speaking=CharacterSpeaking(
                vocabulary=data.get("speaking", {}).get("vocabulary", []),
                sentence_patterns=data.get("speaking", {}).get("sentence_patterns", []),
                catchphrases=data.get("speaking", {}).get("catchphrases", []),
                style_description=data.get("speaking", {}).get("style_description")
            ),
            background=CharacterBackground(**data.get("background", {})),
            relationships={
                k: RelationshipEntry(**v) for k, v in data.get("relationships", {}).items()
            },
            custom_fields=data.get("custom_fields", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )


# 全局角色管理器
_character_manager: Optional[CharacterManager] = None


def get_character_manager() -> CharacterManager:
    """获取角色管理器"""
    global _character_manager
    if _character_manager is None:
        _character_manager = CharacterManager()
    return _character_manager
