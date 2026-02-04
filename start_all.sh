#!/bin/bash

# 小说 AI 代理系统 - 启动所有服务
# Novel AI Agent - Start All Services

set -e

echo "🚀 启动小说 AI 代理系统..."
echo "================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查是否在项目根目录
if [ ! -f "README.md" ]; then
    echo -e "${RED}❌ 错误: 请在项目根目录运行此脚本${NC}"
    exit 1
fi

# 检查 Python 依赖
echo -e "${BLUE}📦 检查 Python 依赖...${NC}"
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Python 依赖未安装，正在安装...${NC}"
    pip3 install -r requirements.txt
fi

# 检查前端依赖
echo -e "${BLUE}📦 检查前端依赖...${NC}"
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}⚠️  前端依赖未安装，正在安装...${NC}"
    cd frontend
    npm install --legacy-peer-deps
    cd ..
fi

# 检查环境变量
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ 错误: .env 文件不存在${NC}"
    echo "请先创建 .env 文件并配置 ANTHROPIC_API_KEY"
    exit 1
fi

# 启动后端 API
echo ""
echo -e "${GREEN}🔧 启动后端 API 服务...${NC}"
python3 -m uvicorn novel_ai_agent.api.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo -e "${GREEN}✓ 后端 API 已启动 (PID: $BACKEND_PID)${NC}"

# 等待后端启动
echo -e "${BLUE}⏳ 等待后端服务就绪...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1 || curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 后端服务就绪${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}⚠️  后端服务可能还在启动中...${NC}"
    fi
    sleep 1
done

# 启动前端
echo ""
echo -e "${GREEN}🎨 启动前端开发服务器...${NC}"
cd frontend
npm start &
FRONTEND_PID=$!
cd ..
echo -e "${GREEN}✓ 前端服务已启动 (PID: $FRONTEND_PID)${NC}"

# 保存 PID 到文件
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

# 显示访问信息
echo ""
echo "================================"
echo -e "${GREEN}✅ 所有服务启动成功！${NC}"
echo "================================"
echo ""
echo -e "${BLUE}📍 访问地址:${NC}"
echo -e "  • 前端应用:    ${GREEN}http://localhost:3000${NC}"
echo -e "  • 后端 API:    ${GREEN}http://localhost:8000${NC}"
echo -e "  • API 文档:    ${GREEN}http://localhost:8000/docs${NC}"
echo -e "  • WebSocket:   ${GREEN}ws://localhost:8000/ws${NC}"
echo ""
echo -e "${BLUE}📊 进程信息:${NC}"
echo -e "  • 后端 PID:    ${GREEN}$BACKEND_PID${NC}"
echo -e "  • 前端 PID:    ${GREEN}$FRONTEND_PID${NC}"
echo ""
echo -e "${YELLOW}💡 提示:${NC}"
echo "  • 按 Ctrl+C 停止所有服务"
echo "  • 或运行: ./stop_all.sh"
echo ""

# 等待用户中断
trap "echo ''; echo -e '${YELLOW}🛑 正在停止所有服务...${NC}'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; rm -f .backend.pid .frontend.pid; echo -e '${GREEN}✓ 所有服务已停止${NC}'; exit 0" INT TERM

# 保持脚本运行
echo -e "${BLUE}⌛ 服务运行中... (按 Ctrl+C 停止)${NC}"
wait
