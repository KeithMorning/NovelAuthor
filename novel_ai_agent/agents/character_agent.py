"""
角色设定Agent
负责创建和完善角色设定
"""
import json
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, SystemMessage
from .base_agent import BaseAgent
from ..models.character import Character
from ..models.outline import Outline
from ..prompts.character_prompts import (
    CHARACTER_SYSTEM_PROMPT,
    get_character_generation_prompt,
    get_character_refinement_prompt
)
from ..utils.yaml_parser import extract_yaml_from_response


class CharacterAgent(BaseAgent):
    """
    角色设定Agent

    职责:
    1. 根据大纲生成角色设定
    2. 设计角色性格和背景
    3. 构建角色关系网络
    4. 规划角色发展弧线
    """

    def __init__(self):
        super().__init__(
            name="Character",
            description="负责创建和完善角色设定，构建角色关系网络"
        )

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行角色生成任务

        Args:
            **kwargs: 任务参数
                - action: 操作类型 (generate/refine)
                - 其他参数根据action不同

        Returns:
            Dict: 包含生成的角色列表或错误信息
        """
        action = kwargs.get("action", "generate")

        if action == "generate":
            return await self.generate_characters(**kwargs)
        elif action == "refine":
            return await self.refine_character(**kwargs)
        else:
            return {"status": "error", "message": f"未知操作: {action}"}

    async def generate_characters(
        self,
        outline: Outline,
        character_requirements: str = "",
        chapter_count: int = 0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        根据大纲生成角色设定

        Args:
            outline: 故事大纲
            character_requirements: 用户对角色的特殊要求
            chapter_count: 目标章节数，0则从大纲自动推断

        Returns:
            Dict: 包含生成的Character对象列表
        """
        try:
            # 如果未指定章节数，从大纲推断
            if chapter_count <= 0:
                chapter_count = len(outline.chapters_plan) if outline.chapters_plan else 20

            # 提取大纲关键信息
            outline_key_points = self._extract_outline_key_points(outline)

            # 构建prompt
            user_prompt = get_character_generation_prompt(
                title=outline.title,
                genre=outline.genre,
                summary=outline.summary,
                theme=outline.theme,
                outline_key_points=outline_key_points,
                character_requirements=character_requirements,
                chapter_count=chapter_count
            )

            # 调用LLM
            messages = [
                SystemMessage(content=CHARACTER_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt)
            ]

            response = await self.llm.ainvoke(messages)
            content = response.content

            # 解析YAML响应
            characters_data = extract_yaml_from_response(content, "debug_character_generation")

            # 如果返回的不是列表，尝试找到列表
            if isinstance(characters_data, dict):
                # 可能返回的是 {"characters": [...]} 或 {characters: [...]}
                if "characters" in characters_data:
                    characters_data = characters_data["characters"]
                else:
                    # 可能只返回了一个角色
                    characters_data = [characters_data]

            # 构建Character对象列表
            characters = []
            for char_data in characters_data:
                character = Character(**char_data)
                characters.append(character)

            return {
                "status": "success",
                "characters": characters,
                "count": len(characters),
                "raw_response": content
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"生成角色时出错: {str(e)}",
                "error": str(e)
            }

    async def refine_character(
        self,
        character: Character,
        refinement_requirements: str,
        story_context: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """
        完善单个角色设定

        Args:
            character: 当前角色
            refinement_requirements: 完善要求
            story_context: 故事上下文

        Returns:
            Dict: 包含完善后的Character对象
        """
        try:
            # 将当前角色转为JSON字符串
            current_character_str = character.model_dump_json(indent=2, ensure_ascii=False)

            # 构建prompt
            user_prompt = get_character_refinement_prompt(
                current_character=current_character_str,
                refinement_requirements=refinement_requirements,
                story_context=story_context
            )

            # 调用LLM
            messages = [
                SystemMessage(content=CHARACTER_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt)
            ]

            response = await self.llm.ainvoke(messages)
            content = response.content

            # 解析YAML响应
            character_data = extract_yaml_from_response(content, "debug_character_refinement")

            # 构建新的Character对象
            refined_character = Character(**character_data)

            return {
                "status": "success",
                "character": refined_character,
                "raw_response": content
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"完善角色时出错: {str(e)}",
                "error": str(e)
            }

    def _extract_outline_key_points(self, outline: Outline) -> str:
        """
        提取大纲的关键信息

        Args:
            outline: 大纲对象

        Returns:
            str: 格式化的关键信息
        """
        key_points = []

        # 添加情节点
        if outline.plot_points:
            key_points.append("主要情节点:")
            for i, pp in enumerate(outline.plot_points, 1):
                key_points.append(f"{i}. {pp.name} - {pp.description}")

        # 添加部分章节规划
        if outline.chapters_plan:
            key_points.append("\n前几章梗概:")
            for cp in outline.chapters_plan[:5]:  # 只取前5章
                key_points.append(f"第{cp.chapter_number}章 {cp.title}: {cp.summary}")
                if cp.characters_involved:
                    key_points.append(f"  涉及角色: {', '.join(cp.characters_involved)}")

        return "\n".join(key_points)

    def get_characters_summary(self, characters: List[Character]) -> str:
        """
        生成角色列表摘要

        Args:
            characters: 角色列表

        Returns:
            str: 格式化的角色摘要
        """
        lines = []
        for char in characters:
            lines.append(f"- {char.name} ({char.role}): {char.personality[:50]}...")
        return "\n".join(lines)

    def get_character_by_name(self, characters: List[Character], name: str) -> Character:
        """
        根据名字查找角色

        Args:
            characters: 角色列表
            name: 角色名字

        Returns:
            Character: 找到的角色

        Raises:
            ValueError: 如果角色不存在
        """
        for char in characters:
            if char.name == name:
                return char
        raise ValueError(f"未找到角色: {name}")
