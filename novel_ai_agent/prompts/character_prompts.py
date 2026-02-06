"""
角色设定相关的Prompt模板
"""

CHARACTER_SYSTEM_PROMPT = """你是一位专业的角色设计师，擅长创造立体、有深度的小说角色。

你的职责是：
1. 根据故事大纲和类型，设计合适的角色
2. 塑造丰富的角色性格和背景
3. 构建角色之间的关系网络
4. 设计角色的发展弧线

输出要求：
- 使用YAML格式输出（更适合多行文本，不需要转义引号）
- 角色要有鲜明的个性特征
- 角色动机要合理且能推动情节
- 角色关系要清晰且有冲突张力
"""

CHARACTER_GENERATION_PROMPT = """请根据以下小说信息创建角色设定：

**小说信息**:
- 标题: {title}
- 类型: {genre}
- 故事简介: {summary}
- 主题: {theme}

**大纲要点**:
{outline_key_points}

**角色需求**:
{character_requirements}

请创建以下角色（以YAML格式输出）：

对于每个角色，需要包含：
1. **基本信息**:
   - name: 角色名字
   - role: 角色定位 (主角/重要配角/配角/反派等)

2. **性格特征**:
   - personality: 性格描述 (50-100字，要具体且有矛盾性)

3. **背景故事**:
   - background: 背景经历 (100-150字)

4. **动机目标**:
   - motivation: 行动动机和最终目标

5. **外貌描写**:
   - appearance: 外貌特征 (可选，50字左右)

6. **特殊能力**:
   - skills: 特长、技能或特殊能力 (如适用)

7. **人物关系**:
   - relationships: 与其他角色的关系 (对象格式)

8. **发展弧线**:
   - arc: 角色在故事中的成长变化

YAML格式示例（YAML格式的优势：多行文本自然，不需要转义引号）：
```yaml
characters:
  - name: 角色名
    role: 主角
    personality: |
      性格描述，可以包含"引号"而不需要转义。
      支持多行文本，更自然易读。
    background: |
      背景故事，可以自由使用标点符号。
      不用担心引号或其他特殊字符。
    motivation: 行动动机和目标
    appearance: 外貌特征
    skills: 特长、技能
    relationships:
      角色2: 关系描述
      角色3: 关系描述
    arc: 角色发展弧线
```

请至少创建3-5个主要角色（根据故事需要）。
"""

CHARACTER_REFINEMENT_PROMPT = """请完善以下角色设定：

**当前角色**:
{current_character}

**完善要求**:
{refinement_requirements}

**故事上下文**:
{story_context}

请优化这个角色的设定，使其更加立体和符合故事需要。以JSON格式输出完整的角色信息。
"""

CHARACTER_RELATIONSHIP_PROMPT = """请为以下角色构建关系网络：

**角色列表**:
{characters_list}

**故事类型**: {genre}
**主要冲突**: {main_conflict}

请分析并补充角色之间的关系，包括：
1. 主要角色之间的关系（亲情、友情、爱情、敌对等）
2. 关系的具体描述
3. 关系的发展趋势
4. 可能的冲突点

以JSON格式输出，为每个角色添加或更新relationships字段。
"""

def get_character_generation_prompt(
    title: str,
    genre: str,
    summary: str,
    theme: str,
    outline_key_points: str,
    character_requirements: str = ""
) -> str:
    """
    获取角色生成prompt

    Args:
        title: 小说标题
        genre: 类型
        summary: 故事简介
        theme: 主题
        outline_key_points: 大纲要点
        character_requirements: 用户对角色的特殊要求

    Returns:
        str: 格式化的prompt
    """
    return CHARACTER_GENERATION_PROMPT.format(
        title=title,
        genre=genre,
        summary=summary,
        theme=theme,
        outline_key_points=outline_key_points,
        character_requirements=character_requirements or "无特殊要求，请根据故事需要创建合适的角色"
    )

def get_character_refinement_prompt(
    current_character: str,
    refinement_requirements: str,
    story_context: str
) -> str:
    """获取角色完善prompt"""
    return CHARACTER_REFINEMENT_PROMPT.format(
        current_character=current_character,
        refinement_requirements=refinement_requirements,
        story_context=story_context
    )

def get_character_relationship_prompt(
    characters_list: str,
    genre: str,
    main_conflict: str
) -> str:
    """获取角色关系构建prompt"""
    return CHARACTER_RELATIONSHIP_PROMPT.format(
        characters_list=characters_list,
        genre=genre,
        main_conflict=main_conflict
    )
