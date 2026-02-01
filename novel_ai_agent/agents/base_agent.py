"""
Agent基础类
所有专业Agent的基类
支持多个LLM提供商
"""
from abc import ABC, abstractmethod
from typing import Optional, Union
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_core.language_models import BaseChatModel
from ..config.settings import get_settings


class BaseAgent(ABC):
    """Agent基类"""

    def __init__(self, name: str, description: str):
        """
        初始化Agent

        Args:
            name: Agent名称
            description: Agent描述
        """
        self.name = name
        self.description = description
        self.settings = get_settings()
        self.llm = self._create_llm()

    def _create_llm(self) -> BaseChatModel:
        """
        根据配置创建LLM实例

        Returns:
            BaseChatModel: LLM实例

        Raises:
            ValueError: 如果配置无效或不支持的provider
        """
        provider = self.settings.llm_provider.lower()

        # 验证配置
        is_valid, error_msg = self.settings.validate_provider_config()
        if not is_valid:
            raise ValueError(f"LLM配置无效: {error_msg}")

        model_name = self.settings.get_model_name()
        temperature = self.settings.temperature
        max_tokens = self.settings.max_tokens

        if provider == "anthropic":
            return ChatAnthropic(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                anthropic_api_key=self.settings.anthropic_api_key,
                anthropic_api_url=self.settings.anthropic_api_base,
            )

        elif provider == "openai":
            return ChatOpenAI(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                openai_api_key=self.settings.openai_api_key,
                openai_api_base=self.settings.openai_api_base,
                organization=self.settings.openai_organization,
            )

        elif provider == "deepseek":
            # DeepSeek使用OpenAI兼容API
            return ChatOpenAI(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                openai_api_key=self.settings.deepseek_api_key,
                openai_api_base=self.settings.deepseek_api_base,
            )

        elif provider == "azure":
            return AzureChatOpenAI(
                azure_deployment=self.settings.azure_openai_deployment,
                azure_endpoint=self.settings.azure_openai_endpoint,
                api_key=self.settings.azure_openai_api_key,
                api_version=self.settings.azure_openai_api_version,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        else:
            raise ValueError(
                f"不支持的LLM提供商: {provider}. "
                f"支持的提供商: anthropic, openai, deepseek, azure"
            )

    @abstractmethod
    async def execute(self, **kwargs):
        """
        执行Agent任务 (异步)

        Args:
            **kwargs: 任务参数

        Returns:
            执行结果
        """
        pass

    def execute_sync(self, **kwargs):
        """
        执行Agent任务 (同步)

        Args:
            **kwargs: 任务参数

        Returns:
            执行结果
        """
        import asyncio
        return asyncio.run(self.execute(**kwargs))

    def get_provider_info(self) -> dict:
        """
        获取当前使用的LLM提供商信息

        Returns:
            dict: 提供商信息
        """
        return {
            "provider": self.settings.llm_provider,
            "model": self.settings.get_model_name(),
            "temperature": self.settings.temperature,
            "max_tokens": self.settings.max_tokens
        }

    def __repr__(self):
        provider_info = self.get_provider_info()
        return (
            f"{self.name}Agent: {self.description}\n"
            f"  Provider: {provider_info['provider']}\n"
            f"  Model: {provider_info['model']}"
        )
