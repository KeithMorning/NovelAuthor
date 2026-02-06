# 日志系统快速入门

## 🚀 5分钟上手

### 1. 查看现有小说的日志

如果你有一个创建失败的小说（如 87c32361），可以直接查看日志：

```bash
# 方式1: 使用API查询
curl http://localhost:8000/api/novels/87c32361/logs/status

# 方式2: 直接查看日志文件
cat logs/novel_87c32361.log

# 方式3: 查看JSON格式
cat logs/novel_87c32361.json | jq '.'
```

### 2. 创建新小说时自动记录日志

启动服务后，创建新小说会自动记录日志：

```bash
# 启动服务
./start_all.sh

# 在前端或通过API创建小说
# 日志会自动保存到 logs/ 目录
```

### 3. 前端查看日志

在小说详情页面添加日志组件：

```tsx
import CreationLogs from './components/CreationLogs';

function NovelDetailPage({ novelId }) {
  return (
    <div>
      <h1>小说详情</h1>
      <CreationLogs 
        novelId={novelId} 
        autoRefresh={true} 
        refreshInterval={3000} 
      />
    </div>
  );
}
```

### 4. 查看日志示例

**成功的日志**:
```
[2026-02-05T10:30:00] [SUCCESS] [初始化] ✓ 小说对象创建成功
[2026-02-05T10:30:15] [SUCCESS] [生成大纲] ✓ 大纲生成成功，包含 20 章
[2026-02-05T10:31:00] [SUCCESS] [生成角色] ✓ 角色生成成功，创建了 3 个角色
[2026-02-05T10:31:05] [SUCCESS] [保存文件] ✓ 小说文件保存成功
[2026-02-05T10:31:10] [SUCCESS] [加载记忆] ✓ 记忆系统加载成功
[2026-02-05T10:31:12] [SUCCESS] [完成] 小说创建成功！
```

**失败的日志**:
```
[2026-02-05T10:30:00] [INFO] [初始化] 开始创建小说
[2026-02-05T10:30:02] [SUCCESS] [初始化] ✓ 小说对象创建成功
[2026-02-05T10:30:15] [SUCCESS] [生成大纲] ✓ 大纲生成成功
[2026-02-05T10:31:00] [ERROR] [生成角色] ✗ 角色生成失败
  错误类型: ValueError
  错误信息: 无法从响应中提取有效的JSON: Expecting value: line 73
```

## 📊 常用API

### 获取日志状态（轻量级）
```bash
curl http://localhost:8000/api/novels/{novel_id}/logs/status
```

返回：
```json
{
  "status": "running",
  "current_step": "生成角色",
  "steps_completed": ["初始化", "生成大纲"],
  "has_errors": false
}
```

### 获取完整日志
```bash
curl http://localhost:8000/api/novels/{novel_id}/logs
```

返回完整的日志数据和摘要。

## 🐛 调试技巧

### 问题：小说创建失败，不知道哪里出错

```bash
# 1. 查看状态
curl http://localhost:8000/api/novels/87c32361/logs/status

# 2. 如果has_errors为true，查看详细日志
curl http://localhost:8000/api/novels/87c32361/logs | jq '.workflow_status.errors'

# 3. 查看完整日志文件
cat logs/novel_87c32361.log | grep ERROR -A 5
```

### 问题：想知道每个步骤花了多长时间

```bash
# 查看JSON日志中的时间戳
cat logs/novel_87c32361.json | jq '.logs[] | {step: .step, timestamp: .timestamp, message: .message}'
```

## 📁 日志文件位置

```
项目根目录/
└── logs/
    ├── novel_87c32361.log      # 文本格式
    ├── novel_87c32361.json     # JSON格式
    ├── novel_abc12345.log
    └── novel_abc12345.json
```

## 💡 提示

- 日志会自动创建，无需手动配置
- 创建成功的小说也会有日志，可以查看耗时等信息
- 日志文件可以安全删除（不影响小说本身）
- 建议定期清理旧日志以节省磁盘空间

## 📖 更多信息

- [完整文档](docs/LOGGING_SYSTEM.md)
- [更新日志](CHANGELOG_LOGGING.md)

---

有问题？查看 `docs/LOGGING_SYSTEM.md` 获取详细说明。
