"""
上下文构建器
实现模式B：完整上下文模式 - 将所有前文内容直接纳入上下文窗口
"""
from typing import List, Optional, Dict, Any
from ..models.outline import Outline, ChapterPlan, DetailedChapterPlan
from ..models.character import Character
from ..models.chapter import Chapter
from ..models.bible import NovelBible, CharacterState


class WritingContext:
    """写作上下文数据类"""

    def __init__(
        self,
        chapter_plan: ChapterPlan,
        detailed_plan: Optional[DetailedChapterPlan],
        outline: Outline,
        characters: List[Character],
        previous_chapters: List[Chapter],
        novel_bible: Optional[NovelBible],
        system_prompt: str = "",
    ):
        self.chapter_plan = chapter_plan
        self.detailed_plan = detailed_plan
        self.outline = outline
        self.characters = characters
        self.previous_chapters = previous_chapters
        self.novel_bible = novel_bible
        self.system_prompt = system_prompt

    def to_prompt_parts(self) -> Dict[str, str]:
        """将上下文转换为prompt的各个部分"""
        parts = {}

        # 1. 章节规划
        parts["chapter_plan"] = self._format_chapter_plan()

        # 2. 前文完整内容（核心！）
        parts["previous_content"] = self._format_previous_content()

        # 3. 角色信息
        parts["characters"] = self._format_characters()

        # 4. 世界/伏笔信息
        parts["world_info"] = self._format_world_info()

        # 5. 一致性约束
        parts["constraints"] = self._format_constraints()

        return parts

    def _format_chapter_plan(self) -> str:
        """格式化章节规划"""
        lines = ["【当前章节规划】"]

        plan = self.chapter_plan
        lines.append(f"第{plan.chapter_number}章: {plan.title}")
        lines.append(f"章节摘要: {plan.summary}")
        lines.append(f"目标字数: {plan.estimated_words}")

        if self.detailed_plan:
            if self.detailed_plan.scenes:
                lines.append("\n场景规划:")
                for i, scene in enumerate(self.detailed_plan.scenes, 1):
                    lines.append(f"  场景{i}: {scene}")

        return "\n".join(lines)

    def _format_previous_content(self) -> str:
        """格式化前文完整内容（模式B核心）"""
        if not self.previous_chapters:
            return "【前文】这是第一章，无前文内容。"

        lines = ["【前文完整内容】"]

        # 按顺序输出每一章的完整内容
        for ch in self.previous_chapters:
            lines.append(f"\n{'='*40}")
            lines.append(f"第{ch.number}章 {ch.title}")
            lines.append(f"{'='*40}")
            lines.append(ch.content)

        return "\n".join(lines)

    def _format_characters(self) -> str:
        """格式化角色信息"""
        lines = ["【角色信息】"]

        for char in self.characters:
            lines.append(f"\n{char.name} ({char.role})")
            lines.append(f"  核心特质与矛盾: {char.core_contradiction}")
            lines.append(f"  背景: {char.background}")
            if char.appearance:
                lines.append(f"  外貌: {char.appearance}")

        return "\n".join(lines)

    def _format_world_info(self) -> str:
        """格式化世界/伏笔信息"""
        lines = ["【世界观与伏笔】"]

        # 来自NovelBible
        if self.novel_bible:
            bible_context = self.novel_bible.to_full_context()
            lines.append(bible_context)

        # 补充：从大纲提取情节点
        if self.outline and self.outline.plot_points:
            lines.append("\n【核心情节点】")
            for point in self.outline.plot_points:
                lines.append(f"- {point.name}: {point.description}")

        return "\n".join(lines)

    def _format_constraints(self) -> str:
        """格式化一致性约束"""
        lines = ["【重要一致性约束】（必须严格遵守）"]

        # 角色状态约束
        if self.novel_bible:
            unavailable = self.novel_bible.characters.get_dead_or_gone_characters()
            if unavailable:
                lines.append("\n⚠️ 已死亡/消失角色（绝对不能出场）:")
                for name in unavailable:
                    state = self.novel_bible.characters.get_state(name)
                    lines.append(f"  - {name}: {state.status if state else '未知'}")

        # 章节过渡约束
        if self.previous_chapters:
            last_ch = self.previous_chapters[-1]
            lines.append(f"\n【章节过渡】必须承接上一章结尾:")
            if last_ch.content:
                tail = last_ch.content[-1500:] if len(last_ch.content) > 1500 else last_ch.content
                lines.append(f"...{tail}")

        # 伏笔约束
        if self.novel_bible:
            unresolved = self.novel_bible.plot_threads.get_unresolved()
            if unresolved:
                lines.append("\n【待回收伏笔】必须考虑以下伏笔:")
                for t in unresolved:
                    lines.append(f"  - {t.name}: {t.description}")

        return "\n".join(lines)


class ContextBuilder:
    """
    上下文构建器
    支持模式B：完整上下文模式
    """

    def __init__(self, novel_bible: Optional[NovelBible] = None):
        self.novel_bible = novel_bible

    def build_context(
        self,
        chapter_plan: ChapterPlan,
        detailed_plan: Optional[DetailedChapterPlan],
        outline: Outline,
        characters: List[Character],
        previous_chapters: List[Chapter],
    ) -> WritingContext:
        """
        构建完整的写作上下文

        Args:
            chapter_plan: 当前章节规划
            detailed_plan: 详细章节规划（可选）
            outline: 小说大纲
            characters: 角色列表
            previous_chapters: 之前所有章节（完整内容）

        Returns:
            WritingContext: 完整的写作上下文
        """
        return WritingContext(
            chapter_plan=chapter_plan,
            detailed_plan=detailed_plan,
            outline=outline,
            characters=characters,
            previous_chapters=previous_chapters,
            novel_bible=self.novel_bible,
        )

    def estimate_token_count(self, context: WritingContext) -> int:
        """
        估算上下文的token数量（粗略估算：中文约1.5字/token，英文约4字符/token）
        """
        parts = context.to_prompt_parts()
        total_chars = sum(len(p) for p in parts.values())
        # 粗略估算：中文环境按 1.5:1
        return total_chars // 1

    def get_context_size_info(self, context: WritingContext) -> Dict[str, Any]:
        """获取上下文大小信息"""
        parts = context.to_prompt_parts()
        info = {}
        for key, value in parts.items():
            chars = len(value)
            info[key] = {
                "chars": chars,
                "chapters": chars // 3000 if key == "previous_content" else 0
            }
        info["total"] = sum(item["chars"] for item in info.values())
        return info
