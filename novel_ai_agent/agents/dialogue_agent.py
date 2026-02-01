"""
对话Agent
负责与用户进行多轮对话，理解修改意图并执行修改
"""
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from .base_agent import BaseAgent
from .writer_agent import WriterAgent
from .editor_agent import EditorAgent
from ..models.novel import Novel
from ..models.chapter import Chapter
from ..memory import get_memory_manager


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

你可以处理的修改类型：
- 情节修改：调整故事走向、增删情节
- 角色修改：调整角色行为、对话
- 文字润色：改进表达、风格调整
- 逻辑优化：修复漏洞、增强合理性
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
        # 简单的关键词匹配（可以改进为更智能的意图识别）
        action_keywords = {
            "修改": "revise",
            "润色": "polish",
            "删除": "delete",
            "添加": "add",
            "重写": "rewrite"
        }

        for keyword, action_type in action_keywords.items():
            if keyword in user_input:
                return {
                    "type": action_type,
                    "target": context.get("current_chapter") if context else None,
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
