# WebSocket 实时通信使用指南

## 📡 概述

Novel AI Agent API 提供了 WebSocket 实时通信功能，可以：
- 实时接收小说创作进度
- 实时接收章节生成状态
- 实时接收任务完成通知
- 双向通信，支持订阅/取消订阅

---

## 🚀 快速开始

### 1. 连接到 WebSocket

#### JavaScript/浏览器

```javascript
const ws = new WebSocket('ws://localhost:8000/ws?client_id=my_client');

ws.onopen = function() {
    console.log('连接成功');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('收到消息:', data);
};

ws.onerror = function(error) {
    console.error('错误:', error);
};

ws.onclose = function() {
    console.log('连接关闭');
};
```

#### Python

```python
import asyncio
import websockets
import json

async def connect():
    uri = "ws://localhost:8000/ws?client_id=my_client"
    async with websockets.connect(uri) as websocket:
        # 接收消息
        message = await websocket.recv()
        data = json.loads(message)
        print(data)

        # 发送消息
        await websocket.send(json.dumps({
            "type": "subscribe",
            "novel_id": "novel_123"
        }))

asyncio.run(connect())
```

### 2. 使用测试客户端

#### 方式 1: HTML 测试客户端

```bash
# 在浏览器中打开
open test_websocket.html
```

**功能**:
- 可视化界面
- 连接/断开
- 订阅/取消订阅
- 实时查看消息
- 获取连接统计

#### 方式 2: Python 测试脚本

```bash
# 确保 API 服务器正在运行
./start_api.sh

# 运行测试
python3 test_websocket.py
```

---

## 📨 消息格式

### 客户端 → 服务器

#### 1. 订阅小说更新

```json
{
    "type": "subscribe",
    "novel_id": "novel_62c8c6f1"
}
```

**响应**:
```json
{
    "type": "subscribed",
    "novel_id": "novel_62c8c6f1",
    "message": "已订阅小说 novel_62c8c6f1 的更新"
}
```

#### 2. 取消订阅小说

```json
{
    "type": "unsubscribe",
    "novel_id": "novel_62c8c6f1"
}
```

#### 3. 订阅全局消息

```json
{
    "type": "subscribe_global"
}
```

订阅后将接收所有小说的更新。

#### 4. 取消全局订阅

```json
{
    "type": "unsubscribe_global"
}
```

#### 5. 心跳检测

```json
{
    "type": "ping"
}
```

**响应**:
```json
{
    "type": "pong",
    "message": "连接正常"
}
```

#### 6. 获取统计信息

```json
{
    "type": "get_stats"
}
```

**响应**:
```json
{
    "type": "stats",
    "data": {
        "total_connections": 3,
        "global_subscribers": 1,
        "novel_subscriptions": {
            "novel_62c8c6f1": 2
        }
    }
}
```

---

### 服务器 → 客户端

#### 1. 连接成功

```json
{
    "type": "connected",
    "client_id": "client_xxx",
    "message": "WebSocket 连接成功",
    "timestamp": "2026-02-02T12:00:00"
}
```

#### 2. 进度更新

```json
{
    "type": "progress",
    "novel_id": "novel_62c8c6f1",
    "task_type": "write_chapter",
    "progress": 50,
    "message": "正在写作第3章...",
    "timestamp": "2026-02-02T12:05:00"
}
```

**task_type 可能的值**:
- `create_novel` - 创建小说
- `write_chapter` - 写作章节
- `polish_chapter` - 润色章节
- `review_chapter` - 评审章节

**progress**: 0-100 的整数，表示进度百分比

#### 3. 任务完成

```json
{
    "type": "task_complete",
    "novel_id": "novel_62c8c6f1",
    "task_type": "write_chapter",
    "result": {
        "chapter_number": 3,
        "word_count": 3000
    },
    "timestamp": "2026-02-02T12:10:00"
}
```

#### 4. 任务错误

```json
{
    "type": "task_error",
    "novel_id": "novel_62c8c6f1",
    "task_type": "write_chapter",
    "error": "LLM API 调用失败",
    "timestamp": "2026-02-02T12:10:00"
}
```

#### 5. 任务开始

```json
{
    "type": "task_start",
    "task_type": "create_novel",
    "title": "星际探险"
}
```

---

## 🎯 使用场景

### 场景 1: 监控小说创作进度

```javascript
const ws = new WebSocket('ws://localhost:8000/ws?client_id=monitor');

ws.onopen = function() {
    // 订阅特定小说
    ws.send(JSON.stringify({
        type: 'subscribe',
        novel_id: 'novel_62c8c6f1'
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);

    if (data.type === 'progress') {
        // 更新进度条
        updateProgressBar(data.progress);
        console.log(`${data.message} (${data.progress}%)`);
    }

    if (data.type === 'task_complete') {
        console.log('任务完成！', data.result);
        showNotification('章节创作完成');
    }

    if (data.type === 'task_error') {
        console.error('任务失败:', data.error);
        showError(data.error);
    }
};
```

### 场景 2: 全局监控仪表板

```javascript
const ws = new WebSocket('ws://localhost:8000/ws?client_id=dashboard');

ws.onopen = function() {
    // 订阅全局消息
    ws.send(JSON.stringify({
        type: 'subscribe_global'
    }));

    // 定期获取统计信息
    setInterval(() => {
        ws.send(JSON.stringify({ type: 'get_stats' }));
    }, 5000);
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);

    if (data.type === 'stats') {
        // 更新仪表板
        updateDashboard(data.data);
    }

    if (data.type === 'task_start') {
        // 显示新任务
        addTaskToList(data);
    }
};
```

### 场景 3: 多小说同时监控

```javascript
const ws = new WebSocket('ws://localhost:8000/ws?client_id=multi_monitor');

const novels = ['novel_001', 'novel_002', 'novel_003'];

ws.onopen = function() {
    // 订阅多个小说
    novels.forEach(novelId => {
        ws.send(JSON.stringify({
            type: 'subscribe',
            novel_id: novelId
        }));
    });
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);

    // 根据 novel_id 更新相应的界面
    const novelId = data.novel_id;
    if (novelId) {
        updateNovelProgress(novelId, data);
    }
};
```

---

## 🛠️ React 集成示例

```jsx
import React, { useEffect, useState } from 'react';

function NovelProgressMonitor({ novelId }) {
    const [progress, setProgress] = useState(0);
    const [message, setMessage] = useState('');
    const [ws, setWs] = useState(null);

    useEffect(() => {
        const websocket = new WebSocket(
            `ws://localhost:8000/ws?client_id=react_${novelId}`
        );

        websocket.onopen = () => {
            console.log('WebSocket 连接成功');
            // 订阅小说
            websocket.send(JSON.stringify({
                type: 'subscribe',
                novel_id: novelId
            }));
        };

        websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'progress') {
                setProgress(data.progress);
                setMessage(data.message);
            }

            if (data.type === 'task_complete') {
                setProgress(100);
                setMessage('任务完成！');
            }
        };

        websocket.onerror = (error) => {
            console.error('WebSocket 错误:', error);
        };

        setWs(websocket);

        return () => {
            websocket.close();
        };
    }, [novelId]);

    return (
        <div>
            <h3>创作进度</h3>
            <div className="progress-bar">
                <div
                    className="progress-fill"
                    style={{ width: `${progress}%` }}
                />
            </div>
            <p>{message}</p>
            <p>{progress}% 完成</p>
        </div>
    );
}
```

---

## 🔧 Vue 集成示例

```vue
<template>
  <div class="progress-monitor">
    <h3>创作进度</h3>
    <el-progress :percentage="progress" />
    <p>{{ message }}</p>
  </div>
</template>

<script>
export default {
  name: 'NovelProgressMonitor',
  props: {
    novelId: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      ws: null,
      progress: 0,
      message: ''
    };
  },
  mounted() {
    this.connectWebSocket();
  },
  beforeUnmount() {
    if (this.ws) {
      this.ws.close();
    }
  },
  methods: {
    connectWebSocket() {
      this.ws = new WebSocket(
        `ws://localhost:8000/ws?client_id=vue_${this.novelId}`
      );

      this.ws.onopen = () => {
        this.ws.send(JSON.stringify({
          type: 'subscribe',
          novel_id: this.novelId
        }));
      };

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'progress') {
          this.progress = data.progress;
          this.message = data.message;
        }

        if (data.type === 'task_complete') {
          this.progress = 100;
          this.message = '任务完成！';
          this.$emit('task-complete', data.result);
        }
      };
    }
  }
};
</script>
```

---

## 🎨 HTML/CSS 进度条示例

```html
<!DOCTYPE html>
<html>
<head>
    <style>
        .progress-container {
            width: 100%;
            background-color: #f0f0f0;
            border-radius: 4px;
            overflow: hidden;
        }
        .progress-bar {
            height: 30px;
            background-color: #4CAF50;
            text-align: center;
            line-height: 30px;
            color: white;
            transition: width 0.3s ease;
        }
        .status {
            margin-top: 10px;
            font-size: 14px;
            color: #666;
        }
    </style>
</head>
<body>
    <h2>小说创作进度</h2>
    <div class="progress-container">
        <div class="progress-bar" id="progressBar">0%</div>
    </div>
    <div class="status" id="status">等待连接...</div>

    <script>
        const ws = new WebSocket('ws://localhost:8000/ws?client_id=progress_demo');

        ws.onopen = function() {
            document.getElementById('status').textContent = '已连接';
            ws.send(JSON.stringify({
                type: 'subscribe',
                novel_id: 'novel_62c8c6f1'
            }));
        };

        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);

            if (data.type === 'progress') {
                const progressBar = document.getElementById('progressBar');
                progressBar.style.width = data.progress + '%';
                progressBar.textContent = data.progress + '%';
                document.getElementById('status').textContent = data.message;
            }
        };
    </script>
</body>
</html>
```

---

## 📊 API 端点

### HTTP 端点

```bash
GET /ws/stats
```

获取 WebSocket 连接统计信息（不需要 WebSocket 连接）。

**响应**:
```json
{
    "total_connections": 5,
    "global_subscribers": 2,
    "novel_subscriptions": {
        "novel_62c8c6f1": 3,
        "novel_abc123": 1
    }
}
```

---

## 🔒 安全建议

### 1. 认证

生产环境建议添加认证：

```javascript
const token = getUserToken();
const ws = new WebSocket(
    `ws://api.example.com/ws?client_id=${clientId}&token=${token}`
);
```

### 2. 心跳保活

定期发送 ping 保持连接：

```javascript
setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
    }
}, 30000); // 每30秒
```

### 3. 自动重连

```javascript
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

function connect() {
    const ws = new WebSocket('ws://localhost:8000/ws');

    ws.onclose = function() {
        if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            console.log(`重连中... (${reconnectAttempts}/${maxReconnectAttempts})`);
            setTimeout(connect, 1000 * reconnectAttempts);
        }
    };

    ws.onopen = function() {
        reconnectAttempts = 0; // 重置计数
    };
}
```

---

## ❓ 常见问题

### Q1: 如何知道连接是否还活着？

定期发送 `ping` 消息：

```javascript
setInterval(() => {
    ws.send(JSON.stringify({ type: 'ping' }));
}, 30000);
```

### Q2: 可以同时订阅多个小说吗？

可以！发送多个 `subscribe` 消息：

```javascript
['novel_001', 'novel_002'].forEach(novelId => {
    ws.send(JSON.stringify({
        type: 'subscribe',
        novel_id: novelId
    }));
});
```

### Q3: 如何处理连接断开？

实现自动重连逻辑（见上文"安全建议"部分）。

### Q4: WebSocket 支持 HTTPS/WSS 吗？

支持。生产环境使用 `wss://` 协议：

```javascript
const ws = new WebSocket('wss://api.example.com/ws');
```

### Q5: 消息会丢失吗？

WebSocket 是可靠的协议，但建议：
- 实现心跳保活
- 自动重连
- 关键操作使用 HTTP API 确认

---

## 🧪 测试工具

### 1. HTML 测试客户端

```bash
open test_websocket.html
```

可视化测试界面，适合手动测试。

### 2. Python 测试脚本

```bash
python3 test_websocket.py
```

自动化测试，验证所有功能。

### 3. 浏览器开发工具

Chrome DevTools → Network → WS 标签页

可以查看：
- 连接状态
- 发送/接收的消息
- 连接时长

---

## 📚 参考资料

- FastAPI WebSocket 文档: https://fastapi.tiangolo.com/advanced/websockets/
- WebSocket MDN: https://developer.mozilla.org/en-US/docs/Web/API/WebSocket
- Python websockets: https://websockets.readthedocs.io/

---

**需要帮助？** 查看 [API_GUIDE.md](API_GUIDE.md) 或提交 Issue。
