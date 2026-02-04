import React, { useEffect, useState } from 'react';
import {
  Box,
  Progress,
  Text,
  VStack,
  HStack,
  Badge,
  useColorModeValue,
} from '@chakra-ui/react';
import { useWebSocketContext } from '../contexts/WebSocketContext';

interface ProgressMonitorProps {
  novelId?: string;
}

export const ProgressMonitor: React.FC<ProgressMonitorProps> = ({ novelId }) => {
  const { lastMessage, subscribe, unsubscribe, isConnected } = useWebSocketContext();
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('');
  const [taskType, setTaskType] = useState('');

  const bg = useColorModeValue('white', 'gray.700');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  useEffect(() => {
    if (novelId) {
      subscribe(novelId);
      return () => {
        unsubscribe(novelId);
      };
    }
  }, [novelId, subscribe, unsubscribe]);

  useEffect(() => {
    if (lastMessage) {
      if (lastMessage.type === 'progress') {
        setProgress(lastMessage.progress || 0);
        setMessage(lastMessage.message || '');
        setTaskType(lastMessage.task_type || '');
      } else if (lastMessage.type === 'task_complete') {
        setProgress(100);
        setMessage('任务完成！');
        setTimeout(() => {
          setProgress(0);
          setMessage('');
          setTaskType('');
        }, 3000);
      }
    }
  }, [lastMessage]);

  if (!isConnected) {
    return null;
  }

  if (progress === 0 && !message) {
    return null;
  }

  return (
    <Box bg={bg} borderWidth="1px" borderColor={borderColor} borderRadius="md" p={4}>
      <VStack align="stretch" gap={3}>
        <HStack justify="space-between">
          <Text fontWeight="bold">实时进度</Text>
          {taskType && <Badge colorScheme="blue">{taskType}</Badge>}
        </HStack>

        <Progress
          value={progress}
          size="lg"
          colorScheme="blue"
          borderRadius="full"
          hasStripe
          isAnimated
        />

        <HStack justify="space-between">
          <Text fontSize="sm" color="gray.600">{message}</Text>
          <Text fontSize="sm" fontWeight="bold">{progress}%</Text>
        </HStack>
      </VStack>
    </Box>
  );
};
