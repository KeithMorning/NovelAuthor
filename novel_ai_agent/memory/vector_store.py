"""
向量数据库管理
使用Chroma存储和检索小说相关信息
"""
import os
from typing import List, Dict, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document


class VectorMemoryStore:
    """
    向量记忆存储

    用途：
    1. 存储角色信息，支持快速检索
    2. 存储情节点，便于查找相关内容
    3. 存储章节摘要，用于上下文回顾
    4. 存储世界观设定，保持一致性
    """

    def __init__(self, persist_directory: Optional[str] = None):
        """
        初始化向量存储

        Args:
            persist_directory: 持久化目录路径
        """
        if persist_directory is None:
            persist_directory = os.path.join(
                os.getcwd(),
                "novel_ai_agent",
                "data",
                "chroma"
            )

        self.persist_directory = persist_directory
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        # 使用本地开源embedding模型
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        # 初始化Chroma客户端
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

    def get_collection(self, novel_id: str, collection_type: str) -> Chroma:
        """
        获取或创建指定小说的集合

        Args:
            novel_id: 小说ID
            collection_type: 集合类型 (characters/plots/chapters/worldbuilding)

        Returns:
            Chroma: 向量存储集合
        """
        collection_name = f"{novel_id}_{collection_type}"

        return Chroma(
            client=self.client,
            collection_name=collection_name,
            embedding_function=self.embeddings
        )

    def store_characters(
        self,
        novel_id: str,
        characters: List[Dict]
    ) -> int:
        """
        存储角色信息

        Args:
            novel_id: 小说ID
            characters: 角色列表

        Returns:
            int: 存储的角色数量
        """
        vectorstore = self.get_collection(novel_id, "characters")

        documents = []
        for char in characters:
            # 构建文本内容
            content = f"""
角色名称: {char.get('name', '')}
角色定位: {char.get('role', '')}
性格: {char.get('personality', '')}
背景: {char.get('background', '')}
动机: {char.get('motivation', '')}
外貌: {char.get('appearance', '')}
技能: {char.get('skills', '')}
人物关系: {char.get('relationships', '')}
发展弧线: {char.get('arc', '')}
            """.strip()

            # 创建Document对象
            doc = Document(
                page_content=content,
                metadata={
                    "novel_id": novel_id,
                    "type": "character",
                    "name": char.get('name', ''),
                    "role": char.get('role', '')
                }
            )
            documents.append(doc)

        # 批量添加
        if documents:
            vectorstore.add_documents(documents)

        return len(documents)

    def search_characters(
        self,
        novel_id: str,
        query: str,
        k: int = 3
    ) -> List[Document]:
        """
        搜索角色信息

        Args:
            novel_id: 小说ID
            query: 搜索查询
            k: 返回结果数量

        Returns:
            List[Document]: 搜索结果
        """
        vectorstore = self.get_collection(novel_id, "characters")
        return vectorstore.similarity_search(query, k=k)

    def store_plot_points(
        self,
        novel_id: str,
        plot_points: List[Dict]
    ) -> int:
        """
        存储情节点

        Args:
            novel_id: 小说ID
            plot_points: 情节点列表

        Returns:
            int: 存储的情节点数量
        """
        vectorstore = self.get_collection(novel_id, "plots")

        documents = []
        for plot in plot_points:
            content = f"""
情节点: {plot.get('name', '')}
描述: {plot.get('description', '')}
章节位置: {plot.get('chapter_range', '未指定')}
重要性: {plot.get('importance', '中')}
            """.strip()

            doc = Document(
                page_content=content,
                metadata={
                    "novel_id": novel_id,
                    "type": "plot",
                    "name": plot.get('name', ''),
                    "chapter_range": plot.get('chapter_range', '')
                }
            )
            documents.append(doc)

        if documents:
            vectorstore.add_documents(documents)

        return len(documents)

    def search_plot_points(
        self,
        novel_id: str,
        query: str,
        k: int = 5
    ) -> List[Document]:
        """
        搜索情节点

        Args:
            novel_id: 小说ID
            query: 搜索查询
            k: 返回结果数量

        Returns:
            List[Document]: 搜索结果
        """
        vectorstore = self.get_collection(novel_id, "plots")
        return vectorstore.similarity_search(query, k=k)

    def store_chapters(
        self,
        novel_id: str,
        chapters: List[Dict]
    ) -> int:
        """
        存储章节摘要

        Args:
            novel_id: 小说ID
            chapters: 章节列表

        Returns:
            int: 存储的章节数量
        """
        vectorstore = self.get_collection(novel_id, "chapters")

        documents = []
        for chapter in chapters:
            content = f"""
第{chapter.get('number', '')}章: {chapter.get('title', '')}
摘要: {chapter.get('summary', '')}
涉及角色: {', '.join(chapter.get('characters_involved', []))}
关键事件: {', '.join(chapter.get('key_events', []))}
            """.strip()

            # 添加内容片段（前500字）
            if chapter.get('content'):
                content += f"\n内容片段: {chapter.get('content', '')[:500]}"

            doc = Document(
                page_content=content,
                metadata={
                    "novel_id": novel_id,
                    "type": "chapter",
                    "number": chapter.get('number', 0),
                    "title": chapter.get('title', '')
                }
            )
            documents.append(doc)

        if documents:
            vectorstore.add_documents(documents)

        return len(documents)

    def search_chapters(
        self,
        novel_id: str,
        query: str,
        k: int = 3
    ) -> List[Document]:
        """
        搜索章节

        Args:
            novel_id: 小说ID
            query: 搜索查询
            k: 返回结果数量

        Returns:
            List[Document]: 搜索结果
        """
        vectorstore = self.get_collection(novel_id, "chapters")
        return vectorstore.similarity_search(query, k=k)

    def store_worldbuilding(
        self,
        novel_id: str,
        worldbuilding_items: List[Dict]
    ) -> int:
        """
        存储世界观设定

        Args:
            novel_id: 小说ID
            worldbuilding_items: 世界观设定列表

        Returns:
            int: 存储的设定数量
        """
        vectorstore = self.get_collection(novel_id, "worldbuilding")

        documents = []
        for item in worldbuilding_items:
            content = f"""
类型: {item.get('category', '')}
名称: {item.get('name', '')}
描述: {item.get('description', '')}
规则: {item.get('rules', '')}
            """.strip()

            doc = Document(
                page_content=content,
                metadata={
                    "novel_id": novel_id,
                    "type": "worldbuilding",
                    "category": item.get('category', ''),
                    "name": item.get('name', '')
                }
            )
            documents.append(doc)

        if documents:
            vectorstore.add_documents(documents)

        return len(documents)

    def search_worldbuilding(
        self,
        novel_id: str,
        query: str,
        k: int = 3
    ) -> List[Document]:
        """
        搜索世界观设定

        Args:
            novel_id: 小说ID
            query: 搜索查询
            k: 返回结果数量

        Returns:
            List[Document]: 搜索结果
        """
        vectorstore = self.get_collection(novel_id, "worldbuilding")
        return vectorstore.similarity_search(query, k=k)

    def delete_novel_collections(self, novel_id: str):
        """
        删除指定小说的所有集合

        Args:
            novel_id: 小说ID
        """
        collection_types = ["characters", "plots", "chapters", "worldbuilding"]

        for ctype in collection_types:
            collection_name = f"{novel_id}_{ctype}"
            try:
                self.client.delete_collection(collection_name)
            except Exception:
                # 集合不存在，忽略错误
                pass

    def get_collection_stats(self, novel_id: str) -> Dict[str, int]:
        """
        获取指定小说各集合的统计信息

        Args:
            novel_id: 小说ID

        Returns:
            Dict[str, int]: 各集合的文档数量
        """
        stats = {}
        collection_types = ["characters", "plots", "chapters", "worldbuilding"]

        for ctype in collection_types:
            collection_name = f"{novel_id}_{ctype}"
            try:
                collection = self.client.get_collection(collection_name)
                stats[ctype] = collection.count()
            except Exception:
                stats[ctype] = 0

        return stats


# 全局实例
_vector_store = None


def get_vector_store() -> VectorMemoryStore:
    """
    获取全局向量存储实例

    Returns:
        VectorMemoryStore: 向量存储实例
    """
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorMemoryStore()
    return _vector_store
