"""
章节操作相关 API 路由
包含写作、润色、评审等操作
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
from datetime import datetime

from novel_ai_agent.api.schemas.requests import (
    WriteChapterRequest, WriteAllChaptersRequest, PolishChapterRequest, ReviewChapterRequest
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


@router.post("/write-all", response_model=ApiResponse)
async def write_all_chapters(request: WriteAllChaptersRequest, background_tasks: BackgroundTasks) -> ApiResponse:
    """
    批量写作全部章节
    这是一个异步操作，会在后台按顺序写作所有章节
    """
    try:
        novel = file_manager.load_novel_json(request.novel_id)

        if not novel:
            raise HTTPException(status_code=404, detail=f"小说 {request.novel_id} 不存在")

        if not novel.outline or not novel.outline.chapters_plan:
            raise HTTPException(status_code=400, detail="小说没有大纲或章节规划")

        from novel_ai_agent.agents.coordinator import CoordinatorAgent
        coordinator = CoordinatorAgent()

        async def write_all_task():
            try:
                await ws_manager.broadcast_to_novel({
                    "type": "task_start",
                    "task_type": "write_all_chapters",
                    "novel_id": request.novel_id,
                    "message": "开始批量写作全部章节..."
                }, request.novel_id)

                async def progress_callback(chapter_num, total, status, message):
                    await ws_manager.send_progress_update(
                        request.novel_id,
                        "write_all_chapters",
                        int(chapter_num / total * 100) if total > 0 else 0,
                        message
                    )

                result = await coordinator.write_all_chapters_workflow(
                    novel_id=request.novel_id,
                    start_chapter=request.start_chapter,
                    progress_callback=progress_callback
                )

                if result["status"] in ("success", "partial"):
                    await ws_manager.send_task_complete(
                        request.novel_id,
                        "write_all_chapters",
                        {
                            "chapters_written": result.get("chapters_written", 0),
                            "total_words": result.get("total_words", 0),
                            "status": result["status"]
                        }
                    )
                else:
                    raise Exception(result.get("message", "未知错误"))

            except Exception as e:
                print(f"批量写作失败: {str(e)}")
                await ws_manager.send_task_error(
                    request.novel_id,
                    "write_all_chapters",
                    str(e)
                )

        background_tasks.add_task(write_all_task)

        total_chapters = len(novel.outline.chapters_plan)
        written = len(novel.chapters) if novel.chapters else 0

        return ApiResponse(
            success=True,
            message=f"批量写作任务已启动，将从第{request.start_chapter}章开始",
            data={
                "novel_id": request.novel_id,
                "start_chapter": request.start_chapter,
                "total_chapters": total_chapters,
                "already_written": written
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量写作失败: {str(e)}")


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

                # 获取目标章节
                target_chapter = novel.get_chapter(request.chapter_number)
                if not target_chapter:
                    raise Exception(f"未找到第{request.chapter_number}章")

                result = await editor.polish_chapter(
                    chapter=target_chapter,
                    style=novel.author_style,
                    focus_areas=[f.strip() for f in request.focus.split(",")] if request.focus else None,
                    user_requirements=request.requirements or ""
                )
                
                if result["status"] == "success":
                    polished_chapter = result["chapter"]
                    # 更新并保存
                    novel.update_chapter(polished_chapter)
                    file_manager.save_novel_json(novel)
                    file_manager.save_chapter_markdown(polished_chapter, request.novel_id)
                    print(f"章节 {request.chapter_number} 润色完成")

                    # 发送完成通知
                    await ws_manager.send_task_complete(
                        request.novel_id,
                        "polish_chapter",
                        {"chapter_number": request.chapter_number}
                    )
                else:
                    raise Exception(result.get("message", "润色失败"))

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
                "focus": request.focus,
                "requirements": request.requirements
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

        target_chapter = novel.get_chapter(request.chapter_number)
        if not target_chapter:
            raise HTTPException(status_code=404, detail=f"未找到第{request.chapter_number}章")

        from novel_ai_agent.agents.editor_agent import EditorAgent
        editor = EditorAgent()

        # 获取前文
        previous_chapters = [ch for ch in novel.chapters if ch.number < request.chapter_number]

        # 执行评审
        result = await editor.comprehensive_review(
            chapter=target_chapter,
            style=novel.author_style,
            characters=novel.characters,
            outline=novel.outline,
            previous_chapters=previous_chapters if previous_chapters else None,
            user_requirements=request.requirements or ""
        )

        if result["status"] != "success":
            raise HTTPException(status_code=500, detail=result.get("message", "评审失败"))

        review_result = result["review"]

        return ReviewResult(
            novel_id=request.novel_id,
            chapter_number=request.chapter_number,
            score=review_result.get("overall_score", 0),
            strengths=review_result.get("strengths", []),
            weaknesses=review_result.get("weaknesses", []),
            suggestions=review_result.get("revision_suggestions", []),
            overall_comment=review_result.get("summary", "")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"评审章节失败: {str(e)}")
