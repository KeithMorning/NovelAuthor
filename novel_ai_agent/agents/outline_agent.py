"""
大纲规划Agent
负责生成和完善故事大纲
"""
import json
from typing import Dict, Any, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from .base_agent import BaseAgent
from ..models.outline import Outline, PlotPoint, ChapterPlan
from ..prompts.outline_prompts import (
    OUTLINE_SYSTEM_PROMPT,
    get_outline_generation_prompt,
    get_outline_refinement_prompt
)


class OutlineAgent(BaseAgent):
    """
    大纲规划Agent

    职责:
    1. 根据主题和需求生成完整大纲
    2. 规划章节结构
    3. 设计情节点和转折
    4. 优化和完善大纲
    """

    def __init__(self):
        super().__init__(
            name="Outline",
            description="负责生成和完善故事大纲，规划章节结构"
        )

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行大纲生成任务

        Args:
            **kwargs: 任务参数
                - action: 操作类型 (generate/refine)
                - 其他参数根据action不同

        Returns:
            Dict: 包含生成的大纲或错误信息
        """
        action = kwargs.get("action", "generate")

        if action == "generate":
            return await self.generate_outline(**kwargs)
        elif action == "refine":
            return await self.refine_outline(**kwargs)
        else:
            return {"status": "error", "message": f"未知操作: {action}"}

    async def generate_outline(
        self,
        title: str,
        genre: str,
        theme: str,
        chapter_count: int = 20,
        words_per_chapter: int = 3000,
        user_requirements: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成小说大纲

        Args:
            title: 小说标题
            genre: 类型
            theme: 主题
            chapter_count: 章节数
            words_per_chapter: 每章字数
            user_requirements: 用户额外需求

        Returns:
            Dict: 包含生成的Outline对象
        """
        try:
            # 构建prompt
            user_prompt = get_outline_generation_prompt(
                title=title,
                genre=genre,
                theme=theme,
                chapter_count=chapter_count,
                words_per_chapter=words_per_chapter,
                user_requirements=user_requirements
            )

            # 调用LLM
            messages = [
                SystemMessage(content=OUTLINE_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt)
            ]

            response = await self.llm.ainvoke(messages)
            content = response.content

            # 解析JSON响应
            outline_data = self._extract_json_from_response(content)

            # 构建Outline对象
            outline = self._build_outline_from_data(
                outline_data,
                title=title,
                genre=genre
            )

            return {
                "status": "success",
                "outline": outline,
                "raw_response": content
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"生成大纲时出错: {str(e)}",
                "error": str(e)
            }

    async def refine_outline(
        self,
        current_outline: Outline,
        user_feedback: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        优化完善大纲

        Args:
            current_outline: 当前大纲
            user_feedback: 用户反馈

        Returns:
            Dict: 包含优化后的Outline对象
        """
        try:
            # 将当前大纲转为JSON字符串
            current_outline_str = current_outline.model_dump_json(indent=2, ensure_ascii=False)

            # 构建prompt
            user_prompt = get_outline_refinement_prompt(
                current_outline=current_outline_str,
                user_feedback=user_feedback
            )

            # 调用LLM
            messages = [
                SystemMessage(content=OUTLINE_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt)
            ]

            response = await self.llm.ainvoke(messages)
            content = response.content

            # 解析JSON响应
            outline_data = self._extract_json_from_response(content)

            # 构建新的Outline对象，版本号+1
            outline = self._build_outline_from_data(
                outline_data,
                title=current_outline.title,
                genre=current_outline.genre,
                version=current_outline.version + 1
            )

            return {
                "status": "success",
                "outline": outline,
                "raw_response": content,
                "changes": "大纲已根据反馈更新"
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"优化大纲时出错: {str(e)}",
                "error": str(e)
            }

    def _extract_json_from_response(self, response: str) -> Dict:
        """
        从LLM响应中提取JSON

        Args:
            response: LLM的响应文本

        Returns:
            Dict: 解析后的JSON对象
        """
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

        # 清理可能的BOM和其他特殊字符
        json_str = json_str.replace('\ufeff', '').replace('\r\n', '\n')

        # 移除可能的尾部逗号（JSON标准不允许）
        import re
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            # 如果解析失败，尝试找到第一个{到最后一个}
            start_idx = json_str.find('{')
            end_idx = json_str.rfind('}')
            if start_idx != -1 and end_idx != -1:
                json_str_cleaned = json_str[start_idx:end_idx+1]
                # 再次清理尾部逗号
                json_str_cleaned = re.sub(r',(\s*[}\]])', r'\1', json_str_cleaned)
                try:
                    return json.loads(json_str_cleaned)
                except json.JSONDecodeError:
                    # 保存原始响应用于调试
                    import os
                    debug_file = os.path.join(os.getcwd(), "debug_response.txt")
                    with open(debug_file, "w", encoding="utf-8") as f:
                        f.write(f"原始响应:\n{response}\n\n")
                        f.write(f"提取的JSON:\n{json_str}\n\n")
                        f.write(f"错误: {e}")
                    raise ValueError(f"无法从响应中提取有效的JSON: {e}\n调试信息已保存到: {debug_file}")
            else:
                raise ValueError(f"无法从响应中提取有效的JSON: {e}")

    def _build_outline_from_data(
        self,
        data: Dict,
        title: str,
        genre: str,
        version: int = 1
    ) -> Outline:
        """
        从字典数据构建Outline对象

        Args:
            data: 字典数据
            title: 标题
            genre: 类型
            version: 版本号

        Returns:
            Outline: 大纲对象
        """
        # 构建情节点列表
        plot_points = []
        for pp_data in data.get("plot_points", []):
            plot_points.append(PlotPoint(**pp_data))

        # 构建章节规划列表
        chapters_plan = []
        for cp_data in data.get("chapters_plan", []):
            chapters_plan.append(ChapterPlan(**cp_data))

        # 计算目标总字数
        target_words = sum(cp.estimated_words for cp in chapters_plan)

        # 构建Outline对象
        outline = Outline(
            title=title,
            genre=genre,
            summary=data.get("summary", ""),
            theme=data.get("theme", ""),
            setting=data.get("setting"),
            plot_points=plot_points,
            chapters_plan=chapters_plan,
            target_words=target_words,
            version=version
        )

        return outline

    def get_chapter_plan(self, outline: Outline, chapter_number: int) -> Optional[ChapterPlan]:
        """
        获取指定章节的规划

        Args:
            outline: 大纲
            chapter_number: 章节号

        Returns:
            ChapterPlan: 章节规划，如果不存在则返回None
        """
        for cp in outline.chapters_plan:
            if cp.chapter_number == chapter_number:
                return cp
        return None
