"""
大纲规划Agent
负责生成和完善故事大纲
"""
import json
from typing import Dict, Any, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from .base_agent import BaseAgent
from ..models.outline import Outline, PlotPoint, ChapterPlan, DetailedChapterPlan
from ..utils.json_parser import extract_json_from_response
from ..prompts.outline_prompts import (
    OUTLINE_SYSTEM_PROMPT,
    get_outline_generation_prompt,
    get_outline_refinement_prompt,
    get_chapter_expansion_prompt
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
                - action: 操作类型 (generate/refine/expand)
                - 其他参数根据action不同

        Returns:
            Dict: 包含任务结果
        """
        action = kwargs.get("action", "generate")

        if action == "generate":
            return await self.generate_outline(**kwargs)
        elif action == "refine":
            return await self.refine_outline(**kwargs)
        elif action == "expand":
            return await self.expand_chapter_plan(**kwargs)
        else:
            return {"status": "error", "message": f"未知操作: {action}"}

    async def expand_chapter_plan(
        self,
        outline: Outline,
        chapter_number: int,
        story_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        针对特定章节生成更详细的规划

        Args:
            outline: 完整大纲
            chapter_number: 章节号
            story_context: 故事上下文（包含世界状态和最近剧情）

        Returns:
            Dict: 包含 DetailedChapterPlan 的结果
        """
        try:
            chapter_plan = self.get_chapter_plan(outline, chapter_number)
            if not chapter_plan:
                return {"status": "error", "message": f"未找到第{chapter_number}章的规划"}

            # 构建大纲上下文（为了节省 token，只提取关键信息）
            outline_context = {
                "summary": outline.summary,
                "theme": outline.theme,
                "setting": outline.setting,
                "plot_points": [p.model_dump() for p in outline.plot_points],
                "previous_chapters_plan": [
                    {"number": c.chapter_number, "title": c.title, "summary": c.summary}
                    for c in outline.chapters_plan if c.chapter_number < chapter_number
                ],
                "next_chapters_plan": [
                    {"number": c.chapter_number, "title": c.title, "summary": c.summary}
                    for c in outline.chapters_plan if c.chapter_number > chapter_number
                ]
            }

            # 格式化故事上下文字符串
            story_context_str = ""
            if story_context:
                parts = []
                
                # 1. 世界状态
                world_state = story_context.get("world_state", {})
                if world_state:
                    state_lines = ["【当前世界状态 (Current World State)】"]
                    for name, state in world_state.items():
                        # 重点标记死亡/下线状态
                        if any(k in state for k in ["死", "亡", "牺牲", "离队", "消失", "Dead", "Gone"]):
                            state_lines.append(f"- ⚠️ {name}: {state} (不可出场)")
                        else:
                            state_lines.append(f"- {name}: {state}")
                    parts.append("\n".join(state_lines))
                
                # 2. 最近剧情
                recent_history = story_context.get("recent_history", [])
                if recent_history:
                    history_lines = ["【最近实际剧情 (Actual History)】"]
                    for h in recent_history:
                        history_lines.append(f"- 第{h['number']}章 {h['title']}: {h['summary']}")
                    parts.append("\n".join(history_lines))
                
                story_context_str = "\n\n".join(parts)

            user_prompt = get_chapter_expansion_prompt(
                chapter_number=chapter_number,
                current_title=chapter_plan.title,
                current_summary=chapter_plan.summary,
                outline_context=json.dumps(outline_context, ensure_ascii=False),
                story_context=story_context_str
            )

            # 调用LLM
            json_llm = self._get_json_llm()
            messages = [
                SystemMessage(content=OUTLINE_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt)
            ]

            response = await json_llm.ainvoke(messages)
            content = response.content

            # 解析JSON响应
            expansion_data = extract_json_from_response(content, "expansion")

            # 鲁棒性处理：如果模型返回了嵌套结构，尝试解包
            if "detailed_plan" in expansion_data:
                expansion_data = expansion_data["detailed_plan"]
            elif "chapter_plan" in expansion_data:
                expansion_data = expansion_data["chapter_plan"]

            # 构建 DetailedChapterPlan 对象
            detailed_plan = DetailedChapterPlan(**expansion_data)

            return {
                "status": "success",
                "detailed_plan": detailed_plan,
                "raw_response": content
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"细化描述章节时出错: {str(e)}",
                "error": str(e)
            }

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

            # 调用LLM（使用 JSON Output Mode）
            json_llm = self._get_json_llm()
            messages = [
                SystemMessage(content=OUTLINE_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt)
            ]

            response = await json_llm.ainvoke(messages)
            content = response.content

            # 解析JSON响应
            outline_data = extract_json_from_response(content, "debug_outline")

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

            # 调用LLM（使用 JSON Output Mode）
            json_llm = self._get_json_llm()
            messages = [
                SystemMessage(content=OUTLINE_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt)
            ]

            response = await json_llm.ainvoke(messages)
            content = response.content

            # 解析JSON响应
            outline_data = extract_json_from_response(content, "debug_outline")

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
