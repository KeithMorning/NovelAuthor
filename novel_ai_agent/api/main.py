"""
FastAPI 主应用
提供小说创作系统的 Web API 接口
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Any
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from novel_ai_agent.api.routes import novels, chapters, memory, styles, websocket

# 创建 FastAPI 应用
app = FastAPI(
    title="Novel AI Agent API",
    description="AI 驱动的小说创作系统 Web API",
    version="0.4.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["根路径"])
async def root() -> Dict[str, Any]:
    """
    API 根路径
    返回 API 基本信息
    """
    return {
        "name": "Novel AI Agent API",
        "version": "0.4.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "novels": "/api/novels",
            "chapters": "/api/chapters",
            "memory": "/api/memory",
            "styles": "/api/styles",
            "websocket": "/ws"
        }
    }


@app.get("/health", tags=["健康检查"])
async def health_check() -> Dict[str, str]:
    """
    健康检查端点
    用于监控和负载均衡器
    """
    return {"status": "healthy"}


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """自定义 HTTP 异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "status_code": 500
        }
    )


# 注册路由
app.include_router(novels.router, prefix="/api/novels", tags=["小说管理"])
app.include_router(chapters.router, prefix="/api/chapters", tags=["章节操作"])
app.include_router(memory.router, prefix="/api/memory", tags=["记忆系统"])
app.include_router(styles.router, prefix="/api/styles", tags=["风格系统"])
app.include_router(websocket.router, tags=["WebSocket 实时通信"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
