"""
OpenAI Provider Implementation
"""
import asyncio
from typing import List
from openai import AsyncOpenAI, APITimeoutError, APIConnectionError
import structlog

from app.services.ai_provider import BaseAIProvider, AIMessage, AIResponse
from app.core.config import settings

logger = structlog.get_logger()

# Errors that are safe to retry (transient network/infra issues)
_RETRYABLE_ERRORS = (APITimeoutError, APIConnectionError)
_MAX_RETRIES = 2
_RETRY_BACKOFF = 2.0  # seconds before first retry; doubles each attempt


class OpenAIProvider(BaseAIProvider):
    """
    OpenAI API provider

    Supports GPT-4, GPT-4 Turbo, GPT-3.5, etc.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        super().__init__(api_key, model)
        self.client = AsyncOpenAI(api_key=api_key, timeout=settings.AI_TIMEOUT)

    async def chat_completion(
        self,
        messages: List[AIMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> AIResponse:
        """
        Generate chat completion using OpenAI

        Args:
            messages: List of messages
            temperature: Sampling temperature (0-2 for OpenAI)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional OpenAI parameters

        Returns:
            AIResponse with generated content
        """
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        last_error: Exception = RuntimeError("No attempts made")
        for attempt in range(1 + _MAX_RETRIES):
            if attempt > 0:
                delay = _RETRY_BACKOFF * (2 ** (attempt - 1))
                self.logger.warning(
                    "Retrying OpenAI completion",
                    attempt=attempt,
                    delay=delay,
                    error=str(last_error),
                    model=self.model,
                )
                await asyncio.sleep(delay)

            try:
                self.logger.info(
                    "Requesting OpenAI completion",
                    model=self.model,
                    message_count=len(messages)
                )

                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=openai_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )

                content = response.choices[0].message.content
                tokens_used = response.usage.total_tokens if response.usage else None
                finish_reason = response.choices[0].finish_reason

                self.logger.info(
                    "OpenAI completion successful",
                    model=self.model,
                    tokens=tokens_used,
                    finish_reason=finish_reason
                )

                return AIResponse(
                    content=content,
                    model=self.model,
                    provider="openai",
                    tokens_used=tokens_used,
                    finish_reason=finish_reason,
                    metadata={
                        "response_id": response.id,
                        "created": response.created
                    }
                )

            except _RETRYABLE_ERRORS as e:
                last_error = e
                self.logger.error(
                    "OpenAI completion failed",
                    error=str(e),
                    model=self.model,
                    attempt=attempt,
                )
            except Exception as e:
                # Non-retryable (auth errors, bad requests, etc.) — fail immediately
                self.logger.error(
                    "OpenAI completion failed",
                    error=str(e),
                    model=self.model,
                )
                raise

        raise last_error

    def get_provider_name(self) -> str:
        """Get provider name"""
        return "openai"
