# 更新日志 - 日志系统

## [2026-02-05] 新增完整的日志记录系统

### 🎯 背景
用户反馈在创建小说过程中（如ID 87c32361）遇到问题时，无法快速定位失败的具体步骤和原因。需要一个完整的日志系统来跟踪整个创建流程。

### ✨ 新功能

#### 1. 完整的日志记录系统
- ✅ 跟踪工作流的每个步骤
- ✅ 记录成功、失败和警告信息
- ✅ 捕获详细的错误信息和堆栈跟踪
- ✅ 保存为文本和JSON两种格式
- ✅ 实时状态查询

#### 2. 工作流步骤跟踪
系统跟踪以下关键步骤：
1. 初始化 - 创建小说对象
2. 生成大纲 - AI生成故事大纲
3. 生成角色 - AI生成角色设定
4. 保存文件 - 保存小说数据
5. 加载记忆 - 加载到向量记忆系统
6. 完成 - 创建流程完成

#### 3. API端点
- `GET /api/novels/{novel_id}/logs` - 获取完整日志
- `GET /api/novels/{novel_id}/logs/status` - 获取当前状态

#### 4. 前端组件
- `CreationLogs.tsx` - 可视化日志显示组件
- 步骤进度条
- 错误高亮显示
- 自动刷新状态

### 📝 实现的文件

#### 新增文件
- `novel_ai_agent/utils/logger.py` - 日志核心模块
- `frontend/src/components/CreationLogs.tsx` - 前端组件
- `docs/LOGGING_SYSTEM.md` - 完整文档
- `test_logging_system.py` - 测试脚本
- `CHANGELOG_LOGGING.md` - 此文件

#### 修改文件
- `novel_ai_agent/agents/coordinator.py` - 集成日志系统
- `novel_ai_agent/api/routes/novels.py` - 添加日志API

### 🎨 使用示例

#### 后端使用
```python
from novel_ai_agent.utils.logger import get_logger, WorkflowStep

# 获取日志记录器
logger = get_logger(novel_id)

# 记录步骤
logger.step_start(WorkflowStep.OUTLINE_GENERATION, "开始生成大纲")

try:
    result = await generate_outline()
    logger.step_success(
        WorkflowStep.OUTLINE_GENERATION,
        "大纲生成成功",
        details={"chapter_count": len(result.chapters)}
    )
except Exception as e:
    logger.step_error(
        WorkflowStep.OUTLINE_GENERATION,
        "大纲生成失败",
        e
    )
```

#### API查询
```bash
# 获取完整日志
curl http://localhost:8000/api/novels/87c32361/logs

# 获取状态
curl http://localhost:8000/api/novels/87c32361/logs/status
```

#### 前端使用
```tsx
import CreationLogs from './components/CreationLogs';

<CreationLogs novelId={novelId} autoRefresh={true} />
```

### 📊 日志格式

#### 文本日志 (`logs/{novel_id}.log`)
```
[2026-02-05T10:30:00] [INFO] [初始化] 创建小说对象: 智治纪元 (科幻)
  详情: {
    "novel_id": "novel_87c32361",
    "title": "智治纪元"
  }
--------------------------------------------------------------------------------
[2026-02-05T10:31:00] [ERROR] [生成角色] 角色生成失败
  错误类型: ValueError
  错误信息: 无法从响应中提取有效的JSON
--------------------------------------------------------------------------------
```

#### JSON日志 (`logs/{novel_id}.json`)
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
  "logs": [...]
}
```

### 🔍 调试案例演示

**场景**: 小说87c32361在生成角色时失败

**步骤1**: 查询状态
```bash
curl http://localhost:8000/api/novels/87c32361/logs/status
```

**返回**:
```json
{
  "status": "failed",
  "current_step": "生成角色",
  "steps_completed": ["初始化", "生成大纲"],
  "has_errors": true,
  "error_count": 1
}
```

**步骤2**: 查看详细日志
```bash
curl http://localhost:8000/api/novels/87c32361/logs | jq '.workflow_status.errors'
```

**返回**:
```json
[
  {
    "timestamp": "2026-02-05T10:31:00",
    "step": "生成角色",
    "error": "无法从响应中提取有效的JSON: Expecting value: line 73"
  }
]
```

**结论**: 在生成角色步骤失败，原因是JSON解析错误。
**解决方案**: 已通过YAML迁移解决（见 `CHANGELOG_YAML.md`）

### ✅ 测试结果

运行 `python3 test_logging_system.py`：

```
✅ 所有测试通过！

已验证的功能：
  1. ✅ 基本日志记录（INFO, SUCCESS, WARNING, ERROR）
  2. ✅ 错误捕获和记录
  3. ✅ 日志查询和过滤
  4. ✅ 工作流状态跟踪
  5. ✅ 文件持久化（文本 + JSON）
  6. ✅ 时间统计
```

### 🎯 核心特性

| 特性 | 说明 | 状态 |
|------|------|------|
| 步骤跟踪 | 记录每个工作流步骤 | ✅ |
| 错误捕获 | 捕获异常和堆栈跟踪 | ✅ |
| 详细信息 | 记录每步的详细数据 | ✅ |
| 时间统计 | 记录开始/结束时间和耗时 | ✅ |
| 实时查询 | API查询当前状态 | ✅ |
| 文件持久化 | 保存为文本和JSON | ✅ |
| 前端可视化 | React组件显示日志 | ✅ |

### 📖 相关文档

- [日志系统完整文档](docs/LOGGING_SYSTEM.md)
- [YAML格式迁移](docs/YAML_FORMAT_MIGRATION.md)
- [Bug修复 - JSON解析](docs/BUGFIX_JSON_PARSING.md)
- [API文档](docs/API_DOCUMENTATION.md)

### 🚀 下一步

1. **启动服务测试**:
   ```bash
   ./start_all.sh
   ```

2. **创建小说并查看日志**:
   - 在前端创建新小说
   - 访问小说详情页查看创建日志
   - 或通过API查询: `GET /api/novels/{novel_id}/logs`

3. **查看日志文件**:
   ```bash
   cat logs/{novel_id}.log
   ```

### 💡 最佳实践

1. **定期清理日志**: 日志会占用磁盘空间，建议定期清理旧日志
2. **错误处理**: 所有关键步骤都应该有try-catch和日志记录
3. **详细信息**: 记录足够的上下文信息以便调试
4. **性能考虑**: 日志写入有I/O开销，不要过度记录

### 🐛 解决的问题

- ✅ 无法知道小说创建失败在哪个步骤
- ✅ 错误信息不完整，难以调试
- ✅ 无法追踪创建过程的详细状态
- ✅ 缺少时间统计和性能分析数据

### 🔄 向后兼容性

- ✅ 不影响现有功能
- ✅ 日志系统是可选的（如果不初始化logger，不会影响功能）
- ✅ API端点是新增的，不会破坏现有接口

---

**更新人**: Claude (claude-4.5-sonnet)
**更新日期**: 2026-02-05
**影响范围**: 全局（增强型功能，不破坏现有代码）
**状态**: ✅ 已完成并测试
**测试**: ✅ 所有单元测试通过
