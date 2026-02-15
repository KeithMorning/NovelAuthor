"""
小说管理相关 API 路由
包含创建、查询、删除小说等操作
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any
import os
import json
from pathlib import Path
from datetime import datetime

from novel_ai_agent.api.schemas.requests import CreateNovelRequest
from novel_ai_agent.api.schemas.responses import (
    NovelSummary, NovelDetail, ApiResponse,
    CharacterInfo, PlotPointInfo, ChapterInfo
)
from novel_ai_agent.utils.file_manager import file_manager
from novel_ai_agent.models.novel import Novel
from novel_ai_agent.api.websocket import manager as ws_manager
from novel_ai_agent.utils.logger import get_novel_logs, get_logger

router = APIRouter()


@router.get("/", response_model=List[NovelSummary])
async def list_novels() -> List[NovelSummary]:
    """
    获取所有小说列表
    返回小说的摘要信息
    """
    try:
        novels = file_manager.list_novels()

        summaries = []
        for novel_id in novels:
            novel = file_manager.load_novel_json(novel_id)
            if novel:
                # 计算总章节数（从大纲或metadata获取）
                total_chapters = 0
                if novel.outline and hasattr(novel.outline, 'total_chapters'):
                    total_chapters = novel.outline.total_chapters
                elif 'total_chapters' in novel.metadata:
                    total_chapters = novel.metadata['total_chapters']
                else:
                    total_chapters = len(novel.chapters) if novel.chapters else 0

                # 确定状态
                completed = len(novel.chapters) if novel.chapters else 0
                if completed == 0:
                    status = "创建中"
                elif completed >= total_chapters and total_chapters > 0:
                    status = "已完成"
                else:
                    status = "进行中"

                summary = NovelSummary(
                    id=novel.id,
                    title=novel.title,
                    genre=novel.genre,
                    style=novel.author_style,
                    total_chapters=total_chapters,
                    completed_chapters=completed,
                    status=status,
                    created_at=novel.created_at.isoformat() if isinstance(novel.created_at, datetime) else str(novel.created_at)
                )
                summaries.append(summary)

        return summaries

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取小说列表失败: {str(e)}")


@router.get("/{novel_id}", response_model=NovelDetail)
async def get_novel(novel_id: str) -> NovelDetail:
    """
    获取指定小说的详细信息
    包含角色、情节点、章节等完整信息
    """
    try:
        novel = file_manager.load_novel_json(novel_id)

        if not novel:
            raise HTTPException(status_code=404, detail=f"小说 {novel_id} 不存在")

        # 转换角色信息
        characters = []
        if novel.characters:
            characters = [
                CharacterInfo(
                    name=char.name,
                    role=char.role,
                    personality=char.personality,
                    background=char.background
                )
                for char in novel.characters
            ]

        # 转换情节点信息
        plot_points = []
        if novel.outline and novel.outline.plot_points:
            plot_points = [
                PlotPointInfo(
                    name=pp.name,
                    description=pp.description,
                    chapter_range=pp.chapter_range,
                    importance=pp.importance
                )
                for pp in novel.outline.plot_points
            ]

        # 转换章节信息
        chapters = []
        if novel.chapters:
            chapters = [
                ChapterInfo(
                    number=ch.number,
                    title=ch.title,
                    summary=ch.summary,
                    word_count=len(ch.content) if ch.content else 0,
                    status="已完成" if ch.content else "未完成"
                )
                for ch in novel.chapters
            ]

        # 获取主题（从大纲或metadata）
        theme = ""
        if novel.outline and hasattr(novel.outline, 'theme'):
            theme = novel.outline.theme
        elif 'theme' in novel.metadata:
            theme = novel.metadata['theme']

        # 计算总章节数
        total_chapters = 0
        if novel.outline and hasattr(novel.outline, 'total_chapters'):
            total_chapters = novel.outline.total_chapters
        elif 'total_chapters' in novel.metadata:
            total_chapters = novel.metadata['total_chapters']
        else:
            total_chapters = len(novel.chapters) if novel.chapters else 0

        # 确定状态
        completed = len(novel.chapters) if novel.chapters else 0
        if completed == 0:
            status = "创建中"
        elif completed >= total_chapters and total_chapters > 0:
            status = "已完成"
        else:
            status = "进行中"

        detail = NovelDetail(
            id=novel.id,
            title=novel.title,
            genre=novel.genre,
            theme=theme,
            style=novel.author_style,
            total_chapters=total_chapters,
            status=status,
            characters=characters,
            plot_points=plot_points,
            chapters=chapters,
            created_at=novel.created_at.isoformat() if isinstance(novel.created_at, datetime) else str(novel.created_at),
            updated_at=novel.updated_at.isoformat() if isinstance(novel.updated_at, datetime) else str(novel.updated_at)
        )

        return detail

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取小说详情失败: {str(e)}")


@router.post("/", response_model=ApiResponse)
async def create_novel(request: CreateNovelRequest, background_tasks: BackgroundTasks) -> ApiResponse:
    """
    创建新小说
    这是一个异步操作，会在后台执行创作流程
    """
    try:
        from novel_ai_agent.agents.coordinator import CoordinatorAgent

        # 创建协调器
        coordinator = CoordinatorAgent()

        # 在后台任务中执行创作
        # 在后台任务中执行创作
        async def create_novel_task(novel_id: str):
            try:
                # 发送开始通知
                await ws_manager.broadcast_to_novel({
                    "type": "task_start",
                    "task_type": "create_novel",
                    "title": request.title,
                    "message": "开始创建小说..."
                }, novel_id)

                # 调用 Workflow
                result = await coordinator.create_novel_workflow(
                    title=request.title,
                    genre=request.genre,
                    theme=request.theme,
                    style=request.style,
                    chapter_count=request.chapters,
                    novel_id=novel_id
                )
                
                if result["status"] == "success":
                    novel = result["novel"]
                    print(f"小说创建完成: {novel.id}")

                    # 发送完成通知
                    await ws_manager.send_task_complete(
                        novel_id,
                        "create_novel",
                        {"novel_id": novel_id, "title": novel.title}
                    )
                else:
                    raise Exception(result.get("message", "未知错误"))

            except Exception as e:
                print(f"小说创建失败: {str(e)}")
                await ws_manager.send_task_error(
                    novel_id,
                    "create_novel",
                    str(e)
                )

        # 生成 ID
        import uuid
        novel_id = f"novel_{uuid.uuid4().hex[:8]}"
        
        # 启动后台任务
        background_tasks.add_task(create_novel_task, novel_id)

        return ApiResponse(
            success=True,
            message="小说创建任务已启动，正在后台处理",
            data={
                "novel_id": novel_id,
                "title": request.title,
                "genre": request.genre,
                "chapters": request.chapters
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建小说失败: {str(e)}")


@router.delete("/{novel_id}", response_model=ApiResponse)
async def delete_novel(novel_id: str) -> ApiResponse:
    """
    删除指定小说
    会删除小说文件和相关记忆数据
    """
    try:
        novel = file_manager.load_novel_json(novel_id)

        if not novel:
            raise HTTPException(status_code=404, detail=f"小说 {novel_id} 不存在")

        # 删除小说文件
        file_manager.delete_novel(novel_id)

        # 清除记忆缓存
        from novel_ai_agent.memory import clear_memory_cache
        clear_memory_cache()

        return ApiResponse(
            success=True,
            message=f"小说 {novel_id} 已删除",
            data={"novel_id": novel_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除小说失败: {str(e)}")


@router.get("/{novel_id}/export")
async def export_novel(novel_id: str, format: str = "txt") -> Dict[str, Any]:
    """
    导出小说
    支持格式: txt, json
    """
    try:
        novel = file_manager.load_novel_json(novel_id)

        if not novel:
            raise HTTPException(status_code=404, detail=f"小说 {novel_id} 不存在")

        if format == "json":
            return novel.model_dump()

        elif format == "txt":
            # 生成文本格式
            lines = []
            lines.append(f"《{novel.title}》")
            lines.append(f"类型: {novel.genre}")
            lines.append(f"风格: {novel.style}")
            lines.append(f"主题: {novel.theme}")
            lines.append("\n" + "="*50 + "\n")

            if novel.chapters:
                for chapter in novel.chapters:
                    lines.append(f"第{chapter.number}章 {chapter.title}")
                    lines.append("")
                    lines.append(chapter.content or "（章节内容为空）")
                    lines.append("\n" + "-"*50 + "\n")

            content = "\n".join(lines)

            return {
                "novel_id": novel_id,
                "title": novel.title,
                "format": "txt",
                "content": content
            }

        else:
            raise HTTPException(status_code=400, detail=f"不支持的导出格式: {format}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出小说失败: {str(e)}")


@router.get("/{novel_id}/logs", response_model=Dict[str, Any])
async def get_novel_creation_logs(novel_id: str) -> Dict[str, Any]:
    """
    获取小说创建过程的日志

    返回完整的日志记录，包括：
    - 工作流状态
    - 各步骤的执行情况
    - 错误信息（如果有）
    - 时间统计
    """
    try:
        logs = get_novel_logs(novel_id)

        if not logs:
            raise HTTPException(
                status_code=404,
                detail=f"未找到小说 {novel_id} 的日志记录"
            )

        return {
            "novel_id": novel_id,
            "workflow_status": logs.get("workflow_status", {}),
            "logs": logs.get("logs", []),
            "summary": _generate_log_summary(logs)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取日志失败: {str(e)}"
        )


@router.get("/{novel_id}/logs/status", response_model=Dict[str, Any])
async def get_novel_creation_status(novel_id: str) -> Dict[str, Any]:
    """
    获取小说创建的当前状态（简化版）

    只返回工作流状态，不返回详细日志
    """
    try:
        logs = get_novel_logs(novel_id)

        if not logs:
            # 如果没有日志文件，尝试从内存中的logger获取
            try:
                logger = get_logger(novel_id)
                return {
                    "novel_id": novel_id,
                    "status": logger.get_status()
                }
            except:
                raise HTTPException(
                    status_code=404,
                    detail=f"未找到小说 {novel_id} 的状态信息"
                )

        workflow_status = logs.get("workflow_status", {})

        return {
            "novel_id": novel_id,
            "status": workflow_status.get("status", "unknown"),
            "current_step": workflow_status.get("current_step"),
            "steps_completed": workflow_status.get("steps_completed", []),
            "start_time": workflow_status.get("start_time"),
            "end_time": workflow_status.get("end_time"),
            "has_errors": len(workflow_status.get("errors", [])) > 0,
            "error_count": len(workflow_status.get("errors", []))
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取状态失败: {str(e)}"
        )


def _generate_log_summary(logs: Dict[str, Any]) -> Dict[str, Any]:
    """
    生成日志摘要

    Args:
        logs: 完整的日志数据

    Returns:
        Dict: 日志摘要
    """
    workflow_status = logs.get("workflow_status", {})
    log_entries = logs.get("logs", [])

    # 统计各级别的日志数量
    level_counts = {}
    for entry in log_entries:
        level = entry.get("level", "UNKNOWN")
        level_counts[level] = level_counts.get(level, 0) + 1

    # 计算耗时
    duration = None
    if workflow_status.get("start_time") and workflow_status.get("end_time"):
        from datetime import datetime
        start = datetime.fromisoformat(workflow_status["start_time"])
        end = datetime.fromisoformat(workflow_status["end_time"])
        duration = (end - start).total_seconds()

    return {
        "total_logs": len(log_entries),
        "level_counts": level_counts,
        "steps_completed": len(workflow_status.get("steps_completed", [])),
        "errors": workflow_status.get("errors", []),
        "duration_seconds": duration,
        "final_status": workflow_status.get("status", "unknown")
    }
