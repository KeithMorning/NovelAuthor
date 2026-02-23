"""
对话Agent
负责与用户进行多轮对话，理解修改意图并执行修改
"""
import re
import json
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
from ..prompts.dialogue_prompts import get_dialogue_system_prompt


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

            # 使用新的prompt模板
            system_prompt = get_dialogue_system_prompt(context_str)

            # 构建消息列表
            messages = [SystemMessage(content=system_prompt)]

            # 添加对话历史（最近10轮）
            recent_history = self.conversation_history[-10:]
            for msg in recent_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                else:
                    messages.append(AIMessage(content=msg["content"]))

            # 使用JSON模式调用LLM
            json_llm = self._get_json_llm()
            response_content = await self._stream_invoke(json_llm, messages)

            # 解析JSON响应
            try:
                parsed = json.loads(response_content)
                ai_response = parsed.get("response", response_content)
                action = parsed.get("action")
            except json.JSONDecodeError:
                # JSON解析失败，回退到原始响应
                ai_response = response_content
                action = None

            # 添加AI回复到历史
            self.conversation_history.append({
                "role": "assistant",
                "content": ai_response
            })

            # 添加到记忆系统
            self.memory_manager.add_conversation_turn("assistant", ai_response)

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


    def _build_context_string(self, context: Optional[Dict]) -> str:
        """构建上下文字符串"""
        if not context:
            return ""

        lines = []

        if "novel_title" in context:
            lines.append(f"小说：{context['novel_title']}")

        # 添加大纲信息
        novel = context.get("novel")
        if novel:
            if novel.outline:
                lines.append(f"类型：{novel.genre}")
                lines.append(f"主题：{novel.outline.theme}")
                lines.append(f"摘要：{novel.outline.summary}")
                if novel.outline.chapters_plan:
                    lines.append(f"章节数：{len(novel.outline.chapters_plan)}")

            # 添加完整角色信息
            if novel.characters:
                lines.append(f"\n当前角色列表（共{len(novel.characters)}个）：")
                for char in novel.characters:
                    lines.append(f"\n【{char.name}】（{char.role}）")
                    lines.append(f"  性格：{char.personality}")
                    if char.background:
                        lines.append(f"  背景：{char.background}")
                    if char.motivation:
                        lines.append(f"  动机：{char.motivation}")
                    if char.arc:
                        lines.append(f"  发展弧线：{char.arc}")
                    if char.quirk:
                        lines.append(f"  个人特点：{char.quirk}")
                    if char.relationships:
                        rel_str = "、".join(f"{k}:{v}" for k, v in char.relationships.items())
                        lines.append(f"  关系：{rel_str}")

        if "current_chapter" in context:
            ch = context["current_chapter"]
            lines.append(f"\n当前章节：第{ch.get('number', '?')}章 - {ch.get('title', '')}")
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

    def fast_route(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        基于规则的快速意图路由，零 LLM 调用。

        命中常见指令模式时直接返回 action dict；
        无法识别时返回 None，由调用方降级到 LLM 解析。

        支持的模式:
          - 细化/展开/扩展 第N章
          - 润色 第N章
          - 修改/重写/改写 第N章 [具体要求]
          - 修改/调整/改/更新 大纲 [具体要求]
          - 修改/改 角色 [角色名] [具体要求]
        """
        text = user_input.strip()

        # ── 细化章节 ──────────────────────────────────────────
        m = re.search(r'(?:细化|展开|扩展|详细规划)[第\s]*(\d+)[章节]', text)
        if m:
            return {
                "tool": "expand_chapter",
                "params": {"chapter_number": int(m.group(1))},
                "reason": f"用户要求细化第{m.group(1)}章"
            }

        # ── 润色章节 ──────────────────────────────────────────
        m = re.search(r'润色[第\s]*(\d+)[章节]', text)
        if m:
            return {
                "tool": "polish_chapter",
                "params": {"chapter_number": int(m.group(1))},
                "reason": f"用户要求润色第{m.group(1)}章"
            }

        # ── 修改/重写章节（可带要求）──────────────────────────
        m = re.search(r'(?:修改|重写|改写|重新写)[第\s]*(\d+)[章节][，,。\s]*(.+)?', text)
        if m:
            ch_num = int(m.group(1))
            req = (m.group(2) or text).strip()
            return {
                "tool": "revise_chapter",
                "params": {"chapter_number": ch_num, "requirements": req},
                "reason": f"用户要求修改第{ch_num}章"
            }

        # ── 修改大纲 ──────────────────────────────────────────
        if re.search(r'(?:修改|调整|改|更新|优化)(?:一下|下)?大纲', text):
            return {
                "tool": "modify_outline",
                "params": {"feedback": text},
                "reason": "用户要求修改大纲"
            }

        # ── 修改角色（尝试提取角色名）────────────────────────
        m = re.search(r'(?:修改|调整|改)[一下]?角色[：:\s]*([^\s，,的]+)', text)
        if m:
            char_name = m.group(1)
            return {
                "tool": "modify_character",
                "params": {"character_name": char_name, "modifications": text},
                "reason": f"用户要求修改角色 {char_name}"
            }
        # 不含具体名字的角色修改
        if re.search(r'(?:修改|调整|改)[一下]?(?:角色|人物)', text):
            return {
                "tool": "modify_character",
                "params": {"modifications": text},
                "reason": "用户要求修改角色"
            }

        # ── 未命中任何规则 ────────────────────────────────────
        return None

    async def execute_action(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行识别出的动作

        Args:
            action: 动作信息，格式：{
                "tool": "工具名",
                "params": {...},
                "reason": "调用原因"
            }
            context: 执行上下文

        Returns:
            Dict: 执行结果
        """
        tool_name = action.get("tool")
        params = action.get("params", {})
        reason = action.get("reason", "")
        novel_id = context.get("novel_id")

        if not novel_id:
            return {"status": "error", "message": "缺少小说ID"}

        # 加载小说
        novel = file_manager.load_novel_json(novel_id)
        if not novel:
            return {"status": "error", "message": f"未找到小说 {novel_id}"}

        if tool_name == "expand_chapter":
            # 章节细化
            chapter_num = params.get("chapter_number")
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
                story_context={"context": reason}
            )

            if result.get("status") == "success":
                # 保存细化后的规划
                chapter_plan.detailed_plan = result.get("detailed_plan")
                file_manager.save_novel_json(novel)

            return result

        elif tool_name == "modify_outline":
            # 大纲细化
            outline_agent = OutlineAgent()

            # 获取用户反馈：优先用 params.feedback，其次用 reason
            user_feedback = params.get("feedback") or reason or "优化大纲"

            # 添加角色信息到上下文中（完整信息）
            character_context = ""
            if novel.characters:
                char_lines = []
                for c in novel.characters:
                    rel_str = ", ".join(f"{k}:{v}" for k, v in c.relationships.items()) if c.relationships else "无"
                    arc_str = f", 发展弧线={c.arc}" if c.arc else ""
                    skills_str = f", 技能={c.skills}" if c.skills else ""
                    quirk_str = f", 个人特点={c.quirk}" if c.quirk else ""
                    appearance_str = f", 外貌={c.appearance}" if c.appearance else ""

                    char_lines.append(
                        f"- {c.name}（{c.role}）\n"
                        f"  性格: {c.personality}\n"
                        f"  背景: {c.background}\n"
                        f"  动机: {c.motivation}"
                        f"{appearance_str}{skills_str}{arc_str}{quirk_str}\n"
                        f"  关系: {rel_str}"
                    )
                character_context = "\n当前角色列表：\n" + "\n".join(char_lines)

            # 将角色信息附加到反馈中
            full_feedback = f"{user_feedback}\n\n{character_context}"

            result = await outline_agent.refine_outline(
                current_outline=novel.outline,
                user_feedback=full_feedback
            )

            if result.get("status") == "success":
                # 保存细化后的大纲
                novel.outline = result.get("outline")
                file_manager.save_novel_json(novel)
                file_manager.save_outline_markdown(novel.outline, novel_id)
                result["message"] = "大纲已修改"

            return result

        elif tool_name == "modify_character":
            # 角色调整 - 找到具体角色，调用refine_character修改
            character_agent = CharacterAgent()
            target_name = params.get("character_name")
            modifications = params.get("modifications", reason)

            # 找到目标角色
            target_char = None
            if target_name and novel.characters:
                for c in novel.characters:
                    if c.name == target_name:
                        target_char = c
                        break

            if target_char:
                # 修改单个角色
                story_context = f"小说：{novel.title}，类型：{novel.genre}"
                if novel.outline:
                    story_context += f"，主题：{novel.outline.theme}"

                result = await character_agent.refine_character(
                    character=target_char,
                    refinement_requirements=modifications,
                    story_context=story_context
                )

                if result.get("status") == "success" and result.get("character"):
                    # 替换对应角色
                    refined_char = result["character"]
                    novel.characters = [
                        refined_char if c.name == target_name else c
                        for c in novel.characters
                    ]
                    file_manager.save_novel_json(novel)
                    file_manager.save_characters_markdown(novel.characters, novel_id)
                    result["message"] = f"角色 {target_name} 已修改并保存"
            else:
                # 没有找到具体角色，把用户需求和当前角色信息一起传给角色Agent重新生成
                current_chars_desc = ""
                if novel.characters:
                    char_lines = []
                    for c in novel.characters:
                        char_lines.append(f"- {c.name}（{c.role}）: 性格={c.personality}, 背景={c.background}")
                    current_chars_desc = "\n".join(char_lines)

                combined_requirements = (
                    f"用户修改要求：{modifications}\n\n"
                    f"当前角色列表（请在此基础上修改，保持未涉及角色不变）：\n{current_chars_desc}"
                )

                result = await character_agent.generate_characters(
                    outline=novel.outline,
                    character_requirements=combined_requirements,
                    chapter_count=len(novel.outline.chapters_plan) if novel.outline else 20,
                    title=novel.title,
                    genre=novel.genre,
                    theme=novel.outline.theme if novel.outline else ""
                )

                if result.get("status") == "success" and result.get("characters"):
                    novel.characters = result["characters"]
                    file_manager.save_novel_json(novel)
                    file_manager.save_characters_markdown(novel.characters, novel_id)

            return result

        elif tool_name == "redesign_characters":
            # 重新设计整个角色列表
            character_agent = CharacterAgent()
            requirements = params.get("requirements", reason)

            # 构建当前角色信息供AI参考
            current_chars_desc = ""
            if novel.characters:
                char_lines = []
                for c in novel.characters:
                    char_lines.append(f"- {c.name}（{c.role}）: 性格={c.personality}, 背景={c.background}, 关系={c.relationships}")
                current_chars_desc = "\n".join(char_lines)

            combined_requirements = (
                f"用户修改要求：{requirements}\n\n"
                f"请在以下角色基础上进行调整，保持合理的角色结构：\n{current_chars_desc}"
            )

            result = await character_agent.generate_characters(
                outline=novel.outline,
                character_requirements=combined_requirements,
                chapter_count=len(novel.outline.chapters_plan) if novel.outline else 20,
                title=novel.title,
                genre=novel.genre,
                theme=novel.outline.theme if novel.outline else ""
            )

            if result.get("status") == "success" and result.get("characters"):
                novel.characters = result["characters"]
                file_manager.save_novel_json(novel)
                file_manager.save_characters_markdown(novel.characters, novel_id)
                result["message"] = f"角色列表已重新设计，共 {len(novel.characters)} 个角色"
            else:
                result["message"] = "角色列表重新设计失败"

            return result

        elif tool_name == "revise_chapter":
            # 章节修改
            chapter_num = params.get("chapter_number")
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
                revision_requirements=params.get("requirements", reason),
                context=""
            )

            if result.get("status") == "success":
                revised_ch = result.get("chapter")
                novel.chapters = [
                    revised_ch if c.number == chapter_num else c
                    for c in (novel.chapters or [])
                ]
                file_manager.save_novel_json(novel)
                file_manager.save_chapter_markdown(revised_ch, novel_id)
                result["message"] = (
                    f"第{chapter_num}章已修改并保存"
                    f"（v{revised_ch.version}，{revised_ch.word_count}字）"
                )

            return result

        elif tool_name == "polish_chapter":
            # 章节润色
            chapter_num = params.get("chapter_number")
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
                polished_ch = result.get("chapter")
                novel.chapters = [
                    polished_ch if c.number == chapter_num else c
                    for c in (novel.chapters or [])
                ]
                file_manager.save_novel_json(novel)
                file_manager.save_chapter_markdown(polished_ch, novel_id)
                result["message"] = (
                    f"第{chapter_num}章已润色并保存"
                    f"（v{polished_ch.version}，{polished_ch.word_count}字）"
                )

            return result

        return {"status": "error", "message": f"未知工具: {tool_name}"}
