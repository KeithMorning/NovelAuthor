# 📝 文档维护指南

> **核心原则：文档即代码 (Documentation as Code)**
>
> 文档应该像代码一样被维护：每次更新一个文档时，所有相关的文档都应该同步更新。

---

## 🎯 核心原则

### 1. 文档即代码 (Documentation as Code)
- ✅ 文档和代码同等重要
- ✅ 文档更新要及时、准确
- ✅ 保持文档间的一致性
- ✅ 建立文档依赖关系

### 2. 代码即文档 (Code as Documentation)
**⚠️ 重要：更新代码时，必须同步更新文档！**

当更新代码时，必须更新：
- ✅ 相关的功能文档
- ✅ API 文档（如修改了API）
- ✅ 使用指南（如改变了用法）
- ✅ 代码注释（Swagger/DocString）
- ✅ 示例代码
- ✅ README（如影响核心功能）

### 3. 更新连锁反应（双向同步）

**更新文档时**，必须检查并更新：
- ✅ 直接引用该文档的其他文档
- ✅ 文档索引和导航
- ✅ README 中的相关链接
- ✅ 统计数据和状态信息

**更新代码时**，必须检查并更新：
- ✅ 对应的功能文档
- ✅ API 参考文档
- ✅ 使用示例
- ✅ 状态报告中的统计数据
- ✅ 相关的链接和引用

---

## 📚 文档依赖关系

### 核心依赖链
```
README.md (主入口)
    ↓ 影响
docs/AI_QUICK_START.md (AI快速上手)
docs/DOCUMENTATION_INDEX.md (完整索引)
    ↓ 影响
所有其他文档
```

### 更新影响矩阵

| 更新文档 | 必须同步更新 |
|---------|-------------|
| **任何文档** | docs/DOCUMENTATION_INDEX.md (更新索引) |
| **功能/API变更** | README.md, API_GUIDE.md, PROJECT_STATUS_FINAL.md |
| **项目状态变更** | README.md, PROJECT_STATUS_FINAL.md, AI_QUICK_START.md |
| **新增文档** | README.md, docs/README.md, DOCUMENTATION_INDEX.md |
| **技术栈变更** | README.md, PROJECT_STATUS_FINAL.md, AI_QUICK_START.md |
| **代码统计变更** | PROJECT_STATUS_FINAL.md, AI_QUICK_START.md |

---

## ✅ 文档更新检查清单

### 当添加新功能时
- [ ] 更新 README.md 的功能特性部分
- [ ] 更新 docs/PROJECT_STATUS_FINAL.md 的功能清单
- [ ] 更新 docs/AI_QUICK_START.md 的核心概念
- [ ] 如涉及API，更新 docs/API_GUIDE.md
- [ ] 更新 docs/DOCUMENTATION_INDEX.md
- [ ] 更新相关的测试文档

### 当修改API时
- [ ] 更新 docs/API_GUIDE.md 的端点文档
- [ ] 更新 Swagger/OpenAPI 注释（代码中）
- [ ] 更新 docs/PROJECT_STATUS_FINAL.md 的API统计
- [ ] 更新示例代码
- [ ] 更新测试文档

### 当添加新文档时
- [ ] 在 docs/ 目录创建文档
- [ ] 更新 docs/README.md 添加文档条目
- [ ] 更新 docs/DOCUMENTATION_INDEX.md 添加到索引
- [ ] 在 README.md 中添加链接（如适用）
- [ ] 更新文档统计数字

### 当修改项目状态时
- [ ] 更新 docs/PROJECT_STATUS_FINAL.md
- [ ] 更新 docs/AI_QUICK_START.md 的统计数据
- [ ] 更新 README.md 的项目状态部分
- [ ] 更新版本号（如适用）
- [ ] 记录更新时间

### 当归档文档时
- [ ] 移动到 docs/archive/
- [ ] 从 docs/README.md 移除
- [ ] 从 docs/DOCUMENTATION_INDEX.md 更新状态
- [ ] 在 README.md 中标注为归档
- [ ] 更新文档统计数字

---

## 📋 常见更新场景

### 场景0：修改代码功能
**需要更新的内容**：
1. **代码层面**：
   - 更新函数/类的 DocString
   - 更新 Swagger/OpenAPI 注释
   - 更新代码中的注释
   - 更新示例代码

2. **文档层面**：
   - 更新 `API_GUIDE.md`（如是API变更）
   - 更新 `README.md`（如影响核心功能）
   - 更新相关的使用指南
   - 更新 `PROJECT_STATUS_FINAL.md`（如影响统计）
   - 更新 `AI_QUICK_START.md`（如影响核心概念）

### 场景1：完成一个新Phase
**需要更新的文档**：
1. 创建 Phase 完成报告（如 `PHASE5_COMPLETED.md`）
2. 更新 `PROJECT_STATUS_FINAL.md` 的 Phase 状态
3. 更新 `README.md` 的开发进度
4. 更新 `AI_QUICK_START.md` 的统计数据
5. 更新 `DOCUMENTATION_INDEX.md` 添加新报告

### 场景2：添加新API端点
**需要更新的文档**：
1. 更新 `API_GUIDE.md` 添加端点文档
2. 更新 Swagger 注释（代码中）
3. 更新 `PROJECT_STATUS_FINAL.md` 的API统计
4. 更新 `AI_QUICK_START.md` 的API数量
5. 添加使用示例

### 场景3：前端新增组件
**需要更新的文档**：
1. 更新 `PHASE4_FRONTEND_STATUS.md`
2. 更新 `PROJECT_STATUS_FINAL.md` 的组件统计
3. 更新 `AI_QUICK_START.md` 的前端组件数量
4. 在 `FRONTEND_SETUP.md` 中说明用法
5. 更新项目结构图（如有必要）

### 场景4：修复重大Bug
**需要更新的文档**：
1. 在相关文档中更新已知问题
2. 更新测试文档
3. 如影响使用方式，更新使用指南
4. 记录在 CHANGELOG（如有）

---

## 🔄 代码-文档同步工作流

### 代码变更工作流

```
修改代码
    ↓
识别影响的功能
    ↓
更新代码注释（Swagger/DocString）
    ↓
更新相关文档（API_GUIDE, README等）
    ↓
更新使用示例
    ↓
更新统计数据
    ↓
提交代码和文档
```

### 文档变更工作流

```
修改文档
    ↓
识别引用该文档的其他文档
    ↓
同步更新所有相关文档
    ↓
更新索引和导航
    ↓
验证链接有效性
    ↓
提交文档
```

### 步骤1：识别影响范围
```
代码/文档变更
    ↓
列出受影响的功能领域
    ↓
查找相关文档（使用DOCUMENTATION_INDEX.md）
    ↓
查找相关代码（如果是文档变更）
```

### 步骤2：更新主要文档
```
更新直接相关的文档
    ↓
更新文档内的示例代码
    ↓
更新统计数据
```

### 步骤3：更新索引和导航
```
更新 DOCUMENTATION_INDEX.md
    ↓
更新 docs/README.md
    ↓
更新主 README.md（如适用）
```

### 步骤4：验证一致性
```
检查文档间链接是否有效
    ↓
确认统计数据一致
    ↓
验证示例代码可运行
```

---

## 📊 文档质量标准

### 必须包含的信息
- ✅ 创建/更新时间
- ✅ 文档版本（如适用）
- ✅ 清晰的标题和结构
- ✅ 目录（对于长文档）
- ✅ 相关文档链接

### 文档命名规范
- `*_GUIDE.md` - 使用指南
- `*_STATUS.md` - 状态报告
- `*_COMPLETED.md` - 完成报告
- `*_RESULTS.md` - 测试结果
- `*_GUIDELINES.md` - 指导方针
- `README.md` - 目录说明

### 内容质量要求
- ✅ 信息准确、最新
- ✅ 清晰的层次结构
- ✅ 适当的示例代码
- ✅ 有效的内外部链接
- ✅ 对AI友好的格式

---

## 🤖 AI友好的文档格式

### 结构化信息
```markdown
## 标题

### 子标题

| 项目 | 说明 | 状态 |
|------|------|------|
| 功能1 | 描述 | ✅ |
```

### 清晰的列表
```markdown
- ✅ 已完成项
- ⏳ 进行中
- ❌ 未开始
```

### 代码示例
```markdown
\`\`\`python
# 清晰的代码示例
def example():
    pass
\`\`\`
```

### 链接导航
```markdown
- [相关文档](link)
- [另一文档](link)
```

---

## 📝 模板示例

### 新功能文档模板
```markdown
# 功能名称

## 概述
简短描述

## 功能特性
- 特性1
- 特性2

## 使用方法
详细说明

## API参考
相关API

## 示例代码
\`\`\`python
示例
\`\`\`

## 相关文档
- [文档1](link)

---
**创建时间**: YYYY-MM-DD
**版本**: v1.0
```

---

## 🎯 维护责任

### 开发者责任
- 代码变更时更新相关文档
- 添加清晰的注释
- 保持示例代码最新

### 文档维护者责任
- 定期检查文档一致性
- 更新索引和导航
- 归档过时文档
- 维护文档统计

### AI助手责任
- 按照本指南维护文档
- 确保文档间的连锁更新
- 标注更新时间和版本
- 保持文档质量

---

## 🔍 文档审查清单

### 每周检查
- [ ] 所有链接是否有效
- [ ] 统计数据是否一致
- [ ] 示例代码是否可运行
- [ ] 是否有过时信息

### 每月检查
- [ ] 文档结构是否合理
- [ ] 是否需要归档旧文档
- [ ] 索引是否完整
- [ ] 是否需要新建文档

### 发布前检查
- [ ] 所有文档已更新
- [ ] 版本号已更新
- [ ] CHANGELOG 已更新
- [ ] README 反映最新状态

---

## 💡 最佳实践

### DO ✅
- ✅ 同步更新相关文档
- ✅ 保持简洁清晰
- ✅ 使用统一的格式
- ✅ 提供实用示例
- ✅ 维护文档索引
- ✅ 标注更新时间

### DON'T ❌
- ❌ 只更新一个文档
- ❌ 留下无效链接
- ❌ 保留过时信息
- ❌ 遗漏统计更新
- ❌ 忽视文档索引
- ❌ 忘记标注日期

---

## 📈 文档度量

### 质量指标
- **一致性**: 文档间信息是否一致
- **完整性**: 是否覆盖所有功能
- **准确性**: 信息是否正确最新
- **可用性**: 是否易于查找和理解

### 维护指标
- **更新频率**: 与代码变更同步
- **响应时间**: 发现问题后的修复时间
- **覆盖率**: 功能的文档覆盖程度

---

## 🚀 快速参考

### 更新一个文档时，检查：
1. ✅ README.md - 主入口更新了吗？
2. ✅ DOCUMENTATION_INDEX.md - 索引更新了吗？
3. ✅ 相关的状态报告 - 数据一致吗？
4. ✅ AI_QUICK_START.md - 统计更新了吗？
5. ✅ 其他引用该文档的地方 - 链接有效吗？

### 添加新功能时，记得：
1. ✅ 写功能文档
2. ✅ 更新API文档
3. ✅ 更新主README
4. ✅ 更新状态报告
5. ✅ 更新索引文档

---

## 📞 获取帮助

如果不确定应该更新哪些文档：
1. 查看 [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) 的文档依赖图
2. 查看本文档的"更新影响矩阵"
3. 参考"常见更新场景"部分

---

<div align="center">

## ✨ 记住：文档即代码！

**文档和代码同等重要，都需要精心维护**

[返回文档中心](README.md) • [文档索引](DOCUMENTATION_INDEX.md)

</div>

---

**创建时间**: 2026-02-04
**维护者**: Claude Code
**版本**: v1.0
**原则**: Documentation as Code
