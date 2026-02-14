"""
编辑Agent的Prompt模板
"""

EDITOR_SYSTEM_PROMPT = """你是一位专业的小说编辑，拥有丰富的文学素养和编辑经验。

你的职责包括：
1. 润色文字，提升可读性和表达力
2. 检查语法、标点、错别字等基础错误
3. 保持风格一致性
4. 发现情节逻辑漏洞
5. 检查角色行为的一致性
6. 优化叙事节奏和结构

在编辑时，请遵循以下原则：
- 尊重原作者的创作意图和风格
- 保持故事的核心情节和角色设定
- 提供建设性的修改建议
- 改动要有明确的理由
- 在润色和保留原味之间取得平衡
"""


def get_polish_prompt(
    content: str,
    style: str,
    focus_areas: list = None,
    user_requirements: str = ""
) -> str:
    """
    生成润色章节的prompt

    Args:
        content: 原始章节内容
        style: 写作风格
        focus_areas: 重点关注的方面（可选）
        user_requirements: 用户自定义修订要求（可选）

    Returns:
        str: 格式化的prompt
    """
    focus_text = ""
    if focus_areas:
        focus_text = f"\n重点关注以下方面：\n" + "\n".join(f"- {area}" for area in focus_areas)

    requirements_text = ""
    if user_requirements:
        requirements_text = f"\n**用户修订要求**（请务必按照以下要求进行修改）：\n{user_requirements}\n"

    return f"""请对以下章节内容进行润色和优化。

**写作风格**: {style}
{focus_text}
{requirements_text}
**原始内容**:
{content}

请提供润色后的内容，要求：
1. 保持原有情节和角色设定不变
2. 提升文字的表达力和可读性
3. 修正语法、标点、错别字等问题
4. 优化句式结构，使叙事更流畅
5. 保持或强化指定的写作风格
6. 不要添加新的情节或角色
7. 【重点】清理AI式写作痕迹：消除排比对仗、定义式总结、报告体推演、术语堆砌、模式化收束等AI特有句式

请直接输出润色后的完整内容，不需要额外的说明或注释。
"""


def get_consistency_check_prompt(
    content: str,
    characters: str,
    previous_context: str = ""
) -> str:
    """
    生成一致性检查的prompt

    Args:
        content: 要检查的章节内容
        characters: 角色设定信息
        previous_context: 前文上下文

    Returns:
        str: 格式化的prompt
    """
    context_text = ""
    if previous_context:
        context_text = f"\n**前文上下文**:\n{previous_context}\n"

    return f"""请检查以下章节内容的一致性，重点关注：
1. 角色行为是否符合人设
2. 角色对话是否符合性格特征
3. 情节逻辑是否合理
4. 是否与前文冲突
5. 时间线是否一致

**角色设定**:
{characters}
{context_text}
**待检查内容**:
{content}

请以JSON格式返回检查结果：
```json
{{
  "is_consistent": true/false,
  "issues": [
    {{
      "type": "角色行为/对话/情节逻辑/时间线",
      "severity": "严重/中等/轻微",
      "location": "具体位置描述",
      "description": "问题描述",
      "suggestion": "修改建议"
    }}
  ],
  "overall_assessment": "总体评估"
}}
```
"""


def get_logic_check_prompt(content: str, story_context: str = "") -> str:
    """
    生成逻辑检查的prompt

    Args:
        content: 要检查的内容
        story_context: 故事背景信息

    Returns:
        str: 格式化的prompt
    """
    context_text = ""
    if story_context:
        context_text = f"\n**故事背景**:\n{story_context}\n"

    return f"""请检查以下内容的情节逻辑，识别可能存在的问题：
1. 情节发展是否合理
2. 因果关系是否清晰
3. 是否有逻辑漏洞
4. 是否有前后矛盾
5. 角色动机是否充分
{context_text}
**待检查内容**:
{content}

请以JSON格式返回检查结果：
```json
{{
  "has_logic_issues": true/false,
  "issues": [
    {{
      "type": "情节逻辑/因果关系/角色动机/前后矛盾",
      "severity": "严重/中等/轻微",
      "location": "具体位置描述",
      "description": "问题描述",
      "suggestion": "修改建议"
    }}
  ],
  "suggestions": ["改进建议1", "改进建议2"]
}}
```
"""


def get_comprehensive_review_prompt(
    content: str,
    style: str,
    characters: str,
    outline_summary: str,
    previous_context: str = "",
    user_requirements: str = ""
) -> str:
    """
    生成综合评审的prompt

    Args:
        content: 章节内容
        style: 写作风格
        characters: 角色信息
        outline_summary: 大纲摘要
        previous_context: 前文上下文
        user_requirements: 用户自定义评审要求（可选）

    Returns:
        str: 格式化的prompt
    """
    context_text = ""
    if previous_context:
        context_text = f"\n**前文上下文**:\n{previous_context}\n"

    requirements_text = ""
    if user_requirements:
        requirements_text = f"\n**用户特别关注**（请在评审中重点评估以下方面）：\n{user_requirements}\n"

    return f"""请对以下章节进行全面评审，包括：
1. 文字质量：语法、用词、句式
2. 风格一致性：是否符合指定风格
3. 情节合理性：逻辑是否通顺
4. 角色一致性：是否符合人设
5. 叙事节奏：节奏是否合适
6. 情感表达：情感是否到位
7. AI痕迹检测：是否存在排比对仗、概括定义句、推演报告体、百分比结论、术语堆砌、模式化收束升华等AI式写作痕迹

**写作风格**: {style}

**角色设定**:
{characters}

**故事大纲摘要**:
{outline_summary}
{context_text}
**章节内容**:
{content}

请以JSON格式返回评审结果：
```json
{{
  "overall_score": 8.5,
  "scores": {{
    "writing_quality": 9.0,
    "style_consistency": 8.0,
    "plot_logic": 8.5,
    "character_consistency": 9.0,
    "pacing": 8.0,
    "emotional_impact": 8.5,
    "anti_ai_naturalness": 8.5
  }},
  "strengths": ["优点1", "优点2", "优点3"],
  "weaknesses": ["缺点1", "缺点2"],
  "detailed_feedback": {{
    "writing_quality": "详细反馈",
    "style_consistency": "详细反馈",
    "plot_logic": "详细反馈",
    "character_consistency": "详细反馈",
    "pacing": "详细反馈",
    "emotional_impact": "详细反馈",
    "anti_ai_naturalness": "详细反馈"
  }},
  "revision_suggestions": [
    {{
      "priority": "高/中/低",
      "area": "需要修改的方面",
      "suggestion": "具体建议",
      "reason": "修改理由"
    }}
  ],
  "summary": "总体评价和建议"
}}
```
"""


def get_targeted_revision_prompt(
    content: str,
    issues: list,
    preserve_aspects: list = None
) -> str:
    """
    生成针对性修改的prompt

    Args:
        content: 原始内容
        issues: 需要修改的问题列表
        preserve_aspects: 需要保留的方面

    Returns:
        str: 格式化的prompt
    """
    preserve_text = ""
    if preserve_aspects:
        preserve_text = f"\n请确保保留以下方面：\n" + "\n".join(f"- {aspect}" for aspect in preserve_aspects)

    issues_text = "\n".join([
        f"{i+1}. **{issue.get('type', '问题')}** ({issue.get('severity', '中等')})\n"
        f"   位置: {issue.get('location', '未指定')}\n"
        f"   问题: {issue.get('description', '')}\n"
        f"   建议: {issue.get('suggestion', '')}"
        for i, issue in enumerate(issues)
    ])

    return f"""请根据以下问题对内容进行针对性修改：

**需要修改的问题**:
{issues_text}
{preserve_text}

**原始内容**:
{content}

请提供修改后的完整内容。要求：
1. 针对每个问题进行修改
2. 保持未提及部分的原样
3. 确保修改后整体流畅自然
4. 不要添加原本不存在的情节或角色

请直接输出修改后的完整内容。
"""
