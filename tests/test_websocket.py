#!/usr/bin/env python3
"""
WebSocket 测试客户端 (Python)
测试 WebSocket 连接和消息功能
"""
import asyncio
import websockets
import json
from datetime import datetime


async def test_websocket():
    """测试 WebSocket 连接"""
    uri = "ws://localhost:8000/ws?client_id=test_client_001"

    print("🔌 连接到 WebSocket 服务器...")
    print(f"URI: {uri}\n")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ 连接成功！\n")

            # 1. 接收欢迎消息
            message = await websocket.recv()
            data = json.loads(message)
            print(f"📨 接收: {json.dumps(data, indent=2, ensure_ascii=False)}\n")

            # 2. 发送 ping
            print("📤 发送 ping...")
            await websocket.send(json.dumps({"type": "ping"}))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📨 接收: {json.dumps(data, indent=2, ensure_ascii=False)}\n")

            # 3. 订阅小说
            novel_id = "novel_62c8c6f1"
            print(f"📤 订阅小说: {novel_id}...")
            await websocket.send(json.dumps({
                "type": "subscribe",
                "novel_id": novel_id
            }))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📨 接收: {json.dumps(data, indent=2, ensure_ascii=False)}\n")

            # 4. 获取统计信息
            print("📤 请求统计信息...")
            await websocket.send(json.dumps({"type": "get_stats"}))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📨 接收: {json.dumps(data, indent=2, ensure_ascii=False)}\n")

            # 5. 订阅全局消息
            print("📤 订阅全局消息...")
            await websocket.send(json.dumps({"type": "subscribe_global"}))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📨 接收: {json.dumps(data, indent=2, ensure_ascii=False)}\n")

            # 6. 模拟接收进度更新（等待5秒）
            print("⏳ 等待消息（5秒）...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                print(f"📨 接收到推送: {json.dumps(data, indent=2, ensure_ascii=False)}\n")
            except asyncio.TimeoutError:
                print("⏰ 未收到推送消息（正常，因为没有活动任务）\n")

            # 7. 取消订阅
            print(f"📤 取消订阅小说: {novel_id}...")
            await websocket.send(json.dumps({
                "type": "unsubscribe",
                "novel_id": novel_id
            }))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📨 接收: {json.dumps(data, indent=2, ensure_ascii=False)}\n")

            print("✅ 测试完成！所有功能正常工作。")

    except Exception as e:
        print(f"❌ 错误: {e}")
        print("\n提示: 请确保 API 服务器正在运行")
        print("启动命令: ./start_api.sh")


if __name__ == "__main__":
    print("=" * 60)
    print("WebSocket 功能测试")
    print("=" * 60)
    print()

    asyncio.run(test_websocket())
