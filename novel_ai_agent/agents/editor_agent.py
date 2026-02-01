"""
编辑Agent
负责章节润色、一致性检查、逻辑审查等编辑工作
"""
import json
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from .base_agent import BaseAgent
from ..models.chapter import Chapter
from ..models.character import Character
from ..models.outline import Outline
from ..prompts.editor_prompts import (
    EDITOR_SYSTEM_PROMPT,
    get_polish_prompt,
    get_consistency_check_prompt,
    get_logic_check_prompt,
    get_comprehensive_review_prompt,
    get_targeted_revision_prompt
)


class EditorAgent(BaseAgent):
    """
    编辑Agent

    职责:
    1. 润色章节内容，提升文字质量
    2. 检查角色和情节的一致性
    3. 发现逻辑漏洞
    4. 提供综合评审和修改建议
    5. 执行针对性修改
    """

    def __init__(self):
        super().__init__(
            name="Editor",
            description="负责章节编辑、润色和质量把控"
        )

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行编辑任务

        Args:
            **kwargs: 任务参数
                - action: 操作类型 (polish/check_consistency/check_logic/review/revise)
                - 其他参数根据action不同

        Returns:
            Dict: 包含编辑结果或错误信息
        """
        action = kwargs.get("action", "polish")

        if action == "polish":
            return await self.polish_chapter(**kwargs)
        elif action == "check_consistency":
            return await self.check_consistency(**kwargs)
        elif action == "check_logic":
            return await self.check_logic(**kwargs)
        elif action == "review":
            return await self.comprehensive_review(**kwargs)
        elif action == "revise":
            return await self.targeted_revision(**kwargs)
        else:
            return {"status": "error", "message": f"未知操作: {action}"}

    async def polish_chapter(
        self,
        chapter: Chapter,
        style: str,
        focus_areas: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        润色章节内容

        Args:
            chapter: 章节对象
            style: 写作风格
            focus_areas: 重点关注的方面（如：对话、环境描写、动作场面等）

        Returns:
            Dict: 包含润色后的章节
        """
        try:
            # 构建prompt
            user_prompt = get_polish_prompt(
                content=chapter.content,
                style=style,
                focus_areas=focus_areas
            )

            # 调用LLM
            messages = [
                SystemMessage(content=EDITOR_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt)
            ]

            response = await self.llm.ainvoke(messages)
            polished_content = response.content

            # 创建新版本的章节
            polished_chapter = Chapter(
                number=chapter.number,
                title=chapter.title,
                summary=chapter.summary,
                content=polished_content,
                status=chapter.status,
                version=chapter.version + 1,
                notes=f"润色版本 - 关注: {', '.join(focus_areas) if focus_areas else '全面润色'}"
            )

            polished_chapter.update_word_count()

            return {
                "status": "success",
                "chapter": polished_chapter,
                "original_word_count": chapter.word_count,
                "polished_word_count": polished_chapter.word_count,
                "message": "章节润色完成"
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"润色章节时出错: {str(e)}",
                "error": str(e)
            }

    async def check_consistency(
        self,
        chapter: Chapter,
        characters: List[Character],
        previous_chapters: Optional[List[Chapter]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        检查章节的一致性

        Args:
            chapter: 要检查的章节
            characters: 角色列表
            previous_chapters: 前面的章节（用于上下文）

        Returns:
            Dict: 包含一致性检查结果
        """
        try:
            # 准备角色信息
            characters_info = self._format_characters_info(characters)

            # 准备前文上下文
            previous_context = ""
            if previous_chapters:
                previous_context = self._format_previous_context(previous_chapters)

            # 构建prompt
            user_prompt = get_consistency_check_prompt(
                content=chapter.content,
                characters=characters_info,
                previous_context=previous_context
            )

            # 调用LLM
            messages = [
                SystemMessage(content=EDITOR_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt)
            ]

            response = await self.llm.ainvoke(messages)
            content = response.content

            # 解析JSON响应
            result = self._extract_json_from_response(content)

            return {
                "status": "success",
                "is_consistent": result.get("is_consistent", True),
                "issues": result.get("issues", []),
                "overall_assessment": result.get("overall_assessment", ""),
                "raw_response": content
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"一致性检查时出错: {str(e)}",
                "error": str(e)
            }

    async def check_logic(
        self,
        chapter: Chapter,
        outline: Optional[Outline] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        检查章节的逻辑合理性

        Args:
            chapter: 要检查的章节
            outline: 故事大纲（提供背景信息）

        Returns:
            Dict: 包含逻辑检查结果
        """
        try:
            # 准备故事背景
            story_context = ""
            if outline:
                story_context = f"故事简介: {outline.summary}\n主题: {outline.theme}"
                if outline.setting:
                    story_context += f"\n背景设定: {outline.setting}"

            # 构建prompt
            user_prompt = get_logic_check_prompt(
                content=chapter.content,
                story_context=story_context
            )

            # 调用LLM
            messages = [
                SystemMessage(content=EDITOR_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt)
            ]

            response = await self.llm.ainvoke(messages)
            content = response.content

            # 解析JSON响应
            result = self._extract_json_from_response(content)

            return {
                "status": "success",
                "has_logic_issues": result.get("has_logic_issues", False),
                "issues": result.get("issues", []),
                "suggestions": result.get("suggestions", []),
                "raw_response": content
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"逻辑检查时出错: {str(e)}",
                "error": str(e)
            }

    async def comprehensive_review(
        self,
        chapter: Chapter,
        style: str,
        characters: List[Character],
        outline: Outline,
        previous_chapters: Optional[List[Chapter]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        对章节进行综合评审

        Args:
            chapter: 要评审的章节
            style: 写作风格
            characters: 角色列表
            outline: 故事大纲
            previous_chapters: 前面的章节

        Returns:
            Dict: 包含详细的评审报告
        """
        try:
            # 准备各种信息
            characters_info = self._format_characters_info(characters)
            outline_summary = f"故事简介: {outline.summary}\n主题: {outline.theme}"

            previous_context = ""
            if previous_chapters:
                previous_context = self._format_previous_context(previous_chapters)

            # 构建prompt
            user_prompt = get_comprehensive_review_prompt(
                content=chapter.content,
                style=style,
                characters=characters_info,
                outline_summary=outline_summary,
                previous_context=previous_context
            )

            # 调用LLM
            messages = [
                SystemMessage(content=EDITOR_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt)
            ]

            response = await self.llm.ainvoke(messages)
            content = response.content

            # 解析JSON响应
            result = self._extract_json_from_response(content)

            return {
                "status": "success",
                "review": result,
                "raw_response": content
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"综合评审时出错: {str(e)}",
                "error": str(e)
            }

    async def targeted_revision(
        self,
        chapter: Chapter,
        issues: List[Dict],
        preserve_aspects: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        根据问题列表进行针对性修改

        Args:
            chapter: 要修改的章节
            issues: 问题列表（通常来自检查或评审结果）
            preserve_aspects: 需要保留的方面

        Returns:
            Dict: 包含修改后的章节
        """
        try:
            # 构建prompt
            user_prompt = get_targeted_revision_prompt(
                content=chapter.content,
                issues=issues,
                preserve_aspects=preserve_aspects
            )

            # 调用LLM
            messages = [
                SystemMessage(content=EDITOR_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt)
            ]

            response = await self.llm.ainvoke(messages)
            revised_content = response.content

            # 创建新版本的章节
            revised_chapter = Chapter(
                number=chapter.number,
                title=chapter.title,
                summary=chapter.summary,
                content=revised_content,
                status=chapter.status,
                version=chapter.version + 1,
                notes=f"针对性修改 - 修复了 {len(issues)} 个问题"
            )

            revised_chapter.update_word_count()

            return {
                "status": "success",
                "chapter": revised_chapter,
                "issues_addressed": len(issues),
                "message": f"针对性修改完成，处理了 {len(issues)} 个问题"
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"针对性修改时出错: {str(e)}",
                "error": str(e)
            }

    def _format_characters_info(self, characters: List[Character]) -> str:
        """格式化角色信息"""
        lines = []
        for char in characters:
            lines.append(f"**{char.name}** ({char.role})")
            lines.append(f"性格: {char.personality}")
            lines.append(f"背景: {char.background}")
            if char.relationships:
                lines.append(f"关系: {char.relationships}")
            lines.append("")
        return "\n".join(lines)

    def _format_previous_context(self, previous_chapters: List[Chapter]) -> str:
        """格式化前文上下文"""
        # 取最近的2章
        recent = previous_chapters[-2:] if len(previous_chapters) > 2 else previous_chapters

        lines = []
        for ch in recent:
            lines.append(f"第{ch.number}章 {ch.title}")
            lines.append(f"摘要: {ch.summary}")
            # 内容片段（前200字）
            if ch.content:
                lines.append(f"内容片段: {ch.content[:200]}...")
            lines.append("")

        return "\n".join(lines)

    def _extract_json_from_response(self, response: str) -> Dict:
        """从LLM响应中提取JSON"""
        # 尝试找到JSON代码块
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            json_str = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            json_str = response[start:end].strip()
        else:
            # 假设整个响应就是JSON
            json_str = response.strip()

        # 清理可能的问题
        json_str = json_str.replace('\ufeff', '').replace('\r\n', '\n')

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            # 尝试找到第一个{到最后一个}
            start_idx = json_str.find('{')
            end_idx = json_str.rfind('}')
            if start_idx != -1 and end_idx != -1:
                json_str = json_str[start_idx:end_idx+1]
                return json.loads(json_str)
            else:
                raise ValueError(f"无法从响应中提取有效的JSON: {e}")
