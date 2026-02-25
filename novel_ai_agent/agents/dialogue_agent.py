"""
对话Agent
负责与用户进行多轮对话，理解修改意图并执行修改
"""
import re
import json
from typing import Dict, Any, List, Optional, Callable
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from .base_agent import BaseAgent
from .writer_agent import WriterAgent
from .editor_agent import EditorAgent
from .outline_agent import OutlineAgent
from .character_agent import CharacterAgent
from ..models.novel import Novel
from ..models.chapter import Chapter
from ..memory import get_memory_manager, new_session_memory_manager
from ..utils.file_manager import file_manager
from ..prompts.dialogue_prompts import get_dialogue_system_prompt, get_planning_prompt


# 触发计划模式的关键词（用户输入中只要包含其中一个就自动进入计划模式）
_PLANNING_KEYWORDS = {
    "先计划", "先想想", "先分析", "先规划", "计划一下", "先梳理",
    "模拟情节", "模拟一下", "推演", "先看看怎么", "先评估",
    "设计一下", "先评估一下", "先了解一下", "分析一下"
}


def is_planning_request(text: str) -> bool:
    """検查用户输入是否是计划模式请求"""
    return any(kw in text for kw in _PLANNING_KEYWORDS)


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
        # 每次 DialogueAgent 初始化 = 新的 chat 会话，清除旧对话历史
        self.memory_manager = new_session_memory_manager(novel_id)
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
                actions = parsed.get("actions", [])
                
                # 向后兼容：如果大模型还是返回了单数形式的 action
                if "action" in parsed and parsed["action"] is not None and not actions:
                    actions = [parsed["action"]]

            except json.JSONDecodeError:
                # JSON解析失败，回退到原始响应
                ai_response = response_content
                actions = []

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
                "actions": actions,
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
                    lines.append(f"  核心特质与矛盾：{char.core_contradiction}")
                    if char.deep_desire:
                        lines.append(f"  深层渴望：{char.deep_desire}")
                    if char.life_filter:
                        lines.append(f"  人生滤镜：{char.life_filter}")
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

    async def make_plan(
        self,
        user_input: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        计划模式：分析现有剧情，制定详细修改方案，不执行任何操作。

        Args:
            user_input: 用户的修改需求
            context: 上下文（包含 novel 对象）

        Returns:
            Dict: {
                "status": "success",
                "plan_text": 分析和计划的纯文本,
                "proposed_actions": 建议执行的 action 列表（供用户确认后使用）,
                "chapter_num": 目标章节号（如果检测到）
            }
        """
        try:
            novel = context.get("novel") if context else None
            novel_id = context.get("novel_id") if context else self.novel_id

            # ── 1. 从用户输入中提取目标章节号 ──────────────────
            ch_match = re.search(r'第\s*(\d+)\s*[章节]', user_input)
            chapter_num = int(ch_match.group(1)) if ch_match else None

            # ── 2. 加载章节内容 ──────────────────────────────────
            chapter_obj = None
            if novel and chapter_num:
                for ch in (novel.chapters or []):
                    if ch.number == chapter_num:
                        chapter_obj = ch
                        break

            if not chapter_obj and chapter_num:
                # 也尝试从 context 里获取当前章节
                if context and "current_chapter" in context:
                    cc = context["current_chapter"]
                    if cc.get("number") == chapter_num:
                        chapter_num = cc["number"]

            # 没有找到章节内容时给出提示
            if chapter_obj:
                chapter_content = chapter_obj.content or ""
                chapter_title = chapter_obj.title or f"第{chapter_num}章"
            else:
                # 用大纲摘要代替
                chapter_title = f"第{chapter_num}章" if chapter_num else "（未指定章节）"
                chapter_content = ""
                if novel and novel.outline and novel.outline.chapters_plan:
                    for cp in novel.outline.chapters_plan:
                        if cp.chapter_number == chapter_num:
                            chapter_content = f"[大纲描述]\n{cp.summary or ''}"
                            chapter_title = cp.title or chapter_title
                            break

            # ── 3. 构建小说背景信息 ──────────────────────────────
            novel_ctx_lines = []
            if novel:
                novel_ctx_lines.append(f"小说：{novel.title}（{novel.genre}）")
                if novel.outline:
                    novel_ctx_lines.append(f"主题：{novel.outline.theme}")
                    novel_ctx_lines.append(f"摘要：{novel.outline.summary[:300]}")
                if novel.characters:
                    novel_ctx_lines.append("\n主要角色：")
                    for c in novel.characters[:5]:
                        novel_ctx_lines.append(f"  - {c.name}（{c.role}）：{c.core_contradiction[:60]}")
            novel_context_str = "\n".join(novel_ctx_lines)

            # ── 4. 调用 LLM 生成计划（纯文本）──────────────────
            planning_prompt = get_planning_prompt(
                user_request=user_input,
                chapter_num=chapter_num or 0,
                chapter_title=chapter_title,
                chapter_content=chapter_content,
                novel_context=novel_context_str
            )
            messages = [HumanMessage(content=planning_prompt)]
            plan_text = await self._stream_invoke(self.llm, messages)

            # ── 5. 同步推断 proposed_actions（供确认后执行）──────
            # 优先用 fast_route 从 user_input 提取 action
            proposed_actions = self.fast_route(user_input)
            if not proposed_actions and chapter_num:
                # fallback: 通用修改章节 action
                proposed_actions = [{
                    "tool": "revise_chapter",
                    "params": {"chapter_number": chapter_num, "requirements": user_input},
                    "reason": f"根据计划修改第{chapter_num}章"
                }]

            return {
                "status": "success",
                "plan_text": plan_text,
                "proposed_actions": proposed_actions or [],
                "chapter_num": chapter_num
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"计划生成出错: {str(e)}",
                "error": str(e)
            }

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
        self.memory_manager.short_term_memory["conversation_history"] = []

    def get_history(self) -> List[Dict]:
        """获取完整对话历史"""
        return self.conversation_history.copy()

    def save_session(self) -> Optional[str]:
        """
        将当前对话历史保存到磁盘（用于 /resume）。
        Returns: 保存的文件路径，失败返回 None
        """
        try:
            import os, json
            from datetime import datetime
            sessions_dir = os.path.join(
                file_manager.settings.output_dir, self.novel_id, "sessions"
            )
            os.makedirs(sessions_dir, exist_ok=True)
            path = os.path.join(sessions_dir, "last_session.json")
            data = {
                "novel_id": self.novel_id,
                "saved_at": datetime.now().isoformat(),
                "conversation_history": self.conversation_history
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return path
        except Exception as e:
            return None

    def load_session(self) -> int:
        """
        从磁盘加载上一次的对话历史（用于 /resume）。
        Returns: 恢复的对话轮次数，0 表示没有历史或失败
        """
        try:
            import os, json
            path = os.path.join(
                file_manager.settings.output_dir, self.novel_id, "sessions", "last_session.json"
            )
            if not os.path.exists(path):
                return 0
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.conversation_history = data.get("conversation_history", [])
            # 同步到 memory_manager
            self.memory_manager.short_term_memory["conversation_history"] = self.conversation_history.copy()
            return len(self.conversation_history)
        except Exception:
            return 0

    def fast_route(self, user_input: str) -> Optional[List[Dict[str, Any]]]:
        """
        基于规则的快速意图路由，零 LLM 调用。

        命中常见指令模式时直接返回 actions 数组；
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
            return [{
                "tool": "expand_chapter",
                "params": {"chapter_number": int(m.group(1))},
                "reason": f"用户要求细化第{m.group(1)}章"
            }]

        # ── 润色章节 ──────────────────────────────────────────
        m = re.search(r'润色[第\s]*(\d+)[章节]', text)
        if m:
            return [{
                "tool": "polish_chapter",
                "params": {"chapter_number": int(m.group(1))},
                "reason": f"用户要求润色第{m.group(1)}章"
            }]

        # ── 局部编辑章节（Edit Instruction 快速模式）──────────
        m = re.search(r'(?:局部修改|微调|补充|插入|增加|删除)[第\s]*(\d+)[章节][，,。\s]*(.+)?', text)
        if m:
            ch_num = int(m.group(1))
            req = (m.group(2) or text).strip()
            return [{
                "tool": "edit_chapter",
                "params": {"chapter_number": ch_num, "requirements": req},
                "reason": f"用户要求局部编辑第{ch_num}章"
            }]

        # ── 修改/重写章节（可带要求）──────────────────────────
        m = re.search(r'(?:修改|重写|改写|重新写)[第\s]*(\d+)[章节][，,。\s]*(.+)?', text)
        if m:
            ch_num = int(m.group(1))
            req = (m.group(2) or text).strip()
            return [{
                "tool": "revise_chapter",
                "params": {"chapter_number": ch_num, "requirements": req},
                "reason": f"用户要求修改第{ch_num}章"
            }]

        # ── 创作新章节 ────────────────────────────────────────
        m = re.search(r'(?:开始写|写|创作)[第\s]*(\d+)[章节]', text)
        if m:
            ch_num = int(m.group(1))
            return [{
                "tool": "write_chapter",
                "params": {"chapter_number": ch_num},
                "reason": f"用户要求创作第{ch_num}章"
            }]

        # ── 修改大纲 ──────────────────────────────────────────
        if re.search(r'(?:修改|调整|改|更新|优化)(?:一下|下)?大纲', text):
            return [{
                "tool": "modify_outline",
                "params": {"feedback": text},
                "reason": "用户要求修改大纲"
            }]

        # ── 修改角色（尝试提取角色名）────────────────────────
        m = re.search(r'(?:修改|调整|改)[一下]?角色[：:\s]*([^\s，,的]+)', text)
        if m:
            char_name = m.group(1)
            return [{
                "tool": "modify_character",
                "params": {"character_name": char_name, "modifications": text},
                "reason": f"用户要求修改角色 {char_name}"
            }]
        # 不含具体名字的角色修改
        if re.search(r'(?:修改|调整|改)[一下]?(?:角色|人物)', text):
            return [{
                "tool": "modify_character",
                "params": {"modifications": text},
                "reason": "用户要求修改角色"
            }]

        # ── 本地精确替换 ──────────────────────────────────────────
        m = re.search(r'(?:把|将)[第\s]*(\d+)[章节]的[\"\'“‘](.*?)[\"\'”’]替换为[\"\'“‘](.*?)[\"\'”’]', text)
        if m:
            ch_num = int(m.group(1))
            search_t = m.group(2)
            replace_t = m.group(3)
            return [{
                "tool": "local_replace_text",
                "params": {"chapter_number": ch_num, "search_text": search_t, "replace_text": replace_t},
                "reason": f"快速指令触发：将第{ch_num}章的 '{search_t}' 替换为 '{replace_t}'"
            }]

        # ── 同步章节 ──────────────────────────────────────────
        m = re.search(r'(?:同步|更新|读取)[第\s]*(\d+)[章节]', text)
        if m:
            ch_num = int(m.group(1))
            return [{
                "tool": "sync_chapter",
                "params": {"chapter_number": ch_num},
                "reason": f"用户要求同步第{ch_num}章的手动修改"
            }]

        # ── 未命中任何规则 ────────────────────────────────────
        return None

    async def execute_action(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any],
        on_token: Optional[Callable[[str], None]] = None
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

        if tool_name == "write_chapter":
            # 创作全新章节
            chapter_num = params.get("chapter_number")
            if not chapter_num:
                return {"status": "error", "message": "未指定章节号"}
                
            from .coordinator import CoordinatorAgent
            coordinator = CoordinatorAgent()
            
            # 使用 CoordinatorAgent 的工作流来创作单章
            result = await coordinator.write_chapter_workflow(
                novel_id=novel_id,
                chapter_number=chapter_num,
                enable_expansion=True,
                force=True,
                on_token=on_token
            )
            
            if result.get("status") == "success":
                result["message"] = f"第{chapter_num}章创作完成"
                
            return result

        elif tool_name == "expand_chapter":
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
                        f"  核心特质与矛盾: {c.core_contradiction}\n"
                        f"  深层渴望: {c.deep_desire}\n"
                        f"  人生滤镜(背景): {c.life_filter}"
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
                        char_lines.append(f"- {c.name}（{c.role}）: 核心矛盾={c.core_contradiction}, 人生滤镜={c.life_filter}")
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
                    char_lines.append(f"- {c.name}（{c.role}）: 核心矛盾={c.core_contradiction}, 人生滤镜={c.life_filter}, 关系={c.relationships}")
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

        elif tool_name == "edit_chapter":
            # 局部编辑章节（Edit Instruction 快速模式）
            chapter_num = params.get("chapter_number")
            if not chapter_num:
                return {"status": "error", "message": "未指定章节号"}

            chapter = None
            for ch in novel.chapters or []:
                if ch.number == chapter_num:
                    chapter = ch
                    break

            if not chapter:
                return {"status": "error", "message": f"未找到第{chapter_num}章的内容"}

            writer = WriterAgent(style_name=novel.author_style)
            result = await writer.edit_chapter(
                chapter=chapter,
                revision_requirements=params.get("requirements", reason),
                on_token=on_token
            )

            if result.get("status") == "success":
                edited_ch = result.get("chapter")
                novel.chapters = [
                    edited_ch if c.number == chapter_num else c
                    for c in (novel.chapters or [])
                ]
                file_manager.save_novel_json(novel)
                file_manager.save_chapter_markdown(edited_ch, novel_id)
                file_manager.save_novel_markdown(novel)
                mode = "局部编辑" if result.get("mode") == "edit_instruction" else "全文重写"
                result["message"] = (
                    f"第{chapter_num}章已{mode}并保存"
                    f"（v{edited_ch.version}，{edited_ch.word_count}字）"
                )

            return result

        elif tool_name == "local_replace_text":
            # 纯本地文本精确替换（不调用大模型）
            chapter_num = params.get("chapter_number")
            search_text = params.get("search_text")
            replace_text = params.get("replace_text")

            if not chapter_num or not search_text or replace_text is None:
                return {"status": "error", "message": "缺少必要的替换参数 (chapter_number, search_text, replace_text)"}

            # 找到对应章节
            chapter = None
            for ch in novel.chapters or []:
                if ch.number == chapter_num:
                    chapter = ch
                    break

            if not chapter:
                return {"status": "error", "message": f"未找到第{chapter_num}章的内容"}
                
            if search_text not in chapter.content:
                return {"status": "error", "message": f"在第{chapter_num}章中未找到要替换的内容：'{search_text}'"}

            # 执行替换计数
            count = chapter.content.count(search_text)
            
            # 字符串替换
            chapter.content = chapter.content.replace(search_text, replace_text)
            
            # 保存回文件
            novel.chapters = [
                chapter if c.number == chapter_num else c
                for c in (novel.chapters or [])
            ]
            file_manager.save_novel_json(novel)
            file_manager.save_chapter_markdown(chapter, novel_id)
            file_manager.save_novel_markdown(novel)
            
            return {
                "status": "success",
                "message": f"成功在第{chapter_num}章将 '{search_text}' 替换为 '{replace_text}'，共替换了 {count} 处。"
            }

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
                context="",
                on_token=on_token
            )

            if result.get("status") == "success":
                revised_ch = result.get("chapter")
                novel.chapters = [
                    revised_ch if c.number == chapter_num else c
                    for c in (novel.chapters or [])
                ]
                file_manager.save_novel_json(novel)
                file_manager.save_chapter_markdown(revised_ch, novel_id)
                file_manager.save_novel_markdown(novel)
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
                focus_areas=None,
                on_token=on_token
            )

            if result.get("status") == "success":
                polished_ch = result.get("chapter")
                novel.chapters = [
                    polished_ch if c.number == chapter_num else c
                    for c in (novel.chapters or [])
                ]
                file_manager.save_novel_json(novel)
                file_manager.save_chapter_markdown(polished_ch, novel_id)
                file_manager.save_novel_markdown(novel)
                result["message"] = (
                    f"第{chapter_num}章已润色并保存"
                    f"（v{polished_ch.version}，{polished_ch.word_count}字）"
                )

            return result

        elif tool_name == "sync_chapter":
            chapter_num = params.get("chapter_number")
            if not chapter_num:
                return {"status": "error", "message": "未指定需要同步的章节号"}
                
            success = file_manager.sync_chapter_markdown_to_json(novel_id, chapter_num)
            if success:
                return {
                    "status": "success",
                    "message": f"成功将第 {chapter_num} 章的 Markdown 修改同步到了系统中！"
                }
            else:
                return {
                    "status": "error",
                    "message": f"同步第 {chapter_num} 章失败，请检查文件是否存在或格式是否正确。"
                }

        return {"status": "error", "message": f"未知工具: {tool_name}"}
