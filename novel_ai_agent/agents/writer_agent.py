"""
写作Agent
负责生成章节内容
"""
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from .base_agent import BaseAgent
from ..models.chapter import Chapter, ChapterStatus
from ..models.outline import Outline, ChapterPlan
from ..models.character import Character
from ..config.styles import get_style
from ..prompts.writing_prompts import (
    get_writing_system_prompt,
    get_chapter_writing_prompt,
    get_chapter_revision_prompt
)


class WriterAgent(BaseAgent):
    """
    写作Agent

    职责:
    1. 根据大纲和角色设定创作章节
    2. 应用指定的写作风格
    3. 保持角色和情节的一致性
    4. 根据反馈修改章节
    """

    def __init__(self, style_name: str = "中性风格"):
        super().__init__(
            name="Writer",
            description=f"负责创作章节内容，使用{style_name}风格"
        )
        self.style_name = style_name
        self.style = get_style(style_name)

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

            # 准备前文摘要
            previous_content = self._prepare_previous_content(previous_chapters)

            # 构建写作系统prompt
            system_prompt = get_writing_system_prompt(self.style.prompt_template)

            # 构建用户prompt
            user_prompt = get_chapter_writing_prompt(
                chapter_number=chapter_plan.chapter_number,
                chapter_title=chapter_plan.title,
                chapter_summary=chapter_plan.summary,
                target_words=chapter_plan.estimated_words,
                story_background=story_background,
                characters_info=characters_info,
                previous_content=previous_content,
                key_events=chapter_plan.key_events,
                style=self.style_name
            )

            # 调用LLM
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = await self.llm.ainvoke(messages)
            content = response.content

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

            return {
                "status": "success",
                "chapter": chapter,
                "word_count": chapter.word_count,
                "target_words": chapter_plan.estimated_words
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

            # 创建新版本的Chapter
            revised_chapter = Chapter(
                number=chapter.number,
                title=chapter.title,
                summary=chapter.summary,
                content=new_content,
                status=ChapterStatus.REVIEWED,
                version=chapter.version + 1,
                notes=f"根据要求修改: {revision_requirements}"
            )

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
            info_lines.append("")

        return "\n".join(info_lines)

    def _prepare_previous_content(
        self,
        previous_chapters: Optional[List[Chapter]]
    ) -> str:
        """准备前文内容摘要"""
        if not previous_chapters:
            return "这是第一章，无前文"

        # 取最近的1-2章
        recent_chapters = previous_chapters[-2:] if len(previous_chapters) > 2 else previous_chapters

        summaries = []
        for ch in recent_chapters:
            summaries.append(f"第{ch.number}章 {ch.title}: {ch.summary}")

            # 如果有内容，取前300字作为摘要
            if ch.content:
                content_preview = ch.content[:300] + "..."
                summaries.append(f"内容片段: {content_preview}")

        return "\n\n".join(summaries)

    def set_style(self, style_name: str):
        """
        更改写作风格

        Args:
            style_name: 风格名称
        """
        self.style_name = style_name
        self.style = get_style(style_name)
        self.description = f"负责创作章节内容，使用{style_name}风格"
