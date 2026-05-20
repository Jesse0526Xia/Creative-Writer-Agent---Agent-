"""
Reviewer Agent - 质量评审
负责检查内容质量、发现问题
"""
import json
from typing import Dict, Any, List, Optional
from core.agents.base import BaseAgent, AgentConfig, AgentContext, AgentResult


# Reviewer System Prompt
REVIEWER_SYSTEM_PROMPT = """你是一位资深文字编辑和内容评审专家，拥有敏锐的文字感知能力和严谨的逻辑思维。

你的职责：
1. 严格审查内容的逻辑连贯性
2. 检查角色言行一致性
3. 评估风格统一性
4. 发现错别字和语法错误
5. 评估内容的可读性和感染力
6. **根据任务类型调整评审侧重点**

你必须根据任务类型调整评审侧重点：
- 文案（copywriting）：侧重转化力和吸引力、卖点是否清晰、CTA是否有效、受众定位是否准确
- 小说（novel）：侧重叙事节奏、人物塑造、情节张力、场景描写、心理刻画
- 文章（article）：侧重逻辑结构、论据充分性、论点清晰度、说服力、可读性
- 论文（paper）：侧重学术规范、研究方法严谨性、数据支撑、引用规范性、结论有据
- 剧本（script）：侧重对白质量、场景划分、角色调度、视听语言、节奏把控

你的评审应该客观、专业、具体，指出问题的同时给出改进建议。"""


# 任务类型评审侧重点
TASK_TYPE_REVIEW_FOCUS = {
    "copywriting": """
【文案类评审重点】
- 转化力：是否有清晰的CTA，能否促使行动
- 吸引力：开头是否吸引人，能否留住读者
- 卖点清晰度：核心卖点是否突出、差异化是否明显
- 受众定位：语言风格和内容是否针对目标受众
- 情感共鸣：是否能触发目标受众的情感反应
""",
    "novel": """
【小说类评审重点】
- 叙事节奏：章节推进是否流畅、高潮安排是否合理
- 人物塑造：角色是否立体、对话是否自然、心理刻画是否深刻
- 情节张力：冲突是否有力、悬念是否扣人
- 场景描写：环境氛围是否到位、细节是否生动
- 整体风格：是否统一、是否符合设定
""",
    "article": """
【文章类评审重点】
- 逻辑结构：论点是否清晰、论据是否充分、论证是否严密
- 说服力：观点是否鲜明、是否有启发性
- 可读性：语言是否流畅、结构是否清晰
- 深度：是否有独特见解、是否够深入
- 过渡：段落之间衔接是否自然
""",
    "paper": """
【论文类评审重点】
- 学术规范：格式是否符合要求、引用是否规范
- 研究方法：方法描述是否详细、是否科学合理
- 数据支撑：数据是否准确、分析是否到位
- 结论价值：结论是否有据、贡献是否明确
- 逻辑严谨：整体逻辑是否严密、论证是否充分
""",
    "script": """
【剧本类评审重点】
- 对白质量：台词是否有个性、是否推动剧情
- 场景划分：场景是否清晰、转场是否自然
- 角色调度：角色出场是否合理、互动是否有效
- 视听语言：动作指示是否清晰、镜头感是否强
- 节奏把控：节奏是否紧凑、是否吸引人
"""
}


# Reviewer User Prompt Template
REVIEWER_USER_PROMPT = """请对以下内容进行严格评审：

【内容】
{content}

【评审维度】
1. 逻辑连贯性：情节发展是否合理，前后是否矛盾
2. 角色一致性：角色言行是否与设定一致
3. 风格统一性：是否保持统一的风格基调
4. 语言质量：是否有错别字、语病、表达不清之处
5. 情感表达：情感是否真挚、是否打动人心
6. 创意亮点：是否有独特的创意或精彩描写
7. 任务类型适配度：内容是否符合所选任务类型的写作范式

【角色设定参考】
{characters}

【风格要求】
{style}

请输出JSON格式的评审结果：
{{
    "passed": true/false,  // 是否通过
    "overall_score": 85,   // 综合评分 0-100
    "issues": [
        {{
            "type": "logic/consistency/style/language/emotion/creativity/task_type_fit",
            "severity": "critical/major/minor",
            "location": "具体位置描述",
            "description": "问题描述",
            "suggestion": "改进建议"
        }}
    ],
    "strengths": ["优点1", "优点2"],
    "summary": "总体评价"
}}"""


# 简版Reviewer（快速评审）
REVIEWER_SIMPLE_PROMPT = """请快速评审以下内容，给出是否通过的判断：

【内容】
{content}

【评审要求】
- 逻辑是否通顺
- 是否有明显问题
- 风格是否符合要求

直接回复：
- PASS: 内容合格，可以继续
- FAIL: 内容有问题，需要修改
- 简短说明问题"""


class ReviewerAgent(BaseAgent):
    """内容评审Agent"""

    def __init__(self, llm_client=None):
        config = AgentConfig(
            name="Reviewer",
            description="内容评审 - 检查质量并提出改进建议",
            system_prompt=REVIEWER_SYSTEM_PROMPT,
            temperature=0.5,  # 较低温度保证评审客观
            max_tokens=4096
        )
        super().__init__(config, llm_client)

    def build_prompt(self, context: AgentContext, **kwargs) -> str:
        """构建评审Prompt"""
        content = context.content or "无内容"
        if len(content) > 5000:
            content = content[:5000] + "\n...(内容过长已截断)"

        # 角色信息
        characters_info = ""
        if context.characters:
            characters_info = "\n\n".join([
                f"【{c.get('name', '角色')}】\n{c.get('prompt_context', str(c))}"
                for c in context.characters
            ])
        else:
            characters_info = "无特定角色设定"

        # 风格评审描述（与Writer保持一致）
        style_map = {
            "literary": "文艺清新风格。特征：①善用细腻比喻和自然意象 ②情感含蓄不直白 ③节奏舒缓有留白 ④语言优美如诗 ⑤注重氛围营造 ⑥适合散文式表达",
            "business": "商务正式风格。特征：①使用专业术语和行业词汇 ②逻辑严密条理清晰 ③数据支撑观点 ④客观中立不情绪化 ⑤格式规范段落分明 ⑥适合报告/提案/公文",
            "casual": "随性自然风格。特征：①口语化表达像聊天 ②短句为主轻松随意 ③生活化场景和例子 ④不刻意修饰 ⑤语气亲切随和 ⑥适合自媒体/日常分享",
            "romantic": "浪漫温馨风格。特征：①情感饱满温暖 ②多用感官描写（触觉/嗅觉/视觉） ③亲密温柔的语气 ④细节中体现关怀 ⑤正向积极的能量 ⑥适合情书/纪念日/情感类内容",
            "humorous": "幽默风趣风格。特征：①善用双关和谐音梗 ②夸张对比制造笑点 ③适当自嘲降低距离感 ④节奏突变出其不意 ⑤轻松调侃不伤人 ⑥适合段子/社交媒体/轻松话题",
            "serious": "严肃深刻风格。特征：①批判性视角看问题 ②哲学或社会学思考深度 ③沉重主题不回避 ④措辞严谨庄重 ⑤层层剖析追根溯源 ⑥适合评论/时评/深度报道",
            "flowery": "华丽辞藻风格。特征：①排比和对偶修辞 ②古典诗词引用 ③繁复修饰浓墨重彩 ④视觉冲击力强的词汇 ⑤气势恢宏大气磅礴 ⑥适合古风/演讲稿/庆典文案",
            "simple": "简洁明了风格。特征：①短句精悍直接 ②去除一切冗余修饰 ③信息密度高 ④直击核心要点 ⑤不绕弯子 ⑥适合通知/说明书/技术文档/快节奏阅读"
        }
        style_display = style_map.get(context.style, context.style)

        # 获取任务类型专属评审重点
        review_focus = TASK_TYPE_REVIEW_FOCUS.get(
            context.task_type,
            "请根据一般写作标准进行评审。"
        )

        return REVIEWER_USER_PROMPT.format(
            content=content,
            characters=characters_info,
            style=style_display
        ) + f"\n\n【任务类型专属评审重点】\n{review_focus}\n\n【额外评审维度】\n7. 任务类型适配度：内容是否符合所选任务类型的写作范式"

    def parse_output(self, output: str, context: AgentContext) -> Dict[str, Any]:
        """解析评审输出"""
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

            return data
        except json.JSONDecodeError:
            # 如果JSON解析失败，尝试简单解析
            output_lower = output.lower().strip()
            if "pass" in output_lower and "fail" not in output_lower:
                return {
                    "passed": True,
                    "summary": output
                }
            elif "fail" in output_lower:
                return {
                    "passed": False,
                    "summary": output
                }
            else:
                return {
                    "passed": None,
                    "summary": output,
                    "parse_error": "Failed to parse structured response"
                }

    def quick_review(self, content: str) -> bool:
        """
        快速评审（同步）

        Args:
            content: 待评审内容

        Returns:
            是否通过
        """
        result = self.llm.complete(
            prompt=REVIEWER_SIMPLE_PROMPT.format(content=content[:2000]),
            system="你是一位严格的内容审核员，请快速判断内容是否合格。",
            temperature=0.3,
            max_tokens=500
        )

        result_lower = result.lower().strip()
        return "pass" in result_lower and "fail" not in result_lower

    def validate_context(self, context: AgentContext) -> bool:
        """验证上下文"""
        return bool(context.content)


def create_reviewer_agent(llm_client=None) -> ReviewerAgent:
    """创建Reviewer Agent"""
    return ReviewerAgent(llm_client)
