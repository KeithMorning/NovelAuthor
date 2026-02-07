"""
本地 Embedding 调试测试
目标：找出为什么 download_models.py 可以离线工作，但集成到系统中就失败
"""
import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/embedding_debug.log', mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 测试用例
test_texts = [
    "这是第一个测试句子。",
    "人工智能正在改变世界。",
    "科幻小说充满想象力。"
]

test_query = "AI 技术"


def test_step_1_direct_sentence_transformers():
    """
    测试 1: 直接使用 sentence-transformers（模拟 download_models.py 的做法）
    """
    print("\n" + "="*80)
    print("测试 1: 直接使用 sentence-transformers")
    print("="*80)

    logger.info("开始测试 1: 直接使用 sentence-transformers")

    try:
        # 设置环境变量（和 download_models.py 一样）
        logger.info("设置离线模式环境变量")
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        os.environ['HF_DATASETS_OFFLINE'] = '1'
        os.environ['TOKENIZERS_PARALLELISM'] = 'false'

        logger.info("导入 sentence_transformers")
        from sentence_transformers import SentenceTransformer

        logger.info("初始化 SentenceTransformer")
        model = SentenceTransformer(
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            device='cpu'
        )
        logger.info("✓ 模型初始化成功")

        logger.info("开始编码文本")
        embeddings = model.encode(
            test_texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        logger.info(f"✓ 编码成功，向量形状: {embeddings.shape}")

        print(f"✅ 测试 1 成功")
        print(f"   向量维度: {embeddings.shape[1]}")
        print(f"   文本数量: {embeddings.shape[0]}")
        return True

    except Exception as e:
        logger.error(f"✗ 测试 1 失败: {e}", exc_info=True)
        print(f"❌ 测试 1 失败: {e}")
        return False


def test_step_2_local_embeddings_class():
    """
    测试 2: 使用 LocalEmbeddings 类
    """
    print("\n" + "="*80)
    print("测试 2: 使用 LocalEmbeddings 类")
    print("="*80)

    logger.info("开始测试 2: 使用 LocalEmbeddings 类")

    try:
        logger.info("导入 LocalEmbeddings")
        from novel_ai_agent.memory.local_embeddings import LocalEmbeddings

        logger.info("初始化 LocalEmbeddings")
        embeddings = LocalEmbeddings()
        logger.info("✓ LocalEmbeddings 初始化成功")

        logger.info("调用 embed_documents")
        vectors = embeddings.embed_documents(test_texts)
        logger.info(f"✓ embed_documents 成功，向量数量: {len(vectors)}, 维度: {len(vectors[0])}")

        logger.info("调用 embed_query")
        query_vector = embeddings.embed_query(test_query)
        logger.info(f"✓ embed_query 成功，向量维度: {len(query_vector)}")

        print(f"✅ 测试 2 成功")
        print(f"   向量维度: {len(vectors[0])}")
        print(f"   文本数量: {len(vectors)}")
        return True

    except Exception as e:
        logger.error(f"✗ 测试 2 失败: {e}", exc_info=True)
        print(f"❌ 测试 2 失败: {e}")
        return False


def test_step_3_vector_store_integration():
    """
    测试 3: 集成到 VectorMemoryStore（模拟真实使用场景）
    """
    print("\n" + "="*80)
    print("测试 3: VectorMemoryStore 集成测试")
    print("="*80)

    logger.info("开始测试 3: VectorMemoryStore 集成测试")

    try:
        logger.info("导入 VectorMemoryStore")
        from novel_ai_agent.memory.vector_store import VectorMemoryStore

        logger.info("初始化 VectorMemoryStore")
        vector_store = VectorMemoryStore()
        logger.info("✓ VectorMemoryStore 初始化成功")

        # 测试存储角色信息
        logger.info("测试存储角色信息")
        test_characters = [
            {
                "name": "张三",
                "role": "主角",
                "personality": "勇敢、聪明",
                "background": "程序员出身",
                "motivation": "拯救世界",
                "appearance": "黑色短发",
                "skills": "编程、黑客",
                "relationships": "李四的好友",
                "arc": "从普通人成长为英雄"
            }
        ]

        count = vector_store.store_characters("test_novel", test_characters)
        logger.info(f"✓ 存储角色成功，数量: {count}")

        # 测试搜索角色
        logger.info("测试搜索角色")
        results = vector_store.search_characters("test_novel", "程序员", k=1)
        logger.info(f"✓ 搜索角色成功，结果数量: {len(results)}")

        print(f"✅ 测试 3 成功")
        print(f"   存储角色数: {count}")
        print(f"   搜索结果数: {len(results)}")

        # 清理测试数据
        logger.info("清理测试数据")
        vector_store.delete_novel_collections("test_novel")
        logger.info("✓ 清理完成")

        return True

    except Exception as e:
        logger.error(f"✗ 测试 3 失败: {e}", exc_info=True)
        print(f"❌ 测试 3 失败: {e}")
        return False


def test_step_4_concurrent_usage():
    """
    测试 4: 并发使用（模拟真实场景中可能的并发问题）
    """
    print("\n" + "="*80)
    print("测试 4: 并发使用测试")
    print("="*80)

    logger.info("开始测试 4: 并发使用测试")

    try:
        from novel_ai_agent.memory.local_embeddings import LocalEmbeddings

        logger.info("创建多个 LocalEmbeddings 实例")
        embeddings1 = LocalEmbeddings()
        embeddings2 = LocalEmbeddings()
        logger.info("✓ 创建多个实例成功")

        logger.info("实例 1 编码")
        vectors1 = embeddings1.embed_documents(test_texts)
        logger.info(f"✓ 实例 1 编码成功")

        logger.info("实例 2 编码")
        vectors2 = embeddings2.embed_documents(test_texts)
        logger.info(f"✓ 实例 2 编码成功")

        # 验证结果一致性
        import numpy as np
        diff = np.abs(np.array(vectors1) - np.array(vectors2)).max()
        logger.info(f"两次编码的最大差异: {diff}")

        print(f"✅ 测试 4 成功")
        print(f"   实例 1 向量维度: {len(vectors1[0])}")
        print(f"   实例 2 向量维度: {len(vectors2[0])}")
        print(f"   最大差异: {diff}")
        return True

    except Exception as e:
        logger.error(f"✗ 测试 4 失败: {e}", exc_info=True)
        print(f"❌ 测试 4 失败: {e}")
        return False


def test_step_5_model_loading_timing():
    """
    测试 5: 模型加载时机测试（懒加载 vs 立即加载）
    """
    print("\n" + "="*80)
    print("测试 5: 模型加载时机测试")
    print("="*80)

    logger.info("开始测试 5: 模型加载时机测试")

    try:
        from novel_ai_agent.memory.local_embeddings import LocalEmbeddings
        import time

        logger.info("创建实例（此时应该是懒加载，不加载模型）")
        start_time = time.time()
        embeddings = LocalEmbeddings()
        init_time = time.time() - start_time
        logger.info(f"✓ 实例创建耗时: {init_time:.3f}秒")

        logger.info("首次调用 embed_documents（此时才会加载模型）")
        start_time = time.time()
        vectors = embeddings.embed_documents(test_texts)
        first_encode_time = time.time() - start_time
        logger.info(f"✓ 首次编码耗时: {first_encode_time:.3f}秒")

        logger.info("第二次调用 embed_documents（模型已加载）")
        start_time = time.time()
        vectors = embeddings.embed_documents(test_texts)
        second_encode_time = time.time() - start_time
        logger.info(f"✓ 第二次编码耗时: {second_encode_time:.3f}秒")

        print(f"✅ 测试 5 成功")
        print(f"   实例创建: {init_time:.3f}秒")
        print(f"   首次编码: {first_encode_time:.3f}秒")
        print(f"   第二次编码: {second_encode_time:.3f}秒")
        return True

    except Exception as e:
        logger.error(f"✗ 测试 5 失败: {e}", exc_info=True)
        print(f"❌ 测试 5 失败: {e}")
        return False


def test_step_6_environment_variables():
    """
    测试 6: 环境变量影响测试
    """
    print("\n" + "="*80)
    print("测试 6: 环境变量影响测试")
    print("="*80)

    logger.info("开始测试 6: 环境变量影响测试")

    try:
        # 保存当前环境变量
        original_env = {}
        for key in ['HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'HF_DATASETS_OFFLINE']:
            original_env[key] = os.environ.get(key)

        logger.info("当前环境变量:")
        logger.info(f"  HF_HUB_OFFLINE: {os.environ.get('HF_HUB_OFFLINE')}")
        logger.info(f"  TRANSFORMERS_OFFLINE: {os.environ.get('TRANSFORMERS_OFFLINE')}")
        logger.info(f"  HF_DATASETS_OFFLINE: {os.environ.get('HF_DATASETS_OFFLINE')}")

        # 测试清除环境变量后的行为
        logger.info("清除所有离线模式环境变量")
        for key in ['HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'HF_DATASETS_OFFLINE']:
            os.environ.pop(key, None)

        logger.info("环境变量清除后尝试初始化")
        from novel_ai_agent.memory.local_embeddings import LocalEmbeddings
        embeddings = LocalEmbeddings()

        logger.info("检查环境变量是否被重新设置")
        logger.info(f"  HF_HUB_OFFLINE: {os.environ.get('HF_HUB_OFFLINE')}")
        logger.info(f"  TRANSFORMERS_OFFLINE: {os.environ.get('TRANSFORMERS_OFFLINE')}")

        vectors = embeddings.embed_documents(test_texts)
        logger.info(f"✓ 编码成功，向量维度: {len(vectors[0])}")

        # 恢复环境变量
        logger.info("恢复原始环境变量")
        for key, value in original_env.items():
            if value is not None:
                os.environ[key] = value

        print(f"✅ 测试 6 成功")
        return True

    except Exception as e:
        logger.error(f"✗ 测试 6 失败: {e}", exc_info=True)
        print(f"❌ 测试 6 失败: {e}")

        # 恢复环境变量
        for key, value in original_env.items():
            if value is not None:
                os.environ[key] = value

        return False


def main():
    """
    运行所有测试
    """
    print("\n" + "🔍 " + "="*78)
    print("本地 Embedding 调试测试套件")
    print("目标: 找出为什么 download_models.py 可以工作，但集成后失败")
    print("="*80 + "\n")

    # 确保日志目录存在
    Path("logs").mkdir(exist_ok=True)

    logger.info("="*80)
    logger.info("开始本地 Embedding 调试测试")
    logger.info("="*80)

    # 运行测试
    tests = [
        ("直接使用 sentence-transformers", test_step_1_direct_sentence_transformers),
        ("使用 LocalEmbeddings 类", test_step_2_local_embeddings_class),
        ("VectorMemoryStore 集成", test_step_3_vector_store_integration),
        ("并发使用", test_step_4_concurrent_usage),
        ("模型加载时机", test_step_5_model_loading_timing),
        ("环境变量影响", test_step_6_environment_variables),
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
    logger.info("详细日志已保存到: logs/embedding_debug.log")
    logger.info("="*80)

    print(f"\n详细日志已保存到: logs/embedding_debug.log")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
