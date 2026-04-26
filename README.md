# Nover CLI - 命令行小说创作工具

基于多 Agent 架构的 AI 小说创作系统。

## 快速开始

```bash
# 安装依赖
pip3 install -r requirements.txt

# 初始化配置
python3 main.py init

# 创建小说
python3 main.py create --title "我的小说" --genre "科幻" --theme "AI觉醒"

# 一键自动创作（创建 + 写完全部章节）
python3 main.py create --title "我的小说" --genre "科幻" --theme "AI觉醒" --auto

# 查看帮助
python3 main.py --help
```

## 命令列表

### 小说管理

| 命令 | 说明 |
|------|------|
| `create` | 创建新小说（含大纲和角色），支持 `--auto` 自动写完所有章节 |
| `list-novels` | 列出所有小说 |
| `check` | 检查小说内容一致性 |
| `export` | 导出为 Markdown |
| `resume` | 从中断继续创作 |

### 章节创作

| 命令 | 说明 |
|------|------|
| `write` | 写作单个章节 |
| `write-all` | 批量写作全部章节 |
| `polish` | 润色章节 |
| `review` | 评审章节 |
| `interactive` | 交互式创作模式 |

### 修改功能

| 命令 | 说明 |
|------|------|
| `edit-outline` | 修改大纲 |
| `edit-character` | 修改角色 |
| `expand-chapters` | 批量细化章节规划 |

### 其他

| 命令 | 说明 |
|------|------|
| `styles` | 列出所有写作风格 |
| `style-info` | 查看风格详情 |
| `version` | 显示版本 |

## 详细用法

### create - 创建小说

```bash
# 基础创建
python3 main.py create \
  --title "时空守护者" \
  --genre "科幻" \
  --theme "量子物理学家发现平行宇宙"

# 完整参数示例
python3 main.py create \
  --title "时空守护者" \
  --genre "科幻" \
  --theme "量子物理学家发现平行宇宙" \
  --style "刘慈欣" \
  --chapters 15 \
  --interactive

# 一键自动创作（创建后自动写完所有章节）
python3 main.py create \
  --title "我的小说" \
  --genre "科幻" \
  --theme "AI觉醒" \
  --auto
```

**参数**:
- `--title, -t`: 小说标题（必填）
- `--genre, -g`: 小说类型（必填）
- `--theme`: 故事主题（必填）
- `--style, -s`: 作家风格（默认：中性风格）
- `--chapters, -n`: 章节数量（默认：20）
- `--requirements, -r`: 额外需求
- `--interactive, -i`: 创建后进入交互式对话模式
- `--auto, -a`: 创建后自动按顺序写完所有章节

### write - 写作章节

```bash
# 基础写作
python3 main.py write --id <novel_id> --chapter 1

# 写完后自动评审
python3 main.py write --id <novel_id> --chapter 1 --review

# 写完后进入交互式对话模式
python3 main.py write --id <novel_id> --chapter 1 --interactive

# 强制重写已存在章节
python3 main.py write --id <novel_id> --chapter 1 --force
```

**参数**:
- `--id, -i`: 小说ID（必填）
- `--chapter, -c`: 章节编号（必填）
- `--expand/--no-expand`: 是否启用章节规划细化（默认启用）
- `--review/--no-review`: 写完后是否自动评审（默认否）
- `--force, -f`: 强制重写已存在章节
- `--interactive`: 写完后进入交互式对话模式

### write-all - 批量写作

```bash
# 写作所有章节
python3 main.py write-all --id <novel_id>

# 从第5章开始（断点恢复）
python3 main.py write-all --id <novel_id> --start 5

# 全部写完后进入交互式模式
python3 main.py write-all --id <novel_id> --interactive
```

**参数**:
- `--id, -i`: 小说ID（必填）
- `--start, -s`: 起始章节号（默认：1）
- `--expand/--no-expand`: 是否启用章节规划细化
- `--force, -f`: 强制重写已存在章节
- `--interactive`: 全部写完后进入交互式对话模式

### interactive - 交互式模式

```bash
# 启动交互式模式
python3 main.py interactive --id <novel_id>

# 指定当前章节
python3 main.py interactive --id <novel_id> --chapter 3
```

**参数**:
- `--id, -i`: 小说ID（必填）
- `--chapter, -c`: 起始章节编号（可选）

### edit-outline - 修改大纲

```bash
# 修改整体大纲
python3 main.py edit-outline --id <novel_id> --feedback "增加更多悬疑反转"

# 修改特定章节
python3 main.py edit-outline --id <novel_id> --feedback "第3章需要更激烈冲突" --chapter 3
```

**参数**:
- `--id, -i`: 小说ID（必填）
- `--feedback, -f`: 修改意见（必填）
- `--chapter, -c`: 指定章节号（可选）

### edit-character - 修改角色

```bash
# 指定角色名修改
python3 main.py edit-character --id <novel_id> --name "林思远" --feedback "个人特点改成更合理的"

# 从反馈中自动分析角色名
python3 main.py edit-character --id <novel_id> --feedback "林思远的个人特点改成更合理的"
```

**参数**:
- `--id, -i`: 小说ID（必填）
- `--name, -n`: 角色名（可选，不指定则从反馈中分析）
- `--feedback, -f`: 修改意见（必填）

**输出**: 自动展示修改前后的对比（性格、背景、动机、个人特点、技能）

### expand-chapters - 细化章节规划

```bash
# 细化所有章节规划
python3 main.py expand-chapters --id <novel_id>

# 只细化前3章
python3 main.py expand-chapters --id <novel_id> --chapters 1-3
```

**参数**:
- `--id, -i`: 小说ID（必填）
- `--chapters`: 章节范围，如 "1-5"（可选）

### 其他命令

```bash
# 列出所有小说
python3 main.py list-novels

# 导出小说
python3 main.py export --id <novel_id> --output ./my_novel.md

# 润色章节
python3 main.py polish --id <novel_id> --chapter 1

# 评审章节
python3 main.py review --id <novel_id> --chapter 1

# 查看风格
python3 main.py styles

# 风格推荐
python3 main.py recommend-style --genre "科幻"
```

## 交互式模式

在交互式模式下，你可以用自然语言表达修改需求，AI会自动理解意图并选择合适的工具执行：

- **细化章节**: 输入 "细化第3章" 或 "把第3章展开详细规划"
- **修改大纲**: 输入 "修改大纲，调整故事走向" 或 "这个结局不太满意"
- **修改角色**: 输入 "林思远的个人特点改成更合理的" 或 "反派太弱了，改得更聪明"
- **重新设计角色**: 输入 "反派变强了，需要调整和他的对抗关系"（影响多人时）
- **重写章节**: 输入 "修改第5章，让冲突更激烈" 或 "重写第3章"
- **局部修改**: 输入 "把第3章的'卫离'改成'卫长官'"
- **润色章节**: 输入 "润色第2章"
- **计划模式**: 输入 "先计划：如何让故事更有张力"

AI会自动识别你的意图并选择合适的工具执行。输入 "quit" 或 "exit" 退出对话。

**注意**: 角色特点会符合小说风格（如科幻风格不会出现"收集旧钢笔"），配角不需要刻意添加特点。

## 配置

在 `.env` 文件中配置：

```bash
# API 密钥
DEEPSEEK_API_KEY=your_key_here

# 或使用 Anthropic
ANTHROPIC_API_KEY=your_key_here

# 模型配置
DEFAULT_MODEL=deepseek-chat
MAX_TOKENS=8000
DEFAULT_CHAPTER_WORDS=4000
```

## 作家风格

可用风格：`中性风格`、`金庸`、`刘慈欣`、`东野圭吾`、`村上春树`、`莫言` 等。

## 输出目录

- 小说 JSON: `novels/<novel_id>.json`
- 章节文件: `output/novels/<novel_id>_chapter_*.md`
- 完整版: `output/novels/<novel_id>_*.md`
