"""
AI Provider Base Classes
Abstract interface for AI model providers (OpenAI, Anthropic)
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import structlog

logger = structlog.get_logger()


class AIProvider(str, Enum):
    """Supported AI providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class AIMessage:
    """Message for AI chat completion"""
    role: str  # system, user, assistant
    content: str


@dataclass
class AIResponse:
    """Response from AI provider"""
    content: str
    model: str
    provider: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseAIProvider(ABC):
    """
    Abstract base class for AI providers

    Implementations should provide provider-specific API integration
    """

    def __init__(self, api_key: str, model: str):
        """
        Initialize AI provider

        Args:
            api_key: API key for the provider
            model: Model name to use
        """
        self.api_key = api_key
        self.model = model
        self.logger = logger.bind(provider=self.get_provider_name())

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[AIMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> AIResponse:
        """
        Generate chat completion

        Args:
            messages: List of messages (system, user, assistant)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters

        Returns:
            AIResponse with generated content
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get provider name"""
        pass

    async def simple_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        Simple completion helper

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text content
        """
        messages = []

        if system_prompt:
            messages.append(AIMessage(role="system", content=system_prompt))

        messages.append(AIMessage(role="user", content=prompt))

        response = await self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return response.content


class AIProviderFactory:
    """Factory for creating AI provider instances"""

    @staticmethod
    def create_provider(
        provider: AIProvider,
        api_key: str,
        model: Optional[str] = None
    ) -> BaseAIProvider:
        """
        Create AI provider instance

        Args:
            provider: Provider type (openai, anthropic)
            api_key: API key for the provider
            model: Optional model override

        Returns:
            BaseAIProvider instance

        Raises:
            ValueError: If provider not supported
        """
        if provider == AIProvider.OPENAI:
            from app.services.openai_provider import OpenAIProvider
            default_model = model or "gpt-4o"
            return OpenAIProvider(api_key, default_model)

        elif provider == AIProvider.ANTHROPIC:
            from app.services.anthropic_provider import AnthropicProvider
            default_model = model or "claude-3-5-sonnet-20241022"
            return AnthropicProvider(api_key, default_model)

        else:
            raise ValueError(f"Unsupported AI provider: {provider}")

    @staticmethod
    def create_from_settings() -> BaseAIProvider:
        """
        Create AI provider from application settings

        Uses DEFAULT_AI_PROVIDER and corresponding API key from settings

        Returns:
            BaseAIProvider instance

        Raises:
            ValueError: If no API key configured
        """
        from app.core.config import settings

        provider = AIProvider(settings.DEFAULT_AI_PROVIDER)

        # Get API key based on provider
        if provider == AIProvider.OPENAI:
            api_key = settings.OPENAI_API_KEY
            if not api_key:
                raise ValueError("OPENAI_API_KEY not configured")
        elif provider == AIProvider.ANTHROPIC:
            api_key = settings.ANTHROPIC_API_KEY
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not configured")
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        return AIProviderFactory.create_provider(
            provider=provider,
            api_key=api_key,
            model=settings.DEFAULT_AI_MODEL
        )
