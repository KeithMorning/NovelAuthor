"""
Agent基础类
所有专业Agent的基类
支持多个LLM提供商
"""
from abc import ABC, abstractmethod
from typing import Optional, Callable, List
import httpx
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from ..config.settings import get_settings


def get_proxy_client() -> Optional[httpx.AsyncClient]:
    """获取代理客户端，用于Charles抓包"""
    settings = get_settings()
    if settings.proxy_enabled:
        return httpx.AsyncClient(proxy=settings.proxy_url, verify=False)
    return None


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

        # 获取代理客户端（用于Charles抓包）
        proxy_client = get_proxy_client()

        # 构建参数
        common_kwargs = {}
        if proxy_client is not None:
            common_kwargs["http_async_client"] = proxy_client

        if provider == "openai":
            return ChatOpenAI(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                openai_api_key=self.settings.openai_api_key,
                openai_api_base=self.settings.openai_api_base,
                organization=self.settings.openai_organization,
                **common_kwargs,
            )

        if provider == "deepseek":
            # DeepSeek使用OpenAI兼容API，禁用缓存确保每次生成都是新的
            return ChatOpenAI(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                openai_api_key=self.settings.deepseek_api_key,
                openai_api_base=self.settings.deepseek_api_base,
                extra_body={"enable_cache": False},
                **common_kwargs,
            )

        if provider == "azure":
            return AzureChatOpenAI(
                azure_deployment=self.settings.azure_openai_deployment,
                azure_endpoint=self.settings.azure_openai_endpoint,
                api_key=self.settings.azure_openai_api_key,
                api_version=self.settings.azure_openai_api_version,
                temperature=temperature,
                max_tokens=max_tokens,
                **common_kwargs,
            )

        if provider == "gemini":
            return ChatGoogleGenerativeAI(
                model=model_name,
                temperature=temperature,
                max_output_tokens=max_tokens,
                google_api_key=self.settings.gemini_api_key,
            )

        raise ValueError(
            f"不支持的LLM提供商: {provider}. "
            f"支持的提供商: anthropic, openai, deepseek, azure, gemini"
        )

    @property
    def _supports_json_mode(self) -> bool:
        """检查当前 LLM provider 是否支持 JSON Output Mode"""
        # Gemini 通过 response_mime_type 支持 JSON 输出
        # OpenAI/DeepSeek/Azure 通过 response_format 支持
        return self.settings.llm_provider.lower() in ("deepseek", "openai", "azure", "gemini")

    def _get_json_llm(self) -> BaseChatModel:
        """
        获取启用了 JSON Output Mode 的 LLM 实例。

        - OpenAI/DeepSeek/Azure: 使用 response_format={"type": "json_object"}
        - Gemini: 使用 response_mime_type="application/json"
        - Anthropic: 不支持，回退到普通 LLM（由 prompt + json_parser 兼底）
        """
        provider = self.settings.llm_provider.lower()
        if provider in ("openai", "deepseek", "azure"):
            return self.llm.bind(
                response_format={"type": "json_object"}
            )
        if provider == "gemini":
            return self.llm.bind(
                response_mime_type="application/json"
            )
        # Anthropic 不支持 response_format
        return self.llm

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

    async def _stream_invoke(
        self,
        llm: BaseChatModel,
        messages: List[BaseMessage],
        on_token: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        流式调用 LLM，实时拼接 chunk 并通过回调通知。

        Args:
            llm: 要调用的 LLM 实例（可以是 self.llm 或 self._get_json_llm()）
            messages: 消息列表
            on_token: 可选回调，每次收到新 chunk 时调用，参数为 chunk 文本

        Returns:
            str: 完整的响应内容
        """
        full_chunks: list[str] = []
        async for chunk in llm.astream(messages):
            chunk_text = chunk.content if hasattr(chunk, "content") else str(chunk)
            if chunk_text:
                full_chunks.append(chunk_text)
                if on_token:
                    on_token(chunk_text)
        return "".join(full_chunks)

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
