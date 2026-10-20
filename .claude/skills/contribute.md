# 代码贡献 Skill

## 概述

这个 skill 用于帮助 AI Agent 贡献代码到 Nover 项目。

## 使用方式

在对话中输入 `/contribute` 或 `贡献代码` 来启动代码贡献流程。

## 第一步：阅读项目文档

在开始任何代码修改之前，必须先阅读以下文档来理解项目：

### 必读文档

1. **AGENT.md** - 项目完整文档
   - 包含项目概述、技术栈、核心架构
   - 所有 Agent 的职责和主要方法
   - CLI 命令列表和使用方法
   - 工作流和数据模型说明

2. **README.md** - CLI 使用指南
   - 命令行工具的详细用法
   - 所有命令的参数说明

### 文档位置

```
/Users/keithxi/Documents/work/Nover/AGENT.md
/Users/keithxi/Documents/work/Nover/README.md
```

## 项目结构速览

```
Nover/
├── main.py                      # CLI 入口（Typer + Rich）
├── novel_ai_agent/
│   ├── agents/                  # AI Agent（6个）
│   │   ├── coordinator.py      # 工作流编排
│   │   ├── writer_agent.py    # 章节写作
│   │   ├── outline_agent.py   # 大纲生成
│   │   ├── character_agent.py # 角色生成
│   │   ├── editor_agent.py    # 润色评审
│   │   └── dialogue_agent.py # 对话模式
│   ├── models/                  # 数据模型（Pydantic）
│   ├── prompts/                # Prompt 模板
│   ├── config/                 # 配置
│   └── memory/                 # 记忆系统
├── AGENT.md                    # 项目文档（必读）
└── README.md              # CLI 文档
```

## 修改代码流程

### 1. 理解需求
明确要实现的功能，查看现有实现方式。

### 2. 找到相关文件
- CLI 命令 → main.py
- Agent 逻辑 → novel_ai_agent/agents/
- 数据模型 → novel_ai_agent/models/
- Prompt 模板 → novel_ai_agent/prompts/

### 3. 小步修改
每次只做一件事，保持修改最小化。

### 4. 测试验证
```bash
python3 -m py_compile <修改的文件>
python3 -c "import main"
```

### 5. 提交代码
```bash
git checkout -b feat/your-feature
git add <files>
git commit -m "描述"
git push -u origin feat/your-feature
```

## 注意事项

1. **不要重复文档** - 项目文档在 AGENT.md 和 README.md 中
2. **保持兼容性** - 修改模型时考虑已有数据
3. **遵循规范** - 方法签名和返回格式保持一致

## 需要了解更多信息时

查看：
- AGENT.md - 完整的架构和 API 说明
- README.md - CLI 命令用法
