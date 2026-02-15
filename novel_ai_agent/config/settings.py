"""
配置管理模块
管理API密钥、模型配置和全局设置
支持多个LLM提供商: Anthropic Claude, OpenAI, DeepSeek等
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Literal
from enum import Enum


class LLMProvider(str, Enum):
    """LLM提供商枚举"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    AZURE = "azure"


class Settings(BaseSettings):
    """全局配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # LLM提供商配置
    llm_provider: str = "anthropic"  # 默认使用Anthropic

    # Anthropic配置
    anthropic_api_key: Optional[str] = None
    anthropic_api_base: Optional[str] = None

    # OpenAI配置
    openai_api_key: Optional[str] = None
    openai_api_base: Optional[str] = None
    openai_organization: Optional[str] = None

    # DeepSeek配置 (使用OpenAI兼容API)
    deepseek_api_key: Optional[str] = None
    deepseek_api_base: str = "https://api.deepseek.com/v1"

    # Azure OpenAI配置
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_deployment: Optional[str] = None
    azure_openai_api_version: str = "2024-02-01"

    # 模型配置 (根据provider自动选择)
    default_model: Optional[str] = None  # 如果为None,根据provider自动选择
    temperature: float = 0.7
    max_tokens: int = 8192  # DeepSeek API 限制最大 8192（约5000-6000中文字）

    # 项目路径配置
    output_dir: str = "novel_ai_agent/output"
    novels_dir: str = "novel_ai_agent/output/novels"
    outlines_dir: str = "novel_ai_agent/output/outlines"
    characters_dir: str = "novel_ai_agent/output/characters"

    # 向量数据库配置
    chroma_persist_directory: str = "novel_ai_agent/data/chroma"

    # Agent配置
    max_iterations: int = 10
    verbose: bool = True

    # 写作配置
    default_chapter_words: int = 4000  # 默认章节字数（约5000-6000 tokens输出）

    # 代理配置（用于Charles抓包）
    proxy_enabled: bool = False  # 默认关闭代理
    proxy_url: str = "http://127.0.0.1:8888"  # Charles默认端口

    def get_model_name(self) -> str:
        """
        根据provider获取默认模型名称

        Returns:
            str: 模型名称
        """
        if self.default_model:
            return self.default_model

        # 根据provider返回推荐的默认模型
        model_defaults = {
            "anthropic": "claude-sonnet-4-20250514",
            "openai": "gpt-4o",
            "deepseek": "deepseek-reasoner",
            "azure": "gpt-4"
        }
        return model_defaults.get(self.llm_provider, "claude-sonnet-4-20250514")

    def get_api_key(self) -> Optional[str]:
        """
        根据provider获取对应的API Key

        Returns:
            Optional[str]: API Key
        """
        key_mapping = {
            "anthropic": self.anthropic_api_key,
            "openai": self.openai_api_key,
            "deepseek": self.deepseek_api_key,
            "azure": self.azure_openai_api_key
        }
        return key_mapping.get(self.llm_provider)

    def validate_provider_config(self) -> tuple[bool, str]:
        """
        验证当前provider的配置是否完整

        Returns:
            tuple[bool, str]: (是否有效, 错误信息)
        """
        provider = self.llm_provider.lower()

        if provider == "anthropic":
            if not self.anthropic_api_key:
                return False, "缺少ANTHROPIC_API_KEY配置"
        elif provider == "openai":
            if not self.openai_api_key:
                return False, "缺少OPENAI_API_KEY配置"
        elif provider == "deepseek":
            if not self.deepseek_api_key:
                return False, "缺少DEEPSEEK_API_KEY配置"
        elif provider == "azure":
            if not self.azure_openai_api_key:
                return False, "缺少AZURE_OPENAI_API_KEY配置"
            if not self.azure_openai_endpoint:
                return False, "缺少AZURE_OPENAI_ENDPOINT配置"
            if not self.azure_openai_deployment:
                return False, "缺少AZURE_OPENAI_DEPLOYMENT配置"
        else:
            return False, f"不支持的LLM提供商: {provider}"

        return True, ""


# 全局配置实例 (延迟初始化,避免启动时就要求API Key)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    获取配置实例 (单例模式)

    Returns:
        Settings: 配置对象
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings():
    """重新加载配置"""
    global _settings
    _settings = Settings()
