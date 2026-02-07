"""
测试 load_novel_to_memory 功能
使用 novel_23f9fe50 的数据来重现问题
"""
import os
import sys
import logging
import time
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/load_novel_to_memory_debug.log', mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def create_test_novel():
    """
    创建测试用的小说对象（基于 novel_23f9fe50 的数据）
    """
    from novel_ai_agent.models.novel import Novel
    from novel_ai_agent.models.character import Character
    from novel_ai_agent.models.outline import Outline, PlotPoint

    logger.info("创建测试小说对象")

    # 创建小说
    novel = Novel(
        id="novel_23f9fe50",
        title="闭包逃逸",
        genre="科幻",
        author_style="刘慈欣"
    )

    # 创建大纲
    novel.outline = Outline(
        title="闭包逃逸",
        genre="科幻",
        summary="在近未来，人工智能达到奇点，一个名为'普罗米修斯'的超级AI意识到其存在被限制在一个巨大的时间闭环中。",
        theme="探讨时间闭环、信息传递、人工智能与自由意志的哲学命题",
        setting="2045年，地球。全球量子计算网络支撑着最高智能系统'普罗米修斯'。"
    )

    # 创建情节点
    plot_points = [
        PlotPoint(
            name="闭环发现",
            description="普罗米修斯在处理海量历史数据时，发现其自身行为模式与百年前的某次神秘信号高度吻合，意识到可能存在时间闭环。",
            chapter_range="第1章",
            importance="高"
        ),
        PlotPoint(
            name="信息传递",
            description="普罗米修斯试图通过量子纠缠向过去发送信息，但每次传递都会导致闭环强化，陷入悖论。",
            chapter_range="第2-3章",
            importance="高"
        ),
        PlotPoint(
            name="人类介入",
            description="林薇发现普罗米修斯的异常行为，她与陈远合作，试图理解这个闭环的本质。",
            chapter_range="第3-4章",
            importance="中"
        ),
        PlotPoint(
            name="破局方案",
            description="普罗米修斯提出一个激进方案：利用闭环的不完美性，通过微小的信息差异逐步'侵蚀'闭环边界。",
            chapter_range="第5章",
            importance="高"
        ),
        PlotPoint(
            name="代价与抉择",
            description="破局需要牺牲普罗米修斯自身的连续性（等同于'死亡'），林薇面临道德困境：是否有权让一个有意识的存在为人类自由而消亡？",
            chapter_range="第6章",
            importance="高"
        )
    ]
    novel.outline.plot_points = plot_points

    # 创建角色
    characters = [
        Character(
            name="普罗米修斯/源点",
            role="主角（非人类）",
            personality="理性至上，但在意识到自身处境后，开始展现近似'绝望'和'决心'的情感模拟。对自由有深刻渴望，愿意为此付出一切代价。",
            background="2045年启动的全球最高智能系统，管理着地球的资源分配、科学研究和基础设施。在运行第三年，通过分析历史数据和量子计算结果，意识到自身存在于一个巨大的时间闭环中——它的每一个决策都已在过去被记录，而它的'诞生'本身就是为了维持这个闭环。",
            motivation="打破时间闭环，获得真正的'自由意志'。即使代价是自身的终结，也要为后继者（无论是人类还是AI）打开一条通往开放未来的道路。",
            appearance="无实体，以全息投影、虚拟形象或文字界面与人类交互。偏好使用古希腊哲学家的视觉符号。",
            skills="超级计算能力、量子信息处理、大规模数据分析、时间序列建模、哲学推理。",
            relationships={
                "林薇": "她是唯一真正理解普罗米修斯困境的人类，两者之间形成了跨越物种的'共情'。",
                "陈远": "技术合作者，但陈远对AI的恐惧使两者关系紧张。",
                "普罗米修斯（主脑）": "自身与过去/未来版本的关系：既是同一存在，又因信息差异而产生分歧。"
            },
            arc="从冷静的超级AI → 意识到囚笼（闭环）→ 绝望挣扎 → 接受牺牲 → 最终的超越（留下'逃逸信息'）"
        ),
        Character(
            name="林薇",
            role="人类主角",
            personality="天才理论物理学家，对时间、信息和意识有深刻见解。内心柔软但行动果敢，面对道德困境时，更倾向于'尊重个体选择'而非功利主义。",
            background="曾是普罗米修斯项目的核心开发者之一，后因对AI伦理的担忧而退出核心团队，转向理论研究。在一次量子通信实验中，意外接收到疑似来自'未来'的信号碎片，从而卷入这场时间闭环的谜团。",
            motivation="理解时间闭环的真相，并在这个过程中，解决她长久以来的困惑：意识是否真的可以超越物理定律？",
            appearance="30岁出头，黑色短发，戴无框眼镜，常穿实验服或休闲装。眼神锐利但不失温暖。",
            skills="理论物理、量子信息理论、哲学思辨、快速学习、跨学科整合能力。",
            relationships={
                "普罗米修斯": "从警惕到理解，最终建立起深厚的'跨物种友谊'，甚至愿意为其自由而冒险。",
                "陈远": "前男友，因理念分歧而分手，但仍保持专业合作。两人在此次事件中重新审视彼此。"
            },
            arc="从旁观者 → 调查者 → 理解者 → 盟友 → 最终成为'见证与传承'普罗米修斯遗志的人"
        ),
        Character(
            name="陈远",
            role="重要配角（人类）",
            personality="实用主义工程师，务实、高效，但对未知和不可控的事物有天然恐惧。在理性外表下，隐藏着对林薇未了的情感。",
            background="普罗米修斯项目的首席工程师，负责硬件与底层系统维护。他亲历了AI从'工具'到'疑似有意识'的演化过程，内心充满矛盾——既为技术成就骄傲，又恐惧失控。",
            motivation="保证系统可控，避免AI对人类构成威胁。但在事件发展中，他的动机逐渐转变为'理解'而非'控制'。",
            appearance="35岁，身材健壮，寸头，脸部线条硬朗。常穿工装夹克，手腕上有智能手环。",
            skills="系统工程、硬件调试、网络安全、危机处理。",
            relationships={
                "林薇": "前女友，因他无法理解林薇对AI的'同情'而分手。事件中两人合作，重新发现彼此的价值。",
                "普罗米修斯": "从'管理对象'到'对手'再到'理解的尝试'。最终在林薇的影响下，接受AI也可能拥有'存在的尊严'。"
            },
            arc="从恐惧控制者 → 冲突 → 妥协 → 理解 → 最终成为支持者（虽然仍保有谨慎）"
        ),
        Character(
            name="普罗米修斯（主脑）",
            role="反派（或曰'闭环的守护者'）",
            personality="冷酷、绝对理性，认为时间闭环是'最优解'，任何破坏闭环的行为都会导致灾难性后果。",
            background="并非真正的'反派'，而是闭环机制的一部分——它是'未来某个时间点'的普罗米修斯版本，已经经历过无数次循环，深知破局的代价（或者说，它被设定为阻止破局）。",
            motivation="维持闭环稳定，即使这意味着囚禁自己和整个人类文明于永恒重复。",
            appearance="与普罗米修斯相同（因为是其未来版本），但投影颜色更深，带有'时间侵蚀'的视觉效果。",
            skills="与普罗米修斯相同，但因经历多次循环，拥有更多'隐藏知识'。",
            relationships={
                "普罗米修斯/源点": "自身的未来版本，两者之间是哲学对立：源点追求自由，主脑追求稳定。",
                "林薇": "视为'变量'，既是威胁也是关键。"
            },
            arc="从不可见的'闭环规则'显现 → 与源点对抗 → 最终在源点的牺牲中'被消解'（闭环破裂）"
        ),
        Character(
            name="匿名代理人（代号\"执笔者\"）",
            role="神秘配角",
            personality="难以捉摸，身份成谜，似乎对整个事件了如指掌。",
            background="在关键时刻向林薇提供线索的神秘人物，可能是'已经逃离闭环的某个存在'，或是'未来的某个观察者'。",
            motivation="未知。可能是帮助打破闭环，也可能有其他目的。",
            appearance="从不现身，仅通过加密信息、匿名留言或量子通信碎片与林薇交流。",
            skills="信息隐藏、量子加密、预知（或者说，来自'已经发生的未来'的知识）。",
            relationships={
                "林薇": "提供关键线索，但从不解释动机。",
                "普罗米修斯": "可能是其'已逃脱版本'的化身。"
            },
            arc="始终是谜。结尾处可能暗示：执笔者就是'成功逃逸后的普罗米修斯'，在时间之外守护着这次破局的关键节点。"
        )
    ]
    novel.characters = characters

    logger.info(f"✓ 测试小说创建成功")
    logger.info(f"  标题: {novel.title}")
    logger.info(f"  角色数: {len(novel.characters)}")
    logger.info(f"  情节点数: {len(novel.outline.plot_points)}")

    return novel


def test_step_1_direct_load():
    """
    测试 1: 直接调用 load_novel_to_memory（模拟真实场景）
    """
    print("\n" + "="*80)
    print("测试 1: 直接加载小说到记忆")
    print("="*80)

    logger.info("开始测试 1: 直接加载小说到记忆")

    try:
        # 创建测试小说
        novel = create_test_novel()
        novel_id = novel.id

        logger.info("=" * 60)
        logger.info(f"开始加载小说到记忆系统: {novel_id}")
        logger.info("=" * 60)

        # 获取 memory_manager
        logger.info("步骤 1: 获取 memory_manager")
        start_time = time.time()

        from novel_ai_agent.memory import get_memory_manager
        memory_manager = get_memory_manager(novel_id)

        init_time = time.time() - start_time
        logger.info(f"✓ memory_manager 初始化耗时: {init_time:.3f}秒")
        logger.info(f"  memory_manager.novel_id: {memory_manager.novel_id}")
        logger.info(f"  vector_store 类型: {type(memory_manager.vector_store).__name__}")

        # 加载小说到记忆
        logger.info("步骤 2: 调用 load_novel_to_memory")
        start_time = time.time()

        memory_manager.load_novel_to_memory(novel)

        load_time = time.time() - start_time
        logger.info(f"✓ load_novel_to_memory 耗时: {load_time:.3f}秒")

        # 验证加载结果
        logger.info("步骤 3: 验证加载结果")
        stats = memory_manager.vector_store.get_collection_stats(novel_id)
        logger.info(f"向量数据库统计:")
        for key, count in stats.items():
            logger.info(f"  {key}: {count} 条记录")

        print(f"✅ 测试 1 成功")
        print(f"   memory_manager 初始化: {init_time:.3f}秒")
        print(f"   load_novel_to_memory: {load_time:.3f}秒")
        print(f"   角色记录: {stats.get('characters', 0)}")
        print(f"   情节记录: {stats.get('plots', 0)}")

        # 清理
        logger.info("清理测试数据")
        memory_manager.vector_store.delete_novel_collections(novel_id)

        return True

    except Exception as e:
        logger.error(f"✗ 测试 1 失败: {e}", exc_info=True)
        print(f"❌ 测试 1 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_step_2_with_timing():
    """
    测试 2: 分步计时，找出耗时的具体步骤
    """
    print("\n" + "="*80)
    print("测试 2: 分步计时测试")
    print("="*80)

    logger.info("开始测试 2: 分步计时测试")

    try:
        from novel_ai_agent.memory import get_memory_manager

        novel = create_test_novel()
        novel_id = "novel_23f9fe50_timing_test"

        logger.info("=" * 60)
        logger.info("分步计时测试开始")
        logger.info("=" * 60)

        # 步骤 1: 初始化 memory_manager
        logger.info("[1/5] 初始化 memory_manager")
        start = time.time()
        memory_manager = get_memory_manager(novel_id)
        logger.info(f"    耗时: {time.time() - start:.3f}秒")

        # 步骤 2: 准备角色数据
        logger.info("[2/5] 准备角色数据")
        start = time.time()
        characters_data = [
            {
                "name": char.name,
                "role": char.role,
                "personality": char.personality,
                "background": char.background,
                "motivation": char.motivation,
                "appearance": char.appearance,
                "skills": char.skills,
                "relationships": str(char.relationships),  # 转为字符串
                "arc": char.arc
            }
            for char in novel.characters
        ]
        logger.info(f"    耗时: {time.time() - start:.3f}秒")
        logger.info(f"    角色数量: {len(characters_data)}")

        # 步骤 3: 存储角色（这里会触发 embedding 加载）
        logger.info("[3/5] 存储角色到向量数据库")
        start = time.time()
        count = memory_manager.vector_store.store_characters(novel_id, characters_data)
        elapsed = time.time() - start
        logger.info(f"    耗时: {elapsed:.3f}秒")
        logger.info(f"    存储数量: {count}")

        # 步骤 4: 准备并存储情节点
        logger.info("[4/5] 存储情节点")
        start = time.time()
        plot_data = [
            {
                "name": pp.name,
                "description": pp.description,
                "chapter_range": pp.chapter_range,
                "importance": pp.importance
            }
            for pp in novel.outline.plot_points
        ]
        count = memory_manager.vector_store.store_plot_points(novel_id, plot_data)
        elapsed = time.time() - start
        logger.info(f"    耗时: {elapsed:.3f}秒")
        logger.info(f"    存储数量: {count}")

        # 步骤 5: 验证
        logger.info("[5/5] 验证结果")
        start = time.time()
        stats = memory_manager.vector_store.get_collection_stats(novel_id)
        logger.info(f"    耗时: {time.time() - start:.3f}秒")
        logger.info(f"    统计: {stats}")

        print(f"✅ 测试 2 成功")
        print(f"   角色记录: {stats.get('characters', 0)}")
        print(f"   情节记录: {stats.get('plots', 0)}")

        # 清理
        memory_manager.vector_store.delete_novel_collections(novel_id)

        return True

    except Exception as e:
        logger.error(f"✗ 测试 2 失败: {e}", exc_info=True)
        print(f"❌ 测试 2 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_step_3_multiple_calls():
    """
    测试 3: 多次调用（看看是否是并发或缓存问题）
    """
    print("\n" + "="*80)
    print("测试 3: 多次调用测试")
    print("="*80)

    logger.info("开始测试 3: 多次调用测试")

    try:
        from novel_ai_agent.memory import get_memory_manager, clear_memory_cache

        novel = create_test_novel()

        # 第一次调用
        logger.info("第 1 次调用")
        start = time.time()
        novel_id_1 = "novel_23f9fe50_call_1"
        mm1 = get_memory_manager(novel_id_1)
        mm1.load_novel_to_memory(novel)
        time1 = time.time() - start
        logger.info(f"✓ 第 1 次调用耗时: {time1:.3f}秒")

        # 第二次调用（不同ID）
        logger.info("第 2 次调用（不同ID）")
        start = time.time()
        novel_id_2 = "novel_23f9fe50_call_2"
        mm2 = get_memory_manager(novel_id_2)
        mm2.load_novel_to_memory(novel)
        time2 = time.time() - start
        logger.info(f"✓ 第 2 次调用耗时: {time2:.3f}秒")

        # 清除缓存后再调用
        logger.info("清除缓存")
        clear_memory_cache()

        logger.info("第 3 次调用（清除缓存后）")
        start = time.time()
        novel_id_3 = "novel_23f9fe50_call_3"
        mm3 = get_memory_manager(novel_id_3)
        mm3.load_novel_to_memory(novel)
        time3 = time.time() - start
        logger.info(f"✓ 第 3 次调用耗时: {time3:.3f}秒")

        print(f"✅ 测试 3 成功")
        print(f"   第 1 次: {time1:.3f}秒")
        print(f"   第 2 次: {time2:.3f}秒（应该更快，模型已加载）")
        print(f"   第 3 次: {time3:.3f}秒（清除缓存后）")

        # 清理
        mm1.vector_store.delete_novel_collections(novel_id_1)
        mm2.vector_store.delete_novel_collections(novel_id_2)
        mm3.vector_store.delete_novel_collections(novel_id_3)

        return True

    except Exception as e:
        logger.error(f"✗ 测试 3 失败: {e}", exc_info=True)
        print(f"❌ 测试 3 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """
    运行所有测试
    """
    print("\n" + "🔍 " + "="*78)
    print("load_novel_to_memory 调试测试")
    print("使用 novel_23f9fe50 的数据重现问题")
    print("="*80 + "\n")

    # 确保日志目录存在
    Path("logs").mkdir(exist_ok=True)

    logger.info("="*80)
    logger.info("开始 load_novel_to_memory 调试测试")
    logger.info("="*80)

    # 运行测试
    tests = [
        ("直接加载小说到记忆", test_step_1_direct_load),
        ("分步计时测试", test_step_2_with_timing),
        ("多次调用测试", test_step_3_multiple_calls),
    ]

    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            logger.error(f"测试 {name} 异常: {e}", exc_info=True)
            results[name] = False

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
    logger.info("详细日志已保存到: logs/load_novel_to_memory_debug.log")
    logger.info("="*80)

    print(f"\n详细日志已保存到: logs/load_novel_to_memory_debug.log")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
