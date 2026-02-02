# 快速启动 Novel AI Agent API

## 🚀 一分钟快速启动

### 1. 启动 API 服务器

```bash
cd /Users/keithxi/Documents/work/Nover

# 启动服务器
./start_api.sh
```

服务器启动后会显示：
```
🚀 启动 Novel AI Agent API 服务器...

API 文档: http://localhost:8000/docs
备用文档: http://localhost:8000/redoc

按 Ctrl+C 停止服务器
```

### 2. 打开 API 文档

在浏览器中访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. 测试 API

#### 方式 1: 使用 Swagger UI（推荐）

1. 打开 http://localhost:8000/docs
2. 点击任意端点（如 `GET /api/novels/`）
3. 点击 "Try it out"
4. 点击 "Execute"
5. 查看响应结果

#### 方式 2: 使用 curl

```bash
# 获取所有小说列表
curl http://localhost:8000/api/novels/

# 获取所有风格
curl http://localhost:8000/api/styles/

# 获取健康状态
curl http://localhost:8000/health
```

---

## 📚 常用操作示例

### 1. 查看现有小说

```bash
curl http://localhost:8000/api/novels/
```

如果有已完成的小说（如 `novel_62c8c6f1`），会返回：
```json
[
  {
    "id": "novel_62c8c6f1",
    "title": "不同的AI种族",
    "genre": "科幻",
    "style": "刘慈欣",
    "total_chapters": 5,
    "completed_chapters": 5,
    "status": "已完成",
    "created_at": "2026-02-02T10:00:00"
  }
]
```

### 2. 查看小说详情

```bash
curl http://localhost:8000/api/novels/novel_62c8c6f1
```

返回完整的小说信息，包括角色、情节点、章节列表。

### 3. 获取章节内容

```bash
curl http://localhost:8000/api/chapters/novel_62c8c6f1/1
```

返回第一章的完整内容。

### 4. 评审章节

```bash
curl -X POST http://localhost:8000/api/chapters/review \
  -H "Content-Type: application/json" \
  -d '{
    "novel_id": "novel_62c8c6f1",
    "chapter_number": 1
  }'
```

返回评审结果（评分、优点、缺点、建议）。

### 5. 创建新小说

```bash
curl -X POST http://localhost:8000/api/novels/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试小说",
    "genre": "科幻",
    "theme": "AI与人类的未来",
    "style": "刘慈欣",
    "chapters": 3
  }'
```

这是一个异步操作，会在后台执行。

### 6. 查看所有可用风格

```bash
curl http://localhost:8000/api/styles/
```

返回 10 种可用的写作风格。

---

## 🐍 Python 客户端示例

创建文件 `test_api.py`:

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. 获取所有小说
response = requests.get(f"{BASE_URL}/api/novels/")
novels = response.json()
print(f"📚 共有 {len(novels)} 部小说")
for novel in novels:
    print(f"  - {novel['title']} ({novel['genre']}, {novel['style']})")

# 2. 获取所有风格
response = requests.get(f"{BASE_URL}/api/styles/")
styles = response.json()
print(f"\n🎨 共有 {len(styles)} 种风格")
for style in styles[:3]:  # 只显示前3个
    print(f"  - {style['name']}: {style['description']}")

# 3. 如果有小说，获取第一个小说的详情
if novels:
    novel_id = novels[0]['id']
    response = requests.get(f"{BASE_URL}/api/novels/{novel_id}")
    novel = response.json()
    print(f"\n📖 小说《{novel['title']}》详情:")
    print(f"  主题: {novel['theme']}")
    print(f"  角色数: {len(novel['characters'])}")
    print(f"  章节数: {len(novel['chapters'])}")

    # 4. 评审第一章
    if novel['chapters']:
        print(f"\n⭐ 评审第一章...")
        response = requests.post(
            f"{BASE_URL}/api/chapters/review",
            json={
                "novel_id": novel_id,
                "chapter_number": 1
            }
        )
        review = response.json()
        print(f"  评分: {review['score']}/10")
        print(f"  优点: {', '.join(review['strengths'][:2])}")
```

运行：
```bash
python3 test_api.py
```

---

## 💻 JavaScript/Node.js 示例

创建文件 `test_api.js`:

```javascript
const BASE_URL = 'http://localhost:8000';

async function testAPI() {
  // 1. 获取所有小说
  const novelsRes = await fetch(`${BASE_URL}/api/novels/`);
  const novels = await novelsRes.json();
  console.log(`📚 共有 ${novels.length} 部小说`);

  // 2. 获取所有风格
  const stylesRes = await fetch(`${BASE_URL}/api/styles/`);
  const styles = await stylesRes.json();
  console.log(`🎨 共有 ${styles.length} 种风格`);

  // 3. 如果有小说，评审第一章
  if (novels.length > 0) {
    const novelId = novels[0].id;
    const reviewRes = await fetch(`${BASE_URL}/api/chapters/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        novel_id: novelId,
        chapter_number: 1
      })
    });
    const review = await reviewRes.json();
    console.log(`⭐ 评分: ${review.score}/10`);
  }
}

testAPI();
```

运行：
```bash
node test_api.js
```

---

## 📊 API 端点速查

| 功能 | 方法 | 端点 | 说明 |
|------|------|------|------|
| 列出小说 | GET | `/api/novels/` | 获取所有小说 |
| 小说详情 | GET | `/api/novels/{id}` | 获取指定小说 |
| 创建小说 | POST | `/api/novels/` | 创建新小说（异步） |
| 删除小说 | DELETE | `/api/novels/{id}` | 删除小说 |
| 导出小说 | GET | `/api/novels/{id}/export` | 导出 txt/json |
| 章节内容 | GET | `/api/chapters/{id}/{num}` | 获取章节 |
| 写作章节 | POST | `/api/chapters/write` | 写作（异步） |
| 润色章节 | POST | `/api/chapters/polish` | 润色（异步） |
| 评审章节 | POST | `/api/chapters/review` | 评审（同步） |
| 记忆统计 | GET | `/api/memory/{id}/stats` | 统计信息 |
| 搜索记忆 | POST | `/api/memory/search` | 语义搜索 |
| 风格列表 | GET | `/api/styles/` | 所有风格 |
| 风格详情 | GET | `/api/styles/{name}` | 指定风格 |
| 推荐风格 | GET | `/api/styles/recommend/{genre}` | 风格推荐 |

---

## 🔧 故障排查

### 问题 1: 启动失败

```bash
# 检查依赖是否安装
pip3 list | grep fastapi
pip3 list | grep uvicorn

# 如果没有，安装依赖
pip3 install fastapi uvicorn python-multipart websockets
```

### 问题 2: 端口被占用

```bash
# 修改端口
python3 -m uvicorn novel_ai_agent.api.main:app --reload --port 8001
```

### 问题 3: 导入错误

```bash
# 确保在项目根目录
cd /Users/keithxi/Documents/work/Nover

# 测试导入
python3 -c "from novel_ai_agent.api.main import app; print('OK')"
```

### 问题 4: 找不到小说

```bash
# 检查小说文件是否存在
ls -la novel_ai_agent/data/novels/*.json
```

---

## 📚 完整文档

- **API 使用指南**: [API_GUIDE.md](API_GUIDE.md) - 完整的 API 文档
- **完成报告**: [PHASE4.1_COMPLETED.md](PHASE4.1_COMPLETED.md) - Phase 4.1 详细报告
- **项目说明**: [README.md](README.md) - 项目总体说明

---

## 🎯 下一步

1. **测试 API**: 使用 Swagger UI 测试所有端点
2. **开发前端**: 开始 Phase 4.2 React 前端开发
3. **WebSocket**: 实现 Task #9 实时通信功能

---

## ✨ 快速命令

```bash
# 启动 API
./start_api.sh

# 测试健康状态
curl http://localhost:8000/health

# 查看所有小说
curl http://localhost:8000/api/novels/

# 查看所有风格
curl http://localhost:8000/api/styles/

# 打开文档
open http://localhost:8000/docs
```

---

**需要帮助？** 查看 [API_GUIDE.md](API_GUIDE.md) 或 [PHASE4.1_COMPLETED.md](PHASE4.1_COMPLETED.md)
