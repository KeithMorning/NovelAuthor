"""
协调Agent
负责任务分发、流程编排和上下文管理
"""
from typing import Dict, Any, Optional, Callable
import asyncio
import uuid
from datetime import datetime
from .base_agent import BaseAgent
from .outline_agent import OutlineAgent
from .character_agent import CharacterAgent
from .writer_agent import WriterAgent
from ..models.novel import Novel
from ..utils.file_manager import file_manager
from ..memory import get_memory_manager
from ..utils.logger import get_logger, WorkflowStep, NovelCreationLogger, LogLevel


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
        self.logger = get_logger("Coordinator")

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

            # 2. 先生成角色（在大纲之前，以便大纲可以使用角色名）
            logger.step_start(
                WorkflowStep.CHARACTER_GENERATION,
                "开始生成角色"
            )

            self.character_agent = CharacterAgent()
            # 先生成角色，不需要outline（因为还没有）
            char_result = await self.character_agent.generate_characters(
                outline=None,
                chapter_count=chapter_count,
                title=title,
                genre=genre,
                theme=theme,
                user_requirements=user_requirements
            )

            if char_result["status"] != "success":
                logger.step_error(
                    WorkflowStep.CHARACTER_GENERATION,
                    "角色生成失败",
                    Exception(char_result.get("message", "Unknown error")),
                    details=char_result
                )
                return char_result

            # 保存角色到novel对象（临时存储，用于后续生成大纲）
            temp_characters = char_result["characters"]
            for character in temp_characters:
                novel.add_character(character)

            logger.step_success(
                WorkflowStep.CHARACTER_GENERATION,
                f"角色生成成功，创建了 {len(novel.characters)} 个角色",
                details={
                    "character_count": len(novel.characters),
                    "characters": [char.name for char in novel.characters]
                }
            )

            # 3. 生成大纲（使用已创建的角色信息）
            logger.step_start(
                WorkflowStep.OUTLINE_GENERATION,
                f"开始生成大纲，目标章节数: {chapter_count}"
            )

            self.outline_agent = OutlineAgent()

            # 格式化角色信息传递给大纲生成
            character_info = _format_character_info_for_outline(novel.characters)

            outline_result = await self.outline_agent.generate_outline(
                title=title,
                genre=genre,
                theme=theme,
                chapter_count=chapter_count,
                user_requirements=user_requirements,
                character_info=character_info
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

            # 5. 加载到记忆系统 (暂时禁用,因为目前未使用)
            # TODO: 当实现章节写作时的上下文检索功能后，再启用此步骤
            logger.step_start(
                WorkflowStep.MEMORY_LOADING,
                "跳过记忆系统加载（当前未使用）"
            )

            # memory_manager = get_memory_manager(novel_id)
            # memory_manager.load_novel_to_memory(novel)

            logger.step_success(
                WorkflowStep.MEMORY_LOADING,
                "记忆系统加载已跳过（当前功能未启用）"
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

    async def write_all_chapters_workflow(
        self,
        novel_id: str,
        start_chapter: int = 1,
        progress_callback=None,
        enable_expansion: bool = True,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        批量写作全部章节工作流

        按顺序从 start_chapter 开始写作所有章节，跳过已完成的章节（除非 force=True）。
        某章失败时停止并返回已完成的信息，支持通过 start_chapter 从断点恢复。

        Args:
            novel_id: 小说ID
            start_chapter: 起始章节号（默认1）
            progress_callback: 可选的进度回调函数，签名为 (chapter_number, total, status, message)
            force: 是否强制重写已存在的章节（默认False）

        Returns:
            Dict: 包含写作结果
        """
        try:
            # 1. 加载小说
            novel = file_manager.load_novel_json(novel_id)
            if not novel:
                return {
                    "status": "error",
                    "message": f"未找到小说: {novel_id}"
                }

            if not novel.outline or not novel.outline.chapters_plan:
                return {
                    "status": "error",
                    "message": "小说没有大纲或章节规划，无法批量创作"
                }

            # 2. 确定需要写作的章节
            total_chapters = len(novel.outline.chapters_plan)
            written_numbers = {ch.number for ch in novel.chapters} if novel.chapters else set()

            if force:
                # force=True: 重写所有从 start_chapter 开始的章节
                chapters_to_write = [
                    cp for cp in novel.outline.chapters_plan
                    if cp.chapter_number >= start_chapter
                ]
            else:
                # force=False: 跳过已存在的章节
                chapters_to_write = [
                    cp for cp in novel.outline.chapters_plan
                    if cp.chapter_number >= start_chapter and cp.chapter_number not in written_numbers
                ]
            chapters_to_write.sort(key=lambda x: x.chapter_number)

            if not chapters_to_write:
                action = "重写" if force else "写作"
                return {
                    "status": "success",
                    "message": f"所有章节已完成，无需{action}",
                    "novel_id": novel_id,
                    "chapters_written": 0,
                    "total_chapters": total_chapters
                }

            # 3. 逐章写作
            completed = []
            total_words = 0

            for i, chapter_plan in enumerate(chapters_to_write):
                chapter_num = chapter_plan.chapter_number

                # 进度回调（支持同步和异步回调）
                if progress_callback:
                    cb_result = progress_callback(
                        chapter_num, total_chapters,
                        "writing",
                        f"正在创作第{chapter_num}章: {chapter_plan.title}"
                    )
                    if asyncio.iscoroutine(cb_result):
                        await cb_result

                # 调用已有的单章写作工作流
                result = await self.write_chapter_workflow(
                    novel_id=novel_id,
                    chapter_number=chapter_num,
                    enable_expansion=enable_expansion,
                    force=force
                )

                if result["status"] != "success":
                    # 某章失败，停止并返回部分结果
                    if progress_callback:
                        cb_result = progress_callback(
                            chapter_num, total_chapters,
                            "error",
                            f"第{chapter_num}章创作失败: {result.get('message', '未知错误')}"
                        )
                        if asyncio.iscoroutine(cb_result):
                            await cb_result

                    return {
                        "status": "partial",
                        "message": f"第{chapter_num}章创作失败: {result.get('message', '')}。已完成 {len(completed)}/{len(chapters_to_write)} 章。",
                        "novel_id": novel_id,
                        "chapters_written": len(completed),
                        "chapters_completed": completed,
                        "total_chapters": total_chapters,
                        "total_words": total_words,
                        "failed_chapter": chapter_num,
                        "error": result.get("error", "")
                    }

                # 记录完成
                chapter = result["chapter"]
                completed.append({
                    "number": chapter_num,
                    "title": chapter.title,
                    "word_count": chapter.word_count
                })
                total_words += chapter.word_count

                if progress_callback:
                    cb_result = progress_callback(
                        chapter_num, total_chapters,
                        "done",
                        f"第{chapter_num}章完成: {chapter.title} ({chapter.word_count}字)"
                    )
                    if asyncio.iscoroutine(cb_result):
                        await cb_result

            return {
                "status": "success",
                "message": f"全部 {len(completed)} 章创作完成！总字数: {total_words}",
                "novel_id": novel_id,
                "chapters_written": len(completed),
                "chapters_completed": completed,
                "total_chapters": total_chapters,
                "total_words": total_words
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"批量创作时出错: {str(e)}",
                "error": str(e)
            }

    async def write_chapter_workflow(
        self,
        novel_id: str,
        chapter_number: int,
        enable_expansion: bool = True,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        章节写作工作流

        Args:
            novel_id: 小说ID
            chapter_number: 章节号
            force: 是否强制重写已存在的章节

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

            # 4. 获取前面的章节 (提前获取以构建上下文)
            previous_chapters = [ch for ch in novel.chapters if ch.number < chapter_number]
            previous_chapters.sort(key=lambda x: x.number)

            # 3. 检查是否需要细化章节规划
            if enable_expansion and not chapter_plan.detailed_plan:
                self.logger.log(
                    level=LogLevel.INFO,
                    step=WorkflowStep.CHAPTER_WRITING,
                    message=f"正在细化第{chapter_number}章的规划..."
                )
                
                # 构建故事上下文
                story_context = {
                    "world_state": {},
                    "recent_history": []
                }
                
                if previous_chapters:
                    # 提取世界状态
                    latest_states = {}
                    for ch in previous_chapters:
                        if ch.character_states:
                            latest_states.update(ch.character_states)
                    story_context["world_state"] = latest_states
                    
                    # 提取最近章节摘要（取出最近5章）
                    recent_chapters = previous_chapters[-5:]
                    story_context["recent_history"] = [
                        {
                            "number": ch.number, 
                            "title": ch.title, 
                            "summary": ch.actual_summary or ch.summary
                        } 
                        for ch in recent_chapters
                    ]

                self.outline_agent = OutlineAgent()
                expand_result = await self.outline_agent.expand_chapter_plan(
                    outline=novel.outline,
                    chapter_number=chapter_number,
                    story_context=story_context  # 传入上下文
                )
                if expand_result["status"] == "success":
                    chapter_plan.detailed_plan = expand_result["detailed_plan"]
                    # 保存细化后的规划
                    file_manager.save_novel_json(novel)
                    self.logger.log(
                        level=LogLevel.SUCCESS,
                        step=WorkflowStep.CHAPTER_WRITING,
                        message=f"第{chapter_number}章规划细化完成"
                    )
                else:
                    self.logger.log(
                        level=LogLevel.WARNING,
                        step=WorkflowStep.CHAPTER_WRITING,
                        message=f"细化章节规划失败，将使用原始规划: {expand_result.get('message')}"
                    )

            # 5. 创作章节
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
            if force:
                # force=True: 删除已存在的章节，重新添加
                existing = novel.get_chapter(chapter_number)
                if existing:
                    novel.chapters = [c for c in novel.chapters if c.number != chapter_number]
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

    async def edit_outline_workflow(
        self,
        novel_id: str,
        feedback: str,
        chapter_number: int = None
    ) -> Dict[str, Any]:
        """
        修改大纲工作流

        Args:
            novel_id: 小说ID
            feedback: 用户修改意见
            chapter_number: 可选，指定修改某一章

        Returns:
            Dict: 修改结果
        """
        try:
            # 加载小说
            novel = file_manager.load_novel_json(novel_id)
            if not novel:
                return {"status": "error", "message": f"未找到小说: {novel_id}"}

            if not novel.outline:
                return {"status": "error", "message": "小说没有大纲"}

            # 调用OutlineAgent优化大纲
            self.outline_agent = OutlineAgent()
            result = await self.outline_agent.refine_outline(
                current_outline=novel.outline,
                user_feedback=feedback,
                chapter_number=chapter_number
            )

            if result["status"] != "success":
                return result

            # 更新小说大纲
            novel.outline = result["outline"]
            file_manager.save_novel_json(novel)
            file_manager.save_outline_markdown(novel.outline, novel_id)

            changed_info = result.get("changed", "全大纲")
            return {
                "status": "success",
                "message": f"大纲修改成功 ({changed_info})",
                "novel_id": novel_id,
                "changed": changed_info
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"修改大纲时出错: {str(e)}",
                "error": str(e)
            }

    async def edit_character_workflow(
        self,
        novel_id: str,
        character_name: str,
        feedback: str
    ) -> Dict[str, Any]:
        """
        修改角色工作流

        Args:
            novel_id: 小说ID
            character_name: 要修改的角色名
            feedback: 用户修改意见

        Returns:
            Dict: 修改结果
        """
        try:
            # 加载小说
            novel = file_manager.load_novel_json(novel_id)
            if not novel:
                return {"status": "error", "message": f"未找到小说: {novel_id}"}

            # 查找角色
            target_character = None
            for char in novel.characters:
                if char.name == character_name:
                    target_character = char
                    break

            if not target_character:
                return {
                    "status": "error",
                    "message": f"未找到角色: {character_name}。可用角色: {[c.name for c in novel.characters]}"
                }

            # 调用CharacterAgent优化角色
            self.character_agent = CharacterAgent()
            result = await self.character_agent.refine_character(
                character=target_character,
                refinement_requirements=feedback,
                story_context=f"小说标题: {novel.title}\n类型: {novel.genre}\n大纲: {novel.outline.summary if novel.outline else '暂无'}"
            )

            if result["status"] != "success":
                return result

            # 更新角色
            updated_char = result["character"]
            for i, char in enumerate(novel.characters):
                if char.name == character_name:
                    novel.characters[i] = updated_char
                    break

            file_manager.save_novel_json(novel)
            file_manager.save_characters_markdown(novel.characters, novel_id)

            return {
                "status": "success",
                "message": f"角色 '{character_name}' 修改成功",
                "novel_id": novel_id
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"修改角色时出错: {str(e)}",
                "error": str(e)
            }

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


def _format_character_info_for_outline(characters) -> str:
    """
    格式化角色信息以便传递给大纲生成

    Args:
        characters: Character对象列表

    Returns:
        str: 格式化后的角色信息
    """
    if not characters:
        return "暂无角色设定"

    info_parts = []
    for char in characters:
        part = f"- {char.name}（{char.role}）: {char.personality[:50] if char.personality else '暂无描述'}..."
        if hasattr(char, 'quirk') and char.quirk:
            part += f" 个人怪癖: {char.quirk}"
        info_parts.append(part)

    return "\n".join(info_parts)
