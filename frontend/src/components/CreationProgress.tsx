import React, { useEffect, useState } from 'react';
import {
    Box,
    VStack,
    Text,
    Progress,
    Step,
    StepDescription,
    StepIcon,
    StepIndicator,
    StepNumber,
    StepSeparator,
    StepStatus,
    StepTitle,
    Stepper,
    useSteps,
    Button,
} from '@chakra-ui/react';
import { useWebSocketContext } from '../contexts/WebSocketContext';
import { useNavigate } from 'react-router-dom';

interface CreationProgressProps {
    novelId: string;
    onComplete: () => void;
}

const steps = [
    { title: 'Initialization', description: 'Starting task' },
    { title: 'Outline', description: 'Generating plot' },
    { title: 'Characters', description: 'Creating characters' },
    { title: 'Saving', description: 'Finalizing' },
];

export const CreationProgress: React.FC<CreationProgressProps> = ({ novelId, onComplete }) => {
    const { subscribe, unsubscribe, lastMessage } = useWebSocketContext();
    const navigate = useNavigate();
    const [logs, setLogs] = useState<string[]>([]);
    const { activeStep, setActiveStep } = useSteps({
        index: 0,
        count: steps.length,
    });

    useEffect(() => {
        subscribe(novelId);
        return () => unsubscribe(novelId);
    }, [novelId, subscribe, unsubscribe]);

    useEffect(() => {
        if (lastMessage && lastMessage.novel_id === novelId) {
            if (lastMessage.type === 'progress') {
                setLogs(prev => [...prev, lastMessage.message || 'Processing...']);
                // Simple heuristic for steps based on message content
                const msg = lastMessage.message || '';
                if (msg.includes('大纲')) setActiveStep(1);
                if (msg.includes('角色')) setActiveStep(2);
                if (msg.includes('保存')) setActiveStep(3);
            } else if (lastMessage.type === 'task_complete') {
                setActiveStep(4);
                setLogs(prev => [...prev, 'Creation Complete!']);
            }
        }
    }, [lastMessage, novelId, setActiveStep]);

    return (
        <VStack align="stretch" spacing={6} p={4}>
            <Text fontWeight="bold" fontSize="lg">Creating your novel...</Text>

            <Stepper index={activeStep} orientation="horizontal" size="sm" colorScheme="brand">
                {steps.map((step, index) => (
                    <Step key={index}>
                        <StepIndicator>
                            <StepStatus
                                complete={<StepIcon />}
                                incomplete={<StepNumber />}
                                active={<StepNumber />}
                            />
                        </StepIndicator>
                        <Box flexShrink='0'>
                            <StepTitle>{step.title}</StepTitle>
                            <StepDescription>{step.description}</StepDescription>
                        </Box>
                        <StepSeparator />
                    </Step>
                ))}
            </Stepper>

            <Box bg="gray.900" color="green.300" p={4} borderRadius="md" h="200px" overflowY="auto" fontFamily="mono" fontSize="sm">
                {logs.map((log, i) => (
                    <Text key={i}>&gt; {log}</Text>
                ))}
                {logs.length === 0 && <Text color="gray.500">Waiting for updates...</Text>}
            </Box>

            {activeStep === 4 && (
                <Button colorScheme="brand" onClick={() => {
                    onComplete();
                    navigate(`/novel/${novelId}`);
                }}>
                    View Novel
                </Button>
            )}
        </VStack>
    );
};
