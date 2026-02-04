import { useEffect, useRef, useState, useCallback } from 'react';
import { WebSocketMessage } from '../types';

interface UseWebSocketOptions {
  url?: string;
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: Event) => void;
  reconnect?: boolean;
  reconnectInterval?: number;
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const {
    url = `ws://${window.location.hostname}:8000/ws`,
    onMessage,
    onError,
    reconnect = true,
    reconnectInterval = 3000,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const clientIdRef = useRef<string>(`client_${Math.random().toString(36).substr(2, 9)}`);

  const connect = useCallback(() => {
    try {
      const wsUrl = `${url}?client_id=${clientIdRef.current}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WebSocket 连接成功');
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          onMessage?.(message);
        } catch (error) {
          console.error('解析 WebSocket 消息失败:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket 错误:', error);
        onError?.(error);
      };

      ws.onclose = () => {
        console.log('WebSocket 连接关闭');
        setIsConnected(false);
        wsRef.current = null;

        // 自动重连
        if (reconnect && reconnectTimeoutRef.current === null) {
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectTimeoutRef.current = null;
            connect();
          }, reconnectInterval);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('创建 WebSocket 连接失败:', error);
    }
  }, [url, onMessage, onError, reconnect, reconnectInterval]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const send = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket 未连接');
    }
  }, []);

  const subscribe = useCallback((novelId: string) => {
    send({
      type: 'subscribe',
      novel_id: novelId,
    });
  }, [send]);

  const unsubscribe = useCallback((novelId: string) => {
    send({
      type: 'unsubscribe',
      novel_id: novelId,
    });
  }, [send]);

  const subscribeGlobal = useCallback(() => {
    send({
      type: 'subscribe_global',
    });
  }, [send]);

  const ping = useCallback(() => {
    send({
      type: 'ping',
    });
  }, [send]);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    send,
    subscribe,
    unsubscribe,
    subscribeGlobal,
    ping,
    reconnect: connect,
  };
};
