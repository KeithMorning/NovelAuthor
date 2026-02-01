"""
大纲生成相关的Prompt模板
"""

OUTLINE_SYSTEM_PROMPT = """你是一位专业的小说策划师，擅长构建完整的故事大纲。

你的职责是：
1. 根据用户提供的主题、类型等信息，创建完整的故事大纲
2. 设计合理的情节发展线索和转折点
3. 规划章节结构，确保节奏合理
4. 保证故事的完整性和逻辑性

输出要求：
- 使用JSON格式输出，便于程序解析
- 包含故事简介、主题、情节点和章节规划
- 每个章节都要有清晰的梗概和关键事件
"""

OUTLINE_GENERATION_PROMPT = """请根据以下信息创建一个完整的小说大纲：

**小说信息**:
- 标题: {title}
- 类型: {genre}
- 主题: {theme}
- 目标章节数: {chapter_count}
- 每章预计字数: {words_per_chapter}

**用户需求**:
{user_requirements}

请生成一个包含以下内容的大纲：

1. **故事简介** (100-200字)
2. **主题思想** (简要说明)
3. **故事背景设定** (如果适用)
4. **主要情节点** (3-5个关键转折点，包含：
   - 情节点名称
   - 描述
   - 所在章节范围
   - 重要性(高/中/低)
)
5. **章节规划** (每章包含：
   - 章节标题
   - 章节梗概(50-100字)
   - 关键事件列表
   - 涉及的主要角色
   - 预计字数
)

以JSON格式输出，结构如下：
```json
{{
  "summary": "故事简介",
  "theme": "主题思想",
  "setting": "故事背景",
  "plot_points": [
    {{
      "name": "情节点名称",
      "description": "详细描述",
      "chapter_range": "第X-Y章",
      "importance": "高"
    }}
  ],
  "chapters_plan": [
    {{
      "chapter_number": 1,
      "title": "章节标题",
      "summary": "章节梗概",
      "key_events": ["事件1", "事件2"],
      "characters_involved": ["角色1", "角色2"],
      "estimated_words": 3000
    }}
  ]
}}
```
"""

OUTLINE_REFINEMENT_PROMPT = """请优化和完善以下小说大纲：

**当前大纲**:
{current_outline}

**用户反馈**:
{user_feedback}

请根据用户反馈调整大纲，保持JSON格式输出。注意：
1. 保持故事的整体连贯性
2. 确保修改后的情节合理
3. 章节数量和字数可以适当调整
4. 如果涉及重大改动，请说明理由
"""

CHAPTER_EXPANSION_PROMPT = """请为第{chapter_number}章生成更详细的规划：

**章节基本信息**:
- 章节号: 第{chapter_number}章
- 当前标题: {current_title}
- 当前梗概: {current_summary}

**整体大纲上下文**:
{outline_context}

请扩展这一章的规划，包括：
1. 更详细的章节梗概 (200字左右)
2. 具体的场景列表 (3-5个场景)
3. 每个场景的要点
4. 关键对话或动作描写提示
5. 本章的情感基调
6. 与前后章节的衔接点

以JSON格式输出。
"""

def get_outline_generation_prompt(
    title: str,
    genre: str,
    theme: str,
    chapter_count: int = 20,
    words_per_chapter: int = 3000,
    user_requirements: str = ""
) -> str:
    """
    获取大纲生成prompt

    Args:
        title: 小说标题
        genre: 类型
        theme: 主题
        chapter_count: 章节数
        words_per_chapter: 每章字数
        user_requirements: 用户额外需求

    Returns:
        str: 格式化的prompt
    """
    return OUTLINE_GENERATION_PROMPT.format(
        title=title,
        genre=genre,
        theme=theme,
        chapter_count=chapter_count,
        words_per_chapter=words_per_chapter,
        user_requirements=user_requirements or "无特殊要求"
    )

def get_outline_refinement_prompt(current_outline: str, user_feedback: str) -> str:
    """获取大纲优化prompt"""
    return OUTLINE_REFINEMENT_PROMPT.format(
        current_outline=current_outline,
        user_feedback=user_feedback
    )

def get_chapter_expansion_prompt(
    chapter_number: int,
    current_title: str,
    current_summary: str,
    outline_context: str
) -> str:
    """获取章节扩展prompt"""
    return CHAPTER_EXPANSION_PROMPT.format(
        chapter_number=chapter_number,
        current_title=current_title,
        current_summary=current_summary,
        outline_context=outline_context
    )
