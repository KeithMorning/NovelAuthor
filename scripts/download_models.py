#!/usr/bin/env python3
"""
预下载所有需要的模型到本地缓存
确保后续运行完全离线
"""
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def download_embedding_models():
    """下载 Embedding 模型"""
    print("=" * 80)
    print("下载 Embedding 模型")
    print("=" * 80)

    from sentence_transformers import SentenceTransformer

    model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    print(f"\n正在下载模型: {model_name}")
    print("这可能需要几分钟，取决于网络速度...")
    print("模型大小: ~470MB")

    try:
        # 下载模型
        model = SentenceTransformer(model_name)

        # 获取缓存路径
        cache_dir = Path.home() / '.cache' / 'huggingface' / 'hub'
        model_cache = cache_dir / f'models--{model_name.replace("/", "--")}'

        print(f"\n✓ 模型下载成功!")
        print(f"   缓存位置: {model_cache}")

        # 测试模型
        print("\n测试模型...")
        test_text = "这是一个测试句子。"
        embedding = model.encode(test_text)
        print(f"   ✓ 模型工作正常，向量维度: {len(embedding)}")

        return True

    except Exception as e:
        print(f"\n✗ 下载失败: {e}")
        print("\n可能的原因:")
        print("  1. 网络连接问题")
        print("  2. 无法访问 huggingface.co")
        print("  3. 磁盘空间不足")
        print("\n解决方案:")
        print("  1. 检查网络连接")
        print("  2. 如果在国内，可能需要配置镜像或使用代理")
        print("  3. 确保至少有 1GB 可用磁盘空间")
        return False


def check_model_cache():
    """检查模型是否已缓存"""
    print("\n" + "=" * 80)
    print("检查本地模型缓存")
    print("=" * 80)

    cache_dir = Path.home() / '.cache' / 'huggingface' / 'hub'
    model_name = "sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2"
    model_cache = cache_dir / f'models--{model_name}'

    print(f"\n缓存目录: {cache_dir}")
    print(f"模型目录: {model_cache}")

    if model_cache.exists():
        print(f"\n✓ 模型已缓存到本地")

        # 计算缓存大小
        total_size = sum(f.stat().st_size for f in model_cache.rglob('*') if f.is_file())
        size_mb = total_size / (1024 * 1024)
        print(f"   缓存大小: {size_mb:.1f} MB")

        # 列出主要文件
        print("\n   主要文件:")
        for item in sorted(model_cache.rglob('*'))[:10]:
            if item.is_file():
                size = item.stat().st_size / (1024 * 1024)
                print(f"   - {item.name}: {size:.1f} MB")

        return True
    else:
        print(f"\n✗ 模型未缓存")
        print("   需要运行下载")
        return False


def setup_offline_mode():
    """配置离线模式"""
    print("\n" + "=" * 80)
    print("配置离线模式")
    print("=" * 80)

    # 设置环境变量
    env_vars = {
        'HF_HUB_OFFLINE': '1',
        'TRANSFORMERS_OFFLINE': '1',
        'HF_DATASETS_OFFLINE': '1',
    }

    print("\n建议添加以下环境变量到 ~/.zshrc 或 ~/.bashrc:")
    print()
    for key, value in env_vars.items():
        print(f'export {key}={value}')

    print("\n或者在 Python 代码中设置:")
    print("```python")
    print("import os")
    for key, value in env_vars.items():
        print(f"os.environ['{key}'] = '{value}'")
    print("```")


def test_offline_mode():
    """测试离线模式"""
    print("\n" + "=" * 80)
    print("测试离线模式")
    print("=" * 80)

    # 设置离线模式
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'

    print("\n设置环境变量:")
    print("  HF_HUB_OFFLINE=1")
    print("  TRANSFORMERS_OFFLINE=1")

    try:
        from sentence_transformers import SentenceTransformer

        print("\n加载模型（离线模式）...")
        model = SentenceTransformer(
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )

        # 测试
        test_texts = [
            "人工智能正在改变世界。",
            "科幻小说充满想象力。",
        ]

        print("生成嵌入向量...")
        embeddings = model.encode(test_texts)

        print(f"\n✓ 离线模式测试成功!")
        print(f"   处理文本数: {len(test_texts)}")
        print(f"   向量维度: {embeddings.shape[1]}")
        print("   无任何网络请求")

        return True

    except Exception as e:
        print(f"\n✗ 离线模式测试失败: {e}")
        print("\n这可能意味着:")
        print("  1. 模型未完全下载")
        print("  2. 缓存文件损坏")
        print("  3. 需要重新下载模型")
        return False


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("本地模型管理工具")
    print("=" * 80)
    print()
    print("功能:")
    print("  1. 下载模型到本地缓存")
    print("  2. 配置完全离线运行模式")
    print("  3. 避免运行时的网络依赖")
    print()

    # 检查当前状态
    is_cached = check_model_cache()

    if not is_cached:
        print("\n" + "=" * 80)
        choice = input("\n是否现在下载模型? (y/n): ").strip().lower()

        if choice == 'y':
            success = download_embedding_models()
            if not success:
                print("\n下载失败，请检查网络连接后重试")
                sys.exit(1)
        else:
            print("\n跳过下载")
            print("注意: 首次运行时仍需要网络下载模型")
            sys.exit(0)

    # 配置离线模式
    setup_offline_mode()

    # 测试离线模式
    print("\n" + "=" * 80)
    choice = input("\n是否测试离线模式? (y/n): ").strip().lower()

    if choice == 'y':
        success = test_offline_mode()
        if success:
            print("\n" + "=" * 80)
            print("✓ 所有检查通过!")
            print("=" * 80)
            print("\n现在可以完全离线运行小说生成系统")
            print("无需担心 HuggingFace Hub 的网络问题")
        else:
            print("\n请重新运行此脚本下载模型")
            sys.exit(1)

    print()


if __name__ == "__main__":
    main()
