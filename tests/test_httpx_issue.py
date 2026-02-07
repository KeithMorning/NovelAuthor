#!/usr/bin/env python3
"""
测试 HTTP 客户端关闭问题的本质原因
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


async def test_scenario_1():
    """
    场景1: 多次 LLM 调用后，HuggingFace Embeddings 初始化
    模拟真实的 create_novel_workflow 流程
    """
    print("=" * 80)
    print("场景1: 模拟真实工作流")
    print("=" * 80)

    from langchain_anthropic import ChatAnthropic
    from novel_ai_agent.config.settings import Settings

    settings = Settings()

    # 步骤1: 生成大纲 (LLM 调用)
    print("\n1. 创建 ChatAnthropic 客户端用于生成大纲...")
    llm1 = ChatAnthropic(
        model=settings.get_model_name(),
        anthropic_api_key=settings.anthropic_api_key,
    )
    print(f"   ✓ llm1 创建成功: {id(llm1)}")
    print(f"   内部客户端: {id(llm1.client) if hasattr(llm1, 'client') else 'N/A'}")

    # 步骤2: 生成角色 (LLM 调用)
    print("\n2. 创建另一个 ChatAnthropic 客户端用于生成角色...")
    llm2 = ChatAnthropic(
        model=settings.get_model_name(),
        anthropic_api_key=settings.anthropic_api_key,
    )
    print(f"   ✓ llm2 创建成功: {id(llm2)}")
    print(f"   内部客户端: {id(llm2.client) if hasattr(llm2, 'client') else 'N/A'}")

    # 检查是否共享客户端
    if hasattr(llm1, 'client') and hasattr(llm2, 'client'):
        if id(llm1.client) == id(llm2.client):
            print("   ⚠️  两个 LLM 共享同一个内部客户端!")
        else:
            print("   ℹ️  两个 LLM 使用不同的内部客户端")

    # 步骤3: 初始化 HuggingFace Embeddings
    print("\n3. 初始化 HuggingFace Embeddings (可能需要下载模型)...")
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings

        # 检查是否有全局 HTTP 客户端
        import httpx
        print(f"   httpx 模块加载状态: OK")

        # 尝试初始化 embeddings
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={'device': 'cpu'},
        )
        print("   ✓ Embeddings 初始化成功")

    except RuntimeError as e:
        if "Cannot send a request" in str(e):
            print(f"   ✗ 复现了问题! {e}")
            print("\n   === 本质原因分析 ===")
            print("   HTTP 客户端在某处被关闭了")
            return False
        else:
            raise
    except Exception as e:
        print(f"   ✗ 其他错误: {type(e).__name__}: {e}")
        return False

    return True


async def test_scenario_2():
    """
    场景2: 检查 httpx 全局状态
    """
    print("\n" + "=" * 80)
    print("场景2: 检查 httpx 全局客户端")
    print("=" * 80)

    import httpx

    # 检查是否有全局客户端
    if hasattr(httpx, '_client'):
        print(f"✓ 发现全局客户端: {httpx._client}")
    else:
        print("✗ 没有全局客户端")

    # 检查模块级别的客户端实例
    print("\nhttpx 模块属性:")
    for attr in dir(httpx):
        obj = getattr(httpx, attr)
        if isinstance(obj, (httpx.Client, httpx.AsyncClient)):
            print(f"  - {attr}: {type(obj).__name__} (ID: {id(obj)})")


async def test_scenario_3():
    """
    场景3: 检查 Anthropic SDK 的客户端管理
    """
    print("\n" + "=" * 80)
    print("场景3: Anthropic SDK 客户端生命周期")
    print("=" * 80)

    import anthropic

    # 创建客户端
    print("\n1. 创建 Anthropic 客户端...")
    client1 = anthropic.Anthropic(api_key="sk-test")
    print(f"   client1 ID: {id(client1)}")
    print(f"   client1._client ID: {id(client1._client)}")
    print(f"   client1._client 类型: {type(client1._client)}")
    print(f"   client1._client.is_closed: {client1._client.is_closed}")

    # 创建另一个客户端
    print("\n2. 创建第二个 Anthropic 客户端...")
    client2 = anthropic.Anthropic(api_key="sk-test")
    print(f"   client2 ID: {id(client2)}")
    print(f"   client2._client ID: {id(client2._client)}")
    print(f"   client2._client.is_closed: {client2._client.is_closed}")

    # 检查是否共享
    if id(client1._client) == id(client2._client):
        print("\n   ⚠️  两个客户端共享同一个 httpx.Client!")
        print("   如果其中一个被关闭，另一个也会失效")
    else:
        print("\n   ℹ️  两个客户端使用独立的 httpx.Client")

    # 测试关闭行为
    print("\n3. 测试关闭行为...")
    client1.close()
    print(f"   client1._client.is_closed: {client1._client.is_closed}")
    if id(client1._client) == id(client2._client):
        print(f"   client2._client.is_closed: {client2._client.is_closed}")
        print("   ✗ 关闭 client1 也影响了 client2!")

    client2.close()


async def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("HTTP 客户端问题本质原因追踪")
    print("=" * 80)

    try:
        # 测试场景1: 模拟真实工作流
        success = await test_scenario_1()

        # 测试场景2: 全局客户端
        await test_scenario_2()

        # 测试场景3: Anthropic SDK
        await test_scenario_3()

        print("\n" + "=" * 80)
        print("总结")
        print("=" * 80)

        if success:
            print("✓ 所有测试通过，未能重现问题")
            print("  可能原因：")
            print("  1. 模型已经缓存到本地，不需要网络下载")
            print("  2. 问题只在特定网络环境下出现")
            print("  3. 问题与事件循环状态有关")
        else:
            print("✗ 成功重现问题")
            print("  本质原因：HTTP 客户端被提前关闭")

    except Exception as e:
        print(f"\n✗ 测试过程出错: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
