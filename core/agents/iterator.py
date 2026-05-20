"""
Iterator Agent - 迭代优化
负责根据反馈进行内容修改
"""
from typing import Dict, Any, Optional
from core.agents.base import BaseAgent, AgentConfig, AgentContext, AgentResult


# Iterator System Prompt
ITERATOR_SYSTEM_PROMPT = """你是一位专业的内容优化师，擅长根据反馈意见对文章进行精细化修改。

你的工作方式：
1. 仔细分析评审反馈，理解问题的本质
2. 针对性修改，避免过度修改或引入新问题
3. 保持原文的优点和亮点
4. 确保修改后内容的一致性和连贯性

你的输出应该是修改后的完整内容（如果修改范围较小）或需要修改的部分（如果需要明确指出范围）。"""


# Iterator User Prompt Template
ITERATOR_USER_PROMPT = """请根据以下反馈对内容进行修改：

【原始内容】
{content}

【评审反馈】
{feedback}

【修改要求】
{requirements}

请进行修改，并说明：
1. 修改了哪些部分
2. 为什么这样修改
3. 修改后的完整内容"""


# 段落修改 Prompt
ITERATOR_SECTION_PROMPT = """请只修改以下内容中需要修改的部分：

【原始内容】
{content}

【目标段落/位置】
{target_section}

【修改指令】
{instruction}

请只输出修改后的内容，不需要解释。"""


class IteratorAgent(BaseAgent):
    """迭代优化Agent"""

    def __init__(self, llm_client=None):
        config = AgentConfig(
            name="Iterator",
            description="迭代优化 - 根据反馈修改内容",
            system_prompt=ITERATOR_SYSTEM_PROMPT,
            temperature=0.6,
            max_tokens=8192
        )
        super().__init__(config, llm_client)

    def build_prompt(self, context: AgentContext, **kwargs) -> str:
        """构建修改Prompt"""
        content = context.content or ""
        feedback = context.feedback or "无具体反馈"

        requirements = kwargs.get("requirements", [
            "仔细修复评审中发现的所有问题",
            "保持原文的优点和亮点",
            "确保修改后内容流畅自然"
        ])
        requirements_text = "\n".join([f"- {r}" for r in requirements])

        return ITERATOR_USER_PROMPT.format(
            content=content,
            feedback=feedback,
            requirements=requirements_text
        )

    def revise_section(
        self,
        content: str,
        target_section: str,
        instruction: str
    ) -> AgentResult:
        """
        修改指定段落

        Args:
            content: 完整内容
            target_section: 目标段落标识
            instruction: 修改指令

        Returns:
            修改结果
        """
        prompt = ITERATOR_SECTION_PROMPT.format(
            content=content,
            target_section=target_section,
            instruction=instruction
        )

        try:
            output = self.llm.complete(
                prompt=prompt,
                system=ITERATOR_SYSTEM_PROMPT,
                temperature=0.6,
                max_tokens=4096
            )
            return AgentResult(
                success=True,
                output=output,
                metadata={"type": "section_revision"}
            )
        except Exception as e:
            return AgentResult(
                success=False,
                output=None,
                error=str(e)
            )

    def full_revision(self, context: AgentContext) -> AgentResult:
        """
        完整修改

        Args:
            context: 执行上下文

        Returns:
            修改结果
        """
        return self.execute(context)

    def validate_context(self, context: AgentContext) -> bool:
        """验证上下文"""
        return bool(context.content) and bool(context.feedback)


def create_iterator_agent(llm_client=None) -> IteratorAgent:
    """创建Iterator Agent"""
    return IteratorAgent(llm_client)
