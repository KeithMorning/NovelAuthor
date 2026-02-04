#!/bin/bash

# 小说 AI 代理系统 - 停止所有服务
# Novel AI Agent - Stop All Services

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🛑 停止小说 AI 代理系统..."
echo "================================"
echo ""

# 从 PID 文件停止服务
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${BLUE}停止后端服务 (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID
        echo -e "${GREEN}✓ 后端服务已停止${NC}"
    fi
    rm -f .backend.pid
fi

if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${BLUE}停止前端服务 (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID
        echo -e "${GREEN}✓ 前端服务已停止${NC}"
    fi
    rm -f .frontend.pid
fi

# 额外检查：停止所有相关进程
echo ""
echo -e "${BLUE}检查残留进程...${NC}"

# 停止所有 uvicorn 进程
UVICORN_PIDS=$(ps aux | grep "uvicorn novel_ai_agent.api.main:app" | grep -v grep | awk '{print $2}')
if [ ! -z "$UVICORN_PIDS" ]; then
    echo -e "${YELLOW}发现残留的后端进程，正在清理...${NC}"
    echo $UVICORN_PIDS | xargs kill 2>/dev/null
    echo -e "${GREEN}✓ 后端进程已清理${NC}"
fi

# 停止前端进程 (react-scripts)
REACT_PIDS=$(ps aux | grep "react-scripts start" | grep -v grep | awk '{print $2}')
if [ ! -z "$REACT_PIDS" ]; then
    echo -e "${YELLOW}发现残留的前端进程，正在清理...${NC}"
    echo $REACT_PIDS | xargs kill 2>/dev/null
    echo -e "${GREEN}✓ 前端进程已清理${NC}"
fi

# 停止 node 进程（前端相关）
NODE_PIDS=$(ps aux | grep "node.*frontend" | grep -v grep | awk '{print $2}')
if [ ! -z "$NODE_PIDS" ]; then
    echo -e "${YELLOW}发现残留的 Node 进程，正在清理...${NC}"
    echo $NODE_PIDS | xargs kill 2>/dev/null
    echo -e "${GREEN}✓ Node 进程已清理${NC}"
fi

echo ""
echo "================================"
echo -e "${GREEN}✅ 所有服务已停止${NC}"
echo "================================"
