"""
写作Agent
负责生成章节内容
"""
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from langchain_core.messages import HumanMessage, SystemMessage
from .base_agent import BaseAgent
from ..models.chapter import Chapter, ChapterStatus
from ..models.outline import Outline, ChapterPlan
from ..models.character import Character
from ..config.styles import get_style
from ..utils.json_parser import extract_json_from_response
from ..utils.text_utils import estimate_tokens, strip_generated_chapter_title
from ..prompts.writing_prompts import (
    get_writing_system_prompt,
    get_chapter_writing_prompt,
    get_chapter_revision_prompt,
    get_chapter_edit_prompt,
    apply_edits,
    get_chapter_edit_system_prompt
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
        on_token: Optional[Callable[[str], None]] = None,
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
            target_words = self.settings.default_chapter_words

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

            # 流式调用LLM，实时输出 token
            content = await self._stream_invoke(
                self.llm,
                messages,
                on_token=on_token
            )

            self.logger.log(
                level=LogLevel.INFO,
                step=WorkflowStep.CHAPTER_WRITING,
                message=f"API响应: content长度={len(content)}"
            )

            # 计算输入token数量（粗略估算）
            input_text = system_prompt + user_prompt
            input_tokens_estimate = estimate_tokens(input_text)

            # 计算输出token数量
            output_tokens_estimate = estimate_tokens(content)

            # 记录章节写作统计到日志
            self.logger.log(
                level=LogLevel.INFO,
                step=WorkflowStep.CHAPTER_WRITING,
                message=f"章节写作完成: 第{chapter_plan.chapter_number}章, 输入~{input_tokens_estimate}, 输出~{output_tokens_estimate}, 内容长度{len(content)}"
            )

            # 清理生成的文本，防止带有重复的大标题 (如 `# 第1章 XXX`)
            content = strip_generated_chapter_title(content)

            # 空响应保护：绝不允许把空章节写入存档
            if len(content.strip()) < 500:
                raise RuntimeError(
                    f"LLM 返回的章节内容过短（{len(content.strip())} 字符），已中止保存"
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
        on_token: Optional[Callable[[str], None]] = None,
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

            new_content = await self._stream_invoke(
                self.llm,
                messages,
                on_token=on_token
            )

            # 清理生成的文本，防止带有重复的大标题 (如 `# 第1章 XXX`)
            new_content = strip_generated_chapter_title(new_content)

            if len(new_content.strip()) < 500:
                raise RuntimeError(
                    f"LLM 返回的修改内容过短（{len(new_content.strip())} 字符），已中止保存"
                )

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

    async def edit_chapter(
        self,
        chapter: Chapter,
        revision_requirements: str,
        on_token: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        局部编辑章节（Edit Instruction 模式）。

        相比 revise_chapter 全文重写，此方法只输出编辑指令 JSON，
        由 apply_edits() 在本地将 patch 应用到原文，大幅减少 LLM 输出 token。

        若 LLM 判断修改量过大（summary 含 FULL_REWRITE），自动降级到 revise_chapter。
        """
        try:
            # 构建 prompt
            system_prompt = get_chapter_edit_system_prompt(self.style.prompt_template)
            user_prompt = get_chapter_edit_prompt(
                original_content=chapter.content or "",
                revision_requirements=revision_requirements
            )
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            # 调用 JSON 模式 LLM（输出量远少于全文重写）
            json_llm = self._get_json_llm()
            raw = await self._stream_invoke(json_llm, messages, on_token=on_token)

            # 解析 JSON
            raw_stripped = raw.strip()
            if raw_stripped.startswith("```"):
                parts = raw_stripped.split("```")
                raw_stripped = parts[1][4:] if parts[1].startswith("json") else parts[1]
            try:
                parsed = json.loads(raw_stripped.strip())
            except Exception as e:
                return {"status": "error", "message": f"解析局部修改 JSON 失败: {e}\nRaw={raw_stripped[:100]}"}

            summary = parsed.get("summary", "")

            # LLM 主动提示需要全文重写
            if "FULL_REWRITE_NEEDED" in summary.upper() or "FULL_REWRITE" in summary.upper():
                return await self.revise_chapter(
                    chapter=chapter,
                    revision_requirements=revision_requirements,
                    context="（EditInstruction 降级为全文重写）",
                    on_token=on_token
                )

            edits = parsed.get("edits", [])
            if not edits:
                return {
                    "status": "error", 
                    "message": "AI 未能生成任何有效的局部修改指令。可能是Prompt施加了过多约束，或者它认为不需要修改。",
                    "raw_response": raw_stripped
                }

            new_content, failed = apply_edits(chapter.content or "", edits)

            # 打印调试信息到日志
            self.logger.log(
                level=LogLevel.INFO,
                step=WorkflowStep.CHAPTER_WRITING,
                message=f"edit_chapter raw: {raw_stripped}\nFailed edits: {failed}"
            )

            # 如果超过一半的指令未命中，也降级
            if len(failed) > len(edits) / 2:
                self.logger.log(
                    level=LogLevel.WARNING,
                    step=WorkflowStep.CHAPTER_WRITING,
                    message=f"edit_chapter anchor 命中率过低 ({len(failed)}/{len(edits)} failed)，开始降级。Failed: {failed}"
                )
                return await self.revise_chapter(
                    chapter=chapter,
                    revision_requirements=revision_requirements,
                    context="（EditInstruction anchor 命中率过低，降级为全文重写）",
                    on_token=on_token
                )

            # 创建新版 Chapter
            edited_chapter = chapter.model_copy(update={
                "content": new_content,
                "status": ChapterStatus.REVIEWED,
                "version": chapter.version + 1,
                "notes": f"局部编辑: {revision_requirements[:60]}",
                "updated_at": datetime.now()
            })
            edited_chapter.update_word_count()

            return {
                "status": "success",
                "chapter": edited_chapter,
                "word_count": edited_chapter.word_count,
                "version": edited_chapter.version,
                "edit_count": len(edits),
                "failed_edits": failed,
                "mode": "edit_instruction"
            }

        except Exception as e:
            # 任何异常都降级到 revise_chapter
            return await self.revise_chapter(
                chapter=chapter,
                revision_requirements=revision_requirements,
                context=f"（EditInstruction 解析失败 {e}，降级为全文重写）",
                on_token=on_token
            )

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

        # 摘要不能只看开头：章节的死亡、转折、伏笔回收往往发生在结尾。
        # 短章节直接用全文；长章节保留开头 4000 字 + 结尾 3000 字。
        if len(content) <= 6000:
            digest_excerpt = content
        else:
            digest_excerpt = (
                content[:4000]
                + "\n\n……（中段省略）……\n\n"
                + content[-3000:]
            )

        prompt = f"""请从以下章节内容中提取结构化信息，以JSON格式返回。

## 第{chapter_plan.chapter_number}章 {chapter_plan.title}

### 章节内容（开头与结尾节选）
{digest_excerpt}

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

        # 使用 JSON Output Mode 提高解析可靠性，流式静默收集
        json_llm = self._get_json_llm()
        digest_content = await self._stream_invoke(json_llm, messages)

        # 解析JSON
        result = extract_json_from_response(digest_content, "digest")

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
        
        if getattr(outline, "core_concepts", ""):
            background.append(f"**核心概念与设定（强制物理法则/世界观约束）**:\n{outline.core_concepts}")
            
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
            info_lines.append(f"- 核心特质与矛盾: {char.core_contradiction}")
            info_lines.append(f"- 深层渴望: {char.deep_desire}")
            info_lines.append(f"- 人生滤镜(背景): {char.life_filter}")
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
        full_context_mode: Optional[bool] = None,
        max_context_chars: Optional[int] = None,
    ) -> str:
        """
        准备前文内容。

        默认优先使用完整上下文（模式B）；当前文全文超过字符预算时，
        自动降级为“摘要 + 最近章节片段”，避免长篇小说撑爆上下文窗口。

        Args:
            previous_chapters: 前文章节列表
            outline: 大纲
            current_chapter_num: 当前章节号
            full_context_mode: 是否优先使用完整上下文；默认读取 settings
            max_context_chars: 全文上下文字符预算；默认读取 settings

        Returns:
            str: 可直接放入 prompt 的前文内容
        """
        if full_context_mode is None:
            configured = getattr(self.settings, "full_context_mode", True)
            full_context_mode = configured if isinstance(configured, bool) else True
        if max_context_chars is None:
            configured = getattr(self.settings, "max_previous_context_chars", 80000)
            max_context_chars = configured if isinstance(configured, int) else 80000

        # 1. 核心剧情线索（两种模式共用）
        sections = self._plot_point_sections(outline, current_chapter_num)

        if not previous_chapters:
            if not sections:
                return "【前文】这是第一章，无前文内容。"
            return "\n".join(sections) + "\n【前文】这是第一章，开始创作之旅吧。"

        hooks = self._collect_unresolved_hooks(previous_chapters)
        states = self._collect_character_states(previous_chapters)

        if full_context_mode:
            full_chars = sum(len(ch.content or "") for ch in previous_chapters)
            if full_chars <= max_context_chars:
                return self._render_full_context(
                    sections, hooks, states, previous_chapters
                )

            # 超过预算：记录一次告警后降级，避免无提示地损失上下文
            self.logger.log(
                level=LogLevel.WARNING,
                step=WorkflowStep.CHAPTER_WRITING,
                message=(
                    f"前文全文 {full_chars} 字符超过预算 "
                    f"{max_context_chars}，自动切换为摘要上下文"
                ),
            )

        return self._render_summary_context(
            sections, hooks, states, previous_chapters
        )

    @staticmethod
    def _plot_point_sections(
        outline: Optional[Outline],
        current_chapter_num: int,
    ) -> List[str]:
        """提取当前章节之前的核心剧情线索"""
        if not outline or not outline.plot_points:
            return []

        relevant_points: List[str] = []
        for point in outline.plot_points:
            # 尝试解析 chapter_range，如 "第1-5章"
            try:
                range_str = point.chapter_range.replace("第", "").replace("章", "")
                if "-" in range_str:
                    start, _end = map(int, range_str.split("-", 1))
                    if start <= current_chapter_num:
                        relevant_points.append(
                            f"- 【{point.name}】({point.chapter_range}): {point.description}"
                        )
                else:
                    num = int(range_str)
                    if num <= current_chapter_num:
                        relevant_points.append(
                            f"- 【{point.name}】(第{num}章): {point.description}"
                        )
            except (ValueError, AttributeError):
                # 解析失败则默认包含
                relevant_points.append(f"- 【{point.name}】: {point.description}")

        if not relevant_points:
            return []
        return ["【核心剧情线索】", *relevant_points, ""]

    @staticmethod
    def _collect_unresolved_hooks(previous_chapters: List[Chapter]) -> List[str]:
        """收集前文中尚未回收的伏笔"""
        resolved = set()
        for ch in previous_chapters:
            resolved.update(ch.hooks_resolved or [])

        hooks: List[str] = []
        for ch in previous_chapters:
            for hook in ch.hooks_planted or []:
                if hook not in resolved:
                    hooks.append(f"第{ch.number}章: {hook}")
        return hooks

    @staticmethod
    def _collect_character_states(previous_chapters: List[Chapter]) -> Dict[str, str]:
        """合并所有前文章节中的角色状态（后面的状态覆盖前面的）"""
        states: Dict[str, str] = {}
        for ch in previous_chapters:
            states.update(ch.character_states or {})
        return states

    @staticmethod
    def _append_hook_sections(sections: List[str], hooks: List[str]) -> None:
        if not hooks:
            return
        sections.append("【待回收的伏笔】")
        sections.extend(f"- {hook}" for hook in hooks)
        sections.append("")

    @staticmethod
    def _append_state_sections(
        sections: List[str],
        states: Dict[str, str],
        strict: bool = False,
    ) -> None:
        if not states:
            return

        sections.append("【角色当前状态】（必须严格遵守）" if strict else "【角色当前状态】")
        for name, state in states.items():
            state_text = str(state)
            if strict and any(k in state_text for k in ("死", "亡", "消失")):
                sections.append(
                    f"- ⚠️ {name}: {state_text} （已死亡/消失，绝对不能出场）"
                )
            else:
                sections.append(f"- {name}: {state_text}")
        sections.append("")

    def _render_full_context(
        self,
        sections: List[str],
        hooks: List[str],
        states: Dict[str, str],
        previous_chapters: List[Chapter],
    ) -> str:
        """渲染完整上下文（模式B）"""
        sections = list(sections)
        self._append_hook_sections(sections, hooks)
        self._append_state_sections(sections, states, strict=True)

        sections.append("【前文完整内容】（必须承接以下内容）")
        for ch in previous_chapters:
            sections.append(f"\n{'=' * 40}")
            sections.append(f"第{ch.number}章 {ch.title}")
            sections.append(f"{'=' * 40}")
            sections.append(ch.content or "")

        return "\n".join(sections)

    def _render_summary_context(
        self,
        sections: List[str],
        hooks: List[str],
        states: Dict[str, str],
        previous_chapters: List[Chapter],
    ) -> str:
        """渲染摘要上下文（token 友好模式）"""
        sections = list(sections)
        self._append_hook_sections(sections, hooks)

        # 全部章节摘要
        sections.append("【故事进展】")
        for ch in previous_chapters:
            summary = ch.actual_summary or ch.summary
            sections.append(f"第{ch.number}章 {ch.title}: {summary}")
        sections.append("")

        self._append_state_sections(sections, states, strict=True)

        # 最近 2 章的结尾片段，保证行文衔接
        sections.append("【最近章节详情】")
        for ch in previous_chapters[-2:]:
            sections.append(f"第{ch.number}章 {ch.title}")
            if ch.content:
                tail = ch.content[-800:]
                sections.append(f"结尾片段: ...{tail}")
            sections.append("")

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
