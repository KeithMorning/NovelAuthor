"""
风格系统相关 API 路由
包含风格列表、推荐等操作
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from novel_ai_agent.api.schemas.responses import StyleInfo, ApiResponse
from novel_ai_agent.config.styles import (
    WRITER_STYLES, get_style, get_recommended_styles
)

router = APIRouter()


@router.get("/", response_model=List[StyleInfo])
async def list_styles() -> List[StyleInfo]:
    """
    获取所有可用的写作风格
    """
    try:
        style_infos = []
        for style_name, style_obj in WRITER_STYLES.items():
            style_info = StyleInfo(
                name=style_obj.name,
                description=style_obj.description,
                characteristics=style_obj.features,
                suitable_genres=[]  # 暂时留空，可以后续添加
            )
            style_infos.append(style_info)

        return style_infos

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取风格列表失败: {str(e)}")


@router.get("/{style_name}", response_model=StyleInfo)
async def get_style_info(style_name: str) -> StyleInfo:
    """
    获取指定风格的详细信息
    """
    try:
        style_obj = get_style(style_name)

        if not style_obj:
            raise HTTPException(status_code=404, detail=f"风格 {style_name} 不存在")

        return StyleInfo(
            name=style_obj.name,
            description=style_obj.description,
            characteristics=style_obj.features,
            suitable_genres=[]  # 暂时留空
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取风格信息失败: {str(e)}")


@router.get("/recommend/{genre}", response_model=List[str])
async def recommend_styles(genre: str) -> List[str]:
    """
    根据类型推荐适合的风格
    """
    try:
        recommendations = get_recommended_styles(genre)
        return recommendations

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推荐风格失败: {str(e)}")
