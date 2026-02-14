"""
Transformers 离线模式补丁
必须在导入 transformers 之前加载此模块
"""
import os
import logging

logger = logging.getLogger(__name__)

# 设置所有离线环境变量
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

logger.debug("embedding_patch: 环境变量已设置")

# 立即导入并 patch transformers
try:
    import transformers.tokenization_utils_tokenizers as tok_utils

    _original_is_base_mistral = tok_utils.is_base_mistral

    def patched_is_base_mistral(model_id):
        """
        替代 is_base_mistral，避免调用 model_info()
        直接检查本地文件系统
        """
        logger.debug(f"patched_is_base_mistral({model_id}) called")

        # 如果是本地路径,直接返回 False
        if os.path.exists(model_id):
            logger.debug(f"  -> 本地路径存在，返回 False")
            return False

        # 否则也返回 False（避免网络请求）
        logger.debug(f"  -> 非本地路径，返回 False（避免网络请求）")
        return False

    # 替换函数
    tok_utils.is_base_mistral = patched_is_base_mistral
    logger.debug("embedding_patch: is_base_mistral 已被 patch")

except ImportError as e:
    logger.warning(f"embedding_patch: 无法导入 transformers: {e}")
except Exception as e:
    logger.warning(f"embedding_patch: patch 失败: {e}")
