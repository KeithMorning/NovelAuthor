"""
小说数据模型 - 顶层模型
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from .character import Character
from .chapter import Chapter
from .outline import Outline


class Novel(BaseModel):
    """小说完整模型"""

    id: str = Field(..., description="小说唯一ID")
    title: str = Field(..., description="小说标题")
    author_style: str = Field("中性风格", description="作家风格")
    genre: str = Field(..., description="小说类型")
    outline: Optional[Outline] = Field(None, description="故事大纲")
    characters: List[Character] = Field(default_factory=list, description="角色列表")
    chapters: List[Chapter] = Field(default_factory=list, description="章节列表")
    metadata: Dict = Field(default_factory=dict, description="其他元数据")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def get_character(self, name: str) -> Optional[Character]:
        """根据名字获取角色"""
        for char in self.characters:
            if char.name == name:
                return char
        return None

    def get_chapter(self, number: int) -> Optional[Chapter]:
        """根据章节号获取章节"""
        for chapter in self.chapters:
            if chapter.number == number:
                return chapter
        return None

    def add_character(self, character: Character):
        """添加角色"""
        # 检查是否已存在同名角色
        if self.get_character(character.name):
            raise ValueError(f"角色 '{character.name}' 已存在")
        self.characters.append(character)
        self.updated_at = datetime.now()

    def add_chapter(self, chapter: Chapter):
        """添加章节"""
        # 检查是否已存在相同序号的章节
        if self.get_chapter(chapter.number):
            raise ValueError(f"第{chapter.number}章已存在")
        self.chapters.append(chapter)
        self.chapters.sort(key=lambda x: x.number)  # 保持章节顺序
        self.updated_at = datetime.now()

    def update_chapter(self, chapter: Chapter):
        """更新章节"""
        for i, ch in enumerate(self.chapters):
            if ch.number == chapter.number:
                self.chapters[i] = chapter
                self.updated_at = datetime.now()
                return
        raise ValueError(f"第{chapter.number}章不存在")

    def get_total_words(self) -> int:
        """获取总字数"""
        return sum(chapter.word_count for chapter in self.chapters)

    def to_markdown(self, include_metadata: bool = True) -> str:
        """
        转换为完整的Markdown格式小说

        Args:
            include_metadata: 是否包含元数据

        Returns:
            str: 完整的Markdown格式小说
        """
        md = f"# {self.title}\n\n"

        if include_metadata:
            md += f"**作者风格**: {self.author_style}\n\n"
            md += f"**类型**: {self.genre}\n\n"
            md += f"**创作日期**: {self.created_at.strftime('%Y-%m-%d')}\n\n"
            md += f"**总字数**: {self.get_total_words():,}\n\n"
            md += f"**章节数**: {len(self.chapters)}\n\n"

        md += "---\n\n"

        # 简介 (从大纲获取)
        if self.outline:
            md += "## 简介\n\n"
            md += f"{self.outline.summary}\n\n"
            md += "---\n\n"

        # 角色介绍
        if self.characters:
            md += "## 角色介绍\n\n"
            for character in self.characters:
                md += character.to_markdown()
                md += "---\n\n"

        # 正文
        md += "## 正文\n\n"
        for chapter in sorted(self.chapters, key=lambda x: x.number):
            md += chapter.to_markdown(include_metadata=False)
            md += "---\n\n"

        # 创作信息
        if include_metadata:
            md += "## 创作信息\n\n"
            if self.outline:
                md += f"- **大纲版本**: v{self.outline.version}\n"
            md += f"- **小说ID**: {self.id}\n"
            md += f"- **最后更新**: {self.updated_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

        return md

    class Config:
        json_schema_extra = {
            "example": {
                "id": "novel_001",
                "title": "江湖往事",
                "author_style": "金庸",
                "genre": "武侠",
                "metadata": {
                    "tags": ["武侠", "江湖", "复仇"],
                    "inspiration": "经典武侠小说"
                }
            }
        }
