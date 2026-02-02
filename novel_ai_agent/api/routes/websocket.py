"""
WebSocket 路由
处理 WebSocket 连接和消息
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import uuid
import json

from novel_ai_agent.api.websocket import manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None)
):
    """
    WebSocket 连接端点

    连接 URL: ws://localhost:8000/ws?client_id=xxx

    如果不提供 client_id，将自动生成一个
    """
    # 如果没有提供 client_id，自动生成一个
    if not client_id:
        client_id = str(uuid.uuid4())

    # 接受连接
    await manager.connect(websocket, client_id)

    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                await handle_client_message(client_id, message)
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    {
                        "type": "error",
                        "message": "无效的 JSON 格式"
                    },
                    client_id
                )
            except Exception as e:
                await manager.send_personal_message(
                    {
                        "type": "error",
                        "message": f"处理消息失败: {str(e)}"
                    },
                    client_id
                )

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        print(f"客户端 {client_id} 断开连接")


async def handle_client_message(client_id: str, message: dict):
    """
    处理客户端消息

    支持的消息类型：
    - subscribe: 订阅小说更新
    - unsubscribe: 取消订阅
    - subscribe_global: 订阅全局消息
    - unsubscribe_global: 取消全局订阅
    - ping: 心跳检测
    - get_stats: 获取连接统计

    Args:
        client_id: 客户端ID
        message: 消息内容
    """
    msg_type = message.get("type")

    if msg_type == "subscribe":
        # 订阅小说更新
        novel_id = message.get("novel_id")
        if novel_id:
            manager.subscribe_to_novel(client_id, novel_id)
            await manager.send_personal_message(
                {
                    "type": "subscribed",
                    "novel_id": novel_id,
                    "message": f"已订阅小说 {novel_id} 的更新"
                },
                client_id
            )
        else:
            await manager.send_personal_message(
                {
                    "type": "error",
                    "message": "缺少 novel_id 参数"
                },
                client_id
            )

    elif msg_type == "unsubscribe":
        # 取消订阅
        novel_id = message.get("novel_id")
        if novel_id:
            manager.unsubscribe_from_novel(client_id, novel_id)
            await manager.send_personal_message(
                {
                    "type": "unsubscribed",
                    "novel_id": novel_id,
                    "message": f"已取消订阅小说 {novel_id}"
                },
                client_id
            )

    elif msg_type == "subscribe_global":
        # 订阅全局消息
        manager.subscribe_global(client_id)
        await manager.send_personal_message(
            {
                "type": "subscribed_global",
                "message": "已订阅全局消息"
            },
            client_id
        )

    elif msg_type == "unsubscribe_global":
        # 取消全局订阅
        manager.unsubscribe_global(client_id)
        await manager.send_personal_message(
            {
                "type": "unsubscribed_global",
                "message": "已取消全局订阅"
            },
            client_id
        )

    elif msg_type == "ping":
        # 心跳检测
        await manager.send_personal_message(
            {
                "type": "pong",
                "message": "连接正常"
            },
            client_id
        )

    elif msg_type == "get_stats":
        # 获取连接统计
        stats = manager.get_stats()
        await manager.send_personal_message(
            {
                "type": "stats",
                "data": stats
            },
            client_id
        )

    else:
        # 未知消息类型
        await manager.send_personal_message(
            {
                "type": "error",
                "message": f"未知的消息类型: {msg_type}"
            },
            client_id
        )


@router.get("/ws/stats")
async def get_websocket_stats():
    """
    获取 WebSocket 连接统计（HTTP 端点）
    """
    return manager.get_stats()
