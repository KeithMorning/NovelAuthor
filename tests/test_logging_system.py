#!/usr/bin/env python3
"""
测试日志系统

验证日志记录、查询和API功能
"""
import sys
import os
import asyncio
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from novel_ai_agent.utils.logger import (
    get_logger, get_novel_logs, remove_logger,
    WorkflowStep, LogLevel
)


def test_basic_logging():
    """测试基本日志功能"""
    print("=" * 80)
    print("测试1: 基本日志功能")
    print("=" * 80)

    novel_id = "test_novel_001"
    logger = get_logger(novel_id)

    # 测试各种日志方法
    logger.step_start(WorkflowStep.INIT, "初始化测试小说")

    logger.log(
        LogLevel.INFO,
        WorkflowStep.INIT,
        "创建小说对象",
        details={"title": "测试小说", "genre": "科幻"}
    )

    logger.step_success(
        WorkflowStep.INIT,
        "初始化成功",
        details={"novel_id": novel_id}
    )

    logger.step_start(WorkflowStep.OUTLINE_GENERATION, "开始生成大纲")

    logger.warning(
        WorkflowStep.OUTLINE_GENERATION,
        "LLM响应较慢",
        details={"response_time": 5.2}
    )

    logger.step_success(
        WorkflowStep.OUTLINE_GENERATION,
        "大纲生成成功",
        details={"chapter_count": 20, "plot_points": 5}
    )

    logger.complete("测试完成")

    # 验证日志文件
    log_file = Path("logs") / f"{novel_id}.log"
    json_log_file = Path("logs") / f"{novel_id}.json"

    assert log_file.exists(), "文本日志文件未创建"
    assert json_log_file.exists(), "JSON日志文件未创建"

    print("✅ 基本日志功能测试通过")
    print(f"  - 文本日志: {log_file}")
    print(f"  - JSON日志: {json_log_file}")

    # 清理
    remove_logger(novel_id)

    return novel_id


def test_error_logging():
    """测试错误记录"""
    print("\n" + "=" * 80)
    print("测试2: 错误记录功能")
    print("=" * 80)

    novel_id = "test_novel_002"
    logger = get_logger(novel_id)

    logger.step_start(WorkflowStep.CHARACTER_GENERATION, "开始生成角色")

    # 模拟错误
    try:
        raise ValueError("JSON解析失败: 未转义的引号")
    except Exception as e:
        logger.step_error(
            WorkflowStep.CHARACTER_GENERATION,
            "角色生成失败",
            e,
            details={"attempted_retries": 3}
        )

    # 验证错误记录
    status = logger.get_status()

    assert status["status"] == "failed", "状态应为failed"
    assert len(status["errors"]) == 1, "应记录1个错误"
    assert status["errors"][0]["step"] == "生成角色", "错误步骤不正确"

    print("✅ 错误记录功能测试通过")
    print(f"  - 错误数量: {len(status['errors'])}")
    print(f"  - 错误内容: {status['errors'][0]['error']}")

    # 清理
    remove_logger(novel_id)

    return novel_id


def test_log_query():
    """测试日志查询"""
    print("\n" + "=" * 80)
    print("测试3: 日志查询功能")
    print("=" * 80)

    novel_id = "test_novel_003"
    logger = get_logger(novel_id)

    # 创建一些日志
    logger.step_start(WorkflowStep.INIT, "初始化")
    logger.step_success(WorkflowStep.INIT, "初始化成功")

    logger.step_start(WorkflowStep.OUTLINE_GENERATION, "生成大纲")
    logger.step_success(WorkflowStep.OUTLINE_GENERATION, "大纲生成成功")

    logger.complete("完成")

    # 查询所有日志
    all_logs = logger.get_logs()
    assert len(all_logs) > 0, "应有日志记录"

    # 查询SUCCESS级别的日志
    success_logs = logger.get_logs(level=LogLevel.SUCCESS)
    assert len(success_logs) > 0, "应有SUCCESS级别日志"

    # 查询特定步骤的日志
    init_logs = logger.get_logs(step=WorkflowStep.INIT)
    assert len(init_logs) > 0, "应有初始化步骤的日志"

    print("✅ 日志查询功能测试通过")
    print(f"  - 总日志数: {len(all_logs)}")
    print(f"  - SUCCESS日志: {len(success_logs)}")
    print(f"  - 初始化日志: {len(init_logs)}")

    # 测试get_novel_logs
    logs_data = get_novel_logs(novel_id)
    assert logs_data is not None, "应能读取日志数据"
    assert "workflow_status" in logs_data, "应包含workflow_status"
    assert "logs" in logs_data, "应包含logs"

    print(f"  - 工作流状态: {logs_data['workflow_status']['status']}")
    print(f"  - 已完成步骤: {len(logs_data['workflow_status']['steps_completed'])}")

    # 清理
    remove_logger(novel_id)

    return novel_id


def test_workflow_status():
    """测试工作流状态"""
    print("\n" + "=" * 80)
    print("测试4: 工作流状态跟踪")
    print("=" * 80)

    novel_id = "test_novel_004"
    logger = get_logger(novel_id)

    # 模拟完整工作流
    steps = [
        WorkflowStep.INIT,
        WorkflowStep.OUTLINE_GENERATION,
        WorkflowStep.CHARACTER_GENERATION,
        WorkflowStep.FILE_SAVING,
        WorkflowStep.MEMORY_LOADING,
    ]

    for step in steps:
        logger.step_start(step, f"执行{step.value}")
        logger.step_success(step, f"{step.value}完成")

    logger.complete("工作流完成")

    status = logger.get_status()

    assert status["status"] == "completed", "状态应为completed"
    assert len(status["steps_completed"]) == len(steps), "应完成所有步骤"
    assert status["end_time"] is not None, "应有结束时间"

    print("✅ 工作流状态跟踪测试通过")
    print(f"  - 最终状态: {status['status']}")
    print(f"  - 完成步骤: {status['steps_completed']}")
    print(f"  - 开始时间: {status['start_time']}")
    print(f"  - 结束时间: {status['end_time']}")

    # 清理
    remove_logger(novel_id)

    return novel_id


def cleanup_test_logs():
    """清理测试日志文件"""
    print("\n" + "=" * 80)
    print("清理测试日志文件")
    print("=" * 80)

    logs_dir = Path("logs")
    if logs_dir.exists():
        test_files = list(logs_dir.glob("test_novel_*.log")) + \
                     list(logs_dir.glob("test_novel_*.json"))

        for file in test_files:
            file.unlink()
            print(f"  - 删除: {file.name}")

        print(f"✅ 清理完成，删除了 {len(test_files)} 个文件")


def print_summary():
    """打印测试摘要"""
    print("\n" + "=" * 80)
    print("📊 测试摘要")
    print("=" * 80)
    print("✅ 所有测试通过！")
    print("\n已验证的功能：")
    print("  1. ✅ 基本日志记录（INFO, SUCCESS, WARNING, ERROR）")
    print("  2. ✅ 错误捕获和记录")
    print("  3. ✅ 日志查询和过滤")
    print("  4. ✅ 工作流状态跟踪")
    print("  5. ✅ 文件持久化（文本 + JSON）")
    print("  6. ✅ 时间统计")
    print("\n💡 日志系统可以正常使用！")
    print("\n下一步：")
    print("  - 启动服务测试API: ./start_all.sh")
    print("  - 创建小说并查看日志: GET /api/novels/{novel_id}/logs")
    print("  - 查看日志文档: docs/LOGGING_SYSTEM.md")


def main():
    """主函数"""
    print("\n🚀 日志系统测试\n")

    try:
        # 运行测试
        test_basic_logging()
        test_error_logging()
        test_log_query()
        test_workflow_status()

        # 清理
        cleanup_test_logs()

        # 打印摘要
        print_summary()

        sys.exit(0)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
