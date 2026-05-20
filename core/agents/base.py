"""
Agent 基类
所有Agent的抽象基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from core.llm import LLMClient


@dataclass
class AgentConfig:
    """Agent配置"""
    name: str
    description: str
    system_prompt: str
    temperature: float = 0.7
    max_tokens: int = 2048
    model: Optional[str] = None


@dataclass
class AgentContext:
    """Agent执行上下文"""
    session_id: str
    task_type: str
    topic: str
    style: str
    characters: List[Dict[str, Any]] = field(default_factory=list)
    materials: List[Dict[str, Any]] = field(default_factory=list)
    outline: Optional[Dict[str, Any]] = None
    content: Optional[str] = None
    feedback: Optional[str] = None
    iteration: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_character(self, character: Dict[str, Any]):
        """添加角色"""
        self.characters.append(character)

    def add_material(self, material: Dict[str, Any]):
        """添加素材"""
        self.materials.append(material)


@dataclass
class AgentResult:
    """Agent执行结果"""
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Agent抽象基类"""

    def __init__(self, config: AgentConfig, llm_client: Optional[LLMClient] = None):
        """
        初始化Agent

        Args:
            config: Agent配置
            llm_client: LLM客户端
        """
        self.config = config
        self.llm = llm_client or LLMClient()
        self._system_prompt = config.system_prompt

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def description(self) -> str:
        return self.config.description

    def build_prompt(self, context: AgentContext, **kwargs) -> str:
        """
        构建Prompt
        子类可重写此方法

        Args:
            context: 执行上下文
            **kwargs: 其他参数

        Returns:
            完整的Prompt
        """
        return ""

    def build_system_prompt(self, context: AgentContext) -> str:
        """
        构建系统Prompt

        Args:
            context: 执行上下文

        Returns:
            系统Prompt
        """
        return self._system_prompt

    def execute(self, context: AgentContext, **kwargs) -> AgentResult:
        """
        同步执行Agent

        Args:
            context: 执行上下文
            **kwargs: 其他参数

        Returns:
            执行结果
        """
        try:
            prompt = self.build_prompt(context, **kwargs)
            system = self.build_system_prompt(context)

            output = self.llm.complete(
                prompt=prompt,
                system=system,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            return AgentResult(
                success=True,
                output=self.parse_output(output, context),
                metadata={"raw_output": output}
            )
        except Exception as e:
            return AgentResult(
                success=False,
                output=None,
                error=str(e)
            )

    async def aexecute(self, context: AgentContext, **kwargs) -> AgentResult:
        """
        异步执行Agent

        Args:
            context: 执行上下文
            **kwargs: 其他参数

        Returns:
            执行结果
        """
        try:
            prompt = self.build_prompt(context, **kwargs)
            system = self.build_system_prompt(context)

            output = await self.llm.acomplete(
                prompt=prompt,
                system=system,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            return AgentResult(
                success=True,
                output=self.parse_output(output, context),
                metadata={"raw_output": output}
            )
        except Exception as e:
            return AgentResult(
                success=False,
                output=None,
                error=str(e)
            )

    def parse_output(self, output: str, context: AgentContext) -> Any:
        """
        解析输出
        子类可重写此方法

        Args:
            output: 原始输出
            context: 执行上下文

        Returns:
            解析后的输出
        """
        return output

    def validate_context(self, context: AgentContext) -> bool:
        """
        验证上下文是否满足Agent执行条件
        子类可重写此方法

        Args:
            context: 执行上下文

        Returns:
            是否有效
        """
        return True
