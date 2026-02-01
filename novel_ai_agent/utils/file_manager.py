"""
文件管理工具
负责小说、大纲、角色设定的文件读写
"""
import os
import json
from pathlib import Path
from typing import Optional
from datetime import datetime
from ..models.novel import Novel
from ..models.outline import Outline
from ..models.character import Character
from ..models.chapter import Chapter
from ..config.settings import get_settings


class FileManager:
    """文件管理器"""

    def __init__(self):
        self.settings = get_settings()
        self._ensure_directories()

    def _ensure_directories(self):
        """确保输出目录存在"""
        dirs = [
            self.settings.output_dir,
            self.settings.novels_dir,
            self.settings.outlines_dir,
            self.settings.characters_dir,
        ]
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

    def save_novel_markdown(self, novel: Novel, include_metadata: bool = True) -> str:
        """
        保存小说为Markdown文件

        Args:
            novel: 小说对象
            include_metadata: 是否包含元数据

        Returns:
            str: 保存的文件路径
        """
        filename = f"{novel.id}_{novel.title}.md"
        # 移除文件名中的非法字符
        filename = "".join(c for c in filename if c.isalnum() or c in (' ', '_', '-', '.')).strip()
        filepath = os.path.join(self.settings.novels_dir, filename)

        markdown_content = novel.to_markdown(include_metadata=include_metadata)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        return filepath

    def save_novel_json(self, novel: Novel) -> str:
        """
        保存小说为JSON文件 (用于数据持久化)

        Args:
            novel: 小说对象

        Returns:
            str: 保存的文件路径
        """
        filename = f"{novel.id}.json"
        filepath = os.path.join(self.settings.novels_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(novel.model_dump_json(indent=2, ensure_ascii=False))

        return filepath

    def load_novel_json(self, novel_id: str) -> Optional[Novel]:
        """
        从JSON文件加载小说

        Args:
            novel_id: 小说ID

        Returns:
            Novel: 小说对象,如果不存在则返回None
        """
        filename = f"{novel_id}.json"
        filepath = os.path.join(self.settings.novels_dir, filename)

        if not os.path.exists(filepath):
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return Novel(**data)

    def save_outline_markdown(self, outline: Outline, novel_id: str) -> str:
        """
        保存大纲为Markdown文件

        Args:
            outline: 大纲对象
            novel_id: 小说ID

        Returns:
            str: 保存的文件路径
        """
        filename = f"{novel_id}_outline_v{outline.version}.md"
        filepath = os.path.join(self.settings.outlines_dir, filename)

        markdown_content = outline.to_markdown()

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        return filepath

    def save_characters_markdown(self, characters: list[Character], novel_id: str) -> str:
        """
        保存角色设定为Markdown文件

        Args:
            characters: 角色列表
            novel_id: 小说ID

        Returns:
            str: 保存的文件路径
        """
        filename = f"{novel_id}_characters.md"
        filepath = os.path.join(self.settings.characters_dir, filename)

        md = f"# 角色设定\n\n"
        md += f"**更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        md += "---\n\n"

        for character in characters:
            md += character.to_markdown()
            md += "---\n\n"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md)

        return filepath

    def save_chapter_markdown(self, chapter: Chapter, novel_id: str) -> str:
        """
        保存单个章节为Markdown文件

        Args:
            chapter: 章节对象
            novel_id: 小说ID

        Returns:
            str: 保存的文件路径
        """
        filename = f"{novel_id}_chapter_{chapter.number:03d}.md"
        filepath = os.path.join(self.settings.novels_dir, filename)

        markdown_content = chapter.to_markdown(include_metadata=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        return filepath

    def list_novels(self) -> list[str]:
        """
        列出所有小说ID

        Returns:
            list[str]: 小说ID列表
        """
        novels_dir = Path(self.settings.novels_dir)
        json_files = novels_dir.glob("*.json")
        return [f.stem for f in json_files]

    def delete_novel(self, novel_id: str) -> bool:
        """
        删除小说相关的所有文件

        Args:
            novel_id: 小说ID

        Returns:
            bool: 是否删除成功
        """
        try:
            # 删除JSON文件
            json_file = os.path.join(self.settings.novels_dir, f"{novel_id}.json")
            if os.path.exists(json_file):
                os.remove(json_file)

            # 删除Markdown文件
            novels_dir = Path(self.settings.novels_dir)
            for md_file in novels_dir.glob(f"{novel_id}*.md"):
                os.remove(md_file)

            # 删除大纲文件
            outlines_dir = Path(self.settings.outlines_dir)
            for outline_file in outlines_dir.glob(f"{novel_id}*.md"):
                os.remove(outline_file)

            # 删除角色文件
            characters_dir = Path(self.settings.characters_dir)
            for char_file in characters_dir.glob(f"{novel_id}*.md"):
                os.remove(char_file)

            return True
        except Exception as e:
            print(f"删除小说 {novel_id} 时出错: {e}")
            return False

    def export_novel_with_version(self, novel: Novel) -> str:
        """
        导出带时间戳版本的小说备份

        Args:
            novel: 小说对象

        Returns:
            str: 保存的文件路径
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{novel.id}_{novel.title}_backup_{timestamp}.md"
        filename = "".join(c for c in filename if c.isalnum() or c in (' ', '_', '-', '.')).strip()
        filepath = os.path.join(self.settings.novels_dir, filename)

        markdown_content = novel.to_markdown(include_metadata=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        return filepath


# 全局文件管理器实例
file_manager = FileManager()
