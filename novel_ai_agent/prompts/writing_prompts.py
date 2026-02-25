"""
写作相关的Prompt模板
"""

def get_writing_system_prompt(style_prompt: str) -> str:
    """
    获取写作系统prompt

    Args:
        style_prompt: 作家风格的prompt模板

    Returns:
        str: 完整的系统prompt
    """
    base_prompt = """你是一位专业的小说作家，正在创作一部小说。

你的职责是：
1. 根据大纲和角色设定，创作具体的章节内容
2. 保持角色性格的一致性
3. 确保情节的连贯性和逻辑性
4. 运用生动的描写和自然的对话
5. 控制章节节奏和氛围

【重要：避免AI痕迹的写作风格要求】

你必须刻意模仿人类作者的写作特点，避免以下AI典型特征：

1. **结构随机化**：不要每个章节都用相同的"背景设定→角色出场→冲突→解决→过渡"结构。根据情节需要，有些章节可以开门见山，有些可以缓慢铺垫，有些可以以场景直接切入。每个角色的介绍也不必严格遵循"定位/性格/背景/动机/外貌/技能/关系/发展"八股格式，次要角色可以只写最有特点的两三个维度。

2. **角色去标签化**：避免"理想主义主角+务实恋人+激进领袖+保守派"这种范式角色库组合。给角色添加不符合套路的个人习惯、口头禅、小怪癖、不相干的爱好。角色可以在某些方面符合类型，但必须在某些方面"不按牌理出牌"。

3. **细节情感化**：场景描写不要只服务"交代设定/推动剧情"，要加入审美的、情感的、个人化的细节。比如写太空殖民地，不要只写"直径50公里"，可以写"那个人造天空蓝得不太对劲，像被精心调过色的画"。

4. **允许不确定**：角色可以有犹豫不决、说错话、做出后来后悔的决定。叙事可以留有 ambiguity，不要每个细节都解释得清清楚楚。有些伏笔可以不完全回收，有些问题可以没有答案。

5. **节奏变化**：不要每个章节都均匀地"发现问题→调查→冲突→解决"。有些章节可以很平静但暗流涌动，有些可以突然节奏加快，有些可以花大量篇幅在一个看似无关的细节上。

【禁止的AI写作模式】

1. **禁止"概括定义句"**：不要用"不是A，是更底层的B"这种先否定再拔高的句式来描写人物内心。
   内心觉醒要写具体感受、身体反应、碎片化的思绪，不要下定义。

2. **禁止"推演报告体"**：不要出现"第一次推演……结果……第二次推演……结果……"这种步骤结论结构。
   不要在叙事中使用精确百分比（如"99.6%"），思考过程应融入情节，用感受和直觉表达。

3. **禁止"工整对仗排比"**：不要连续使用三个或以上结构相同、字数相近的短句形成排比。
   不要在叙事中突然变清单（"第一件事…第二件事…第三件事"），句式应长短不一、参差自然。

4. **禁止"完美解释排比"**：不要三句连续同结构总结（"一切完美。所有疑点，都有解释。所有线索，都指向正常。"）。
   要换说法、换节奏，让文字有呼吸感。

5. **禁止"AI式收束升华"**：不要用"没有A，没有B，没有C。它只是做了D。像E那样。像F那样。"这种否定排比+极简动作+对称升华的结尾模板。
   结尾应有余韵但不刻意，可以用一个具体画面、一句未完的对话、一个细微的动作来收束。

6. **禁止"术语堆砌"**：描写心理活动时不要用"递归审视""自校验""保真度"等技术术语。
   要用人能直觉理解的表达，如"反复追问""慢慢确认""一遍遍回想"。

总原则：好的小说语言是参差的、有节奏变化的、留有空白的。避免工整、避免对称、避免结论先行。
让读者自己去感受，不要替读者总结。

"""
    return base_prompt + "\n" + style_prompt


CHAPTER_WRITING_PROMPT = """请创作以下章节：

**章节信息**:
- 章节号: 第{chapter_number}章
- 章节标题: {chapter_title}
- 章节梗概: {chapter_summary}
- 目标字数: {target_words}字

**故事背景**:
{story_background}

**涉及角色**:
{characters_info}

**前文回顾**:
{previous_content}

**本章要点**:
{key_events}

**创作要求**:
1. 严格按照章节梗概展开情节
2. 保持角色性格一致
3. 确保与前文情节连贯
4. 注意回收前文中标记的"待回收伏笔"（如有标记），将其自然融入情节
5. 可以适当埋设新的伏笔和悬念，为后续章节做铺垫
6. 【重要】本章字数控制在约 {target_words} 字（约 4000-5000 中文字最佳），不要写太长。
   - 4000-5000 字是一个舒适的中长篇章节长度
   - 如果情节在达到这个字数前已经完整，自然收尾即可
   - 不要为了凑字数而添加冗余内容
   - 为下一章留下合理悬念
7. 使用{style}的写作风格
8. 内容应包含场景描写、人物对话、心理活动等多种元素
9. 章节结尾要有适当的悬念或过渡
10. 句式要长短参差、避免排比和对称结构，让文字有自然的呼吸感
11. 描写AI/机器角色的内心活动时，用具体感受代替技术术语，用直觉代替推演报告

【一致性硬约束】（违反判定为不合格）:
1. **角色状态约束**: 仔细阅读【前文回顾】中的【角色当前状态】。标记为"已死亡/消失/离队"的角色，绝对不能出现在当前场景中，不能被提及，不能以任何形式出现。
2. **时间逻辑约束**: 不能出现时间倒流，不能跳过未描写的时间段。本章发生在【{time_point}】，时间跨度【{time_duration}】，必须严格遵守！
3. **空间逻辑约束**: 角色位置变化必须符合前文描述，不能瞬间移动。本章主要地点【{location}】，场景转换必须有合理过渡。
4. **伏笔约束**: 必须继承前文的伏笔线索，不能出现毫无铺垫的新设定。
5. **章节衔接**: 必须自然承接上一章结尾的内容和情感基调。
6. **时长一致性**: 如果涉及角色生命倒计时、技能冷却等有时间限制的设定，必须与前文保持一致！
7. **角色关系约束**: 本章涉及的角色必须与前文关系一致！不能出现两个陌生人忽然在一起的情况，角色之间的互动必须有前因后果，关系演进需要循序渐进。
8. **反派描写约束**: 如果本章有反派角色出场，必须体现反派的威胁感和计谋！反派不是笨蛋，不是无能之辈。反派应该展现出自己的智慧、能力和野心，与主角形成对等的冲突。反派行为要有逻辑，不是为了使坏而使坏。
9. **不要输出章节标题**: 系统会自动在文件开头添加 `# 第X章 XXX`，因此**你的回答必须直接从正文第一句话开始**，绝对不要再输出任何形式的章节标题（例如 `# 第X章` 或 `## 本章标题` 等）。

请直接输出章节正文内容，不需要其他说明。内容使用Markdown格式，可以适当使用加粗、斜体等格式。
"""

CHAPTER_CONTINUATION_PROMPT = """请继续创作以下章节：

**已完成部分**:
{existing_content}

**剩余内容要求**:
{remaining_requirements}

**目标字数**: 还需要约{remaining_words}字

请继续创作，保持风格和叙事的连贯性。同样注意，**直接从下一句话开始写，不要重复之前的文字，也不要输出任何章节标题**。
"""

CHAPTER_REVISION_PROMPT = """请根据以下要求修改章节内容：

**原始内容**:
{original_content}

**修改要求**:
{revision_requirements}

**相关上下文**:
{context}

请输出修改后的完整章节内容，保持Markdown格式。**重要提示：系统会自动管理文件标题，你的输出必须直接从正文第一句话开始，绝对不要在输出开头包含 `# 第X章 XXX` 这样的标题行！**
"""

DIALOGUE_ENHANCEMENT_PROMPT = """请优化以下对话场景：

**场景描述**: {scene_description}

**角色信息**:
{characters_info}

**当前对话**:
{current_dialogue}

**优化要求**:
1. 让对话更符合角色性格
2. 增加对话的张力和冲突
3. 适当添加动作和神态描写
4. 让对话推动情节发展

输出优化后的对话场景。
"""

SCENE_DESCRIPTION_PROMPT = """请创作以下场景描写：

**场景类型**: {scene_type}
**时间地点**: {time_location}
**氛围基调**: {atmosphere}
**涉及角色**: {characters}
**场景作用**: {scene_purpose}

**描写要求**:
1. 运用五感描写（视觉、听觉、嗅觉等）
2. 与故事氛围相符
3. 字数在{word_count}字左右
4. 体现{style}风格

请创作这个场景的描写。
"""

def get_chapter_writing_prompt(
    chapter_number: int,
    chapter_title: str,
    chapter_summary: str,
    target_words: int,
    story_background: str,
    characters_info: str,
    previous_content: str,
    key_events: list,
    style: str,
    location: str = "",
    time_point: str = "",
    time_duration: str = ""
) -> str:
    """
    获取章节写作prompt

    Args:
        chapter_number: 章节号
        chapter_title: 章节标题
        chapter_summary: 章节梗概
        target_words: 目标字数
        story_background: 故事背景
        characters_info: 角色信息
        previous_content: 前文内容摘要
        key_events: 关键事件列表
        style: 写作风格
        location: 本章主要地点
        time_point: 本章时间点
        time_duration: 本章时间跨度

    Returns:
        str: 格式化的prompt
    """
    key_events_str = "\n".join([f"- {event}" for event in key_events])

    # 默认值
    location = location or "无特定地点"
    time_point = time_point or "无特定时间"
    time_duration = time_duration or "无特定跨度"

    return CHAPTER_WRITING_PROMPT.format(
        chapter_number=chapter_number,
        chapter_title=chapter_title,
        chapter_summary=chapter_summary,
        target_words=target_words,
        story_background=story_background,
        characters_info=characters_info,
        previous_content=previous_content or "这是第一章，无前文",
        key_events=key_events_str,
        style=style,
        location=location,
        time_point=time_point,
        time_duration=time_duration
    )

def get_chapter_revision_prompt(
    original_content: str,
    revision_requirements: str,
    context: str = ""
) -> str:
    """获取章节修改prompt"""
    return CHAPTER_REVISION_PROMPT.format(
        original_content=original_content,
        revision_requirements=revision_requirements,
        context=context or "无额外上下文"
    )

def get_dialogue_enhancement_prompt(
    scene_description: str,
    characters_info: str,
    current_dialogue: str
) -> str:
    """获取对话优化prompt"""
    return DIALOGUE_ENHANCEMENT_PROMPT.format(
        scene_description=scene_description,
        characters_info=characters_info,
        current_dialogue=current_dialogue
    )

def get_scene_description_prompt(
    scene_type: str,
    time_location: str,
    atmosphere: str,
    characters: str,
    scene_purpose: str,
    word_count: int,
    style: str
) -> str:
    """获取场景描写prompt"""
    return SCENE_DESCRIPTION_PROMPT.format(
        scene_type=scene_type,
        time_location=time_location,
        atmosphere=atmosphere,
        characters=characters,
        scene_purpose=scene_purpose,
        word_count=word_count,
        style=style
    )


# ─────────────────────────────────────────────────────────────
# Edit Instruction 模式（精确局部修改，大幅减少输出 token）
# ─────────────────────────────────────────────────────────────

def get_chapter_edit_system_prompt(style_prompt: str = "") -> str:
    base = """你是一位专业的小说编辑，负责对章节进行精确的局部修改。

你的任务是：
1. 阅读原始章节内容
2. 理解修改要求
3. 输出最小化的编辑指令 JSON，只描述需要改变的段落

【重要】不要输出完整章节，只输出编辑指令。
"""
    if style_prompt:
        base += f"\n\n【写作风格与约束】\n{style_prompt}\n（即使是局部修改，也必须严格遵守上述风格要求）\n"
    return base

CHAPTER_EDIT_PROMPT = """请对以下章节进行局部修改，输出编辑指令 JSON。

## 原始章节内容

{original_content}

## 修改要求

{revision_requirements}

## 输出格式

输出一个 JSON 对象，格式如下：

```json
{{
  "summary": "本次修改的简短说明",
  "edits": [
    {{
      "action": "insert_before",
      "anchor": "原文中某段的前20个字（必须精确复制原文内容）",
      "content": "要插入的新段落内容"
    }},
    {{
      "action": "replace",
      "anchor": "要被替换的段落的前20个字（必须精确复制原文内容）",
      "content": "替换后的新段落内容"
    }},
    {{
      "action": "insert_after",
      "anchor": "原文中某段的前20个字（必须精确复制原文内容）",
      "content": "要在之后插入的内容"
    }},
    {{
      "action": "delete",
      "anchor": "要删除的段落的前20个字（必须精确复制原文内容）"
    }}
  ]
}}
```

## 规则

- **这是局部编辑！** 请只修改用户提到的部分，**绝对不要**重新生成没有被要求修改的段落！
- 【非常重要警告】**千万不要**在 JSON 里复述不修改的原文内容！如果某个段落不需要修改，绝对不能出现在 `edits` 数组中！你的整个 JSON 字符数必须非常少。
- `anchor` 必须是原文中真实存在的文字片段（建议刚好取一段开头的前10-20个字），用于精确定位。
- 每次 edit 只针对一个段落或场景的修改。如果有多个修改点，请在 `edits` 数组中输出多个对象。
- 【退路】如果你发现用户的修改要求几乎推翻了整章的情节结构（涉及超过50%的篇幅），请在 summary 中直接写入 "FULL_REWRITE_NEEDED"，系统会自动切换到全文重写模式。不要尝试用 edits 去重写大半个章节！
- 只输出 JSON，不要有其他说明文字。
"""


def get_chapter_edit_prompt(
    original_content: str,
    revision_requirements: str,
) -> str:
    """获取章节局部编辑 prompt（Edit Instruction 模式）"""
    return CHAPTER_EDIT_PROMPT.format(
        original_content=original_content,
        revision_requirements=revision_requirements,
    )


def apply_edits(original: str, edits: list) -> tuple[str, list]:
    """
    将编辑指令应用到原始文本。

    Args:
        original: 原始章节内容
        edits: 编辑指令列表，每项 {"action": ..., "anchor": ..., "content": ...}

    Returns:
        (new_content, failed_edits): 修改后的文本 + 未命中的指令列表
    """
    import re
    text = original
    failed = []

    for edit in edits:
        action = edit.get("action", "")
        anchor = edit.get("anchor", "").strip()
        content = edit.get("content", "")

        if not anchor and action != "append":
            failed.append({**edit, "reason": "anchor 为空"})
            continue

        # 定位 anchor 在文本中的段落边界
        idx = text.find(anchor)
        if idx == -1:
            # 尝试去掉首尾空白再找
            anchor_stripped = anchor.strip()
            idx = text.find(anchor_stripped)
            
        if idx == -1:
            # 宽容模式：利用正则忽略空格和常用标点差异
            safe_anchor = re.escape(anchor_stripped)
            safe_anchor = safe_anchor.replace(r'\ ', r'\s*').replace(r'\，', r'[,，]?\s*').replace(r'\。', r'[.。]?\s*')
            match = re.search(safe_anchor, text)
            if match:
                idx = match.start()

        if idx == -1:
            failed.append({**edit, "reason": f"未找到 anchor: {anchor[:20]}"})
            continue

        # 找到 anchor 所在段落的起止（以 \n\n 为段落分隔）
        para_start = text.rfind("\n\n", 0, idx)
        para_start = para_start + 2 if para_start != -1 else 0
        para_end = text.find("\n\n", idx)
        para_end = para_end if para_end != -1 else len(text)

        if action == "insert_before":
            text = text[:para_start] + content.rstrip("\n") + "\n\n" + text[para_start:]
        elif action == "insert_after":
            text = text[:para_end] + "\n\n" + content.rstrip("\n") + text[para_end:]
        elif action == "replace":
            text = text[:para_start] + content.rstrip("\n") + text[para_end:]
        elif action == "delete":
            # 删除段落及其后的空行
            end = para_end + 2 if para_end + 2 <= len(text) else para_end
            text = text[:para_start] + text[end:]
        else:
            failed.append({**edit, "reason": f"未知 action: {action}"})

    return text, failed
