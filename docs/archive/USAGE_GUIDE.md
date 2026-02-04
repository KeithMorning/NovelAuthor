# 小说AI Agent 使用指南

## 快速开始 5 步曲

### 第 1 步：查看可用风格

```bash
python main.py styles
```

这会显示所有10种作家风格，选择一个适合你小说的风格。

---

### 第 2 步：创建新小说

```bash
python main.py create \
  --title "你的小说标题" \
  --genre "类型" \
  --theme "主题描述" \
  --style "风格名称" \
  --chapters 5
```

**示例 - 创建一部武侠小说**：
```bash
python main.py create \
  --title "江湖往事" \
  --genre "武侠" \
  --theme "一个少年的江湖复仇之路，探讨正义与复仇的边界" \
  --style "金庸" \
  --chapters 10
```

**示例 - 创建一部推理小说**：
```bash
python main.py create \
  --title "密室谜案" \
  --genre "推理" \
  --theme "一起发生在封闭山庄的连环谋杀案" \
  --style "东野圭吾" \
  --chapters 15
```

**示例 - 创建一部科幻小说**：
```bash
python main.py create \
  --title "星际流浪" \
  --genre "科幻" \
  --theme "人类在宇宙中寻找新家园的史诗之旅" \
  --style "刘慈欣" \
  --chapters 20
```

创建成功后会显示：
- ✅ 小说ID（例如：`novel_abc123`）- **保存这个ID，后续操作都需要它**
- ✅ 大纲章节数
- ✅ 角色数量

---

### 第 3 步：查看大纲和角色

```bash
# 查看大纲
cat novel_ai_agent/output/outlines/你的小说ID_outline_v1.md

# 查看角色设定
cat novel_ai_agent/output/characters/你的小说ID_characters.md
```

**示例**：
```bash
cat novel_ai_agent/output/outlines/novel_abc123_outline_v1.md
cat novel_ai_agent/output/characters/novel_abc123_characters.md
```

---

### 第 4 步：开始写作

```bash
# 写第1章
python main.py write --id 你的小说ID --chapter 1

# 写第2章
python main.py write --id 你的小说ID --chapter 2

# 继续写更多章节...
python main.py write --id 你的小说ID --chapter 3
```

**示例**：
```bash
python main.py write --id novel_abc123 --chapter 1
```

写作完成后，章节会保存到：
- `novel_ai_agent/output/novels/你的小说ID_chapter_001.md`

---

### 第 5 步：导出完整小说

```bash
python main.py export --id 你的小说ID
```

完整小说会导出为：
- `novel_ai_agent/output/novels/你的小说ID_小说标题.md`

---

## 高级功能

### 📝 润色章节

如果觉得某章写得不够好，可以润色：

```bash
# 全面润色
python main.py polish --id novel_abc123 --chapter 1

# 重点润色特定方面
python main.py polish --id novel_abc123 --chapter 1 --focus "对话,动作场面"
python main.py polish --id novel_abc123 --chapter 1 --focus "环境描写,心理描写"
```

---

### ⭐ 评审章节

获取专业的章节评审报告：

```bash
python main.py review --id novel_abc123 --chapter 1
```

会显示：
- 综合评分（满分10分）
- 分项评分（文字质量、风格一致性、情节逻辑等）
- 优点和需要改进的地方
- 具体修改建议

---

### 💬 交互式修改

通过自然对话来修改小说：

```bash
# 启动交互模式
python main.py interactive --id novel_abc123

# 针对特定章节
python main.py interactive --id novel_abc123 --chapter 1
```

进入对话模式后，你可以：
- "帮我把第3段改得更有紧张感"
- "主角的对话太平淡了，能不能更有个性一些"
- "这里的情节转折太突然，需要铺垫"

输入 `quit` 或 `exit` 退出对话。

---

### 🔍 搜索记忆

查找之前写过的内容：

```bash
# 搜索角色信息
python main.py search-memory --id novel_abc123 --query "主角" --type characters

# 搜索情节点
python main.py search-memory --id novel_abc123 --query "决战" --type plots

# 搜索章节内容
python main.py search-memory --id novel_abc123 --query "初次见面" --type chapters
```

---

### 📊 查看记忆统计

```bash
python main.py memory-stats --id novel_abc123
```

显示：
- 短期记忆状态
- 长期记忆数量（角色、情节点、章节等）

---

### 📚 查看所有小说

```bash
python main.py list-novels
```

---

### 🎨 风格相关

```bash
# 查看风格详情
python main.py style-info --style "金庸"

# 根据类型推荐风格
python main.py recommend-style --genre "武侠"
python main.py recommend-style --genre "科幻"
python main.py recommend-style --genre "推理"
```

---

## 💡 实用技巧

### 1. 创作短篇小说（3-5章）
```bash
python main.py create \
  --title "午夜咖啡馆" \
  --genre "现代" \
  --theme "一家深夜咖啡馆里发生的温暖故事" \
  --style "村上春树" \
  --chapters 3
```

### 2. 创作中篇小说（10-15章）
```bash
python main.py create \
  --title "古堡谜影" \
  --genre "悬疑" \
  --theme "一个家族的百年秘密" \
  --style "东野圭吾" \
  --chapters 12
```

### 3. 创作长篇小说（20+章）
```bash
python main.py create \
  --title "三体之后" \
  --genre "科幻" \
  --theme "地球文明与外星文明的最终对决" \
  --style "刘慈欣" \
  --chapters 25
```

### 4. 批量写作
```bash
# 使用循环批量创作多章
for i in {1..5}; do
  python main.py write --id novel_abc123 --chapter $i
  echo "第 $i 章完成！"
done
```

### 5. 创作工作流
```bash
# 完整工作流示例
NOVEL_ID="novel_abc123"

# 1. 创建小说
python main.py create --title "标题" --genre "类型" --theme "主题" --style "风格" --chapters 10

# 2. 查看大纲
cat novel_ai_agent/output/outlines/${NOVEL_ID}_outline_v1.md

# 3. 写作第一章
python main.py write --id $NOVEL_ID --chapter 1

# 4. 评审第一章
python main.py review --id $NOVEL_ID --chapter 1

# 5. 润色第一章（如果需要）
python main.py polish --id $NOVEL_ID --chapter 1

# 6. 继续后续章节...
```

---

## ⚙️ 配置说明

### 切换 LLM 提供商

在 `.env` 文件中配置：

```bash
# 使用 Anthropic Claude
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_key_here
DEFAULT_MODEL=claude-sonnet-4-20250514

# 使用 OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
DEFAULT_MODEL=gpt-4o

# 使用 DeepSeek
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_key_here
DEFAULT_MODEL=deepseek-chat
```

### 调整创作参数

在 `.env` 中：
```bash
# 生成温度（0.0-1.0，越高越创意）
TEMPERATURE=0.7

# 默认章节字数
DEFAULT_CHAPTER_WORDS=3000

# 最大Token数
MAX_TOKENS=4096
```

---

## 🆘 常见问题

### Q: 创建小说时出错？
A: 检查以下几点：
1. API Key 是否正确配置
2. 网络连接是否正常
3. LLM 提供商是否可用

### Q: 写作速度慢？
A: 这是正常的，AI生成需要时间：
- 短篇（3000字）：约3-5分钟
- 可以在生成时做其他事情

### Q: 如何修改已生成的内容？
A: 三种方式：
1. 使用 `polish` 命令润色
2. 使用 `interactive` 命令对话修改
3. 直接编辑 Markdown 文件

### Q: 记忆系统的作用？
A: 记忆系统会：
- 自动记住所有角色、情节、章节
- 写作时提供相关上下文
- 支持语义搜索查找信息

### Q: 可以中断后继续吗？
A: 可以！使用小说ID随时继续：
```bash
# 查看已有小说
python main.py list-novels

# 继续写作
python main.py write --id novel_abc123 --chapter 5
```

---

## 📁 文件位置

所有生成的文件都在 `novel_ai_agent/output/` 目录：

```
novel_ai_agent/output/
├── novels/          # 小说章节和完整版
│   ├── novel_abc123_chapter_001.md
│   ├── novel_abc123_chapter_002.md
│   └── novel_abc123_小说标题.md  (完整版)
├── outlines/        # 大纲文件
│   └── novel_abc123_outline_v1.md
└── characters/      # 角色设定
    └── novel_abc123_characters.md
```

---

## 🎓 学习资源

- 查看示例小说：`novel_ai_agent/output/novels/novel_62c8c6f1_不同的AI种族.md`
- 查看 Phase 3 完成报告：`PHASE3_COMPLETED.md`
- 查看项目架构：`README.md`

---

**祝你创作愉快！** 📝✨

有任何问题都可以：
1. 查看帮助：`python main.py --help`
2. 查看版本：`python main.py version`
3. 查看命令帮助：`python main.py write --help`
