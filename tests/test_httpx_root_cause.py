#!/usr/bin/env python3
"""
追踪 HTTP 客户端关闭的本质原因
"""
import asyncio


async def test_anthropic_client_lifecycle():
    """
    测试 Anthropic SDK 的客户端生命周期
    这是问题的本质
    """
    print("=" * 80)
    print("测试: Anthropic SDK 的 httpx.Client 管理")
    print("=" * 80)

    import anthropic
    import httpx

    print("\n1. 创建第一个 Anthropic 客户端")
    client1 = anthropic.Anthropic(api_key="sk-fake-key-for-testing")
    print(f"   client1 ID: {id(client1)}")
    print(f"   client1._client (httpx.Client) ID: {id(client1._client)}")
    print(f"   client1._client.is_closed: {client1._client.is_closed}")

    print("\n2. 创建第二个 Anthropic 客户端")
    client2 = anthropic.Anthropic(api_key="sk-fake-key-for-testing")
    print(f"   client2 ID: {id(client2)}")
    print(f"   client2._client (httpx.Client) ID: {id(client2._client)}")
    print(f"   client2._client.is_closed: {client2._client.is_closed}")

    print("\n3. 比较两个客户端的 httpx.Client")
    if id(client1._client) == id(client2._client):
        print("   ⚠️  共享同一个 httpx.Client!")
        print("   ✗ 这就是问题的本质：如果一个被关闭，另一个也会失效")
        shared_client = True
    else:
        print("   ℹ️  使用独立的 httpx.Client")
        shared_client = False

    print("\n4. 关闭 client1 并检查影响")
    client1.close()
    print(f"   client1._client.is_closed: {client1._client.is_closed}")

    if shared_client:
        print(f"   client2._client.is_closed: {client2._client.is_closed}")
        if client2._client.is_closed:
            print("   ✗ 关闭 client1 导致 client2 的 httpx.Client 也被关闭!")
            print("   ✗ 这就是 'Cannot send a request, as the client has been closed' 的根源")
        else:
            print("   ✓ client2 的 httpx.Client 仍然可用")
    else:
        print(f"   client2._client.is_closed: {client2._client.is_closed}")
        print("   ✓ client2 不受影响")

    print("\n5. 尝试使用已关闭的客户端")
    try:
        # 模拟 HuggingFace Embeddings 使用 httpx
        test_client = httpx.Client()
        test_client.close()

        # 尝试发送请求
        test_client.get("https://huggingface.co")
    except RuntimeError as e:
        print(f"   ✓ 成功重现错误: {e}")
        print("   这就是用户看到的错误信息!")

    client2.close()

    return shared_client


async def test_huggingface_hub_client():
    """
    测试 HuggingFace Hub 如何使用 HTTP 客户端
    """
    print("\n" + "=" * 80)
    print("测试: HuggingFace Hub 的 HTTP 客户端")
    print("=" * 80)

    try:
        import huggingface_hub
        print(f"\nhuggingface_hub version: {huggingface_hub.__version__}")

        # 检查是否有全局 HTTP 客户端
        if hasattr(huggingface_hub, '_http_client'):
            print("✓ 找到全局 HTTP 客户端")

        # 检查 huggingface_hub 的内部实现
        import huggingface_hub.file_download as fd
        import inspect

        # 查看 get_hf_file_metadata 函数（用于检查文件是否存在）
        if hasattr(fd, 'get_hf_file_metadata'):
            print("\n✓ 找到 get_hf_file_metadata 函数")
            sig = inspect.signature(fd.get_hf_file_metadata)
            print(f"   签名: {sig}")

            # 查看源码中是否使用了全局客户端
            source = inspect.getsource(fd.get_hf_file_metadata)
            if 'http_client' in source or 'httpx' in source:
                print("   ℹ️  函数内部使用了 HTTP 客户端")

        # 检查是否有 get_session 或类似函数
        for attr_name in dir(fd):
            if 'session' in attr_name.lower() or 'client' in attr_name.lower():
                attr = getattr(fd, attr_name)
                if callable(attr):
                    print(f"   找到相关函数: {attr_name}")

    except ImportError:
        print("✗ huggingface_hub 未安装")


async def test_langchain_anthropic():
    """
    测试 LangChain ChatAnthropic 如何管理客户端
    """
    print("\n" + "=" * 80)
    print("测试: LangChain ChatAnthropic 的客户端管理")
    print("=" * 80)

    try:
        from langchain_anthropic import ChatAnthropic
        import inspect

        print("\n1. 检查 ChatAnthropic 的属性")

        # 检查是否有 client 属性
        # 我们需要创建一个实例，但这需要 API key
        # 所以我们只检查类定义

        print("   ChatAnthropic 的方法:")
        for method_name in dir(ChatAnthropic):
            if not method_name.startswith('_'):
                method = getattr(ChatAnthropic, method_name)
                if callable(method) and 'client' in method_name.lower():
                    print(f"   - {method_name}")

        # 查看 __init__ 方法
        if hasattr(ChatAnthropic, '__init__'):
            try:
                source = inspect.getsource(ChatAnthropic.__init__)
                if 'Anthropic(' in source:
                    print("\n   ℹ️  ChatAnthropic 在 __init__ 中创建 Anthropic 客户端")
                    print("   ℹ️  每个 ChatAnthropic 实例可能共享或独立管理客户端")
            except (OSError, TypeError):
                print("\n   ℹ️  无法获取源码（可能是编译的代码）")

    except ImportError:
        print("✗ langchain_anthropic 未安装")


async def main():
    print("\n" + "=" * 80)
    print("HTTP 客户端关闭问题 - 本质原因追踪")
    print("=" * 80)
    print("\n问题描述:")
    print("  在 create_novel_workflow 中，'加载记忆' 步骤失败")
    print("  错误: RuntimeError: Cannot send a request, as the client has been closed")
    print("\n追踪目标:")
    print("  1. 是否有多个组件共享同一个 httpx.Client?")
    print("  2. 谁关闭了这个共享的客户端?")
    print("  3. 为什么 HuggingFace Embeddings 初始化会受影响?")
    print("\n" + "=" * 80)

    # 测试1: Anthropic SDK 的客户端管理
    shared = await test_anthropic_client_lifecycle()

    # 测试2: HuggingFace Hub 的客户端
    await test_huggingface_hub_client()

    # 测试3: LangChain ChatAnthropic
    await test_langchain_anthropic()

    # 总结
    print("\n" + "=" * 80)
    print("本质原因分析")
    print("=" * 80)

    if shared:
        print("\n✗ 发现问题: Anthropic SDK 的多个实例共享同一个 httpx.Client")
        print("\n可能的情况:")
        print("1. LangChain 创建了多个 ChatAnthropic 实例（用于大纲、角色生成）")
        print("2. 这些实例内部的 Anthropic 客户端可能共享同一个 httpx.Client")
        print("3. 当某个实例被销毁或关闭时，共享的 httpx.Client 被关闭")
        print("4. 后续的 HuggingFace Embeddings 初始化尝试使用这个已关闭的客户端")
        print("5. 导致 'Cannot send a request, as the client has been closed' 错误")
    else:
        print("\n✓ Anthropic SDK 的实例使用独立的 httpx.Client")
        print("\n其他可能原因:")
        print("1. 全局的 httpx 客户端被某处关闭")
        print("2. HuggingFace Hub 内部的客户端管理问题")
        print("3. 事件循环相关的问题")

    print("\n" + "=" * 80)
    print("解决方案")
    print("=" * 80)
    print("\n1. 确保每个组件使用独立的 HTTP 客户端")
    print("2. 避免共享全局 HTTP 客户端")
    print("3. 在异步环境中正确管理客户端生命周期")
    print("4. 使用 context manager 确保资源正确释放")
    print("5. 为 HuggingFace Embeddings 提供独立的、不会被关闭的客户端")


if __name__ == "__main__":
    asyncio.run(main())
