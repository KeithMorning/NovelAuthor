"""
简单记忆管理器
仅保留短期记忆功能（模式B下不需要向量检索）
"""
from typing import List, Dict, Any, Optional
from ..models.chapter import Chapter


class MemoryManager:
    """
    简化的记忆管理器

    功能（模式B - 完整上下文下）：
    - 短期记忆：当前章节、最近章节等
    - 长期记忆由上下文窗口直接提供，无需向量检索
    """

    def __init__(self, novel_id: str):
        self.novel_id = novel_id

        # 短期记忆（在内存中）
        self.short_term_memory: Dict[str, Any] = {
            "current_chapter": None,
            "recent_chapters": [],  # 最近5章
            "conversation_history": []
        }

    def add_chapter_to_memory(self, chapter: Chapter):
        """
        添加新章节到短期记忆

        Args:
            chapter: 章节对象
        """
        # 更新短期记忆
        self.short_term_memory["current_chapter"] = chapter
        self.short_term_memory["recent_chapters"].append(chapter)

        # 只保留最近5章
        if len(self.short_term_memory["recent_chapters"]) > 5:
            self.short_term_memory["recent_chapters"].pop(0)

    def add_conversation_turn(self, role: str, content: str):
        """
        添加对话轮次到短期记忆
        """
        self.short_term_memory["conversation_history"].append({
            "role": role,
            "content": content
        })

        # 只保留最近20轮对话
        if len(self.short_term_memory["conversation_history"]) > 20:
            self.short_term_memory["conversation_history"] = \
                self.short_term_memory["conversation_history"][-20:]

    def get_conversation_history(self, last_n: int = 10) -> List[Dict]:
        """获取对话历史"""
        history = self.short_term_memory.get("conversation_history", [])
        return history[-last_n:] if len(history) > last_n else history

    def get_recent_chapters(self, count: int = 5) -> List[Chapter]:
        """获取最近的章节"""
        chapters = self.short_term_memory.get("recent_chapters", [])
        return chapters[-count:] if len(chapters) > count else chapters

    def get_current_chapter(self) -> Optional[Chapter]:
        """获取当前章节"""
        return self.short_term_memory.get("current_chapter")

    def clear_short_term_memory(self):
        """清空短期记忆"""
        self.short_term_memory = {
            "current_chapter": None,
            "recent_chapters": [],
            "conversation_history": []
        }

    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        return {
            "novel_id": self.novel_id,
            "recent_chapters_count": len(self.short_term_memory.get("recent_chapters", [])),
            "conversation_turns": len(self.short_term_memory.get("conversation_history", []))
        }


# 全局记忆管理器缓存
_memory_managers: Dict[str, MemoryManager] = {}


def get_memory_manager(novel_id: str) -> MemoryManager:
    """获取或创建指定小说的记忆管理器"""
    if novel_id not in _memory_managers:
        _memory_managers[novel_id] = MemoryManager(novel_id)
    return _memory_managers[novel_id]


def clear_memory_cache():
    """清空记忆管理器缓存"""
    global _memory_managers
    _memory_managers.clear()
