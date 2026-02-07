# 小说创建恢复功能

## 功能说明

`resume` 命令允许你从中断的位置继续创建小说，避免重新生成已完成的部分（大纲、角色等）。

## 使用场景

当小说创建过程中遇到错误时（例如：网络错误、Embedding 加载失败、系统崩溃等），可以使用 `resume` 命令从上次中断的地方继续，而不需要重新开始。

## 命令格式

```bash
python3 main.py resume --id <novel_id> [--skip-memory]
```

### 参数说明

- `--id, -i`: **必需**，指定要恢复的小说ID
- `--skip-memory`: **可选**，跳过记忆系统加载（如果记忆系统有问题可以先跳过）

## 使用示例

### 示例 1: 从中断位置恢复

假设你在创建小说 `novel_23f9fe50` 时，大纲和角色已生成，但在加载记忆系统时失败了：

```bash
python3 main.py resume --id novel_23f9fe50
```

**输出示例：**

```
╭──────────────────────────────────────────────────────────────────────────────╮
│ 恢复小说创建: novel_23f9fe50                                                 │
╰──────────────────────────────────────────────────────────────────────────────╯
✓ 找到小说: 闭包逃逸

工作流状态:
  当前步骤: 加载记忆
  状态: running

已完成步骤:
  ✓ 初始化
  ✓ 生成大纲
  ✓ 生成角色
  ✓ 保存文件

错误信息:
  ✗ 加载记忆: 网络错误导致模型加载失败...

小说信息:
  标题: 闭包逃逸
  类型: 科幻
  风格: 刘慈欣
  大纲: ✓ 已生成
  角色数: 5
  章节数: 0

检测到需要加载到记忆系统

正在加载小说到记忆系统...
✓ 小说已成功加载到记忆系统

记忆统计:
  角色记录: 5
  情节记录: 5
  章节记录: 0

✓ 小说恢复完成！

接下来可以:
- 开始写作第1章: python main.py write --id novel_23f9fe50 --chapter 1
- 查看大纲: cat novel_ai_agent/output/outlines/novel_23f9fe50_outline_v1.md
- 查看角色: cat novel_ai_agent/output/characters/novel_23f9fe50_characters.md
- 查看记忆统计: python main.py memory-stats --id novel_23f9fe50
```

### 示例 2: 跳过记忆加载

如果记忆系统持续出现问题，可以先跳过记忆加载，直接开始写作：

```bash
python3 main.py resume --id novel_23f9fe50 --skip-memory
```

**输出：**

```
✓ 找到小说: 闭包逃逸
...
! 已跳过记忆加载

✓ 小说数据已就绪

接下来可以:
- 开始写作第1章: python main.py write --id novel_23f9fe50 --chapter 1
```

注意：跳过记忆加载后，向量搜索功能将不可用，但基本的写作功能仍然可以正常使用。

## 工作原理

### 1. 检查小说状态

`resume` 命令会：
- 读取小说 JSON 文件
- 读取工作流日志文件（`logs/novel_<id>.json`）
- 判断哪些步骤已完成，哪些步骤需要重新执行

### 2. 确定恢复策略

根据小说状态自动判断：

| 已完成步骤 | 恢复操作 |
|-----------|---------|
| 初始化 | 重新生成大纲和角色 |
| 大纲生成 | 重新生成角色 |
| 角色生成 | 保存文件 |
| 文件保存 | 加载到记忆系统 |
| 记忆加载（失败） | 重新加载记忆 |
| 全部完成 | 无需操作 |

### 3. 执行恢复

自动执行未完成的步骤，确保小说创建流程完整。

## 故障排除

### 问题1: 找不到小说ID

**错误信息：**
```
✗ 未找到小说文件: novel_xxx
```

**解决方案：**
1. 使用 `python main.py list` 查看所有小说ID
2. 检查 `novel_ai_agent/output/novels/` 目录下是否存在对应的 JSON 文件

### 问题2: 记忆加载持续失败

**错误信息：**
```
✗ 加载记忆失败: 网络错误导致模型加载失败...
```

**解决方案：**

方案1：使用 `--skip-memory` 跳过记忆加载
```bash
python3 main.py resume --id novel_xxx --skip-memory
```

方案2：检查 Embedding 模型
```bash
# 重新下载模型
python3 scripts/download_models.py

# 测试 Embedding
python3 tests/test_local_embedding_debug.py
```

方案3：查看详细日志
```bash
# 查看创建日志
cat logs/novel_xxx.json

# 查看 Embedding 日志
cat logs/load_novel_to_memory_debug.log
```

### 问题3: 工作流日志不存在

**提示信息：**
```
! 未找到工作流日志文件
```

**说明：**
- 这不是错误，只是表示没有详细的工作流日志
- `resume` 命令仍会根据小说文件状态进行恢复
- 工作流日志会在 Phase 3 之后的版本中完善

## 与其他命令的区别

| 命令 | 用途 | 何时使用 |
|------|------|---------|
| `create` | 创建全新小说 | 开始新的小说项目 |
| `resume` | 从中断位置继续 | 创建过程中遇到错误 |
| `write` | 写作指定章节 | 小说已创建完成，开始写作章节 |

## 最佳实践

1. **创建失败后立即恢复**
   ```bash
   # 如果 create 命令失败
   python3 main.py create --title "..." --genre "..." ...
   # 失败后立即使用 resume
   python3 main.py resume --id <novel_id>
   ```

2. **定期检查记忆状态**
   ```bash
   # 恢复后检查记忆是否正常加载
   python3 main.py memory-stats --id <novel_id>
   ```

3. **保存小说ID**
   - 创建小说后记录小说ID
   - 或者使用 `python main.py list` 查看所有小说

## 技术细节

### 文件结构

```
novel_ai_agent/output/
├── novels/
│   └── novel_xxx.json          # 小说主文件
├── outlines/
│   └── novel_xxx_outline_v1.md # 大纲文件
├── characters/
│   └── novel_xxx_characters.md # 角色文件
└── ...

logs/
└── novel_xxx.json              # 工作流日志（可选）

novel_ai_agent/data/chroma/     # 向量数据库（记忆系统）
```

### 状态判断逻辑

```python
def determine_resume_action(novel, workflow_status):
    """
    判断需要执行的恢复操作
    """
    if not novel.outline:
        return "generate_outline"
    elif not novel.characters:
        return "generate_characters"
    elif not is_saved():
        return "save_files"
    elif not is_memory_loaded():
        return "load_memory"
    else:
        return "complete"
```

## 未来改进

- [ ] 支持指定从哪个步骤开始恢复
- [ ] 自动备份和版本控制
- [ ] 更详细的恢复进度显示
- [ ] 支持批量恢复多个小说
- [ ] 恢复后的完整性检查

## 总结

`resume` 命令是一个强大的容错机制，可以：
- ✅ 节省时间：无需重新生成已完成的内容
- ✅ 提高稳定性：优雅处理各种错误场景
- ✅ 灵活性：支持跳过有问题的步骤
- ✅ 用户友好：自动判断恢复策略，无需手动干预

在遇到任何创建错误时，首先尝试使用 `resume` 命令恢复！
