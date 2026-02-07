# 小说 AI 代理系统 (Novel AI Agent)

<div align="center">

**基于多 Agent 架构的智能小说创作系统**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[快速开始](#快速开始) • [功能特性](#功能特性) • [文档](#文档索引) • [API 文档](#api-文档) • [架构](#系统架构)

</div>

---

## 📖 项目简介

Novel AI Agent 是一个完整的 AI 辅助小说创作系统，从创意到成品，提供全流程自动化支持：

- 🎨 **智能大纲生成** - 输入创意，AI 自动生成完整故事结构
- ✍️ **自动章节创作** - 基于大纲和记忆系统自动写作
- ✨ **智能润色评审** - AI 提升文本质量并提供专业建议
- 🎭 **风格模仿** - 支持金庸、刘慈欣等多种作家风格
- 🧠 **记忆系统** - 基于向量数据库的语义记忆，保持故事连贯性
- 🌐 **Web 界面** - 现代化的 Web 应用，实时进度显示
- 📝 **专业编辑器** - Monaco Editor，VS Code 级别的编辑体验

---

## 🚀 快速开始

### 方式 1: Web 应用（推荐）

适合大多数用户，提供友好的图形界面。

#### 1. 启动后端服务

```bash
# 克隆项目
git clone <repository_url>
cd Nover

# 安装 Python 依赖
pip3 install -r requirements.txt

# 配置 API Key
cp .env.example .env
# 编辑 .env 文件，填入 ANTHROPIC_API_KEY

# 启动后端 API
./start_api.sh
# 或者手动启动: python -m uvicorn novel_ai_agent.api.main:app --host 0.0.0.0 --port 8000
```

后端 API 将运行在 http://localhost:8000

#### 2. 启动前端界面

```bash
# 进入前端目录
cd frontend

# 安装依赖（首次运行）
npm install

# 启动开发服务器
npm start
```

前端应用将自动打开 http://localhost:3000

#### 3. 开始创作

1. 在首页点击"创建新小说"
2. 填写小说信息（标题、类型、主题、风格、章节数）
3. 等待 AI 生成大纲（30-60秒）
4. 查看生成的角色和情节设计
5. 点击"开始写作第1章"
6. 在编辑器中查看、修改、润色章节

**详细使用指南**: [前端使用指南](FRONTEND_SETUP.md)

---

### 方式 2: 命令行工具

适合开发者和自动化场景。

#### 安装和配置

```bash
# 安装依赖
pip3 install -r requirements.txt

# 配置 API Key
python main.py init
```

#### 基本命令

```bash
# 查看所有命令
python main.py --help

# 查看可用风格
python main.py styles

# 创建新小说
python main.py create --title "星际迷航" --genre "科幻" --style "刘慈欣"

# 生成大纲
python main.py outline --id novel_001 --theme "人类探索宇宙的故事"

# 写作章节
python main.py write --id novel_001 --chapter 1

# 润色章节
python main.py polish --id novel_001 --chapter 1

# 评审章节
python main.py review --id novel_001 --chapter 1

# 导出小说
python main.py export --id novel_001

# 中断继续
python main.py resume --id novel_001
```




**详细命令文档**: [CLI 使用指南](Doc/cli_guide.md)

---

## ✨ 功能特性

### 核心功能

| 功能 | 说明 | 状态 |
|------|------|------|
| 🎨 **智能大纲生成** | 基于主题自动生成故事结构、角色设定、情节设计 | ✅ |
| ✍️ **自动章节创作** | AI 根据大纲和上下文自动写作章节内容 | ✅ |
| 🎭 **风格模仿** | 模仿金庸、刘慈欣、东野圭吾等作家风格 | ✅ |
| ✨ **智能润色** | 三种强度润色：轻度/中度/重度 | ✅ |
| 📊 **专业评审** | 多维度评分和详细改进建议 | ✅ |
| 🧠 **记忆系统** | 向量数据库存储角色、情节、章节记忆 | ✅ |
| 🌐 **Web 界面** | 现代化 React 应用，实时进度显示 | ✅ |
| 📝 **专业编辑器** | Monaco Editor，自动保存，实时统计 | ✅ |
| ⚡ **实时通信** | WebSocket 推送进度和任务状态 | ✅ |

### AI Agents

系统包含 4 个专业 AI Agent，协同工作：

- **OutlineAgent** - 大纲规划专家
  - 生成故事结构和章节规划
  - 创建角色设定和关系网络
  - 设计情节点和故事走向

- **WriterAgent** - 内容创作专家
  - 基于大纲自动写作章节
  - 维护故事连贯性和风格一致性
  - 生成高质量的叙事内容

- **EditorAgent** - 编辑润色专家
  - 章节润色和文字优化
  - 多维度质量评审
  - 提供专业改进建议

- **DialogueAgent** - 对话生成专家
  - 生成符合角色性格的对话
  - 优化对话的自然度和戏剧性

### Web 应用功能

#### 前端界面
- 📋 **小说列表** - 卡片式展示，实时刷新
- 📖 **小说详情** - 章节/角色/情节标签页
- ✏️ **章节编辑器** - Monaco Editor，自动保存
- 🎨 **润色和评审** - 可视化操作和结果展示
- 📊 **实时进度** - WebSocket 实时推送
- 📱 **响应式设计** - 适配移动端和桌面端

#### 后端 API
- 16 个 RESTful API 端点
- WebSocket 实时通信
- Swagger UI 交互式文档
- 完整的错误处理和验证

**详细功能文档**: [功能清单](PHASE4_FRONTEND_STATUS.md#功能特性总结)

---

## 📚 文档索引

> 所有详细文档已整理到 **[docs/](docs/)** 目录

### 核心文档（必读）⭐⭐⭐⭐⭐
- **[AI 快速上手](docs/AI_QUICK_START.md)** - AI助手5分钟快速理解 🤖
- **[完整文档索引](docs/DOCUMENTATION_INDEX.md)** - 所有文档导航
- **[项目最终状态](docs/PROJECT_STATUS_FINAL.md)** - 完整项目报告

### API 文档
- **[API 使用指南](docs/API_GUIDE.md)** - 完整API文档（13个端点）
- **[WebSocket 指南](docs/WEBSOCKET_GUIDE.md)** - WebSocket使用和示例
- **[Swagger UI](http://localhost:8000/docs)** - 交互式API文档（需启动后端）
- **[ReDoc](http://localhost:8000/redoc)** - 文档风格（需启动后端）

### 开发文档
- **[前端设置指南](docs/FRONTEND_SETUP.md)** - 前端项目完整设置
- **[系统架构](Doc/architecture.md)** - 技术架构和设计决策

### 更多文档
查看 **[docs/](docs/)** 目录获取完整文档列表，包括：
- Phase 完成报告
- 测试结果文档
- 开发状态报告

### 对 AI 特别友好的文档 🤖
**推荐AI助手阅读顺序**：

1. **[AI 快速上手](docs/AI_QUICK_START.md)** ⭐ 5分钟快速理解
   - 项目30秒速览
   - 文档阅读优先级
   - 项目结构速览
   - 核心概念
   - 常见任务

2. **[完整文档索引](docs/DOCUMENTATION_INDEX.md)** ⭐ 完整导航
   - 文档分类索引
   - 依赖关系图
   - 按角色推荐路径
   - 按主题查找

3. **[项目最终状态](docs/PROJECT_STATUS_FINAL.md)** ⭐ 深入理解
   - 完整的项目概览
   - 系统架构图
   - 功能清单
   - 技术栈详解
   - 代码统计

---

## 🏗️ 系统架构

### 技术栈

**后端**
```
Python 3.11+
├── FastAPI          - Web 框架
├── Pydantic v2      - 数据验证
├── ChromaDB         - 向量数据库
├── OpenAI API       - LLM 接口
└── WebSocket        - 实时通信
```

**前端**
```
React 18 + TypeScript
├── Chakra UI 2.8    - UI 组件库
├── React Query 5.x  - 数据管理
├── React Router 7.x - 路由管理
├── Axios            - HTTP 客户端
├── Monaco Editor    - 代码编辑器
└── WebSocket        - 实时通信
```

### 架构图

```
┌─────────────────────────────────────────────┐
│            Frontend (React)                  │
│  ┌────────────┐  ┌────────────┐             │
│  │  列表页面  │  │ 详情页面   │             │
│  └────────────┘  └────────────┘             │
│  ┌────────────┐  ┌────────────┐             │
│  │  编辑器    │  │  实时进度  │             │
│  └────────────┘  └────────────┘             │
└─────────────────────────────────────────────┘
                  ↕ HTTP/WebSocket
┌─────────────────────────────────────────────┐
│         Backend API (FastAPI)               │
│  ┌────────────┐  ┌────────────┐             │
│  │ 小说 API   │  │ 章节 API   │             │
│  └────────────┘  └────────────┘             │
│  ┌────────────┐  ┌────────────┐             │
│  │ WebSocket  │  │ 风格 API   │             │
│  └────────────┘  └────────────┘             │
└─────────────────────────────────────────────┘
                  ↕ 调用
┌─────────────────────────────────────────────┐
│          Agent System                        │
│  ┌─────────────┐  ┌─────────────┐           │
│  │OutlineAgent │  │ WriterAgent │           │
│  └─────────────┘  └─────────────┘           │
│  ┌─────────────┐  ┌─────────────┐           │
│  │EditorAgent  │  │DialogueAgent│           │
│  └─────────────┘  └─────────────┘           │
└─────────────────────────────────────────────┘
                  ↕ 使用
┌─────────────────────────────────────────────┐
│         Core Systems                         │
│  ┌─────────────┐  ┌─────────────┐           │
│  │ 记忆系统    │  │ 向量存储    │           │
│  └─────────────┘  └─────────────┘           │
│  ┌─────────────┐  ┌─────────────┐           │
│  │ 文件管理    │  │ 风格系统    │           │
│  └─────────────┘  └─────────────┘           │
└─────────────────────────────────────────────┘
```

**详细架构文档**: [系统架构](Doc/architecture.md)

---

## 📂 项目结构

```
Nover/
├── novel_ai_agent/          # 核心 Python 包
│   ├── agents/              # AI Agent 实现
│   │   ├── outline_agent.py     # 大纲生成
│   │   ├── writer_agent.py      # 章节写作
│   │   ├── editor_agent.py      # 润色评审
│   │   └── dialogue_agent.py    # 对话生成
│   ├── api/                 # FastAPI 后端
│   │   ├── main.py             # 应用入口
│   │   ├── routes/             # API 路由
│   │   │   ├── novels.py       # 小说 API
│   │   │   ├── chapters.py     # 章节 API
│   │   │   ├── styles.py       # 风格 API
│   │   │   └── websocket.py    # WebSocket
│   │   └── websocket.py        # WebSocket 管理器
│   ├── memory/              # 记忆系统
│   │   ├── vector_store.py     # 向量数据库
│   │   └── memory_manager.py   # 记忆管理
│   ├── storage/             # 存储系统
│   │   └── file_manager.py     # 文件管理
│   ├── config/              # 配置
│   │   └── styles.py           # 风格定义
│   └── models/              # 数据模型
│       └── novel.py            # Novel/Chapter 模型
├── frontend/                # React 前端
│   ├── src/
│   │   ├── api/                # API 客户端
│   │   ├── components/         # UI 组件
│   │   │   ├── NovelCard.tsx       # 小说卡片
│   │   │   ├── ChapterEditor.tsx   # 编辑器
│   │   │   └── ProgressMonitor.tsx # 进度监控
│   │   ├── pages/              # 页面组件
│   │   │   ├── HomePage.tsx        # 首页
│   │   │   ├── NovelDetailPage.tsx # 详情页
│   │   │   └── ChapterPage.tsx     # 编辑页
│   │   ├── hooks/              # 自定义 Hooks
│   │   ├── contexts/           # Context
│   │   └── types/              # TypeScript 类型
│   └── package.json
├── output/                  # 输出目录
│   ├── novels/             # 小说文件
│   └── chroma/             # 向量数据库
├── main.py                 # CLI 入口
├── start_api.sh            # 后端启动脚本
├── requirements.txt        # Python 依赖
├── .env                    # 环境变量
└── README.md               # 本文件
```

---

## 🔧 配置说明

### 环境变量

所有配置在 `.env` 文件中：

```bash
# API 密钥（必填）
ANTHROPIC_API_KEY=your_key_here

# 模型配置
DEFAULT_MODEL=claude-sonnet-4-20250514
TEMPERATURE=0.7
MAX_TOKENS=4096

# 创作配置
DEFAULT_CHAPTER_WORDS=3000
```

### 作家风格

系统预置了多种作家风格：

| 风格 | 特点 | 适用类型 |
|------|------|----------|
| 金庸 | 武侠风格，注重江湖恩怨和侠义精神 | 武侠 |
| 刘慈欣 | 硬科幻，宏大叙事，理性冷静 | 科幻 |
| 东野圭吾 | 推理悬疑，精密逻辑，人性探讨 | 推理、悬疑 |
| 村上春树 | 现代派，孤独感，魔幻现实 | 现代、文艺 |
| 莫言 | 魔幻现实主义，乡土气息 | 历史、乡土 |
| 中性风格 | 通用叙事风格 | 所有类型 |

可在 `novel_ai_agent/config/styles.py` 中扩展更多风格。

---

## 📊 项目状态

### 开发进度

| Phase | 任务 | 状态 |
|-------|------|------|
| Phase 1 | 基础框架搭建 | ✅ 100% |
| Phase 2 | 核心 Agent 开发 | ✅ 100% |
| Phase 3 | 高级功能（记忆、对话） | ✅ 100% |
| Phase 4.1 | 后端 API + WebSocket | ✅ 100% |
| Phase 4.2 | 前端界面 + 编辑器 | ✅ 100% |

**总体完成度**: ✅ 100%

### 统计数据

- **代码文件**: 47 个
- **代码行数**: ~6,500 行
- **API 端点**: 13 个 RESTful + 1 个 WebSocket
- **前端组件**: 22 个
- **文档页数**: 11 个主要文档

### 服务状态

访问 http://localhost:8000/docs 查看 API 健康状态

---

## 🎯 使用场景

### 1. 个人创作者
- 快速搭建故事框架
- AI 辅助内容创作
- 保持故事连贯性

### 2. 网文作者
- 批量生成章节内容
- 风格模仿和学习
- 提升创作效率

### 3. 创作工作室
- 多人协作创作
- 标准化创作流程
- 质量控制和评审

### 4. 学习研究
- 了解 AI 写作技术
- 研究多 Agent 协作
- 学习全栈开发

---

## 🐛 已知限制

1. **LLM 依赖**: 需要 Anthropic API Key，存在 API 调用成本
2. **中文优化**: 主要针对中文小说创作优化
3. **创作速度**: 章节生成需要 30-90 秒（取决于长度）
4. **记忆容量**: ChromaDB 性能随数据量增长而下降

---

## 🔮 未来计划

### 短期（可选）
- [ ] 完善 WebSocket 结果接收
- [ ] 实现并排对比视图
- [ ] 添加搜索和过滤功能
- [ ] 批量操作章节

### 中期（扩展）
- [ ] 用户系统和认证
- [ ] 多小说项目管理
- [ ] 版本历史和回退
- [ ] 导出为 EPUB/PDF

### 长期（愿景）
- [ ] 多人协作创作
- [ ] AI 风格训练
- [ ] 出版流程集成
- [ ] 移动端 APP

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

### 贡献方式
1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 开发指南
- 遵循项目代码风格
- 添加必要的单元测试
- 更新相关文档

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 👥 联系方式

- **作者**: Keith Xi
- **项目主页**: [GitHub Repository](https://github.com/your-repo)
- **问题反馈**: [Issues](https://github.com/your-repo/issues)
- **技术文档**: [Documentation](Doc/)

---

## 🙏 致谢

- [Anthropic](https://www.anthropic.com/) - Claude API
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [React](https://reactjs.org/) - 前端框架
- [ChromaDB](https://www.trychroma.com/) - 向量数据库
- [Monaco Editor](https://microsoft.github.io/monaco-editor/) - 代码编辑器

---

## 📈 项目信息

**当前版本**: v1.0.0
**最后更新**: 2026-02-03
**状态**: ✅ 生产就绪

---

<div align="center">

**🎉 所有核心功能已完成！开始您的 AI 创作之旅吧！**

[立即开始](#快速开始) • [查看文档](#文档索引) • [访问 API](http://localhost:8000/docs)

</div>
