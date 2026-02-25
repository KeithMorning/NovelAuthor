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
    get_character_refinement_prompt,
    get_bulk_character_refinement_prompt
)
from ..utils.json_parser import extract_json_from_response
from ..utils.logger import get_logger, WorkflowStep, LogLevel


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
        self.logger = get_logger("CharacterAgent")

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
        elif action == "refine_characters":
            return await self.refine_characters(**kwargs)
        else:
            return {"status": "error", "message": f"未知操作: {action}"}

    async def generate_characters(
        self,
        outline: Outline = None,
        character_requirements: str = "",
        chapter_count: int = 0,
        title: str = "",
        genre: str = "",
        theme: str = "",
        user_requirements: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """
        根据大纲生成角色设定

        Args:
            outline: 故事大纲（可选，如果未提供则使用title/genre/theme参数）
            character_requirements: 用户对角色的特殊要求
            chapter_count: 目标章节数，0则从大纲自动推断
            title: 小说标题（当outline为None时必需）
            genre: 小说类型（当outline为None时必需）
            theme: 小说主题（当outline为None时必需）
            user_requirements: 用户需求（当outline为None时使用）

        Returns:
            Dict: 包含生成的Character对象列表
        """
        try:
            # 处理两种模式：有大纲和无大纲
            if outline is not None:
                # 模式A：有大纲
                if chapter_count <= 0:
                    chapter_count = len(outline.chapters_plan) if outline.chapters_plan else 20
                outline_key_points = self._extract_outline_key_points(outline)
                story_title = outline.title
                story_genre = outline.genre
                story_theme = outline.theme
                story_summary = outline.summary
            else:
                # 模式B：无大纲（先生成角色的情况）
                if not title or not genre:
                    return {
                        "status": "error",
                        "message": "生成角色时需要提供title和genre参数"
                    }
                chapter_count = chapter_count or 20
                outline_key_points = "暂无大纲，将根据故事主题和类型自动设计角色"
                story_title = title
                story_genre = genre
                story_theme = theme or "根据故事类型自动确定"
                story_summary = f"这是一部{genre}类型的小说，主题是{theme}"

            # 构建prompt
            self.logger.log(
                level=LogLevel.INFO,
                step=WorkflowStep.CHARACTER_GENERATION,
                message=f"开始构建prompt: title={story_title}, genre={story_genre}"
            )

            user_prompt = get_character_generation_prompt(
                title=story_title,
                genre=story_genre,
                summary=story_summary,
                theme=story_theme,
                outline_key_points=outline_key_points,
                character_requirements=character_requirements or user_requirements,
                chapter_count=chapter_count
            )

            self.logger.log(
                level=LogLevel.INFO,
                step=WorkflowStep.CHARACTER_GENERATION,
                message=f"Prompt构建完成, 长度={len(user_prompt)}"
            )

            # 调用LLM
            messages = [
                SystemMessage(content=CHARACTER_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt)
            ]

            # 使用 JSON Output Mode 确保输出合法的 JSON
            json_llm = self._get_json_llm()

            self.logger.log(
                level=LogLevel.INFO,
                step=WorkflowStep.CHARACTER_GENERATION,
                message=f"开始调用API, model={getattr(self.llm, 'model_name', 'unknown')}"
            )

            response_content = await self._stream_invoke(json_llm, messages)
            content = response_content

            # 记录API输出
            self.logger.log(
                level=LogLevel.INFO,
                step=WorkflowStep.CHARACTER_GENERATION,
                message=f"API响应: 输出长度={len(content)}, 内容: {content[:500]}"
            )

            # 解析 JSON 响应
            try:
                characters_data = extract_json_from_response(content, "debug_character_generation")
            except Exception as parse_err:
                self.logger.log(
                    level=LogLevel.ERROR,
                    step=WorkflowStep.CHARACTER_GENERATION,
                    message=f"JSON解析失败: {parse_err}, 原始内容长度: {len(content)}, 内容前500字: {content[:500]}"
                )
                raise

            # 如果返回的不是列表，尝试找到列表
            if isinstance(characters_data, dict):
                # 可能返回的是 {"characters": [...]} 或 {characters: [...]}
                if "characters" in characters_data:
                    characters_data = characters_data["characters"]
                else:
                    # 可能只返回了一个角色
                    characters_data = [characters_data]
            elif isinstance(characters_data, str):
                # 如果返回的是字符串而不是字典，说明 JSON 不完整
                self.logger.log(
                    level=LogLevel.ERROR,
                    step=WorkflowStep.CHARACTER_GENERATION,
                    message=f"JSON解析结果为字符串而非字典: {characters_data[:200]}"
                )
                raise ValueError(f"JSON输出不完整: {characters_data[:100]}")

            # 构建Character对象列表
            characters = []
            for char_data in characters_data:
                # 确保 relationships 是字典类型
                if "relationships" in char_data:
                    rel = char_data["relationships"]
                    # 如果是字符串（YAML解析问题），尝试转换为字典
                    if isinstance(rel, str):
                        # 尝试解析为简单的 key: value 格式
                        new_rel = {}
                        for line in rel.strip().split("\n"):
                            if ":" in line:
                                key, value = line.split(":", 1)
                                new_rel[key.strip()] = value.strip()
                        char_data["relationships"] = new_rel
                    elif not isinstance(rel, dict):
                        # 其他类型转为空字典
                        char_data["relationships"] = {}

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

            # 使用 JSON Output Mode 确保输出合法的 JSON
            json_llm = self._get_json_llm()

            response_content = await self._stream_invoke(json_llm, messages)
            content = response_content

            # 解析 JSON 响应
            character_data = extract_json_from_response(content, "debug_character_refinement")

            # 确保 relationships 是字典类型
            if "relationships" in character_data:
                rel = character_data["relationships"]
                if isinstance(rel, str):
                    new_rel = {}
                    for line in rel.strip().split("\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            new_rel[key.strip()] = value.strip()
                    character_data["relationships"] = new_rel
                elif not isinstance(rel, dict):
                    character_data["relationships"] = {}

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

    async def refine_characters(
        self,
        characters: List[Character],
        refinement_requirements: str,
        story_context: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """
        批量完善角色设定

        Args:
            characters: 当前角色列表
            refinement_requirements: 完善/修改要求
            story_context: 故事大纲上下文

        Returns:
            Dict: 包含完善后的Character列表
        """
        try:
            # 将当前角色列表转为JSON字符串
            current_characters_str = json.dumps(
                [char.model_dump() for char in characters],
                ensure_ascii=False,
                indent=2
            )

            # 构建prompt
            user_prompt = get_bulk_character_refinement_prompt(
                current_characters=current_characters_str,
                refinement_requirements=refinement_requirements,
                story_context=story_context
            )

            # 调用LLM
            messages = [
                SystemMessage(content=CHARACTER_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt)
            ]

            json_llm = self._get_json_llm()
            # 批量生成，响应可能较长
            json_llm = json_llm.bind(max_tokens=8192)

            self.logger.log(
                level=LogLevel.INFO,
                step=WorkflowStep.CHARACTER_GENERATION,
                message="开始调用API批量修改角色..."
            )

            content = await self._stream_invoke(json_llm, messages)

            try:
                characters_data = extract_json_from_response(content, "debug_bulk_character_refinement")
            except Exception as parse_err:
                self.logger.log(
                    level=LogLevel.ERROR,
                    step=WorkflowStep.CHARACTER_GENERATION,
                    message=f"JSON解析失败: {parse_err}"
                )
                raise

            if isinstance(characters_data, dict):
                if "characters" in characters_data:
                    characters_data = characters_data["characters"]
                else:
                    characters_data = [characters_data]

            refined_characters = []
            for char_data in characters_data:
                if "relationships" in char_data:
                    rel = char_data["relationships"]
                    if isinstance(rel, str):
                        new_rel = {}
                        for line in rel.strip().split("\n"):
                            if ":" in line:
                                key, value = line.split(":", 1)
                                new_rel[key.strip()] = value.strip()
                        char_data["relationships"] = new_rel
                    elif not isinstance(rel, dict):
                        char_data["relationships"] = {}

                refined_characters.append(Character(**char_data))

            return {
                "status": "success",
                "characters": refined_characters,
                "count": len(refined_characters),
                "raw_response": content
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"批量修改角色时出错: {str(e)}",
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
            lines.append(f"- {char.name} ({char.role}): {char.core_contradiction[:50]}...")
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
