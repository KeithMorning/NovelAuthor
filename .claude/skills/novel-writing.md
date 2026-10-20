# 小说 AI Agent Skill

## 概述

Nover 是一个多 Agent 协作的 AI 写作系统，帮助你规划、写作和修改小说。
通过命令行工具 `python3 main.py` 使用，主要有两种工作流：**批量写作**和**交互式对话**。

---

## 快速开始

### 创建新小说

```bash
python3 main.py create-novel
```

按提示输入标题、类型、故事简介、主题、目标章节数即可。命令执行后会显示 `novel_id`，后续所有操作都用这个 ID。

### 查看已有小说

```bash
python3 main.py list-novels
```

---

## 常用命令

### 写作流程

```bash
# 1. 创建大纲（如果 create-novel 已创建则跳过）
python3 main.py create-outline --id <novel_id>

# 2. 批量写作（所有章节）
python3 main.py write-all --id <novel_id>

# 3. 写单章
python3 main.py write --id <novel_id> --chapter 3

# 4. 细化某章规划（先做这步再写，质量更好）
python3 main.py expand-chapter --id <novel_id> --chapter 3
```

### 对话修改模式（最常用）

```bash
python3 main.py chat --id <novel_id>

# 开启计划模式（修改前先展示计划，确认后再执行）
python3 main.py chat --id <novel_id> --plan
```

**对话内置指令：**

| 指令 | 功能 |
|------|------|
| `/plan` | 切换计划模式（修改前先分析剧情、制定方案） |
| `/clear` | 清除当前对话历史 |
| `/resume` | 恢复上次对话（退出时自动保存） |
| `/help` | 显示所有指令 |

**对话中的自然语言命令示例：**

```
# 修改章节
你> 修改第3章开头，补充李泽言察觉异常的情节

# 局部编辑（更快，只改特定段落）
你> 微调第3章 把那段对话改得更克制

# 先计划后执行（输入计划关键词自动触发）
你> 先计划一下第4章的修改方案

# 大纲修改
你> 修改大纲 调整第5-8章的节奏

# 角色修改
你> 把李泽言改得更有城府一点
```

### 大纲同步

如果你直接编辑了大纲 Markdown 文件，用此命令同步回 JSON：

```bash
python3 main.py sync-outline --id <novel_id>

# 指定文件
python3 main.py sync-outline --id <novel_id> --file /path/to/outline.md
```

### 润色和评审

```bash
# 润色单章
python3 main.py polish --id <novel_id> --chapter 3

# 编辑器评审（给出修改建议）
python3 main.py review --id <novel_id> --chapter 3
```

---

## 输出文件结构

```
novel_ai_agent/output/<novel_id>/
├── novels/
│   ├── <novel_id>.json              # 主数据文件（JSON）
│   ├── <novel_id>_chapter_001.md   # 各章节 Markdown
│   └── <novel_id>_<title>.md       # 完整小说
├── outlines/
│   └── <novel_id>_outline_v1.md    # 大纲（可手动编辑后 sync-outline）
├── characters/
│   └── <novel_id>_characters.md    # 角色设定
└── sessions/
    └── last_session.json            # 上次对话历史（/resume 使用）
```

---

## 修改代码指南

### 文件职责速查

| 需求 | 修改位置 |
|------|---------|
| 新增 CLI 命令 | `main.py` |
| 修改写作逻辑 | `novel_ai_agent/agents/writer_agent.py` |
| 修改大纲/角色逻辑 | `novel_ai_agent/agents/outline_agent.py` / `character_agent.py` |
| 修改对话交互逻辑 | `novel_ai_agent/agents/dialogue_agent.py` |
| 修改 Prompt 模板 | `novel_ai_agent/prompts/` |
| 修改数据模型 | `novel_ai_agent/models/` |

### 验证修改

```bash
# 语法检查
python3 -c "import ast; ast.parse(open('main.py').read()); print('OK')"
python3 -c "import ast; ast.parse(open('novel_ai_agent/agents/dialogue_agent.py').read()); print('OK')"

# 导入测试
python3 -c "from novel_ai_agent.agents.dialogue_agent import DialogueAgent; print('OK')"
```

### 关键架构说明

- **计划模式**：`make_plan()` 读取章节全文，调用 LLM 分析并输出结构化修改方案（不执行），用户确认后再执行
- **Edit Instruction 模式**：`edit_chapter()` 只输出 JSON 编辑指令（insert/replace/delete），`apply_edits()` 在本地 patch 原文，比全文重写快 5-10 倍。修改量过大时自动降级为 `revise_chapter()`
- **Todo 列表**：`TodoDisplay` 类用 `rich.Live` 实时渲染进度，模仿 Claude Code 体验
- **会话隔离**：每次启动 `chat` 调用 `new_session_memory_manager()` 清除旧对话历史，避免跨会话污染

---

## 参考文档

- `AGENT.md` — 完整架构和 API 说明
- `README.md` — 所有 CLI 命令详细用法
