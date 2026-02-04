import React, { createContext, useContext, ReactNode } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { WebSocketMessage } from '../types';
import { useToast } from '@chakra-ui/react';

interface WebSocketContextType {
  isConnected: boolean;
  lastMessage: WebSocketMessage | null;
  subscribe: (novelId: string) => void;
  unsubscribe: (novelId: string) => void;
  subscribeGlobal: () => void;
  ping: () => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

interface WebSocketProviderProps {
  children: ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const toast = useToast();

  const ws = useWebSocket({
    onMessage: (message) => {
      // 处理不同类型的消息
      if (message.type === 'task_complete') {
        toast({
          title: '任务完成',
          description: message.message || '操作已完成',
          status: 'success',
          duration: 5000,
          isClosable: true,
        });
      } else if (message.type === 'task_error') {
        toast({
          title: '任务失败',
          description: message.error || '操作失败',
          status: 'error',
          duration: 5000,
          isClosable: true,
        });
      }
    },
    onError: (error) => {
      console.error('WebSocket 错误:', error);
    },
  });

  return (
    <WebSocketContext.Provider value={ws}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocketContext = () => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocketContext 必须在 WebSocketProvider 内使用');
  }
  return context;
};
