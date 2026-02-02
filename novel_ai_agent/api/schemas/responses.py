"""
API 响应数据模式
定义服务器返回的响应数据结构
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class NovelSummary(BaseModel):
    """小说摘要信息"""
    id: str = Field(..., description="小说ID")
    title: str = Field(..., description="小说标题")
    genre: str = Field(..., description="小说类型")
    style: str = Field(..., description="写作风格")
    total_chapters: int = Field(..., description="总章节数")
    completed_chapters: int = Field(..., description="已完成章节数")
    status: str = Field(..., description="状态（创建中/进行中/已完成）")
    created_at: str = Field(..., description="创建时间")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "novel_abc123",
                "title": "星际迷航",
                "genre": "科幻",
                "style": "刘慈欣",
                "total_chapters": 10,
                "completed_chapters": 5,
                "status": "进行中",
                "created_at": "2026-02-02T10:00:00"
            }
        }
    }


class CharacterInfo(BaseModel):
    """角色信息"""
    name: str
    role: str
    personality: str
    background: str


class PlotPointInfo(BaseModel):
    """情节点信息"""
    name: str
    description: str
    chapter_range: str
    importance: str


class ChapterInfo(BaseModel):
    """章节信息"""
    number: int
    title: str
    summary: str
    word_count: int
    status: str


class NovelDetail(BaseModel):
    """小说详细信息"""
    id: str
    title: str
    genre: str
    theme: str
    style: str
    total_chapters: int
    status: str
    characters: List[CharacterInfo]
    plot_points: List[PlotPointInfo]
    chapters: List[ChapterInfo]
    created_at: str
    updated_at: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "novel_abc123",
                "title": "星际迷航",
                "genre": "科幻",
                "theme": "探索未知星系",
                "style": "刘慈欣",
                "total_chapters": 10,
                "status": "进行中",
                "characters": [
                    {
                        "name": "张伟",
                        "role": "主角",
                        "personality": "勇敢果断",
                        "background": "星际舰队船长"
                    }
                ],
                "plot_points": [],
                "chapters": [],
                "created_at": "2026-02-02T10:00:00",
                "updated_at": "2026-02-02T12:00:00"
            }
        }
    }


class ChapterContent(BaseModel):
    """章节内容"""
    novel_id: str
    chapter_number: int
    title: str
    summary: str
    content: str
    word_count: int
    created_at: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "novel_id": "novel_abc123",
                "chapter_number": 1,
                "title": "启航",
                "summary": "星际舰队开始了探险之旅",
                "content": "在遥远的未来...",
                "word_count": 3000,
                "created_at": "2026-02-02T11:00:00"
            }
        }
    }


class ReviewResult(BaseModel):
    """评审结果"""
    novel_id: str
    chapter_number: int
    score: float = Field(..., ge=0, le=10)
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    overall_comment: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "novel_id": "novel_abc123",
                "chapter_number": 1,
                "score": 8.5,
                "strengths": ["场景描写生动", "人物塑造立体"],
                "weaknesses": ["节奏略慢"],
                "suggestions": ["可以加快开场节奏"],
                "overall_comment": "整体质量优秀"
            }
        }
    }


class MemoryStats(BaseModel):
    """记忆统计信息"""
    novel_id: str
    characters_count: int
    plots_count: int
    chapters_count: int
    worldbuilding_count: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "novel_id": "novel_abc123",
                "characters_count": 5,
                "plots_count": 12,
                "chapters_count": 5,
                "worldbuilding_count": 8
            }
        }
    }


class StyleInfo(BaseModel):
    """风格信息"""
    name: str
    description: str
    characteristics: List[str]
    suitable_genres: List[str]

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "刘慈欣",
                "description": "硬科幻风格",
                "characteristics": ["科技感强", "逻辑严密"],
                "suitable_genres": ["科幻", "未来"]
            }
        }
    }


class ApiResponse(BaseModel):
    """通用 API 响应"""
    success: bool = Field(..., description="请求是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "操作成功",
                "data": {"key": "value"}
            }
        }
    }
