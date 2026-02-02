#!/usr/bin/env python3
"""
WebSocket 实时进度演示
模拟一个章节写作任务，展示实时进度推送
"""
import asyncio
import websockets
import json
from datetime import datetime


async def simulate_progress_updates():
    """模拟进度更新"""
    # 这个函数会被服务器调用来推送进度
    # 这里我们只是演示客户端如何接收
    pass


async def demo_client():
    """演示客户端"""
    uri = "ws://localhost:8000/ws?client_id=demo_progress_client"

    print("=" * 70)
    print("📡 WebSocket 实时进度演示")
    print("=" * 70)
    print()
    print("这个演示展示了如何使用 WebSocket 实时接收创作进度。")
    print()
    print("🔌 连接到服务器...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ 连接成功！")
            print()

            # 接收欢迎消息
            message = await websocket.recv()
            data = json.loads(message)
            print(f"📨 {data['message']}")
            print()

            # 订阅小说
            novel_id = "novel_62c8c6f1"
            print(f"📤 订阅小说: {novel_id}")
            await websocket.send(json.dumps({
                "type": "subscribe",
                "novel_id": novel_id
            }))

            response = await websocket.recv()
            data = json.loads(response)
            print(f"✅ {data['message']}")
            print()

            print("=" * 70)
            print("📊 模拟进度推送演示")
            print("=" * 70)
            print()
            print("如果现在有任务正在运行，你会看到类似这样的消息：")
            print()

            # 模拟显示进度消息的格式
            demo_messages = [
                {
                    "type": "progress",
                    "novel_id": novel_id,
                    "task_type": "write_chapter",
                    "progress": 0,
                    "message": "开始写作第3章...",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "type": "progress",
                    "novel_id": novel_id,
                    "task_type": "write_chapter",
                    "progress": 25,
                    "message": "构思章节大纲...",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "type": "progress",
                    "novel_id": novel_id,
                    "task_type": "write_chapter",
                    "progress": 50,
                    "message": "正在生成内容...",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "type": "progress",
                    "novel_id": novel_id,
                    "task_type": "write_chapter",
                    "progress": 75,
                    "message": "润色文字...",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "type": "task_complete",
                    "novel_id": novel_id,
                    "task_type": "write_chapter",
                    "result": {
                        "chapter_number": 3,
                        "word_count": 3000
                    },
                    "timestamp": datetime.now().isoformat()
                }
            ]

            print("💡 模拟的进度消息示例:")
            print()
            for msg in demo_messages:
                if msg['type'] == 'progress':
                    progress = msg['progress']
                    bar_length = 30
                    filled = int(bar_length * progress / 100)
                    bar = '█' * filled + '░' * (bar_length - filled)
                    print(f"[{bar}] {progress}% - {msg['message']}")
                    await asyncio.sleep(0.5)
                elif msg['type'] == 'task_complete':
                    print()
                    print("✅ 任务完成！")
                    print(f"   章节号: {msg['result']['chapter_number']}")
                    print(f"   字数: {msg['result']['word_count']}")

            print()
            print("=" * 70)
            print("⏳ 等待实际任务（10秒）...")
            print("=" * 70)
            print()
            print("提示: 如果你现在创建小说或写作章节，你会在这里看到实时进度！")
            print()
            print("要测试实时推送，请在另一个终端运行：")
            print("  curl -X POST http://localhost:8000/api/novels/ \\")
            print("    -H 'Content-Type: application/json' \\")
            print("    -d '{\"title\": \"测试\", \"genre\": \"科幻\", \"theme\": \"AI\",")
            print("         \"style\": \"刘慈欣\", \"chapters\": 1}'")
            print()

            # 等待实际的推送消息
            try:
                for i in range(10):
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(response)

                        # 显示收到的消息
                        if data['type'] == 'progress':
                            progress = data.get('progress', 0)
                            bar_length = 30
                            filled = int(bar_length * progress / 100)
                            bar = '█' * filled + '░' * (bar_length - filled)
                            print(f"📨 [{bar}] {progress}% - {data['message']}")

                        elif data['type'] == 'task_complete':
                            print()
                            print("📨 ✅ 任务完成！")
                            print(f"   结果: {json.dumps(data['result'], indent=2, ensure_ascii=False)}")
                            break

                        elif data['type'] == 'task_error':
                            print()
                            print(f"📨 ❌ 任务失败: {data['error']}")
                            break

                    except asyncio.TimeoutError:
                        print(f"⏰ 等待中... ({i+1}/10)")
                        continue

            except Exception as e:
                print(f"接收消息时出错: {e}")

            print()
            print("=" * 70)
            print("演示结束")
            print("=" * 70)
            print()
            print("📖 更多信息:")
            print("  - 查看文档: WEBSOCKET_GUIDE.md")
            print("  - HTML 测试: open test_websocket.html")
            print("  - API 文档: http://localhost:8000/docs")
            print()

    except Exception as e:
        print(f"❌ 错误: {e}")
        print()
        print("提示: 请确保 API 服务器正在运行")
        print("启动命令: ./start_api.sh")


if __name__ == "__main__":
    asyncio.run(demo_client())
