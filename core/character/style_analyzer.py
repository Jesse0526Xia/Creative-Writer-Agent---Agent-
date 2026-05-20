"""
角色分析器 - 从文档中提取角色特点
"""
from typing import Dict, Any, Optional
from core.llm import get_llm_client


# 角色提取Prompt
EXTRACT_CHARACTER_PROMPT = """请从以下文本中分析并提取角色特点。

【文本内容】
{content}

请提取以下信息，以JSON格式输出：

{{
    "characters": [
        {{
            "name": "角色名称",
            "identity": "身份背景（职业、年龄、社会地位等）",
            "personality_traits": ["性格特点1", "性格特点2"],
            "speaking_style": "说话方式特点",
            "catchphrases": ["口头禅1", "口头禅2"],
            "key_events": ["关键经历1", "关键经历2"],
            "relationships": {{
                "相关角色名": "关系描述"
            }},
            "mbti_hint": "可能的MBTI类型（可选）"
        }}
    ],
    "writing_style": "整体写作风格描述",
    "themes": ["主题1", "主题2"]
}}

如果没有明确识别出角色，请返回空的characters数组。"""


class CharacterAnalyzer:
    """角色分析器"""

    def __init__(self):
        self.llm = get_llm_client()

    def analyze_text(self, content: str) -> Dict[str, Any]:
        """
        分析文本提取角色

        Args:
            content: 文本内容

        Returns:
            分析结果
        """
        try:
            result = self.llm.structured_complete(
                prompt=EXTRACT_CHARACTER_PROMPT.format(content=content[:4000]),
                response_format={
                    "characters": [],
                    "writing_style": "",
                    "themes": []
                },
                temperature=0.5,
                max_tokens=4096
            )
            return result
        except Exception as e:
            return {
                "characters": [],
                "writing_style": "",
                "themes": [],
                "error": str(e)
            }

    def extract_from_document(
        self,
        content: str,
        file_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        从文档提取角色信息

        Args:
            content: 文档内容
            file_name: 文件名（可选）

        Returns:
            提取结果，包含可直接用于创建角色的数据
        """
        analysis = self.analyze_text(content)

        characters = []
        for char in analysis.get("characters", []):
            char_data = {
                "name": char.get("name", "未命名"),
                "age": None,  # 需要从identity中解析
                "occupation": self._extract_occupation(char.get("identity", "")),
                "personality_traits": char.get("personality_traits", []),
                "mbti": char.get("mbti_hint"),
                "speaking_style": char.get("speaking_style"),
                "catchphrases": char.get("catchphrases", []),
                "background": char.get("identity", ""),
                "custom_fields": {
                    "key_events": char.get("key_events", []),
                    "relationships": char.get("relationships", {}),
                    "source_file": file_name
                }
            }
            characters.append(char_data)

        return {
            "characters": characters,
            "writing_style": analysis.get("writing_style", ""),
            "themes": analysis.get("themes", []),
            "source_file": file_name
        }

    def _extract_occupation(self, identity: str) -> Optional[str]:
        """从身份描述中提取职业"""
        # 简单的关键词匹配
        keywords = [
            "学生", "老师", "医生", "护士", "律师", "警察", "商人",
            "作家", "画家", "歌手", "演员", "工程师", "设计师",
            "程序员", "记者", "编辑", "老板", "经理", "员工"
        ]
        for kw in keywords:
            if kw in identity:
                return kw
        return None


# 全局分析器
_character_analyzer: Optional[CharacterAnalyzer] = None


def get_character_analyzer() -> CharacterAnalyzer:
    """获取角色分析器"""
    global _character_analyzer
    if _character_analyzer is None:
        _character_analyzer = CharacterAnalyzer()
    return _character_analyzer
