"""
章节操作相关 API 路由
包含写作、润色、评审等操作
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
from datetime import datetime

from novel_ai_agent.api.schemas.requests import (
    WriteChapterRequest, PolishChapterRequest, ReviewChapterRequest
)
from novel_ai_agent.api.schemas.responses import ChapterContent, ReviewResult, ApiResponse
from novel_ai_agent.utils.file_manager import file_manager
from novel_ai_agent.api.websocket import manager as ws_manager

router = APIRouter()


@router.get("/{novel_id}/{chapter_number}", response_model=ChapterContent)
async def get_chapter(novel_id: str, chapter_number: int) -> ChapterContent:
    """
    获取指定章节的内容
    """
    try:
        novel = file_manager.load_novel_json(novel_id)

        if not novel:
            raise HTTPException(status_code=404, detail=f"小说 {novel_id} 不存在")

        # 查找章节
        chapter = None
        if novel.chapters:
            for ch in novel.chapters:
                if ch.number == chapter_number:
                    chapter = ch
                    break

        if not chapter:
            raise HTTPException(
                status_code=404,
                detail=f"章节 {chapter_number} 不存在"
            )

        return ChapterContent(
            novel_id=novel_id,
            chapter_number=chapter.number,
            title=chapter.title,
            summary=chapter.summary,
            content=chapter.content or "",
            word_count=len(chapter.content) if chapter.content else 0,
            created_at=novel.updated_at.isoformat() if isinstance(novel.updated_at, datetime) else str(novel.updated_at)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取章节失败: {str(e)}")


@router.post("/write", response_model=ApiResponse)
async def write_chapter(request: WriteChapterRequest, background_tasks: BackgroundTasks) -> ApiResponse:
    """
    写作指定章节
    这是一个异步操作，会在后台执行
    """
    try:
        novel = file_manager.load_novel_json(request.novel_id)

        if not novel:
            raise HTTPException(status_code=404, detail=f"小说 {request.novel_id} 不存在")

        from novel_ai_agent.agents.coordinator import CoordinatorAgent
        coordinator = CoordinatorAgent()

        # 在后台任务中执行写作
        async def write_chapter_task():
            try:
                # 发送开始通知
                await ws_manager.send_progress_update(
                    request.novel_id,
                    "write_chapter",
                    0,
                    f"开始写作第{request.chapter_number}章..."
                )

                coordinator.write_chapter(request.novel_id, request.chapter_number)
                print(f"章节 {request.chapter_number} 写作完成")

                # 发送完成通知
                await ws_manager.send_task_complete(
                    request.novel_id,
                    "write_chapter",
                    {"chapter_number": request.chapter_number}
                )
            except Exception as e:
                print(f"章节写作失败: {str(e)}")
                await ws_manager.send_task_error(
                    request.novel_id,
                    "write_chapter",
                    str(e)
                )

        background_tasks.add_task(write_chapter_task)

        return ApiResponse(
            success=True,
            message=f"章节 {request.chapter_number} 写作任务已启动",
            data={
                "novel_id": request.novel_id,
                "chapter_number": request.chapter_number
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"写作章节失败: {str(e)}")


@router.post("/polish", response_model=ApiResponse)
async def polish_chapter(request: PolishChapterRequest, background_tasks: BackgroundTasks) -> ApiResponse:
    """
    润色指定章节
    这是一个异步操作，会在后台执行
    """
    try:
        novel = file_manager.load_novel_json(request.novel_id)

        if not novel:
            raise HTTPException(status_code=404, detail=f"小说 {request.novel_id} 不存在")

        from novel_ai_agent.agents.editor_agent import EditorAgent
        editor = EditorAgent()

        # 在后台任务中执行润色
        async def polish_chapter_task():
            try:
                # 发送开始通知
                await ws_manager.send_progress_update(
                    request.novel_id,
                    "polish_chapter",
                    0,
                    f"开始润色第{request.chapter_number}章..."
                )

                result = editor.polish_chapter(
                    request.novel_id,
                    request.chapter_number,
                    focus=request.focus
                )
                print(f"章节 {request.chapter_number} 润色完成")

                # 发送完成通知
                await ws_manager.send_task_complete(
                    request.novel_id,
                    "polish_chapter",
                    {"chapter_number": request.chapter_number}
                )
            except Exception as e:
                print(f"章节润色失败: {str(e)}")
                await ws_manager.send_task_error(
                    request.novel_id,
                    "polish_chapter",
                    str(e)
                )

        background_tasks.add_task(polish_chapter_task)

        return ApiResponse(
            success=True,
            message=f"章节 {request.chapter_number} 润色任务已启动",
            data={
                "novel_id": request.novel_id,
                "chapter_number": request.chapter_number,
                "focus": request.focus
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"润色章节失败: {str(e)}")


@router.post("/review", response_model=ReviewResult)
async def review_chapter(request: ReviewChapterRequest) -> ReviewResult:
    """
    评审指定章节
    返回评审结果，包括评分、优点、缺点和建议
    """
    try:
        novel = file_manager.load_novel_json(request.novel_id)

        if not novel:
            raise HTTPException(status_code=404, detail=f"小说 {request.novel_id} 不存在")

        from novel_ai_agent.agents.editor_agent import EditorAgent
        editor = EditorAgent()

        # 执行评审
        result = editor.comprehensive_review(request.novel_id, request.chapter_number)

        return ReviewResult(
            novel_id=request.novel_id,
            chapter_number=request.chapter_number,
            score=result.get("score", 0),
            strengths=result.get("strengths", []),
            weaknesses=result.get("weaknesses", []),
            suggestions=result.get("suggestions", []),
            overall_comment=result.get("overall_comment", "")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"评审章节失败: {str(e)}")
