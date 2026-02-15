"""
一致性验证器
用于验证章节内容与全局设定的一致性
"""
from typing import List, Dict, Any, Optional
from ..models.chapter import Chapter
from ..models.bible import NovelBible


class ConsistencyIssue:
    """一致性问题的数据类"""

    def __init__(self, issue_type: str, severity: str, description: str, suggestion: str = ""):
        self.issue_type = issue_type  # character_dead, timeline, plot_thread, etc.
        self.severity = severity  # critical, warning, info
        self.description = description
        self.suggestion = suggestion

    def to_dict(self) -> Dict[str, str]:
        return {
            "type": self.issue_type,
            "severity": self.severity,
            "description": self.description,
            "suggestion": self.suggestion
        }


class ConsistencyValidator:
    """
    一致性验证器
    检查章节内容是否与全局设定冲突
    """

    def __init__(self, novel_bible: Optional[NovelBible] = None):
        self.novel_bible = novel_bible

    def validate_chapter(
        self,
        chapter: Chapter,
        previous_chapters: List[Chapter]
    ) -> Dict[str, Any]:
        """
        验证章节一致性

        Args:
            chapter: 要验证的章节
            previous_chapters: 前文章节

        Returns:
            验证报告
        """
        issues = []

        # 1. 检查角色状态一致性
        if self.novel_bible:
            issues.extend(self._check_character_states(chapter))

        # 2. 检查章节过渡
        if previous_chapters:
            issues.extend(self._check_transition(chapter, previous_chapters[-1]))

        # 3. 检查伏笔
        issues.extend(self._check_plot_threads(chapter, previous_chapters))

        return {
            "passed": len([i for i in issues if i.severity == "critical"]) == 0,
            "issue_count": len(issues),
            "issues": [i.to_dict() for i in issues]
        }

    def _check_character_states(self, chapter: Chapter) -> List[ConsistencyIssue]:
        """检查角色状态一致性"""
        issues = []

        if not self.novel_bible:
            return issues

        dead_chars = self.novel_bible.characters.get_dead_or_gone_characters()

        # 检查章节内容是否提到了已死亡角色
        for char_name in dead_chars:
            if char_name in chapter.content:
                state = self.novel_bible.characters.get_state(char_name)
                issues.append(ConsistencyIssue(
                    issue_type="character_dead",
                    severity="critical",
                    description=f"章节中出现了已死亡/消失的角色 '{char_name}'",
                    suggestion=f"移除所有关于 {char_name} 的提及，或将戏份转移给其他角色"
                ))

        return issues

    def _check_transition(
        self,
        chapter: Chapter,
        previous_chapter: Chapter
    ) -> List[ConsistencyIssue]:
        """检查章节过渡"""
        issues = []

        # 简单检查：当前章标题是否与上一章结尾的基调/场景有冲突
        # 这里可以添加更复杂的检查逻辑

        return issues

    def _check_plot_threads(
        self,
        chapter: Chapter,
        previous_chapters: List[Chapter]
    ) -> List[ConsistencyIssue]:
        """检查伏笔一致性"""
        issues = []

        # 检查是否有未回收的伏笔被意外提及但未处理
        # 这是一个简化的实现

        return issues


def validate_chapter_quick(
    chapter: Chapter,
    dead_characters: List[str]
) -> List[str]:
    """
    快速验证章节（不依赖NovelBible）

    Args:
        chapter: 章节
        dead_characters: 已死亡/消失角色列表

    Returns:
        问题列表（空表示通过）
    """
    issues = []

    for char_name in dead_characters:
        if char_name in chapter.content:
            issues.append(f"章节中出现了已死亡角色 '{char_name}'")

    return issues
