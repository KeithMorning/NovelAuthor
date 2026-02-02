# NumPy 版本问题修复指南

## 问题描述

运行时出现错误：
```
Numpy is not available
A module that was compiled using NumPy 1.x cannot be run in NumPy 2.4.1
```

## 原因

sentence-transformers 等库是用 NumPy 1.x 编译的，与 NumPy 2.x 不兼容。

## 解决方案

### 方案 1：降级 NumPy（推荐）

```bash
pip3 uninstall numpy -y
pip3 install "numpy<2.0"
```

### 方案 2：更新所有依赖

```bash
pip3 install --upgrade sentence-transformers torch transformers
```

### 方案 3：临时禁用记忆系统

如果你现在不需要记忆功能，可以临时禁用：

修改 `novel_ai_agent/agents/coordinator.py`：

```python
# 注释掉记忆系统相关代码（第157-159行和第241-243行）

# 第157-159行
# memory_manager = get_memory_manager(novel_id)
# memory_manager.load_novel_to_memory(novel)

# 第241-243行
# memory_manager = get_memory_manager(novel_id)
# memory_manager.add_chapter_to_memory(chapter)
```

## 推荐做法

使用方案 1（最简单）：

```bash
cd /Users/keithxi/Documents/work/Nover
pip3 uninstall numpy -y
pip3 install "numpy<2.0"
```

然后重新测试：

```bash
python3 main.py create --title "测试" --genre "武侠" --theme "测试主题" --style "金庸" --chapters 3
```

## 验证修复

```bash
python3 -c "import numpy; print(f'NumPy version: {numpy.__version__}')"
```

应该显示类似：`NumPy version: 1.26.x`

---

**修复完成后，系统应该可以正常运行了！** ✅
