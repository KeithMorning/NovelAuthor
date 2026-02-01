"""
章节数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class ChapterStatus(str, Enum):
    """章节状态枚举"""
    DRAFT = "draft"  # 草稿
    REVIEWED = "reviewed"  # 已审阅
    FINAL = "final"  # 最终版


class Chapter(BaseModel):
    """章节模型"""

    number: int = Field(..., description="章节序号")
    title: str = Field(..., description="章节标题")
    summary: str = Field(..., description="章节梗概")
    content: str = Field(..., description="章节正文内容 (Markdown格式)")
    word_count: int = Field(0, description="字数统计")
    status: ChapterStatus = Field(ChapterStatus.DRAFT, description="章节状态")
    version: int = Field(1, description="版本号")
    notes: Optional[str] = Field(None, description="备注或修改说明")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def update_word_count(self):
        """更新字数统计 (统计中文字符)"""
        # 统计中文字符数
        chinese_chars = sum(1 for char in self.content if '\u4e00' <= char <= '\u9fff')
        # 统计英文单词数 (简化处理)
        english_words = len([word for word in self.content.split() if any(c.isalpha() for c in word)])
        self.word_count = chinese_chars + english_words

    def to_markdown(self, include_metadata: bool = False) -> str:
        """
        转换为Markdown格式

        Args:
            include_metadata: 是否包含元数据信息

        Returns:
            str: Markdown格式的章节内容
        """
        md = f"## 第{self.number}章 {self.title}\n\n"

        if include_metadata:
            md += f"> **状态**: {self.status.value} | **版本**: v{self.version} | **字数**: {self.word_count}\n"
            md += f"> **创建**: {self.created_at.strftime('%Y-%m-%d')} | **更新**: {self.updated_at.strftime('%Y-%m-%d')}\n\n"
            if self.notes:
                md += f"> **备注**: {self.notes}\n\n"
            md += "---\n\n"

        md += self.content + "\n\n"

        return md

    class Config:
        json_schema_extra = {
            "example": {
                "number": 1,
                "title": "初遇",
                "summary": "主角在江湖中初次亮相,遭遇劲敌",
                "content": "月黑风高的夜晚,一个黑衣人影出现在小镇的街道上...",
                "word_count": 3500,
                "status": "draft",
                "version": 1,
                "notes": "需要加强动作场面的描写"
            }
        }
