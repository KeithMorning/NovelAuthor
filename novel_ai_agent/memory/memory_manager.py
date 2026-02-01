"""
记忆管理器
整合短期和长期记忆，提供统一的记忆访问接口
"""
from typing import List, Dict, Optional, Any
from ..models.novel import Novel
from ..models.character import Character
from ..models.outline import Outline, PlotPoint
from ..models.chapter import Chapter
from .vector_store import get_vector_store


class MemoryManager:
    """
    记忆管理器

    功能：
    1. 短期记忆：当前对话上下文、最近的章节等
    2. 长期记忆：角色、情节、世界观等（存储在向量数据库）
    3. 记忆检索：根据查询快速找到相关信息
    4. 记忆更新：同步更新短期和长期记忆
    """

    def __init__(self, novel_id: str):
        """
        初始化记忆管理器

        Args:
            novel_id: 小说ID
        """
        self.novel_id = novel_id
        self.vector_store = get_vector_store()

        # 短期记忆（在内存中）
        self.short_term_memory: Dict[str, Any] = {
            "current_chapter": None,
            "recent_chapters": [],
            "active_characters": [],
            "conversation_history": []
        }

    def load_novel_to_memory(self, novel: Novel):
        """
        将小说加载到记忆系统

        Args:
            novel: 小说对象
        """
        # 存储角色到向量数据库
        if novel.characters:
            characters_data = [
                {
                    "name": char.name,
                    "role": char.role,
                    "personality": char.personality,
                    "background": char.background,
                    "motivation": char.motivation,
                    "appearance": char.appearance,
                    "skills": char.skills,
                    "relationships": char.relationships,
                    "arc": char.arc
                }
                for char in novel.characters
            ]
            self.vector_store.store_characters(self.novel_id, characters_data)

        # 存储情节点到向量数据库
        if novel.outline and novel.outline.plot_points:
            plot_data = [
                {
                    "name": pp.name,
                    "type": pp.type,
                    "description": pp.description,
                    "chapter": pp.chapter_number,
                    "characters_involved": pp.characters_involved
                }
                for pp in novel.outline.plot_points
            ]
            self.vector_store.store_plot_points(self.novel_id, plot_data)

        # 存储章节到向量数据库
        if novel.chapters:
            chapters_data = [
                {
                    "number": ch.number,
                    "title": ch.title,
                    "summary": ch.summary,
                    "content": ch.content,
                    "characters_involved": [],  # 可以从content中提取
                    "key_events": []  # 可以从content中提取
                }
                for ch in novel.chapters
            ]
            self.vector_store.store_chapters(self.novel_id, chapters_data)

    def add_chapter_to_memory(self, chapter: Chapter):
        """
        添加新章节到记忆

        Args:
            chapter: 章节对象
        """
        # 更新短期记忆
        self.short_term_memory["current_chapter"] = chapter
        self.short_term_memory["recent_chapters"].append(chapter)

        # 只保留最近5章
        if len(self.short_term_memory["recent_chapters"]) > 5:
            self.short_term_memory["recent_chapters"].pop(0)

        # 更新长期记忆
        chapter_data = [{
            "number": chapter.number,
            "title": chapter.title,
            "summary": chapter.summary,
            "content": chapter.content,
            "characters_involved": [],
            "key_events": []
        }]
        self.vector_store.store_chapters(self.novel_id, chapter_data)

    def recall_characters(self, query: str, k: int = 3) -> List[str]:
        """
        根据查询回忆相关角色

        Args:
            query: 查询文本
            k: 返回数量

        Returns:
            List[str]: 角色信息列表
        """
        docs = self.vector_store.search_characters(self.novel_id, query, k)
        return [doc.page_content for doc in docs]

    def recall_plot_points(self, query: str, k: int = 5) -> List[str]:
        """
        根据查询回忆相关情节点

        Args:
            query: 查询文本
            k: 返回数量

        Returns:
            List[str]: 情节点信息列表
        """
        docs = self.vector_store.search_plot_points(self.novel_id, query, k)
        return [doc.page_content for doc in docs]

    def recall_chapters(self, query: str, k: int = 3) -> List[str]:
        """
        根据查询回忆相关章节

        Args:
            query: 查询文本
            k: 返回数量

        Returns:
            List[str]: 章节信息列表
        """
        docs = self.vector_store.search_chapters(self.novel_id, query, k)
        return [doc.page_content for doc in docs]

    def get_context_for_writing(
        self,
        chapter_number: int,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取写作上下文

        Args:
            chapter_number: 当前章节号
            query: 可选的查询，用于检索特定信息

        Returns:
            Dict: 包含写作所需的上下文信息
        """
        context = {
            "recent_chapters": [],
            "relevant_characters": [],
            "relevant_plots": []
        }

        # 获取最近的章节
        recent_chapters = self.short_term_memory.get("recent_chapters", [])
        context["recent_chapters"] = [
            {
                "number": ch.number,
                "title": ch.title,
                "summary": ch.summary
            }
            for ch in recent_chapters
            if ch.number < chapter_number
        ]

        # 如果有查询，检索相关信息
        if query:
            context["relevant_characters"] = self.recall_characters(query, k=3)
            context["relevant_plots"] = self.recall_plot_points(query, k=3)

        return context

    def add_conversation_turn(self, role: str, content: str):
        """
        添加对话轮次到短期记忆

        Args:
            role: 角色（user/assistant）
            content: 内容
        """
        self.short_term_memory["conversation_history"].append({
            "role": role,
            "content": content
        })

        # 只保留最近10轮对话
        if len(self.short_term_memory["conversation_history"]) > 20:
            self.short_term_memory["conversation_history"] = \
                self.short_term_memory["conversation_history"][-20:]

    def get_conversation_history(self, last_n: int = 10) -> List[Dict]:
        """
        获取对话历史

        Args:
            last_n: 返回最近的N轮对话

        Returns:
            List[Dict]: 对话历史
        """
        history = self.short_term_memory.get("conversation_history", [])
        return history[-last_n:] if len(history) > last_n else history

    def clear_short_term_memory(self):
        """清空短期记忆"""
        self.short_term_memory = {
            "current_chapter": None,
            "recent_chapters": [],
            "active_characters": [],
            "conversation_history": []
        }

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        获取记忆统计信息

        Returns:
            Dict: 记忆统计
        """
        vector_stats = self.vector_store.get_collection_stats(self.novel_id)

        return {
            "novel_id": self.novel_id,
            "short_term": {
                "current_chapter": self.short_term_memory.get("current_chapter") is not None,
                "recent_chapters_count": len(self.short_term_memory.get("recent_chapters", [])),
                "conversation_turns": len(self.short_term_memory.get("conversation_history", []))
            },
            "long_term": vector_stats
        }


# 全局记忆管理器缓存
_memory_managers: Dict[str, MemoryManager] = {}


def get_memory_manager(novel_id: str) -> MemoryManager:
    """
    获取或创建指定小说的记忆管理器

    Args:
        novel_id: 小说ID

    Returns:
        MemoryManager: 记忆管理器实例
    """
    if novel_id not in _memory_managers:
        _memory_managers[novel_id] = MemoryManager(novel_id)
    return _memory_managers[novel_id]


def clear_memory_cache():
    """清空记忆管理器缓存"""
    global _memory_managers
    _memory_managers.clear()
