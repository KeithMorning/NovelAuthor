# 小说AI Agent 系统架构设计

## 项目概述

基于LangChain和多Agent协作模式的AI小说创作系统,支持大纲规划、章节创作、多轮对话修改和作家风格模仿。

## 核心需求

- ✅ 大纲规划与扩展
- ✅ 根据大纲自动生成章节内容
- ✅ 支持多轮对话对特定章节修改
- ✅ 支持设置不同作家风格
- ✅ 小说输出为Markdown格式

## 系统架构

### 多Agent协作架构

```
┌─────────────────────────────────────────────────────────┐
│                  CoordinatorAgent                        │
│              (协调器 - 任务分发与上下文管理)                │
└────────────┬────────────────────────────────────────────┘
             │
    ┌────────┼────────┬────────────┬─────────────┐
    │        │        │            │             │
    ▼        ▼        ▼            ▼             ▼
┌────────┐┌──────┐┌──────────┐┌──────────┐┌──────────┐
│Outline ││Char  ││  Writer  ││  Editor  ││  Memory  │
│ Agent  ││Agent ││  Agent   ││  Agent   ││  System  │
└────────┘└──────┘└──────────┘└──────────┘└──────────┘
```

### Agent职责划分

#### 1. CoordinatorAgent (协调Agent)
**职责**: 主控制器,负责任务分发和流程编排
- 解析用户意图
- 分发任务到各个专业Agent
- 管理全局上下文和状态
- 处理多轮对话逻辑

#### 2. OutlineAgent (大纲规划Agent)
**职责**: 故事结构设计
- 分析故事主题和类型
- 生成完整故事大纲
- 规划章节结构和数量
- 设计主要情节线索和转折点
- 构建情节时间线

**输入**: 故事主题、类型、长度要求
**输出**: 结构化大纲 (Markdown格式)

#### 3. CharacterAgent (角色设定Agent)
**职责**: 人物设定和关系管理
- 创建主要角色档案 (性格、背景、动机)
- 设计角色关系网络
- 规划角色发展弧线
- 维护角色一致性

**输入**: 大纲、故事需求
**输出**: 角色设定文档 (Markdown格式)

#### 4. WriterAgent (写作Agent)
**职责**: 内容创作
- 根据大纲生成章节内容
- 模仿指定作家风格
- 处理对话、描写、叙事等不同写作场景
- 保持前后文连贯性

**输入**: 章节大纲、角色设定、风格要求、前文上下文
**输出**: 章节内容 (Markdown格式)

#### 5. EditorAgent (编辑润色Agent)
**职责**: 质量控制
- 检查内容质量和可读性
- 验证前后一致性 (人物、情节、世界观)
- 提供文笔优化建议
- 检查逻辑漏洞

**输入**: 章节内容、全局上下文
**输出**: 修改建议和润色后的内容

## 技术架构

### 技术栈

| 组件 | 技术选型 | 说明 |
|-----|---------|------|
| LLM | Claude 4 Sonnet | 高质量文本生成,较好的中文支持 |
| Agent框架 | LangChain + LangGraph | 构建复杂Agent工作流 |
| 向量数据库 | Chroma | 轻量级,用于检索相关情节和人物 |
| 记忆系统 | LangChain Memory | 管理长短期记忆 |
| 数据模型 | Pydantic v2 | 类型安全的数据模型 |
| 存储 | JSON + Markdown | 可读性好,易于版本控制 |
| 终端UI | Rich | 美化命令行输出 |

### 项目结构

```
novel_ai_agent/
├── agents/                      # Agent实现
│   ├── __init__.py
│   ├── coordinator.py          # 主协调Agent
│   ├── outline_agent.py        # 大纲规划Agent
│   ├── character_agent.py      # 角色设定Agent
│   ├── writer_agent.py         # 内容创作Agent
│   └── editor_agent.py         # 编辑润色Agent
│
├── tools/                       # Agent工具
│   ├── __init__.py
│   ├── outline_tools.py        # 大纲生成、修改工具
│   ├── writing_tools.py        # 章节创作工具
│   ├── style_tools.py          # 风格迁移工具
│   └── file_tools.py           # 文件读写工具
│
├── memory/                      # 记忆系统
│   ├── __init__.py
│   ├── novel_memory.py         # 小说记忆管理
│   ├── vector_store.py         # 向量数据库封装
│   └── context_manager.py      # 上下文窗口管理
│
├── prompts/                     # Prompt模板
│   ├── __init__.py
│   ├── outline_prompts.py      # 大纲相关prompt
│   ├── character_prompts.py    # 角色设定prompt
│   ├── writing_prompts.py      # 写作prompt
│   └── style_prompts.py        # 风格模仿prompt库
│
├── models/                      # 数据模型
│   ├── __init__.py
│   ├── novel.py                # 小说整体数据结构
│   ├── chapter.py              # 章节模型
│   ├── character.py            # 角色模型
│   └── outline.py              # 大纲模型
│
├── utils/                       # 工具函数
│   ├── __init__.py
│   ├── file_manager.py         # 文件管理 (MD格式)
│   ├── consistency_checker.py  # 一致性检查
│   └── markdown_formatter.py   # Markdown格式化
│
├── config/                      # 配置
│   ├── __init__.py
│   ├── settings.py             # 全局配置
│   └── styles.py               # 作家风格配置
│
├── output/                      # 输出目录
│   ├── novels/                 # 小说MD文件
│   ├── outlines/               # 大纲文件
│   └── characters/             # 角色设定文件
│
├── tests/                       # 测试
│   ├── __init__.py
│   └── test_agents.py
│
├── examples/                    # 示例
│   ├── sample_novel.json       # 示例数据
│   └── sample_outline.md       # 示例大纲
│
├── Doc/                         # 文档
│   ├── architecture.md         # 架构设计 (本文件)
│   ├── user_guide.md          # 使用指南
│   └── api_reference.md       # API参考
│
├── main.py                      # 主入口
├── requirements.txt             # 依赖
├── .env.example                # 环境变量示例
├── .gitignore
└── README.md
```

## 核心工作流

### 1. 初始化流程 (新小说创建)

```
用户输入主题和需求
        ↓
CoordinatorAgent 解析需求
        ↓
OutlineAgent 生成初始大纲
        ↓
CharacterAgent 设定主要角色
        ↓
用户审阅并确认/修改
        ↓
保存大纲和角色设定 (MD格式)
```

### 2. 章节创作流程

```
用户请求创作特定章节
        ↓
CoordinatorAgent 加载上下文
    ├── 读取大纲
    ├── 读取角色设定
    └── 读取前面章节内容 (向量检索)
        ↓
WriterAgent 生成章节初稿
    ├── 应用风格设置
    └── 保持角色一致性
        ↓
EditorAgent 检查和润色
    ├── 一致性检查
    └── 文笔优化
        ↓
输出章节 (Markdown格式)
        ↓
用户审阅
```

### 3. 修改流程 (多轮对话)

```
用户提出修改意见
"第三章的对话太平淡,让角色更有冲突感"
        ↓
CoordinatorAgent 定位目标章节
        ↓
加载相关上下文
        ↓
WriterAgent 重新生成
        ↓
EditorAgent 验证修改
        ↓
更新MD文件
        ↓
显示修改对比
```

## 数据模型设计

### Novel (小说)

```python
class Novel:
    id: str
    title: str
    author_style: str          # 作家风格
    genre: str                 # 类型
    outline: Outline           # 大纲
    characters: List[Character] # 角色列表
    chapters: List[Chapter]    # 章节列表
    metadata: dict             # 元数据
    created_at: datetime
    updated_at: datetime
```

### Outline (大纲)

```python
class Outline:
    summary: str               # 故事简介
    theme: str                 # 主题
    plot_points: List[PlotPoint] # 情节点
    chapters_plan: List[ChapterPlan] # 章节规划
```

### Character (角色)

```python
class Character:
    name: str
    role: str                  # 主角/配角/反派
    personality: str           # 性格
    background: str            # 背景
    motivation: str            # 动机
    relationships: dict        # 与其他角色的关系
    arc: str                   # 角色发展弧线
```

### Chapter (章节)

```python
class Chapter:
    number: int
    title: str
    summary: str               # 章节梗概
    content: str               # 正文 (Markdown)
    word_count: int
    status: str                # draft/reviewed/final
    version: int               # 版本号
    created_at: datetime
    updated_at: datetime
```

## Markdown输出格式

### 小说完整版式

```markdown
# {小说标题}

**作者**: AI创作 (风格: {作家风格})
**类型**: {类型}
**创作日期**: {日期}

---

## 简介

{故事简介}

---

## 角色介绍

### {角色名}
- **角色定位**: {主角/配角/反派}
- **性格**: {性格描述}
- **背景**: {背景故事}

---

## 正文

### 第一章 {章节标题}

{章节内容...}

### 第二章 {章节标题}

{章节内容...}

---

## 创作信息

- **大纲版本**: v1.2
- **总字数**: 50,000
- **章节数**: 20
```

## 记忆系统设计

### 长期记忆 (Long-term Memory)
- **存储内容**: 完整大纲、角色设定、世界观设定
- **实现方式**: 向量数据库 (Chroma) + JSON文件
- **用途**: 检索历史情节、角色信息、保持一致性

### 短期记忆 (Short-term Memory)
- **存储内容**: 当前章节上下文、最近几章内容、当前对话历史
- **实现方式**: LangChain ConversationBufferMemory
- **用途**: 保持当前创作连贯性

### 工作记忆 (Working Memory)
- **存储内容**: 当前任务状态、用户指令、临时数据
- **实现方式**: 内存字典
- **用途**: Agent间信息传递

## 作家风格系统

### 风格配置

```python
WRITER_STYLES = {
    "金庸": {
        "description": "武侠风格,注重江湖恩怨和侠义精神",
        "prompt_template": "...",
        "features": ["丰富的武打描写", "深刻的人物塑造", "历史背景融入"]
    },
    "刘慈欣": {
        "description": "硬科幻,宏大叙事",
        "prompt_template": "...",
        "features": ["科学理论", "宇宙级视野", "冷静的笔触"]
    },
    "东野圭吾": {
        "description": "推理悬疑,人性探讨",
        "prompt_template": "...",
        "features": ["缜密的逻辑", "意外的反转", "人性的灰色地带"]
    },
    # ... 可扩展更多风格
}
```

### 风格应用方式

1. **Prompt工程**: 在WriterAgent的system prompt中注入风格描述
2. **Few-shot示例**: 提供该风格的写作示例
3. **后处理**: 使用EditorAgent调整语言风格

## 依赖包清单

```txt
# LLM和Agent框架
langchain>=0.1.0
langchain-anthropic>=0.1.0
langgraph>=0.0.20
anthropic>=0.18.0

# 向量数据库
chromadb>=0.4.0

# 数据模型和验证
pydantic>=2.0.0
pydantic-settings>=2.0.0

# 工具库
python-dotenv>=1.0.0
rich>=13.0.0              # 终端美化
typer>=0.9.0              # CLI框架

# 文本处理
markdown>=3.5.0
beautifulsoup4>=4.12.0    # MD解析

# 其他
requests>=2.31.0
aiohttp>=3.9.0
```

## 实施计划

### Phase 1: 基础框架 (第1周)
- [ ] 项目结构搭建
- [ ] 基础数据模型定义
- [ ] 配置系统和环境设置
- [ ] Markdown文件读写工具

### Phase 2: 核心Agent开发 (第2-3周)
- [ ] CoordinatorAgent实现
- [ ] OutlineAgent实现
- [ ] CharacterAgent实现
- [ ] WriterAgent基础版本

### Phase 3: 高级功能 (第4周)
- [ ] EditorAgent实现
- [ ] 记忆系统集成
- [ ] 风格系统实现
- [ ] 多轮对话修改功能

### Phase 4: 优化和测试 (第5周)
- [ ] 完整工作流测试
- [ ] 性能优化
- [ ] 用户界面优化
- [ ] 文档完善

## 关键技术难点

1. **上下文窗口管理**: 长篇小说可能超过LLM上下文限制
   - 解决方案: 向量检索 + 摘要技术

2. **角色一致性**: 确保角色在不同章节的行为一致
   - 解决方案: 角色记忆系统 + 定期一致性检查

3. **情节连贯性**: 避免前后矛盾
   - 解决方案: 情节知识图谱 + EditorAgent验证

4. **风格稳定性**: 保持统一的写作风格
   - 解决方案: 风格模板 + Few-shot示例 + 后处理

5. **成本控制**: 长篇创作API调用成本
   - 解决方案: 缓存机制 + 增量生成 + 模型选择策略

## 扩展方向

- 多语言支持
- Web界面
- 协作创作 (多用户)
- 版本管理和分支
- 发布格式转换 (EPUB, PDF等)
- AI插图生成集成

---

**文档版本**: v1.0
**最后更新**: 2026-01-27
**维护者**: Keith Xi
