"""
协调Agent
负责任务分发、流程编排和上下文管理
"""
from typing import Dict, Any, Optional
import uuid
from datetime import datetime
from .base_agent import BaseAgent
from .outline_agent import OutlineAgent
from .character_agent import CharacterAgent
from .writer_agent import WriterAgent
from ..models.novel import Novel
from ..utils.file_manager import file_manager
from ..memory import get_memory_manager
from ..utils.logger import get_logger, WorkflowStep, NovelCreationLogger


class CoordinatorAgent(BaseAgent):
    """
    协调Agent - 系统的主控制器

    职责:
    1. 解析用户意图
    2. 分发任务到专业Agent
    3. 管理全局上下文
    4. 处理多轮对话
    """

    def __init__(self):
        super().__init__(
            name="Coordinator",
            description="协调各个专业Agent,管理整体创作流程"
        )
        self.current_novel: Optional[Novel] = None
        self.context: Dict[str, Any] = {}

        # 初始化各个专业Agent
        self.outline_agent: Optional[OutlineAgent] = None
        self.character_agent: Optional[CharacterAgent] = None
        self.writer_agent: Optional[WriterAgent] = None

    async def execute(self, **kwargs):
        """
        执行协调任务

        Args:
            **kwargs: 包含用户输入和当前状态

        Returns:
            执行结果
        """
        user_input = kwargs.get("user_input", "")
        intent = await self._parse_intent(user_input)

        if intent == "create_novel":
            return await self._handle_create_novel(kwargs)
        elif intent == "create_outline":
            return await self._handle_create_outline(kwargs)
        elif intent == "create_characters":
            return await self._handle_create_characters(kwargs)
        elif intent == "write_chapter":
            return await self._handle_write_chapter(kwargs)
        elif intent == "edit_chapter":
            return await self._handle_edit_chapter(kwargs)
        else:
            return {"status": "unknown_intent", "message": "无法理解您的请求"}

    async def _parse_intent(self, user_input: str) -> str:
        """
        解析用户意图

        Args:
            user_input: 用户输入

        Returns:
            str: 意图类型
        """
        # 简单的关键词匹配,后续可以用LLM来理解
        input_lower = user_input.lower()

        if any(keyword in input_lower for keyword in ["创建小说", "新建小说", "开始写"]):
            return "create_novel"
        elif any(keyword in input_lower for keyword in ["大纲", "规划", "outline"]):
            return "create_outline"
        elif any(keyword in input_lower for keyword in ["角色", "人物", "character"]):
            return "create_characters"
        elif any(keyword in input_lower for keyword in ["写", "章节", "chapter", "第"]):
            return "write_chapter"
        elif any(keyword in input_lower for keyword in ["修改", "编辑", "润色", "edit"]):
            return "edit_chapter"
        else:
            return "unknown"

    async def create_novel_workflow(
        self,
        title: str,
        genre: str,
        theme: str,
        style: str = "中性风格",
        chapter_count: int = 20,
        user_requirements: str = "",
        novel_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        完整的小说创建工作流

        Args:
            title: 小说标题
            genre: 类型
            theme: 主题
            style: 作家风格
            chapter_count: 章节数
            user_requirements: 用户需求
            novel_id: 可选的小说ID，如果未提供则自动生成

        Returns:
            Dict: 包含novel_id和创建状态
        """
        # 生成novel_id（用于日志）
        if not novel_id:
            novel_id = f"novel_{uuid.uuid4().hex[:8]}"

        # 创建日志记录器
        logger = get_logger(novel_id)

        try:
            # 1. 创建小说对象
            logger.step_start(
                WorkflowStep.INIT,
                f"创建小说对象: {title} ({genre})"
            )

            novel = Novel(
                id=novel_id,
                title=title,
                genre=genre,
                author_style=style
            )

            logger.step_success(
                WorkflowStep.INIT,
                "小说对象创建成功",
                details={
                    "novel_id": novel_id,
                    "title": title,
                    "genre": genre,
                    "style": style,
                    "chapter_count": chapter_count
                }
            )

            # 2. 生成大纲
            logger.step_start(
                WorkflowStep.OUTLINE_GENERATION,
                f"开始生成大纲，目标章节数: {chapter_count}"
            )

            self.outline_agent = OutlineAgent()
            outline_result = await self.outline_agent.generate_outline(
                title=title,
                genre=genre,
                theme=theme,
                chapter_count=chapter_count,
                user_requirements=user_requirements
            )

            if outline_result["status"] != "success":
                logger.step_error(
                    WorkflowStep.OUTLINE_GENERATION,
                    "大纲生成失败",
                    Exception(outline_result.get("message", "Unknown error")),
                    details=outline_result
                )
                return outline_result

            novel.outline = outline_result["outline"]

            logger.step_success(
                WorkflowStep.OUTLINE_GENERATION,
                f"大纲生成成功，包含 {len(novel.outline.chapters_plan)} 章",
                details={
                    "chapter_count": len(novel.outline.chapters_plan),
                    "plot_points": len(novel.outline.plot_points)
                }
            )

            # 3. 生成角色
            logger.step_start(
                WorkflowStep.CHARACTER_GENERATION,
                "开始生成角色"
            )

            self.character_agent = CharacterAgent()
            char_result = await self.character_agent.generate_characters(
                outline=novel.outline
            )

            if char_result["status"] != "success":
                logger.step_error(
                    WorkflowStep.CHARACTER_GENERATION,
                    "角色生成失败",
                    Exception(char_result.get("message", "Unknown error")),
                    details=char_result
                )
                return char_result

            for character in char_result["characters"]:
                novel.add_character(character)

            logger.step_success(
                WorkflowStep.CHARACTER_GENERATION,
                f"角色生成成功，创建了 {len(novel.characters)} 个角色",
                details={
                    "character_count": len(novel.characters),
                    "characters": [char.name for char in novel.characters]
                }
            )

            # 4. 保存小说
            logger.step_start(
                WorkflowStep.FILE_SAVING,
                "保存小说文件"
            )

            self.current_novel = novel
            file_manager.save_novel_json(novel)
            file_manager.save_outline_markdown(novel.outline, novel_id)
            file_manager.save_characters_markdown(novel.characters, novel_id)

            logger.step_success(
                WorkflowStep.FILE_SAVING,
                "小说文件保存成功",
                details={
                    "files": ["novel.json", "outline.md", "characters.md"]
                }
            )

            # 5. 加载到记忆系统
            logger.step_start(
                WorkflowStep.MEMORY_LOADING,
                "加载到记忆系统"
            )

            memory_manager = get_memory_manager(novel_id)
            memory_manager.load_novel_to_memory(novel)

            logger.step_success(
                WorkflowStep.MEMORY_LOADING,
                "记忆系统加载成功"
            )

            # 完成
            logger.complete(
                f"小说 '{title}' 创建成功！包含 {len(novel.outline.chapters_plan)} 章大纲和 {len(novel.characters)} 个角色"
            )

            return {
                "status": "success",
                "novel_id": novel_id,
                "novel": novel,
                "message": f"小说 '{title}' 创建成功！包含 {len(novel.outline.chapters_plan)} 章大纲和 {len(novel.characters)} 个角色"
            }

        except Exception as e:
            # 获取当前步骤，如果是字符串则转换为枚举
            current_step_str = logger.workflow_status.get("current_step")
            if current_step_str:
                # 根据字符串查找对应的枚举
                current_step = next(
                    (step for step in WorkflowStep if step.value == current_step_str),
                    WorkflowStep.FAILED
                )
            else:
                current_step = WorkflowStep.INIT

            logger.step_error(
                current_step,
                f"创建小说时出错: {str(e)}",
                e,
                details={"title": title, "genre": genre}
            )

            return {
                "status": "error",
                "message": f"创建小说时出错: {str(e)}",
                "error": str(e),
                "novel_id": novel_id
            }

    async def write_chapter_workflow(
        self,
        novel_id: str,
        chapter_number: int
    ) -> Dict[str, Any]:
        """
        章节写作工作流

        Args:
            novel_id: 小说ID
            chapter_number: 章节号

        Returns:
            Dict: 包含生成的章节
        """
        try:
            # 1. 加载小说
            novel = file_manager.load_novel_json(novel_id)
            if not novel:
                return {
                    "status": "error",
                    "message": f"未找到小说: {novel_id}"
                }

            self.current_novel = novel

            # 2. 获取章节规划
            if not novel.outline:
                return {
                    "status": "error",
                    "message": "小说没有大纲，无法创作章节"
                }

            chapter_plan = None
            for cp in novel.outline.chapters_plan:
                if cp.chapter_number == chapter_number:
                    chapter_plan = cp
                    break

            if not chapter_plan:
                return {
                    "status": "error",
                    "message": f"未找到第{chapter_number}章的规划"
                }

            # 3. 获取前面的章节
            previous_chapters = [ch for ch in novel.chapters if ch.number < chapter_number]
            previous_chapters.sort(key=lambda x: x.number)

            # 4. 创作章节
            self.writer_agent = WriterAgent(style_name=novel.author_style)
            write_result = await self.writer_agent.write_chapter(
                chapter_plan=chapter_plan,
                outline=novel.outline,
                characters=novel.characters,
                previous_chapters=previous_chapters if previous_chapters else None
            )

            if write_result["status"] != "success":
                return write_result

            chapter = write_result["chapter"]

            # 5. 保存章节
            novel.add_chapter(chapter)
            file_manager.save_novel_json(novel)
            file_manager.save_chapter_markdown(chapter, novel_id)
            file_manager.save_novel_markdown(novel)

            # 6. 添加到记忆系统
            memory_manager = get_memory_manager(novel_id)
            memory_manager.add_chapter_to_memory(chapter)

            return {
                "status": "success",
                "chapter": chapter,
                "novel_id": novel_id,
                "message": f"第{chapter_number}章 '{chapter.title}' 创作完成！字数: {chapter.word_count}"
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"创作章节时出错: {str(e)}",
                "error": str(e)
            }

    async def _handle_create_novel(self, params: Dict) -> Dict:
        """处理创建小说请求"""
        return await self.create_novel_workflow(**params)

    async def _handle_create_outline(self, params: Dict) -> Dict:
        """处理创建大纲请求"""
        # 可以单独创建大纲
        self.outline_agent = OutlineAgent()
        return await self.outline_agent.execute(**params)

    async def _handle_create_characters(self, params: Dict) -> Dict:
        """处理创建角色请求"""
        # 可以单独创建角色
        self.character_agent = CharacterAgent()
        return await self.character_agent.execute(**params)

    async def _handle_write_chapter(self, params: Dict) -> Dict:
        """处理写作章节请求"""
        return await self.write_chapter_workflow(**params)

    async def _handle_edit_chapter(self, params: Dict) -> Dict:
        """处理编辑章节请求"""
        novel_id = params.get("novel_id")
        chapter_number = params.get("chapter_number")
        revision_requirements = params.get("revision_requirements", "")

        novel = file_manager.load_novel_json(novel_id)
        if not novel:
            return {"status": "error", "message": f"未找到小说: {novel_id}"}

        chapter = novel.get_chapter(chapter_number)
        if not chapter:
            return {"status": "error", "message": f"未找到第{chapter_number}章"}

        self.writer_agent = WriterAgent(style_name=novel.author_style)
        return await self.writer_agent.revise_chapter(
            chapter=chapter,
            revision_requirements=revision_requirements
        )

    def set_current_novel(self, novel: Novel):
        """设置当前工作的小说"""
        self.current_novel = novel
        self.context["novel_id"] = novel.id
        self.context["novel_title"] = novel.title

    def get_current_novel(self) -> Optional[Novel]:
        """获取当前小说"""
        return self.current_novel

    def update_context(self, key: str, value: Any):
        """更新上下文"""
        self.context[key] = value

    def get_context(self, key: str) -> Any:
        """获取上下文值"""
        return self.context.get(key)

    def clear_context(self):
        """清空上下文"""
        self.context.clear()
        self.current_novel = None
