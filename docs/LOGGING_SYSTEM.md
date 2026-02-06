# 日志系统文档

## 概述

小说AI创作系统集成了完整的日志记录系统，用于跟踪小说创建过程中的每个步骤、状态和错误信息。

当创建过程中出现问题时，可以通过日志快速定位问题所在的步骤和具体错误信息。

## 功能特性

### ✅ 核心功能

1. **步骤跟踪** - 记录每个工作流步骤的开始、成功和失败
2. **错误捕获** - 捕获并记录所有异常和错误信息
3. **详细信息** - 保存每个步骤的详细数据（如角色数量、章节数等）
4. **时间统计** - 记录开始时间、结束时间和总耗时
5. **状态监控** - 实时查询创建状态
6. **日志持久化** - 保存为文本和JSON两种格式

### 📊 工作流步骤

系统跟踪以下步骤：

1. **初始化** - 创建小说对象
2. **生成大纲** - AI生成故事大纲
3. **生成角色** - AI生成角色设定
4. **保存文件** - 保存小说数据到文件
5. **加载记忆** - 加载到向量记忆系统
6. **完成** - 创建流程完成

## 使用方法

### 后端使用

#### 1. 在Agent中使用日志

```python
from novel_ai_agent.utils.logger import get_logger, WorkflowStep

# 获取日志记录器
logger = get_logger(novel_id)

# 记录步骤开始
logger.step_start(
    WorkflowStep.OUTLINE_GENERATION,
    "开始生成大纲"
)

try:
    # 执行任务
    result = await generate_outline()

    # 记录成功
    logger.step_success(
        WorkflowStep.OUTLINE_GENERATION,
        "大纲生成成功",
        details={
            "chapter_count": len(result.chapters),
            "plot_points": len(result.plot_points)
        }
    )

except Exception as e:
    # 记录错误
    logger.step_error(
        WorkflowStep.OUTLINE_GENERATION,
        "大纲生成失败",
        e,
        details={"title": title, "genre": genre}
    )
    raise

# 标记完成
logger.complete("小说创建完成")
```

#### 2. 查询日志

```python
from novel_ai_agent.utils.logger import get_novel_logs

# 读取日志
logs = get_novel_logs(novel_id)

if logs:
    status = logs["workflow_status"]
    print(f"状态: {status['status']}")
    print(f"当前步骤: {status['current_step']}")
    print(f"已完成: {status['steps_completed']}")
    print(f"错误数: {len(status['errors'])}")
```

### API端点

#### 1. 获取完整日志

```http
GET /api/novels/{novel_id}/logs
```

**响应**:
```json
{
  "novel_id": "novel_87c32361",
  "workflow_status": {
    "novel_id": "novel_87c32361",
    "start_time": "2026-02-05T10:30:00",
    "end_time": "2026-02-05T10:35:00",
    "current_step": "完成",
    "status": "completed",
    "steps_completed": ["初始化", "生成大纲", "生成角色", "保存文件", "加载记忆"],
    "errors": []
  },
  "logs": [
    {
      "timestamp": "2026-02-05T10:30:00",
      "level": "INFO",
      "step": "初始化",
      "message": "创建小说对象: 智治纪元 (科幻)"
    }
  ],
  "summary": {
    "total_logs": 15,
    "level_counts": {
      "INFO": 8,
      "SUCCESS": 6,
      "ERROR": 1
    },
    "steps_completed": 5,
    "errors": [],
    "duration_seconds": 300.5,
    "final_status": "completed"
  }
}
```

#### 2. 获取状态（简化版）

```http
GET /api/novels/{novel_id}/logs/status
```

**响应**:
```json
{
  "novel_id": "novel_87c32361",
  "status": "running",
  "current_step": "生成角色",
  "steps_completed": ["初始化", "生成大纲"],
  "start_time": "2026-02-05T10:30:00",
  "end_time": null,
  "has_errors": false,
  "error_count": 0
}
```

### 前端使用

#### 1. 使用CreationLogs组件

```tsx
import CreationLogs from './components/CreationLogs';

function NovelDetailPage() {
  return (
    <div>
      <h1>小说详情</h1>

      {/* 显示创建日志 */}
      <CreationLogs
        novelId={novelId}
        autoRefresh={true}
        refreshInterval={3000}
      />
    </div>
  );
}
```

#### 2. 直接调用API

```typescript
// 获取日志
const response = await fetch(`/api/novels/${novelId}/logs`);
const data = await response.json();

console.log('工作流状态:', data.workflow_status);
console.log('日志条目:', data.logs);
console.log('摘要:', data.summary);

// 获取状态
const statusResponse = await fetch(`/api/novels/${novelId}/logs/status`);
const status = await statusResponse.json();

console.log('当前状态:', status.status);
console.log('当前步骤:', status.current_step);
```

## 日志文件位置

日志保存在项目根目录的 `logs/` 目录下：

```
logs/
├── novel_87c32361.log      # 文本格式日志
├── novel_87c32361.json     # JSON格式日志
├── novel_abc12345.log
└── novel_abc12345.json
```

### 文本日志格式

```
[2026-02-05T10:30:00] [INFO] [初始化] 创建小说对象: 智治纪元 (科幻)
  详情: {
    "novel_id": "novel_87c32361",
    "title": "智治纪元",
    "genre": "科幻"
  }
--------------------------------------------------------------------------------
[2026-02-05T10:31:00] [ERROR] [生成角色] 角色生成失败
  错误类型: ValueError
  错误信息: 无法从响应中提取有效的JSON
  详情: {
    "outline_chapters": 20
  }
--------------------------------------------------------------------------------
```

### JSON日志格式

```json
{
  "workflow_status": {
    "novel_id": "novel_87c32361",
    "start_time": "2026-02-05T10:30:00",
    "end_time": null,
    "current_step": "生成角色",
    "status": "running",
    "steps_completed": ["初始化", "生成大纲"],
    "errors": [
      {
        "timestamp": "2026-02-05T10:31:00",
        "step": "生成角色",
        "error": "无法从响应中提取有效的JSON"
      }
    ]
  },
  "logs": [
    {
      "timestamp": "2026-02-05T10:30:00",
      "level": "INFO",
      "step": "初始化",
      "message": "创建小说对象: 智治纪元 (科幻)",
      "details": {
        "novel_id": "novel_87c32361",
        "title": "智治纪元",
        "genre": "科幻"
      }
    }
  ]
}
```

## 调试案例

### 案例：创建87c32361失败

**问题描述**: 小说创建在完成大纲和outline后失败

**步骤1**: 查看日志状态
```bash
curl http://localhost:8000/api/novels/87c32361/logs/status
```

**响应**:
```json
{
  "status": "failed",
  "current_step": "生成角色",
  "steps_completed": ["初始化", "生成大纲"],
  "has_errors": true,
  "error_count": 1
}
```

**步骤2**: 查看详细错误
```bash
curl http://localhost:8000/api/novels/87c32361/logs
```

**在日志中找到**:
```json
{
  "timestamp": "2026-02-05T10:31:00",
  "level": "ERROR",
  "step": "生成角色",
  "message": "✗ 角色生成失败",
  "error": {
    "type": "ValueError",
    "message": "无法从响应中提取有效的JSON: Expecting value: line 73 column 15"
  },
  "details": {
    "outline_chapters": 20
  }
}
```

**结论**: 在"生成角色"步骤失败，原因是JSON解析错误。

**解决方案**: 已通过迁移到YAML格式解决（参见 `docs/YAML_FORMAT_MIGRATION.md`）

## 日志级别

| 级别 | 用途 | 图标 |
|------|------|------|
| DEBUG | 调试信息 | 🔍 |
| INFO | 一般信息 | ℹ️ |
| SUCCESS | 成功完成 | ✅ |
| WARNING | 警告信息 | ⚠️ |
| ERROR | 错误信息 | ❌ |

## 最佳实践

### 1. 记录关键步骤

为每个重要步骤记录开始和结束：
```python
logger.step_start(WorkflowStep.OUTLINE_GENERATION, "开始生成大纲")
# ... 执行任务 ...
logger.step_success(WorkflowStep.OUTLINE_GENERATION, "大纲生成成功")
```

### 2. 包含详细信息

在成功时记录有用的统计数据：
```python
logger.step_success(
    WorkflowStep.CHARACTER_GENERATION,
    "角色生成成功",
    details={
        "character_count": len(characters),
        "characters": [char.name for char in characters],
        "total_relationships": sum(len(c.relationships) for c in characters)
    }
)
```

### 3. 记录完整错误

捕获异常时记录上下文：
```python
except Exception as e:
    logger.step_error(
        WorkflowStep.OUTLINE_GENERATION,
        "大纲生成失败",
        e,
        details={
            "title": title,
            "genre": genre,
            "chapter_count": chapter_count,
            "attempted_retries": retry_count
        }
    )
```

### 4. 使用警告

对非致命问题使用警告：
```python
if len(characters) < 3:
    logger.warning(
        WorkflowStep.CHARACTER_GENERATION,
        "角色数量较少，可能影响故事丰富度",
        details={"character_count": len(characters)}
    )
```

## 性能考虑

- **内存管理**: 日志保存在内存中，完成后建议调用 `remove_logger(novel_id)` 释放
- **文件I/O**: 每次日志写入都会更新文件，对于频繁日志可能影响性能
- **日志大小**: 建议定期清理旧日志文件

## 扩展功能

### 计划中的功能

- [ ] 日志归档和压缩
- [ ] 日志搜索和过滤
- [ ] 日志可视化图表
- [ ] 邮件/Webhook通知
- [ ] 性能指标统计

## 相关文档

- [Bug修复 - JSON解析](./BUGFIX_JSON_PARSING.md)
- [YAML格式迁移](./YAML_FORMAT_MIGRATION.md)
- [API文档](./API_DOCUMENTATION.md)
- [系统架构](../README.md#系统架构)

---

**更新日期**: 2026-02-05
**版本**: 1.0
**状态**: ✅ 已实现并测试
