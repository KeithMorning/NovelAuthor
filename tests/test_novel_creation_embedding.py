"""
模拟真实小说创建流程的 Embedding 测试
测试从 coordinator 到 memory_manager 到 vector_store 的完整流程
"""
import os
import sys
import logging
import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/novel_creation_embedding_debug.log', mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def test_step_1_memory_manager_init():
    """
    测试 1: MemoryManager 初始化（这会触发 VectorMemoryStore 初始化）
    """
    print("\n" + "="*80)
    print("测试 1: MemoryManager 初始化")
    print("="*80)

    logger.info("开始测试 1: MemoryManager 初始化")

    try:
        logger.info("导入 get_memory_manager")
        from novel_ai_agent.memory import get_memory_manager

        logger.info("调用 get_memory_manager")
        memory_manager = get_memory_manager("test_novel_001")
        logger.info("✓ MemoryManager 初始化成功")

        logger.info(f"memory_manager.novel_id: {memory_manager.novel_id}")
        logger.info(f"memory_manager.vector_store: {type(memory_manager.vector_store)}")

        print(f"✅ 测试 1 成功")
        print(f"   小说ID: {memory_manager.novel_id}")
        print(f"   Vector Store 类型: {type(memory_manager.vector_store).__name__}")
        return True

    except Exception as e:
        logger.error(f"✗ 测试 1 失败: {e}", exc_info=True)
        print(f"❌ 测试 1 失败: {e}")
        return False


def test_step_2_load_characters():
    """
    测试 2: 加载角色到记忆（模拟小说创建后的操作）
    """
    print("\n" + "="*80)
    print("测试 2: 加载角色到记忆")
    print("="*80)

    logger.info("开始测试 2: 加载角色到记忆")

    try:
        from novel_ai_agent.memory import get_memory_manager
        from novel_ai_agent.models.character import Character

        logger.info("获取 memory_manager")
        memory_manager = get_memory_manager("test_novel_002")

        logger.info("创建测试角色")
        test_character = Character(
            name="李明",
            role="主角",
            personality="勇敢、坚韧、富有同情心",
            background="曾是一名普通的程序员，在一次意外中获得了AI能力",
            motivation="拯救被AI控制的世界",
            appearance="黑色短发，戴眼镜，身材瘦削",
            skills="编程、黑客技术、快速学习",
            relationships="与张华是好友，与陈雪是恋人",
            arc="从一个普通人成长为拯救世界的英雄"
        )

        logger.info("准备角色数据")
        characters_data = [{
            "name": test_character.name,
            "role": test_character.role,
            "personality": test_character.personality,
            "background": test_character.background,
            "motivation": test_character.motivation,
            "appearance": test_character.appearance,
            "skills": test_character.skills,
            "relationships": test_character.relationships,
            "arc": test_character.arc
        }]

        logger.info("存储角色到向量数据库")
        count = memory_manager.vector_store.store_characters("test_novel_002", characters_data)
        logger.info(f"✓ 角色存储成功，数量: {count}")

        logger.info("搜索角色")
        results = memory_manager.vector_store.search_characters("test_novel_002", "程序员", k=1)
        logger.info(f"✓ 搜索成功，结果数量: {len(results)}")

        if results:
            logger.info(f"第一个结果: {results[0].page_content[:100]}...")

        print(f"✅ 测试 2 成功")
        print(f"   存储角色数: {count}")
        print(f"   搜索结果数: {len(results)}")

        # 清理
        memory_manager.vector_store.delete_novel_collections("test_novel_002")
        return True

    except Exception as e:
        logger.error(f"✗ 测试 2 失败: {e}", exc_info=True)
        print(f"❌ 测试 2 失败: {e}")
        return False


def test_step_3_multiple_memory_managers():
    """
    测试 3: 多个 MemoryManager 实例（模拟并发场景）
    """
    print("\n" + "="*80)
    print("测试 3: 多个 MemoryManager 实例")
    print("="*80)

    logger.info("开始测试 3: 多个 MemoryManager 实例")

    try:
        from novel_ai_agent.memory import get_memory_manager

        logger.info("创建第一个 MemoryManager")
        mm1 = get_memory_manager("novel_a")
        logger.info("✓ MemoryManager 1 创建成功")

        logger.info("创建第二个 MemoryManager")
        mm2 = get_memory_manager("novel_b")
        logger.info("✓ MemoryManager 2 创建成功")

        logger.info("创建第三个 MemoryManager（重复ID）")
        mm3 = get_memory_manager("novel_a")
        logger.info("✓ MemoryManager 3 创建成功")

        # 验证缓存机制
        same_instance = mm1 is mm3
        logger.info(f"mm1 和 mm3 是同一个实例: {same_instance}")

        # 测试它们使用的是同一个 vector_store
        same_vector_store = mm1.vector_store is mm2.vector_store
        logger.info(f"mm1 和 mm2 使用同一个 vector_store: {same_vector_store}")

        print(f"✅ 测试 3 成功")
        print(f"   同一小说ID使用缓存: {same_instance}")
        print(f"   共享 vector_store: {same_vector_store}")
        return True

    except Exception as e:
        logger.error(f"✗ 测试 3 失败: {e}", exc_info=True)
        print(f"❌ 测试 3 失败: {e}")
        return False


async def test_step_4_coordinator_workflow():
    """
    测试 4: 完整的 Coordinator 工作流（最接近真实场景）
    """
    print("\n" + "="*80)
    print("测试 4: Coordinator 完整工作流")
    print("="*80)

    logger.info("开始测试 4: Coordinator 完整工作流")

    try:
        logger.info("导入 CoordinatorAgent")
        from novel_ai_agent.agents.coordinator import CoordinatorAgent

        logger.info("创建 CoordinatorAgent 实例")
        coordinator = CoordinatorAgent()
        logger.info("✓ CoordinatorAgent 创建成功")

        logger.info("调用 create_novel_workflow")
        result = await coordinator.create_novel_workflow(
            title="AI觉醒",
            genre="科幻",
            theme="人工智能与人类共存",
            style="现代科幻",
            chapter_count=2  # 只生成2章，减少测试时间
        )

        logger.info(f"✓ create_novel_workflow 完成")
        logger.info(f"结果状态: {result.get('status')}")
        logger.info(f"小说ID: {result.get('novel_id')}")

        if result.get('novel'):
            novel = result['novel']
            logger.info(f"小说标题: {novel.title}")
            logger.info(f"角色数量: {len(novel.characters)}")
            logger.info(f"情节点数量: {len(novel.outline.plot_points) if novel.outline else 0}")
            logger.info(f"章节数量: {len(novel.chapters)}")

        print(f"✅ 测试 4 成功")
        print(f"   小说ID: {result.get('novel_id')}")
        print(f"   状态: {result.get('status')}")

        # 清理
        if result.get('novel_id'):
            from novel_ai_agent.memory import get_memory_manager
            mm = get_memory_manager(result['novel_id'])
            mm.vector_store.delete_novel_collections(result['novel_id'])

        return True

    except Exception as e:
        logger.error(f"✗ 测试 4 失败: {e}", exc_info=True)
        print(f"❌ 测试 4 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_step_5_clear_cache_and_reinit():
    """
    测试 5: 清除缓存并重新初始化
    """
    print("\n" + "="*80)
    print("测试 5: 清除缓存并重新初始化")
    print("="*80)

    logger.info("开始测试 5: 清除缓存并重新初始化")

    try:
        from novel_ai_agent.memory import get_memory_manager, clear_memory_cache

        logger.info("创建第一个 MemoryManager")
        mm1 = get_memory_manager("test_novel_003")
        logger.info(f"mm1 ID: {id(mm1)}")

        logger.info("清除缓存")
        clear_memory_cache()
        logger.info("✓ 缓存清除成功")

        logger.info("创建第二个 MemoryManager（相同ID）")
        mm2 = get_memory_manager("test_novel_003")
        logger.info(f"mm2 ID: {id(mm2)}")

        # 验证是否是不同实例
        different_instance = mm1 is not mm2
        logger.info(f"清除缓存后是新实例: {different_instance}")

        print(f"✅ 测试 5 成功")
        print(f"   清除缓存后创建新实例: {different_instance}")
        return True

    except Exception as e:
        logger.error(f"✗ 测试 5 失败: {e}", exc_info=True)
        print(f"❌ 测试 5 失败: {e}")
        return False


def main():
    """
    运行所有测试
    """
    print("\n" + "🔍 " + "="*78)
    print("小说创建流程 Embedding 测试套件")
    print("目标: 模拟真实的小说创建流程，找出 Embedding 失败的原因")
    print("="*80 + "\n")

    # 确保日志目录存在
    Path("logs").mkdir(exist_ok=True)

    logger.info("="*80)
    logger.info("开始小说创建流程 Embedding 测试")
    logger.info("="*80)

    # 同步测试
    sync_tests = [
        ("MemoryManager 初始化", test_step_1_memory_manager_init),
        ("加载角色到记忆", test_step_2_load_characters),
        ("多个 MemoryManager 实例", test_step_3_multiple_memory_managers),
        ("清除缓存并重新初始化", test_step_5_clear_cache_and_reinit),
    ]

    results = {}
    for name, test_func in sync_tests:
        try:
            results[name] = test_func()
        except Exception as e:
            logger.error(f"测试 {name} 异常: {e}", exc_info=True)
            results[name] = False

    # 异步测试
    async_test_name = "Coordinator 完整工作流"
    try:
        logger.info(f"运行异步测试: {async_test_name}")
        results[async_test_name] = asyncio.run(test_step_4_coordinator_workflow())
    except Exception as e:
        logger.error(f"异步测试 {async_test_name} 异常: {e}", exc_info=True)
        results[async_test_name] = False

    # 总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)

    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")

    passed = sum(1 for r in results.values() if r)
    total = len(results)
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")

    logger.info("="*80)
    logger.info(f"测试完成，通过率: {passed}/{total}")
    logger.info("详细日志已保存到: logs/novel_creation_embedding_debug.log")
    logger.info("="*80)

    print(f"\n详细日志已保存到: logs/novel_creation_embedding_debug.log")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
