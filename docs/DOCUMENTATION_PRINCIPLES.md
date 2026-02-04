# 📖 文档核心原则

> **Documentation as Code & Code as Documentation**
>
> 文档和代码是一体的，必须同步更新

---

## 🎯 核心原则

### 1️⃣ 文档即代码 (Documentation as Code)

**更新一个文档时，必须更新所有相关文档**

```
更新文档A
    ↓
检查哪些文档引用了A
    ↓
同步更新所有引用文档
    ↓
更新文档索引
```

### 2️⃣ 代码即文档 (Code as Documentation)

**⚠️ 更新代码时，必须同步更新文档！**

```
修改代码
    ↓
更新代码注释（Swagger/DocString）
    ↓
更新相关功能文档
    ↓
更新API文档
    ↓
更新使用示例
```

---

## ✅ 快速检查清单

### 当你修改代码时
- [ ] 更新了函数/类的注释吗？
- [ ] 更新了 Swagger/OpenAPI 注释吗？
- [ ] 更新了 API_GUIDE.md 吗？
- [ ] 更新了 README.md（如影响核心功能）吗？
- [ ] 更新了示例代码吗？
- [ ] 更新了相关统计数据吗？

### 当你修改文档时
- [ ] 检查了其他文档是否引用它吗？
- [ ] 更新了所有引用的文档吗？
- [ ] 更新了 DOCUMENTATION_INDEX.md 吗？
- [ ] 更新了 docs/README.md 吗？
- [ ] 验证了所有链接有效吗？
- [ ] 更新了文档日期吗？

---

## 🔗 关键文档

### 必须了解
1. **[DOCUMENTATION_GUIDELINES.md](DOCUMENTATION_GUIDELINES.md)** - 完整的文档维护指南
2. **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - 文档索引和依赖关系

### 核心依赖链
```
README.md (主入口)
    ↓
docs/AI_QUICK_START.md (AI快速理解)
docs/DOCUMENTATION_INDEX.md (完整索引)
    ↓
所有其他文档
```

---

## 💡 记住

> **文档不是可选的，它和代码一样重要！**
>
> **每次提交代码，都要提交对应的文档更新！**

---

## 🚀 开始行动

1. 阅读 [DOCUMENTATION_GUIDELINES.md](DOCUMENTATION_GUIDELINES.md)
2. 理解文档依赖关系
3. 在每次代码/文档变更时遵循指南

---

**创建时间**: 2026-02-04
**原则**: Documentation as Code & Code as Documentation
