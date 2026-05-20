"""
Pydantic 数据模型定义
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TaskType(str, Enum):
    """写作任务类型"""
    NOVEL = "novel"          # 小说
    ARTICLE = "article"       # 文章
    COPYWRITING = "copywriting"  # 文案
    PAPER = "paper"          # 论文
    SCRIPT = "script"        # 剧本


class WritingStyle(str, Enum):
    """写作风格"""
    LITERARY = "literary"    # 文艺
    BUSINESS = "business"    # 商务
    CASUAL = "casual"        # 随性
    ROMANTIC = "romantic"    # 浪漫
    HUMOROUS = "humorous"    # 幽默
    SERIOUS = "serious"      # 严肃
    FLOWERY = "flowery"      # 华丽
    SIMPLE = "simple"        # 简洁


# ========== 项目/工作相关模型 ==========

class ProjectCreateRequest(BaseModel):
    """创建项目请求"""
    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")


class ProjectUpdateRequest(BaseModel):
    """更新项目请求"""
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    """项目响应"""
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    character_count: int = 0
    material_count: int = 0
    session_count: int = 0


class ProjectDetailResponse(BaseModel):
    """项目详情响应"""
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    characters: List["CharacterProfile"] = Field(default_factory=list)
    materials: List["MaterialDocument"] = Field(default_factory=list)
    sessions: List["WritingSession"] = Field(default_factory=list)


# ========== 角色相关模型 ==========

class CharacterBasic(BaseModel):
    """角色基础信息"""
    name: str = Field(..., description="角色名称")
    gender: Optional[str] = Field(None, description="性别: male/female/other")
    age: Optional[int] = Field(None, description="年龄")
    occupation: Optional[str] = Field(None, description="职业")


class CharacterPersonality(BaseModel):
    """角色性格"""
    traits: List[str] = Field(default_factory=list, description="性格关键词")
    mbti: Optional[str] = Field(None, description="MBTI类型")
    strengths: Optional[str] = Field(None, description="优点")
    weaknesses: Optional[str] = Field(None, description="缺点")


class CharacterAppearance(BaseModel):
    """角色外貌"""
    style: Optional[str] = Field(None, description="风格描述")
    distinctive_features: List[str] = Field(default_factory=list, description="显著特征")


class CharacterSpeaking(BaseModel):
    """角色说话方式"""
    vocabulary: List[str] = Field(default_factory=list, description="常用词汇")
    sentence_patterns: List[str] = Field(default_factory=list, description="句式特点")
    catchphrases: List[str] = Field(default_factory=list, description="口头禅")


class CharacterBackground(BaseModel):
    """角色背景"""
    origin: Optional[str] = Field(None, description="来历")
    key_events: List[str] = Field(default_factory=list, description="关键事件")
    current_situation: Optional[str] = Field(None, description="现状")


class RelationshipEntry(BaseModel):
    """人物关系"""
    type: str = Field(..., description="关系类型: family/friend/enemy/lover/colleague/rival/mentor")
    description: str = Field(..., description="关系描述")
    story: Optional[str] = Field(None, description="两人之间的故事/回忆")
    related_id: Optional[str] = Field(None, description="关联角色ID")


class CharacterProfile(BaseModel):
    """完整角色档案"""
    id: Optional[str] = Field(None, description="角色ID")
    basic: CharacterBasic
    personality: CharacterPersonality = Field(default_factory=CharacterPersonality)
    appearance: CharacterAppearance = Field(default_factory=CharacterAppearance)
    speaking: CharacterSpeaking = Field(default_factory=CharacterSpeaking)
    background: CharacterBackground = Field(default_factory=CharacterBackground)
    relationships: Dict[str, RelationshipEntry] = Field(default_factory=dict)
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="自定义字段")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_prompt_context(self) -> str:
        """转换为Prompt上下文"""
        gender_text = {"male": "男", "female": "女", "other": "其他"}.get(self.basic.gender, "未设定")
        lines = [
            f"角色名称: {self.basic.name}",
            f"性别: {gender_text}",
            f"年龄: {self.basic.age or '未设定'}",
            f"职业: {self.basic.occupation or '未设定'}",
        ]
        if self.personality.traits:
            lines.append(f"性格特点: {', '.join(self.personality.traits)}")
        if self.personality.mbti:
            lines.append(f"MBTI: {self.personality.mbti}")
        if self.personality.strengths:
            lines.append(f"优点: {self.personality.strengths}")
        if self.personality.weaknesses:
            lines.append(f"缺点: {self.personality.weaknesses}")
        if self.speaking.catchphrases:
            lines.append(f"口头禅: {', '.join(self.speaking.catchphrases)}")
        if self.speaking.vocabulary:
            lines.append(f"常用词汇: {', '.join(self.speaking.vocabulary)}")
        if self.background.origin:
            lines.append(f"背景: {self.background.origin}")
        if self.background.key_events:
            lines.append(f"关键经历: {'; '.join(self.background.key_events)}")
        if self.relationships:
            lines.append("人物关系:")
            for name, rel in self.relationships.items():
                lines.append(f"  - 与{name}: {rel.type} - {rel.description}")
        return "\n".join(lines)


class CharacterCreateRequest(BaseModel):
    """创建角色请求"""
    name: str
    gender: Optional[str] = Field(None, description="性别: male/female/other")
    age: Optional[int] = None
    occupation: Optional[str] = None
    personality_traits: List[str] = Field(default_factory=list)
    mbti: Optional[str] = None
    speaking_style: Optional[str] = None
    catchphrases: List[str] = Field(default_factory=list)
    background: Optional[str] = None
    # 关系：列表形式，每个关系包含目标角色ID、关系类型、描述、故事
    relationships: List[Dict[str, Any]] = Field(default_factory=list, description="人物关系列表")
    custom_template: Optional[Dict[str, Any]] = Field(default_factory=dict)
    project_id: Optional[str] = Field(None, description="所属项目ID，null表示全局角色")


# ========== 素材相关模型 ==========

class MaterialDocument(BaseModel):
    """素材文档"""
    id: Optional[str] = None
    content: str
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None


# ========== 写作相关模型 ==========

class ChapterOutline(BaseModel):
    """章节大纲"""
    chapter: int
    title: str
    key_points: List[str]
    target_length: Optional[int] = Field(None, description="目标字数")


class WritingOutline(BaseModel):
    """完整大纲"""
    task_type: TaskType
    writing_style: str
    target_audience: Optional[str] = None
    outline: List[ChapterOutline]
    character_requirements: List[str] = Field(default_factory=list)
    style_guidelines: Optional[str] = None


class WriteRequest(BaseModel):
    """写作请求"""
    project_id: str = Field(..., description="所属项目ID")
    task_type: TaskType = Field(..., description="任务类型")
    topic: str = Field(..., description="写作主题")
    style: WritingStyle = Field(..., description="写作风格")
    character_ids: List[str] = Field(default_factory=list, description="角色ID列表")
    material_ids: List[str] = Field(default_factory=list, description="素材ID列表")
    custom_outline: Optional[List[Dict[str, Any]]] = Field(None, description="自定义大纲")
    iterations: int = Field(default=3, ge=1, le=10, description="迭代次数")
    target_length: Optional[int] = Field(None, description="目标字数")


class WriteResponse(BaseModel):
    """写作响应"""
    session_id: str
    status: str
    outline: Optional[WritingOutline] = None
    content: Optional[str] = None
    iterations_completed: int = 0
    feedback: Optional[str] = None


class RevisionRequest(BaseModel):
    """修改请求"""
    session_id: str
    instruction: str = Field(..., description="修改指令")
    target_section: Optional[str] = Field(None, description="目标段落")


# ========== 会话相关模型 ==========

class SessionStatus(str, Enum):
    """会话状态"""
    PENDING = "pending"
    PLANNING = "planning"
    WRITING = "writing"
    REVIEWING = "reviewing"
    ITERATING = "iterating"
    COMPLETED = "completed"
    FAILED = "failed"


class WritingSession(BaseModel):
    """写作会话"""
    id: Optional[str] = None
    task_type: TaskType
    topic: str
    style: WritingStyle
    character_ids: List[str] = Field(default_factory=list)
    material_ids: List[str] = Field(default_factory=list)
    outline: Optional[Dict[str, Any]] = None
    final_content: Optional[str] = None
    status: SessionStatus = SessionStatus.PENDING
    iterations: int = 0
    current_agent: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class VersionRecord(BaseModel):
    """版本记录"""
    id: Optional[str] = None
    session_id: str
    version_number: int
    content: str
    feedback: Optional[str] = None
    created_at: Optional[datetime] = None


# ========== 通用响应模型 ==========

class ApiResponse(BaseModel):
    """通用API响应"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[Any] = None
    error: Optional[str] = None
