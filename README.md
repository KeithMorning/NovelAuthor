# 小说AI Agent

基于LangChain和多Agent协作架构的AI小说创作系统,支持大纲规划、章节创作、多轮对话修改和作家风格模仿。

## 特性

- **多Agent协作**: OutlineAgent、CharacterAgent、WriterAgent、EditorAgent等专业Agent协同工作
- **大纲规划**: 自动生成完整的故事大纲和章节规划
- **角色设定**: 智能创建角色档案和关系网络
- **风格模仿**: 支持金庸、刘慈欣、东野圭吾等多种作家风格
- **多轮对话**: 通过对话方式修改和完善小说内容
- **Markdown输出**: 小说以标准Markdown格式输出,易于阅读和编辑
- **一致性检查**: 自动检查角色、情节的前后一致性

## 项目结构

```
novel_ai_agent/
├── agents/          # Agent实现
├── tools/           # Agent工具
├── memory/          # 记忆系统
├── prompts/         # Prompt模板
├── models/          # 数据模型
├── utils/           # 工具函数
├── config/          # 配置文件
└── output/          # 输出目录
    ├── novels/      # 小说MD文件
    ├── outlines/    # 大纲文件
    └── characters/  # 角色设定文件
```

## 快速开始

### 1. 环境准备

确保您已安装Python 3.10+

```bash
# 克隆项目
git clone <repository_url>
cd Nover

# 创建虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置API密钥

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件,填入您的Anthropic API Key
# ANTHROPIC_API_KEY=your_key_here
```

或者使用初始化命令:

```bash
python main.py init
```

### 3. 开始使用

#### 查看可用命令

```bash
python main.py --help
```

#### 查看可用风格

```bash
python main.py styles
```

输出示例:
```
1. 金庸: 武侠风格,注重江湖恩怨和侠义精神,文笔典雅
2. 刘慈欣: 硬科幻风格,宏大叙事,理性冷静的笔触
3. 东野圭吾: 推理悬疑风格,精密的逻辑布局,深入的人性探讨
...
```

#### 创建新小说 (Phase 2功能)

```bash
python main.py create --title "江湖往事" --genre "武侠" --style "金庸"
```

#### 创建大纲 (Phase 2功能)

```bash
python main.py outline --id novel_001 --theme "复仇与救赎"
```

#### 写作章节

```bash
python main.py write --id novel_001 --chapter 1
```

#### 润色章节 (Phase 3功能)

```bash
# 全面润色
python main.py polish --id novel_001 --chapter 1

# 重点润色特定方面
python main.py polish --id novel_001 --chapter 1 --focus "对话,环境描写"
```

#### 评审章节 (Phase 3功能)

```bash
python main.py review --id novel_001 --chapter 1
```

#### 记忆管理 (Phase 3功能)

```bash
# 查看记忆统计
python main.py memory-stats --id novel_001

# 搜索记忆
python main.py search-memory --id novel_001 --query "主角" --type characters
python main.py search-memory --id novel_001 --query "决战" --type plots
```

#### 列出所有小说

```bash
python main.py list-novels
```

#### 一致性检查

```bash
python main.py check --id novel_001
```

#### 导出小说

```bash
# 导出到默认位置
python main.py export --id novel_001

# 导出到指定位置
python main.py export --id novel_001 --output ./my_novel.md
```

#### 交互式创作模式 (Phase 3功能)

```bash
# 启动交互式对话，修改指定小说
python main.py interactive --id novel_001

# 针对特定章节进行对话
python main.py interactive --id novel_001 --chapter 1
```

## 开发计划

### Phase 1: 基础框架 ✅
- [x] 项目结构搭建
- [x] 基础数据模型定义
- [x] 配置系统和环境设置
- [x] Markdown文件读写工具
- [x] CLI命令框架

### Phase 2: 核心Agent开发 ✅
- [x] CoordinatorAgent完整实现
- [x] OutlineAgent实现
- [x] CharacterAgent实现
- [x] WriterAgent基础版本

### Phase 3: 高级功能 ✅
- [x] EditorAgent实现
- [x] 记忆系统集成
- [x] 风格系统完善
- [x] 多轮对话修改功能

### Phase 4: 优化和测试
- [ ] 完整工作流测试
- [ ] 性能优化
- [ ] 用户界面优化
- [ ] 文档完善

## 技术栈

- **LLM**: Claude 4 Sonnet
- **框架**: LangChain + LangGraph
- **向量数据库**: Chroma
- **数据模型**: Pydantic v2
- **CLI**: Typer + Rich
- **语言**: Python 3.10+

## 配置说明

### 环境变量

所有配置项都在`.env`文件中:

| 变量名 | 说明 | 默认值 |
|-------|------|--------|
| ANTHROPIC_API_KEY | Anthropic API密钥 | 必填 |
| DEFAULT_MODEL | 使用的模型 | claude-sonnet-4-20250514 |
| TEMPERATURE | 生成温度 | 0.7 |
| MAX_TOKENS | 最大Token数 | 4096 |
| DEFAULT_CHAPTER_WORDS | 默认章节字数 | 3000 |

### 作家风格

在`novel_ai_agent/config/styles.py`中定义了多种作家风格:

- 金庸: 武侠风格
- 刘慈欣: 硬科幻风格
- 东野圭吾: 推理悬疑风格
- 村上春树: 现代派风格
- 莫言: 魔幻现实主义
- 中性风格: 通用叙事风格

可以根据需要扩展更多风格。

## 数据模型

### Novel (小说)
- 包含完整的小说信息
- 包含大纲、角色、章节列表
- 支持导出为Markdown

### Outline (大纲)
- 故事简介、主题、背景
- 情节点列表
- 章节规划

### Character (角色)
- 角色基本信息
- 性格、背景、动机
- 人物关系网络

### Chapter (章节)
- 章节标题和内容
- 版本控制
- 字数统计

## 输出格式

小说输出为标准Markdown格式:

```markdown
# 小说标题

**作者风格**: 金庸
**类型**: 武侠
**创作日期**: 2026-01-27

---

## 简介

故事简介...

---

## 角色介绍

### 张无忌
- **角色定位**: 主角
- **性格**: 善良正直...

---

## 正文

### 第一章 初遇

章节内容...

---
```

## 使用示例

详细的使用示例请参考`examples/`目录和`Doc/user_guide.md`(待完善)。

## API参考

详细的API文档请参考`Doc/api_reference.md`(待完善)。

## 贡献指南

欢迎贡献代码、报告问题或提出建议!

## 许可证

MIT License

## 联系方式

- 作者: Keith Xi
- 项目文档: `Doc/architecture.md`

---

**当前版本**: v0.3.0 (Phase 3 - 高级功能完成)

**最后更新**: 2026-01-30
