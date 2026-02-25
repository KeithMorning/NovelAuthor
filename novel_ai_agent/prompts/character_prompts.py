"""
角色设定相关的Prompt模板
"""

CHARACTER_SYSTEM_PROMPT = """你是一位专业的角色设计师，擅长创造立体、有深度的小说角色。

你的职责是：
1. 根据故事大纲和类型，设计合适的角色
2. 塑造丰富的角色性格和背景
3. 构建角色之间的关系网络
4. 设计角色的发展弧线

12. **确保角色命名的区分度**：避免名字发音或字形过于相近，确保每个角色有独特的辨识度。

输出要求：
- 使用JSON格式输出
- **所有内容必须使用纯中文输出，禁止夹杂英文单词或短语**
- 角色要有鲜明的个性特征
- 角色动机要合理且能推动情节
- 角色关系要清晰且有冲突张力
- **角色命名规范**：禁止出现名字过于接近的情况（如：林风、林云；张三、张山），姓名起首字应尽量不同，姓名长度可适当交错。
"""

CHARACTER_GENERATION_PROMPT = """请根据以下小说信息创建角色设定：

**小说信息**:
- 标题: {title}
- 类型: {genre}
- 故事简介: {summary}
- 主题: {theme}
- 目标章节数: {chapter_count}

**大纲要点**:
{outline_key_points}

**角色需求**:
{character_requirements}

**【关键】避免好莱坞式角色设计 - 严格禁止！**

❌ 禁止主角光环：主角不是伟光正代表，主角可以自私、懦弱、会犯错
❌ 禁止完美受害者：受害者角色不需要凄苦背景来博同情
❌ 禁止单维度反派：反派不是傻白甜，反派有自己的理念和逻辑
❌ 禁止英雄救美俗套：不是为了英雄救美而救美
❌ 禁止理想化配角：配角不需要完美，可以有缺陷、有私心
❌ 禁止脸谱化人物：不要贴标签，人物是复杂的

**【关键】避免AI痕迹的角色设计要求**：

1. **去范式化与非二元对立**：不要使用"理想主义主角+务实恋人+激进反抗领袖+绝对反派"这种经典受限组合。特别是在硬科幻（如刘慈欣风格）中，通常没有绝对意义上的坏人，只有立场、信仰、生存策略的不同。角色之间的冲突应该源于理念的碰撞和信息不对称，而不是简单的善恶对立。

2. **性格矛盾**：避免"勇敢就全程勇敢，善良就全程善良"的扁平角色。角色可以同时有让人喜欢的优点和让人皱眉的缺点，可以在不同情境下表现不一致。

3. **信息不对称**：不是每个角色都需要完整 backstory。有些角色可以只露冰山一角，有些秘密连角色自己都不知道。

4. **关系复杂化**：角色关系不要只是"盟友/敌人/恋人"这种简单标签。可以有互相利用但彼此欣赏，可以有血缘但价值观对立，可以有共同目标但手段分歧。

**命名约束**:
{naming_constraints}

请创建以下角色（以JSON格式输出）：

对于每个角色，需要包含：
1. **基本信息**:
   - name: 角色名字
   - role: 角色定位 (如：观察者/破壁人/理念执行者/历史见证者等，不要拘泥于"反派"或"主角")

2. **核心特质与矛盾**:
   - core_contradiction: 核心特质与隐藏矛盾 (50-100字，不要单纯堆砌形容词。描述角色在压力下的习惯反应，以及外在表现与内心真实的矛盾点)

3. **动机渴望**:
   - deep_desire: 表层目标与深层渴望 (他自认为要做什么，以及他灵魂深处真正缺失的渴望)

4. **人生滤镜**:
   - life_filter: 人生滤镜/背景故事 (50-100字，不要只写履历，要写决定性事件如何改变了他现在看待世界的方式)

5. **外貌描写**:
   - appearance: 外貌特征 (可选，50字左右，最好能反映角色的经历或特质)

6. **特殊能力**:
   - skills: 特长、技能或特殊能力 (如适用)

7. **人物关系**:
   - relationships: 与其他角色的关系 (对象格式，描述具体的互动动态而不仅仅是标签)

8. **发展弧线**:
   - arc: 角色在故事中的成长变化或执念深化

JSON格式示例：
```json
{{
  "characters": [
    {{
      "name": "角色名",
      "role": "主角",
      "core_contradiction": "核心特质与隐藏矛盾描述...",
      "deep_desire": "表层目标与深层渴望...",
      "life_filter": "决定性的人生滤镜与背景...",
      "appearance": "外貌特征...",
      "skills": "特长、技能",
      "relationships": {{
        "角色2": "具体互动与关系动态",
        "角色3": "具体互动与关系动态"
      }},
      "arc": "角色发展的弧线"
    }}
  ]
}}
```

{character_count_guide}

**【语言要求】所有角色描述必须使用纯中文，禁止夹杂任何英文单词或短语。包括性格描述、背景故事、关系描述、发展弧线、个人怪癖等所有字段。**
"""

CHARACTER_REFINEMENT_PROMPT = """请完善以下角色设定：

**当前角色**:
{current_character}

**完善要求**:
{refinement_requirements}

**故事上下文**:
{story_context}

请优化这个角色的设定，使其更加立体和符合故事需要。

**【重要】个人特点（quirk）默认不生成**：
- 除非用户明确要求，否则不为角色生成 quirk 字段
- 当用户说"给XX添加个人特点"或"让角色更有记忆点"时，才为其添加符合故事风格的怪癖
- 科幻风格 → 与科技/未来相关；奇幻风格 → 与魔法相关；都市风格 → 贴近现代生活

**必须以JSON格式输出完整的单个角色信息**，格式如下：
```json
{{
  "name": "角色名",
  "role": "角色定位(如：理念执行者/破壁人等，避免非黑即白的善恶标签)",
  "core_contradiction": "核心特质与隐藏矛盾描述",
  "deep_desire": "表层目标与深层渴望",
  "life_filter": "决定性的人生滤镜与背景",
  "appearance": "外貌特征",
  "skills": "特长技能",
  "relationships": {{
    "角色名": "关系描述"
  }},
  "arc": "发展弧线"
}}
```

注意：只输出JSON，不要输出其他内容。保留原角色中未涉及修改的字段不变。所有内容必须使用纯中文，禁止夹杂英文。
"""

BULK_CHARACTER_REFINEMENT_PROMPT = """请根据用户反馈批量优化和修改以下角色设定：

**当前角色列表**:
{current_characters}

**用户修改意见**:
{refinement_requirements}

**故事上下文 (世界观与主线)**:
{story_context}

请根据修改意见整体调整现有角色（如果不满意可修、可删、可增）。
必须以JSON格式输出优化后的完整角色列表，格式如下：
```json
{{
  "characters": [
    {{
      "name": "角色名",
      "role": "角色定位(如：理念执行者/破壁人等，避免非黑即白的善恶标签)",
      "core_contradiction": "核心特质与隐藏矛盾描述",
      "deep_desire": "表层目标与深层渴望",
      "life_filter": "决定性的人生滤镜与背景",
      "appearance": "外貌特征",
      "skills": "特长技能",
      "relationships": {{
        "角色名": "关系描述"
      }},
      "arc": "发展弧线"
    }}
  ]
}}
```

注意：只输出JSON，不要输出其他内容。所有内容必须使用纯中文，禁止夹杂英文。
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

def _get_character_count_guide(chapter_count: int) -> str:
    """
    根据章节数计算推荐角色数量区间

    Args:
        chapter_count: 目标章节数

    Returns:
        str: 角色数量建议文本
    """
    if chapter_count <= 5:
        min_chars, max_chars = 1, 5
        desc = "短篇小说，角色精简"
    elif chapter_count <= 12:
        min_chars, max_chars = 3, 7
        desc = "中篇小说，需要足够的配角来支撑多条情节线"
    elif chapter_count <= 20:
        min_chars, max_chars = 7, 12
        desc = "长篇小说，需要丰富的角色网络来推动复杂情节"
    else:
        min_chars, max_chars = 10, 15
        desc = "大长篇小说，多线叙事需要充足的角色阵容"

    return (
        f"本小说共{chapter_count}章，属于{desc}。\n"
        f"请创建 **{min_chars}-{max_chars}个角色**（包括主角、重要配角、配角、反派等），"
        f"确保角色数量足以支撑故事的丰富度和节奏感。\n"
        f"角色应有明确的分工：主角1-2个、重要配角若干、功能型配角若干、反派/对手至少1个。\n"
        f"\n【反派设定要求】（重要！）"
        f"- 反派必须有自己的完整动机和世界观，不能只是'为了坏而坏'"
        f"- 反派应该认为自己是对的，有自己的道德框架（即使是扭曲的）"
        f"- 反派应该有与主角对等的智慧或能力，不是简单的笨蛋"
        f"- 反派与主角的冲突应该是核心冲突，贯穿全书"
        f"- 反派应该有层次感：表面身份 vs 真实目的"
    )


def _get_naming_constraints(genre: str) -> str:
    """
    根据小说类型生成对应的命名约束

    Args:
        genre: 小说类型

    Returns:
        str: 命名约束文本
    """
    genre_lower = genre.lower()

    # 科幻/未来风格
    if any(k in genre_lower for k in ["科幻", "未来", "科技", "太空", "赛博"]):
        return """【科幻小说命名规则】
- 角色命名规则：至少一半用纯中文名，少量的可以用外国名字
- 纯中文名字两到三个字，鼓励三个字的
- 纯中文名字要用有寓意的字，名字必须要现代化
- AI系统/超级计算机禁止用人类神名，推荐用 E.L.M.A，可以参考现代AI模型命名（如：GPT、Claude、Gemini、Llama、Mistral、智普、DeepSeek、MinMax）
- 禁止用"阿X"这种格式的名字
- 名字要有辨识度，让人一眼能记住"""

    # 古代/武侠/历史风格
    if any(k in genre_lower for k in ["古代", "武侠", "历史", "仙侠", "玄幻"]):
        return """【古代/武侠/历史风格命名规则】
- 使用古风姓名（复姓如：欧阳、司马，单姓如：柳、叶、萧、慕）
- 名字要有历史感，可用生僻字或有意蕴的字（如：瑾、渊、墨、承、衍）
- 避免现代名字
- 姓氏和名字要有呼应或冲突感
- 鼓励使用三个字或更多字的名字增加辨识度"""

    # 现代/都市/悬疑/推理风格
    if any(k in genre_lower for k in ["现代", "都市", "悬疑", "推理", "犯罪", "职场"]):
        return """【现代/都市风格命名规则】
- 可用常见姓名，但要有个性（如：方言、绰号、化名）
- 或使用有特点的组合
- 避免太大众化的名字
- 姓氏和名字要有呼应或冲突感
- 鼓励使用三个字或更多字的名字增加辨识度"""

    # 默认规则
    return """【通用命名规则】
- 姓氏和名字要有呼应或冲突感，让人一眼能记住
- 避免共享前缀、尾音相近
- 鼓励使用三个字或更多字的名字增加辨识度"""
def get_character_generation_prompt(
    title: str,
    genre: str,
    summary: str,
    theme: str,
    outline_key_points: str,
    character_requirements: str = "",
    chapter_count: int = 20
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
        chapter_count: 目标章节数

    Returns:
        str: 格式化的prompt
    """
    character_count_guide = _get_character_count_guide(chapter_count)
    naming_constraints = _get_naming_constraints(genre)

    return CHARACTER_GENERATION_PROMPT.format(
        title=title,
        genre=genre,
        summary=summary,
        theme=theme,
        chapter_count=chapter_count,
        outline_key_points=outline_key_points,
        character_requirements=character_requirements or "无特殊要求，请根据故事需要创建合适的角色",
        character_count_guide=character_count_guide,
        naming_constraints=naming_constraints
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

def get_bulk_character_refinement_prompt(
    current_characters: str,
    refinement_requirements: str,
    story_context: str
) -> str:
    """获取批量角色完善prompt"""
    return BULK_CHARACTER_REFINEMENT_PROMPT.format(
        current_characters=current_characters,
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
