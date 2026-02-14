"""
大纲数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class PlotPoint(BaseModel):
    """情节点模型"""

    name: str = Field(..., description="情节点名称")
    description: str = Field(..., description="情节点描述")
    chapter_range: str = Field(..., description="所在章节范围, 如'第1-3章'")
    importance: str = Field(..., description="重要性: 高/中/低")


class Scene(BaseModel):
    """场景模型"""
    description: str = Field(..., description="场景描述")
    focus: str = Field(..., description="场景焦点")
    characters: List[str] = Field(default_factory=list, description="涉及角色")


class DetailedChapterPlan(BaseModel):
    """详细章节规划模型"""
    detailed_summary: str = Field(..., description="详细章节梗概")
    scenes: List[Scene] = Field(default_factory=list, description="场景列表")
    emotional_tone: str = Field(..., description="情感基调")
    key_dialogues: List[str] = Field(default_factory=list, description="关键对话或动作点")
    transitions: Dict[str, str] = Field(default_factory=dict, description="与前后章的衔接点")


class ChapterPlan(BaseModel):
    """章节规划模型"""

    chapter_number: int = Field(..., description="章节序号")
    title: str = Field(..., description="章节标题")
    summary: str = Field(..., description="章节梗概")
    key_events: List[str] = Field(default_factory=list, description="关键事件列表")
    characters_involved: List[str] = Field(default_factory=list, description="涉及角色")
    estimated_words: int = Field(3000, description="预计字数")
    detailed_plan: Optional[DetailedChapterPlan] = Field(None, description="详细章节规划")


class Outline(BaseModel):
    """大纲模型"""

    title: str = Field(..., description="小说标题")
    genre: str = Field(..., description="类型: 武侠/科幻/推理等")
    summary: str = Field(..., description="故事简介")
    theme: str = Field(..., description="主题思想")
    setting: Optional[str] = Field(None, description="故事背景设定")
    plot_points: List[PlotPoint] = Field(default_factory=list, description="主要情节点")
    chapters_plan: List[ChapterPlan] = Field(default_factory=list, description="章节规划")
    target_words: Optional[int] = Field(None, description="目标总字数")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    version: int = Field(1, description="大纲版本号")

    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        md = f"# {self.title} - 故事大纲\n\n"
        md += f"**类型**: {self.genre}\n\n"
        md += f"**版本**: v{self.version}\n\n"

        md += "## 故事简介\n\n"
        md += f"{self.summary}\n\n"

        md += "## 主题\n\n"
        md += f"{self.theme}\n\n"

        if self.setting:
            md += "## 故事背景\n\n"
            md += f"{self.setting}\n\n"

        if self.plot_points:
            md += "## 主要情节点\n\n"
            for i, point in enumerate(self.plot_points, 1):
                md += f"### {i}. {point.name}\n\n"
                md += f"**位置**: {point.chapter_range}\n\n"
                md += f"**重要性**: {point.importance}\n\n"
                md += f"**描述**: {point.description}\n\n"

        if self.chapters_plan:
            md += "## 章节规划\n\n"
            for chapter in self.chapters_plan:
                md += f"### 第{chapter.chapter_number}章: {chapter.title}\n\n"
                md += f"**梗概**: {chapter.summary}\n\n"

                if chapter.key_events:
                    md += "**关键事件**:\n"
                    for event in chapter.key_events:
                        md += f"- {event}\n"
                    md += "\n"

                if chapter.characters_involved:
                    md += f"**涉及角色**: {', '.join(chapter.characters_involved)}\n\n"

                md += f"**预计字数**: {chapter.estimated_words}\n\n"
                md += "---\n\n"

        if self.target_words:
            md += f"**目标总字数**: {self.target_words:,}\n\n"

        md += f"**创建时间**: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        md += f"**最后更新**: {self.updated_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

        return md

    class Config:
        json_schema_extra = {
            "example": {
                "title": "三体往事",
                "genre": "科幻",
                "summary": "人类首次接触外星文明,面临生存危机",
                "theme": "文明的冲突与选择",
                "setting": "近未来地球,三体星系",
                "plot_points": [
                    {
                        "name": "接收外星信号",
                        "description": "科学家首次接收到三体文明的信号",
                        "chapter_range": "第1-2章",
                        "importance": "高"
                    }
                ],
                "chapters_plan": [
                    {
                        "chapter_number": 1,
                        "title": "信号",
                        "summary": "天文台接收到神秘信号",
                        "key_events": ["发现信号", "初步解密"],
                        "characters_involved": ["叶文洁", "汪淼"],
                        "estimated_words": 3000
                    }
                ],
                "target_words": 100000,
                "version": 1
            }
        }
