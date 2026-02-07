"""
本地 Embedding 实现
完全离线运行，避免 HuggingFace Hub 网络依赖
"""
import os
import time
from pathlib import Path
from typing import List
import numpy as np


class LocalEmbeddings:
    """
    本地 Embedding 实现，使用已缓存的模型
    避免运行时的网络请求
    """

    def __init__(self, model_name: str = None, cache_folder: str = None):
        """
        初始化本地 embedding

        Args:
            model_name: 模型名称（可选）
            cache_folder: 本地缓存目录（可选）
        """
        self.model_name = model_name or "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

        # 设置完全离线模式
        self._setup_offline_mode(cache_folder)

        # 延迟加载模型（懒加载）
        self._model = None
        self._tokenizer = None

    def _setup_offline_mode(self, cache_folder: str = None):
        """
        配置完全离线模式
        """
        # 1. 设置环境变量，禁用网络
        # 这些环境变量必须在导入 sentence_transformers 之前设置
        os.environ['HF_HUB_OFFLINE'] = '1'  # HuggingFace Hub 离线模式
        os.environ['TRANSFORMERS_OFFLINE'] = '1'  # Transformers 离线模式
        os.environ['HF_DATASETS_OFFLINE'] = '1'  # Datasets 离线模式

        # 禁用 telemetry 和更新检查
        os.environ['TOKENIZERS_PARALLELISM'] = 'false'
        os.environ['NO_PROXY'] = '*'  # 禁用所有代理

        # 2. 如果指定了缓存目录，设置它
        if cache_folder:
            os.environ['TRANSFORMERS_CACHE'] = cache_folder
            os.environ['HF_HOME'] = cache_folder

        # 3. 检查模型是否已缓存
        self._check_model_cache()

    def _check_model_cache(self):
        """检查模型是否已在本地缓存"""
        cache_dir = Path(os.environ.get('HF_HOME', Path.home() / '.cache' / 'huggingface'))

        # 转换模型名称为缓存目录格式
        model_cache_name = self.model_name.replace('/', '--')
        model_path = cache_dir / 'hub' / f'models--{model_cache_name}'

        if not model_path.exists():
            raise RuntimeError(
                f"模型未缓存到本地: {self.model_name}\n"
                f"预期路径: {model_path}\n"
                f"请先运行预下载脚本: python scripts/download_models.py"
            )

        self.model_cache_path = model_path
        print(f"✓ 使用本地缓存模型: {model_path}")

    def _load_model(self):
        """懒加载模型（只在首次使用时加载）"""
        import logging
        logger = logging.getLogger(__name__)

        if self._model is not None:
            logger.debug("模型已加载，跳过重复加载")
            return

        logger.info("="*60)
        logger.info("开始加载 Embedding 模型")
        logger.info("="*60)

        # 确保离线模式环境变量已设置（防止被其他代码重置）
        logger.info("步骤 1: 设置离线模式环境变量")
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        logger.info(f"  HF_HUB_OFFLINE = {os.environ.get('HF_HUB_OFFLINE')}")
        logger.info(f"  TRANSFORMERS_OFFLINE = {os.environ.get('TRANSFORMERS_OFFLINE')}")

        # 禁用 huggingface_hub 的日志，避免显示网络重试信息
        logger.info("步骤 2: 禁用 huggingface_hub 日志")
        import logging as std_logging
        std_logging.getLogger('huggingface_hub').setLevel(std_logging.ERROR)
        std_logging.getLogger('huggingface_hub.file_download').setLevel(std_logging.ERROR)

        # 重试逻辑：处理网络不稳定导致的加载失败
        max_retries = 3
        retry_delay = 2  # 秒

        logger.info(f"步骤 3: 开始加载模型（最多重试 {max_retries} 次）")

        for attempt in range(max_retries):
            try:
                logger.info(f"  尝试 {attempt + 1}/{max_retries}:")

                # 使用 sentence-transformers 加载本地模型
                logger.info(f"    [1] 导入 SentenceTransformer")
                load_start = time.time()
                from sentence_transformers import SentenceTransformer
                logger.info(f"    [1] 导入完成，耗时: {time.time() - load_start:.3f}秒")

                logger.info(f"    [2] 创建 SentenceTransformer 实例")
                logger.info(f"        模型名: {self.model_name}")
                logger.info(f"        设备: cpu")
                logger.info(f"        缓存目录: {os.environ.get('TRANSFORMERS_CACHE', 'default')}")

                model_start = time.time()

                # 根据 download_models.py 的成功经验：
                # 只设置环境变量，不使用 local_files_only 参数
                # 因为 sentence-transformers 在设置了 HF_HUB_OFFLINE 后会自动处理
                self._model = SentenceTransformer(
                    self.model_name,
                    device='cpu',
                    cache_folder=os.environ.get('TRANSFORMERS_CACHE'),
                    trust_remote_code=False,
                )

                model_time = time.time() - model_start
                logger.info(f"    [2] 实例创建完成，耗时: {model_time:.3f}秒")

                success_msg = "✓ 模型加载成功（完全离线）"
                logger.info(success_msg)
                logger.info("="*60)

                return  # 成功，退出函数

            except Exception as e:
                error_msg = str(e)
                logger.error(f"    [!] 模型加载失败: {error_msg}")
                logger.error(f"    [!] 错误类型: {type(e).__name__}")

                # 记录详细的堆栈信息
                import traceback
                logger.debug("详细堆栈:")
                logger.debug(traceback.format_exc())

                # 检查是否是网络相关错误
                is_network_error = any(keyword in error_msg for keyword in [
                    "Connection reset",
                    "client has been closed",
                    "Errno 54",
                    "EOF occurred",
                    "RemoteDisconnected",
                    "ConnectionResetError"
                ])

                if is_network_error and attempt < max_retries - 1:
                    # 网络错误且还有重试机会
                    warning_msg = f"⚠️  检测到网络错误，{retry_delay}秒后重试..."
                    logger.warning(warning_msg)
                    logger.warning(f"    原因: {error_msg[:100]}")

                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                    logger.info(f"  准备第 {attempt + 2} 次尝试...")
                    continue
                else:
                    # 最后一次尝试失败，或者是非网络错误
                    logger.error("="*60)
                    logger.error("模型加载最终失败")
                    logger.error("="*60)

                    if is_network_error:
                        logger.error(f"网络错误导致失败（已重试 {max_retries} 次）")
                        logger.error(f"原始错误: {error_msg}")
                        logger.error("可能的原因:")
                        logger.error("  1. sentence-transformers 仍在尝试网络请求")
                        logger.error("  2. httpx 客户端连接被中断")
                        logger.error("  3. 环境变量未生效")
                        logger.error("当前环境变量:")
                        logger.error(f"  HF_HUB_OFFLINE={os.environ.get('HF_HUB_OFFLINE')}")
                        logger.error(f"  TRANSFORMERS_OFFLINE={os.environ.get('TRANSFORMERS_OFFLINE')}")

                        raise RuntimeError(
                            f"网络错误导致模型加载失败（已重试 {max_retries} 次）。\n"
                            f"这通常是因为 sentence-transformers 尝试检查模型更新，但网络不稳定。\n"
                            f"解决方案：\n"
                            f"1. 检查网络连接是否稳定\n"
                            f"2. 稍后重试\n"
                            f"3. 或者使用完全断网的环境运行\n"
                            f"原始错误: {error_msg}"
                        ) from e
                    else:
                        logger.error(f"非网络错误: {error_msg}")
                        raise RuntimeError(
                            f"本地模型加载失败: {error_msg}\n"
                            f"请确保模型已缓存到本地，或运行: python3 scripts/download_models.py"
                        ) from e

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        对文档列表生成嵌入向量

        Args:
            texts: 文本列表

        Returns:
            嵌入向量列表
        """
        import logging
        logger = logging.getLogger(__name__)

        if not texts:
            logger.debug("embed_documents: 空文本列表，返回空结果")
            return []

        logger.info(f"embed_documents: 开始编码 {len(texts)} 个文本")
        logger.debug(f"  文本长度: {[len(t) for t in texts[:3]]}{'...' if len(texts) > 3 else ''}")

        # 懒加载模型
        if self._model is None:
            logger.info("  模型未加载，触发懒加载...")
            load_start = time.time()
            self._load_model()
            logger.info(f"  模型加载完成，耗时: {time.time() - load_start:.3f}秒")
        else:
            logger.debug("  模型已加载，直接使用")

        # 生成嵌入
        logger.info("  开始调用 model.encode()...")
        encode_start = time.time()

        try:
            embeddings = self._model.encode(
                texts,
                normalize_embeddings=True,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            encode_time = time.time() - encode_start

            logger.info(f"  ✓ 编码完成，耗时: {encode_time:.3f}秒")
            logger.info(f"  生成向量形状: {embeddings.shape}")

            result = embeddings.tolist()
            logger.debug(f"  返回 {len(result)} 个向量，每个维度: {len(result[0])}")

            return result

        except Exception as e:
            logger.error(f"  ✗ 编码失败: {e}")
            logger.error(f"  错误类型: {type(e).__name__}")
            import traceback
            logger.error(f"  堆栈信息:\n{traceback.format_exc()}")
            raise

    def embed_query(self, text: str) -> List[float]:
        """
        对单个查询生成嵌入向量

        Args:
            text: 查询文本

        Returns:
            嵌入向量
        """
        return self.embed_documents([text])[0]


class FallbackEmbeddings:
    """
    后备 Embedding 方案（如果模型未缓存）
    使用 TF-IDF 作为简单的文本向量化方法
    """

    def __init__(self, vector_size: int = 384):
        """
        Args:
            vector_size: 向量维度（与 paraphrase-multilingual-MiniLM-L12-v2 保持一致）
        """
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD

        self.vector_size = vector_size
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.svd = TruncatedSVD(n_components=min(vector_size, 1000))
        self._fitted = False

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """生成 TF-IDF 嵌入"""
        if not texts:
            return []

        # 首次使用时训练
        if not self._fitted:
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            embeddings = self.svd.fit_transform(tfidf_matrix)
            self._fitted = True
        else:
            tfidf_matrix = self.vectorizer.transform(texts)
            embeddings = self.svd.transform(tfidf_matrix)

        # 归一化
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / (norms + 1e-8)

        # 填充到目标维度
        if embeddings.shape[1] < self.vector_size:
            padding = np.zeros((embeddings.shape[0], self.vector_size - embeddings.shape[1]))
            embeddings = np.hstack([embeddings, padding])

        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """生成查询嵌入"""
        return self.embed_documents([text])[0]


def get_local_embeddings(use_fallback: bool = False) -> object:
    """
    获取本地 Embedding 实例

    Args:
        use_fallback: 如果为 True，在主方案失败时使用 TF-IDF 后备方案

    Returns:
        Embedding 实例
    """
    try:
        # 尝试使用完全本地的 sentence-transformers
        embeddings = LocalEmbeddings()
        return embeddings
    except RuntimeError as e:
        if use_fallback:
            print(f"⚠️  主 Embedding 方案不可用，使用 TF-IDF 后备方案")
            print(f"   原因: {str(e)}")
            return FallbackEmbeddings()
        else:
            raise


if __name__ == "__main__":
    # 测试本地 embedding
    print("=" * 80)
    print("测试本地 Embedding")
    print("=" * 80)

    # 测试主方案
    print("\n1. 测试 LocalEmbeddings:")
    try:
        embeddings = LocalEmbeddings()

        # 测试文本
        texts = [
            "这是一个测试句子。",
            "人工智能正在改变世界。",
            "科幻小说充满想象力。"
        ]

        print(f"   输入文本数: {len(texts)}")

        # 生成嵌入
        vectors = embeddings.embed_documents(texts)
        print(f"   ✓ 生成嵌入成功")
        print(f"   向量维度: {len(vectors[0])}")
        print(f"   向量示例: {vectors[0][:5]}...")

        # 测试查询
        query = "AI 技术"
        query_vector = embeddings.embed_query(query)
        print(f"   ✓ 查询嵌入成功，维度: {len(query_vector)}")

    except Exception as e:
        print(f"   ✗ LocalEmbeddings 失败: {e}")

    # 测试后备方案
    print("\n2. 测试 FallbackEmbeddings (TF-IDF):")
    try:
        fallback = FallbackEmbeddings()

        vectors = fallback.embed_documents(texts)
        print(f"   ✓ TF-IDF 嵌入成功")
        print(f"   向量维度: {len(vectors[0])}")

    except Exception as e:
        print(f"   ✗ FallbackEmbeddings 失败: {e}")

    print("\n" + "=" * 80)
