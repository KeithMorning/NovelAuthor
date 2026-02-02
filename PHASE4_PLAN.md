# Phase 4 开发计划：Web界面实现

**目标**：将命令行工具升级为功能完整的 Web 应用，提供更好的用户体验。

---

## 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                      前端 (React)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ 小说管理 │  │ 创作界面 │  │ 对话界面 │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────┘
                        ↕ REST API / WebSocket
┌─────────────────────────────────────────────────────────┐
│                   后端 API (FastAPI)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ API路由  │  │ WebSocket│  │ 任务队列 │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────┘
                        ↕
┌─────────────────────────────────────────────────────────┐
│              现有的 Agent 系统 (不变)                    │
│  CoordinatorAgent, WriterAgent, EditorAgent...          │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 4.1: Web后端 API（1-2周）

### 目标
将现有的命令行功能包装成 RESTful API，提供 Web 前端调用。

### 技术选型
- **FastAPI**: 现代、快速的 Python Web 框架
- **Uvicorn**: ASGI 服务器
- **Celery** (可选): 异步任务队列
- **Redis** (可选): 任务队列和缓存

### 主要任务

#### 1. 项目结构搭建
```
novel_ai_agent/
├── api/
│   ├── __init__.py
│   ├── main.py           # FastAPI 应用入口
│   ├── routes/           # API 路由
│   │   ├── novels.py     # 小说相关API
│   │   ├── chapters.py   # 章节相关API
│   │   ├── editing.py    # 编辑相关API
│   │   └── dialogue.py   # 对话相关API
│   ├── schemas/          # Pydantic 模型
│   │   ├── requests.py   # 请求模型
│   │   └── responses.py  # 响应模型
│   ├── dependencies.py   # FastAPI 依赖注入
│   └── websocket.py      # WebSocket 处理
```

#### 2. 核心 API 端点设计

**小说管理 API**
```
POST   /api/novels/create          # 创建小说
GET    /api/novels/list            # 列出所有小说
GET    /api/novels/{novel_id}      # 获取小说详情
DELETE /api/novels/{novel_id}      # 删除小说
GET    /api/novels/{novel_id}/export # 导出小说
```

**章节操作 API**
```
POST   /api/novels/{novel_id}/chapters/{chapter_num}/write   # 写作章节
POST   /api/novels/{novel_id}/chapters/{chapter_num}/polish  # 润色章节
POST   /api/novels/{novel_id}/chapters/{chapter_num}/review  # 评审章节
GET    /api/novels/{novel_id}/chapters/{chapter_num}         # 获取章节内容
```

**风格和配置 API**
```
GET    /api/styles                 # 获取所有风格
GET    /api/styles/{style_name}    # 获取风格详情
POST   /api/styles/recommend       # 推荐风格
```

**记忆系统 API**
```
GET    /api/novels/{novel_id}/memory/stats    # 记忆统计
POST   /api/novels/{novel_id}/memory/search   # 搜索记忆
```

**对话 API**
```
POST   /api/dialogue/start         # 开始对话会话
POST   /api/dialogue/chat          # 发送消息
GET    /api/dialogue/history       # 获取对话历史
```

#### 3. WebSocket 实时通信
```python
# 用于实时显示创作进度
ws://localhost:8000/ws/novels/{novel_id}/write
ws://localhost:8000/ws/dialogue/{session_id}
```

#### 4. 任务进度追踪
```
GET    /api/tasks/{task_id}/status  # 查询任务状态
GET    /api/tasks/{task_id}/result  # 获取任务结果
DELETE /api/tasks/{task_id}         # 取消任务
```

### 实现步骤

1. **安装依赖**
```bash
pip install fastapi uvicorn python-multipart
pip install celery redis  # 可选，用于异步任务
```

2. **创建 FastAPI 应用**
```python
# novel_ai_agent/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Novel AI Agent API",
    version="0.4.0",
    description="AI小说创作系统 API"
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
from .routes import novels, chapters, editing, dialogue
app.include_router(novels.router, prefix="/api", tags=["novels"])
app.include_router(chapters.router, prefix="/api", tags=["chapters"])
app.include_router(editing.router, prefix="/api", tags=["editing"])
app.include_router(dialogue.router, prefix="/api", tags=["dialogue"])
```

3. **实现示例路由**
```python
# novel_ai_agent/api/routes/novels.py
from fastapi import APIRouter, HTTPException
from ..schemas.requests import CreateNovelRequest
from ..schemas.responses import NovelResponse
from ...agents.coordinator import CoordinatorAgent

router = APIRouter()

@router.post("/novels/create", response_model=NovelResponse)
async def create_novel(request: CreateNovelRequest):
    coordinator = CoordinatorAgent()
    result = await coordinator.create_novel_workflow(
        title=request.title,
        genre=request.genre,
        theme=request.theme,
        style=request.style,
        chapter_count=request.chapters
    )

    if result["status"] != "success":
        raise HTTPException(status_code=500, detail=result["message"])

    return result
```

### 测试
```bash
# 启动服务器
uvicorn novel_ai_agent.api.main:app --reload --port 8000

# 访问 API 文档
open http://localhost:8000/docs
```

---

## Phase 4.2: Web前端界面（2-3周）

### 目标
构建现代化的 Web 界面，提供直观的小说创作体验。

### 技术选型

**方案A: React (推荐)**
- **React 18**: 现代化的前端框架
- **TypeScript**: 类型安全
- **Ant Design / Material-UI**: UI 组件库
- **React Query**: 数据获取和状态管理
- **React Router**: 路由管理
- **Monaco Editor**: 代码/文本编辑器

**方案B: Vue 3 (备选)**
- **Vue 3**: 渐进式框架
- **TypeScript**: 类型安全
- **Element Plus**: UI 组件库
- **Pinia**: 状态管理
- **Vue Router**: 路由管理

### 页面设计

#### 1. 首页 / 小说列表
```
┌─────────────────────────────────────────────────────────┐
│  Novel AI Agent                    [+ 创建新小说]       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  🔍 搜索小说...                  [风格筛选▼] [状态▼]   │
│                                                          │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │ 📖 江湖往事      │  │ 📖 星际流浪      │            │
│  │ 金庸 | 武侠      │  │ 刘慈欣 | 科幻    │            │
│  │ 10/20 章完成     │  │ 5/15 章完成      │            │
│  │ [继续写作] [编辑]│  │ [继续写作] [编辑]│            │
│  └──────────────────┘  └──────────────────┘            │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

#### 2. 创建小说向导
```
┌─────────────────────────────────────────────────────────┐
│  创建新小说                       [1/3 基本信息]        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  小说标题: [____________________]                       │
│                                                          │
│  类型:     [武侠 ▼]                                     │
│                                                          │
│  风格:     ○ 金庸  ○ 古龙  ○ 刘慈欣  ○ 东野圭吾      │
│           ○ 村上春树  ○ 其他...                        │
│                                                          │
│  章节数:   [___] 章                                     │
│                                                          │
│  主题描述:                                              │
│  ┌───────────────────────────────────────────┐         │
│  │                                           │         │
│  │                                           │         │
│  └───────────────────────────────────────────┘         │
│                                                          │
│                         [上一步]  [下一步 →]            │
└─────────────────────────────────────────────────────────┘
```

#### 3. 小说工作台
```
┌─────────────────────────────────────────────────────────┐
│  江湖往事  [保存] [导出] [设置]                         │
├──────────┬──────────────────────────────────────────────┤
│          │                                               │
│ 📋 大纲  │  第一章 初入江湖                              │
│          │  ┌─────────────────────────────────────┐     │
│ 👥 角色  │  │ 清晨，少年张无忌站在山巅...          │     │
│          │  │                                     │     │
│ 📖 章节  │  │ [编辑器内容区域]                    │     │
│  ├ 1. ✅│  │                                     │     │
│  ├ 2. ✅│  │                                     │     │
│  ├ 3. 📝│  │                                     │     │
│  ├ 4. ⏳│  │                                     │     │
│  └ 5. ⏳│  │                                     │     │
│          │  └─────────────────────────────────────┘     │
│ 💬 对话  │                                               │
│          │  [✨ AI 助手] [🔄 润色] [⭐ 评审]            │
│ 🧠 记忆  │                                               │
│          │  字数: 3240  字                               │
└──────────┴───────────────────────────────────────────────┘
```

#### 4. 交互对话界面
```
┌─────────────────────────────────────────────────────────┐
│  AI 创作助手                              [关闭对话]     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  👤 你: 帮我把第三段改得更有紧张感                      │
│                                                          │
│  🤖 助手: 好的，我来帮你修改。第三段目前是这样的...    │
│         我建议可以这样改：                              │
│         [显示修改建议]                                  │
│         是否应用这个修改？                              │
│         [应用修改] [继续调整]                           │
│                                                          │
│  👤 你: 应用修改                                        │
│                                                          │
│  🤖 助手: ✅ 已应用修改。还有其他需要调整的吗？        │
│                                                          │
├─────────────────────────────────────────────────────────┤
│  💬 [输入消息...]                              [发送 →]│
└─────────────────────────────────────────────────────────┘
```

#### 5. 章节评审界面
```
┌─────────────────────────────────────────────────────────┐
│  章节评审 - 第3章                                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  综合评分: ⭐ 8.5/10                                    │
│                                                          │
│  📊 分项评分                                            │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━           │
│  文字质量      ████████░░ 9.0                          │
│  风格一致性    ████████░░ 8.0                          │
│  情节逻辑      █████████░ 8.5                          │
│  角色一致性    █████████░ 9.0                          │
│  叙事节奏      ████████░░ 8.0                          │
│  情感表达      █████████░ 8.5                          │
│                                                          │
│  ✅ 优点                                                │
│  • 环境描写生动，渲染到位                              │
│  • 对话自然流畅                                        │
│  • 情节推进合理                                        │
│                                                          │
│  ⚠️ 需要改进                                           │
│  • 第5段节奏略慢，可以精简                             │
│  • 结尾转折可以更自然一些                              │
│                                                          │
│             [接受评审] [忽略] [查看详细建议]            │
└─────────────────────────────────────────────────────────┘
```

### 核心功能组件

#### 1. 小说编辑器
```typescript
interface NovelEditorProps {
  novelId: string;
  chapterNumber: number;
  content: string;
  onSave: (content: string) => void;
}

// 使用 Monaco Editor 或 Slate
const NovelEditor: React.FC<NovelEditorProps> = ({ ... }) => {
  // 实时保存
  // 语法高亮
  // 字数统计
  // 版本对比
}
```

#### 2. AI 对话组件
```typescript
interface DialogueProps {
  novelId: string;
  chapterNumber?: number;
  onMessageSent: (message: string) => void;
}

const Dialogue: React.FC<DialogueProps> = ({ ... }) => {
  // WebSocket 连接
  // 消息显示
  // 实时输入
  // 操作确认
}
```

#### 3. 创作进度指示器
```typescript
interface ProgressProps {
  totalChapters: number;
  completedChapters: number;
  currentTask?: string;
}

const CreationProgress: React.FC<ProgressProps> = ({ ... }) => {
  // 进度条
  // 当前状态
  // 预计完成时间
}
```

### 状态管理

使用 React Query 管理服务器状态：
```typescript
// hooks/useNovels.ts
export const useNovels = () => {
  return useQuery(['novels'], fetchNovels);
};

export const useNovel = (novelId: string) => {
  return useQuery(['novels', novelId], () => fetchNovel(novelId));
};

export const useCreateNovel = () => {
  const queryClient = useQueryClient();

  return useMutation(createNovel, {
    onSuccess: () => {
      queryClient.invalidateQueries(['novels']);
    }
  });
};
```

### 实现步骤

1. **创建 React 项目**
```bash
cd novel_ai_agent
npx create-react-app frontend --template typescript
cd frontend
npm install @tanstack/react-query antd axios react-router-dom
```

2. **配置 API 客户端**
```typescript
// src/api/client.ts
import axios from 'axios';

export const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  }
});
```

3. **实现页面和组件**
按照上面的设计实现各个页面

---

## Phase 4.3: 高级功能（1-2周）

### 1. 实时创作进度
- WebSocket 推送创作状态
- 进度百分比显示
- 预计完成时间
- 可取消操作

### 2. 章节版本管理
- 保存多个版本
- 版本对比（diff 显示）
- 版本回退
- 版本合并

### 3. 角色关系图
- 使用 D3.js 或 vis.js
- 可视化角色关系
- 交互式节点编辑
- 导出为图片

### 4. 大纲思维导图
- 使用 react-mindmap 或类似库
- 可拖拽编辑
- 折叠/展开节点
- 导出功能

---

## Phase 4.4: 性能优化（1周）

### 1. 批量章节生成
```python
@router.post("/novels/{novel_id}/chapters/batch")
async def write_chapters_batch(
    novel_id: str,
    chapter_range: tuple[int, int]
):
    # 使用 Celery 异步执行
    # 返回任务ID
    pass
```

### 2. 缓存机制
- Redis 缓存常用数据
- 浏览器端缓存
- API 响应缓存

### 3. 数据库优化
- 索引优化
- 查询优化
- 连接池管理

---

## Phase 4.5: 测试和部署（1周）

### 1. 测试
```bash
# 后端测试
pytest novel_ai_agent/api/tests/

# 前端测试
cd frontend
npm test
```

### 2. Docker 容器化
```dockerfile
# Dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "novel_ai_agent.api.main:app", "--host", "0.0.0.0"]
```

### 3. Docker Compose
```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

---

## 开发时间线

| 阶段 | 任务 | 预计时间 | 优先级 |
|------|------|----------|--------|
| 4.1 | 后端 API 基础框架 | 3天 | P0 |
| 4.1 | 核心 API 端点 | 4天 | P0 |
| 4.1 | WebSocket 实时通信 | 3天 | P1 |
| 4.2 | 前端项目搭建 | 2天 | P0 |
| 4.2 | 小说列表和创建 | 3天 | P0 |
| 4.2 | 编辑器界面 | 5天 | P0 |
| 4.2 | 对话界面 | 4天 | P1 |
| 4.3 | 高级功能 | 7天 | P2 |
| 4.4 | 性能优化 | 5天 | P2 |
| 4.5 | 测试和部署 | 5天 | P1 |

**总计：约 6-8 周**

---

## 下一步行动

### 立即开始（本周）
1. ✅ 创建 Phase 4 计划文档（完成）
2. ⏳ 安装 FastAPI 和相关依赖
3. ⏳ 创建基础的 API 项目结构
4. ⏳ 实现第一个 API 端点（小说列表）

### 第一周目标
- 完成后端 API 基础框架
- 实现小说管理相关的 API
- API 文档自动生成（Swagger UI）

### 第二周目标
- 完成前端项目搭建
- 实现小说列表和创建界面
- 前后端联调

---

**准备好开始 Phase 4.1 了吗？** 🚀
