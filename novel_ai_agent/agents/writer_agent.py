"""
写作Agent
负责生成章节内容
"""
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from .base_agent import BaseAgent
from ..models.chapter import Chapter, ChapterStatus
from ..models.outline import Outline, ChapterPlan
from ..models.character import Character
from ..config.styles import get_style
from ..utils.json_parser import extract_json_from_response
from ..prompts.writing_prompts import (
    get_writing_system_prompt,
    get_chapter_writing_prompt,
    get_chapter_revision_prompt
)
from ..utils.logger import get_logger, WorkflowStep, LogLevel


class WriterAgent(BaseAgent):
    """
    写作Agent

    职责:
    1. 根据大纲和角色设定创作章节
    2. 应用指定的写作风格
    3. 保持角色和情节的一致性
    4. 根据反馈修改章节
    5. 写完后提取结构化摘要（伏笔、角色状态等）
    """

    def __init__(self, style_name: str = "中性风格"):
        super().__init__(
            name="Writer",
            description=f"负责创作章节内容，使用{style_name}风格"
        )
        self.style_name = style_name
        self.style = get_style(style_name)
        self.logger = get_logger("WriterAgent")

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行写作任务

        Args:
            **kwargs: 任务参数
                - action: 操作类型 (write/revise)
                - 其他参数根据action不同

        Returns:
            Dict: 包含生成的Chapter对象或错误信息
        """
        action = kwargs.get("action", "write")

        if action == "write":
            return await self.write_chapter(**kwargs)
        elif action == "revise":
            return await self.revise_chapter(**kwargs)
        else:
            return {"status": "error", "message": f"未知操作: {action}"}

    async def write_chapter(
        self,
        chapter_plan: ChapterPlan,
        outline: Outline,
        characters: List[Character],
        previous_chapters: Optional[List[Chapter]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        创作章节

        Args:
            chapter_plan: 章节规划
            outline: 完整大纲
            characters: 角色列表
            previous_chapters: 前面的章节（用于保持连贯性）

        Returns:
            Dict: 包含生成的Chapter对象
        """
        try:
            # 准备故事背景信息
            story_background = self._prepare_story_background(outline)

            # 准备角色信息
            characters_info = self._prepare_characters_info(
                characters,
                chapter_plan.characters_involved
            )

            # 准备前文摘要（含伏笔追踪）
            previous_content = self._prepare_previous_content(
                previous_chapters,
                outline=outline,
                current_chapter_num=chapter_plan.chapter_number
            )

            # 如果有详细规划，则整合到 prompt 中
            chapter_summary = chapter_plan.summary
            key_events = chapter_plan.key_events
            if chapter_plan.detailed_plan:
                # 使用细化后的梗概
                chapter_summary = f"{chapter_plan.summary}\n\n详细展开: {chapter_plan.detailed_plan.detailed_summary}"
                # 整合场景信息到关键事件中
                detailed_events = []
                for i, scene in enumerate(chapter_plan.detailed_plan.scenes, 1):
                    detailed_events.append(f"场景{i}: {scene.description} (焦点: {scene.focus})")
                key_events = detailed_events + key_events

            # 构建写作系统prompt
            system_prompt = get_writing_system_prompt(self.style.prompt_template)

            # 获取目标字数（优先使用 settings 默认值，避免大纲旧值）
            from ..config.settings import Settings
            target_words = Settings().default_chapter_words

            # 获取地点和时间信息
            location = ""
            time_point = ""
            time_duration = ""
            if chapter_plan.detailed_plan:
                location = getattr(chapter_plan.detailed_plan, 'location', '') or ""
                time_point = getattr(chapter_plan.detailed_plan, 'time_point', '') or ""
                time_duration = getattr(chapter_plan.detailed_plan, 'time_duration', '') or ""

            # 构建用户prompt
            user_prompt = get_chapter_writing_prompt(
                chapter_number=chapter_plan.chapter_number,
                chapter_title=chapter_plan.title,
                chapter_summary=chapter_summary,
                target_words=target_words,
                story_background=story_background,
                characters_info=characters_info,
                previous_content=previous_content,
                key_events=key_events,
                style=self.style_name,
                location=location,
                time_point=time_point,
                time_duration=time_duration
            )

            # 调用LLM - 强制设置更高的 max_tokens
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            # 记录API调用信息到日志
            self.logger.log(
                level=LogLevel.INFO,
                step=WorkflowStep.CHAPTER_WRITING,
                message=f"API请求: model={self.llm.model_name}, max_tokens={self.llm.max_tokens}, prompt长度={len(user_prompt)}"
            )

            # 调用LLM
            response = await self.llm.ainvoke(messages)
            content = response.content

            # 记录API响应信息到日志
            usage_info = {}
            if hasattr(response, 'usage_metadata'):
                usage_info = response.usage_metadata
            elif hasattr(response, 'response_metadata') and 'token_usage' in response.response_metadata:
                usage_info = response.response_metadata['token_usage']

            self.logger.log(
                level=LogLevel.INFO,
                step=WorkflowStep.CHAPTER_WRITING,
                message=f"API响应: content长度={len(content)}, usage={usage_info}"
            )

            # 计算输入token数量（粗略估算）
            input_text = system_prompt + user_prompt
            input_tokens_estimate = len(input_text) // 3

            # 计算输出token数量
            output_tokens_estimate = len(content) // 3

            # 记录章节写作统计到日志
            self.logger.log(
                level=LogLevel.INFO,
                step=WorkflowStep.CHAPTER_WRITING,
                message=f"章节写作完成: 第{chapter_plan.chapter_number}章, 输入~{input_tokens_estimate}, 输出~{output_tokens_estimate}, 内容长度{len(content)}"
            )

            # 创建Chapter对象
            chapter = Chapter(
                number=chapter_plan.chapter_number,
                title=chapter_plan.title,
                summary=chapter_plan.summary,
                content=content,
                status=ChapterStatus.DRAFT
            )

            # 更新字数统计
            chapter.update_word_count()

            # 提取结构化摘要（伏笔、角色状态等）
            try:
                digest = await self._extract_chapter_digest(
                    content, chapter_plan, previous_chapters
                )
                chapter.actual_summary = digest.get("actual_summary", "")
                chapter.hooks_planted = digest.get("hooks_planted", [])
                chapter.hooks_resolved = digest.get("hooks_resolved", [])
                chapter.character_states = digest.get("character_states", {})
                chapter.key_items = digest.get("key_items", [])
                chapter.emotional_tone = digest.get("emotional_tone", "")
            except Exception as e:
                # 提取失败不影响核心功能，降级为使用大纲摘要
                self.logger.log(
                    level=LogLevel.WARNING,
                    step=WorkflowStep.CHAPTER_WRITING,
                    message=f"结构化摘要提取失败: {e}"
                )

            return {
                "status": "success",
                "chapter": chapter,
                "word_count": chapter.word_count,
                "target_words": target_words
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"创作章节时出错: {str(e)}",
                "error": str(e)
            }

    async def revise_chapter(
        self,
        chapter: Chapter,
        revision_requirements: str,
        context: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """
        修改章节

        Args:
            chapter: 当前章节
            revision_requirements: 修改要求
            context: 额外上下文

        Returns:
            Dict: 包含修改后的Chapter对象
        """
        try:
            # 构建写作系统prompt
            system_prompt = get_writing_system_prompt(self.style.prompt_template)

            # 构建修改prompt
            user_prompt = get_chapter_revision_prompt(
                original_content=chapter.content,
                revision_requirements=revision_requirements,
                context=context
            )

            # 调用LLM
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = await self.llm.ainvoke(messages)
            new_content = response.content

            # 创建新版本的Chapter（使用 model_copy 保留伏笔等结构化数据）
            revised_chapter = chapter.model_copy(update={
                "content": new_content,
                "status": ChapterStatus.REVIEWED,
                "version": chapter.version + 1,
                "notes": f"根据要求修改: {revision_requirements}",
                "updated_at": datetime.now()
            })

            # 更新字数统计
            revised_chapter.update_word_count()

            return {
                "status": "success",
                "chapter": revised_chapter,
                "word_count": revised_chapter.word_count,
                "version": revised_chapter.version
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"修改章节时出错: {str(e)}",
                "error": str(e)
            }

    async def _extract_chapter_digest(
        self,
        content: str,
        chapter_plan: ChapterPlan,
        previous_chapters: Optional[List[Chapter]] = None
    ) -> Dict[str, Any]:
        """
        从实际写完的章节内容中提取结构化摘要

        用一次轻量级 LLM 调用提取：实际摘要、伏笔、角色状态等

        Args:
            content: 章节实际写出的内容
            chapter_plan: 章节规划
            previous_chapters: 前面的章节

        Returns:
            Dict: 结构化摘要
        """
        # 收集前文未解决的伏笔，供 LLM 判断本章是否回收了某些
        unresolved_hooks = []
        if previous_chapters:
            all_resolved = set()
            for ch in previous_chapters:
                all_resolved.update(ch.hooks_resolved)
            for ch in previous_chapters:
                for hook in ch.hooks_planted:
                    if hook not in all_resolved:
                        unresolved_hooks.append(f"第{ch.number}章: {hook}")

        unresolved_hooks_text = "\n".join(unresolved_hooks) if unresolved_hooks else "无"

        prompt = f"""请从以下章节内容中提取结构化信息，以JSON格式返回。

## 第{chapter_plan.chapter_number}章 {chapter_plan.title}

### 章节内容（节选关键部分）
{content[:3000]}

### 前文尚未回收的伏笔
{unresolved_hooks_text}

### 请提取以下信息，返回JSON格式

```json
{{
    "actual_summary": "本章实际发生了什么（2-3句话概括，不要照抄大纲）",
    "hooks_planted": ["本章新埋下的伏笔或悬念（列出具体内容）"],
    "hooks_resolved": ["本章回收了上面列出的哪些前文伏笔（原文匹配）"],
    "character_states": {{"角色名": "状态描述"}},
    "key_items": ["出现的关键道具、线索、地点"],
    "emotional_tone": "本章结尾的情感基调"
}}
```

注意：
- character_states：**重点关注** 角色的生死、健康或位置变化。
  - 如果角色死亡，必须标记为 "已死亡" 或 "Dead"。
  - 如果角色重伤/离队，必须明确说明。
  - 格式示例：{{"张强": "已死亡", "李薇": "右臂受伤", "主角": "获得关键密钥"}}
- hooks_planted：只填本章新埋下的
- hooks_resolved：只填本章回收的"""

        messages = [
            SystemMessage(content="你是一个专业的小说分析助手，擅长从章节内容中提取结构化信息。请严格按JSON格式返回。"),
            HumanMessage(content=prompt)
        ]

        # 使用 JSON Output Mode 提高解析可靠性
        json_llm = self._get_json_llm()
        response = await json_llm.ainvoke(messages)

        # 解析JSON
        result = extract_json_from_response(response.content, "digest")

        # 确保所有字段存在且类型正确
        return {
            "actual_summary": result.get("actual_summary", ""),
            "hooks_planted": result.get("hooks_planted", []),
            "hooks_resolved": result.get("hooks_resolved", []),
            "character_states": result.get("character_states", {}),
            "key_items": result.get("key_items", []),
            "emotional_tone": result.get("emotional_tone", "")
        }

    def _prepare_story_background(self, outline: Outline) -> str:
        """准备故事背景信息"""
        background = []
        background.append(f"**故事简介**: {outline.summary}")
        background.append(f"**主题**: {outline.theme}")
        if outline.setting:
            background.append(f"**背景设定**: {outline.setting}")
        return "\n".join(background)

    def _prepare_characters_info(
        self,
        characters: List[Character],
        involved_names: List[str]
    ) -> str:
        """准备涉及角色的信息"""
        if not involved_names:
            # 如果没有指定，使用所有角色
            involved_chars = characters
        else:
            # 筛选涉及的角色
            involved_chars = [c for c in characters if c.name in involved_names]

        if not involved_chars:
            return "无特定角色信息"

        info_lines = []
        for char in involved_chars:
            info_lines.append(f"**{char.name}** ({char.role})")
            info_lines.append(f"- 性格: {char.personality}")
            info_lines.append(f"- 背景: {char.background}")
            info_lines.append(f"- 动机: {char.motivation}")
            if char.skills:
                info_lines.append(f"- 技能: {char.skills}")
            if char.quirk:
                info_lines.append(f"- 个人特点: {char.quirk}")
            info_lines.append("")

        return "\n".join(info_lines)

    def _prepare_previous_content(
        self,
        previous_chapters: Optional[List[Chapter]],
        outline: Optional[Outline] = None,
        current_chapter_num: int = 1,
        full_context_mode: bool = True  # 模式B：完整上下文
    ) -> str:
        """
        准备前文内容

        Args:
            previous_chapters: 前文章节列表
            outline: 大纲
            current_chapter_num: 当前章节号
            full_context_mode: 是否使用完整上下文模式（模式B）

        构建结构（摘要模式）:
            1. 核心剧情线索
            2. 待回收的伏笔
            3. 全部章节摘要
            4. 角色当前状态
            5. 最近2章结尾片段

        构建结构（完整模式）:
            1. 核心剧情线索
            2. 全部章节完整内容
            3. 伏笔追踪
            4. 角色状态约束
        """
        # 模式B：完整上下文
        if full_context_mode:
            return self._prepare_full_context(previous_chapters, outline, current_chapter_num)
        sections = []

        # 1. 核心剧情线索
        if outline and outline.plot_points:
            relevant_points = []
            for point in outline.plot_points:
                # 尝试解析 chapter_range，如 "第1-5章"
                try:
                    range_str = point.chapter_range.replace("第", "").replace("章", "")
                    if "-" in range_str:
                        start, end = map(int, range_str.split("-"))
                        # 如果该情节点涉及当前章节或之前章节，则包含进来
                        if start <= current_chapter_num:
                            relevant_points.append(f"- 【{point.name}】({point.chapter_range}): {point.description}")
                    else:
                        num = int(range_str)
                        if num <= current_chapter_num:
                            relevant_points.append(f"- 【{point.name}】(第{num}章): {point.description}")
                except:
                    # 解析失败则默认包含
                    relevant_points.append(f"- 【{point.name}】: {point.description}")
            
            if relevant_points:
                sections.append("【核心剧情线索】")
                sections.extend(relevant_points)
                sections.append("")

        if not previous_chapters:
            if not sections:
                return "这是第一章，无前文"
            return "\n".join(sections) + "\n这是第一章，开始创作之旅吧。"

        # 2. 全局伏笔追踪
        all_unresolved_hooks = []
        all_resolved = set()
        for ch in previous_chapters:
            all_resolved.update(ch.hooks_resolved)
        for ch in previous_chapters:
            for hook in ch.hooks_planted:
                if hook not in all_resolved:
                    all_unresolved_hooks.append(f"第{ch.number}章: {hook}")

        if all_unresolved_hooks:
            sections.append("【待回收的伏笔】")
            for hook in all_unresolved_hooks:
                sections.append(f"- {hook}")
            sections.append("")

        # 3. 全部章节摘要
        sections.append("【故事进展】")
        for ch in previous_chapters:
            summary = ch.actual_summary or ch.summary
            sections.append(f"第{ch.number}章 {ch.title}: {summary}")
        sections.append("")

        # 4. 角色当前状态
        latest_states = {}
        for ch in previous_chapters:
            latest_states.update(ch.character_states)
        if latest_states:
            sections.append("【角色当前状态】")
            for name, state in latest_states.items():
                sections.append(f"- {name}: {state}")
            sections.append("")

        # 5. 最近2章的详细内容
        recent = previous_chapters[-2:]
        sections.append("【最近章节详情】")
        for ch in recent:
            sections.append(f"第{ch.number}章 {ch.title}")
            if ch.content:
                tail = ch.content[-800:] if len(ch.content) > 800 else ch.content
                sections.append(f"结尾片段: ...{tail}")
            sections.append("")

        return "\n".join(sections)

    def _prepare_full_context(
        self,
        previous_chapters: Optional[List[Chapter]],
        outline: Optional[Outline] = None,
        current_chapter_num: int = 1
    ) -> str:
        """
        准备完整上下文（模式B）
        将所有前文内容完整纳入上下文窗口
        """
        sections = []

        if not previous_chapters:
            return "【前文】这是第一章，无前文内容。"

        # 1. 核心剧情线索
        if outline and outline.plot_points:
            relevant_points = []
            for point in outline.plot_points:
                try:
                    range_str = point.chapter_range.replace("第", "").replace("章", "")
                    if "-" in range_str:
                        start, end = map(int, range_str.split("-"))
                        if start <= current_chapter_num:
                            relevant_points.append(f"- 【{point.name}】({point.chapter_range}): {point.description}")
                    else:
                        num = int(range_str)
                        if num <= current_chapter_num:
                            relevant_points.append(f"- 【{point.name}】(第{num}章): {point.description}")
                except:
                    relevant_points.append(f"- 【{point.name}】: {point.description}")

            if relevant_points:
                sections.append("【核心剧情线索】")
                sections.extend(relevant_points)
                sections.append("")

        # 2. 伏笔追踪
        all_unresolved_hooks = []
        all_resolved = set()
        for ch in previous_chapters:
            all_resolved.update(ch.hooks_resolved)
        for ch in previous_chapters:
            for hook in ch.hooks_planted:
                if hook not in all_resolved:
                    all_unresolved_hooks.append(f"第{ch.number}章: {hook}")

        if all_unresolved_hooks:
            sections.append("【待回收的伏笔】")
            for hook in all_unresolved_hooks:
                sections.append(f"- {hook}")
            sections.append("")

        # 3. 角色当前状态
        latest_states = {}
        for ch in previous_chapters:
            latest_states.update(ch.character_states)
        if latest_states:
            sections.append("【角色当前状态】（必须严格遵守）")
            for name, state in latest_states.items():
                # 标记不可出场的角色
                if "死" in state or "亡" in state or "消失" in state:
                    sections.append(f"- ⚠️ {name}: {state} （已死亡/消失，绝对不能出场）")
                else:
                    sections.append(f"- {name}: {state}")
            sections.append("")

        # 4. 全部章节完整内容（核心！需要128k上下文窗口）
        sections.append("【前文完整内容】（必须承接以下内容）")
        for ch in previous_chapters:
            sections.append(f"\n{'='*40}")
            sections.append(f"第{ch.number}章 {ch.title}")
            sections.append(f"{'='*40}")
            sections.append(ch.content)

        return "\n".join(sections)

    def set_style(self, style_name: str):
        """
        更改写作风格

        Args:
            style_name: 风格名称
        """
        self.style_name = style_name
        self.style = get_style(style_name)
        self.description = f"负责创作章节内容，使用{style_name}风格"
