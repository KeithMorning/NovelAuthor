import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Stepper, Step, StepLabel, Alert, CircularProgress, Accordion, AccordionSummary, AccordionDetails, Chip, List, ListItem, ListItemText } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import InfoIcon from '@mui/icons-material/Info';
import WarningIcon from '@mui/icons-material/Warning';

interface LogEntry {
  timestamp: string;
  level: string;
  step: string;
  message: string;
  details?: any;
  error?: {
    type: string;
    message: string;
  };
}

interface WorkflowStatus {
  novel_id: string;
  start_time: string;
  end_time: string | null;
  current_step: string | null;
  status: string;
  steps_completed: string[];
  errors: Array<{
    timestamp: string;
    step: string;
    error: string;
  }>;
}

interface CreationLogsProps {
  novelId: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

const STEP_ORDER = [
  '初始化',
  '生成大纲',
  '生成角色',
  '保存文件',
  '加载记忆',
  '完成'
];

const CreationLogs: React.FC<CreationLogsProps> = ({
  novelId,
  autoRefresh = true,
  refreshInterval = 3000
}) => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLogs = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/novels/${novelId}/logs`);

      if (!response.ok) {
        if (response.status === 404) {
          setError('未找到日志记录');
          return;
        }
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      setLogs(data.logs || []);
      setWorkflowStatus(data.workflow_status);
      setError(null);
    } catch (err: any) {
      console.error('获取日志失败:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();

    if (autoRefresh && workflowStatus?.status === 'running') {
      const interval = setInterval(fetchLogs, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [novelId, autoRefresh, refreshInterval, workflowStatus?.status]);

  const getStepIcon = (stepName: string) => {
    if (!workflowStatus) return null;

    const isCompleted = workflowStatus.steps_completed.includes(stepName);
    const hasError = workflowStatus.errors.some(e => e.step === stepName);

    if (hasError) {
      return <ErrorIcon color="error" />;
    }
    if (isCompleted) {
      return <CheckCircleIcon color="success" />;
    }
    if (workflowStatus.current_step === stepName) {
      return <CircularProgress size={20} />;
    }
    return null;
  };

  const getLogLevelIcon = (level: string) => {
    switch (level) {
      case 'SUCCESS':
        return <CheckCircleIcon fontSize="small" color="success" />;
      case 'ERROR':
        return <ErrorIcon fontSize="small" color="error" />;
      case 'WARNING':
        return <WarningIcon fontSize="small" color="warning" />;
      case 'INFO':
        return <InfoIcon fontSize="small" color="info" />;
      default:
        return <InfoIcon fontSize="small" />;
    }
  };

  const getLogLevelColor = (level: string): "default" | "success" | "error" | "warning" | "info" => {
    switch (level) {
      case 'SUCCESS':
        return 'success';
      case 'ERROR':
        return 'error';
      case 'WARNING':
        return 'warning';
      case 'INFO':
        return 'info';
      default:
        return 'default';
    }
  };

  const getStatusColor = (status: string): "success" | "error" | "warning" | "info" => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'running':
        return 'info';
      default:
        return 'warning';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={200}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="warning">
        暂无日志记录：{error}
      </Alert>
    );
  }

  if (!workflowStatus) {
    return (
      <Alert severity="info">
        未找到创建日志
      </Alert>
    );
  }

  const activeStep = STEP_ORDER.indexOf(workflowStatus.current_step || '');

  return (
    <Box>
      {/* 状态概览 */}
      <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">创建状态</Typography>
          <Chip
            label={workflowStatus.status === 'completed' ? '已完成' :
                   workflowStatus.status === 'running' ? '进行中' :
                   workflowStatus.status === 'failed' ? '失败' : '未知'}
            color={getStatusColor(workflowStatus.status)}
            icon={workflowStatus.status === 'running' ? <CircularProgress size={16} /> : undefined}
          />
        </Box>

        {/* 步骤进度 */}
        <Stepper activeStep={activeStep} alternativeLabel>
          {STEP_ORDER.map((step, index) => {
            const isCompleted = workflowStatus.steps_completed.includes(step);
            const hasError = workflowStatus.errors.some(e => e.step === step);

            return (
              <Step key={step} completed={isCompleted}>
                <StepLabel
                  error={hasError}
                  icon={getStepIcon(step)}
                >
                  {step}
                </StepLabel>
              </Step>
            );
          })}
        </Stepper>

        {/* 时间信息 */}
        <Box mt={2} display="flex" gap={2}>
          <Typography variant="body2" color="text.secondary">
            开始时间: {formatTimestamp(workflowStatus.start_time)}
          </Typography>
          {workflowStatus.end_time && (
            <Typography variant="body2" color="text.secondary">
              结束时间: {formatTimestamp(workflowStatus.end_time)}
            </Typography>
          )}
        </Box>
      </Paper>

      {/* 错误信息 */}
      {workflowStatus.errors.length > 0 && (
        <Alert severity="error" sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            发现 {workflowStatus.errors.length} 个错误：
          </Typography>
          <List dense>
            {workflowStatus.errors.map((err, index) => (
              <ListItem key={index}>
                <ListItemText
                  primary={`[${err.step}] ${err.error}`}
                  secondary={formatTimestamp(err.timestamp)}
                />
              </ListItem>
            ))}
          </List>
        </Alert>
      )}

      {/* 详细日志 */}
      <Paper elevation={2} sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          详细日志 ({logs.length} 条)
        </Typography>

        {logs.map((log, index) => (
          <Accordion key={index}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box display="flex" alignItems="center" gap={1} width="100%">
                {getLogLevelIcon(log.level)}
                <Chip
                  label={log.level}
                  size="small"
                  color={getLogLevelColor(log.level)}
                />
                <Chip label={log.step} size="small" variant="outlined" />
                <Typography variant="body2" sx={{ flexGrow: 1, ml: 1 }}>
                  {log.message}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {formatTimestamp(log.timestamp)}
                </Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              {log.details && (
                <Box mb={1}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    详细信息:
                  </Typography>
                  <Paper variant="outlined" sx={{ p: 1, bgcolor: 'grey.50' }}>
                    <pre style={{ margin: 0, fontSize: '0.75rem', overflow: 'auto' }}>
                      {JSON.stringify(log.details, null, 2)}
                    </pre>
                  </Paper>
                </Box>
              )}
              {log.error && (
                <Box>
                  <Typography variant="subtitle2" color="error" gutterBottom>
                    错误信息:
                  </Typography>
                  <Paper variant="outlined" sx={{ p: 1, bgcolor: 'error.light', color: 'error.contrastText' }}>
                    <Typography variant="body2">
                      <strong>{log.error.type}:</strong> {log.error.message}
                    </Typography>
                  </Paper>
                </Box>
              )}
            </AccordionDetails>
          </Accordion>
        ))}
      </Paper>
    </Box>
  );
};

export default CreationLogs;
