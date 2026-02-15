"""
对话Agent
负责与用户进行多轮对话，理解修改意图并执行修改
"""
import re
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from .base_agent import BaseAgent
from .writer_agent import WriterAgent
from .editor_agent import EditorAgent
from .outline_agent import OutlineAgent
from .character_agent import CharacterAgent
from ..models.novel import Novel
from ..models.chapter import Chapter
from ..memory import get_memory_manager
from ..utils.file_manager import file_manager


DIALOGUE_SYSTEM_PROMPT = """你是一位专业的小说编辑助手，负责与作者进行对话，理解他们的修改需求。

你的职责：
1. 理解用户的修改意图和需求
2. 询问必要的细节和澄清
3. 提供建设性的建议
4. 确认修改方案
5. 执行修改操作

对话风格：
- 友好、专业、耐心
- 主动提问，帮助用户明确需求
- 提供具体的修改建议
- 在执行修改前确认方案

【重要：你必须识别以下修改意图并返回对应的action】

修改意图识别规则：
1. 如果用户说"细化第X章"、"扩展第X章"、"详细规划第X章" → action: expand_chapter（章节细化）
2. 如果用户说"修改大纲"、"调整大纲"、"优化大纲" → action: refine_outline（大纲细化）
3. 如果用户说"修改角色"、"调整角色"、"添加角色" → action: refine_character（角色调整）
4. 如果用户说"修改本章"、"重写本章"、"调整本章" → action: revise_chapter（章节修改）
5. 如果用户说"润色本章"、"优化本章" → action: polish_chapter（章节润色）

你可以处理的修改类型：
- 情节修改：调整故事走向、增删情节
- 角色修改：调整角色行为、对话、添加新角色
- 文字润色：改进表达、风格调整
- 逻辑优化：修复漏洞、增强合理性
- 大纲细化：调整情节点、章节规划
- 章节细化：扩展章节规划、增加场景细节
"""


class DialogueAgent(BaseAgent):
    """
    对话Agent

    职责:
    1. 与用户进行多轮对话
    2. 理解修改需求
    3. 协调其他Agent执行修改
    4. 记录对话历史
    """

    def __init__(self, novel_id: str):
        super().__init__(
            name="Dialogue",
            description="负责与用户对话，理解和执行修改需求"
        )
        self.novel_id = novel_id
        self.memory_manager = get_memory_manager(novel_id)
        self.conversation_history: List[Dict] = []

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行对话任务

        Args:
            **kwargs: 任务参数
                - user_input: 用户输入
                - context: 当前上下文

        Returns:
            Dict: 对话响应
        """
        user_input = kwargs.get("user_input", "")
        context = kwargs.get("context", {})

        return await self.chat(user_input, context)

    async def chat(
        self,
        user_input: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        处理一轮对话

        Args:
            user_input: 用户输入
            context: 上下文信息（当前章节、小说等）

        Returns:
            Dict: 包含AI回复和可能的操作
        """
        try:
            # 添加用户消息到历史
            self.conversation_history.append({
                "role": "user",
                "content": user_input
            })

            # 添加到记忆系统
            self.memory_manager.add_conversation_turn("user", user_input)

            # 构建上下文信息
            context_str = self._build_context_string(context)

            # 构建消息列表
            messages = [SystemMessage(content=DIALOGUE_SYSTEM_PROMPT)]

            # 添加上下文
            if context_str:
                messages.append(HumanMessage(content=f"上下文信息：\n{context_str}"))

            # 添加对话历史（最近5轮）
            recent_history = self.conversation_history[-10:]
            for msg in recent_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                else:
                    messages.append(AIMessage(content=msg["content"]))

            # 调用LLM
            response = await self.llm.ainvoke(messages)
            ai_response = response.content

            # 添加AI回复到历史
            self.conversation_history.append({
                "role": "assistant",
                "content": ai_response
            })

            # 添加到记忆系统
            self.memory_manager.add_conversation_turn("assistant", ai_response)

            # 分析是否包含执行指令
            action = await self._analyze_action(user_input, ai_response, context)

            return {
                "status": "success",
                "response": ai_response,
                "action": action,
                "conversation_length": len(self.conversation_history)
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"对话处理出错: {str(e)}",
                "error": str(e)
            }

    async def _analyze_action(
        self,
        user_input: str,
        ai_response: str,
        context: Optional[Dict]
    ) -> Optional[Dict]:
        """
        分析对话中是否包含需要执行的操作

        Args:
            user_input: 用户输入
            ai_response: AI回复
            context: 上下文

        Returns:
            Optional[Dict]: 操作信息，如果没有则返回None
        """
        user_input_lower = user_input.lower()

        # 章节细化：细化第X章、扩展第X章、详细规划第X章
        expand_match = re.search(r'第(\d+)章', user_input)
        if any(kw in user_input for kw in ['细化', '扩展', '详细规划', '展开']):
            if expand_match:
                chapter_num = int(expand_match.group(1))
                return {
                    "type": "expand_chapter",
                    "target": {"chapter_number": chapter_num},
                    "user_request": user_input
                }

        # 大纲细化
        if any(kw in user_input for kw in ['修改大纲', '调整大纲', '优化大纲', '完善大纲', '改大纲']):
            return {
                "type": "refine_outline",
                "target": None,
                "user_request": user_input
            }

        # 角色调整
        if any(kw in user_input for kw in ['修改角色', '调整角色', '添加角色', '完善角色', '改角色']):
            return {
                "type": "refine_character",
                "target": None,
                "user_request": user_input
            }

        # 章节修改
        if expand_match and any(kw in user_input for kw in ['修改', '重写', '调整', '改写']):
            chapter_num = int(expand_match.group(1))
            return {
                "type": "revise_chapter",
                "target": {"chapter_number": chapter_num},
                "user_request": user_input
            }

        # 章节润色
        if expand_match and any(kw in user_input for kw in ['润色', '优化', '美化']):
            chapter_num = int(expand_match.group(1))
            return {
                "type": "polish_chapter",
                "target": {"chapter_number": chapter_num},
                "user_request": user_input
            }

        return None

    def _build_context_string(self, context: Optional[Dict]) -> str:
        """构建上下文字符串"""
        if not context:
            return ""

        lines = []

        if "novel_title" in context:
            lines.append(f"小说：{context['novel_title']}")

        if "current_chapter" in context:
            ch = context["current_chapter"]
            lines.append(f"当前章节：第{ch.get('number', '?')}章 - {ch.get('title', '')}")
            if "summary" in ch:
                lines.append(f"摘要：{ch['summary']}")

        if "recent_chapters" in context:
            lines.append(f"\n最近章节：{len(context['recent_chapters'])}章")

        return "\n".join(lines)

    async def execute_revision(
        self,
        chapter: Chapter,
        revision_request: str,
        novel: Novel
    ) -> Dict[str, Any]:
        """
        执行章节修改

        Args:
            chapter: 要修改的章节
            revision_request: 修改请求
            novel: 小说对象

        Returns:
            Dict: 修改结果
        """
        writer = WriterAgent(style_name=novel.author_style)

        result = await writer.revise_chapter(
            chapter=chapter,
            revision_requirements=revision_request,
            context=""
        )

        return result

    async def execute_polish(
        self,
        chapter: Chapter,
        focus_areas: Optional[List[str]],
        style: str
    ) -> Dict[str, Any]:
        """
        执行章节润色

        Args:
            chapter: 要润色的章节
            focus_areas: 关注点
            style: 风格

        Returns:
            Dict: 润色结果
        """
        editor = EditorAgent()

        result = await editor.polish_chapter(
            chapter=chapter,
            style=style,
            focus_areas=focus_areas
        )

        return result

    def get_conversation_summary(self) -> str:
        """获取对话摘要"""
        if not self.conversation_history:
            return "暂无对话历史"

        summary_lines = []
        for i, msg in enumerate(self.conversation_history[-5:], 1):
            role = "用户" if msg["role"] == "user" else "助手"
            content = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
            summary_lines.append(f"{i}. {role}: {content}")

        return "\n".join(summary_lines)

    def clear_history(self):
        """清空对话历史"""
        self.conversation_history.clear()

    def get_history(self) -> List[Dict]:
        """获取完整对话历史"""
        return self.conversation_history.copy()

    async def execute_action(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行识别出的动作

        Args:
            action: 动作信息
            context: 执行上下文

        Returns:
            Dict: 执行结果
        """
        action_type = action.get("type")
        novel_id = context.get("novel_id")

        if not novel_id:
            return {"status": "error", "message": "缺少小说ID"}

        # 加载小说
        novel = file_manager.load_novel_json(novel_id)
        if not novel:
            return {"status": "error", "message": f"未找到小说 {novel_id}"}

        if action_type == "expand_chapter":
            # 章节细化
            chapter_num = action.get("target", {}).get("chapter_number")
            if not chapter_num:
                return {"status": "error", "message": "未指定章节号"}

            # 找到对应的章节规划
            chapter_plan = None
            for plan in novel.outline.chapters_plan:
                if plan.chapter_number == chapter_num:
                    chapter_plan = plan
                    break

            if not chapter_plan:
                return {"status": "error", "message": f"未找到第{chapter_num}章的规划"}

            # 调用OutlineAgent进行章节细化
            outline_agent = OutlineAgent()
            result = await outline_agent.expand_chapter_plan(
                outline=novel.outline,
                chapter_number=chapter_num,
                story_context={"context": action.get("user_request", "")}
            )

            if result.get("status") == "success":
                # 保存细化后的规划
                chapter_plan.detailed_plan = result.get("detailed_plan")
                file_manager.save_novel_json(novel)

            return result

        elif action_type == "refine_outline":
            # 大纲细化
            outline_agent = OutlineAgent()
            result = await outline_agent.refine_outline(
                current_outline=novel.outline,
                user_feedback=action.get("user_request", "")
            )

            if result.get("status") == "success":
                # 保存细化后的大纲
                novel.outline = result.get("outline")
                file_manager.save_novel_json(novel)

            return result

        elif action_type == "refine_character":
            # 角色调整 - 重新生成角色
            character_agent = CharacterAgent()
            result = await character_agent.generate_characters(
                outline=novel.outline,
                user_requirements=action.get("user_request", ""),
                chapter_count=len(novel.outline.chapters_plan) if novel.outline else 20,
                title=novel.title,
                genre=novel.genre,
                theme=novel.outline.theme if novel.outline else ""
            )

            if result.get("status") == "success":
                # 保存更新后的角色
                if result.get("characters"):
                    novel.characters = result.get("characters")
                file_manager.save_novel_json(novel)

            return result

        elif action_type == "revise_chapter":
            # 章节修改
            chapter_num = action.get("target", {}).get("chapter_number")
            if not chapter_num:
                return {"status": "error", "message": "未指定章节号"}

            # 找到对应的章节
            chapter = None
            for ch in novel.chapters or []:
                if ch.number == chapter_num:
                    chapter = ch
                    break

            if not chapter:
                return {"status": "error", "message": f"未找到第{chapter_num}章的内容"}

            writer = WriterAgent(style_name=novel.author_style)
            result = await writer.revise_chapter(
                chapter=chapter,
                revision_requirements=action.get("user_request", ""),
                context=""
            )

            if result.get("status") == "success":
                # 更新章节
                novel.chapters = [result.get("chapter") if c.number == chapter_num else c
                                 for c in (novel.chapters or [])]
                file_manager.save_novel_json(novel)

            return result

        elif action_type == "polish_chapter":
            # 章节润色
            chapter_num = action.get("target", {}).get("chapter_number")
            if not chapter_num:
                return {"status": "error", "message": "未指定章节号"}

            # 找到对应的章节
            chapter = None
            for ch in novel.chapters or []:
                if ch.number == chapter_num:
                    chapter = ch
                    break

            if not chapter:
                return {"status": "error", "message": f"未找到第{chapter_num}章的内容"}

            editor = EditorAgent()
            result = await editor.polish_chapter(
                chapter=chapter,
                style=novel.author_style,
                focus_areas=None
            )

            if result.get("status") == "success":
                # 更新章节
                novel.chapters = [result.get("chapter") if c.number == chapter_num else c
                                 for c in (novel.chapters or [])]
                file_manager.save_novel_json(novel)

            return result

        return {"status": "error", "message": f"未知动作类型: {action_type}"}
