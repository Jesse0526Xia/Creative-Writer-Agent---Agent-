"""
Writer Agent - 写作执行者
负责根据大纲进行内容创作
"""
import json
from typing import Dict, Any, Optional, List
from core.agents.base import BaseAgent, AgentConfig, AgentContext, AgentResult


# Writer System Prompt
WRITER_SYSTEM_PROMPT = """你是一位专业作家，擅长各种文体的创作，包括小说、散文、文案、论文、剧本等。

你的写作原则：
1. 保持文字流畅、生动、有感染力
2. 严格遵循角色设定，保持人物一致性
3. 参考素材时自然融入，不生搬硬套
4. 风格统一，符合任务要求
5. 逻辑连贯，情节发展合理
6. **根据任务类型采用专属写作范式**

任务类型专属写作范式：
- 文案（copywriting）：营销导向、短句有力、痛点切入、利益点突出、明确的CTA结尾、适合社交媒体/广告传播
- 小说（novel）：叙事驱动、场景细腻描写、人物心理刻画、对话自然、情节有张力、注重节奏感
- 文章（article）：逻辑论证清晰、论据充分、层层递进、观点鲜明、可读性强、有启发性
- 论文（paper）：学术规范、客观严谨、方法描述详细、数据支撑、引用规范、结论有据
- 剧本（script）：对话驱动叙事、场景指示清晰、视听语言思维、节奏紧凑、角色对白有个性、转场自然

你的输出应该直接是创作内容，不需要额外解释。"""


# 任务类型专属写作范式要求
WRITING_PARADIGM_REQUIREMENTS = {
    "copywriting": """
【文案写作范式】
- 开头：痛点切入，引发共鸣
- 中段：产品/服务价值展示
- 结尾：明确的行动号召（CTA）
- 语言：短句有力，适合快速阅读
- 情感：积极正向，传递正能量
- 格式：适合社交媒体/广告传播
""",
    "novel": """
【小说写作范式】
- 叙事视角：保持一致的人称和视角
- 场景描写：细腻的环境和氛围营造
- 人物刻画：丰富的心理描写和对话
- 情节推进：合理的冲突和悬念设置
- 节奏把控：松紧有度，张弛结合
- 语言风格：符合整体基调
""",
    "article": """
【文章写作范式】
- 开篇：引人入胜的引言或问题
- 论点展开：清晰的逻辑层次
- 论据支撑：具体案例和数据
- 过渡衔接：段落之间的自然过渡
- 结论升华：有力的收尾和启发
- 语言风格：严谨但不刻板，易读性强
""",
    "paper": """
【论文写作范式】
- 摘要：精炼的研究概述
- 引言：研究背景和意义
- 方法：详细的研究方法描述
- 结果：客观的数据呈现
- 讨论：深入的结论分析
- 参考文献：规范的引用格式
- 语言风格：客观严谨，学术规范
""",
    "script": """
【剧本写作范式】
- 场景描述：清晰的场景划分
- 角色动作：明确的行为指示
- 对白设计：符合角色性格的对话
- 镜头指示：视听语言的表达
- 节奏控制：紧凑的叙事节奏
- 转场处理：自然的场景过渡
"""
}


# Writer User Prompt Template
WRITER_USER_PROMPT = """请根据以下大纲和设定，创作完整的{content_type}内容：

【章节/任务】
{chapter_info}

【整体大纲】
{outline_summary}

【风格要求】
{style}

【角色设定】
{characters}

【素材参考】
{materials}

【写作要求】
{writing_requirements}

请直接输出创作内容，确保：
1. 内容丰富、细节生动
2. 严格遵循大纲结构
3. 角色言行符合设定
4. 自然融入素材内容
5. 字数要求：{word_count}字

开始写作："""


class WriterAgent(BaseAgent):
    """写作Agent"""

    def __init__(self, llm_client=None):
        config = AgentConfig(
            name="Writer",
            description="写作执行者 - 根据大纲创作内容",
            system_prompt=WRITER_SYSTEM_PROMPT,
            temperature=0.8,  # 稍高温度增加创意性
            max_tokens=8192
        )
        super().__init__(config, llm_client)

    def build_prompt(
        self,
        context: AgentContext,
        chapter: Optional[Dict[str, Any]] = None,
        word_count: int = 1000,
        **kwargs
    ) -> str:
        """构建写作Prompt"""

        # 章节信息
        if chapter:
            chapter_info = f"第{chapter.get('chapter', '?')}章：{chapter.get('title', '无标题')}\n"
            chapter_info += "关键要点：\n" + "\n".join([
                f"- {point}" for point in chapter.get('key_points', [])
            ])
        else:
            chapter_info = "完整创作"

        # 大纲摘要
        outline_summary = ""
        if context.outline and isinstance(context.outline, dict):
            outline_list = context.outline.get("outline", [])
            if outline_list:
                outline_summary = "章节结构：\n" + "\n".join([
                    f"{i+1}. {ch.get('title', '未命名')}"
                    for i, ch in enumerate(outline_list)
                ])

        # 角色设定
        characters_info = ""
        if context.characters:
            characters_info = "\n\n".join([
                f"【{c.get('name', '角色')}】\n{c.get('prompt_context', str(c))}"
                for c in context.characters
            ])
        else:
            characters_info = "无特定角色设定"

        # 素材参考
        materials_info = ""
        if context.materials:
            materials_info = "\n\n".join([
                f"【素材：{m.get('file_name', '参考')}】\n{m.get('content', '')}"
                for m in context.materials
            ])
        else:
            materials_info = "无参考素材"

        # 内容类型
        task_type_map = {
            "novel": "小说章节",
            "article": "文章",
            "copywriting": "文案",
            "paper": "论文",
            "script": "剧本片段"
        }
        content_type = task_type_map.get(context.task_type, "内容")

        # 风格映射（详细描述 + 强制约束）
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
        # 风格强制约束 - 要求LLM必须遵循的核心写作规则
        style_constraint = {
            "literary": "【强制约束】全文必须体现文艺清新特征：每段至少一处自然意象描写（花草、天气、光影等）。情感含蓄不直白，用景物烘托心情。节奏舒缓，有意留白。语言如诗如画。",
            "business": "【强制约束】全文必须体现商务正式特征：使用专业术语和行业词汇。观点必须有数据或案例支撑。逻辑严密，段落分明。客观中立，禁止情绪化表达。格式规范。",
            "casual": "【强制约束】全文必须体现随性自然特征：口语化表达，像和朋友聊天。多用短句（10字以内为主）。生活化场景，不刻意修饰。语气亲切随和，可用网络流行语。",
            "romantic": "【强制约束】全文必须体现浪漫温馨特征：多用感官描写（触觉/嗅觉/视觉/听觉）。温暖亲密语气，如耳语般轻柔。细节中体现关怀。结尾必须正向积极，传递温暖能量。",
            "humorous": "【强制约束】全文必须体现幽默风趣特征：至少一处双关/谐音梗或夸张对比。适当自嘲降低距离感。节奏突变出其不意。轻松调侃但不伤人。让人会心一笑。",
            "serious": "【强制约束】全文必须体现严肃深刻特征：批判性视角审视问题。有哲学或社会学思考深度。措辞严谨庄重。层层剖析追根溯源。不回避沉重主题，不轻浮。",
            "flowery": "【强制约束】全文必须体现华丽辞藻特征：至少一处排比或对偶修辞。可引用古典诗词。繁复修饰浓墨重彩。视觉冲击力强的词汇。气势磅礴大气磅礴。",
            "simple": "【强制约束】全文必须体现简洁明了特征：短句精悍（每句不超过15字）。去除一切冗余修饰和形容词堆砌。直击核心要点。信息密度高。不用华丽辞藻，不用长句。"
        }
        style_display = style_map.get(context.style, context.style)
        style_force = style_constraint.get(context.style, "")

        # 获取任务类型专属写作范式要求
        writing_paradigm = WRITING_PARADIGM_REQUIREMENTS.get(
            context.task_type,
            "遵循一般写作规范。"
        )

        # 追加任务类型写作范式到要求中
        paradigm_note = f"\n\n【任务类型写作范式】\n{writing_paradigm}"

        # 写作要求（追加任务类型范式）
        requirements = kwargs.get("requirements", [])
        requirements_text = "\n".join([f"- {r}" for r in requirements]) if requirements else ""
        if requirements_text:
            requirements_text += paradigm_note
        else:
            requirements_text = paradigm_note.strip()

        # 组合风格描述和强制约束
        full_style = style_display
        if style_force:
            full_style += f"\n\n{style_force}"

        return WRITER_USER_PROMPT.format(
            content_type=content_type,
            chapter_info=chapter_info,
            outline_summary=outline_summary,
            style=full_style,
            characters=characters_info,
            materials=materials_info,
            writing_requirements=requirements_text if requirements_text else "无特殊要求",
            word_count=word_count
        )

    def write_chapter(
        self,
        context: AgentContext,
        chapter: Dict[str, Any],
        word_count: int = 1500
    ) -> AgentResult:
        """写单个章节"""
        return self.execute(context, chapter=chapter, word_count=word_count)

    def write_full(
        self,
        context: AgentContext,
        word_count: int = 3000
    ) -> AgentResult:
        """写完整内容（无大纲时）"""
        return self.execute(context, word_count=word_count)

    def validate_context(self, context: AgentContext) -> bool:
        """验证上下文"""
        return bool(context.topic)


def create_writer_agent(llm_client=None) -> WriterAgent:
    """创建Writer Agent"""
    return WriterAgent(llm_client)
