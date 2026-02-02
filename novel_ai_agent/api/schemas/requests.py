"""
API 请求数据模式
定义客户端发送的请求数据结构
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class CreateNovelRequest(BaseModel):
    """创建小说请求"""
    title: str = Field(..., description="小说标题", min_length=1, max_length=100)
    genre: str = Field(..., description="小说类型（科幻/武侠/现代/悬疑/奇幻等）", min_length=1, max_length=50)
    theme: str = Field(..., description="主题描述", min_length=1, max_length=500)
    style: str = Field(..., description="写作风格", min_length=1, max_length=50)
    chapters: int = Field(5, description="章节数量", ge=1, le=100)

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "星际迷航",
                "genre": "科幻",
                "theme": "探索未知星系，发现外星文明",
                "style": "刘慈欣",
                "chapters": 10
            }
        }
    }


class WriteChapterRequest(BaseModel):
    """写作章节请求"""
    novel_id: str = Field(..., description="小说ID")
    chapter_number: int = Field(..., description="章节号", ge=1)

    model_config = {
        "json_schema_extra": {
            "example": {
                "novel_id": "novel_abc123",
                "chapter_number": 1
            }
        }
    }


class PolishChapterRequest(BaseModel):
    """润色章节请求"""
    novel_id: str = Field(..., description="小说ID")
    chapter_number: int = Field(..., description="章节号", ge=1)
    focus: Optional[str] = Field(None, description="润色重点（可选）")

    model_config = {
        "json_schema_extra": {
            "example": {
                "novel_id": "novel_abc123",
                "chapter_number": 1,
                "focus": "提升动作场景的描写"
            }
        }
    }


class ReviewChapterRequest(BaseModel):
    """评审章节请求"""
    novel_id: str = Field(..., description="小说ID")
    chapter_number: int = Field(..., description="章节号", ge=1)

    model_config = {
        "json_schema_extra": {
            "example": {
                "novel_id": "novel_abc123",
                "chapter_number": 1
            }
        }
    }


class SearchMemoryRequest(BaseModel):
    """搜索记忆请求"""
    novel_id: str = Field(..., description="小说ID")
    query: str = Field(..., description="搜索查询", min_length=1, max_length=200)
    memory_type: str = Field("all", description="记忆类型（characters/plots/chapters/all）")
    k: int = Field(5, description="返回结果数量", ge=1, le=20)

    model_config = {
        "json_schema_extra": {
            "example": {
                "novel_id": "novel_abc123",
                "query": "主角的背景故事",
                "memory_type": "characters",
                "k": 3
            }
        }
    }
