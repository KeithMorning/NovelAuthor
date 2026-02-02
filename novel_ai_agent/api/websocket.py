"""
WebSocket 连接管理
提供实时通信功能，推送创作进度和状态更新
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import json
import asyncio
from datetime import datetime


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # 活跃连接: {client_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}

        # 按小说ID分组的连接: {novel_id: Set[client_id]}
        self.novel_subscribers: Dict[str, Set[str]] = {}

        # 全局订阅者（接收所有消息）
        self.global_subscribers: Set[str] = set()

    async def connect(self, websocket: WebSocket, client_id: str):
        """
        接受 WebSocket 连接

        Args:
            websocket: WebSocket 连接对象
            client_id: 客户端唯一ID
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket

        # 发送欢迎消息
        await self.send_personal_message(
            {
                "type": "connected",
                "client_id": client_id,
                "message": "WebSocket 连接成功",
                "timestamp": datetime.now().isoformat()
            },
            client_id
        )

    def disconnect(self, client_id: str):
        """
        断开连接并清理

        Args:
            client_id: 客户端ID
        """
        # 从活跃连接中移除
        if client_id in self.active_connections:
            del self.active_connections[client_id]

        # 从全局订阅中移除
        if client_id in self.global_subscribers:
            self.global_subscribers.remove(client_id)

        # 从所有小说订阅中移除
        for subscribers in self.novel_subscribers.values():
            if client_id in subscribers:
                subscribers.remove(client_id)

    async def send_personal_message(self, message: dict, client_id: str):
        """
        发送消息给指定客户端

        Args:
            message: 消息内容（字典）
            client_id: 客户端ID
        """
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                print(f"发送消息失败: {e}")
                self.disconnect(client_id)

    async def broadcast(self, message: dict):
        """
        广播消息给所有连接的客户端

        Args:
            message: 消息内容（字典）
        """
        disconnected_clients = []

        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"广播消息失败 ({client_id}): {e}")
                disconnected_clients.append(client_id)

        # 清理断开的连接
        for client_id in disconnected_clients:
            self.disconnect(client_id)

    async def broadcast_to_novel(self, message: dict, novel_id: str):
        """
        向订阅特定小说的客户端广播消息

        Args:
            message: 消息内容（字典）
            novel_id: 小说ID
        """
        if novel_id not in self.novel_subscribers:
            return

        subscribers = list(self.novel_subscribers[novel_id])
        disconnected_clients = []

        for client_id in subscribers:
            if client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].send_json(message)
                except Exception as e:
                    print(f"广播消息失败 ({client_id}): {e}")
                    disconnected_clients.append(client_id)

        # 清理断开的连接
        for client_id in disconnected_clients:
            self.disconnect(client_id)

    def subscribe_to_novel(self, client_id: str, novel_id: str):
        """
        订阅特定小说的更新

        Args:
            client_id: 客户端ID
            novel_id: 小说ID
        """
        if novel_id not in self.novel_subscribers:
            self.novel_subscribers[novel_id] = set()

        self.novel_subscribers[novel_id].add(client_id)

    def unsubscribe_from_novel(self, client_id: str, novel_id: str):
        """
        取消订阅特定小说

        Args:
            client_id: 客户端ID
            novel_id: 小说ID
        """
        if novel_id in self.novel_subscribers:
            self.novel_subscribers[novel_id].discard(client_id)

    def subscribe_global(self, client_id: str):
        """
        订阅全局消息

        Args:
            client_id: 客户端ID
        """
        self.global_subscribers.add(client_id)

    def unsubscribe_global(self, client_id: str):
        """
        取消全局订阅

        Args:
            client_id: 客户端ID
        """
        self.global_subscribers.discard(client_id)

    async def send_progress_update(
        self,
        novel_id: str,
        task_type: str,
        progress: int,
        message: str,
        **kwargs
    ):
        """
        发送进度更新

        Args:
            novel_id: 小说ID
            task_type: 任务类型（create/write/polish/review）
            progress: 进度（0-100）
            message: 状态消息
            **kwargs: 其他附加信息
        """
        update_message = {
            "type": "progress",
            "novel_id": novel_id,
            "task_type": task_type,
            "progress": progress,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }

        await self.broadcast_to_novel(update_message, novel_id)

    async def send_task_complete(
        self,
        novel_id: str,
        task_type: str,
        result: dict
    ):
        """
        发送任务完成通知

        Args:
            novel_id: 小说ID
            task_type: 任务类型
            result: 任务结果
        """
        message = {
            "type": "task_complete",
            "novel_id": novel_id,
            "task_type": task_type,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }

        await self.broadcast_to_novel(message, novel_id)

    async def send_task_error(
        self,
        novel_id: str,
        task_type: str,
        error: str
    ):
        """
        发送任务错误通知

        Args:
            novel_id: 小说ID
            task_type: 任务类型
            error: 错误信息
        """
        message = {
            "type": "task_error",
            "novel_id": novel_id,
            "task_type": task_type,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }

        await self.broadcast_to_novel(message, novel_id)

    def get_stats(self) -> dict:
        """
        获取连接统计信息

        Returns:
            dict: 统计信息
        """
        return {
            "total_connections": len(self.active_connections),
            "global_subscribers": len(self.global_subscribers),
            "novel_subscriptions": {
                novel_id: len(subscribers)
                for novel_id, subscribers in self.novel_subscribers.items()
            }
        }


# 全局连接管理器实例
manager = ConnectionManager()
