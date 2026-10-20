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
- 包含故事简介、主题、情节点等
"""

PRELIMINARY_OUTLINE_GENERATION_PROMPT = """请根据以下信息创建一个小说的初级大纲（无需细化章节，仅构建世界观和故事主轴）：

**小说信息**:
- 标题: {title}
- 类型: {genre}
- 主题: {theme}
- 预计总章节数: {chapter_count}

**核心概念与设定（强制物理法则/世界观约束）**:
{core_concepts}

**用户需求**:
{user_requirements}

请生成一个包含以下内容的初级大纲：

1. **故事简介** (150-300字，要求包含核心冲突、高潮点和结局走向)
2. **主题思想** (简要说明故事探讨的深层问题)
3. **故事背景设定** (详细描述世界观、核心设定和环境氛围)
4. **主要情节点** (要求：
   - 如果总章节数 <= 10，请设计 3-5 个关键转折点
   - 如果总章节数 > 10，请设计 6-10 个关键转折点
   - 每个情节点包含：名称、描述、所在章节范围、重要性
   - 确保情节点的分布合理，避免出现故事中后期情节稀释或节奏拖累)
5. **核心冲突与核心对立面规划**（重要！必须包含）：
   - 冲突的核心性质（理念分歧、生存资源、信息不对称等，而非简单的善恶对立）
   - 持不同理念者/对立面的核心动机（为什么他们认为自己是对的）
   - 对立面的能力和威胁程度（要与主角方形成有效制衡）
   - 核心冲突如何随着情节推进而演变、升级
   - 关键理念对抗节点（至少3个主要冲突爆发点）

以JSON格式输出，结构如下：
```json
{{
  "summary": "故事简介",
  "theme": "主题思想",
  "core_concepts": "核心概念与世界观设定",
  "setting": "故事背景",
  "plot_points": [
    {{
      "name": "情节点名称",
      "description": "详细描述",
      "chapter_range": "第X-Y章",
      "importance": "高"
    }}
  ]
}}
```
"""

OUTLINE_GENERATION_PROMPT = """请根据以下信息创建一个完整的小说大纲：

**小说信息**:
- 标题: {title}
- 类型: {genre}
- 主题: {theme}
- 目标章节数: {chapter_count}
- 每章预计字数: {words_per_chapter}

**核心概念与设定（高级限制：所有情节必须绝对符合此逻辑）**:
{core_concepts}

**用户需求**:
{user_requirements}

**初级大纲 (必须遵循此故事脉络与世界观)**:
{preliminary_outline_content}

**角色设定 (严格按照此设定安排剧情)**:
{character_info}

请生成一个包含以下内容的大纲：

1. **故事简介** (150-300字，要求包含核心冲突、高潮点和结局走向)
2. **主题思想** (简要说明故事探讨的深层问题)
3. **故事背景设定** (详细描述世界观、核心设定和环境氛围)
4. **主要情节点** (要求：
   - 如果总章节数 <= 10，请设计 3-5 个关键转折点
   - 如果总章节数 > 10，请设计 6-10 个关键转折点
   - 每个情节点包含：名称、描述、所在章节范围、重要性
   - 确保情节点的分布合理，避免出现故事中后期情节稀释或节奏拖累)
5. **核心冲突与核心对立面规划**（重要！必须包含）：
   - 冲突的核心性质（理念分歧、生存资源、信息不对称等，而非简单的善恶对立）
   - 持不同理念者/对立面的核心动机（为什么他们认为自己是对的）
   - 对立面的能力和威胁程度（要与主角方形成有效制衡）
   - 核心冲突如何随着情节推进而演变、升级
   - 关键理念对抗节点（至少3个主要冲突爆发点）
6. **章节规划** (要求：
   - 【关键指令】你必须精确生成恰好 {chapter_count} 个章节规划！不能多也不能少。
   - 每章包含：章节标题、章节梗概、关键事件列表、涉及角色、预计字数
   - 章节梗概应具体到本章的行为驱动（不仅是发生了什么，还有为什么发生）
   - 关键事件应包含 3-4 个具体的冲突点或情感转折点
   - 【严格角色出场逻辑】**绝对不要**为了让所有角色露脸而强行把他们塞进章节中！每一章的 `characters_involved` 只能包含那些**真正在本章节推动了核心剧情**的角色。如果某人的出场不符合当前的剧情推理逻辑，就不要写他。
   - 确保每一章都有明确的叙事任务，严禁出现"为了填充字数"的平淡章节)

以JSON格式输出，结构如下：
```json
{{
  "summary": "故事简介",
  "theme": "主题思想",
  "core_concepts": "核心概念与世界观设定",
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
      "key_events": ["冲突点/事件1", "冲突点/事件2", "情感转折/事件3"],
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

PRELIMINARY_OUTLINE_REFINEMENT_PROMPT = """请优化和完善以下小说的初级大纲：

**当前初级大纲**:
{current_outline}

**用户反馈**:
{user_feedback}

请根据用户反馈调整初级大纲，保持JSON格式输出，仅构建世界观和故事主轴，无需细化章节。注意：
1. 保持故事的整体连贯性
2. 确保修改后的情节合理
3. 保持原有结构：故事简介、主题、世界观、主要情节点等。

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
  ]
}}
```
"""

CHAPTER_EXPANSION_PROMPT = """请为第{chapter_number}章生成更详细的规划：

**章节基本信息**:
- 章节号: 第{chapter_number}章
- 当前标题: {current_title}
- 当前梗概: {current_summary}

**实际故事上下文 (MUST FOLLOW)**:
{story_context}

**整体大纲上下文 (Reference)**:
{outline_context}

**核心指令: 渐进式适配 (Progressive Adaptation)**
1. **世界状态优先**: 上方的 [实际故事上下文] 是已发生的既定事实。如果它与 [大纲上下文] 冲突，**必须以实际故事上下文为准**。
   - **禁止复活**: 如果角色在 [实际故事上下文] 中标记为"已死亡"或"下线"，他们 **绝对不能** 在本章作为活跃角色出现。
   - **剧情替补 (Substitution)**: 如果原大纲安排了已死亡角色进行关键行动，你必须 **指派其他合适的在场角色** 替代其完成该行动，确保主线剧情逻辑得以延续。
2. **剧情连贯性**: 请根据 [最近实际剧情] 推演本章的开篇，确保与上一章的结尾自然衔接，填补大纲与实际剧情之间的空白。

请扩展这一章的规划，包括：
1. 更详细的章节梗概 (200字左右)
2. 具体的场景列表 (3-5个场景)。**【严格场景逻辑】**每个场景中的 `characters` 只能包含真正在该物理空间或通讯链路中推动剧情发展的人。绝不要让无关角色强行登场，只写情节推理需要的角色。
3. 每个场景的要点
4. 关键对话或动作描写提示
5. 本章的情感基调
6. 与前后章节的衔接点
7. **本章的地点**：主要发生在哪里（具体到房间/区域名称）
8. **本章的时间点**：故事开始后第几天/第几小时
9. **本章的时间跨度**：本章内过了多久（如"2小时"、"半天"、"1天"）

以JSON格式输出，结构如下：
```json
{{
  "detailed_summary": "详细章节梗概 (200字以上)",
  "scenes": [
    {{
      "description": "场景描述",
      "focus": "场景焦点",
      "characters": ["角色1", "角色2"]
    }}
  ],
  "emotional_tone": "情感基调",
  "key_dialogues": ["对话点/动作点1", "对话点/动作点2"],
  "transitions": {{
    "previous": "与前一章的衔接逻辑",
    "next": "与后一章的铺垫逻辑"
  }},
  "location": "本章主要地点（如：普罗米修斯服务器中心-地下七层）",
  "time_point": "本章发生在"故事开始后"的具体时间（如：第1天上午/第3小时）",
  "time_duration": "本章内时间跨度（如：2小时/半天/1天）"
}}
```
"""

def get_outline_generation_prompt(
    title: str,
    genre: str,
    theme: str,
    chapter_count: int = 20,
    words_per_chapter: int = None,
    user_requirements: str = "",
    character_info: str = "",
    preliminary_outline_content: str = "",
    core_concepts: str = ""
) -> str:
    from ..config.settings import get_settings
    if words_per_chapter is None:
        words_per_chapter = get_settings().default_chapter_words

    prompt = OUTLINE_GENERATION_PROMPT.format(
        title=title,
        genre=genre,
        theme=theme,
        core_concepts=core_concepts if core_concepts else "无特殊限制，基于主题自由发挥",
        chapter_count=chapter_count,
        words_per_chapter=words_per_chapter,
        user_requirements=f"用户额外要求: {user_requirements}" if user_requirements else "无特殊要求",
        character_info=f"预设角色:\n{character_info}" if character_info else "暂无角色设定，将根据故事需要自动安排角色",
        preliminary_outline_content=preliminary_outline_content if preliminary_outline_content else "无预设主干，请自行构建"
    )
    return prompt

def get_preliminary_outline_generation_prompt(
    title: str,
    genre: str,
    theme: str,
    core_concepts: str = "",
    chapter_count: int = 20,
    user_requirements: str = ""
) -> str:
    from ..config.settings import Settings
    prompt = PRELIMINARY_OUTLINE_GENERATION_PROMPT.format(
        title=title,
        genre=genre,
        theme=theme,
        core_concepts=core_concepts if core_concepts else "无特殊限制，基于主题自由发挥",
        chapter_count=chapter_count,
        user_requirements=f"用户额外要求: {user_requirements}" if user_requirements else "无特殊要求"
    )
    return prompt

def get_outline_refinement_prompt(current_outline: str, user_feedback: str) -> str:
    """获取大纲优化prompt"""
    return OUTLINE_REFINEMENT_PROMPT.format(
        current_outline=current_outline,
        user_feedback=user_feedback
    )

def get_preliminary_outline_refinement_prompt(current_outline: str, user_feedback: str) -> str:
    """获取初级大纲优化prompt"""
    return PRELIMINARY_OUTLINE_REFINEMENT_PROMPT.format(
        current_outline=current_outline,
        user_feedback=user_feedback
    )

def get_chapter_expansion_prompt(
    chapter_number: int,
    current_title: str,
    current_summary: str,
    outline_context: str,
    story_context: str = ""
) -> str:
    """获取章节扩展prompt"""
    return CHAPTER_EXPANSION_PROMPT.format(
        chapter_number=chapter_number,
        current_title=current_title,
        current_summary=current_summary,
        outline_context=outline_context,
        story_context=story_context or "暂无特殊状态"
    )
