"""
小说创作流程日志系统

用于记录小说创建过程中的每个步骤、错误和状态
"""
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from pathlib import Path


class LogLevel(str, Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"


class WorkflowStep(str, Enum):
    """工作流步骤"""
    INIT = "初始化"
    OUTLINE_GENERATION = "生成大纲"
    CHARACTER_GENERATION = "生成角色"
    CHAPTER_WRITING = "写作章节"
    CHAPTER_EDITING = "编辑章节"
    MEMORY_LOADING = "加载记忆"
    FILE_SAVING = "保存文件"
    COMPLETED = "完成"
    FAILED = "失败"


class NovelCreationLogger:
    """
    小说创作日志记录器

    记录小说创建过程中的所有步骤和事件
    """

    def __init__(self, novel_id: str, log_dir: str = "logs"):
        """
        初始化日志记录器

        Args:
            novel_id: 小说ID
            log_dir: 日志目录
        """
        self.novel_id = novel_id
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # 日志文件路径
        self.log_file = self.log_dir / f"{novel_id}.log"
        self.json_log_file = self.log_dir / f"{novel_id}.json"

        # 内存中的日志记录
        self.logs: List[Dict[str, Any]] = []

        # 工作流状态
        self.workflow_status = {
            "novel_id": novel_id,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "current_step": None,
            "status": "running",
            "steps_completed": [],
            "errors": []
        }

        # 初始化日志
        self._init_log()

    def _init_log(self):
        """初始化日志文件"""
        self.log(
            level=LogLevel.INFO,
            step=WorkflowStep.INIT,
            message=f"开始创建小说，ID: {self.novel_id}"
        )

    def log(
        self,
        level: LogLevel,
        step: WorkflowStep,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None
    ):
        """
        记录日志

        Args:
            level: 日志级别
            step: 工作流步骤
            message: 日志消息
            details: 详细信息
            error: 异常对象
        """
        timestamp = datetime.now().isoformat()

        # 构建日志条目
        log_entry = {
            "timestamp": timestamp,
            "level": level.value,
            "step": step.value,
            "message": message,
        }

        if details:
            log_entry["details"] = details

        if error:
            log_entry["error"] = {
                "type": type(error).__name__,
                "message": str(error),
            }
            # 记录到工作流状态
            self.workflow_status["errors"].append({
                "timestamp": timestamp,
                "step": step.value,
                "error": str(error)
            })

        # 添加到内存日志
        self.logs.append(log_entry)

        # 更新工作流状态
        self.workflow_status["current_step"] = step.value

        # 写入文本日志
        self._write_text_log(log_entry)

        # 写入JSON日志
        self._write_json_log()

    def _write_text_log(self, log_entry: Dict[str, Any]):
        """写入文本格式日志"""
        timestamp = log_entry["timestamp"]
        level = log_entry["level"]
        step = log_entry["step"]
        message = log_entry["message"]

        log_line = f"[{timestamp}] [{level}] [{step}] {message}"

        if "error" in log_entry:
            error = log_entry["error"]
            log_line += f"\n  错误类型: {error['type']}\n  错误信息: {error['message']}"

        if "details" in log_entry:
            log_line += f"\n  详情: {json.dumps(log_entry['details'], ensure_ascii=False, indent=2)}"

        log_line += "\n" + "-" * 80 + "\n"

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_line)

    def _write_json_log(self):
        """写入JSON格式日志"""
        with open(self.json_log_file, "w", encoding="utf-8") as f:
            json.dump({
                "workflow_status": self.workflow_status,
                "logs": self.logs
            }, f, ensure_ascii=False, indent=2)

    def step_start(self, step: WorkflowStep, message: str = None):
        """
        标记步骤开始

        Args:
            step: 工作流步骤
            message: 可选的消息
        """
        msg = message or f"开始执行: {step.value}"
        self.log(
            level=LogLevel.INFO,
            step=step,
            message=msg
        )

    def step_success(
        self,
        step: WorkflowStep,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        标记步骤成功

        Args:
            step: 工作流步骤
            message: 成功消息
            details: 详细信息
        """
        self.log(
            level=LogLevel.SUCCESS,
            step=step,
            message=f"✓ {message}",
            details=details
        )

        # 添加到已完成步骤
        if step.value not in self.workflow_status["steps_completed"]:
            self.workflow_status["steps_completed"].append(step.value)

    def step_error(
        self,
        step: WorkflowStep,
        message: str,
        error: Exception,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        标记步骤失败

        Args:
            step: 工作流步骤
            message: 错误消息
            error: 异常对象
            details: 详细信息
        """
        self.log(
            level=LogLevel.ERROR,
            step=step,
            message=f"✗ {message}",
            error=error,
            details=details
        )

        # 更新工作流状态为失败
        self.workflow_status["status"] = "failed"
        self.workflow_status["end_time"] = datetime.now().isoformat()

    def warning(
        self,
        step: WorkflowStep,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        记录警告

        Args:
            step: 工作流步骤
            message: 警告消息
            details: 详细信息
        """
        self.log(
            level=LogLevel.WARNING,
            step=step,
            message=f"⚠ {message}",
            details=details
        )

    def complete(self, message: str = "小说创建流程完成"):
        """
        标记工作流完成

        Args:
            message: 完成消息
        """
        self.workflow_status["status"] = "completed"
        self.workflow_status["end_time"] = datetime.now().isoformat()

        self.log(
            level=LogLevel.SUCCESS,
            step=WorkflowStep.COMPLETED,
            message=message
        )

        # 生成摘要
        self._write_summary()

    def _write_summary(self):
        """生成并写入摘要"""
        start_time = datetime.fromisoformat(self.workflow_status["start_time"])
        end_time = datetime.fromisoformat(self.workflow_status["end_time"])
        duration = (end_time - start_time).total_seconds()

        summary = f"""
{'=' * 80}
小说创建流程摘要
{'=' * 80}
小说ID: {self.novel_id}
开始时间: {self.workflow_status['start_time']}
结束时间: {self.workflow_status['end_time']}
总耗时: {duration:.2f} 秒
最终状态: {self.workflow_status['status']}

完成的步骤:
{chr(10).join(f"  ✓ {step}" for step in self.workflow_status['steps_completed'])}

"""

        if self.workflow_status["errors"]:
            summary += "遇到的错误:\n"
            for error in self.workflow_status["errors"]:
                summary += f"  ✗ [{error['step']}] {error['error']}\n"

        summary += "=" * 80 + "\n"

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(summary)

    def get_status(self) -> Dict[str, Any]:
        """
        获取当前工作流状态

        Returns:
            Dict: 工作流状态
        """
        return self.workflow_status.copy()

    def get_logs(
        self,
        level: Optional[LogLevel] = None,
        step: Optional[WorkflowStep] = None
    ) -> List[Dict[str, Any]]:
        """
        获取日志记录

        Args:
            level: 可选的日志级别过滤
            step: 可选的步骤过滤

        Returns:
            List[Dict]: 过滤后的日志列表
        """
        logs = self.logs

        if level:
            logs = [log for log in logs if log["level"] == level.value]

        if step:
            logs = [log for log in logs if log["step"] == step.value]

        return logs


# 全局日志管理器
_loggers: Dict[str, NovelCreationLogger] = {}


def get_logger(novel_id: str) -> NovelCreationLogger:
    """
    获取或创建日志记录器

    Args:
        novel_id: 小说ID

    Returns:
        NovelCreationLogger: 日志记录器实例
    """
    if novel_id not in _loggers:
        _loggers[novel_id] = NovelCreationLogger(novel_id)
    return _loggers[novel_id]


def remove_logger(novel_id: str):
    """
    移除日志记录器（释放内存）

    Args:
        novel_id: 小说ID
    """
    if novel_id in _loggers:
        del _loggers[novel_id]


def get_novel_logs(novel_id: str) -> Optional[Dict[str, Any]]:
    """
    读取小说的完整日志

    Args:
        novel_id: 小说ID

    Returns:
        Optional[Dict]: 日志数据，如果不存在返回None
    """
    log_file = Path("logs") / f"{novel_id}.json"

    if not log_file.exists():
        return None

    with open(log_file, "r", encoding="utf-8") as f:
        return json.load(f)
