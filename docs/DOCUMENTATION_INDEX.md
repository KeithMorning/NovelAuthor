# 📚 项目文档索引

> 本文档为 Novel AI Agent 项目的完整文档导航，特别针对 AI 助手优化，方便快速理解项目结构和功能。

---

## 🎯 快速导航

### 核心文档（推荐优先阅读）

1. **[README.md](../README.md)** - 项目主文档 ⭐⭐⭐⭐⭐
   - 项目简介和核心功能
   - 快速开始指南
   - 系统架构概览

2. **[API_GUIDE.md](API_GUIDE.md)** - API 完整文档 ⭐⭐⭐⭐⭐
   - 所有 API 端点列表
   - 请求/响应格式
   - 使用示例

3. **[LOGGING_SYSTEM.md](LOGGING_SYSTEM.md)** - 日志系统文档 ⭐⭐⭐⭐⭐
   - 日志记录和查询
   - 工作流跟踪
   - 调试指南

---

## 📁 文档分类

### 📖 核心文档（docs/）

这些是需要AI或人经常阅读的重要文档：

| 文档 | 内容 | 重要度 |
|------|------|--------|
| [README.md](README.md) | 项目文档主入口 | ⭐⭐⭐⭐⭐ |
| [API_GUIDE.md](API_GUIDE.md) | 完整 API 文档 | ⭐⭐⭐⭐⭐ |
| [LOGGING_SYSTEM.md](LOGGING_SYSTEM.md) | 日志系统完整文档 | ⭐⭐⭐⭐⭐ |
| [YAML_FORMAT_MIGRATION.md](YAML_FORMAT_MIGRATION.md) | YAML格式迁移指南 | ⭐⭐⭐⭐ |
| [BUGFIX_JSON_PARSING.md](BUGFIX_JSON_PARSING.md) | JSON解析问题修复 | ⭐⭐⭐⭐ |
| [WEBSOCKET_GUIDE.md](WEBSOCKET_GUIDE.md) | WebSocket 使用指南 | ⭐⭐⭐⭐ |
| [FRONTEND_SETUP.md](FRONTEND_SETUP.md) | 前端项目设置 | ⭐⭐⭐⭐ |
| [AI_QUICK_START.md](AI_QUICK_START.md) | AI 助手快速开始 | ⭐⭐⭐⭐ |
| [DOCUMENTATION_GUIDELINES.md](DOCUMENTATION_GUIDELINES.md) | 文档维护指南 | ⭐⭐⭐ |
| [DOCUMENTATION_PRINCIPLES.md](DOCUMENTATION_PRINCIPLES.md) | 文档原则 | ⭐⭐⭐ |

### 📄 快速参考（根目录）

放在根目录便于快速访问：

| 文档 | 内容 | 用途 |
|------|------|------|
| [README.md](../README.md) | 项目主文档 | 项目入口 |
| [HOW_TO_USE_NEW_FEATURES.md](../HOW_TO_USE_NEW_FEATURES.md) | 新功能使用指南 | 快速上手 |
| [QUICK_START_LOGGING.md](../QUICK_START_LOGGING.md) | 日志系统快速入门 | 快速参考 |
| [DOCUMENTATION_SUMMARY.md](../DOCUMENTATION_SUMMARY.md) | 文档总结 | 快速概览 |

### 🗄️ 归档文档（docs/archive/）

历史文档和完成报告，不常访问但保留记录：

| 类型 | 文档示例 | 说明 |
|------|----------|------|
| 阶段报告 | PHASE4_COMPLETED.md | 各阶段完成报告 |
| 任务报告 | TASK12_COMPLETION_REPORT.md | 具体任务完成记录 |
| 测试结果 | FRONTEND_TEST_RESULTS.md | 历史测试结果 |
| 历史状态 | PROJECT_STATUS_FINAL.md | 过时的状态快照 |
| 更新日志 | CHANGELOG_*.md | 历史更新记录 |

**归档文档列表** (共21个)：
- API_TEST_RESULTS.md
- CHANGELOG_LOGGING.md
- CHANGELOG_YAML.md
- CHECKLIST.md
- CURRENT_STATUS.md
- FIX_NUMPY.md
- FRONTEND_TEST_RESULTS.md
- INSTALLATION_SUCCESS.md
- MULTI_LLM_SUPPORT.md
- PHASE3_COMPLETED.md
- PHASE4_COMPLETED.md
- PHASE4_FRONTEND_STATUS.md
- PHASE4_PLAN.md
- PHASE4_QUICKSTART.md
- PHASE4.1_COMPLETED.md
- PROJECT_STATUS_FINAL.md
- QUICK_START_API.md
- SUMMARY_2026_02_05.md
- TASK12_COMPLETION_REPORT.md
- USAGE_GUIDE.md
- WEBSOCKET_TEST_RESULTS.md

---

## 🗺️ 文档依赖关系

```
README.md (项目入口)
    │
    ├─→ docs/API_GUIDE.md (API参考)
    │   └─→ Swagger UI (交互式)
    │
    ├─→ docs/LOGGING_SYSTEM.md (日志文档)
    │   ├─→ HOW_TO_USE_NEW_FEATURES.md
    │   └─→ QUICK_START_LOGGING.md
    │
    ├─→ docs/YAML_FORMAT_MIGRATION.md (YAML迁移)
    │   └─→ docs/BUGFIX_JSON_PARSING.md
    │
    ├─→ docs/WEBSOCKET_GUIDE.md (WebSocket)
    │
    └─→ docs/FRONTEND_SETUP.md (前端)
```

---

## 📖 按角色推荐阅读

### 🤖 对于 AI 助手

**推荐阅读顺序**:
1. [README.md](../README.md) - 5分钟，了解项目全貌
2. [API_GUIDE.md](API_GUIDE.md) - 10分钟，理解API结构
3. [LOGGING_SYSTEM.md](LOGGING_SYSTEM.md) - 了解调试方法

**快速参考**:
- API列表 → [API_GUIDE.md](API_GUIDE.md)
- 日志查询 → [LOGGING_SYSTEM.md](LOGGING_SYSTEM.md)
- 问题修复 → [BUGFIX_JSON_PARSING.md](BUGFIX_JSON_PARSING.md)

### 👤 对于新用户

**推荐阅读顺序**:
1. [README.md](../README.md) → 快速开始
2. [HOW_TO_USE_NEW_FEATURES.md](../HOW_TO_USE_NEW_FEATURES.md) → 新功能
3. [FRONTEND_SETUP.md](FRONTEND_SETUP.md) → 使用界面

### 👨‍💻 对于开发者

**推荐阅读顺序**:
1. [README.md](../README.md) → 项目概览
2. [API_GUIDE.md](API_GUIDE.md) → API参考
3. [DOCUMENTATION_GUIDELINES.md](DOCUMENTATION_GUIDELINES.md) → 文档规范
4. docs/archive/ → 查看历史实现

---

## 🔍 按主题查找

### 新功能（2026-02-05）
- [LOGGING_SYSTEM.md](LOGGING_SYSTEM.md) - 完整日志系统
- [YAML_FORMAT_MIGRATION.md](YAML_FORMAT_MIGRATION.md) - YAML格式支持
- [HOW_TO_USE_NEW_FEATURES.md](../HOW_TO_USE_NEW_FEATURES.md) - 使用指南
- [QUICK_START_LOGGING.md](../QUICK_START_LOGGING.md) - 快速开始

### API 开发
- [API_GUIDE.md](API_GUIDE.md) - 完整API文档
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### WebSocket
- [WEBSOCKET_GUIDE.md](WEBSOCKET_GUIDE.md) - 使用指南
- 示例代码和测试

### 前端开发
- [FRONTEND_SETUP.md](FRONTEND_SETUP.md) - 前端设置
- docs/archive/TASK12_COMPLETION_REPORT.md - 编辑器实现

### 问题解决
- [LOGGING_SYSTEM.md](LOGGING_SYSTEM.md) - 日志调试
- [BUGFIX_JSON_PARSING.md](BUGFIX_JSON_PARSING.md) - JSON问题
- docs/archive/ - 历史问题和解决方案

---

## 📊 文档统计

### 当前活跃文档
- **核心文档**: 11 个（docs/）
- **快速参考**: 4 个（根目录）
- **归档文档**: 21 个（docs/archive/）
- **总计**: 36 个

### 最新更新（2026-02-05）
- ✅ 新增日志系统文档
- ✅ 新增YAML迁移文档
- ✅ 新增快速使用指南
- ✅ 整理文档结构（核心/归档分离）

---

## 💡 文档维护原则

### 文档放置规则

1. **docs/** - 核心文档
   - 需要经常阅读的文档
   - 系统功能说明
   - 使用指南和API文档

2. **根目录** - 快速参考
   - README.md（项目入口）
   - 快速入门指南
   - 使用说明

3. **docs/archive/** - 历史归档
   - 阶段完成报告
   - 历史状态记录
   - 测试结果
   - 更新日志

### 文档更新流程

1. 创建新文档时决定位置
2. 旧文档定期归档到 archive/
3. 更新本索引文档
4. 保持文档结构清晰

---

## 🔗 外部资源

### 在线文档（需启动服务）
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 前端应用: http://localhost:3000

### 日志文件
- 位置: `logs/` 目录
- 格式: `.log`（文本）+ `.json`（结构化）

---

## ✨ 使用建议

### 查找文档时
1. 先看本索引的分类
2. 确定是核心文档还是归档
3. 使用"按主题查找"快速定位

### 创建新文档时
1. 参考 [DOCUMENTATION_GUIDELINES.md](DOCUMENTATION_GUIDELINES.md)
2. 决定放在 docs/ 还是 archive/
3. 更新本索引文档

### 归档文档时
1. 移动到 docs/archive/
2. 更新本索引
3. 检查是否有文档引用需要更新

---

**文档维护**: Claude Code
**最后更新**: 2026-02-05
**版本**: v2.0 - 重构文档结构

---

<div align="center">

**📚 清晰的文档结构，让查找更轻松！**

[返回主文档](../README.md) • [API 文档](API_GUIDE.md) • [日志系统](LOGGING_SYSTEM.md)

</div>
