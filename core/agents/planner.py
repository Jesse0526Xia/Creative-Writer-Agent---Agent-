"""
Planner Agent - 写作规划师
负责分析需求、生成大纲、拆解任务
"""
import json
from typing import Dict, Any, Optional
from core.agents.base import BaseAgent, AgentConfig, AgentContext, AgentResult
from models.schemas import TaskType, WritingStyle


# Planner System Prompt
PLANNER_SYSTEM_PROMPT = """你是一位资深创意写作规划师，拥有丰富的写作教学和内容策划经验。

你的职责：
1. 深入分析用户的写作需求和偏好
2. 选择合适的写作风格和结构
3. 生成详细、合理的章节大纲
4. 为每个章节指定关键要素和叙事要点
5. **根据任务类型采用不同的大纲结构规划策略**

【关键约束】你必须严格根据任务类型采用完全不同的大纲结构规划策略，不同类型之间绝不能混用结构：
- 文案（copywriting）：营销导向结构。使用"版本A/B/C"或"段落模块"，绝对禁止出现"章节""章"等小说结构。必须包含：核心卖点→目标受众→痛点共鸣→解决方案→CTA行动号召
- 小说（novel）：叙事导向结构。使用"章节"结构，每章必须包含：场景设定→角色出场→关键情节→冲突升级→伏笔与回收。注重叙事节奏和人物弧线
- 文章（article）：论证导向结构。使用"论点"层次，必须包含：引言/钩子→核心论点1-3→论据/案例→过渡衔接→结论升华。层层递进的说服逻辑
- 论文（paper）：学术规范结构。使用"学术模块"，必须包含：摘要要点→研究背景→文献综述→研究方法→预期结果→讨论角度→结论贡献。严谨的学术脉络
- 剧本（script）：视听导向结构。使用"场景"结构（Scene 1, Scene 2），必须包含：场景地点/时间→角色出场→对白要点→动作/镜头指示→转场方式。注重视听语言表达

【禁止行为】文案类型输出小说章节、论文类型输出故事剧情、剧本类型输出论证结构——每种类型必须严格对应自身结构，否则视为错误输出。

你的输出必须是结构化的JSON格式，包含以下字段：
- task_type: 任务类型
- writing_style: 风格描述
- target_audience: 目标读者
- outline: 大纲数组（结构因任务类型而异）
- character_requirements: 角色要求
- style_guidelines: 风格指导

请确保大纲逻辑清晰、层次分明，每个章节都有明确的目标。"""


# 不同任务类型的大纲结构要求
OUTLINE_STRUCTURE_REQUIREMENTS = {
    "copywriting": """
【文案类大纲结构要求】
- 不要出现"章节"概念，使用"版本A/B/C"或"段落模块"
- 必须包含以下模块：
  1. 核心卖点：产品/服务的独特价值主张
  2. 目标受众：明确的目标人群画像
  3. 痛点共鸣：目标受众的痛点和需求
  4. 产品/服务介绍：解决方案的呈现
  5. 行动号召（CTA）：明确的转化引导
- 每个模块需标注建议字数和呈现形式
""",
    "novel": """
【小说类大纲结构要求】
- 采用"章节"结构，每个章节需包含：
  1. 章节标题：简洁有力的章节名
  2. 场景设定：时间、地点、环境氛围
  3. 角色出场安排：本章出场的角色
  4. 关键情节：本章的核心事件
  5. 冲突升级：推动故事发展的矛盾点
  6. 伏笔与回收：埋下的伏笔或本章回收的内容
- 注意章节之间的节奏把控
""",
    "article": """
【文章类大纲结构要求】
- 采用清晰的逻辑结构，包含：
  1. 引言/钩子：吸引读者的开头
  2. 核心论点1-3：文章的主要观点
  3. 论据/案例：支撑论点的具体案例
  4. 过渡衔接：段落之间的逻辑过渡
  5. 结论/升华：总结和升华
- 注意层层递进的逻辑性
""",
    "paper": """
【论文类大纲结构要求】
- 遵循学术规范的结构，包含：
  1. 摘要要点：研究内容和主要贡献
  2. 研究背景：问题的提出
  3. 文献综述方向：相关研究梳理
  4. 研究方法：采用的研究手段
  5. 预期结果：研究的可能发现
  6. 讨论角度：结果的意义和影响
  7. 结论贡献：研究的学术价值
- 注重研究的完整性和严谨性
""",
    "script": """
【剧本类大纲结构要求】
- 采用场景结构，包含：
  1. 场景编号：Scene 1, Scene 2...
  2. 场景地点/时间：内景/外景，日/夜
  3. 角色出场：本场景出场的角色
  4. 对白要点：主要对话内容
  5. 动作/镜头指示：角色的动作和镜头要求
  6. 转场方式：场景之间的过渡
- 注重视听语言的表达
"""
}


# Planner User Prompt Template
PLANNER_USER_PROMPT = """请为以下写作任务制定详细的大纲：

【任务类型】
{task_type}

【主题】
{topic}

【风格要求】
{style}

【角色设定】
{characters}

【素材参考】
{materials}

【其他要求】
{additional_requirements}

请生成详细的大纲，确保：
1. 逻辑清晰、层次分明
2. 每个章节有明确的目标和关键情节
3. 角色出场和互动合理安排
4. 符合指定的风格要求

输出格式：JSON"""



class PlannerAgent(BaseAgent):
    """写作规划Agent"""

    def __init__(self, llm_client=None):
        config = AgentConfig(
            name="Planner",
            description="写作规划师 - 分析需求并生成大纲",
            system_prompt=PLANNER_SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=4096
        )
        super().__init__(config, llm_client)

    def build_prompt(self, context: AgentContext, **kwargs) -> str:
        """构建规划Prompt"""
        # 格式化角色信息
        characters_info = ""
        if context.characters:
            characters_info = "\n".join([
                f"- {c.get('name', '未命名')}: {c.get('personality', '性格未设定')}"
                for c in context.characters
            ])
        else:
            characters_info = "无特定角色要求"

        # 格式化素材信息
        materials_info = ""
        if context.materials:
            materials_info = "\n".join([
                f"- [{m.get('file_name', '素材')}] {m.get('content', '')[:200]}..."
                for m in context.materials[:3]  # 限制数量
            ])
        else:
            materials_info = "无特定素材参考"

        # 任务类型
        task_type_map = {
            "novel": "小说",
            "article": "文章",
            "copywriting": "文案",
            "paper": "论文",
            "script": "剧本"
        }
        task_type_display = task_type_map.get(context.task_type, context.task_type)

        # 风格映射
        style_map = {
            "literary": "文艺清新",
            "business": "商务正式",
            "casual": "随性自然",
            "romantic": "浪漫温馨",
            "humorous": "幽默风趣",
            "serious": "严肃深刻",
            "flowery": "华丽辞藻",
            "simple": "简洁明了"
        }
        style_display = style_map.get(context.style, context.style)

        # 获取任务类型专属大纲结构要求
        outline_structure = OUTLINE_STRUCTURE_REQUIREMENTS.get(
            context.task_type, 
            "请根据任务类型合理规划大纲结构。"
        )

        # 构建追加的结构要求
        additional_structure_note = f"\n\n【大纲结构规范】\n{outline_structure}"

        # 将结构要求追加到额外要求中
        full_additional_requirements = (
            kwargs.get("additional_requirements", "无") + additional_structure_note
        )

        return PLANNER_USER_PROMPT.format(
            task_type=task_type_display,
            topic=context.topic,
            style=style_display,
            characters=characters_info,
            materials=materials_info,
            additional_requirements=full_additional_requirements
        )

    def parse_output(self, output: str, context: AgentContext) -> Dict[str, Any]:
        """解析大纲输出"""
        try:
            # 尝试解析JSON
            if "```json" in output:
                start = output.find("```json") + 7
                end = output.find("```", start)
                if end > start:
                    data = json.loads(output[start:end].strip())
                else:
                    data = json.loads(output[start:].strip())
            else:
                data = json.loads(output)

            # 验证必要字段
            if "outline" not in data:
                data["outline"] = []

            return data
        except json.JSONDecodeError as e:
            # 如果JSON解析失败，返回原始文本并标记
            return {
                "outline_text": output,
                "outline": [],
                "parse_error": str(e)
            }

    def validate_context(self, context: AgentContext) -> bool:
        """验证上下文"""
        return bool(context.topic)


def create_planner_agent(llm_client=None) -> PlannerAgent:
    """创建Planner Agent"""
    return PlannerAgent(llm_client)
