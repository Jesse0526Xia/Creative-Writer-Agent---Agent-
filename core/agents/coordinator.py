"""
Agent 协调器
管理多Agent协作流程
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from core.agents.base import AgentContext, AgentResult
from core.agents.planner import PlannerAgent, create_planner_agent
from core.agents.writer import WriterAgent, create_writer_agent
from core.agents.reviewer import ReviewerAgent, create_reviewer_agent
from core.agents.iterator import IteratorAgent, create_iterator_agent
from core.llm import LLMClient


@dataclass
class WorkflowState:
    """工作流状态"""
    current_agent: str = "idle"  # idle, planner, writer, reviewer, iterator
    stage: str = "initial"  # initial, planning, writing, reviewing, iterating, completed, failed
    outline: Optional[Dict[str, Any]] = None
    content: Optional[str] = None
    review_result: Optional[Dict[str, Any]] = None
    iterations: int = 0
    max_iterations: int = 3
    history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_agent": self.current_agent,
            "stage": self.stage,
            "outline": self.outline,
            "iterations": self.iterations,
            "max_iterations": self.max_iterations
        }


class AgentCoordinator:
    """多Agent协作协调器"""

    def __init__(
        self,
        planner: Optional[PlannerAgent] = None,
        writer: Optional[WriterAgent] = None,
        reviewer: Optional[ReviewerAgent] = None,
        iterator: Optional[IteratorAgent] = None,
        llm_client: Optional[LLMClient] = None
    ):
        """
        初始化协调器

        Args:
            planner: Planner Agent
            writer: Writer Agent
            reviewer: Reviewer Agent
            iterator: Iterator Agent
            llm_client: LLM客户端
        """
        self.llm = llm_client or LLMClient()
        self.planner = planner or create_planner_agent(self.llm)
        self.writer = writer or create_writer_agent(self.llm)
        self.reviewer = reviewer or create_reviewer_agent(self.llm)
        self.iterator = iterator or create_iterator_agent(self.llm)
        self.state = WorkflowState()

    def plan(self, context: AgentContext) -> AgentResult:
        """
        规划阶段

        Args:
            context: 执行上下文

        Returns:
            规划结果
        """
        self.state.current_agent = "planner"
        self.state.stage = "planning"

        result = self.planner.execute(context)

        if result.success:
            self.state.outline = result.output
            context.outline = result.output
            self.state.history.append({
                "agent": "planner",
                "result": "success",
                "output": result.output
            })

        self.state.current_agent = "idle"
        self.state.stage = "planned"

        return result

    def write(self, context: AgentContext) -> AgentResult:
        """
        写作阶段

        Args:
            context: 执行上下文

        Returns:
            写作结果
        """
        self.state.current_agent = "writer"
        self.state.stage = "writing"

        # 根据是否有大纲决定写作方式
        if context.outline and context.outline.get("outline"):
            # 按章节写作
            full_content = []
            outline_list = context.outline["outline"]

            for i, chapter in enumerate(outline_list):
                chapter_result = self.writer.write_chapter(
                    context,
                    chapter=chapter,
                    word_count=chapter.get("target_length", 1500)
                )

                if chapter_result.success:
                    full_content.append(f"\n\n{'='*20}\n")
                    full_content.append(f"第{chapter.get('chapter', i+1)}章：{chapter.get('title', '')}\n")
                    full_content.append(f"{'='*20}\n\n")
                    full_content.append(str(chapter_result.output))

                self.state.history.append({
                    "agent": "writer",
                    "chapter": chapter.get("title", f"Chapter {i+1}"),
                    "result": "success" if chapter_result.success else "failed",
                    "error": chapter_result.error
                })

            content = "".join(full_content)
        else:
            # 直接写作
            result = self.writer.write_full(context, word_count=3000)
            content = result.output if result.success else None

            self.state.history.append({
                "agent": "writer",
                "result": "success" if result.success else "failed",
                "error": result.error
            })

        if content:
            self.state.content = content
            context.content = content

        self.state.current_agent = "idle"
        self.state.stage = "written"

        return AgentResult(
            success=bool(content),
            output=content,
            metadata={"chapters_written": len(context.outline.get("outline", [])) if context.outline else 1}
        )

    def review(self, context: AgentContext) -> AgentResult:
        """
        评审阶段

        Args:
            context: 执行上下文

        Returns:
            评审结果
        """
        self.state.current_agent = "reviewer"
        self.state.stage = "reviewing"

        result = self.reviewer.execute(context)

        if result.success:
            self.state.review_result = result.output
            context.feedback = self._extract_feedback(result.output)

            self.state.history.append({
                "agent": "reviewer",
                "result": "success",
                "passed": result.output.get("passed", None),
                "score": result.output.get("overall_score", None)
            })

        self.state.current_agent = "idle"
        self.state.stage = "reviewed"

        return result

    def iterate(self, context: AgentContext) -> AgentResult:
        """
        迭代阶段

        Args:
            context: 执行上下文

        Returns:
            迭代结果
        """
        self.state.current_agent = "iterator"
        self.state.stage = "iterating"
        self.state.iterations += 1

        result = self.iterator.full_revision(context)

        if result.success:
            self.state.content = result.output
            context.content = result.output

            self.state.history.append({
                "agent": "iterator",
                "iteration": self.state.iterations,
                "result": "success"
            })

        self.state.current_agent = "idle"

        return result

    def _extract_feedback(self, review_result: Dict[str, Any]) -> str:
        """从评审结果中提取反馈"""
        if not review_result:
            return "无具体反馈"

        issues = review_result.get("issues", [])
        if not issues:
            return review_result.get("summary", "无具体反馈")

        feedback_parts = ["评审反馈：\n"]
        for i, issue in enumerate(issues[:5], 1):  # 最多5条
            feedback_parts.append(f"{i}. [{issue.get('severity', 'unknown')}] {issue.get('description', '')}")
            if issue.get('suggestion'):
                feedback_parts.append(f"   建议: {issue['suggestion']}")

        return "\n".join(feedback_parts)

    def run_full_workflow(
        self,
        context: AgentContext,
        max_iterations: int = 3,
        auto_approve: bool = False
    ) -> Dict[str, Any]:
        """
        运行完整工作流

        Args:
            context: 执行上下文
            max_iterations: 最大迭代次数
            auto_approve: 是否自动批准（跳过评审）

        Returns:
            最终结果
        """
        self.state.max_iterations = max_iterations

        # 1. 规划
        plan_result = self.plan(context)
        if not plan_result.success:
            return {
                "status": "failed",
                "stage": "planning",
                "error": plan_result.error
            }

        # 2. 写作
        write_result = self.write(context)
        if not write_result.success:
            return {
                "status": "failed",
                "stage": "writing",
                "error": write_result.error
            }

        # 3. 迭代评审
        for i in range(max_iterations):
            # 评审
            review_result = self.review(context)

            if review_result.success:
                passed = review_result.output.get("passed", False)
                score = review_result.output.get("overall_score", 0)

                # 高分或auto_approve则通过
                if passed or score >= 85 or auto_approve:
                    return {
                        "status": "completed",
                        "outline": self.state.outline,
                        "content": self.state.content,
                        "iterations": self.state.iterations,
                        "final_score": score,
                        "history": self.state.history
                    }

            # 迭代修改
            if self.state.iterations < max_iterations:
                self.iterate(context)
            else:
                break

        return {
            "status": "completed",
            "outline": self.state.outline,
            "content": self.state.content,
            "iterations": self.state.iterations,
            "final_score": self.state.review_result.get("overall_score") if self.state.review_result else None,
            "history": self.state.history
        }

    def get_state(self) -> WorkflowState:
        """获取当前状态"""
        return self.state


def create_coordinator(llm_client=None) -> AgentCoordinator:
    """创建协调器"""
    return AgentCoordinator(llm_client=llm_client)
