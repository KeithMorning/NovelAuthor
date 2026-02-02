#!/bin/bash
# 启动 Novel AI Agent API 服务器

echo "🚀 启动 Novel AI Agent API 服务器..."
echo ""
echo "API 文档: http://localhost:8000/docs"
echo "备用文档: http://localhost:8000/redoc"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

python3 -m uvicorn novel_ai_agent.api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info
