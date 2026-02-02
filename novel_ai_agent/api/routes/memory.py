"""
记忆系统相关 API 路由
包含记忆检索、统计等操作
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from novel_ai_agent.api.schemas.requests import SearchMemoryRequest
from novel_ai_agent.api.schemas.responses import MemoryStats, ApiResponse
from novel_ai_agent.memory.memory_manager import get_memory_manager

router = APIRouter()


@router.get("/{novel_id}/stats", response_model=MemoryStats)
async def get_memory_stats(novel_id: str) -> MemoryStats:
    """
    获取指定小说的记忆统计信息
    包含各类记忆的数量
    """
    try:
        memory_manager = get_memory_manager(novel_id)
        stats = memory_manager.get_memory_stats()

        long_term = stats.get("long_term", {})

        return MemoryStats(
            novel_id=novel_id,
            characters_count=long_term.get("characters", 0),
            plots_count=long_term.get("plots", 0),
            chapters_count=long_term.get("chapters", 0),
            worldbuilding_count=long_term.get("worldbuilding", 0)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取记忆统计失败: {str(e)}")


@router.post("/search", response_model=Dict[str, Any])
async def search_memory(request: SearchMemoryRequest) -> Dict[str, Any]:
    """
    搜索记忆
    根据查询返回相关的记忆内容
    """
    try:
        memory_manager = get_memory_manager(request.novel_id)

        results = {}

        if request.memory_type in ["characters", "all"]:
            results["characters"] = memory_manager.recall_characters(
                request.query,
                k=request.k
            )

        if request.memory_type in ["plots", "all"]:
            results["plots"] = memory_manager.recall_plot_points(
                request.query,
                k=request.k
            )

        if request.memory_type in ["chapters", "all"]:
            results["chapters"] = memory_manager.recall_chapters(
                request.query,
                k=request.k
            )

        return {
            "novel_id": request.novel_id,
            "query": request.query,
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索记忆失败: {str(e)}")
