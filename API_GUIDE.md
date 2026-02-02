# Novel AI Agent API 使用指南

## 快速开始

### 1. 启动 API 服务器

```bash
# 方式 1: 使用启动脚本
./start_api.sh

# 方式 2: 直接使用 uvicorn
python3 -m uvicorn novel_ai_agent.api.main:app --reload --port 8000
```

启动后，可以访问：
- **API 文档（Swagger UI）**: http://localhost:8000/docs
- **备用文档（ReDoc）**: http://localhost:8000/redoc
- **API 根路径**: http://localhost:8000/

### 2. API 端点概览

#### 小说管理 (`/api/novels`)

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/novels/` | 获取所有小说列表 |
| GET | `/api/novels/{novel_id}` | 获取指定小说详情 |
| POST | `/api/novels/` | 创建新小说（异步） |
| DELETE | `/api/novels/{novel_id}` | 删除指定小说 |
| GET | `/api/novels/{novel_id}/export` | 导出小说 (txt/json) |

#### 章节操作 (`/api/chapters`)

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/chapters/{novel_id}/{chapter_number}` | 获取章节内容 |
| POST | `/api/chapters/write` | 写作章节（异步） |
| POST | `/api/chapters/polish` | 润色章节（异步） |
| POST | `/api/chapters/review` | 评审章节 |

#### 记忆系统 (`/api/memory`)

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/memory/{novel_id}/stats` | 获取记忆统计 |
| POST | `/api/memory/search` | 搜索记忆 |

#### 风格系统 (`/api/styles`)

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/styles/` | 获取所有风格 |
| GET | `/api/styles/{style_name}` | 获取指定风格信息 |
| GET | `/api/styles/recommend/{genre}` | 推荐适合的风格 |

---

## 使用示例

### 1. 获取所有小说列表

```bash
curl http://localhost:8000/api/novels/
```

**响应示例**:
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

### 2. 获取小说详情

```bash
curl http://localhost:8000/api/novels/novel_62c8c6f1
```

**响应示例**:
```json
{
  "id": "novel_62c8c6f1",
  "title": "不同的AI种族",
  "genre": "科幻",
  "theme": "探索AI文明的多样性",
  "style": "刘慈欣",
  "total_chapters": 5,
  "status": "已完成",
  "characters": [
    {
      "name": "张伟",
      "role": "主角",
      "personality": "理性、好奇",
      "background": "AI研究员"
    }
  ],
  "plot_points": [...],
  "chapters": [...]
}
```

### 3. 创建新小说

```bash
curl -X POST http://localhost:8000/api/novels/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "星际探险",
    "genre": "科幻",
    "theme": "探索未知星系",
    "style": "刘慈欣",
    "chapters": 10
  }'
```

**响应示例**:
```json
{
  "success": true,
  "message": "小说创建任务已启动，正在后台处理",
  "data": {
    "title": "星际探险",
    "genre": "科幻",
    "chapters": 10
  }
}
```

> **注意**: 创建小说是异步操作，会在后台执行。可以通过轮询 `/api/novels/` 查看创建进度。

### 4. 获取章节内容

```bash
curl http://localhost:8000/api/chapters/novel_62c8c6f1/1
```

**响应示例**:
```json
{
  "novel_id": "novel_62c8c6f1",
  "chapter_number": 1,
  "title": "觉醒",
  "summary": "AI们开始意识到自己的存在...",
  "content": "在遥远的未来...",
  "word_count": 3000,
  "created_at": "2026-02-02T11:00:00"
}
```

### 5. 评审章节

```bash
curl -X POST http://localhost:8000/api/chapters/review \
  -H "Content-Type: application/json" \
  -d '{
    "novel_id": "novel_62c8c6f1",
    "chapter_number": 1
  }'
```

**响应示例**:
```json
{
  "novel_id": "novel_62c8c6f1",
  "chapter_number": 1,
  "score": 8.7,
  "strengths": [
    "场景描写生动形象",
    "人物塑造立体饱满"
  ],
  "weaknesses": [
    "节奏略显平缓"
  ],
  "suggestions": [
    "可以在开头增加更多悬念",
    "部分科技细节可以更加深入"
  ],
  "overall_comment": "整体质量优秀，具有刘慈欣式的硬科幻风格..."
}
```

### 6. 搜索记忆

```bash
curl -X POST http://localhost:8000/api/memory/search \
  -H "Content-Type: application/json" \
  -d '{
    "novel_id": "novel_62c8c6f1",
    "query": "主角的背景",
    "memory_type": "characters",
    "k": 3
  }'
```

**响应示例**:
```json
{
  "novel_id": "novel_62c8c6f1",
  "query": "主角的背景",
  "results": {
    "characters": [
      "角色名称: 张伟\n角色定位: 主角\n性格: 理性、好奇...",
      "..."
    ]
  }
}
```

### 7. 获取所有风格

```bash
curl http://localhost:8000/api/styles/
```

**响应示例**:
```json
[
  {
    "name": "刘慈欣",
    "description": "硬科幻风格,宏大叙事,理性冷静的笔触",
    "characteristics": [
      "严谨的科学理论基础",
      "宇宙级别的宏大视野",
      "冷静客观的叙述口吻"
    ],
    "suitable_genres": []
  },
  {
    "name": "金庸",
    "description": "武侠风格,注重江湖恩怨和侠义精神,文笔典雅",
    "characteristics": [
      "丰富的武打动作描写",
      "深刻的人物性格塑造"
    ],
    "suitable_genres": []
  }
]
```

### 8. 导出小说

```bash
# 导出为文本格式
curl "http://localhost:8000/api/novels/novel_62c8c6f1/export?format=txt"

# 导出为 JSON 格式
curl "http://localhost:8000/api/novels/novel_62c8c6f1/export?format=json"
```

---

## Python 客户端示例

### 使用 requests 库

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# 1. 获取所有小说
response = requests.get(f"{BASE_URL}/api/novels/")
novels = response.json()
print(f"共有 {len(novels)} 部小说")

# 2. 创建新小说
novel_data = {
    "title": "星际探险",
    "genre": "科幻",
    "theme": "探索未知星系",
    "style": "刘慈欣",
    "chapters": 10
}
response = requests.post(f"{BASE_URL}/api/novels/", json=novel_data)
print(response.json())

# 3. 获取章节内容
novel_id = "novel_62c8c6f1"
chapter_num = 1
response = requests.get(f"{BASE_URL}/api/chapters/{novel_id}/{chapter_num}")
chapter = response.json()
print(f"章节标题: {chapter['title']}")
print(f"字数: {chapter['word_count']}")

# 4. 评审章节
review_data = {
    "novel_id": novel_id,
    "chapter_number": chapter_num
}
response = requests.post(f"{BASE_URL}/api/chapters/review", json=review_data)
review = response.json()
print(f"评分: {review['score']}/10")
print(f"优点: {', '.join(review['strengths'])}")
```

### 使用 httpx (异步)

```python
import httpx
import asyncio

BASE_URL = "http://localhost:8000"

async def main():
    async with httpx.AsyncClient() as client:
        # 获取所有小说
        response = await client.get(f"{BASE_URL}/api/novels/")
        novels = response.json()
        print(f"共有 {len(novels)} 部小说")

        # 获取风格列表
        response = await client.get(f"{BASE_URL}/api/styles/")
        styles = response.json()
        for style in styles:
            print(f"- {style['name']}: {style['description']}")

asyncio.run(main())
```

---

## JavaScript/TypeScript 示例

### 使用 fetch API

```javascript
const BASE_URL = 'http://localhost:8000';

// 1. 获取所有小说
async function getNovels() {
  const response = await fetch(`${BASE_URL}/api/novels/`);
  const novels = await response.json();
  console.log(`共有 ${novels.length} 部小说`);
  return novels;
}

// 2. 创建新小说
async function createNovel(novelData) {
  const response = await fetch(`${BASE_URL}/api/novels/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(novelData),
  });
  return await response.json();
}

// 3. 获取章节内容
async function getChapter(novelId, chapterNumber) {
  const response = await fetch(
    `${BASE_URL}/api/chapters/${novelId}/${chapterNumber}`
  );
  return await response.json();
}

// 使用示例
const novelData = {
  title: '星际探险',
  genre: '科幻',
  theme: '探索未知星系',
  style: '刘慈欣',
  chapters: 10,
};

createNovel(novelData).then(result => {
  console.log('小说创建任务已启动:', result);
});
```

### 使用 axios

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// 获取所有小说
const novels = await api.get('/api/novels/');

// 创建新小说
const result = await api.post('/api/novels/', {
  title: '星际探险',
  genre: '科幻',
  theme: '探索未知星系',
  style: '刘慈欣',
  chapters: 10,
});

// 评审章节
const review = await api.post('/api/chapters/review', {
  novel_id: 'novel_62c8c6f1',
  chapter_number: 1,
});
```

---

## 错误处理

API 使用标准的 HTTP 状态码：

| 状态码 | 说明 |
|-------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

**错误响应格式**:
```json
{
  "error": "错误描述",
  "status_code": 404
}
```

**Python 错误处理示例**:
```python
try:
    response = requests.get(f"{BASE_URL}/api/novels/invalid_id")
    response.raise_for_status()
    novel = response.json()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 404:
        print("小说不存在")
    else:
        print(f"错误: {e.response.json()['error']}")
```

---

## 异步操作说明

以下操作是**异步**的，会在后台执行：

1. **创建小说** (`POST /api/novels/`)
2. **写作章节** (`POST /api/chapters/write`)
3. **润色章节** (`POST /api/chapters/polish`)

这些操作会立即返回成功消息，但实际处理在后台进行。

**轮询检查完成状态**:
```python
import time

# 创建小说
response = requests.post(f"{BASE_URL}/api/novels/", json=novel_data)
print("小说创建任务已启动")

# 轮询检查
while True:
    time.sleep(5)  # 等待 5 秒
    response = requests.get(f"{BASE_URL}/api/novels/")
    novels = response.json()

    # 查找新创建的小说
    new_novel = next(
        (n for n in novels if n['title'] == novel_data['title']),
        None
    )

    if new_novel and new_novel['completed_chapters'] > 0:
        print("小说创建完成！")
        break
```

---

## CORS 配置

当前 API 允许所有来源的跨域请求（开发环境）。

生产环境建议修改 `novel_ai_agent/api/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # 限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 性能建议

1. **批量操作**: 使用并发请求提高效率
2. **缓存**: 对频繁访问的数据进行缓存
3. **限流**: 生产环境建议添加速率限制
4. **超时设置**: 异步操作可能需要较长时间

---

## 下一步开发

- [ ] WebSocket 实时通信（Task #9）
- [ ] 任务队列系统（Celery）
- [ ] 进度查询端点
- [ ] 用户认证和授权
- [ ] API 速率限制
- [ ] 日志和监控

---

## 常见问题

**Q: 如何查看创建小说的进度？**

A: 目前通过轮询 `/api/novels/` 端点查看。后续会添加专门的进度查询接口和 WebSocket 实时通知。

**Q: API 支持并发请求吗？**

A: 是的，FastAPI 基于异步设计，天然支持高并发。

**Q: 如何部署到生产环境？**

A: 使用 Docker 容器化部署，配置 Nginx 反向代理，使用 Gunicorn + Uvicorn workers。详见 Phase 4.5 部署文档。

**Q: 数据存储在哪里？**

A: 小说数据存储在 `novel_ai_agent/data/novels/` 目录下的 JSON 文件中。记忆数据存储在 ChromaDB 向量数据库中。

---

**需要帮助？** 查看 [USAGE_GUIDE.md](USAGE_GUIDE.md) 或提交 Issue。
